# tests/test_f078_contrato_fila.py
"""F-078 · R18, R19 · tests de contrato en sv9 (sv9 no cambia de código).

Las filas del caso (``86c13097…``, ``progress/spec_F-078.md`` §1) tal como las
dejaba sv4/sv6 antes de F-078 y tal como quedan después: la regla común
``ruesma_comun.linea_valorada.fila_a_guardar`` (la que aplican sv6, sv4 y el
relleno) sobre la fila de antes. Cada fila pasa por la traducción real del
repositorio de sv9 (``_linea_de_fila``, la de ``SQL_LINEAS``) y por el validador
real (``validar_y_construir``):

- R18: la manual 386 (Nueva sin blanca) deja de salir ``falta_descripcion`` y se
  manda con la descripción, la unidad y la cantidad de la fila; la 385 (Nueva
  con blanca) se manda con su unidad, que antes faltaba.
- R19: una Nueva de sv6 creada desde una línea de contrato (derivada
  ``missing_partida`` «MATERIAL DE FERRETERIA») va a Sigrid con el concepto del
  papel, que es lo que guarda la fila (P1 = (b)).
- La vinculada con ``cantidad_convertida`` nula y factor 1 se admite (P3).

Puro: ni red ni BBDD.
"""
from __future__ import annotations

from typing import Any

import pytest
from ruesma_comun.linea_valorada import CamposFila, LineaDeLaFila, fila_a_guardar

from domain.models.alta_models import Motivo, PeticionAlbaran
from domain.services.validador_alta import validar_y_construir
from infrastructure.database.sql_alta_repository import _linea_de_fila
from tests.f053_datos import CONFIG, CONTRATO, HOY, USU, datos

_CAMPOS = (
    "descripcion_linea", "unidad_contrato", "unidad_albaran", "precio_unitario_final",
    "cantidad_albaran", "cantidad_convertida", "factor_conversion",
)


def _fila(**campos: Any) -> dict[str, Any]:
    """Una fila de ``SQL_LINEAS`` (con las columnas que decide ``fila_a_guardar``)."""
    base = {
        "id": 0, "merge_line_id": None, "line_index": None, "cantidad_albaran": None,
        "cantidad_convertida": None, "unidad_albaran": None, "unidad_contrato": None,
        "precio_unitario_final": None, "factor_conversion": 1.0, "importe_calculado": None,
        "matched_contrato_line_id": None, "derived_contrato_line_id": None,
        "codigo_partida_final": None, "descripcion_linea": None, "producto_sigrid": None,
        "descripcion_merge": None, "contexto_linea_json": None, "ctrpro_ide": None,
        "contrato_linea": None,
    }
    base.update(campos)
    return base


def _guardada(fila: dict[str, Any], linea: LineaDeLaFila | None) -> dict[str, Any]:
    """La fila tal como queda tras F-078 (sv6, sv4 o el relleno)."""
    nueva = fila_a_guardar(
        CamposFila(**{c: fila[c] for c in _CAMPOS}), linea, fila["descripcion_merge"],
    )
    return {**fila, **{c: getattr(nueva, c) for c in _CAMPOS}}


def _validar(fila: dict[str, Any]):
    return validar_y_construir(datos(_linea_de_fila(fila)), CONFIG, HOY, USU)


def _enviada(fila: dict[str, Any]):
    peticion = _validar(fila)
    assert isinstance(peticion, PeticionAlbaran), f"no admitida: {peticion!r}"
    (linea,) = peticion.lineas
    return linea


#: 386: manual, Nueva (derivada 239 «CARGA INCOMPLETA», M3), almacén, 12,50 €.
FILA_386 = _fila(
    id=386, cantidad_albaran=1.0, cantidad_convertida=1.0, unidad_contrato="M3",
    precio_unitario_final=12.5, importe_calculado=12.5, derived_contrato_line_id=239,
)
DERIVADA_239 = LineaDeLaFila(es_contrato=False, descripcion="CARGA INCOMPLETA", unidad="M3",
                             precio_unitario=12.5)

#: 385: from_albaran, Nueva (derivada 238 «MORTERO M-5»), con blanca «Mortero M-5».
FILA_385 = _fila(
    id=385, merge_line_id=7385, line_index=0, cantidad_albaran=3.0, unidad_contrato="m3",
    precio_unitario_final=100.6, importe_calculado=301.8, derived_contrato_line_id=238,
    codigo_partida_final="01.05.07", descripcion_merge="Mortero M-5",
)
DERIVADA_238 = LineaDeLaFila(es_contrato=False, descripcion="MORTERO M-5", unidad="m3",
                             precio_unitario=100.6)


# =================================================================== #
# R18 · la manual 386 y la 385 del caso
# =================================================================== #
def test_f078_r18_la_386_de_antes_es_la_que_se_rechazaba():
    assert _validar(FILA_386) == [Motivo("falta_descripcion", "", "386")]


def test_f078_r18_la_386_guardada_se_manda_con_lo_de_la_fila():
    guardada = _guardada(FILA_386, DERIVADA_239)

    enviada = _enviada(guardada)

    assert (enviada.descripcion, enviada.unidad, enviada.cantidad) == (
        "CARGA INCOMPLETA", "M3", 1.0)
    assert enviada.precio == pytest.approx(12.5)
    assert enviada.partida is None                 # almacén
    assert enviada.producto == "MA9999"            # el por defecto (R20, sin guardar)


def test_f078_r18_la_385_de_antes_iba_sin_unidad():
    assert _enviada(FILA_385).unidad is None


def test_f078_r18_la_385_guardada_se_manda_con_su_descripcion_unidad_y_cantidad():
    guardada = _guardada(FILA_385, DERIVADA_238)

    enviada = _enviada(guardada)

    assert guardada["descripcion_linea"] == "Mortero M-5"   # P1 = (b): el del papel
    assert (enviada.descripcion, enviada.unidad, enviada.cantidad) == ("Mortero M-5", "m3", 3.0)
    assert enviada.precio == pytest.approx(100.6)
    assert enviada.partida == "01.05.07"


# =================================================================== #
# R19 · la Nueva de sv6 desde una línea de contrato, con el concepto del papel
# =================================================================== #
def test_f078_r19_nueva_de_ferreteria_va_con_el_concepto_del_papel():
    fila = _fila(
        id=379, merge_line_id=7379, line_index=2, cantidad_albaran=2.0, unidad_albaran="UD",
        unidad_contrato="UD", precio_unitario_final=6.4, importe_calculado=12.8,
        derived_contrato_line_id=231, codigo_partida_final="02.01",
        descripcion_merge="DISCO C/ACERO 230 BOSCH",
    )
    derivada = LineaDeLaFila(es_contrato=False, descripcion="MATERIAL DE FERRETERIA",
                             unidad="UD", precio_unitario=6.4)

    guardada = _guardada(fila, derivada)

    assert guardada["descripcion_linea"] == "DISCO C/ACERO 230 BOSCH"
    assert _enviada(guardada).descripcion == "DISCO C/ACERO 230 BOSCH"
    # Lo que va a Sigrid no cambia: sv9 ya mandaba el concepto del papel.
    assert _enviada(fila).descripcion == "DISCO C/ACERO 230 BOSCH"


# =================================================================== #
# P3 · la vinculada con la convertida nula y factor 1
# =================================================================== #
def test_f078_vinculada_sin_convertida_y_factor_1_se_admite_tras_guardarla():
    fila = _fila(
        id=401, merge_line_id=7401, line_index=1, cantidad_albaran=6.0, unidad_contrato="UD",
        precio_unitario_final=68.4, importe_calculado=410.4, matched_contrato_line_id=50,
        ctrpro_ide=700101, contrato_linea=CONTRATO, codigo_partida_final="03.02.01",
        descripcion_merge="HA-25/B/20/IIa",
    )
    contrato = LineaDeLaFila(es_contrato=True, descripcion="HORMIGON HA-25", unidad="UD",
                             precio_unitario=68.4)

    assert _validar(fila) == [Motivo("cantidad_sin_convertir", "", "401")]

    enviada = _enviada(_guardada(fila, contrato))
    assert (enviada.ctrpro_ide, enviada.cantidad) == (700101, 6.0)
