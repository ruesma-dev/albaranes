# tests/test_f075_importes.py
"""F-075 R1, R2: el importe del albarán y el control del pie, una sola vez en comun."""
from __future__ import annotations

import math

import pytest
from ruesma_comun.importes import (
    ComparacionPie,
    ImporteAlbaran,
    difieren,
    importe_albaran,
    pie_cuadra,
    unitario_despejado,
)


# --------------------------------------------------------------------- R1
def test_f075_r1_suma_con_signo_y_sin_redondear():
    r = importe_albaran([10.005, -2.0, 0.001])
    assert r.total == pytest.approx(8.006)
    assert r.lineas == 3
    assert r.lineas_con_importe == 3
    assert r.parcial is False
    assert r.sin_importe == 0
    assert r.trae_importes is True


def test_f075_r1_none_no_suman_y_marcan_parcial():
    r = importe_albaran([100.0, None, 50.5, None])
    assert r.total == pytest.approx(150.5)
    assert r.lineas == 4
    assert r.lineas_con_importe == 2
    assert r.sin_importe == 2
    assert r.parcial is True
    assert r.trae_importes is True


def test_f075_r1_ningun_importe_total_nulo():
    r = importe_albaran([None, None])
    assert r.total is None
    assert r.lineas == 2
    assert r.lineas_con_importe == 0
    assert r.parcial is False
    assert r.trae_importes is False
    assert r.sin_importe == 2


def test_f075_r1_sin_lineas():
    r = importe_albaran([])
    assert r.total is None
    assert (r.lineas, r.lineas_con_importe, r.parcial, r.trae_importes) == (0, 0, False, False)


def test_f075_r1_cero_es_un_importe_leido():
    r = importe_albaran([0.0])
    assert r.total == 0.0
    assert r.trae_importes is True
    assert r.parcial is False


@pytest.mark.parametrize("raro", [math.nan, math.inf, -math.inf, "abc", object()])
def test_f075_r1_no_finito_o_no_numerico_cuenta_como_sin_importe(raro):
    r = importe_albaran([5.0, raro])
    assert r.total == 5.0
    assert r.lineas == 2
    assert r.lineas_con_importe == 1
    assert r.parcial is True


def test_f075_r1_acepta_texto_numerico_y_generador():
    r = importe_albaran(x for x in ["2.5", 1])
    assert r.total == pytest.approx(3.5)
    assert r.lineas_con_importe == 2


def test_f075_r1_es_inmutable():
    r = importe_albaran([1.0])
    with pytest.raises(Exception):
        r.total = 2.0  # type: ignore[misc]
    assert isinstance(r, ImporteAlbaran)


# --------------------------------------------------------------- difieren
@pytest.mark.parametrize(
    ("a", "b", "esperado"),
    [
        (100.0, 100.0, False),
        (100.0, 100.004, False),
        (100.0, 100.01, True),
        (100.0, 99.99, True),
        (100.0, 100.006, True),   # round(0.006, 2) = 0.01
        (None, 100.0, False),
        (100.0, None, False),
        (None, None, False),
        (-5.0, 5.0, True),
    ],
)
def test_f075_difieren(a, b, esperado):
    assert difieren(a, b) is esperado


def test_f075_difieren_umbral_configurable():
    assert difieren(10.0, 10.5, umbral=1.0) is False
    assert difieren(10.0, 11.0, umbral=1.0) is True


# --------------------------------------------------------------------- R2
def test_f075_r2_cuadra_con_la_base():
    assert pie_cuadra(100.0, base=100.01, cuota=21.0, total=121.01, tolerancia=0.02) == (
        ComparacionPie.CUADRA, 100.01,
    )


def test_f075_r2_no_cuadra_con_la_base():
    estado, ref = pie_cuadra(100.0, base=110.0, cuota=None, total=None, tolerancia=0.02)
    assert estado is ComparacionPie.NO_CUADRA
    assert ref == 110.0


def test_f075_r2_borde_de_la_tolerancia():
    assert pie_cuadra(100.0, base=100.02, cuota=None, total=None, tolerancia=0.02)[0] is ComparacionPie.CUADRA
    assert pie_cuadra(100.0, base=100.03, cuota=None, total=None, tolerancia=0.02)[0] is ComparacionPie.NO_CUADRA
    assert pie_cuadra(100.0, base=99.97, cuota=None, total=None, tolerancia=0.02)[0] is ComparacionPie.NO_CUADRA


def test_f075_r2_sin_base_usa_total_menos_cuota():
    estado, ref = pie_cuadra(100.0, base=None, cuota=21.0, total=121.0, tolerancia=0.02)
    assert estado is ComparacionPie.CUADRA
    assert ref == pytest.approx(100.0)
    estado, ref = pie_cuadra(90.0, base=None, cuota=21.0, total=121.0, tolerancia=0.02)
    assert estado is ComparacionPie.NO_CUADRA
    assert ref == pytest.approx(100.0)


def test_f075_r2_solo_total_no_comparable_y_no_supone_iva():
    # 100 + 21 % = 121: aun así no se compara (v2-P4).
    assert pie_cuadra(100.0, base=None, cuota=None, total=121.0, tolerancia=0.02) == (
        ComparacionPie.NO_COMPARABLE, None,
    )
    assert pie_cuadra(100.0, base=None, cuota=21.0, total=None, tolerancia=0.02) == (
        ComparacionPie.NO_COMPARABLE, None,
    )


def test_f075_r2_nada_o_sin_suma_no_comparable():
    assert pie_cuadra(100.0, base=None, cuota=None, total=None, tolerancia=0.02) == (
        ComparacionPie.NO_COMPARABLE, None,
    )
    assert pie_cuadra(None, base=100.0, cuota=None, total=None, tolerancia=0.02) == (
        ComparacionPie.NO_COMPARABLE, 100.0,
    )


def test_f075_r2_base_no_finita_cae_a_total_menos_cuota():
    estado, ref = pie_cuadra(100.0, base=math.nan, cuota=21.0, total=121.0, tolerancia=0.02)
    assert estado is ComparacionPie.CUADRA
    assert ref == pytest.approx(100.0)


def test_f075_r2_valores_son_texto_estable():
    assert [c.value for c in ComparacionPie] == ["cuadra", "no_cuadra", "no_comparable"]


# ------------------------------------------------------- unitario despejado
def test_f075_r6_unitario_despejado_sin_descuento():
    assert unitario_despejado(importe=50.0, cantidad=4.0) == 12.5


def test_f075_r6_unitario_despejado_deshace_el_descuento():
    # 108 ud × 0,543 × 0,6 = 35,1864 ⇒ el bruto es 0,543.
    assert unitario_despejado(importe=35.1864, cantidad=108, descuento_pct=40) == pytest.approx(0.543)


def test_f075_r6_unitario_despejado_redondea_a_seis():
    assert unitario_despejado(importe=10.0, cantidad=3.0) == 3.333333


@pytest.mark.parametrize(
    ("importe", "cantidad", "dto"),
    [(None, 2.0, None), (10.0, None, None), (10.0, 0.0, None), (10.0, 2.0, 100), ("x", 2.0, None), (10.0, "y", None)],
)
def test_f075_r6_unitario_despejado_no_derivable(importe, cantidad, dto):
    assert unitario_despejado(importe=importe, cantidad=cantidad, descuento_pct=dto) is None


def test_f075_r6_unitario_despejado_descuento_invalido_no_descuenta():
    assert unitario_despejado(importe=20.0, cantidad=2.0, descuento_pct=150) == 10.0


def test_f075_r2_la_diferencia_se_mide_en_centimos():
    # 0,024 € son 2 céntimos: con 0,02 de tolerancia, cuadra.
    assert pie_cuadra(100.0, base=100.024, cuota=None, total=None, tolerancia=0.02)[0] is ComparacionPie.CUADRA
    assert pie_cuadra(100.0, base=100.026, cuota=None, total=None, tolerancia=0.02)[0] is ComparacionPie.NO_CUADRA
