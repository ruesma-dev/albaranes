# ruesma_comun/markdown/__init__.py
"""Conversión de documentos a Markdown (markitdown)."""
from ruesma_comun.markdown.markitdown_converter import (
    FuenteDocumento,
    a_markdown,
    combinar_a_markdown,
    markitdown_disponible,
)

__all__ = [
    "FuenteDocumento",
    "a_markdown",
    "combinar_a_markdown",
    "markitdown_disponible",
]
