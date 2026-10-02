# tests/test_f048_r3_r5_pipeline.py
"""R2, R3 y R5 en el pipeline de sv1 (F-048, T8).

El pipeline pide el contenido del correo UNA vez por mensaje con adjuntos
elegibles, construye el contexto con la funcion de ``ruesma_comun`` y lo
entrega al intake. Sin ``uniqueBody`` el contexto es solo el asunto; si
pedirlo falla, los adjuntos siguen sin contexto y el correo NO va a Errores
por ese motivo. Dobles en memoria y textos inventados.
"""
from __future__ import annotations

import logging

import pytest
from config.settings import Settings
from dobles_sv1 import (
    CENTINELA,
    ID_ERRORES,
    ID_PROCESADOS,
    BuzonDoble,
    IntakeDoble,
    adjunto,
    construir_pipeline,
    contenido_inventado,
    ejecutar_ciclo,
    mensaje,
    pdf_de_paginas,
)
from domain.models.email_models import EmailMessage
from pydantic import ValidationError
from ruesma_comun.correo import MAX_CARACTERES_DEFECTO, construir_contexto_correo


def _buzon(**opciones) -> BuzonDoble:
    return BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("att-1"), adjunto("att-2")]},
        ficheros={"att-1": pdf_de_paginas(2), "att-2": pdf_de_paginas(1)},
        **opciones,
    )


def test_f048_r2_el_contenido_se_pide_una_vez_por_mensaje():
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1"), mensaje("msg-2")],
        adjuntos={
            "msg-1": [adjunto("att-1"), adjunto("att-2")],
            "msg-2": [adjunto("att-3")],
        },
        ficheros={
            "att-1": pdf_de_paginas(2),
            "att-2": pdf_de_paginas(1),
            "att-3": pdf_de_paginas(1),
        },
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    pedidos = [ident for nombre, ident in buzon.llamadas if nombre == "get_contenido"]
    assert pedidos == ["msg-1", "msg-2"]
    assert len(intake.envios) == 4


def test_f048_r2_sin_adjuntos_elegibles_no_se_pide_el_contenido():
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("att-1", inline=True)]},
        ficheros={},
    )

    ejecutar_ciclo(construir_pipeline(buzon, IntakeDoble()))

    assert buzon.veces("get_contenido") == 0
    assert buzon.movidos == [("msg-1", ID_ERRORES)]


def test_f048_r1_el_contexto_es_el_de_la_funcion_de_comun():
    buzon = _buzon()
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    esperado = construir_contexto_correo(
        "Albaran obra",
        f"Material para la obra 0945. {CENTINELA}",
        recibido_utc="2026-09-23T08:00:00Z",
    )
    assert [e.contexto_correo for e in intake.envios] == [esperado] * 3


def test_f048_r1_el_recorte_sale_de_la_configuracion():
    buzon = _buzon(contenido=contenido_inventado(cuerpo="0123456789" * 3))
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake, correo_max_caracteres=10))

    ctx = intake.envios[0].contexto_correo
    assert ctx.cuerpo == "0123456789"
    assert ctx.truncado is True
    assert ctx.caracteres_originales == 30


@pytest.mark.parametrize("cuerpo", ["", "  \r\n \t "])
def test_f048_r3_unique_body_vacio_el_contexto_lleva_solo_el_asunto(cuerpo):
    buzon = _buzon(contenido=contenido_inventado(cuerpo=cuerpo, asunto="Obra 0945 - pedido"))
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    ctx = intake.envios[0].contexto_correo
    assert ctx.asunto == "Obra 0945 - pedido"
    assert ctx.cuerpo == ""
    assert ctx.sha256 == construir_contexto_correo("Obra 0945 - pedido", "").sha256
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]


def test_f048_r5_si_pedir_el_contenido_falla_sigue_sin_contexto_y_va_a_procesados(caplog):
    buzon = _buzon(contenido=RuntimeError(f"Graph 500 con texto {CENTINELA}"))
    intake = IntakeDoble()

    with caplog.at_level(logging.DEBUG):
        ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert len(intake.envios) == 3
    assert [e.contexto_correo for e in intake.envios] == [None] * 3
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1
    assert "msg-1" in avisos[0].getMessage()
    assert "RuntimeError" in avisos[0].getMessage()
    assert CENTINELA not in caplog.text


def test_f048_r5_el_fallo_del_contenido_no_tapa_un_fallo_real_de_adjunto():
    """Sin contexto Y con un adjunto roto, el correo va a Errores por el adjunto."""
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("att-1"), adjunto("att-2")]},
        ficheros={"att-1": pdf_de_paginas(1), "att-2": RuntimeError("descarga rota")},
        contenido=RuntimeError("Graph caido"),
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert [e.contexto_correo for e in intake.envios] == [None]
    assert buzon.movidos == [("msg-1", ID_ERRORES)]


def test_f048_r1_correo_max_caracteres_por_defecto_y_validado(monkeypatch):
    monkeypatch.delenv("CORREO_MAX_CARACTERES", raising=False)
    obligatorias = {"MAILBOX_ADDRESS": "b@ejemplo.test", "GRAPH_KEY": "k", "PG_PASSWORD": "p"}

    assert Settings(_env_file=None, **obligatorias).correo_max_caracteres == MAX_CARACTERES_DEFECTO
    assert Settings(
        _env_file=None, CORREO_MAX_CARACTERES="250", **obligatorias
    ).correo_max_caracteres == 250
    with pytest.raises(ValidationError):
        Settings(_env_file=None, CORREO_MAX_CARACTERES="0", **obligatorias)


def test_f048_r1_sin_fecha_de_recepcion_el_contexto_no_la_inventa():
    sin_fecha = EmailMessage(id="msg-1", subject="Albaran", sender=None, received_datetime=None)
    buzon = BuzonDoble(
        mensajes=[sin_fecha],
        adjuntos={"msg-1": [adjunto("att-1")]},
        ficheros={"att-1": pdf_de_paginas(1)},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert intake.envios[0].contexto_correo.recibido_utc is None
