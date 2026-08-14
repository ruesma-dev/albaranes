# tests/test_f012_r2_r9_r10_worktrees.py
"""F-012 · R2, R9 y R10: aislamiento en worktrees, guarda y limpieza.

Se usa git de verdad, pero siempre sobre repositorios diminutos creados en
`tmp_path`: ni red, ni el repositorio real, ni un solo fichero del árbol de
trabajo del proyecto.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from harness.mutacion_paralela import Worktrees, arbol_limpio


def _git(raiz: Path, *args: str) -> str:
    proceso = subprocess.run(
        ["git", "-C", str(raiz), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return proceso.stdout or ""


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """Repositorio git mínimo, con un commit y el árbol limpio."""
    raiz = tmp_path / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.email", "arnes@ejemplo.invalid")
    _git(raiz, "config", "user.name", "Arnes")
    (raiz / "codigo.py").write_text("VALOR = 1\n", encoding="utf-8")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "inicial")
    return raiz


# --- R9: guarda de árbol limpio ---------------------------------------------


def test_f012_r9_arbol_limpio_con_el_repositorio_recien_commiteado(repo: Path) -> None:
    assert arbol_limpio(str(repo)) is True


def test_f012_r9_arbol_limpio_es_falso_con_cambios_sin_commitear(repo: Path) -> None:
    (repo / "codigo.py").write_text("VALOR = 2\n", encoding="utf-8")

    assert arbol_limpio(str(repo)) is False


def test_f012_r9_arbol_limpio_es_falso_con_ficheros_sin_seguir(repo: Path) -> None:
    (repo / "suelto.py").write_text("X = 1\n", encoding="utf-8")

    assert arbol_limpio(str(repo)) is False


def test_f012_r9_arbol_limpio_es_falso_fuera_de_un_repositorio(tmp_path: Path) -> None:
    fuera = tmp_path / "sin_git"
    fuera.mkdir()

    assert arbol_limpio(str(fuera)) is False


# --- R2 y R10: creación, aislamiento y limpieza ------------------------------


def test_f012_r10_crea_un_worktree_por_worker_con_el_codigo_de_head(repo: Path) -> None:
    with Worktrees(str(repo), 2, etiqueta="F-012") as rutas:
        assert len(rutas) == 2
        for ruta in rutas:
            assert (Path(ruta) / "codigo.py").read_text(encoding="utf-8") == "VALOR = 1\n"
        listado = _git(repo, "worktree", "list")
        assert all(Path(ruta).name in listado for ruta in rutas)


def test_f012_r2_los_worktrees_viven_fuera_del_arbol_principal(repo: Path) -> None:
    with Worktrees(str(repo), 2) as rutas:
        for ruta in rutas:
            assert repo not in Path(ruta).resolve().parents


def test_f012_r2_escribir_en_un_worktree_no_toca_el_arbol_principal(repo: Path) -> None:
    with Worktrees(str(repo), 1) as rutas:
        (Path(rutas[0]) / "codigo.py").write_text("VALOR = 99\n", encoding="utf-8")

        assert (repo / "codigo.py").read_text(encoding="utf-8") == "VALOR = 1\n"
        assert arbol_limpio(str(repo)) is True


def test_f012_r10_los_worktrees_se_retiran_al_salir(repo: Path) -> None:
    with Worktrees(str(repo), 2) as rutas:
        creadas = list(rutas)

    listado = _git(repo, "worktree", "list")
    for ruta in creadas:
        assert Path(ruta).name not in listado
        assert not Path(ruta).exists()


def test_f012_r10_los_worktrees_se_retiran_con_una_excepcion_en_vuelo(repo: Path) -> None:
    creadas: list[str] = []

    with pytest.raises(RuntimeError, match="campaña rota"), Worktrees(str(repo), 2) as rutas:
        creadas = list(rutas)
        raise RuntimeError("campaña rota")

    listado = _git(repo, "worktree", "list")
    assert creadas
    for ruta in creadas:
        assert Path(ruta).name not in listado
        assert not Path(ruta).exists()


def test_f012_r10_los_worktrees_se_retiran_con_ctrl_c(repo: Path) -> None:
    creadas: list[str] = []

    with pytest.raises(KeyboardInterrupt), Worktrees(str(repo), 1) as rutas:
        creadas = list(rutas)
        raise KeyboardInterrupt

    assert creadas and not Path(creadas[0]).exists()
    assert Path(creadas[0]).name not in _git(repo, "worktree", "list")


def test_f012_r10_el_arranque_poda_los_huerfanos_de_campanias_muertas(
    repo: Path, tmp_path: Path
) -> None:
    huerfano = tmp_path / "huerfano_de_campania_muerta"
    _git(repo, "worktree", "add", "--detach", str(huerfano), "HEAD")
    shutil.rmtree(huerfano)
    assert huerfano.name in _git(repo, "worktree", "list")

    with Worktrees(str(repo), 1):
        assert huerfano.name not in _git(repo, "worktree", "list")


def test_f012_r10_si_falla_la_retirada_el_registro_se_poda_igual(repo: Path) -> None:
    """El caso Windows: el `worktree remove` no puede con el directorio.

    Se fuerza borrando el directorio por debajo, que es lo que deja `remove`
    con un error. Al salir no puede quedar ni el registro ni una excepción
    escapándose: la limpieza es una promesa, no un intento.
    """
    gestor = Worktrees(str(repo), 1)
    with gestor as rutas:
        shutil.rmtree(rutas[0])
        fallado = _git(repo, "worktree", "list")
        assert Path(rutas[0]).name in fallado  # sigue registrado antes de salir

    assert Path(rutas[0]).name not in _git(repo, "worktree", "list")


def test_f012_r10_un_fichero_abierto_no_impide_salir_del_gestor(repo: Path) -> None:
    """El caso Windows de verdad: un fichero abierto bloquea el borrado.

    Comprobado contra git en esta máquina: con un fichero del worktree abierto,
    `git worktree remove --force` devuelve 255 («failed to delete ...: Invalid
    argument») y un `rmtree` sin `ignore_errors` lanza `PermissionError`. La
    promesa del gestor es que, aun así, salir del `with` no lanza nada: una
    campaña de dos horas no puede morir en la limpieza.
    """
    gestor = Worktrees(str(repo), 1)
    abierto = None
    rutas: list[str] = []
    try:
        with gestor as creadas:
            rutas = list(creadas)
            abierto = (Path(rutas[0]) / "codigo.py").open("a", encoding="utf-8")

        assert gestor.rutas == []
    finally:
        if abierto is not None:
            abierto.close()
        for ruta in rutas:
            shutil.rmtree(ruta, ignore_errors=True)
        _git(repo, "worktree", "prune")


def test_f012_r10_un_worktree_que_no_se_puede_crear_aborta_con_el_motivo(
    tmp_path: Path,
) -> None:
    """Sin `HEAD` no hay worktree posible, y el motivo tiene que ser legible.

    El mensaje lleva la salida REAL de git (que la escribe en stderr): sin ella
    quien lanza la campaña se queda con «no se pudo» y ninguna pista.
    """
    vacio = tmp_path / "sin_commits"
    vacio.mkdir()
    _git(vacio, "init", "-q")
    gestor = Worktrees(str(vacio), 1)

    with pytest.raises(RuntimeError, match="No se pudo crear el worktree") as fallo, gestor:
        pass  # pragma: no cover

    mensaje = str(fallo.value)
    assert "fatal" in mensaje.lower()
    assert "b'" not in mensaje  # la salida de git va como texto, no como bytes
    assert gestor.rutas == []  # el gestor se limpió a sí mismo antes de salir


def test_f012_r10_sin_workers_no_crea_ningun_worktree(repo: Path) -> None:
    antes = _git(repo, "worktree", "list").strip().splitlines()

    with Worktrees(str(repo), 0) as rutas:
        assert rutas == []
        assert len(_git(repo, "worktree", "list").strip().splitlines()) == len(antes)
