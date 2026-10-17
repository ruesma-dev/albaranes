# ruesma_comun/linea_valorada.py
"""(F-078) La línea valorada guarda lo que se ve.

Principio del humano (2026-10-16): «Lo que está en la tabla es lo que debería
estar guardado en BBDD, ya que lo ha puesto el humano. No es que sv9 tenga que
buscar en muchos sitios, sino que esté bien guardado todo.»

Una fila de ``albaran_line_valuations`` debe llevar en sus columnas lo que la
ficha de sv4 enseña en «Líneas a Sigrid». Esta es la regla que dice QUÉ se
guarda (``fila_a_guardar``), escrita una sola vez: la aplican sv6 al valorar,
sv4 al crear o reapuntar una fila y el script de relleno de lo existente.

Glosario (requirements de F-078):

- **Su línea** (:class:`LineaDeLaFila`): la de contrato si la fila la tiene
  (fila **Contrato**); si no, su derivada (fila **Nueva**).
- **Su blanca**: la línea leída del albarán (``merge_line_id``). Las
  sintéticas, las ``manual`` y las ``reparto`` no tienen blanca propia: se
  llama con ``concepto_blanca=None``.
- **Sin conversión**: ``factor_conversion`` = 1 exactamente (nulo o ≠ 1 = con
  conversión o desconocida).
- **Vacío**: nulo o solo espacios. Los textos se guardan recortados.

Lo que se guarda (es lo que pintaba la ficha hasta F-078 salvo el concepto de
las Nueva con blanca, P1 = (b)):

- concepto: Nueva CON blanca ⇒ el de la fila; si vacío, el del papel (su
  blanca), no el de su derivada. Nueva SIN blanca ⇒ el de su derivada; si
  vacío, el de la fila. Contrato ⇒ el de la fila; si vacío, el de su línea. Si
  aún vacío, el de su blanca (P9).
- unidad: la de su línea; si vacía, la de la fila.
- precio: el de la fila; si vacío, el de su línea.
- sin conversión: ``unidad_albaran`` vacía ⇒ la unidad de arriba;
  ``cantidad_convertida`` nula ⇒ ``cantidad_albaran``. Con conversión no se
  tocan (R3).

Puro: sin BBDD ni red.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

#: Tolerancia con la que un ``factor_conversion`` cuenta como 1.
TOLERANCIA_FACTOR = 1e-9


@dataclass(frozen=True)
class CamposFila:
    """Las columnas de la fila que decide la regla (y las que la acompañan)."""

    descripcion_linea: str | None = None
    unidad_contrato: str | None = None
    unidad_albaran: str | None = None
    precio_unitario_final: float | None = None
    cantidad_albaran: float | None = None
    cantidad_convertida: float | None = None
    factor_conversion: float | None = None


@dataclass(frozen=True)
class LineaDeLaFila:
    """Su línea: la de contrato (``es_contrato``) o su derivada."""

    es_contrato: bool
    descripcion: str | None = None
    unidad: str | None = None
    precio_unitario: float | None = None


def _texto(valor: Any) -> str | None:
    """Recortado; vacío (nulo o solo espacios) = ``None``."""
    if valor is None:
        return None
    limpio = str(valor).strip()
    return limpio or None


def _primero(*valores: str | None) -> str | None:
    for valor in valores:
        if valor is not None:
            return valor
    return None


def sin_conversion(factor: float | None) -> bool:
    """``factor_conversion`` = 1 (con tolerancia ``TOLERANCIA_FACTOR``). Nulo
    no cuenta: la conversión falló o se desconoce (D2)."""
    if factor is None:
        return False
    return abs(float(factor) - 1.0) <= TOLERANCIA_FACTOR


def concepto_a_guardar(
    descripcion_fila: str | None,
    linea: LineaDeLaFila | None,
    concepto_blanca: str | None,
) -> str | None:
    """El concepto de «Lo que se guarda».

    «CON blanca» es tener un concepto del papel que guardar: una blanca sin
    concepto deja la fila como una Nueva sin blanca (su derivada; si no, la
    fila), que es lo que pintaba la ficha de antes."""
    propia = _texto(descripcion_fila)
    papel = _texto(concepto_blanca)
    de_linea = _texto(linea.descripcion) if linea is not None else None
    if linea is not None and not linea.es_contrato:
        if papel is not None:
            return _primero(propia, papel)
        return _primero(de_linea, propia)
    return _primero(propia, de_linea, papel)


def fila_a_guardar(
    fila: CamposFila,
    linea: LineaDeLaFila | None,
    concepto_blanca: str | None,
) -> CamposFila:
    """(R1–R3) Lo que debe quedar guardado en la fila: concepto, unidad,
    precio, ``unidad_albaran`` y ``cantidad_convertida``. ``cantidad_albaran``
    y ``factor_conversion`` salen tal cual."""
    unidad = _primero(
        _texto(linea.unidad) if linea is not None else None,
        _texto(fila.unidad_contrato),
    )
    precio = fila.precio_unitario_final
    if precio is None and linea is not None:
        precio = linea.precio_unitario
    unidad_albaran = fila.unidad_albaran
    cantidad_convertida = fila.cantidad_convertida
    if sin_conversion(fila.factor_conversion):
        unidad_albaran = _primero(_texto(fila.unidad_albaran), unidad)
        if cantidad_convertida is None:
            cantidad_convertida = fila.cantidad_albaran
    return CamposFila(
        descripcion_linea=concepto_a_guardar(
            fila.descripcion_linea, linea, concepto_blanca,
        ),
        unidad_contrato=unidad,
        unidad_albaran=unidad_albaran,
        precio_unitario_final=precio,
        cantidad_albaran=fila.cantidad_albaran,
        cantidad_convertida=cantidad_convertida,
        factor_conversion=fila.factor_conversion,
    )


def cambios_a_guardar(
    fila: CamposFila,
    linea: LineaDeLaFila | None,
    concepto_blanca: str | None,
) -> dict[str, Any]:
    """Solo las columnas de la fila que ``fila_a_guardar`` cambia, con su valor
    nuevo (lo que escriben sv4 al materializar y el relleno; vacío = nada)."""
    nueva = fila_a_guardar(fila, linea, concepto_blanca)
    return {
        campo.name: getattr(nueva, campo.name)
        for campo in fields(CamposFila)
        if getattr(nueva, campo.name) != getattr(fila, campo.name)
    }
