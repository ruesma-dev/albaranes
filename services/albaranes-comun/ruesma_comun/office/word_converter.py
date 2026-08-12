# ruesma_comun/office/word_converter.py
"""Conversores de Word (.doc/.docx) → PDF + Markdown tras un protocolo común.

Dos implementaciones intercambiables (patrón puerto/adaptador):

  - ``LibreOfficeWordConverter``: usa LibreOffice headless local/contenedor.
    Sin dependencias de red. Necesita ``soffice`` disponible.
  - ``GraphWordConverter``: usa Microsoft Graph (``content?format=pdf``), el
    motor de Office 365 — máxima fidelidad y misma salida en local y Azure,
    sin LibreOffice. Necesita un cliente Graph con ``convert_to_pdf`` y, por
    tanto, credenciales/permisos de SharePoint (``Sites.ReadWrite.All``).

El llamante (p. ej. el cliente Sigrid de contratos) recibe el conversor
inyectado y NO sabe cuál es. La factoría ``build_word_converter`` lo elige
por configuración (``WORD_TO_PDF_BACKEND`` = ``graph`` | ``libreoffice``).

Para el Markdown:
  - ``.docx``: markitdown directo (tabla Markdown limpia), sin red ni LibreOffice.
  - ``.doc`` (legacy): no lo lee markitdown → se pasa a PDF (LibreOffice o
    Graph) y de ahí a Markdown (texto + tablas best-effort).
"""
from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

from ruesma_comun.markdown.markitdown_converter import a_markdown
from ruesma_comun.office import libreoffice_converter as _lo

logger = logging.getLogger(__name__)


@runtime_checkable
class WordConverter(Protocol):
    """Puerto de conversión de Word a PDF y a Markdown."""

    def disponible(self) -> bool: ...

    def word_a_pdf(self, data: bytes, src_ext: str) -> bytes | None: ...

    def word_a_markdown(
        self, data: bytes, src_ext: str, *, texto_fallback: str | None = None
    ) -> str | None: ...


class LibreOfficeWordConverter:
    """Adaptador LibreOffice (local/contenedor)."""

    nombre = "libreoffice"

    def disponible(self) -> bool:
        return _lo.disponible()

    def word_a_pdf(self, data: bytes, src_ext: str) -> bytes | None:
        return _lo.word_a_pdf(data, src_ext)

    def word_a_markdown(
        self, data: bytes, src_ext: str, *, texto_fallback: str | None = None
    ) -> str | None:
        return _lo.word_a_markdown(data, src_ext, texto_fallback=texto_fallback)


class GraphWordConverter:
    """Adaptador Microsoft Graph (``content?format=pdf``).

    ``graph_client`` es cualquier objeto con
    ``convert_to_pdf(file_bytes, src_ext, *, temp_folder=...) -> bytes | None``
    (lo cumple ``GraphSharePointClient`` de este paquete y, por herencia, el
    ``SharePointDocumentStorage`` de sv3).
    """

    nombre = "graph"

    def __init__(self, graph_client, *, temp_folder: str = "_conversion_tmp"):
        self._graph = graph_client
        self._temp_folder = temp_folder

    def disponible(self) -> bool:
        return self._graph is not None and hasattr(self._graph, "convert_to_pdf")

    def word_a_pdf(self, data: bytes, src_ext: str) -> bytes | None:
        if not self.disponible():
            return None
        return self._graph.convert_to_pdf(
            data, src_ext, temp_folder=self._temp_folder
        )

    def word_a_markdown(
        self, data: bytes, src_ext: str, *, texto_fallback: str | None = None
    ) -> str | None:
        # .docx: markitdown directo, sin red (tabla limpia).
        if src_ext.lower().endswith(".docx"):
            md = a_markdown(data, "documento.docx")
            if md:
                return md
        # .doc (o si lo anterior falló): Graph → PDF → markitdown.
        pdf = self.word_a_pdf(data, src_ext)
        if pdf:
            md = a_markdown(pdf, "documento.pdf", texto_fallback=texto_fallback)
            if md:
                return md
        return texto_fallback or None


def build_word_converter(
    backend: str | None,
    *,
    graph_client=None,
) -> WordConverter:
    """Construye el conversor según ``backend`` (``graph`` | ``libreoffice``).

    Si se pide ``graph`` pero no hay cliente Graph utilizable, degrada a
    LibreOffice (y lo registra), de modo que el sistema nunca se queda sin
    conversor por configuración.
    """
    elegido = (backend or "libreoffice").strip().lower()
    if elegido == "graph":
        conv = GraphWordConverter(graph_client) if graph_client is not None else None
        if conv is not None and conv.disponible():
            logger.info("[word_converter] backend = graph (Microsoft 365).")
            return conv
        logger.warning(
            "[word_converter] backend 'graph' pedido pero sin cliente Graph "
            "utilizable; degrado a LibreOffice."
        )
    logger.info("[word_converter] backend = libreoffice.")
    return LibreOfficeWordConverter()
