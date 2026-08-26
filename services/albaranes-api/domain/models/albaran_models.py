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
    precio: Optional[float] = None
    descuento: Optional[float] = None
    precio_neto: Optional[float] = None
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

    # -----------------------------------------------------------------
    # (F-043, R8) Clasificacion de DOCUMENTO decidida por la IA: a que
    # familia pertenece el albaran, con cuanta confianza y por que. Es
    # propiedad del DOCUMENTO; `contexto_linea.tipo_familia` sigue
    # siendo el afinado por LINEA (R17).
    #
    # Viaja aqui, dentro de `data`, y NO en `meta`: sv3 filtra `meta`
    # contra un modelo estricto y hoy descarta `meta.tipologia`, que es
    # por lo que sv5 y sv6 la exigian sin recibirla nunca (R9).
    #
    # Default `None` a proposito: un envelope anterior a esta feature
    # no la trae y tiene que seguir validando (R8). El `extra='forbid'`
    # de StrictSchemaModel no estorba porque el campo esta declarado.
    # -----------------------------------------------------------------
    clasificacion: Optional[ClasificacionAlbaran] = None
