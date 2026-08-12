# ruesma_comun/workflows/estados.py
"""Máquina de estados del albarán — heredada LITERALMENTE de sv7.

sv7 desaparece como proceso, pero su máquina de estados (validada en
producción local) sobrevive como contrato compartido: cada worker
transiciona el estado de su paso y sv4 lo muestra. No se inventan
estados nuevos.
"""
from __future__ import annotations

from enum import Enum


class WorkflowState(str, Enum):
    """Estados posibles del workflow albaran_e2e.

    Activos (un worker está trabajando el paso):
      - email_received        — creado por sv1-intake, listo para extraer
      - extracting            — sv2 fase 1 en curso
      - reviewing             — sv2 grounding + fase 2 en curso
      - persisting            — sv3 en curso
      - valuing               — valorador (sv5+sv6) en curso

    Pasivos (esperando al revisor en sv4):
      - awaiting_contract_selection
      - awaiting_approval

    Terminales OK:
      - approved
      - completed_duplicate

    Terminales con fallo (reintetables desde sv4 re-encolando el paso):
      - extraction_failed
      - review_failed
      - persistence_failed
      - valuation_failed
    """

    EMAIL_RECEIVED = "email_received"
    EXTRACTING = "extracting"
    REVIEWING = "reviewing"
    PERSISTING = "persisting"
    AWAITING_CONTRACT_SELECTION = "awaiting_contract_selection"
    VALUING = "valuing"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    COMPLETED_DUPLICATE = "completed_duplicate"
    EXTRACTION_FAILED = "extraction_failed"
    REVIEW_FAILED = "review_failed"
    PERSISTENCE_FAILED = "persistence_failed"
    VALUATION_FAILED = "valuation_failed"

    # Terminal administrativo: el documento asociado fue PURGADO
    # (hard-delete) desde sv4. El workflow se conserva como auditoría
    # pero NO cuenta para el dedup por correlation_key ni sha256: el
    # mismo PDF puede reprocesarse.
    PURGED = "purged"


ACTIVE_STATES = frozenset({
    WorkflowState.EMAIL_RECEIVED,
    WorkflowState.EXTRACTING,
    WorkflowState.REVIEWING,
    WorkflowState.PERSISTING,
    WorkflowState.VALUING,
})

WAITING_STATES = frozenset({
    WorkflowState.AWAITING_CONTRACT_SELECTION,
    WorkflowState.AWAITING_APPROVAL,
})

TERMINAL_OK_STATES = frozenset({
    WorkflowState.APPROVED,
    WorkflowState.COMPLETED_DUPLICATE,
})

FAILED_STATES = frozenset({
    WorkflowState.EXTRACTION_FAILED,
    WorkflowState.REVIEW_FAILED,
    WorkflowState.PERSISTENCE_FAILED,
    WorkflowState.VALUATION_FAILED,
})

TERMINAL_STATES = TERMINAL_OK_STATES | {WorkflowState.PURGED}

# Estado de fallo que corresponde a cada cola — lo usa el ``on_poison``
# del consumidor de cada worker para marcar el workflow.
ESTADO_FALLO_POR_COLA: dict[str, WorkflowState] = {
    "q-extraccion": WorkflowState.EXTRACTION_FAILED,
    "q-persistencia": WorkflowState.PERSISTENCE_FAILED,
    "q-valoracion": WorkflowState.VALUATION_FAILED,
}
