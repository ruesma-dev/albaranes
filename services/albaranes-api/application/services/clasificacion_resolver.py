# application/services/clasificacion_resolver.py
"""Consolida la clasificacion del albaran que decidio la IA (F-043).

Sustituye al `tipologia_resolver`, y la diferencia es toda la feature: aquel
DECIDIA la familia con reglas deterministas (codigo LER, familia dominante
de las lineas, override por CIF) y con esa decision elegia el prompt de fase
2, asi que la regla acotaba lo que la IA podia concluir. Este NO decide
nada. La familia del documento es EXACTAMENTE la que dijo la IA (R12).

Lo unico que hace este modulo, y esta escrito para que se vea:

1. Elige la fuente: el bloque de fase 2 si existe, si no el de fase 1 (R16).
2. Normaliza la familia contra el catalogo de familias de DOCUMENTO.
3. Sella el `origen` (`ia1` / `ia2` / `ausente`): es el unico campo del
   bloque que no le pertenece a la IA.
4. Deja constancia de los dos huecos posibles, sin taparlos:
   - familia fuera de catalogo (R10): se registra `generico`, el valor
     original se conserva DENTRO del motivo y la confianza baja a 0 para
     que el umbral de sv3 mande el documento a revision.
   - sin bloque (R11): `generico`, confianza 0, motivo
     `ia_sin_clasificacion`, origen `ausente`.

Lo que este modulo tiene PROHIBIDO hacer, por decision expresa del humano
del 2026-08-25: inferir o forzar la familia a partir del codigo LER, de la
familia de producto, de palabras del texto o del CIF del proveedor. No
importa `ruesma_comun.ler`, ni funciones de texto, ni mira la cabecera. Si
la IA clasifica mal, se arregla el PROMPT (R13).

Funcion PURA: sin I/O, sin red, sin BBDD.
"""
from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from ruesma_comun.contratos import ClasificacionAlbaran
from ruesma_comun.contratos.clasificacion import (
    MOTIVO_SIN_CLASIFICACION,
    ORIGEN_AUSENTE,
    ORIGEN_IA1,
    ORIGEN_IA2,
)
from ruesma_comun.contratos.familias import familias_documento

logger = logging.getLogger(__name__)

_LOG = "[clasificacion]"

FAMILIA_POR_DEFECTO = "generico"

CONFIANZA_MINIMA = 0.0
CONFIANZA_MAXIMA = 100.0


def _campo(bloque: Any, nombre: str) -> Any:
    """Lee un campo venga el bloque como dict o como contrato validado."""
    if isinstance(bloque, Mapping):
        return bloque.get(nombre)
    return getattr(bloque, nombre, None)


def _bloque_de(data: Any) -> Any | None:
    """Extrae el bloque `clasificacion` de un `data` de fase 1 o de fase 2.

    Acepta tambien el envoltorio de fase 2 (`{documento_revisado, ...}`):
    pasar el nivel equivocado degradaria a la clasificacion de fase 1 sin
    que nadie lo notase, y ese fallo no se ve en ningun log.
    """
    if not isinstance(data, Mapping):
        return None
    bloque = data.get("clasificacion")
    if bloque is None:
        revisado = data.get("documento_revisado")
        if isinstance(revisado, Mapping):
            bloque = revisado.get("clasificacion")
    if bloque is None:
        return None
    familia = _texto(_campo(bloque, "familia"))
    # Un bloque con la familia en blanco es una ausencia, no una familia
    # vacia: lo que no puede salir de aqui es `familia=''`.
    return bloque if familia else None


def _texto(valor: Any) -> str:
    return str(valor).strip() if valor is not None else ""


def _confianza(valor: Any) -> float:
    """Acota la confianza al rango del contrato (0-100).

    Un valor imposible (150, 'alta', null) no puede tumbar la validacion del
    bloque entero: se perderia la familia, que es el dato que importa.
    """
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return CONFIANZA_MINIMA
    return max(CONFIANZA_MINIMA, min(CONFIANZA_MAXIMA, numero))


def _secundarias(valor: Any) -> list[str]:
    if not isinstance(valor, (list, tuple)):
        return []
    return [f.strip().lower() for f in (_texto(x) for x in valor) if f]


def _sin_clasificacion() -> ClasificacionAlbaran:
    """R11: se registra el hueco, no se adivina la familia."""
    return ClasificacionAlbaran(
        familia=FAMILIA_POR_DEFECTO,
        confianza_pct=CONFIANZA_MINIMA,
        motivo=MOTIVO_SIN_CLASIFICACION,
        origen=ORIGEN_AUSENTE,
    )


def resolver_clasificacion(
    data_fase1: Mapping[str, Any] | None,
    data_fase2: Mapping[str, Any] | None = None,
) -> ClasificacionAlbaran:
    """Clasificacion consolidada del DOCUMENTO. Nunca devuelve ``None``."""
    bloque = _bloque_de(data_fase2)
    origen = ORIGEN_IA2
    if bloque is None:
        bloque = _bloque_de(data_fase1)
        origen = ORIGEN_IA1
    if bloque is None:
        resultado = _sin_clasificacion()
        logger.info(
            "%s familia=%s origen=%s motivo=%s",
            _LOG, resultado.familia, resultado.origen, resultado.motivo,
        )
        return resultado

    dicha = _texto(_campo(bloque, "familia"))
    familia = dicha.lower()
    motivo = _texto(_campo(bloque, "motivo"))
    confianza = _confianza(_campo(bloque, "confianza_pct"))

    if familia not in familias_documento():
        # R10: se conserva lo que dijo la IA dentro del motivo y se manda a
        # revision (confianza 0). PROHIBIDO deducir la familia de otra
        # senal: si la IA se inventa la etiqueta, se arregla el prompt.
        motivo = (
            f"familia fuera de catalogo: '{dicha}'"
            + (f"; motivo de la IA: {motivo}" if motivo else "")
        )
        familia = FAMILIA_POR_DEFECTO
        confianza = CONFIANZA_MINIMA

    resultado = ClasificacionAlbaran(
        familia=familia,
        confianza_pct=confianza,
        motivo=motivo,
        mixto=bool(_campo(bloque, "mixto")),
        familias_secundarias=_secundarias(
            _campo(bloque, "familias_secundarias")
        ),
        origen=origen,
    )
    logger.info(
        "%s familia=%s confianza=%.1f origen=%s mixto=%s secundarias=%s",
        _LOG, resultado.familia, resultado.confianza_pct, resultado.origen,
        resultado.mixto, resultado.familias_secundarias or "-",
    )
    return resultado
