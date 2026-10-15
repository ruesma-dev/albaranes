# ruesma_comun/configuracion.py
"""Motivo de una configuración que no se puede leer, SIN sus valores.

``str(ValidationError)`` vuelca ``input_value``: con un obligatorio ausente es
el diccionario de TODO el entorno leído por pydantic-settings (``PG_PASSWORD``,
``GRAPH_KEY``, ``SIGRID_API_FUNCTION_KEY``...). Al log solo van el campo
(``loc``) y el motivo (``msg``). Lección H1 de la fase 1 de F-053 (R35); lo
usan sv9 y sv4 al arrancar (R44).

Función pura, sin E/S.
"""
from __future__ import annotations

from pydantic import ValidationError


def motivos_configuracion(exc: ValidationError) -> str:
    """``campo: motivo`` de cada error, separados por ``; ``."""
    return "; ".join(
        f"{'.'.join(str(parte) for parte in error['loc'])}: {error['msg']}"
        for error in exc.errors(include_input=False, include_url=False)
    )
