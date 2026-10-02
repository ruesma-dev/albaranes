# tests/test_f054_pipeline.py
"""R5 y R13-R24 (F-054): el pipeline de sv1 con correos adjuntos.

Piezas reales (``PdfPageSplitter`` y, desde T7, ``MimeDocumentoExtractor``)
y dobles en memoria para el buzon y el intake (``dobles_sv1``). Los correos
adjuntos se construyen en memoria (``eml_sinteticos``): sin red, sin BBDD,
sin datos reales.
"""
from __future__ import annotations

import hashlib

from dobles_sv1 import (
    ID_PROCESADOS,
    BuzonDoble,
    IntakeDoble,
    adjunto,
    construir_pipeline,
    ejecutar_ciclo,
    mensaje,
    pdf_de_paginas,
)


def _sha(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


# --- R16 · el meta de un adjunto directo no cambia ------------------------ #
def test_f054_r16_meta_de_adjunto_directo_identico_clave_a_clave():
    pdf = pdf_de_paginas(1)
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1", asunto="Albaran obra")],
        adjuntos={"msg-1": [adjunto("a", "albaran.pdf")]},
        ficheros={"a": pdf},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert [e.meta for e in intake.envios] == [{
        "email_message_id": "msg-1",
        "email_received_at_utc": "2026-09-23T08:00:00Z",
        "from_address": "proveedor@ejemplo.test",
        "subject": "Albaran obra",
        "attachment_filename": "albaran.pdf",
        "attachment_sha256": _sha(pdf),
        "attachment_content_type": "application/pdf",
        "attachment_size_bytes": len(pdf),
        "page_number": 1,
        "total_pages": 1,
        "page_sha256": _sha(pdf),
    }]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f054_r16_meta_de_una_imagen_directa_identico_clave_a_clave():
    foto = b"\x89PNG\r\n\x1a\nfoto inventada"
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("a", "foto.png", content_type="image/png")]},
        ficheros={"a": foto},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    (envio,) = intake.envios
    assert set(envio.meta) == {
        "email_message_id", "email_received_at_utc", "from_address", "subject",
        "attachment_filename", "attachment_sha256", "attachment_content_type",
        "attachment_size_bytes", "page_number", "total_pages", "page_sha256",
    }
    assert (envio.meta["attachment_filename"], envio.meta["attachment_content_type"]) == ("foto.png", "image/png")
    assert (envio.meta["page_number"], envio.meta["total_pages"]) == (1, 1)
    assert envio.meta["attachment_sha256"] == envio.meta["page_sha256"] == _sha(foto)


def test_f054_r16_paginas_de_un_pdf_directo_multipagina():
    pdf = pdf_de_paginas(3)
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("a", "lote.pdf")]},
        ficheros={"a": pdf},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert [(e.meta["page_number"], e.meta["total_pages"]) for e in intake.envios] == [(1, 3), (2, 3), (3, 3)]
    assert {e.meta["attachment_sha256"] for e in intake.envios} == {_sha(pdf)}
    assert [e.meta["attachment_filename"] for e in intake.envios] == [
        "lote__page_001_of_003.pdf", "lote__page_002_of_003.pdf", "lote__page_003_of_003.pdf"]
    assert all("correo_adjunto_id" not in e.meta for e in intake.envios)
