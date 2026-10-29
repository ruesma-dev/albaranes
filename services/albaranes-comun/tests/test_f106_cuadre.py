# tests/test_f106_cuadre.py
"""F-106 R1–R3: cuadre de una línea, «a Sigrid» y la regla de recálculo (D1).

Funciones puras de comun que comparten sv4 (PATCH, ficha, aprobar), sv6
(reaplicar) y sv9 (alta). Casos de la fila de producción AC26/30435: el papel
dice 10 × 11,20 −7 % = 104,16 y la fila acabó en 48 × 11,20 −7 % con I 104,16.
"""
from __future__ import annotations

import math

import pytest
from ruesma_comun import alta_sigrid, importes
from ruesma_comun.alta_sigrid import linea_a_sigrid
from ruesma_comun.edicion_manual import (
    NoDespejable,
    PrecioEImporte,
    recalcular_fila,
)
from ruesma_comun.importes import TOLERANCIA_CUADRE_EUR, cuadra_linea


# --------------------------------------------------------------------- R1
def test_f106_r1_tolerancia_unica_de_dos_centimos():
    assert TOLERANCIA_CUADRE_EUR == 0.02


def test_f106_r1_cuadra_la_linea_del_papel():
    # 10 × 11,20 × 0,93 = 104,16
    assert cuadra_linea(10, 11.2, 7, 104.16) is True


def test_f106_r1_no_cuadra_la_fila_de_produccion():
    # 48 × 11,20 × 0,93 = 499,97 ≠ 104,16
    assert cuadra_linea(48, 11.2, 7, 104.16) is False


@pytest.mark.parametrize(
    ("importe", "esperado"),
    [
        (100.02, True),   # dos céntimos: borde incluido
        (99.98, True),
        (100.03, False),  # tres: fuera
        (99.97, False),
    ],
)
def test_f106_r1_borde_de_dos_centimos(importe, esperado):
    # 10 × 10 = 100,00
    assert cuadra_linea(10, 10, None, importe) is esperado


def test_f106_r1_tolerancia_explicita():
    assert cuadra_linea(10, 10, None, 100.5, tolerancia=1.0) is True
    assert cuadra_linea(10, 10, None, 100.02, tolerancia=0.0) is False


@pytest.mark.parametrize(
    ("cantidad", "precio", "importe"),
    [
        (None, 10, 100),
        (10, None, 100),
        (10, 10, None),
    ],
)
def test_f106_r1_no_comparable_con_nulos(cantidad, precio, importe):
    assert cuadra_linea(cantidad, precio, None, importe) is None


@pytest.mark.parametrize(
    ("cantidad", "precio", "importe"),
    [
        ("diez", 10, 100),
        (10, "x", 100),
        (10, 10, "cien"),
        (math.nan, 10, 100),
        (10, math.inf, 100),
        (10, 10, math.nan),
        (10, 10, -math.inf),
        (object(), 10, 100),
    ],
)
def test_f106_r1_ilegible_es_no_comparable_y_nunca_lanza(cantidad, precio, importe):
    assert cuadra_linea(cantidad, precio, None, importe) is None


def test_f106_r1_descuento_invalido_no_descuenta():
    # Como importe_de_linea: un dto absurdo se ignora (factor 1).
    assert cuadra_linea(10, 10, 150, 100) is True
    assert cuadra_linea(10, 10, "x", 100) is True
    assert cuadra_linea(10, 10, 150, 50) is False


def test_f106_r1_descuento_del_cien_por_cien_importe_cero():
    assert cuadra_linea(10, 10, 100, 0) is True
    assert cuadra_linea(10, 10, 100, 5) is False


def test_f106_r1_negativos_cuadran_con_signo():
    assert cuadra_linea(-2, 10, None, -20) is True
    assert cuadra_linea(-2, 10, None, 20) is False


def test_f106_r1_numeros_como_texto():
    assert cuadra_linea("10", "11.2", "7", "104.16") is True


# --------------------------------------------------------------------- R2
def test_f106_r2_sin_vincular_usa_la_cantidad_del_albaran():
    # La fila de producción: 104,16 / 48 = 2,17.
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=48, cantidad_convertida=99, importe=104.16,
    ) == (48.0, 2.17)


def test_f106_r2_vinculada_usa_la_convertida():
    assert linea_a_sigrid(
        vinculada=True, cantidad_albaran=48, cantidad_convertida=4, importe=100,
    ) == (4.0, 25.0)


def test_f106_r2_signo_del_importe_en_la_cantidad():
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=2, cantidad_convertida=None, importe=-20,
    ) == (-2.0, 10.0)
    # La cantidad negativa con importe positivo va en positivo.
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=-2, cantidad_convertida=None, importe=20,
    ) == (2.0, 10.0)


def test_f106_r2_importe_cero_cantidad_en_positivo():
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=2, cantidad_convertida=None, importe=0,
    ) == (2.0, 0.0)
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=-2, cantidad_convertida=None, importe=-0.0,
    ) == (2.0, 0.0)


def test_f106_r2_texto_ilegible_no_da_linea():
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran="x", cantidad_convertida=None, importe=10,
    ) is None
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=2, cantidad_convertida=None, importe="x",
    ) is None
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=math.inf, cantidad_convertida=None, importe=10,
    ) is None


def test_f106_r2_seis_decimales():
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=3, cantidad_convertida=None, importe=10,
    ) == (3.0, 3.333333)


@pytest.mark.parametrize("cantidad", [None, 0, 0.0, 1e-12, 1e-9, -1e-9])  # 1e-9: el borde
def test_f106_r2_cantidad_nula_o_cero_no_da_linea(cantidad):
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=cantidad, cantidad_convertida=5, importe=10,
    ) is None
    assert linea_a_sigrid(
        vinculada=True, cantidad_albaran=5, cantidad_convertida=cantidad, importe=10,
    ) is None


@pytest.mark.parametrize("importe", [None, math.nan, math.inf])
def test_f106_r2_importe_nulo_o_ilegible_no_da_linea(importe):
    assert linea_a_sigrid(
        vinculada=False, cantidad_albaran=5, cantidad_convertida=None, importe=importe,
    ) is None


def test_f106_r2_es_la_unica_definicion_en_comun():
    assert alta_sigrid.linea_a_sigrid is linea_a_sigrid


# --------------------------------------------------------------------- R3
def test_f106_r3_cantidad_mueve_el_importe():
    # CECOIS: 10 → 48 con 11,20 −7 % ⇒ 499,97
    assert recalcular_fila(
        cantidad=48, precio=11.2, descuento=7, importe=104.16, editados={"cantidad"},
    ) == (11.2, 499.97)


@pytest.mark.parametrize("campo", ["precio_unitario", "descuento"])
def test_f106_r3_precio_o_dto_mueven_el_importe(campo):
    assert recalcular_fila(
        cantidad=10, precio=12, descuento=10, importe=104.16, editados={campo},
    ) == (12, 108.0)


def test_f106_r3_importe_mueve_el_precio_y_el_dto_se_queda():
    # 104,16 / (48 × 0,93) = 2,333333
    assert recalcular_fila(
        cantidad=48, precio=11.2, descuento=7, importe=104.16, editados={"importe"},
    ) == (2.333333, 104.16)


def test_f106_r3_importe_con_cantidad_tambien_despeja_el_precio():
    assert recalcular_fila(
        cantidad=48, precio=11.2, descuento=7, importe=104.16,
        editados={"importe", "cantidad", "descuento"},
    ) == (2.333333, 104.16)


def test_f106_r3_importe_a_dos_decimales():
    precio, importe = recalcular_fila(
        cantidad=3, precio=1, descuento=None, importe=10.004, editados={"importe"},
    )
    assert importe == 10.0
    assert precio == 3.333333


def test_f106_r3_despeje_es_el_de_unitario_despejado():
    precio, _ = recalcular_fila(
        cantidad=7, precio=1, descuento=3, importe=100, editados={"importe"},
    )
    assert precio == importes.unitario_despejado(importe=100, cantidad=7, descuento_pct=3)


def test_f106_r3_importe_y_precio_a_la_vez_es_error():
    with pytest.raises(PrecioEImporte) as exc:
        recalcular_fila(
            cantidad=10, precio=11, descuento=None, importe=100,
            editados={"importe", "precio_unitario"},
        )
    assert str(exc.value) == "Cambia el precio o el importe, no los dos"


@pytest.mark.parametrize(
    ("cantidad", "descuento"),
    [(0, None), (None, None), (10, 100), (0.0, 7)],
)
def test_f106_r3_importe_cero_sin_divisor_conserva_el_precio(cantidad, descuento):
    assert recalcular_fila(
        cantidad=cantidad, precio=11.2, descuento=descuento, importe=0,
        editados={"importe"},
    ) == (11.2, 0.0)


@pytest.mark.parametrize(
    ("cantidad", "descuento"),
    [(0, None), (None, None), (10, 100)],
)
def test_f106_r3_importe_no_cero_sin_divisor_no_se_despeja(cantidad, descuento):
    with pytest.raises(NoDespejable) as exc:
        recalcular_fila(
            cantidad=cantidad, precio=11.2, descuento=descuento, importe=50,
            editados={"importe"},
        )
    assert str(exc.value) == (
        "No se puede calcular el precio con cantidad 0 o descuento del 100 %: "
        "cambia la cantidad, el descuento o el precio"
    )


def test_f106_r3_importe_nulo_no_se_despeja():
    with pytest.raises(NoDespejable):
        recalcular_fila(
            cantidad=10, precio=11.2, descuento=None, importe=None, editados={"importe"},
        )


def test_f106_r3_cantidad_cero_da_importe_cero():
    assert recalcular_fila(
        cantidad=0, precio=11.2, descuento=None, importe=50, editados={"cantidad"},
    ) == (11.2, 0.0)


def test_f106_r3_sin_precio_el_importe_no_se_inventa():
    assert recalcular_fila(
        cantidad=10, precio=None, descuento=None, importe=50, editados={"cantidad"},
    ) == (None, None)


def test_f106_r3_nada_que_mueva_el_importe_lo_deja_igual():
    assert recalcular_fila(
        cantidad=48, precio=11.2, descuento=7, importe=104.16,
        editados={"codigo_partida", "descripcion"},
    ) == (11.2, 104.16)
    assert recalcular_fila(
        cantidad=48, precio=11.2, descuento=7, importe=104.16, editados=set(),
    ) == (11.2, 104.16)


def test_f106_r3_tras_recalcular_la_fila_cuadra():
    for editados in ({"cantidad"}, {"importe"}):
        precio, importe = recalcular_fila(
            cantidad=48, precio=11.2, descuento=7, importe=104.16, editados=editados,
        )
        assert cuadra_linea(48, precio, 7, importe) is True


def test_f106_r3_errores_son_value_error():
    assert issubclass(NoDespejable, ValueError)
    assert issubclass(PrecioEImporte, ValueError)


# ------------------------------------------------------------------ versión
def test_f106_t2_version_0100():
    from pathlib import Path

    import ruesma_comun

    assert ruesma_comun.__version__ == "0.10.0"
    pyproject = (Path(ruesma_comun.__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.10.0"' in pyproject
