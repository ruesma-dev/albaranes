# tests/test_f085_settings.py
"""F-085 · R8–R10: sv5 no arranca con IA3_PROVIDER / IA4_PROVIDER incoherentes.

Sin red ni BBDD: solo se construye ``Settings`` con valores explícitos, sin
``.env`` (``_env_file=None``) y con las variables del proceso borradas.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from config.settings import Settings

#: Variables del proceso que podrían colarse en ``Settings()`` (las de la
#: consola de quien lance la suite).
_VARIABLES = (
    "ENABLE_OPENAI", "ENABLE_GEMINI", "ENABLE_CLAUDE",
    "OPENAI_API_KEY", "GEMINI_API_KEY", "ANTHROPIC_API_KEY",
    "OPENAI_MODEL", "GEMINI_MODEL", "ANTHROPIC_MODEL",
    "IA3_PROVIDER", "IA4_PROVIDER", "PG_USER", "PG_PASSWORD", "GRAPH_KEY",
)


@pytest.fixture(autouse=True)
def _entorno_limpio(monkeypatch):
    for variable in _VARIABLES:
        monkeypatch.delenv(variable, raising=False)


def _settings(**entorno: str) -> Settings:
    base = {"PG_USER": "u", "PG_PASSWORD": "p", "GRAPH_KEY": "{}", "ANTHROPIC_API_KEY": "a"}
    base.update(entorno)
    return Settings(_env_file=None, **base)


#: Lo que el humano dejó en ``ca-sv5-valuation`` el 2026-10-20 (paso 1).
PASO_1 = {
    "ENABLE_OPENAI": "true",
    "OPENAI_API_KEY": "o",
    "OPENAI_MODEL": "gpt-6.1-sol",
    "IA3_PROVIDER": "openai",
    "IA4_PROVIDER": "openai",
}


# --- R8 -----------------------------------------------------------------------


@pytest.mark.parametrize("variable", ["IA3_PROVIDER", "IA4_PROVIDER"])
@pytest.mark.parametrize("valor", ["mistral", "open-ai", "claude4"])
def test_f085_r8_proveedor_desconocido_no_arranca(variable, valor):
    with pytest.raises(ValidationError) as error:
        _settings(**{variable: valor})
    texto = str(error.value)
    assert variable in texto and repr(valor) in texto
    assert "openai, gemini o claude" in texto


def test_f085_r8_ia4_se_valida_aunque_ia3_este_vacia():
    with pytest.raises(ValidationError, match="IA4_PROVIDER='mistral'"):
        _settings(IA3_PROVIDER="", IA4_PROVIDER="mistral")


def test_f085_r8_ia4_se_valida_aunque_ia3_sea_valida():
    with pytest.raises(ValidationError, match="IA4_PROVIDER='mistral'"):
        _settings(IA3_PROVIDER="claude", IA4_PROVIDER="mistral")


@pytest.mark.parametrize("valor", [" OpenAI ", "OPENAI", "openai\n"])
def test_f085_r8_se_normaliza_con_strip_y_minusculas(valor):
    settings = _settings(**{**PASO_1, "IA3_PROVIDER": valor, "IA4_PROVIDER": valor})
    assert settings.ia3_provider == valor  # se valida normalizado, se guarda tal cual


# --- R9 -----------------------------------------------------------------------


@pytest.mark.parametrize("variable", ["IA3_PROVIDER", "IA4_PROVIDER"])
@pytest.mark.parametrize(
    ("proveedor", "flag"),
    [("openai", "ENABLE_OPENAI"), ("gemini", "ENABLE_GEMINI")],
)
def test_f085_r9_proveedor_apagado_no_arranca(variable, proveedor, flag):
    with pytest.raises(ValidationError) as error:
        _settings(**{variable: proveedor})
    texto = str(error.value)
    assert variable in texto and flag in texto and "no está a true" in texto


@pytest.mark.parametrize("variable", ["IA3_PROVIDER", "IA4_PROVIDER"])
def test_f085_r9_claude_apagado_no_arranca(variable):
    with pytest.raises(ValidationError) as error:
        _settings(ENABLE_CLAUDE="false", ENABLE_OPENAI="true", OPENAI_API_KEY="o",
                  **{variable: "claude"})
    assert variable in str(error.value) and "ENABLE_CLAUDE" in str(error.value)


@pytest.mark.parametrize(
    ("proveedor", "entorno"),
    [
        ("openai", {"ENABLE_OPENAI": "true", "OPENAI_API_KEY": "o"}),
        ("gemini", {"ENABLE_GEMINI": "true", "GEMINI_API_KEY": "g"}),
        ("claude", {}),
    ],
)
def test_f085_r9_proveedor_encendido_arranca(proveedor, entorno):
    settings = _settings(IA3_PROVIDER=proveedor, IA4_PROVIDER=proveedor, **entorno)
    assert settings.ia3_provider == settings.ia4_provider == proveedor


def test_f085_r9_los_valores_del_paso_1_arrancan():
    settings = _settings(**PASO_1)
    assert settings.enabled_llm_providers == ["openai", "claude"]
    assert (settings.ia3_provider, settings.ia4_provider) == ("openai", "openai")
    assert settings.openai_model == "gpt-6.1-sol"


# --- R10 ----------------------------------------------------------------------


@pytest.mark.parametrize("valor", [None, "", "   "])
def test_f085_r10_vacias_arrancan_como_hoy(valor):
    entorno = {} if valor is None else {"IA3_PROVIDER": valor, "IA4_PROVIDER": valor}
    settings = _settings(**entorno)
    assert settings.enabled_llm_providers == ["claude"]
    assert settings.ia3_provider == settings.ia4_provider == valor


def test_f085_r10_vacias_con_varios_proveedores_arrancan():
    settings = _settings(ENABLE_OPENAI="true", OPENAI_API_KEY="o")
    assert settings.enabled_llm_providers == ["openai", "claude"]
    assert settings.ia3_provider is None and settings.ia4_provider is None


def test_f085_r10_las_validaciones_de_antes_siguen():
    with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
        _settings(ENABLE_OPENAI="true")
    with pytest.raises(ValidationError, match="Al menos un proveedor"):
        _settings(ENABLE_CLAUDE="false")
