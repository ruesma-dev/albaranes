# domain/ports/orchestrator_port.py — NUEVO sv1
"""Puerto de salida hacia sv7 (orchestrator-api).

sv1 ya no conoce sv2 ni sv3: solo sabe del orquestador.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class OrchestratorAck:
    accepted: bool
    workflow_id: str
    duplicate: bool
    message: str


class OrchestratorClient(ABC):
    @abstractmethod
    def submit_email_received(
        self,
        *,
        meta: dict,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> OrchestratorAck:
        """POST /v1/events/email-received en multipart.

        Lanza OrchestratorError tras agotar reintentos HTTP.
        """
        raise NotImplementedError


class OrchestratorError(RuntimeError):
    pass
