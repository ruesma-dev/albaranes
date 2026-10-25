# domain/services/partidas_ficha.py
"""F-098 · la partida en la ficha: se enseña el código completo, se guarda el cod.

Decisión del humano (P1 = a, 2026-10-24): en ``codigo_partida_final`` se
guarda el cod de Sigrid (``99.01.64``) y la ficha enseña el código completo
(``CD.99.01.64``), que calcula comun desde el árbol de la obra. Aquí, puro y
sin I/O (la lista llega por ``PartidasObraPort``):

- :func:`presentar_partidas`: el mapa cod → completo de los cod que pinta la
  ficha y el ✓ de la partida cuando la leída y la de su línea de contrato son
  la misma hoja (R23, R24). Sin lista, el mismo detalle (R28).
- :func:`traducir_partida`: lo que se guarda al editar una fila o dividirla: el
  cod de la lista si la partida casa, si no tal cual (R25). Nunca recorta
  texto (P6: «quitar CD al registrar» se cumple guardando el cod de la lista).

La regla (capítulo, completo, casar) es de comun; aquí no se copia nada.
"""
from __future__ import annotations

from collections.abc import Iterator

from ruesma_comun.sigrid import (
    ListaPartidasObra,
    misma_partida,
    mostrar_partida,
    resolver_partida_obra,
)
from ruesma_comun.sigrid.partidas import RESOLUCION_EXACTA, RESOLUCION_NORMALIZADA

from domain.models.review_models import (
    ConciliacionDisplay,
    DisplayLine,
    DocumentDetailPayload,
)


def _cods_de_la_ficha(detalle: DocumentDetailPayload) -> Iterator[str | None]:
    """Los cod que pinta la ficha: finales y casadas de las filas, líneas de
    contrato («Origen ✎», «Traer líneas contrato») y finales de la valoración
    («Líneas a Sigrid»)."""
    for linea in detalle.display_lines:
        if linea.concilia is not None:
            yield linea.concilia.codigo_partida
            yield linea.concilia.codigo_partida_casada
    for contrato in detalle.contrato_lines:
        yield contrato.codigo_partida
    if detalle.valuation is not None:
        for valorada in detalle.valuation.lines_by_merge_line_id.values():
            yield valorada.codigo_partida_final
        for valorada in detalle.valuation.synthetic_lines:
            yield valorada.codigo_partida_final


def _mostradas(detalle: DocumentDetailPayload, lista: ListaPartidasObra) -> dict[str, str]:
    mapa: dict[str, str] = {}
    for cod in _cods_de_la_ficha(detalle):
        clave = (cod or "").strip()
        if not clave:
            continue
        completo = mostrar_partida(lista, clave)
        if completo != clave:
            mapa[clave] = completo
    return mapa


def _conciliacion(
    linea: DisplayLine, lista: ListaPartidasObra, mostradas: dict[str, str],
) -> ConciliacionDisplay | None:
    """(R24) La conciliación con ✓ si su ⚠ era la misma hoja; si no, ``None``.

    Solo toca un ``agree_partida`` falso (nunca un ✓ ni un «sin icono») y solo
    fuera de almacén. La leída es la del albarán o, sin blanca, la final (como
    el repositorio, F-076).
    """
    conc = linea.concilia
    if conc is None or conc.agree_partida is not False or conc.estado_partida == "almacen":
        return None
    leida = linea.codigo_imputacion if linea.line_kind == "from_albaran" else conc.codigo_partida
    if not misma_partida(lista, leida, conc.codigo_partida_casada):
        return None
    final = (conc.codigo_partida or "").strip()
    pintado = mostradas.get(final, final)
    texto = (leida or "").strip()
    return conc.model_copy(update={
        "agree_partida": True,
        "aviso_partida": None,
        "partida_normalizada_desde": texto if texto != pintado else None,
    })


def presentar_partidas(
    detalle: DocumentDetailPayload, lista: ListaPartidasObra | None,
) -> DocumentDetailPayload:
    """(F-098 R23, R24, R28) El detalle con la partida pintada en completo.

    Sin lista, el MISMO objeto: la ficha sale como antes de F-098 (cod, aviso
    por la clave de F-076). Con lista, una copia (``model_copy``, no muta) con
    ``partidas_mostradas`` y el ✓ de las filas cuya leída y casada son la
    misma hoja (``CD.99.01.64`` frente a ``99.01.64`` de CD), con la nota
    «Normalizada» solo si la leída no es lo que se pinta.
    """
    if lista is None:
        return detalle
    mostradas = _mostradas(detalle, lista)
    lineas = []
    for linea in detalle.display_lines:
        conc = _conciliacion(linea, lista, mostradas)
        lineas.append(linea if conc is None else linea.model_copy(update={"concilia": conc}))
    return detalle.model_copy(update={"partidas_mostradas": mostradas, "display_lines": lineas})


def traducir_partida(lista: ListaPartidasObra | None, valor: str | None) -> str | None:
    """(F-098 R25) Lo que se guarda para la partida que manda la ficha.

    Vacía o sin lista ⇒ igual. Con lista, si casa ``exacta``, ``normalizada`` o
    ``completa`` (``resolver_partida_obra``, con la guarda de no hoja) ⇒ el cod
    de la lista (``CD.99.01.64`` ⇒ ``99.01.64``); si no, igual: el servidor no
    la rechaza, como hasta ahora. Nunca recorta un prefijo por su cuenta:
    ``CD2.01`` de la 0692 es un cod y se guarda ``CD2.01``.
    """
    if lista is None or valor is None or not valor.strip():
        return valor
    resolucion = resolver_partida_obra(lista, valor, None)
    if resolucion.motivo in (RESOLUCION_EXACTA, RESOLUCION_NORMALIZADA):
        return resolucion.codigo
    return valor
