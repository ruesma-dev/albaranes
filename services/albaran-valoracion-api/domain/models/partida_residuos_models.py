# domain/models/partida_residuos_models.py
"""(F-111 R31) Entrada y salida de ``POST /v1/albaranes/partida-residuos``.

sv6 manda las líneas de residuos de un documento que llegan SIN partida y las
hojas candidatas del capítulo de gestión de residuos de su obra
(``ruesma_comun.sigrid.candidatas_residuos``); la IA elige POR SIGNIFICADO una
candidata por línea, o ``null``. Nunca pone precios ni inventa códigos.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from domain.models.schema_base import StrictSchemaModel


class LineaPartidaResiduos(BaseModel):
    """Una línea de residuos sin partida."""

    line_ref: int
    descripcion: Optional[str] = None
    codigo_ler: Optional[str] = None


class CandidataPartida(BaseModel):
    """Una hoja del capítulo de gestión de residuos de la obra."""

    codigo: str
    descripcion: Optional[str] = None
    descripcion_agregada: Optional[str] = None


class PartidaResiduosRequest(BaseModel):
    """Cuerpo del endpoint: UNA llamada por documento (R34)."""

    document_id: str
    lineas: List[LineaPartidaResiduos] = []
    candidatas: List[CandidataPartida] = []


class EleccionPartida(StrictSchemaModel):
    """La partida que la IA elige para UNA línea."""

    line_ref: int = Field(
        description="El mismo line_ref que llegó en la entrada.",
    )
    codigo: Optional[str] = Field(
        default=None,
        description=(
            "codigo de UNA de las candidatas, tal cual llegó. null si ninguna "
            "encaja por significado o si dos encajan igual. Nunca un código "
            "que no esté en las candidatas."
        ),
    )
    confianza_pct: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Confianza 0-100.",
    )
    razon_corta: str = Field(
        description="Por qué esa candidata (o por qué ninguna), para auditoría.",
    )


class DocumentoPartidaResiduos(StrictSchemaModel):
    """Salida completa: una elección por línea de entrada."""

    elecciones: List[EleccionPartida] = Field(
        default_factory=list,
        description="Una entrada por cada línea de entrada, aunque sea null.",
    )
