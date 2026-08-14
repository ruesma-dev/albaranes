# tests/test_f012_r7_r8_cli.py
"""F-012 · R7 y R8: de dónde sale el número de workers y cuándo NO se paraleliza.

El default por núcleos con tope, la precedencia `--workers` > `rigor.json` >
default, y la garantía de que con menos de dos mutantes la campaña sigue siendo
la de siempre: in situ y sin crear ni un worktree.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from harness.alcance import Alcance
from harness.mutacion import (
    MUERTO,
    TOPE_WORKERS,
    InformeMutacion,
    main,
    resolver_workers,
    workers_por_defecto,
)
from harness.mutacion_paralela import ejecutar_campania_paralela
from harness.rigor import workers_mutacion

FUENTE_BASE = "def suma(a, b):\n    return 0\n"
FUENTE_NUEVA = (
    "def suma(a, b):\n"
    "    if a == b:\n"
    "        return a + b\n"
    "    return a - b\n"
)


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
def repo_con_feature(tmp_path: Path) -> Path:
    """Repositorio con `dev` y una rama de feature que cambia UNA línea."""
    raiz = tmp_path / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.email", "arnes@ejemplo.invalid")
    _git(raiz, "config", "user.name", "Arnes")
    (raiz / "codigo.py").write_text(FUENTE_BASE, encoding="utf-8")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "base")
    _git(raiz, "branch", "-M", "dev")
    _git(raiz, "checkout", "-q", "-b", "feature/F-999-prueba")
    (raiz / "codigo.py").write_text(FUENTE_NUEVA, encoding="utf-8")
    _git(raiz, "commit", "-q", "-a", "-m", "F-999: una linea")
    return raiz


class _EjecutorFalso:
    def __init__(self, registro: list[str], raiz: str) -> None:
        self.registro = registro
        self.raiz = raiz

    def ejecutar(self, timeout_s: int) -> str:
        self.registro.append(self.raiz)
        return MUERTO


# --- R7: de dónde sale el número de workers ---------------------------------


def test_f012_r7_workers_por_defecto_son_los_nucleos_menos_dos(monkeypatch) -> None:
    monkeypatch.setattr("harness.mutacion.os.cpu_count", lambda: 8)

    assert workers_por_defecto() == 6


def test_f012_r7_workers_por_defecto_tienen_tope(monkeypatch) -> None:
    monkeypatch.setattr("harness.mutacion.os.cpu_count", lambda: 22)

    assert workers_por_defecto() == TOPE_WORKERS == 16


def test_f012_r7_workers_por_defecto_nunca_bajan_de_uno(monkeypatch) -> None:
    monkeypatch.setattr("harness.mutacion.os.cpu_count", lambda: 1)
    assert workers_por_defecto() == 1

    monkeypatch.setattr("harness.mutacion.os.cpu_count", lambda: None)
    assert workers_por_defecto() == 1


def test_f012_r7_la_cli_manda_sobre_rigor_json_y_sobre_el_default() -> None:
    assert resolver_workers(3, 8) == 3
    assert resolver_workers(1, 8) == 1


def test_f012_r7_sin_cli_manda_rigor_json() -> None:
    assert resolver_workers(None, 8) == 8


def test_f012_r7_sin_cli_ni_rigor_json_manda_el_default_por_nucleos() -> None:
    assert resolver_workers(None, None) == workers_por_defecto()


def test_f012_r7_la_clave_workers_de_rigor_json_es_opcional() -> None:
    assert workers_mutacion({"mutacion": {"timeout_por_mutante_s": 120}}) is None
    assert workers_mutacion({}) is None


def test_f012_r7_la_clave_workers_se_lee_cuando_esta_declarada() -> None:
    assert workers_mutacion({"mutacion": {"workers": 6}}) == 6


def test_f012_r7_un_solo_worker_declarado_en_rigor_json_vale() -> None:
    assert workers_mutacion({"mutacion": {"workers": 1}}) == 1


def test_f012_r7_una_clave_workers_absurda_se_ignora() -> None:
    assert workers_mutacion({"mutacion": {"workers": 0}}) is None
    assert workers_mutacion({"mutacion": {"workers": -4}}) is None
    assert workers_mutacion({"mutacion": {"workers": "muchos"}}) is None
    assert workers_mutacion({"mutacion": {"workers": True}}) is None


def test_f012_r7_el_default_de_este_repositorio_no_cablea_ningun_numero() -> None:
    from harness.rigor import RUTA_RIGOR, cargar_rigor

    assert workers_mutacion(cargar_rigor(RUTA_RIGOR)) is None


# --- R8: cuándo NO se paraleliza --------------------------------------------


def test_f012_r8_con_un_solo_mutante_no_se_crea_ningun_worktree(
    repo_con_feature: Path,
) -> None:
    registro: list[str] = []
    alcance = Alcance(
        feature="F-999",
        origen="rama",
        ref_diff=("dev", "feature/F-999-prueba"),
        lineas={"codigo.py": {2}},
    )

    informe = ejecutar_campania_paralela(
        alcance,
        servicios=[],
        raiz=str(repo_con_feature),
        workers=8,
        fabrica=lambda _fichero, raiz: _EjecutorFalso(registro, raiz),
    )

    assert informe.evaluados == 1
    assert len(_git(repo_con_feature, "worktree", "list").strip().splitlines()) == 1
    assert registro == [str(repo_con_feature)]
    assert (repo_con_feature / "codigo.py").read_text(encoding="utf-8") == FUENTE_NUEVA


def test_f012_r8_sin_mutantes_no_se_crea_ningun_worktree(repo_con_feature: Path) -> None:
    alcance = Alcance(
        feature="F-999",
        origen="rama",
        ref_diff=("dev", "feature/F-999-prueba"),
        lineas={"codigo.py": {1}},
    )

    informe = ejecutar_campania_paralela(
        alcance,
        servicios=[],
        raiz=str(repo_con_feature),
        workers=8,
        fabrica=lambda _f, raiz: _EjecutorFalso([], raiz),
    )

    assert informe.evaluados == 0
    assert informe.generados == 0
    assert len(_git(repo_con_feature, "worktree", "list").strip().splitlines()) == 1


def test_f012_r8_con_workers_1_la_cli_no_llama_a_la_campania_paralela(
    repo_con_feature: Path, tmp_path: Path, monkeypatch
) -> None:
    import harness.mutacion_paralela as paralela

    def prohibido(*_args, **_kwargs):
        raise AssertionError("con --workers 1 no se paraleliza")

    monkeypatch.setattr(paralela, "ejecutar_campania_paralela", prohibido)
    salida = tmp_path / "informe.md"

    codigo = main(
        [
            "--feature", "F-999",
            "--rama", "feature/F-999-prueba",
            "--base", "dev",
            "--raiz", str(repo_con_feature),
            "--salida", str(salida),
            "--workers", "1",
        ],
        ejecutor=_EjecutorFalso([], str(repo_con_feature)),
    )

    assert codigo == 0
    assert "Mutantes evaluados | 3" in salida.read_text(encoding="utf-8")
    assert len(_git(repo_con_feature, "worktree", "list").strip().splitlines()) == 1


def test_f012_r7_la_cli_pasa_el_numero_de_workers_al_coordinador(
    repo_con_feature: Path, tmp_path: Path, monkeypatch
) -> None:
    import harness.mutacion_paralela as paralela

    recibido: dict[str, object] = {}

    def espia(alcance, servicios, **kwargs):
        recibido.update(kwargs)
        recibido["ficheros"] = alcance.ficheros()
        return InformeMutacion(feature=alcance.feature, alcance=alcance)

    monkeypatch.setattr(paralela, "ejecutar_campania_paralela", espia)

    codigo = main(
        [
            "--feature", "F-999",
            "--rama", "feature/F-999-prueba",
            "--base", "dev",
            "--raiz", str(repo_con_feature),
            "--salida", str(tmp_path / "informe.md"),
            "--workers", "5",
            "--max-mutantes", "60",
            "--semilla", "20260813",
        ]
    )

    assert codigo == 0
    assert recibido["workers"] == 5
    assert recibido["max_mutantes"] == 60
    assert recibido["semilla"] == 20260813
    assert recibido["raiz"] == str(repo_con_feature)
    assert recibido["ficheros"] == ["codigo.py"]


def test_f012_r8_con_workers_2_la_cli_ya_paraleliza(
    repo_con_feature: Path, tmp_path: Path, monkeypatch
) -> None:
    """Dos es la frontera: con dos workers ya se paraleliza, no a partir de tres."""
    import harness.mutacion_paralela as paralela

    recibido: dict[str, object] = {}

    def espia(alcance, servicios, **kwargs):
        recibido.update(kwargs)
        return InformeMutacion(feature=alcance.feature, alcance=alcance)

    monkeypatch.setattr(paralela, "ejecutar_campania_paralela", espia)

    codigo = main(
        [
            "--feature", "F-999",
            "--rama", "feature/F-999-prueba",
            "--base", "dev",
            "--raiz", str(repo_con_feature),
            "--salida", str(tmp_path / "informe.md"),
            "--workers", "2",
        ]
    )

    assert codigo == 0
    assert recibido["workers"] == 2


def test_f012_r8_un_ejecutor_inyectado_desactiva_la_paralela(
    repo_con_feature: Path, tmp_path: Path, monkeypatch
) -> None:
    """Con ejecutor inyectado se juzga con ESE, aunque se pidan varios workers."""
    import harness.mutacion_paralela as paralela

    def prohibido(*_args, **_kwargs):
        raise AssertionError("con ejecutor inyectado no se paraleliza")

    monkeypatch.setattr(paralela, "ejecutar_campania_paralela", prohibido)
    registro: list[str] = []

    codigo = main(
        [
            "--feature", "F-999",
            "--rama", "feature/F-999-prueba",
            "--base", "dev",
            "--raiz", str(repo_con_feature),
            "--salida", str(tmp_path / "informe.md"),
            "--workers", "4",
        ],
        ejecutor=_EjecutorFalso(registro, str(repo_con_feature)),
    )

    assert codigo == 0
    assert len(registro) == 3  # los tres mutantes, todos con el ejecutor inyectado


def test_f012_r8_con_servicios_declarados_el_ejecutor_inyectado_sigue_mandando(
    tmp_path: Path
) -> None:
    """El ejecutor inyectado gana también en un monorepo con servicios.

    Si aquí se colara la factoría por servicio, el test lanzaría pytest de
    verdad contra un servicio de mentira: el registro se quedaría vacío.
    """
    raiz = tmp_path / "repo"
    (raiz / "services" / "svc").mkdir(parents=True)
    (raiz / "harness").mkdir()
    (raiz / "harness" / "servicios.json").write_text(
        '{"servicios": [{"nombre": "svc", "ruta": "services/svc", '
        '"lenguaje": "python"}]}',
        encoding="utf-8",
    )
    (raiz / "services" / "svc" / "codigo.py").write_text(FUENTE_BASE, encoding="utf-8")
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.email", "arnes@ejemplo.invalid")
    _git(raiz, "config", "user.name", "Arnes")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "base")
    _git(raiz, "branch", "-M", "dev")
    _git(raiz, "checkout", "-q", "-b", "feature/F-999-prueba")
    (raiz / "services" / "svc" / "codigo.py").write_text(FUENTE_NUEVA, encoding="utf-8")
    _git(raiz, "commit", "-q", "-a", "-m", "F-999: una linea")
    registro: list[str] = []

    codigo = main(
        [
            "--feature", "F-999",
            "--rama", "feature/F-999-prueba",
            "--base", "dev",
            "--raiz", str(raiz),
            "--salida", str(tmp_path / "informe.md"),
            "--workers", "1",
        ],
        ejecutor=_EjecutorFalso(registro, str(raiz)),
    )

    assert codigo == 0
    assert len(registro) == 3


def test_f012_r9_la_cli_devuelve_2_con_el_arbol_sucio(
    repo_con_feature: Path, tmp_path: Path
) -> None:
    (repo_con_feature / "codigo.py").write_text(
        FUENTE_NUEVA + "# sucio\n", encoding="utf-8"
    )

    codigo = main(
        [
            "--feature", "F-999",
            "--rama", "feature/F-999-prueba",
            "--base", "dev",
            "--raiz", str(repo_con_feature),
            "--salida", str(tmp_path / "informe.md"),
            "--workers", "4",
        ]
    )

    assert codigo == 2
    assert len(_git(repo_con_feature, "worktree", "list").strip().splitlines()) == 1
