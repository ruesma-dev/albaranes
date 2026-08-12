# infrastructure/http/service3_http_client.py
from __future__ import annotations

import json
import logging
from typing import Any, Dict

import httpx

from domain.ports.persistence_client import PersistenceClient

logger = logging.getLogger(__name__)


class Service3HttpClient(PersistenceClient):
    def __init__(self, base_url: str, path: str, timeout_s: int) -> None:
        self._url = base_url.rstrip("/") + "/" + path.lstrip("/")
        self._client = httpx.Client(timeout=timeout_s)

    def persist(
        self,
        *,
        filename: str,
        mime_type: str,
        file_bytes: bytes,
        extraction_envelope: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        logger.info("Servicio3 HTTP -> %s | file=%s", self._url, filename)
        files = {
            "file": (
                filename,
                file_bytes,
                mime_type or "application/octet-stream",
            )
        }
        data = {
            "extraction_json": json.dumps(
                extraction_envelope,
                ensure_ascii=False,
            ),
            "context_json": json.dumps(context, ensure_ascii=False),
        }
        response = self._client.post(self._url, data=data, files=files)
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(
                f"Servicio3 error {response.status_code}: {response.text[:800]}"
            )

        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Servicio3 devolvió una respuesta no válida.")
        return payload
