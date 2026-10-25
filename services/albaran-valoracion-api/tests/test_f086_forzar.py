# tests/test_f086_forzar.py
"""F-086 · R1–R6 y R12: sv5 lee ``ANTHROPIC_FORZAR_HERRAMIENTA``.

Sin red, sin BBDD y sin LLM. Para R4, R5 y R12 se usa el cliente de Claude de
verdad (el de comun) con el SDK sustituido por un doble que apunta los
argumentos de ``messages.create``; para R3 y R6, los dobles de cliente de
``test_f085_wiring.py``. Mismo sustituto de ``fastapi`` que ese fichero.
"""
from __future__ import annotations

import logging
import sys
import types

import pytest
from pydantic import ValidationError


def _fastapi_de_prueba() -> types.ModuleType:
    """Sustituto mínimo de ``fastapi`` (ver ``test_f085_wiring.py``)."""
    modulo = types.ModuleType("fastapi")

    class FastAPI:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def get(self, ruta):
            return lambda funcion: funcion

        def post(self, ruta):
            return lambda funcion: funcion

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = "") -> None:
            super().__init__(detail)
            self.status_code = status_code

    modulo.FastAPI = FastAPI
    modulo.HTTPException = HTTPException
    return modulo


try:
    import fastapi  # noqa: F401
except ModuleNotFoundError:
    sys.modules["fastapi"] = _fastapi_de_prueba()

from config.settings import Settings

_VARIABLES = (
    "ENABLE_OPENAI", "ENABLE_GEMINI", "ENABLE_CLAUDE",
    "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
    "OPENAI_MODEL", "GEMINI_MODEL", "ANTHROPIC_MODEL",
    "ANTHROPIC_MAX_TOKENS", "ANTHROPIC_TIMEOUT_S", "ANTHROPIC_FORZAR_HERRAMIENTA",
    "IA3_PROVIDER", "IA4_PROVIDER", "PG_USER", "PG_PASSWORD", "GRAPH_KEY",
)

#: La herramienta que sv5 pide hoy a Claude (antes, en línea en ``app.py``).
TOOL_NAME_DE_HOY = "emit_valuation_result"
TOOL_DESCRIPTION_DE_HOY = (
    "Devuelve la valoración estructurada de las líneas del albarán "
    "conforme al esquema exigido. Llama SIEMPRE y SOLO a esta herramienta."
)

#: ``ca-sv5-valuation`` hoy (F-085, paso 1).
PASO_1 = {
    "ENABLE_OPENAI": "true", "OPENAI_API_KEY": "o", "OPENAI_MODEL": "gpt-6.1-sol",
    "ANTHROPIC_MODEL": "claude-opus-4-8", "IA3_PROVIDER": "openai", "IA4_PROVIDER": "openai",
}


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch):
    for variable in _VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def _settings(**entorno: str) -> Settings:
    base = {"PG_USER": "u", "PG_PASSWORD": "p", "GRAPH_KEY": "{}", "ANTHROPIC_API_KEY": "a"}
    base.update(entorno)
    return Settings(_env_file=None, **base)


# --- R1, R2 · Settings -------------------------------------------------------------


def test_f086_r1_por_defecto_true():
    assert _settings().anthropic_forzar_herramienta is True


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [("true", True), ("True", True), ("1", True), ("yes", True), ("on", True),
     ("false", False), ("FALSE", False), ("0", False), ("no", False), ("off", False)],
)
def test_f086_r1_se_lee_como_booleana(valor, esperado):
    assert _settings(ANTHROPIC_FORZAR_HERRAMIENTA=valor).anthropic_forzar_herramienta is esperado


def test_f086_r1_se_lee_del_entorno(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_FORZAR_HERRAMIENTA", "false")
    assert _settings().anthropic_forzar_herramienta is False


@pytest.mark.parametrize("valor", ["quizá", "2", "verdadero", "si"])
def test_f086_r2_valor_no_booleano_no_arranca(valor):
    with pytest.raises(ValidationError) as error:
        _settings(ANTHROPIC_FORZAR_HERRAMIENTA=valor)
    assert "ANTHROPIC_FORZAR_HERRAMIENTA" in str(error.value)
