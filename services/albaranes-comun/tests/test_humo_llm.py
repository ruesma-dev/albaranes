# tests/test_humo_llm.py
"""Test de humo de la capa LLM canónica (sin llamadas de red).

Valida lo que el merge sv2+sv5 debía garantizar:
  1. Los tres clientes se instancian y aceptan ``attachment=None``
     (modo texto puro, fix de sv5/abr 2026).
  2. El cliente Claude parametriza ``tool_name``/``tool_description``
     (sv2 usa emit_albaran_extraction, sv5 emit_valuation_result).
  3. El puerto compartido declara ``attachment`` opcional.

Ejecutar:  pytest tests/test_humo_llm.py -v
(Requiere los SDKs: pip install -e ".[dev]")
"""
from __future__ import annotations

import inspect

from ruesma_comun.llm.claude_messages_client import ClaudeMessagesVisionClient
from ruesma_comun.llm.gemini_genai_client import GeminiGenAiVisionClient
from ruesma_comun.llm.llm_attachment import LlmAttachment
from ruesma_comun.llm.llm_client import LlmVisionClient
from ruesma_comun.llm.openai_responses_client import OpenAIResponsesVisionClient
from ruesma_comun.llm.retry_policy import RetryPolicy


def test_puerto_declara_attachment_opcional() -> None:
    firma = inspect.signature(LlmVisionClient.extract_document)
    parametro = firma.parameters["attachment"]
    assert parametro.default is None, "attachment debe ser opcional en el puerto"


def test_claude_tool_parametrizado_y_texto_puro() -> None:
    cliente = ClaudeMessagesVisionClient(
        api_key="clave-de-prueba",
        tool_name="emit_valuation_result",
        tool_description="descripción de prueba",
    )
    assert cliente._tool_name == "emit_valuation_result"

    # Modo texto puro: un único bloque de texto, sin documento.
    bloques = cliente._build_content_block(attachment=None, user_text="hola")
    assert bloques == [{"type": "text", "text": "hola"}]

    # Modo documento: bloque document + bloque text.
    adjunto = LlmAttachment(
        kind="pdf", filename="a.pdf", mime_type="application/pdf", data=b"%PDF-1.4"
    )
    bloques = cliente._build_content_block(attachment=adjunto, user_text="hola")
    assert [b["type"] for b in bloques] == ["document", "text"]


def test_claude_defaults_genericos() -> None:
    cliente = ClaudeMessagesVisionClient(api_key="clave-de-prueba")
    assert cliente._tool_name == "emit_structured_result"


def test_los_tres_clientes_se_instancian_y_comparten_puerto() -> None:
    politica = RetryPolicy()
    clientes = [
        ClaudeMessagesVisionClient(api_key="x", retry_policy=politica),
        OpenAIResponsesVisionClient("x", retry_policy=politica),
        GeminiGenAiVisionClient(api_key="x", retry_policy=politica),
    ]
    for cliente in clientes:
        assert isinstance(cliente, LlmVisionClient)
        firma = inspect.signature(cliente.extract_document)
        assert firma.parameters["attachment"].default is None, type(cliente).__name__
