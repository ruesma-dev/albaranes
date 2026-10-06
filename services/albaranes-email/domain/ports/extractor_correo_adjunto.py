# domain/ports/extractor_correo_adjunto.py
"""Puerto del extractor de documentos de un correo adjunto (F-054).

Un correo adjunto es un adjunto de Graph con ``contentType``
``message/rfc822``; su ``$value`` es el MIME RFC 822 del correo. El
extractor lo recorre y devuelve los PDF e imagenes validas de su interior.
La implementacion vive en ``infrastructure/document/`` y la inyecta
``main.py`` (R27): el pipeline solo conoce este puerto.
"""
from __future__ import annotations

from typing import Protocol

from domain.models.email_models import ExtraccionCorreoAdjunto


class CorreoAdjuntoIlegible(Exception):
    """Los bytes no son un mensaje RFC 822 legible (R11).

    El texto nombra solo el tipo de error: nunca contenido del correo.
    """


class ExtractorCorreoAdjunto(Protocol):
    @property
    def nivel_maximo(self) -> int:
        """Niveles de correo que se abren como maximo (va al log de R9)."""
        ...

    def extraer(self, *, raw_mime: bytes) -> ExtraccionCorreoAdjunto:
        """Documentos interiores del correo adjunto, sin red ni disco (R12).

        Lanza ``CorreoAdjuntoIlegible`` si los bytes estan vacios o no son
        un mensaje.
        """
        ...
