# interface_adapters/worker/correo_adapter.py
"""Adaptador de PRODUCCIÓN del puerto ``FuenteContextoCorreo`` sobre Blob (F-048).

Lee el blob lateral ``input/{document_id}.correo.json`` que dejó sv1 (o
``encolar_extraccion.py --correo``) con la MISMA función de ``ruesma_comun``
con la que se escribió: si cada lado leyera a su manera, el mismo correo
podría validar en uno y no en el otro.

- Blob ausente o que no valida ⇒ ``None``: el documento se extrae sin correo
  (R11). El aviso del log lo escribe ``leer_contexto_correo`` y nunca lleva
  texto del correo (R36).
- Fallo de red ⇒ se propaga: la cola reintenta, como con el PDF, en vez de
  extraer sin correo por un corte transitorio.
"""
from __future__ import annotations

from interface_adapters.worker.ports import FuenteContextoCorreo
from ruesma_comun.correo import ContextoCorreo, leer_contexto_correo
from ruesma_comun.correo.contexto import AlmacenJson


class FuenteContextoCorreoBlob(FuenteContextoCorreo):
    """Lee el contexto del correo de ``input/``."""

    def __init__(self, almacen: AlmacenJson) -> None:
        self._almacen = almacen

    def obtener(self, nombre_blob: str) -> ContextoCorreo | None:
        return leer_contexto_correo(self._almacen, nombre_blob)
