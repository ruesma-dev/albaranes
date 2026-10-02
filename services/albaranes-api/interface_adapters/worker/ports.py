# interface_adapters/worker/ports.py
"""Puertos del worker de extracción (sv2 como consumidor de q-extraccion).

El worker recibe SOLO ``{document_id}``. Necesita tres colaboradores que en
producción serán adaptadores reales y aquí (piloto) tienen stubs locales:

- :class:`FuenteDocumento`  — resuelve document_id -> bytes del PDF
  (en producción: descarga de SharePoint por la ruta guardada en BBDD).
- :class:`GroundingCabecera` — grounding determinista contra Sigrid para
  fase 2 (en producción se mueve aquí desde sv3). Devuelve dict o None.
- :class:`SumideroEnvelope` — persiste el envelope para que sv3 lo recupere
  por document_id (en producción: tabla en PostgreSQL).
- :class:`FuenteContextoCorreo` — (F-048) resuelve el blob lateral del
  correo (``MensajeExtraccion.correo_blob``) a su ``ContextoCorreo``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ruesma_comun.correo import ContextoCorreo


@dataclass(frozen=True)
class DocumentoPdf:
    filename: str
    mime_type: str
    file_bytes: bytes


class FuenteDocumento(ABC):
    @abstractmethod
    def obtener(self, document_id: str) -> DocumentoPdf:
        """Devuelve el PDF del documento. Lanza si no existe."""
        raise NotImplementedError


class GroundingCabecera(ABC):
    @abstractmethod
    def contexto(self, *, document_id: str, phase_1_json: dict) -> dict | None:
        """Contexto Sigrid para fase 2, o None (fase 2 clásica)."""
        raise NotImplementedError


class SumideroEnvelope(ABC):
    @abstractmethod
    def persistir(self, *, document_id: str, envelope: dict, fase: str) -> None:
        """Guarda el envelope (lo recupera sv3 por document_id)."""
        raise NotImplementedError


class FuenteContextoCorreo(ABC):
    @abstractmethod
    def obtener(self, nombre_blob: str) -> ContextoCorreo | None:
        """Contexto del correo del documento (F-048, R11).

        ``None`` si el blob falta o no valida: el documento se extrae sin
        correo. Un fallo de red se propaga, para que la cola reintente.
        """
        raise NotImplementedError
