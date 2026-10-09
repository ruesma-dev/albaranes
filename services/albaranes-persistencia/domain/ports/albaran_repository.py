# domain/ports/albaran_repository.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from domain.models.extraction_models import ExtractionEnvelope
from domain.models.persistence_models import ExistingDocument, StoredFile


class AlbaranRepository(ABC):
    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_sha256(self, source_sha256: str) -> ExistingDocument | None:
        raise NotImplementedError

    @abstractmethod
    def buscar_conservado_por_alta(
        self, source_sha256: str
    ) -> ExistingDocument | None:
        """(F-053 · R45, D3) El documento con este PDF (activo o en la
        papelera) que tiene un alta en Sigrid bloqueante, con
        ``conservado_por_alta``; ``None`` si no hay. Solo lectura."""
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        *,
        envelope: ExtractionEnvelope,
        context: Dict[str, Any],
        stored_file: StoredFile,
    ) -> ExistingDocument:
        raise NotImplementedError
