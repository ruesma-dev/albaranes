# ruesma_comun/blobs/almacen.py
"""API de alto nivel sobre Blob: get/put de bytes por contenedor+nombre.

Pensado para el hand-off entre workers (PDF de entrada y envelope). Es el
equivalente al ``PublicadorColas``/``ConsumidorCola`` pero para artefactos
binarios/JSON. Todo es por referencia: el mensaje de cola solo lleva el
``document_id`` y el contenido pesado se resuelve aquí.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, Mapping

from azure.core.exceptions import ResourceNotFoundError

from ruesma_comun.blobs.conexion import (
    ConfiguracionBlobs,
    FabricaBlobs,
)

logger = logging.getLogger(__name__)

ENV_CONNECTION_STRING = "BLOBS_CONNECTION_STRING"
ENV_CONNECTION_STRING_FALLBACK = "COLAS_CONNECTION_STRING"
ENV_ACCOUNT_URL = "BLOBS_ACCOUNT_URL"


class ConfiguracionBlobsAusenteError(RuntimeError):
    """No hay ni cadena de conexión ni account_url para Blob."""


class BlobNoEncontradoError(FileNotFoundError):
    """El blob pedido no existe (p. ej. sv2 aún no escribió el envelope)."""


class AlmacenBlobs:
    """Operaciones de blob de grano grueso, idempotentes y con logging."""

    def __init__(self, fabrica: FabricaBlobs) -> None:
        self._fabrica = fabrica

    # ----------------------------------------------------------- #
    def put_bytes(
        self,
        contenedor: str,
        nombre: str,
        data: bytes,
        *,
        content_type: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        """Sube ``data`` a ``contenedor/nombre`` (sobrescribe si existe)."""
        from azure.storage.blob import ContentSettings

        blob = self._fabrica.blob(contenedor, nombre)
        content_settings = (
            ContentSettings(content_type=content_type) if content_type else None
        )
        blob.upload_blob(
            data,
            overwrite=True,
            content_settings=content_settings,
            metadata=dict(metadata) if metadata else None,
        )
        logger.info(
            "[blobs] put %s/%s (%d bytes, type=%s)",
            contenedor, nombre, len(data), content_type or "n/a",
        )

    def put_json(
        self,
        contenedor: str,
        nombre: str,
        objeto: Any,
        *,
        metadata: Mapping[str, str] | None = None,
    ) -> None:
        data = json.dumps(objeto, ensure_ascii=False, indent=2).encode("utf-8")
        self.put_bytes(
            contenedor, nombre, data,
            content_type="application/json; charset=utf-8",
            metadata=metadata,
        )

    # ----------------------------------------------------------- #
    def get_bytes(self, contenedor: str, nombre: str) -> bytes:
        blob = self._fabrica.blob(contenedor, nombre, crear_contenedor=False)
        try:
            datos = blob.download_blob().readall()
        except ResourceNotFoundError as exc:
            raise BlobNoEncontradoError(
                f"No existe el blob {contenedor}/{nombre}."
            ) from exc
        logger.info("[blobs] get %s/%s (%d bytes)", contenedor, nombre, len(datos))
        return datos

    def get_con_metadata(
        self, contenedor: str, nombre: str
    ) -> tuple[bytes, dict[str, str], str | None]:
        """Devuelve (bytes, metadata, content_type) del blob."""
        blob = self._fabrica.blob(contenedor, nombre, crear_contenedor=False)
        try:
            stream = blob.download_blob()
            datos = stream.readall()
        except ResourceNotFoundError as exc:
            raise BlobNoEncontradoError(
                f"No existe el blob {contenedor}/{nombre}."
            ) from exc
        props = stream.properties
        metadata = dict(props.metadata or {})
        content_type = None
        if props.content_settings is not None:
            content_type = props.content_settings.content_type
        logger.info(
            "[blobs] get %s/%s (%d bytes, meta=%s)",
            contenedor, nombre, len(datos), list(metadata.keys()),
        )
        return datos, metadata, content_type

    def get_json(self, contenedor: str, nombre: str) -> Any:
        return json.loads(self.get_bytes(contenedor, nombre).decode("utf-8"))

    # ----------------------------------------------------------- #
    def existe(self, contenedor: str, nombre: str) -> bool:
        blob = self._fabrica.blob(contenedor, nombre, crear_contenedor=False)
        return bool(blob.exists())


def construir_almacen_desde_entorno(
    env: Mapping[str, str] | None = None,
) -> AlmacenBlobs:
    """Crea el ``AlmacenBlobs`` leyendo el entorno.

    Prioridad de la cadena de conexión: ``BLOBS_CONNECTION_STRING`` y, si no,
    ``COLAS_CONNECTION_STRING`` (Blob y colas comparten storage account en
    local). Para la nube: ``BLOBS_ACCOUNT_URL`` (managed identity).
    """
    env = env if env is not None else os.environ
    conn = (
        env.get(ENV_CONNECTION_STRING)
        or env.get(ENV_CONNECTION_STRING_FALLBACK)
        or None
    )
    account_url = env.get(ENV_ACCOUNT_URL) or None

    if conn:
        logger.info("[blobs] modo cadena de conexión (local/Azurite)")
        return AlmacenBlobs(FabricaBlobs(ConfiguracionBlobs(connection_string=conn)))
    if account_url:
        logger.info("[blobs] modo managed identity (%s)", account_url)
        return AlmacenBlobs(FabricaBlobs(ConfiguracionBlobs(account_url=account_url)))

    raise ConfiguracionBlobsAusenteError(
        f"Define {ENV_CONNECTION_STRING} o {ENV_CONNECTION_STRING_FALLBACK} "
        f"(local/Azurite) o {ENV_ACCOUNT_URL} (managed identity)."
    )
