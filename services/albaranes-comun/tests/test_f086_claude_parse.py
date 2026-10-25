# tests/test_f086_claude_parse.py
"""F-086 · R8–R11: la respuesta de Claude sin `tool_use`.

Con `tool_choice` `auto` (los Claude 5.5) el modelo puede contestar en texto
en vez de llamar a la herramienta. Si ese texto es un objeto JSON que valida
contra el modelo, el cliente lo acepta (y avisa); si no, `ValueError` con el
`stop_reason`. El camino `tool_use` no cambia. Sin red: el SDK se sustituye
por un doble que devuelve la respuesta que pide cada test.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace as NS

import pytest
from pydantic import BaseModel, ConfigDict
from ruesma_comun.llm import claude_messages_client as modulo
from ruesma_comun.llm.claude_messages_client import ClaudeMessagesVisionClient


class _Linea(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concepto: str


class _Salida(BaseModel):
    model_config = ConfigDict(extra="forbid")
    numero: str
    lineas: list[_Linea] = []


class _Logger:
    def __init__(self):
        self.llamadas: list[dict] = []

    def log_call(self, **kwargs):
        self.llamadas.append(kwargs)


def _texto(texto: str) -> NS:
    return NS(type="text", text=texto)


def _respuesta(*bloques, stop_reason="end_turn") -> NS:
    return NS(content=list(bloques), stop_reason=stop_reason)


def _extraer(respuesta, logger=None):
    cliente = ClaudeMessagesVisionClient(
        api_key="clave-de-prueba", tool_name="emitir", forzar_herramienta=False,
        call_logger=logger,
    )
    cliente._client = NS(messages=NS(create=lambda **kwargs: respuesta))
    return cliente.extract_document(
        model="claude-opus-5-5", instructions="sistema", user_text="texto",
        response_model=_Salida,
    )


def _avisos(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.name == modulo.logger.name and r.levelno == logging.WARNING]


# --- R8 · texto JSON sin tool_use: se acepta validado -----------------------------


def test_f086_r8_texto_json_sin_cerca_se_acepta():
    resultado = _extraer(_respuesta(_texto('{"numero": "A-1"}')))
    assert resultado == _Salida(numero="A-1")


@pytest.mark.parametrize(
    "texto",
    [
        '```json\n{"numero": "A-1"}\n```',
        '```\n{"numero": "A-1"}\n```',
        '  ```json\n{"numero": "A-1"}\n```  ',
    ],
)
def test_f086_r8_texto_json_con_cerca_se_acepta(texto):
    assert _extraer(_respuesta(_texto(texto))) == _Salida(numero="A-1")


def test_f086_r8_aplica_sanear_para_modelo():
    # La lista llega como string con JSON dentro y sobra un campo a None: sin
    # `sanear_para_modelo`, `extra="forbid"` y `list` lo rechazarían.
    texto = '{"numero": "A-1", "lineas": "[{\\"concepto\\": \\"arena\\"}]", "sobra": null}'
    resultado = _extraer(_respuesta(_texto(texto)))
    assert resultado == _Salida(numero="A-1", lineas=[_Linea(concepto="arena")])


def test_f086_r8_une_los_bloques_de_texto_y_salta_los_demas():
    resultado = _extraer(_respuesta(
        NS(type="thinking", thinking="pienso"),
        _texto('{"numero":'),
        _texto("   "),
        NS(type="text", text=None),
        _texto('"A-1"}'),
    ))
    assert resultado == _Salida(numero="A-1")


def test_f086_r8_tool_use_de_otra_herramienta_no_cuenta():
    resultado = _extraer(_respuesta(
        NS(type="tool_use", name="otra", input={"numero": "OTRA"}),
        _texto('{"numero": "A-1"}'),
    ))
    assert resultado == _Salida(numero="A-1")


def test_f086_r8_el_call_logger_registra_el_exito():
    logger = _Logger()
    _extraer(_respuesta(_texto('{"numero": "A-1"}')), logger)
    (llamada,) = logger.llamadas
    assert llamada["error"] is None
    assert llamada["response_payload"]["parsed_pydantic"] == {"numero": "A-1", "lineas": []}


# --- R9 · el WARNING, sin texto de la respuesta ni valores del albarán ------------


def test_f086_r9_warning_con_modelo_y_stop_reason(caplog):
    caplog.set_level(logging.DEBUG, logger=modulo.logger.name)
    _extraer(_respuesta(_texto('{"numero": "A-1"}'), stop_reason="end_turn"))
    assert _avisos(caplog) == [
        "[claude] sin tool_use: JSON de texto aceptado model=claude-opus-5-5 stop_reason=end_turn"
    ]


def test_f086_r9_el_warning_no_lleva_el_texto(caplog):
    caplog.set_level(logging.DEBUG, logger=modulo.logger.name)
    _extraer(_respuesta(_texto('{"numero": "SECRETO-77"}'), stop_reason="max_tokens"))
    (aviso,) = _avisos(caplog)
    assert "SECRETO-77" not in aviso and "numero" not in aviso
    assert aviso.endswith("stop_reason=max_tokens")


def test_f086_r9_con_tool_use_no_hay_warning(caplog):
    caplog.set_level(logging.DEBUG, logger=modulo.logger.name)
    _extraer(_respuesta(NS(type="tool_use", name="emitir", input={"numero": "A-1"})))
    assert _avisos(caplog) == []


# --- R10 · sin tool_use ni JSON válido: ValueError con el stop_reason -------------


@pytest.mark.parametrize(
    ("bloques", "stop_reason"),
    [
        ((), "refusal"),
        ((_texto(""),), "end_turn"),
        ((_texto("no es json"),), "end_turn"),
        ((_texto('["numero", "A-1"]'),), "end_turn"),
        ((_texto('"A-1"'),), "end_turn"),
        ((_texto('{"otro": 1}'),), "max_tokens"),
        ((_texto('{"numero": "A-1", "sobra": 3}'),), "end_turn"),
        ((NS(type="thinking", thinking="pienso"),), "max_tokens"),
    ],
)
def test_f086_r10_valueerror_con_el_stop_reason(bloques, stop_reason):
    with pytest.raises(ValueError) as error:
        _extraer(_respuesta(*bloques, stop_reason=stop_reason))
    assert str(error.value) == (
        "Claude no devolvió tool_use ni JSON válido en la respuesta "
        f"(stop_reason={stop_reason})."
    )


def test_f086_r10_sin_stop_reason_dice_none():
    with pytest.raises(ValueError, match=r"\(stop_reason=None\)\.$"):
        _extraer(NS(content=None))


def test_f086_r10_el_call_logger_registra_parse_error():
    logger = _Logger()
    respuesta = _respuesta(_texto("no es json"), stop_reason="refusal")
    with pytest.raises(ValueError):
        _extraer(respuesta, logger)
    (llamada,) = logger.llamadas
    assert llamada["error"] == (
        "PARSE ERROR: ValueError: Claude no devolvió tool_use ni JSON válido en la "
        "respuesta (stop_reason=refusal)."
    )
    assert llamada["response_payload"] is respuesta


def test_f086_r10_sin_warning_de_exito(caplog):
    caplog.set_level(logging.DEBUG, logger=modulo.logger.name)
    with pytest.raises(ValueError):
        _extraer(_respuesta(_texto("no es json")))
    assert _avisos(caplog) == []


# --- R11 · el camino tool_use, como hoy -------------------------------------------


@pytest.mark.parametrize(
    "previos",
    [
        (),
        (NS(type="thinking", thinking="pienso"),),
        (_texto("Aquí va la valoración."), NS(type="thinking", thinking="x")),
        (_texto('{"numero": "DEL-TEXTO"}'),),
    ],
)
def test_f086_r11_tool_use_manda_aunque_haya_bloques_antes(previos):
    resultado = _extraer(_respuesta(
        *previos, NS(type="tool_use", name="emitir", input={"numero": "A-1"}),
        stop_reason="tool_use",
    ))
    assert resultado == _Salida(numero="A-1")


def test_f086_r11_tool_use_con_input_string_como_hoy():
    resultado = _extraer(_respuesta(
        NS(type="tool_use", name="emitir", input='{"numero": "A-1"}'), stop_reason="tool_use",
    ))
    assert resultado == _Salida(numero="A-1")
