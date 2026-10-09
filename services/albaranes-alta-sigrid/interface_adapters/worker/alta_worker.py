# interface_adapters/worker/alta_worker.py
"""Handler del worker de sv9 (consumidor de ``q-feedback``, F-053).

Traduce el ``MensajeFeedback`` (``document_id``, ``accion``) y llama a
``AltaSigridService.procesar``:

- Todo resultado de negocio (cualquier estado, también «ignorado») vuelve sin
  excepción ⇒ el consumidor común CONFIRMA (borra) el mensaje.
- Solo un fallo de infraestructura antes de reclamar (el servicio lo deja
  propagar) llega aquí como excepción ⇒ el mensaje se queda en la cola y se
  reintenta (y a poison tras ``max_desencolados``).
- Un mensaje de otro ``tipo`` (o una ``accion`` desconocida) lo manda a poison
  el consumidor común antes de llegar aquí (``tipo_mensaje="feedback"``).
"""
from __future__ import annotations

import logging
from typing import Protocol

from ruesma_comun.colas import MensajeFeedback
from ruesma_comun.colas.consumidor import ManejadorMensaje

from application.alta_sigrid_service import ResultadoProceso

logger = logging.getLogger(__name__)


class _Servicio(Protocol):
    def procesar(self, document_id: str, accion: str) -> ResultadoProceso: ...


def construir_handler_alta(*, servicio: _Servicio) -> ManejadorMensaje:
    """El handler que el consumidor invoca por cada mensaje."""

    def handler(mensaje: MensajeFeedback) -> None:
        accion = getattr(mensaje, "accion", "alta")
        logger.info("[ca-sv9-alta-sigrid] document_id=%s accion=%s START",
                    mensaje.document_id, accion)
        resultado = servicio.procesar(mensaje.document_id, accion)
        logger.info(
            "[ca-sv9-alta-sigrid] document_id=%s decision=%s estado=%s %s",
            mensaje.document_id, resultado.decision.value,
            resultado.estado.value if resultado.estado else "-", resultado.motivo,
        )

    return handler
