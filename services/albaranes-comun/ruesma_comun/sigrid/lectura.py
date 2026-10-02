# ruesma_comun/sigrid/lectura.py
"""``truncated`` nunca en silencio y paginación ``OFFSET/FETCH`` (F-052).

sigrid-api corta cada respuesta de ``/api/sql/read`` en ``max_rows`` y lo
avisa con ``truncated=true`` (``azure-apps/sigrid_api.md`` §6.3). Durante
meses ningún cliente lo miró: la lista de proveedores de una obra llegaba
cortada a 1.000 filas y el resolver de sv3 concluía «nadie casa».

Aquí vive lo que es igual para todos los clientes, sin HTTP ni BBDD:

- :class:`PoliticaTruncado`: cada consulta declara si tolera un truncado
  (usa las filas y deja WARNING) o no (excepción).
- :func:`comprobar_truncado`: aplica esa política a una respuesta.
- :func:`con_paginacion`: añade ``OFFSET ? ROWS FETCH NEXT ? ROWS ONLY``
  a una SQL que ya trae ``ORDER BY`` (sin orden estable, paginar repite o
  pierde filas: se rechaza).
- :func:`leer_paginado`: encadena páginas hasta una incompleta, con tope.
- :data:`MAX_FILAS_POR_PETICION` y :data:`PAGINA_MAXIMA`: el ``max_rows``
  más alto que admite sigrid-api y la página que le corresponde.

La SQL de cada servicio NO se comparte (decisión D2 de F-052).
"""
from __future__ import annotations

import logging
import re
from collections.abc import Callable
from enum import Enum
from typing import Any

_RE_ORDER_BY = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)

_SUFIJO_PAGINACION = "OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"

#: Filas que sigrid-api acepta como ``max_rows`` en una petición: su
#: ``MAX_ALLOWED_ROWS`` en la instancia desplegada (leído en Azure el
#: 2026-09-30; ``azure-apps/sigrid_api.md`` §4.1). El 1.000 que cortaba las
#: listas era el ``max_rows`` por defecto del cliente de sv3, no un tope de
#: sigrid-api. Es un techo, no un objetivo: lo que acota una lectura es su
#: ``timeout_s`` (por debajo del corte de 230 s del balanceador).
MAX_FILAS_POR_PETICION = 500_000

#: Mayor página con la que ``max_rows = pagina + 1`` (así se distingue una
#: página llena de una truncada) no pasa de :data:`MAX_FILAS_POR_PETICION`.
PAGINA_MAXIMA = MAX_FILAS_POR_PETICION - 1


class PoliticaTruncado(Enum):
    """Qué hacer si sigrid-api devuelve ``truncated=true``."""

    TOLERA = "tolera"
    NO_TOLERA = "no_tolera"


class SigridRespuestaTruncada(RuntimeError):
    """Respuesta incompleta de sigrid-api en una consulta que no lo tolera.

    Hereda de ``RuntimeError`` a propósito: los ``except Exception`` que
    ya envuelven las consultas la tratan como un fallo de consulta, que es
    lo que es (nunca como «no hay datos»).
    """

    def __init__(self, etiqueta: str, filas: int, detalle: str = "") -> None:
        self.etiqueta = etiqueta
        self.filas = filas
        mensaje = (
            f"sigrid-api devolvió una respuesta truncada [{etiqueta}]: "
            f"{filas} filas recibidas"
        )
        if detalle:
            mensaje = f"{mensaje} ({detalle})"
        super().__init__(mensaje)


def _validar_politica(politica: Any) -> PoliticaTruncado:
    if not isinstance(politica, PoliticaTruncado):
        raise TypeError(
            "politica debe ser un PoliticaTruncado (TOLERA o NO_TOLERA), "
            f"no {politica!r}"
        )
    return politica


def _truncado(
    *,
    politica: PoliticaTruncado,
    etiqueta: str,
    filas: int,
    detalle: str,
    logger: logging.Logger,
) -> None:
    """Aplica la política a un truncado ya detectado."""
    if politica is PoliticaTruncado.NO_TOLERA:
        raise SigridRespuestaTruncada(etiqueta, filas, detalle)
    logger.warning(
        "[sigrid] respuesta truncada tolerada [%s]: %s filas recibidas (%s); "
        "se usan tal cual.",
        etiqueta,
        filas,
        detalle,
    )


def comprobar_truncado(
    body: dict,
    *,
    politica: PoliticaTruncado,
    etiqueta: str,
    logger: logging.Logger,
) -> None:
    """Aplica ``politica`` a una respuesta de ``/api/sql/read``.

    Sin ``truncated`` (o a ``false``) no hace nada. Con ``truncated=true``:
    ``NO_TOLERA`` lanza :class:`SigridRespuestaTruncada` con ``etiqueta``
    y el número de filas recibidas; ``TOLERA`` registra un WARNING con la
    etiqueta y deja seguir. Una política que no sea
    :class:`PoliticaTruncado` es un error de programación y falla siempre,
    trunque o no la respuesta.
    """
    politica = _validar_politica(politica)
    if not body.get("truncated"):
        return
    filas = len(body.get("rows") or [])
    _truncado(
        politica=politica,
        etiqueta=etiqueta,
        filas=filas,
        detalle="se alcanzó max_rows",
        logger=logger,
    )


def con_paginacion(sql: str) -> str:
    """Añade ``OFFSET ? ROWS FETCH NEXT ? ROWS ONLY`` al final de ``sql``.

    Los dos ``?`` nuevos son, en este orden, el desplazamiento y el tamaño
    de página. ``ValueError`` si la SQL no trae ``ORDER BY``: SQL Server
    lo exige para ``OFFSET`` y, sin un orden estable, las páginas repiten
    o pierden filas.
    """
    if not _RE_ORDER_BY.search(sql or ""):
        raise ValueError(
            "con_paginacion: la SQL no tiene ORDER BY; paginar sin un orden "
            "estable repite o pierde filas"
        )
    return f"{sql.rstrip()}\n{_SUFIJO_PAGINACION}"


def leer_paginado(
    leer_pagina: Callable[[int, int], tuple[list, list, bool]],
    *,
    pagina: int,
    max_paginas: int,
    etiqueta: str,
    politica: PoliticaTruncado,
    logger: logging.Logger,
) -> tuple[list[str], list[list]]:
    """Encadena páginas hasta la primera incompleta.

    ``leer_pagina(offset, tamano)`` devuelve ``(columnas, filas,
    truncated)`` de una página. Se sigue mientras la página venga llena
    (``len(filas) == pagina``). El llamante pide cada página con
    ``max_rows = pagina + 1``, así que una página marcada ``truncated`` es
    una anomalía y se trata con ``politica``. Si se leen ``max_paginas``
    páginas llenas, puede haber más: ``NO_TOLERA`` lanza
    :class:`SigridRespuestaTruncada` y ``TOLERA`` devuelve lo leído con
    WARNING. Una página con MÁS filas que las pedidas es siempre un error
    (``RuntimeError``, con cualquier política): aceptarla repetiría filas.
    ``pagina`` va de 1 a :data:`PAGINA_MAXIMA` (``ValueError`` si no).
    """
    politica = _validar_politica(politica)
    if pagina < 1:
        raise ValueError(f"leer_paginado: pagina debe ser >= 1, no {pagina}")
    if pagina > PAGINA_MAXIMA:
        raise ValueError(
            f"leer_paginado: pagina {pagina} pediría max_rows={pagina + 1}, por "
            f"encima del tope de sigrid-api ({MAX_FILAS_POR_PETICION}); "
            f"máximo {PAGINA_MAXIMA}"
        )
    if max_paginas < 1:
        raise ValueError(
            f"leer_paginado: max_paginas debe ser >= 1, no {max_paginas}"
        )
    columnas: list[str] = []
    filas: list[list] = []
    for n in range(max_paginas):
        cols, trozo, truncated = leer_pagina(n * pagina, pagina)
        if len(trozo) > pagina:
            # La fuente no respetó el tamaño (FETCH no aplicado): la
            # siguiente página repetiría filas. Nunca se acepta.
            raise RuntimeError(
                f"sigrid-api devolvió una página de más filas que las pedidas "
                f"[{etiqueta}]: página {n + 1}, {len(trozo)} filas para un "
                f"tamaño de {pagina}"
            )
        if n == 0:
            columnas = list(cols)
        filas.extend(trozo)
        if truncated:
            _truncado(
                politica=politica,
                etiqueta=etiqueta,
                filas=len(filas),
                detalle=f"página {n + 1} marcada truncated",
                logger=logger,
            )
        if len(trozo) < pagina:
            return columnas, filas
    _truncado(
        politica=politica,
        etiqueta=etiqueta,
        filas=len(filas),
        detalle=f"tope de {max_paginas} páginas de {pagina} filas",
        logger=logger,
    )
    return columnas, filas
