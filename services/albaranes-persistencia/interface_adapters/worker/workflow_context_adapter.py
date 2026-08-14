# interface_adapters/worker/workflow_context_adapter.py
"""Contexto de email desde ``workflow_runs`` (F-002 · R12).

sv1 guarda en ``workflow_runs.payload_json`` todo lo que se sabe del
correo y del adjunto al crear el workflow. En modo colas, el mensaje de
``q-persistencia`` solo trae ``document_id`` + ``correlation_key``, asi
que sv3 persistia el merge sin ``email_received_datetime`` (NULL) y sin
los metadatos del adjunto. Este adaptador recupera esa fila y traduce el
payload a las claves que ya espera el repositorio de sv3.

``ruesma_comun`` NO se toca: se usa su API publica
(``RepositorioWorkflows.obtener_por_correlation_key``) tal cual. Tocarlo
obligaria a reconstruir cuatro imagenes.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from interface_adapters.worker.ports import FuenteContextoEmail

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sv3-worker][contexto-email]"

#: payload de sv1 -> bloque ``email`` del contexto de sv3.
_MAPEO_EMAIL: tuple[tuple[str, str], ...] = (
    ("email_message_id", "id"),
    ("subject", "subject"),
    ("from_address", "sender"),
    ("email_received_at_utc", "receivedDateTime"),
)

#: payload de sv1 -> bloque ``document`` del contexto de sv3.
_MAPEO_DOCUMENTO: tuple[tuple[str, str], ...] = (
    ("attachment_filename", "source_attachment_filename"),
    ("attachment_content_type", "source_attachment_mime_type"),
    ("attachment_sha256", "source_attachment_sha256"),
    ("page_number", "page_number"),
    ("total_pages", "page_count"),
)


def _traducir(payload: Dict[str, Any], mapeo) -> Dict[str, Any]:
    """Bloque con las claves presentes en el payload (las ausentes no se
    inventan: mejor NULL que un valor de relleno)."""
    return {
        destino: payload[origen]
        for origen, destino in mapeo
        if payload.get(origen) is not None
    }


class FuenteContextoEmailWorkflows(FuenteContextoEmail):
    """Implementa el puerto leyendo ``workflow_runs``.

    ``repositorio`` es un ``ruesma_comun.workflows.RepositorioWorkflows``
    (o cualquier objeto con ``obtener_por_correlation_key``).

    Best-effort de principio a fin: sin fila, con payload roto o con la
    BBDD caida devuelve ``{}`` y el worker sigue con el contexto de
    siempre. Perder la fecha del correo degrada el guard de año; que
    reviente el worker, no.
    """

    def __init__(self, repositorio) -> None:  # noqa: ANN001 — duck typing
        self._repositorio = repositorio

    def obtener(self, correlation_key: str) -> Dict[str, Any]:
        if not (correlation_key or "").strip():
            return {}
        try:
            fila = self._repositorio.obtener_por_correlation_key(
                correlation_key,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo leer workflow_runs. correlation_key=%s",
                _LOG_PREFIX, correlation_key,
            )
            return {}
        if fila is None:
            logger.info(
                "%s sin fila de workflow para correlation_key=%s; el "
                "contexto va vacio.", _LOG_PREFIX, correlation_key,
            )
            return {}

        try:
            payload = json.loads(getattr(fila, "payload_json", "") or "{}")
        except (TypeError, ValueError):
            logger.warning(
                "%s payload_json no es JSON valido. correlation_key=%s",
                _LOG_PREFIX, correlation_key,
            )
            return {}
        if not isinstance(payload, dict):
            logger.warning(
                "%s payload_json no es un objeto (%s). correlation_key=%s",
                _LOG_PREFIX, type(payload).__name__, correlation_key,
            )
            return {}

        contexto: Dict[str, Any] = {}
        email = _traducir(payload, _MAPEO_EMAIL)
        if email:
            contexto["email"] = email
        documento = _traducir(payload, _MAPEO_DOCUMENTO)
        if documento:
            contexto["document"] = documento
        logger.info(
            "%s contexto reconstruido correlation_key=%s email=%s "
            "documento=%s recibido=%s",
            _LOG_PREFIX, correlation_key, bool(email), bool(documento),
            email.get("receivedDateTime"),
        )
        return contexto
