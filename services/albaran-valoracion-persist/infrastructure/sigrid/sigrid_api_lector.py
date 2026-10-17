# infrastructure/sigrid/sigrid_api_lector.py
"""Lector de solo lectura de sigrid-api para sv6 (F-076 R18).

Es el ``LectorSql`` de ``ruesma_comun.sigrid``: recibe la SQL, sus parámetros,
la etiqueta, la política de truncado y el ``max_rows`` y devuelve
``(columnas, filas)``. Solo usa ``POST /api/sql/read`` (sv6 nunca escribe en
Sigrid: eso es de sv9).

- Reintentos con tenacity y espera exponencial ante fallos transitorios (5xx,
  tiempo agotado, conexión): 3 intentos por defecto. Un 4xx, ``ok=false`` o una
  respuesta que no es JSON no se reintentan: :class:`SigridLecturaError`.
- La política se aplica con ``comprobar_truncado``: con ``NO_TOLERA``,
  ``truncated=true`` lanza ``SigridRespuestaTruncada``.
- Sin secretos en el log: ni la clave (cabecera ``x-functions-key``) ni el
  cuerpo de la respuesta; solo etiqueta, estado HTTP y número de filas.
"""
from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from ruesma_comun.sigrid import PoliticaTruncado, comprobar_truncado
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

_LOG = "[sv6][sigrid-api]"

RUTA_SQL_READ = "/api/sql/read"
INTENTOS_POR_DEFECTO = 3
ESPERA_BASE_S = 1.0
ESPERA_MAX_S = 10.0


class SigridLecturaError(RuntimeError):
    """Una lectura de ``sql/read`` que no se pudo hacer."""


class _Transitorio(Exception):
    """5xx: se reintenta."""

    def __init__(self, estado: int) -> None:
        super().__init__(f"HTTP {estado}")
        self.estado = estado


_EXCEPCIONES_TRANSITORIAS = (_Transitorio, httpx.TimeoutException, httpx.TransportError)


class SigridApiLector:
    """``LectorSql`` sobre ``POST /api/sql/read`` (F-076 R18)."""

    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        timeout_s: float = 30.0,
        intentos: int = INTENTOS_POR_DEFECTO,
        espera_base_s: float = ESPERA_BASE_S,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not (base_url or "").strip():
            raise ValueError("SigridApiLector requiere base_url")
        if not (function_key or "").strip():
            raise ValueError("SigridApiLector requiere la clave de sigrid-api")
        if not (database or "").strip():
            raise ValueError("SigridApiLector requiere database")
        self._base_url = base_url.strip().rstrip("/")
        self._clave = function_key.strip()
        self._database = database.strip()
        self._timeout_s = float(timeout_s)
        self._intentos = max(1, int(intentos))
        self._espera_base_s = float(espera_base_s)
        self._transport = transport
        logger.info(
            "%s base_url=%s database=%s timeout=%ss intentos=%s",
            _LOG, self._base_url, self._database, self._timeout_s, self._intentos,
        )

    def __repr__(self) -> str:  # sin la clave
        return f"SigridApiLector(base_url={self._base_url!r}, database={self._database!r})"

    def __call__(
        self,
        sql: str,
        parametros: list[Any],
        etiqueta: str,
        politica: PoliticaTruncado,
        max_rows: int,
    ) -> tuple[list[str], list[list[Any]]]:
        cuerpo = {
            "database": self._database,
            "sql": sql,
            "parameters": list(parametros),
            "timeout_seconds": int(self._timeout_s),
            "max_rows": int(max_rows),
        }
        try:
            respuesta = self._post_con_reintentos(cuerpo, etiqueta)
        except _EXCEPCIONES_TRANSITORIAS as exc:
            raise SigridLecturaError(
                f"sql/read [{etiqueta}] sin respuesta tras {self._intentos} intentos: {type(exc).__name__}"
            ) from exc
        if respuesta.status_code != 200:
            raise SigridLecturaError(f"sql/read [{etiqueta}] HTTP {respuesta.status_code}")
        try:
            datos = respuesta.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise SigridLecturaError(f"sql/read [{etiqueta}] respuesta no JSON") from exc
        if not isinstance(datos, dict) or datos.get("ok") is not True:
            raise SigridLecturaError(f"sql/read [{etiqueta}] respuesta no válida (ok distinto de true)")
        comprobar_truncado(datos, politica=politica, etiqueta=etiqueta, logger=logger)
        columnas = list(datos.get("columns") or [])
        filas = list(datos.get("rows") or [])
        logger.info("%s [%s] filas=%s", _LOG, etiqueta, len(filas))
        return columnas, filas

    def _post_con_reintentos(self, cuerpo: dict[str, Any], etiqueta: str) -> httpx.Response:
        cabeceras = {"x-functions-key": self._clave, "Content-Type": "application/json"}

        def intento() -> httpx.Response:
            with httpx.Client(timeout=self._timeout_s, transport=self._transport) as cliente:
                respuesta = cliente.post(f"{self._base_url}{RUTA_SQL_READ}", json=cuerpo, headers=cabeceras)
            logger.info("%s [%s] POST %s -> %s", _LOG, etiqueta, RUTA_SQL_READ, respuesta.status_code)
            if respuesta.status_code >= 500:
                raise _Transitorio(respuesta.status_code)
            return respuesta

        reintentos = Retrying(
            stop=stop_after_attempt(self._intentos),
            wait=wait_exponential(multiplier=self._espera_base_s, max=ESPERA_MAX_S),
            retry=retry_if_exception_type(_EXCEPCIONES_TRANSITORIAS),
            before_sleep=lambda estado: logger.warning(
                "%s [%s] intento %s fallido (%s); reintento", _LOG, etiqueta,
                estado.attempt_number, type(estado.outcome.exception()).__name__,
            ),
            reraise=True,
        )
        return reintentos(intento)
