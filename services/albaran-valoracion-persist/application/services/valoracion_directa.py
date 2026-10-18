# application/services/valoracion_directa.py
"""(F-075) Valoración directa: sin contrato y con importes, manda el albarán.

Decisión del humano (2026-10-15): «si trae importes no hace valorar ni
contrato, pasa directo». Cuando sv5 devuelve el sobre ``no_contract`` y
alguna línea de ``context.lineas_albaran`` trae importe LEÍDO
(``precio_neto_albaran``, el importe tras descuento sin IVA; sv5 lo manda
desde F-075 R5 bis), sv6 construye la valoración desde las propias líneas
del albarán:

- sin IA, sin contrato y sin sintéticas (R7);
- cabecera ``no_contract`` (D2: así ``esta_valorado`` y sv9 no cambian) con
  ``prompt_key`` y motivo ``valoracion_directa_albaran``, que la distinguen
  de la cabecera vacía de siempre;
- una línea ``from_albaran`` por cada línea del albarán (R6), con una
  derivada ``nueva_no_match`` con ``codigo_contrato=""`` (F-065: sin línea de
  contrato ni derivada la ficha no la pinta y no se aprueba).

Se usa el ``precio_neto`` PURO, no ``importe_albaran``, que sv5 deriva con la
fórmula cuando falta (P3): una línea sin importe leído queda con importe
nulo, va a revisión (``sin_importe_en_albaran``) y el documento no se aprueba
hasta completarla (F-053 R37). La aritmética es la de ``ruesma_comun.importes``.

Puro: sin BBDD ni red. El pipeline aplica después ``completar_registros``
(F-078) y ``NormalizadorPartidas.anotar`` (F-076), como en la rama normal.
"""
from __future__ import annotations

from ruesma_comun.importes import importe_albaran, unitario_despejado

from domain.models.valuation_envelope import AlbaranLineContextDto, ValuationEnvelope
from domain.models.valuation_records import (
    DerivedContratoLineRecord,
    LineValuationRecord,
    PrecioUnitarioSource,
    ValuationHeaderRecord,
)

#: ``prompt_key`` y motivo de cabecera de una valoración directa.
PROMPT_KEY_DIRECTA = "valoracion_directa_albaran"
MOTIVO_DIRECTA = "valoracion_directa_albaran"
#: (R6) Motivo de una línea sin importe leído.
MOTIVO_SIN_IMPORTE = "sin_importe_en_albaran"
#: El motivo de cabecera que pone el builder cuando alguna línea va a revisión.
MOTIVO_CABECERA_REVISION = "at_least_one_line_requires_review"


def _texto(valor: str | None) -> str | None:
    if valor is None:
        return None
    limpio = valor.strip()
    return limpio or None


def _numero(valor: float | None) -> float | None:
    """El importe leído como número finito (``importe_albaran`` decide qué
    cuenta como importe: lo mismo aquí, línea a línea)."""
    resumen = importe_albaran([valor])
    return resumen.total


class ValoracionDirectaBuilder:
    """Construye la valoración directa de un sobre ``no_contract`` (design §5)."""

    @staticmethod
    def aplica(envelope: ValuationEnvelope) -> bool:
        """(R5, R8) ``no_contract`` y alguna línea con importe leído."""
        if envelope.status != "no_contract":
            return False
        return importe_albaran(
            linea.precio_neto_albaran for linea in envelope.context.lineas_albaran
        ).trae_importes

    def construir(
        self, envelope: ValuationEnvelope, document_id: str,
    ) -> tuple[ValuationHeaderRecord, list[LineValuationRecord]]:
        """(R5, R6) Cabecera y una línea por cada línea del albarán."""
        lineas = [self._linea(l) for l in envelope.context.lineas_albaran]
        resumen = importe_albaran(l.importe_calculado for l in lineas)
        revision = any(l.review_required for l in lineas)
        motivos = [MOTIVO_DIRECTA]
        if revision:
            motivos.append(MOTIVO_CABECERA_REVISION)
        cabecera = ValuationHeaderRecord(
            document_id=document_id,
            contrato_codigo=None,
            status="no_contract",
            provider_ia=None,
            model_name=None,
            prompt_key=PROMPT_KEY_DIRECTA,
            total_valorado=round(resumen.total or 0.0, 2),
            total_lines=len(lineas),
            lines_matched_exact=0,
            lines_matched_semantic=0,
            lines_matched_price_only=0,
            lines_unmatched=len(lineas),
            review_required=revision,
            review_reasons=motivos,
            raw_ia_envelope_json=None,
        )
        return cabecera, lineas

    @staticmethod
    def _unitario(linea: AlbaranLineContextDto, importe: float | None) -> tuple[float | None, PrecioUnitarioSource]:
        """(R6) El unitario leído o, si falta (o es 0, como en ``PriceReconciler``),
        el despejado del importe leído."""
        leido = _numero(linea.precio_unitario_albaran)
        if leido is not None and leido != 0.0:
            return leido, "albaran_declared"
        despejado = unitario_despejado(
            importe=importe, cantidad=linea.cantidad, descuento_pct=linea.descuento_albaran,
        )
        if despejado is not None:
            return despejado, "albaran_calculated"
        return None, "none"

    def _linea(self, linea: AlbaranLineContextDto) -> LineValuationRecord:
        importe = _numero(linea.precio_neto_albaran)
        unitario, fuente = self._unitario(linea, importe)
        partida = _texto(linea.codigo_partida_albaran)
        sin_importe = importe is None
        rol = linea.contexto_linea.rol_linea if linea.contexto_linea is not None else None
        return LineValuationRecord(
            merge_line_id=linea.merge_line_id,
            matched_contrato_line_id=None,
            derived_contrato_line_record=DerivedContratoLineRecord(
                codigo_contrato="",
                codigo_producto=None,
                descripcion_linea=_texto(linea.descripcion),
                unidad_medida=linea.unidad_medida,
                precio_unitario=unitario,
                codigo_partida=partida,
                origen="nueva_no_match",
            ),
            precio_unitario_contrato_db=None,
            precio_unitario_pdf_inferido=None,
            precio_unitario_final=unitario,
            precio_unitario_source=fuente,
            precio_unitario_agreement="neither",
            unidad_albaran=linea.unidad_medida,
            unidad_contrato=linea.unidad_medida,
            unidad_categoria=linea.unidad_categoria,
            unidad_category_match=True,
            cantidad_albaran=linea.cantidad,
            cantidad_convertida=linea.cantidad,
            factor_conversion=1.0,
            importe_calculado=importe,
            importe_albaran_declarado=importe,
            importe_source="none" if sin_importe else "declared_albaran",
            codigo_partida_albaran=linea.codigo_partida_albaran,
            codigo_partida_final=partida,
            partida_action="new_line_created" if partida is not None else "almacen_sin_partida",
            match_confidence_pct=0.0,
            match_method="no_match",
            review_required=sin_importe,
            review_reasons=[MOTIVO_SIN_IMPORTE] if sin_importe else [],
            ia_reasoning=None,
            rol_linea=rol,
            descuento_albaran_aplicado=linea.descuento_albaran,
        )
