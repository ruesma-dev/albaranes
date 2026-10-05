# tests/test_f051_almacen_front.py
"""F-051 · almacén por línea · sv4 pinta, elige y asigna almacén.

Decisión del humano (D1, PARADA 1 del 2026-10-05): «en el visor cuando
una línea no tenga partida que sea almacén […] negocio ya funciona así a
mano». Una línea con valoración y ``codigo_partida_final`` vacío ES
almacén, tenga o no marca en ``partida_action`` (la marca solo deja
rastro de quién o por qué). Vaciar la partida en sv4 es elegir almacén
(R12) y una fila de contrato en almacén sigue siendo de contrato (D4).

Sin red, sin BBDD real y sin LLM: funciones puras, el repositorio sobre
SQLite en memoria (patrón de ``conftest.py``), la plantilla real con
Jinja2 y la API con ``TestClient`` y servicio falso.
"""
from __future__ import annotations

import pytest

# =================================================================== #
# R10 · estado de partida: dos valores, sin mirar la marca
# =================================================================== #


@pytest.mark.parametrize("final", ["03.02", " 03.02 ", "ALM"])
def test_f051_r10_partida_no_vacia_es_partida(final):
    from domain.services.almacen import estado_partida

    assert estado_partida(final) == "partida"


@pytest.mark.parametrize("final", [None, "", "   ", "\t"])
def test_f051_r10_vacia_o_espacios_es_almacen(final):
    from domain.services.almacen import estado_partida

    assert estado_partida(final) == "almacen"


def test_f051_r10_la_firma_no_recibe_la_marca():
    """D1 v4: ninguna marca decide el estado (legado ``no_action``,
    ``almacen_sin_partida``, ``almacen_elegido`` o sin marca)."""
    import inspect

    from domain.services.almacen import estado_partida

    assert list(inspect.signature(estado_partida).parameters) == [
        "codigo_partida_final",
    ]


def test_f051_r10_accion_almacen_elegido():
    from domain.services.almacen import ACCION_ALMACEN_ELEGIDO

    assert ACCION_ALMACEN_ELEGIDO == "almacen_elegido"


def test_f051_r17_contar_con_partida():
    from domain.services.almacen import contar_con_partida

    assert contar_con_partida(["03.02", None, "", "  ", "04.05", "ALM"]) == 3
    assert contar_con_partida([]) == 0
    assert contar_con_partida(iter([None, "01"])) == 1


# =================================================================== #
# R21 · confianza: la partida vacía con valoración está resuelta
# =================================================================== #


def _conciliacion(**campos):
    from domain.models.review_models import ConciliacionDisplay

    return ConciliacionDisplay(**{"kind": "assigned", **campos})


@pytest.mark.parametrize("partida", [None, "", "  "])
def test_f051_r21_almacen_con_valoracion_puntua_1(partida):
    from domain.services.confianza import _partida_factor

    assert _partida_factor(_conciliacion(codigo_partida=partida)) == 1.0


def test_f051_r21_con_partida_sigue_puntuando_1():
    from domain.services.confianza import _partida_factor

    assert _partida_factor(_conciliacion(codigo_partida="03.02")) == 1.0


def test_f051_r21_sin_valoracion_sigue_puntuando_0():
    from domain.services.confianza import _partida_factor

    assert _partida_factor(None) == 0.0


def test_f051_r21_la_linea_en_almacen_no_resta_confianza():
    """Misma línea, con y sin partida: misma puntuación."""
    from domain.services.confianza import _line_score

    con = _conciliacion(codigo_partida="03.02", match_method="exact_concept",
                        match_confidence_pct=95.0, agree_unitario=True,
                        precio_unitario_final=10.0)
    sin = _conciliacion(codigo_partida=None, match_method="exact_concept",
                        match_confidence_pct=95.0, agree_unitario=True,
                        precio_unitario_final=10.0)
    assert _line_score(sin) == _line_score(con)
