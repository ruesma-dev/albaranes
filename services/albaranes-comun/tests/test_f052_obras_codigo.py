# tests/test_f052_obras_codigo.py
"""F-052 CR-C1 · una sola normalización del código de obra para sv3 y sv4.

sv3 sella con ella el rastro de la búsqueda de contratos y consulta Sigrid;
sv4 compara con ella el rastro contra los datos actuales. Antes cada uno
tenía la suya y no coincidían (`12`: `None` en sv3, `0012` en sv4).

Semántica (la de sv3, que manda): 3 dígitos ⇒ `0` delante; 4 dígitos solo
si empiezan por `0`; cualquier otra cosa ⇒ `None` (no se consulta).

NO es `ruesma_comun.contratos.origen_datos.normalizar_codigo` (F-048), que
es una forma de COMPARACIÓN sin ceros a la izquierda.
"""
from __future__ import annotations

import pytest

from ruesma_comun.obras import normalizar_codigo_obra


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("0691", "0691"),
        ("691", "0691"),
        (" 0691 ", "0691"),
        ("12", None),
        ("7", None),
        ("1234", None),
        ("1001", None),
        ("", None),
        ("abc", None),
        (None, None),
        ("12345", None),
        ("06a1", None),
        ("   ", None),
    ],
)
def test_f052_cr_c1_normalizar_codigo_obra(valor, esperado):
    assert normalizar_codigo_obra(valor) == esperado


def test_f052_cr_c1_acepta_enteros_como_texto():
    """sv3 recibe a veces la obra como número desde el JSON de la IA."""
    assert normalizar_codigo_obra(691) == "0691"  # type: ignore[arg-type]


def test_f052_cr_c1_no_es_la_forma_de_comparacion_de_f048():
    from ruesma_comun.contratos.origen_datos import normalizar_codigo

    assert normalizar_codigo("0691") == "691"
    assert normalizar_codigo_obra("0691") == "0691"
