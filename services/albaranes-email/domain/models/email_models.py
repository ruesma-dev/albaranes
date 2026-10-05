# domain/models/email_models.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EmailMessage:
    id: str
    subject: str
    sender: Optional[str]
    received_datetime: Optional[str]


@dataclass(frozen=True)
class EmailAttachment:
    id: str
    name: str
    content_type: str
    size: int
    is_inline: bool
    odata_type: Optional[str] = None


@dataclass(frozen=True)
class ContenidoCorreo:
    """Texto de un correo tal como lo da Graph (F-048, R2-R4).

    ``cuerpo_unico`` es la parte NO citada del cuerpo (``uniqueBody``), ya
    en texto plano; vacio si Graph no la trae (R3: nunca se cae al
    ``body``, que arrastra la cadena de respuestas). ``tipo`` es el
    ``contentType`` que devolvio Graph (``text`` o ``html``), en minusculas.
    """

    asunto: str
    cuerpo_unico: str
    tipo: str = "text"
    # ``receivedDateTime`` tal cual lo da Graph (ISO UTC) o ``None``; lo
    # guarda la captura de evals (CR-B5). El pipeline usa el del listado.
    recibido_utc: str | None = None


@dataclass(frozen=True)
class DocumentoInterior:
    """PDF o imagen valida hallada dentro de un correo adjunto (F-054, R7).

    ``filename`` es el nombre base de R10; ``content_type`` es
    ``application/pdf`` para un PDF o el ``image/*`` de la parte, en
    minusculas; ``file_bytes`` son los bytes ya decodificados; ``nivel`` es
    el del correo que lo contiene (el correo adjunto es el 1).
    """

    filename: str
    content_type: str
    file_bytes: bytes
    nivel: int


@dataclass(frozen=True)
class ExtraccionCorreoAdjunto:
    """Resultado de recorrer un correo adjunto (F-054, R6-R9).

    ``documentos`` va en el orden de aparicion de R6. Con
    ``tope_excedido`` el pipeline no ingiere ninguno (R9, todo o nada).
    """

    documentos: tuple[DocumentoInterior, ...]
    tope_excedido: bool
    partes_ignoradas: int
