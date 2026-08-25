# tests/test_f036_r22_prompt_residuos_orden.py
"""F-036 R22 · el prompt de residuos documenta el ORDEN NUEVO.

El prompt `valuation_residuos` le explica a IA3 con que prioridad
calcula OTRO servicio (sv6) el numero de contenedores. Desde el
2026-08-19 ese orden es: 1) explicitos, 2) ceil(volumen / tamano),
3) resta llevadas - retiradas.

Si el prompt sigue describiendo el orden anterior, describe un sistema
que ya no existe: IA3 razona sobre una regla falsa y el proximo que lo
lea la dara por buena. Por eso R22 exige actualizarlo a la vez que
`residuos_container_calc.py` (T12), y por eso este test lo vigila.

Carga el YAML REAL de produccion con el repositorio REAL del servicio:
sin red y sin LLM, pero sin copia del texto.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.prompts.yaml_prompt_repository import (
    YamlPromptRepository,
)

RAIZ_SERVICIO = Path(__file__).resolve().parents[1]
PROMPTS_YAML = RAIZ_SERVICIO / "config" / "prompts.yaml"


@pytest.fixture(scope="module")
def prompt_residuos():
    return YamlPromptRepository(PROMPTS_YAML).get("valuation_residuos")


def _texto(spec) -> str:
    return f"{spec.system}\n{spec.task}".lower()


def test_f036_r22_el_prompt_nombra_las_tres_fuentes():
    """Ninguna de las tres desaparece: cambia el ORDEN, no la regla."""
    texto = _texto(YamlPromptRepository(PROMPTS_YAML).get("valuation_residuos"))

    assert "contexto_linea.contenedores" in texto
    assert "volumen_m3" in texto
    assert "contenedores_retirados" in texto


def test_f036_r22_el_prompt_pone_el_volumen_antes_que_la_resta(
    prompt_residuos,
):
    """El orden se lee por la POSICION de cada fuente en el texto."""
    texto = _texto(prompt_residuos)

    pos_explicitos = texto.find("contexto_linea.contenedores")
    pos_volumen = texto.find("ceil(volumen_m3")
    pos_resta = texto.find("contenedores_retirados")

    assert pos_explicitos > 0
    assert pos_volumen > 0, "el prompt no describe el calculo por volumen"
    assert pos_resta > 0, "el prompt no describe la resta"
    assert pos_explicitos < pos_volumen < pos_resta, (
        "el prompt no describe el orden de R22: "
        "explicitos -> volumen -> resta"
    )


def test_f036_r22_el_prompt_numera_el_volumen_como_prioridad_2(
    prompt_residuos,
):
    """Que la numeracion escrita coincida con el orden real."""
    texto = _texto(prompt_residuos)

    assert "2) ceil(volumen_m3" in texto
    assert "3) resta" in texto


def test_f036_r22_ia3_sigue_sin_calcular_el_numero_de_contenedores(
    prompt_residuos,
):
    """Reordenar la lista no puede ablandar la prohibicion.

    Quien calcula es sv6, de forma determinista; el bloque D3 de F-036
    (sinteticas por LER) se apoya en que IA3 NO lo haga.
    """
    texto = _texto(prompt_residuos)

    assert "tu no calculas ninguna de las tres" in texto
    assert "nunca calcules importes ni numero de contenedores" in texto
