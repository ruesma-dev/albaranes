# tests/test_f011_r11_ia12.py
"""F-011 · R11 — IA1/IA2: proveedor primario por defecto y `--proveedores`.

Decisión D3: una corrida invoca por defecto SOLO el proveedor primario de cada
fase (lo que corre en producción). Ampliar a varios es una opción explícita,
porque cada proveedor extra es otra factura.
"""

import pytest

from evals.procesos.sv2_extraccion import (
    PROMPT_FASE_1,
    prompt_de_fase_2,
    proveedores_a_invocar,
    proyectar_ia1,
    proyectar_ia2,
)

_ENTORNO = {"IA_PRIMERA_FASE": "gemini", "IA_SEGUNDA_FASE": "openai"}


def test_f011_r11_por_defecto_solo_el_primario_de_cada_fase():
    assert proveedores_a_invocar("IA1", entorno=_ENTORNO) == ["gemini"]
    assert proveedores_a_invocar("IA2", entorno=_ENTORNO) == ["openai"]


def test_f011_r11_el_primario_sale_del_entorno_como_en_produccion():
    entorno = {"IA_PRIMERA_FASE": "claude", "IA_SEGUNDA_FASE": "claude"}

    assert proveedores_a_invocar("IA1", entorno=entorno) == ["claude"]


def test_f011_r11_sin_variable_se_usa_el_mismo_defecto_que_sv2():
    assert proveedores_a_invocar("IA1", entorno={}) == ["gemini"]
    assert proveedores_a_invocar("IA2", entorno={}) == ["openai"]


def test_f011_r11_proveedores_amplia_la_corrida():
    pedidos = proveedores_a_invocar(
        "IA1", solicitados=["Gemini", "openai "], entorno=_ENTORNO
    )

    assert pedidos == ["gemini", "openai"]


def test_f011_r11_el_prompt_de_fase_2_se_especializa_por_tipologia():
    assert prompt_de_fase_2("Hormigon") == "albaran_revision_fase2_hormigon"
    assert prompt_de_fase_2("Residuos") == "albaran_revision_fase2_residuos"
    assert prompt_de_fase_2("Bombeo") == "albaran_revision_fase2_es"


def test_f011_r11_el_prompt_de_fase_1_es_el_de_produccion():
    assert PROMPT_FASE_1 == "albaran_factura_es"


def test_f011_r11_la_extraccion_se_proyecta_al_vocabulario_del_libro_ia1():
    documento = {
        "cabecera": {
            "proveedor_nombre": "HORMIGONES DEL NORTE S.L.",
            "proveedor_cif": "B12345678",
            "fecha": "2026-03-04",
            "numero_albaran": "A-2201",
            "obra_codigo": "OBR-77",
            "obra_nombre": "Nave 3",
            "forma_pago": None,
        },
        "lineas": [
            {
                "concepto": "HA-25/B/20/IIa",
                "cantidad": 8.0,
                "precio": 72.5,
                "precio_neto": 580.0,
                "codigo_imputacion": None,
            }
        ],
    }

    proyeccion = proyectar_ia1(documento, "HOR-001")

    assert proyeccion["cabeceras"][0]["numero_albaran"] == "A-2201"
    assert proyeccion["lineas"][0]["num_linea"] == 1
    assert proyeccion["lineas"][0]["cantidad"] == pytest.approx(8.0)


def test_f011_r11_el_contexto_de_ia2_se_proyecta_en_formato_largo():
    documento = {
        "lineas": [
            {
                "contexto_linea": {
                    "tipo_familia": "hormigon",
                    "resistencia": "25",
                    "consistencia": None,
                }
            }
        ]
    }

    proyeccion = proyectar_ia2(documento, "HOR-001")

    assert proyeccion["contexto"] == [
        {"num_linea": 1, "campo_contexto": "resistencia", "valor_esperado": "25"},
        {"num_linea": 1, "campo_contexto": "tipo_familia", "valor_esperado": "hormigon"},
    ]
