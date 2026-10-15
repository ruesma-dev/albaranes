# ruesma_comun/obras/__init__.py
"""Código de obra de Ruesma (F-052 CR-C1).

Una sola normalización para todos los servicios: sv3 la usa para consultar
Sigrid y sellar el rastro de la búsqueda de contratos, sv4 para comparar ese
rastro con los datos actuales del albarán.

F-070: VAR y POSTV2 son canónicos (``CODIGOS_OBRA_SIN_CERO``) y
``canonizar_codigo_obra`` da el código que sellan sv3, consultan y guardan
sv4 y manda sv9 al alta.
"""
from ruesma_comun.obras.codigo import (
    CODIGOS_OBRA_SIN_CERO,
    canonizar_codigo_obra,
    normalizar_codigo_obra,
)

__all__ = [
    "CODIGOS_OBRA_SIN_CERO",
    "canonizar_codigo_obra",
    "normalizar_codigo_obra",
]
