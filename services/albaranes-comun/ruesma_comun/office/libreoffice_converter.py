# ruesma_comun/office/libreoffice_converter.py
"""Conversión de documentos de oficina con **LibreOffice headless**.

Motivo (jun 2026): los contratos de Sigrid son en su mayoría Word binario
LEGACY (`.doc`, Word 97-2003). Ni `mammoth` ni `markitdown` leen `.doc`
(markitdown lanza ``UnsupportedFormatException``), así que el camino
anterior caía a extracción de texto plano y **aplanaba las tablas** de
tarifas — tanto en el PDF para el revisor como en el MD para la IA.

LibreOffice sí lee `.doc` y `.docx` reales conservando la estructura.
Este módulo expone la mecánica:

  - `word_a_pdf`      : Word (.doc/.docx) → PDF (tablas intactas) para el
                        PDF combinado que consulta el revisor.
  - `word_a_markdown` : Word → HTML (LibreOffice) → Markdown (markitdown).
                        La ruta vía HTML conserva las tablas como tablas
                        Markdown (la ruta vía .docx NO siempre lo hace).
  - `pdf_a_markdown`  : PDF → Markdown (markitdown; texto, tablas best-effort).
  - `combinar_pdfs`   : fusiona PDFs página a página (pypdf), sin aplanar.
  - `disponible`      : True si `soffice` está en el PATH.

LibreOffice es dependencia **del sistema** (no pip): se instala en la
imagen de sv3 (`apt-get install -y libreoffice-writer`). En local debe
estar `soffice` en el PATH. Si no está, `word_a_*` degradan a ``None`` y
el llamante usa su texto de fallback (nunca rompe el flujo).
"""
from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from ruesma_comun.markdown.markitdown_converter import a_markdown

logger = logging.getLogger(__name__)

_TIMEOUT_S = 120
_EXT_WORD = (".doc", ".docx")


# Override explícito por variable de entorno (ruta completa a soffice).
_ENV_SOFFICE = "RUESMA_SOFFICE"


def _candidatos_soffice() -> list[str]:
    """Rutas candidatas a LibreOffice, multiplataforma. En Windows
    ``soffice.exe`` NO suele estar en el PATH (se instala en
    ``C:\\Program Files\\LibreOffice\\program``), por eso ademas del PATH
    se prueban las ubicaciones estandar y la variable ``RUESMA_SOFFICE``."""
    cands: list[str] = []
    env = os.environ.get(_ENV_SOFFICE)
    if env:
        cands.append(env)
    for nombre in ("soffice", "libreoffice"):
        encontrado = shutil.which(nombre)
        if encontrado:
            cands.append(encontrado)
    if sys.platform.startswith("win"):
        bases = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
            os.environ.get("LOCALAPPDATA", ""),
        ]
        for base in bases:
            if base:
                cands.append(
                    str(Path(base) / "LibreOffice" / "program" / "soffice.exe")
                )
    elif sys.platform == "darwin":
        cands.append("/Applications/LibreOffice.app/Contents/MacOS/soffice")
    else:
        cands += [
            "/usr/bin/soffice",
            "/usr/bin/libreoffice",
            "/usr/local/bin/soffice",
            "/snap/bin/libreoffice",
            "/opt/libreoffice/program/soffice",
        ]
    return cands


def _binario() -> str | None:
    for c in _candidatos_soffice():
        try:
            if c and Path(c).exists():
                return c
        except OSError:
            continue
    return None


def disponible() -> bool:
    """True si se localiza LibreOffice (PATH, RUESMA_SOFFICE o ruta estandar)."""
    return _binario() is not None


def _convertir(data: bytes, src_ext: str, destino: str) -> bytes | None:
    """Convierte ``data`` (con extensión ``src_ext``) al formato ``destino``
    (p. ej. "pdf" o "html") usando LibreOffice headless. Devuelve los bytes
    del resultado o ``None`` si falla (logueado, nunca lanza).

    Usa un directorio de trabajo + perfil de usuario EFÍMERO por llamada
    (``-env:UserInstallation``): así varias conversiones concurrentes no
    se pisan el perfil — relevante en el worker de Azure.
    """
    binario = _binario()
    if binario is None:
        logger.info("[libreoffice] soffice no está en el PATH; degrado a None.")
        return None

    ext = src_ext if src_ext.startswith(".") else f".{src_ext}"
    with tempfile.TemporaryDirectory(prefix="lo-") as tmp:
        tmp_path = Path(tmp)
        entrada = tmp_path / f"in{ext}"
        entrada.write_bytes(data)
        perfil = tmp_path / "profile"

        cmd = [
            binario,
            "--headless",
            "--norestore",
            "--nolockcheck",
            f"-env:UserInstallation={perfil.as_uri()}",
            "--convert-to",
            destino,
            "--outdir",
            str(tmp_path),
            str(entrada),
        ]
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                timeout=_TIMEOUT_S,
                check=False,
            )
        except subprocess.TimeoutExpired:
            logger.warning("[libreoffice] timeout convirtiendo %s → %s", ext, destino)
            return None
        except Exception:  # noqa: BLE001
            logger.warning(
                "[libreoffice] error ejecutando soffice (%s → %s)",
                ext,
                destino,
                exc_info=True,
            )
            return None

        # El destino puede llevar opciones ("html:HTML"): nos quedamos con
        # la extensión real del fichero generado.
        salida_ext = destino.split(":", 1)[0].strip()
        salida = tmp_path / f"in.{salida_ext}"
        if not salida.exists():
            # Algún filtro escribe con otro nombre; busca el primero que no
            # sea la entrada ni el perfil.
            candidatos = [
                p for p in tmp_path.glob(f"*.{salida_ext}") if p != entrada
            ]
            if not candidatos:
                logger.warning(
                    "[libreoffice] sin salida %s. stderr=%s",
                    salida_ext,
                    (proc.stderr or b"")[:300],
                )
                return None
            salida = candidatos[0]
        return salida.read_bytes()


def word_a_pdf(data: bytes, src_ext: str) -> bytes | None:
    """Word (.doc/.docx) → PDF conservando tablas. ``None`` si falla."""
    if not data:
        return None
    return _convertir(data, src_ext, "pdf")


def word_a_markdown(
    data: bytes,
    src_ext: str,
    *,
    texto_fallback: str | None = None,
) -> str | None:
    """Word (.doc/.docx) → Markdown con tablas, vía HTML de LibreOffice.

    Pasos: Word → HTML (LibreOffice exporta tablas como ``<table>``) →
    Markdown (markitdown convierte la tabla HTML en tabla Markdown). Si
    LibreOffice no está o falla, devuelve ``texto_fallback``.
    """
    if not data:
        return texto_fallback or None

    # .docx: markitdown lo lee directo y da una tabla Markdown impecable
    # (probado con tablas anchas de tarifas). Es lo más limpio y rápido.
    if src_ext.lower().endswith(".docx"):
        md = a_markdown(data, "documento.docx")
        if md:
            return md

    # .doc (y .docx si lo anterior falló): LibreOffice → HTML → markitdown.
    # LibreOffice exporta la tabla como <table> y markitdown la convierte
    # en tabla Markdown.
    html = _convertir(data, src_ext, "html")
    if not html:
        logger.info(
            "[libreoffice] HTML no disponible para %s; uso texto de fallback.",
            src_ext,
        )
        return texto_fallback or None
    md = a_markdown(html, "documento.html", texto_fallback=texto_fallback)
    return md or texto_fallback or None


def pdf_a_markdown(data: bytes, *, texto_fallback: str | None = None) -> str | None:
    """PDF → Markdown (markitdown). Tablas best-effort (PDF es texto)."""
    return a_markdown(data, "documento.pdf", texto_fallback=texto_fallback)


def es_word(filename: str) -> bool:
    return (filename or "").lower().strip().endswith(_EXT_WORD)


def combinar_pdfs(blobs: list[bytes]) -> bytes | None:
    """Fusiona varios PDF página a página (sin aplanar). ``None`` si no hay
    nada utilizable."""
    blobs = [b for b in blobs if b]
    if not blobs:
        return None
    if len(blobs) == 1:
        return blobs[0]
    try:
        from pypdf import PdfReader, PdfWriter
    except Exception:  # noqa: BLE001
        logger.warning("[libreoffice] pypdf no instalado; no se pueden fusionar PDFs.")
        return blobs[0]

    import io

    writer = PdfWriter()
    for blob in blobs:
        try:
            for page in PdfReader(io.BytesIO(blob)).pages:
                writer.add_page(page)
        except Exception:  # noqa: BLE001
            logger.warning("[libreoffice] PDF ilegible omitido en la fusión.", exc_info=True)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
