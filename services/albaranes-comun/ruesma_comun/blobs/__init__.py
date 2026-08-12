# ruesma_comun/blobs/__init__.py
"""Adaptador de Azure Blob Storage para el hand-off entre workers."""
from ruesma_comun.blobs.almacen import (
    AlmacenBlobs,
    BlobNoEncontradoError,
    ConfiguracionBlobsAusenteError,
    construir_almacen_desde_entorno,
)
from ruesma_comun.blobs.conexion import (
    CONTENEDOR_ENVELOPES,
    CONTENEDOR_INPUT,
    TODOS_LOS_CONTENEDORES,
    ConfiguracionBlobs,
    FabricaBlobs,
)

__all__ = [
    "AlmacenBlobs",
    "BlobNoEncontradoError",
    "ConfiguracionBlobsAusenteError",
    "construir_almacen_desde_entorno",
    "CONTENEDOR_ENVELOPES",
    "CONTENEDOR_INPUT",
    "TODOS_LOS_CONTENEDORES",
    "ConfiguracionBlobs",
    "FabricaBlobs",
]
