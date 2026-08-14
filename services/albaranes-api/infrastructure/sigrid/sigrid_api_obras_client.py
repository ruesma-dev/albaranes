# infrastructure/sigrid/sigrid_api_obras_client.py
"""Lista de obras de Sigrid para el prompt de IA1 (sv2 -> sigrid-api).

sigrid-api es el UNICO acceso al SQL Server de Sigrid (nadie se conecta
por SQL directo). sv2 la consulta en solo lectura, una vez por replica y
TTL (la cache la pone ``ObrasActivasCacheTTL``).

Por que sv2 llama a sigrid-api en vez de pedirselo a sv3 (decision D1 de
la spec): en Azure ``ca-sv3-persistencia`` es un worker KEDA SIN ingress,
asi que sv2 no puede llamarle; y una cache en Blob mantenida por sv3 no
sirve porque sv3 corre DESPUES de sv2 en la cadena.

Best-effort: cualquier fallo devuelve ``None`` (lista no disponible) y la
extraccion sigue como siempre. Nunca propaga la excepcion.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from domain.ports.obras_activas_provider import ObraActiva

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[obras-activas][sigrid-client]"

#: MISMA query de obras que usa sv3 para su reverse lookup, recortada a
#: lo que el prompt necesita (codigo + nombre). SIN DISTINCT: ``obr.res``
#: es ntext y SQL Server no admite DISTINCT sobre ntext (la duplicidad se
#: resuelve en Python, ver ``filas_a_obras``).
_SQL_OBRAS = """\
SELECT
    con.cod        AS codigo_obra,
    obr.res        AS nombre_obra
FROM obr
JOIN con ON obr.ide = con.ide
WHERE con.cod IS NOT NULL
"""

#: Filas por peticion. sigrid-api esta configurado a 10.000 (dato
#: corregido por el humano el 2026-08-13; ``docs/ARCHITECTURE.md`` decia
#: 1.000). Si llegan exactamente estas, se avisa de posible truncado.
MAX_ROWS_POR_DEFECTO = 10000

#: Corte PROVISIONAL de «obra activa» (D2): solo obras con codigo de 4
#: digitos y mayor que este valor. NO es la definicion de negocio, que
#: sigue pendiente; con 0 el corte por valor queda desactivado.
COD_MIN_POR_DEFECTO = 450


def filas_a_obras(columnas: list[str], filas: list[list[Any]]) -> list[ObraActiva]:
    """Convierte la respuesta de sigrid-api en obras, sin duplicados.

    ``con.cod`` aparece varias veces en Sigrid (varias filas por obra):
    el prompt no puede listar la misma obra dos veces, asi que se
    conserva la PRIMERA aparicion de cada codigo.
    """
    indice_codigo = columnas.index("codigo_obra") if "codigo_obra" in columnas else 0
    indice_nombre = columnas.index("nombre_obra") if "nombre_obra" in columnas else 1
    vistos: set[str] = set()
    obras: list[ObraActiva] = []
    for fila in filas:
        codigo = str(fila[indice_codigo] or "").strip()
        if not codigo or codigo in vistos:
            continue
        vistos.add(codigo)
        nombre_bruto = (
            fila[indice_nombre] if len(fila) > indice_nombre else None
        )
        nombre = str(nombre_bruto).strip() if nombre_bruto is not None else ""
        obras.append(ObraActiva(codigo=codigo, nombre=nombre or None))
    return obras


def filtrar_obras_activas(
    obras: list[ObraActiva], *, cod_min: int,
) -> list[ObraActiva]:
    """Aplica el criterio PROVISIONAL de «obra activa» (R1-bis).

    Se conservan SOLO las obras cuyo codigo sea de 4 digitos numericos y
    cuyo valor sea ESTRICTAMENTE mayor que ``cod_min`` (0450 por
    defecto). El filtro va en Python, no en la query, para que retirarlo
    cuando negocio defina el criterio real sea un cambio de configuracion
    (``OBRAS_ACTIVAS_COD_MIN=0``) y no de codigo.
    """
    seleccionadas: list[ObraActiva] = []
    for obra in obras:
        codigo = (obra.codigo or "").strip()
        if len(codigo) != 4 or not codigo.isdigit():
            continue
        if int(codigo) <= cod_min:
            continue
        seleccionadas.append(obra)
    return seleccionadas


class SigridApiObrasClient:
    """Adaptador HTTP contra ``sigrid-api`` (cumple ``ObrasActivasProvider``)."""

    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        timeout_s: float = 30.0,
        max_rows: int = MAX_ROWS_POR_DEFECTO,
        cod_min: int = COD_MIN_POR_DEFECTO,
    ) -> None:
        if not base_url:
            raise ValueError("SigridApiObrasClient requiere base_url no vacio")
        if not function_key:
            raise ValueError(
                "SigridApiObrasClient requiere function_key no vacio"
            )
        if not database:
            raise ValueError("SigridApiObrasClient requiere database no vacio")
        self._base_url = base_url.rstrip("/")
        self._function_key = function_key
        self._database = database
        self._timeout_s = float(timeout_s)
        self._max_rows = int(max_rows)
        self._cod_min = int(cod_min)
        logger.info(
            "%s Instanciado. base_url=%s database=%s timeout_s=%s "
            "max_rows=%s cod_min=%s",
            _LOG_PREFIX, self._base_url, self._database, self._timeout_s,
            self._max_rows, self._cod_min,
        )

    def obtener(self) -> list[ObraActiva] | None:
        try:
            columnas, filas = self._consultar()
        except Exception:  # noqa: BLE001 — best-effort: el prompt sigue
            logger.exception(
                "%s no se pudo obtener la lista de obras; la extraccion "
                "sigue sin ella.", _LOG_PREFIX,
            )
            return None

        if len(filas) >= self._max_rows:
            logger.warning(
                "%s llegaron %s filas (= max_rows): la lista PUEDE estar "
                "truncada.", _LOG_PREFIX, len(filas),
            )
        obras = filas_a_obras(columnas, filas)
        activas = filtrar_obras_activas(obras, cod_min=self._cod_min)
        logger.info(
            "%s obras: %s filas -> %s codigos unicos -> %s activas "
            "(cod_min=%s).",
            _LOG_PREFIX, len(filas), len(obras), len(activas), self._cod_min,
        )
        return activas or None

    def _consultar(self) -> tuple[list[str], list[list[Any]]]:
        url = f"{self._base_url}/api/sql/read"
        payload = {
            "database": self._database,
            "sql": _SQL_OBRAS,
            "parameters": [],
            "timeout_seconds": int(self._timeout_s),
            "max_rows": self._max_rows,
        }
        headers = {
            "x-functions-key": self._function_key,
            "Content-Type": "application/json",
        }
        logger.info(
            "%s REQUEST -> POST %s database=%s max_rows=%s",
            _LOG_PREFIX, url, self._database, self._max_rows,
        )
        transport = httpx.HTTPTransport(retries=1)
        with httpx.Client(timeout=self._timeout_s, transport=transport) as client:
            response = client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            raise RuntimeError(
                f"sigrid-api respondio {response.status_code}: "
                f"{(response.text or '')[:300]}"
            )
        body: dict[str, Any] = response.json()
        if not body.get("ok", False):
            raise RuntimeError(f"sigrid-api devolvio ok=false: {body!r}")
        return list(body.get("columns") or []), list(body.get("rows") or [])
