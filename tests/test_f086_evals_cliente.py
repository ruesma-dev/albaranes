# tests/test_f086_evals_cliente.py
"""F-086 · R13–R15: el banco construye para sv5 el cliente de Claude de producción.

Sin LLM ni red. Las clases de cliente de comun se sustituyen por dobles que
apuntan con qué se construyeron (como `clientes_falsos` de
`test_f083_fases.py`) y el módulo de sv5 con la herramienta se registra en
`sys.modules` desde su fichero (fixture `herramienta_sv5` de `conftest.py`).
"""

from __future__ import annotations

import inspect
import sys
import types
from types import SimpleNamespace as NS

import pytest

from evals.procesos import sv2_extraccion, sv5_valoracion

#: Lo que sv5 pide en producción (`infrastructure/llm/claude_messages_client.py`).
DESCRIPCION_SV5 = (
    "Devuelve la valoración estructurada de las líneas del albarán "
    "conforme al esquema exigido. Llama SIEMPRE y SOLO a esta herramienta."
)


class _Cliente:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


@pytest.fixture
def clientes(monkeypatch, herramienta_sv5):
    from ruesma_comun.llm import (
        claude_messages_client,
        gemini_genai_client,
        openai_responses_client,
    )

    for modulo, nombre in (
        (claude_messages_client, "ClaudeMessagesVisionClient"),
        (gemini_genai_client, "GeminiGenAiVisionClient"),
        (openai_responses_client, "OpenAIResponsesVisionClient"),
    ):
        monkeypatch.setattr(modulo, nombre, type(nombre, (_Cliente,), {}))
    spec = types.ModuleType("spec_falsa")
    spec.ProviderClientSpec = lambda **kwargs: NS(**kwargs)
    monkeypatch.setitem(sys.modules, "application.services.albaran_extraction_service", spec)
    monkeypatch.setitem(sys.modules, "application.services.valuation_extraction_service", spec)
    for variable in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.setenv(variable, f"clave-{variable}")
    for variable in ("ANTHROPIC_MODEL", "GEMINI_MODEL", "OPENAI_MODEL",
                     "ANTHROPIC_MAX_TOKENS", "ANTHROPIC_TIMEOUT_S"):
        monkeypatch.delenv(variable, raising=False)
    return herramienta_sv5


# --- R13 · la herramienta de sv5, de una sola definición ---------------------------


def test_f086_r13_la_definicion_de_sv5_es_la_de_produccion(herramienta_sv5):
    assert herramienta_sv5.TOOL_NAME_VALORACION == "emit_valuation_result"
    assert herramienta_sv5.TOOL_DESCRIPTION_VALORACION == DESCRIPCION_SV5


def test_f086_r13_runner_claude_con_la_herramienta_de_sv5(clientes):
    claude = sv5_valoracion._clientes_reales("claude")
    assert claude.client.kwargs == {
        "api_key": "clave-ANTHROPIC_API_KEY",
        "tool_name": "emit_valuation_result",
        "tool_description": DESCRIPCION_SV5,
    }
    assert claude.model_name == "claude-sonnet-4-5"


def test_f086_r13_comparador_claude_5_5_con_la_herramienta_de_sv5(clientes):
    medidor = object()
    opus = sv5_valoracion._clientes_reales(
        "claude", modelo="claude-opus-5-5", call_logger=medidor, forzar_herramienta=False
    )
    assert opus.client.kwargs == {
        "api_key": "clave-ANTHROPIC_API_KEY",
        "tool_name": "emit_valuation_result",
        "tool_description": DESCRIPCION_SV5,
        "call_logger": medidor,
        "forzar_herramienta": False,
    }
    assert opus.model_name == "claude-opus-5-5"


def test_f086_r13_sale_del_modulo_de_sv5_y_no_de_una_copia(clientes, monkeypatch):
    otra = types.ModuleType("herramienta_falsa")
    otra.TOOL_NAME_VALORACION = "herramienta_x"
    otra.TOOL_DESCRIPTION_VALORACION = "descripcion x"
    monkeypatch.setitem(sys.modules, "infrastructure.llm.claude_messages_client", otra)
    kwargs = sv5_valoracion._clientes_reales("claude").client.kwargs
    assert (kwargs["tool_name"], kwargs["tool_description"]) == ("herramienta_x", "descripcion x")


def test_f086_r13_otros_proveedores_de_sv5_sin_cambios(clientes, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MAX_TOKENS", "16000")
    openai = sv5_valoracion._clientes_reales("openai")
    gemini = sv5_valoracion._clientes_reales("gemini")
    assert openai.client.args == ("clave-OPENAI_API_KEY",) and openai.client.kwargs == {}
    assert gemini.client.args == ("clave-GEMINI_API_KEY",) and gemini.client.kwargs == {}


# --- R14 · max_tokens y timeout del entorno, si existen ----------------------------


def test_f086_r14_sin_variables_no_se_pasan(clientes):
    kwargs = sv5_valoracion._clientes_reales("claude").client.kwargs
    assert "max_tokens" not in kwargs and "timeout_s" not in kwargs


def test_f086_r14_defectos_de_comun_iguales_a_los_de_sv5():
    from ruesma_comun.llm.claude_messages_client import ClaudeMessagesVisionClient

    parametros = inspect.signature(ClaudeMessagesVisionClient.__init__).parameters
    assert parametros["max_tokens"].default == 8192
    assert parametros["timeout_s"].default == 120


def test_f086_r14_con_variables_las_toma_del_entorno(clientes, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MAX_TOKENS", "16000")
    monkeypatch.setenv("ANTHROPIC_TIMEOUT_S", " 180 ")
    kwargs = sv5_valoracion._clientes_reales("claude", forzar_herramienta=False).client.kwargs
    assert kwargs["max_tokens"] == 16000
    assert kwargs["timeout_s"] == 180


@pytest.mark.parametrize("variable", ["ANTHROPIC_MAX_TOKENS", "ANTHROPIC_TIMEOUT_S"])
def test_f086_r14_cada_variable_por_separado(clientes, monkeypatch, variable):
    monkeypatch.setenv(variable, "99")
    kwargs = sv5_valoracion._clientes_reales("claude").client.kwargs
    clave = {"ANTHROPIC_MAX_TOKENS": "max_tokens", "ANTHROPIC_TIMEOUT_S": "timeout_s"}
    assert kwargs[clave[variable]] == 99
    otra = ({"max_tokens", "timeout_s"} - {clave[variable]}).pop()
    assert otra not in kwargs


@pytest.mark.parametrize("valor", ["", "   "])
def test_f086_r14_vacia_es_como_si_no_existiera(clientes, monkeypatch, valor):
    monkeypatch.setenv("ANTHROPIC_MAX_TOKENS", valor)
    monkeypatch.setenv("ANTHROPIC_TIMEOUT_S", valor)
    kwargs = sv5_valoracion._clientes_reales("claude").client.kwargs
    assert "max_tokens" not in kwargs and "timeout_s" not in kwargs


@pytest.mark.parametrize("variable", ["ANTHROPIC_MAX_TOKENS", "ANTHROPIC_TIMEOUT_S"])
def test_f086_r14_valor_no_entero_falla_nombrando_la_variable(clientes, monkeypatch, variable):
    monkeypatch.setenv(variable, "mucho")
    with pytest.raises(ValueError, match=f"{variable}='mucho' no es un entero"):
        sv5_valoracion._clientes_reales("claude")


# --- cliente_llm: los argumentos nuevos solo llegan si se dan (R14, R15) ------------


def test_f086_r14_cliente_llm_pasa_solo_lo_que_se_da(clientes):
    _, cliente = sv5_valoracion.cliente_llm(
        "claude", "t", "m", None, True, tool_description="d", max_tokens=5, timeout_s=7
    )
    assert cliente.kwargs == {
        "api_key": "clave-ANTHROPIC_API_KEY", "tool_name": "t",
        "tool_description": "d", "max_tokens": 5, "timeout_s": 7,
    }
    _, cliente = sv5_valoracion.cliente_llm("claude", "t", "m", None, True)
    assert cliente.kwargs == {"api_key": "clave-ANTHROPIC_API_KEY", "tool_name": "t"}


def test_f086_r14_cliente_llm_no_los_pasa_a_otros_proveedores(clientes):
    for proveedor in ("openai", "gemini"):
        _, cliente = sv5_valoracion.cliente_llm(
            proveedor, "t", "m", None, True, tool_description="d", max_tokens=5, timeout_s=7
        )
        assert cliente.kwargs == {}


# --- R15 · sv2 no cambia -----------------------------------------------------------


def test_f086_r15_sv2_igual_aunque_haya_variables(clientes, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_MAX_TOKENS", "16000")
    monkeypatch.setenv("ANTHROPIC_TIMEOUT_S", "180")
    claude = sv2_extraccion._especificacion("claude")
    assert claude.client.kwargs == {
        "api_key": "clave-ANTHROPIC_API_KEY", "tool_name": "emit_albaran_extraction",
    }
    opus = sv2_extraccion._especificacion("claude", modelo="claude-opus-5-5",
                                          forzar_herramienta=False)
    assert opus.client.kwargs == {
        "api_key": "clave-ANTHROPIC_API_KEY", "tool_name": "emit_albaran_extraction",
        "forzar_herramienta": False,
    }
