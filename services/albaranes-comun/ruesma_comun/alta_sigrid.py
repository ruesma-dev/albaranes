# ruesma_comun/alta_sigrid.py
"""Producto genérico de Sigrid de las líneas sin vincular (F-053, R38-R44).

Decisión del humano (2026-10-05): una línea que no casa con el contrato se da
de alta en Sigrid con un producto genérico de la lista blanca de sigrid-api,
**por línea** y según su familia: alquiler de maquinaria → ``QA9999``, medios
auxiliares → ``XA9999``, el resto → ``MA9999``. El administrativo lo cambia
en sv4 antes de aprobar (``albaran_line_valuations.producto_sigrid``; nulo =
por defecto).

El por defecto **no se guarda**: se calcula al leer, en sv4 al pintar y en sv9
al construir la petición, con esta misma función y el mismo mapeo
(``ALTA_SIGRID_PRODUCTO_POR_DEFECTO``, con el mismo valor en los dos).

Funciones puras, sin E/S.
"""
from __future__ import annotations

import json
from collections.abc import Mapping

from ruesma_comun.contratos.familias import familia_efectiva

#: Clave comodín del mapeo: la familia que no tenga clave propia (o ninguna).
CLAVE_COMODIN = "*"

#: Mapeo por defecto (design §7). Sus valores deben estar en la lista blanca
#: ``SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO`` de sigrid-api.
MAPEO_PRODUCTO_POR_DEFECTO: dict[str, str] = {
    "alquiler_maquinaria": "QA9999",
    "medios_auxiliares": "XA9999",
    CLAVE_COMODIN: "MA9999",
}

#: El mismo mapeo como texto, para el defecto de los ``settings``.
MAPEO_PRODUCTO_POR_DEFECTO_TEXTO = json.dumps(MAPEO_PRODUCTO_POR_DEFECTO)

#: Nombre legible de cada genérico (para sv4). Sin nombre, se enseña el código.
NOMBRES_PRODUCTO: dict[str, str] = {
    "MA9999": "Suministro de materiales",
    "QA9999": "Alquiler de maquinaria",
    "XA9999": "Alquiler de medios auxiliares",
}


def leer_mapeo(texto: str) -> dict[str, str]:
    """Lee ``ALTA_SIGRID_PRODUCTO_POR_DEFECTO`` (R44).

    Debe ser un objeto JSON cuyos valores sean textos no vacíos y que tenga
    la clave ``*``. Si no, ``ValueError`` con el motivo: sv4 y sv9 no deben
    arrancar con un mapeo roto (un producto vacío acabaría en un 400 de
    sigrid-api en cada alta).
    """
    if not isinstance(texto, str):
        # ValueError y no TypeError a propósito (R44): los validadores de
        # pydantic-settings solo convierten ValueError en error de arranque.
        raise ValueError("ALTA_SIGRID_PRODUCTO_POR_DEFECTO debe ser un texto JSON")  # noqa: TRY004
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"ALTA_SIGRID_PRODUCTO_POR_DEFECTO no es JSON válido: {exc}"
        ) from exc
    if not isinstance(datos, dict):
        raise ValueError("ALTA_SIGRID_PRODUCTO_POR_DEFECTO debe ser un objeto JSON")  # noqa: TRY004
    for clave, valor in datos.items():
        if not isinstance(valor, str) or not valor.strip():
            raise ValueError(
                f"ALTA_SIGRID_PRODUCTO_POR_DEFECTO: el producto de {clave!r} "
                "debe ser un texto no vacío"
            )
    if CLAVE_COMODIN not in datos:
        raise ValueError(
            f"ALTA_SIGRID_PRODUCTO_POR_DEFECTO debe tener la clave {CLAVE_COMODIN!r}"
        )
    return dict(datos)


def productos_admitidos(mapeo: Mapping[str, str]) -> frozenset[str]:
    """Productos que se pueden elegir o mandar: los valores del mapeo."""
    return frozenset(mapeo.values())


def producto_efectivo(
    elegido: str | None,
    tipo_familia_linea: str | None,
    clasificacion: object,
    mapeo: Mapping[str, str],
) -> str:
    """Producto con el que se da de alta una línea sin vincular (R38, R40).

    El elegido en sv4 si lo hay; si no, el del mapeo para la familia efectiva
    de la línea (``familia_efectiva``: la de la línea; si no, la del documento
    salvo mixto), o el de ``*`` si esa familia no tiene clave o no hay
    familia. ``clasificacion`` es la del documento (objeto o diccionario con
    ``familia`` y ``mixto``) o ``None``.
    """
    if elegido is not None and elegido.strip():
        return elegido.strip()
    familia = familia_efectiva(tipo_familia_linea, clasificacion)
    if familia is not None and familia in mapeo:
        return mapeo[familia]
    return mapeo[CLAVE_COMODIN]


def nombre_producto(codigo: str) -> str:
    """Nombre legible del producto o, si no se conoce, el propio código."""
    return NOMBRES_PRODUCTO.get(codigo, codigo)
