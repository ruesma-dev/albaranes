# tests/conftest.py
"""Ancla la raíz de sv9 en ``sys.path``.

Los tests importan ``application``, ``domain``, ``config``, ``infrastructure``
e ``interface_adapters`` como paquetes de primer nivel (igual que el servicio
al arrancar). Como sv3, sv5 y sv6 usan los mismos nombres de primer nivel, la
suite de sv9 se ejecuta SOLA, con ``cd`` a esta carpeta (sección 7 bis de
``harness/init.sh``); nunca en el mismo pytest que otro servicio.

NINGÚN test de este directorio toca red ni BBDD: fakes de los tres puertos
(``AltaRepository``, ``SigridAltaPort``, ``PdfAlbaranPort``),
``httpx.MockTransport`` para el cliente de sigrid-api y sesión simulada para el
repositorio SQL.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))
