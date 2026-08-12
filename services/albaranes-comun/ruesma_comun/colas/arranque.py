# ruesma_comun/colas/arranque.py
"""Arranque de productores y workers de cola desde el entorno.

Convierte la configuración (variables de entorno) en una ``FabricaColas`` y,
sobre ella, en un ``PublicadorColas`` (productor) o en un bucle de
``ConsumidorCola`` (worker). Es lo que cada ``main.py`` usa para volverse
worker en ~3 líneas, idéntico en local (Azurite) y en la nube (managed
identity); la diferencia la dan SOLO las variables de entorno:

  - Local / Azurite:  ``COLAS_CONNECTION_STRING`` = cadena de Azurite.
  - Nube (ACA):       ``COLAS_ACCOUNT_URL`` = https://<cuenta>.queue.core.windows.net
                      (+ rol "Storage Queue Data Contributor" en la identidad).

Ejemplo de ``main.py`` de un worker::

    from ruesma_comun.colas import COLA_EXTRACCION
    from ruesma_comun.colas.arranque import ejecutar_worker

    def _handler(mensaje):
        ...  # lógica del servicio (descarga SharePoint, fase1, publica siguiente)

    def main() -> int:
        return ejecutar_worker(
            nombre_cola=COLA_EXTRACCION,
            tipo_mensaje="extraccion",
            handler=_handler,
            emitido_por="ca-sv2-extraccion",
        )
"""
from __future__ import annotations

import logging
import os
from typing import Mapping

from ruesma_comun.colas.conexion import ConfiguracionColas, FabricaColas
from ruesma_comun.colas.consumidor import (
    ConfiguracionConsumidor,
    ConsumidorCola,
    ManejadorMensaje,
    ManejadorPoison,
)
from ruesma_comun.colas.publicador import PublicadorColas

logger = logging.getLogger(__name__)

ENV_CONNECTION_STRING = "COLAS_CONNECTION_STRING"
ENV_ACCOUNT_URL = "COLAS_ACCOUNT_URL"


class ConfiguracionColasAusenteError(RuntimeError):
    """Ni COLAS_CONNECTION_STRING ni COLAS_ACCOUNT_URL están definidas."""


def construir_fabrica_desde_entorno(
    env: Mapping[str, str] | None = None,
) -> FabricaColas:
    """Crea la ``FabricaColas`` leyendo el entorno.

    Prioridad: si está ``COLAS_CONNECTION_STRING`` (local/Azurite) se usa
    esa; si no, ``COLAS_ACCOUNT_URL`` (managed identity). Si no hay ninguna,
    se lanza :class:`ConfiguracionColasAusenteError`.
    """
    env = env if env is not None else os.environ
    conn = env.get(ENV_CONNECTION_STRING) or None
    account_url = env.get(ENV_ACCOUNT_URL) or None

    if conn:
        logger.info("[colas] modo cadena de conexión (local/Azurite)")
        return FabricaColas(ConfiguracionColas(connection_string=conn))
    if account_url:
        logger.info("[colas] modo managed identity (%s)", account_url)
        return FabricaColas(ConfiguracionColas(account_url=account_url))

    raise ConfiguracionColasAusenteError(
        f"Define {ENV_CONNECTION_STRING} (local/Azurite) o "
        f"{ENV_ACCOUNT_URL} (managed identity)."
    )


def construir_publicador(
    *,
    emitido_por: str,
    env: Mapping[str, str] | None = None,
    fabrica: FabricaColas | None = None,
) -> PublicadorColas:
    """Crea un ``PublicadorColas`` listo para usar (productor)."""
    fabrica = fabrica or construir_fabrica_desde_entorno(env)
    return PublicadorColas(fabrica, emitido_por=emitido_por)


def construir_consumidor(
    *,
    nombre_cola: str,
    tipo_mensaje: str,
    handler: ManejadorMensaje,
    on_poison: ManejadorPoison | None = None,
    visibilidad_s: int = 600,
    max_desencolados: int = 5,
    espera_vacia_s: float = 5.0,
    env: Mapping[str, str] | None = None,
    fabrica: FabricaColas | None = None,
) -> ConsumidorCola:
    """Crea un ``ConsumidorCola`` (worker) con sus colas ya garantizadas."""
    fabrica = fabrica or construir_fabrica_desde_entorno(env)
    return ConsumidorCola(
        config=ConfiguracionConsumidor(
            nombre_cola=nombre_cola,
            tipo_mensaje=tipo_mensaje,
            visibilidad_s=visibilidad_s,
            max_desencolados=max_desencolados,
            espera_vacia_s=espera_vacia_s,
        ),
        cliente=fabrica.cliente(nombre_cola),
        cliente_poison=fabrica.cliente_poison(nombre_cola),
        handler=handler,
        on_poison=on_poison,
    )


def ejecutar_worker(
    *,
    nombre_cola: str,
    tipo_mensaje: str,
    handler: ManejadorMensaje,
    emitido_por: str | None = None,  # solo informativo en el log
    on_poison: ManejadorPoison | None = None,
    visibilidad_s: int = 600,
    max_desencolados: int = 5,
    espera_vacia_s: float = 5.0,
    env: Mapping[str, str] | None = None,
) -> int:
    """Arranca el bucle de consumo (bloqueante). Devuelve código de salida.

    Es el cuerpo del ``main.py`` de un worker: construye la fábrica desde el
    entorno, garantiza la cola + su poison, y entra en ``run_forever`` hasta
    recibir SIGTERM/SIGINT (escalado a 0 de Container Apps / Ctrl+C local).
    """
    try:
        fabrica = construir_fabrica_desde_entorno(env)
    except ConfiguracionColasAusenteError:
        logger.exception("[colas] no hay configuración de colas; no arranco")
        return 2

    consumidor = construir_consumidor(
        nombre_cola=nombre_cola,
        tipo_mensaje=tipo_mensaje,
        handler=handler,
        on_poison=on_poison,
        visibilidad_s=visibilidad_s,
        max_desencolados=max_desencolados,
        espera_vacia_s=espera_vacia_s,
        fabrica=fabrica,
    )
    logger.info(
        "[arranque] worker %s sobre cola=%s tipo=%s",
        emitido_por or "(sin-nombre)",
        nombre_cola,
        tipo_mensaje,
    )
    consumidor.run_forever()
    return 0
