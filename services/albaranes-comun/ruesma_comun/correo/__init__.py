# ruesma_comun/correo/__init__.py
"""Texto del correo como contexto de IA1 (F-048).

Se reexporta aqui para que los servicios importen de UN solo sitio
(``from ruesma_comun.correo import construir_contexto_correo``).
"""
from ruesma_comun.correo.contexto import (
    MAX_CARACTERES_DEFECTO,
    ContextoCorreo,
    construir_contexto_correo,
    guardar_contexto_correo,
    leer_contexto_correo,
    nombre_blob_correo,
)

__all__ = [
    "MAX_CARACTERES_DEFECTO",
    "ContextoCorreo",
    "construir_contexto_correo",
    "guardar_contexto_correo",
    "leer_contexto_correo",
    "nombre_blob_correo",
]
