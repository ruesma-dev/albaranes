# tests/test_f075_pie_ia1.py
"""F-075 R13, R14 · IA1 lee el pie del albarán y sv2 no lo pierde en la fase 2.

- R13: ``CabeceraAlbaran`` lleva ``base_imponible``, ``tipo_iva_pct``,
  ``cuota_iva`` y ``total_albaran`` (``null`` si no figuran); el prompt de IA1
  tiene la sección «## Pie del albarán», aparte de las reglas de proveedor de
  F-064, y los de fase 2 la reciben por ``{prompt_fase_1}``.
- R14: si la fase 2 devuelve el pie nulo y la fase 1 lo traía, se conserva el
  de la fase 1.

Se comprueba el texto que recibe el LLM y el esquema; que la IA acierte lo
miden los evals (T17, MANUAL). Sin red ni LLM.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from application.services.phase_merge import construir_envelope_final
from domain.models.albaran_models import CabeceraAlbaran, DocumentoAlbaran

RAIZ = Path(__file__).resolve().parents[1]
PROMPTS = yaml.safe_load((RAIZ / "config" / "prompts.yaml").read_text(encoding="utf-8"))
PIE = ("base_imponible", "tipo_iva_pct", "cuota_iva", "total_albaran")
FASE_1 = "albaran_factura_es"
FASES_2 = ("albaran_revision_fase2_es", "albaran_revision_fase2_residuos",
           "albaran_revision_fase2_hormigon", "albaran_revision_fase2_mortero")


def _plano(texto: str) -> str:
    return " ".join(texto.split())


# ------------------------------------------------------------------ #
# R13 · esquema
# ------------------------------------------------------------------ #
def test_f075_r13_cabecera_con_los_cuatro_campos_del_pie():
    cab = CabeceraAlbaran(base_imponible=100.0, tipo_iva_pct=21, cuota_iva=21.0, total_albaran=121.0)
    assert [getattr(cab, c) for c in PIE] == [100.0, 21.0, 21.0, 121.0]
    assert all(getattr(CabeceraAlbaran(), c) is None for c in PIE)


def test_f075_r13_el_esquema_del_llm_los_lleva_y_admite_null():
    esquema = DocumentoAlbaran.model_json_schema()
    cabecera = esquema["$defs"]["CabeceraAlbaran"]["properties"]
    for campo in PIE:
        tipos = {t.get("type") for t in cabecera[campo].get("anyOf", [cabecera[campo]])}
        assert tipos == {"number", "null"}, (campo, cabecera[campo])


def test_f075_r13_el_esquema_de_la_fase_2_tambien():
    from domain.models.revision_models import RevisionAlbaranFase2

    texto = str(RevisionAlbaranFase2.model_json_schema())
    for campo in PIE:
        assert campo in texto


# ------------------------------------------------------------------ #
# R13 · prompt
# ------------------------------------------------------------------ #
def _seccion_pie(task: str) -> str:
    m = re.search(r"## Pie del albarán\n(.*?)(?=\n    ## |\n## |\Z)", task, re.S)
    assert m, "no está la sección «## Pie del albarán»"
    return _plano(m.group(1))


def test_f075_r13_ia1_tiene_la_seccion_del_pie():
    seccion = _seccion_pie(PROMPTS[FASE_1]["task"])
    for campo in PIE:
        assert campo in seccion
    assert "tal y como están impresas" in seccion
    assert "suma las bases y las cuotas y deja tipo_iva_pct a null" in seccion
    assert "No los calcules ni los deduzcas unos de otros" in seccion
    assert "si una cifra no está impresa, null" in seccion
    assert "suma y sigue" in seccion and "subtotal de página" in seccion
    assert "también en los albaranes que el proveedor ya trae valorados" in seccion
    assert "nunca como línea" in seccion


def test_f075_r13_la_seccion_va_tras_la_cabecera_y_antes_de_las_lineas():
    task = PROMPTS[FASE_1]["task"]
    assert task.index("## Reglas para la cabecera") < task.index("## Pie del albarán")
    assert task.index("## Pie del albarán") < task.index("## Reglas generales para las líneas")


def test_f075_r13_no_toca_las_reglas_de_proveedor_de_f064():
    """La sección del pie es aparte: las viñetas de proveedor siguen intactas."""
    cabecera = PROMPTS[FASE_1]["task"]
    cabecera = cabecera[cabecera.index("## Reglas para la cabecera"):cabecera.index("## Obras entre las que elegir")]
    assert "base_imponible" not in cabecera and "Pie" not in cabecera
    assert cabecera.count("{empresas_cliente}") == 1


@pytest.mark.parametrize("clave", FASES_2)
def test_f075_r13_la_fase_2_la_recibe_por_prompt_fase_1(clave):
    assert "{prompt_fase_1}" in PROMPTS[clave]["task"]
    assert "## Pie del albarán" not in PROMPTS[clave]["task"]  # una sola fuente


# ------------------------------------------------------------------ #
# R14 · la fase 2 no pierde el pie
# ------------------------------------------------------------------ #
def _env(cabecera, fase=1):
    documento = {"cabecera": cabecera, "lineas": []}
    if fase == 1:
        return {"meta": {"prompt_key": FASE_1}, "data": documento}
    return {"meta": {"prompt_key": "albaran_revision_fase2_es"},
            "data": {"documento_revisado": documento, "razonamientos": []}}


def test_f075_r14_fase_2_con_el_pie_nulo_conserva_el_de_fase_1():
    pie1 = {"base_imponible": 100.0, "tipo_iva_pct": 21.0, "cuota_iva": 21.0, "total_albaran": 121.0}
    final = construir_envelope_final(
        env_fase1=_env({"proveedor_nombre": "DISCOIN", **pie1}),
        env_fase2=_env({"proveedor_nombre": "DISCOIN S.L.", **{c: None for c in PIE}}, fase=2),
    )
    cab = final["data"]["cabecera"]
    assert {c: cab[c] for c in PIE} == pie1
    assert cab["proveedor_nombre"] == "DISCOIN S.L."  # lo demás, el de fase 2


def test_f075_r14_fase_2_sin_las_claves_del_pie_tambien_conserva():
    final = construir_envelope_final(
        env_fase1=_env({"base_imponible": 100.0}),
        env_fase2=_env({"proveedor_nombre": "X"}, fase=2),
    )
    assert final["data"]["cabecera"]["base_imponible"] == 100.0


def test_f075_r14_fase_2_con_algun_campo_del_pie_manda_la_fase_2():
    final = construir_envelope_final(
        env_fase1=_env({"base_imponible": 100.0, "total_albaran": 121.0}),
        env_fase2=_env({"base_imponible": 99.0, "tipo_iva_pct": None, "cuota_iva": None,
                        "total_albaran": None}, fase=2),
    )
    cab = final["data"]["cabecera"]
    assert cab["base_imponible"] == 99.0 and cab["total_albaran"] is None


def test_f075_r14_sin_fase_2_ni_pie_nada_cambia():
    final = construir_envelope_final(env_fase1=_env({"proveedor_nombre": "X"}))
    assert "base_imponible" not in final["data"]["cabecera"]
    final = construir_envelope_final(
        env_fase1=_env({"proveedor_nombre": "X"}),
        env_fase2=_env({"proveedor_nombre": "Y"}, fase=2),
    )
    assert all(final["data"]["cabecera"].get(c) is None for c in PIE)


def test_f075_r14_no_muta_el_envelope_persistido_de_fase_2():
    env2 = _env({"proveedor_nombre": "Y"}, fase=2)
    construir_envelope_final(env_fase1=_env({"base_imponible": 1.0}), env_fase2=env2)
    assert "base_imponible" not in env2["data"]["documento_revisado"]["cabecera"]
