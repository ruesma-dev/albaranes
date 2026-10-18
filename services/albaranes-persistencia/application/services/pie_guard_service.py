# application/services/pie_guard_service.py
"""(F-075 R16–R18) Control del pie: la suma de las líneas frente al pie impreso.

Decisión del humano (2026-10-15): «que lea el pie y sirva para revisar». IA1
lee la base imponible, el tipo de IVA, la cuota y el total tal como están
impresos; este guard compara la suma de los importes leídos de las líneas
(``precio_neto``, sin IVA) con la base o, sin base, con ``total − cuota``
(``ruesma_comun.importes.pie_cuadra``; nunca se supone el tipo de IVA, v2-P4).

- ``no_cuadra`` ⇒ el merge va a revisión con el motivo
  ``pie_no_cuadra:<suma>!=<pie>`` y una sola nota viva con el prefijo
  :data:`NOTA_PIE_PREFIJO` (R16).
- ``cuadra`` o ``no_comparable`` (solo el total, sin pie, o el albarán no trae
  importes) ⇒ se retiran el motivo y la nota si estaban; ``review_required``
  no baja, que puede haber otros motivos vivos (R17).
- El aviso no bloquea: no toca nada más que motivo, nota y revisión (R18). El
  pie es un control, nunca una fuente de importes.

Un albarán de varias páginas (sv1 trocea: 1 página = 1 albarán) trae el pie en
la última, que suma todas: no cuadra con su página y va a revisión. Se acepta
(v2-P5) y la nota lo dice. Mismo patrón que ``FechaGuardService``: se ejecuta
en los tres puntos del pipeline y es best-effort.
"""
from __future__ import annotations

import logging
from typing import Protocol

from ruesma_comun.importes import ComparacionPie, importe_albaran, pie_cuadra

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[pie-guard]"

#: Prefijo (y texto) de la nota de revisión. Una sola nota viva por prefijo.
NOTA_PIE_PREFIJO = "[AVISO] La suma de las líneas no cuadra con el pie del albarán"

#: Motivo que se añade a ``review_reasons_json`` (``pie_no_cuadra:<suma>!=<pie>``).
MOTIVO_PIE = "pie_no_cuadra"

#: Tolerancia por defecto, en euros (``PIE_TOLERANCIA_EUR``).
TOLERANCIA_PIE_EUR = 0.02

Pie = tuple[float | None, float | None, float | None, float | None]


class PieGuardRepository(Protocol):
    def get_merge_pie_para_guard(
        self, *, document_id: str,
    ) -> tuple[Pie, list[float | None]]: ...

    def marcar_revision_cabecera(
        self, *, document_id: str, motivo: str, nota: str, nota_prefijo: str,
    ) -> None: ...

    def retirar_revision_cabecera(
        self, *, document_id: str, motivo_prefijo: str, nota_prefijo: str,
    ) -> None: ...


def _euros(valor: float) -> str:
    entero, _, decimales = f"{valor:,.2f}".partition(".")
    return f"{entero.replace(',', '.')},{decimales} €"


class PieGuardService:
    """Marca a revisión el merge cuya suma de líneas no cuadra con su pie."""

    def __init__(
        self,
        *,
        repository: PieGuardRepository,
        enabled: bool = True,
        tolerancia_eur: float = TOLERANCIA_PIE_EUR,
    ) -> None:
        self._repository = repository
        self._enabled = bool(enabled)
        self._tolerancia = float(tolerancia_eur)
        logger.info(
            "%s INSTANCIADO (enabled=%s tolerancia_eur=%s)",
            _LOG_PREFIX, self._enabled, self._tolerancia,
        )

    def check_merge_document(self, *, merge_document_id: str) -> None:
        if not self._enabled:
            logger.info("%s DESHABILITADO. document_id=%s", _LOG_PREFIX, merge_document_id)
            return
        try:
            (base, _tipo, cuota, total), importes = (
                self._repository.get_merge_pie_para_guard(document_id=merge_document_id)
            )
        except Exception:
            logger.exception(
                "%s no se pudo leer el pie del merge. document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )
            return

        suma = importe_albaran(importes).total
        comparacion, referencia = pie_cuadra(
            suma, base=base, cuota=cuota, total=total, tolerancia=self._tolerancia,
        )
        try:
            if comparacion is ComparacionPie.NO_CUADRA:
                # NO_CUADRA solo sale con suma y referencia (pie_cuadra).
                suma, referencia = float(suma or 0.0), float(referencia or 0.0)
                # Un solo `pie_no_cuadra:*` vivo: si la suma o el pie cambian al
                # reprocesar, se retira el anterior antes de marcar el nuevo
                # (sv4 lee el primero que encuentra).
                self._repository.retirar_revision_cabecera(
                    document_id=merge_document_id,
                    motivo_prefijo=f"{MOTIVO_PIE}:",
                    nota_prefijo=NOTA_PIE_PREFIJO,
                )
                self._repository.marcar_revision_cabecera(
                    document_id=merge_document_id,
                    motivo=f"{MOTIVO_PIE}:{suma:.2f}!={referencia:.2f}",
                    nota=(
                        f"{NOTA_PIE_PREFIJO}: suma de las líneas {_euros(suma)}, "
                        f"pie {_euros(referencia)} (sin IVA). Puede ser un "
                        "albarán de varias páginas: revísalo."
                    ),
                    nota_prefijo=NOTA_PIE_PREFIJO,
                )
                logger.warning(
                    "%s document_id=%s suma=%.2f pie=%.2f -> REVISION",
                    _LOG_PREFIX, merge_document_id, suma, referencia,
                )
                return
            self._repository.retirar_revision_cabecera(
                document_id=merge_document_id,
                motivo_prefijo=f"{MOTIVO_PIE}:",
                nota_prefijo=NOTA_PIE_PREFIJO,
            )
            logger.info(
                "%s document_id=%s %s (suma=%s pie=%s)",
                _LOG_PREFIX, merge_document_id, comparacion.value, suma, referencia,
            )
        except Exception:
            logger.exception(
                "%s no se pudo marcar o retirar la revisión del pie. document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )
