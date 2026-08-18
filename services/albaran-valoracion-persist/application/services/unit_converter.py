# application/services/unit_converter.py
from __future__ import annotations

import logging
from dataclasses import dataclass

from domain.models.unit_models import ConversionResult
from domain.ports.unit_registry_port import UnitRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConvertedQuantity:
    cantidad_convertida: float | None
    factor: float | None
    ambiguous: bool
    reasons: list[str]


# (jul 2026) Plausibilidad de TONELADAS cuando el albarán NO trae unidad.
# Caso real: albarán de árido "M 20/40" con cantidad 29920 sin unidad,
# contrato en TN a 9,97 €/TN → 298.302 € (un camión lleva ~25-30 TN; el
# número era claramente KG). Dos niveles:
#   * >= _TN_UMBRAL_CONVERTIR (1000): es KG con certeza (1000 KG = 1 TN;
#     ningún albarán real trae >= 1000 TN) → se reinterpreta /1000 y se
#     marca revisión.
#   * >= _TN_UMBRAL_AVISAR (100): implausible pero no seguro → NO se toca
#     la cantidad, solo se marca revisión.
# Ambos casos ponen ambiguous=True, que aguas abajo activa
# review_required (el revisor siempre lo ve).
#
# (ago 2026 · F-027) ESTA RED VIVIÓ MUERTA ENTRE JUL Y AGO DE 2026.
# No por estar mal escrita —sus tests unitarios pasaban— sino porque
# nadie la llamaba con una cantidad: el ValuationBuilder pasaba
# cantidad=None a propósito cuando el guard de categoría devolvía
# category_match=False, que es EXACTAMENTE el caso en que esta red
# aplica (albarán sin unidad ⇒ categoría 'unknown' ⇒ desacuerdo con el
# 'mass' del contrato). La guarda de `cantidad is None` de abajo salía
# antes de llegar aquí.
# Coste medido en la prueba local del 2026-08-18: albarán 58826 de
# MAHORSA (30.380 kg sin literal de unidad, contrato CTSU25/0085 en TN)
# valorado en 468.763,40 € frente a los 390,99 € del administrativo, y
# el 58878 en 462.282,80 € frente a 385,59 €. Con la cantidad real,
# este mismo código devuelve 30,38 TN con factor 0,001.
# Y el warning de abajo NUNCA se emitió: su ausencia en los logs es la
# señal de que la red no se está ejecutando. Si vuelve a desaparecer,
# sospechar de quién llama, no de este fichero.
#
# La guarda de `cantidad is None` de convert() es la PRIMERA a
# propósito, y solo debe dispararse cuando la cantidad falta DE VERDAD:
# sin cantidad no hay nada que reinterpretar. Usarla como forma de
# "saltarse la conversión" es lo que produjo el ×1000 — y además no
# protegía de nada, porque ante categorías incompatibles de verdad
# (UD → M3) convert() ya devuelve None por su cuenta.
_TN_UMBRAL_CONVERTIR = 1000.0
_TN_UMBRAL_AVISAR = 100.0
_UNIDADES_TONELADA = frozenset({
    "tn", "t", "tm", "ton", "tons", "tonelada", "toneladas", "tns",
})


def _es_tonelada(unidad: str | None) -> bool:
    return (unidad or "").strip().lower().rstrip(".") in _UNIDADES_TONELADA


class UnitConverter:
    """Fachada sobre el ``UnitRegistry`` para convertir cantidades."""

    def __init__(
        self,
        registry: UnitRegistry,
        *,
        tn_umbral_convertir: float = _TN_UMBRAL_CONVERTIR,
        tn_umbral_avisar: float = _TN_UMBRAL_AVISAR,
    ) -> None:
        self._registry = registry
        self._tn_umbral_convertir = float(tn_umbral_convertir)
        self._tn_umbral_avisar = float(tn_umbral_avisar)

    def convert(
        self,
        *,
        cantidad: float | None,
        unidad_albaran: str | None,
        unidad_contrato: str | None,
    ) -> ConvertedQuantity:
        if cantidad is None:
            return ConvertedQuantity(
                cantidad_convertida=None,
                factor=None,
                ambiguous=False,
                reasons=["no_quantity_in_albaran"],
            )

        # Si no tenemos unidad de contrato, devolvemos la cantidad tal
        # cual (factor 1). El guard del paso anterior ya marcará
        # review_required si hace falta.
        if unidad_contrato is None or not unidad_contrato.strip():
            return ConvertedQuantity(
                cantidad_convertida=float(cantidad),
                factor=1.0,
                ambiguous=False,
                reasons=["no_contract_unit_assumed_same"],
            )

        if unidad_albaran is None or not unidad_albaran.strip():
            # (jul 2026) Plausibilidad TN: ver nota de cabecera.
            if _es_tonelada(unidad_contrato):
                valor = float(cantidad)
                if valor >= self._tn_umbral_convertir:
                    logger.warning(
                        "[unit-converter] cantidad %s sin unidad con "
                        "contrato en TN: reinterpretada como KG -> %s TN",
                        valor, valor / 1000.0,
                    )
                    return ConvertedQuantity(
                        cantidad_convertida=valor / 1000.0,
                        factor=0.001,
                        ambiguous=True,
                        reasons=[
                            "cantidad_sin_unidad_reinterpretada_kg_a_tn"
                        ],
                    )
                if valor >= self._tn_umbral_avisar:
                    return ConvertedQuantity(
                        cantidad_convertida=valor,
                        factor=1.0,
                        ambiguous=True,
                        reasons=["cantidad_tn_implausible_revisar"],
                    )
            return ConvertedQuantity(
                cantidad_convertida=float(cantidad),
                factor=1.0,
                ambiguous=False,
                reasons=["no_albaran_unit_assumed_same"],
            )

        result: ConversionResult = self._registry.convert(
            quantity=float(cantidad),
            from_unit=unidad_albaran,
            to_unit=unidad_contrato,
        )
        reasons: list[str] = []
        if result.reason:
            reasons.append(result.reason)
        if result.ambiguous:
            reasons.append("ambiguous_unit_conversion")
        if not result.category_match:
            reasons.append("unit_category_mismatch_in_conversion")
            return ConvertedQuantity(
                cantidad_convertida=None,
                factor=None,
                ambiguous=False,
                reasons=reasons,
            )
        return ConvertedQuantity(
            cantidad_convertida=result.converted_quantity,
            factor=result.factor,
            ambiguous=result.ambiguous,
            reasons=reasons,
        )
