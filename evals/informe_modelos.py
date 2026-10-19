# evals/informe_modelos.py
"""Informes del comparador de modelos (F-083): el resumen versionable y el detalle.

Puro: recibe lo medido y devuelve texto. El resumen versionable
(`progress/comparar_modelos_F-083.md`) NO lleva valores de albarán: solo
caso_id, recuentos, tokens, tiempos y costes (R29). Cada invocación añade su
sección y dos clases de líneas que se leen de vuelta:

- `GASTO: <fecha> · <fase> · <usd>`, el gasto real de la invocación: su suma
  es el gasto acumulado de la feature que vigila `--tope-total-usd` (R18);
- `TOKENS: <fase> · <modelo> · <entrada> · <salida>`, los tokens medios por
  llamada: la estimación de la invocación siguiente los usa en vez de los de
  por defecto (R15).
"""

from __future__ import annotations

import re
from decimal import Decimal

_GASTO = re.compile(r"^GASTO: \S+ · \S+ · (\d+(?:\.\d+)?)[ \t]*$", re.MULTILINE)
_TOKENS = re.compile(r"^TOKENS: (\S+) · (\S+) · (\d+) · (\d+)[ \t]*$", re.MULTILINE)


def gasto_acumulado(texto: str) -> Decimal:
    """La suma de las líneas `GASTO:` del resumen versionable (R18)."""
    return sum((Decimal(usd) for usd in _GASTO.findall(texto)), Decimal(0))


def tokens_medidos(texto: str) -> dict[tuple[str, str], tuple[int, int]]:
    """Tokens medios por (fase, modelo); manda la última sección que los midió."""
    return {
        (fase, modelo): (int(entrada), int(salida))
        for fase, modelo, entrada, salida in _TOKENS.findall(texto)
    }
