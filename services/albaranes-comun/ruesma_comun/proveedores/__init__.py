# ruesma_comun/proveedores/__init__.py
"""Identificador fiscal de los proveedores (F-062 · R1, R2).

Una sola regla del CIF/NIF/NIE para todos los servicios: hoy la importa
sv3 (red de proveedor); sv4 y F-055 la querrán al elegir o verificar un
proveedor.

F-063: la lista de CIF propios (Construcciones Ruesma), que nunca son el
proveedor de un albarán.
"""
from ruesma_comun.proveedores.identificador import (
    identificador_fiscal_valido,
    normalizar_cif,
)
from ruesma_comun.proveedores.propios import (
    CIFS_PROPIOS_POR_DEFECTO,
    cifs_propios,
    es_cif_propio,
)

__all__ = [
    "CIFS_PROPIOS_POR_DEFECTO",
    "cifs_propios",
    "es_cif_propio",
    "identificador_fiscal_valido",
    "normalizar_cif",
]
