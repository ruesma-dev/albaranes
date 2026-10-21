# tests/test_f085_wiring.py
"""F-085 · R10–R14: el wiring de proveedores de sv5, sin red, sin BBDD y sin LLM.

Las tres clases de cliente de los SDK se sustituyen por dobles sobre el módulo
``app`` (``monkeypatch``), que apuntan con qué se construyeron y a qué modelo
se les llamó. En la prueba de ``build_app`` también se sustituyen la BBDD,
SharePoint y el repositorio de prompts: nada abre conexión.
"""
from __future__ import annotations

import logging
import sys
import types

import pytest
from pydantic import BaseModel


def _fastapi_de_prueba() -> types.ModuleType:
    """Sustituto mínimo de ``fastapi`` para importar ``app.py``.

    El intérprete con que el arnés corre la suite de sv5 (el ``.venv`` de la
    raíz) no trae FastAPI, que solo vive en la imagen del servicio. Para estos
    tests basta con que ``FastAPI()`` acepte los decoradores de ruta: no se
    sirve ninguna petición. Con FastAPI instalado se usa el de verdad.
    """
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

from application.pipelines.value_albaran_pipeline import ValueAlbaranPipeline
from application.services.valuation_extraction_service import (
    ProviderClientSpec,
    ValuationExtractionService,
)
from config.settings import Settings
from domain.models.valuation_context import ContextoValoracion
from interface_adapters.api import app as modulo

_VARIABLES = (
    "ENABLE_OPENAI", "ENABLE_GEMINI", "ENABLE_CLAUDE",
    "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
    "OPENAI_MODEL", "GEMINI_MODEL", "ANTHROPIC_MODEL",
    "ANTHROPIC_MAX_TOKENS", "ANTHROPIC_TIMEOUT_S",
    "IA3_PROVIDER", "IA4_PROVIDER", "PG_USER", "PG_PASSWORD", "GRAPH_KEY",
)


class _Cliente:
    """Doble de un cliente LLM: apunta su construcción y cada llamada."""

    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.kwargs = kwargs
        self.llamadas: list[str] = []

    def extract_document(self, *, model, instructions, user_text, attachment, response_model):
        self.llamadas.append(model)
        return response_model()


class _Claude(_Cliente):
    pass


class _Gemini(_Cliente):
    pass


class _OpenAI(_Cliente):
    pass


@pytest.fixture(autouse=True)
def _dobles(monkeypatch):
    for variable in _VARIABLES:
        monkeypatch.delenv(variable, raising=False)
    monkeypatch.setattr(modulo, "ClaudeMessagesVisionClient", _Claude)
    monkeypatch.setattr(modulo, "GeminiGenAiVisionClient", _Gemini)
    monkeypatch.setattr(modulo, "OpenAIResponsesVisionClient", _OpenAI)


def _settings(**entorno: str) -> Settings:
    base = {"PG_USER": "u", "PG_PASSWORD": "p", "GRAPH_KEY": "{}", "ANTHROPIC_API_KEY": "a"}
    base.update(entorno)
    return Settings(_env_file=None, **base)


TRES = {
    "ENABLE_OPENAI": "true", "OPENAI_API_KEY": "o", "OPENAI_MODEL": "gpt-6.1-sol",
    "ENABLE_GEMINI": "true", "GEMINI_API_KEY": "g", "GEMINI_MODEL": "gemini-4-argon",
    "ANTHROPIC_MODEL": "claude-opus-4-8",
}

#: ``ca-sv5-valuation`` tras el paso 1 (2026-10-20).
PASO_1 = {
    "ENABLE_OPENAI": "true", "OPENAI_API_KEY": "o", "OPENAI_MODEL": "gpt-6.1-sol",
    "ANTHROPIC_MODEL": "claude-opus-4-8", "IA3_PROVIDER": "openai", "IA4_PROVIDER": "openai",
}

RETRY = object()
LOGGER = object()


def _construir(settings: Settings) -> list[ProviderClientSpec]:
    return modulo.construir_proveedores(settings, retry_policy=RETRY, call_logger=LOGGER)


def _spec(proveedor: str, modelo: str) -> ProviderClientSpec:
    return ProviderClientSpec(provider=proveedor, model_name=modelo, client=_Cliente())


# --- R14: construir_proveedores, función pura de wiring ---------------------------


def test_f085_r14_construye_los_tres_en_el_orden_de_siempre():
    proveedores = _construir(_settings(**TRES))
    assert [(p.provider, p.model_name, type(p.client)) for p in proveedores] == [
        ("claude", "claude-opus-4-8", _Claude),
        ("gemini", "gemini-4-argon", _Gemini),
        ("openai", "gpt-6.1-sol", _OpenAI),
    ]


def test_f085_r14_cada_cliente_con_los_argumentos_de_hoy():
    claude, gemini, openai = _construir(
        _settings(**TRES, ANTHROPIC_MAX_TOKENS="4096", ANTHROPIC_TIMEOUT_S="90")
    )
    assert claude.client.args == ()
    assert claude.client.kwargs == {
        "api_key": "a",
        "max_tokens": 4096,
        "timeout_s": 90,
        "retry_policy": RETRY,
        "call_logger": LOGGER,
        "tool_name": "emit_valuation_result",
        "tool_description": (
            "Devuelve la valoración estructurada de las líneas del albarán "
            "conforme al esquema exigido. Llama SIEMPRE y SOLO a esta herramienta."
        ),
    }
    assert gemini.client.args == ()
    assert gemini.client.kwargs == {"api_key": "g", "retry_policy": RETRY, "call_logger": LOGGER}
    assert openai.client.args == ("o",)
    assert openai.client.kwargs == {"retry_policy": RETRY, "call_logger": LOGGER}


def test_f085_r14_solo_los_habilitados():
    assert [p.provider for p in _construir(_settings())] == ["claude"]
    assert [p.provider for p in _construir(_settings(**PASO_1))] == ["claude", "openai"]
    solo_openai = _settings(ENABLE_CLAUDE="false", ENABLE_OPENAI="true", OPENAI_API_KEY="o")
    assert [p.provider for p in _construir(solo_openai)] == ["openai"]
    solo_gemini = _settings(ENABLE_CLAUDE="false", ENABLE_GEMINI="true", GEMINI_API_KEY="g")
    assert [p.provider for p in _construir(solo_gemini)] == ["gemini"]


# --- R13 / R10: IA4 ---------------------------------------------------------------


@pytest.mark.parametrize("valor", ["openai", " OpenAI ", "OPENAI"])
def test_f085_r13_ia4_openai_recibe_solo_openai(valor):
    proveedores = [_spec("claude", "claude-opus-4-8"), _spec("openai", "gpt-6.1-sol")]
    assert modulo.seleccionar_ia4(proveedores, valor) == [proveedores[1]]


@pytest.mark.parametrize("valor", [None, "", "  "])
def test_f085_r10_ia4_vacia_recibe_todos_y_manda_el_primero(valor):
    proveedores = [_spec("claude", "claude-opus-4-8"), _spec("openai", "gpt-6.1-sol")]
    assert modulo.seleccionar_ia4(proveedores, valor) == proveedores


def test_f085_r10_ia4_que_no_esta_cae_a_todos_como_hoy():
    # Settings ya no deja arrancar así (R9); la función conserva la semántica.
    proveedores = [_spec("claude", "claude-opus-4-8")]
    assert modulo.seleccionar_ia4(proveedores, "openai") == proveedores


# --- R13 / R10: IA3, llamadas y primario del sobre -----------------------------------


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
        class _Respuesta(BaseModel):
            lineas: list = []

        return _Respuesta


def _contexto() -> ContextoValoracion:
    return ContextoValoracion(
        document_id="doc-f085", codigo_contrato="C-1", nombre_contrato=None,
        cif_proveedor=None, nombre_proveedor=None, codigo_obra=None, nombre_obra=None,
        pdf_relative_path=None, pdf_filename=None, lineas_albaran=[], lineas_contrato=[],
    )


def _valorar(settings: Settings):
    proveedores = _construir(settings)
    servicio = ValuationExtractionService(
        providers=proveedores, prompt_repo=_Prompts(), schema_registry=_Esquemas(),
        prompt_key="valuation_es", ia3_provider=settings.ia3_provider,
    )
    resultados = servicio.extract(context=_contexto(), pdf_attachment=None)
    pipeline = ValueAlbaranPipeline(
        context_repository=None, pdf_downloader=None, prefilter=None,
        extraction_service=servicio, max_pdf_mb=10, ia3_provider=settings.ia3_provider,
        service_version="test",
    )
    sobre = pipeline._build_envelope(context=_contexto(), results=resultados, pdf_attachment=None)
    llamadas = {p.provider: p.client.llamadas for p in proveedores}
    return llamadas, sobre


def test_f085_r13_ia3_openai_llama_solo_a_openai_y_es_el_primario():
    llamadas, sobre = _valorar(_settings(**PASO_1))
    assert llamadas == {"claude": [], "openai": ["gpt-6.1-sol"]}
    assert sobre["meta"]["primary_provider"] == "openai"
    assert sobre["meta"]["model"] == "gpt-6.1-sol"
    assert sobre["meta"]["providers_used"] == ["openai"]


def test_f085_r10_ia3_vacia_llama_a_todos_y_manda_claude():
    llamadas, sobre = _valorar(_settings(**{**PASO_1, "IA3_PROVIDER": "", "IA4_PROVIDER": ""}))
    assert llamadas == {"claude": ["claude-opus-4-8"], "openai": ["gpt-6.1-sol"]}
    assert sobre["meta"]["primary_provider"] == "claude"
    assert sobre["meta"]["providers_used"] == ["claude", "openai"]


# --- build_app usa las funciones de wiring ---------------------------------------------------


class _Nada:
    def __init__(self, *args, **kwargs) -> None:
        pass


@pytest.fixture
def _sin_infra(monkeypatch):
    for nombre in ("SessionFactory", "SqlAlchemyValuationContextRepository",
                   "SharePointContratoPdfDownloader", "YamlPromptRepository"):
        monkeypatch.setattr(modulo, nombre, _Nada)


def _mensajes(caplog, nivel):
    return [r.getMessage() for r in caplog.records
            if r.name == modulo.logger.name and r.levelno == nivel]


def test_f085_r13_build_app_da_a_ia4_solo_openai(_sin_infra, monkeypatch):
    recibidos = {}

    class _Conciliacion:
        def __init__(self, *, providers, **kwargs):
            recibidos["ia4"] = [p.provider for p in providers]

    class _Extraccion:
        def __init__(self, *, providers, ia3_provider, **kwargs):
            recibidos["ia3"] = ([p.provider for p in providers], ia3_provider)

    monkeypatch.setattr(modulo, "ConciliacionService", _Conciliacion)
    monkeypatch.setattr(modulo, "ValuationExtractionService", _Extraccion)
    modulo.build_app(_settings(**PASO_1))
    assert recibidos == {"ia4": ["openai"], "ia3": (["claude", "openai"], "openai")}
