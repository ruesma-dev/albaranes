# tests/test_f078_linea_valorada.py
"""F-078 · R1–R3 · ``ruesma_comun.linea_valorada.fila_a_guardar``.

Tabla de casos: Contrato / Nueva × campo lleno / vacío × factor 1 / nulo / ≠ 1
× blanca sí / no, con las filas del caso (385, Nueva con blanca; 386, manual
sin blanca) y la Nueva de ferretería cuya derivada dice «MATERIAL DE
FERRETERIA» (P1 = (b): se guarda el concepto del papel). Puro.
"""
from __future__ import annotations

import itertools

import pytest

from ruesma_comun.linea_valorada import (
    CamposFila,
    LineaDeLaFila,
    cambios_a_guardar,
    concepto_a_guardar,
    fila_a_guardar,
    sin_conversion,
)

CONTRATO = LineaDeLaFila(
    es_contrato=True, descripcion="PUERTA CORTAFUEGOS EI2-60", unidad="UD",
    precio_unitario=115.0,
)
FERRETERIA = LineaDeLaFila(
    es_contrato=False, descripcion="MATERIAL DE FERRETERIA", unidad="UD",
    precio_unitario=3.2,
)
CARGA = LineaDeLaFila(
    es_contrato=False, descripcion="CARGA INCOMPLETA", unidad="M3", precio_unitario=12.5,
)


def _fila(**campos) -> CamposFila:
    base = {
        "descripcion_linea": None, "unidad_contrato": None, "unidad_albaran": None,
        "precio_unitario_final": None, "cantidad_albaran": 3.0,
        "cantidad_convertida": None, "factor_conversion": 1.0,
    }
    base.update(campos)
    return CamposFila(**base)


# ------------------------------------------------------------------ #
# R1 · concepto
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("descripcion", "linea", "blanca", "esperado"),
    [
        # Contrato: la de la fila; si vacía, la de su línea; si no, el papel (P9).
        ("MI TEXTO", CONTRATO, "PUERTA EI2-60", "MI TEXTO"),
        (None, CONTRATO, "PUERTA EI2-60", "PUERTA CORTAFUEGOS EI2-60"),
        ("   ", CONTRATO, None, "PUERTA CORTAFUEGOS EI2-60"),
        (None, LineaDeLaFila(es_contrato=True), "PUERTA EI2-60", "PUERTA EI2-60"),
        (None, LineaDeLaFila(es_contrato=True, descripcion=" "), None, None),
        # Nueva CON blanca (P1 = (b)): la de la fila; si vacía, el papel.
        (None, FERRETERIA, "DISCO C/ACERO 230 BOSCH", "DISCO C/ACERO 230 BOSCH"),
        ("SIKAFLEX 11 FC", FERRETERIA, "DISCO C/ACERO 230 BOSCH", "SIKAFLEX 11 FC"),
        # Nueva SIN blanca (manual, reparto, sintética): su derivada; si no, la fila.
        (None, CARGA, None, "CARGA INCOMPLETA"),
        ("OTRA", CARGA, None, "CARGA INCOMPLETA"),
        ("OTRA", LineaDeLaFila(es_contrato=False), None, "OTRA"),
        (None, LineaDeLaFila(es_contrato=False, descripcion="  "), None, None),
        # Una blanca sin concepto no cuenta como blanca: su derivada, luego la fila.
        ("OTRA", CARGA, "   ", "CARGA INCOMPLETA"),
        # Sin línea: la de la fila; si no, el papel.
        (None, None, "PORTES", "PORTES"),
        ("PORTES URGENTES", None, "PORTES", "PORTES URGENTES"),
        (None, None, None, None),
        # Recortados.
        ("  CON ESPACIOS  ", CONTRATO, None, "CON ESPACIOS"),
        (None, FERRETERIA, "  Mortero M-5 ", "Mortero M-5"),
        (None, LineaDeLaFila(es_contrato=False, descripcion=" — AÑO 2026 "), None,
         "— AÑO 2026"),
    ],
)
def test_f078_r1_concepto(descripcion, linea, blanca, esperado):
    assert concepto_a_guardar(descripcion, linea, blanca) == esperado
    assert fila_a_guardar(_fila(descripcion_linea=descripcion), linea, blanca)\
        .descripcion_linea == esperado


# ------------------------------------------------------------------ #
# R1 · unidad y precio
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("fila_unidad", "linea", "esperada"),
    [
        ("M3", CONTRATO, "UD"),             # la de su línea manda
        ("M3", LineaDeLaFila(es_contrato=False, unidad=" "), "M3"),
        (" m3 ", None, "m3"),
        (None, LineaDeLaFila(es_contrato=True), None),
        (None, CARGA, "M3"),
    ],
)
def test_f078_r1_unidad(fila_unidad, linea, esperada):
    assert fila_a_guardar(_fila(unidad_contrato=fila_unidad), linea, None)\
        .unidad_contrato == esperada


@pytest.mark.parametrize(
    ("fila_precio", "linea", "esperado"),
    [
        (100.6, CONTRATO, 100.6),            # el de la fila manda
        (0.0, CONTRATO, 0.0),                # 0 es lleno
        (None, CONTRATO, 115.0),
        (None, LineaDeLaFila(es_contrato=False), None),
        (None, None, None),
        (7.5, None, 7.5),
    ],
)
def test_f078_r1_precio(fila_precio, linea, esperado):
    assert fila_a_guardar(_fila(precio_unitario_final=fila_precio), linea, None)\
        .precio_unitario_final == esperado


# ------------------------------------------------------------------ #
# R1, R3 · sin conversión / con conversión
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("factor", "esperado"),
    [(1.0, True), (1, True), (1.0 + 1e-10, True), (1.0 - 1e-10, True),
     (1.00001, False), (0.99999, False), (None, False), (0.0, False), (1000.0, False)],
)
def test_f078_r1_sin_conversion(factor, esperado):
    assert sin_conversion(factor) is esperado


def test_f078_r1_sin_conversion_completa_unidad_albaran_y_convertida():
    resultado = fila_a_guardar(
        _fila(unidad_contrato="m3", cantidad_albaran=3.0, cantidad_convertida=None),
        LineaDeLaFila(es_contrato=False, descripcion="MORTERO M-5", unidad="m3"),
        "Mortero M-5",
    )
    assert (resultado.unidad_albaran, resultado.cantidad_convertida) == ("m3", 3.0)


def test_f078_r1_sin_conversion_conserva_lo_que_ya_hay():
    resultado = fila_a_guardar(
        _fila(unidad_contrato="UD", unidad_albaran=" T ", cantidad_albaran=3.0,
              cantidad_convertida=2.0),
        CONTRATO, None,
    )
    assert (resultado.unidad_albaran, resultado.cantidad_convertida) == ("T", 2.0)


@pytest.mark.parametrize("factor", [None, 1000.0, 0.001, 1.00001])
def test_f078_r3_con_conversion_no_toca_unidad_albaran_ni_convertida(factor):
    for unidad_albaran, convertida in ((None, None), (" t ", None), ("t", 3000.0)):
        fila = _fila(unidad_albaran=unidad_albaran, cantidad_convertida=convertida,
                     factor_conversion=factor, unidad_contrato="kg")
        resultado = fila_a_guardar(fila, CONTRATO, "BLANCA")
        assert resultado.unidad_albaran == unidad_albaran
        assert resultado.cantidad_convertida == convertida


def test_f078_r1_cantidad_albaran_y_factor_salen_tal_cual():
    fila = _fila(cantidad_albaran=8.0, cantidad_convertida=None, factor_conversion=1.0)
    resultado = fila_a_guardar(fila, CONTRATO, None)
    assert (resultado.cantidad_albaran, resultado.factor_conversion) == (8.0, 1.0)


# ------------------------------------------------------------------ #
# Las filas del caso (progress/spec_F-078.md §1)
# ------------------------------------------------------------------ #
def test_f078_r1_fila_385_nueva_con_blanca():
    """from_albaran Nueva (derivada 238 «MORTERO M-5»), todo vacío, Q 3, factor 1."""
    fila = _fila(unidad_contrato="m3", precio_unitario_final=100.6)
    derivada = LineaDeLaFila(es_contrato=False, descripcion="MORTERO M-5", unidad="m3",
                             precio_unitario=100.6)
    assert fila_a_guardar(fila, derivada, "Mortero M-5") == CamposFila(
        descripcion_linea="Mortero M-5", unidad_contrato="m3", unidad_albaran="m3",
        precio_unitario_final=100.6, cantidad_albaran=3.0, cantidad_convertida=3.0,
        factor_conversion=1.0,
    )


def test_f078_r1_fila_386_manual_sin_blanca():
    fila = _fila(unidad_contrato="M3", precio_unitario_final=12.5, cantidad_albaran=1.0,
                 cantidad_convertida=1.0)
    assert fila_a_guardar(fila, CARGA, None) == CamposFila(
        descripcion_linea="CARGA INCOMPLETA", unidad_contrato="M3", unidad_albaran="M3",
        precio_unitario_final=12.5, cantidad_albaran=1.0, cantidad_convertida=1.0,
        factor_conversion=1.0,
    )


# ------------------------------------------------------------------ #
# R2 · nunca vacía un campo lleno (salvo las excepciones de R2)
# ------------------------------------------------------------------ #
_LINEAS = (
    None, CONTRATO, FERRETERIA, LineaDeLaFila(es_contrato=True),
    LineaDeLaFila(es_contrato=False), LineaDeLaFila(es_contrato=False, unidad="  "),
)


@pytest.mark.parametrize(
    ("linea", "blanca", "factor"),
    list(itertools.product(_LINEAS, (None, "", "PAPEL"), (1.0, None, 1000.0))),
)
def test_f078_r2_no_vacia_lo_que_la_fila_tiene(linea, blanca, factor):
    llena = CamposFila(
        descripcion_linea="DESC", unidad_contrato="UNI", unidad_albaran="UA",
        precio_unitario_final=1.5, cantidad_albaran=2.0, cantidad_convertida=2.0,
        factor_conversion=factor,
    )
    resultado = fila_a_guardar(llena, linea, blanca)
    for campo in ("descripcion_linea", "unidad_contrato", "unidad_albaran",
                  "precio_unitario_final", "cantidad_albaran", "cantidad_convertida"):
        assert getattr(resultado, campo) not in (None, ""), campo


# ------------------------------------------------------------------ #
# cambios_a_guardar · solo lo que cambia; aplicada dos veces, nada
# ------------------------------------------------------------------ #
def test_f078_r1_cambios_a_guardar_solo_lo_que_cambia_e_idempotente():
    fila = _fila(unidad_contrato="m3", precio_unitario_final=100.6)
    derivada = LineaDeLaFila(es_contrato=False, descripcion="MORTERO M-5", unidad="m3")
    cambios = cambios_a_guardar(fila, derivada, "Mortero M-5")
    assert cambios == {
        "descripcion_linea": "Mortero M-5", "unidad_albaran": "m3",
        "cantidad_convertida": 3.0,
    }
    guardada = CamposFila(**{**fila.__dict__, **cambios})
    assert cambios_a_guardar(guardada, derivada, "Mortero M-5") == {}


def test_f078_r1_cambios_a_guardar_recorta_textos():
    fila = _fila(descripcion_linea=" X ", unidad_contrato=" UD ", unidad_albaran="UD",
                 precio_unitario_final=1.0, cantidad_convertida=3.0)
    assert cambios_a_guardar(fila, None, None) == {
        "descripcion_linea": "X", "unidad_contrato": "UD",
    }
