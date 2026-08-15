# application/services/descuento_cascada.py
"""Descuento efectivo en cascada (F-003, R3).

Los albaranes valorados traen a veces VARIAS columnas de descuento
(DTO1, DTO2...). La IA las TRANSCRIBE todas en ``LineaAlbaran.descuentos``
y no las combina nunca: combinar es aritmética, y la aritmética la hace
código determinista.

Los descuentos encadenados se aplican uno sobre el resto del anterior,
no se suman: dos del 10 % dejan un 19 % efectivo, no un 20 %.

    efectivo = (1 − Π(1 − dᵢ/100)) × 100

Módulo puro: sin BBDD, sin red, sin estado.
"""
from __future__ import annotations

from typing import Any, Iterable, Optional

# Decimales del descuento efectivo. Suficiente para que un porcentaje
# encadenado no arrastre ruido de coma flotante a la BBDD.
_DECIMALES = 4


def _a_float(valor: Any) -> Optional[float]:
    """Convierte a float lo que se pueda; lo demás es 'no hay descuento'."""
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def descuento_efectivo(descuentos: Iterable[Any]) -> float:
    """Porcentaje único equivalente a aplicar ``descuentos`` en cascada.

    Los valores nulos o no numéricos se ignoran (una columna vacía no es
    un descuento del 0 %: no existe). Sin ningún valor útil, el efectivo
    es 0.0 — que es exactamente «no hay descuento».
    """
    resto = 1.0
    for bruto in descuentos or ():
        porcentaje = _a_float(bruto)
        if porcentaje is None:
            continue
        resto *= 1.0 - (porcentaje / 100.0)
    return round((1.0 - resto) * 100.0, _DECIMALES)


def resolver_descuento(
    descuento: Optional[float],
    descuentos: Optional[Iterable[Any]],
) -> Optional[float]:
    """Descuento a persistir en la columna ``descuento``.

    Transcribir manda sobre calcular: si la IA leyó un descuento único
    (aunque sea 0.0), se respeta. La cascada solo se deriva cuando el
    documento trae MÁS DE UNA columna de descuento y no hay descuento
    único transcrito.
    """
    if descuento is not None:
        return descuento

    valores = [
        porcentaje
        for porcentaje in (_a_float(v) for v in (descuentos or ()))
        if porcentaje is not None
    ]
    if len(valores) < 2:
        # Una sola columna: el efectivo es ese mismo valor, sin cascada
        # que derivar. Ninguna columna: no se inventa un 0 %.
        return valores[0] if valores else None

    return descuento_efectivo(valores)
