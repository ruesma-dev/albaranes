# tests/dobles_sv1.py
"""Dobles de los puertos de sv1 para su suite de tests (F-048, T6).

Ninguno toca red, buzon ni BBDD: registran lo que el pipeline les pide para
que el test compruebe que hizo. Los textos de correo de los tests son
inventados y llevan el centinela ``CENTINELA-F048``.
"""
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO

from pypdf import PdfWriter

from application.pipelines.polling_pipeline import PollingPipeline
from domain.models.email_models import ContenidoCorreo, EmailAttachment, EmailMessage
from domain.ports.mailbox_client import MailboxClient
from domain.ports.orchestrator_port import (
    OrchestratorAck,
    OrchestratorClient,
    OrchestratorError,
)
from infrastructure.document.pdf_page_splitter import PdfPageSplitter

CENTINELA = "CENTINELA-F048"
BUZON = "buzon@ejemplo.test"
CARPETA_ORIGEN = "inbox"
ID_PROCESADOS = "carpeta-procesados"
ID_ERRORES = "carpeta-errores"


def pdf_de_paginas(paginas: int) -> bytes:
    """Un PDF en blanco de ``paginas`` paginas, generado en memoria."""
    escritor = PdfWriter()
    for _ in range(paginas):
        escritor.add_blank_page(width=200, height=200)
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def mensaje(msg_id: str = "msg-1", asunto: str = "Albaran obra") -> EmailMessage:
    return EmailMessage(
        id=msg_id,
        subject=asunto,
        sender="proveedor@ejemplo.test",
        received_datetime="2026-09-23T08:00:00Z",
    )


def adjunto(att_id: str, nombre: str = "albaran.pdf", *, inline: bool = False) -> EmailAttachment:
    return EmailAttachment(
        id=att_id,
        name=nombre,
        content_type="application/pdf",
        size=1000,
        is_inline=inline,
    )


def contenido_inventado(cuerpo: str = f"Material para la obra 0945. {CENTINELA}", asunto: str = "Albaran obra") -> ContenidoCorreo:
    """Contenido inventado de un correo, con el centinela en el cuerpo."""
    return ContenidoCorreo(asunto=asunto, cuerpo_unico=cuerpo, tipo="text")


class BuzonDoble(MailboxClient):
    """Buzon en memoria. ``ficheros[att_id]`` son los bytes o una excepcion.

    ``contenido`` es lo que devuelve ``get_contenido`` (o la excepcion que
    lanza); por defecto, un correo inventado con el centinela.
    """

    def __init__(
        self,
        *,
        mensajes: list[EmailMessage],
        adjuntos: dict[str, list[EmailAttachment]],
        ficheros: dict[str, bytes | Exception],
        contenido: ContenidoCorreo | Exception | None = None,
    ) -> None:
        self._mensajes = mensajes
        self._adjuntos = adjuntos
        self._ficheros = ficheros
        self._contenido = contenido if contenido is not None else contenido_inventado()
        self.llamadas: list[tuple[str, str]] = []
        self.movidos: list[tuple[str, str]] = []

    def assert_folder_accessible(self, mailbox: str, folder: str) -> None:
        self.llamadas.append(("assert_folder_accessible", folder))

    def ensure_folder(self, mailbox: str, display_name: str) -> str:
        self.llamadas.append(("ensure_folder", display_name))
        return f"carpeta-{display_name}"

    def list_unread_with_attachments(self, mailbox: str, folder: str, top: int) -> list[EmailMessage]:
        self.llamadas.append(("list_unread_with_attachments", folder))
        return list(self._mensajes)

    def list_attachments(self, mailbox: str, message_id: str) -> list[EmailAttachment]:
        self.llamadas.append(("list_attachments", message_id))
        return list(self._adjuntos.get(message_id, []))

    def download_attachment_value(self, mailbox: str, message_id: str, attachment_id: str) -> bytes:
        self.llamadas.append(("download_attachment_value", attachment_id))
        valor = self._ficheros[attachment_id]
        if isinstance(valor, Exception):
            raise valor
        return valor

    def move_message(self, mailbox: str, message_id: str, destination_folder_id: str) -> None:
        self.llamadas.append(("move_message", message_id))
        self.movidos.append((message_id, destination_folder_id))

    def get_contenido(self, mailbox: str, message_id: str) -> ContenidoCorreo:
        self.llamadas.append(("get_contenido", message_id))
        if isinstance(self._contenido, Exception):
            raise self._contenido
        return self._contenido

    def veces(self, metodo: str) -> int:
        """Cuantas veces se llamo a ``metodo``."""
        return sum(1 for nombre, _ in self.llamadas if nombre == metodo)


@dataclass(frozen=True)
class EnvioRegistrado:
    """Lo que el pipeline entrego al intake por una pagina."""

    meta: dict
    file_bytes: bytes
    filename: str
    content_type: str


class IntakeDoble(OrchestratorClient):
    """Intake que acepta todo y registra cada pagina (o falla si se le pide)."""

    def __init__(self, *, fallar: bool = False) -> None:
        self._fallar = fallar
        self.envios: list[EnvioRegistrado] = []

    def submit_email_received(
        self,
        *,
        meta: dict,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> OrchestratorAck:
        self.envios.append(EnvioRegistrado(meta, file_bytes, filename, content_type))
        if self._fallar:
            raise OrchestratorError("intake doble: fallo pedido por el test")
        return OrchestratorAck(
            accepted=True,
            workflow_id=f"wf-{len(self.envios)}",
            duplicate=False,
            message="encolado",
        )


def construir_pipeline(buzon: MailboxClient, intake: OrchestratorClient) -> PollingPipeline:
    return PollingPipeline(mailbox=buzon, orchestrator=intake, pdf_splitter=PdfPageSplitter())


def ejecutar_ciclo(pipeline: PollingPipeline) -> None:
    """Una iteracion de polling con los valores de siempre."""
    pipeline.run_once(
        mailbox=BUZON,
        source_folder=CARPETA_ORIGEN,
        processed_folder_id=ID_PROCESADOS,
        errors_folder_id=ID_ERRORES,
        top=10,
        max_attachment_bytes=25 * 1024 * 1024,
    )
