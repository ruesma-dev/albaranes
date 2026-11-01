# tests/test_f110_linea_a_sigrid.py
"""F-110 · la línea a Sigrid con descuento (R1–R5, R14, R22).

- R1/R2: ``linea_a_sigrid`` devuelve ``LineaASigrid(cantidad, precio, dto)``;
  con los valores por defecto (o sin descuento aplicable), lo de F-106 R2 con
  ``dto`` nulo.
- R3: con ``con_descuento`` y descuento aplicable, ``dto = round(d, 2)`` y el
  precio es P si da el importe al céntimo con la cantidad a Sigrid; si no, el
  bruto despejado.
- R4: ``None`` sin importe, sin cantidad o con el precio no despejable; nunca
  lanza.
- R5/R14: ``enviar_dto_activo`` solo con el literal ``true``.

Los casos de R22 viven en ``f110_casos.json``: el test de JS de sv4 lee la
misma tabla (R16).
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from ruesma_comun import alta_sigrid
from ruesma_comun.alta_sigrid import (
    LITERAL_ENVIAR_DTO,
    LineaASigrid,
    enviar_dto_activo,
    linea_a_sigrid,
)

CASOS = json.loads(
    (Path(__file__).with_name("f110_casos.json")).read_text(encoding="utf-8"),
)["casos"]


def _llamar(caso: dict) -> LineaASigrid | None:
    return linea_a_sigrid(
        vinculada=caso["vinculada"],
        cantidad_albaran=caso["cantidad_albaran"],
        cantidad_convertida=caso["cantidad_convertida"],
        importe=caso["importe"],
        precio=caso["precio"],
        descuento=caso["descuento"],
        con_descuento=caso["con_descuento"],
    )


# --------------------------------------------------------------------- R22
@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_f110_r22_casos_de_la_tabla(caso):
    linea = _llamar(caso)
    esperado = caso["esperado"]
    if esperado is None:
        assert linea is None
        return
    assert isinstance(linea, LineaASigrid)
    assert (linea.cantidad, linea.precio, linea.dto) == (
        esperado["cantidad"], esperado["precio"], esperado["dto"],
    )


def test_f110_r22_la_tabla_cubre_los_casos_de_la_spec():
    ids = {c["id"] for c in CASOS}
    for prefijo in ("a_", "b_", "c_", "d_", "e_", "f_", "g_", "h_"):
        assert any(i.startswith(prefijo) for i in ids), prefijo
    assert sum(1 for i in ids if i.startswith("g_")) == 4  # nulo, 0, −5 y 150


# ---------------------------------------------------------------- R1 / R2
def test_f110_r1_devuelve_linea_a_sigrid_con_sus_campos():
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.20,
        precio=0.645, descuento=7, con_descuento=True,
    )
    assert linea == LineaASigrid(12.0, 0.645, 7.0)
    assert (linea.cantidad, linea.precio, linea.dto) == (12.0, 0.645, 7.0)


def test_f110_r2_por_defecto_es_f106_con_dto_nulo():
    """Sin los parámetros nuevos, lo de F-106 R2: neto y sin ``dto``; se
    desempaqueta como antes (cantidad, precio)."""
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.20,
    )
    assert linea is not None
    assert (linea.cantidad, linea.precio, linea.dto) == (12.0, 0.6, None)
    cantidad, precio = linea
    assert (cantidad, precio) == (12.0, 0.6)
    assert linea == (12.0, 0.6)


def test_f110_r2_apagada_ignora_precio_y_descuento():
    con = linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.20,
        precio=0.645, descuento=7, con_descuento=False,
    )
    sin = linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.20,
    )
    assert con == sin
    assert con.dto is None


def test_f110_r1_con_dto_no_es_igual_a_la_tupla_sin_dto():
    """Una línea con ``dto`` nunca se confunde con la de F-106 (mismo
    cantidad y precio, sin ``dto``)."""
    con = LineaASigrid(12.0, 0.645, 7.0)
    assert con != (12.0, 0.645)
    assert con != LineaASigrid(12.0, 0.645, None)
    assert con != LineaASigrid(12.0, 0.645, 7.5)
    assert LineaASigrid(12.0, 0.645, None) == (12.0, 0.645)
    assert LineaASigrid(12.0, 0.645, None) != (12.0, 0.646)
    assert hash(LineaASigrid(12.0, 0.645, None)) == hash((12.0, 0.645))
    assert hash(con) == hash(LineaASigrid(12.0, 0.645, 7.0))
    assert len({con, LineaASigrid(12.0, 0.645, 7.0)}) == 1
    assert "dto=7.0" in repr(con)


def test_f110_r1_linea_inmutable():
    linea = LineaASigrid(12.0, 0.645, 7.0)
    with pytest.raises(AttributeError):
        linea.dto = 8.0  # type: ignore[misc]


# --------------------------------------------------------------------- R3
def test_f110_r3_precio_p_redondeado_a_seis():
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.20,
        precio=0.64500004, descuento=7, con_descuento=True,
    )
    assert (linea.precio, linea.dto) == (0.645, 7.0)


def test_f110_r3_un_centimo_ya_difiere():
    """``difieren`` con 0,01 €: 249,20 frente a 249,21 ya es distinto ⇒ despeje."""
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=10, cantidad_convertida=None, importe=249.20,
        precio=26.796, descuento=7, con_descuento=True,
    )
    assert linea.precio == 26.796  # 10 × 26,796 × 0,93 = 249,2028 → 249,20


def test_f110_r3_compara_con_el_valor_absoluto_del_importe():
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=2, cantidad_convertida=None, importe=-36.0,
        precio=20, descuento=10, con_descuento=True,
    )
    assert (linea.cantidad, linea.precio, linea.dto) == (-2.0, 20.0, 10.0)


def test_f110_r3_precio_negativo_se_despeja_en_positivo():
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=-2, cantidad_convertida=None, importe=-36.0,
        precio=-20, descuento=10, con_descuento=True,
    )
    assert (linea.cantidad, linea.precio, linea.dto) == (-2.0, 20.0, 10.0)


def test_f110_r3_dto_redondeado_antes_del_precio():
    """El precio se despeja con el ``dto`` redondeado (el que verá Sigrid)."""
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=10, cantidad_convertida=None, importe=100,
        precio=None, descuento=7.456, con_descuento=True,
    )
    assert linea.dto == 7.46
    assert linea.precio == round(100 / (10 * (1 - 7.46 / 100)), 6)


@pytest.mark.parametrize("precio", ["x", math.nan, math.inf, True])
def test_f110_r3_precio_ilegible_se_despeja(precio):
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.20,
        precio=precio, descuento=7, con_descuento=True,
    )
    assert (linea.precio, linea.dto) == (0.645161, 7.0)


def test_f110_r3_descuento_como_texto():
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.20,
        precio="0.645", descuento="7", con_descuento=True,
    )
    assert (linea.precio, linea.dto) == (0.645, 7.0)


def test_f110_r3_descuento_ilegible_va_como_hoy():
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.20,
        precio=0.645, descuento="siete", con_descuento=True,
    )
    assert (linea.precio, linea.dto) == (0.6, None)


def test_f110_r3_dto_justo_por_debajo_de_cien():
    linea = linea_a_sigrid(
        vinculada=False, cantidad_albaran=10, cantidad_convertida=None, importe=1,
        precio=None, descuento=99.99, con_descuento=True,
    )
    assert (linea.precio, linea.dto) == (1000.0, 99.99)


# --------------------------------------------------------------------- R4
@pytest.mark.parametrize("descuento", [100, 99.999])
def test_f110_r4_cien_por_cien_no_da_linea(descuento):
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=10, cantidad_convertida=None, importe=5,
        precio=10, descuento=descuento, con_descuento=True,
    ) is None


@pytest.mark.parametrize("cantidad", [None, 0, 1e-12, "x", math.inf])
def test_f110_r4_sin_cantidad_no_da_linea(cantidad):
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=cantidad, cantidad_convertida=None, importe=7.2,
        precio=0.645, descuento=7, con_descuento=True,
    ) is None


@pytest.mark.parametrize("importe", [None, "x", math.nan])
def test_f110_r4_sin_importe_no_da_linea(importe):
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=importe,
        precio=0.645, descuento=7, con_descuento=True,
    ) is None


def test_f110_r4_nunca_lanza_con_basura():
    for valor in (object(), [], {}, "", b"7"):
        linea_a_sigrid(
            vinculada=False, cantidad_albaran=12, cantidad_convertida=None, importe=7.2,
            precio=valor, descuento=valor, con_descuento=True,
        )


# ---------------------------------------------------------------- R5 / R14
def test_f110_r5_literal():
    assert LITERAL_ENVIAR_DTO == "true"


@pytest.mark.parametrize("valor, activo", [
    ("true", True),
    ("True", False), ("TRUE", False), (" true", False), ("true ", False),
    ("1", False), ("yes", False), ("false", False), ("", False), (None, False),
])
def test_f110_r5_enviar_dto_activo(valor, activo):
    assert enviar_dto_activo(valor) is activo


def test_f110_r1_unica_definicion_en_comun():
    assert alta_sigrid.linea_a_sigrid is linea_a_sigrid
    assert alta_sigrid.LineaASigrid is LineaASigrid
