# ruesma_comun/colas/conexion.py
"""Fábrica de clientes de Azure Storage Queue.

Dos modos, decididos por configuración (el código de los servicios no
distingue local de nube — mismo binario en ambos sitios):

1. **Cadena de conexión** (``COLAS_CONNECTION_STRING``): para desarrollo
   local contra **Azurite** y para entornos sin managed identity.
2. **Managed identity** (``COLAS_ACCOUNT_URL`` =
   ``https://<cuenta>.queue.core.windows.net``): en Container Apps, con
   ``DefaultAzureCredential`` y el rol *Storage Queue Data Contributor*.
   Sin secretos.

La cadena de conexión de Azurite (cuenta de desarrollo well-known) está
en ``local/docker-compose.azurite.yml`` y en el README del paquete.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from azure.core.exceptions import ResourceExistsError
from azure.storage.queue import QueueClient

logger = logging.getLogger(__name__)

# Nombres canónicos de las colas del sistema (única fuente de verdad).
COLA_EMAILS = "q-emails"
COLA_EXTRACCION = "q-extraccion"
COLA_PERSISTENCIA = "q-persistencia"
COLA_VALORACION = "q-valoracion"
COLA_FEEDBACK = "q-feedback"

TODAS_LAS_COLAS = (
    COLA_EMAILS,
    COLA_EXTRACCION,
    COLA_PERSISTENCIA,
    COLA_VALORACION,
    COLA_FEEDBACK,
)

SUFIJO_POISON = "-poison"

# Cadena de conexión de la cuenta de desarrollo well-known de Azurite
# (idéntica en todas las instalaciones de Azurite). Úsala SOLO en local;
# en la nube se usa COLAS_ACCOUNT_URL + managed identity.
AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/"
    "K1SZFPTOtr/KBHBeksoGMGw==;"
    "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
)


def nombre_poison(nombre_cola: str) -> str:
    return f"{nombre_cola}{SUFIJO_POISON}"


@dataclass(frozen=True)
class ConfiguracionColas:
    """Config de conexión. Exactamente uno de los dos campos debe venir.

    Variables de entorno esperadas en los servicios:
      - ``COLAS_CONNECTION_STRING`` (local / Azurite), o
      - ``COLAS_ACCOUNT_URL`` (nube, managed identity).
    """

    connection_string: str | None = None
    account_url: str | None = None

    def __post_init__(self) -> None:
        if bool(self.connection_string) == bool(self.account_url):
            raise ValueError(
                "ConfiguracionColas: indica connection_string (local/Azurite) "
                "O account_url (managed identity), pero no ambos ni ninguno."
            )


class FabricaColas:
    """Crea ``QueueClient`` ya configurados y garantiza que la cola existe.

    La credencial de managed identity se crea perezosamente y UNA sola
    vez (``DefaultAzureCredential`` cachea tokens internamente).
    """

    def __init__(self, config: ConfiguracionColas) -> None:
        self._config = config
        self._credential = None  # lazy: solo en modo account_url

    # ----------------------------------------------------------- #
    def cliente(self, nombre_cola: str, *, crear: bool = True) -> QueueClient:
        if self._config.connection_string:
            client = QueueClient.from_connection_string(
                self._config.connection_string,
                queue_name=nombre_cola,
            )
        else:
            client = QueueClient(
                account_url=self._config.account_url,
                queue_name=nombre_cola,
                credential=self._obtener_credencial(),
            )
        if crear:
            self._asegurar_cola(client)
        return client

    def cliente_poison(self, nombre_cola: str) -> QueueClient:
        return self.cliente(nombre_poison(nombre_cola))

    def asegurar_todas(self) -> None:
        """Crea (si no existen) todas las colas del sistema + sus poison.

        Pensado para el bootstrap local y para el job de aprovisionado.
        En producción las colas las crea el script de infraestructura,
        pero esto hace el sistema autocurativo e idempotente.
        """
        for nombre in TODAS_LAS_COLAS:
            self.cliente(nombre)
            self.cliente(nombre_poison(nombre))

    # ----------------------------------------------------------- #
    def _obtener_credencial(self):
        if self._credential is None:
            # Import perezoso: azure-identity solo hace falta en nube.
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
        return self._credential

    @staticmethod
    def _asegurar_cola(client: QueueClient) -> None:
        try:
            client.create_queue()
            logger.info("[colas] creada cola %s", client.queue_name)
        except ResourceExistsError:
            pass
