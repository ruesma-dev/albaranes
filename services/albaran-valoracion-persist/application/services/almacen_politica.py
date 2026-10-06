# application/services/almacen_politica.py
"""F-051 · política pura del almacén por línea (sin I/O).

Una línea sin partida «no se asocia a partida»: es ALMACÉN, que se
representa con ``codigo_partida_final`` vacío, nunca con un literal
(D1 del humano, 2026-10-05). Cuando sv6 lo decide porque el albarán no
trae partida, deja rastro en ``partida_action`` con
``ACCION_ALMACEN_SIN_PARTIDA``; la marca es solo trazabilidad, no decide
el estado (sv4 pinta «Almacén» toda partida final vacía).

Cualquier familia puede ir a almacén (D2). Las familias «destinadas»
(las que normalmente se imputan a una partida a la entrada) solo añaden
un motivo de revisión NO bloqueante (R4, R5). La lista viene del
entorno (``FAMILIAS_DESTINADAS``, CSV) y la familia de la línea es la
efectiva (``ruesma_comun.contratos.familias.familia_efectiva``), que el
builder ya calcula: aquí no se infiere familia de nada.
"""
from __future__ import annotations

#: ``partida_action`` que sv6 escribe cuando el albarán no trae partida.
ACCION_ALMACEN_SIN_PARTIDA = "almacen_sin_partida"

#: Razón que acompaña a ``ACCION_ALMACEN_SIN_PARTIDA`` en la línea.
MOTIVO_SIN_PARTIDA = "almacen_sin_partida_en_albaran"

#: Motivo de revisión (no bloqueante) de una línea en almacén de una
#: familia destinada.
MOTIVO_FAMILIA_DESTINADA = "partida_ausente_familia_destinada"


def _normalizar_familia(familia: str | None) -> str:
    """Familia en minúsculas y sin espacios alrededor ('' si no hay)."""
    return (familia or "").strip().lower()


def familias_destinadas_de_csv(csv: str | None) -> frozenset[str]:
    """Conjunto de familias destinadas a partir del CSV del entorno (R9).

    No distingue mayúsculas ni espacios e ignora los elementos vacíos;
    un CSV vacío (o ``None``) significa «ninguna familia destinada».
    """
    if not csv:
        return frozenset()
    familias = (_normalizar_familia(trozo) for trozo in csv.split(","))
    return frozenset(familia for familia in familias if familia)


def motivo_revision_almacen(
    familia: str | None,
    destinadas: frozenset[str],
) -> str | None:
    """Motivo de revisión de una línea que va a almacén sin partida.

    Devuelve ``MOTIVO_FAMILIA_DESTINADA`` si la familia efectiva de la
    línea está entre las destinadas (R4) y ``None`` en cualquier otro
    caso: familia no destinada o línea sin familia (R5).
    """
    normalizada = _normalizar_familia(familia)
    if normalizada and normalizada in destinadas:
        return MOTIVO_FAMILIA_DESTINADA
    return None
