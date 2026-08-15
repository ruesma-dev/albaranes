# tests/test_f003_prompt_transcripcion.py
"""F-003 · Prompt de IA1: transcribir, no recomponer (R1).

Causa raiz del caso x120: el prompt ordenaba "precio_neto: si figura,
leelo; si no, calcula cantidad*precio*(1 - descuento/100)" — una formula
de IMPORTE TOTAL en un campo que aguas abajo se trata como precio
UNITARIO neto. Con 120,55 l y un importe impreso de 191,40 EUR, sv5
volvia a multiplicar por la cantidad: 23.073,60 EUR.

Estos tests leen el ``config/prompts.yaml`` REAL (el que se carga en
produccion, no una copia) y comprueban que la instruccion de calcular ha
DESAPARECIDO y que cada valor se pide por su etiqueta de columna.

Sin red ni LLM: solo lectura del YAML.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"
CLAVE_FASE_1 = "albaran_factura_es"
CLAVE_FASE_2 = "albaran_revision_fase2_es"


@pytest.fixture(scope="module")
def prompt_fase_1() -> str:
    """system + task + schema_hint del prompt REAL de IA1, en minusculas."""
    spec = YamlPromptRepository(PROMPTS_REALES).get(CLAVE_FASE_1)
    return f"{spec.system}\n{spec.task}\n{spec.schema_hint}".lower()


def _sin_espacios(texto: str) -> str:
    """Colapsa saltos de linea y espacios: el YAML pliega el texto y una
    regla puede partirse en dos lineas."""
    return " ".join(texto.split())


# ---------------------------------------------------------------------
# R1 · La instruccion de CALCULAR ha desaparecido
# ---------------------------------------------------------------------


def test_f003_r1_el_prompt_ya_no_manda_calcular_el_precio_neto(
    prompt_fase_1: str,
) -> None:
    """La formula que causo el x120 no puede seguir en el prompt."""
    plano = _sin_espacios(prompt_fase_1)

    assert "cantidad*precio*(1 - descuento/100)" not in plano
    assert "cantidad*precio*(1-descuento/100)" not in plano.replace(" ", "")


def test_f003_r1_el_prompt_prohibe_derivar_unos_valores_de_otros(
    prompt_fase_1: str,
) -> None:
    plano = _sin_espacios(prompt_fase_1)

    assert "prohibido" in plano
    assert "no calcules" in plano or "nunca calcules" in plano
    # Y dice explicitamente que lo que no figura va a null.
    assert "null" in plano


# ---------------------------------------------------------------------
# R1 · Cada valor, por su etiqueta de columna
# ---------------------------------------------------------------------


def test_f003_r1_el_prompt_tiene_el_bloque_de_albaranes_valorados(
    prompt_fase_1: str,
) -> None:
    plano = _sin_espacios(prompt_fase_1)

    assert "transcribir, no recomponer" in plano


def test_f003_r1_precio_solo_de_la_columna_de_precio_unitario(
    prompt_fase_1: str,
) -> None:
    plano = _sin_espacios(prompt_fase_1)

    assert "p.u." in plano or "precio unit" in plano


def test_f003_r1_importe_se_lee_de_la_columna_de_importe_de_linea(
    prompt_fase_1: str,
) -> None:
    plano = _sin_espacios(prompt_fase_1)

    assert "importe:" in plano
    # Las etiquetas reales de la columna de importe de linea.
    for etiqueta in ("importe", "total", "neto"):
        assert etiqueta in plano


def test_f003_r1_descuentos_se_transcriben_todos_y_en_orden(
    prompt_fase_1: str,
) -> None:
    plano = _sin_espacios(prompt_fase_1)

    assert "descuentos:" in plano
    assert "dto1" in plano or "dto 1" in plano
    assert "orden" in plano


def test_f003_r1_con_varios_descuentos_la_ia_deja_descuento_a_null(
    prompt_fase_1: str,
) -> None:
    """La IA jamas combina descuentos: la cascada la deriva sv3 (R3)."""
    plano = _sin_espacios(prompt_fase_1)

    assert "no los combines" in plano or "no combines" in plano


def test_f003_r1_precio_neto_solo_si_figura_impreso(
    prompt_fase_1: str,
) -> None:
    plano = _sin_espacios(prompt_fase_1)

    assert "precio_neto:" in plano
    assert "solo si" in plano or "sólo si" in plano


# ---------------------------------------------------------------------
# R1/R2 · Total del albaran en cabecera, con su marca de IVA
# ---------------------------------------------------------------------


def test_f003_r1_la_cabecera_pide_el_total_del_albaran(
    prompt_fase_1: str,
) -> None:
    plano = _sin_espacios(prompt_fase_1)

    assert "importe_total:" in plano
    assert "base imponible" in plano


def test_f003_r1_el_total_con_iva_se_transcribe_y_se_marca(
    prompt_fase_1: str,
) -> None:
    """Decision del humano 2026-08-13: nunca null por incluir IVA."""
    plano = _sin_espacios(prompt_fase_1)

    assert "importe_total_incluye_iva:" in plano
    assert "iva" in plano


# ---------------------------------------------------------------------
# La fase 2 hereda estas reglas por placeholder: no se toca
# ---------------------------------------------------------------------


def test_f003_r1_la_fase_2_sigue_heredando_la_fase_1_por_placeholder() -> None:
    spec = YamlPromptRepository(PROMPTS_REALES).get(CLAVE_FASE_2)

    assert "{prompt_fase_1}" in spec.task


def test_f003_r1_el_prompt_de_obras_de_f002_sigue_intacto(
    prompt_fase_1: str,
) -> None:
    """Regresion: F-003 no puede llevarse por delante lo de F-002."""
    plano = _sin_espacios(prompt_fase_1)

    assert "{obras_activas}" in plano
    assert "bloque fiscal" in plano
