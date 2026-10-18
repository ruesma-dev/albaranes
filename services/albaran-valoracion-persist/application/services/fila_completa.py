# application/services/fila_completa.py
"""(F-078 R4, R5) Cada fila que sv6 persiste lleva lo que la ficha va a enseñar.

Antes del ``replace_valuation`` con líneas, ``completar_registros`` aplica a
cada registro (``from_albaran`` y ``synthetic_modifier``, de cualquier builder)
la regla común ``ruesma_comun.linea_valorada.fila_a_guardar``: concepto,
unidad, precio, ``unidad_albaran`` y ``cantidad_convertida``. Nada más (R5):
importes, partida, ``partida_action``, cantidades con conversión, motivos y
``review_required`` salen tal cual.

- **Su línea**: la de contrato del sobre (``context.lineas_contrato``) si el
  registro casa con una; si no, su derivada del propio registro
  (``derived_contrato_line_record``). Es el orden con el que la ficha de sv4
  decide Contrato / Nueva.
- **Concepto de su blanca**: la ``descripcion`` de ``context.lineas_albaran``
  por ``merge_line_id``. Una sintética no tiene blanca propia y NO hereda el
  concepto de su base: ``None``.
"""
from __future__ import annotations

from dataclasses import replace

from ruesma_comun.linea_valorada import CamposFila, LineaDeLaFila, fila_a_guardar

from domain.models.valuation_envelope import ValuationEnvelope
from domain.models.valuation_records import LineValuationRecord


def _linea_de_la_fila(
    record: LineValuationRecord, envelope: ValuationEnvelope,
) -> LineaDeLaFila | None:
    if record.matched_contrato_line_id is not None:
        for contrato in envelope.context.lineas_contrato:
            if contrato.contrato_line_id == record.matched_contrato_line_id:
                return LineaDeLaFila(
                    es_contrato=True,
                    descripcion=contrato.descripcion,
                    unidad=contrato.unidad_medida,
                    precio_unitario=contrato.precio_unitario,
                )
    derivada = record.derived_contrato_line_record
    if derivada is not None:
        return LineaDeLaFila(
            es_contrato=False,
            descripcion=derivada.descripcion_linea,
            unidad=derivada.unidad_medida,
            precio_unitario=derivada.precio_unitario,
        )
    return None


def _concepto_blanca(
    record: LineValuationRecord, envelope: ValuationEnvelope,
) -> str | None:
    if record.merge_line_id is None:
        return None
    for blanca in envelope.context.lineas_albaran:
        if blanca.merge_line_id == record.merge_line_id:
            return blanca.descripcion
    return None


def completar_registro(
    record: LineValuationRecord, envelope: ValuationEnvelope,
) -> LineValuationRecord:
    """El registro con los cinco campos de ``fila_a_guardar`` (R4)."""
    guardar = fila_a_guardar(
        CamposFila(
            descripcion_linea=record.descripcion_linea,
            unidad_contrato=record.unidad_contrato,
            unidad_albaran=record.unidad_albaran,
            precio_unitario_final=record.precio_unitario_final,
            cantidad_albaran=record.cantidad_albaran,
            cantidad_convertida=record.cantidad_convertida,
            factor_conversion=record.factor_conversion,
        ),
        _linea_de_la_fila(record, envelope),
        _concepto_blanca(record, envelope),
    )
    return replace(
        record,
        descripcion_linea=guardar.descripcion_linea,
        unidad_contrato=guardar.unidad_contrato,
        unidad_albaran=guardar.unidad_albaran,
        precio_unitario_final=guardar.precio_unitario_final,
        cantidad_convertida=guardar.cantidad_convertida,
    )


def completar_registros(
    lines: list[LineValuationRecord], envelope: ValuationEnvelope,
) -> list[LineValuationRecord]:
    """(R4) Registros nuevos, en el mismo orden; los de entrada no cambian."""
    return [completar_registro(record, envelope) for record in lines]
