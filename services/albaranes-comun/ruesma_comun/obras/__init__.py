# ruesma_comun/obras/__init__.py
"""Código de obra de Ruesma (F-052 CR-C1).

Una sola normalización para todos los servicios: sv3 la usa para consultar
Sigrid y sellar el rastro de la búsqueda de contratos, sv4 para comparar ese
rastro con los datos actuales del albarán.
"""
from ruesma_comun.obras.codigo import normalizar_codigo_obra

__all__ = ["normalizar_codigo_obra"]
