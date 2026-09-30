# ruesma_comun/sigrid/__init__.py
"""Lectura de sigrid-api compartida (F-052).

Solo lo que es igual en todos los clientes: qué hacer con ``truncated`` y
cómo encadenar páginas ``OFFSET/FETCH``. La SQL de cada servicio NO vive
aquí (D2): cada cliente conserva la suya.
"""
from ruesma_comun.sigrid.lectura import (
    PoliticaTruncado,
    SigridRespuestaTruncada,
    comprobar_truncado,
    con_paginacion,
    leer_paginado,
)

__all__ = [
    "PoliticaTruncado",
    "SigridRespuestaTruncada",
    "comprobar_truncado",
    "con_paginacion",
    "leer_paginado",
]
