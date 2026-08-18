# infrastructure/database/sqlalchemy_valuation_context_repository.py
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text

from domain.ports.valuation_context_repository import (
    RawAlbaranLine,
    RawContratoHeader,
    RawContratoLine,
    ValuationContextRaw,
    ValuationContextRepository,
)
from infrastructure.database.session_factory import SessionFactory

logger = logging.getLogger(__name__)


# SQL crudo: no reutilizamos los ORM del servicio 3 para no acoplar
# este microservicio a su código. Esto es una VIEW conceptual sobre
# las tablas públicas del modelo de persistencia.

_SQL_MERGE_HEADER = text(
    """
    SELECT
        id AS document_id,
        proveedor_cif AS cif_proveedor,
        proveedor_nombre AS nombre_proveedor,
        obra_codigo AS codigo_obra,
        obra_nombre AS nombre_obra,
        selected_contrato_codigo AS codigo_contrato_seleccionado
    FROM albaran_documents_merge
    WHERE id = :document_id
    """
)

# -----------------------------------------------------------------
# Tras la sub-tanda 2A, la tabla albaran_lines_merge tiene dos
# columnas nuevas:
#   - unidad_medida (VARCHAR 32) — la unidad real extraída por el OCR.
#   - contexto_linea_json (TEXT) — JSON con la familia/rol/etc.
#     (hormigón, combustible, alquiler), o NULL si la línea es
#     de producto simple.
# Las leemos aquí. El prefilter del svc5:
#   - clasifica unidad_medida en UnitCategory,
#   - deserializa contexto_linea_json a ContextoLinea.
#
# COMPATIBILIDAD: para albaranes persistidos ANTES de la sub-tanda 2A
# las dos columnas vienen NULL → unidad_categoria='unknown' y
# contexto_linea=None, que es el comportamiento previo. No rompe.
#
# -----------------------------------------------------------------
# Tanda descuento — abr 2026:
#
# Se añaden al SELECT las columnas ``descuento`` y ``precio_neto``
# de ``albaran_lines_merge``. Viajan por el envelope hasta el svc6
# donde se usan para calcular el importe valorado con descuento.
#
# -----------------------------------------------------------------
# SEMÁNTICA DE ``precio_neto`` (F-019, ago 2026) — LEER ANTES DE TOCAR
# -----------------------------------------------------------------
# ``precio_neto`` de ``albaran_lines_merge`` es el **IMPORTE de la
# línea DESPUÉS del descuento**, NUNCA un precio unitario. En esa
# tabla conviven:
#
#   - ``precio``      → unitario BRUTO, antes de descuento.
#   - ``descuento``   → porcentaje (40 = 40 %).
#   - ``precio_neto`` → IMPORTE de la línea tras descuento
#                       (la columna "NETO" del albarán impreso).
#
# Fórmula canónica del dominio, única y sin excepciones:
#
#     importe_de_linea = cantidad × precio × (1 − descuento/100)
#
# No es una interpretación de este servicio: es la semántica que ya
# aplican TODOS los demás consumidores del campo —
#   * el prompt de IA1 (``albaranes-api/config/prompts.yaml``:
#     «si figura, léelo; si no, calcula cantidad*precio*
#     (1 - descuento/100)»),
#   * el guard de consistencia de svc3
#     (``albaran_confidence_service._is_line_net_consistent``, que
#     contrasta precio_neto contra cantidad × precio × (1 − dto/100)),
#   * el front svc4 (``review_repository``: eff_importe =
#     line.precio_neto),
#   * los clientes de Document AI / Document Intelligence
#     (precio_neto ← Amount / LineAmount / TotalPrice).
# El único que la contradecía era este SELECT.
#
# ERRATA CORREGIDA (F-019). El comentario «FIX (jun 2026)» que vivía
# aquí afirmaba que ``precio_neto`` era el "precio unitario NETO" y,
# en consecuencia, el SELECT multiplicaba por la cantidad un valor
# que YA era el importe. Medido en la prueba local del 2026-08-18
# (``progress/prueba_local_feymaco_20260818.md``): el albarán Feymaco
# 2.137.569 (139,66 €) llegó al svc6 valorado en 6.238,14 €, y su
# primera línea —108 ud, 0,543 €/ud, 40 % dto, neto 35,19 €— viajó
# como 108 × 35,19 = 3.800,52 €. El comentario que mintió era parte
# del bug: por eso se corrige con la misma seriedad que el código.
#
# El problema que aquel FIX quiso arreglar (la línea base de hormigón
# con importe 0/vacío) NO lo causaba el alias: lo causaba que en
# hormigón ``precio_neto`` viene NULL porque el albarán no imprime
# precios. Lo resuelve la cascada del «FIX 2 (jul 2026)», que se
# conserva ENTERA.
#
# Compatibilidad: para albaranes sin columna descuento (anteriores
# al fix de svc3), la columna viene NULL → descuento=None en el
# DTO → el svc6 lo interpreta como "sin descuento" → fórmula sin
# cambios.
# -----------------------------------------------------------------
# (jul 2026) Cabecera del albarán: fecha y número para el contexto de
# valoración. La FECHA es imprescindible para los incrementos por año
# (M1): el prompt de IA3 referenciaba context.meta.fecha_albaran pero
# el campo nunca se enviaba, así que la IA no podía computarlos.
_SQL_DOC_HEADER = text(
    """
    SELECT fecha, numero_albaran
    FROM albaran_documents_merge
    WHERE id = :document_id
    """
)

_SQL_ALBARAN_LINES = text(
    """
    SELECT
        id                  AS merge_line_id,
        line_index          AS line_index,
        codigo              AS codigo,
        concepto            AS descripcion,
        unidad_medida       AS unidad_medida,
        cantidad            AS cantidad,
        precio              AS precio_unitario_albaran,
        -- importe_albaran = IMPORTE de la línea (tras descuento), que
        -- es lo que el ImporteCalculator del svc6 espera. Cascada:
        --   1. precio_neto, si viene: YA ES el importe de la línea, se
        --      entrega TAL CUAL (F-019 R4/R7 — ver el bloque de
        --      semántica de arriba: multiplicarlo por la cantidad fue
        --      el bug que infló el albarán Feymaco 2.137.569).
        --      Se entrega aunque falte 'cantidad': el importe leído no
        --      se pierde por un campo vacío al lado.
        --   2. si no hay precio_neto, se DERIVA con la fórmula
        --      canónica cantidad × precio × (1 − dto/100)
        --      (FIX 2, jul 2026: sin esta rama, un albarán con precios
        --      pero sin descuento llegaba al svc6 con el importe mudo,
        --      porque fase 1 deja precio_neto a NULL).
        --   3. sin precio_neto ni precio → NULL, y el svc6 cae al
        --      precio del contrato (caso hormigón: el albarán no
        --      imprime precios).
        COALESCE(
            precio_neto,
            cantidad * precio * (1 - COALESCE(descuento, 0) / 100.0)
        ) AS importe_albaran,
        codigo_imputacion   AS codigo_partida_albaran,
        contexto_linea_json AS contexto_linea_json,
        descuento           AS descuento_albaran,
        precio_neto         AS precio_neto_albaran
    FROM albaran_lines_merge
    WHERE document_id = :document_id
    ORDER BY line_index
    """
)


_SQL_CONTRATO_HEADER = text(
    """
    SELECT
        id,
        codigo_contrato,
        nombre_contrato,
        cif_proveedor,
        nombre_proveedor,
        codigo_obra,
        nombre_obra,
        pdf_sharepoint_relative_path,
        pdf_sharepoint_web_url,
        md_sharepoint_relative_path
    FROM albaran_contratos_merge
    WHERE codigo_contrato = :codigo_contrato
    ORDER BY id DESC
    LIMIT 1
    """
)

_SQL_CONTRATO_LINES = text(
    """
    SELECT
        cl.id                AS contrato_line_id,
        cl.codigo_contrato   AS codigo_contrato,
        cl.codigo_producto   AS codigo_producto,
        cl.descripcion_linea AS descripcion,
        cl.unidad_medida     AS unidad_medida,
        cl.precio_unitario   AS precio_unitario,
        cl.codigo_partida    AS codigo_partida
    FROM albaran_contrato_lines_merge cl
    WHERE cl.contrato_id = :contrato_id
    ORDER BY cl.linea NULLS LAST, cl.id
    """
)


class SqlAlchemyValuationContextRepository(ValuationContextRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    def load_context(
        self,
        *,
        document_id: str,
        codigo_contrato_override: str | None = None,
    ) -> ValuationContextRaw:
        with self._session_factory.create_session() as session:
            header_row = session.execute(
                _SQL_MERGE_HEADER,
                {"document_id": document_id},
            ).mappings().first()
            if header_row is None:
                raise KeyError(
                    f"Documento merge no encontrado: {document_id}"
                )

            codigo_contrato = (
                codigo_contrato_override
                or header_row.get("codigo_contrato_seleccionado")
            )

            albaran_rows = session.execute(
                _SQL_ALBARAN_LINES,
                {"document_id": document_id},
            ).mappings().all()

            lineas_albaran = [
                self._build_albaran_line(row) for row in albaran_rows
            ]

            if not codigo_contrato:
                logger.warning(
                    "document_id=%s sin contrato seleccionado. "
                    "Devolviendo contexto sin contrato.",
                    document_id,
                )
                doc_row = session.execute(
                    _SQL_DOC_HEADER, {"document_id": document_id}
                ).mappings().first() or {}
                return ValuationContextRaw(
                    document_id=document_id,
                    codigo_contrato_seleccionado=None,
                    contrato=None,
                    lineas_albaran=lineas_albaran,
                    lineas_contrato=[],
                    fecha_albaran=_opt_str(doc_row.get("fecha")),
                    numero_albaran=_opt_str(doc_row.get("numero_albaran")),
                )

            # La cabecera del contrato se busca por CODIGO (no por
            # document_id): es unica por sigrid_ide y su document_id es el
            # del ultimo albaran enriquecido, asi que los albaranes que
            # COMPARTEN contrato no la encontraban por document_id.
            contrato_row = session.execute(
                _SQL_CONTRATO_HEADER,
                {"codigo_contrato": codigo_contrato},
            ).mappings().first()

            if contrato_row is None:
                raise KeyError(
                    f"Contrato no encontrado para document_id={document_id} "
                    f"codigo_contrato={codigo_contrato}"
                )

            # Las lineas se atan al id de ESA cabecera (contrato_id), no al
            # document_id, para que coincidan con la cabecera elegida.
            contrato_lines_rows = session.execute(
                _SQL_CONTRATO_LINES,
                {"contrato_id": contrato_row["id"]},
            ).mappings().all()

            lineas_contrato = [
                self._build_contrato_line(row) for row in contrato_lines_rows
            ]

            doc_row = session.execute(
                _SQL_DOC_HEADER, {"document_id": document_id}
            ).mappings().first() or {}

            return ValuationContextRaw(
                document_id=document_id,
                codigo_contrato_seleccionado=codigo_contrato,
                contrato=self._build_contrato_header(contrato_row),
                lineas_albaran=lineas_albaran,
                lineas_contrato=lineas_contrato,
                fecha_albaran=_opt_str(doc_row.get("fecha")),
                numero_albaran=_opt_str(doc_row.get("numero_albaran")),
            )

    @staticmethod
    def _build_albaran_line(row: dict[str, Any]) -> RawAlbaranLine:
        return RawAlbaranLine(
            merge_line_id=int(row["merge_line_id"]),
            line_index=int(row["line_index"] or 0),
            codigo=_opt_str(row.get("codigo")),
            descripcion=_opt_str(row.get("descripcion")),
            unidad_medida=_opt_str(row.get("unidad_medida")),
            cantidad=_opt_float(row.get("cantidad")),
            precio_unitario_albaran=_opt_float(row.get("precio_unitario_albaran")),
            importe_albaran=_opt_float(row.get("importe_albaran")),
            codigo_partida_albaran=_opt_str(row.get("codigo_partida_albaran")),
            contexto_linea_json=_opt_str(row.get("contexto_linea_json")),
            # Tanda descuento — abr 2026
            descuento=_opt_float(row.get("descuento_albaran")),
            precio_neto=_opt_float(row.get("precio_neto_albaran")),
        )

    @staticmethod
    def _build_contrato_line(row: dict[str, Any]) -> RawContratoLine:
        return RawContratoLine(
            contrato_line_id=int(row["contrato_line_id"]),
            codigo_contrato=str(row["codigo_contrato"]),
            codigo_producto=_opt_str(row.get("codigo_producto")),
            descripcion=_opt_str(row.get("descripcion")),
            unidad_medida=_opt_str(row.get("unidad_medida")),
            precio_unitario=_opt_float(row.get("precio_unitario")),
            codigo_partida=_opt_str(row.get("codigo_partida")),
        )

    @staticmethod
    def _build_contrato_header(row: dict[str, Any]) -> RawContratoHeader:
        return RawContratoHeader(
            codigo_contrato=str(row["codigo_contrato"]),
            nombre_contrato=_opt_str(row.get("nombre_contrato")),
            cif_proveedor=_opt_str(row.get("cif_proveedor")),
            nombre_proveedor=_opt_str(row.get("nombre_proveedor")),
            codigo_obra=_opt_str(row.get("codigo_obra")),
            nombre_obra=_opt_str(row.get("nombre_obra")),
            pdf_relative_path=_opt_str(row.get("pdf_sharepoint_relative_path")),
            pdf_web_url=_opt_str(row.get("pdf_sharepoint_web_url")),
            md_relative_path=_opt_str(row.get("md_sharepoint_relative_path")),
        )


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


def _opt_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
