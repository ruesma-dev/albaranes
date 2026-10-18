# application/services/empresas_cliente.py
"""Empresas del CLIENTE que leen IA1 e IA2 (F-064 · R1, R3, R4).

El cliente de todos los albaranes es la constructora, y su CIF va impreso en
ellos (casillas «Cliente», «C.I.F./D.N.I.» del bloque del cliente...). El
2026-10-08 IA1 leyó ese CIF como el del proveedor en un albarán de FEYMACO:
la única casilla rotulada CIF era la del cliente. F-064 le dice a la IA
cuáles son las empresas del cliente para que las ignore y busque al emisor.

Una sola fuente, la de F-063: ``ruesma_comun.proveedores``
(``CIFS_PROPIOS_POR_DEFECTO`` y ``cifs_propios``), ampliada con la variable
``CIFS_PROPIOS`` de sv2, que solo AMPLÍA. Así lo que la IA ignora y lo que
sv3 descarta son siempre las mismas empresas. Ningún YAML las escribe a mano:
el task de fase 1 lleva el marcador ``{empresas_cliente}`` y
``AlbaranExtractionService._render_task_fase_1`` lo sustituye por el bloque
de ``render_empresas_cliente``.

Puro: sin I/O; solo importa ``ruesma_comun.proveedores``.
"""
from __future__ import annotations

from dataclasses import dataclass

from ruesma_comun.proveedores import (
    CIFS_PROPIOS_POR_DEFECTO,
    cifs_propios,
    normalizar_cif,
)

#: Marcador del task de fase 1 que sustituye el bloque.
MARCADOR_EMPRESAS_CLIENTE = "{empresas_cliente}"

#: Primera línea del bloque (fija).
CABECERA_BLOQUE = "EMPRESAS DEL CLIENTE (CIF — razón social):"

#: Texto de una empresa sin razón social (las añadidas por configuración).
SIN_RAZON_SOCIAL = "empresa del grupo, sin razón social configurada"


@dataclass(frozen=True)
class EmpresaCliente:
    """Una empresa del cliente: CIF normalizado y razón social, si se sabe."""

    cif: str
    razon_social: str | None


def empresas_cliente(extra: str | None = None) -> tuple[EmpresaCliente, ...]:
    """Las empresas del cliente: las de serie y después las de ``extra``.

    Las de serie (``CIFS_PROPIOS_POR_DEFECTO``), en el orden del diccionario
    y con su razón social. Después, las que ``cifs_propios(extra)`` añade y no
    son de serie, ordenadas, sin razón social. El diccionario se lee en cada
    llamada (R4): una entrada nueva en comun llega sin tocar sv2.
    """
    de_serie: list[EmpresaCliente] = []
    vistos: set[str] = set()
    for cif, razon_social in CIFS_PROPIOS_POR_DEFECTO.items():
        normalizado = normalizar_cif(cif)
        if normalizado is None or normalizado in vistos:
            continue
        vistos.add(normalizado)
        de_serie.append(EmpresaCliente(normalizado, razon_social or None))

    anadidos = {normalizar_cif(cif) for cif in cifs_propios(extra)}
    anadidos.discard(None)
    anadidas = [EmpresaCliente(cif, None) for cif in sorted(anadidos - vistos)]
    return (*de_serie, *anadidas)


def render_empresas_cliente(empresas: tuple[EmpresaCliente, ...] | list[EmpresaCliente]) -> str:
    """Bloque determinista: cabecera fija y una línea ``CIF — razón social``."""
    lineas = [CABECERA_BLOQUE]
    lineas.extend(
        f"  - {empresa.cif} — {empresa.razon_social or SIN_RAZON_SOCIAL}"
        for empresa in empresas
    )
    if not empresas:
        lineas.append("  - (ninguna)")
    return "\n".join(lineas)
