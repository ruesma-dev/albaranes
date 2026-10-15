# tests/test_f072_r31_r33_escenarios.py
"""F-072 · R31–R33 (y R16): escenarios de punta a punta del módulo de caché.

Git y sonda reales: la sonda se lanza con el intérprete de este test, sobre un
repositorio diminuto en `tmp_path`. Son los tres casos que motivaron la
feature: (a) un commit en la comun no invalidaba la caché de quien la importa;
(b) en un worktree, la suite importaba la comun de OTRO árbol y la caché daba
verde; y el del encargo 1.7.12 del taller: un `.env` que cambia.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from harness.cache_suites import decidir, lineas_de_salida, sondear
from harness.servicios import Servicio

PY = sys.executable


@pytest.fixture(autouse=True)
def _sin_variables_git(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in list(os.environ):
        if variable.startswith("GIT_"):
            monkeypatch.delenv(variable, raising=False)


def _git(raiz: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=Arnes", "-c", "user.email=arnes@ejemplo.invalid",
         "-C", str(raiz), *args],
        capture_output=True, text=True, encoding="utf-8", check=True,
        env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
    )


def _escribir(raiz: Path, ruta: str, texto: str) -> Path:
    fichero = raiz / ruta
    fichero.parent.mkdir(parents=True, exist_ok=True)
    fichero.write_text(texto, encoding="utf-8")
    return fichero


def _commit(raiz: Path) -> None:
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "cambio")


@pytest.fixture(scope="module")
def _plantilla(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Se crea una vez por módulo: en Windows, cada proceso git cuesta."""
    raiz = tmp_path_factory.mktemp("plantilla_f072_escenarios") / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    _escribir(raiz, ".gitignore", ".env\n__pycache__/\n")
    _escribir(raiz, "services/app/main.py", "import comunlib\n")
    _escribir(raiz, "services/comun/comunlib/__init__.py", "VALOR = 1\n")
    _escribir(raiz, "services/solo/main.py", "X = 1\n")
    _commit(raiz)
    return raiz


@pytest.fixture
def repo(_plantilla: Path, tmp_path: Path) -> Path:
    raiz = tmp_path / "repo"
    shutil.copytree(_plantilla, raiz)
    return raiz


APP = Servicio(nombre="app", ruta="services/app", lenguaje="python",
               depende_de=("services/comun",))
SOLO = Servicio(nombre="solo", ruta="services/solo", lenguaje="python")


# --- R31: escenario (a) -------------------------------------------------------


def test_f072_r31_commit_en_la_dependencia_cambia_la_clave_del_dependiente(
    repo: Path,
) -> None:
    app_antes = decidir(APP, str(repo)).clave
    solo_antes = decidir(SOLO, str(repo)).clave

    _escribir(repo, "services/comun/comunlib/__init__.py", "VALOR = 2  # comentario\n")
    _commit(repo)

    app_despues = decidir(APP, str(repo)).clave
    assert app_antes is not None and app_despues is not None
    assert app_despues != app_antes
    assert solo_antes is not None
    assert decidir(SOLO, str(repo)).clave == solo_antes


# --- R32: escenario (b), el worktree que importa la comun de otro árbol --------


def test_f072_r32_modulo_de_fuera_del_repositorio_ejecuta_sin_clave_y_avisa(
    repo: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fuera = tmp_path / "fuera"
    _escribir(fuera, "comunlib/__init__.py", "VALOR = 'del arbol principal'\n")
    monkeypatch.setenv("PYTHONPATH", str(fuera))
    servicio = Servicio(nombre="app", ruta="services/app", lenguaje="python",
                        depende_de=("services/comun",), importa=("comunlib",))
    (repo / ".arnes_cache").mkdir()
    (repo / ".arnes_cache" / "suite_app.ok").write_text("x" * 64, encoding="utf-8")

    decision = decidir(servicio, str(repo))
    lineas = lineas_de_salida(decision)

    assert decision.servir is False and decision.clave is None
    assert lineas[-1] == "EJECUTAR|"
    assert len(lineas) == 2 and lineas[0].startswith("AVISO|")
    assert "comunlib" in lineas[0]
    assert "fuera de este repositorio" in lineas[0]
    assert os.path.normcase(str(fuera.resolve())) in os.path.normcase(lineas[0])


# --- R33: el encargo 1.7.12, el .env que cambia y el __pycache__ que no cuenta --


def test_f072_r33_tocar_el_env_del_servicio_cambia_la_clave(repo: Path) -> None:
    env = _escribir(repo, "services/solo/.env", "A=1\n")
    os.utime(env, ns=(1_600_000_000_000_000_000, 1_600_000_000_000_000_000))
    antes = decidir(SOLO, str(repo)).clave

    os.utime(env, ns=(1_600_000_000_000_000_000, 1_600_000_100_000_000_000))

    despues = decidir(SOLO, str(repo)).clave
    assert antes is not None and despues is not None and despues != antes


def test_f072_r33_tocar_el_pycache_del_servicio_no_cambia_la_clave(repo: Path) -> None:
    antes = decidir(SOLO, str(repo)).clave

    _escribir(repo, "services/solo/__pycache__/main.cpython-312.pyc", "basura")

    assert antes is not None
    assert decidir(SOLO, str(repo)).clave == antes


# --- R16: la sonda localiza sin importar --------------------------------------


def test_f072_r16_la_sonda_real_no_ejecuta_el_modulo_vigilado(tmp_path: Path) -> None:
    marcador = tmp_path / "importado.txt"
    carpeta = tmp_path / "servicio"
    _escribir(carpeta, "vigilado/__init__.py",
              f"open({str(marcador)!r}, 'w').write('importado')\n")

    sondeo = sondear(PY, ("vigilado",), carpeta)

    assert not marcador.exists(), "la sonda ejecutó el __init__ del módulo vigilado"
    assert sondeo.origenes["vigilado"] is not None
    assert Path(sondeo.origenes["vigilado"]).resolve() == (
        carpeta / "vigilado" / "__init__.py").resolve()


def test_f072_r16_la_sonda_real_resuelve_desde_la_carpeta_del_servicio(
    tmp_path: Path,
) -> None:
    """El módulo solo es alcanzable desde la carpeta del servicio (su cwd)."""
    _escribir(tmp_path / "a", "solo_en_a.py", "")
    _escribir(tmp_path / "b", "otra.py", "")

    assert sondear(PY, ("solo_en_a",), tmp_path / "a").origenes["solo_en_a"] is not None
    assert sondear(PY, ("solo_en_a",), tmp_path / "b").origenes["solo_en_a"] is None


def test_f072_r16_la_sonda_real_paquete_de_espacio_de_nombres_y_submodulo(
    tmp_path: Path,
) -> None:
    _escribir(tmp_path, "espacio/modulo.py", "")
    _escribir(tmp_path, "pkg/__init__.py", "")
    _escribir(tmp_path, "pkg/sub.py", "")

    sondeo = sondear(PY, ("espacio", "pkg.sub", "pkg.falta", "nada.de.nada"), tmp_path)

    assert Path(sondeo.origenes["espacio"]).resolve() == (tmp_path / "espacio").resolve()
    assert Path(sondeo.origenes["pkg.sub"]).resolve() == (tmp_path / "pkg/sub.py").resolve()
    assert sondeo.origenes["pkg.falta"] is None
    assert sondeo.origenes["nada.de.nada"] is None


def test_f072_r16_la_sonda_real_dice_si_hay_coverage(tmp_path: Path) -> None:
    try:
        import coverage  # noqa: F401

        esperado = True
    except ImportError:
        esperado = False

    assert sondear(PY, (), tmp_path).tiene_coverage is esperado


def test_f072_r16_la_sonda_ignora_lo_que_imprima_un_paquete_padre(tmp_path: Path) -> None:
    _escribir(tmp_path, "ruidoso/__init__.py", "print('hola desde el padre')\n")
    _escribir(tmp_path, "ruidoso/hijo.py", "")

    sondeo = sondear(PY, ("ruidoso.hijo",), tmp_path)

    assert Path(sondeo.origenes["ruidoso.hijo"]).name == "hijo.py"
