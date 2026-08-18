# ruesma_comun/importes.py
"""Fórmula canónica del importe de una línea de albarán.

Regla de negocio de Construcciones Ruesma, única y sin excepciones
(`docs/ARCHITECTURE.md`, regla 13):

    importe = cantidad × precio_unitario × (1 − descuento/100)

POR QUÉ VIVE AQUÍ Y NO EN UN SERVICIO
-------------------------------------
La escriben **dos** servicios: sv6 al valorar (`ImporteCalculator`) y
sv4 cuando el revisor guarda (`review_repository._importe_de_linea`).
`CLAUDE.md`, LÍMITE DE SERVICIO: «la lógica compartida va a
`services/albaranes-comun`, **nunca copiada entre servicios**».

No es una precaución teórica. Con una copia en cada servicio, el
2026-08-18 sv6 valoró el albarán Feymaco 2.137.569 en sus 139,66 €
correctos y el primer guardado desde el front lo dejó en 232,76 €,
porque la copia de sv4 se dejaba el factor del descuento. Y una vez
unificado sv4 por dentro, las dos copias supervivientes **ya divergían**
en tres puntos observables: qué hacían con un descuento ilegible (una
devolvía `None`, la otra reventaba con `ValueError`), qué dejaban escrito
y dónde estaba el borde del cero.

QUÉ **NO** VIVE AQUÍ
--------------------
La **política** de cada servicio. Este módulo decide aritmética y
rangos; no decide si manda el importe declarado o el calculado, ni qué
motivos de revisión se emiten, ni qué se persiste. Eso es de sv6
(`ImporteCalculator`) y de sv4, y cada uno lo mantiene encima de esta
base.
"""
from __future__ import annotations

from typing import Literal, Tuple

#: Estados en que puede quedar un descuento leído de un albarán.
#:
#: - ``ausente``:   no vino ninguno (``None``).
#: - ``cero``:      vino, y es 0 % — sin descuento, pero CONSTA que vino.
#: - ``aplicable``: dentro de (0, 100]; se aplica.
#: - ``invalido``:  fuera de rango o no interpretable como número.
EstadoDescuento = Literal["ausente", "cero", "aplicable", "invalido"]


def clasificar_descuento(
    descuento_pct: object,
) -> Tuple[EstadoDescuento, float | None]:
    """Clasifica un descuento porcentual leído de un albarán.

    Devuelve el estado y el valor normalizado a ``float`` cuando se pudo
    convertir (para ``invalido`` fuera de rango se devuelve el número
    leído, que es lo que hace falta para dejar traza de qué llegó).

    Nunca lanza: un dato mal leído de un PDF no puede tumbar ni una
    valoración ni el guardado de un revisor.

    Distinguir ``cero`` de ``ausente`` importa aunque el importe salga
    igual: es la diferencia entre «el albarán dice 0 %» y «el albarán no
    dice nada», y cada servicio decide qué persiste en cada caso.
    """
    if descuento_pct is None:
        return "ausente", None
    try:
        valor = float(descuento_pct)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "invalido", None
    if valor != valor:  # NaN: float('nan') != float('nan')
        return "invalido", None
    if valor == 0.0:
        return "cero", 0.0
    if 0.0 < valor <= 100.0:
        return "aplicable", valor
    return "invalido", valor


def factor_descuento(descuento_pct: object) -> float:
    """Factor multiplicador del descuento: ``1 − dto/100``.

    Un descuento ausente, cero o inválido no descuenta (factor 1,0): un
    porcentaje absurdo se ignora en vez de fabricar un importe negativo.
    """
    estado, valor = clasificar_descuento(descuento_pct)
    if estado != "aplicable" or valor is None:
        return 1.0
    return 1.0 - valor / 100.0


def importe_de_linea(
    *,
    cantidad: object,
    precio_unitario: object,
    descuento_pct: object = None,
) -> float | None:
    """Importe de una línea, redondeado a 2 decimales (es dinero).

    Devuelve ``None`` si falta la cantidad o el precio, o si alguno no
    es interpretable como número — nunca un importe inventado ni una
    excepción.
    """
    if cantidad is None or precio_unitario is None:
        return None
    try:
        base = float(cantidad) * float(precio_unitario)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return round(base * factor_descuento(descuento_pct), 2)
