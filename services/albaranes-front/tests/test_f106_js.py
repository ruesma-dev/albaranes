# tests/test_f106_js.py
"""F-106 · el JS de la ficha (``static/app.js``), EJECUTADO con node.

- R11: al teclear Q, P o d se repinta el importe; al teclear el importe, P con 6
  decimales y el dto se queda; sin divisor (Q 0 o vacía, d 100 %) e importe ≠ 0,
  no se repinta y el importe se marca en rojo con el texto de R7.
- R12: el PATCH lleva ``importe`` (y no ``precio_unitario``) si el último de
  precio, importe, cantidad y dto que se tecleó fue el importe; si no, P solo si
  cambió y nunca ``importe``. Las tres vías de ``enviarFila`` usan
  ``_camposCambiados``.
- R13: «≠ albarán» repintado al teclear.
- R14: «Recalcular importe» y «Recalcular precio» mandan ``cuadrar``.
- R15: «A Sigrid» repintado al teclear, visible solo si difiere de P.

Las funciones se sacan tal cual de ``app.js`` y corren con entradas falsas o con
el DOM falso (``tests/dom_falso.js``).
"""
from __future__ import annotations

import json

import pytest
from test_f051_almacen_front import _app_js, _funcion_js
from test_f065_f1_js import _CAMBIADOS, _ejecutar, con_node
from test_f065_f3bis_front import _ejecutar_dom

from ruesma_comun.edicion_manual import MENSAJE_NO_DESPEJABLE

_FORMATOS = ["precioEs", "cantidadEs", "importeEs"]
_REPINTAR = ["parseNumEs", "importeDeFila", "precioDespejado", "precioASigrid", "textoASigrid",
             "avisoImporte", "marcarNoDespejable", "syncImporteUnitario", *_FORMATOS]


# =================================================================== #
# R11 · P despejado a 6 decimales
# =================================================================== #
@con_node
def test_f106_r11_js_precio_despejado(tmp_path):
    casos = _ejecutar(tmp_path, ["precioDespejado"], """
        console.log(JSON.stringify([
            precioDespejado(104.16, 48, 7), precioDespejado(104.16, 48, null),
            precioDespejado(10, 3, 0), precioDespejado(-18, 2, null),
            precioDespejado(5, 0, null), precioDespejado(5, 2, 100),
            precioDespejado(null, 2, null), precioDespejado(5, null, null),
        ]));
    """)
    assert casos == [2.333333, 2.17, 3.333333, -9, None, None, None, None]


# =================================================================== #
# R15 · A Sigrid
# =================================================================== #
@con_node
def test_f106_r15_js_precio_a_sigrid(tmp_path):
    casos = _ejecutar(tmp_path, ["precioASigrid"], """
        console.log(JSON.stringify([
            precioASigrid(48, 104.16, 1), precioASigrid(1, 120, 6),
            precioASigrid(2, -18, 1), precioASigrid(2, -18, -1),
            precioASigrid(48, 499.97, 1),
            precioASigrid(2, 0, 1), precioASigrid(2, null, 1),
            precioASigrid(0, 10, 1), precioASigrid(2, 10, null),
        ]));
    """)
    assert casos == [
        {"cantidad": 48, "precio": 2.17}, {"cantidad": 6, "precio": 20},
        {"cantidad": -2, "precio": 9}, {"cantidad": -2, "precio": 9},
        {"cantidad": 48, "precio": 10.416042},
        None, None, None, None,
    ]


@con_node
def test_f106_r15_js_formatos_como_la_plantilla(tmp_path):
    casos = _ejecutar(tmp_path, _FORMATOS + ["textoASigrid"], """
        console.log(JSON.stringify({
            precio: [precioEs(120), precioEs(11.2), precioEs(2.333333), precioEs(1234.5),
                     precioEs(-9), precioEs(115.12345)],
            cantidad: [cantidadEs(48), cantidadEs(2.5), cantidadEs(-2), cantidadEs(0.125)],
            importe: [importeEs(104.16), importeEs(1234.5), importeEs(-18)],
            texto: textoASigrid({cantidad: 48, precio: 2.17}),
        }));
    """)
    assert casos == {
        "precio": ["120,00", "11,20", "2,333333", "1.234,50", "-9,00", "115,12345"],
        "cantidad": ["48", "2,5", "-2", "0,125"],
        "importe": ["104,16", "1.234,50", "-18,00"],
        "texto": "A Sigrid: 48 × 2,17 €",
    }


# =================================================================== #
# R13 · ≠ albarán
# =================================================================== #
@con_node
def test_f106_r13_js_aviso_de_importe(tmp_path):
    casos = _ejecutar(tmp_path, ["avisoImporte", "importeEs"], """
        console.log(JSON.stringify([
            avisoImporte(499.97, 104.16), avisoImporte(104.16, 104.16),
            avisoImporte(104.17, 104.16), avisoImporte(null, 104.16), avisoImporte(1, null),
        ]));
    """)
    assert casos == ["≠ albarán: 104,16", None, "≠ albarán: 104,16", None, None]


# =================================================================== #
# R11, R13, R15 · repintar la fila al teclear (DOM falso)
# =================================================================== #
_FILA = """
    const tbody = el("tbody", "", document.body);
    const tr = el("tr", "conciliacion-row concilia-editable", tbody);
    function celda(campo, valor) {
        const inp = el("input", "cell-input js-cedit", el("td", "concilia-td", tr));
        inp.dataset.field = campo; inp.dataset.numeric = "1";
        inp.value = valor; inp.defaultValue = valor;
        return inp;
    }
    const cant = celda("cantidad", "10");
    const pu = celda("precio_unitario", "11.20");
    pu.dataset.factorAlta = "1.0";
    pu.title = "Precio del contrato: 11.2000 €\\nA Sigrid: 10 × 10,416 €";
    const sigrid = el("span", "a-sigrid js-a-sigrid", pu.parentNode);
    sigrid.hidden = true;
    const imp = celda("importe", "104.16");
    imp.dataset.importeAlbaran = "104.16";
    const aviso = el("span", "aviso-importe js-aviso-importe", imp.parentNode);
    aviso.hidden = true;
    const dto = celda("descuento", "7");
    function foto() {
        return {cant: cant.value, pu: pu.value, imp: imp.value, aviso: aviso.hidden ? null : aviso.textContent,
                sigrid: sigrid.hidden ? null : sigrid.textContent, sigridTexto: sigrid.textContent,
                titulo: pu.title, rojo: imp.classList.contains("importe-no-despejable"),
                tituloImporte: imp.title || ""};
    }
"""


def _repintar(tmp_path, programa):
    return _ejecutar_dom(tmp_path, _REPINTAR, _FILA, programa)


@con_node
def test_f106_r11_r13_r15_js_cantidad_repinta_importe_aviso_y_a_sigrid(tmp_path):
    f = _repintar(tmp_path, """
        cant.value = "48"; syncImporteUnitario(tr, "cantidad");
        console.log(JSON.stringify(foto()));
    """)
    assert f["imp"] == "499.97" and f["pu"] == "11.20"
    assert f["aviso"] == "≠ albarán: 104,16"
    assert f["sigrid"] == "A Sigrid: 48 × 10,416042 €"
    assert f["titulo"] == "Precio del contrato: 11.2000 €\nA Sigrid: 48 × 10,416042 €"
    assert f["rojo"] is False


@con_node
def test_f106_r11_r15_js_importe_despeja_p_a_seis_y_el_dto_se_queda(tmp_path):
    f = _repintar(tmp_path, """
        cant.value = "48"; syncImporteUnitario(tr, "cantidad");
        imp.value = "104,16"; syncImporteUnitario(tr, "importe");
        console.log(JSON.stringify(Object.assign(foto(), {dto: dto.value})));
    """)
    assert (f["pu"], f["dto"]) == ("2.333333", "7")
    assert f["aviso"] is None
    # P 2,333333 ≠ 2,17: visible.
    assert f["sigrid"] == "A Sigrid: 48 × 2,17 €"


@con_node
def test_f106_r15_js_a_sigrid_igual_a_p_se_oculta(tmp_path):
    f = _repintar(tmp_path, """
        dto.value = ""; syncImporteUnitario(tr, "descuento");
        console.log(JSON.stringify(foto()));
    """)
    # 10 × 11,20 = 112,00 ⇒ a Sigrid 10 × 11,20 = P.
    assert f["imp"] == "112" and f["sigrid"] is None
    assert f["sigridTexto"] == "A Sigrid: 10 × 11,20 €"


@con_node
@pytest.mark.parametrize(("cantidad", "descuento"), [("0", "7"), ("", "7"), ("10", "100")])
def test_f106_r11_js_sin_divisor_no_repinta_y_marca_en_rojo(tmp_path, cantidad, descuento):
    f = _repintar(tmp_path, f"""
        cant.value = {json.dumps(cantidad)}; dto.value = {json.dumps(descuento)};
        imp.value = "50"; syncImporteUnitario(tr, "importe");
        const rojo = foto();
        imp.value = "0"; syncImporteUnitario(tr, "importe");
        const cero = foto();
        cant.value = "10"; dto.value = "7"; imp.value = "50"; syncImporteUnitario(tr, "importe");
        console.log(JSON.stringify({{rojo: rojo, cero: cero, bien: foto()}}));
    """)
    assert f["rojo"]["pu"] == "11.20" and f["rojo"]["rojo"] is True
    assert f["rojo"]["tituloImporte"] == MENSAJE_NO_DESPEJABLE
    # Importe 0: I = 0 y P se conserva (R7), sin rojo.
    assert f["cero"]["pu"] == "11.20" and f["cero"]["rojo"] is False
    # Con divisor, se quita la marca.
    assert f["bien"]["rojo"] is False and f["bien"]["tituloImporte"] == ""
    assert f["bien"]["pu"] == "5.376344"


@con_node
def test_f106_r13_js_sin_blanca_no_hay_aviso_que_repintar(tmp_path):
    f = _repintar(tmp_path, """
        delete imp.dataset.importeAlbaran;
        cant.value = "48"; syncImporteUnitario(tr, "cantidad");
        console.log(JSON.stringify(foto()));
    """)
    assert f["aviso"] is None and f["imp"] == "499.97"


def test_f106_r11_wire_usa_repintar_fila_y_apunta_la_ultima_celda():
    js = _app_js()
    inicio = js.index("function wireConciliaEdit()")
    cuerpo = js[inicio:js.index("saveBtn.addEventListener", inicio)]
    assert "syncImporteUnitario(tr, inp.dataset.field)" in cuerpo
    assert "ultimoCampo" in cuerpo


# =================================================================== #
# R12 · el cuerpo del PATCH
# =================================================================== #
_FILA_SALMON = """
    function fila_salmon(cambios, ultimo) {
        const base = {codigo_partida: "01.01", descripcion: "PUERTA",
                      cantidad: "8", unidad: "UD", precio_unitario: "115.00",
                      importe: "920.00", descuento: "", codigo_externo: ""};
        const numericos = {cantidad: 1, precio_unitario: 1, importe: 1, descuento: 1};
        const f = fila(Object.keys(base).map(function (k) {
            return entrada(k, base[k], k in cambios ? cambios[k] : base[k],
                           numericos[k] ? {numeric: "1"} : {});
        }));
        f.dataset = ultimo === undefined ? {} : {ultimoCampo: ultimo};
        return f;
    }
"""


@con_node
def test_f106_r12_js_el_importe_viaja_si_fue_lo_ultimo_tecleado(tmp_path):
    casos = _ejecutar(tmp_path, _CAMBIADOS, _FILA_SALMON + """
        console.log(JSON.stringify({
            importe_ultimo: _camposCambiados(fila_salmon(
                {importe: "1000", precio_unitario: "125"}, "importe")),
            importe_con_cantidad: _camposCambiados(fila_salmon(
                {cantidad: "10", importe: "1000", precio_unitario: "100"}, "importe")),
            precio_ultimo: _camposCambiados(fila_salmon(
                {importe: "1000", precio_unitario: "125"}, "precio_unitario")),
            cantidad_ultima: _camposCambiados(fila_salmon(
                {cantidad: "10", importe: "1150"}, "cantidad")),
            dto_ultimo: _camposCambiados(fila_salmon(
                {importe: "1000", precio_unitario: "125", descuento: "10"}, "descuento")),
            importe_igual: _camposCambiados(fila_salmon({}, "importe")),
            sin_rastro: _camposCambiados(fila_salmon({importe: "1000"})),
        }));
    """)
    assert casos["importe_ultimo"] == {"importe": 1000}
    assert casos["importe_con_cantidad"] == {"cantidad": 10, "importe": 1000}
    assert casos["precio_ultimo"] == {"precio_unitario": 125}
    assert casos["cantidad_ultima"] == {"cantidad": 10}
    assert casos["dto_ultimo"] == {"precio_unitario": 125, "descuento": 10}
    assert casos["importe_igual"] == {}
    assert casos["sin_rastro"] == {"importe": 1000}


def test_f106_r12_las_tres_vias_de_enviar_fila_usan_campos_cambiados():
    js = _app_js()
    assert js.count("_camposCambiados(tr, lista.items)") == 3


# =================================================================== #
# R14 · los botones
# =================================================================== #
@con_node
def test_f106_r14_js_cuerpo_de_los_botones(tmp_path):
    casos = _ejecutar(tmp_path, ["cuerpoCuadrar"], """
        console.log(JSON.stringify([cuerpoCuadrar("importe"), cuerpoCuadrar("precio")]));
    """)
    assert casos == [{"cuadrar": "importe"}, {"cuadrar": "precio"}]


def test_f106_r14_los_botones_mandan_por_enviar_fila_y_recargan():
    js = _app_js()
    cuerpo = _funcion_js(js, "wireCuadrar")
    assert ".js-cuadrar" in cuerpo
    assert "enviarFila(vid, cuerpoCuadrar(" in cuerpo
    assert "window.location.reload()" in cuerpo
    assert "wireCuadrar();" in js


# =================================================================== #
# R17 · el motivo de sv9 tiene texto en sv4
# =================================================================== #
def test_f106_r17_texto_del_motivo_linea_no_cuadra():
    from domain.models.alta_sigrid_models import TEXTOS_MOTIVO_ALTA

    assert TEXTOS_MOTIVO_ALTA["linea_no_cuadra"] == (
        "La línea no cuadra (cantidad × precio × (1 − dto) ≠ importe)")
