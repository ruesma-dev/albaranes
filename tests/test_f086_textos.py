# tests/test_f086_textos.py
"""F-086 · R7 y R16: lo que dicen el código de sv2 y los documentos.

Se leen los ficheros como texto: ni se importa sv2 ni se ejecuta PowerShell.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SV2 = RAIZ / "services" / "albaranes-api"


def _codigo_de_sv2() -> dict[str, str]:
    """El código Python de producción de sv2 (sin tests ni entornos virtuales)."""
    return {
        ruta.relative_to(RAIZ).as_posix(): ruta.read_text(encoding="utf-8-sig")
        for ruta in SV2.rglob("*.py")
        if not {".venv", "tests", "__pycache__"} & set(ruta.relative_to(SV2).parts)
    }


# --- R7 · sv2 sigue forzando la herramienta --------------------------------------


def test_f086_r7_hay_codigo_de_sv2_que_revisar():
    codigo = _codigo_de_sv2()
    assert "services/albaranes-api/interface_adapters/composition.py" in codigo
    assert sum("ClaudeMessagesVisionClient(" in texto for texto in codigo.values()) >= 1


@pytest.mark.parametrize("palabra", ["forzar_herramienta", "ANTHROPIC_FORZAR_HERRAMIENTA"])
def test_f086_r7_sv2_no_pasa_forzar_herramienta(palabra):
    con_la_palabra = [ruta for ruta, texto in _codigo_de_sv2().items() if palabra in texto]
    assert con_la_palabra == [], (
        f"sv2 debe seguir con el defecto de comun (herramienta forzada): {con_la_palabra}"
    )


# --- R16 · la documentación dice que sv5 lee la variable ---------------------------

SV5_MD = RAIZ / "services" / "albaran-valoracion-api" / "sv5.md"
ARQUITECTURA = RAIZ / "docs" / "ARCHITECTURE.md"
SET_MODELS = RAIZ / "infra" / "set_models.ps1"
CREATE_CAPPS = RAIZ / "infra" / "create_capps.ps1"
README_CAPPS = RAIZ / "infra" / "README_capps.md"

#: Formas de «sv5 aún no la lee» que había antes de F-086.
AUN_NO_LA_LEE = re.compile(r"a[uú]n\s+(no|NO)\s+(la\s+)?lee|no se pone aqu[ií] hasta F-086")


def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8-sig")


def _documentos() -> dict[str, str]:
    return {
        "sv5.md": _texto(SV5_MD),
        "ARCHITECTURE.md": _texto(ARQUITECTURA).split("- **APIs LLM**")[1].split("\n- **")[0],
        "set_models.ps1 (ayuda)": _texto(SET_MODELS).split("param(")[0],
        "create_capps.ps1": _texto(CREATE_CAPPS),
        "README_capps.md": _texto(README_CAPPS),
    }


@pytest.mark.parametrize("documento", list(_documentos()))
def test_f086_r16_nombra_la_variable(documento):
    assert "ANTHROPIC_FORZAR_HERRAMIENTA" in _documentos()[documento]


@pytest.mark.parametrize("documento", list(_documentos()))
def test_f086_r16_ninguno_dice_que_aun_no_la_lee(documento):
    assert not AUN_NO_LA_LEE.search(_documentos()[documento]), documento


@pytest.mark.parametrize(
    "documento", ["sv5.md", "ARCHITECTURE.md", "set_models.ps1 (ayuda)", "create_capps.ps1"]
)
def test_f086_r16_un_claude_5_5_la_necesita_a_false(documento):
    texto = re.sub(r"\s+", " ", _documentos()[documento])
    assert re.search(r"Claude 5\.5 .{0,120}ANTHROPIC_FORZAR_HERRAMIENTA[`=]*\s*=?\s*`?false", texto), (
        documento
    )


def _fila(variable: str) -> list[str]:
    for linea in _texto(SV5_MD).splitlines():
        if linea.startswith(f"| `{variable}`"):
            return [celda.strip() for celda in linea.strip("|").split("|")]
    raise AssertionError(f"sv5.md no tiene fila de {variable}")


def test_f086_r16_sv5_md_fila_de_la_variable_con_defecto_true():
    assert _fila("ANTHROPIC_FORZAR_HERRAMIENTA")[1] == "`true`"


def test_f086_r16_sv5_md_timeout_es_el_de_settings():
    assert _fila("ANTHROPIC_TIMEOUT_S")[1] == "`120`"
    assert _fila("ANTHROPIC_MAX_TOKENS")[1] == "`8192`"
