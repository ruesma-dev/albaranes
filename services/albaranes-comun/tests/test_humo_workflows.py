# tests/test_humo_workflows.py
"""Test de humo del repositorio compartido de workflows.

Usa SQLite en memoria (no requiere PostgreSQL): valida la creación
idempotente por ``correlation_key`` y las transiciones de estado.

Ejecutar:  pytest tests/test_humo_workflows.py -v
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine

from ruesma_comun.db.session_factory import SessionFactoryDesdeEngine
from ruesma_comun.workflows.estados import WorkflowState
from ruesma_comun.workflows.orm import crear_tablas
from ruesma_comun.workflows.repositorio import RepositorioWorkflows


@pytest.fixture()
def repo() -> RepositorioWorkflows:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    crear_tablas(engine)
    return RepositorioWorkflows(SessionFactoryDesdeEngine(engine))


def test_creacion_idempotente_por_correlation_key(repo: RepositorioWorkflows) -> None:
    clave = "email:MSG123:abcdef0123456789"

    primero = repo.crear_si_no_existe(correlation_key=clave, attachment_sha256="abc")
    assert primero.creado is True
    assert primero.estado_actual == WorkflowState.EMAIL_RECEIVED.value

    # Reenvío del mismo evento (Graph es "al menos una vez"): NO se
    # crea otro workflow y el llamante sabe que NO debe encolar.
    segundo = repo.crear_si_no_existe(correlation_key=clave)
    assert segundo.creado is False
    assert segundo.workflow_id == primero.workflow_id


def test_transiciones_y_vinculo_de_documento(repo: RepositorioWorkflows) -> None:
    res = repo.crear_si_no_existe(correlation_key="email:M1:sha1")

    assert repo.transicionar(
        workflow_id=res.workflow_id, a_estado=WorkflowState.EXTRACTING
    )
    assert repo.vincular_documento(
        workflow_id=res.workflow_id, document_id="doc-1", attachment_sha256="sha1"
    )
    assert repo.transicionar(
        document_id="doc-1", a_estado=WorkflowState.AWAITING_APPROVAL
    )

    wf = repo.obtener_por_document_id("doc-1")
    assert wf is not None
    assert wf.current_state == WorkflowState.AWAITING_APPROVAL.value
    assert wf.completed_at_utc is None  # estado pasivo, no terminal

    # Terminal: queda sellado con completed_at.
    assert repo.transicionar(document_id="doc-1", a_estado=WorkflowState.APPROVED)
    wf = repo.obtener_por_document_id("doc-1")
    assert wf.completed_at_utc is not None


def test_marcar_fallo_incrementa_reintentos(repo: RepositorioWorkflows) -> None:
    res = repo.crear_si_no_existe(correlation_key="email:M2:sha2")
    repo.vincular_documento(workflow_id=res.workflow_id, document_id="doc-2")

    repo.marcar_fallo(
        document_id="doc-2",
        estado_fallo=WorkflowState.EXTRACTION_FAILED,
        error="boom",
    )
    wf = repo.obtener_por_document_id("doc-2")
    assert wf.current_state == WorkflowState.EXTRACTION_FAILED.value
    assert wf.retry_count == 1
    assert wf.last_error == "boom"

    # La transición que no localiza workflow no revienta: devuelve False.
    assert (
        repo.transicionar(document_id="no-existe", a_estado=WorkflowState.VALUING)
        is False
    )
