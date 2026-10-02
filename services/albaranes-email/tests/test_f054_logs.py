# tests/test_f054_logs.py
"""R25 (F-054): ningun log de sv1 lleva datos del correo interior.

Ni bytes de un documento o del MIME, ni ``Subject``, ``From``, ``Date`` o
cuerpo de un correo interior, ni el ``name`` de Graph de un correo adjunto
(Graph pone ahi el asunto del interior). El cuerpo del exterior sigue fuera
(R36 de F-048). El centinela ``CENTINELA-F054`` va en el ``name`` del
adjunto y en las cabeceras y el cuerpo de los interiores; se busca en TODO
lo logueado a nivel DEBUG, tambien en las ramas de error. Los nombres de
los documentos interiores SI se loguean (DA6): por eso no llevan centinela.
"""
from __future__ import annotations

import base64
import logging

import pytest
from dobles_sv1 import (
    BUZON,
    CARPETA_ORIGEN,
    CENTINELA,
    ID_ERRORES,
    ID_PROCESADOS,
    BuzonDoble,
    IntakeDoble,
    adjunto,
    construir_pipeline,
    mensaje,
    pdf_de_paginas,
)
from eml_sinteticos import (
    CENTINELA_F054,
    FECHA_INTERIOR,
    Anidado,
    a_bytes,
    correo,
    envolver,
    fichero_pdf,
    fichero_png,
    fichero_texto,
    png_bytes,
)

ITEM = "#microsoft.graph.itemAttachment"
REFERENCE = "#microsoft.graph.referenceAttachment"
NOMBRE_GRAPH = f"RV: Albaran del proveedor {CENTINELA_F054}"
RELLENO_IMAGEN = b"IMAGEN-SECRETA-F054"


def _correo_adjunto(att_id="c1", *, inline=False, odata_type=ITEM, size=5000):
    return adjunto(
        att_id, NOMBRE_GRAPH, inline=inline, content_type="message/rfc822", odata_type=odata_type, size=size
    )


def _eml_completo() -> bytes:
    interior = correo(adjuntos=[fichero_pdf("nivel2.pdf")])
    return a_bytes(correo(adjuntos=[
        fichero_pdf("albaran.pdf", paginas=2),
        fichero_png("foto.png", datos=png_bytes(RELLENO_IMAGEN)),
        fichero_png("logo.png", disposicion="inline"),
        fichero_texto(),
        Anidado(interior, nombre=f"{CENTINELA_F054}.eml"),
    ]))


def _escenario(nombre: str):
    """(adjuntos, ficheros, max_bytes) de cada rama del pipeline."""
    directo = adjunto("a", "fuera.pdf")
    base = {"a": pdf_de_paginas(1)}
    if nombre == "exito_mixto":
        return [directo, _correo_adjunto()], {**base, "c1": _eml_completo()}, 25 * 1024 * 1024
    if nombre == "descarga_falla":
        return [_correo_adjunto()], {"c1": RuntimeError(f"Graph 500 {CENTINELA_F054}")}, 25 * 1024 * 1024
    if nombre == "ilegible":
        return [_correo_adjunto()], {"c1": b""}, 25 * 1024 * 1024
    if nombre == "tope_excedido":
        return [_correo_adjunto()], {"c1": a_bytes(envolver(correo(adjuntos=[fichero_pdf("x.pdf")]), 5))}, 25 * 1024 * 1024
    if nombre == "sin_documentos":
        return [directo, _correo_adjunto()], {**base, "c1": a_bytes(correo(adjuntos=[fichero_texto()]))}, 25 * 1024 * 1024
    if nombre == "documento_excede":
        grande = a_bytes(correo(adjuntos=[fichero_png("grande.png", datos=png_bytes(RELLENO_IMAGEN * 200))]))
        return [_correo_adjunto(size=100)], {"c1": grande}, 2000
    if nombre == "descartes_r2":
        return (
            [directo, _correo_adjunto("c1", inline=True), _correo_adjunto("c2", odata_type=REFERENCE),
             _correo_adjunto("c3", size=10_000)],
            base,
            5000,
        )
    assert nombre == "nada_elegible"
    return [_correo_adjunto(inline=True)], {}, 25 * 1024 * 1024


ESCENARIOS = [
    "exito_mixto", "descarga_falla", "ilegible", "tope_excedido",
    "sin_documentos", "documento_excede", "descartes_r2", "nada_elegible",
]


@pytest.mark.parametrize("escenario", ESCENARIOS)
def test_f054_r25_ningun_log_lleva_datos_del_correo_interior(caplog, escenario):
    adjuntos, ficheros, max_bytes = _escenario(escenario)
    buzon = BuzonDoble(mensajes=[mensaje("msg-1")], adjuntos={"msg-1": adjuntos}, ficheros=ficheros)

    with caplog.at_level(logging.DEBUG):
        construir_pipeline(buzon, IntakeDoble()).run_once(
            mailbox=BUZON,
            source_folder=CARPETA_ORIGEN,
            processed_folder_id=ID_PROCESADOS,
            errors_folder_id=ID_ERRORES,
            top=10,
            max_attachment_bytes=max_bytes,
        )

    texto = caplog.text
    # El ciclo llego hasta el final y el correo adjunto aparece por su id.
    assert buzon.movidos, "el correo tiene que haberse movido"
    assert "c1" in texto
    # R25: nada del interior ni el name de Graph del correo adjunto.
    assert CENTINELA_F054 not in texto
    assert FECHA_INTERIOR not in texto
    assert "proveedor@ejemplo.test>" not in texto
    assert RELLENO_IMAGEN.decode() not in texto
    assert "%PDF" not in texto
    for crudo in ficheros.values():
        if isinstance(crudo, bytes) and len(crudo) > 60:
            assert base64.b64encode(crudo)[:40].decode() not in texto
    # R36 de F-048: el cuerpo del exterior sigue fuera.
    assert CENTINELA not in texto


def test_f054_r25_el_exito_registra_ids_y_recuentos_sin_contenido(caplog):
    adjuntos, ficheros, max_bytes = _escenario("exito_mixto")
    buzon = BuzonDoble(mensajes=[mensaje("msg-1")], adjuntos={"msg-1": adjuntos}, ficheros=ficheros)

    with caplog.at_level(logging.DEBUG):
        construir_pipeline(buzon, IntakeDoble()).run_once(
            mailbox=BUZON,
            source_folder=CARPETA_ORIGEN,
            processed_folder_id=ID_PROCESADOS,
            errors_folder_id=ID_ERRORES,
            top=10,
            max_attachment_bytes=max_bytes,
        )

    resumen = [r.getMessage() for r in caplog.records if "documentos interiores" in r.getMessage()]
    assert resumen == ["msg=msg-1 att=c1 documentos interiores: 2 PDF y 1 imagen(es), partes_ignoradas=4"]
    assert buzon.movidos == [("msg-1", ID_PROCESADOS)]
