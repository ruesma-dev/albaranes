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

import json
import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

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


# --------------------------------------------------------------------------- #
# Fase B (R19–R27): la edición guardada en ``edicion_manual_json``
# --------------------------------------------------------------------------- #

#: Versión del JSON de la edición: otra versión se lee como «sin edición».
VERSION_EDICION = 1

CAMPO_PARTIDA = "codigo_partida"
CAMPO_ORIGEN = "origen"
CAMPO_BLOQUEADA = "bloqueada"

#: (design §5) Campo de la edición -> columnas de la fila que ese campo escribe,
#: en el orden de la regla. ``origen`` no tiene columnas: se guarda como
#: ``{"tipo": "nueva"}`` o ``{"tipo": "contrato", "linea": id}`` y lo aplica sv6
#: (recrear la derivada o pasar a Nueva, R27).
COLUMNAS_DE_CAMPO: dict[str, tuple[str, ...]] = {
    CAMPO_CANTIDAD: ("cantidad_albaran", "cantidad_convertida"),
    CAMPO_PRECIO: ("precio_unitario_final",),
    CAMPO_IMPORTE: ("importe_calculado",),
    CAMPO_DESCUENTO: ("descuento_albaran_aplicado",),
    CAMPO_PARTIDA: ("codigo_partida_final", "partida_action"),
    "unidad": ("unidad_contrato",),
    "descripcion": ("descripcion_linea",),
    "codigo_externo": ("codigo_externo",),
    "producto_sigrid": ("producto_sigrid",),
    CAMPO_BLOQUEADA: ("bloqueada",),
    CAMPO_ORIGEN: (),
}

#: (design §5) Lo que se guarda en ``calculado``: la fila tal como la dejó sv6
#: (para «Volver a lo calculado» y para la marca «✋»).
COLUMNAS_CALCULADO: tuple[str, ...] = (
    "cantidad_albaran", "cantidad_convertida", "precio_unitario_final",
    "descuento_albaran_aplicado", "importe_calculado", "importe_source",
    "codigo_partida_final", "partida_action", "unidad_contrato", "descripcion_linea",
    "matched_contrato_line_id", "derived_contrato_line_id",
)

#: Campos de la edición que entran en el importe (los de ``recalcular_fila``).
CAMPOS_DEL_IMPORTE = frozenset({CAMPO_CANTIDAD, CAMPO_PRECIO, CAMPO_DESCUENTO, CAMPO_IMPORTE})

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EdicionManual:
    """(R20, R21) Lo editado a mano en una fila: ``campos`` (campo -> sus
    columnas con el valor puesto, u ``origen``), ``calculado`` (la fila como la
    dejó sv6; vacío en una ``fila_entera``) y ``fila_entera`` (la creó sv4)."""

    campos: dict[str, Any]
    calculado: dict[str, Any]
    fila_entera: bool = False

    def a_json(self) -> str:
        return json.dumps(
            {"v": VERSION_EDICION, "campos": self.campos, "calculado": self.calculado,
             "fila_entera": self.fila_entera},
            ensure_ascii=False,
        )


def leer_edicion(texto: str | None) -> EdicionManual | None:
    """La edición de ``edicion_manual_json``; ``None`` si no hay. Un JSON roto o
    de otra versión es «sin edición» con un aviso en el log: nunca lanza (un dato
    malo no puede tumbar una valoración ni la ficha)."""
    if texto is None or not str(texto).strip():
        return None
    try:
        datos = json.loads(texto)
    except (TypeError, ValueError):
        _log.warning("[edicion-manual] JSON ilegible, se ignora")
        return None
    if (
        not isinstance(datos, dict)
        or datos.get("v") != VERSION_EDICION
        or not isinstance(datos.get("campos"), dict)
        or not isinstance(datos.get("calculado"), dict)
    ):
        _log.warning("[edicion-manual] edición de otra versión o mal formada, se ignora")
        return None
    return EdicionManual(
        campos=dict(datos["campos"]),
        calculado=dict(datos["calculado"]),
        fila_entera=bool(datos.get("fila_entera", False)),
    )


def origen_de_fila(fila: Mapping[str, Any]) -> dict[str, Any]:
    """(R20, R27) El origen de una fila tal como lo guarda la edición."""
    if fila.get("derived_contrato_line_id") is not None or fila.get("matched_contrato_line_id") is None:
        return {"tipo": "nueva"}
    return {"tipo": "contrato", "linea": fila["matched_contrato_line_id"]}


def registrar_edicion(
    previa: str | None,
    *,
    fila_antes: Mapping[str, Any] | None,
    fila_despues: Mapping[str, Any],
    campos: Iterable[str],
    fila_entera: bool = False,
) -> str:
    """(R20, R21) El nuevo ``edicion_manual_json`` tras escribir ``campos`` en
    una fila: lo previo fusionado con lo nuevo (los valores salen de
    ``fila_despues``). La primera vez, ``calculado`` es ``fila_antes`` (la fila
    de sv6); después no cambia. Precio e importe se excluyen: queda el último
    (y si llegan los dos, el importe, del que salió el precio). ``fila_entera``
    se conserva una vez puesta. ``ValueError`` con un campo desconocido."""
    nuevos = set(campos)
    desconocidos = nuevos - set(COLUMNAS_DE_CAMPO)
    if desconocidos:
        raise ValueError(f"campos de edición desconocidos: {sorted(desconocidos)}")
    if CAMPO_IMPORTE in nuevos:
        nuevos.discard(CAMPO_PRECIO)
    previa_ed = leer_edicion(previa)
    if previa_ed is None:
        entera = fila_entera
        calculado = (
            {} if entera or fila_antes is None
            else {c: fila_antes.get(c) for c in COLUMNAS_CALCULADO}
        )
        guardados: dict[str, Any] = {}
    else:
        entera = previa_ed.fila_entera or fila_entera
        calculado = previa_ed.calculado
        guardados = dict(previa_ed.campos)
    for campo in nuevos:
        if campo == CAMPO_IMPORTE:
            guardados.pop(CAMPO_PRECIO, None)
        elif campo == CAMPO_PRECIO:
            guardados.pop(CAMPO_IMPORTE, None)
        guardados[campo] = (
            origen_de_fila(fila_despues) if campo == CAMPO_ORIGEN
            else {c: fila_despues.get(c) for c in COLUMNAS_DE_CAMPO[campo]}
        )
    ordenados = {c: guardados[c] for c in COLUMNAS_DE_CAMPO if c in guardados}
    return EdicionManual(campos=ordenados, calculado=calculado, fila_entera=entera).a_json()


def aplicar_edicion(fila: Mapping[str, Any], edicion: EdicionManual) -> dict[str, Any]:
    """(R25) La fila nueva de sv6 con la edición encima: sustituye las columnas
    de los campos editados y recalcula P o I con :func:`recalcular_fila` (Q =
    convertida o, sin ella, la del albarán). Un importe editado que ya no se
    puede despejar (Q 0) se queda como se editó, con el P de sv6: la fila no
    cuadrará y no se podrá aprobar (R16). ``edicion_manual_json`` lleva la misma
    edición con ``calculado`` = la fila que acaba de calcular sv6 (salvo en una
    ``fila_entera``). El origen no se aplica aquí (lo hace sv6, R27). No toca
    ``fila``."""
    nueva = dict(fila)
    for campo, valores in edicion.campos.items():
        if campo == CAMPO_ORIGEN or not isinstance(valores, dict):
            continue
        for columna in COLUMNAS_DE_CAMPO.get(campo, ()):
            if columna in valores:
                nueva[columna] = valores[columna]
    editados = CAMPOS_DEL_IMPORTE & set(edicion.campos)
    if editados:
        cantidad = (
            nueva.get("cantidad_convertida")
            if nueva.get("cantidad_convertida") is not None
            else nueva.get("cantidad_albaran")
        )
        try:
            precio, importe = recalcular_fila(
                cantidad=cantidad,
                precio=nueva.get("precio_unitario_final"),
                descuento=nueva.get("descuento_albaran_aplicado"),
                importe=nueva.get("importe_calculado"),
                editados=editados,
            )
        except NoDespejable:
            precio = _numero_finito(nueva.get("precio_unitario_final"))
            importe = _numero_finito(nueva.get("importe_calculado"))
        nueva["precio_unitario_final"] = precio
        nueva["importe_calculado"] = importe
        nueva["importe_source"] = "calculated"
    calculado = {} if edicion.fila_entera else {c: fila.get(c) for c in COLUMNAS_CALCULADO}
    nueva["edicion_manual_json"] = EdicionManual(
        campos=edicion.campos, calculado=calculado, fila_entera=edicion.fila_entera,
    ).a_json()
    return nueva


#: (F-051) La acción de partida del almacén elegido a mano.
ACCION_ALMACEN_ELEGIDO = "almacen_elegido"


def es_fila_manual(
    *,
    line_kind: str | None,
    bloqueada: bool,
    derivada_origen: str | None,
    precio_unitario_agreement: str | None,
    partida_action: str | None,
    edicion_manual_json: str | None = None,
) -> bool:
    """(F-065 R22, F-106 R22) ¿La tocó el administrativo? Línea ``manual`` o
    ``reparto``, bloqueada, con derivada ``manual_override``, con precio fijado
    a mano, con el almacén elegido o con edición guardada."""
    return (
        line_kind in ("manual", "reparto")
        or bool(bloqueada)
        or derivada_origen == "manual_override"
        or precio_unitario_agreement == "manual"
        or partida_action == ACCION_ALMACEN_ELEGIDO
        or leer_edicion(edicion_manual_json) is not None
    )
