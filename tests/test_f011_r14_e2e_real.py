# tests/test_f011_r14_e2e_real.py
"""F-011 · R14 — Extremo a extremo con sv5 real: contexto, envelope y hand-off.

Aquí se prueba la parte que no cuesta dinero: que el contexto salga bien de los
fixtures, que el envelope tenga la forma que sv6 sabe consumir (el hand-off) y
que sin claves LLM se pare ANTES de gastar un solo caso.

El eval real lo lanza el humano con `--con-llm`; estos tests no llaman a nada.
"""

import pytest

from evals.procesos.sv5_valoracion import (
    ClavesAusentes,
    aplicar_conciliacion,
    comprobar_claves,
    construir_contexto,
    envelope_desde,
    lineas_no_casadas,
    proyectar_ia4,
)
from evals.procesos.sv6_build import ejecutar_en_subproceso

_INPUTS = {
    "caso_id": "MOR-001",
    "tipologia": "Mortero",
    "tablas": {
        "caso": [{"caso_id": "MOR-001", "contrato_codigo": "CTSU26/0007"}],
        "lineas_albaran": [
            {
                "caso_id": "MOR-001",
                "num_linea": 1,
                "descripcion": "MORTERO M-7,5",
                "cantidad": 4,
                "unidad": "m3",
                "precio_unitario": 60.0,
                "importe": 240.0,
            },
            {
                "caso_id": "MOR-001",
                "num_linea": 2,
                "descripcion": "PORTES",
                "cantidad": 1,
                "unidad": "ud",
                "precio_unitario": 30.0,
                "importe": 30.0,
            },
        ],
        "contrato_lineas": [
            {
                "caso_id": "MOR-001",
                "codigo_producto": "M-75",
                "descripcion_recurso": "MORTERO M-7,5",
                "unidad": "m3",
                "precio_unitario": 60.0,
                "codigo_partida": "02.01.01",
            }
        ],
        "condiciones": [
            {"caso_id": "MOR-001", "campo": "fecha_albaran", "valor": "2026-05-06"}
        ],
    },
}


def test_f011_r14_el_contexto_sale_de_los_fixtures_de_inputs():
    contexto = construir_contexto(_INPUTS)

    assert contexto["document_id"] == "MOR-001"
    assert contexto["codigo_contrato"] == "CTSU26/0007"
    assert contexto["fecha_albaran"] == "2026-05-06"
    assert [linea["merge_line_id"] for linea in contexto["lineas_albaran"]] == [1, 2]
    assert contexto["lineas_albaran"][0]["contexto_linea"]["tipo_familia"] == "mortero"
    assert contexto["lineas_contrato"][0]["contrato_line_id"] == 1


def test_f011_r14_el_envelope_tiene_la_forma_que_consume_sv6():
    contexto = construir_contexto(_INPUTS)
    lineas = [
        {
            "merge_line_id": 1,
            "line_kind": "from_albaran",
            "match_method": "exact_concept",
            "matched_contrato_line_id": 1,
            "match_confidence_pct": 95.0,
            "unidad_categoria_albaran": "volume",
            "unidad_category_match": True,
            "precio_unitario_contrato_db": 60.0,
            "razon_corta": "casa por concepto",
        }
    ]

    envelope = envelope_desde(contexto, lineas, "gemini", "gemini-2.5-flash")

    salida = ejecutar_en_subproceso(
        {"casos": [{"caso_id": "MOR-001", "envelope": envelope}]}
    )
    resultado = salida["resultados"][0]
    assert resultado["header"]["contrato_codigo"] == "CTSU26/0007"
    assert resultado["lineas"][0]["codigo_partida_final"] == "02.01.01"
    assert resultado["lineas"][0]["importe_calculado"] == pytest.approx(240.0)


def test_f011_r14_ia4_recibe_las_lineas_que_ia3_dejo_sin_resolver():
    contexto = construir_contexto(_INPUTS)
    envelope = envelope_desde(
        contexto,
        [
            {
                "merge_line_id": 1,
                "line_kind": "from_albaran",
                "match_method": "exact_concept",
                "matched_contrato_line_id": 1,
                "precio_unitario_contrato_db": 60.0,
            },
            {
                "merge_line_id": 2,
                "line_kind": "from_albaran",
                "match_method": "no_match",
                "matched_contrato_line_id": None,
                "precio_unitario_contrato_db": None,
            },
        ],
        "gemini",
        None,
    )

    pendientes = lineas_no_casadas(envelope)

    assert [linea["line_ref"] for linea in pendientes] == [2]
    assert pendientes[0]["descripcion"] == "PORTES"


def test_f011_r14_la_conciliacion_muta_el_envelope_antes_del_build():
    contexto = construir_contexto(_INPUTS)
    envelope = envelope_desde(
        contexto,
        [
            {
                "merge_line_id": 2,
                "line_kind": "from_albaran",
                "match_method": "no_match",
                "matched_contrato_line_id": None,
                "precio_unitario_contrato_db": None,
            }
        ],
        "gemini",
        None,
    )
    conciliaciones = [
        {
            "line_ref": 2,
            "matched_contrato_line_id": 1,
            "precio_unitario_contrato_db": 30.0,
            "match_method": "semantic",
            "match_confidence_pct": 80.0,
            "razon_corta": "casa con portes del contrato",
        }
    ]

    mutadas = aplicar_conciliacion(envelope, conciliaciones)

    assert mutadas == 1
    assert envelope["data"]["lineas"][0]["matched_contrato_line_id"] == 1
    assert envelope["data"]["lineas"][0]["match_method"] == "semantic"


def test_f011_r14_una_conciliacion_que_no_concilia_no_toca_nada():
    contexto = construir_contexto(_INPUTS)
    envelope = envelope_desde(
        contexto,
        [{"merge_line_id": 2, "line_kind": "from_albaran", "match_method": "no_match"}],
        "gemini",
        None,
    )

    assert aplicar_conciliacion(envelope, [{"line_ref": 2, "matched_contrato_line_id": None}]) == 0
    assert envelope["data"]["lineas"][0].get("matched_contrato_line_id") is None


def test_f011_r14_la_salida_de_ia4_se_proyecta_al_libro_ia4():
    contexto = construir_contexto(_INPUTS)
    envelope = envelope_desde(contexto, [], "gemini", None)

    proyeccion = proyectar_ia4(
        [
            {
                "line_ref": 2,
                "matched_contrato_line_id": 1,
                "precio_unitario_contrato_db": 30.0,
            },
            {"line_ref": 3, "matched_contrato_line_id": None},
        ],
        envelope,
    )

    assert proyeccion[0] == {
        "num_linea": 2,
        "concilia": True,
        "linea_contrato_esperada": "M-75",
        "precio_unitario_esperado": 30.0,
    }
    assert proyeccion[1]["concilia"] is False


def test_f011_r14_sin_claves_se_para_antes_de_consumir_ningun_caso():
    with pytest.raises(ClavesAusentes) as error:
        comprobar_claves(["gemini", "openai"], entorno={"OPENAI_API_KEY": "  "})

    mensaje = str(error.value)
    assert "GEMINI_API_KEY" in mensaje
    assert "OPENAI_API_KEY" in mensaje
    assert "ningún caso" in mensaje


def test_f011_r14_con_las_claves_puestas_no_se_queja():
    comprobar_claves(
        ["gemini"], entorno={"GEMINI_API_KEY": "una-clave-de-prueba-no-real"}
    )
