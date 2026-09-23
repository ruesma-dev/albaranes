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
