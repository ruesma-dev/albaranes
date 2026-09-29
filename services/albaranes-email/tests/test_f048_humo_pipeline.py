# tests/test_f048_humo_pipeline.py
"""Humo de la primera suite de sv1 (F-048, T6).

Importa el pipeline de polling y lo hace girar una vez con dobles del
buzon y del intake: si esto se rompe, ningun otro test de sv1 vale.
"""
from __future__ import annotations

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


def test_f048_humo_un_pdf_de_dos_paginas_llega_al_intake_y_va_a_procesados():
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("att-1")]},
        ficheros={"att-1": pdf_de_paginas(2)},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert [e.meta["page_number"] for e in intake.envios] == [1, 2]
    assert {e.meta["email_message_id"] for e in intake.envios} == {"msg-1"}
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f048_humo_sin_adjuntos_elegibles_va_a_errores_sin_llamar_al_intake():
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("att-1", inline=True)]},
        ficheros={},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert intake.envios == []
    assert buzon.movidos == [("msg-1", ID_ERRORES)]


def test_f048_humo_sin_mensajes_no_hace_nada():
    buzon = BuzonDoble(mensajes=[], adjuntos={}, ficheros={})
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert intake.envios == []
    assert buzon.movidos == []
