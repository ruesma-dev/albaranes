# application/pipelines/polling_pipeline.py
"""Loop de polling. sv1 detecta correos nuevos y delega TODO el
procesamiento al orquestador (sv7). sv1 ya no llama a sv2 ni a sv3.

Flujo (run_once):
  1. Lista mensajes no leídos con adjuntos del SOURCE_FOLDER vía Graph.
  2. Para cada mensaje:
     a. Lista adjuntos.
     b. Filtra adjuntos no-inline tipo file (descarta inline e items).
     c. Para cada adjunto válido:
        i.   Descarga sus bytes vía Graph.
        ii.  Si es PDF, lo divide por páginas (cada página es un evento
             independiente para sv7 — la idempotencia evita procesar dos
             veces lo mismo).
        iii. Calcula sha256 del adjunto y de cada página.
        iv.  POST sv7 /v1/events/email-received con multipart (meta + file).
     d. Mueve el email a:
        - 'Procesados' si TODAS las páginas devolvieron 202 (accepted=true,
          incluso si duplicate=true).
        - 'Errores' si alguna falló o no había adjuntos válidos.

Notas:
  - La idempotencia la garantiza sv7 (correlation_key UNIQUE):
    `email:{message_id}:{page_sha256}`. Si sv1 reenvía el mismo evento,
    sv7 devuelve duplicate=true sin reabrir el workflow.
  - sv7 responde 202 inmediatamente y procesa en BackgroundTask.
  - El loop es síncrono (bloqueante) — un error en una página no impide
    procesar el siguiente adjunto/email; solo afecta al move final.
"""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timezone

from domain.models.email_models import EmailAttachment, EmailMessage
from domain.ports.mailbox_client import MailboxClient
from domain.ports.orchestrator_port import OrchestratorClient, OrchestratorError
from infrastructure.document.pdf_page_splitter import (
    PdfPageSplitter,
    PreparedDocument,
)

logger = logging.getLogger(__name__)


# Tipos de adjunto que vienen en Graph y NO son archivos reales que
# queramos procesar (referencias a otros items, mensajes embebidos…).
_NON_FILE_ODATA_TYPES = frozenset({
    "#microsoft.graph.itemAttachment",
    "#microsoft.graph.referenceAttachment",
})


class PollingPipeline:
    """Pipeline principal del sv1.

    Firma del constructor IGUAL que la versión anterior — solo se
    sustituyen `extractor` y `persistence` por `orchestrator`. Así
    `main.py` solo tiene que cambiar el cableado, no la forma de
    construir el pipeline.
    """

    def __init__(
        self,
        *,
        mailbox: MailboxClient,
        orchestrator: OrchestratorClient,
        pdf_splitter: PdfPageSplitter,
    ) -> None:
        self._mailbox = mailbox
        self._orchestrator = orchestrator
        self._splitter = pdf_splitter

    # ----------------------------------------------------------- #
    # Bucle infinito (lo invoca main.py).
    # ----------------------------------------------------------- #
    def run_forever(self, settings) -> None:
        """Polling con sleep entre iteraciones. Se rompe solo con
        SIGINT/SIGTERM (uvicorn no aplica aquí: sv1 no es API)."""
        # Pre-checks: el folder fuente debe ser accesible y los
        # destinos de Procesados/Errores deben existir (los crea si
        # no existen). Hacerlo al arranque evita errores tardíos.
        self._mailbox.assert_folder_accessible(
            settings.mailbox_address,
            settings.source_folder,
        )
        processed_folder_id = self._mailbox.ensure_folder(
            settings.mailbox_address,
            settings.folder_procesados,
        )
        errors_folder_id = self._mailbox.ensure_folder(
            settings.mailbox_address,
            settings.folder_errores,
        )

        logger.info(
            "Pre-checks OK. procesados_id=%s errores_id=%s",
            processed_folder_id,
            errors_folder_id,
        )

        max_attachment_bytes = settings.max_attachment_mb * 1024 * 1024

        while True:
            try:
                self.run_once(
                    mailbox=settings.mailbox_address,
                    source_folder=settings.source_folder,
                    processed_folder_id=processed_folder_id,
                    errors_folder_id=errors_folder_id,
                    top=settings.max_emails,
                    max_attachment_bytes=max_attachment_bytes,
                )
            except Exception:
                # Cualquier excepción no controlada: log y seguimos.
                # El sistema debe ser resiliente a errores transitorios
                # de Graph o del orquestador.
                logger.exception("error en run_once, continuando…")

            time.sleep(settings.poll_interval_s)

    # ----------------------------------------------------------- #
    # Una iteración del polling (testeable, sin sleep).
    # ----------------------------------------------------------- #
    def run_once(
        self,
        *,
        mailbox: str,
        source_folder: str,
        processed_folder_id: str,
        errors_folder_id: str,
        top: int,
        max_attachment_bytes: int,
    ) -> None:
        messages = self._mailbox.list_unread_with_attachments(
            mailbox=mailbox,
            folder=source_folder,
            top=top,
        )
        if not messages:
            logger.debug("sin mensajes nuevos")
            return

        logger.info("polling: %d mensaje(s) con adjuntos", len(messages))
        for msg in messages:
            try:
                self._process_message(
                    msg=msg,
                    mailbox=mailbox,
                    processed_folder_id=processed_folder_id,
                    errors_folder_id=errors_folder_id,
                    max_attachment_bytes=max_attachment_bytes,
                )
            except Exception:
                # Salvavidas por mensaje: si uno falla, los demás siguen.
                logger.exception(
                    "msg=%s error inesperado, intentando mover a Errores",
                    msg.id,
                )
                self._safe_move(
                    mailbox=mailbox,
                    message_id=msg.id,
                    target_folder_id=errors_folder_id,
                )

    # ----------------------------------------------------------- #
    # Procesamiento de un mensaje individual.
    # ----------------------------------------------------------- #
    def _process_message(
        self,
        *,
        msg: EmailMessage,
        mailbox: str,
        processed_folder_id: str,
        errors_folder_id: str,
        max_attachment_bytes: int,
    ) -> None:
        logger.info(
            "msg=%s subject=%r sender=%s received=%s",
            msg.id,
            msg.subject,
            msg.sender,
            msg.received_datetime,
        )

        attachments = self._mailbox.list_attachments(
            mailbox=mailbox,
            message_id=msg.id,
        )
        eligible = [a for a in attachments if self._is_eligible(a, max_attachment_bytes)]

        if not eligible:
            logger.warning(
                "msg=%s sin adjuntos elegibles (total=%d) → Errores",
                msg.id,
                len(attachments),
            )
            self._safe_move(
                mailbox=mailbox,
                message_id=msg.id,
                target_folder_id=errors_folder_id,
            )
            return

        all_ok = True
        for att in eligible:
            ok = self._process_attachment(
                msg=msg,
                attachment=att,
                mailbox=mailbox,
            )
            all_ok = all_ok and ok

        target = processed_folder_id if all_ok else errors_folder_id
        target_label = "Procesados" if all_ok else "Errores"
        self._safe_move(
            mailbox=mailbox,
            message_id=msg.id,
            target_folder_id=target,
        )
        logger.info("msg=%s movido a %s", msg.id, target_label)

    def _process_attachment(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        mailbox: str,
    ) -> bool:
        """Devuelve True si TODAS las páginas se enviaron a sv7 con éxito."""
        logger.info(
            "msg=%s att=%s name=%r type=%s size=%dB",
            msg.id,
            attachment.id,
            attachment.name,
            attachment.content_type,
            attachment.size,
        )

        try:
            file_bytes = self._mailbox.download_attachment_value(
                mailbox=mailbox,
                message_id=msg.id,
                attachment_id=attachment.id,
            )
        except Exception as exc:
            logger.error(
                "msg=%s att=%s error descarga Graph: %s",
                msg.id,
                attachment.id,
                exc,
            )
            return False

        attachment_sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Splitting de PDF: si el adjunto es PDF multi-página, devuelve
        # una página por elemento; si es 1 página o no es PDF, una sola
        # PreparedDocument con was_split=False.
        try:
            prepared_pages = self._splitter.split(
                filename=attachment.name,
                mime_type=attachment.content_type,
                file_bytes=file_bytes,
            )
        except Exception as exc:
            logger.error(
                "msg=%s att=%s error splitting PDF: %s",
                msg.id,
                attachment.id,
                exc,
            )
            return False

        all_pages_ok = True
        for prepared in prepared_pages:
            page_ok = self._submit_page_to_orchestrator(
                msg=msg,
                attachment=attachment,
                attachment_sha256=attachment_sha256,
                prepared=prepared,
            )
            all_pages_ok = all_pages_ok and page_ok

        return all_pages_ok

    def _submit_page_to_orchestrator(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        attachment_sha256: str,
        prepared: PreparedDocument,
    ) -> bool:
        page_sha256 = hashlib.sha256(prepared.file_bytes).hexdigest()

        meta = {
            "email_message_id": msg.id,
            "email_received_at_utc": _to_iso_utc(msg.received_datetime),
            "from_address": msg.sender or "",
            "subject": msg.subject or "",
            "attachment_filename": prepared.filename,
            "attachment_sha256": attachment_sha256,
            "attachment_content_type": prepared.mime_type,
            "attachment_size_bytes": len(prepared.file_bytes),
            "page_number": prepared.page_number,
            "total_pages": prepared.page_count,
            "page_sha256": page_sha256,
        }

        try:
            ack = self._orchestrator.submit_email_received(
                meta=meta,
                file_bytes=prepared.file_bytes,
                filename=prepared.filename,
                content_type=prepared.mime_type,
            )
        except OrchestratorError as exc:
            logger.error(
                "msg=%s page=%d/%d ERROR sv7: %s",
                msg.id,
                prepared.page_number,
                prepared.page_count,
                exc,
            )
            return False

        logger.info(
            "msg=%s page=%d/%d → sv7 wf=%s duplicate=%s msg=%r",
            msg.id,
            prepared.page_number,
            prepared.page_count,
            ack.workflow_id or "?",
            ack.duplicate,
            ack.message,
        )
        return ack.accepted

    # ----------------------------------------------------------- #
    # Helpers.
    # ----------------------------------------------------------- #
    @staticmethod
    def _is_eligible(att: EmailAttachment, max_bytes: int) -> bool:
        """Filtra adjuntos válidos: no inline, no item/reference, y
        bajo el límite de tamaño configurado."""
        if att.is_inline:
            return False
        if att.odata_type and att.odata_type in _NON_FILE_ODATA_TYPES:
            return False
        if max_bytes > 0 and att.size > max_bytes:
            logger.warning(
                "att=%s name=%r tamaño %dB excede límite %dB → descartado",
                att.id,
                att.name,
                att.size,
                max_bytes,
            )
            return False
        return True

    def _safe_move(
        self,
        *,
        mailbox: str,
        message_id: str,
        target_folder_id: str,
    ) -> None:
        """Mueve un email tolerando errores (los loguea pero no relanza)."""
        try:
            self._mailbox.move_message(
                mailbox=mailbox,
                message_id=message_id,
                destination_folder_id=target_folder_id,
            )
        except Exception:
            logger.exception(
                "msg=%s no se pudo mover al folder destino %s",
                message_id,
                target_folder_id,
            )


def _to_iso_utc(value) -> str:
    """Normaliza un timestamp ISO (string o datetime) a ISO-8601 UTC con Z."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)
