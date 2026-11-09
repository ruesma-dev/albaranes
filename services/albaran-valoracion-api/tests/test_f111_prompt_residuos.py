# tests/test_f111_prompt_residuos.py
"""F-111 R12–R16 · el prompt de IA3 de residuos con la regla 3/6/9.

Test sobre el YAML REAL (``config/prompts.yaml``, el que carga sv5) y sobre el
histórico ``config/prompts/svc5_prompt_valuation_es.yaml`` (D1 = a). Sin red ni
LLM.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
PROMPTS_YAML = RAIZ_SERVICIO / "config" / "prompts.yaml"
HISTORICO_YAML = RAIZ_SERVICIO / "config" / "prompts" / "svc5_prompt_valuation_es.yaml"


@pytest.fixture(scope="module")
def prompt_residuos():
    return YamlPromptRepository(PROMPTS_YAML).get("valuation_residuos")


def _plano(texto: str) -> str:
    """Minúsculas y espacios simples (el YAML pliega líneas)."""
    return re.sub(r"\s+", " ", texto).lower()


def _texto(spec) -> str:
    return _plano(f"{spec.system}\n{spec.task}\n{spec.schema_hint}")


def _paso_4(spec) -> str:
    texto = _plano(spec.task)
    inicio = texto.find("4. tamano del contenedor")
    fin = texto.find("4-bis.")
    assert 0 < inicio < fin, "no se encuentra el paso 4 del prompt de residuos"
    return texto[inicio:fin]


# R12 · la regla de R1, R2, R6 y R7, sin el «6 por defecto»
def test_f111_r12_el_prompt_no_dice_6_por_defecto(prompt_residuos):
    texto = _texto(prompt_residuos)
    assert "6 m3 por defecto" not in texto
    assert "valor por defecto" not in texto
    assert "ante cualquier duda" not in texto
    assert "estandar y el valor" not in texto
    assert "contenedor estandar" not in _paso_4(prompt_residuos).replace(
        "contenedores estandar de 3, 6 o 9", ""
    )


def test_f111_r12_el_paso_4_describe_la_regla_3_6_9(prompt_residuos):
    paso = _paso_4(prompt_residuos)
    assert "3, 6 o 9" in paso
    assert "mas pequeno" in paso
    assert "ceil(volumen_m3 / 6)" in paso
    assert "no se mezclan" in paso
    # R6/R7: con tamaños del contrato, manda el contrato; si no caben, D2.
    assert "manda el contrato" in paso
    assert "paquetes de 6" in paso
    assert "del mayor" in paso


# R13 · contenedor_m3 = null si el contrato no da el tamaño
def test_f111_r13_contenedor_m3_null_sin_tamano_en_el_contrato(prompt_residuos):
    paso = _paso_4(prompt_residuos)
    assert "contenedor_m3 = null" in paso
    assert "otro servicio" in paso
    assert "no rellenes contenedor_m3" in paso


# R14 · con varios tamaños, casar la línea del tamaño elegido
def test_f111_r14_con_varios_tamanos_casa_la_linea_del_elegido(prompt_residuos):
    paso = _paso_4(prompt_residuos)
    assert "varios tamanos" in paso
    assert "casa la linea de ese tamano" in paso


# R4 · el precio sigue siendo el de la línea casada
def test_f111_r4_el_precio_es_el_de_la_linea_casada(prompt_residuos):
    paso = _paso_4(prompt_residuos)
    assert "precio general" in paso


# R16 · el histórico deja de decir «el por defecto»
def test_f111_r16_el_historico_no_dice_el_por_defecto():
    texto = _plano(HISTORICO_YAML.read_text(encoding="utf-8"))
    assert "el por defecto" not in texto
    assert "3, 6 o 9" in texto
