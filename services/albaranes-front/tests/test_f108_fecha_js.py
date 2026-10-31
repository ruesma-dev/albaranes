# tests/test_f108_fecha_js.py
"""F-108 · D · la fecha en la ficha (``static/app.js``), EJECUTADA con node.

Patrón de ``test_f077_guardar_y_aprobar_js.py``: las funciones se sacan tal
cual de ``app.js`` y corren sobre ``tests/dom_falso.js`` con una ficha
mínima (``#fecha``, el botón del calendario, ``#fecha_calendario`` y
``#fecha-error``) y dobles de ``fetch``, ``alert`` y ``showPicker``.

- R20: ``parseFechaEs`` da lo mismo que Python en toda la tabla ``CASOS``.
- R3: el aviso de ``app.js`` es el de ``AVISO_FECHA_NO_VALIDA``.
- R16, R17: al salir del campo, se reescribe en ``dd/mm/aaaa`` o se marca.
- R19: ``collectPayload`` manda ISO, nulo o lo escrito.
- R14, R15: el calendario (con y sin ``showPicker``).
- R18: «Guardar» y «Guardar y aprobar» con una fecha mala no envían nada.
- R21: ningún manejador nuevo impide teclear.
"""
from __future__ import annotations

import json

import pytest
from test_f051_almacen_front import _app_js, _funcion_js
from test_f065_f1_js import con_node
from test_f065_f3bis_front import _ejecutar_dom
from test_f108_fecha_albaran import CASOS, NO_VALIDA

#: Lo de ``app.js`` que usa la fecha de la ficha.
_FECHA = ["avisoFechaNoValida", "parseFechaEs", "fechaParaVer", "fechaParaEnviar",
          "marcarFechaNoValida", "limpiarMarcaFecha", "fechaEscritaValida", "wireFechaAlbaran"]

# La ficha editable (lo que pinta la plantilla de F-108, §4.4).
_ESCENA = """
    const campo = el("span", "campo-fecha", document.body);
    const fecha = el("input", "", campo);
    fecha.id = "fecha"; fecha.type = "text";
    const boton = el("button", "btn secondary small js-fecha-calendario", campo);
    boton.type = "button";
    const cal = el("input", "fecha-calendario", campo);
    cal.id = "fecha_calendario"; cal.type = "date";
    const error = el("small", "error js-fecha-error", document.body);
    error.id = "fecha-error"; error.hidden = true;
    const alertas = [];
    window.alert = function (m) { alertas.push(m); };
    function alert(m) { alertas.push(m); }
    function marca() {
        return {roja: fecha.classList.contains("campo-no-valido"), oculto: error.hidden,
                aviso: error.textContent, valor: fecha.value,
                invalida: fecha.getAttribute("aria-invalid")};
    }
"""


def _correr(tmp_path, programa, funciones=(), preparacion=""):
    js = _app_js()
    lista = list(funciones) + _FECHA
    faltan = [f for f in lista if f"function {f}(" not in js]
    assert not faltan, f"faltan en app.js: {faltan}"
    return _ejecutar_dom(tmp_path, lista, _ESCENA + preparacion, programa)


def _aviso(texto):
    from domain.services.fecha_albaran import AVISO_FECHA_NO_VALIDA

    return AVISO_FECHA_NO_VALIDA.format(texto=texto)


# =================================================================== #
# R20 · la misma regla que Python, caso a caso
# =================================================================== #
@con_node
def test_f108_r20_parse_fecha_es_da_lo_mismo_que_python(tmp_path):
    textos = [c[0] for c in CASOS]
    salida = _correr(tmp_path, f"""
        const textos = {json.dumps(textos, ensure_ascii=False)};
        console.log(JSON.stringify(textos.map(parseFechaEs)));
    """)

    esperado = [None if e == NO_VALIDA else ("" if e is None else e) for _, e in CASOS]
    assert dict(zip(map(repr, textos), salida)) == dict(zip(map(repr, textos), esperado))


@con_node
def test_f108_r4_fecha_para_ver(tmp_path):
    salida = _correr(tmp_path, """
        console.log(JSON.stringify(["2026-10-28", "2026-06-05", "2024-02-29"].map(fechaParaVer)));
    """)

    assert salida == ["28/10/2026", "05/06/2026", "29/02/2024"]


# =================================================================== #
# R3 · el aviso de app.js es el de Python
# =================================================================== #
@con_node
def test_f108_r3_el_aviso_de_la_ficha_es_el_del_servidor(tmp_path):
    salida = _correr(tmp_path, """
        console.log(JSON.stringify([avisoFechaNoValida("31/02/2026"), avisoFechaNoValida("abc")]));
    """)

    assert salida == [_aviso("31/02/2026"), _aviso("abc")]


# =================================================================== #
# R16, R17 · al salir del campo
# =================================================================== #
@con_node
@pytest.mark.parametrize("escrita, vista", [
    ("28-10-26", "28/10/2026"), ("5.6.2026", "05/06/2026"), ("2026-10-28", "28/10/2026"),
    ("  ", ""),
])
def test_f108_r16_al_salir_se_reescribe_en_dd_mm_aaaa(tmp_path, escrita, vista):
    salida = _correr(tmp_path, f"""
        wireFechaAlbaran();
        fecha.focus();
        teclear(fecha, {json.dumps(escrita)});
        fecha.blur();
        console.log(JSON.stringify(marca()));
    """)

    assert salida == {"roja": False, "oculto": True, "aviso": "", "valor": vista,
                      "invalida": None}


@con_node
def test_f108_r17_al_salir_con_una_fecha_mala_se_marca_y_se_quita_al_corregir(tmp_path):
    salida = _correr(tmp_path, """
        wireFechaAlbaran();
        fecha.focus();
        teclear(fecha, " 31/02/2026 ");
        fecha.blur();
        const mala = marca();
        fecha.focus();
        teclear(fecha, "28/02/2026");
        const corregida = marca();
        fecha.blur();
        console.log(JSON.stringify({mala: mala, corregida: corregida, final: marca()}));
    """)

    assert salida["mala"] == {"roja": True, "oculto": False, "aviso": _aviso("31/02/2026"),
                              "valor": " 31/02/2026 ", "invalida": "true"}
    assert salida["corregida"] == {"roja": False, "oculto": True, "aviso": "",
                                   "valor": "28/02/2026", "invalida": None}
    assert salida["final"]["valor"] == "28/02/2026" and not salida["final"]["roja"]


@con_node
def test_f108_r22_sin_calendario_wire_no_hace_nada(tmp_path):
    """Ficha aprobada: hay ``#fecha`` (solo lectura) pero no botón ni selector."""
    salida = _correr(tmp_path, """
        campo.removeChild(boton);
        campo.removeChild(cal);
        wireFechaAlbaran();
        fecha.focus();
        fecha.value = "31/02/2026";
        fecha.blur();
        console.log(JSON.stringify(marca()));
    """)

    assert salida["roja"] is False and salida["valor"] == "31/02/2026"


# =================================================================== #
# R19 · lo que manda collectPayload
# =================================================================== #
@con_node
@pytest.mark.parametrize("escrita, enviada", [
    ("28/10/2026", "2026-10-28"), ("1-1-26", "2026-01-01"), ("", None), ("   ", None),
    (" 31/02/2026 ", "31/02/2026"), ("abc", "abc"),
])
def test_f108_r19_collect_payload_manda_iso_nulo_o_lo_escrito(tmp_path, escrita, enviada):
    salida = _correr(tmp_path, f"""
        fecha.value = {json.dumps(escrita)};
        console.log(JSON.stringify(collectPayload(false)));
    """, funciones=["collectSelectedContratoCodigo", "collectPayload"])

    assert salida["fecha"] == enviada


@con_node
def test_f108_r19_sin_campo_de_fecha_manda_nulo(tmp_path):
    salida = _correr(tmp_path, """
        campo.removeChild(fecha);
        console.log(JSON.stringify(collectPayload(false)));
    """, funciones=["collectSelectedContratoCodigo", "collectPayload"])

    assert salida["fecha"] is None


def test_f108_r19_collect_payload_usa_fecha_para_enviar():
    fuente = _funcion_js(_app_js(), "collectPayload")

    assert "fecha: fechaParaEnviar()," in fuente
    assert 'getInput("fecha")' not in fuente


# =================================================================== #
# R14 · el botón abre el selector nativo en el día escrito
# =================================================================== #
_PICKER = """
    const abiertos = [];
    cal.showPicker = function () { abiertos.push(cal.value); };
"""


@con_node
@pytest.mark.parametrize("escrita, dia", [("28-10-26", "2026-10-28"), ("abc", ""), ("", "")])
def test_f108_r14_el_boton_abre_el_selector_en_el_dia_escrito(tmp_path, escrita, dia):
    salida = _correr(tmp_path, f"""
        wireFechaAlbaran();
        fecha.value = {json.dumps(escrita)};
        boton.click();
        console.log(JSON.stringify({{abiertos: abiertos, visible: cal.classList.contains("visible"),
                                     valor: fecha.value}}));
    """, preparacion=_PICKER)

    assert salida == {"abiertos": [dia], "visible": False, "valor": escrita}


@con_node
@pytest.mark.parametrize("picker", ["", "cal.showPicker = function () { throw new Error('NotAllowed'); };"],
                         ids=["sin_showPicker", "showPicker_falla"])
def test_f108_r14_sin_show_picker_el_selector_queda_visible_y_con_el_foco(tmp_path, picker):
    salida = _correr(tmp_path, """
        wireFechaAlbaran();
        fecha.value = "5/6/2026";
        boton.click();
        console.log(JSON.stringify({visible: cal.classList.contains("visible"),
                                    foco: document.activeElement === cal, dia: cal.value}));
    """, preparacion=picker)

    assert salida == {"visible": True, "foco": True, "dia": "2026-06-05"}


# =================================================================== #
# R15 · elegir un día lo escribe en dd/mm/aaaa y quita la marca
# =================================================================== #
@con_node
def test_f108_r15_elegir_un_dia_lo_escribe_y_quita_la_marca(tmp_path):
    salida = _correr(tmp_path, """
        wireFechaAlbaran();
        fecha.focus();
        teclear(fecha, "31/02/2026");
        fecha.blur();
        const antes = marca();
        cal.classList.add("visible");
        cal.value = "2026-11-03";
        cal.dispatchEvent(new Event("change", {bubbles: true}));
        console.log(JSON.stringify({antes: antes.roja, despues: marca(),
                                    visible: cal.classList.contains("visible")}));
    """)

    assert salida["antes"] is True
    assert salida["despues"] == {"roja": False, "oculto": True, "aviso": "", "valor": "03/11/2026",
                                 "invalida": None}
    assert salida["visible"] is False


@con_node
def test_f108_r15_un_change_sin_dia_no_borra_lo_escrito(tmp_path):
    salida = _correr(tmp_path, """
        wireFechaAlbaran();
        fecha.value = "28/10/2026";
        cal.value = "";
        cal.dispatchEvent(new Event("change", {bubbles: true}));
        console.log(JSON.stringify(marca()));
    """)

    assert salida["valor"] == "28/10/2026"


# =================================================================== #
# R18 · «Guardar» / «Guardar y aprobar» con una fecha mala: nada enviado
# =================================================================== #
def _correr_guardar(tmp_path, programa):
    from test_f077_guardar_y_aprobar_js import _ESCENA as ESCENA_F077
    from test_f077_guardar_y_aprobar_js import _FUNCIONES as FUNCIONES_F077
    from test_f077_guardar_y_aprobar_js import AVISO_GET, AVISO_PINTADO

    preparacion = ("const AVISO_PINTADO = " + json.dumps(AVISO_PINTADO) + ";\n"
                   + "const AVISO_GET = " + json.dumps(AVISO_GET) + ";\n" + ESCENA_F077 + """
        const fecha = el("input", "", document.body);
        fecha.id = "fecha";
        const error = el("small", "error", document.body);
        error.id = "fecha-error"; error.hidden = true;
    """)
    return _ejecutar_dom(tmp_path, FUNCIONES_F077 + _FECHA, preparacion, programa + """
        console.log(JSON.stringify(Object.assign(estado(), {
            roja: fecha.classList.contains("campo-no-valido"), foco: document.activeElement === fecha,
            aviso: error.textContent, oculto: error.hidden})));
    """)


@con_node
@pytest.mark.parametrize("aprobar", [True, False])
def test_f108_r18_con_fecha_mala_no_se_envia_nada(tmp_path, aprobar):
    salida = _correr_guardar(tmp_path, f"""
        f1.cant.value = "6";
        fecha.value = " 31/02/2026 ";
        await guardarCabecera({json.dumps(aprobar)});
    """)

    assert salida["peticiones"] == []
    assert salida["alertas"] == [_aviso("31/02/2026")]
    assert salida["confirmaciones"] == []
    assert salida["roja"] is True and salida["foco"] is True
    assert salida["aviso"] == _aviso("31/02/2026") and salida["oculto"] is False
    assert salida["guardarActivo"] and salida["aprobarActivo"]


@con_node
def test_f108_r18_corregida_se_guarda_con_la_fecha_en_iso(tmp_path):
    salida = _correr_guardar(tmp_path, """
        fecha.value = "31/02/2026";
        await guardarCabecera(false);
        fecha.value = "28/02/2026";
        await guardarCabecera(false);
    """)

    assert len(salida["peticiones"]) == 1
    metodo, _url, cuerpo = salida["peticiones"][0].split(" ", 2)
    assert metodo == "PUT" and json.loads(cuerpo)["fecha"] == "2026-02-28"


@con_node
def test_f108_r18_vacia_no_para_el_guardado(tmp_path):
    """Sin fecha se puede guardar (R6); aprobar lo para el servidor (R11)."""
    salida = _correr_guardar(tmp_path, """
        fecha.value = "";
        await guardarCabecera(false);
    """)

    assert len(salida["peticiones"]) == 1 and salida["alertas"] == []
    assert json.loads(salida["peticiones"][0].split(" ", 2)[2])["fecha"] is None


def test_f108_r18_la_guarda_va_antes_de_desactivar_y_de_guardar_filas():
    fuente = _funcion_js(_app_js(), "guardarCabecera")

    guarda = fuente.index("fechaEscritaValida()")
    assert guarda < fuente.index("b.disabled = true")
    assert guarda < fuente.index("guardarFilasPendientes()")


# =================================================================== #
# R21 · los manejadores nuevos no impiden teclear
# =================================================================== #
@con_node
def test_f108_r21_ninguna_tecla_queda_impedida(tmp_path):
    teclas = ["Enter", "F7", "F8", "Escape", "1", "/", "Backspace", "Delete", "ArrowLeft", "Tab"]
    salida = _correr(tmp_path, f"""
        wireFechaAlbaran();
        const impedidas = [];
        [fecha, boton, cal].forEach(function (destino) {{
            {json.dumps(teclas)}.forEach(function (k) {{
                if (tecla(destino, k).defaultPrevented) {{ impedidas.push(destino.id + ":" + k); }}
            }});
        }});
        console.log(JSON.stringify(impedidas));
    """)

    assert salida == []


def test_f108_r21_el_codigo_nuevo_no_llama_a_prevent_default():
    js = _app_js()
    for nombre in _FECHA:
        assert "preventDefault" not in _funcion_js(js, nombre), nombre
