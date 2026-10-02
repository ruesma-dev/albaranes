# tests/test_f054_clasificacion.py
"""R1-R4 (F-054): que adjunto es un correo adjunto y que adjunto es directo.

Se comprueba a traves del pipeline entero (dobles en memoria): un adjunto
se «procesa» si sv1 lo descarga. Los adjuntos directos siguen la regla de
antes de F-054 sin cambios (R3; la tabla se escribio en T5 contra el
pipeline sin modificar). Textos inventados, direcciones ``@ejemplo.test``.
"""
from __future__ import annotations

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
