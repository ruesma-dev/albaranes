# tests/test_f083_claude_forzar_herramienta.py
"""F-083 · R38: `forzar_herramienta` del cliente de Claude.

Los Claude 5.5 (y Fable 5.1) rechazan con 400 `tool_choice` de tipo `tool`.
Con `forzar_herramienta=False` el cliente pide `auto`; con el valor por
defecto, la petición es EXACTAMENTE la de hoy. Sin red: el SDK se sustituye
por un doble que captura los argumentos de `messages.create`.
"""

from __future__ import annotations

from types import SimpleNamespace as NS

import pytest
from pydantic import BaseModel

from ruesma_comun.llm.claude_messages_client import ClaudeMessagesVisionClient


class _Salida(BaseModel):
    numero: str


class _Mensajes:
    def __init__(self):
        self.llamadas: list[dict] = []

    def create(self, **kwargs):
        self.llamadas.append(kwargs)
        return NS(content=[NS(type="tool_use", name="emitir", input={"numero": "A-1"})])


class _Logger:
    def __init__(self):
        self.resumenes: list[dict] = []

    def log_call(self, **kwargs):
        self.resumenes.append(kwargs["request_summary"])


def _cliente(**extra):
    logger = _Logger()
    cliente = ClaudeMessagesVisionClient(
        api_key="clave-de-prueba", tool_name="emitir", call_logger=logger, **extra
    )
    mensajes = _Mensajes()
    cliente._client = NS(messages=mensajes)
    resultado = cliente.extract_document(
        model="claude-opus-5-5", instructions="sistema", user_text="texto",
        response_model=_Salida,
    )
    assert resultado == _Salida(numero="A-1")
    (llamada,) = mensajes.llamadas
    (resumen,) = logger.resumenes
    return llamada, resumen


def test_f083_r38_por_defecto_la_peticion_es_la_de_hoy():
    llamada, resumen = _cliente()
    esquema = {
        "properties": {"numero": {"type": "string"}},
        "required": ["numero"],
        "type": "object",
    }
    assert llamada == {
        "model": "claude-opus-5-5",
        "max_tokens": 8192,
        "system": "sistema",
        "tools": [{
            "name": "emitir",
            "description": (
                "Devuelve el resultado estructurado conforme al esquema exigido. "
                "Debes llamar SIEMPRE a esta herramienta y solo a ella."
            ),
            "input_schema": esquema,
        }],
        "tool_choice": {"type": "tool", "name": "emitir"},
        "messages": [{"role": "user", "content": [{"type": "text", "text": "texto"}]}],
    }
    assert resumen["response_format"] == "tool_use forced"


def test_f083_r38_true_explicito_es_identico_al_defecto():
    assert _cliente(forzar_herramienta=True) == _cliente()


def test_f083_r38_false_pide_auto_y_nada_mas_cambia():
    sin_forzar, resumen = _cliente(forzar_herramienta=False)
    forzada, _ = _cliente()
    assert sin_forzar["tool_choice"] == {"type": "auto"}
    assert {k: v for k, v in sin_forzar.items() if k != "tool_choice"} == {
        k: v for k, v in forzada.items() if k != "tool_choice"
    }
    assert resumen["response_format"] == "tool_use auto"


def test_f083_r38_sin_tool_use_falla_como_hoy():
    cliente = ClaudeMessagesVisionClient(api_key="x", tool_name="emitir",
                                         forzar_herramienta=False)
    mensajes = _Mensajes()
    mensajes.create = lambda **kwargs: NS(content=[NS(type="text", text="no es json")])
    cliente._client = NS(messages=mensajes)
    with pytest.raises(ValueError, match="no devolvió tool_use"):
        cliente.extract_document(model="claude-opus-5-5", instructions="s", user_text="t",
                                 response_model=_Salida)
