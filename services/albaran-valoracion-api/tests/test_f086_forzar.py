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
from types import SimpleNamespace as NS

import pytest
from pydantic import BaseModel, ValidationError


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

from application.services.valuation_extraction_service import ValuationExtractionService
from config.settings import Settings
from domain.models.valuation_context import ContextoValoracion
from infrastructure.llm import claude_messages_client as reexport
from infrastructure.llm.retry_policy import RetryPolicy
from interface_adapters.api import app as modulo

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


# --- R3 · construir_proveedores pasa el valor al cliente -----------------------------


class _Cliente:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs


@pytest.fixture
def _dobles(monkeypatch):
    for nombre in ("ClaudeMessagesVisionClient", "GeminiGenAiVisionClient",
                   "OpenAIResponsesVisionClient"):
        monkeypatch.setattr(modulo, nombre, type(nombre, (_Cliente,), {}))


RETRY = object()
LOGGER = object()


def _claude_de(settings: Settings):
    (claude,) = [p for p in modulo.construir_proveedores(
        settings, retry_policy=RETRY, call_logger=LOGGER) if p.provider == "claude"]
    return claude


@pytest.mark.parametrize(("valor", "esperado"), [(None, True), ("true", True), ("false", False)])
def test_f086_r3_el_wiring_pasa_forzar_herramienta(_dobles, valor, esperado):
    entorno = {} if valor is None else {"ANTHROPIC_FORZAR_HERRAMIENTA": valor}
    claude = _claude_de(_settings(**PASO_1, **entorno))
    assert claude.client.kwargs["forzar_herramienta"] is esperado
    assert claude.client.kwargs["tool_name"] == TOOL_NAME_DE_HOY
    assert claude.client.kwargs["tool_description"] == TOOL_DESCRIPTION_DE_HOY


def test_f086_r3_las_constantes_de_la_herramienta_son_las_de_hoy():
    assert reexport.TOOL_NAME_VALORACION == TOOL_NAME_DE_HOY
    assert reexport.TOOL_DESCRIPTION_VALORACION == TOOL_DESCRIPTION_DE_HOY
    assert set(reexport.__all__) == {
        "ClaudeMessagesVisionClient", "TOOL_NAME_VALORACION", "TOOL_DESCRIPTION_VALORACION",
    }


def test_f086_r3_fuera_la_constante_de_f085():
    assert not hasattr(modulo, "FORZAR_HERRAMIENTA_CLAUDE")


# --- R4, R5 · lo que llega a messages.create -----------------------------------------


class _Salida(BaseModel):
    numero: str


class _Mensajes:
    def __init__(self, respuesta=None):
        self.llamadas: list[dict] = []
        self.respuesta = respuesta or NS(
            content=[NS(type="tool_use", name=TOOL_NAME_DE_HOY, input={"numero": "A-1"})],
            stop_reason="tool_use",
        )

    def create(self, **kwargs):
        self.llamadas.append(kwargs)
        return self.respuesta


class _Registro:
    def __init__(self):
        self.resumenes: list[dict] = []
        self.errores: list[str | None] = []

    def log_call(self, **kwargs):
        self.resumenes.append(dict(kwargs["request_summary"]))
        self.errores.append(kwargs["error"])


def _claude_real(settings: Settings, mensajes: _Mensajes, registro: _Registro):
    (claude,) = [p for p in modulo.construir_proveedores(
        settings, retry_policy=RetryPolicy(max_retries=0), call_logger=registro,
    ) if p.provider == "claude"]
    claude.client._client = NS(messages=mensajes)
    return claude


def _peticion(**entorno: str):
    mensajes, registro = _Mensajes(), _Registro()
    claude = _claude_real(_settings(**PASO_1, **entorno), mensajes, registro)
    resultado = claude.client.extract_document(
        model=claude.model_name, instructions="sistema", user_text="texto",
        response_model=_Salida,
    )
    assert resultado == _Salida(numero="A-1")
    (llamada,) = mensajes.llamadas
    (resumen,) = registro.resumenes
    return llamada, resumen


def test_f086_r4_sin_variable_la_peticion_es_la_de_hoy():
    llamada, resumen = _peticion()
    assert llamada == {
        "model": "claude-opus-4-8",
        "max_tokens": 8192,
        "system": "sistema",
        "tools": [{
            "name": TOOL_NAME_DE_HOY,
            "description": TOOL_DESCRIPTION_DE_HOY,
            "input_schema": {
                "properties": {"numero": {"type": "string"}},
                "required": ["numero"],
                "type": "object",
            },
        }],
        "tool_choice": {"type": "tool", "name": TOOL_NAME_DE_HOY},
        "messages": [{"role": "user", "content": [{"type": "text", "text": "texto"}]}],
    }
    assert resumen["response_format"] == "tool_use forced"


def test_f086_r4_true_es_identico_a_sin_variable():
    assert _peticion(ANTHROPIC_FORZAR_HERRAMIENTA="true") == _peticion()


def test_f086_r5_false_pide_auto():
    sin_forzar, resumen = _peticion(ANTHROPIC_FORZAR_HERRAMIENTA="false")
    forzada, _ = _peticion()
    assert sin_forzar["tool_choice"] == {"type": "auto"}
    assert {k: v for k, v in sin_forzar.items() if k != "tool_choice"} == {
        k: v for k, v in forzada.items() if k != "tool_choice"
    }
    assert resumen["response_format"] == "tool_use auto"


# --- R6 · la línea de wiring con el valor leído ---------------------------------------


class _Nada:
    def __init__(self, *args, **kwargs) -> None:
        pass


@pytest.fixture
def _sin_infra(monkeypatch):
    for nombre in ("SessionFactory", "SqlAlchemyValuationContextRepository",
                   "SharePointContratoPdfDownloader", "YamlPromptRepository"):
        monkeypatch.setattr(modulo, nombre, _Nada)


def _lineas_info(caplog) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.name == modulo.logger.name and r.levelno == logging.INFO]


@pytest.mark.parametrize(("valor", "texto"), [(None, "True"), ("true", "True"), ("false", "False")])
def test_f086_r6_build_app_escribe_el_valor_leido(_dobles, _sin_infra, caplog, valor, texto):
    caplog.set_level(logging.INFO, logger=modulo.logger.name)
    entorno = {} if valor is None else {"ANTHROPIC_FORZAR_HERRAMIENTA": valor}
    modulo.build_app(_settings(**PASO_1, **entorno))
    assert (
        "[svc5][wiring] IA3=openai/gpt-6.1-sol IA4=openai/gpt-6.1-sol "
        f"forzar_herramienta={texto}"
    ) in _lineas_info(caplog)


# --- R12 · el ValueError del cliente llega sin envolver y la API responde 400 ---------


class _Spec:
    system = "s"
    task = "t"
    schema_hint = "h"
    schema = "esquema"


class _Prompts:
    def get(self, clave):
        return _Spec()

    def has(self, clave):
        return False


class _Esquemas:
    def get(self, nombre):
        return _Salida


def _contexto() -> ContextoValoracion:
    return ContextoValoracion(
        document_id="doc-f086", codigo_contrato="C-1", nombre_contrato=None,
        cif_proveedor=None, nombre_proveedor=None, codigo_obra=None, nombre_obra=None,
        pdf_relative_path=None, pdf_filename=None, lineas_albaran=[], lineas_contrato=[],
    )


MENSAJE_R10 = (
    "Claude no devolvió tool_use ni JSON válido en la respuesta (stop_reason=refusal)."
)


def _error_del_servicio() -> ValueError:
    respuesta = NS(content=[NS(type="text", text="no puedo")], stop_reason="refusal")
    registro = _Registro()
    claude = _claude_real(
        _settings(**{**PASO_1, "IA3_PROVIDER": "claude", "ANTHROPIC_FORZAR_HERRAMIENTA": "false"}),
        _Mensajes(respuesta), registro,
    )
    servicio = ValuationExtractionService(
        providers=[claude], prompt_repo=_Prompts(), schema_registry=_Esquemas(),
        prompt_key="valuation_es", ia3_provider="claude",
    )
    with pytest.raises(ValueError) as error:
        servicio.extract(context=_contexto(), pdf_attachment=None)
    assert registro.errores == [f"PARSE ERROR: ValueError: {MENSAJE_R10}"]
    return error.value


def test_f086_r12_el_servicio_no_transforma_el_valueerror():
    error = _error_del_servicio()
    assert type(error) is ValueError
    assert str(error) == MENSAJE_R10


class _HTTPException(Exception):
    def __init__(self, status_code: int, detail: str = "") -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class _FastAPI:
    """Apunta las rutas para poder llamar a sus funciones sin servidor."""

    def __init__(self, **kwargs) -> None:
        self.rutas: dict[tuple[str, str], object] = {}

    def get(self, ruta):
        return self._ruta("GET", ruta)

    def post(self, ruta):
        return self._ruta("POST", ruta)

    def _ruta(self, metodo, ruta):
        def registrar(funcion):
            self.rutas[(metodo, ruta)] = funcion
            return funcion
        return registrar


def test_f086_r12_la_api_responde_400_con_el_mensaje(_sin_infra, monkeypatch):
    error = _error_del_servicio()

    class _Pipeline:
        def __init__(self, **kwargs) -> None:
            pass

        def run(self, peticion):
            raise error

    monkeypatch.setattr(modulo, "FastAPI", _FastAPI)
    monkeypatch.setattr(modulo, "HTTPException", _HTTPException)
    monkeypatch.setattr(modulo, "ValueAlbaranPipeline", _Pipeline)
    app = modulo.build_app(_settings(**PASO_1))
    valorar = app.rutas[("POST", "/v1/albaranes/value")]
    with pytest.raises(_HTTPException) as respuesta:
        valorar(modulo.ValueRequestBody(document_id="doc-f086"))
    assert respuesta.value.status_code == 400
    assert respuesta.value.detail == MENSAJE_R10
    assert respuesta.value.__cause__ is error
