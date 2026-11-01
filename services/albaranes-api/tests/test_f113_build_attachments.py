# tests/test_f113_build_attachments.py
"""F-113 · sv2 se defiende de los blobs de ``input/`` con MIME genérico (R17–R19).

``_build_attachments`` con el preproceso REAL de ``ruesma_comun.imaging``
(``PREPROCESO_IMAGEN`` a ``false`` y a ``true``). El JPEG es uno mínimo
generado con OpenCV: ninguna foto real de albarán entra al repositorio.
"""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from application.pipelines.extract_albaran_pipeline import ExtractAlbaranPipeline
from domain.models.llm_attachment import LlmAttachment
from ruesma_comun.imaging.preprocess import preparar_imagen_para_ia

OCTET = "application/octet-stream"
PDF = b"%PDF-1.4\n% sintetico F-113\n" + b"\x00" * 32


def _jpeg() -> bytes:
    """JPEG real de 32×32 con un degradado, para que el realce lo decodifique."""
    gris = np.tile(np.linspace(40, 220, 32, dtype=np.uint8), (32, 1))
    ok, buf = cv2.imencode(".jpg", cv2.merge([gris, gris, gris]))
    assert ok
    return buf.tobytes()


JPEG = _jpeg()


def _build(filename: str, mime_type: str, data: bytes) -> list[LlmAttachment]:
    return ExtractAlbaranPipeline._build_attachments(filename=filename, mime_type=mime_type, file_bytes=data)


@pytest.fixture
def sin_preproceso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PREPROCESO_IMAGEN", "false")


@pytest.fixture
def con_preproceso(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PREPROCESO_IMAGEN", "true")


# --------------------------------------------------------------------- #
# R17 · JPEG declarado octet-stream ⇒ imagen suelta realzada
# --------------------------------------------------------------------- #
def test_f113_r17_jpeg_octet_stream_sin_preproceso_va_como_image_jpeg(sin_preproceso: None) -> None:
    [adj] = _build("WhatsApp Image 2026-10-30.jpeg", OCTET, JPEG)
    assert adj == LlmAttachment(kind="image", filename="WhatsApp Image 2026-10-30.jpeg", mime_type="image/jpeg", data=JPEG)


def test_f113_r17_jpeg_octet_stream_pasa_por_el_realce(con_preproceso: None) -> None:
    [adj] = _build("WhatsApp Image 2026-10-30.jpeg", OCTET, JPEG)
    esperado = preparar_imagen_para_ia(JPEG, "image/jpeg", activar=True, iluminacion=True, denoise=False, deskew=True)
    assert adj.kind == "image"
    assert adj.mime_type == "image/jpeg"
    assert adj.data == esperado[2]
    assert adj.data != JPEG
    assert adj.filename == "WhatsApp Image 2026-10-30.jpg"


@pytest.mark.parametrize("mime", [OCTET, "application/pdf"])
def test_f113_r17_jpeg_con_nombre_pdf_no_va_como_pdf(sin_preproceso: None, mime: str) -> None:
    [adj] = _build("albaran.pdf", mime, JPEG)
    assert adj == LlmAttachment(kind="image", filename="albaran.jpg", mime_type="image/jpeg", data=JPEG)


# --------------------------------------------------------------------- #
# R18 · PDF con MIME genérico y nombre sin .pdf ⇒ PDF
# --------------------------------------------------------------------- #
@pytest.mark.parametrize(("nombre", "mime"), [("documento.bin", OCTET), ("escaneo", ""), ("x.dat", "binary/octet-stream")])
def test_f113_r18_pdf_generico_sin_extension_pdf_va_como_pdf(sin_preproceso: None, nombre: str, mime: str) -> None:
    [adj] = _build(nombre, mime, PDF)
    assert adj.kind == "pdf"
    assert adj.mime_type == "application/pdf"
    assert adj.data == PDF
    assert adj.filename.endswith(".pdf")


# --------------------------------------------------------------------- #
# R19 · MIME específico coherente con la firma ⇒ la salida de siempre
# --------------------------------------------------------------------- #
def test_f113_r19_jpeg_coherente_sin_preproceso_identico(sin_preproceso: None) -> None:
    assert _build("foto.jpg", "image/jpeg", JPEG) == [
        LlmAttachment(kind="image", filename="foto.jpg", mime_type="image/jpeg", data=JPEG)
    ]


def test_f113_r19_jpeg_coherente_con_preproceso_identico(con_preproceso: None) -> None:
    _k, _m, datos = preparar_imagen_para_ia(JPEG, "image/jpeg", activar=True, iluminacion=True, denoise=False, deskew=True)
    assert _build("foto.jpg", "image/jpeg", JPEG) == [
        LlmAttachment(kind="image", filename="foto.jpg", mime_type="image/jpeg", data=datos)
    ]


def test_f113_r19_pdf_coherente_sin_preproceso_identico(sin_preproceso: None) -> None:
    assert _build("albaran.pdf", "application/pdf", PDF) == [
        LlmAttachment(kind="pdf", filename="albaran.pdf", mime_type="application/pdf", data=PDF)
    ]


def test_f113_r19_png_coherente_sin_preproceso_identico(sin_preproceso: None) -> None:
    ok, buf = cv2.imencode(".png", np.zeros((4, 4, 3), dtype=np.uint8))
    png = buf.tobytes()
    assert _build("foto.png", "image/png", png) == [
        LlmAttachment(kind="image", filename="foto.png", mime_type="image/png", data=png)
    ]

