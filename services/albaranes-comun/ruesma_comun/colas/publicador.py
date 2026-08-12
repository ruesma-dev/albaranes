# ruesma_comun/colas/publicador.py
"""Publicador de mensajes hacia las colas del sistema.

Es el adaptador de SALIDA que sustituye a los clientes HTTP entre
servicios (p. ej. el ``HttpOrchestratorClient`` de sv4 o el trigger de
valoración de sv3). Dos sabores:

- :class:`PublicadorColas` — publica y propaga errores. Para los pasos
  del pipeline donde NO encolar es un fallo del paso (el mensaje debe
  volver a la cola de origen y reintentarse).
- :class:`PublicadorBestEffort` — envoltorio que captura y loguea, no
  lanza nunca. Para sv4, donde la filosofía actual se conserva: el dato
  ya está persistido en BBDD antes de notificar; el mensaje es solo el
  disparador y su pérdida es recuperable a mano.
"""
from __future__ import annotations

import logging

from azure.storage.queue import QueueClient

from ruesma_comun.colas.conexion import FabricaColas
from ruesma_comun.colas.mensajes import MensajeBase

logger = logging.getLogger(__name__)


class PublicadorColas:
    """Publica mensajes tipados. Un cliente por cola, cacheado."""

    def __init__(self, fabrica: FabricaColas, *, emitido_por: str) -> None:
        self._fabrica = fabrica
        self._emitido_por = emitido_por
        self._clientes: dict[str, QueueClient] = {}

    def publicar(self, nombre_cola: str, mensaje: MensajeBase) -> None:
        if mensaje.emitido_por is None:
            mensaje = mensaje.model_copy(update={"emitido_por": self._emitido_por})
        cliente = self._cliente(nombre_cola)
        cliente.send_message(mensaje.a_texto())
        logger.info(
            "[colas] publicado tipo=%s document_id=%s → %s",
            mensaje.tipo,
            mensaje.document_id,
            nombre_cola,
        )

    def _cliente(self, nombre_cola: str) -> QueueClient:
        if nombre_cola not in self._clientes:
            self._clientes[nombre_cola] = self._fabrica.cliente(nombre_cola)
        return self._clientes[nombre_cola]


class PublicadorBestEffort:
    """Decorador best-effort sobre :class:`PublicadorColas`.

    Devuelve ``True`` si publicó, ``False`` si no pudo (ya logueado).
    """

    def __init__(self, publicador: PublicadorColas) -> None:
        self._publicador = publicador

    def publicar(self, nombre_cola: str, mensaje: MensajeBase) -> bool:
        try:
            self._publicador.publicar(nombre_cola, mensaje)
            return True
        except Exception:  # noqa: BLE001 — best-effort explícito
            logger.exception(
                "[colas] no se pudo publicar tipo=%s document_id=%s → %s "
                "(best-effort: el dato ya está en BBDD; reintentar desde sv4)",
                mensaje.tipo,
                mensaje.document_id,
                nombre_cola,
            )
            return False
