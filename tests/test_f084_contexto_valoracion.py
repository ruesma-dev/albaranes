# tests/test_f084_contexto_valoracion.py
"""F-084 · C — El contexto de valoración del banco es el de producción.

R12 (las líneas de albarán salen de UNA función, con descuento, precio neto e
importe derivado como el `SELECT` de sv5), R13 (descuento compuesto), R14
(clasificación del documento desde la tipología), R15 (`UnitCategoryPrefilter`
en el subproceso de sv5), R16 (fecha y número desde CONDICIONES), R17
(cabecera del contrato del índice), R32 y R33 (documento del contrato local).

Sin red ni BBDD (R25): sv6 corre en su subproceso con un envelope ya fabricado
y sv5, cuando hace falta, con un doble de LLM.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from evals.procesos import sv6_build
from evals.procesos.sv6_build import (
    MAPA_FAMILIA_DOCUMENTO,
    DescuentoCompuesto,
    clasificacion_de,
    construir_envelope_estimulado,
    lineas_albaran_de,
)

RAIZ = Path(__file__).resolve().parent.parent
FIXTURES = RAIZ / "evals" / "fixtures"


def _fixture(fase: str, caso: str) -> dict:
    return json.loads((FIXTURES / fase / f"{caso}.json").read_text(encoding="utf-8"))


def _inputs(lineas: list[dict], tipologia: str = "Ferreteria", condiciones=None) -> dict:
    return {
        "caso_id": "FER-900",
        "tipologia": tipologia,
        "tablas": {
            "caso": [{"caso_id": "FER-900", "contrato_codigo": "CTSU26/0001", "tipologia": tipologia}],
            "condiciones": condiciones or [],
            "contrato_lineas": [],
            "lineas_albaran": lineas,
        },
    }


def _linea(**cambios) -> dict:
    base = {
        "caso_id": "FER-900",
        "num_linea": 1,
        "descripcion": "DISCO",
        "cantidad": 50,
        "unidad": "UD",
        "precio_unitario": 0.647,
        "descuentos": 40,
        "importe": None,
        "codigo_imputacion": None,
        "observaciones_albaran": None,
    }
    base.update(cambios)
    return base


# --- R12 · descuento, precio neto e importe derivado --------------------------


def test_f084_r12_el_descuento_y_el_precio_neto_viajan_en_la_linea():
    linea = lineas_albaran_de(_inputs([_linea(importe=19.41)]))[0]

    assert linea["descuento_albaran"] == 40.0
    assert linea["precio_neto_albaran"] == 19.41
    assert linea["importe_albaran"] == 19.41


def test_f084_r12_sin_importe_se_deriva_con_la_formula_canonica():
    """`COALESCE(precio_neto, cantidad × precio × (1 − dto/100))` del SELECT de sv5."""
    linea = lineas_albaran_de(_inputs([_linea()]))[0]

    assert linea["importe_albaran"] == 19.41  # 50 × 0,647 × 0,60, sin ruido de float
    assert linea["precio_neto_albaran"] is None


def test_f084_r12_sin_descuento_el_importe_derivado_es_cantidad_por_precio():
    linea = lineas_albaran_de(_inputs([_linea(descuentos=None, cantidad=8, precio_unitario=72.5)]))[0]

    assert linea["importe_albaran"] == 580.0
    assert linea["descuento_albaran"] is None


@pytest.mark.parametrize("cambio", [{"cantidad": None}, {"precio_unitario": None}])
def test_f084_r12_sin_cantidad_o_sin_precio_no_se_deriva(cambio):
    """Como en SQL: un factor NULL deja el importe NULL (caso hormigón)."""
    assert lineas_albaran_de(_inputs([_linea(**cambio)]))[0]["importe_albaran"] is None


def test_f084_r12_el_importe_leido_manda_sobre_el_derivado():
    linea = lineas_albaran_de(_inputs([_linea(importe=20.0)]))[0]

    assert linea["importe_albaran"] == 20.0


def test_f084_r12_un_descuento_de_lista_con_un_valor_vale_ese_valor():
    """El conversor guarda `descuentos` como lista si el libro escribe `a;b`."""
    linea = lineas_albaran_de(_inputs([_linea(descuentos=["40"])]))[0]

    assert linea["descuento_albaran"] == 40.0
    assert linea["importe_albaran"] == 19.41


def test_f084_r12_un_descuento_vacio_o_en_interrogante_es_sin_descuento():
    for vacio in ([], "?", "@@NO_COMPARAR@@", ""):
        linea = lineas_albaran_de(_inputs([_linea(descuentos=vacio)]))[0]
        assert linea["descuento_albaran"] is None, vacio
        assert linea["importe_albaran"] == 32.35


def test_f084_r12_las_lineas_conservan_el_resto_de_campos_de_siempre():
    linea = lineas_albaran_de(
        _inputs([_linea(codigo_imputacion="CI.4.18", observaciones_albaran="nota")])
    )[0]

    assert linea["merge_line_id"] == 1 and linea["line_index"] == 1
    assert linea["descripcion"] == "DISCO" and linea["unidad_medida"] == "UD"
    assert linea["cantidad"] == 50.0 and linea["precio_unitario_albaran"] == 0.647
    assert linea["codigo_partida_albaran"] == "CI.4.18"
    assert linea["unidad_categoria"] == "unknown"
    assert linea["contexto_linea"]["descripcion_extendida"] == "nota"


def test_f084_r12_una_linea_sin_numero_no_entra():
    assert lineas_albaran_de(_inputs([_linea(num_linea=None)])) == []


def test_f084_r12_el_envelope_estimulado_usa_la_misma_funcion():
    inputs = _inputs([_linea()])
    envelope = construir_envelope_estimulado(inputs, {"tablas": {}})

    assert envelope["context"]["lineas_albaran"] == lineas_albaran_de(inputs)


def test_f084_r12_fer001_determinista_valora_19_41():
    """El caso del diagnóstico: hoy 32,35 = 50 × 0,647, sin el 40 % de descuento."""
    inputs, ia3 = _fixture("inputs", "FER-001"), _fixture("IA3", "FER-001")
    envelope = construir_envelope_estimulado(inputs, ia3)

    salida = sv6_build.ejecutar_en_subproceso(
        {"casos": [{"caso_id": "FER-001", "envelope": envelope}]}
    )
    resultado = salida["resultados"][0]
    base = [l for l in resultado["lineas"] if l["line_kind"] == "from_albaran"]

    assert base[0]["importe_calculado"] == pytest.approx(19.41)


# --- R13 · descuento compuesto -----------------------------------------------


@pytest.mark.parametrize("compuesto", [["40", "10"], [40, 10], "40;10"])
def test_f084_r13_un_descuento_compuesto_no_se_representa(compuesto):
    with pytest.raises(DescuentoCompuesto) as error:
        lineas_albaran_de(_inputs([_linea(descuentos=compuesto)]))

    assert "descuento compuesto no representable" in str(error.value)


# --- R14 · clasificación del documento desde la tipología ---------------------


@pytest.mark.parametrize(
    ("tipologia", "familia"),
    [
        ("Residuos", "residuos"),
        ("Hormigon", "hormigon"),
        ("Mortero", "mortero"),
        ("Combustible", "combustible"),
        ("Alquiler", "alquiler_maquinaria"),
        ("Ferreteria", "generico"),
        ("Grava", "generico"),
        ("Generico-Suministros", "generico"),
        ("Bombeo", "generico"),
        ("", "generico"),
    ],
)
def test_f084_r14_la_familia_sale_de_la_tipologia(tipologia, familia):
    clasificacion = clasificacion_de(_inputs([], tipologia=tipologia))

    assert clasificacion["familia"] == familia


def test_f084_r14_la_clasificacion_es_del_banco_y_valida_contra_comun():
    from ruesma_comun.contratos import ClasificacionAlbaran

    clasificacion = clasificacion_de(_inputs([], tipologia="Residuos"))

    assert clasificacion["origen"] == "banco_evals"
    assert clasificacion["confianza_pct"] == 100.0
    assert clasificacion["mixto"] is False
    assert clasificacion["familias_secundarias"] == []
    assert ClasificacionAlbaran.model_validate(clasificacion).familia == "residuos"


def test_f084_r14_las_familias_del_mapa_existen_en_el_catalogo():
    from ruesma_comun.contratos.familias import prompt_valoracion_de

    assert MAPA_FAMILIA_DOCUMENTO == {
        "Residuos": "residuos",
        "Hormigon": "hormigon",
        "Mortero": "mortero",
        "Combustible": "combustible",
        "Alquiler": "alquiler_maquinaria",
    }
    assert prompt_valoracion_de("residuos") == "valuation_residuos"


def test_f084_r14_el_envelope_estimulado_lleva_la_clasificacion_en_context():
    inputs = _inputs([_linea()], tipologia="Residuos")
    envelope = construir_envelope_estimulado(inputs, {"tablas": {}})

    assert envelope["context"]["clasificacion"] == clasificacion_de(inputs)


def test_f084_r14_el_estimulo_de_matches_no_cambia():
    """La clasificación y el descuento se añaden; el estímulo de IA3 es el de siempre."""
    inputs, ia3 = _fixture("inputs", "RES-001"), _fixture("IA3", "RES-001")
    envelope = construir_envelope_estimulado(copy.deepcopy(inputs), ia3)

    por_linea = {l["merge_line_id"]: l for l in envelope["data"]["lineas"] if l["merge_line_id"]}
    for fila in ia3["tablas"]["lineas_valoradas"]:
        linea = por_linea[int(fila["num_linea"])]
        assert linea["match_method"] == (fila["match_method"] or "no_match")
        assert linea["razon_corta"] == "estímulo del eval desde el ground truth de IA3"
