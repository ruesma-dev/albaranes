# tests/ayudas_f003.py
"""Fabricas compartidas por los tests de F-003 (sv6).

Montan un ``ValuationBuilder`` REAL con sus servicios deterministas (el
registro de unidades del propio servicio) y envelopes minimos. Nada de
red, BBDD ni LLM: todo son objetos en memoria.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from application.services.importe_calculator import ImporteCalculator
from application.services.partida_matcher import PartidaMatcher
from application.services.price_reconciler import PriceReconciler
from application.services.unit_category_guard import UnitCategoryGuard
from application.services.unit_converter import UnitConverter
from application.services.valuation_builder import ValuationBuilder
from domain.models.valuation_envelope import ValuationEnvelope
from infrastructure.units.yaml_unit_registry import YamlUnitRegistry

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
UNIT_REGISTRY = RAIZ_SERVICIO / "config" / "unit_registry.yaml"

PRICE_TOLERANCE_PCT = 2.0
IMPORTE_TOLERANCE_PCT = 5.0


def construir_builder(**kwargs: Any) -> ValuationBuilder:
    """ValuationBuilder con el mismo cableado que ``composition.py``."""
    registry = YamlUnitRegistry(str(UNIT_REGISTRY))
    parametros: dict[str, Any] = {
        "unit_category_guard": UnitCategoryGuard(unit_registry=registry),
        "price_reconciler": PriceReconciler(
            tolerance_pct=PRICE_TOLERANCE_PCT,
        ),
        "partida_matcher": PartidaMatcher(alm_codigo_partida="ALM"),
        "unit_converter": UnitConverter(registry=registry),
        "importe_calculator": ImporteCalculator(
            tolerance_pct=IMPORTE_TOLERANCE_PCT,
        ),
    }
    parametros.update(kwargs)
    return ValuationBuilder(**parametros)


def linea_contexto(**kwargs: Any) -> dict[str, Any]:
    """Una linea del bloque ``context.lineas_albaran`` del envelope."""
    base: dict[str, Any] = {
        "merge_line_id": 1,
        "line_index": 1,
        "codigo": "P1",
        "descripcion": "PRODUCTO",
        "unidad_medida": "ud",
        "unidad_categoria": "count",
        "cantidad": 1.0,
        "precio_unitario_albaran": 10.0,
        "importe_albaran": 10.0,
        "codigo_partida_albaran": "01.01",
    }
    base.update(kwargs)
    return base


def linea_contrato(**kwargs: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "contrato_line_id": 100,
        "codigo_contrato": "C-1",
        "codigo_producto": "P1",
        "descripcion": "PRODUCTO",
        "unidad_medida": "ud",
        "unidad_categoria": "count",
        "precio_unitario": 10.0,
        "codigo_partida": "01.01",
    }
    base.update(kwargs)
    return base


def linea_valorada(**kwargs: Any) -> dict[str, Any]:
    """Una linea del bloque ``data.lineas`` (salida de IA3/IA4)."""
    base: dict[str, Any] = {
        "merge_line_id": 1,
        "line_kind": "from_albaran",
        "match_method": "exact_concept",
        "matched_contrato_line_id": 100,
        "match_confidence_pct": 95.0,
        "unidad_categoria_albaran": "count",
        "unidad_category_match": True,
        "precio_unitario_contrato_db": 10.0,
        "razon_corta": "casa",
    }
    base.update(kwargs)
    return base


def envelope(
    *,
    lineas_data: list[dict[str, Any]] | None = None,
    lineas_albaran: list[dict[str, Any]] | None = None,
    lineas_contrato: list[dict[str, Any]] | None = None,
    meta: dict[str, Any] | None = None,
) -> ValuationEnvelope:
    meta_base: dict[str, Any] = {
        "document_id": "doc-1",
        "codigo_contrato": "C-1",
        "primary_provider": "claude",
        "model": "fake-model",
        "prompt_key": "valuation_es",
    }
    meta_base.update(meta or {})
    return ValuationEnvelope.model_validate(
        {
            "status": "ok",
            "meta": meta_base,
            "data": {
                "lineas": (
                    lineas_data
                    if lineas_data is not None
                    else [linea_valorada()]
                )
            },
            "context": {
                "lineas_albaran": (
                    lineas_albaran
                    if lineas_albaran is not None
                    else [linea_contexto()]
                ),
                "lineas_contrato": (
                    lineas_contrato
                    if lineas_contrato is not None
                    else [linea_contrato()]
                ),
            },
        }
    )


def construir(builder: ValuationBuilder, sobre: ValuationEnvelope):
    return builder.build(
        envelope=sobre,
        existing_document_already_valued=False,
    )
