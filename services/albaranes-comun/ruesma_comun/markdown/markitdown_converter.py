# ruesma_comun/markdown/markitdown_converter.py
"""Conversión de documentos (PDF / Word) a Markdown con *markitdown*.

Motivación: antes de enviar un contrato a la IA conviene mandarlo como
**Markdown** en lugar del PDF. markitdown convierte ``.docx`` conservando
las TABLAS de tarifas como tablas Markdown reales (mucha mejor señal para
el LLM que un PDF aplanado), y extrae el texto de los PDF digitales. El
Markdown se genera a partir de las fuentes ORIGINALES de Sigrid (Word o
PDF), no del PDF ya renderizado, para no perder esa estructura.

Diseño:
  - **Degradación elegante**: si markitdown no está instalado o un
    documento concreto falla, se usa ``texto_fallback`` (el texto plano
    que sv3 ya extrae) o se omite la sección; NUNCA se lanza excepción.
    Generar el MD jamás debe romper el flujo del contrato.
  - **Sin red ni estado**: markitdown trabaja sobre bytes en memoria.
  - markitdown es dependencia OPCIONAL del paquete (extra ``markdown``):
    los servicios que no convierten (sv1, sv4, sv6) no la instalan.

Limitación conocida: para PDF **escaneados** (imagen, sin capa de texto)
markitdown extrae poco o nada — no hace OCR. Los contratos de Sigrid que
nacen de Word no se ven afectados; un PDF escaneado caería al PDF como
adjunto (sv5 mantiene ese fallback).
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Extensiones que markitdown convierte con BUENA fidelidad. Deliberadamente
# NO incluye ``.doc`` (Word binario antiguo): markitdown no lo entiende y
# devuelve texto basura en vez de fallar, así que ese caso se enruta al
# ``texto_fallback`` que el servicio ya extrae — igual que hace sv3 hoy.
_EXT_MARKITDOWN = (".pdf", ".docx", ".html", ".htm")


@dataclass(frozen=True)
class FuenteDocumento:
    """Un documento fuente del contrato a convertir.

    - ``titulo``: encabezado de la sección en el MD combinado
      (p. ej. "DOCUMENTO: contrato_0464.docx (12/03/2026)").
    - ``filename``: nombre original (markitdown usa la extensión para
      elegir conversor).
    - ``contenido``: bytes del documento.
    - ``texto_fallback``: texto plano ya extraído por el servicio; se usa
      si markitdown no puede convertir este documento.
    """

    titulo: str
    filename: str
    contenido: bytes
    texto_fallback: str | None = None


def markitdown_disponible() -> bool:
    """True si la librería markitdown está instalada en el entorno."""
    try:
        import markitdown  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


def a_markdown(
    contenido: bytes,
    filename: str,
    *,
    texto_fallback: str | None = None,
) -> str | None:
    """Convierte UN documento (bytes) a Markdown.

    Devuelve el Markdown, o ``texto_fallback`` si markitdown no está
    disponible o falla, o ``None`` si no hay nada utilizable.
    """
    if not contenido:
        return texto_fallback or None

    extension = _extension(filename)
    if extension not in _EXT_MARKITDOWN:
        # Extensión no soportada con garantías (p. ej. .doc binario):
        # markitdown podría devolver basura. Usamos el texto ya extraído.
        logger.info(
            "[markitdown] extensión %s sin garantía; uso fallback para %s",
            extension,
            filename,
        )
        return texto_fallback or None
    try:
        from markitdown import MarkItDown, StreamInfo
    except Exception:  # noqa: BLE001 — markitdown no instalado
        logger.info(
            "[markitdown] no instalado; uso texto de fallback para %s", filename
        )
        return texto_fallback or None

    try:
        md = MarkItDown()
        resultado = md.convert_stream(
            io.BytesIO(contenido),
            stream_info=StreamInfo(extension=extension),
        )
        texto = (resultado.markdown or "").strip()
        if texto:
            return texto
        logger.info("[markitdown] conversión vacía para %s; uso fallback", filename)
        return texto_fallback or None
    except Exception:  # noqa: BLE001 — cualquier fallo degrada al fallback
        logger.warning(
            "[markitdown] fallo convirtiendo %s; uso texto de fallback",
            filename,
            exc_info=True,
        )
        return texto_fallback or None


def combinar_a_markdown(fuentes: list[FuenteDocumento]) -> str | None:
    """Convierte y combina varias fuentes en un único Markdown.

    Cada sección se encabeza con su ``titulo`` (## ...) y se separa con
    una línea horizontal. El orden de ``fuentes`` se respeta (lo fija el
    llamante: del documento más antiguo al más moderno). Devuelve ``None``
    si no se obtuvo ninguna sección con contenido.
    """
    secciones: list[str] = []
    for fuente in fuentes:
        cuerpo = a_markdown(
            fuente.contenido,
            fuente.filename,
            texto_fallback=fuente.texto_fallback,
        )
        if not cuerpo:
            continue
        titulo = (fuente.titulo or "").strip()
        if titulo:
            secciones.append(f"## {titulo}\n\n{cuerpo}")
        else:
            secciones.append(cuerpo)

    if not secciones:
        return None
    return "\n\n---\n\n".join(secciones).strip() or None


def _extension(filename: str) -> str:
    nombre = (filename or "").lower().strip()
    for ext in (*_EXT_MARKITDOWN, ".doc", ".txt", ".rtf"):
        if nombre.endswith(ext):
            return ext
    # Por defecto tratamos como PDF (el caso más común en este flujo).
    return ".pdf"
