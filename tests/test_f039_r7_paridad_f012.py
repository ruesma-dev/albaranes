# tests/test_f039_r7_paridad_f012.py
"""F-039 · R7: el test de paridad de F-012 usa la constante, no una lista propia.

Qué filas del informe de mutación son «reloj» se declara una sola vez, en
`harness.mutacion.FILAS_DE_RELOJ`, y se compara con `lineas_comparables`. R3–R6
(la constante, la comparación y sus guardas) los cubre el test genérico del
arnés `tests/test_mutacion_filas_de_reloj.py`; hasta la 1.10.0 vivían aquí como
copia con nombre de requisito y se retiraron al actualizar el arnés porque la
copia se quedó atrás (no conocía las filas de la selección de F-019). Lo único
propio de este repositorio es R7: el test de paridad de F-012 no puede volver a
llevar un filtro de filas de reloj propio.
"""

from __future__ import annotations

from pathlib import Path

from harness.mutacion import FILAS_DE_RELOJ

RUTA_TEST_F012 = Path("tests/test_f012_r1_r5_r11_coordinador.py")


def test_f039_r7_el_test_de_paridad_de_f012_usa_lineas_comparables() -> None:
    fuente = RUTA_TEST_F012.read_text(encoding="utf-8")

    assert "lineas_comparables" in fuente, (
        "el test de paridad de F-012 debe comparar con `lineas_comparables`"
    )
    assert "def _comparable" not in fuente, (
        "sigue habiendo un filtro de filas de reloj propio en el test de F-012"
    )
    for prefijo in FILAS_DE_RELOJ:
        assert prefijo not in fuente, (
            f"el test de F-012 vuelve a declarar el prefijo {prefijo!r} por su cuenta"
        )
