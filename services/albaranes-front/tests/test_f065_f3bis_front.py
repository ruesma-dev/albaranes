# tests/test_f065_f3bis_front.py
"""F-065 · fase 3 bis · ajustes de front de las MANUAL T19/T27 (design §5.5).

- R29 v3: F7 abre «Dividir» y F6 ya no (queda para el navegador); la última
  parte de la ventana se rellena sola (Q − las demás), es de solo lectura y
  sale en rojo si queda a 0 o de otro signo; «Aceptar», con la regla de
  siempre. La columna «Acciones» no oculta nunca sus botones (y vuelve el
  bloque de columnas que T24 borró por error).
- R27 v3: el combo de partida no se reabre al elegir; al teclear, la lista
  vuelve arriba y «al», «alm», «almacén»… dejan «Almacén» marcada.

El JS se EJECUTA con node sobre un DOM mínimo (``tests/dom_falso.js``): las
funciones se sacan tal cual de ``static/app.js`` (patrón de
``test_f051_almacen_front.py``) y lo que no es suyo se sustituye por dobles.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from test_f051_almacen_front import _app_js, _funcion_js
from test_f065_f1_js import _NODE, con_node

_RAIZ = Path(__file__).resolve().parent.parent
_DOM = (Path(__file__).resolve().parent / "dom_falso.js").read_text(encoding="utf-8")


def _ejecutar_dom(tmp_path, funciones, preparacion, programa):
    """Ejecuta ``programa`` (cuerpo de una función ``async``) con el DOM falso,
    las ``funciones`` de ``app.js`` y la ``preparacion`` (dobles y elementos,
    en el ámbito global: es donde las funciones de ``app.js`` los buscan);
    devuelve el JSON que imprime."""
    js = _app_js()
    fuente = "\n".join(_funcion_js(js, f) for f in funciones)
    guion = tmp_path / "f065_3bis.js"
    guion.write_text(
        _DOM + "\n" + fuente + "\n" + preparacion + "\n(async function () {\n" + programa + "\n})()"
        ".catch(function (e) { console.error(e && e.stack || e); process.exit(1); });\n",
        encoding="utf-8",
    )
    salida = subprocess.run(
        [_NODE, str(guion)], capture_output=True, text=True, encoding="utf-8", check=False,
    )
    assert salida.returncode == 0, salida.stderr
    return json.loads(salida.stdout)


# =================================================================== #
# La ventana de «Dividir»: F7 y la última parte automática (R29 v3)
# =================================================================== #
_DIVIDIR = ["parseNumEs", "faltaPorRepartir", "repartoValido", "cuerpoDivision",
            "estadoReparto", "wireDividir"]

# Una fila con su «Dividir» (Q y partida en data-*) y la ventana de la
# plantilla, vacía. Lo que wireDividir usa y no es suyo, con dobles.
_FICHA = """
    const tabla = el("tbody", "", document.body);
    const tr = el("tr", "conciliacion-row concilia-editable", tabla);
    const celda = el("input", "js-cedit", el("td", "", tr));
    const boton = el("button", "js-dividir", el("td", "", tr));
    boton.dataset.valuationLineId = "12";
    boton.dataset.q = Q;
    boton.dataset.partida = "01.01";
    const dlg = el("dialog", "", document.body);
    dlg.id = "dividir-dialog";
    el("strong", "js-dividir-q", dlg);
    const nEl = el("input", "js-dividir-n", dlg);
    const cuerpo = el("tbody", "js-dividir-partes", dlg);
    const faltaEl = el("p", "js-dividir-falta", dlg);
    el("p", "js-dividir-error", dlg);
    const aceptar = el("button", "js-dividir-aceptar", dlg);
    el("button", "js-dividir-cancelar", dlg);
    var linesBody = tabla;
    var documentId = "DOC";
    function attachPartidaCombo() {}
    function contarFilasConCambios() { return 0; }
    function avisoFilasSinGuardar() { return ""; }
    let enviado = null;
    function fetch(url, init) {
        enviado = {url: url, cuerpo: JSON.parse(init.body)};
        return Promise.resolve({ok: true});
    }
    wireDividir();
    function cantidades() { return cuerpo.querySelectorAll(".js-dividir-cantidad"); }
    function ultima() { const c = cantidades(); return c[c.length - 1]; }
    function foto() {
        return {
            valores: cantidades().map(function (i) { return i.value; }),
            mal: ultima().classList.contains("dividir-resto-mal"),
            mensaje: faltaEl.textContent,
            aceptar: !aceptar.disabled,
        };
    }
"""


def _ficha(q="18"):
    return "const Q = " + json.dumps(q) + ";\n" + _FICHA


@con_node
def test_f065_r29v3_f7_abre_dividir_y_f6_no(tmp_path):
    casos = _ejecutar_dom(tmp_path, _DIVIDIR, _ficha(), """
        celda.focus();
        const f6 = tecla(celda, "F6");
        const trasF6 = {abierta: dlg.open, prevenida: f6.defaultPrevented};
        const f7 = tecla(celda, "F7");
        console.log(JSON.stringify({
            f6: trasF6,
            f7: {abierta: dlg.open, prevenida: f7.defaultPrevented},
        }));
    """)

    assert casos == {
        "f6": {"abierta": False, "prevenida": False},  # F6 es del navegador
        "f7": {"abierta": True, "prevenida": True},
    }


@con_node
def test_f065_r29v3_f7_fuera_de_una_fila_no_hace_nada(tmp_path):
    casos = _ejecutar_dom(tmp_path, _DIVIDIR, _ficha(), """
        const fuera = el("input", "", document.body);
        fuera.focus();
        const f7 = tecla(fuera, "F7");
        console.log(JSON.stringify({abierta: dlg.open, prevenida: f7.defaultPrevented}));
    """)

    assert casos == {"abierta": False, "prevenida": False}


def test_f065_r29v3_f7_en_titulos_y_nada_del_duplicar_antiguo():
    js = _app_js()
    plantilla = (_RAIZ / "templates" / "document_detail.html").read_text(encoding="utf-8")
    css = (_RAIZ / "static" / "styles.css").read_text(encoding="utf-8")

    assert '"F7"' in js and '"F6"' not in js
    assert "duplicateRow" not in js and "camposBody" not in js and "Duplicar" not in js
    assert "(F7)" in plantilla and "(F6)" not in plantilla
    assert not re.search(r"\bF6\b", plantilla + css)


@con_node
def test_f065_r29v3_f7_con_la_ventana_abierta_no_la_reinicia(tmp_path):
    casos = _ejecutar_dom(tmp_path, _DIVIDIR, _ficha(), """
        celda.focus();
        tecla(celda, "F7");
        teclear(cantidades()[0], "6");
        celda.focus();
        const otra = tecla(celda, "F7");
        console.log(JSON.stringify({valores: foto().valores, prevenida: otra.defaultPrevented}));
    """)

    assert casos == {"valores": ["6", "12"], "prevenida": False}


@con_node
def test_f065_r29v3_ultima_parte_se_rellena_sola(tmp_path):
    casos = _ejecutar_dom(tmp_path, _DIVIDIR, _ficha(), """
        boton.dispatchEvent(new Event("click"));
        const u = ultima();
        const inicial = foto();
        const forma = {soloLectura: u.readOnly, sinTab: u.tabIndex, auto: u.classList.contains("dividir-auto"),
                       primeraEditable: !cantidades()[0].readOnly, foco: document.activeElement === cantidades()[0]};
        teclear(cantidades()[0], "6");
        const seis = foto();
        teclear(cantidades()[0], "20");
        const veinte = foto();
        teclear(cantidades()[0], "18");
        const dieciocho = foto();
        teclear(cantidades()[0], "6");
        teclear(nEl, "3");
        const tres = foto();
        teclear(cantidades()[1], "7");
        const completo = foto();
        aceptar.dispatchEvent(new Event("click"));
        await tiempo();
        console.log(JSON.stringify({inicial, forma, seis, veinte, dieciocho, tres, completo, enviado}));
    """)

    assert casos["forma"] == {"soloLectura": True, "sinTab": -1, "auto": True,
                              "primeraEditable": True, "foco": True}
    assert casos["inicial"] == {"valores": ["", "18"], "mal": False,
                                "mensaje": "Falta la cantidad de la parte 1.", "aceptar": False}
    # Con 2 partes basta teclear la primera.
    assert casos["seis"] == {"valores": ["6", "12"], "mal": False,
                             "mensaje": "Reparto completo.", "aceptar": True}
    # Las demás se pasan: la última en rojo, negativa, y «Aceptar» apagado.
    assert casos["veinte"] == {"valores": ["20", "-2"], "mal": True, "mensaje": "Sobra: 2", "aceptar": False}
    # Las demás suman la original: la última quedaría a 0.
    assert casos["dieciocho"] == {"valores": ["18", "0"], "mal": True,
                                  "mensaje": "La última parte quedaría a 0.", "aceptar": False}
    # Al pasar a 3 se conservan las editables (no el resto viejo, que era 12).
    assert casos["tres"] == {"valores": ["6", "", "12"], "mal": False,
                             "mensaje": "Falta la cantidad de la parte 2.", "aceptar": False}
    assert casos["completo"] == {"valores": ["6", "7", "5"], "mal": False,
                                 "mensaje": "Reparto completo.", "aceptar": True}
    assert casos["enviado"] == {"url": "/api/documents/DOC/lines/12/dividir", "cuerpo": {"partes": [
        {"cantidad": 6, "codigo_partida": "01.01"},
        {"cantidad": 7, "codigo_partida": "01.01"},
        {"cantidad": 5, "codigo_partida": "01.01"},
    ]}}


@con_node
def test_f065_r29v3_ultima_parte_con_decimales_y_negativas(tmp_path):
    casos = _ejecutar_dom(tmp_path, _DIVIDIR, _ficha("10.25"), """
        boton.dispatchEvent(new Event("click"));
        teclear(cantidades()[0], "4,1");
        const decimales = foto();
        teclear(cantidades()[0], "10,2549");
        const casi = foto();
        console.log(JSON.stringify({decimales, casi}));
    """)

    assert casos["decimales"] == {"valores": ["4,1", "6,15"], "mal": False,
                                  "mensaje": "Reparto completo.", "aceptar": True}
    # Sin el redondeo a milésimas de antes: el resto es exacto (y negativo).
    assert casos["casi"]["valores"] == ["10,2549", "-0,0049"] and casos["casi"]["mal"] is True


@con_node
def test_f065_r29v3_estado_del_reparto(tmp_path):
    casos = _ejecutar_dom(tmp_path, ["parseNumEs", "faltaPorRepartir", "estadoReparto"], "", """
        console.log(JSON.stringify([
            estadoReparto(18, ["6"]),
            estadoReparto(18, ["6", ""]),
            estadoReparto(18, ["6", "abc"]),
            estadoReparto(18, ["6", "0"]),
            estadoReparto(18, ["6", "-1"]),
            estadoReparto(18, ["10", "9"]),
            estadoReparto(18, ["10", "8"]),
            estadoReparto(-10, ["-4"]),
            estadoReparto(-10, ["4"]),
            estadoReparto(-10, ["-12"]),
            estadoReparto(1, ["0,1", "0,2"]),
            estadoReparto(-10, ["-10"]),
            estadoReparto(-10, ["0"]),
            estadoReparto(-10, ["-4", "1"]),
        ]));
    """)

    def e(resto, mal, mensaje):
        return {"resto": resto, "ultimaMal": mal, "mensaje": mensaje}

    assert casos == [
        e(12, False, "Reparto completo."),
        e(12, False, "Falta la cantidad de la parte 2."),
        e(12, False, "Falta la cantidad de la parte 2."),
        e(12, False, "La parte 2 no puede ser 0 ni de otro signo."),
        e(13, False, "La parte 2 no puede ser 0 ni de otro signo."),
        e(-1, True, "Sobra: 1"),
        e(0, True, "La última parte quedaría a 0."),
        e(-6, False, "Reparto completo."),
        e(-14, False, "La parte 1 no puede ser 0 ni de otro signo."),
        e(2, True, "Sobra: 2"),
        e(0.7, False, "Reparto completo."),
        e(0, True, "La última parte quedaría a 0."),
        e(-10, False, "La parte 1 no puede ser 0 ni de otro signo."),
        e(-7, False, "La parte 2 no puede ser 0 ni de otro signo."),
    ]


# =================================================================== #
# El combo de partida (R27 v3)
# =================================================================== #
_COMBO = ["_normLine", "opcionesPartida", "partidaValida", "siguienteActivo", "_scrollActive",
          "attachPartidaCombo"]

# Una fila con su partida; las partidas de la obra (algunas con «al»), sin
# red; «Almacén» de la fila, con un doble que cuenta.
_FILA_COMBO = """
    const tr = el("tr", "conciliacion-row concilia-editable", document.body);
    const td = el("td", "", tr);
    const inp = el("input", "js-partida-combo", td);
    inp.value = "";  // sin partida: al abrir, la lista entera
    let avisos = 0;
    tr.addEventListener("input", function () { avisos += 1; });  // wireConciliaEdit
    let almacen = 0;
    function elegirAlmacen() { almacen += 1; }
    const ITEMS = ["01.01 · Cimentación", "02.03 · Puertas", "03.01 · Instalaciones",
                   "04.02 · Saneamiento general", "05.01 · Albañilería", "06.07 · Metales"]
        .map(function (l) { return {code: l.split(" · ")[0], label: l, norm: _normLine(l)}; });
    function cargarPartidasObra() { return Promise.resolve({items: ITEMS, error: false}); }
    attachPartidaCombo(inp);
    const panel = td.querySelector(".combo-panel");
    function activa() {
        const a = panel.children.filter(function (d) { return d.classList.contains("active"); });
        return a.length ? a[0].textContent : null;
    }
"""


@con_node
def test_f065_r27v3_combo_elegir_con_el_raton_lo_deja_cerrado(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILA_COMBO, """
        inp.focus();
        await tiempo();
        const abierto = !panel.hidden;
        panel.children[2].dispatchEvent(new Event("mousedown"));
        await tiempo();
        console.log(JSON.stringify({abierto, cerrado: panel.hidden, valor: inp.value, avisos,
                                    foco: document.activeElement === inp}));
    """)

    assert casos == {"abierto": True, "cerrado": True, "valor": "02.03", "avisos": 1, "foco": True}


@con_node
def test_f065_r27v3_combo_elegir_con_enter_lo_deja_cerrado(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILA_COMBO, """
        inp.focus();
        await tiempo();
        tecla(inp, "ArrowDown");
        tecla(inp, "ArrowDown");
        const enter = tecla(inp, "Enter");
        await tiempo();
        const tras = {cerrado: panel.hidden, valor: inp.value, avisos, prevenido: enter.defaultPrevented};
        // Con la lista cerrada, el siguiente Enter ya no es del combo (es el «Guardar» de la fila).
        const otro = tecla(inp, "Enter");
        await tiempo();
        console.log(JSON.stringify({tras, otro: {prevenido: otro.defaultPrevented, cerrado: panel.hidden}}));
    """)

    assert casos == {
        "tras": {"cerrado": True, "valor": "01.01", "avisos": 1, "prevenido": True},
        "otro": {"prevenido": False, "cerrado": True},
    }


@con_node
def test_f065_r27v3_combo_teclear_sigue_abriendo_la_lista(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.focus();
        await tiempo();
        tecla(inp, "Escape");
        const cerrado = panel.hidden;
        teclear(inp, "puer");
        await tiempo();
        console.log(JSON.stringify({cerrado, abierto: !panel.hidden,
                                    opciones: panel.children.map(function (d) { return d.textContent; })}));
    """)

    assert casos == {"cerrado": True, "abierto": True,
                     "opciones": ["Almacén (sin partida)", "02.03 · Puertas"]}


@con_node
def test_f065_r27v3_combo_al_marca_almacen_arriba(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.focus();
        await tiempo();
        tecla(inp, "ArrowDown");
        tecla(inp, "ArrowDown");
        tecla(inp, "ArrowDown");
        const antes = activa();
        panel.scrollTop = 150;  // la lista quedó bajada
        teclear(inp, "al");
        await tiempo();
        const tras = {activa: activa(), arriba: panel.scrollTop, primera: panel.children[0].textContent};
        const enter = tecla(inp, "Enter");
        await tiempo();
        console.log(JSON.stringify({antes, tras, almacen, cerrado: panel.hidden, prevenido: enter.defaultPrevented}));
    """)

    assert casos == {
        "antes": "02.03 · Puertas",
        "tras": {"activa": "Almacén (sin partida)", "arriba": 0, "primera": "Almacén (sin partida)"},
        "almacen": 1,
        "cerrado": True,
        "prevenido": True,
    }


@con_node
def test_f065_r27v3_combo_otro_texto_vuelve_arriba_sin_marcar(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.focus();
        await tiempo();
        tecla(inp, "ArrowDown");
        tecla(inp, "ArrowDown");
        panel.scrollTop = 90;
        teclear(inp, "0");
        await tiempo();
        console.log(JSON.stringify({activa: activa(), arriba: panel.scrollTop}));
    """)

    assert casos == {"activa": None, "arriba": 0}


@con_node
def test_f065_r27v3_que_cuenta_como_almacen(tmp_path):
    casos = _ejecutar_dom(tmp_path, ["_normLine", "esAlmacenTecleado"], "", """
        console.log(JSON.stringify([
            "a", "al", "AL", " alm ", "almacén", "ALMACEN", "Almacén (sin partida)", "almacenes",
            "", "  ", "01", "cal", "ala", "alb", "almacenar", "macen", "cen", "lmac"
        ].map(esAlmacenTecleado)));
    """)

    assert casos == [True, True, True, True, True, True, True, True,
                     False, False, False, False, False, False, True, False, False, False]


# Pasada 2, CR1 · R27 «solo admite valores de la lista» también tras elegir:
# el combo queda cerrado con el foco dentro y lo siguiente que se teclea NO
# es «el valor de antes» (antes de CR1, open(true) lo capturaba como tal y el
# blur o el Esc lo dejaban puesto).
@con_node
def test_f065_cr1_elegir_y_teclear_algo_fuera_de_la_lista_vuelve_la_elegida_al_salir(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.focus();
        await tiempo();
        panel.children[2].dispatchEvent(new Event("mousedown"));
        await tiempo();
        teclear(inp, "02.0x");
        await tiempo();
        inp.blur();
        await tiempo();
        console.log(JSON.stringify({valor: inp.value, cerrado: panel.hidden}));
    """)

    assert casos == {"valor": "02.03", "cerrado": True}


@con_node
def test_f065_cr1_elegir_teclear_y_esc_vuelve_la_elegida(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.focus();
        await tiempo();
        panel.children[2].dispatchEvent(new Event("mousedown"));
        await tiempo();
        teclear(inp, "02.0x");
        await tiempo();
        const esc = tecla(inp, "Escape");
        await tiempo();
        console.log(JSON.stringify({valor: inp.value, cerrado: panel.hidden, prevenido: esc.defaultPrevented}));
    """)

    assert casos == {"valor": "02.03", "cerrado": True, "prevenido": True}


@con_node
def test_f065_cr1_foco_esc_teclear_y_salir_vuelve_la_original(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.value = "01.01";
        inp.focus();
        await tiempo();
        tecla(inp, "Escape");
        teclear(inp, "zz");
        await tiempo();
        inp.blur();
        await tiempo();
        console.log(JSON.stringify({valor: inp.value, cerrado: panel.hidden}));
    """)

    assert casos == {"valor": "01.01", "cerrado": True}


@con_node
def test_f065_cr1_tras_elegir_teclear_vuelve_a_abrir_la_lista(tmp_path):
    """Elegir no deja el combo «mudo»: la tecla siguiente abre la lista filtrada."""
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.focus();
        await tiempo();
        panel.children[2].dispatchEvent(new Event("mousedown"));
        await tiempo();
        const cerrado = panel.hidden;
        teclear(inp, "puer");
        await tiempo();
        console.log(JSON.stringify({cerrado, abierto: !panel.hidden,
                                    opciones: panel.children.map(function (d) { return d.textContent; })}));
    """)

    assert casos == {"cerrado": True, "abierto": True,
                     "opciones": ["Almacén (sin partida)", "02.03 · Puertas"]}


@con_node
def test_f065_cr1_teclear_pinchar_en_la_casilla_y_salir_vuelve_la_original(tmp_path):
    """Con la lista ABIERTA, pinchar otra vez en la casilla no convierte lo
    tecleado en «el valor de antes» (solo se toma al abrirla)."""
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.value = "01.01";
        inp.focus();
        await tiempo();
        teclear(inp, "zz");
        await tiempo();
        inp.dispatchEvent(new Event("click", {bubbles: true}));
        await tiempo();
        const abierto = !panel.hidden;
        inp.blur();
        await tiempo();
        console.log(JSON.stringify({abierto, valor: inp.value}));
    """)

    assert casos == {"abierto": True, "valor": "01.01"}


@con_node
def test_f065_cr1_teclear_una_valida_y_salir_la_deja(tmp_path):
    """La otra cara: lo que SÍ es de la lista se queda al salir."""
    casos = _ejecutar_dom(tmp_path, _COMBO + ["esAlmacenTecleado"], _FILA_COMBO, """
        inp.focus();
        await tiempo();
        panel.children[2].dispatchEvent(new Event("mousedown"));
        await tiempo();
        teclear(inp, "05.01");
        await tiempo();
        inp.blur();
        await tiempo();
        console.log(JSON.stringify({valor: inp.value}));
    """)

    assert casos == {"valor": "05.01"}


# =================================================================== #
# «Acciones» sin recortar y las columnas de vuelta (R29 v3)
# =================================================================== #
def _regla_css(css, selector):
    """Cuerpo de la ÚLTIMA regla con exactamente ese selector (la que manda)."""
    cuerpos = re.findall(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    assert cuerpos, selector
    return cuerpos[-1]


def test_f065_r29v3_acciones_siempre_a_la_vista():
    """Lo que vio el humano: con una fila «Desbloquear» la tabla se ensanchaba y
    «Guardar» y «Dividir» quedaban fuera de la vista (scroll horizontal). La
    columna va pegada a la derecha, opaca, y sus botones bajan de línea antes
    que recortarse."""
    css = (_RAIZ / "static" / "styles.css").read_text(encoding="utf-8")

    celda = _regla_css(css, ".salmon-table td.td-acciones")
    cabecera = _regla_css(css, '.salmon-table thead tr.salmon-head th[data-col="acciones"]')
    boton = _regla_css(css, ".salmon-table td.td-acciones .btn")
    for regla in (celda, cabecera):
        assert "position: sticky" in regla and "right: 0" in regla
    assert "nowrap" not in celda
    assert "overflow: visible" in celda
    assert "white-space: nowrap" in boton  # cada botón entero


# Pasada 2, CR2 · que la regla no solo EXISTA sino que GANE la cascada. Un
# mini motor de cascada: qué reglas de styles.css casan con la celda y la
# cabecera de «Acciones» tal como las pinta la plantilla, y cuál manda en cada
# propiedad (especificidad y, a igualdad, la última). Simplificaciones, del
# lado prudente para lo que se mira aquí: sin !important; una pseudoclase
# (:hover, :nth-child…), un pseudoelemento (::before), un atributo con otro
# operador que «=» o un combinador «+»/«~» hacen que la regla NO case (en
# styles.css ninguna de esas fija position, right, z-index, overflow ni
# white-space en estas celdas); las @media se toman como si aplicaran.
_SIMPLE = r"::?[\w-]+(?:\([^)]*\))?|[#.][\w-]+|\[[^\]]+\]"
_COMPUESTO = re.compile(r"^([a-z*]+)?((?:" + _SIMPLE + r")*)$", re.I)


def _partes(compuesto):
    m = _COMPUESTO.match(compuesto)
    assert m, compuesto
    return (m.group(1) or "").lower(), re.findall(_SIMPLE, m.group(2))


def _especificidad(selector):
    a = b = c = 0
    for compuesto in re.split(r"\s*>\s*|\s+", selector.strip()):
        tag, simples = _partes(compuesto)
        c += 1 if tag and tag != "*" else 0
        a += sum(1 for s in simples if s.startswith("#"))
        b += sum(1 for s in simples if not s.startswith("#"))
    return (a, b, c)


def _casa_compuesto(compuesto, nodo):
    tag, simples = _partes(compuesto)
    if tag and tag != "*" and tag != nodo["tag"]:
        return False
    for s in simples:
        if s.startswith("#") and nodo.get("id") != s[1:]:
            return False
        if s.startswith(".") and s[1:] not in nodo.get("clases", ()):
            return False
        if s.startswith(":"):
            return False
        if s.startswith("["):
            m = re.match(r'^\[([\w-]+)(?:="([^"]*)")?\]$', s)
            atributos = nodo.get("atributos", {})
            if not m or m.group(1) not in atributos or (
                    m.group(2) is not None and atributos[m.group(1)] != m.group(2)):
                return False
    return True


def _casa(selector, cadena):
    """``cadena``: del elemento hacia arriba ([elemento, padre, abuelo…])."""
    if re.search(r"[+~]", selector):
        return False
    tokens = re.split(r"(\s*>\s*|\s+)", selector.strip())
    compuestos, combinadores = tokens[0::2], [x.strip() or " " for x in tokens[1::2]]

    def desde(i_comp, i_nodo):
        if not _casa_compuesto(compuestos[i_comp], cadena[i_nodo]):
            return False
        if i_comp == 0:
            return True
        if combinadores[i_comp - 1] == ">":
            return i_nodo + 1 < len(cadena) and desde(i_comp - 1, i_nodo + 1)
        return any(desde(i_comp - 1, j) for j in range(i_nodo + 1, len(cadena)))

    return desde(len(compuestos) - 1, 0)


def _gana(css, cadena, propiedad, *, puede_faltar=False):
    """Valor de ``propiedad`` que manda en el elemento de ``cadena`` y su
    selector; ``(None, None)`` si ninguna regla la fija y ``puede_faltar``."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    candidatos = []
    for orden, m in enumerate(re.finditer(r"([^{}@]+)\{([^{}]*)\}", css)):
        valores = re.findall(r"(?:^|;)\s*" + re.escape(propiedad) + r"\s*:\s*([^;]+)", m.group(2))
        if not valores:
            continue
        for selector in m.group(1).split(","):
            selector = selector.strip()
            if selector and _casa(selector, cadena):
                candidatos.append((_especificidad(selector), orden, valores[-1].strip(), selector))
    if not candidatos and puede_faltar:
        return None, None
    assert candidatos, propiedad
    ganador = max(candidatos)
    return ganador[2], ganador[3]


_TABLA = {"tag": "table", "id": "lines-table", "clases": {"table", "editable-table", "salmon-table"}}
_CABECERA = [
    {"tag": "th", "atributos": {"data-col": "acciones", "data-col-fixed": ""}},
    {"tag": "tr", "clases": {"salmon-head"}},
    {"tag": "thead"},
    _TABLA,
]
_CELDA = [
    {"tag": "td", "clases": {"concilia-td", "td-acciones"}, "atributos": {"data-col": "acciones"}},
    {"tag": "tr", "clases": {"conciliacion-row", "salmon-row", "concilia-contract", "concilia-editable"}},
    {"tag": "tbody"},
    _TABLA,
]


def test_f065_cr2_el_motor_de_cascada_se_comporta():
    """El motor en sí: especificidad, combinadores y orden."""
    assert _especificidad(".salmon-table thead tr.salmon-head th") == (0, 2, 3)
    assert _especificidad('.salmon-table thead th[data-col="acciones"]') == (0, 2, 2)
    assert _especificidad("#lines-table td.line-index-cell") == (1, 1, 1)
    assert _casa("tr.conciliacion-row > td.concilia-td", _CELDA)
    assert not _casa("thead > td.concilia-td", _CELDA)
    assert not _casa(".docs-table td", _CELDA)
    assert not _casa(".salmon-table tbody tr:hover td.concilia-td", _CELDA)
    css = (".a td { position: relative; } .salmon-table td.td-acciones { position: sticky; } "
           "td.td-acciones { position: static; } .x::before { position: fixed; } td + td { position: fixed; }")
    assert _gana(css, _CELDA, "position") == ("sticky", ".salmon-table td.td-acciones")
    css = ".salmon-table td { position: sticky; } table td { position: static; } .salmon-table td { position: fixed; }"
    assert _gana(css, _CELDA, "position")[0] == "fixed"


def test_f065_cr2_la_cabecera_de_acciones_gana_la_cascada():
    """Antes, ``.salmon-table thead tr.salmon-head th`` (0,2,3) le ganaba con
    ``position: relative`` y la cabecera se iba con el scroll."""
    css = (_RAIZ / "static" / "styles.css").read_text(encoding="utf-8")

    assert _gana(css, _CABECERA, "position")[0] == "sticky"
    assert _gana(css, _CABECERA, "right")[0] == "0"
    assert _gana(css, _CABECERA, "background")[0].startswith("var(--brand")  # opaca
    assert _gana(css, _CABECERA, "cursor")[0] == "default"  # fija: no se arrastra
    assert "rgba" in _gana(css, _CABECERA, "box-shadow")[0]


def test_f065_cr2_la_celda_de_acciones_gana_la_cascada():
    css = (_RAIZ / "static" / "styles.css").read_text(encoding="utf-8")

    assert _gana(css, _CELDA, "position")[0] == "sticky"
    assert _gana(css, _CELDA, "right")[0] == "0"
    assert _gana(css, _CELDA, "overflow")[0] == "visible"
    # Sin nowrap (los botones bajan de línea): ninguna regla se lo pone a la celda.
    assert _gana(css, _CELDA, "white-space", puede_faltar=True)[0] in (None, "normal")
    for k in range(1, len(_CELDA)):  # ni la hereda de la fila, el tbody o la tabla
        assert _gana(css, _CELDA[k:], "white-space", puede_faltar=True)[0] in (None, "normal")
    assert _gana(css, _CELDA, "text-align")[0] == "right"
    assert "rgba" in _gana(css, _CELDA, "box-shadow")[0]
    # Opaca: el fondo que manda es el de la fila (#f7f4f5), sin transparencia.
    fondo, selector = _gana(css, _CELDA, "background")
    assert fondo == "#f7f4f5" and selector == "tr.conciliacion-row > td.concilia-td"
    boton = [{"tag": "button", "clases": {"btn", "small", "success", "js-cedit-save"}}] + _CELDA
    assert _gana(css, boton, "white-space")[0] == "nowrap"  # cada botón entero


def test_f065_r29v3_acciones_ancho_estable_y_botones_compactos():
    """El ancho no depende de qué botones salgan: columna fija (no se arrastra
    a otro sitio: es la pegada a la derecha) con su ancho por defecto, y
    «Borrar» compacto (✕ con su title)."""
    plantilla = (_RAIZ / "templates" / "document_detail.html").read_text(encoding="utf-8")

    assert '<col data-col="acciones" data-w="200">' in plantilla
    assert '<th data-col="acciones" data-col-fixed>' in plantilla
    borrar = re.search(r'<button[^>]*js-concilia-remove[^>]*>([^<]*)</button>', plantilla)
    assert borrar and borrar.group(1) == "✕"
    assert 'aria-label="Borrar"' in borrar.group(0) and 'title="Borrar esta línea' in borrar.group(0)
    for etiqueta in ("Guardar", "Dividir", "Desbloquear"):  # la lógica de qué botones salen, igual
        assert re.search(r'<button[^>]*>' + etiqueta + '</button>', plantilla), etiqueta


def test_f065_r29v3_columnas_el_bloque_esta_cableado():
    js = _app_js()

    assert 'var gridApi = enhanceTable(document.getElementById("lines-table"));' in js
    assert "document.querySelectorAll('table[data-cols-store]')" in js  # también la bandeja
    assert 'document.getElementById("reset-cols-btn")' in js
    assert "gridApi.reset()" in js


_LOCAL_STORAGE = """
    const LS = {};
    const localStorage = {
        getItem: function (k) { return k in LS ? LS[k] : null; },
        setItem: function (k, v) { LS[k] = String(v); },
        removeItem: function (k) { delete LS[k]; },
    };
    var MIN_W = 56;
"""


@con_node
def test_f065_r29v3_columnas_anchos_orden_y_restablecer(tmp_path):
    casos = _ejecutar_dom(tmp_path, ["rj", "wj", "enhanceTable"], _LOCAL_STORAGE, """
        const tabla = el("table", "", document.body);
        tabla.setAttribute("data-cols-store", "t");
        tabla.setAttribute("data-resizable", "1");
        const cg = el("colgroup", "", tabla);
        const htr = el("tr", "", el("thead", "", tabla));
        const fila = el("tr", "", el("tbody", "", tabla));
        [["partida", 150], ["acciones", 230]].forEach(function (c) {
            const col = el("col", "", cg);
            col.setAttribute("data-col", c[0]);
            col.setAttribute("data-w", String(c[1]));
            el("th", "", htr).setAttribute("data-col", c[0]);
            el("td", "", fila).setAttribute("data-col", c[0]);
        });
        LS["t.width.v1"] = JSON.stringify({partida: 20});  // por debajo del mínimo: no vale
        LS["t.order.v1"] = JSON.stringify(["acciones", "partida"]);
        function orden(tr) { return tr.children.map(function (n) { return n.getAttribute("data-col"); }); }
        const api = enhanceTable(tabla);
        const guardado = {
            cabecera: orden(htr), fila: orden(fila),
            anchos: cg.children.map(function (c) { return [c.getAttribute("data-col"), c.style.width]; }),
            tabla: tabla.style.width,
        };
        api.reset();
        console.log(JSON.stringify({guardado, reset: {cabecera: orden(htr), fila: orden(fila), claves: Object.keys(LS)}}));
    """)

    assert casos == {
        "guardado": {
            "cabecera": ["acciones", "partida"], "fila": ["acciones", "partida"],
            "anchos": [["acciones", "230px"], ["partida", "150px"]],
            "tabla": "380px",
        },
        "reset": {"cabecera": ["partida", "acciones"], "fila": ["partida", "acciones"], "claves": []},
    }
