# tests/test_f048_r36_logs.py
"""R36 (F-048, T11): ningun log de sv1 contiene el CUERPO del correo.

Ciclo completo de ``run_once`` a nivel DEBUG con las piezas reales de sv1
—``GraphMailClient`` sobre ``httpx.MockTransport``, el ``PdfPageSplitter`` y
el ``IntakeColaClient``— y dobles solo en los bordes (Graph, almacen, cola,
``workflow_runs``). El cuerpo lleva el centinela ``CENTINELA-F048`` y se
busca en TODO lo que se ha logueado. El asunto lo loguea sv1 desde antes
de esta feature (decision del humano): por eso el centinela va solo en el
cuerpo. Ningun test sale a la red; textos inventados.
"""
from __future__ import annotations

import logging

import httpx
import pytest
from application.pipelines.polling_pipeline import PollingPipeline
from dobles_sv1 import (
    BUZON,
    CARPETA_ORIGEN,
    CENTINELA,
    ID_ERRORES,
    ID_PROCESADOS,
    AlmacenDoble,
    PublicadorDoble,
    RepositorioDoble,
    ejecutar_ciclo,
    pdf_de_paginas,
)
from infrastructure.colas.intake_cola_adapter import IntakeColaClient
from infrastructure.document.mime_documento_extractor import MimeDocumentoExtractor
from infrastructure.document.pdf_page_splitter import PdfPageSplitter
from infrastructure.graph.mail_client import GraphMailClient

CUERPO_TEXTO = f"Buenos dias, material para la obra 0945.\n{CENTINELA} datos personales"
CUERPO_HTML = f"<html><body><p>Obra 0945</p><div>{CENTINELA} datos personales</div></body></html>"


class _Token:
    def get_token(self) -> str:
        return "token-de-prueba"


class _GraphFalso:
    """Graph en memoria: un mensaje con un PDF de dos paginas."""

    def __init__(self, contenido: dict | None, estado_contenido: int = 200) -> None:
        self._contenido = contenido
        self._estado_contenido = estado_contenido
        self.metodos: list[tuple[str, str]] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        ruta = request.url.path.removeprefix(f"/v1.0/users/{BUZON}")
        self.metodos.append((request.method, ruta))
        if request.method == "POST" and ruta == "/messages/msg-1/move":
            return httpx.Response(201, json={"id": "msg-1"})
        assert request.method == "GET", f"escritura inesperada: {request.method} {ruta}"
        if ruta == f"/mailFolders/{CARPETA_ORIGEN}/messages":
            return httpx.Response(200, json={"value": [{
                "id": "msg-1",
                "subject": "Albaran obra",
                "from": {"emailAddress": {"address": "proveedor@ejemplo.test"}},
                "receivedDateTime": "2026-09-23T08:00:00Z",
                "isRead": False,
                "hasAttachments": True,
            }]})
        if ruta == "/messages/msg-1/attachments":
            return httpx.Response(200, json={"value": [{
                "id": "att-1", "name": "albaran.pdf", "contentType": "application/pdf",
                "size": 1000, "isInline": False,
            }]})
        if ruta == "/messages/msg-1/attachments/att-1/$value":
            return httpx.Response(200, content=pdf_de_paginas(2))
        if ruta == "/messages/msg-1":
            return httpx.Response(self._estado_contenido, json=self._contenido)
        raise AssertionError(f"ruta inesperada: {ruta}")


class _AlmacenQueCitaElCorreo(AlmacenDoble):
    """Almacen cuyo ``put_json`` falla citando lo que se le pidio guardar.

    Simula un SDK que, al fallar, repite el contenido en el mensaje de la
    excepcion: el peor caso para el log de ``OrchestratorError`` (CR-B3).
    """

    def put_json(self, contenedor: str, nombre: str, objeto: object) -> None:
        self._llamadas.append(("put_json", contenedor, nombre))
        raise OSError(f"no se pudo guardar {nombre}: {objeto!r}")


def _ciclo(
    graph: _GraphFalso, almacen: AlmacenDoble | None = None
) -> tuple[AlmacenDoble, PublicadorDoble]:
    llamadas: list = []
    almacen = almacen if almacen is not None else AlmacenDoble(llamadas)
    llamadas = almacen._llamadas
    publicador = PublicadorDoble(llamadas)
    pipeline = PollingPipeline(
        mailbox=GraphMailClient(
            token_provider=_Token(),
            timeout_s=5,
            http_client=httpx.Client(transport=httpx.MockTransport(graph)),
        ),
        orchestrator=IntakeColaClient(
            repositorio=RepositorioDoble(llamadas),
            almacen=almacen,
            publicador=publicador,
        ),
        pdf_splitter=PdfPageSplitter(),
        extractor_correo=MimeDocumentoExtractor(),
    )
    ejecutar_ciclo(pipeline)
    return almacen, publicador


@pytest.mark.parametrize(
    "unico",
    [
        {"contentType": "text", "content": CUERPO_TEXTO},
        {"contentType": "html", "content": CUERPO_HTML},
    ],
    ids=["texto", "html"],
)
def test_f048_r36_ciclo_completo_a_debug_sin_el_cuerpo_en_el_log(caplog, unico):
    graph = _GraphFalso({"subject": "Albaran obra", "uniqueBody": unico})

    with caplog.at_level(logging.DEBUG):
        almacen, publicador = _ciclo(graph)

    # El cuerpo SI viajo (al blob lateral): el test no es vacuo...
    blobs_correo = [v for (_, nombre), v in almacen.blobs.items() if nombre.endswith(".correo.json")]
    assert len(blobs_correo) == 2
    assert all(CENTINELA in b["cuerpo"] for b in blobs_correo)
    assert len(publicador.publicados) == 2
    # ...pero no al log: solo la huella abreviada.
    assert caplog.records, "el ciclo tiene que haber logueado algo"
    assert CENTINELA not in caplog.text
    assert blobs_correo[0]["sha256"][:8] in caplog.text
    assert ("POST", "/messages/msg-1/move") in graph.metodos
    assert [m for m, _ in graph.metodos].count("POST") == 1


def test_f048_r36_fallo_de_graph_al_pedir_el_contenido_sin_el_cuerpo_en_el_log(caplog):
    graph = _GraphFalso({"error": {"message": f"no disponible: {CENTINELA}"}}, estado_contenido=503)

    with caplog.at_level(logging.DEBUG):
        almacen, publicador = _ciclo(graph)

    assert CENTINELA not in caplog.text
    assert not [n for (_, n) in almacen.blobs if n.endswith(".correo.json")]
    assert [m.correo_blob for _, m in publicador.publicados] == [None, None]
    assert ("POST", "/messages/msg-1/move") in graph.metodos
    assert "sin contexto de correo (RuntimeError)" in caplog.text


def test_f048_r36_error_del_intake_que_cita_el_correo_no_llega_al_log(caplog):
    """CR-B3: el log de ``OrchestratorError`` no repite el cuerpo aunque la excepcion lo cite."""
    graph = _GraphFalso({"subject": "Albaran obra", "uniqueBody": {"contentType": "text", "content": CUERPO_TEXTO}})
    almacen = _AlmacenQueCitaElCorreo([])

    with caplog.at_level(logging.DEBUG):
        _, publicador = _ciclo(graph, almacen)

    # El fallo ocurrio de verdad y se registro (el test no es vacuo)...
    assert [n for (_, _, n) in (c for c in almacen._llamadas if c[0] == "put_json")]
    assert publicador.publicados == []
    errores = [r.getMessage() for r in caplog.records if "ERROR sv7" in r.getMessage()]
    assert len(errores) == 2
    # ...sin el cuerpo (solo el tipo de la excepcion), y el correo va a
    # Errores como hoy con un fallo de blob.
    assert CENTINELA not in caplog.text
    assert all("OSError" in m for m in errores)
    (movimiento,) = [c for c in graph.metodos if c[0] == "POST"]
    assert movimiento == ("POST", "/messages/msg-1/move")


def test_f048_r36_el_destino_del_ciclo_completo_es_procesados():
    """Control: el ciclo real llega hasta el final y mueve a Procesados."""
    graph = _GraphFalso({"subject": "Albaran obra", "uniqueBody": {"contentType": "text", "content": "x"}})
    peticiones: list[httpx.Request] = []

    def espia(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return graph(request)

    llamadas: list = []
    pipeline = PollingPipeline(
        mailbox=GraphMailClient(
            token_provider=_Token(),
            timeout_s=5,
            http_client=httpx.Client(transport=httpx.MockTransport(espia)),
        ),
        orchestrator=IntakeColaClient(
            repositorio=RepositorioDoble(llamadas),
            almacen=AlmacenDoble(llamadas),
            publicador=PublicadorDoble(llamadas),
        ),
        pdf_splitter=PdfPageSplitter(),
        extractor_correo=MimeDocumentoExtractor(),
    )
    ejecutar_ciclo(pipeline)

    (movimiento,) = [p for p in peticiones if p.method == "POST"]
    assert b'"destinationId":"' + ID_PROCESADOS.encode() in movimiento.content.replace(b" ", b"")
    assert ID_ERRORES.encode() not in movimiento.content
