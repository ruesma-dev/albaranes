# tests/test_f110_js.py
"""F-110 · T11 · el JS de «A Sigrid» con el descuento (R15, R16), EJECUTADO con node.

- R16: ``precioASigrid`` da lo mismo que ``linea_a_sigrid`` de comun en cada caso
  de ``services/albaranes-comun/tests/f110_casos.json`` (la misma tabla que el
  test de comun).
- R15: al teclear Q, P, d o el importe, «A Sigrid» se repinta con la regla de
  comun si la fila lleva ``data-alta-dto``: con ``dto``, «… € −7 %», visible si
  el precio o el ``dto`` a Sigrid no son los de la fila. Sin la marca, F-106.

Las funciones se sacan tal cual de ``app.js`` y corren con entradas falsas o con
el DOM falso (``tests/dom_falso.js``).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_f065_f1_js import _ejecutar, con_node
from test_f065_f3bis_front import _ejecutar_dom
from test_f106_js import _FILA, _REPINTAR

from ruesma_comun.alta_sigrid import linea_a_sigrid

CASOS = json.loads(
    (Path(__file__).resolve().parents[2] / "albaranes-comun" / "tests" / "f110_casos.json")
    .read_text(encoding="utf-8"),
)["casos"]

_FUNCIONES = ["importeDeFila", "precioDespejado", "precioASigrid"]


def _argumentos(caso: dict) -> list:
    """Lo que la ficha tiene en la fila: Q de la ficha (la convertida o, sin
    ella, la del albarán), importe, factor del servidor (Q a Sigrid / Q de la
    ficha), P, d y la guarda."""
    q_ficha = caso["cantidad_convertida"] if caso["cantidad_convertida"] is not None \
        else caso["cantidad_albaran"]
    q_sigrid = caso["cantidad_convertida"] if caso["vinculada"] else caso["cantidad_albaran"]
    factor = q_sigrid / q_ficha if q_ficha else 1.0
    return [q_ficha, caso["importe"], factor, caso["precio"], caso["descuento"],
            caso["con_descuento"]]


# =================================================================== #
# R16 · misma tabla que comun
# =================================================================== #
@con_node
def test_f110_r16_js_da_lo_mismo_que_comun_en_la_tabla(tmp_path):
    llamadas = ", ".join(f"precioASigrid(...{json.dumps(_argumentos(c))})" for c in CASOS)
    salidas = _ejecutar(tmp_path, _FUNCIONES, f"console.log(JSON.stringify([{llamadas}]));")
    assert len(salidas) == len(CASOS)
    for caso, js in zip(CASOS, salidas, strict=True):
        esperado = caso["esperado"]
        python = linea_a_sigrid(
            vinculada=caso["vinculada"], cantidad_albaran=caso["cantidad_albaran"],
            cantidad_convertida=caso["cantidad_convertida"], importe=caso["importe"],
            precio=caso["precio"], descuento=caso["descuento"],
            con_descuento=caso["con_descuento"],
        )
        if esperado is None:
            assert js is None and python is None, caso["id"]
            continue
        assert (js["cantidad"], js["precio"], js.get("dto")) == (
            esperado["cantidad"], esperado["precio"], esperado["dto"]), caso["id"]
        assert (js["cantidad"], js["precio"], js.get("dto")) == (
            python.cantidad, python.precio, python.dto), caso["id"]


@con_node
def test_f110_r16_js_sin_guarda_no_lleva_la_clave_dto(tmp_path):
    salidas = _ejecutar(tmp_path, _FUNCIONES, """
        console.log(JSON.stringify([
            precioASigrid(12, 7.2, 1, 0.645, 7, false), precioASigrid(12, 7.2, 1),
            precioASigrid(12, 7.2, 1, 0.645, 7, true), precioASigrid(10, 100, 1, 10, null, true),
        ]));
    """)
    assert salidas[0] == salidas[1] == {"cantidad": 12, "precio": 0.6}
    assert salidas[2] == {"cantidad": 12, "precio": 0.645, "dto": 7}
    assert salidas[3] == {"cantidad": 10, "precio": 10, "dto": None}


@con_node
def test_f110_r15_js_texto_con_dto(tmp_path):
    salidas = _ejecutar(tmp_path, ["precioEs", "cantidadEs", "textoASigrid"], """
        console.log(JSON.stringify([
            textoASigrid({cantidad: 12, precio: 0.645, dto: 7}),
            textoASigrid({cantidad: 10, precio: 10, dto: 7.46}),
            textoASigrid({cantidad: 10, precio: 10, dto: null}),
            textoASigrid({cantidad: 48, precio: 2.17}),
        ]));
    """)
    assert salidas == [
        "A Sigrid: 12 × 0,645 € −7 %", "A Sigrid: 10 × 10,00 € −7,46 %",
        "A Sigrid: 10 × 10,00 €", "A Sigrid: 48 × 2,17 €",
    ]


@con_node
@pytest.mark.parametrize(("dto_sigrid", "d", "difiere"), [
    (7, 7, False), (7.46, 7.456, True), (None, None, False), (None, 7, True), (7, None, True),
    (None, 150, False), (None, -5, False), (None, 0, False),
])
def test_f110_r15_js_dto_difiere(tmp_path, dto_sigrid, d, difiere):
    salida = _ejecutar(tmp_path, ["dtoDifiere"], f"""
        console.log(JSON.stringify(dtoDifiere({json.dumps(dto_sigrid)}, {json.dumps(d)})));
    """)
    assert salida is difiere


# =================================================================== #
# R15 · repintar al teclear (DOM falso)
# =================================================================== #
_REPINTAR_DTO = [*_REPINTAR, "dtoDifiere"]
_GUARDA = 'pu.dataset.altaDto = "1";'


def _repintar(tmp_path, programa, guarda=True):
    return _ejecutar_dom(tmp_path, _REPINTAR_DTO, _FILA + (_GUARDA if guarda else ""), programa)


@con_node
def test_f110_r15_js_con_guarda_cantidad_repinta_con_dto(tmp_path):
    f = _repintar(tmp_path, """
        cant.value = "48"; syncImporteUnitario(tr, "cantidad");
        console.log(JSON.stringify(foto()));
    """)
    assert f["imp"] == "499.97"
    # 48 × 11,20 × 0,93 = 499,97 = I ⇒ a Sigrid P y 7 %: igual que la fila, oculto.
    assert f["sigrid"] is None and f["sigridTexto"] == "A Sigrid: 48 × 11,20 € −7 %"
    assert f["titulo"] == "Precio del contrato: 11.2000 €\nA Sigrid: 48 × 11,20 € −7 %"


@con_node
def test_f110_r15_js_con_guarda_importe_despeja_y_coincide(tmp_path):
    """T17: CECOIS 12 × 0,645 −7 %; tecleado 7,21 ⇒ P 0,646057 y a Sigrid igual."""
    f = _repintar(tmp_path, """
        cant.value = "12"; pu.value = "0.645"; syncImporteUnitario(tr, "precio_unitario");
        const antes = foto();
        imp.value = "7,21"; syncImporteUnitario(tr, "importe");
        console.log(JSON.stringify({antes: antes, despues: foto()}));
    """)
    assert f["antes"]["imp"] == "7.2" and f["antes"]["sigrid"] is None
    assert f["antes"]["sigridTexto"] == "A Sigrid: 12 × 0,645 € −7 %"
    assert f["despues"]["pu"] == "0.646057" and f["despues"]["sigrid"] is None
    assert f["despues"]["sigridTexto"] == "A Sigrid: 12 × 0,646057 € −7 %"


@con_node
def test_f110_r15_js_con_guarda_dto_redondeado_se_ve(tmp_path):
    f = _repintar(tmp_path, """
        pu.value = "10"; dto.value = "7,456"; syncImporteUnitario(tr, "descuento");
        console.log(JSON.stringify(foto()));
    """)
    assert f["imp"] == "92.54"
    assert f["sigrid"] == "A Sigrid: 10 × 10,00 € −7,46 %"


@con_node
def test_f110_r15_js_con_guarda_sin_descuento(tmp_path):
    f = _repintar(tmp_path, """
        dto.value = ""; syncImporteUnitario(tr, "descuento");
        console.log(JSON.stringify(foto()));
    """)
    assert f["imp"] == "112" and f["sigrid"] is None
    assert f["sigridTexto"] == "A Sigrid: 10 × 11,20 €"


@con_node
def test_f110_r15_js_sin_guarda_es_f106(tmp_path):
    f = _repintar(tmp_path, """
        cant.value = "48"; syncImporteUnitario(tr, "cantidad");
        console.log(JSON.stringify(foto()));
    """, guarda=False)
    assert f["sigrid"] == "A Sigrid: 48 × 10,416042 €"


@con_node
def test_f110_r15_js_con_guarda_cien_por_cien_sin_texto(tmp_path):
    f = _repintar(tmp_path, """
        dto.value = "100"; syncImporteUnitario(tr, "descuento");
        console.log(JSON.stringify(foto()));
    """)
    # Importe 0 ⇒ no es a registrar: sin «A Sigrid» y la línea fuera del title.
    assert f["sigrid"] is None and "A Sigrid" not in f["titulo"]
