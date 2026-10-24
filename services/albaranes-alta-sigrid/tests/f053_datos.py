# tests/f053_datos.py
"""Datos de prueba de F-053 (sv9): documentos y líneas construidos a mano.

Valores ficticios, en la línea de los ejemplos del contrato (§6): obra
``0404``, contrato ``CTSU16/0206``, CIF inventado. Sin red ni BBDD.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import date

from domain.models.alta_models import CabeceraAlta, DatosAlta, LineaAlta
from domain.services.validador_alta import ConfigAlta

DOCUMENT_ID = "3f2b9c1e-0000-4000-8000-000000000002"
CONTRATO = "CTSU16/0206"
HOY = date(2026, 10, 6)
MAPEO = {"alquiler_maquinaria": "QA9999", "medios_auxiliares": "XA9999", "*": "MA9999"}
CONFIG = ConfigAlta(mapeo=MAPEO)
#: `usu` de las peticiones de prueba (v8: por documento, R47; ya no en `ConfigAlta`).
USU = "USU_ALTA"


def cabecera(**cambios) -> CabeceraAlta:
    base = CabeceraAlta(
        document_id=DOCUMENT_ID,
        obra_codigo="0404",
        proveedor_cif="B00000000",
        numero_albaran="ALB-58260",
        fecha="2026-10-03",
        valoracion_status="ok",
        contrato_codigo=CONTRATO,
        tipologia="generico",
        tipologia_mixta=False,
        sharepoint_relative_path="albaranes/2026/10/alb.pdf",
    )
    return replace(base, **cambios)


def vinculada(id_: int, **cambios) -> LineaAlta:
    base = LineaAlta(
        id=id_, merge_line_id=id_ + 1000, line_index=id_ % 100,
        cantidad_albaran=6.0, cantidad_convertida=6.0, unidad_albaran="M3",
        importe_calculado=410.4, matched_contrato_line_id=50, derived_contrato_line_id=None,
        ctrpro_ide=700101, contrato_linea=CONTRATO, codigo_partida_final="03.02.01",
        descripcion_linea="HORMIGON HA-25", descripcion_merge="HA-25/B/20/IIa",
        tipo_familia=None, producto_sigrid=None,
    )
    return replace(base, **cambios)


def sin_vincular(id_: int, **cambios) -> LineaAlta:
    base = LineaAlta(
        id=id_, merge_line_id=id_ + 1000, line_index=id_ % 100,
        cantidad_albaran=10.0, cantidad_convertida=None, unidad_albaran="UD",
        importe_calculado=44.0, matched_contrato_line_id=None, derived_contrato_line_id=None,
        ctrpro_ide=None, contrato_linea=None, codigo_partida_final="03.04.02",
        descripcion_linea="SACO CEMENTO CEM II 25 KG", descripcion_merge="CEMENTO",
        tipo_familia=None, producto_sigrid=None,
    )
    return replace(base, **cambios)


def datos(*lineas: LineaAlta, **cambios_cabecera) -> DatosAlta:
    return DatosAlta(cabecera=cabecera(**cambios_cabecera), lineas=tuple(lineas))
