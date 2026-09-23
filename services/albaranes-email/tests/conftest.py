# tests/conftest.py
"""Ancla la raiz de sv1 en ``sys.path`` (primera suite del servicio, F-048 T6).

Los tests importan ``application``, ``domain``, ``config`` e
``infrastructure`` como paquetes de primer nivel, igual que hace
``main.py`` al arrancar. Si la suite se lanza desde la raiz del monorepo,
el directorio del servicio no esta en ``sys.path``: este conftest lo mete
en vez de depender del cwd desde el que se invoque pytest.

NINGUN test de este directorio toca red, buzon M365 ni BBDD: el buzon,
Graph (``httpx.MockTransport``), el intake, el almacen de blobs y la cola
son dobles (``dobles_sv1.py``). Los textos de correo son inventados y
llevan el centinela ``CENTINELA-F048``; nunca un correo real (R38).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))
