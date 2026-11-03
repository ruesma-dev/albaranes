# application/services/partida_residuos.py
"""(F-111 parte B) Una línea de residuos sin partida NO va a almacén.

Regla del humano (2026-10-29): «si no tienen partida no van a almacén sino que
busque la partida en el capítulo de gestión de residuos». Tras la
normalización de F-076 y ANTES de la valoración directa, de IA4 y del build,
:meth:`AsignadorPartidaResiduos.asignar` busca partida a cada línea de familia
efectiva ``residuos`` que llega sin partida leída (vacía; la de almacén
``ALM_CODIGO_PARTIDA`` es una lectura y no se toca) entre las hojas del
capítulo de gestión de residuos de su obra
(:func:`ruesma_comun.sigrid.candidatas_residuos`):

- 1 candidata ⇒ esa, sin IA (R21).
- 2 o más ⇒ la IA de sv5 elige por significado en UNA llamada por documento
  (``EligePartidaPort``); solo vale el código de una candidata (R22, R34).
- 0 candidatas ⇒ ``partida_residuos_sin_capitulo`` (R25); la IA no elige o
  elige algo que no es candidata ⇒ ``partida_residuos_sin_candidata``; la IA
  falla ⇒ ``partida_residuos_ia_fallo`` (R26); sin lista de la obra ⇒
  ``partida_residuos_sin_lista`` (R27). Todas a revisión y NUNCA a almacén:
  sus ``merge_line_id`` van en :attr:`AsignacionResiduos.sin_almacen`, que el
  builder pasa al ``PartidaMatcher`` para saltarse la rama de F-051.

La partida asignada entra en una COPIA del sobre (como F-076) y se valora como
si se hubiera leído; :meth:`AsignadorPartidaResiduos.anotar` deja después el
rastro ``partida_residuos:<cod>`` (sin revisión, D4) y devuelve a
``codigo_partida_albaran`` la lectura (vacía): leída ≠ decisión.
``PARTIDA_RESIDUOS_ENABLED=false`` apaga todo (R29). Sin I/O propio.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from application.services.almacen_politica import ACCION_ALMACEN_SIN_PARTIDA
from application.services.valuation_builder import _familia_de
from domain.models.valuation_envelope import ValuationEnvelope
from domain.models.valuation_records import LineValuationRecord, ValuationHeaderRecord
from domain.ports.elige_partida_port import EligePartidaPort
from domain.ports.partidas_obra_port import PartidasObraPort
from ruesma_comun.sigrid import PartidaObra, candidatas_residuos, normalizar_partida

logger = logging.getLogger(__name__)

#: (R23) Rastro sin revisión de una partida asignada: ``partida_residuos:<cod>``.
PREFIJO_PARTIDA_RESIDUOS = "partida_residuos:"
#: (R25) La obra no tiene capítulo de gestión de residuos.
MOTIVO_SIN_CAPITULO = "partida_residuos_sin_capitulo"
#: (R26) La IA no eligió ninguna candidata (o eligió algo que no lo es).
MOTIVO_SIN_CANDIDATA = "partida_residuos_sin_candidata"
#: (R26) La IA falló (sv5 caído, sin proveedor, sin el endpoint).
MOTIVO_IA_FALLO = "partida_residuos_ia_fallo"
#: (R27) No hay lista de partidas de la obra.
MOTIVO_SIN_LISTA = "partida_residuos_sin_lista"
#: Cuántos códigos de candidata se citan en el motivo (R26).
MAX_CANDIDATAS_EN_MOTIVO = 5
#: El motivo de cabecera que el builder pone cuando alguna línea va a revisión.
_MOTIVO_CABECERA_REVISION = "at_least_one_line_requires_review"
_FAMILIA_RESIDUOS = "residuos"


@dataclass(frozen=True)
class ResultadoPartidaResiduos:
    """Qué se decidió para UNA línea."""

    #: Código asignado (de la lista de la obra) o ``None``.
    codigo: str | None
    #: ``partida_residuos:<cod>`` o el motivo de revisión.
    motivo: str
    #: La lectura con la que llegó (vacía), para devolverla al registro.
    leida: str | None = None

    @property
    def revision(self) -> bool:
        return self.codigo is None


@dataclass(frozen=True)
class AsignacionResiduos:
    """Resultado de :meth:`AsignadorPartidaResiduos.asignar`."""

    #: El sobre con el que se valora (copia con las partidas asignadas, o el
    #: original si no cambia nada).
    envelope: ValuationEnvelope
    #: ``merge_line_id`` ⇒ decisión, solo de las líneas buscadas.
    por_linea: dict[int, ResultadoPartidaResiduos] = field(default_factory=dict)
    #: Líneas buscadas SIN partida: el builder no las manda a almacén (D5).
    sin_almacen: frozenset[int] = frozenset()


def _motivo_con_candidatas(motivo: str, candidatas: tuple[PartidaObra, ...]) -> str:
    codigos = [c.codigo for c in candidatas]
    citados = ",".join(codigos[:MAX_CANDIDATAS_EN_MOTIVO])
    resto = len(codigos) - MAX_CANDIDATAS_EN_MOTIVO
    return f"{motivo}:{citados}" + (f"(+{resto})" if resto > 0 else "")


class AsignadorPartidaResiduos:
    """Partida del capítulo de gestión de residuos para las líneas sin partida."""

    def __init__(
        self,
        *,
        partidas: PartidasObraPort | None,
        elector: EligePartidaPort | None,
        alm_codigo_partida: str,
        activo: bool,
    ) -> None:
        self._partidas = partidas
        self._elector = elector
        # ``alm_codigo_partida`` se acepta por simetría con el normalizador de
        # F-076, pero no hace falta: ``ALM`` es una lectura (no vacía) y por
        # eso ya no se busca (R28).
        del alm_codigo_partida
        self._activo = bool(activo)

    # ------------------------------------------------------------------ #
    def _objetivo(self, envelope: ValuationEnvelope) -> list[Any]:
        """(R20) Las líneas de residuos sin partida leída (ni vacía ni ALM)."""
        if not self._activo:
            return []
        clasificacion = getattr(envelope.context, "clasificacion", None)
        return [
            linea
            for linea in envelope.context.lineas_albaran
            if normalizar_partida(linea.codigo_partida_albaran) is None
            and _familia_de(linea.contexto_linea, clasificacion) == _FAMILIA_RESIDUOS
        ]

    def necesita_obra(self, envelope: ValuationEnvelope) -> bool:
        """Encendido y con alguna línea de residuos sin partida (R20, R30)."""
        return bool(self._objetivo(envelope))

    def degradada(self, envelope: ValuationEnvelope) -> AsignacionResiduos:
        """(R27) Algo falló: el sobre tal cual y todas las buscadas sin lista."""
        return self._sin_asignar(envelope, self._objetivo(envelope), MOTIVO_SIN_LISTA)

    @staticmethod
    def _sin_asignar(envelope: ValuationEnvelope, lineas: list[Any], motivo: str) -> AsignacionResiduos:
        por_linea = {
            l.merge_line_id: ResultadoPartidaResiduos(None, motivo, l.codigo_partida_albaran)
            for l in lineas
        }
        return AsignacionResiduos(
            envelope=envelope, por_linea=por_linea, sin_almacen=frozenset(por_linea),
        )

    # ------------------------------------------------------------------ #
    def asignar(self, *, envelope: ValuationEnvelope, obra: str | None) -> AsignacionResiduos:
        """(R20–R27) El sobre con el que se valora y la decisión por línea."""
        lineas = self._objetivo(envelope)
        if not lineas:
            return AsignacionResiduos(envelope=envelope)
        documento = envelope.meta.document_id
        obra_limpia = (obra or "").strip() or None
        lista = (
            self._partidas.lista(obra_limpia)
            if self._partidas is not None and obra_limpia is not None
            else None
        )
        if lista is None:
            logger.warning(
                "[partida-residuos] document_id=%s obra=%s: sin lista de la obra; "
                "%s líneas de residuos a revisión (%s).",
                documento, obra_limpia, len(lineas), MOTIVO_SIN_LISTA,
            )
            return self._sin_asignar(envelope, lineas, MOTIVO_SIN_LISTA)

        candidatas = candidatas_residuos(lista)
        if not candidatas:
            return self._sin_asignar(envelope, lineas, MOTIVO_SIN_CAPITULO)
        if len(candidatas) == 1:  # (R21) esa, sin IA
            elegidas: dict[int, str | None] = {l.merge_line_id: candidatas[0].codigo for l in lineas}
            motivo_no = MOTIVO_SIN_CANDIDATA
        else:
            elegidas, motivo_no = self._elegir_con_ia(documento, lineas, candidatas)

        codigos = {c.codigo for c in candidatas}
        por_linea: dict[int, ResultadoPartidaResiduos] = {}
        nuevas: dict[int, str] = {}  # posición ⇒ código asignado
        posiciones = {id(l): i for i, l in enumerate(envelope.context.lineas_albaran)}
        for linea in lineas:
            codigo = elegidas.get(linea.merge_line_id)
            if codigo in codigos:
                por_linea[linea.merge_line_id] = ResultadoPartidaResiduos(
                    codigo, f"{PREFIJO_PARTIDA_RESIDUOS}{codigo}", linea.codigo_partida_albaran,
                )
                nuevas[posiciones[id(linea)]] = codigo
            else:
                por_linea[linea.merge_line_id] = ResultadoPartidaResiduos(
                    None, _motivo_con_candidatas(motivo_no, candidatas), linea.codigo_partida_albaran,
                )
        logger.info(
            "[partida-residuos] document_id=%s obra=%s candidatas=%s asignadas=%s a_revision=%s",
            documento, lista.obra, len(candidatas), len(nuevas), len(por_linea) - len(nuevas),
        )
        sin_almacen = frozenset(k for k, v in por_linea.items() if v.codigo is None)
        if not nuevas:
            return AsignacionResiduos(envelope=envelope, por_linea=por_linea, sin_almacen=sin_almacen)
        copia = envelope.model_copy(deep=True)
        for posicion, codigo in nuevas.items():
            copia.context.lineas_albaran[posicion].codigo_partida_albaran = codigo
        return AsignacionResiduos(envelope=copia, por_linea=por_linea, sin_almacen=sin_almacen)

    def _elegir_con_ia(
        self, documento: str, lineas: list[Any], candidatas: tuple[PartidaObra, ...],
    ) -> tuple[dict[int, str | None], str]:
        """(R22, R26, R34) Una llamada a sv5 con todas las líneas del documento."""
        if self._elector is None:
            return {}, MOTIVO_IA_FALLO
        try:
            elegidas = self._elector.elegir(
                document_id=documento,
                lineas=[
                    {
                        "line_ref": l.merge_line_id,
                        "descripcion": l.descripcion,
                        "codigo_ler": getattr(l.contexto_linea, "codigo_ler", None),
                    }
                    for l in lineas
                ],
                candidatas=[
                    {
                        "codigo": c.codigo,
                        "descripcion": c.descripcion,
                        "descripcion_agregada": c.descripcion_agregada,
                    }
                    for c in candidatas
                ],
            )
        except Exception as exc:  # noqa: BLE001 - R26: la IA caída no rompe la valoración
            logger.warning(
                "[partida-residuos] document_id=%s la IA no pudo elegir partida (%r); "
                "a revisión (%s).",
                documento, exc, MOTIVO_IA_FALLO,
            )
            return {}, MOTIVO_IA_FALLO
        return dict(elegidas), MOTIVO_SIN_CANDIDATA

    # ------------------------------------------------------------------ #
    @staticmethod
    def anotar(
        header: ValuationHeaderRecord,
        lines: list[LineValuationRecord],
        asignacion: AsignacionResiduos,
    ) -> None:
        """(R23, R25–R27) Rastro de la asignación en los registros ya construidos.

        Solo las líneas ``from_albaran`` cuyo ``merge_line_id`` está en
        ``asignacion.por_linea``; los registros se modifican en su sitio (los
        motivos, en una lista nueva) y sin duplicar si se anota dos veces.

        - Asignada ⇒ ``partida_residuos:<cod>`` sin revisión y
          ``codigo_partida_albaran`` vuelve a la lectura (vacía).
        - Sin asignar ⇒ el motivo en la línea y en la cabecera, más
          ``review_required`` en las dos (como F-076); si la línea llegó como
          ``almacen_sin_partida`` (valoración directa), pasa a ``no_action``.
        """
        for record in lines:
            if record.line_kind != "from_albaran" or record.merge_line_id not in asignacion.por_linea:
                continue
            resultado = asignacion.por_linea[record.merge_line_id]
            record.codigo_partida_albaran = resultado.leida
            _anadir(record, resultado.motivo)
            if resultado.revision:
                # (R25, D5) Nunca almacén: la valoración directa (F-075), que
                # no pasa por el matcher, la marcaría así.
                if record.partida_action == ACCION_ALMACEN_SIN_PARTIDA:
                    record.partida_action = "no_action"
                record.review_required = True
                _anadir(header, resultado.motivo.split(":", 1)[0])
                _anadir(header, _MOTIVO_CABECERA_REVISION)
                header.review_required = True


def _anadir(destino: LineValuationRecord | ValuationHeaderRecord, motivo: str) -> None:
    """Añade ``motivo`` sin duplicar, en una lista NUEVA."""
    if motivo not in destino.review_reasons:
        destino.review_reasons = [*destino.review_reasons, motivo]
