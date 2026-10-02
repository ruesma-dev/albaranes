# tests/test_f054_clasificacion.py
"""R1-R4 (F-054): que adjunto es un correo adjunto y que adjunto es directo.

Se comprueba a traves del pipeline entero (dobles en memoria): un adjunto
se «procesa» si sv1 lo descarga. Los adjuntos directos siguen la regla de
antes de F-054 sin cambios (R3; la tabla se escribio en T5 contra el
pipeline sin modificar). Textos inventados, direcciones ``@ejemplo.test``.
"""
from __future__ import annotations

import logging

import pytest
from dobles_sv1 import (
    ID_ERRORES,
    ID_PROCESADOS,
    BuzonDoble,
    IntakeDoble,
    adjunto,
    construir_pipeline,
    ejecutar_ciclo,
    mensaje,
    pdf_de_paginas,
)
from domain.models.email_models import EmailMessage
from eml_sinteticos import a_bytes, correo, fichero_pdf

LIMITE = 25 * 1024 * 1024
ITEM = "#microsoft.graph.itemAttachment"
FILE = "#microsoft.graph.fileAttachment"
REFERENCE = "#microsoft.graph.referenceAttachment"


def _ciclo_con(att, fichero: bytes):
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [att]},
        ficheros={att.id: fichero},
    )
    intake = IntakeDoble()
    ejecutar_ciclo(construir_pipeline(buzon, intake))
    return buzon, intake


# --- R3 · adjuntos directos: la regla de hoy, sin filtro de tipo ---------- #
CASOS_DIRECTOS = [
    # (id, content_type, odata_type, inline, size, se_procesa)
    ("pdf-file", "application/pdf", FILE, False, 1000, True),
    ("pdf-sin-odata", "application/pdf", None, False, 1000, True),
    ("jpeg", "image/jpeg", FILE, False, 1000, True),
    ("png", "image/png", None, False, 1000, True),
    ("msg-outlook", "application/vnd.ms-outlook", FILE, False, 1000, True),
    ("texto", "text/plain", FILE, False, 1000, True),
    ("zip", "application/zip", FILE, False, 1000, True),
    ("sin-tipo", "", FILE, False, 1000, True),
    ("justo-en-el-limite", "application/pdf", FILE, False, LIMITE, True),
    ("inline", "image/png", FILE, True, 1000, False),
    ("item-no-correo", "text/calendar", ITEM, False, 1000, False),
    ("reference", "application/pdf", REFERENCE, False, 1000, False),
    ("excede-limite", "application/pdf", FILE, False, LIMITE + 1, False),
]


@pytest.mark.parametrize(
    ("att_id", "content_type", "odata_type", "inline", "size", "se_procesa"),
    CASOS_DIRECTOS,
    ids=[c[0] for c in CASOS_DIRECTOS],
)
def test_f054_r3_adjuntos_directos_con_la_regla_de_hoy(att_id, content_type, odata_type, inline, size, se_procesa):
    att = adjunto(att_id, "fichero.bin", inline=inline, content_type=content_type, odata_type=odata_type, size=size)
    fichero = pdf_de_paginas(1) if content_type == "application/pdf" else b"bytes inventados"

    buzon, intake = _ciclo_con(att, fichero)

    assert buzon.veces("download_attachment_value") == (1 if se_procesa else 0)
    assert len(intake.envios) == (1 if se_procesa else 0)
    assert buzon.movidos == [("msg-1", ID_PROCESADOS if se_procesa else ID_ERRORES)]
    if se_procesa:
        assert intake.envios[0].meta["attachment_content_type"] == (content_type or "application/octet-stream")


# --- R1 · que es un correo adjunto --------------------------------------- #
def _correo_adjunto(att_id="c1", *, content_type="message/rfc822", odata_type=ITEM, inline=False, size=5000):
    return adjunto(
        att_id,
        "RV: albaran inventado",
        inline=inline,
        content_type=content_type,
        odata_type=odata_type,
        size=size,
    )


def _eml_con_pdf() -> bytes:
    return a_bytes(correo(adjuntos=[fichero_pdf("interior.pdf")]))


@pytest.mark.parametrize("odata_type", [ITEM, FILE, None], ids=["item", "file", "sin-odata"])
@pytest.mark.parametrize("content_type", ["message/rfc822", "MESSAGE/RFC822", "Message/Rfc822"])
def test_f054_r1_message_rfc822_no_inline_se_abre_como_correo_adjunto(odata_type, content_type):
    buzon, intake = _ciclo_con(_correo_adjunto(content_type=content_type, odata_type=odata_type), _eml_con_pdf())

    assert buzon.veces("download_attachment_value") == 1
    assert [(e.meta["attachment_filename"], e.content_type) for e in intake.envios] == [
        ("interior.pdf", "application/pdf")]
    assert intake.envios[0].meta["correo_adjunto_id"] == "c1"
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f054_r1_un_eml_como_file_attachment_tambien_se_abre():
    att = adjunto("c1", "reenviado.eml", content_type="message/rfc822", odata_type=FILE)

    buzon, intake = _ciclo_con(att, _eml_con_pdf())

    assert [e.meta["attachment_filename"] for e in intake.envios] == ["interior.pdf"]
    assert all(e.meta["attachment_content_type"] != "message/rfc822" for e in intake.envios)


# --- R2 · correos adjuntos descartados ----------------------------------- #
@pytest.mark.parametrize(
    ("att", "nivel"),
    [
        (_correo_adjunto(inline=True), logging.INFO),
        (_correo_adjunto(odata_type=REFERENCE), logging.INFO),
        (_correo_adjunto(size=LIMITE + 1), logging.WARNING),
    ],
    ids=["inline", "reference", "excede-limite"],
)
def test_f054_r2_correo_adjunto_descartado_ni_como_correo_ni_como_directo(caplog, att, nivel):
    with caplog.at_level(logging.DEBUG):
        buzon, intake = _ciclo_con(att, _eml_con_pdf())

    assert buzon.veces("download_attachment_value") == 0
    assert intake.envios == []
    assert buzon.movidos == [("msg-1", ID_ERRORES)]
    descartes = [r for r in caplog.records if "c1" in r.getMessage() and "descartado" in r.getMessage()]
    assert [r.levelno for r in descartes] == [nivel]


def test_f054_r2_el_limite_exacto_no_descarta():
    buzon, intake = _ciclo_con(_correo_adjunto(size=LIMITE), _eml_con_pdf())

    assert buzon.veces("download_attachment_value") == 1
    assert len(intake.envios) == 1


# --- R4 · ni el remitente ni el asunto deciden ---------------------------- #
@pytest.mark.parametrize(
    ("remitente", "asunto"),
    [
        ("proveedor@ejemplo.test", "Albaran obra"),
        ("escaner@ejemplo.test", ""),
        (None, "RV: RV: cualquier cosa"),
    ],
)
def test_f054_r4_la_clasificacion_no_depende_de_remitente_ni_asunto(remitente, asunto):
    msg = EmailMessage(id="msg-1", subject=asunto, sender=remitente, received_datetime="2026-09-23T08:00:00Z")
    buzon = BuzonDoble(
        mensajes=[msg],
        adjuntos={"msg-1": [_correo_adjunto(), adjunto("a", "directo.pdf"), _correo_adjunto("c2", inline=True)]},
        ficheros={"c1": _eml_con_pdf(), "a": pdf_de_paginas(1)},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert [e.meta["attachment_filename"] for e in intake.envios] == ["interior.pdf", "directo.pdf"]
    assert buzon.veces("download_attachment_value") == 2
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]
