# infrastructure/colas/colas_orchestrator_client.py
"""Adapter de COLAS del puerto :class:`OrchestratorClient`.

Sustituye al ``HttpOrchestratorClient`` (HTTP → sv7, disuelto). Mismos
métodos, misma filosofía best-effort: el dato fundamental ya está en
BBDD antes de notificar; la publicación/limpieza es solo el disparador.

Mapeo de eventos:
  - contract-selected → ``MensajePersistencia(force=True)`` → q-persistencia
    (sv3 re-enriquece el merge: PDF/MD del contrato + valoracion).
  - document-approved → ``MensajeFeedback(accion="alta")`` → q-feedback
    (F-053: lo consume sv9, que da de alta el albarán en Sigrid); y
    ``solicitar_alta_sigrid`` desde la ficha (``alta`` o
    ``verificar_anulacion``). Devuelven si publicaron.
  - document-purged   → limpieza directa de ``workflow_runs`` (BBDD), que
    desbloquea el dedup por contenido tras un hard-delete.

Honestidad del botón "Valorar ahora"
-------------------------------------
El endpoint ``/valuate`` del portal interpreta el ``dict`` devuelto: si
es ``None`` avisa "no se pudo encolar"; si ``action == "no_op"`` avisa
"nada que valorar"; en otro caso "valoración encolada". Para conservar
ese contrato sin sv7, devolvemos un dict equivalente al ``EventApplyResult``:
  - publicado OK → ``{"action": "queued", ...}``
  - no publicado → ``None``
"""
from __future__ import annotations

import logging
from typing import Any, get_args

from ruesma_comun.colas import (
    COLA_FEEDBACK,
    COLA_PERSISTENCIA,
    COLA_VALORACION,
)
from ruesma_comun.colas.mensajes import (
    MensajeFeedback,
    MensajePersistencia,
    MensajeValoracion,
)
from ruesma_comun.colas.publicador import PublicadorBestEffort

from domain.ports.orchestrator_port import OrchestratorClient
from infrastructure.database.workflow_runs_purger import WorkflowRunsPurger

logger = logging.getLogger(__name__)

#: Acciones de ``MensajeFeedback`` (R32): ``alta`` y ``verificar_anulacion``.
ACCIONES_FEEDBACK: frozenset[str] = frozenset(
    get_args(MensajeFeedback.model_fields["accion"].annotation)
)


class ColasOrchestratorClient(OrchestratorClient):
    def __init__(
        self,
        *,
        publicador: PublicadorBestEffort,
        workflow_runs_purger: WorkflowRunsPurger | None = None,
        cola_valoracion: str = COLA_VALORACION,
        cola_feedback: str = COLA_FEEDBACK,
    ) -> None:
        self._pub = publicador
        self._purger = workflow_runs_purger
        self._cola_valoracion = cola_valoracion
        self._cola_feedback = cola_feedback

    # --------------------------------------------------------------- #
    # contract-selected → q-valoracion (force=True)
    # --------------------------------------------------------------- #
    def notify_contract_selected(
        self,
        *,
        document_id: str,
        codigo_contrato: str,
        selected_by: str | None,
        selected_at_utc: str,
    ) -> dict[str, Any] | None:
        # Al SELECCIONAR contrato hay que pasar por sv3 (q-persistencia):
        # con VARIOS contratos, solo sv3 descarga el PDF/MD del elegido y
        # encadena la valoracion. Se publica el MERGE id: el worker de sv3
        # detecta que no hay blob con ese id y ejecuta el re-enrichment
        # del merge (reenrich_by_merge_id), que baja el PDF del contrato
        # seleccionado y dispara q-valoracion.
        mensaje = MensajePersistencia(document_id=document_id, force=True)
        publicado = self._pub.publicar(COLA_PERSISTENCIA, mensaje)
        if not publicado:
            return None
        return {
            "action": "queued",
            "detail": (
                f"publicado en {COLA_PERSISTENCIA} (contrato="
                f"{codigo_contrato}, force=True): sv3 baja PDF/MD del "
                f"contrato y encadena la valoracion."
            ),
            "previous_state": None,
            "new_state": "valuing",
            "workflow_id": None,
        }

    # --------------------------------------------------------------- #
    # document-approved → q-feedback
    # --------------------------------------------------------------- #
    def notify_document_approved(
        self,
        *,
        document_id: str,
        approved_by: str | None,
        approved_at_utc: str | None = None,
        review_notes: str | None = None,
    ) -> bool:
        """F-053 R1: el documento pasó a aprobado ⇒ alta en Sigrid (sv9).
        Devuelve si publicó (R4)."""
        return self.solicitar_alta_sigrid(
            document_id=document_id, accion="alta", solicitado_por=approved_by,
        )

    def solicitar_alta_sigrid(
        self,
        *,
        document_id: str,
        accion: str,
        solicitado_por: str | None,
    ) -> bool:
        """F-053 R28/R30: ``MensajeFeedback`` con su ``accion`` a
        ``q-feedback``. ``ValueError`` (sin publicar) si la acción no es de
        las de R32."""
        if accion not in ACCIONES_FEEDBACK:
            raise ValueError(f"accion de q-feedback no valida: {accion!r}")
        mensaje = MensajeFeedback(
            document_id=document_id,
            approved_by=solicitado_por,
            accion=accion,
        )
        return bool(self._pub.publicar(self._cola_feedback, mensaje))

    # --------------------------------------------------------------- #
    # document-purged → limpieza directa de workflow_runs (BBDD)
    # --------------------------------------------------------------- #
    def notify_document_purged(
        self,
        *,
        document_id: str,
        source_sha256: str | None,
        purged_by: str | None,
        purged_at_utc: str,
    ) -> dict[str, Any] | None:
        if self._purger is None:
            logger.warning(
                "[sv4-colas][purge] sin purger wire-ado; no se limpia "
                "workflow_runs doc=%s",
                document_id,
            )
            return None
        try:
            borradas = self._purger.purge(
                document_id=document_id,
                source_sha256=source_sha256,
            )
        except Exception:  # noqa: BLE001 — best-effort explícito
            logger.exception(
                "[sv4-colas][purge] fallo limpiando workflow_runs doc=%s "
                "(el hard-delete local ya se aplicó)",
                document_id,
            )
            return None
        return {
            "action": "purged",
            "detail": f"workflow_runs eliminados={borradas}",
            "previous_state": None,
            "new_state": "purged",
            "workflow_id": None,
        }
