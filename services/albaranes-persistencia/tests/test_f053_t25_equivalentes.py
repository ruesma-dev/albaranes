# tests/test_f053_t25_equivalentes.py
"""F-053 · T25 · RM5 (review fase 2): demostración EJECUTABLE de los
equivalentes #8, #9 y #10 de ``progress/mutacion_F-053.md``
(``scripts/medir_admisibilidad_f053.py:275``, recuento de líneas negativas).

Mismo patrón que ``services/albaranes-alta-sigrid/tests/test_f053_t25_equivalentes.py``
(y que F-048, ``7b8adab``): se carga el script REAL desde una fuente normalizada
(si una campaña ha inyectado uno de los equivalentes, se devuelve la línea a su
forma original), se fabrica cada variante mutada sustituyendo el texto y se
compara ``evaluar`` de las dos sobre un dominio amplio de albaranes. Un control
NO equivalente (``<= 0`` en la cantidad, que la campaña mató) sí se detecta.
"""
from __future__ import annotations

import itertools
import random
import sys
import types
from pathlib import Path

import pytest

from scripts import medir_admisibilidad_f053 as m
from tests.test_f053_medicion_admisibilidad import _fila

_NEGATIVAS = "1 for l in con_imp if (l.cantidad or 0) < 0 or (l.importe or 0) < 0"
_EQUIVALENTES = (
    _NEGATIVAS.replace("(l.cantidad or 0) < 0", "(l.cantidad or 1) < 0"),   # 8
    _NEGATIVAS.replace("(l.importe or 0) < 0", "(l.importe or 1) < 0"),     # 9
    _NEGATIVAS.replace("(l.importe or 0) < 0", "(l.importe or 0) <= 0"),    # 10
)


def _fuente() -> str:
    fuente = Path(m.__file__).read_text(encoding="utf-8")
    for mutado in _EQUIVALENTES:
        fuente = fuente.replace(mutado, _NEGATIVAS)
    assert fuente.count(_NEGATIVAS) == 1, "la línea cambió: rehacer la justificación"
    return fuente


def _cargar(fuente: str, *cambios: tuple[str, str]) -> types.ModuleType:
    for de, a in cambios:
        assert fuente.count(de) == 1
        fuente = fuente.replace(de, a)
    nombre = f"{m.__name__}__variante_{abs(hash(fuente))}"
    nuevo = types.ModuleType(nombre)
    nuevo.__file__ = m.__file__
    sys.modules[nombre] = nuevo  # dataclasses mira el módulo de la clase
    try:
        exec(compile(fuente, m.__file__, "exec"), nuevo.__dict__)  # noqa: S102
    finally:
        sys.modules.pop(nombre, None)
    return nuevo


def _albaranes():
    valores = (None, 0, 0.0, -0.0, 1e-12, -1e-12, 1e-9, -1e-9, 0.5, -0.5, 2.0, -2.0)
    lineas = [
        _fila("d", 1, cantidad_convertida=cantidad, cantidad_albaran=cantidad,
              importe_calculado=importe)
        for cantidad, importe in itertools.product(valores, valores)
    ]
    azar = random.Random(275)
    lotes = [[linea] for linea in lineas]
    lotes += [azar.sample(lineas, azar.randint(2, 6)) for _ in range(1500)]
    albaranes = []
    for n, lote in enumerate(lotes):
        filas = [{**fila, "document_id": f"d{n}", "lv_id": i} for i, fila in enumerate(lote, start=1)]
        (alb,) = m.agrupar(filas, [])
        albaranes.append(alb)
    return albaranes


@pytest.mark.parametrize("mutado", _EQUIVALENTES,
                         ids=["equivalente_8", "equivalente_9", "equivalente_10"])
def test_f053_t25_rm5_equivalentes_8_9_10_lineas_negativas(mutado):
    fuente = _fuente()
    base = _cargar(fuente)
    variante = _cargar(fuente, (_NEGATIVAS, mutado))
    control = _cargar(fuente, (_NEGATIVAS, _NEGATIVAS.replace(
        "(l.cantidad or 0) < 0", "(l.cantidad or 0) <= 0")))
    albaranes = _albaranes()

    assert len(albaranes) == 144 + 1500
    assert sum(base.evaluar(a) != variante.evaluar(a) for a in albaranes) == 0
    assert sum(base.evaluar(a) != control.evaluar(a) for a in albaranes) > 0
