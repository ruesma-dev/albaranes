# tests/test_f038_r10_r12_informe.py
"""F-038 · R10–R12: el informe de mutación trae los datos que hoy cuesta pedir.

Las dos reglas que más tokens habrían ahorrado en F-034 (RM1 y RM2) exigen dos
datos que hasta hoy no estaban en el informe:

- Contra qué commit se midió. La rama de F-034 creció de 56 a 1.057 líneas
  DESPUÉS de medir, y el informe seguía pareciendo válido: ~200.000 tokens de
  primer rechazo.
- Cuánto tarda una suite limpia ahí. Se declararon 18 mutantes en 111 s cuando
  la realidad eran 63 minutos; con la línea base y la media por mutante
  impresas, la incoherencia se ve leyendo, sin reejecutar nada (~350.000
  tokens de segundo rechazo).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from harness.alcance import Alcance
from harness.mutacion import (
    PYTEST_FALLOS,
    PYTEST_OK,
    BaseRota,
    InformeMutacion,
    ResultadoSuite,
    comprobar_linea_base,
    ejecutar_campania,
    sha_de_head,
)
from harness.mutacion_paralela import fusionar

FUENTE = "# app.py\ndef bandera():\n    return True\n"


class _EjecutorFalso:
    """Interfaz mínima que `ejecutar_campania` espera, sin lanzar procesos."""

    def __init__(self, raiz: str = ".", base: ResultadoSuite | None = None) -> None:
        self.raiz = raiz
        self.base = base or ResultadoSuite(codigo=PYTEST_OK)

    def identidad(self) -> tuple[str, str]:
        return (self.raiz, "falso")

    def ejecutar(self, timeout_s: int) -> str:
        return "muerto"

    def linea_base(self, timeout_s: int) -> ResultadoSuite:
        return self.base


class _SinLineaBase:
    """Doble que no sabe correr una suite: no puede aportar un tiempo."""

    raiz = "."

    def ejecutar(self, timeout_s: int) -> str:
        return "muerto"


@pytest.fixture
def arbol(tmp_path: Path) -> Path:
    """Repositorio git de un solo fichero, commiteado y limpio."""
    subprocess.run(["git", "init", "-q", "-b", "dev", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "arnes@ruesma.es"], check=True
    )
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "Arnes"], check=True)
    (tmp_path / "app.py").write_text(FUENTE, encoding="utf-8", newline="")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-q", "-m", "inicial"], check=True)
    return tmp_path


def _alcance() -> Alcance:
    return Alcance(
        feature="F-999",
        origen="rama",
        ref_diff=("dev", "feature/F-999-prueba"),
        lineas={"app.py": {3}},
    )


# --- R11: la línea base deja su tiempo medido -------------------------------


def test_f038_r11_comprobar_linea_base_devuelve_los_segundos_de_cada_ejecutor() -> None:
    tiempos = comprobar_linea_base(
        [("raiz", _EjecutorFalso()), ("servicio", _EjecutorFalso(raiz="s"))], 10
    )

    assert sorted(tiempos) == ["raiz", "servicio"]
    assert all(segundos >= 0.0 for segundos in tiempos.values())


def test_f038_r11_un_ejecutor_sin_linea_base_no_inventa_un_tiempo() -> None:
    """Mejor `n/d` que un cero: un cero se suma y se lee como medición."""
    assert comprobar_linea_base([("doble", _SinLineaBase())], 10) == {}


def test_f038_r11_una_base_roja_sigue_abortando_la_campania() -> None:
    """El tiempo es un dato de más; el veredicto de la base no cambia."""
    with pytest.raises(BaseRota):
        comprobar_linea_base(
            [("raiz", _EjecutorFalso(base=ResultadoSuite(codigo=PYTEST_FALLOS)))], 10
        )


def test_f038_r11_la_campania_guarda_el_tiempo_de_la_base_en_su_informe(
    arbol: Path,
) -> None:
    informe = ejecutar_campania(
        _alcance(), _EjecutorFalso(raiz=str(arbol)), raiz=str(arbol)
    )

    assert list(informe.segundos_linea_base) == [Path(arbol).as_posix()]


# --- R10: contra qué commit se midió ----------------------------------------


def test_f038_r10_la_campania_declara_el_sha_completo_de_head(arbol: Path) -> None:
    esperado = subprocess.run(
        ["git", "-C", str(arbol), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    informe = ejecutar_campania(
        _alcance(), _EjecutorFalso(raiz=str(arbol)), raiz=str(arbol)
    )

    assert informe.sha_head == esperado
    assert re.fullmatch(r"[0-9a-f]{40}", informe.sha_head or ""), "completo, no abreviado"


def test_f038_r10_fuera_de_un_repositorio_no_se_inventa_un_sha(tmp_path: Path) -> None:
    assert sha_de_head(str(tmp_path)) is None


# --- R12: la campaña paralela propaga lo que midieron sus workers -----------


def test_f038_r10_r11_la_agregacion_propaga_sha_y_tiempos_de_los_workers() -> None:
    alcance = _alcance()
    parciales = [
        InformeMutacion(
            feature="F-999",
            alcance=alcance,
            sha_head="a" * 40,
            segundos_linea_base={"wk_0": 12.0},
        ),
        InformeMutacion(
            feature="F-999",
            alcance=alcance,
            sha_head="a" * 40,
            segundos_linea_base={"wk_1": 13.0},
        ),
    ]

    informe = fusionar(alcance, parciales, generados=2, segundos=30.0)

    assert informe.sha_head == "a" * 40
    assert informe.segundos_linea_base == {"wk_0": 12.0, "wk_1": 13.0}


def test_f038_r12_sin_parciales_no_hay_dato_que_propagar() -> None:
    """El caso de R12: el informe tendrá que imprimir `n/d`, no un cero."""
    informe = fusionar(_alcance(), [], generados=0, segundos=0.0)

    assert informe.sha_head is None
    assert informe.segundos_linea_base == {}
