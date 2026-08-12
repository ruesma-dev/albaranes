# ruesma_comun/office/__init__.py
"""Conversión de documentos de oficina (LibreOffice headless o Microsoft Graph)."""
from ruesma_comun.office.libreoffice_converter import (
    combinar_pdfs,
    disponible,
    es_word,
    pdf_a_markdown,
    word_a_markdown,
    word_a_pdf,
)
from ruesma_comun.office.word_converter import (
    GraphWordConverter,
    LibreOfficeWordConverter,
    WordConverter,
    build_word_converter,
)

__all__ = [
    "combinar_pdfs",
    "disponible",
    "es_word",
    "pdf_a_markdown",
    "word_a_markdown",
    "word_a_pdf",
    # Adaptadores conmutables Word→PDF/MD
    "WordConverter",
    "LibreOfficeWordConverter",
    "GraphWordConverter",
    "build_word_converter",
]
