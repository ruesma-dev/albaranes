# tests/test_f065_partes.py
"""F-065 · tests de contrato en sv9 (sv9 no cambia de código).

- R10 (fase 1): una fila Contrato editada en sv4 queda con
  ``cantidad_convertida`` = Q (la cantidad en la unidad del precio que ve y
  edita la ficha). sv9 la admite (sin ``cantidad_sin_convertir``) y la manda
  vinculada, con ``cantidad = Q`` y su ``ctrpro_ide``; el precio sale de
  ``importe / Q``. Las filas legadas que el PATCH viejo dejaba con la
  convertida nula son justo las que sv9 rechaza (fallo seguro).
- R36 (fase 3): las partes de una fila dividida en sv4 (``reparto``, sin
  blanca) pasan por el validador real: con su partida o en almacén, vinculadas
  a su ``ctrpro_ide`` (N partes al mismo ``ctrpro``, N líneas); con otra
  partida, Nueva sin vincular con producto genérico y su descripción; cada una
  en su unidad y la familia suma el importe original.

Puro: ni red ni BBDD.
"""
from __future__ import annotations

import pytest
from domain.models.alta_models import Motivo, PeticionAlbaran
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, HOY, datos, sin_vincular, vinculada


def _linea_unica(linea):
    peticion = validar_y_construir(datos(linea), CONFIG, HOY)
    assert isinstance(peticion, PeticionAlbaran), f"no admitida: {peticion!r}"
    (enviada,) = peticion.lineas
    return enviada


@pytest.mark.parametrize(
    ("cantidad_albaran", "cantidad_convertida", "importe", "q", "precio"),
    [
        # (b) sin conversión: la administrativa deja 7 puertas de 8 a 115 €.
        (7.0, 7.0, 805.0, 7.0, 115.0),
        # (c) contenedores: 6 m³ declarados, 2 contenedores a 120 €.
        (6.0, 2.0, 240.0, 2.0, 120.0),
        # (a) reproducible t → kg: 3 t = 3000 kg a 0,05 €/kg.
        (3.0, 3000.0, 150.0, 3000.0, 0.05),
    ],
    ids=["sin_conversion", "contenedores", "toneladas_a_kg"],
)
def test_f065_r10_fila_contrato_editada_se_admite_con_cantidad_q(
    cantidad_albaran, cantidad_convertida, importe, q, precio,
):
    enviada = _linea_unica(vinculada(
        11, cantidad_albaran=cantidad_albaran, cantidad_convertida=cantidad_convertida,
        importe_calculado=importe,
    ))

    assert enviada.ctrpro_ide == 700101
    assert enviada.cantidad == pytest.approx(q)
    assert enviada.precio == pytest.approx(precio)
    assert enviada.producto is None  # vinculada: el producto es el de su línea


def test_f065_r10_la_fila_legada_sin_convertida_es_la_que_se_rechaza():
    """Lo que el PATCH viejo dejaba (convertida nula): ``no_admitido``."""
    resultado = validar_y_construir(
        datos(vinculada(11, cantidad_albaran=7.0, cantidad_convertida=None,
                        importe_calculado=805.0)),
        CONFIG, HOY,
    )

    assert resultado == [Motivo("cantidad_sin_convertir", "", "11")]


# ------------------------------------------------------------------ #
# CR1 y H1 (pasada 2 de la fase 2): la descripción de las Nuevas
# ------------------------------------------------------------------ #
def test_f065_cr1_traida_pasada_a_nueva_se_admite_sin_vincular_con_su_descripcion():
    """Como la deja sv4: fila traída del contrato (sin blanca) con otra partida ⇒
    Nueva (derivada propia, sin línea de contrato) y su descripción en la
    valoración."""
    enviada = _linea_unica(sin_vincular(
        77, merge_line_id=None, line_index=None, descripcion_merge=None,
        descripcion_linea="PUERTA CORTAFUEGOS EI2-120", derived_contrato_line_id=602,
        codigo_partida_final="09.09", cantidad_albaran=5.0, cantidad_convertida=5.0,
        importe_calculado=575.0,
    ))

    assert enviada.ctrpro_ide is None
    assert enviada.descripcion == "PUERTA CORTAFUEGOS EI2-120"
    assert enviada.partida == "09.09"
    assert (enviada.cantidad, enviada.precio) == (5.0, 115.0)
    assert enviada.producto == "MA9999"


def test_f065_cr1_sin_descripcion_ni_blanca_no_se_admite():
    """Lo que dejaba sv4 antes de la pasada 2: el albarán entero, ``no_admitido``."""
    resultado = validar_y_construir(datos(sin_vincular(
        77, merge_line_id=None, line_index=None, descripcion_merge=None,
        descripcion_linea=None, derived_contrato_line_id=602,
    )), CONFIG, HOY)

    assert resultado == [Motivo("falta_descripcion", "", "77")]


def test_f065_h1_la_descripcion_editada_manda_sobre_el_concepto_leido():
    enviada = _linea_unica(sin_vincular(
        12, descripcion_linea="PORTES URGENTES", descripcion_merge="PORTES",
    ))

    assert enviada.descripcion == "PORTES URGENTES"


def test_f065_h1_sin_descripcion_editada_va_el_concepto_leido():
    enviada = _linea_unica(sin_vincular(12, descripcion_linea=None, descripcion_merge="PORTES"))

    assert enviada.descripcion == "PORTES"


# ------------------------------------------------------------------ #
# R36 (fase 3): las partes de un reparto, tal como las deja sv4
# ------------------------------------------------------------------ #
def _reparto_18_en_6_7_5():
    """La fila 12 (Contrato, 18 m³ a 115 €: 2070 €) dividida en sv4 en 6 con su
    partida (la original), 7 con otra (Nueva: derivada propia, sin línea de
    contrato) y 5 a almacén (Contrato, partida vacía). Las partes no tienen
    blanca: llevan la descripción en la valoración (CR1) y la convertida = qk."""
    original = vinculada(12, cantidad_albaran=6.0, cantidad_convertida=6.0,
                         importe_calculado=690.0)
    nueva = sin_vincular(
        31, merge_line_id=None, line_index=None, descripcion_merge=None,
        descripcion_linea="HA-25/B/20/IIa", derived_contrato_line_id=902,
        codigo_partida_final="03.02.02", unidad_albaran="M3",
        cantidad_albaran=7.0, cantidad_convertida=7.0, importe_calculado=805.0,
    )
    almacen = vinculada(
        32, merge_line_id=None, line_index=None, descripcion_merge=None,
        descripcion_linea="HA-25/B/20/IIa", codigo_partida_final=None,
        cantidad_albaran=5.0, cantidad_convertida=5.0, importe_calculado=575.0,
    )
    return original, nueva, almacen


def test_f065_r36_las_partes_pasan_el_validador_real():
    peticion = validar_y_construir(datos(*_reparto_18_en_6_7_5()), CONFIG, HOY)

    assert isinstance(peticion, PeticionAlbaran), f"no admitida: {peticion!r}"
    original, nueva, almacen = peticion.lineas
    # 6 y 5: vinculadas al mismo ctrpro, dos líneas (F-009 R12).
    assert (original.ctrpro_ide, original.cantidad, original.partida) == (
        700101, 6.0, "03.02.01")
    assert (almacen.ctrpro_ide, almacen.cantidad, almacen.partida) == (700101, 5.0, None)
    # 7: Nueva, sin vincular, producto genérico y su descripción.
    assert (nueva.ctrpro_ide, nueva.producto, nueva.descripcion, nueva.unidad) == (
        None, "MA9999", "HA-25/B/20/IIa", "M3")
    assert (nueva.cantidad, nueva.partida) == (7.0, "03.02.02")
    assert [linea.precio for linea in peticion.lineas] == [115.0, 115.0, 115.0]
    # La familia suma el importe original.
    assert sum(linea.cantidad * linea.precio for linea in peticion.lineas) == 2070.0


def test_f065_r36_las_partes_van_detras_de_las_lineas_del_albaran():
    original, nueva, almacen = _reparto_18_en_6_7_5()
    otra = vinculada(13, cantidad_albaran=1.0, cantidad_convertida=1.0,
                     importe_calculado=115.0)

    peticion = validar_y_construir(datos(almacen, nueva, otra, original), CONFIG, HOY)

    assert [linea.referencia_linea for linea in peticion.lineas] == [
        original.referencia_linea, otra.referencia_linea,
        nueva.referencia_linea, almacen.referencia_linea]


def test_f065_r36_con_conversion_cada_parte_en_su_unidad():
    """3 t leídas = 3000 kg a 0,05 €/kg (150 €) en 1000 kg con su partida y
    2000 kg con otra: la vinculada va en kg (la convertida) y la Nueva en t (la
    del albarán, ``ca0 × qk / Q`` = 2), cada una con su precio."""
    original = vinculada(12, cantidad_albaran=1.0, cantidad_convertida=1000.0,
                         unidad_albaran="T", importe_calculado=50.0)
    nueva = sin_vincular(
        31, merge_line_id=None, line_index=None, descripcion_merge=None,
        descripcion_linea="ACERO B500S", derived_contrato_line_id=902,
        unidad_albaran="T", cantidad_albaran=2.0, cantidad_convertida=2000.0,
        importe_calculado=100.0,
    )

    peticion = validar_y_construir(datos(original, nueva), CONFIG, HOY)

    vinc, sin = peticion.lineas
    assert (vinc.cantidad, vinc.precio) == (1000.0, 0.05)
    assert (sin.cantidad, sin.unidad, sin.precio) == (2.0, "T", 50.0)


def test_f065_r36_el_redondeo_lo_absorbe_la_ultima_parte():
    """100 € en tres partes de 1: 33,33 + 33,33 + 33,34; sv9 las admite y el
    total es el original."""
    partes = [
        vinculada(12, cantidad_albaran=1.0, cantidad_convertida=1.0, importe_calculado=33.33),
        vinculada(41, merge_line_id=None, line_index=None, cantidad_albaran=1.0,
                  cantidad_convertida=1.0, importe_calculado=33.33),
        vinculada(42, merge_line_id=None, line_index=None, cantidad_albaran=1.0,
                  cantidad_convertida=1.0, importe_calculado=33.34),
    ]

    peticion = validar_y_construir(datos(*partes), CONFIG, HOY)

    assert [linea.precio for linea in peticion.lineas] == [33.33, 33.33, 33.34]
    assert round(sum(linea.precio for linea in peticion.lineas), 2) == 100.0
