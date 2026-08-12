# ruesma_comun/blobs/conexion.py
"""Fábrica de clientes de Azure Blob Storage.

Espejo de :mod:`ruesma_comun.colas.conexion`. El Blob vive en la MISMA
storage account que las colas; por eso, en local, reutiliza la cadena de
conexión de Azurite. Dos modos:

1. **Cadena de conexión** (``BLOBS_CONNECTION_STRING`` o, en su defecto,
   ``COLAS_CONNECTION_STRING``): desarrollo local contra **Azurite**.
2. **Managed identity** (``BLOBS_ACCOUNT_URL`` =
   ``https://<cuenta>.blob.core.windows.net``): en Container Apps, con
   ``DefaultAzureCredential`` y el rol *Storage Blob Data Contributor*.

Nota Azurite: la cadena de las colas suele traer solo ``QueueEndpoint``
(puerto 10001). Para Blob hace falta ``BlobEndpoint`` (puerto 10000). Si la
cadena trae el QueueEndpoint de Azurite y NO el BlobEndpoint, este módulo lo
deriva automáticamente (10001 -> 10000), de modo que el ``.env`` existente
(pensado para colas) funciona también para Blob sin tocar nada.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

logger = logging.getLogger(__name__)

# Contenedores canónicos del hand-off entre workers (única fuente de verdad).
# Son EFÍMEROS: una lifecycle policy los purga a los 7-30 días. El dato
# durable vive en SharePoint (PDF) y PostgreSQL (datos extraídos/valoración).
CONTENEDOR_INPUT = "input"          # input/{document_id}.pdf      (lo deja sv1)
CONTENEDOR_ENVELOPES = "envelopes"  # envelopes/{document_id}_{fase}.json (sv2)

TODOS_LOS_CONTENEDORES = (CONTENEDOR_INPUT, CONTENEDOR_ENVELOPES)

# Cadena de conexión well-known de Azurite, COMPLETA (incluye BlobEndpoint).
# Úsala SOLO en local. En la nube: BLOBS_ACCOUNT_URL + managed identity.
AZURITE_CONNECTION_STRING = (
    "DefaultEndpointsProtocol=http;"
    "AccountName=devstoreaccount1;"
    "AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/"
    "K1SZFPTOtr/KBHBeksoGMGw==;"
    "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
    "QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;"
)


def _normalizar_conn_para_blob(conn: str) -> str:
    """Garantiza que la cadena tenga BlobEndpoint cuando es Azurite.

    Si ya trae ``BlobEndpoint=`` se devuelve igual. Si trae el
    ``QueueEndpoint`` de Azurite (``127.0.0.1:10001``) y no el de blob, se
    deriva el ``BlobEndpoint`` apuntando al puerto 10000 y se añade. En
    cualquier otro caso (cadena de producción con AccountKey/AccountName) se
    devuelve tal cual: el SDK ya resuelve el endpoint de blob.
    """
    if "BlobEndpoint=" in conn:
        return conn
    if "QueueEndpoint=" in conn and "127.0.0.1:10001" in conn:
        # Azurite: el blob escucha en 10000, las colas en 10001.
        blob_ep = "BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
        sep = "" if conn.endswith(";") else ";"
        nueva = f"{conn}{sep}{blob_ep}"
        logger.info(
            "[blobs] cadena sin BlobEndpoint; derivado de Azurite "
            "(QueueEndpoint:10001 -> BlobEndpoint:10000)."
        )
        return nueva
    return conn


@dataclass(frozen=True)
class ConfiguracionBlobs:
    """Config de conexión. Exactamente uno de los dos campos debe venir."""

    connection_string: str | None = None
    account_url: str | None = None

    def __post_init__(self) -> None:
        if bool(self.connection_string) == bool(self.account_url):
            raise ValueError(
                "ConfiguracionBlobs: indica connection_string (local/Azurite) "
                "O account_url (managed identity), pero no ambos ni ninguno."
            )


class FabricaBlobs:
    """Crea clientes de contenedor/blob y garantiza que el contenedor existe.

    La credencial de managed identity se crea perezosamente y una sola vez.
    """

    def __init__(self, config: ConfiguracionBlobs) -> None:
        self._config = config
        self._credential = None  # lazy: solo en modo account_url
        self._service: BlobServiceClient | None = None

    # ----------------------------------------------------------- #
    def _servicio(self) -> BlobServiceClient:
        if self._service is None:
            if self._config.connection_string:
                conn = _normalizar_conn_para_blob(self._config.connection_string)
                self._service = BlobServiceClient.from_connection_string(conn)
            else:
                self._service = BlobServiceClient(
                    account_url=self._config.account_url,
                    credential=self._obtener_credencial(),
                )
        return self._service

    def contenedor(self, nombre: str, *, crear: bool = True):
        client = self._servicio().get_container_client(nombre)
        if crear:
            self._asegurar_contenedor(client)
        return client

    def blob(self, contenedor: str, nombre: str, *, crear_contenedor: bool = True):
        cont = self.contenedor(contenedor, crear=crear_contenedor)
        return cont.get_blob_client(nombre)

    def asegurar_todos(self) -> None:
        """Crea (si no existen) los contenedores del sistema. Idempotente."""
        for nombre in TODOS_LOS_CONTENEDORES:
            self.contenedor(nombre)

    # ----------------------------------------------------------- #
    def _obtener_credencial(self):
        if self._credential is None:
            from azure.identity import DefaultAzureCredential

            self._credential = DefaultAzureCredential()
        return self._credential

    @staticmethod
    def _asegurar_contenedor(client) -> None:
        try:
            client.create_container()
            logger.info("[blobs] creado contenedor %s", client.container_name)
        except ResourceExistsError:
            pass
