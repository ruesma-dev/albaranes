# application/services/fecha_guard_service.py
"""Guard de año: fecha del albarán frente a la recepción del email.

Un albarán fechado en 2023 que llega en un correo de 2026 casi nunca es
un albarán de 2023: es un año mal leído (o un documento traspapelado que,
en cualquier caso, merece que alguien lo mire). Hasta ahora se persistía
tal cual y nadie se enteraba.

Esta red NO corrige la fecha —no hay forma determinista de saber cuál es
la buena— : marca el documento a revisión con un motivo y una nota, y
decide el humano en sv4. Best-effort completo: cualquier fallo se loguea
y la persistencia continúa (R16).
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone

from domain.ports.header_resolver_ports import HeaderMergeRepository

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[fecha-guard]"

#: Prefijo de la nota de revisión que deja este guard. Igual que el resto
#: de redes: una sola nota viva por prefijo, sustituible al reprocesar.
NOTA_FECHA_PREFIJO = "[AVISO] Fecha"

#: Motivo que se añade a ``review_reasons_json``.
MOTIVO_FECHA = "fecha_albaran_fuera_de_rango"


def _a_fecha(valor: str | None) -> date | None:
    """Parsea la parte de FECHA de un valor ISO, o ``None``.

    ``fecha`` viene ya normalizada a ``YYYY-MM-DD`` por la extracción,
    pero ``email_received_datetime`` llega de Graph como
    ``2026-08-12T09:00:00Z`` (con zona horaria, que
    ``date.fromisoformat`` no admite): nos quedamos con los 10 primeros
    caracteres. La diferencia de horas es irrelevante frente a un margen
    de un año.
    """
    texto = (valor or "").strip()
    if not texto:
        return None
    try:
        return date.fromisoformat(texto[:10])
    except ValueError:
        return None


class FechaGuardService:
    """Marca a revisión los albaranes cuya fecha se aleja de la recepción.

    ``max_dias`` es el margen tolerado en CUALQUIER sentido
    (``FECHA_GUARD_MAX_DIAS``, 365 por defecto).
    """

    def __init__(
        self,
        *,
        repository: HeaderMergeRepository,
        enabled: bool = True,
        max_dias: int = 365,
    ) -> None:
        self._repository = repository
        self._enabled = bool(enabled)
        self._max_dias = int(max_dias)
        logger.info(
            "%s INSTANCIADO (enabled=%s max_dias=%s)",
            _LOG_PREFIX, self._enabled, self._max_dias,
        )

    def check_merge_document(self, *, merge_document_id: str) -> None:
        if not self._enabled:
            logger.info(
                "%s DESHABILITADO. document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )
            return

        try:
            fecha_raw, recibido_raw = (
                self._repository.get_merge_fechas_para_guard(
                    document_id=merge_document_id,
                )
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudieron leer las fechas del merge. document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )
            return

        fecha = _a_fecha(fecha_raw)
        if fecha is None:
            # R15: sin fecha utilizable no hay nada que comparar. La
            # ausencia de fecha ya penaliza la confianza del merge por la
            # vía existente.
            logger.info(
                "%s sin fecha parseable (%r); guard omitido. document_id=%s",
                _LOG_PREFIX, fecha_raw, merge_document_id,
            )
            return

        # R14: sin fecha de email, la referencia es hoy (UTC). El
        # procesamiento ocurre a días de la recepción y el margen de un
        # año absorbe de sobra esa diferencia.
        referencia = _a_fecha(recibido_raw) or datetime.now(timezone.utc).date()
        distancia = abs((fecha - referencia).days)
        if distancia <= self._max_dias:
            logger.info(
                "%s fecha %s a %s dias de la referencia %s: dentro de "
                "margen. document_id=%s",
                _LOG_PREFIX, fecha, distancia, referencia, merge_document_id,
            )
            return

        nota = (
            f"{NOTA_FECHA_PREFIJO} la fecha del albaran ({fecha.isoformat()}) "
            f"dista {distancia} dias de la recepcion del correo "
            f"({referencia.isoformat()}), mas del maximo admitido "
            f"({self._max_dias}). Suele ser un año mal leido: revisala."
        )
        try:
            self._repository.marcar_revision_cabecera(
                document_id=merge_document_id,
                motivo=f"{MOTIVO_FECHA}:{fecha.isoformat()}",
                nota=nota,
                nota_prefijo=NOTA_FECHA_PREFIJO,
            )
            logger.warning(
                "%s document_id=%s fecha=%s referencia=%s distancia=%s "
                "-> REVISION",
                _LOG_PREFIX, merge_document_id, fecha, referencia, distancia,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo marcar la revision de fecha. document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )
