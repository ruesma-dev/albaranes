# infrastructure/http/service2_http_client.py
from __future__ import annotations

import logging
import time
from typing import Any, Dict

import httpx

from domain.ports.extraction_client import ExtractionClient

logger = logging.getLogger(__name__)


class Service2HttpClient(ExtractionClient):
    def __init__(self, base_url: str, path: str, timeout_s: int) -> None:
        self._url = base_url.rstrip("/") + "/" + path.lstrip("/")
        self._timeout_s = int(timeout_s)
        timeout = httpx.Timeout(
            connect=15.0,
            read=float(self._timeout_s),
            write=float(self._timeout_s),
            pool=30.0,
        )
        self._client = httpx.Client(timeout=timeout)

    def extract(
        self,
        *,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
    ) -> Dict[str, Any]:
        logger.info(
            "Servicio2 HTTP -> %s | file=%s | timeout_s=%s",
            self._url,
            filename,
            self._timeout_s,
        )
        files = {
            "file": (
                filename,
                file_bytes,
                mime_type or "application/octet-stream",
            )
        }
        started = time.perf_counter()
        try:
            response = self._client.post(self._url, files=files)
        except httpx.ReadTimeout as exc:
            elapsed = time.perf_counter() - started
            raise RuntimeError(
                "Servicio2 timeout esperando respuesta. "
                f"file={filename} timeout_s={self._timeout_s} "
                f"elapsed_s={elapsed:.2f}"
            ) from exc

        elapsed = time.perf_counter() - started
        logger.info(
            "Servicio2 HTTP <- status=%s | file=%s | elapsed_s=%.2f",
            response.status_code,
            filename,
            elapsed,
        )

        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(
                f"Servicio2 error {response.status_code}: {response.text[:800]}"
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Servicio2 devolvió una respuesta no válida.")
        return payload
