# application/services/normalizador_partidas.py
"""(F-076) La partida se normaliza contra las de la obra, ANTES de las reglas.

sv6 recibe en el sobre de sv5 la partida leída de cada línea
(``context.lineas_albaran[i].codigo_partida_albaran``). Antes de IA4, de la
rama ``no_contract`` y del ``ValuationBuilder``, :meth:`NormalizadorPartidas.normalizar`
la resuelve contra la lista de partidas HOJA de la obra con
``ruesma_comun.sigrid.resolver_partida_obra`` (R5): con ``exacta`` o
``normalizada`` las reglas trabajan con el código TAL COMO FIGURA EN LA LISTA
(``CI.04.18`` ⇒ ``CI.4.18``); en cualquier otro caso, con la lectura intacta.
El sobre normalizado es una COPIA (el de sv5 no se muta).

Tras el build, :meth:`NormalizadorPartidas.anotar` deja el rastro en las
líneas: el motivo ``partida_normalizada:<leída>><lista>`` (sin revisión) o
``partida_fuera_de_lista`` / ``partida_ambigua_en_obra`` (a revisión), y
devuelve a ``codigo_partida_albaran`` la leída (regla 6: leída ≠ decisión).

Sin lista (sin configuración de sigrid-api, obra vacía, consulta fallida o
truncada, 0 hojas) se valora EXACTAMENTE como antes, con un WARNING y el
motivo de cabecera ``partidas_obra_no_disponibles`` sin revisión (R11). Con
``PARTIDAS_OBRA_NORMALIZAR_ENABLED=false`` no se consulta ni se cambia nada
(R12). La partida vacía y la de almacén (``ALM_CODIGO_PARTIDA``) no se tocan
(R13, F-051).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from domain.models.valuation_envelope import ValuationEnvelope
from domain.models.valuation_records import LineValuationRecord, ValuationHeaderRecord
from domain.ports.partidas_obra_port import PartidasObraPort
from ruesma_comun.sigrid import (
    ResolucionPartida,
    normalizar_partida,
    resolver_partida_obra,
)

logger = logging.getLogger(__name__)

#: (R11) Motivo de cabecera cuando no hay lista de la obra (sin revisión).
MOTIVO_PARTIDAS_NO_DISPONIBLES = "partidas_obra_no_disponibles"
#: (R9) Prefijo del rastro de una partida normalizada (sin revisión):
#: ``partida_normalizada:<leída>><lista>``.
PREFIJO_PARTIDA_NORMALIZADA = "partida_normalizada:"
#: (R10) Motivos de línea y de cabecera que mandan la línea a revisión.
MOTIVO_PARTIDA_FUERA_DE_LISTA = "partida_fuera_de_lista"
MOTIVO_PARTIDA_AMBIGUA = "partida_ambigua_en_obra"
#: El motivo de cabecera que el builder pone cuando alguna línea va a revisión.
_MOTIVO_CABECERA_REVISION = "at_least_one_line_requires_review"

_MOTIVO_A_REVISION = {
    "fuera_de_lista": MOTIVO_PARTIDA_FUERA_DE_LISTA,
    "ambigua": MOTIVO_PARTIDA_AMBIGUA,
}


@dataclass(frozen=True)
class NormalizacionSobre:
    """Resultado de :meth:`NormalizadorPartidas.normalizar`."""

    #: El sobre con el que se valora (copia con las lecturas ya normalizadas,
    #: o el original si no cambia nada).
    envelope: ValuationEnvelope
    #: ``merge_line_id`` ⇒ resolución, solo de las líneas con lectura.
    por_linea: dict[int, ResolucionPartida] = field(default_factory=dict)
    #: Motivos de cabecera (p. ej. ``partidas_obra_no_disponibles``).
    motivos_cabecera: tuple[str, ...] = ()


class NormalizadorPartidas:
    """Normaliza la partida leída contra la lista de la obra (F-076, design §5.2)."""

    def __init__(
        self,
        *,
        partidas: PartidasObraPort | None,
        alm_codigo_partida: str,
        activo: bool,
    ) -> None:
        self._partidas = partidas
        self._alm = (alm_codigo_partida or "").strip().upper()
        self._activo = bool(activo)

    # ------------------------------------------------------------------ #
    def _es_lectura(self, partida: str | None) -> bool:
        """(R13) Hay algo que resolver: ni vacía ni la de almacén."""
        if normalizar_partida(partida) is None:
            return False
        return not (self._alm and str(partida).strip().upper() == self._alm)

    def necesita_obra(self, envelope: ValuationEnvelope) -> bool:
        """Encendido y con alguna lectura: solo entonces se lee la obra (R7)."""
        return self._activo and any(
            self._es_lectura(ln.codigo_partida_albaran) for ln in envelope.context.lineas_albaran
        )

    @staticmethod
    def degradada(envelope: ValuationEnvelope) -> NormalizacionSobre:
        """(R11) Sin lista: el sobre tal cual y el motivo de cabecera."""
        return NormalizacionSobre(
            envelope=envelope, por_linea={}, motivos_cabecera=(MOTIVO_PARTIDAS_NO_DISPONIBLES,),
        )

    # ------------------------------------------------------------------ #
    def normalizar(self, *, envelope: ValuationEnvelope, obra: str | None) -> NormalizacionSobre:
        """(R7, R11, R12, R13) El sobre con el que se valora y cada resolución."""
        if not self.necesita_obra(envelope):
            return NormalizacionSobre(envelope=envelope)

        documento = envelope.meta.document_id
        obra_limpia = (obra or "").strip() or None
        if self._partidas is None:
            return self._sin_lista(envelope, documento, obra_limpia, "sin configuración de sigrid-api")
        if obra_limpia is None:
            return self._sin_lista(envelope, documento, obra_limpia, "obra vacía en el merge")
        lista = self._partidas.lista(obra_limpia)
        if lista is None:
            return self._sin_lista(
                envelope, documento, obra_limpia,
                "sin lista de la obra (consulta fallida o truncada, o 0 hojas)",
            )

        por_linea: dict[int, ResolucionPartida] = {}
        nuevas: dict[int, str | None] = {}  # posición ⇒ código de la lista
        for posicion, linea in enumerate(envelope.context.lineas_albaran):
            if not self._es_lectura(linea.codigo_partida_albaran):
                continue
            resolucion = resolver_partida_obra(lista, linea.codigo_partida_albaran, self._alm or None)
            por_linea[linea.merge_line_id] = resolucion
            if resolucion.cambia:
                nuevas[posicion] = resolucion.codigo

        logger.info(
            "[partidas-obra] document_id=%s obra=%s lecturas=%s cambiadas=%s motivos=%s",
            documento, lista.obra, len(por_linea), len(nuevas),
            sorted({r.motivo for r in por_linea.values()}),
        )
        if not nuevas:
            return NormalizacionSobre(envelope=envelope, por_linea=por_linea)
        # Copia PROFUNDA: IA4 y el builder trabajan sobre ella sin tocar el
        # sobre de sv5, que nunca se muta.
        copia = envelope.model_copy(deep=True)
        for posicion, codigo in nuevas.items():
            copia.context.lineas_albaran[posicion].codigo_partida_albaran = codigo
        return NormalizacionSobre(envelope=copia, por_linea=por_linea)

    @staticmethod
    def _sin_lista(
        envelope: ValuationEnvelope, documento: str, obra: str | None, causa: str,
    ) -> NormalizacionSobre:
        logger.warning(
            "[partidas-obra] document_id=%s obra=%s: %s; se valora sin normalizar la partida (%s).",
            documento, obra, causa, MOTIVO_PARTIDAS_NO_DISPONIBLES,
        )
        return NormalizadorPartidas.degradada(envelope)

    # ------------------------------------------------------------------ #
    @staticmethod
    def anotar(
        header: ValuationHeaderRecord,
        lines: list[LineValuationRecord],
        n: NormalizacionSobre,
    ) -> None:
        """(R9, R10, R11) Rastro de la normalización en los registros ya construidos.

        Solo las líneas ``from_albaran`` cuyo ``merge_line_id`` está en
        ``n.por_linea``; los registros se modifican en su sitio (los motivos,
        en una lista nueva). Sin duplicar motivos si se anota dos veces. No
        toca importes, casado, partida final ni almacén.

        - ``normalizada`` ⇒ motivo ``partida_normalizada:<leída>><lista>``, sin
          revisión, y ``codigo_partida_albaran`` vuelve a la leída (regla 6).
          Una ``exacta`` que solo difería en espacios exteriores también
          recupera la leída, sin motivo.
        - ``fuera_de_lista`` / ``ambigua`` ⇒ ``partida_fuera_de_lista`` /
          ``partida_ambigua_en_obra`` y ``review_required`` en la línea y en la
          cabecera, que lleva el mismo motivo (y, como el builder, el de «alguna
          línea a revisión»).
        - Los motivos de cabecera de ``n`` (``partidas_obra_no_disponibles``) se
          añaden sin revisión.
        """
        for record in lines:
            if record.line_kind != "from_albaran" or record.merge_line_id not in n.por_linea:
                continue
            resolucion = n.por_linea[record.merge_line_id]
            if resolucion.motivo in ("exacta", "normalizada") and resolucion.cambia:
                record.codigo_partida_albaran = resolucion.leida
            if resolucion.motivo == "normalizada":
                leida = (resolucion.leida or "").strip()
                _anadir(record, f"{PREFIJO_PARTIDA_NORMALIZADA}{leida}>{resolucion.codigo}")
            motivo = _MOTIVO_A_REVISION.get(resolucion.motivo)
            if motivo is not None:
                _anadir(record, motivo)
                record.review_required = True
                _anadir(header, motivo)
                _anadir(header, _MOTIVO_CABECERA_REVISION)
                header.review_required = True
        for motivo in n.motivos_cabecera:
            _anadir(header, motivo)


def _anadir(destino: LineValuationRecord | ValuationHeaderRecord, motivo: str) -> None:
    """Añade ``motivo`` sin duplicar, en una lista NUEVA (la de entrada puede
    estar compartida con otro registro)."""
    if motivo not in destino.review_reasons:
        destino.review_reasons = [*destino.review_reasons, motivo]
