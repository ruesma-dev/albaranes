# ruesma_comun/workflows/orm.py
"""ORM de la tabla compartida de estado del albarán.

DECISIÓN: se conservan los nombres FÍSICOS de sv7 (``workflow_runs`` y
``workflow_step_history``) para no migrar los datos existentes — el
"renombrado" a tabla compartida es conceptual, no físico. Las columnas
son idénticas a ``sv7/infrastructure/database/orm_workflow_models.py``.

Propiedad: el DDL lo aporta este módulo (vía ``crear_tablas``) y lo
aplica ``caj-bootstrap-ddl``. Escriben los workers (cada uno SOLO las
transiciones de su paso) y sv1-intake (creación idempotente). Lee sv4.
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WorkflowRunOrm(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parent_workflow_id: Mapped[str | None] = mapped_column(String(36))
    document_id: Mapped[str | None] = mapped_column(String(36), index=True)
    current_state: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    attachment_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    correlation_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    started_at_utc: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    updated_at_utc: Mapped[str] = mapped_column(String(64), nullable=False)
    completed_at_utc: Mapped[str | None] = mapped_column(String(64))
    last_error: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pending_event_json: Mapped[str | None] = mapped_column(Text)


class StepHistoryOrm(Base):
    __tablename__ = "workflow_step_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    workflow_run_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    step_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    input_json: Mapped[str | None] = mapped_column(Text)
    output_json: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    started_at_utc: Mapped[str] = mapped_column(String(64), nullable=False)
    completed_at_utc: Mapped[str | None] = mapped_column(String(64))
    duration_ms: Mapped[int | None] = mapped_column(Integer)


def crear_tablas(engine: Engine) -> None:
    """DDL idempotente (CREATE ... IF NOT EXISTS vía metadata)."""
    Base.metadata.create_all(engine, checkfirst=True)
