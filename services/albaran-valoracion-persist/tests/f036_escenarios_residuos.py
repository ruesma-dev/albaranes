# tests/f036_escenarios_residuos.py
"""Escenarios de RESIDUOS compartidos por los tests de F-036 (bloque D3).

No lleva prefijo ``test_`` a proposito: es un modulo de apoyo, no una
suite. Reutiliza el cableado real del builder de ``f027_escenarios``
—los cinco colaboradores de ``interface_adapters/composition.py``— y
arma el ``ValuationEnvelope`` a mano, tal como lo entrega sv5 con el
prompt ``valuation_residuos``.

El catalogo es el del contrato de SALMEDINA reducido a lo que importa:
la linea de MOVIMIENTO DE CONTENEDOR (lo que se factura) y las lineas
de INCREMENTO LER (el recargo por tipo de residuo). Estan en la MISMA
partida, como en Sigrid.

Sin red, sin BBDD, sin LLM: el unico fichero que se lee del disco es
``config/unit_registry.yaml``, dato versionado del propio servicio.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from domain.models.contexto_linea import ContextoLinea
from domain.models.valuation_envelope import (
    ContratoLineContextDto,
    LineValuationDto,
)
from tests.f027_escenarios import construir_builder

#: Partida unica del escenario: albaran y contrato coinciden, para que
#: el ruido del re-apuntado por partida no tape lo que se mide aqui.
PARTIDA = "32.01"


def linea_contrato(
    contrato_line_id: int,
    descripcion: str,
    precio: float,
    *,
    partida: str = PARTIDA,
    codigo_contrato: str = "CTSU25/0100",
) -> ContratoLineContextDto:
    return ContratoLineContextDto(
        contrato_line_id=contrato_line_id,
        codigo_contrato=codigo_contrato,
        codigo_producto=None,
        descripcion=descripcion,
        unidad_medida="UD",
        precio_unitario=precio,
        codigo_partida=partida,
    )


#: Lo que se factura: un movimiento de contenedor de 6 m3, 120 EUR.
CONTENEDOR_6 = linea_contrato(
    9001,
    "MOVIMIENTO DE CONTENEDOR DE 6 M CUBICOS MEZCLA OTROS RESIDUOS",
    120.0,
)
#: El recargo por LER que hoy no se emite nunca: 51 EUR (SS-0000589).
INCREMENTO_170802 = linea_contrato(
    9002,
    "INCREMENTO LER 170802 MATERIALES DE CONSTRUCCION A BASE DE YESO",
    51.0,
)
#: Un segundo incremento, para comprobar que se elige el del LER bueno.
INCREMENTO_170904 = linea_contrato(
    9003, "INCREMENTO LER 170904 RESIDUOS MEZCLADOS", 16.0,
)

CONTRATO_SALMEDINA = [CONTENEDOR_6, INCREMENTO_170802, INCREMENTO_170904]

#: El mismo contrato SIN ningun incremento por LER (R17): el gestor
#: cobra el recargo pero no esta cargado en Sigrid.
CONTRATO_SIN_INCREMENTOS = [CONTENEDOR_6]


@dataclass(frozen=True)
class LineaResiduos:
    """Una linea de albaran de residuos con su contexto y su match."""

    merge_line_id: int = 700
    descripcion: str = "RETIRADA DE RESIDUOS MEZCLADOS"
    cantidad: float | None = 6.0
    unidad: str | None = "M3"
    codigo_ler: str | None = "170802"
    volumen_m3: float | None = 6.0
    contenedores: float | None = None
    tipo_familia: str | None = "residuos"
    rol_linea: str | None = "base"
    #: Linea de contrato que caso IA3.
    matched_contrato_line_id: int | None = CONTENEDOR_6.contrato_line_id
    precio_contrato_db: float | None = 120.0
    match_method: str = "semantic"
    sin_contexto: bool = False

    def contexto(self) -> ContextoLinea | None:
        if self.sin_contexto:
            return None
        return ContextoLinea(
            tipo_familia=self.tipo_familia,
            rol_linea=self.rol_linea,
            codigo_ler=self.codigo_ler,
            volumen_m3=self.volumen_m3,
            contenedores=self.contenedores,
        )


@dataclass(frozen=True)
class EscenarioResiduos:
    """Un albaran de residuos contra un catalogo de contrato."""

    lineas: tuple[LineaResiduos, ...] = (LineaResiduos(),)
    contrato: tuple[ContratoLineContextDto, ...] = tuple(CONTRATO_SALMEDINA)
    #: Sinteticas que IA3 trajo en el sobre (para probar el dedupe).
    sinteticas_ia: tuple[LineValuationDto, ...] = field(default_factory=tuple)
    numero_albaran: str = "SS-0000589"


def construir_envelope(escenario: EscenarioResiduos):
    """``ValuationEnvelope`` de residuos, como lo entrega sv5."""
    from domain.models.valuation_envelope import (
        AlbaranLineContextDto,
        DocumentoValoracionDto,
        ValuationContextDto,
        ValuationEnvelope,
        ValuationEnvelopeMeta,
    )

    lineas_ia = [
        LineValuationDto(
            merge_line_id=l.merge_line_id,
            line_kind="from_albaran",
            match_method=l.match_method,  # type: ignore[arg-type]
            matched_contrato_line_id=l.matched_contrato_line_id,
            match_confidence_pct=90.0,
            unidad_categoria_albaran="volume",
            unidad_category_match=False,
            precio_unitario_contrato_db=l.precio_contrato_db,
            descripcion_linea=l.descripcion,
        )
        for l in escenario.lineas
    ]
    lineas_ia.extend(escenario.sinteticas_ia)

    contexto = [
        AlbaranLineContextDto(
            merge_line_id=l.merge_line_id,
            line_index=i,
            descripcion=l.descripcion,
            unidad_medida=l.unidad,
            unidad_categoria="volume",
            cantidad=l.cantidad,
            precio_unitario_albaran=None,
            importe_albaran=None,
            codigo_partida_albaran=PARTIDA,
            contexto_linea=l.contexto(),
        )
        for i, l in enumerate(escenario.lineas)
    ]

    return ValuationEnvelope(
        status="ok",
        meta=ValuationEnvelopeMeta(
            document_id=f"doc-{escenario.numero_albaran}",
            codigo_contrato="CTSU25/0100",
            numero_albaran=escenario.numero_albaran,
            fecha_albaran="2025-06-10",
            prompt_key="valuation_residuos",
        ),
        data=DocumentoValoracionDto(lineas=lineas_ia),
        context=ValuationContextDto(
            lineas_albaran=contexto,
            lineas_contrato=list(escenario.contrato),
        ),
    )


def valorar(escenario: EscenarioResiduos):
    """Devuelve ``(cabecera, registros)`` del escenario."""
    return construir_builder().build(
        envelope=construir_envelope(escenario),
        existing_document_already_valued=False,
    )


def base_de(registros):
    """El unico record ``from_albaran`` del escenario."""
    bases = [r for r in registros if r.line_kind == "from_albaran"]
    assert len(bases) == 1, bases
    return bases[0]


def sinteticas_de(registros):
    """Los records ``synthetic_modifier``, en el orden en que salen."""
    return [r for r in registros if r.line_kind == "synthetic_modifier"]
