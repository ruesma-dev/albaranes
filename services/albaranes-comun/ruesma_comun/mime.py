# ruesma_comun/mime.py
"""MIME real de un fichero a partir de sus bytes (F-113).

Graph declara a veces ``application/octet-stream`` para fotos de WhatsApp
(2026-10-30: cinco JPEG de FEYMACO acabaron en IA2 con ``unsupported MIME
type``). Este módulo decide el MIME con los bytes ya descargados, en este
orden (R1):

  1. la firma de los primeros bytes, si se reconoce (manda incluso sobre un
     declarado específico que la contradiga, R2);
  2. el declarado normalizado, si no es genérico (R3);
  3. la extensión del nombre, con una tabla fija (nunca ``mimetypes``: en
     Windows depende del registro);
  4. ``application/octet-stream``.

Funciones puras: sin red, sin disco, sin dependencias fuera de la stdlib.
Infraestructura compartida sin dominio; la usan sv1, sv2 y los clientes de
IA (``ruesma_comun.llm.llm_client.normalizar_adjuntos``).
"""
from __future__ import annotations

import os

__all__ = [
    "MIME_GENERICO",
    "MIME_PDF",
    "detectar_mime",
    "es_mime_generico",
    "nombre_coherente",
    "normalizar_mime",
]

MIME_PDF = "application/pdf"
MIME_GENERICO = "application/octet-stream"

# Glosario de requirements: lo que Graph (o un cliente de correo) pone cuando
# no sabe qué es. Se compara normalizado.
_GENERICOS = frozenset({
    "",
    MIME_GENERICO,
    "binary/octet-stream",
    "application/binary",
    "application/unknown",
    "application/x-unknown",
    "application/download",
    "application/force-download",
})

# Paso 3 de R1. Tabla fija: BMP fuera a propósito (design §4).
_POR_EXTENSION: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jpe": "image/jpeg",
    ".jfif": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".pdf": MIME_PDF,
}

# Extensión que se pone cuando la del nombre no corresponde (R5).
_CANONICA: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/tiff": ".tif",
    "image/heic": ".heic",
    "image/heif": ".heif",
    MIME_PDF: ".pdf",
}

# Alias aceptados por MIME: la tabla de extensiones invertida; HEIC y HEIF
# se aceptan el uno por el otro.
_ALIAS: dict[str, frozenset[str]] = {
    mime: frozenset(ext for ext, m in _POR_EXTENSION.items() if m == mime)
    for mime in _CANONICA
}
_ALIAS["image/heic"] = _ALIAS["image/heif"] = frozenset({".heic", ".heif"})

_MARCAS_HEIC = frozenset({b"heic", b"heix", b"hevc", b"hevx"})
_MARCAS_HEIF = frozenset({b"mif1", b"msf1"})
_VENTANA_PDF = 1024


def normalizar_mime(mime: str | None) -> str:
    """Minúsculas y sin parámetros (``; name=...``); ``""`` si no hay."""
    return (mime or "").split(";")[0].strip().lower()


_normalizar = normalizar_mime


def es_mime_generico(mime: str | None) -> bool:
    """``True`` si el MIME no dice nada útil (vacío, ``None`` u octet-stream y similares)."""
    return _normalizar(mime) in _GENERICOS


def _por_firma(data: bytes | None) -> str | None:
    """MIME por los primeros bytes, o ``None``. Nunca lanza (R4)."""
    if not data:
        return None
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    if data.startswith((b"II*\x00", b"MM\x00*")):
        return "image/tiff"
    if data[4:8] == b"ftyp":
        marca = data[8:12]
        if marca in _MARCAS_HEIC:
            return "image/heic"
        if marca in _MARCAS_HEIF:
            return "image/heif"
    if b"%PDF-" in data[:_VENTANA_PDF]:
        return MIME_PDF
    return None


def detectar_mime(
    data: bytes | None,
    *,
    declarado: str | None = None,
    nombre: str | None = None,
) -> str:
    """MIME real de ``data`` (R1–R4)."""
    por_firma = _por_firma(data)
    if por_firma is not None:
        return por_firma
    if not es_mime_generico(declarado):
        return _normalizar(declarado)
    extension = os.path.splitext(nombre or "")[1].lower()
    return _POR_EXTENSION.get(extension, MIME_GENERICO)


def nombre_coherente(
    nombre: str | None,
    mime: str,
    *,
    defecto: str = "documento",
) -> str:
    """Nombre con una extensión que corresponde a ``mime`` (R5).

    Respeta el tallo tal cual (no sanea: eso lo hace el intake). Si ``mime``
    no tiene extensión en la tabla, devuelve el nombre sin tocarlo.
    """
    mime_n = _normalizar(mime)
    canonica = _CANONICA.get(mime_n)
    if canonica is None:
        return nombre or ""
    if not nombre:
        return f"{defecto}{canonica}"
    tallo, extension = os.path.splitext(nombre)
    if extension.lower() in _ALIAS[mime_n]:
        return nombre
    return f"{tallo}{canonica}"
