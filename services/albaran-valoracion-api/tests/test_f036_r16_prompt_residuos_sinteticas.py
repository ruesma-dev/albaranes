# tests/test_f036_r16_prompt_residuos_sinteticas.py
"""F-036 R16 · el prompt de residuos dice QUIEN emite el incremento LER.

El prompt `valuation_residuos` prohibe a IA3 emitir lineas sinteticas
en residuos, y esa prohibicion SE MANTIENE: el numero de contenedores y
el incremento no los calcula una IA. Pero desde F-036 sv6 SI inyecta de
forma determinista el incremento por codigo LER, y un prompt que no lo
diga describe un sistema que ya no es el real: el proximo que lo lea
entendera que ese recargo no lo pone nadie (que es justo lo que pasaba
hasta ahora, medido en SS-0000589: 120 EUR contra 171).

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


def test_f036_r16_la_prohibicion_de_emitir_sinteticas_sigue_en_pie(
    prompt_residuos,
):
    """Lo que F-036 anade es una aclaracion, no un permiso.

    Si esta prohibicion se ablanda, IA3 empieza a inventar recargos y
    la red determinista de sv6 pasa a duplicarlos.
    """
    assert "NO emitas sinteticas" in prompt_residuos.task
    assert "NO emitas sinteticas" in prompt_residuos.schema_hint
    assert (
        "NO se emiten lineas sinteticas" in prompt_residuos.system
    )


def test_f036_r16_el_prompt_dice_que_el_incremento_ler_lo_inyecta_sv6(
    prompt_residuos,
):
    """Las tres partes del prompt nombran al responsable real."""
    for parte in (
        prompt_residuos.system,
        prompt_residuos.task,
        prompt_residuos.schema_hint,
    ):
        texto = parte.lower()
        assert "incremento por codigo ler" in texto, parte[:120]
        assert "sv6" in texto, parte[:120]
        assert "determinista" in texto, parte[:120]


def test_f036_r16_el_prompt_aclara_que_ia3_no_lo_emite_el_tampoco(
    prompt_residuos,
):
    """Que lo inyecte otro no puede leerse como "emitelo tu tambien"."""
    texto = f"{prompt_residuos.system}\n{prompt_residuos.task}".lower()

    posicion = texto.find("incremento por codigo ler")
    assert posicion > 0
    # En el mismo parrafo, la orden explicita de no emitirlo.
    assert "tu no lo emitas" in texto[posicion:posicion + 400]
