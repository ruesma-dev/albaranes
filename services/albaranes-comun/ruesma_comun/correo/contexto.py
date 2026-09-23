# ruesma_comun/correo/contexto.py
"""Contexto de correo de un albaran (F-048, R1).

El texto del correo con el que llega un albaran (asunto + parte UNICA del
cuerpo, ``uniqueBody`` de Graph) viaja de sv1 a sv2 en un blob LATERAL,
``input/{document_id}.correo.json``, nunca dentro del mensaje de cola (D1):
el mensaje solo lleva el nombre del blob en ``MensajeExtraccion.correo_blob``.

Este modulo es la UNICA definicion de ese contexto y de su construccion. La
usan sv1 (al ingerir), sv2 (al leer), ``encolar_extraccion.py`` y los evals:
si cada uno normalizara o recortara a su manera, el mismo correo daria
huellas distintas segun por donde entrara.

Decisiones:

- **Normalizar** es solo espacios: finales de linea a ``\\n``, cualquier
  racha de espacios horizontales (tabuladores, no separables) a UN espacio,
  lineas sin espacios en los bordes y como mucho UNA linea en blanco
  seguida. No se interpreta el texto: no se quitan firmas ni saludos.
- **Recortar** el cuerpo a ``max_caracteres`` (defecto 4.000). El asunto no
  se recorta: es corto por naturaleza y es donde suele ir el codigo.
  ``caracteres_originales`` cuenta el cuerpo ya normalizado y antes del
  recorte, de modo que ``truncado`` equivale a que se perdio texto.
- **La huella** (``sha256``) se calcula sobre lo CONSERVADO: el asunto y el
  cuerpo recortado, separados por una linea en blanco. Dos correos que solo
  difieren en lo recortado comparten huella (lo que llega a la IA es igual);
  dos con distinto asunto y cuerpo vacio no (R3: sin ``uniqueBody`` el
  contexto es solo el asunto, y la huella tiene que distinguirlos).
- **Leer** devuelve ``None`` si el blob falta o su contenido no valida (R11:
  sv2 sigue sin correo). Un fallo de red NO es ninguna de las dos cosas y se
  propaga, para que la cola reintente en vez de extraer sin correo por un
  corte transitorio. El aviso del log nunca lleva texto del correo.

Sin dependencias de Azure en el import: el almacen entra por parametro (la
forma de ``ruesma_comun.blobs.AlmacenBlobs``) y el contenedor se resuelve al
guardar, para que importar el modelo no arrastre el SDK de Blob.
"""
from __future__ import annotations

import hashlib
import logging
import re
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)

MAX_CARACTERES_DEFECTO = 4000
VERSION_CONTEXTO = 1
SUFIJO_BLOB_CORREO = ".correo.json"

# Cualquier espacio que NO sea salto de linea (tabulador, no separable...).
_ESPACIOS_HORIZONTALES = re.compile(r"[^\S\n]+")
# Tres o mas saltos seguidos = mas de una linea en blanco.
_LINEAS_EN_BLANCO = re.compile(r"\n{3,}")


class AlmacenJson(Protocol):
    """Lo que este modulo necesita de un almacen de blobs."""

    def put_json(self, contenedor: str, nombre: str, objeto: Any) -> None: ...

    def get_json(self, contenedor: str, nombre: str) -> Any: ...


class ContextoCorreo(BaseModel):
    """Texto del correo que acompana a un albaran, ya normalizado y recortado."""

    model_config = ConfigDict(extra="ignore")

    version: int = VERSION_CONTEXTO
    asunto: str
    cuerpo: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    caracteres_originales: int = Field(ge=0)
    truncado: bool
    recibido_utc: str | None = None


def _normalizar_asunto(texto: str | None) -> str:
    return " ".join((texto or "").split())


def _normalizar_cuerpo(texto: str | None) -> str:
    t = (texto or "").replace("\r\n", "\n").replace("\r", "\n")
    t = _ESPACIOS_HORIZONTALES.sub(" ", t)
    t = "\n".join(linea.strip() for linea in t.split("\n"))
    t = _LINEAS_EN_BLANCO.sub("\n\n", t)
    return t.strip()


def _huella(asunto: str, cuerpo: str) -> str:
    return hashlib.sha256(f"{asunto}\n\n{cuerpo}".encode("utf-8")).hexdigest()


def construir_contexto_correo(
    asunto: str | None,
    cuerpo: str | None,
    *,
    max_caracteres: int = MAX_CARACTERES_DEFECTO,
    recibido_utc: str | None = None,
) -> ContextoCorreo:
    """Normaliza, recorta el cuerpo a ``max_caracteres`` y calcula la huella."""
    if max_caracteres <= 0:
        raise ValueError(f"max_caracteres debe ser positivo (llego {max_caracteres}).")
    asunto_norm = _normalizar_asunto(asunto)
    cuerpo_norm = _normalizar_cuerpo(cuerpo)
    originales = len(cuerpo_norm)
    truncado = originales > max_caracteres
    conservado = cuerpo_norm[:max_caracteres].rstrip() if truncado else cuerpo_norm
    return ContextoCorreo(
        asunto=asunto_norm,
        cuerpo=conservado,
        sha256=_huella(asunto_norm, conservado),
        caracteres_originales=originales,
        truncado=truncado,
        recibido_utc=recibido_utc,
    )


def nombre_blob_correo(document_id: str) -> str:
    """Nombre del blob lateral del correo de un documento, dentro de ``input/``."""
    if not str(document_id or "").strip():
        raise ValueError("document_id vacio: no hay blob de correo sin documento.")
    return f"{document_id}{SUFIJO_BLOB_CORREO}"


def guardar_contexto_correo(
    almacen: AlmacenJson, document_id: str, ctx: ContextoCorreo
) -> str:
    """Escribe el contexto en ``input/{document_id}.correo.json`` y devuelve el nombre."""
    from ruesma_comun.blobs.conexion import CONTENEDOR_INPUT

    nombre = nombre_blob_correo(document_id)
    almacen.put_json(CONTENEDOR_INPUT, nombre, ctx.model_dump(mode="json"))
    return nombre


def leer_contexto_correo(almacen: AlmacenJson, nombre_blob: str) -> ContextoCorreo | None:
    """Lee el contexto de ``input/``; ``None`` si el blob falta o no valida."""
    from ruesma_comun.blobs.conexion import CONTENEDOR_INPUT

    try:
        datos = almacen.get_json(CONTENEDOR_INPUT, nombre_blob)
    except FileNotFoundError:
        logger.warning("[correo] no existe el blob de correo %s: se sigue sin correo", nombre_blob)
        return None
    except ValueError as exc:
        # Cubre json.JSONDecodeError y UnicodeDecodeError (ambas son
        # ValueError). Su mensaje puede citar el contenido: solo el tipo.
        logger.warning(
            "[correo] blob de correo %s ilegible (%s): se sigue sin correo",
            nombre_blob, type(exc).__name__,
        )
        return None
    try:
        return ContextoCorreo.model_validate(datos)
    except ValidationError as exc:
        # str(exc) de pydantic incluye los valores de entrada: nunca al log.
        logger.warning(
            "[correo] blob de correo %s no valida (%d errores): se sigue sin correo",
            nombre_blob, exc.error_count(),
        )
        return None
