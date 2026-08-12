# infrastructure/http/orchestrator_client.py — NUEVO sv1
"""Adapter HTTP del puerto OrchestratorClient → sv7."""
from __future__ import annotations

import json
import logging

import httpx

from domain.ports.orchestrator_port import (
    OrchestratorAck,
    OrchestratorClient,
    OrchestratorError,
)

logger = logging.getLogger(__name__)


class HttpOrchestratorClient(OrchestratorClient):
    def __init__(
        self,
        *,
        base_url: str,
        path_email_received: str,
        timeout_s: float,
        max_retries: int = 3,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._path = path_email_received
        self._timeout_s = timeout_s
        self._max_retries = max(1, max_retries)

    def submit_email_received(
        self,
        *,
        meta: dict,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> OrchestratorAck:
        url = f"{self._base_url}{self._path}"
        last_error = ""
        for attempt in range(1, self._max_retries + 1):
            try:
                with httpx.Client(timeout=self._timeout_s) as client:
                    response = client.post(
                        url,
                        files={"file": (filename, file_bytes, content_type)},
                        data={"meta": json.dumps(meta, ensure_ascii=False)},
                    )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                logger.warning(
                    "sv7 attempt %d/%d failed: %s",
                    attempt, self._max_retries, last_error,
                )
                continue

            if response.status_code in (200, 202):
                payload = response.json()
                return OrchestratorAck(
                    accepted=bool(payload.get("accepted", True)),
                    workflow_id=str(payload.get("workflow_id", "")),
                    duplicate=bool(payload.get("duplicate", False)),
                    message=str(payload.get("message", "")),
                )

            last_error = f"HTTP {response.status_code}: {response.text[:300]}"
            if 400 <= response.status_code < 500:
                # 4xx no se reintenta.
                break
            logger.warning(
                "sv7 attempt %d/%d returned: %s",
                attempt, self._max_retries, last_error,
            )

        raise OrchestratorError(
            f"sv7 falló tras {self._max_retries} intentos: {last_error}"
        )
