# application/services/obra_enrichment_service.py
from __future__ import annotations

import logging

from application.services.obra_code_normalizer import normalize_obra_code
from domain.ports.obra_enrichment_port import ObraEnrichmentClient
from domain.ports.obra_merge_repository_port import ObraMergeRepository

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[obra-enrichment]"


class ObraEnrichmentService:
    """Orquesta el enriquecimiento del merge con datos de obra on-prem.

    Flujo:
      1. Lee obra_codigo del registro merge recién persistido.
      2. Normaliza a 4 dígitos con 0 inicial.
      3. Si el código no valida, omite la llamada HTTP.
      4. Pregunta al puerto ObraEnrichmentClient (Sigrid).
      5. Si hay resultado, sobrescribe obra_nombre y obra_direccion
         en albaran_documents_merge.

    RED DE OBRA (ago 2026, F-002): hasta ahora, un código que Sigrid no
    reconocía solo dejaba un WARNING y el merge se quedaba con la obra
    INVENTADA por la IA (caso de referencia: 0937). Con ``enabled_red``
    activo, ese documento pierde la obra y va a revisión (R5/R6), y la
    marca se retira sola cuando un reproceso posterior la valida (R7).

    Best-effort: ningún fallo aquí debe romper el pipeline. Todas las
    excepciones se capturan y se loguean.
    """

    def __init__(
        self,
        *,
        client: ObraEnrichmentClient,
        repository: ObraMergeRepository,
        enabled: bool = True,
        enabled_red: bool = True,
    ) -> None:
        self._client = client
        self._repository = repository
        self._enabled = enabled
        self._enabled_red = bool(enabled_red)
        logger.info(
            "%s ObraEnrichmentService INSTANCIADO (enabled=%s red=%s "
            "client=%s repo=%s)",
            _LOG_PREFIX,
            enabled,
            self._enabled_red,
            type(client).__name__,
            type(repository).__name__,
        )

    def enrich_merge_document(self, *, merge_document_id: str) -> bool:
        logger.info(
            "%s enrich_merge_document() INVOCADO document_id=%s",
            _LOG_PREFIX,
            merge_document_id,
        )

        if not self._enabled:
            logger.info(
                "%s DESHABILITADO por configuración. document_id=%s",
                _LOG_PREFIX,
                merge_document_id,
            )
            return False

        raw_codigo = self._repository.get_merge_obra_codigo(
            document_id=merge_document_id,
        )
        logger.info(
            "%s Paso 1 — obra_codigo leído de merge: raw=%r",
            _LOG_PREFIX,
            raw_codigo,
        )

        normalized = normalize_obra_code(raw_codigo)
        logger.info(
            "%s Paso 2 — normalización: raw=%r -> normalized=%r",
            _LOG_PREFIX,
            raw_codigo,
            normalized,
        )
        if normalized is None:
            logger.warning(
                "%s Código inválido o vacío; se OMITE llamada a Sigrid. raw=%r",
                _LOG_PREFIX,
                raw_codigo,
            )
            # R6: un código NO nulo que no normaliza ("1234", "12345") es
            # una lectura errónea, no una ausencia de obra. Se descarta y
            # va a revisión. Que el albarán NO traiga obra (None / vacío)
            # no es un error de identificación: eso lo resuelve el
            # HeaderResolver o, en su defecto, el revisor.
            if (raw_codigo or "").strip():
                self._descartar_obra_safely(
                    merge_document_id=merge_document_id,
                    codigo_leido=raw_codigo,
                    motivo=f"obra_codigo_invalido:{raw_codigo}",
                )
            return False

        logger.info(
            "%s Paso 3 — LLAMANDO a Sigrid (codigo=%s)...",
            _LOG_PREFIX,
            normalized,
        )
        try:
            result = self._client.fetch_obra_by_codigo(
                codigo_obra_normalizado=normalized,
            )
        except Exception as exc:
            logger.exception(
                "%s ERROR llamando a Sigrid. codigo=%s exc=%r",
                _LOG_PREFIX,
                normalized,
                exc,
            )
            return False
        logger.info(
            "%s Paso 3 — respuesta de Sigrid: result=%r",
            _LOG_PREFIX,
            result,
        )

        if result is None:
            logger.warning(
                "%s Sigrid devolvió 0 filas útiles para codigo=%s",
                _LOG_PREFIX,
                normalized,
            )
            # R5: la obra NO existe en Sigrid. Jamás debe quedar
            # persistida una obra inventada.
            self._descartar_obra_safely(
                merge_document_id=merge_document_id,
                codigo_leido=raw_codigo,
                motivo=f"obra_inexistente:{normalized}",
            )
            return False

        nombre = (result.nombre_obra or "").strip() or None
        direccion = result.direccion_completa
        logger.info(
            "%s Paso 4 — valores compuestos: nombre=%r direccion=%r",
            _LOG_PREFIX,
            nombre,
            direccion,
        )

        try:
            self._repository.update_merge_obra_fields(
                document_id=merge_document_id,
                obra_nombre=nombre,
                obra_direccion=direccion,
            )
        except Exception as exc:
            logger.exception(
                "%s ERROR actualizando merge. document_id=%s exc=%r",
                _LOG_PREFIX,
                merge_document_id,
                exc,
            )
            return False

        # R7: la obra existe -> se retira cualquier aviso de un intento
        # anterior (p. ej. el revisor la corrigió y pulsó "volver a
        # buscar"). Idempotente: si no había aviso, no pasa nada.
        self._retirar_revision_safely(merge_document_id=merge_document_id)

        logger.info(
            "%s OK — merge actualizado. document_id=%s codigo=%s nombre=%r direccion=%r",
            _LOG_PREFIX,
            merge_document_id,
            normalized,
            nombre,
            direccion,
        )
        return True

    # ----------------------------------------------------------------- #
    # Red de obra (R5–R7). Best-effort: si la marca falla, el documento
    # queda como estaba y la persistencia continúa (R16).
    # ----------------------------------------------------------------- #
    def _descartar_obra_safely(
        self,
        *,
        merge_document_id: str,
        codigo_leido: str | None,
        motivo: str,
    ) -> None:
        if not self._enabled_red:
            logger.info(
                "%s RED DE OBRA desactivada (RED_OBRA_ENABLED=false): no "
                "se descarta %r. document_id=%s",
                _LOG_PREFIX, codigo_leido, merge_document_id,
            )
            return
        try:
            self._repository.descartar_obra_no_valida(
                document_id=merge_document_id,
                codigo_leido=codigo_leido,
                motivo=motivo,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo descartar la obra no válida. document_id=%s "
                "motivo=%s",
                _LOG_PREFIX, merge_document_id, motivo,
            )

    def _retirar_revision_safely(self, *, merge_document_id: str) -> None:
        if not self._enabled_red:
            return
        try:
            self._repository.retirar_revision_obra(
                document_id=merge_document_id,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo retirar el aviso de obra. document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )
