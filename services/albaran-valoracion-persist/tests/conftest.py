# tests/conftest.py
"""Ancla la raiz de sv6 en ``sys.path``.

Los tests importan ``application``, ``domain``, ``config`` e
``infrastructure`` como paquetes de primer nivel (igual que hace el
servicio al arrancar). Cuando la suite se lanza desde la raiz del
monorepo, el directorio del servicio no esta en ``sys.path`` y esos
imports fallarian; este conftest lo mete explicitamente en vez de
depender del cwd desde el que se invoque pytest.

AVISO: sv5 y sv6 tienen paquetes ``application``/``domain``/
``infrastructure`` de primer nivel con el MISMO nombre. NO se pueden
mezclar en una misma invocacion de pytest: colisionan en
``sys.modules``. El arnes (seccion 7 bis de ``harness/init.sh``)
ejecuta cada servicio con ``cd`` a su ruta, que es justo lo que evita
la colision.

NINGUN test de este directorio toca red, BBDD ni LLM: ``PriceReconciler``
e ``ImporteCalculator`` son clases puras y se prueban con valores
construidos a mano.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))

#: Valor por defecto de ``PRICE_TOLERANCE_PCT`` en ``config/settings.py``.
#: Los tests lo fijan a mano para no depender de ningun ``.env``.
TOLERANCIA_PRECIO_PCT = 2.0

#: Valor por defecto de ``IMPORTE_TOLERANCE_PCT`` en ``config/settings.py``.
TOLERANCIA_IMPORTE_PCT = 5.0


@pytest.fixture
def reconciliador():
    """``PriceReconciler`` con la tolerancia por defecto del servicio."""
    from application.services.price_reconciler import PriceReconciler

    return PriceReconciler(tolerance_pct=TOLERANCIA_PRECIO_PCT)


@pytest.fixture
def calculador_importe():
    """``ImporteCalculator`` con la tolerancia por defecto del servicio."""
    from application.services.importe_calculator import ImporteCalculator

    return ImporteCalculator(tolerance_pct=TOLERANCIA_IMPORTE_PCT)
