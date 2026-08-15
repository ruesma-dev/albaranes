# tests/test_f003_prompts_match_estricto.py
"""F-003 · Matching estricto en los prompts de IA3 e IA4 (R9, R10).

Un atributo sustantivo distinto —dimension, modelo, tipo, formato de
venta— significa producto distinto. La red determinista de sv6 solo
alcanza los atributos NUMERICOS con unidad; los modelos y nombres
(ladrillos CETOSA, «BOLSA DE CUNAS») dependen de estos prompts.

La maxima de negocio, escrita en el prompt para que la IA la aplique:
mejor una linea nueva SIN precio a revision que un precio equivocado con
apariencia de bueno.

Se lee el ``config/prompts.yaml`` REAL (el que carga el servicio); la
copia de config/prompts/ no esta cargada y no se toca.

Sin red ni LLM.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS_REALES = RAIZ / "config" / "prompts.yaml"


def _texto(clave: str) -> str:
    spec = YamlPromptRepository(PROMPTS_REALES).get(clave)
    plano = f"{spec.system}\n{spec.task}\n{spec.schema_hint}".lower()
    return " ".join(plano.split())


@pytest.fixture(scope="module")
def ia3() -> str:
    return _texto("valuation_es")


@pytest.fixture(scope="module")
def ia4() -> str:
    return _texto("conciliacion_es")


# ---------------------------------------------------------------------
# R9 · IA3 (valuation_es)
# ---------------------------------------------------------------------


def test_f003_r9_ia3_tiene_la_regla_de_atributo_sustantivo(ia3: str) -> None:
    assert "atributo sustantivo" in ia3


def test_f003_r9_ia3_enumera_los_tipos_de_atributo(ia3: str) -> None:
    for atributo in ("espesor", "modelo", "material", "formato de venta"):
        assert atributo in ia3


def test_f003_r9_ia3_trae_el_caso_de_los_ladrillos(ia3: str) -> None:
    assert "cetosa" in ia3


def test_f003_r9_ia3_trae_el_caso_del_elemento_base(ia3: str) -> None:
    assert "elemento base" in ia3
    assert "0,5 mm" in ia3


def test_f003_r9_ia3_trae_el_caso_de_la_bolsa_de_cunas(ia3: str) -> None:
    assert "bolsa de cu" in ia3


def test_f003_r9_ia3_dice_la_maxima_de_negocio(ia3: str) -> None:
    assert "mejor una l" in ia3 and "sin precio" in ia3


def test_f003_r9_ia3_conserva_la_excepcion_tipografica(ia3: str) -> None:
    """La regla no se endurece con el formato: D-300 sigue siendo D300."""
    assert "d-300" in ia3
    assert "d300" in ia3


def test_f003_r9_ia3_conserva_los_casos_previos(ia3: str) -> None:
    """Regresion: la seccion existente no se pierde al ampliarla."""
    for caso in ("ha-25/b/20", "b500s", "mortero m-5", "gas"):
        assert caso in ia3


# ---------------------------------------------------------------------
# R10 · IA4 (conciliacion_es)
# ---------------------------------------------------------------------


def test_f003_r10_ia4_tiene_la_regla_dura_de_atributo(ia4: str) -> None:
    assert "regla dura de atributo sustantivo" in ia4


def test_f003_r10_ia4_prohibe_casar_por_parecido_textual(ia4: str) -> None:
    assert "parecido" in ia4
    assert "no_match" in ia4


def test_f003_r10_ia4_trae_los_casos_de_referencia(ia4: str) -> None:
    assert "elemento base" in ia4
    assert "cu" in ia4  # bolsa de cunas


def test_f003_r10_ia4_conserva_la_regla_dura_de_anos(ia4: str) -> None:
    """Regresion: la regla de años (jul 2026) sigue en pie."""
    assert "regla dura de a" in ia4
    assert "2025" in ia4


def test_f003_r10_ia4_conserva_la_tolerancia_por_significado(ia4: str) -> None:
    """No se puede endurecer hasta romper el match por sinonimos: la
    partida y el precio siguen sin bloquear."""
    assert "el precio no bloquea" in ia4
    assert "la partida no bloquea" in ia4


# ---------------------------------------------------------------------
# El prompt muerto de config/prompts/ NO se toca
# ---------------------------------------------------------------------


def test_f003_r9_la_copia_no_cargada_sigue_sin_tocarse() -> None:
    copia = RAIZ / "config" / "prompts" / "svc5_prompt_valuation_es.yaml"
    if not copia.exists():
        pytest.skip("la copia antigua ya no existe")

    assert "atributo sustantivo" not in copia.read_text(
        encoding="utf-8"
    ).lower()
