# tests/test_f115_js_confirmacion.py
"""F-115 R14, R15 · la ficha pide confirmación antes de cambiar proveedor u obra.

- R14: elegir en el combo un proveedor distinto del actual, con contrato
  seleccionado o con valoración, pide confirmación antes del auto-guardado:
  «Cambiar el proveedor quita el contrato <código> y vuelve a buscar contratos
  y a valorar. Las líneas leídas se conservan[ y N puestas a mano].
  ¿Continuar?». Cancelar deja el combo con el proveedor anterior y no guarda.
- R15: lo mismo con la obra («Cambiar la obra…»), que conserva el proveedor.
- R19: el mismo CIF con otro formato no pregunta.

``avisoCambioCabecera`` (pura) y ``choose`` se sacan tal cual de ``app.js``
(patrón de ``test_f065_f1_js.py``) y se ejecutan con node y dobles mínimos.
"""
from __future__ import annotations

import json
import shutil
import subprocess

import pytest
from test_f051_almacen_front import _app_js, _funcion_js

_NODE = shutil.which("node")
con_node = pytest.mark.skipif(
    _NODE is None, reason="node no está instalado: el JS no se puede ejecutar",
)

_FUNCIONES = ["_normCif", "_normObra", "avisoCambioCabecera"]


def _ejecutar(tmp_path, funciones, programa):
    js = _app_js()
    fuente = "\n".join(_funcion_js(js, f) for f in funciones)
    guion = tmp_path / "f115.js"
    guion.write_text(fuente + "\n" + programa, encoding="utf-8")
    salida = subprocess.run(
        [_NODE, str(guion)], capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout)


def _aviso(tmp_path, kind, previo, nuevo, doc):
    return _ejecutar(tmp_path, _FUNCIONES, f"""
        console.log(JSON.stringify(avisoCambioCabecera(
            {json.dumps(kind)}, {json.dumps(previo)}, {json.dumps(nuevo)}, {json.dumps(doc)})));
    """)


CON_CONTRATO = {"selected_contrato_codigo": "CTA/0001", "valuation": {"id": "v"},
                "n_filas_manuales": 0}


# =================================================================== #
# R14 · el texto
# =================================================================== #
@con_node
def test_f115_r14_js_proveedor_con_contrato_pide_confirmacion(tmp_path):
    assert _aviso(tmp_path, "proveedor", "A11111111", "B22222222", CON_CONTRATO) == (
        "Cambiar el proveedor quita el contrato CTA/0001 y vuelve a buscar contratos y a "
        "valorar. Las líneas leídas se conservan. ¿Continuar?"
    )


@con_node
@pytest.mark.parametrize(("n", "cola"), [(1, " y 1 puesta a mano"), (3, " y 3 puestas a mano")])
def test_f115_r14_js_cuenta_las_puestas_a_mano(tmp_path, n, cola):
    doc = dict(CON_CONTRATO, n_filas_manuales=n)
    assert _aviso(tmp_path, "proveedor", "A11111111", "B22222222", doc) == (
        "Cambiar el proveedor quita el contrato CTA/0001 y vuelve a buscar contratos y a "
        f"valorar. Las líneas leídas se conservan{cola}. ¿Continuar?"
    )


@con_node
def test_f115_r14_js_solo_valoracion_sin_contrato_tambien_pregunta(tmp_path):
    doc = {"selected_contrato_codigo": None, "valuation": {"id": "v"}, "n_filas_manuales": 0}
    assert _aviso(tmp_path, "proveedor", "A11111111", "B22222222", doc) == (
        "Cambiar el proveedor vuelve a buscar contratos y a valorar. "
        "Las líneas leídas se conservan. ¿Continuar?"
    )


@con_node
def test_f115_r14_js_sin_contrato_ni_valoracion_no_pregunta(tmp_path):
    doc = {"selected_contrato_codigo": None, "valuation": None, "n_filas_manuales": 2}
    assert _aviso(tmp_path, "proveedor", "A11111111", "B22222222", doc) is None


@con_node
@pytest.mark.parametrize("nuevo", ["A11111111", "a-11111111", " a 11111111 ", "ESA11111111"])
def test_f115_r19_js_mismo_proveedor_con_otro_formato_no_pregunta(tmp_path, nuevo):
    assert _aviso(tmp_path, "proveedor", "A11111111", nuevo, CON_CONTRATO) is None


# =================================================================== #
# R15 · la obra
# =================================================================== #
@con_node
def test_f115_r15_js_obra_pide_confirmacion_y_conserva_el_proveedor(tmp_path):
    assert _aviso(tmp_path, "obra", "0686", "0700", CON_CONTRATO) == (
        "Cambiar la obra quita el contrato CTA/0001 y vuelve a buscar los contratos del "
        "mismo proveedor en la nueva obra y a valorar. Las líneas leídas se conservan. "
        "¿Continuar?"
    )


@con_node
@pytest.mark.parametrize("nueva", ["0686", "686", " 0686 "])
def test_f115_r15_js_misma_obra_con_otro_formato_no_pregunta(tmp_path, nueva):
    assert _aviso(tmp_path, "obra", "0686", nueva, CON_CONTRATO) is None


# =================================================================== #
# R14, R15 · ``choose``: confirmar guarda, cancelar deja todo como estaba
# =================================================================== #
_DOBLES = """
const campos = {
    proveedor_cif: {value: "A11111111"}, proveedor_nombre: {value: "PROVEEDOR A"},
    obra_codigo: {value: "0686"}, obra_nombre: {value: "OBRA"},
    obra_direccion: {value: "CALLE 1"},
};
const document = {getElementById: function (id) { return campos[id] || null; }};
let respuesta = true;
const preguntas = [];
const window = {confirm: function (t) { preguntas.push(t); return respuesta; }};
let guardados = 0;
function sendSave() { guardados += 1; }
const panel = {hidden: false};
function close() { panel.hidden = true; }
"""


def _choose(tmp_path, *, kind, confirma, doc, elegido):
    val = "proveedor_cif" if kind == "proveedor" else "obra_codigo"
    nombre = "proveedor_nombre" if kind == "proveedor" else "obra_nombre"
    previo = "A11111111 · PROVEEDOR A" if kind == "proveedor" else "0686 · OBRA"
    return _ejecutar(tmp_path, _FUNCIONES + ["choose"], _DOBLES + f"""
        const DOC_DATA = {json.dumps(doc)};
        const kind = {json.dumps(kind)};
        const valInputId = {json.dumps(val)};
        const nombreInputId = {json.dumps(nombre)};
        const combo = {{dataset: {{label: {json.dumps(previo)}}}}};
        const input = {{value: "lo que tecleó"}};
        respuesta = {json.dumps(confirma)};
        choose({json.dumps(elegido)});
        console.log(JSON.stringify({{
            val: campos[valInputId].value, nombre: campos[nombreInputId].value,
            direccion: campos.obra_direccion.value, input: input.value,
            label: combo.dataset.label, guardados: guardados, preguntas: preguntas,
            cerrado: panel.hidden,
        }}));
    """)


_B = {"val": "B22222222", "nombre": "PROVEEDOR B", "label": "B22222222 · PROVEEDOR B"}
_OBRA = {"val": "0700", "nombre": "OBRA NUEVA", "label": "0700 · OBRA NUEVA"}


@con_node
def test_f115_r14_js_choose_cancelar_deja_el_proveedor_anterior_y_no_guarda(tmp_path):
    r = _choose(tmp_path, kind="proveedor", confirma=False, doc=CON_CONTRATO, elegido=_B)
    assert (r["val"], r["nombre"]) == ("A11111111", "PROVEEDOR A")
    assert (r["input"], r["label"]) == ("A11111111 · PROVEEDOR A", "A11111111 · PROVEEDOR A")
    assert r["guardados"] == 0
    assert len(r["preguntas"]) == 1 and r["cerrado"] is True


@con_node
def test_f115_r14_js_choose_confirmar_guarda_con_el_proveedor_nuevo(tmp_path):
    r = _choose(tmp_path, kind="proveedor", confirma=True, doc=CON_CONTRATO, elegido=_B)
    assert (r["val"], r["nombre"], r["label"]) == ("B22222222", "PROVEEDOR B", _B["label"])
    assert r["guardados"] == 1
    assert r["preguntas"][0].startswith("Cambiar el proveedor quita el contrato CTA/0001")


@con_node
def test_f115_r14_js_choose_sin_contrato_ni_valoracion_guarda_sin_preguntar(tmp_path):
    doc = {"selected_contrato_codigo": None, "valuation": None, "n_filas_manuales": 0}
    r = _choose(tmp_path, kind="proveedor", confirma=False, doc=doc, elegido=_B)
    assert r["preguntas"] == [] and r["guardados"] == 1


@con_node
def test_f115_r15_js_choose_cancelar_la_obra_no_borra_la_direccion(tmp_path):
    r = _choose(tmp_path, kind="obra", confirma=False, doc=CON_CONTRATO, elegido=_OBRA)
    assert (r["val"], r["nombre"], r["direccion"]) == ("0686", "OBRA", "CALLE 1")
    assert r["input"] == "0686 · OBRA" and r["guardados"] == 0
    assert r["preguntas"][0].startswith("Cambiar la obra quita el contrato CTA/0001")


@con_node
def test_f115_r15_js_choose_confirmar_la_obra_guarda_y_vacia_la_direccion(tmp_path):
    r = _choose(tmp_path, kind="obra", confirma=True, doc=CON_CONTRATO, elegido=_OBRA)
    assert (r["val"], r["direccion"], r["guardados"]) == ("0700", "", 1)
