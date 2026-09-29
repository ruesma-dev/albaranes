# tests/test_f048_r6_todos_los_albaranes.py
"""R6 (F-048, T9): el contexto de un mensaje llega a TODOS sus documentos.

Cada pagina nueva de cada adjunto recibe el MISMO contexto (mismo sha256),
sea un albaran o varios en el mismo correo (D4). Y el destino del correo
(Procesados / Errores) es el de hoy: el contexto no lo cambia, ni cuando
se obtiene ni cuando falla. Dobles en memoria y textos inventados.
"""
from __future__ import annotations

import pytest
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


def test_f048_r6_varios_albaranes_del_mismo_correo_llevan_el_mismo_contexto():
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("a"), adjunto("b"), adjunto("c")]},
        ficheros={"a": pdf_de_paginas(2), "b": pdf_de_paginas(1), "c": pdf_de_paginas(3)},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert len(intake.envios) == 6
    contextos = [e.contexto_correo for e in intake.envios]
    assert None not in contextos
    assert len({c.sha256 for c in contextos}) == 1
    assert all(c == contextos[0] for c in contextos)
    assert buzon.veces("get_contenido") == 1


def test_f048_r6_un_albaran_de_varias_paginas_lleva_el_mismo_contexto_en_todas():
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("a")]},
        ficheros={"a": pdf_de_paginas(4)},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert [e.meta["page_number"] for e in intake.envios] == [1, 2, 3, 4]
    assert len({e.contexto_correo.sha256 for e in intake.envios}) == 1


def test_f048_r6_cada_mensaje_lleva_su_propio_contexto():
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1"), mensaje("msg-2")],
        adjuntos={"msg-1": [adjunto("a")], "msg-2": [adjunto("b")]},
        ficheros={"a": pdf_de_paginas(2), "b": pdf_de_paginas(1)},
        contenido={
            "msg-1": contenido_inventado(cuerpo=f"Obra 0945 {CENTINELA}"),
            "msg-2": contenido_inventado(cuerpo=f"Obra 1200 {CENTINELA}"),
        },
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    por_mensaje: dict[str, set[str]] = {}
    for envio in intake.envios:
        por_mensaje.setdefault(envio.meta["email_message_id"], set()).add(envio.contexto_correo.cuerpo)
    assert por_mensaje == {"msg-1": {f"Obra 0945 {CENTINELA}"}, "msg-2": {f"Obra 1200 {CENTINELA}"}}


def test_f048_r6_si_un_adjunto_falla_los_demas_llevan_el_contexto_y_va_a_errores():
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")],
        adjuntos={"msg-1": [adjunto("a"), adjunto("roto"), adjunto("c")]},
        ficheros={"a": pdf_de_paginas(1), "roto": RuntimeError("descarga rota"), "c": pdf_de_paginas(2)},
    )
    intake = IntakeDoble()

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert len(intake.envios) == 3
    assert len({e.contexto_correo.sha256 for e in intake.envios}) == 1
    assert buzon.movidos == [("msg-1", ID_ERRORES)]


def _escenario(nombre: str, contenido) -> tuple[BuzonDoble, IntakeDoble]:
    """Los tres destinos de hoy: todo bien, un adjunto falla, sin elegibles."""
    if nombre == "todo_bien":
        adjuntos, ficheros, intake = [adjunto("a"), adjunto("b")], {"a": pdf_de_paginas(2), "b": pdf_de_paginas(1)}, IntakeDoble()
    elif nombre == "adjunto_falla":
        adjuntos, ficheros, intake = [adjunto("a"), adjunto("b")], {"a": pdf_de_paginas(1), "b": RuntimeError("x")}, IntakeDoble()
    elif nombre == "intake_falla":
        adjuntos, ficheros, intake = [adjunto("a")], {"a": pdf_de_paginas(1)}, IntakeDoble(fallar=True)
    else:
        adjuntos, ficheros, intake = [adjunto("a", inline=True)], {}, IntakeDoble()
    buzon = BuzonDoble(
        mensajes=[mensaje("msg-1")], adjuntos={"msg-1": adjuntos}, ficheros=ficheros, contenido=contenido
    )
    return buzon, intake


@pytest.mark.parametrize(
    ("escenario", "destino"),
    [
        ("todo_bien", ID_PROCESADOS),
        ("adjunto_falla", ID_ERRORES),
        ("intake_falla", ID_ERRORES),
        ("sin_elegibles", ID_ERRORES),
    ],
)
@pytest.mark.parametrize(
    "contenido",
    [contenido_inventado(), RuntimeError("Graph caido")],
    ids=["con_contexto", "sin_contexto"],
)
def test_f048_r6_el_destino_del_correo_no_cambia_respecto_a_hoy(escenario, destino, contenido):
    buzon, intake = _escenario(escenario, contenido)

    ejecutar_ciclo(construir_pipeline(buzon, intake))

    assert buzon.movidos == [("msg-1", destino)]
