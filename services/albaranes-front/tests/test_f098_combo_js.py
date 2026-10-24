# services/albaranes-front/tests/test_f098_combo_js.py
"""F-098 · el combo de partida por capítulo (``static/app.js``), EJECUTADO con node.

- R14, R18, R20: ``partidasDeRespuesta`` lee el código completo, el capítulo y
  ``cod_repetido``; la etiqueta es ``completo · descripción agregada``.
- R15, R16: chips «Todas» + uno por capítulo; con un chip, solo sus hojas.
- R17: el capítulo vale para todos los combos y se recuerda por obra
  (``localStorage``, con ``try/catch``: si lanza, «Todas»).
- R19: como mucho 100 partidas y «N partidas más: escribe para afinar».
- R21, R22: se pinta el completo y se manda el cod; vale el completo o el cod.

Patrón de ``test_f065_f1_js.py`` (funciones puras) y ``test_f065_f3bis_front.py``
(combo con ``tests/dom_falso.js``).
"""
from __future__ import annotations

from test_f065_f1_js import _ejecutar, con_node
from test_f065_f3bis_front import _ejecutar_dom

#: Respuesta de ``GET /api/sigrid/partidas?obra=0686`` (forma de R14).
_RESPUESTA = """
const RESP = {ok: true, items: [
    {ide: 2, codigo: "98.01", codigo_completo: "ANT.98.01", capitulo: "ANT.", descripcion: "Anticipos",
     descripcion_agregada: "AJUSTES ALMACÉN › Anticipos", cod_repetido: false},
    {ide: 13, codigo: "99.01.64", codigo_completo: "CD.99.01.64", capitulo: "CD", descripcion: "Material de obra",
     descripcion_agregada: "VARIOS › VARIOS OBRA › Material de obra", cod_repetido: false},
    {ide: 14, codigo: "99.01.65", codigo_completo: "CD.99.01.65", capitulo: "CD", descripcion: "Otro material",
     descripcion_agregada: "VARIOS › VARIOS OBRA › Otro material", cod_repetido: true},
    {ide: 21, codigo: "CI.4.18", codigo_completo: "CI.4.18", capitulo: "CI", descripcion: "Costes indirectos",
     descripcion_agregada: "COSTES INDIRECTOS › Costes indirectos de obra", cod_repetido: false},
    {ide: 31, codigo: "99.01.65", codigo_completo: "CP.99.01.65", capitulo: "CP", descripcion: "Otro material",
     descripcion_agregada: "COSTES PREVISTOS › Otro material", cod_repetido: true},
], capitulos: [
    {codigo: "ANT.", descripcion: "AJUSTES ALMACÉN", n: 1},
    {codigo: "CD", descripcion: "COSTES DIRECTOS", n: 2},
    {codigo: "CI", descripcion: "COSTES INDIRECTOS", n: 1},
    {codigo: "CP", descripcion: "COSTES PREVISTOS", n: 1},
]};
"""

_PURAS = ["_normLine", "partidasDeRespuesta", "opcionesPartida", "partidaValida", "codigoParaEnviar",
          "partidaParaEnviar"]


# =================================================================== #
# R14, R18, R20 · partidasDeRespuesta
# =================================================================== #
@con_node
def test_f098_r18_r20_partidas_de_la_respuesta(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, _RESPUESTA + """
        const r = partidasDeRespuesta(RESP);
        console.log(JSON.stringify({
            r: r,
            caido: partidasDeRespuesta({ok: false, items: []}),
            nada: partidasDeRespuesta(null),
            sin_capitulos: partidasDeRespuesta({ok: true, items: [{codigo: "01.01", descripcion: "X"}]}),
            capitulo_nulo: partidasDeRespuesta({ok: true, items: [{codigo: "01.01", capitulo: null}],
                                                capitulos: [{codigo: null, descripcion: null, n: 1}]}),
        }));
    """)

    r = casos["r"]
    assert r["error"] is False
    assert [i["code"] for i in r["items"]] == ["98.01", "99.01.64", "99.01.65", "CI.4.18", "99.01.65"]
    assert [i["completo"] for i in r["items"]] == ["ANT.98.01", "CD.99.01.64", "CD.99.01.65", "CI.4.18",
                                                   "CP.99.01.65"]
    assert [i["capitulo"] for i in r["items"]] == ["ANT.", "CD", "CD", "CI", "CP"]
    assert r["items"][1]["label"] == "CD.99.01.64 · VARIOS › VARIOS OBRA › Material de obra"
    assert r["items"][1]["repetido"] is False
    assert r["items"][2]["label"] == ("CD.99.01.65 · VARIOS › VARIOS OBRA › Otro material"
                                      " (código repetido en la obra)")
    assert r["items"][2]["repetido"] is True
    assert r["capitulos"] == [
        {"codigo": "ANT.", "descripcion": "AJUSTES ALMACÉN", "n": 1},
        {"codigo": "CD", "descripcion": "COSTES DIRECTOS", "n": 2},
        {"codigo": "CI", "descripcion": "COSTES INDIRECTOS", "n": 1},
        {"codigo": "CP", "descripcion": "COSTES PREVISTOS", "n": 1},
    ]
    assert casos["caido"] == {"items": [], "capitulos": [], "error": True}
    assert casos["nada"] == {"items": [], "capitulos": [], "error": True}
    # Sin los campos de F-098 (una sv4 vieja): el cod como completo, sin capítulos.
    sin = casos["sin_capitulos"]
    assert sin["capitulos"] == []
    assert (sin["items"][0]["completo"], sin["items"][0]["label"]) == ("01.01", "01.01 · X")
    # Capítulo nulo (hoja sin raíz con código): «» en la hoja y en el chip.
    nulo = casos["capitulo_nulo"]
    assert nulo["items"][0]["capitulo"] == ""
    assert nulo["capitulos"] == [{"codigo": "", "descripcion": None, "n": 1}]


# =================================================================== #
# R16, R18, R19 · opcionesPartida
# =================================================================== #
@con_node
def test_f098_r16_r18_opciones_por_capitulo_y_texto(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, _RESPUESTA + """
        const items = partidasDeRespuesta(RESP).items;
        function c(o) { return {shown: o.shown.map(function (x) { return x.almacen ? "ALM" : x.completo; }),
                                resto: o.resto}; }
        console.log(JSON.stringify({
            todas: c(opcionesPartida(items, "", null)),
            sin_capitulo_arg: c(opcionesPartida(items, "")),
            cd: c(opcionesPartida(items, "", "CD")),
            cd_texto: c(opcionesPartida(items, "otro", "CD")),
            ci: c(opcionesPartida(items, "", "CI")),
            completo_tecleado: c(opcionesPartida(items, "cd.99.01", null)),
            cod_tecleado: c(opcionesPartida(items, "99.01.64", null)),
            palabras: c(opcionesPartida(items, "obra material", null)),
            capitulo_vacio: c(opcionesPartida(items, "", "")),
            aviso: c(opcionesPartida(items, "repetido", null)),
        }));
    """)

    assert casos["todas"] == {"shown": ["ALM", "ANT.98.01", "CD.99.01.64", "CD.99.01.65", "CI.4.18",
                                        "CP.99.01.65"], "resto": 0}
    assert casos["sin_capitulo_arg"] == casos["todas"]
    assert casos["cd"] == {"shown": ["ALM", "CD.99.01.64", "CD.99.01.65"], "resto": 0}
    assert casos["cd_texto"] == {"shown": ["ALM", "CD.99.01.65"], "resto": 0}
    assert casos["ci"] == {"shown": ["ALM", "CI.4.18"], "resto": 0}
    assert casos["completo_tecleado"] == {"shown": ["ALM", "CD.99.01.64", "CD.99.01.65"], "resto": 0}
    assert casos["cod_tecleado"] == {"shown": ["ALM", "CD.99.01.64"], "resto": 0}
    # Por palabras, sin contar el aviso «(código repetido en la obra)».
    assert casos["palabras"] == {"shown": ["ALM", "CD.99.01.64", "CD.99.01.65"], "resto": 0}
    assert casos["capitulo_vacio"] == {"shown": ["ALM"], "resto": 0}
    assert casos["aviso"] == {"shown": ["ALM"], "resto": 0}


@con_node
def test_f098_r19_tope_de_100(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, """
        const items = [];
        for (let i = 0; i < 250; i++) {
            const cod = "01." + String(i).padStart(3, "0");
            items.push({code: cod, completo: "CD." + cod, capitulo: i < 120 ? "CD" : "CI",
                        label: "CD." + cod, norm: "cd." + cod});
        }
        function n(o) { return {shown: o.shown.length, resto: o.resto, primera: o.shown[0].label,
                                ultima: o.shown[o.shown.length - 1].completo}; }
        console.log(JSON.stringify({
            todas: n(opcionesPartida(items, "", null)),
            cd: n(opcionesPartida(items, "", "CD")),
            ci: n(opcionesPartida(items, "", "CI")),
            justo: n(opcionesPartida(items.slice(0, 100), "", null)),
            una_mas: n(opcionesPartida(items.slice(0, 101), "", null)),
            afinado: n(opcionesPartida(items, "01.00", null)),
        }));
    """)

    assert casos["todas"] == {"shown": 101, "resto": 150, "primera": "Almacén (sin partida)",
                              "ultima": "CD.01.099"}
    assert casos["cd"] == {"shown": 101, "resto": 20, "primera": "Almacén (sin partida)", "ultima": "CD.01.099"}
    assert casos["ci"] == {"shown": 101, "resto": 30, "primera": "Almacén (sin partida)", "ultima": "CD.01.219"}
    assert casos["justo"]["resto"] == 0 and casos["justo"]["shown"] == 101
    assert casos["una_mas"]["resto"] == 1 and casos["una_mas"]["shown"] == 101
    assert casos["afinado"] == {"shown": 11, "resto": 0, "primera": "Almacén (sin partida)",
                                "ultima": "CD.01.009"}


# =================================================================== #
# R17 · el capítulo de la ficha, recordado por obra
# =================================================================== #
_ALMACEN = """
var _capituloFicha = {};
var obra = "0686";
var document = {getElementById: function (id) { return id === "obra_codigo" ? {value: " " + obra + " "} : null; }};
var guardado = {};
var window = {localStorage: {
    getItem: function (k) { return k in guardado ? guardado[k] : null; },
    setItem: function (k, v) { guardado[k] = String(v); },
    removeItem: function (k) { delete guardado[k]; },
}};
const CAPS = [{codigo: "CD"}, {codigo: "CI"}, {codigo: ""}];
"""


@con_node
def test_f098_r17_capitulo_recordado_por_obra(tmp_path):
    casos = _ejecutar(tmp_path, ["capituloElegido", "elegirCapitulo"], _ALMACEN + """
        const inicial = capituloElegido(CAPS);
        elegirCapitulo("CD");
        const cd = capituloElegido(CAPS);
        const guardadoCd = JSON.parse(JSON.stringify(guardado));
        obra = "0692";
        const otraObra = capituloElegido(CAPS);
        obra = "0686";
        const vuelta = capituloElegido(CAPS);
        // Otra ficha (memoria vacía) de la misma obra: lo lee del navegador.
        _capituloFicha = {};
        const recargada = capituloElegido(CAPS);
        // Un capítulo que ya no es de la obra cuenta como «Todas».
        const sinCi = capituloElegido([{codigo: "CI"}]);
        elegirCapitulo(null);
        const todas = capituloElegido(CAPS);
        const guardadoTodas = JSON.parse(JSON.stringify(guardado));
        elegirCapitulo("");
        const vacio = capituloElegido(CAPS);
        _capituloFicha = {};
        const vacioRecargado = capituloElegido(CAPS);
        console.log(JSON.stringify({inicial, cd, guardadoCd, otraObra, vuelta, recargada, sinCi, todas,
                                    guardadoTodas, vacio, vacioRecargado}));
    """)

    assert casos == {"inicial": None, "cd": "CD", "guardadoCd": {"f098.capitulo.0686": "CD"},
                     "otraObra": None, "vuelta": "CD", "recargada": "CD", "sinCi": None, "todas": None,
                     "guardadoTodas": {}, "vacio": "", "vacioRecargado": ""}


@con_node
def test_f098_r17_sin_almacenamiento_todas_y_sigue_compartido(tmp_path):
    casos = _ejecutar(tmp_path, ["capituloElegido", "elegirCapitulo"], _ALMACEN + """
        window = {get localStorage() { throw new Error("SecurityError"); }};
        const inicial = capituloElegido(CAPS);
        elegirCapitulo("CI");
        const ci = capituloElegido(CAPS);
        window = {localStorage: {getItem: function () { throw new Error("x"); },
                                 setItem: function () { throw new Error("x"); },
                                 removeItem: function () { throw new Error("x"); }}};
        _capituloFicha = {};
        const lanza = capituloElegido(CAPS);
        elegirCapitulo(null);
        const todas = capituloElegido(CAPS);
        console.log(JSON.stringify({inicial, ci, lanza, todas}));
    """)

    assert casos == {"inicial": None, "ci": "CI", "lanza": None, "todas": None}


# =================================================================== #
# R22 · partidaValida, codigoParaEnviar, partidaParaEnviar
# =================================================================== #
@con_node
def test_f098_r22_valida_completo_o_cod(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, _RESPUESTA + """
        const items = partidasDeRespuesta(RESP).items;
        console.log(JSON.stringify([
            "", "  ", "CD.99.01.64", " CD.99.01.64 ", "99.01.64", "CI.4.18", "ANT.98.01", "98.01",
            "cd.99.01.64", "CD.99.01", "CD", "99.01", "zzz",
        ].map(function (v) { return partidaValida(v, items); })));
    """)

    assert casos == [True, True, True, True, True, True, True, True, False, False, False, False, False]


@con_node
def test_f098_r21_codigo_para_enviar(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, _RESPUESTA + """
        const items = partidasDeRespuesta(RESP).items;
        // Un completo que comparten dos hojas (raro): no se adivina, va tal cual.
        const dobles = items.concat([{code: "X.1", completo: "CD.99.01.64"}]);
        console.log(JSON.stringify({
            vacia: codigoParaEnviar("", items),
            blancos: codigoParaEnviar("   ", items),
            nula: codigoParaEnviar(null, items),
            completo: codigoParaEnviar("CD.99.01.64", items),
            completo_blancos: codigoParaEnviar(" CD.99.01.64 ", items),
            cod: codigoParaEnviar("99.01.64", items),
            cod_repetido: codigoParaEnviar("99.01.65", items),
            repetido_cd: codigoParaEnviar("CD.99.01.65", items),
            repetido_cp: codigoParaEnviar("CP.99.01.65", items),
            igual: codigoParaEnviar("CI.4.18", items),
            ant: codigoParaEnviar("ANT.98.01", items),
            fuera: codigoParaEnviar("zzz", items),
            sin_lista: codigoParaEnviar("CD.99.01.64", []),
            ambiguo: codigoParaEnviar("CD.99.01.64", dobles),
        }));
    """)

    assert casos == {"vacia": "", "blancos": "", "nula": "", "completo": "99.01.64",
                     "completo_blancos": "99.01.64", "cod": "99.01.64", "cod_repetido": "99.01.65",
                     "repetido_cd": "99.01.65", "repetido_cp": "99.01.65", "igual": "CI.4.18",
                     "ant": "98.01", "fuera": "zzz", "sin_lista": "CD.99.01.64", "ambiguo": "CD.99.01.64"}


@con_node
def test_f098_r21_partida_para_enviar_y_campos_cambiados(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS + ["parseNumEs", "numerosIguales", "_camposCambiados"],
                      _RESPUESTA + """
        const items = partidasDeRespuesta(RESP).items;
        function inp(defecto, valor) { return {value: valor, defaultValue: defecto,
                                                dataset: {field: "codigo_partida"}}; }
        console.log(JSON.stringify({
            sin_tocar: partidaParaEnviar(inp("CD.99.01.64", "CD.99.01.64"), items),
            sin_tocar_sin_items: partidaParaEnviar(inp("CD.99.01.64", " CD.99.01.64 ")),
            cambiada: partidaParaEnviar(inp("CD.99.01.64", "CI.4.18"), items),
            cambiada_completo: partidaParaEnviar(inp("CI.4.18", "CD.99.01.65"), items),
            cambiada_sin_items: partidaParaEnviar(inp("CI.4.18", "CD.99.01.65")),
            vaciada: partidaParaEnviar(inp("CD.99.01.64", ""), items),
            cuerpo: _camposCambiados(fila([inp("CI.4.18", "CD.99.01.64")]), items),
            cuerpo_sin_items: _camposCambiados(fila([inp("CI.4.18", "CD.99.01.64")])),
            cuerpo_igual: _camposCambiados(fila([inp("CD.99.01.64", "CD.99.01.64")]), items),
        }));
    """)

    assert casos == {"sin_tocar": None, "sin_tocar_sin_items": None, "cambiada": "CI.4.18",
                     "cambiada_completo": "99.01.65", "cambiada_sin_items": "CD.99.01.65", "vaciada": "",
                     "cuerpo": {"codigo_partida": "99.01.64"},
                     "cuerpo_sin_items": {"codigo_partida": "CD.99.01.64"}, "cuerpo_igual": {}}


def test_f098_r21_los_guardados_mandan_el_cod_de_la_lista():
    """«Guardar», «Guardar todas» y «Guardar y aprobar» arman el cuerpo con la lista."""
    from test_f051_almacen_front import _app_js, _funcion_js

    js = _app_js()
    assert js.count("_camposCambiados(tr, lista.items)") == 3
    assert "_camposCambiados(tr, lista.items)" in _funcion_js(js, "guardarFilasPendientes")


# =================================================================== #
# R15–R21 · el combo con el DOM falso
# =================================================================== #
_COMBO = ["_normLine", "partidasDeRespuesta", "opcionesPartida", "partidaValida", "siguienteActivo",
          "_scrollActive", "marcarPartida", "esAlmacenTecleado", "marcadaAlTeclear", "capituloElegido",
          "elegirCapitulo", "attachPartidaCombo"]

_FILAS = _RESPUESTA + """
    var _capituloFicha = {};
    const obraEl = el("input", "", document.body);
    obraEl.id = "obra_codigo";
    obraEl.value = "0686";
    const guardado = {};
    window.localStorage = {
        getItem: function (k) { return k in guardado ? guardado[k] : null; },
        setItem: function (k, v) { guardado[k] = String(v); },
        removeItem: function (k) { delete guardado[k]; },
    };
    let almacen = 0;
    function elegirAlmacen() { almacen += 1; }
    const LISTA = partidasDeRespuesta(RESP);
    function cargarPartidasObra() { return Promise.resolve(LISTA); }
    function fila() {
        const tr = el("tr", "conciliacion-row concilia-editable", document.body);
        const td = el("td", "", tr);
        const inp = el("input", "js-partida-combo", td);
        inp.value = "";
        attachPartidaCombo(inp);
        return {inp: inp, panel: td.querySelector(".combo-panel")};
    }
    const f1 = fila();
    const f2 = fila();
    function chips(panel) {
        const barra = panel.querySelector(".combo-chips");
        return barra ? barra.children.map(function (b) {
            return {t: b.textContent, on: b.classList.contains("on"), title: b.title, tipo: b.type,
                    tag: b.tagName};
        }) : null;
    }
    function items(panel) {
        return panel.querySelectorAll(".combo-item").map(function (d) { return d.textContent; });
    }
    function chip(panel, texto) {
        return panel.querySelector(".combo-chips").children.filter(function (b) {
            return b.textContent === texto; })[0];
    }
"""


@con_node
def test_f098_r15_chips_todas_y_un_capitulo_por_cabeza(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILAS, """
        f1.inp.focus();
        await tiempo();
        console.log(JSON.stringify({chips: chips(f1.panel), items: items(f1.panel),
                                    primero: f1.panel.children[0].className}));
    """)

    assert casos["primero"] == "combo-chips"
    assert casos["chips"] == [
        {"t": "Todas", "on": True, "title": "Todas las partidas de la obra", "tipo": "button", "tag": "BUTTON"},
        {"t": "ANT.", "on": False, "title": "AJUSTES ALMACÉN · 1 partida", "tipo": "button", "tag": "BUTTON"},
        {"t": "CD", "on": False, "title": "COSTES DIRECTOS · 2 partidas", "tipo": "button", "tag": "BUTTON"},
        {"t": "CI", "on": False, "title": "COSTES INDIRECTOS · 1 partida", "tipo": "button", "tag": "BUTTON"},
        {"t": "CP", "on": False, "title": "COSTES PREVISTOS · 1 partida", "tipo": "button", "tag": "BUTTON"},
    ]
    assert casos["items"][0] == "Almacén (sin partida)"
    assert len(casos["items"]) == 6


@con_node
def test_f098_r16_r17_chip_filtra_sin_perder_el_foco_y_vale_para_toda_la_ficha(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILAS, """
        f1.inp.focus();
        await tiempo();
        const ev = new Event("mousedown");
        chip(f1.panel, "CD").dispatchEvent(ev);
        await tiempo();
        const tras = {prevenido: ev.defaultPrevented, foco: document.activeElement === f1.inp,
                      abierto: !f1.panel.hidden, chips: chips(f1.panel).filter(function (c) { return c.on; }),
                      items: items(f1.panel), guardado: JSON.parse(JSON.stringify(guardado))};
        teclear(f1.inp, "otro");
        await tiempo();
        const tecleado = items(f1.panel);
        f2.inp.focus();
        await tiempo();
        const otra = {chips: chips(f2.panel).filter(function (c) { return c.on; }), items: items(f2.panel)};
        chip(f2.panel, "Todas").dispatchEvent(new Event("mousedown"));
        await tiempo();
        const todas = {n: items(f2.panel).length, guardado: JSON.parse(JSON.stringify(guardado))};
        console.log(JSON.stringify({tras, tecleado, otra, todas}));
    """)

    assert casos["tras"] == {
        "prevenido": True, "foco": True, "abierto": True,
        "chips": [{"t": "CD", "on": True, "title": "COSTES DIRECTOS · 2 partidas", "tipo": "button",
                   "tag": "BUTTON"}],
        "items": ["Almacén (sin partida)", "CD.99.01.64 · VARIOS › VARIOS OBRA › Material de obra",
                  "CD.99.01.65 · VARIOS › VARIOS OBRA › Otro material (código repetido en la obra)"],
        "guardado": {"f098.capitulo.0686": "CD"},
    }
    assert casos["tecleado"] == ["Almacén (sin partida)",
                                 "CD.99.01.65 · VARIOS › VARIOS OBRA › Otro material (código repetido en la obra)"]
    assert [c["t"] for c in casos["otra"]["chips"]] == ["CD"]
    assert len(casos["otra"]["items"]) == 3
    assert casos["todas"] == {"n": 6, "guardado": {}}


@con_node
def test_f098_r17_capitulo_recordado_al_abrir_la_ficha(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILAS.replace("const guardado = {};",
                                                           'const guardado = {"f098.capitulo.0686": "CI"};'), """
        f1.inp.focus();
        await tiempo();
        console.log(JSON.stringify({on: chips(f1.panel).filter(function (c) { return c.on; })
                                            .map(function (c) { return c.t; }), items: items(f1.panel)}));
    """)

    assert casos == {"on": ["CI"], "items": ["Almacén (sin partida)",
                                             "CI.4.18 · COSTES INDIRECTOS › Costes indirectos de obra"]}


@con_node
def test_f098_r17_localstorage_que_lanza_es_todas(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILAS + """
        Object.defineProperty(window, "localStorage", {get: function () { throw new Error("SecurityError"); }});
    """, """
        f1.inp.focus();
        await tiempo();
        const antes = chips(f1.panel).filter(function (c) { return c.on; }).map(function (c) { return c.t; });
        chip(f1.panel, "CI").dispatchEvent(new Event("mousedown"));
        await tiempo();
        f2.inp.focus();
        await tiempo();
        const despues = chips(f2.panel).filter(function (c) { return c.on; }).map(function (c) { return c.t; });
        console.log(JSON.stringify({antes, despues, n: items(f2.panel).length}));
    """)

    assert casos == {"antes": ["Todas"], "despues": ["CI"], "n": 2}


@con_node
def test_f098_r15_sin_capitulos_no_hay_barra(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILAS.replace(
        "const LISTA = partidasDeRespuesta(RESP);",
        "const LISTA = partidasDeRespuesta({ok: false});"), """
        f1.inp.focus();
        await tiempo();
        console.log(JSON.stringify({chips: chips(f1.panel), items: items(f1.panel),
                                    msg: f1.panel.querySelector(".combo-msg").textContent}));
    """)

    assert casos == {"chips": None, "items": ["Almacén (sin partida)"],
                     "msg": "No se pudieron cargar las partidas"}


@con_node
def test_f098_r19_mensaje_de_las_que_no_caben(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILAS.replace("const LISTA = partidasDeRespuesta(RESP);", """
        const MUCHAS = {ok: true, items: [], capitulos: [{codigo: "CD", descripcion: "COSTES DIRECTOS", n: 130}]};
        for (let i = 0; i < 130; i++) {
            MUCHAS.items.push({codigo: "01." + String(i).padStart(3, "0"), capitulo: "CD",
                               codigo_completo: "CD.01." + String(i).padStart(3, "0"), descripcion: "P" + i});
        }
        const LISTA = partidasDeRespuesta(MUCHAS);
    """), """
        f1.inp.focus();
        await tiempo();
        const todas = {n: items(f1.panel).length,
                       msg: f1.panel.querySelectorAll(".combo-msg").map(function (d) { return d.textContent; })};
        teclear(f1.inp, "01.00");
        await tiempo();
        const afinado = {n: items(f1.panel).length, msg: f1.panel.querySelectorAll(".combo-msg").length};
        console.log(JSON.stringify({todas, afinado}));
    """)

    assert casos == {"todas": {"n": 101, "msg": ["30 partidas más: escribe para afinar"]},
                     "afinado": {"n": 11, "msg": 0}}


@con_node
def test_f098_r21_elegir_pinta_el_completo_y_guarda_el_cod(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO, _FILAS, """
        f1.inp.focus();
        await tiempo();
        const fila = f1.panel.querySelectorAll(".combo-item").filter(function (d) {
            return d.textContent.indexOf("CD.99.01.64") === 0; })[0];
        fila.dispatchEvent(new Event("mousedown"));
        await tiempo();
        const elegido = {valor: f1.inp.value, cod: f1.inp.dataset.partidaCod, cerrado: f1.panel.hidden};
        f1.inp.blur();
        await tiempo();
        const trasSalir = f1.inp.value;
        console.log(JSON.stringify({elegido, trasSalir}));
    """)

    assert casos == {"elegido": {"valor": "CD.99.01.64", "cod": "99.01.64", "cerrado": True},
                     "trasSalir": "CD.99.01.64"}


# =================================================================== #
# R21 · «Dividir» manda el cod
# =================================================================== #
@con_node
def test_f098_r21_dividir_manda_el_cod(tmp_path):
    from test_f065_f3bis_front import _DIVIDIR, _ficha

    casos = _ejecutar_dom(
        tmp_path, ["_normLine", "partidasDeRespuesta", "codigoParaEnviar", *_DIVIDIR],
        _RESPUESTA + _ficha().replace('boton.dataset.partida = "01.01";',
                                      'boton.dataset.partida = "CD.99.01.64";').replace(
            "function cargarPartidasObra() { return Promise.resolve({items: [], error: false}); }",
            "function cargarPartidasObra() { return Promise.resolve(partidasDeRespuesta(RESP)); }"), """
        boton.dispatchEvent(new Event("click"));
        teclear(nEl, "3");
        teclear(cantidades()[0], "6");
        teclear(cantidades()[1], "7");
        const partes = cuerpo.querySelectorAll(".js-dividir-partida");
        const inicial = partes.map(function (p) { return p.value; });
        partes[1].value = "CI.4.18";
        partes[2].value = "";
        aceptar.dispatchEvent(new Event("click"));
        await tiempo();
        console.log(JSON.stringify({inicial, enviado}));
    """)

    assert casos["inicial"] == ["CD.99.01.64"] * 3
    assert casos["enviado"]["cuerpo"] == {"partes": [
        {"cantidad": 6, "codigo_partida": "99.01.64"},
        {"cantidad": 7, "codigo_partida": "CI.4.18"},
        {"cantidad": 5, "codigo_partida": None},
    ]}


def test_f098_r21_el_resto_de_la_ficha_sin_cambios():
    """El JSON de la respuesta y el envío de «Dividir» pasan por las funciones nuevas."""
    from test_f051_almacen_front import _app_js, _funcion_js

    js = _app_js()
    assert "codigoParaEnviar(" in _funcion_js(js, "wireDividir")
    assert "capituloElegido(" in _funcion_js(js, "attachPartidaCombo")
    assert '"f098.capitulo." + obra' in _funcion_js(js, "capituloElegido")
