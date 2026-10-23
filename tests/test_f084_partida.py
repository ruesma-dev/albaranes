# tests/test_f084_partida.py
"""F-084 · D5 (aprobada por el humano el 2026-10-23) — la partida del albarán.

R38: `codigo_partida_final` no es observable en IA3. La pone sv6 desde la
partida del albarán, no sv5, así que sale de la comparación de IA3, consta en
«Campos no observables» y no cuenta en R28. En E2E (`partida_final`) sigue.

R39: una línea de INPUTS sin `codigo_imputacion` recibe la que el libro IA1
espera para esa línea (mismo caso y `num_linea`), como en producción, donde la
lee IA1 y llega a sv5 y a sv6 por el merge. INPUTS manda si la trae; `?` y
`REVISIÓN` del libro IA1 no son una partida.

Sin red ni BBDD (R25): sv6 por su subproceso, sin llamadas.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

from evals import runner
from evals.conversor import RUTA_FIXTURES
from evals.modelos import ESPERA_REVISION, NO_COMPARAR
from evals.procesos import sv5_valoracion, sv6_build


def _inputs(*lineas: dict) -> dict:
    return {"caso_id": "FER-900", "tablas": {"lineas_albaran": list(lineas)}}


def _ia1(*lineas: dict) -> dict:
    return {"caso_id": "FER-900", "tablas": {"lineas": list(lineas)}}


# --- R38 · codigo_partida_final, no observable en IA3 ---------------------------


def test_f084_r38_codigo_partida_final_no_es_observable_en_ia3():
    assert "codigo_partida_final" not in sv6_build.OBSERVABLES["lineas_valoradas"]
    assert "partida_final" in sv6_build.OBSERVABLES["lineas"]


def test_f084_r38_el_determinista_no_compara_la_partida_en_ia3_y_la_declara():
    fases, no_observables = runner.corrida_determinista(RUTA_FIXTURES, ["FER-001", "COM-001"])

    ia3 = next(f for f in fases if f.nombre == "IA3")
    assert not [d for c in ia3.casos for d in c.discrepancias if "codigo_partida_final" in d.campo]
    assert "codigo_partida_final" in no_observables


# --- R39 · la partida que lee IA1 llega a INPUTS ----------------------------------


def test_f084_r39_la_linea_sin_partida_recibe_la_del_libro_ia1():
    inputs = _inputs({"num_linea": 1, "descripcion": "Papel", "codigo_imputacion": None},
                     {"num_linea": 2.0, "descripcion": "jabón ", "codigo_imputacion": ""})
    ia1 = _ia1({"num_linea": 1.0, "descripcion_esperada": "papel", "codigo_imputacion": "CI.4.18"},
               {"num_linea": 2, "descripcion_esperada": "JABÓN", "codigo_imputacion": "P5.36.01"})

    resultado = sv6_build.con_partidas_de_ia1(inputs, ia1)

    assert [l["codigo_imputacion"] for l in resultado["tablas"]["lineas_albaran"]] == [
        "CI.4.18", "P5.36.01"]


def test_f084_r39_inputs_manda_si_trae_la_partida():
    inputs = _inputs({"num_linea": 1, "descripcion": "papel", "codigo_imputacion": "CI.1.1"})
    ia1 = _ia1({"num_linea": 1, "descripcion_esperada": "papel", "codigo_imputacion": "CI.4.18"})

    resultado = sv6_build.con_partidas_de_ia1(inputs, ia1)

    assert resultado["tablas"]["lineas_albaran"][0]["codigo_imputacion"] == "CI.1.1"


def test_f084_r39_sin_valor_afirmado_en_ia1_no_se_inventa_partida():
    inputs = _inputs(*({"num_linea": n, "descripcion": "papel", "codigo_imputacion": None}
                       for n in (1, 2, 3, 4, 5)))
    ia1 = _ia1(*({"descripcion_esperada": "papel", **fila} for fila in (
        {"num_linea": 1, "codigo_imputacion": NO_COMPARAR},
        {"num_linea": 2, "codigo_imputacion": ESPERA_REVISION},
        {"num_linea": 3, "codigo_imputacion": None},
        {"num_linea": None, "codigo_imputacion": "CI.9.9"},
        {"num_linea": 9, "codigo_imputacion": "CI.9.9"})))

    resultado = sv6_build.con_partidas_de_ia1(inputs, ia1)

    assert [l["codigo_imputacion"] for l in resultado["tablas"]["lineas_albaran"]] == [None] * 5


def test_f084_r39_misma_linea_es_mismo_numero_y_misma_descripcion():
    """FER-002: IA1 numera 4 la línea que INPUTS numera 7; el número solo pondría
    CI.4.18 a una línea que va a P5.36.01."""
    inputs = _inputs({"num_linea": 4, "descripcion": "papel higienico", "codigo_imputacion": None},
                     {"num_linea": 5, "descripcion": "jabon", "codigo_imputacion": None})
    ia1 = _ia1({"num_linea": 4, "descripcion_esperada": "AÑIL ESPECIAL", "codigo_imputacion": "CI.4.18"},
               {"num_linea": 5, "descripcion_esperada": NO_COMPARAR, "codigo_imputacion": "CI.4.18"})

    resultado = sv6_build.con_partidas_de_ia1(inputs, ia1)

    assert [l["codigo_imputacion"] for l in resultado["tablas"]["lineas_albaran"]] == [None, None]


def test_f084_r39_fer_002_no_recibe_partidas_de_otras_lineas():
    inputs = runner.cargar_inputs(RUTA_FIXTURES, ["FER-002"])["FER-002"]

    assert [l["codigo_imputacion"] for l in inputs["tablas"]["lineas_albaran"]] == [None] * 8


def test_f084_r39_no_toca_el_fixture_original_ni_sin_ia1():
    inputs = _inputs({"num_linea": 1, "descripcion": "papel", "codigo_imputacion": None})
    original = copy.deepcopy(inputs)

    con = sv6_build.con_partidas_de_ia1(inputs, _ia1(
        {"num_linea": 1, "descripcion_esperada": "papel", "codigo_imputacion": "CI.4.18"}))
    sin = sv6_build.con_partidas_de_ia1(inputs, None)

    assert inputs == original
    assert sin == original
    assert con["tablas"]["lineas_albaran"][0]["codigo_imputacion"] == "CI.4.18"
    assert sv6_build.con_partidas_de_ia1({"caso_id": "X"}, _ia1()) == {"caso_id": "X"}


def test_f084_r39_cargar_inputs_aplica_el_libro_ia1_de_esos_fixtures(tmp_path):
    fixtures = tmp_path / "fixtures"
    for fase, contenido in (
        ("inputs", _inputs({"num_linea": 1, "descripcion": "papel", "codigo_imputacion": None})),
        ("IA1", _ia1({"num_linea": 1, "descripcion_esperada": "papel",
                      "codigo_imputacion": "CI.4.18"})),
    ):
        (fixtures / fase).mkdir(parents=True)
        (fixtures / fase / "FER-900.json").write_text(json.dumps(contenido), encoding="utf-8")

    inputs = runner.cargar_inputs(fixtures)

    assert inputs["FER-900"]["tablas"]["lineas_albaran"][0]["codigo_imputacion"] == "CI.4.18"
    assert runner.cargar_inputs(fixtures, ["OTRO"]) == {}


def test_f084_r39_sv5_y_sv6_reciben_la_partida_del_albaran():
    inputs = runner.cargar_inputs(RUTA_FIXTURES)["FER-001"]

    contexto = sv5_valoracion.construir_contexto(inputs, indice={})
    envelope = sv6_build.construir_envelope_estimulado(inputs, {"tablas": {}})

    assert [l["codigo_partida_albaran"] for l in contexto["lineas_albaran"]] == ["CI.4.18"]
    assert [l["codigo_partida_albaran"] for l in envelope["context"]["lineas_albaran"]] == ["CI.4.18"]


def test_f084_r39_e2e_mide_la_partida_final_de_sv6():
    fases, _ = runner.corrida_determinista(RUTA_FIXTURES, ["FER-001"])

    (e2e,) = [c for f in fases if f.nombre == "E2E" for c in f.casos]
    assert not [d for d in e2e.fallos if "partida_final" in d.campo]


def test_f084_r39_el_comparador_de_f083_valora_con_la_misma_entrada():
    from evals import comparar_modelos as cm

    trabajos = cm._trabajos_de_casos(
        cm.Plan(fase="IA3", modelos=[], referencia="", referencia_anadida=False,
                preparacion=None, casos=["FER-001"], omitidos={}, repeticiones=1,
                proveedores=[]),
        Path(RUTA_FIXTURES), Path("."),
    )

    (linea,) = trabajos["FER-001"]["contexto"]["lineas_albaran"]
    assert linea["codigo_partida_albaran"] == "CI.4.18"
