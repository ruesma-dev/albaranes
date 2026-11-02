# infrastructure/clients/http_partida_residuos_client.py
"""Cliente HTTP contra ``POST /v1/albaranes/partida-residuos`` de sv5 (F-111).

Mismo sv5 que la valoración y la conciliación (``VALUATION_API_BASE_URL``).
UNA llamada por documento (R34). Reintentos con tenacity y espera exponencial
ante fallos transitorios (5xx, tiempo agotado, conexión); un 4xx (p. ej. 404:
sv5 desplegado sin el endpoint) o una respuesta que no es la esperada no se
reintenta. Todo fallo sale como :class:`PartidaResiduosError`, que el
asignador convierte en revisión con ``partida_residuos_ia_fallo`` (R26, R33).
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

RUTA_PARTIDA_RESIDUOS = "/v1/albaranes/partida-residuos"
INTENTOS_POR_DEFECTO = 3
ESPERA_BASE_S = 1.0
ESPERA_MAX_S = 10.0


class PartidaResiduosError(RuntimeError):
    """La elección de partida de residuos no se pudo obtener de sv5."""


class _Transitorio(Exception):
    """5xx: se reintenta."""

    def __init__(self, estado: int, cuerpo: str) -> None:
        super().__init__(f"HTTP {estado}: {cuerpo}")
        self.estado = estado


_EXCEPCIONES_TRANSITORIAS = (_Transitorio, httpx.TimeoutException, httpx.TransportError)


class HttpPartidaResiduosClient:
    """``EligePartidaPort`` sobre sv5."""

    def __init__(
        self,
        *,
        base_url: str,
        timeout_s: float,
        intentos: int = INTENTOS_POR_DEFECTO,
        espera_base_s: float = ESPERA_BASE_S,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not (base_url or "").strip():
            raise ValueError("HttpPartidaResiduosClient requiere base_url")
        self._url = base_url.strip().rstrip("/") + RUTA_PARTIDA_RESIDUOS
        self._timeout_s = float(timeout_s)
        self._intentos = max(1, int(intentos))
        self._espera_base_s = float(espera_base_s)
        self._transport = transport

    def elegir(
        self,
        *,
        document_id: str,
        lineas: list[dict[str, Any]],
        candidatas: list[dict[str, Any]],
    ) -> dict[int, str | None]:
        payload = {"document_id": document_id, "lineas": lineas, "candidatas": candidatas}
        logger.info(
            "[partida-residuos-client] POST %s document_id=%s lineas=%s candidatas=%s",
            self._url, document_id, len(lineas), len(candidatas),
        )
        reintentos = Retrying(
            stop=stop_after_attempt(self._intentos),
            wait=wait_exponential(multiplier=self._espera_base_s, max=ESPERA_MAX_S),
            retry=retry_if_exception_type(_EXCEPCIONES_TRANSITORIAS),
            reraise=True,
        )
        try:
            datos = reintentos(self._post, payload)
        except _EXCEPCIONES_TRANSITORIAS as exc:
            raise PartidaResiduosError(f"partida-residuos falló: {exc}") from exc
        return self._elecciones(datos)

    def _post(self, payload: dict[str, Any]) -> Any:
        with httpx.Client(timeout=self._timeout_s, transport=self._transport) as client:
            response = client.post(self._url, json=payload)
        if response.status_code >= 500:
            raise _Transitorio(response.status_code, (response.text or "")[:200])
        if response.status_code >= 400:
            raise PartidaResiduosError(
                f"partida-residuos devolvió {response.status_code}: {(response.text or '')[:200]}"
            )
        try:
            return response.json()
        except ValueError as exc:
            raise PartidaResiduosError("partida-residuos no devolvió JSON") from exc

    @staticmethod
    def _elecciones(datos: Any) -> dict[int, str | None]:
        if not isinstance(datos, dict) or not isinstance(datos.get("elecciones"), list):
            raise PartidaResiduosError("partida-residuos sin 'elecciones'")
        resultado: dict[int, str | None] = {}
        for eleccion in datos["elecciones"]:
            try:
                ref = int(eleccion["line_ref"])
            except (KeyError, TypeError, ValueError) as exc:
                raise PartidaResiduosError("elección sin line_ref") from exc
            codigo = eleccion.get("codigo")
            resultado[ref] = (str(codigo).strip() or None) if codigo is not None else None
        return resultado
