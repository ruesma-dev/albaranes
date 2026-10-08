# domain/models/header_resolution_models.py
"""Modelos del HeaderResolverService (resolucion determinista de
cabecera: obra_codigo / proveedor_cif por coincidencia de texto y, desde
jul 2026, por familia de producto + proveedores con contrato en la obra)."""
from __future__ import annotations

from dataclasses import dataclass

# ------------------------------------------------------------------ #
# Marcas de la red de proveedor (F-002, F-062, F-063). Las escribe el
# repositorio y las redacta el resolver: viven en el dominio para que
# ninguna de las dos capas importe a la otra.
# ------------------------------------------------------------------ #
#: Motivo de revision: el CIF leido no existe en Sigrid y no se corrigio.
MOTIVO_PROVEEDOR_NO_CASA = "proveedor_cif_no_casa:"
#: Motivo de revision: sv3 aplico un candidato claro (F-062 · R7). Sella
#: ``<leido>><aplicado>`` para poder retirarlo sin estado extra (R15).
MOTIVO_PROVEEDOR_CORREGIDO = "proveedor_cif_corregido:"
#: Prefijo PROPIO de la nota de la correccion (F-062 · D6): la red borra
#: por prefijo ``[AVISO] Proveedor`` al empezar cada pasada y con ese
#: prefijo la nota desapareceria en la primera re-pasada.
NOTA_PROVEEDOR_CORREGIDO_PREFIJO = "[CORREGIDO] Proveedor"
#: Motivo de revision: la IA leyo un CIF PROPIO (el del cliente, Ruesma)
#: como CIF del proveedor y sv3 lo descarto (F-063 · R4). Sella el CIF.
MOTIVO_PROVEEDOR_CIF_PROPIO = "proveedor_cif_propio:"
#: Prefijo PROPIO de su nota (F-063 · D1, R10): con ``[AVISO] Proveedor``
#: la borraria la propia pasada en cuanto se resuelve por nombre.
NOTA_CIF_PROPIO_PREFIJO = "[AVISO] CIF del cliente"


@dataclass(frozen=True)
class MergeHeaderForResolution:
    """Snapshot de los campos de cabecera del merge que intervienen en
    la resolucion determinista. Lo lee el repositorio."""

    obra_codigo: str | None
    obra_nombre: str | None
    obra_direccion: str | None
    proveedor_cif: str | None
    proveedor_nombre: str | None
    #: (F-062 · R13) ``manual`` = lo fijo el revisor: la red no lo pisa.
    proveedor_cif_origen: str | None = None


@dataclass(frozen=True)
class ProveedorObraResumen:
    """Resumen de UN proveedor con contrato en una obra: su identidad
    canonica y el TEXTO agregado de sus contratos en esa obra (nombres de
    contrato + descripciones de linea + codigos de producto), para que el
    resolver detecte la familia (hormigon, residuos, mortero...) con las
    mismas reglas que el selector de contratos.

    Lo construye ``SigridApiContratoClient.fetch_contratos_resumen_por_obra``.
    """

    cif: str
    nombre: str | None
    codigos_contratos: tuple[str, ...]
    texto: str
