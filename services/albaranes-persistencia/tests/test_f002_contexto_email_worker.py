# tests/test_f002_contexto_email_worker.py
"""F-002 · R12 — contexto de email en el modo colas.

El mensaje de ``q-persistencia`` solo trae ``document_id`` y
``correlation_key``, asi que hasta ahora ``email_received_datetime``
quedaba NULL en el merge y el guard de año (R13) se quedaba sin
referencia. El dato SI existe: sv1 lo guardo en
``workflow_runs.payload_json``.

Sin BBDD: el repositorio de workflows es un doble.
"""
from __future__ import annotations

import json

import pytest
from ruesma_comun.colas import MensajePersistencia

from interface_adapters.worker.persistence_worker import (
    construir_handler_persistencia,
)
from interface_adapters.worker.ports import DocumentoPdf
from interface_adapters.worker.workflow_context_adapter import (
    FuenteContextoEmailWorkflows,
)

CLAVE = "correo-1|adjunto-1|p1"

PAYLOAD_SV1 = {
    "email_message_id": "AAMkAGI2",
    "email_received_at_utc": "2026-08-12T09:30:00Z",
    "from_address": "proveedor@ejemplo.es",
    "subject": "Albaran 12345",
    "attachment_filename": "albaran.pdf",
    "attachment_sha256": "abc123",
    "attachment_content_type": "application/pdf",
    "attachment_size_bytes": 1024,
    "page_number": 2,
    "total_pages": 3,
    "page_sha256": "def456",
}


class FilaWorkflow:
    def __init__(self, payload_json: str) -> None:
        self.payload_json = payload_json


class RepoWorkflowsFake:
    def __init__(self, fila=None, *, error: Exception | None = None) -> None:
        self._fila = fila
        self._error = error
        self.consultas: list[str] = []

    def obtener_por_correlation_key(self, correlation_key: str):
        self.consultas.append(correlation_key)
        if self._error is not None:
            raise self._error
        return self._fila


def _fuente(payload) -> FuenteContextoEmailWorkflows:
    fila = FilaWorkflow(payload) if payload is not None else None
    return FuenteContextoEmailWorkflows(RepoWorkflowsFake(fila))


# ---------------------------------------------------------------- #
# R12 — el adaptador traduce payload_json al contexto que espera sv3.
# ---------------------------------------------------------------- #
def test_f002_r12_payload_de_sv1_se_traduce_a_contexto_de_email() -> None:
    contexto = _fuente(json.dumps(PAYLOAD_SV1)).obtener(CLAVE)

    assert contexto["email"] == {
        "id": "AAMkAGI2",
        "subject": "Albaran 12345",
        "sender": "proveedor@ejemplo.es",
        "receivedDateTime": "2026-08-12T09:30:00Z",
    }


def test_f002_r12_payload_de_sv1_se_traduce_a_contexto_de_documento() -> None:
    contexto = _fuente(json.dumps(PAYLOAD_SV1)).obtener(CLAVE)

    assert contexto["document"] == {
        "source_attachment_filename": "albaran.pdf",
        "source_attachment_mime_type": "application/pdf",
        "source_attachment_sha256": "abc123",
        "page_number": 2,
        "page_count": 3,
    }


def test_f002_r12_sin_fila_de_workflow_el_contexto_va_vacio() -> None:
    assert _fuente(None).obtener(CLAVE) == {}


@pytest.mark.parametrize("payload", ["", "no soy json", "[1,2]", "null"])
def test_f002_r12_payload_roto_no_revienta(payload: str) -> None:
    assert _fuente(payload).obtener(CLAVE) == {}


def test_f002_r12_error_del_repositorio_no_revienta() -> None:
    fuente = FuenteContextoEmailWorkflows(
        RepoWorkflowsFake(error=RuntimeError("BBDD caida")),
    )

    assert fuente.obtener(CLAVE) == {}


def test_f002_r12_sin_correlation_key_no_se_consulta_la_bbdd() -> None:
    repo = RepoWorkflowsFake(FilaWorkflow(json.dumps(PAYLOAD_SV1)))

    assert FuenteContextoEmailWorkflows(repo).obtener("") == {}
    assert repo.consultas == []


# ---------------------------------------------------------------- #
# R12 — el handler del worker fusiona ese contexto con el actual.
# ---------------------------------------------------------------- #
class PipelineEspia:
    def __init__(self) -> None:
        self.contextos: list[dict] = []

    def run(self, request):
        self.contextos.append(request.context)
        return type(
            "R", (), {
                "document_id": "merge-1",
                "contratos_count": 0,
                "selected_contrato_codigo": None,
            },
        )()


class FuenteDocumentoFake:
    def obtener(self, document_id: str) -> DocumentoPdf:
        return DocumentoPdf(
            filename="albaran.pdf",
            mime_type="application/pdf",
            file_bytes=b"%PDF-1.4",
        )


class FuenteEnvelopeFake:
    def obtener(self, document_id: str) -> dict:
        return {"meta": {"source_sha256": "abc123"}, "data": {}}


class FuenteContextoFake:
    def __init__(self, contexto: dict, *, error: Exception | None = None):
        self._contexto = contexto
        self._error = error

    def obtener(self, correlation_key: str) -> dict:
        if self._error is not None:
            raise self._error
        return dict(self._contexto)


def _ejecutar_handler(fuente_contexto) -> PipelineEspia:
    pipeline = PipelineEspia()
    handler = construir_handler_persistencia(
        pipeline=pipeline,
        fuente_documento=FuenteDocumentoFake(),
        fuente_envelope=FuenteEnvelopeFake(),
        fuente_contexto=fuente_contexto,
    )
    handler(MensajePersistencia(document_id="doc-1", correlation_key=CLAVE))
    return pipeline


def test_f002_r12_el_handler_pasa_la_fecha_de_recepcion_al_pipeline() -> None:
    contexto = {
        "email": {
            "id": "AAMkAGI2",
            "subject": "Albaran 12345",
            "sender": "proveedor@ejemplo.es",
            "receivedDateTime": "2026-08-12T09:30:00Z",
        },
    }

    pipeline = _ejecutar_handler(FuenteContextoFake(contexto))

    enviado = pipeline.contextos[0]
    assert enviado["correlation_key"] == CLAVE
    assert enviado["email"]["receivedDateTime"] == "2026-08-12T09:30:00Z"


def test_f002_r12_sin_contexto_el_handler_manda_lo_de_siempre() -> None:
    pipeline = _ejecutar_handler(FuenteContextoFake({}))

    assert pipeline.contextos == [{"correlation_key": CLAVE}]


def test_f002_r12_sin_fuente_cableada_el_handler_manda_lo_de_siempre() -> None:
    pipeline = _ejecutar_handler(None)

    assert pipeline.contextos == [{"correlation_key": CLAVE}]


def test_f002_r16_una_fuente_que_revienta_no_rompe_el_handler() -> None:
    pipeline = _ejecutar_handler(
        FuenteContextoFake({}, error=RuntimeError("BBDD caida")),
    )

    assert pipeline.contextos == [{"correlation_key": CLAVE}]
