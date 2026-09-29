# ruesma_comun/contratos/__init__.py
"""Contratos compartidos por los servicios del pipeline de albaranes.

Se reexportan aqui los modelos para que los servicios importen de UN solo
sitio (`from ruesma_comun.contratos import ClasificacionAlbaran`) y no de la
ruta interna de cada modulo.
"""
from ruesma_comun.contratos.clasificacion import ClasificacionAlbaran
from ruesma_comun.contratos.contexto_linea import ContextoLinea
from ruesma_comun.contratos.origen_datos import (
    MOTIVO_REVISION_OBRA_CORREO_AMBIGUA,
    MOTIVO_REVISION_OBRA_CORREO_DISTINTA,
    MOTIVOS_REVISION_ORIGEN,
    OrigenCampo,
    OrigenDatos,
    normalizar_codigo,
)

__all__ = [
    "MOTIVOS_REVISION_ORIGEN",
    "MOTIVO_REVISION_OBRA_CORREO_AMBIGUA",
    "MOTIVO_REVISION_OBRA_CORREO_DISTINTA",
    "ClasificacionAlbaran",
    "ContextoLinea",
    "OrigenCampo",
    "OrigenDatos",
    "normalizar_codigo",
]
