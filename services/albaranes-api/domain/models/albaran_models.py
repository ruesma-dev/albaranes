# domain/models/albaran_models.py
from __future__ import annotations

from typing import List, Optional

from pydantic import Field

from domain.models.contexto_linea import ContextoLinea
from domain.models.schema_base import StrictSchemaModel


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
    # F-003 · Total del albarán TRANSCRITO (nunca sumado por la IA).
    # `importe_total` es la base imponible si el documento la distingue;
    # si el único total impreso incluye IVA, se transcribe ESE total y
    # `importe_total_incluye_iva` queda a True para que los guards de
    # sv6 avisen en vez de exigir cuadre (los importes de línea del
    # pipeline son sin IVA). Sin total impreso: ambos null.
    # -----------------------------------------------------------------
    importe_total: Optional[float] = None
    importe_total_incluye_iva: Optional[bool] = None


class LineaAlbaran(StrictSchemaModel):
    id: Optional[str] = None
    cabecera_id: Optional[str] = None
    codigo: Optional[str] = None
    cantidad: Optional[float] = None
    concepto: Optional[str] = None
    precio: Optional[float] = None
    descuento: Optional[float] = None
    precio_neto: Optional[float] = None

    # -----------------------------------------------------------------
    # F-003 · Albaranes que VIENEN valorados: transcribir, no recomponer.
    # `importe` es el importe de línea IMPRESO en la columna de importe
    # (IMPORTE / TOTAL / NETO), leído tal cual; jamás derivado de precio
    # y cantidad. `descuentos` transcribe TODAS las columnas de descuento
    # en el orden del documento; cuando hay más de una, la IA deja
    # `descuento` a null y sv3 deriva el efectivo en cascada (R3).
    # -----------------------------------------------------------------
    importe: Optional[float] = None
    descuentos: Optional[List[float]] = None

    codigo_imputacion: Optional[str] = None
    confianza_pct: Optional[float] = Field(default=None, ge=0, le=100)

    # -----------------------------------------------------------------
    # Bloque opcional con info estructural de la línea (familia
    # hormigón / combustible / alquiler_maquinaria). Si la línea no
    # pertenece a una familia compleja, el OCR omite el bloque y llega
    # como None. Ver domain/models/contexto_linea.py y los prompts V2
    # para la semántica exacta.
    #
    # Nota sobre StrictSchemaModel (extra='forbid'): como el campo está
    # declarado explícitamente, 'forbid' no lo bloquea. El 'forbid' solo
    # rechaza campos no declarados en el modelo.
    # -----------------------------------------------------------------
    contexto_linea: Optional[ContextoLinea] = None


class DocumentoAlbaran(StrictSchemaModel):
    cabecera: CabeceraAlbaran
    lineas: List[LineaAlbaran]
