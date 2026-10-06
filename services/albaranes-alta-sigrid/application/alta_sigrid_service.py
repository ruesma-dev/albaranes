# application/alta_sigrid_service.py
"""``AltaSigridService.procesar``: el flujo de sv9 (F-053, design §5).

Única clase que conoce el modo (``simulacion`` | ``real``). Pasos:

1. ``reclamar`` (R5–R8) en una transacción con el merge ``FOR UPDATE``. Una
   excepción AQUÍ se propaga: el worker deja el mensaje en la cola (reintento).
2. Según la decisión: ``ignorar`` / ``a_incierto`` (ya resueltos al reclamar),
   ``verificar_anulacion`` (R28), ``solo_adjunto`` (R23) o ``procesar``.
3. ``procesar``: todo dentro de ``try/finally`` (R9). Tras dejar el alta en
   ``en_curso``, ninguna salida —tampoco una excepción— la deja ahí: queda
   ``incierto`` si la grabación estaba en vuelo y ``error`` si no. Las
   excepciones de esta fase NO se propagan (el mensaje se confirma).
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from domain.models.alta_models import (
    AccionAlta,
    AltaActual,
    Decision,
    EstadoAlta,
    ModoAlta,
    Motivo,
    ResultadoAlta,
)
from domain.ports.alta_repository import AltaRepository
from domain.ports.pdf_port import PdfAlbaranPort
from domain.ports.sigrid_alta_port import SigridAltaPort
from domain.services.validador_alta import ConfigAlta

logger = logging.getLogger(__name__)

_LOG = "[sv9-alta]"


def _ahora_utc() -> datetime:
    return datetime.now(UTC)


def hoy_en_madrid(instante: datetime) -> date:
    """Fecha de hoy en Europe/Madrid (R39). Sin base de zonas horarias en el
    sistema, la hora local del contenedor (``TZ=Europe/Madrid`` en el Dockerfile)."""
    try:
        from zoneinfo import ZoneInfo

        return instante.astimezone(ZoneInfo("Europe/Madrid")).date()
    except Exception:  # noqa: BLE001 — sin tzdata: hora local del sistema
        return instante.astimezone().date()


@dataclass(frozen=True)
class ResultadoProceso:
    """Qué pasó con un mensaje (para el log del worker y los tests)."""

    decision: Decision
    estado: EstadoAlta | None = None
    motivo: str = ""


@dataclass
class _Paso:
    """Estado de un ``procesar`` en marcha, para el ``finally`` de R9."""

    en_vuelo: bool = False
    cerrado: bool = False
    estado: EstadoAlta | None = None
    peticion: dict | None = None


class AltaSigridService:
    def __init__(
        self,
        *,
        repo: AltaRepository,
        sigrid: SigridAltaPort,
        pdf: PdfAlbaranPort,
        config: ConfigAlta,
        modo: ModoAlta,
        desde: datetime | None,
        espera: timedelta,
        tolerancia_eur: float,
        avisos_bloqueantes: frozenset[str],
        reloj: Callable[[], datetime] = _ahora_utc,
    ) -> None:
        self._repo = repo
        self._sigrid = sigrid
        self._pdf = pdf
        self._config = config
        self._modo = ModoAlta(modo)
        self._desde = desde
        self._espera = espera
        self._tolerancia = tolerancia_eur
        self._bloqueantes = frozenset(avisos_bloqueantes)
        self._reloj = reloj

    @property
    def modo(self) -> ModoAlta:
        return self._modo

    # ------------------------------------------------------------------ #
    # Entrada
    # ------------------------------------------------------------------ #
    def procesar(
        self, document_id: str, accion: AccionAlta | str = AccionAlta.ALTA,
    ) -> ResultadoProceso:
        accion = AccionAlta(accion)
        if self._desde is None:
            logger.info("%s document_id=%s ignorado: ALTA_SIGRID_DESDE_UTC vacía",
                        _LOG, document_id)
            return ResultadoProceso(Decision.IGNORAR, None, "DESDE vacía")

        reclamacion = self._repo.reclamar(
            document_id, accion=accion, ahora=self._reloj(), desde=self._desde,
            espera=self._espera, modo=self._modo.value,
        )
        decision = reclamacion.decision
        logger.info(
            "%s document_id=%s accion=%s decision=%s %s",
            _LOG, document_id, accion.value, decision.value, reclamacion.motivo,
        )
        if decision is Decision.IGNORAR:
            return ResultadoProceso(decision, None, reclamacion.motivo)
        if decision is Decision.A_INCIERTO:
            return ResultadoProceso(decision, EstadoAlta.INCIERTO, reclamacion.motivo)
        if decision is Decision.VERIFICAR_ANULACION:
            return self._verificar_anulacion(document_id, reclamacion.alta)
        if decision is Decision.SOLO_ADJUNTO:
            return self._solo_adjunto(document_id, reclamacion.alta)
        return self._procesar_alta(document_id, reclamacion.alta)

    # ------------------------------------------------------------------ #
    # procesar (R9)
    # ------------------------------------------------------------------ #
    def _procesar_alta(self, document_id: str, previa: AltaActual | None) -> ResultadoProceso:
        paso = _Paso()
        try:
            self._flujo(document_id, previa, paso)
        except Exception as exc:
            logger.exception("%s document_id=%s fallo inesperado", _LOG, document_id)
            self._cerrar_por_excepcion(document_id, paso, exc)
        finally:
            if not paso.cerrado:
                self._cerrar_por_excepcion(document_id, paso, None)
        return ResultadoProceso(Decision.PROCESAR, paso.estado)

    def _cerrar_por_excepcion(
        self, document_id: str, paso: _Paso, exc: Exception | None,
    ) -> None:
        if paso.cerrado:
            return
        estado = EstadoAlta.INCIERTO if paso.en_vuelo else EstadoAlta.ERROR
        detalle = type(exc).__name__ if exc is not None else "salida sin estado final"
        paso.estado = estado
        try:
            self._guardar(document_id, paso, ResultadoAlta(
                estado=estado, modo=self._modo.value,
                motivos=(Motivo("excepcion", detalle),), peticion=paso.peticion,
            ))
        except Exception:
            logger.exception(
                "%s document_id=%s no se pudo guardar %s: queda en_curso (R8 lo pasará "
                "a incierto tras la Espera)", _LOG, document_id, estado.value,
            )

    def _guardar(self, document_id: str, paso: _Paso, resultado: ResultadoAlta) -> None:
        self._repo.guardar(document_id, resultado, ahora=self._reloj())
        if resultado.estado is not EstadoAlta.EN_CURSO:
            paso.cerrado = True
            paso.estado = resultado.estado
            logger.info(
                "%s document_id=%s estado=%s modo=%s cod=%s motivos=%s",
                _LOG, document_id, resultado.estado.value, resultado.modo,
                resultado.sigrid_cod, [m.codigo for m in resultado.motivos],
            )

    def _flujo(self, document_id: str, previa: AltaActual | None, paso: _Paso) -> None:
        self._repo.leer_datos(document_id)
        raise NotImplementedError("flujo del alta: T9-T11")

    # ------------------------------------------------------------------ #
    # Otras decisiones
    # ------------------------------------------------------------------ #
    def _verificar_anulacion(self, document_id: str, alta: AltaActual | None) -> ResultadoProceso:
        raise NotImplementedError("R28: T12")

    def _solo_adjunto(self, document_id: str, alta: AltaActual | None) -> ResultadoProceso:
        raise NotImplementedError("R23: T11")
