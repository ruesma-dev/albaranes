# tests/test_f048_r7_r10_intake.py
"""R7, R8 y R10 en el intake por colas de sv1 (F-048, T10).

Por cada pagina NUEVA con contexto, el intake guarda
``input/{document_id}.correo.json`` ANTES de publicar ``MensajeExtraccion``,
que lleva el nombre del blob en ``correo_blob``. En el duplicado no escribe
nada. ``workflow_runs.payload_json`` guarda el sha256 del correo, nunca el
cuerpo. Repositorio, almacen y publicador son dobles; textos inventados.
"""
from __future__ import annotations

import json
import logging

import pytest
from dobles_sv1 import CENTINELA, AlmacenDoble, PublicadorDoble, RepositorioDoble
from domain.ports.orchestrator_port import OrchestratorError
from infrastructure.colas.intake_cola_adapter import IntakeColaClient
from ruesma_comun.colas.mensajes import MensajeExtraccion
from ruesma_comun.correo import (
    construir_contexto_correo,
    leer_contexto_correo,
    nombre_blob_correo,
)

META = {
    "email_message_id": "msg-1",
    "subject": "Albaran obra",
    "page_sha256": "a" * 64,
    "page_number": 1,
}
CTX = construir_contexto_correo("Albaran obra", f"Material para la obra 0945. {CENTINELA}")


def _intake(*, creado: bool = True, error_repo: Exception | None = None, fallar_json: bool = False):
    llamadas: list = []
    repo = RepositorioDoble(llamadas, creado=creado, error=error_repo)
    almacen = AlmacenDoble(llamadas, fallar_json=fallar_json)
    publicador = PublicadorDoble(llamadas)
    cliente = IntakeColaClient(repositorio=repo, almacen=almacen, publicador=publicador)
    return cliente, llamadas, repo, almacen, publicador


def _enviar(cliente: IntakeColaClient, contexto=CTX, meta: dict | None = None):
    return cliente.submit_email_received(
        meta=dict(META) if meta is None else meta,
        file_bytes=b"%PDF-falso",
        filename="albaran.pdf",
        content_type="application/pdf",
        contexto_correo=contexto,
    )


def test_f048_r7_pagina_nueva_guarda_el_blob_lateral_antes_de_publicar():
    cliente, llamadas, _, almacen, publicador = _intake()

    ack = _enviar(cliente)

    assert ack.accepted is True and ack.duplicate is False
    (cola, mensaje), = publicador.publicados
    doc = mensaje.document_id
    assert [c[0] for c in llamadas] == ["crear_si_no_existe", "put_bytes", "put_json", "publicar"]
    assert llamadas[2] == ("put_json", "input", f"{doc}.correo.json")
    assert llamadas.index(("put_json", "input", f"{doc}.correo.json")) < llamadas.index(
        ("publicar", "q-extraccion", doc)
    )
    assert cola == "q-extraccion"
    assert mensaje.correo_blob == nombre_blob_correo(doc) == f"{doc}.correo.json"
    assert almacen.blobs[("input", f"{doc}.correo.json")] == CTX.model_dump(mode="json")


def test_f048_r7_lo_que_guarda_sv1_lo_lee_sv2_con_la_misma_funcion():
    cliente, _, _, almacen, publicador = _intake()

    _enviar(cliente)

    (_, mensaje), = publicador.publicados
    assert leer_contexto_correo(almacen, mensaje.correo_blob) == CTX


def test_f048_r7_sin_contexto_no_hay_blob_ni_campo_y_el_payload_es_el_de_hoy():
    cliente, llamadas, repo, _, publicador = _intake()

    _enviar(cliente, contexto=None)

    assert [c[0] for c in llamadas] == ["crear_si_no_existe", "put_bytes", "publicar"]
    (_, mensaje), = publicador.publicados
    assert mensaje.correo_blob is None
    assert repo.payloads == [json.dumps(META, ensure_ascii=False)]


def test_f048_r7_en_el_duplicado_no_se_escribe_nada():
    cliente, llamadas, _, almacen, publicador = _intake(creado=False)

    ack = _enviar(cliente)

    assert ack.duplicate is True
    assert [c[0] for c in llamadas] == ["crear_si_no_existe"]
    assert almacen.blobs == {}
    assert publicador.publicados == []


def test_f048_r7_sin_dedup_disponible_se_sigue_como_nuevo_con_el_blob():
    cliente, llamadas, _, _, publicador = _intake(error_repo=RuntimeError("tabla no existe"))

    _enviar(cliente)

    assert [c[0] for c in llamadas] == ["crear_si_no_existe", "put_bytes", "put_json", "publicar"]
    (_, mensaje), = publicador.publicados
    assert mensaje.correo_blob is not None


def test_f048_r7_si_no_se_puede_guardar_el_contexto_no_se_publica():
    cliente, llamadas, _, _, publicador = _intake(fallar_json=True)

    with pytest.raises(OrchestratorError):
        _enviar(cliente)

    assert publicador.publicados == []
    assert "publicar" not in [c[0] for c in llamadas]


def test_f048_r10_payload_json_lleva_el_sha256_y_nunca_el_cuerpo():
    cliente, _, repo, _, _ = _intake()
    meta = dict(META)

    _enviar(cliente, meta=meta)

    (payload,) = repo.payloads
    datos = json.loads(payload)
    assert datos["correo_sha256"] == CTX.sha256
    assert CENTINELA not in payload
    assert CTX.cuerpo not in payload
    assert meta == META  # no muta el meta del llamador


def test_f048_r8_el_mensaje_publicado_no_lleva_el_texto():
    grande = construir_contexto_correo("Albaran", CENTINELA + "x" * 60_000, max_caracteres=60_000)
    cliente, _, _, _, publicador = _intake()

    _enviar(cliente, contexto=grande)

    (_, mensaje), = publicador.publicados
    texto = mensaje.a_texto()
    assert len(texto.encode("utf-8")) < 1024
    assert CENTINELA not in texto
    assert isinstance(mensaje, MensajeExtraccion)


def test_f048_r36_el_log_del_intake_lleva_la_huella_y_no_el_texto(caplog):
    cliente, _, _, _, _ = _intake()

    with caplog.at_level(logging.DEBUG):
        _enviar(cliente)

    assert CTX.sha256[:8] in caplog.text
    assert CENTINELA not in caplog.text


def test_f048_r7_el_cliente_http_legado_declara_el_tipo_del_puerto():
    """CR-B6: ``contexto_correo`` con el mismo tipo que el puerto, no ``object``."""
    import inspect

    from domain.ports.orchestrator_port import OrchestratorClient
    from infrastructure.http.orchestrator_client import HttpOrchestratorClient

    def _anotacion(clase: type) -> object:
        return inspect.signature(clase.submit_email_received).parameters["contexto_correo"].annotation

    assert _anotacion(HttpOrchestratorClient) == _anotacion(OrchestratorClient) == "ContextoCorreo | None"
