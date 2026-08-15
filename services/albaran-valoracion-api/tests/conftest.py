# tests/conftest.py
"""Ancla la raiz de sv5 en ``sys.path``.

Los tests importan ``application``, ``domain``, ``config`` e
``infrastructure`` como paquetes de primer nivel (igual que hace el
servicio al arrancar). Cuando la suite se lanza desde la raiz del
monorepo, el directorio del servicio no esta en ``sys.path`` y esos
imports fallarian; este conftest lo mete explicitamente en vez de
depender del cwd desde el que se invoque pytest.

NINGUN test de este directorio toca red, BBDD ni LLM: el repositorio de
contexto se ejercita por sus metodos puros (fila -> DTO) y los prompts se
leen del YAML real.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
if str(RAIZ_SERVICIO) not in sys.path:
    sys.path.insert(0, str(RAIZ_SERVICIO))
