# domain/ports/orchestrator_port.py — NUEVO sv1
"""Puerto de salida hacia sv7 (orchestrator-api).

sv1 ya no conoce sv2 ni sv3: solo sabe del orquestador.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Solo para la firma: el modelo vive en ``ruesma_comun`` (F-048, R1).
    from ruesma_comun.correo import ContextoCorreo


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
        contexto_correo: ContextoCorreo | None = None,
    ) -> OrchestratorAck:
        """POST /v1/events/email-received en multipart.

        ``contexto_correo`` (F-048) es el texto del correo del que sale la
        pagina, el MISMO para todas las paginas del mensaje (R6); ``None`` si
        no se pudo obtener (R5).

        Lanza OrchestratorError tras agotar reintentos HTTP.
        """
        raise NotImplementedError


class OrchestratorError(RuntimeError):
    pass
