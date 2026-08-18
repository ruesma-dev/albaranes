# tests/f027_escenarios.py
"""Escenarios compartidos por los tests de F-027.

No lleva prefijo ``test_`` a proposito: es un modulo de apoyo, no una
suite. Monta el ``ValuationBuilder`` con sus CINCO colaboradores reales
—el mismo cableado que ``interface_adapters/composition.py``— y arma
``ValuationEnvelope`` a mano, tal como los entrega sv5.

Sin red, sin BBDD, sin LLM: el unico fichero que se lee del disco es
``config/unit_registry.yaml``, dato versionado del propio servicio.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def construir_builder():
    """El mismo cableado que ``interface_adapters/composition.py``."""
    from application.services.importe_calculator import ImporteCalculator
    from application.services.partida_matcher import PartidaMatcher
    from application.services.price_reconciler import PriceReconciler
    from application.services.unit_category_guard import UnitCategoryGuard
    from application.services.unit_converter import UnitConverter
    from application.services.valuation_builder import ValuationBuilder
    from infrastructure.units.yaml_unit_registry import YamlUnitRegistry

    from tests.conftest import (
        TOLERANCIA_IMPORTE_PCT,
        TOLERANCIA_PRECIO_PCT,
    )

    yaml_path = (
        Path(__file__).resolve().parents[1] / "config" / "unit_registry.yaml"
    )
    registro = YamlUnitRegistry(str(yaml_path))

    return ValuationBuilder(
        unit_category_guard=UnitCategoryGuard(unit_registry=registro),
        price_reconciler=PriceReconciler(tolerance_pct=TOLERANCIA_PRECIO_PCT),
        partida_matcher=PartidaMatcher(alm_codigo_partida="ALM"),
        unit_converter=UnitConverter(registry=registro),
        importe_calculator=ImporteCalculator(
            tolerance_pct=TOLERANCIA_IMPORTE_PCT,
        ),
    )


@dataclass(frozen=True)
class LineaContrato:
    """Una linea del catalogo de contrato tal como llega en el sobre."""

    contrato_line_id: int
    descripcion: str
    unidad_medida: str | None
    precio_unitario: float
    codigo_partida: str
    codigo_contrato: str = "CTSU25/0085"
    codigo_producto: str = "MA9999"


@dataclass(frozen=True)
class Escenario:
    """Un albaran de una linea contra un catalogo de contrato."""

    numero_albaran: str
    cantidad: float | None
    unidad_albaran: str | None
    codigo_partida_albaran: str | None
    #: Linea de contrato que caso IA3 (``matched_contrato_line_id``).
    matched_contrato_line_id: int | None
    #: Precio que IA3 trae en ``precio_unitario_contrato_db``.
    precio_contrato_db: float | None
    contrato: tuple[LineaContrato, ...] = field(default_factory=tuple)
    descripcion: str = "ARIDO M-20/40-S EN 12620:2002H"
    codigo_contrato: str = "CTSU25/0085"
    #: Lo que IA3 declaro en ``unidad_category_match``.
    unidad_category_match_ia: bool = True
    unidad_categoria_albaran_ia: str = "mass"


def construir_envelope(escenario: Escenario):
    """``ValuationEnvelope`` de una linea, como lo entrega sv5."""
    from domain.models.valuation_envelope import (
        AlbaranLineContextDto,
        ContratoLineContextDto,
        DocumentoValoracionDto,
        LineValuationDto,
        ValuationContextDto,
        ValuationEnvelope,
        ValuationEnvelopeMeta,
    )

    lineas_contrato = [
        ContratoLineContextDto(
            contrato_line_id=cl.contrato_line_id,
            codigo_contrato=cl.codigo_contrato,
            codigo_producto=cl.codigo_producto,
            descripcion=cl.descripcion,
            unidad_medida=cl.unidad_medida,
            precio_unitario=cl.precio_unitario,
            codigo_partida=cl.codigo_partida,
        )
        for cl in escenario.contrato
    ]

    linea_ia = LineValuationDto(
        merge_line_id=621,
        line_kind="from_albaran",
        match_method="semantic",
        matched_contrato_line_id=escenario.matched_contrato_line_id,
        match_confidence_pct=90.0,
        unidad_categoria_albaran=escenario.unidad_categoria_albaran_ia,
        unidad_category_match=escenario.unidad_category_match_ia,
        precio_unitario_contrato_db=escenario.precio_contrato_db,
        precio_unitario_pdf_inferido=None,
        descripcion_linea=escenario.descripcion,
    )
    contexto = AlbaranLineContextDto(
        merge_line_id=621,
        line_index=0,
        descripcion=escenario.descripcion,
        # IA1 no devolvio unidad en ninguna linea del lote
        # alvaro_17082026 (F-024): por eso llega None.
        unidad_medida=escenario.unidad_albaran,
        unidad_categoria="unknown",
        cantidad=escenario.cantidad,
        # El albaran de arido no imprime ni precio ni importe: el
        # unitario sale del contrato (fallback del PriceReconciler).
        precio_unitario_albaran=None,
        importe_albaran=None,
        codigo_partida_albaran=escenario.codigo_partida_albaran,
    )

    return ValuationEnvelope(
        status="ok",
        meta=ValuationEnvelopeMeta(
            document_id=f"doc-{escenario.numero_albaran}",
            codigo_contrato=escenario.codigo_contrato,
            numero_albaran=escenario.numero_albaran,
        ),
        data=DocumentoValoracionDto(lineas=[linea_ia]),
        context=ValuationContextDto(
            lineas_albaran=[contexto],
            lineas_contrato=lineas_contrato,
        ),
    )


def valorar(escenario: Escenario):
    """Devuelve ``(cabecera, unico_registro)`` del escenario."""
    cabecera, registros = construir_builder().build(
        envelope=construir_envelope(escenario),
        existing_document_already_valued=False,
    )
    assert len(registros) == 1, registros
    return cabecera, registros[0]


# --------------------------------------------------------------------- #
# Catalogo real del contrato CTSU25/0085 (MAHORSA), reducido a las dos
# familias de arido 20/40 que documenta
# progress/revision_resto_lote_20260818.md §4.2.
# --------------------------------------------------------------------- #

#: La que caso IA3: caliza a 15,43 EUR/TN, en OTRA partida.
#: Que sea la equivocada es F-031 y sobrevive a F-027 a proposito (R23).
CONTRATO_CALIZA_1543 = LineaContrato(
    contrato_line_id=25980,
    descripcion="ARIDO CALIZA MACHAQUEO T-20/40-C EN 12620:2002H",
    unidad_medida="TN",
    precio_unitario=15.43,
    codigo_partida="P4.14.01.02.01",
)

#: La correcta segun el administrativo: grava a 12,87 EUR/TN, en la
#: partida que el albaran trae manuscrita.
CONTRATO_GRAVA_1287 = LineaContrato(
    contrato_line_id=25972,
    descripcion="SUMINISTRO DE GRAVA 20/40",
    unidad_medida="TN",
    precio_unitario=12.87,
    codigo_partida="P4.22.01.03.07",
)

CATALOGO_MAHORSA = (CONTRATO_CALIZA_1543, CONTRATO_GRAVA_1287)
