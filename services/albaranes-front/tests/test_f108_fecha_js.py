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
