# ruesma_comun/proveedores/propios.py
"""CIF propios: los de Construcciones Ruesma, que nunca es el proveedor.

F-063 (R1, R2). Ruesma es el CLIENTE de todos los albaranes que procesa
el pipeline, y su CIF va impreso en ellos. El 2026-10-08 la IA leyó
A81873903 (el de Construcciones Ruesma) como CIF del proveedor de un
albarán de FEYMACO; sv3 lo dio por bueno porque existe en Sigrid. Un CIF
propio en el campo de proveedor es SIEMPRE una lectura equivocada.

Puro y sin dependencias: hoy lo usa sv3; sv2 y sv4 pueden importarlo.
"""
from __future__ import annotations

import re

from ruesma_comun.proveedores.identificador import normalizar_cif

#: CIF propios que vienen de serie, con el nombre que se pinta en la nota.
#: La configuración (``CIFS_PROPIOS`` en sv3) solo AMPLÍA esta lista:
#: quitar el de Construcciones Ruesma reabriría la incidencia.
CIFS_PROPIOS_POR_DEFECTO: dict[str, str] = {
    "A81873903": "Construcciones Ruesma",
}

#: Separadores admitidos en la variable de configuración.
_SEPARADORES = re.compile(r"[,;\s]+")


def cifs_propios(extra: str | None) -> frozenset[str]:
    """Los CIF propios normalizados: los de serie MÁS los de ``extra``.

    ``extra`` es texto separado por comas, punto y coma o espacios; vacío
    o ``None`` ⇒ solo los de serie.
    """
    anadidos = {
        normalizar_cif(trozo) for trozo in _SEPARADORES.split(extra or "")
    }
    anadidos.discard(None)
    return frozenset(CIFS_PROPIOS_POR_DEFECTO) | frozenset(anadidos)


def es_cif_propio(valor: str | None, propios: frozenset[str]) -> bool:
    """``True`` solo si el CIF normalizado de ``valor`` está en ``propios``."""
    return normalizar_cif(valor) in propios
