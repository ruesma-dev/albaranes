# ruesma_comun/proveedores/__init__.py
"""Identificador fiscal de los proveedores (F-062 · R1, R2).

Una sola regla del CIF/NIF/NIE para todos los servicios: hoy la importa
sv3 (red de proveedor); sv4 y F-055 la querrán al elegir o verificar un
proveedor.
"""
from ruesma_comun.proveedores.identificador import (
    identificador_fiscal_valido,
    normalizar_cif,
)

__all__ = ["identificador_fiscal_valido", "normalizar_cif"]
