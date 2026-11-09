# tests/test_f114_js.py
"""F-114 · el combo de proveedor con «Solo de la obra» (``static/app.js``), con node.

- Funciones puras (T4): R3 mínimo de 3, R6 etiqueta con «N fichas», R10 mensaje
  de lista de la obra vacía. Patrón de ``test_f065_f1_js.py``.
- ``initCombo`` en modo global (T5): R2, R4, R5, R6, R7, R8, R9, R10, R11, con
  ``tests/dom_falso.js``, ``fetch`` falso y temporizadores falsos.
Nombres y CIF inventados.
"""
from __future__ import annotations

from test_f051_almacen_front import _app_js, _funcion_js
from test_f065_f1_js import _ejecutar, con_node
from test_f065_f3bis_front import _ejecutar_dom

_PURAS = ["_comboLabel", "textoBusquedaProveedor", "urlProveedoresTodos",
          "etiquetaProveedorGlobal", "mensajeListaObraVacia"]


# =================================================================== #
# T4 · funciones puras
# =================================================================== #
@con_node
def test_f114_r3_minimo_de_tres_caracteres_utiles(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, """
        console.log(JSON.stringify([
            textoBusquedaProveedor(""), textoBusquedaProveedor(null),
            textoBusquedaProveedor(undefined), textoBusquedaProveedor("ab"),
            textoBusquedaProveedor("  ab  "), textoBusquedaProveedor("abc"),
            textoBusquedaProveedor("  b12 3 "), textoBusquedaProveedor("     "),
            urlProveedoresTodos("/api/sigrid/proveedores/todos", "a&b ñ%"),
        ]));
    """)
    assert casos == [None, None, None, None, None, "abc", "b12 3", None,
                     "/api/sigrid/proveedores/todos?q=a%26b%20%C3%B1%25"]


@con_node
def test_f114_r6_etiqueta_con_varias_fichas(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, """
        console.log(JSON.stringify([
            etiquetaProveedorGlobal({cif: "B00000001", nombre: "ALFA SL", fichas: 1}),
            etiquetaProveedorGlobal({cif: "B00000002", nombre: "BETA SA", fichas: 3}),
            etiquetaProveedorGlobal({cif: "B00000003", nombre: "GAMMA", fichas: 2}),
            etiquetaProveedorGlobal({cif: "B00000004", nombre: "", fichas: null}),
            etiquetaProveedorGlobal({cif: "B00000005", nombre: "DELTA"}),
        ]));
    """)
    assert casos == [
        "ALFA SL — B00000001",
        "BETA SA — B00000002 · 3 fichas en Sigrid",
        "GAMMA — B00000003 · 2 fichas en Sigrid",
        "Sin nombre — B00000004",
        "DELTA — B00000005",
    ]


@con_node
def test_f114_r10_mensaje_lista_de_la_obra_vacia(tmp_path):
    casos = _ejecutar(tmp_path, _PURAS, """
        console.log(JSON.stringify([
            mensajeListaObraVacia(null),
            mensajeListaObraVacia("Falta el codigo de obra."),
            mensajeListaObraVacia("Falta el codigo de obra"),
        ]));
    """)
    desmarca = "Desmarca «Solo de la obra» para buscar entre todos los proveedores de Sigrid"
    assert casos == [
        "Sin proveedores con contrato en la obra. " + desmarca,
        "Falta el codigo de obra. " + desmarca,
        "Falta el codigo de obra. " + desmarca,
    ]


# =================================================================== #
# T5 · initCombo en modo global (DOM falso)
# =================================================================== #
# F-115 R14: ``choose`` pide confirmación con ``avisoCambioCabecera`` sobre
# ``DOC_DATA`` (aquí sin contrato ni valoración: no pregunta, como hoy).
_COMBO = ["_norm", "_comboLabel", "_matchScore", "textoBusquedaProveedor",
          "urlProveedoresTodos", "etiquetaProveedorGlobal", "mensajeListaObraVacia",
          "_normCif", "_normObra", "avisoCambioCabecera", "initCombo"]

_ROTULO_OBRA = "Elegir proveedor (con contrato en la obra · Sigrid) — escribe para buscar"
_ROTULO_TODOS = ("Elegir proveedor (todos los de Sigrid) — escribe al menos 3 letras "
                 "del nombre o del CIF")
_DESMARCA = "Desmarca «Solo de la obra» para buscar entre todos los proveedores de Sigrid"
_HINT = "Escribe al menos 3 letras del nombre o del CIF"

# La cabecera y el combo como los pinta la plantilla de T3, con dobles de
# fetch (promesas que el test resuelve a mano), de los temporizadores largos
# (debounce y blur: el test los dispara con pasar()) y de sendSave.
_FICHA = """
    Elemento.prototype.select = function () {};
    const _st = globalThis.setTimeout, _ct = globalThis.clearTimeout;
    const relojes = [];
    globalThis.setTimeout = function (f, ms) {
        if (ms >= 100) { const t = {f: f, ms: ms, vivo: true}; relojes.push(t); return t; }
        return _st(f, ms);
    };
    globalThis.clearTimeout = function (t) { if (t && t.f) { t.vivo = false; } else { _ct(t); } };
    function vivos() { return relojes.filter(function (t) { return t.vivo; }).map(function (t) { return t.ms; }); }
    function pasar() {
        relojes.filter(function (t) { return t.vivo; }).forEach(function (t) { t.vivo = false; t.f(); });
    }
    const peticiones = [];
    globalThis.fetch = function (url) {
        return new Promise(function (ok, ko) {
            peticiones.push({url: url,
                responder: function (d) { ok({json: function () { return Promise.resolve(d); }}); },
                fallar: function () { ko(new Error("red")); }});
        });
    };
    let usosStorage = 0;
    Object.defineProperty(globalThis, "localStorage", {get: function () { usosStorage++; return {
        getItem: function () { return null; }, setItem: function () {} }; }});
    let guardados = 0;
    function sendSave() { guardados++; }

    function campo(id, valor) { const i = el("input", "", document.body); i.id = id; i.value = valor; return i; }
    const obra = campo("obra_codigo", "0686");
    const cif = campo("proveedor_cif", "B00000009");
    const nombre = campo("proveedor_nombre", "ACTUAL SL");
    const envoltorio = el("div", "full-width campo-combo", document.body);
    const cab = el("div", "campo-combo-cabecera", envoltorio);
    const rotulo = el("span", "", cab);
    rotulo.id = "proveedor_combo_rotulo";
    rotulo.textContent = "Elegir proveedor (con contrato en la obra · Sigrid) — escribe para buscar";
    const check = el("input", "", el("label", "check-inline", cab));
    check.id = "proveedor_solo_obra"; check.type = "checkbox"; check.checked = true;
    const combo = el("div", "combo", envoltorio);
    Object.assign(combo.dataset, {kind: "proveedor", endpoint: "/api/sigrid/proveedores",
        endpointTodos: "/api/sigrid/proveedores/todos", soloObraCheck: "proveedor_solo_obra",
        obraInput: "obra_codigo", valInput: "proveedor_cif", nombreInput: "proveedor_nombre",
        label: "ACTUAL SL — B00000009"});
    const caja = el("input", "combo-input", combo);
    caja.value = combo.dataset.label;
    const panel = el("div", "combo-panel", combo);
    panel.hidden = true;
    initCombo(combo);

    function marcar(valor) { check.checked = valor; check.dispatchEvent(new Event("change")); }
    function textos() { return panel.children.map(function (c) { return c.textContent; }); }
    function clases() { return panel.children.map(function (c) { return c.className; }); }
    function urls() { return peticiones.map(function (p) { return p.url; }); }
    function foto() {
        return {textos: textos(), clases: clases(), hidden: panel.hidden, urls: urls(),
                caja: caja.value, rotulo: rotulo.textContent};
    }
    const ALFA = {cif: "B00000001", nombre: "ALFA SL", fichas: 1};
    const BETA = {cif: "B00000002", nombre: "BETA SA", fichas: 3};
    async function buscar(texto) { teclear(caja, texto); pasar(); await tiempo(); }
    const DOC_DATA = {};
"""


def _combo(tmp_path, programa):
    return _ejecutar_dom(tmp_path, _COMBO, _FICHA, programa)


@con_node
def test_f114_r2_marcado_es_el_combo_de_hoy(tmp_path):
    r = _combo(tmp_path, """
        caja.focus();
        const a = foto();
        peticiones[0].responder({ok: true, items: [ALFA, BETA]});
        await tiempo(); await tiempo();
        teclear(caja, "beta");
        const c = foto();
        console.log(JSON.stringify({a: a, c: c, vivos: vivos()}));
    """)
    assert r["a"]["urls"] == ["/api/sigrid/proveedores?obra=0686"]
    assert r["a"]["textos"] == ["Cargando de Sigrid…"]
    # Lista de la obra filtrada en local por la caja.
    assert r["c"]["textos"] == ["BETA SA — B00000002"]
    assert r["c"]["urls"] == ["/api/sigrid/proveedores?obra=0686"]  # no vuelve a llamar
    assert r["c"]["rotulo"] == _ROTULO_OBRA
    assert r["vivos"] == []  # sin debounce en modo obra


@con_node
def test_f114_r10_lista_de_la_obra_vacia_o_sin_obra(tmp_path):
    r = _combo(tmp_path, """
        caja.focus();
        peticiones[0].responder({ok: true, items: []});
        await tiempo(); await tiempo();
        const vacia = foto();
        caja.blur(); pasar();
        caja.focus();
        peticiones[1].responder({ok: false, error: "Falta el codigo de obra.", items: []});
        await tiempo(); await tiempo();
        const sinObra = foto();
        caja.blur(); pasar();
        caja.focus();
        peticiones[2].responder({ok: false, error: "Error consultando Sigrid: x", items: []});
        await tiempo(); await tiempo();
        console.log(JSON.stringify({vacia: vacia, sinObra: sinObra, error: foto()}));
    """)
    assert r["vacia"]["textos"] == ["Sin proveedores con contrato en la obra. " + _DESMARCA]
    assert r["sinObra"]["textos"] == ["Falta el codigo de obra. " + _DESMARCA]
    assert r["sinObra"]["clases"] == ["combo-msg"]
    # Otro error de Sigrid: el aviso de hoy.
    assert r["error"]["textos"] == ["⚠ Error consultando Sigrid: x"]
    assert r["error"]["clases"] == ["combo-msg combo-error"]


@con_node
def test_f114_r8_cambiar_el_check_vacia_cierra_y_conserva_la_etiqueta(tmp_path):
    r = _combo(tmp_path, """
        caja.focus();
        peticiones[0].responder({ok: true, items: [ALFA, BETA]});
        await tiempo(); await tiempo();
        caja.value = "algo a medias";
        marcar(false);
        const desmarcado = foto();
        marcar(true);
        const marcado = foto();
        caja.blur(); pasar(); caja.focus();
        console.log(JSON.stringify({desmarcado: desmarcado, marcado: marcado, despues: foto(),
                                    guardados: guardados, cif: cif.value}));
    """)
    d = r["desmarcado"]
    assert d["hidden"] is True and d["caja"] == "ACTUAL SL — B00000009"
    assert d["rotulo"] == _ROTULO_TODOS
    assert d["urls"] == ["/api/sigrid/proveedores?obra=0686"]  # cambiar no llama
    assert r["marcado"]["rotulo"] == _ROTULO_OBRA and r["marcado"]["hidden"] is True
    # La lista se vació: al volver a «Solo de la obra», se pide otra vez.
    assert r["despues"]["urls"] == ["/api/sigrid/proveedores?obra=0686"] * 2
    assert r["guardados"] == 0 and r["cif"] == "B00000009"  # no guarda nada


@con_node
def test_f114_r3_desmarcado_busca_en_el_servidor_sin_refiltrar(tmp_path):
    r = _combo(tmp_path, """
        marcar(false);
        caja.focus();
        const alEnfocar = foto();
        teclear(caja, "ab"); pasar(); await tiempo();
        const corto = foto();
        await buscar("  alfa ");
        const buscando = foto();
        peticiones[0].responder({ok: true, items: [ALFA, BETA], mas: false});
        await tiempo(); await tiempo();
        console.log(JSON.stringify({alEnfocar: alEnfocar, corto: corto, buscando: buscando, fin: foto()}));
    """)
    assert r["alEnfocar"]["textos"] == [_HINT] and r["alEnfocar"]["urls"] == []
    assert r["corto"]["textos"] == [_HINT] and r["corto"]["urls"] == []
    assert r["buscando"]["urls"] == ["/api/sigrid/proveedores/todos?q=alfa"]
    # «BETA» no contiene «alfa»: se pinta igual (el servidor ya filtró).
    assert r["fin"]["textos"] == ["ALFA SL — B00000001", "BETA SA — B00000002 · 3 fichas en Sigrid"]


@con_node
def test_f114_r4_debounce_de_300_ms_y_respuestas_viejas_descartadas(tmp_path):
    r = _combo(tmp_path, """
        marcar(false);
        caja.focus();
        teclear(caja, "alf");
        teclear(caja, "alfa");
        const retardos = vivos();
        pasar(); await tiempo();
        const unaSola = urls();
        await buscar("alfab");
        // Llega antes la nueva y luego la vieja: se queda la nueva.
        peticiones[1].responder({ok: true, items: [BETA]});
        await tiempo(); await tiempo();
        peticiones[0].responder({ok: true, items: [ALFA]});
        await tiempo(); await tiempo();
        const fueraDeOrden = foto();
        // Vieja en vuelo y luego texto corto: la vieja no pisa el aviso.
        await buscar("gamma");
        teclear(caja, "ga");
        peticiones[2].responder({ok: true, items: [ALFA]});
        await tiempo(); await tiempo();
        console.log(JSON.stringify({retardos: retardos, unaSola: unaSola,
                                    fueraDeOrden: fueraDeOrden, corto: foto()}));
    """)
    assert r["retardos"] == [300]
    assert r["unaSola"] == ["/api/sigrid/proveedores/todos?q=alfa"]
    assert r["fueraDeOrden"]["textos"] == ["BETA SA — B00000002 · 3 fichas en Sigrid"]
    assert r["corto"]["textos"] == [_HINT]


@con_node
def test_f114_r5_r6_hay_mas_y_varias_fichas(tmp_path):
    r = _combo(tmp_path, """
        marcar(false);
        caja.focus();
        await buscar("sa sl");
        peticiones[0].responder({ok: true, items: [ALFA, BETA], mas: true});
        await tiempo(); await tiempo();
        const f = foto();
        const titulos = panel.children.map(function (c) { return c.title || null; });
        // La línea de «Hay más» no se elige con el teclado.
        tecla(caja, "ArrowDown"); tecla(caja, "ArrowDown"); tecla(caja, "ArrowDown");
        tecla(caja, "Enter");
        console.log(JSON.stringify({f: f, titulos: titulos, cif: cif.value}));
    """)
    assert r["f"]["textos"] == ["ALFA SL — B00000001", "BETA SA — B00000002 · 3 fichas en Sigrid",
                                "Hay más proveedores: escribe más para afinar"]
    assert r["f"]["clases"][2] == "combo-msg"
    assert r["titulos"][0] is None
    assert "3 fichas" in r["titulos"][1] and "proveedor ambiguo" in r["titulos"][1]
    assert r["titulos"][2] is None
    assert r["cif"] == "B00000002"


@con_node
def test_f114_r5_sin_mas_no_hay_linea_final(tmp_path):
    r = _combo(tmp_path, """
        marcar(false); caja.focus(); await buscar("alfa");
        peticiones[0].responder({ok: true, items: [ALFA]});
        await tiempo(); await tiempo();
        console.log(JSON.stringify(foto()));
    """)
    assert r["textos"] == ["ALFA SL — B00000001"]


@con_node
def test_f114_r7_elegir_rellena_y_guarda_como_hoy(tmp_path):
    r = _combo(tmp_path, """
        marcar(false);
        caja.focus();
        await buscar("beta");
        peticiones[0].responder({ok: true, items: [BETA]});
        await tiempo(); await tiempo();
        panel.children[0].dispatchEvent(new Event("mousedown"));
        console.log(JSON.stringify({cif: cif.value, nombre: nombre.value, guardados: guardados,
                                    hidden: panel.hidden}));
    """)
    assert r == {"cif": "B00000002", "nombre": "BETA SA", "guardados": 1, "hidden": True}


@con_node
def test_f114_r11_errores_de_la_busqueda_global(tmp_path):
    r = _combo(tmp_path, """
        marcar(false);
        caja.focus();
        await buscar("alfa");
        peticiones[0].responder({ok: false, error: "Error consultando Sigrid: caido", items: []});
        await tiempo(); await tiempo();
        const okFalse = foto();
        await buscar("alfab");
        peticiones[1].fallar();
        await tiempo(); await tiempo();
        console.log(JSON.stringify({okFalse: okFalse, red: foto(),
                                    editable: !caja.readOnly && !caja.disabled}));
    """)
    assert r["okFalse"]["textos"] == ["⚠ Error consultando Sigrid: caido"]
    assert r["okFalse"]["clases"] == ["combo-msg combo-error"]
    assert r["red"]["textos"] == ["⚠ Error de red consultando Sigrid"]
    assert r["editable"] is True


@con_node
def test_f114_r8_la_lista_de_la_obra_en_vuelo_no_se_pinta_tras_desmarcar(tmp_path):
    r = _combo(tmp_path, """
        caja.focus();
        marcar(false);
        peticiones[0].responder({ok: true, items: [ALFA, BETA]});
        await tiempo(); await tiempo();
        const tras = foto();
        caja.blur(); pasar(); caja.focus();
        console.log(JSON.stringify({tras: tras, enfoca: foto()}));
    """)
    assert r["tras"]["hidden"] is True
    assert r["enfoca"]["textos"] == [_HINT]


@con_node
def test_f114_r4_salir_de_la_caja_cancela_la_busqueda_pendiente(tmp_path):
    r = _combo(tmp_path, """
        marcar(false); caja.focus();
        teclear(caja, "alfa");
        caja.blur(); pasar(); await tiempo();
        const pendiente = foto();
        caja.focus(); await buscar("beta");
        caja.blur(); pasar();
        peticiones[0].responder({ok: true, items: [BETA]});
        await tiempo(); await tiempo();
        console.log(JSON.stringify({pendiente: pendiente, enVuelo: foto()}));
    """)
    assert r["pendiente"]["urls"] == [] and r["pendiente"]["hidden"] is True
    assert r["enVuelo"]["hidden"] is True
    assert r["enVuelo"]["caja"] == "ACTUAL SL — B00000009"


@con_node
def test_f114_r9_nada_en_localstorage(tmp_path):
    assert "localStorage" not in _funcion_js(_app_js(), "initCombo")
    r = _combo(tmp_path, """
        marcar(false); caja.focus(); await buscar("alfa");
        peticiones[0].responder({ok: true, items: [ALFA]});
        await tiempo(); await tiempo();
        marcar(true);
        console.log(JSON.stringify({usos: usosStorage}));
    """)
    assert r == {"usos": 0}
