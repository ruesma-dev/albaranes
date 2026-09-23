# tests/test_f048_r16_prompt_yaml.py
"""F-048 · R15 y R16: lo que el ``config/prompts.yaml`` REAL le pide a IA1.

- El task de fase 1 lleva el marcador ``{contexto_correo}`` UNA vez, junto a
  la seccion de obras (R12).
- Del correo SOLO se lee la obra, nunca la partida (R16, D8).
- La obra del PAPEL se sigue leyendo o deduciendo SIEMPRE, traiga o no obra
  el correo, y no se copia en la cabecera el codigo del correo: son dos
  lecturas que cruza sv2 (R16, D3).
- IA1 devuelve ``lectura_correo`` con ``obra_codigos`` y la ``evidencia``
  como fragmento corto, de 160 caracteres como mucho (R15; menor 7 de la
  review del bloque A: el texto del correo no se copia entero).
- El ``schema_hint`` declara ``lectura_correo.obra_codigos``.

Que la IA obedezca es otra evidencia: evals con LLM real (T40, ruta
sensible, la autoriza el humano). Sin red ni LLM.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from application.services.albaran_extraction_service import (
    AlbaranExtractionService,
    ProviderClientSpec,
)
from application.services.schema_registry import SchemaRegistry
from domain.models.albaran_models import DocumentoAlbaran
from infrastructure.prompts.revision_rules_repository import RevisionRulesRepository
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository
from ruesma_comun.correo import (
    NOTA_SIN_CORREO,
    construir_contexto_correo,
    render_bloque_correo,
)

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
REGLAS_REALES = RAIZ / "config" / "revision_rules.yaml"
CLAVE_FASE_1 = "albaran_factura_es"
MARCADOR = "{contexto_correo}"


def _spec(clave: str = CLAVE_FASE_1):
    return YamlPromptRepository(yaml_path=PROMPTS_REALES).get(clave)


def _plano(texto: str) -> str:
    """Sin saltos ni dobles espacios y en minusculas: el YAML es plegado."""
    return " ".join(texto.split()).lower()


def test_f048_r12_el_task_real_de_fase_1_lleva_el_marcador_una_vez_junto_a_las_obras():
    task = _spec().task

    assert task.count(MARCADOR) == 1
    assert (
        task.index("## Obras entre las que elegir")
        < task.index(MARCADOR)
        < task.index("## Reglas generales para las líneas")
    )


@pytest.mark.parametrize(
    "frase",
    [
        # R16 / D8: del correo, solo la obra.
        "del correo solo se lee el código de obra",
        "nunca la partida",
        # R16 / D3: la obra del papel, siempre y aparte.
        "se lee o se deduce del albarán siempre",
        "traiga o no obra el correo",
        "no copies en cabecera.obra_codigo el código del correo",
        # R15: el bloque de salida.
        "devuelve siempre el bloque lectura_correo",
        "obra_codigos",
        # Menor 7 (review del bloque A): evidencia corta.
        "solo el fragmento corto del correo donde aparece el código",
        "como mucho 160 caracteres",
    ],
)
def test_f048_r16_el_task_real_dice_las_frases_clave(frase):
    assert frase in _plano(_spec().task)


def test_f048_r15_el_schema_hint_real_declara_lectura_correo():
    hint = _plano(_spec().schema_hint)

    assert "lectura_correo.obra_codigos" in hint
    assert "cabecera.obra_codigo" in hint


def test_f048_r14_ningun_otro_prompt_del_yaml_lleva_el_marcador():
    """Solo el task de fase 1: la fase 2 lo recibe dentro de ``{prompt_fase_1}``."""
    crudo = yaml.safe_load(PROMPTS_REALES.read_text(encoding="utf-8"))

    con_marcador = [
        f"{clave}.{campo}"
        for clave, valor in crudo.items()
        for campo, texto in (valor or {}).items()
        if isinstance(texto, str) and MARCADOR in texto
    ]

    assert con_marcador == [f"{CLAVE_FASE_1}.task"]


class _ClienteEspia:
    def __init__(self) -> None:
        self.instructions = ""

    def extract_document(self, *, model, instructions, user_text, attachments, response_model):
        self.instructions = instructions
        return DocumentoAlbaran(cabecera={}, lineas=[])


@pytest.mark.parametrize("con_correo", [True, False], ids=["con_correo", "sin_correo"])
def test_f048_r12_el_prompt_real_renderizado_lleva_el_bloque_o_la_nota(con_correo):
    correo = construir_contexto_correo("Albaran obra 0945", "Va para la 0945. CENTINELA-F048") if con_correo else None
    cliente = _ClienteEspia()
    AlbaranExtractionService(
        providers=[ProviderClientSpec(provider="gemini", model_name="fake", client=cliente)],
        prompt_repo=YamlPromptRepository(yaml_path=PROMPTS_REALES),
        schema_registry=SchemaRegistry(),
        revision_rules_repo=RevisionRulesRepository(yaml_path=REGLAS_REALES),
        prompt_key_phase_1=CLAVE_FASE_1,
    ).extract_phase_1(attachments=[], provider="gemini", prompt_key=CLAVE_FASE_1, contexto_correo=correo)

    assert MARCADOR not in cliente.instructions
    esperado = render_bloque_correo(correo) if con_correo else NOTA_SIN_CORREO
    assert esperado in cliente.instructions
