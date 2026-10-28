# ruesma_comun/edicion_manual.py
"""(F-106) Lo editado a mano en una fila de valoración: la regla de recálculo.

Regla del humano (D1, design §4), única para sv4 (PATCH de la ficha) y sv6
(reaplicar lo editado al revalorar):

- Si cambia la cantidad, el precio o el % de descuento, se recalcula el
  importe: ``I = Q × P × (1 − d/100)``, a 2 decimales.
- Si cambia el importe, se recalcula el precio (6 decimales) y el descuento se
  queda: ``P = I / (Q × (1 − d/100))``.
- Importe y precio a la vez es un error. Con divisor nulo (Q nula o 0, o d del
  100 %) un importe 0 se acepta y conserva P; uno ≠ 0 no se puede despejar.

Dominio puro: sin BBDD ni E/S. Las columnas originales del albarán (las grises)
no pasan por aquí: esto solo calcula lo editable.
"""
from __future__ import annotations

from collections.abc import Iterable

from ruesma_comun.importes import (
    _numero_finito,
    importe_de_linea,
    unitario_despejado,
)

#: Campos de una fila que entran en el importe.
CAMPO_CANTIDAD = "cantidad"
CAMPO_PRECIO = "precio_unitario"
CAMPO_DESCUENTO = "descuento"
CAMPO_IMPORTE = "importe"

#: Cambiar cualquiera de estos (sin el importe) recalcula el importe.
CAMPOS_QUE_MUEVEN_EL_IMPORTE = frozenset({CAMPO_CANTIDAD, CAMPO_PRECIO, CAMPO_DESCUENTO})

MENSAJE_PRECIO_E_IMPORTE = "Cambia el precio o el importe, no los dos"
MENSAJE_NO_DESPEJABLE = (
    "No se puede calcular el precio con cantidad 0 o descuento del 100 %: "
    "cambia la cantidad, el descuento o el precio"
)


class PrecioEImporte(ValueError):
    """(R7) Se pidieron a la vez el precio y el importe: uno de los dos manda."""

    def __init__(self) -> None:
        super().__init__(MENSAJE_PRECIO_E_IMPORTE)


class NoDespejable(ValueError):
    """(R7) Un importe ≠ 0 con cantidad nula o 0, o con descuento del 100 %:
    no hay precio que lo dé."""

    def __init__(self) -> None:
        super().__init__(MENSAJE_NO_DESPEJABLE)


def recalcular_fila(
    *,
    cantidad: object,
    precio: object,
    descuento: object,
    importe: object,
    editados: Iterable[str],
) -> tuple[float | None, float | None]:
    """(F-106 R3, D1) Precio e importe resultantes de una edición.

    ``cantidad``, ``precio``, ``descuento`` e ``importe`` son los valores ya
    resultantes (lo tecleado sustituye a lo que había); ``editados``, los
    campos que tocó el revisor. Devuelve ``(precio, importe)``:

    - con ``importe`` editado: el importe a 2 decimales y el precio despejado
      con ``importes.unitario_despejado`` (6 decimales); el descuento no se
      toca. Sin divisor, importe 0 ⇒ ``(precio, 0.0)``; si no, :class:`NoDespejable`;
    - con cantidad, precio o descuento: ``importe_de_linea`` (``None`` si falta
      Q o P: nunca un importe inventado);
    - con nada de eso: lo que había, sin tocar.

    :class:`PrecioEImporte` si se editaron a la vez precio e importe.
    """
    campos = set(editados)
    if CAMPO_IMPORTE in campos:
        if CAMPO_PRECIO in campos:
            raise PrecioEImporte
        importe_num = _numero_finito(importe)
        if importe_num is None:
            raise NoDespejable
        importe_2 = round(importe_num, 2)
        precio_despejado = unitario_despejado(
            importe=importe_2, cantidad=cantidad, descuento_pct=descuento,
        )
        if precio_despejado is not None:
            return precio_despejado, importe_2
        # Sin divisor (Q nula, 0 o ilegible, o d del 100 %).
        if importe_2 == 0.0:
            return _numero_finito(precio), 0.0
        raise NoDespejable
    if CAMPOS_QUE_MUEVEN_EL_IMPORTE & campos:
        return _numero_finito(precio), importe_de_linea(
            cantidad=cantidad, precio_unitario=precio, descuento_pct=descuento,
        )
    return _numero_finito(precio), _numero_finito(importe)
