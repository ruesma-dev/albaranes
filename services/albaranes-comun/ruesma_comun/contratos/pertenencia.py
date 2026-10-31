# ruesma_comun/contratos/pertenencia.py
"""¿Un contrato es del albarán? (F-115, R1).

Una fila de ``albaran_contratos_merge`` es del albarán si su CIF de proveedor
y su código de obra coinciden con los del merge. Se comparan normalizados:
``normalizar_cif`` (``b-123`` ≡ ``B123``) y ``canonizar_codigo_obra``
(``686`` ≡ ``0686``).

- Un lado del CONTRATO vacío (fila legada sin ``cif_proveedor`` o sin
  ``codigo_obra``) no descalifica: no se sabe y se da por bueno.
- Un lado del ALBARÁN vacío sí descalifica: sin proveedor o sin obra el
  albarán no tiene contratos (D2).

Función pura, sin dependencias fuera de comun: la usan sv3 (al enriquecer)
y sv4 (al guardar la cabecera y al pintar la ficha).
"""
from __future__ import annotations

from ruesma_comun.obras import canonizar_codigo_obra
from ruesma_comun.proveedores.identificador import normalizar_cif


def contrato_es_del_albaran(
    *,
    contrato_cif: str | None,
    contrato_obra: str | None,
    albaran_cif: str | None,
    albaran_obra: str | None,
) -> bool:
    """``True`` si el contrato es del proveedor y de la obra del albarán."""
    cif_albaran = normalizar_cif(albaran_cif)
    obra_albaran = canonizar_codigo_obra(albaran_obra)
    if cif_albaran is None or obra_albaran is None:
        return False
    cif_contrato = normalizar_cif(contrato_cif)
    if cif_contrato is not None and cif_contrato != cif_albaran:
        return False
    obra_contrato = canonizar_codigo_obra(contrato_obra)
    return obra_contrato is None or obra_contrato == obra_albaran
