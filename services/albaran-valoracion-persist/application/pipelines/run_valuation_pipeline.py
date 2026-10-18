# application/pipelines/run_valuation_pipeline.py
from __future__ import annotations

import json
import logging
from typing import Any

from application.services.conciliacion_orchestrator import (
    aplicar_conciliacion_ia4,
)
from application.services.fila_completa import completar_registros
from application.services.normalizador_partidas import (
    NormalizacionSobre,
    NormalizadorPartidas,
)
from dataclasses import dataclass

from application.services.valoracion_directa import ValoracionDirectaBuilder
from application.services.valuation_builder import ValuationBuilder
from domain.models.valuation_records import ValuationHeaderRecord
from domain.ports.valuation_ia_client import ValuationIaClient
from domain.ports.valuation_repository import (
    ExistingValuationSummary,
    PersistedValuation,
    ValuationRepository,
)

from domain.ports.valuation_ia_client import ValuationPeticionInvalida

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunValuationRequest:
    document_id: str
    codigo_contrato: str | None = None
    force: bool = False
    line_already_valued: bool = False


@dataclass(frozen=True)
class RunValuationResult:
    valuation_id: str
    document_id: str
    status: str
    total_valorado: float
    total_lines: int
    review_required: bool
    review_reasons: list[str]
    duplicate: bool


class RunValuationPipeline:
    """Pipeline principal del servicio 6.

    Pasos:
      1. Si existe valoración y no se fuerza: devolver la existente.
      2. Llamar al servicio 5 via HTTP.
      2 bis. (F-076) Normalizar la partida leída de cada línea contra las
         de la obra (``NormalizadorPartidas``); desde aquí se valora con
         ese sobre. Nunca falla: sin lista, se valora como siempre.
      3. Si status == no_contract: (F-075) si alguna línea trae importe
         leído, persistir la valoración directa (``ValoracionDirectaBuilder``,
         sin IA ni contrato); si no, cabecera vacía con
         status='no_contract'. Y terminar.
      4. Pasarle el envelope al ValuationBuilder.
      4 bis. (F-076) Anotar la normalización en los registros.
      5. Persistir en las 3 tablas (replace atómico).
    """

    def __init__(
        self,
        *,
        ia_client: ValuationIaClient,
        repository: ValuationRepository,
        builder: ValuationBuilder,
        conciliacion_client: Any = None,
        normalizador: NormalizadorPartidas | None = None,
        valoracion_directa: ValoracionDirectaBuilder | None = None,
    ) -> None:
        self._ia_client = ia_client
        self._repository = repository
        self._builder = builder
        self._conciliacion_client = conciliacion_client
        # (F-076) None = sin normalizar (como antes de F-076).
        self._normalizador = normalizador
        # (F-075) Sin contrato y con importes leídos: manda el albarán.
        self._valoracion_directa = valoracion_directa or ValoracionDirectaBuilder()

    def _normalizar_partidas(
        self, document_id: str, envelope: Any,
    ) -> NormalizacionSobre:
        """(F-076 R7, R11) El sobre con el que se valora; nunca lanza.

        La obra se lee del merge solo si el normalizador la necesita
        (encendido y con alguna lectura). Cualquier excepción (BBDD,
        caché) ⇒ WARNING y el sobre original con
        ``partidas_obra_no_disponibles``.
        """
        if self._normalizador is None:
            return NormalizacionSobre(envelope=envelope)
        try:
            obra = (
                self._repository.obra_del_documento(document_id=document_id)
                if self._normalizador.necesita_obra(envelope)
                else None
            )
            return self._normalizador.normalizar(envelope=envelope, obra=obra)
        except Exception as exc:  # noqa: BLE001 - R11: nunca falla por la lista
            logger.warning(
                "[run-valuation] document_id=%s no se pudo normalizar la "
                "partida (%r); se valora con el sobre de sv5.",
                document_id, exc,
            )
            return NormalizadorPartidas.degradada(envelope)

    def run(self, request: RunValuationRequest) -> RunValuationResult:
        existing: ExistingValuationSummary | None = (
            self._repository.get_by_document_id(document_id=request.document_id)
        )

        if existing is not None and not request.force:
            logger.info(
                "[run-valuation] existe valoración previa id=%s status=%s; "
                "se devuelve sin re-ejecutar.",
                existing.valuation_id, existing.status,
            )
            return RunValuationResult(
                valuation_id=existing.valuation_id,
                document_id=existing.document_id,
                status=existing.status,
                total_valorado=existing.total_valorado,
                total_lines=existing.total_lines,
                review_required=existing.review_required,
                review_reasons=[],
                duplicate=True,
            )

        # Llamada al servicio 5.
        logger.info(
            "[run-valuation] llamando a IA document_id=%s contrato=%s force=%s",
            request.document_id,
            request.codigo_contrato,
            request.force,
        )
        try:
            envelope = self._ia_client.value(
                document_id=request.document_id,
                codigo_contrato=request.codigo_contrato,
            )
        except ValuationPeticionInvalida as exc:
            # (jul 2026) Peticion invalida (4xx: p. ej. 0 lineas en el
            # merge): se CIERRA la valoracion como 'failed' con el
            # motivo y se termina con normalidad para que el consumidor
            # complete el mensaje. Antes esto reventaba el handler y el
            # mensaje quedaba envenenado en la cola (reintento eterno
            # cada 10 min y "Valorando..." infinito en el front).
            motivo = str(exc)[:300]
            logger.warning(
                "[run-valuation] document_id=%s peticion INVALIDA hacia "
                "valuation-api; se cierra como failed. Motivo: %s",
                request.document_id, motivo,
            )
            failed_header = ValuationHeaderRecord(
                document_id=request.document_id,
                contrato_codigo=request.codigo_contrato,
                status="failed",
                provider_ia=None,
                model_name=None,
                prompt_key=None,
                total_valorado=0.0,
                total_lines=0,
                lines_matched_exact=0,
                lines_matched_semantic=0,
                lines_matched_price_only=0,
                lines_unmatched=0,
                review_required=True,
                review_reasons=[f"peticion_invalida:{motivo}"],
                raw_ia_envelope_json=None,
            )
            persisted = self._repository.replace_valuation(
                header=failed_header, lines=[]
            )
            return RunValuationResult(
                valuation_id=persisted.valuation_id,
                document_id=persisted.document_id,
                status=persisted.status,
                total_valorado=persisted.total_valorado,
                total_lines=persisted.total_lines,
                review_required=persisted.review_required,
                review_reasons=failed_header.review_reasons,
                duplicate=False,
            )

        # (F-076 R7, R14) Normalizar la partida ANTES de la rama
        # no_contract, de IA4 y de las reglas; desde aquí se valora (y se
        # persiste) el sobre normalizado.
        normalizacion = self._normalizar_partidas(request.document_id, envelope)
        envelope = normalizacion.envelope

        # (F-075 R5) Sin contrato y con importes leídos: valoración directa.
        if self._valoracion_directa.aplica(envelope):
            return self._persistir_directa(request.document_id, envelope, normalizacion)

        # Caso "no contrato seleccionado".
        if envelope.status == "no_contract":
            logger.info(
                "[run-valuation] document_id=%s sin contrato; "
                "persistiendo cabecera vacía.",
                request.document_id,
            )
            empty_header = ValuationHeaderRecord(
                document_id=request.document_id,
                contrato_codigo=None,
                status="no_contract",
                provider_ia=None,
                model_name=None,
                prompt_key=None,
                total_valorado=0.0,
                total_lines=0,
                lines_matched_exact=0,
                lines_matched_semantic=0,
                lines_matched_price_only=0,
                lines_unmatched=0,
                review_required=True,
                review_reasons=["no_contract_selected"],
                raw_ia_envelope_json=envelope.model_dump_json(),
            )
            persisted = self._repository.replace_valuation(
                header=empty_header, lines=[]
            )
            return RunValuationResult(
                valuation_id=persisted.valuation_id,
                document_id=persisted.document_id,
                status=persisted.status,
                total_valorado=persisted.total_valorado,
                total_lines=persisted.total_lines,
                review_required=persisted.review_required,
                review_reasons=empty_header.review_reasons,
                duplicate=False,
            )

        # IA4 (condicional): conciliar semanticamente las lineas que el
        # determinista no casara (o casadas sin precio), modificando el
        # envelope ANTES del build. build() recalcula el importe
        # determinista (unitario * (1 - dto/100) * cantidad). Best-effort.
        if self._conciliacion_client is not None:
            try:
                aplicar_conciliacion_ia4(
                    envelope=envelope, client=self._conciliacion_client
                )
            except Exception as exc:  # noqa: BLE001 - best-effort
                logger.warning("[run-valuation] IA4 fallo: %s", exc)

        # Caso normal: aplicar reglas deterministas y persistir.
        header, lines = self._builder.build(
            envelope=envelope,
            existing_document_already_valued=request.line_already_valued,
        )
        # (F-078 R4) Cada fila se guarda con lo que la ficha va a enseñar
        # (concepto, unidad, precio, unidad del albarán y Q sin conversión).
        # Toda rama que persista líneas pasa por aquí (lo exige un test).
        lines = completar_registros(lines, envelope)
        # (F-076 R9, R10, R11) Rastro de la normalización: motivos, revisión
        # y la partida leída de vuelta en ``codigo_partida_albaran``. Modifica
        # los registros en su sitio (no reasigna ``lines``).
        NormalizadorPartidas.anotar(header, lines, normalizacion)

        # Adjuntamos el envelope bruto al header para trazabilidad.
        header_with_envelope = ValuationHeaderRecord(
            document_id=header.document_id,
            contrato_codigo=header.contrato_codigo,
            status=header.status,
            provider_ia=header.provider_ia,
            model_name=header.model_name,
            prompt_key=header.prompt_key,
            total_valorado=header.total_valorado,
            total_lines=header.total_lines,
            lines_matched_exact=header.lines_matched_exact,
            lines_matched_semantic=header.lines_matched_semantic,
            lines_matched_price_only=header.lines_matched_price_only,
            lines_unmatched=header.lines_unmatched,
            review_required=header.review_required,
            review_reasons=header.review_reasons,
            raw_ia_envelope_json=envelope.model_dump_json(),
        )

        persisted: PersistedValuation = self._repository.replace_valuation(
            header=header_with_envelope, lines=lines,
        )
        logger.info(
            "[run-valuation] persistida valoración id=%s document_id=%s "
            "lineas=%s total=%.2f review=%s",
            persisted.valuation_id,
            persisted.document_id,
            persisted.total_lines,
            persisted.total_valorado,
            persisted.review_required,
        )
        return RunValuationResult(
            valuation_id=persisted.valuation_id,
            document_id=persisted.document_id,
            status=persisted.status,
            total_valorado=persisted.total_valorado,
            total_lines=persisted.total_lines,
            review_required=persisted.review_required,
            review_reasons=header_with_envelope.review_reasons,
            duplicate=False,
        )

    def _persistir_directa(
        self,
        document_id: str,
        envelope: Any,
        normalizacion: NormalizacionSobre,
    ) -> RunValuationResult:
        """(F-075 R5–R7) Persiste la valoración directa: sin IA, sin contrato y
        sin sintéticas. Pasa por ``completar_registros`` (F-078) y por
        ``NormalizadorPartidas.anotar`` (F-076) como la rama normal."""
        cabecera, directas = self._valoracion_directa.construir(envelope, document_id)
        directas = completar_registros(directas, envelope)
        NormalizadorPartidas.anotar(cabecera, directas, normalizacion)
        cabecera.raw_ia_envelope_json = envelope.model_dump_json()
        logger.info(
            "[run-valuation] document_id=%s sin contrato y con importes "
            "leídos; valoración directa con %s líneas, total=%.2f.",
            document_id, len(directas), cabecera.total_valorado,
        )
        persisted = self._repository.replace_valuation(header=cabecera, lines=directas)
        return RunValuationResult(
            valuation_id=persisted.valuation_id,
            document_id=persisted.document_id,
            status=persisted.status,
            total_valorado=persisted.total_valorado,
            total_lines=persisted.total_lines,
            review_required=persisted.review_required,
            review_reasons=list(cabecera.review_reasons),
            duplicate=False,
        )
