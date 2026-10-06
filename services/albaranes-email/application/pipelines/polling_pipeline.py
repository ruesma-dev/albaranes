# application/pipelines/polling_pipeline.py
"""Loop de polling. sv1 detecta correos nuevos y delega TODO el
procesamiento al orquestador (sv7). sv1 ya no llama a sv2 ni a sv3.

Flujo (run_once):
  1. Lista mensajes no leídos con adjuntos del SOURCE_FOLDER vía Graph.
  2. Para cada mensaje:
     a. Lista adjuntos y los clasifica en UNA pasada, en el orden de Graph:
        - correo adjunto (``message/rfc822``, item o file, no inline, no
          reference, bajo el límite; F-054 R1-R2). Uno de tipo correo
          descartado no se trata como directo;
        - directo: la regla de siempre (descarta inline, item, reference
          y los que exceden el límite; ningún filtro de tipo, R3).
     b'. Si hay alguno, pide UNA vez el asunto y la parte única del cuerpo
         del correo EXTERIOR y construye el contexto (F-048, R2-R5). Si
         falla, se sigue sin contexto: no es motivo para ir a 'Errores'.
     c. Para cada adjunto, en orden:
        - directo: descarga sus bytes vía Graph;
        - correo adjunto: descarga su MIME (``$value``) y el extractor
          inyectado saca sus PDF e imágenes válidas (5 niveles, todo o
          nada); cada documento interior bajo el límite sigue el camino
          del directo con ``correo_adjunto_id``/``_nivel`` en el meta.
        Camino del directo:
        i.   Si es PDF, lo divide por páginas (cada página es un evento
             independiente — la idempotencia evita procesar dos veces lo
             mismo).
        ii.  Calcula sha256 del fichero y de cada página.
        iii. Lo entrega al intake (dedup, blob ``input/``, q-extraccion).
     d. Mueve el email a:
        - 'Procesados' si nada falló (descarga, extracción, troceo, intake,
          tope de anidamiento) y al menos una página fue aceptada
          (accepted=true, incluso si duplicate=true).
        - 'Errores' en otro caso, o si no había nada que procesar. Un
          correo adjunto sin documentos válidos no es fallo (WARNING).

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
from typing import NamedTuple

from domain.models.email_models import EmailAttachment, EmailMessage
from domain.ports.extractor_correo_adjunto import (
    CorreoAdjuntoIlegible,
    ExtractorCorreoAdjunto,
)
from domain.ports.mailbox_client import MailboxClient
from domain.ports.orchestrator_port import OrchestratorClient, OrchestratorError
from infrastructure.document.pdf_page_splitter import (
    PdfPageSplitter,
    PreparedDocument,
)
from ruesma_comun.correo import (
    MAX_CARACTERES_DEFECTO,
    ContextoCorreo,
    construir_contexto_correo,
)

logger = logging.getLogger(__name__)


_ODATA_REFERENCE = "#microsoft.graph.referenceAttachment"

# Tipos de adjunto que vienen en Graph y NO son archivos reales que
# queramos procesar como directos (referencias a otros items, mensajes
# embebidos…). Un itemAttachment de tipo correo NO llega aquí: lo abre la
# rama de correos adjuntos (F-054).
_NON_FILE_ODATA_TYPES = frozenset({
    "#microsoft.graph.itemAttachment",
    _ODATA_REFERENCE,
})

# ``contentType`` de Graph de un correo adjunto (F-054, R1).
_CONTENT_TYPE_CORREO = "message/rfc822"
_CONTENT_TYPE_PDF = "application/pdf"


class _ResultadoAdjunto(NamedTuple):
    """Lo que deja un adjunto (directo o correo adjunto) para R21."""

    ok: bool
    paginas_aceptadas: int


def _es_tipo_correo(att: EmailAttachment) -> bool:
    """El adjunto es de tipo correo (``message/rfc822``, sin mayúsculas)."""
    return (att.content_type or "").lower() == _CONTENT_TYPE_CORREO


class PollingPipeline:
    """Pipeline principal del sv1.

    ``extractor_correo`` (F-054) es obligatorio: lo construye ``main.py``
    y el pipeline solo conoce su puerto (R27).
    """

    def __init__(
        self,
        *,
        mailbox: MailboxClient,
        orchestrator: OrchestratorClient,
        pdf_splitter: PdfPageSplitter,
        extractor_correo: ExtractorCorreoAdjunto,
        correo_max_caracteres: int = MAX_CARACTERES_DEFECTO,
    ) -> None:
        self._mailbox = mailbox
        self._orchestrator = orchestrator
        self._splitter = pdf_splitter
        self._extractor_correo = extractor_correo
        self._correo_max_caracteres = correo_max_caracteres

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

        # UNA pasada en el orden de Graph (F-054, R20): cada adjunto es un
        # correo adjunto elegible, un adjunto de tipo correo descartado
        # (R2: no cae a la regla de los directos) o un candidato a directo
        # con la regla de siempre (R3).
        a_procesar: list[tuple[bool, EmailAttachment]] = []
        for att in attachments:
            if _es_tipo_correo(att):
                if self._es_correo_adjunto(att, max_attachment_bytes):
                    a_procesar.append((True, att))
                continue
            if self._is_eligible(att, max_attachment_bytes):
                a_procesar.append((False, att))

        if not a_procesar:
            logger.warning(
                "msg=%s sin adjuntos elegibles: ni directos ni correos adjuntos (total=%d) → Errores",
                msg.id,
                len(attachments),
            )
            self._safe_move(
                mailbox=mailbox,
                message_id=msg.id,
                target_folder_id=errors_folder_id,
            )
            return

        # UNA petición por mensaje: el mismo contexto va a todas las
        # páginas de todos sus adjuntos (F-048, R6), también a las de los
        # documentos de un correo adjunto: el del EXTERIOR (F-054, R17).
        contexto = self._contexto_del_correo(msg=msg, mailbox=mailbox)

        resultados: list[_ResultadoAdjunto] = []
        for es_correo, att in a_procesar:
            if es_correo:
                resultado = self._process_correo_adjunto(
                    msg=msg,
                    attachment=att,
                    mailbox=mailbox,
                    contexto=contexto,
                    max_attachment_bytes=max_attachment_bytes,
                )
            else:
                resultado = self._process_attachment(
                    msg=msg,
                    attachment=att,
                    mailbox=mailbox,
                    contexto=contexto,
                )
            resultados.append(resultado)

        # R21: Procesados si y solo si nada falló y entró al menos una página.
        paginas_aceptadas = sum(r.paginas_aceptadas for r in resultados)
        all_ok = all(r.ok for r in resultados) and paginas_aceptadas >= 1
        target = processed_folder_id if all_ok else errors_folder_id
        target_label = "Procesados" if all_ok else "Errores"
        self._safe_move(
            mailbox=mailbox,
            message_id=msg.id,
            target_folder_id=target,
        )
        correos_adjuntos = sum(1 for es_correo, _ in a_procesar if es_correo)
        logger.info(
            "msg=%s movido a %s (directos=%d correos_adjuntos=%d paginas_aceptadas=%d)",
            msg.id,
            target_label,
            len(a_procesar) - correos_adjuntos,
            correos_adjuntos,
            paginas_aceptadas,
        )

    def _process_attachment(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        mailbox: str,
        contexto: ContextoCorreo | None,
    ) -> _ResultadoAdjunto:
        """Adjunto directo. ``ok`` si TODAS sus páginas se aceptaron."""
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
            return _ResultadoAdjunto(ok=False, paginas_aceptadas=0)

        return self._ingerir(
            msg=msg,
            att_id=attachment.id,
            nombre=attachment.name,
            content_type=attachment.content_type,
            file_bytes=file_bytes,
            contexto=contexto,
            extra_meta=None,
        )

    def _process_correo_adjunto(
        self,
        *,
        msg: EmailMessage,
        attachment: EmailAttachment,
        mailbox: str,
        contexto: ContextoCorreo | None,
        max_attachment_bytes: int,
    ) -> _ResultadoAdjunto:
        """Correo adjunto (F-054): descarga su MIME, saca sus documentos y
        mete cada uno por el camino del directo.

        Nunca se loguea ``attachment.name``: Graph pone ahí el asunto del
        correo interior (R25, DA6).
        """
        logger.info(
            "msg=%s att=%s correo adjunto type=%s size=%dB",
            msg.id,
            attachment.id,
            attachment.content_type,
            attachment.size,
        )

        try:
            raw_mime = self._mailbox.download_attachment_value(
                mailbox=mailbox,
                message_id=msg.id,
                attachment_id=attachment.id,
            )
        except Exception as exc:
            # Solo el tipo: el texto del error de Graph podría citar el correo.
            logger.error(
                "msg=%s att=%s error descarga Graph del correo adjunto (%s)",
                msg.id,
                attachment.id,
                type(exc).__name__,
            )
            return _ResultadoAdjunto(ok=False, paginas_aceptadas=0)

        try:
            extraccion = self._extractor_correo.extraer(raw_mime=raw_mime)
        except CorreoAdjuntoIlegible as exc:
            logger.error(
                "msg=%s att=%s correo adjunto ilegible: %s",
                msg.id,
                attachment.id,
                exc,
            )
            return _ResultadoAdjunto(ok=False, paginas_aceptadas=0)

        if extraccion.tope_excedido:
            # R9: todo o nada, tampoco entran los de niveles permitidos.
            logger.error(
                "msg=%s att=%s correo adjunto excede el tope de anidamiento tope=%d:"
                " no se ingiere ningun documento",
                msg.id,
                attachment.id,
                self._extractor_correo.nivel_maximo,
            )
            return _ResultadoAdjunto(ok=False, paginas_aceptadas=0)

        documentos = []
        for doc in extraccion.documentos:
            if max_attachment_bytes > 0 and len(doc.file_bytes) > max_attachment_bytes:
                logger.warning(
                    "msg=%s att=%s documento interior name=%r tamaño %dB excede límite %dB → descartado",
                    msg.id,
                    attachment.id,
                    doc.filename,
                    len(doc.file_bytes),
                    max_attachment_bytes,
                )
                continue
            documentos.append(doc)

        if not documentos:
            # R22: no es un fallo; el destino lo decide R21(c).
            logger.warning(
                "msg=%s att=%s correo adjunto sin ningun documento interior valido (partes_ignoradas=%d)",
                msg.id,
                attachment.id,
                extraccion.partes_ignoradas,
            )
            return _ResultadoAdjunto(ok=True, paginas_aceptadas=0)

        pdfs = sum(1 for doc in documentos if doc.content_type == _CONTENT_TYPE_PDF)
        logger.info(
            "msg=%s att=%s documentos interiores: %d PDF y %d imagen(es), partes_ignoradas=%d",
            msg.id,
            attachment.id,
            pdfs,
            len(documentos) - pdfs,
            extraccion.partes_ignoradas,
        )

        resultados: list[_ResultadoAdjunto] = []
        for doc in documentos:
            logger.info(
                "msg=%s att=%s documento interior name=%r type=%s nivel=%d size=%dB",
                msg.id,
                attachment.id,
                doc.filename,
                doc.content_type,
                doc.nivel,
                len(doc.file_bytes),
            )
            resultados.append(
                self._ingerir(
                    msg=msg,
                    att_id=attachment.id,
                    nombre=doc.filename,
                    content_type=doc.content_type,
                    file_bytes=doc.file_bytes,
                    contexto=contexto,
                    extra_meta={
                        "correo_adjunto_id": attachment.id,
                        "correo_adjunto_nivel": doc.nivel,
                    },
                )
            )

        return _ResultadoAdjunto(
            ok=all(r.ok for r in resultados),
            paginas_aceptadas=sum(r.paginas_aceptadas for r in resultados),
        )

    def _ingerir(
        self,
        *,
        msg: EmailMessage,
        att_id: str,
        nombre: str,
        content_type: str,
        file_bytes: bytes,
        contexto: ContextoCorreo | None,
        extra_meta: dict | None,
    ) -> _ResultadoAdjunto:
        """Troceo, sha256 e intake de un fichero (directo o interior).

        ``ok`` si TODAS sus páginas se aceptaron; ``paginas_aceptadas``
        cuenta las aceptadas, nuevas o duplicadas (DA7).
        """
        attachment_sha256 = hashlib.sha256(file_bytes).hexdigest()

        # Splitting de PDF: si el adjunto es PDF multi-página, devuelve
        # una página por elemento; si es 1 página o no es PDF, una sola
        # PreparedDocument con was_split=False.
        try:
            prepared_pages = self._splitter.split(
                filename=nombre,
                mime_type=content_type,
                file_bytes=file_bytes,
            )
        except Exception as exc:
            logger.error(
                "msg=%s att=%s error splitting PDF: %s",
                msg.id,
                att_id,
                exc,
            )
            return _ResultadoAdjunto(ok=False, paginas_aceptadas=0)

        all_pages_ok = True
        aceptadas = 0
        for prepared in prepared_pages:
            page_ok = self._submit_page_to_orchestrator(
                msg=msg,
                attachment_sha256=attachment_sha256,
                prepared=prepared,
                contexto=contexto,
                extra_meta=extra_meta,
            )
            all_pages_ok = all_pages_ok and page_ok
            aceptadas += 1 if page_ok else 0

        return _ResultadoAdjunto(ok=all_pages_ok, paginas_aceptadas=aceptadas)

    def _submit_page_to_orchestrator(
        self,
        *,
        msg: EmailMessage,
        attachment_sha256: str,
        prepared: PreparedDocument,
        contexto: ContextoCorreo | None,
        extra_meta: dict | None,
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
        # F-054, R15: la página de un documento interior lleva además de
        # qué correo adjunto sale; la de un directo, el dict de siempre (R16).
        if extra_meta is not None:
            meta.update(extra_meta)

        try:
            ack = self._orchestrator.submit_email_received(
                meta=meta,
                file_bytes=prepared.file_bytes,
                filename=prepared.filename,
                content_type=prepared.mime_type,
                contexto_correo=contexto,
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
    def _contexto_del_correo(
        self,
        *,
        msg: EmailMessage,
        mailbox: str,
    ) -> ContextoCorreo | None:
        """Asunto + parte única del cuerpo del mensaje, o ``None`` (F-048).

        Sin ``uniqueBody`` el contexto lleva solo el asunto (R3): nunca se
        pide el ``body``. Si Graph falla, se sigue sin contexto (R5). Los
        logs llevan la huella abreviada, los caracteres y ``truncado``,
        nunca el texto (R36); del error, solo el tipo, porque su mensaje
        podría citar el correo.
        """
        try:
            contenido = self._mailbox.get_contenido(
                mailbox=mailbox,
                message_id=msg.id,
            )
            contexto = construir_contexto_correo(
                contenido.asunto,
                contenido.cuerpo_unico,
                max_caracteres=self._correo_max_caracteres,
                recibido_utc=_to_iso_utc(msg.received_datetime) or None,
            )
        except Exception as exc:  # noqa: BLE001 — cualquier fallo: sin contexto
            logger.warning(
                "msg=%s sin contexto de correo (%s): se sigue con los adjuntos",
                msg.id,
                type(exc).__name__,
            )
            return None

        logger.info(
            "msg=%s contexto de correo sha=%s caracteres=%d truncado=%s",
            msg.id,
            contexto.sha256[:8],
            contexto.caracteres_originales,
            contexto.truncado,
        )
        return contexto

    @staticmethod
    def _es_correo_adjunto(att: EmailAttachment, max_bytes: int) -> bool:
        """Un adjunto de tipo correo se abre si no es inline, ni
        ``referenceAttachment``, ni supera el límite (F-054, R1-R2).

        Los logs llevan id, tipo y tamaño, NUNCA ``att.name``: Graph pone
        ahí el asunto del correo interior (R25).
        """
        if att.is_inline:
            logger.info(
                "att=%s correo adjunto inline type=%s size=%dB → descartado",
                att.id,
                att.content_type,
                att.size,
            )
            return False
        if att.odata_type == _ODATA_REFERENCE:
            logger.info(
                "att=%s correo adjunto referenceAttachment type=%s size=%dB → descartado",
                att.id,
                att.content_type,
                att.size,
            )
            return False
        if max_bytes > 0 and att.size > max_bytes:
            logger.warning(
                "att=%s correo adjunto type=%s tamaño %dB excede límite %dB → descartado",
                att.id,
                att.content_type,
                att.size,
                max_bytes,
            )
            return False
        return True

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
