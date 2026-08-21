# tests/test_f040_r11_r17_honestidad.py
"""F-040 · R11–R17 (+ R20, R21): la campaña deja de mentir sobre lo que midió.

Dos mentiras distintas, las dos vistas en campo el 2026-08-21:

- **D3.** Una línea base que EXPIRA no es una base rota. El arnés decía «La
  base se rompió… arregla la suite y repite la campaña» sobre una suite
  impecable que solo se había quedado sin tiempo, y mandó al humano a buscar un
  fallo que no existía.
- **D4.** Una campaña con CERO mutantes salía en verde, escribiendo un informe
  que se lee como «nada que arreglar». Van tres puertas distintas por las que
  ha entrado el mismo fallo, así que la guarda va en el embudo (`main`), que es
  por donde pasan todas.

Ningún test de este fichero ejecuta una suite real: todos usan ejecutores
dobles que devuelven el `ResultadoSuite` que se les pide.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.alcance import Alcance
from harness.mutacion import (
    InformeMutacion,
    Mutante,
    ResultadoSuite,
    _base_rota_al_final,
    escribir_informe,
    main,
)


class EjecutorDoble:
    """Ejecutor que devuelve los resultados de línea base que se le dicten."""

    def __init__(self, *resultados: ResultadoSuite) -> None:
        self._resultados = list(resultados)
        self.llamadas = 0
        self.raiz = "raiz_doble"

    def linea_base(self, _timeout_s: int) -> ResultadoSuite:
        self.llamadas += 1
        indice = min(self.llamadas - 1, len(self._resultados) - 1)
        return self._resultados[indice]

    def ejecutar(self, _timeout_s: int) -> str:  # pragma: no cover - no se usa
        raise AssertionError("estos tests no juzgan mutantes")


VERDE = ResultadoSuite(codigo=0, salida="")
EXPIRADA = ResultadoSuite(codigo=-1, salida="", expirado=True)
FALLIDA = ResultadoSuite(
    codigo=1, salida="FAILED tests/test_uno.py::test_a\nFAILED tests/test_dos.py::test_b\n"
)


def _mutante(linea: int = 42) -> Mutante:
    return Mutante(
        fichero="harness/mutacion.py",
        linea=linea,
        col=0,
        original="a == b",
        mutado="a != b",
        operador="comparacion",
        longitud=2,
        sustituto="!=",
    )


def _alcance(feature: str = "F-040") -> Alcance:
    return Alcance(
        feature=feature,
        origen="rama",
        ref_diff=("dev", "feature/x"),
        lineas={"harness/mutacion.py": {1, 2, 3}},
    )


# --- R21 y R12: la base que estaba verde y acaba ROJA ------------------------


def test_f040_r21_una_base_verde_al_cerrar_no_produce_ningun_aviso() -> None:
    doble = EjecutorDoble(VERDE)

    assert _base_rota_al_final([("wk_0", doble)], 120) is None


def test_f040_r12_una_base_fallida_nombra_los_tests_caidos() -> None:
    """R12: el aviso de siempre, cuando la suite falla DE VERDAD."""
    aviso = _base_rota_al_final([("wk_0", EjecutorDoble(FALLIDA))], 120)

    assert aviso is not None
    assert "tests/test_uno.py::test_a" in aviso
    assert "tests/test_dos.py::test_b" in aviso
    assert "Arregla la suite" in aviso, (
        "una base realmente rota SÍ se arregla arreglando la suite"
    )


def test_f040_r21_un_ejecutor_sin_linea_base_no_cuenta() -> None:
    """Un doble sin `linea_base` no puede desmentir nada: se salta."""

    class SinBase:
        raiz = "sin_base"

    assert _base_rota_al_final([("sin", SinBase())], 120) is None


# --- R11: una base que EXPIRA no es una base rota ---------------------------


def test_f040_r11_una_base_expirada_dice_que_la_suite_NO_fallo() -> None:
    """El mensaje que mandó al humano a arreglar una suite impecable.

    La suite no falló: se quedó sin tiempo. Decirle «arregla la suite» a quien
    tiene la suite bien es peor que no decir nada, porque le hace perder la
    tarde buscando lo que no hay.
    """
    aviso = _base_rota_al_final([("wk_0", EjecutorDoble(EXPIRADA))], 240)

    assert aviso is not None
    assert "no falló" in aviso or "NO falló" in aviso
    assert "Arregla la suite" not in aviso, (
        "R11: expirar no es fallar; mandar a arreglar la suite es la mentira "
        "que esta feature quita"
    )


def test_f040_r11_la_base_expirada_dice_QUE_HACER_y_con_cuanto_tiempo() -> None:
    aviso = _base_rota_al_final([("wk_0", EjecutorDoble(EXPIRADA))], 240)

    assert aviso is not None
    assert "240" in aviso, "el aviso tiene que decir cuánto tiempo se concedió"
    assert "workers" in aviso.lower(), "la acción es bajar workers…"
    assert "suelo" in aviso.lower(), "…o subir el suelo del timeout configurado"
    assert "timeout_por_mutante_s" in aviso, "…y nombrar la clave que se sube"


def test_f040_r11_r12_los_dos_avisos_no_son_el_mismo_texto() -> None:
    expirada = _base_rota_al_final([("wk_0", EjecutorDoble(EXPIRADA))], 240)
    fallida = _base_rota_al_final([("wk_0", EjecutorDoble(FALLIDA))], 240)

    assert expirada != fallida


def test_f040_r13_los_dos_avisos_invalidan_el_informe_igual(tmp_path: Path) -> None:
    """R13: cambia el texto, no la consecuencia. `fiable` sigue siendo falso."""
    for aviso in (
        _base_rota_al_final([("wk_0", EjecutorDoble(EXPIRADA))], 240),
        _base_rota_al_final([("wk_0", EjecutorDoble(FALLIDA))], 240),
    ):
        informe = InformeMutacion(feature="F-040", alcance=_alcance())
        informe.aviso_base = aviso
        ruta = tmp_path / "informe.md"

        assert informe.fiable is False
        escribir_informe(informe, ruta)
        assert "⚠ CAMPAÑA NO VÁLIDA" in ruta.read_text(encoding="utf-8")


# --- R20: la sección `## Timeouts`, sin el prefijo duplicado ----------------


def test_f040_r20_la_seccion_de_timeouts_nombra_fichero_y_linea_UNA_vez(
    tmp_path: Path,
) -> None:
    """`Mutante.descripcion()` ya lleva `fichero:linea` dentro.

    Anteponérselo daba `- \\`a.py:3\\` a.py:3 [op] x -> y`. No revienta, pero
    nadie lo había leído nunca: la sección entera estaba sin test.
    """
    informe = InformeMutacion(feature="F-040", alcance=_alcance())
    informe.timeouts = [_mutante(42)]
    ruta = tmp_path / "informe.md"

    escribir_informe(informe, ruta)

    fila = next(
        linea
        for linea in ruta.read_text(encoding="utf-8").splitlines()
        if linea.startswith("- `harness/mutacion.py:42`")
    )
    assert fila.count("harness/mutacion.py:42") == 1, (
        f"fichero:línea duplicado en la fila de timeouts: {fila!r}"
    )
    assert "[comparacion]" in fila
    assert "a == b -> a != b" in fila


def test_f040_r20_la_seccion_de_timeouts_solo_existe_si_hay_timeouts(
    tmp_path: Path,
) -> None:
    informe = InformeMutacion(feature="F-040", alcance=_alcance())
    ruta = tmp_path / "informe.md"

    escribir_informe(informe, ruta)

    assert "## Timeouts" not in ruta.read_text(encoding="utf-8")


def test_f040_r20_hay_una_fila_por_mutante_expirado(tmp_path: Path) -> None:
    informe = InformeMutacion(feature="F-040", alcance=_alcance())
    informe.timeouts = [_mutante(10), _mutante(20), _mutante(30)]
    ruta = tmp_path / "informe.md"

    escribir_informe(informe, ruta)

    texto = ruta.read_text(encoding="utf-8")
    assert "## Timeouts" in texto
    filas = [linea for linea in texto.splitlines() if linea.startswith("- `harness/")]
    assert len(filas) == 3
