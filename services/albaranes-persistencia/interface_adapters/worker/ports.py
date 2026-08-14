# interface_adapters/worker/ports.py
"""Puertos del worker de persistencia (sv3 consume q-persistencia).

Necesita DOS colaboradores resueltos por document_id:
- :class:`FuenteEnvelope`  — el envelope de extraccion (lo dejo sv2).
- :class:`FuenteDocumento` — el PDF (sv3 lo persiste/sube a SharePoint).
En produccion ambos vendran de BBDD/SharePoint; en el piloto, de disco.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class DocumentoPdf:
    filename: str
    mime_type: str
    file_bytes: bytes


class FuenteEnvelope(ABC):
    @abstractmethod
    def obtener(self, document_id: str) -> Dict[str, Any]:
        raise NotImplementedError


class FuenteDocumento(ABC):
    @abstractmethod
    def obtener(self, document_id: str) -> DocumentoPdf:
        raise NotImplementedError


class FuenteContextoEmail(ABC):
    """Contexto de email/adjunto a partir de la ``correlation_key``.

    (ago 2026, F-002 · R12) En modo colas el mensaje solo trae
    ``document_id`` y ``correlation_key``, asi que el merge se quedaba sin
    ``email_received_datetime`` y el guard de año no tenia referencia. El
    dato lo dejo sv1 en ``workflow_runs.payload_json``.

    Devuelve el dict de contexto que ya entiende el repositorio de sv3
    (claves ``email`` y ``document``), o ``{}`` si no hay nada que
    aportar: es un colaborador best-effort, no una dependencia dura.
    """

    @abstractmethod
    def obtener(self, correlation_key: str) -> Dict[str, Any]:
        raise NotImplementedError
