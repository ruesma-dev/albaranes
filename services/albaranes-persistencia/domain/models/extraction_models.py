# domain/models/extraction_models.py
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import Field

from domain.models.contexto_linea import ContextoLinea
from domain.models.schema_base import StrictSchemaModel


class ExtractionMeta(StrictSchemaModel):
    prompt_key: str
    schema_name: str = Field(alias="schema")
    source_filename: str
    source_mime_type: str
    source_sha256: str
    model: str
    processed_at_utc: str
    service: Optional[str] = None
    service_version: Optional[str] = None


class CabeceraAlbaran(StrictSchemaModel):
    proveedor_nombre: Optional[str] = None
    proveedor_cif: Optional[str] = None
    fecha: Optional[str] = None
    numero_albaran: Optional[str] = None
    forma_pago: Optional[str] = None
    obra_codigo: Optional[str] = None
    obra_nombre: Optional[str] = None
    obra_direccion: Optional[str] = None
    id: Optional[str] = None

    # -----------------------------------------------------------------
    # F-003 · Total del albarán TRANSCRITO por sv2 (nunca sumado).
    # `importe_total` es la base imponible si el documento la distingue;
    # si el único total impreso incluye IVA, se transcribe ese total y
    # `importe_total_incluye_iva` llega a True. Se persisten en
    # albaran_documents[_merge] para que sv5 los ponga en el meta del
    # envelope y sv6 pueda cuadrar la suma de líneas (o solo avisar).
    # -----------------------------------------------------------------
    importe_total: Optional[float] = None
    importe_total_incluye_iva: Optional[bool] = None


class LineaAlbaran(StrictSchemaModel):
    id: Optional[str] = None
    cabecera_id: Optional[str] = None
    codigo: Optional[str] = None
    cantidad: Optional[float] = None
    concepto: Optional[str] = None
    # -----------------------------------------------------------------
    # Unidad de medida tal y como aparece en el albarán. Llega del svc2
    # en el envelope. Se persiste en albaran_lines[_merge].unidad_medida.
    # -----------------------------------------------------------------
    unidad_medida: Optional[str] = None
    precio: Optional[float] = None
    descuento: Optional[float] = None
    precio_neto: Optional[float] = None

    # -----------------------------------------------------------------
    # F-003 · Lo que el albarán trae IMPRESO cuando viene valorado.
    # `importe` es el importe de LÍNEA leído de su columna (nunca
    # derivado de precio × cantidad); `descuentos` transcribe todas las
    # columnas de descuento en orden. Con más de una, `descuento` llega
    # a null y sv3 deriva el efectivo en cascada (descuento_cascada.py).
    # -----------------------------------------------------------------
    importe: Optional[float] = None
    descuentos: Optional[List[float]] = None

    codigo_imputacion: Optional[str] = None
    confianza_pct: Optional[float] = Field(default=None, ge=0, le=100)

    # -----------------------------------------------------------------
    # Bloque opcional con info estructural de la línea (familia
    # hormigón / combustible / alquiler_maquinaria / otro). Llega del
    # servicio 2 (OCR) dentro del envelope. Si la línea no es de una
    # familia compleja, el campo llega como None.
    # -----------------------------------------------------------------
    contexto_linea: Optional[ContextoLinea] = None


class DocumentoAlbaran(StrictSchemaModel):
    cabecera: CabeceraAlbaran
    lineas: List[LineaAlbaran]


class ProviderExtractionEnvelope(StrictSchemaModel):
    meta: ExtractionMeta
    data: DocumentoAlbaran
    debug: Dict[str, Any] | None = None


class ExtractionEnvelope(ProviderExtractionEnvelope):
    gemini: ProviderExtractionEnvelope | None = None
    claude: ProviderExtractionEnvelope | None = None
    google_document_ai: ProviderExtractionEnvelope | None = None
    azure_document_intelligence: ProviderExtractionEnvelope | None = None

    # Bloque opcional añadido por sv7 cuando hay revisión IA fase 2.
    # Si está presente, sv3 lo lee con Phase2PersistenceService y lo
    # persiste en albaran_documents_merge.review_phase2_*. Es un dict
    # libre porque su forma la define sv7 (no tiene sentido validarlo
    # estrictamente aquí — sv3 solo lo guarda como auditoría).
    review_phase2_metadata: Dict[str, Any] | None = None
