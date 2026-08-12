# infrastructure/colas/intake_cola_adapter.py
"""Adaptador de intake por colas (sustituye al HttpOrchestratorClient/sv7).

Implementa el puerto ``OrchestratorClient``, pero en vez de hacer un POST a
sv7, por cada página de adjunto:

  1. Crea (idempotente, dedup por ``correlation_key``) la fila en
     ``workflow_runs`` vía ``ruesma_comun.workflows``. VESTIGIO de sv7:
     si esa tabla no existe (sv7 disuelto), se continua sin dedup en
     vez de fallar (el correo NO va a Errores por eso).
  2. Si es nueva: sube la página a ``input/{document_id}.pdf`` (Blob) y
     publica ``MensajeExtraccion`` en ``q-extraccion``.
  3. Si ya existía (duplicado): no re-sube ni re-encola (at-least-once).

El ``document_id`` lo genera sv1 y viaja consistente a blob + cola + BBDD.
"""
from __future__ import annotations

import json
import logging
import uuid

from domain.ports.orchestrator_port import (
    OrchestratorAck,
    OrchestratorClient,
    OrchestratorError,
)
from ruesma_comun.blobs.almacen import AlmacenBlobs
from ruesma_comun.blobs.conexion import CONTENEDOR_INPUT
from ruesma_comun.colas.conexion import COLA_EXTRACCION
from ruesma_comun.colas.mensajes import MensajeExtraccion
from ruesma_comun.colas.publicador import PublicadorColas
from ruesma_comun.workflows.repositorio import RepositorioWorkflows

logger = logging.getLogger(__name__)


class IntakeColaClient(OrchestratorClient):
    """OrchestratorClient que entra al pipeline de colas (no a sv7)."""

    def __init__(
        self,
        *,
        repositorio: RepositorioWorkflows,
        almacen: AlmacenBlobs,
        publicador: PublicadorColas,
    ) -> None:
        self._repo = repositorio
        self._almacen = almacen
        self._pub = publicador

    def submit_email_received(
        self,
        *,
        meta: dict,
        file_bytes: bytes,
        filename: str,
        content_type: str,
    ) -> OrchestratorAck:
        message_id = str(meta.get("email_message_id") or "")
        page_sha256 = str(meta.get("page_sha256") or "")
        correlation_key = f"email:{message_id}:{page_sha256}"
        document_id = str(uuid.uuid4())

        # 1) workflow_runs idempotente (dedup). VESTIGIO de sv7: si la
        #    tabla no existe (sv7 disuelto y no se creo), NO tumbamos el
        #    intake ni mandamos el correo a Errores: seguimos como "nuevo".
        #    Si la tabla existe, la dedup sigue funcionando igual que antes.
        creado = True
        workflow_id: str | None = None
        estado_actual: str | None = None
        try:
            res = self._repo.crear_si_no_existe(
                correlation_key=correlation_key,
                payload_json=json.dumps(meta, ensure_ascii=False),
                document_id=document_id,
                attachment_sha256=page_sha256 or None,
            )
            creado = res.creado
            workflow_id = res.workflow_id
            estado_actual = res.estado_actual
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "intake: dedup workflow_runs no disponible (%s); se "
                "continua sin dedup (vestigio de sv7).",
                exc,
            )

        # 2) Duplicado → nada que hacer (ya se subió y encoló).
        if not creado:
            logger.info(
                "intake duplicado correlation_key=%s wf=%s estado=%s",
                correlation_key, workflow_id, estado_actual,
            )
            return OrchestratorAck(
                accepted=True,
                workflow_id=workflow_id,
                duplicate=True,
                message="duplicado",
            )

        # 3) Nuevo → subir página a Blob + publicar q-extraccion.
        safe_name = (filename or f"{document_id}.pdf").encode("ascii", "ignore").decode()
        if not safe_name:
            safe_name = f"{document_id}.pdf"
        try:
            self._almacen.put_bytes(
                CONTENEDOR_INPUT,
                f"{document_id}.pdf",
                file_bytes,
                content_type=content_type or "application/pdf",
                metadata={"filename": safe_name},
            )
            self._pub.publicar(
                COLA_EXTRACCION,
                MensajeExtraccion(
                    document_id=document_id,
                    correlation_key=correlation_key,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            raise OrchestratorError(f"blob/cola: {exc}") from exc

        logger.info(
            "intake encolado document_id=%s wf=%s correlation_key=%s",
            document_id, workflow_id, correlation_key,
        )
        return OrchestratorAck(
            accepted=True,
            workflow_id=workflow_id,
            duplicate=False,
            message="encolado",
        )
