# tests/test_f065_f1_js.py
"""F-065 · fase 1 · el JS de la ficha (``static/app.js``), EJECUTADO con node.

- R1: el PUT de la cabecera ya no manda ``lines`` ni ``valuation_line_updates``.
- R8, R9: el PATCH de una fila lleva solo los campos que el administrativo
  cambió, comparando números como números.
- R12: el importe que se repinta al teclear es ``Q × precio × (1 − dto)``.
- R13, R18: «Guardar» de la fila y «Guardar todas» bloquean (``?bloquear=1``);
  «Guardar todas» solo manda las filas con cambios.
- R19: (sustituido por F-077 R1–R10: «Guardar» y «Guardar y aprobar» guardan
  antes las filas; sus tests viven en ``test_f077_guardar_y_aprobar_js.py``).
- R21: confirmación con las dos sumas antes de aprobar.
- R22: confirmación antes de revalorar si hay filas tocadas a mano.
- R23: «Traer líneas contrato» exige la cantidad de cada línea elegida.
- R14, R15: filas guardadas fuera de los masivos y botón «Desbloquear».

Las funciones se sacan tal cual de ``app.js`` (patrón de
``test_f051_almacen_front.py``) y se les pasan entradas falsas.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess

import pytest
from test_f051_almacen_front import _app_js, _funcion_js

_NODE = shutil.which("node")
con_node = pytest.mark.skipif(
    _NODE is None, reason="node no está instalado: el JS no se puede ejecutar",
)

_PRELUDIO = """
function entrada(field, defecto, valor, extra) {
    return {value: valor, defaultValue: defecto,
            dataset: Object.assign({field: field}, extra || {})};
}
function fila(entradas) {
    return {querySelectorAll: function () { return entradas; }};
}
"""


def _ejecutar(tmp_path, funciones, programa):
    js = _app_js()
    fuente = "\n".join(_funcion_js(js, f) for f in funciones)
    guion = tmp_path / "f065.js"
    guion.write_text(fuente + "\n" + _PRELUDIO + "\n" + programa, encoding="utf-8")
    salida = subprocess.run(
        [_NODE, str(guion)], capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout)


def _bloque(js, desde, hasta=None):
    inicio = js.index(desde)
    return js[inicio:js.index(hasta, inicio)] if hasta else js[inicio:]


_CAMBIADOS = ["parseNumEs", "numerosIguales", "partidaParaEnviar", "_camposCambiados"]


# =================================================================== #
# R8, R9 · solo los campos cambiados
# =================================================================== #
@con_node
def test_f065_r8_js_solo_viajan_los_campos_cambiados(tmp_path):
    casos = _ejecutar(tmp_path, _CAMBIADOS, """
        function fila_salmon(cambios) {
            const base = {codigo_partida: "01.01", descripcion: "PUERTA",
                          cantidad: "8", unidad: "UD", precio_unitario: "115.0000",
                          importe: "920.00", descuento: "", codigo_externo: ""};
            const numericos = {cantidad: 1, precio_unitario: 1, importe: 1, descuento: 1};
            return fila(Object.keys(base).map(function (k) {
                return entrada(k, base[k], k in cambios ? cambios[k] : base[k],
                               numericos[k] ? {numeric: "1"} : {});
            }));
        }
        console.log(JSON.stringify({
            nada: _camposCambiados(fila_salmon({})),
            cantidad: _camposCambiados(fila_salmon({cantidad: "6"})),
            mismo_numero_con_coma: _camposCambiados(fila_salmon({precio_unitario: "115,0"})),
            mismo_numero_sin_decimales: _camposCambiados(fila_salmon({cantidad: "8,000"})),
            precio: _camposCambiados(fila_salmon({precio_unitario: "120"})),
            importe_solo_ajusta_el_precio: _camposCambiados(fila_salmon({importe: "1000"})),
            descuento_vaciado: _camposCambiados(fila_salmon({descuento: ""})),
            descuento_puesto: _camposCambiados(fila_salmon({descuento: "10"})),
            partida_vaciada: _camposCambiados(fila_salmon({codigo_partida: ""})),
            descripcion: _camposCambiados(fila_salmon({descripcion: " PUERTA IZQ "})),
            cantidad_borrada: _camposCambiados(fila_salmon({cantidad: ""})),
        }));
    """)

    assert casos["nada"] == {}
    assert casos["cantidad"] == {"cantidad": 6}
    assert casos["mismo_numero_con_coma"] == {}
    assert casos["mismo_numero_sin_decimales"] == {}
    assert casos["precio"] == {"precio_unitario": 120}
    assert casos["importe_solo_ajusta_el_precio"] == {}
    assert casos["descuento_vaciado"] == {}
    assert casos["descuento_puesto"] == {"descuento": 10}
    assert casos["partida_vaciada"] == {"codigo_partida": ""}
    assert casos["descripcion"] == {"descripcion": "PUERTA IZQ"}
    assert casos["cantidad_borrada"] == {"cantidad": None}


@con_node
def test_f065_r8_js_numeros_iguales(tmp_path):
    casos = _ejecutar(tmp_path, ["numerosIguales"], """
        console.log(JSON.stringify([
            numerosIguales(null, null), numerosIguales(1, null), numerosIguales(null, 1),
            numerosIguales(12.5, 12.5000000001), numerosIguales(12.5, 12.5001),
            numerosIguales(0.0045, 0.004),
        ]));
    """)

    assert casos == [True, False, False, True, False, False]


def test_f065_r8_los_dos_guardados_usan_campos_cambiados():
    js = _app_js()
    fila_guardar = _bloque(js, 'saveBtn.addEventListener("click"',
                           'getElementById("save-all-lines-btn")')
    todas = _bloque(js, 'saveAllLinesBtn.addEventListener("click"', "if (addLineBtn)")

    assert "_camposCambiados(tr" in fila_guardar  # F-098: (tr, lista.items)
    # F-077 R12: «Guardar todas» elige las filas con filasConCambios (que usa
    # _camposCambiados) y las dos envían con enviarFila, el único PATCH con
    # ?bloquear=1 del fichero.
    assert "filasConCambios(" in todas and "_camposCambiados(tr" in todas
    assert "_conciliaBody" not in js
    assert "enviarFila(" in fila_guardar and "enviarFila(" in todas
    assert "?bloquear=1" in _funcion_js(js, "enviarFila")


# =================================================================== #
# R18 · «Guardar todas» solo las filas con cambios
# =================================================================== #
@con_node
def test_f065_r18_js_cuenta_las_filas_con_cambios(tmp_path):
    """F-077 R12: ``filasConCambios`` sustituye a ``contarFilasConCambios``
    (devuelve las filas, y deja fuera las que no tienen id de valoración)."""
    casos = _ejecutar(tmp_path, _CAMBIADOS + ["filasConCambios"], """
        function con_vid(f, vid) { f.dataset = {forValuationLineId: vid}; return f; }
        const limpia = con_vid(fila([entrada("cantidad", "8", "8", {numeric: "1"})]), "1");
        const sucia = con_vid(fila([entrada("cantidad", "8", "6", {numeric: "1"})]), "2");
        const sucia2 = con_vid(fila([entrada("cantidad", "8", "6", {numeric: "1"})]), " 3 ");
        const sin_vid = con_vid(fila([entrada("cantidad", "8", "6", {numeric: "1"})]), "  ");
        console.log(JSON.stringify([
            filasConCambios([]).length, filasConCambios([limpia, limpia]).length,
            filasConCambios([limpia, sucia, sin_vid, sucia2]).map(function (f) { return f.dataset.forValuationLineId; }),
        ]));
    """)

    assert casos == [0, 0, ["2", " 3 "]]


def test_f065_r18_guardar_todas_salta_las_filas_sin_cambios_y_avisa_si_no_hay():
    todas = _bloque(_app_js(), 'saveAllLinesBtn.addEventListener("click"', "if (addLineBtn)")

    assert "No hay cambios en las líneas" in todas
    assert "filasConCambios(" in todas  # F-077 R12: el filtro vive en la función compartida


# R19 (F-065) sustituido por F-077 R1–R10: sus tests (orden «filas ⇒ PUT»,
# sin el aviso «Hay N líneas…») están en test_f077_guardar_y_aprobar_js.py.


# =================================================================== #
# R1 · el PUT de la cabecera sin líneas
# =================================================================== #
@con_node
def test_f065_r1_js_el_put_no_lleva_lineas(tmp_path):
    cuerpo = _ejecutar(tmp_path, ["collectSelectedContratoCodigo", "collectPayload"], """
        var document = {getElementById: function (id) { return {value: " v-" + id + " "}; }};
        console.log(JSON.stringify(collectPayload(true)));
    """)

    assert "lines" not in cuerpo and "valuation_line_updates" not in cuerpo
    assert cuerpo["approved"] is True and cuerpo["numero_albaran"] == "v-numero_albaran"
    assert "collectLinesAndValuationUpdates" not in _app_js()


# =================================================================== #
# R21 · confirmación con las dos sumas
# =================================================================== #
def test_f065_r21_aprobar_confirma_con_el_aviso_de_la_suma():
    guardar = _bloque(_app_js(), "function guardarCabecera(", "if (saveBtn)")

    assert "approveBtn.dataset.avisoSuma" in guardar
    assert re.search(r"window\.confirm\(\s*aviso\s*\)", guardar)


# =================================================================== #
# R22 · confirmación antes de revalorar
# =================================================================== #
@con_node
def test_f065_r22_js_aviso_de_revalorar(tmp_path):
    casos = _ejecutar(tmp_path, ["avisoRevalorar"], """
        console.log(JSON.stringify([avisoRevalorar(0), avisoRevalorar(2), avisoRevalorar(undefined)]));
    """)

    assert casos == [None, "Revalorar descarta 2 líneas tocadas a mano. ¿Continuar?", None]


@con_node
def test_f065_r22_js_confirmar_revalorar(tmp_path):
    casos = _ejecutar(tmp_path, ["avisoRevalorar", "confirmarRevalorar"], """
        var preguntas = [];
        var window = {confirm: function (t) { preguntas.push(t); return false; }};
        var DOC_DATA = {n_filas_manuales: 0};
        const sin = confirmarRevalorar();
        DOC_DATA = {n_filas_manuales: 3};
        const con = confirmarRevalorar();
        console.log(JSON.stringify({sin: sin, con: con, preguntas: preguntas}));
    """)

    assert casos == {"sin": True, "con": False,
                     "preguntas": ["Revalorar descarta 3 líneas tocadas a mano. ¿Continuar?"]}


def test_f065_r22_las_tres_vias_de_revalorar_confirman_antes():
    js = _app_js()
    valorar = _bloque(js, 'valuateBtn.addEventListener("click"', "});")
    contrato = _bloque(js, "async function onPick(codigo)", "await persistSelection();")
    volver_a_buscar = _bloque(js, "async function handleSaveAndRefetch()", "const savePayload")

    for bloque in (valorar, contrato, volver_a_buscar):
        assert "confirmarRevalorar()" in bloque


# =================================================================== #
# R12 · el importe al teclear
# =================================================================== #
@con_node
def test_f065_r12_js_importe_de_la_fila(tmp_path):
    casos = _ejecutar(tmp_path, ["importeDeFila"], """
        console.log(JSON.stringify([
            importeDeFila(2, 120, null), importeDeFila(1, 120, 10), importeDeFila(3000, 0.05, 0),
            importeDeFila(null, 120, 0), importeDeFila(2, null, 0), importeDeFila(1, 0.333, 0),
        ]));
    """)

    assert casos == [240, 108, 150, None, None, 0.33]


def test_f065_r12_al_teclear_se_repinta_con_esa_formula():
    sync = _funcion_js(_app_js(), "syncImporteUnitario")

    assert "importeDeFila(" in sync


# =================================================================== #
# R23 · traer con cantidad
# =================================================================== #
@con_node
def test_f065_r23_js_lineas_a_traer(tmp_path):
    casos = _ejecutar(tmp_path, ["parseNumEs", "lineasATraer"], """
        console.log(JSON.stringify({
            ok: lineasATraer([{id: 503, valor: "5"}, {id: 501, valor: "2,5"}]),
            falta: lineasATraer([{id: 503, valor: "5"}, {id: 501, valor: ""}]),
            cero: lineasATraer([{id: 503, valor: "0"}]),
            ilegible: lineasATraer([{id: 503, valor: "x"}]),
            ninguna: lineasATraer([]),
        }));
    """)

    assert casos["ok"] == [{"contrato_line_id": 503, "cantidad": 5},
                           {"contrato_line_id": 501, "cantidad": 2.5}]
    assert casos["falta"] is None and casos["cero"] is None
    assert casos["ilegible"] is None and casos["ninguna"] is None


def test_f065_r23_incorporar_manda_las_lineas_con_cantidad():
    traer = _bloque(_app_js(), "(function wireTraerContrato()", "})();")

    assert "lineasATraer(" in traer
    assert "lineas:" in traer and "contrato_line_ids" not in traer


# =================================================================== #
# R14, R15 · filas guardadas: fuera de los masivos y «Desbloquear»
# =================================================================== #
def test_f065_r14_borrar_todas_salta_las_filas_guardadas_y_lo_dice():
    js = _app_js()
    casadas = _funcion_js(js, "collectVidsCasadas")
    borrar = _bloque(js, "bulkDeleteBtn.addEventListener(", "// F-051 (R16, R17)")

    assert 'data-bloqueada' in casadas
    assert "guardadas" in borrar


def test_f065_r14_almacen_a_todas_dice_cuantas_se_salto():
    almacen = _bloque(_app_js(), "almacenTodasBtn.addEventListener(", "if (bulkCopyBtn)")

    assert "saltadas" in almacen


def test_f065_r15_desbloquear_llama_al_post_y_recarga():
    desbloquear = _bloque(_app_js(), '".js-desbloquear"', "});")

    assert "/desbloquear`" in desbloquear and 'method: "POST"' in desbloquear
    assert "window.location.reload()" in desbloquear
