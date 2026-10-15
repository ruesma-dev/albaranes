# domain/ports/pdf_port.py
"""Puerto del PDF del albarán (en SharePoint, por la ruta relativa del merge)."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models.alta_models import DatosAlta


class PdfNoDisponibleError(RuntimeError):
    """El documento no tiene PDF localizable (sin ruta en el merge)."""


class PdfAlbaranPort(ABC):
    @abstractmethod
    def descargar(self, datos: DatosAlta) -> bytes:
        """Bytes del PDF del albarán. ``PdfNoDisponibleError`` si no hay ruta."""
