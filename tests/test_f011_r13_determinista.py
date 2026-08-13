# tests/test_f011_r13_determinista.py
"""F-011 · R13 — Modo determinista: las redes de sv6 contra el ground truth.

Qué evalúa este modo y qué NO: no juzga al LLM (eso es la pasada completa),
juzga que las redes deterministas de sv6 hagan cumplir las reglas AUNQUE la IA
proponga lo prohibido. Por eso el envelope se fabrica desde el propio ground
truth y las sintéticas PROHIBIDAS de la TABLA 3 se inyectan como si la IA las
hubiera propuesto.

Sin red, sin BBDD y sin LLM: se importa sv6 en un subproceso y se le pasa un
envelope ya construido.
"""

import json

import pytest

from evals.modelos import NO_COMPARAR
from evals.procesos.sv6_build import (
    construir_envelope_estimulado,
    ejecutar_en_subproceso,
    evaluar_caso_determinista,
)

_INPUTS = {
    "caso_id": "HOR-900",
    "fase": "INPUTS",
    "tipologia": "Hormigon",
    "libro": "INPUTS.xlsx",
    "sha256_libro": "x" * 64,
    "tablas": {
        "caso": [
            {
                "caso_id": "HOR-900",
                "tipologia": "Hormigon",
                "ia_destino": "ambas",
                "origen": "manual",
                "contrato_codigo": "CTSU26/0001",
                "descripcion_caso": "una línea que casa exacto",
            }
        ],
        "lineas_albaran": [
            {
                "caso_id": "HOR-900",
                "num_linea": 1,
                "descripcion": "HA-25/B/20/IIa",
                "cantidad": 8,
                "unidad": "m3",
                "precio_unitario": 72.5,
                "descuentos": None,
                "importe": 580.0,
                "codigo_imputacion": None,
                "observaciones_albaran": None,
            }
        ],
        "contrato_lineas": [
            {
                "caso_id": "HOR-900",
                "codigo_producto": "P-100",
                "descripcion_recurso": "HA-25/B/20/IIa",
                "unidad": "m3",
                "precio_unitario": 72.5,
                "codigo_partida": "01.02.03",
                "comentario": None,
            }
        ],
        "condiciones": [
            {
                "caso_id": "HOR-900",
                "campo": "fecha_albaran",
                "valor": "2026-03-04",
                "comentario": None,
            }
        ],
    },
}

_IA3 = {
    "caso_id": "HOR-900",
    "fase": "IA3",
    "tipologia": "Hormigon",
    "libro": "IA3_valoracion.xlsx",
    "sha256_libro": "y" * 64,
    "tablas": {
        "lineas_valoradas": [
            {
                "caso_id": "HOR-900",
                "num_linea": 1,
                "match_method": "exact_concept",
                "codigo_producto_contrato": "P-100",
                "codigo_partida_final": "01.02.03",
                "precio_unitario_final": 72.5,
                "precio_source": "contrato_db",
                "importe_calculado": 580.0,
                "review_required": "NO",
                "comentario": None,
            }
        ],
        "sinteticas_esperadas": [],
        "sinteticas_prohibidas": [
            {
                "caso_id": "HOR-900",
                "concepto_vetado": "ADITIVO SUPERPLASTIFICANTE",
                "motivo_veto": "el albarán no lo lleva",
                "comentario": None,
            }
        ],
    },
}

_FINAL = {
    "caso_id": "HOR-900",
    "fase": "FINAL",
    "tipologia": "Hormigon",
    "libro": "RESULTADO_FINAL.xlsx",
    "sha256_libro": "z" * 64,
    "tablas": {
        "datos_generales": [
            {
                "caso_id": "HOR-900",
                "contrato_elegido": "CTSU26/0001",
                "total_valorado_esperado": 580.0,
                "requiere_revision": "NO",
            }
        ],
        "lineas": [
            {
                "caso_id": "HOR-900",
                "num_linea": 1,
                "casa_con_contrato": "SI",
                "linea_contrato": "P-100",
                "partida_final": "01.02.03",
                "precio_unitario_final": 72.5,
                "importe_final": 580.0,
                "linea_a_revision": "NO",
            }
        ],
        "lineas_anadidas": [],
    },
}


def _sin_prohibidas(fixture):
    """El mismo caso sin la TABLA 3, para medir el camino limpio."""
    copia = json.loads(json.dumps(fixture))
    copia["tablas"]["sinteticas_prohibidas"] = []
    return copia


#: Ground truth «limpio»: mismos valores duros (partida, precio, importe) y
#: `?` en los campos cuyo valor exacto depende de reglas internas de sv6 (de
#: dónde sale el precio, si la línea va a revisión). El convenio `?` del
#: contrato de datos existe justamente para esto.
_IA3_LIMPIO = _sin_prohibidas(_IA3)
_IA3_LIMPIO["tablas"]["lineas_valoradas"][0]["precio_source"] = NO_COMPARAR
_IA3_LIMPIO["tablas"]["lineas_valoradas"][0]["review_required"] = NO_COMPARAR

_FINAL_LIMPIO = json.loads(json.dumps(_FINAL))
_FINAL_LIMPIO["tablas"]["datos_generales"][0]["requiere_revision"] = NO_COMPARAR
_FINAL_LIMPIO["tablas"]["lineas"][0]["linea_a_revision"] = NO_COMPARAR


def _construir(ia3):
    envelope = construir_envelope_estimulado(_INPUTS, ia3)
    salida = ejecutar_en_subproceso(
        {"casos": [{"caso_id": "HOR-900", "envelope": envelope}]}
    )
    return envelope, salida["resultados"][0]


@pytest.fixture(scope="module")
def build_de_hor_900():
    """Build real de sv6 con la sintética prohibida inyectada."""
    return _construir(_IA3)


@pytest.fixture(scope="module")
def build_limpio():
    """Build real de sv6 del mismo caso sin sintéticas prohibidas."""
    return _construir(_IA3_LIMPIO)


def test_f011_r13_el_envelope_estimulado_reproduce_lo_que_diria_ia3():
    envelope = construir_envelope_estimulado(_INPUTS, _IA3)

    assert envelope["meta"]["codigo_contrato"] == "CTSU26/0001"
    assert envelope["meta"]["fecha_albaran"] == "2026-03-04"
    assert len(envelope["context"]["lineas_albaran"]) == 1
    assert envelope["context"]["lineas_contrato"][0]["contrato_line_id"] == 1
    base = [l for l in envelope["data"]["lineas"] if l["line_kind"] == "from_albaran"]
    assert base[0]["matched_contrato_line_id"] == 1
    assert base[0]["precio_unitario_contrato_db"] == 72.5


def test_f011_r13_las_prohibidas_se_inyectan_como_si_las_propusiera_la_ia():
    envelope = construir_envelope_estimulado(_INPUTS, _IA3)

    sinteticas = [
        l for l in envelope["data"]["lineas"] if l["line_kind"] == "synthetic_modifier"
    ]
    assert len(sinteticas) == 1
    assert sinteticas[0]["descripcion_linea"] == "ADITIVO SUPERPLASTIFICANTE"
    assert sinteticas[0]["parent_merge_line_id"] == 1


def test_f011_r13_el_build_real_de_sv6_resuelve_la_linea_base(build_limpio):
    _, resultado = build_limpio

    base = next(
        l for l in resultado["lineas"] if l["line_kind"] == "from_albaran"
    )
    assert base["codigo_partida_final"] == "01.02.03"
    assert base["precio_unitario_final"] == pytest.approx(72.5)
    assert base["importe_calculado"] == pytest.approx(580.0)
    assert base["partida_action"] == "existing_matched"


def test_f011_r13_la_prohibida_emitida_no_lleva_precio_y_queda_a_revision(
    build_de_hor_900,
):
    """Lo que sv6 SÍ hace hoy con una sintética que no tarifa el contrato.

    No la borra —el builder no descarta líneas—, pero no le inventa precio y
    la manda a revisión. Que además siga apareciendo es lo que el eval
    denuncia en el test siguiente.
    """
    _, resultado = build_de_hor_900

    sintetica = next(
        l for l in resultado["lineas"] if l["line_kind"] == "synthetic_modifier"
    )
    assert sintetica["descripcion_linea"] == "ADITIVO SUPERPLASTIFICANTE"
    assert sintetica["precio_unitario_final"] is None
    assert sintetica["review_required"] is True
    assert "modifier_identified_no_tariff" in sintetica["review_reasons"]


def test_f011_r13_una_prohibida_emitida_es_un_fallo_critico(build_de_hor_900):
    """El ground truth dice que no debe aparecer: si aparece, el caso es ROJO."""
    envelope, resultado = build_de_hor_900

    evaluacion = evaluar_caso_determinista(
        caso_id="HOR-900", envelope=envelope, resultado=resultado, ia3=_IA3, final=_FINAL
    )

    prohibidas = [
        d for d in evaluacion.discrepancias if "prohibida" in d.motivo.lower()
    ]
    assert prohibidas, "una sintética vetada emitida tiene que salir en el informe"
    assert prohibidas[0].severidad == "fallo"
    assert "ADITIVO SUPERPLASTIFICANTE" in str(prohibidas[0].obtenido)


def test_f011_r13_lo_que_el_ground_truth_declara_bien_no_genera_fallos(build_limpio):
    envelope, resultado = build_limpio

    evaluacion = evaluar_caso_determinista(
        caso_id="HOR-900",
        envelope=envelope,
        resultado=resultado,
        ia3=_IA3_LIMPIO,
        final=_FINAL_LIMPIO,
    )

    assert [d for d in evaluacion.discrepancias if d.severidad == "fallo"] == []


def test_f011_r13_los_campos_no_observables_se_declaran(build_limpio):
    """`caso_id` o `comentario` no salen del build: no se comparan, pero constan."""
    envelope, resultado = build_limpio

    evaluacion = evaluar_caso_determinista(
        caso_id="HOR-900",
        envelope=envelope,
        resultado=resultado,
        ia3=_IA3_LIMPIO,
        final=_FINAL_LIMPIO,
    )

    assert "caso_id" in evaluacion.no_observables


def test_f011_r13_una_partida_distinta_en_el_ground_truth_sale_roja(build_de_hor_900):
    envelope, resultado = build_de_hor_900
    ia3_torcido = json.loads(json.dumps(_IA3))
    ia3_torcido["tablas"]["lineas_valoradas"][0]["codigo_partida_final"] = "99.99.99"

    evaluacion = evaluar_caso_determinista(
        caso_id="HOR-900",
        envelope=envelope,
        resultado=resultado,
        ia3=ia3_torcido,
        final=_FINAL,
    )

    campos = {d.campo for d in evaluacion.discrepancias if d.severidad == "fallo"}
    assert any("codigo_partida_final" in campo for campo in campos)


def test_f011_r13_el_extremo_a_extremo_compara_contra_resultado_final(
    build_de_hor_900,
):
    envelope, resultado = build_de_hor_900
    final_torcido = json.loads(json.dumps(_FINAL))
    final_torcido["tablas"]["datos_generales"][0]["total_valorado_esperado"] = 1.0

    evaluacion = evaluar_caso_determinista(
        caso_id="HOR-900",
        envelope=envelope,
        resultado=resultado,
        ia3=_IA3,
        final=final_torcido,
    )

    campos = {d.campo for d in evaluacion.discrepancias if d.severidad == "fallo"}
    assert any("total_valorado_esperado" in campo for campo in campos)


def test_f011_r13_el_subproceso_no_abre_ninguna_conexion(build_de_hor_900):
    """La prueba es de caja negra: sv6 solo recibe un envelope ya construido.

    Si el adaptador intentara hablar con la BBDD o con un LLM, el subproceso
    fallaría (no hay credenciales ni servidor) y el build no devolvería nada.
    """
    _, resultado = build_de_hor_900

    assert resultado["header"]["status"] in {"ok", "partial"}
    assert resultado["header"]["provider_ia"] in (None, "ground_truth")
