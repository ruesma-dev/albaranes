# tests/test_f012_r6_timeout.py
"""F-012 · R6: el timeout por mutante llega a cada worker y se agrega.

Un timeout que se quedara en el coordinador dejaría a los workers colgados para
siempre; uno que no se agregara escondería en el informe justo lo que hay que
mirar cuando la máquina va cargada.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from harness.alcance import Alcance
from harness.mutacion import MUERTO, TIMEOUT
from harness.mutacion_paralela import clave_estable, ejecutar_campania_paralela

FUENTE_LENTA = (
    "def lenta(a, b):\n"
    "    if a == b:\n"
    "        return a + b\n"
    "    return a - b\n"
)
FUENTE_RAPIDA = (
    "def rapida(a, b):\n"
    "    if a < b:\n"
    "        return a * b\n"
    "    return not a\n"
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
def repo(tmp_path: Path) -> Path:
    raiz = tmp_path / "repo"
    raiz.mkdir()
    _git(raiz, "init", "-q")
    _git(raiz, "config", "user.email", "arnes@ejemplo.invalid")
    _git(raiz, "config", "user.name", "Arnes")
    (raiz / "lenta.py").write_text(FUENTE_LENTA, encoding="utf-8")
    (raiz / "rapida.py").write_text(FUENTE_RAPIDA, encoding="utf-8")
    _git(raiz, "add", "-A")
    _git(raiz, "commit", "-q", "-m", "inicial")
    return raiz


def _alcance() -> Alcance:
    return Alcance(
        feature="F-012",
        origen="rama",
        ref_diff=("base", "rama"),
        lineas={"lenta.py": {1, 2, 3, 4}, "rapida.py": {1, 2, 3, 4}},
    )


class _EjecutorConTimeout:
    """Todo lo de `lenta.py` agota el tiempo; lo de `rapida.py`, no."""

    def __init__(self, fichero: str, recibidos: list[int]) -> None:
        self.fichero = fichero
        self.recibidos = recibidos

    def ejecutar(self, timeout_s: int) -> str:
        self.recibidos.append(timeout_s)
        return TIMEOUT if self.fichero == "lenta.py" else MUERTO


def test_f012_r6_el_timeout_configurado_llega_a_todos_los_workers(repo: Path) -> None:
    recibidos: list[int] = []

    ejecutar_campania_paralela(
        _alcance(),
        servicios=[],
        raiz=str(repo),
        workers=3,
        timeout_s=7,
        fabrica=lambda fichero, _raiz: _EjecutorConTimeout(fichero, recibidos),
    )

    assert recibidos
    assert set(recibidos) == {7}


def test_f012_r6_los_timeouts_de_todos_los_workers_se_agregan_y_se_ordenan(
    repo: Path,
) -> None:
    informe = ejecutar_campania_paralela(
        _alcance(),
        servicios=[],
        raiz=str(repo),
        workers=3,
        timeout_s=7,
        fabrica=lambda fichero, _raiz: _EjecutorConTimeout(fichero, []),
    )

    assert informe.timeouts
    assert all(mutante.fichero == "lenta.py" for mutante in informe.timeouts)
    assert [clave_estable(m) for m in informe.timeouts] == sorted(
        clave_estable(m) for m in informe.timeouts
    )
    assert len(informe.timeouts) + informe.muertos == informe.evaluados
    assert informe.supervivientes == []
