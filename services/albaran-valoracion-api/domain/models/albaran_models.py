# domain/models/albaran_models.py
from __future__ import annotations

from typing import List, Optional

from pydantic import Field
from ruesma_comun.contratos import ClasificacionAlbaran

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


class LineaAlbaran(StrictSchemaModel):
    id: Optional[str] = None
    cabecera_id: Optional[str] = None
    codigo: Optional[str] = None
    cantidad: Optional[float] = None
    concepto: Optional[str] = None
    # -----------------------------------------------------------------
    # Unidad de medida tal y como aparece en el albarán ('m3', 'kg',
    # 'ud', 'min', 'h'...). Antes estaba embebida implícitamente en
    # ``concepto``; ahora se persiste como campo propio para que el
    # valorador (svc5) y el conversor de unidades (svc6) tengan un
    # dato fiable sin necesidad de re-parsear el concepto.
    #
    # El prompt V2 del OCR ya pide este dato explícitamente.
    # -----------------------------------------------------------------
    unidad_medida: Optional[str] = None
    precio: Optional[float] = None
    descuento: Optional[float] = None
    precio_neto: Optional[float] = None
    codigo_imputacion: Optional[str] = None
    confianza_pct: Optional[float] = Field(default=None, ge=0, le=100)

    # -----------------------------------------------------------------
    # Bloque opcional con info estructural de la línea (familia
    # hormigón / combustible / alquiler_maquinaria / otro). Si la línea
    # no pertenece a una familia compleja, el OCR omite el bloque y
    # llega como None. Ver domain/models/contexto_linea.py y los
    # prompts V2 para la semántica exacta.
    # -----------------------------------------------------------------
    contexto_linea: Optional[ContextoLinea] = None


class DocumentoAlbaran(StrictSchemaModel):
    cabecera: CabeceraAlbaran
    lineas: List[LineaAlbaran]
    # -----------------------------------------------------------------
    # (ago 2026 · F-043 R8) Clasificacion de DOCUMENTO que IA1 devuelve
    # siempre en fase 1 y que IA2 puede corregir en `documento_revisado`.
    #
    # POR QUE ESTA AQUI SI SV5 NO VALIDA DOCUMENTOS DE FASE 1 NI 2.
    # Esta copia de los schemas de sv2 vive en sv5 sin usarse: el
    # `SchemaRegistry` del servicio solo sirve `documento_valoracion` y
    # `documento_conciliacion`, y el albaran se lee con SQL crudo. Hoy,
    # por tanto, este campo no cambia ningun comportamiento.
    #
    # Se declara igualmente porque el modelo es `extra='forbid'`: sin
    # el, el dia que alguien registre este schema, un documento con
    # `clasificacion` seria RECHAZADO ENTERO y el fallo apareceria
    # lejos de aqui. Es el mismo cepo que se llevo por delante a
    # `meta.tipologia` en el `ExtractionMeta` de sv3 —el defecto que
    # F-043 existe para arreglar— y no se deja montado dos veces.
    #
    # `None` por defecto: un documento anterior a F-043 sigue validando.
    # -----------------------------------------------------------------
    clasificacion: Optional[ClasificacionAlbaran] = None
