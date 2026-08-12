# ruesma_comun/colas/consumidor.py
"""Runtime común de consumo de colas (el "main loop" de cada worker).

Sustituye al servidor HTTP como adaptador de ENTRADA de sv1/sv2/sv3 y
del valorador en la nube. Reglas (alineadas con el doc de arquitectura):

- ``visibility_timeout`` por defecto 600 s: mientras un worker procesa,
  el mensaje es invisible; si el worker muere, el mensaje reaparece solo.
- Si ``dequeue_count`` > ``max_desencolados`` (defecto 5) ANTES de
  procesar → el mensaje va a la cola ``*-poison`` y se invoca
  ``on_poison`` (ahí cada servicio marca su estado ``*_failed`` en
  ``workflow_runs``).
- Si el handler lanza excepción → se loguea y el mensaje se deja en la
  cola (reaparecerá al expirar la visibilidad). El reintento lo da la
  cola, no el proceso — exactamente lo que hacía el FailedWorkflowRetrier
  de sv7, sin proceso residente.
- Mensajes con cuerpo inválido (``MensajeInvalidoError``) van a poison
  INMEDIATAMENTE: reintentar un mensaje corrupto es ruido.
- SIGTERM/SIGINT (escalado a 0 de Container Apps, Ctrl+C local) → se
  termina el mensaje en curso y se sale limpio.

KEDA escala el número de réplicas mirando la longitud de la cola; este
bucle es lo que cada réplica ejecuta. En reposo el bucle duerme
``espera_vacia_s`` entre sondeos hasta que ACA apaga la réplica.
"""
from __future__ import annotations

import logging
import signal
import time
from dataclasses import dataclass
from typing import Callable, Optional

from azure.storage.queue import QueueClient, QueueMessage

from ruesma_comun.colas.mensajes import (
    MensajeBase,
    MensajeInvalidoError,
    desde_texto,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConfiguracionConsumidor:
    nombre_cola: str
    tipo_mensaje: str  # discriminador esperado ("extraccion", "valoracion"…)
    visibilidad_s: int = 600
    max_desencolados: int = 5
    espera_vacia_s: float = 5.0


# Firma del handler de negocio: recibe el mensaje tipado, no devuelve
# nada; si lanza, el runtime gestiona el reintento/poison.
ManejadorMensaje = Callable[[MensajeBase], None]
# Firma del callback de poison: (mensaje | None, cuerpo_crudo, motivo).
ManejadorPoison = Callable[[Optional[MensajeBase], str, str], None]


class ConsumidorCola:
    def __init__(
        self,
        *,
        config: ConfiguracionConsumidor,
        cliente: QueueClient,
        cliente_poison: QueueClient,
        handler: ManejadorMensaje,
        on_poison: ManejadorPoison | None = None,
    ) -> None:
        self._config = config
        self._cliente = cliente
        self._poison = cliente_poison
        self._handler = handler
        self._on_poison = on_poison
        self._parar = False

    # ----------------------------------------------------------- #
    # Bucle principal (lo invoca el main.py del worker).
    # ----------------------------------------------------------- #
    def run_forever(self) -> None:
        self._instalar_senales()
        logger.info(
            "[consumidor] escuchando cola=%s tipo=%s visibilidad=%ss "
            "max_desencolados=%d",
            self._config.nombre_cola,
            self._config.tipo_mensaje,
            self._config.visibilidad_s,
            self._config.max_desencolados,
        )
        while not self._parar:
            try:
                procesado = self.procesar_uno()
            except Exception:
                # Errores de transporte (red, auth): log y seguimos.
                logger.exception("[consumidor] error de transporte; continúo…")
                procesado = False
            if not procesado and not self._parar:
                time.sleep(self._config.espera_vacia_s)
        logger.info("[consumidor] parada limpia de cola=%s", self._config.nombre_cola)

    # ----------------------------------------------------------- #
    # Una iteración (testeable, sin sleep). Devuelve True si hubo mensaje.
    # ----------------------------------------------------------- #
    def procesar_uno(self) -> bool:
        msg: QueueMessage | None = self._cliente.receive_message(
            visibility_timeout=self._config.visibilidad_s,
        )
        if msg is None:
            return False

        cuerpo = msg.content if isinstance(msg.content, str) else str(msg.content)
        desencolados = int(msg.dequeue_count or 1)

        # 1) Veneno por agotamiento de reintentos — ANTES de procesar.
        if desencolados > self._config.max_desencolados:
            self._envenenar(
                msg,
                cuerpo,
                motivo=(
                    f"dequeue_count={desencolados} supera el máximo "
                    f"({self._config.max_desencolados})"
                ),
                mensaje=self._parsear_silencioso(cuerpo),
            )
            return True

        # 2) Veneno por cuerpo inválido — inmediato, sin reintentos.
        try:
            mensaje = desde_texto(cuerpo, tipo_esperado=self._config.tipo_mensaje)
        except MensajeInvalidoError as exc:
            self._envenenar(msg, cuerpo, motivo=str(exc), mensaje=None)
            return True

        # 3) Procesado normal.
        logger.info(
            "[consumidor] cola=%s document_id=%s intento=%d",
            self._config.nombre_cola,
            mensaje.document_id,
            desencolados,
        )
        try:
            self._handler(mensaje)
        except Exception:
            # El mensaje se queda en la cola: reaparece al expirar la
            # visibilidad y KEDA/las réplicas lo reintentarán.
            logger.exception(
                "[consumidor] handler falló (document_id=%s intento=%d/%d); "
                "el mensaje se reintentará",
                mensaje.document_id,
                desencolados,
                self._config.max_desencolados,
            )
            return True

        self._cliente.delete_message(msg)
        return True

    # ----------------------------------------------------------- #
    def _envenenar(
        self,
        msg: QueueMessage,
        cuerpo: str,
        *,
        motivo: str,
        mensaje: MensajeBase | None,
    ) -> None:
        logger.error(
            "[consumidor] → poison cola=%s motivo=%s document_id=%s",
            self._config.nombre_cola,
            motivo,
            mensaje.document_id if mensaje else "(ilegible)",
        )
        try:
            self._poison.send_message(cuerpo)
        except Exception:
            # Si ni siquiera podemos envenenar, NO borramos: mejor que
            # el mensaje siga reapareciendo a perderlo en silencio.
            logger.exception("[consumidor] no se pudo escribir en poison; no borro")
            return
        self._cliente.delete_message(msg)
        if self._on_poison is not None:
            try:
                self._on_poison(mensaje, cuerpo, motivo)
            except Exception:
                logger.exception("[consumidor] on_poison falló (ignorado)")

    @staticmethod
    def _parsear_silencioso(cuerpo: str) -> MensajeBase | None:
        try:
            return desde_texto(cuerpo)
        except MensajeInvalidoError:
            return None

    # ----------------------------------------------------------- #
    def _instalar_senales(self) -> None:
        def _manejador(signum, _frame):  # noqa: ANN001
            logger.info("[consumidor] señal %s recibida; paro tras el mensaje actual", signum)
            self._parar = True

        try:
            signal.signal(signal.SIGTERM, _manejador)
            signal.signal(signal.SIGINT, _manejador)
        except ValueError:
            # No estamos en el hilo principal (p. ej. tests): sin señales.
            logger.debug("[consumidor] señales no instaladas (hilo secundario)")

    def solicitar_parada(self) -> None:
        self._parar = True
