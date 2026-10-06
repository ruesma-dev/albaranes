# domain/services/almacen.py
"""F-051 · almacén por línea: estado de partida de una línea valorada.

Decisión del humano (D1, 2026-10-05): «en el visor cuando una línea no
tenga partida que sea almacén […] negocio ya funciona así a mano». Una
línea con valoración y ``codigo_partida_final`` vacío ES almacén, tenga
o no marca en ``partida_action``: la marca solo deja rastro de quién o
por qué (``almacen_sin_partida`` de sv6, ``ACCION_ALMACEN_ELEGIDO`` de
sv4). Por eso aquí no se mira la marca.

Puro, sin I/O: lo usan el repositorio (montaje de la ficha y edición de
la fila salmón) y la plantilla, a través del payload.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

#: ``partida_action`` que escribe sv4 cuando el revisor elige «Almacén»
#: (o vacía la partida) en una línea.
ACCION_ALMACEN_ELEGIDO = "almacen_elegido"

EstadoPartida = Literal["partida", "almacen"]


def estado_partida(codigo_partida_final: str | None) -> EstadoPartida:
    """``almacen`` si la partida final está vacía (o solo espacios);
    ``partida`` en cualquier otro caso (R10)."""
    if codigo_partida_final is None or not codigo_partida_final.strip():
        return "almacen"
    return "partida"


def contar_con_partida(partidas: Iterable[str | None]) -> int:
    """Cuántas de esas partidas finales NO están en almacén (R17: lo que
    perderá su partida el botón «Almacén a todas las líneas»)."""
    return sum(1 for partida in partidas if estado_partida(partida) == "partida")
