# ruesma_comun/valoracion.py
"""¿Está «valorado» un albarán? (F-053, glosario; R37, R10 y R38).

Una sola definición para sv4 (no deja aprobar lo no valorado) y sv9 (no da
de alta lo no valorado), decidida por el humano el 2026-10-01:

- valoración de sv6 en ``ok``, o
- valoración manual completa del administrativo en sv4: cabecera ``manual``
  (la crea sv4) o ``no_contract`` (la deja sv6 vacía) con **alguna** línea
  con importe distinto de cero y **ninguna** con importe nulo.

``partial``, ``failed``, sin valoración o cualquier otro estado: no.

Función pura, sin E/S.
"""
from __future__ import annotations

from collections.abc import Iterable

#: Cabeceras de valoración que el administrativo completa a mano en sv4.
ESTADOS_VALORACION_MANUAL = frozenset({"manual", "no_contract"})

#: Por debajo de esto un importe cuenta como cero.
_EPSILON = 1e-9


def esta_valorado(status: str | None, importes: Iterable[float | None]) -> bool:
    """``True`` si la valoración ``status`` con esos importes de línea
    (``importe_calculado`` de cada línea valorada) cuenta como valorada."""
    if status == "ok":
        return True
    if status not in ESTADOS_VALORACION_MANUAL:
        return False
    lista = list(importes)
    if not lista or any(imp is None for imp in lista):
        return False
    return any(abs(float(imp)) > _EPSILON for imp in lista)
