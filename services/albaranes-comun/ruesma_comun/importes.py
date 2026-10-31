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

(F-075) EL IMPORTE DEL ALBARÁN Y EL PIE
---------------------------------------
También vive aquí la suma de los importes leídos de un albarán
(``importe_albaran``), la regla «dos importes difieren» (``difieren``) y el
control del pie impreso (``pie_cuadra``): las usan sv3 (disparo y control
del pie), sv4 (bandeja, ficha y aviso al aprobar) y sv6 (valoración directa
y aviso con contrato). El pie es un **control**, nunca una fuente de
importes.

QUÉ **NO** VIVE AQUÍ
--------------------
La **política** de cada servicio. Este módulo decide aritmética y
rangos; no decide si manda el importe declarado o el calculado, ni qué
motivos de revisión se emiten, ni qué se persiste. Eso es de sv6
(`ImporteCalculator`) y de sv4, y cada uno lo mantiene encima de esta
base.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from enum import StrEnum
from typing import Literal, Tuple

from pydantic import BaseModel, ConfigDict, computed_field

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


# --------------------------------------------------------------------------- #
# F-075 · El importe del albarán manda
# --------------------------------------------------------------------------- #

#: (F-075) Diferencia mínima, en euros, para que dos importes «difieran».
UMBRAL_DIFERENCIA_EUR = 0.01


def _numero_finito(valor: object) -> float | None:
    """``float`` finito o ``None`` (nulo, texto no numérico, NaN o infinito)."""
    if valor is None:
        return None
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numero):
        return None
    return numero


class ImporteAlbaran(BaseModel):
    """(F-075 R1) El importe de un albarán: la suma de sus importes leídos.

    ``total`` es ``None`` si ninguna línea trae importe. Sin IVA: el importe
    leído de una línea es su ``precio_neto`` (importe tras descuento).
    """

    model_config = ConfigDict(frozen=True)

    total: float | None
    lineas: int
    lineas_con_importe: int

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sin_importe(self) -> int:
        """Líneas que no traen importe."""
        return self.lineas - self.lineas_con_importe

    @computed_field  # type: ignore[prop-decorator]
    @property
    def trae_importes(self) -> bool:
        """Al menos una línea trae importe leído."""
        return self.lineas_con_importe > 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def parcial(self) -> bool:
        """Trae importes, pero no en todas las líneas (P3)."""
        return 0 < self.lineas_con_importe < self.lineas


def importe_albaran(importes: Iterable[object]) -> ImporteAlbaran:
    """(F-075 R1) Suma con signo de los importes leídos, sin redondear.

    Un ``None`` o un valor no finito o no numérico cuenta como «línea sin
    importe»: no suma y deja el total parcial (P3). No se completa con nada:
    ni con el contrato ni con ``cantidad × precio``.
    """
    lineas = 0
    con_importe = 0
    total = 0.0
    for valor in importes:
        lineas += 1
        numero = _numero_finito(valor)
        if numero is None:
            continue
        con_importe += 1
        total += numero
    return ImporteAlbaran(
        total=total if con_importe else None,
        lineas=lineas,
        lineas_con_importe=con_importe,
    )


def difieren(
    a: float | None, b: float | None, umbral: float = UMBRAL_DIFERENCIA_EUR,
) -> bool:
    """(F-075) ``True`` si los dos importes se apartan en ``umbral`` o más
    (redondeada la diferencia a céntimos). Con alguno nulo, ``False``: no hay
    nada que comparar. Es la regla del aviso de F-065 R21."""
    if a is None or b is None:
        return False
    return round(abs(float(a) - float(b)), 2) >= umbral


class ComparacionPie(StrEnum):
    """(F-075 R2) Resultado de comparar la suma de las líneas con el pie."""

    CUADRA = "cuadra"
    NO_CUADRA = "no_cuadra"
    NO_COMPARABLE = "no_comparable"


def referencia_pie(
    *, base: object, cuota: object, total: object,
) -> float | None:
    """(F-075 R2) La cifra del pie con la que se compara la suma de las líneas:
    la base imponible o, si falta, ``total − cuota``. Nunca supone un tipo de
    IVA (v2-P4): con solo el total, ``None``."""
    base_num = _numero_finito(base)
    if base_num is not None:
        return base_num
    total_num = _numero_finito(total)
    cuota_num = _numero_finito(cuota)
    if total_num is None or cuota_num is None:
        return None
    return total_num - cuota_num


def pie_cuadra(
    suma: float | None,
    *,
    base: float | None,
    cuota: float | None,
    total: float | None,
    tolerancia: float,
) -> tuple[ComparacionPie, float | None]:
    """(F-075 R2) Compara la suma de las líneas con el pie impreso.

    Devuelve el resultado y la referencia usada (base, o ``total − cuota``).
    ``NO_COMPARABLE`` si la suma es nula o el pie no da referencia. Cuadra si
    la diferencia, redondeada a céntimos, no pasa de ``tolerancia``.
    """
    referencia = referencia_pie(base=base, cuota=cuota, total=total)
    suma_num = _numero_finito(suma)
    if suma_num is None or referencia is None:
        return ComparacionPie.NO_COMPARABLE, referencia
    if round(abs(suma_num - referencia), 2) <= tolerancia:
        return ComparacionPie.CUADRA, referencia
    return ComparacionPie.NO_CUADRA, referencia


def unitario_despejado(
    *, importe: object, cantidad: object, descuento_pct: object = None,
) -> float | None:
    """(F-075 R6) Unitario BRUTO despejado de la fórmula canónica:
    ``importe / (cantidad × (1 − dto/100))``, redondeado a 6 decimales.

    ``None`` si falta el importe o la cantidad, si la cantidad es 0 o si el
    descuento es del 100 % (divisor nulo). Un descuento inválido no
    descuenta (``factor_descuento``)."""
    importe_num = _numero_finito(importe)
    cantidad_num = _numero_finito(cantidad)
    if importe_num is None or cantidad_num is None:
        return None
    divisor = cantidad_num * factor_descuento(descuento_pct)
    if divisor == 0.0:
        return None
    return round(importe_num / divisor, 6)


# --------------------------------------------------------------------------- #
# F-106 · La línea cuadra
# --------------------------------------------------------------------------- #

#: (F-106 R1, D5) Tolerancia, en euros, para que una línea «cuadre»: el importe
#: impreso es ``Q × P × (1 − d)`` redondeado a céntimos (±0,005), a menudo con
#: el descuento redondeado aparte (otro ±0,005), y el precio impreso con k
#: decimales añade un poco más. Única constante de cuadre de línea de sv4, sv6
#: y sv9.
TOLERANCIA_CUADRE_EUR = 0.02


def cuadra_linea(
    cantidad: object,
    precio: object,
    descuento: object,
    importe: object,
    tolerancia: float = TOLERANCIA_CUADRE_EUR,
) -> bool | None:
    """(F-106 R1) ¿``|importe_de_linea(Q, P, d) − I| ≤ tolerancia``?

    ``None`` (no comparable) si Q, P o I faltan o no son números finitos.
    Un descuento inválido no descuenta, como en ``importe_de_linea``. Nunca
    lanza: lo usan sv4 al pintar y al aprobar, sv6 y sv9 sobre datos leídos.
    """
    cantidad_num = _numero_finito(cantidad)
    precio_num = _numero_finito(precio)
    importe_num = _numero_finito(importe)
    if cantidad_num is None or precio_num is None or importe_num is None:
        return None
    calculado = importe_de_linea(
        cantidad=cantidad_num, precio_unitario=precio_num, descuento_pct=descuento,
    )
    if calculado is None or not math.isfinite(calculado):
        return None
    return round(abs(calculado - importe_num), 2) <= tolerancia
