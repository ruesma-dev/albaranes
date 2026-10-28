# tests/test_f106_validador.py
"""F-106 R17, R32 b: sv9 no da de alta una línea que no cuadra.

La fila de producción de AC26/30435 (48 × 11,20 −7 % con importe 104,16
``declared_albaran``) se dio de alta como 48 × 2,17 sin aviso. Con F-106 sv9 lee
además P y d, deja el alta ``no_admitido`` con ``linea_no_cuadra`` y no llama a
sigrid-api. Sin ese motivo, la petición es la de hoy (``linea_a_sigrid`` de comun).
"""
from __future__ import annotations

from dataclasses import replace

from domain.models.alta_models import LineaAlta, Motivo, PeticionAlbaran
from domain.services.validador_alta import validar_y_construir
from infrastructure.database.sql_alta_repository import SQL_LINEAS, _linea_de_fila
from tests.f053_datos import CONFIG, HOY, USU, datos, sin_vincular, vinculada

DETALLE_CECOIS = "48 × 11,2 × (1 − 7 %) = 499,97 ≠ 104,16"


def _cecois(**cambios) -> LineaAlta:
    """La fila de producción: sin vincular, Q 48, P 11,2, d 7, I 104,16."""
    base = sin_vincular(
        7, cantidad_albaran=48.0, cantidad_convertida=48.0, importe_calculado=104.16,
        precio_unitario_final=11.2, descuento_albaran_aplicado=7.0,
    )
    return replace(base, **cambios)


def _peticion(*lineas: LineaAlta) -> PeticionAlbaran:
    resultado = validar_y_construir(datos(*lineas), CONFIG, HOY, USU)
    assert isinstance(resultado, PeticionAlbaran), resultado
    return resultado


# -------------------------------------------------------------------- R17
def test_f106_r17_la_fila_de_produccion_no_se_da_de_alta():
    resultado = validar_y_construir(datos(_cecois()), CONFIG, HOY, USU)
    assert resultado == [Motivo("linea_no_cuadra", DETALLE_CECOIS, "7")]


def test_f106_r17_linea_no_cuadra_es_de_no_admitido():
    from domain.services.validador_alta import MOTIVOS_REVISAR_LOCAL

    assert "linea_no_cuadra" not in MOTIVOS_REVISAR_LOCAL


def test_f106_r17_una_vinculada_que_no_cuadra_tampoco():
    linea = vinculada(3, precio_unitario_final=70.0, descuento_albaran_aplicado=None)
    # 6 × 70 = 420,00 ≠ 410,40
    assert validar_y_construir(datos(linea), CONFIG, HOY, USU) == [
        Motivo("linea_no_cuadra", "6 × 70 = 420,00 ≠ 410,40", "3"),
    ]


def test_f106_r17_cuadra_con_la_cantidad_convertida():
    # Sin vincular con convertida distinta: P es el de la unidad de la convertida.
    linea = sin_vincular(
        4, cantidad_albaran=1000.0, cantidad_convertida=2.0, importe_calculado=20.0,
        precio_unitario_final=10.0,
    )
    assert isinstance(validar_y_construir(datos(linea), CONFIG, HOY, USU), PeticionAlbaran)


def test_f106_r17_cuadra_dentro_de_dos_centimos():
    linea = _cecois(importe_calculado=499.99)
    peticion = _peticion(linea)
    assert peticion.lineas[0].cantidad == 48.0
    assert peticion.lineas[0].precio == round(499.99 / 48, 6)


def test_f106_r17_fuera_de_dos_centimos_no():
    linea = _cecois(importe_calculado=500.0)
    resultado = validar_y_construir(datos(linea), CONFIG, HOY, USU)
    assert [m.codigo for m in resultado] == ["linea_no_cuadra"]


def test_f106_r17_sin_precio_no_es_comparable_y_va_como_hoy():
    linea = _cecois(precio_unitario_final=None)
    peticion = _peticion(linea)
    assert peticion.lineas[0].cantidad == 48.0
    assert peticion.lineas[0].precio == 2.17


def test_f106_r17_solo_las_lineas_a_registrar():
    # Importe 0: no va en la petición ni cuenta como «no cuadra».
    cero = _cecois(id=8, importe_calculado=0.0)
    buena = sin_vincular(9, precio_unitario_final=4.4)
    peticion = _peticion(cero, buena)
    assert [l.referencia_linea for l in peticion.lineas] == ["9"]


def test_f106_r17_una_mala_entre_buenas_bloquea_y_dice_cual():
    buena = sin_vincular(9, precio_unitario_final=4.4)  # 10 × 4,4 = 44
    resultado = validar_y_construir(datos(buena, _cecois()), CONFIG, HOY, USU)
    assert resultado == [Motivo("linea_no_cuadra", DETALLE_CECOIS, "7")]


def test_f106_r17_negativa_que_cuadra():
    linea = sin_vincular(
        5, cantidad_albaran=-2.0, importe_calculado=-20.0, precio_unitario_final=10.0,
    )
    peticion = _peticion(linea)
    assert (peticion.lineas[0].cantidad, peticion.lineas[0].precio) == (-2.0, 10.0)


def test_f106_r17_peticion_identica_a_la_de_hoy_sin_p_ni_d():
    # Los datos de F-053 no traen P ni d: la petición no cambia.
    hoy = _peticion(vinculada(1), sin_vincular(2))
    con_p = _peticion(
        vinculada(1, precio_unitario_final=68.4),
        sin_vincular(2, precio_unitario_final=4.4, descuento_albaran_aplicado=0.0),
    )
    assert con_p == hoy
    assert hoy.a_dict()["lineas"] == [
        {"referencia_linea": "1", "ctrpro_ide": 700101, "cantidad": 6.0,
         "precio": 68.4, "partida": "03.02.01"},
        {"referencia_linea": "2", "producto": "MA9999",
         "descripcion": "SACO CEMENTO CEM II 25 KG", "unidad": "UD",
         "cantidad": 10.0, "precio": 4.4, "partida": "03.04.02"},
    ]


def test_f106_r17_detalle_con_decimales_en_coma():
    linea = sin_vincular(
        6, cantidad_albaran=2.5, cantidad_convertida=None, importe_calculado=10.0,
        precio_unitario_final=3.125, descuento_albaran_aplicado=12.5,
    )
    # 2,5 × 3,125 × 0,875 = 6,84 ≠ 10,00
    assert validar_y_construir(datos(linea), CONFIG, HOY, USU) == [
        Motivo("linea_no_cuadra", "2,5 × 3,125 × (1 − 12,5 %) = 6,84 ≠ 10,00", "6"),
    ]


# ------------------------------------------------------- R17 · repositorio
def test_f106_r17_sql_lineas_lee_p_y_d():
    assert "lv.precio_unitario_final" in SQL_LINEAS
    assert "lv.descuento_albaran_aplicado" in SQL_LINEAS


def test_f106_r17_el_repositorio_mapea_p_y_d():
    fila = {
        "id": 7, "merge_line_id": 1007, "line_index": 7, "cantidad_albaran": 48,
        "cantidad_convertida": 48, "unidad_albaran": "UD", "importe_calculado": 104.16,
        "matched_contrato_line_id": None, "derived_contrato_line_id": 5,
        "codigo_partida_final": "01.02", "descripcion_linea": "TUBO",
        "producto_sigrid": None, "descripcion_merge": "TUBO", "contexto_linea_json": None,
        "ctrpro_ide": None, "contrato_linea": None,
        "precio_unitario_final": 11.2, "descuento_albaran_aplicado": 7,
    }
    linea = _linea_de_fila(fila)
    assert linea.precio_unitario_final == 11.2
    assert linea.descuento_albaran_aplicado == 7.0
    sin = _linea_de_fila({**fila, "precio_unitario_final": None, "descuento_albaran_aplicado": None})
    assert sin.precio_unitario_final is None
    assert sin.descuento_albaran_aplicado is None


# --------------------------------------------------------------- R32 b
def test_f106_r32b_fila_de_produccion_de_la_bbdd_a_no_admitido():
    fila = {
        "id": 7, "merge_line_id": 1007, "line_index": 7, "cantidad_albaran": 48,
        "cantidad_convertida": 48, "unidad_albaran": "UD", "importe_calculado": 104.16,
        "matched_contrato_line_id": None, "derived_contrato_line_id": 5,
        "codigo_partida_final": "01.02", "descripcion_linea": "TUBO",
        "producto_sigrid": None, "descripcion_merge": "TUBO", "contexto_linea_json": None,
        "ctrpro_ide": None, "contrato_linea": None,
        "precio_unitario_final": 11.2, "descuento_albaran_aplicado": 7,
    }
    resultado = validar_y_construir(datos(_linea_de_fila(fila)), CONFIG, HOY, USU)
    assert resultado == [Motivo("linea_no_cuadra", DETALLE_CECOIS, "7")]
