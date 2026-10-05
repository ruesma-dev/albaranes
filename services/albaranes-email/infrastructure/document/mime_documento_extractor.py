# infrastructure/document/mime_documento_extractor.py
"""Extractor de los documentos que viajan dentro de un correo adjunto (F-054).

Hay albaranes que llegan como correo adjunto (adjunto de Graph con
``contentType`` ``message/rfc822``), a veces anidado, con el PDF o la foto
dentro. Graph devuelve ese correo como MIME RFC 822 en ``$value``; aqui se
recorre con la biblioteca estandar ``email`` y se sacan los documentos.

Reglas (requirements R6-R12 de F-054):

  - Recorrido en profundidad y en orden de aparicion: ``multipart/*`` se
    recorre parte a parte en el mismo nivel; ``message/rfc822`` se abre como
    el nivel siguiente. La raiz de ``$value`` es el nivel 1.
  - Recursion PROPIA, no ``Message.walk()``: ``walk`` baja a los
    ``message/rfc822`` sin decir en que nivel esta cada parte.
  - Tope de ``NIVEL_MAXIMO_ANIDAMIENTO`` niveles: abrir uno mas marca
    ``tope_excedido`` y no se baja (el pipeline no ingiere nada: R9).
  - Documento = parte no multipart que sea PDF (``application/pdf`` o nombre
    ``.pdf``) o imagen valida (``image/*`` con disposicion ``attachment``,
    el «no inline» de Graph en MIME: DA8). Bytes ya decodificados. Lo demas
    se ignora y se cuenta (log DEBUG solo con tipo y nivel).
  - No se leen ``Subject``, ``From`` ni ``Date`` del interior (DH3).
  - Puro: sin red ni disco. Ningun log lleva bytes ni cabeceras (R25).

Logica traida de ``partes`` (F-020, ``mime_pdf_extractor.py``) y adaptada;
nada se importa de alli.
"""
from __future__ import annotations

import logging
from email import message_from_bytes
from email.message import Message
from email.policy import default as POLITICA_EMAIL
from pathlib import PurePosixPath

from domain.models.email_models import DocumentoInterior, ExtraccionCorreoAdjunto
from domain.ports.extractor_correo_adjunto import CorreoAdjuntoIlegible

logger = logging.getLogger(__name__)

#: Niveles de correo que se abren como maximo (el adjunto de Graph es el 1).
NIVEL_MAXIMO_ANIDAMIENTO = 5

_TIPO_CORREO = "message/rfc822"
_TIPO_PDF = "application/pdf"


class _Acumulador:
    """Estado mutable de un recorrido (uno por llamada a ``extraer``)."""

    def __init__(self) -> None:
        self.documentos: list[DocumentoInterior] = []
        self.tope_excedido = False
        self.partes_ignoradas = 0


class MimeDocumentoExtractor:
    """Implementacion del puerto ``ExtractorCorreoAdjunto``."""

    def __init__(self, nivel_maximo: int = NIVEL_MAXIMO_ANIDAMIENTO) -> None:
        self._nivel_maximo = nivel_maximo

    @property
    def nivel_maximo(self) -> int:
        return self._nivel_maximo

    def extraer(self, *, raw_mime: bytes) -> ExtraccionCorreoAdjunto:
        if not raw_mime:
            raise CorreoAdjuntoIlegible("el correo adjunto no trae bytes")
        acumulador = _Acumulador()
        try:
            raiz = message_from_bytes(raw_mime, policy=POLITICA_EMAIL)
            self._recorrer(raiz, 1, acumulador)
        except Exception as exc:
            # Solo el tipo de la excepcion: su texto podria citar el correo.
            raise CorreoAdjuntoIlegible(
                f"no se pudo interpretar como mensaje RFC 822 ({type(exc).__name__})"
            ) from exc
        return ExtraccionCorreoAdjunto(
            documentos=tuple(acumulador.documentos),
            tope_excedido=acumulador.tope_excedido,
            partes_ignoradas=acumulador.partes_ignoradas,
        )

    # ----------------------------------------------------------- #
    # Recorrido.
    # ----------------------------------------------------------- #
    def _recorrer(self, parte: Message, nivel: int, acumulador: _Acumulador) -> None:
        tipo = parte.get_content_type()

        if tipo == _TIPO_CORREO:
            interior = _primer_mensaje(parte)
            if interior is None:
                _ignorar(acumulador, tipo, nivel)
                return
            if nivel + 1 > self._nivel_maximo:
                acumulador.tope_excedido = True
                return
            self._recorrer(interior, nivel + 1, acumulador)
            return

        if tipo.startswith("multipart/"):
            for subparte in parte.get_payload() or []:
                self._recorrer(subparte, nivel, acumulador)
            return

        nombre = _nombre_fichero(parte)
        if tipo == _TIPO_PDF or (nombre or "").lower().endswith(".pdf"):
            tipo_documento = _TIPO_PDF
        elif parte.get_content_maintype() == "image" and parte.get_content_disposition() == "attachment":
            tipo_documento = tipo
        else:
            _ignorar(acumulador, tipo, nivel)
            return

        datos = parte.get_payload(decode=True)
        if not datos:
            _ignorar(acumulador, tipo, nivel)
            return

        orden = len(acumulador.documentos) + 1
        acumulador.documentos.append(DocumentoInterior(
            filename=_nombre_documento(nombre, orden, tipo_documento),
            content_type=tipo_documento,
            file_bytes=datos,
            nivel=nivel,
        ))


def _primer_mensaje(parte: Message) -> Message | None:
    contenido = parte.get_payload()
    if isinstance(contenido, list) and contenido:
        return contenido[0]
    return None


def _ignorar(acumulador: _Acumulador, tipo: str, nivel: int) -> None:
    acumulador.partes_ignoradas += 1
    logger.debug("parte interior ignorada tipo=%s nivel=%d", tipo, nivel)


def _nombre_fichero(parte: Message) -> str | None:
    try:
        return parte.get_filename()
    except Exception:  # noqa: BLE001 — un nombre ilegible es como no tenerlo
        return None


def _nombre_documento(nombre: str | None, orden: int, tipo: str) -> str:
    """Nombre base del fichero MIME (R10) o ``documento_<orden>.<ext>``."""
    if nombre:
        base = PurePosixPath(nombre.replace("\\", "/")).name
        if base:
            return base
    extension = "pdf" if tipo == _TIPO_PDF else tipo.split("/", 1)[1]
    return f"documento_{orden}.{extension}"
