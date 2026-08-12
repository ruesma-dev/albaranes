# ruesma_comun/workflows/repositorio.py
"""Repositorio compartido de la máquina de estados del albarán.

API mínima que necesitan los workers y sv4 — deliberadamente más
pequeña que el repositorio del motor de sv7 (lo que era del motor,
muere con el motor):

  - ``crear_si_no_existe``  → sv1-intake. Idempotencia por el UNIQUE de
    ``correlation_key``: el INSERT que choca = duplicado = NO encolar.
  - ``transicionar``        → cada worker al empezar/terminar su paso.
  - ``vincular_documento``  → sv2, cuando el document_id queda fijado.
  - ``marcar_fallo``        → el ``on_poison`` de cada consumidor.
  - ``obtener_por_*``       → sv4 (mostrar estado, botón reintentar).
"""
from __future__ import annotations

import logging
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ruesma_comun.workflows.estados import (
    TERMINAL_STATES,
    WorkflowState,
)
from ruesma_comun.workflows.orm import WorkflowRunOrm

logger = logging.getLogger(__name__)

KIND_ALBARAN_E2E = "albaran_e2e"


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class ResultadoCreacion:
    workflow_id: str
    creado: bool  # False ⇒ ya existía (duplicado): NO encolar
    estado_actual: str


class RepositorioWorkflows:
    """Cada método abre/cierra su transacción con la Session recibida
    de una ``session_factory`` (la del paquete común o la del servicio).
    """

    def __init__(self, session_factory) -> None:  # noqa: ANN001 — duck typing
        self._session_factory = session_factory

    @contextmanager
    def _abrir(self):
        """Sesión sobre la API canónica ``create_session()`` del
        ``SessionFactory`` del paquete (o cualquier duck-type)."""
        session: Session = self._session_factory.create_session()
        try:
            yield session
        finally:
            session.close()

    # ----------------------------------------------------------- #
    # Creación idempotente (sv1-intake).
    # ----------------------------------------------------------- #
    def crear_si_no_existe(
        self,
        *,
        correlation_key: str,
        payload_json: str = "{}",
        document_id: str | None = None,
        attachment_sha256: str | None = None,
        kind: str = KIND_ALBARAN_E2E,
    ) -> ResultadoCreacion:
        ahora = _utc_iso()
        nuevo = WorkflowRunOrm(
            id=str(uuid.uuid4()),
            kind=kind,
            document_id=document_id,
            current_state=WorkflowState.EMAIL_RECEIVED.value,
            attachment_sha256=attachment_sha256,
            correlation_key=correlation_key,
            payload_json=payload_json,
            started_at_utc=ahora,
            updated_at_utc=ahora,
            retry_count=0,
        )
        session: Session
        with self._abrir() as session:
            session.add(nuevo)
            try:
                session.commit()
                return ResultadoCreacion(
                    workflow_id=nuevo.id,
                    creado=True,
                    estado_actual=nuevo.current_state,
                )
            except IntegrityError:
                session.rollback()

        # Ya existía: devolvemos el vigente (duplicado).
        with self._abrir() as session:
            existente = (
                session.query(WorkflowRunOrm)
                .filter(WorkflowRunOrm.correlation_key == correlation_key)
                .one()
            )
            logger.info(
                "[workflows] duplicado correlation_key=%s estado=%s",
                correlation_key,
                existente.current_state,
            )
            return ResultadoCreacion(
                workflow_id=existente.id,
                creado=False,
                estado_actual=existente.current_state,
            )

    # ----------------------------------------------------------- #
    # Transiciones (workers).
    # ----------------------------------------------------------- #
    def transicionar(
        self,
        *,
        a_estado: WorkflowState,
        workflow_id: str | None = None,
        document_id: str | None = None,
        error: str | None = None,
        incrementar_reintentos: bool = False,
    ) -> bool:
        """Transiciona el workflow localizado por id o por document_id.

        Devuelve False (y loguea) si no se encuentra — un worker nunca
        debe reventar por no poder anotar estado.
        """
        with self._abrir() as session:
            orm = self._localizar(session, workflow_id, document_id)
            if orm is None:
                logger.warning(
                    "[workflows] transición a %s sin workflow (id=%s doc=%s)",
                    a_estado.value,
                    workflow_id,
                    document_id,
                )
                return False
            orm.current_state = a_estado.value
            orm.updated_at_utc = _utc_iso()
            orm.last_error = error
            if incrementar_reintentos:
                orm.retry_count = int(orm.retry_count or 0) + 1
            if a_estado in TERMINAL_STATES:
                orm.completed_at_utc = orm.updated_at_utc
            session.commit()
            return True

    def vincular_documento(
        self,
        *,
        workflow_id: str,
        document_id: str,
        attachment_sha256: str | None = None,
    ) -> bool:
        with self._abrir() as session:
            orm = session.get(WorkflowRunOrm, workflow_id)
            if orm is None:
                return False
            orm.document_id = document_id
            if attachment_sha256:
                orm.attachment_sha256 = attachment_sha256
            orm.updated_at_utc = _utc_iso()
            session.commit()
            return True

    def marcar_fallo(
        self,
        *,
        estado_fallo: WorkflowState,
        workflow_id: str | None = None,
        document_id: str | None = None,
        error: str | None = None,
    ) -> bool:
        return self.transicionar(
            a_estado=estado_fallo,
            workflow_id=workflow_id,
            document_id=document_id,
            error=error,
            incrementar_reintentos=True,
        )

    # ----------------------------------------------------------- #
    # Lecturas (sv4 y los propios workers).
    # ----------------------------------------------------------- #
    def obtener_por_correlation_key(self, correlation_key: str) -> WorkflowRunOrm | None:
        with self._abrir() as session:
            orm = (
                session.query(WorkflowRunOrm)
                .filter(WorkflowRunOrm.correlation_key == correlation_key)
                .one_or_none()
            )
            if orm is not None:
                session.expunge(orm)
            return orm

    def obtener_por_document_id(self, document_id: str) -> WorkflowRunOrm | None:
        with self._abrir() as session:
            orm = (
                session.query(WorkflowRunOrm)
                .filter(WorkflowRunOrm.document_id == document_id)
                .order_by(WorkflowRunOrm.started_at_utc.desc())
                .first()
            )
            if orm is not None:
                session.expunge(orm)
            return orm

    # ----------------------------------------------------------- #
    @staticmethod
    def _localizar(
        session: Session,
        workflow_id: str | None,
        document_id: str | None,
    ) -> WorkflowRunOrm | None:
        if workflow_id:
            return session.get(WorkflowRunOrm, workflow_id)
        if document_id:
            return (
                session.query(WorkflowRunOrm)
                .filter(WorkflowRunOrm.document_id == document_id)
                .order_by(WorkflowRunOrm.started_at_utc.desc())
                .first()
            )
        return None
