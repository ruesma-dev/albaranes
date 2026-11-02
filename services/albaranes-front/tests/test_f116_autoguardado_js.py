# tests/test_f116_autoguardado_js.py
"""F-116 · B–F · el autoguardado de la ficha, EJECUTADO con node sobre
``tests/dom_falso.js`` (patrón de ``test_f077_guardar_y_aprobar_js.py``).

Una ficha editable con los cuatro Campos de cabecera (y su calendario), dos
filas editables (vid 12 y 13), ``#save-btn``, ``#approve-btn`` y un ``fetch``
falso que registra cada petición y puede RETENER sus respuestas (para ver el
orden y la Cola). Sin red ni servidor.

- R24, R27: la Cola de escritura y el aviso al salir (T6).
- R7–R12, R26: la cabecera (T7).
- R13–R17, R20: las líneas (T8).
- R21–R23, R25: los botones (T9).
- R28: el deshacer global (T10).
"""
from __future__ import annotations

import json

import pytest
from test_f051_almacen_front import _app_js, _funcion_js
from test_f065_f1_js import con_node
from test_f065_f3bis_front import _ejecutar_dom

#: La Cola (R24, R27).
_COLA = ["_estadoCola", "fetchRed", "encolar", "hayEscriturasEnCurso", "instalarColaEscrituras"]
#: La cabecera (R7–R12), con la Cola.
_CABECERA = _COLA + [
    "parseFechaEs", "fechaParaVer", "fechaParaEnviar", "avisoFechaNoValida", "marcarFechaNoValida",
    "limpiarMarcaFecha", "fechaEscritaValida", "wireFechaAlbaran", "motivoDeRespuesta",
    "avisarAutoguardado", "etiquetaCampoCabecera", "valorCabeceraParaGuardar",
    "valorGuardadoCabecera", "autoguardarCampoCabecera", "wireAutoguardadoCabecera",
]
#: Todo: líneas (R13–R20) y botones (R21–R23).
_FUNCIONES = _CABECERA + [
    "parseNumEs", "numerosIguales", "partidaParaEnviar", "_camposCambiados", "partidaValida",
    "codigoParaEnviar", "marcarPartida", "partidasMalas", "filasConCambios", "filasParaGuardar",
    "enviarFila", "consolidarFila", "valoresDeFila", "consolidarSinBloquear", "numeroDeLinea",
    "marcarFilaNoGuardada", "limpiarFilasNoGuardadas", "autoguardarFila", "wireAutoguardadoFilas",
    "importeDeFila", "precioDespejado", "marcarNoDespejable", "avisoImporte", "precioASigrid",
    "textoASigrid", "precioEs", "cantidadEs", "importeEs", "wireConciliaEdit",
    "guardarFilasPendientes", "avisoSumaVigente", "collectSelectedContratoCodigo",
    "collectPayload", "sendSave", "guardarCabecera",
]

_ESCENA = """
    var documentId = "DOC";
    const estadoEl = el("span", "autoguardado-estado", document.body);
    estadoEl.id = "autoguardado-estado";
    function campo(tag, id, valor, guardado) {
        const c = el(tag, "", document.body);
        c.id = id; c.value = valor; c.dataset.guardado = guardado;
        return c;
    }
    const fecha = campo("input", "fecha", "08/10/2026", "2026-10-08");
    const cal = el("input", "fecha-calendario", document.body);
    cal.id = "fecha_calendario";
    const botonCal = el("button", "js-fecha-calendario", document.body);
    const fechaError = el("small", "error js-fecha-error", document.body);
    fechaError.id = "fecha-error"; fechaError.hidden = true;
    const numero = campo("input", "numero_albaran", "A-1", "A-1");
    const forma = campo("input", "forma_pago", "giro", "giro");
    const notas = campo("textarea", "review_notes", "", "");

    const tbody = el("tbody", "", document.body);
    var linesBody = tbody;
    function fila(vid, partida, cantidad) {
        const tr = el("tr", "conciliacion-row concilia-editable", tbody);
        tr.dataset.forValuationLineId = vid;
        const part = el("input", "cell-input js-cedit js-partida-combo", el("td", "concilia-td", tr));
        part.dataset.field = "codigo_partida";
        part.value = partida; part.defaultValue = partida; part.title = "Partida " + vid;
        const cant = el("input", "cell-input js-cedit", el("td", "concilia-td", tr));
        cant.dataset.field = "cantidad"; cant.dataset.numeric = "1";
        cant.value = cantidad; cant.defaultValue = cantidad;
        const guardar = el("button", "js-cedit-save", el("td", "concilia-td td-acciones", tr));
        guardar.textContent = "Guardar";
        return {tr: tr, part: part, cant: cant, guardar: guardar};
    }
    const f1 = fila("12", "01.01", "8");
    const f2 = fila("13", "02.03", "5");
    var saveBtn = el("button", "btn", document.body);
    saveBtn.id = "save-btn";
    var approveBtn = el("button", "btn success", document.body);
    approveBtn.id = "approve-btn";
    approveBtn.dataset.avisoSuma = "";
    const ITEMS = ["01.01", "02.03", "05.01"].map(function (c) { return {code: c, label: c, norm: c}; });
    let partidasListas = true;
    let soltarPartidas = null;
    function cargarPartidasObra() {
        if (partidasListas) { return Promise.resolve({items: ITEMS, error: false}); }
        return new Promise(function (r) { soltarPartidas = function () { r({items: ITEMS, error: false}); }; });
    }

    const peticiones = [];
    const alertas = [];
    const confirmaciones = [];
    const respuestas = {};      // url ⇒ {status, detail}
    let retener = false;        // las escrituras esperan a soltar()
    const enEspera = [];
    function _responder(url, metodo) {
        const r = respuestas[url];
        if (r === "red") { return Promise.reject(new TypeError("Failed to fetch")); }
        let cuerpo = {ok: true};
        if (r) { cuerpo = {detail: r.detail}; }
        else if (metodo === "PUT") { cuerpo = {redirect_url: "/documents/DOC?msg=ok"}; }
        else if (url === "/api/documents/DOC/cabecera") {
            cuerpo = {ok: true, document_id: "DOC", cabecera: ultimoCuerpo};
        }
        const status = r ? r.status : 200;
        return Promise.resolve({ok: status < 300, status: status, statusText: "X",
                                json: function () { return Promise.resolve(cuerpo); }});
    }
    let ultimoCuerpo = null;
    globalThis.fetch = function (url, init) {
        const metodo = (init && init.method) || "GET";
        const cuerpo = init && init.body ? JSON.parse(init.body) : null;
        peticiones.push({metodo: metodo, url: url, cuerpo: cuerpo});
        ultimoCuerpo = cuerpo;
        if (metodo !== "GET" && retener) {
            return new Promise(function (r) { enEspera.push(function () { r(_responder(url, metodo)); }); });
        }
        return _responder(url, metodo);
    };
    async function soltar() {
        retener = false;
        while (enEspera.length) { enEspera.shift()(); await tiempo(); }
        await tiempo(); await tiempo();
    }
    async function dejar() { for (let i = 0; i < 6; i++) { await tiempo(); } }
    window.alert = function (m) { alertas.push(m); };
    globalThis.alert = window.alert;
    window.confirm = function (m) { confirmaciones.push(m); return true; };
    let eventos = 0;
    document.addEventListener("autoguardado", function () { eventos += 1; });
    function resumen() {
        return peticiones.map(function (p) {
            return p.metodo + " " + p.url + (p.cuerpo ? " " + JSON.stringify(p.cuerpo) : "");
        });
    }
    function marcas(c) {
        return {guardado: c.dataset.guardado, ok: c.classList.contains("campo-guardado"),
                mal: c.classList.contains("campo-no-guardado"), title: c.title || null};
    }
    function foto(f) {
        return {defecto: f.cant.defaultValue, valor: f.cant.value, auto: f.tr.dataset.autoguardada || null,
                marca: f.tr.classList.contains("fila-autoguardada"), title: f.tr.title || null,
                rojo: f.tr.classList.contains("fila-no-guardada"),
                desactivada: f.cant.disabled || f.part.disabled || f.guardar.disabled};
    }
    function estado() {
        return {peticiones: resumen(), alertas: alertas, confirmaciones: confirmaciones,
                recargas: window._recargas, href: window.location.href || null,
                aviso: estadoEl.textContent, eventos: eventos, f1: foto(f1), f2: foto(f2),
                fecha: marcas(fecha), numero: marcas(numero), forma: marcas(forma), notas: marcas(notas)};
    }
"""

_MONTAR = {
    "cola": "instalarColaEscrituras();\n",
    "cabecera": "instalarColaEscrituras(); wireFechaAlbaran(); wireAutoguardadoCabecera();\n",
    "todo": """
        instalarColaEscrituras();
        wireFechaAlbaran();
        wireAutoguardadoCabecera();
        wireConciliaEdit();
        wireAutoguardadoFilas();
    """,
}
_GRUPOS = {"cola": _COLA, "cabecera": _CABECERA, "todo": _FUNCIONES}

_CAB = "PATCH /api/documents/DOC/cabecera {cuerpo}"
_FILA = "PATCH /api/documents/DOC/lines/{vid}/conciliacion/campos{q} {cuerpo}"


def _cab(cuerpo):
    return _CAB.format(cuerpo=json.dumps(cuerpo, separators=(",", ":"), ensure_ascii=False))


def _fila(vid, cuerpo, bloquear=False):
    return _FILA.format(vid=vid, q="?bloquear=1" if bloquear else "",
                        cuerpo=json.dumps(cuerpo, separators=(",", ":")))


def _correr(tmp_path, programa, preparacion="", grupo="todo"):
    js = _app_js()
    funciones = _GRUPOS[grupo]
    faltan = [f for f in funciones if f"function {f}(" not in js]
    assert not faltan, f"faltan en app.js: {faltan}"
    return _ejecutar_dom(tmp_path, funciones, _ESCENA + preparacion,
                         _MONTAR[grupo] + programa + "\nawait dejar();\nconsole.log(JSON.stringify(estado()));")


def _salir(campo, valor):
    """Entra en el campo, escribe y sale (``blur``)."""
    return f"{campo}.focus(); {campo}.value = {json.dumps(valor)}; {campo}.blur();\n"


# =================================================================== #
# R24 · la Cola: escrituras en serie y en orden; los GET no esperan
# =================================================================== #
@con_node
def test_f116_r24_escrituras_en_serie_y_en_orden(tmp_path):
    casos = _correr(tmp_path, """
        retener = true;
        const a = fetch("/a", {method: "PUT", body: "{}"});
        const b = fetch("/b", {method: "post"});
        const c = fetch("/c", {method: "DELETE"});
        const g = fetch("/g");
        await tiempo();
        estado.antes = resumen();
        await soltar();
        await Promise.all([a, b, c, g]);
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {antes: estado.antes}); };
    """, grupo="cola")
    # El GET no espera (sale ya); la 1.ª escritura sale y las demás esperan.
    assert casos["antes"] == ["GET /g", "PUT /a {}"]
    assert casos["peticiones"] == ["GET /g", "PUT /a {}", "post /b", "DELETE /c"]


@con_node
def test_f116_r24_un_fallo_no_rompe_la_cola(tmp_path):
    casos = _correr(tmp_path, """
        respuestas["/a"] = "red";
        let error = null;
        try { await fetch("/a", {method: "PATCH"}); } catch (e) { error = e.message; }
        const r = await fetch("/b", {method: "PATCH"});
        estado.extra = {error: error, ok: r.ok, pendiente: hayEscriturasEnCurso()};
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {extra: estado.extra}); };
    """, grupo="cola")
    assert casos["extra"] == {"error": "Failed to fetch", "ok": True, "pendiente": False}
    assert casos["peticiones"] == ["PATCH /a", "PATCH /b"]


@con_node
def test_f116_r24_encolar_espera_a_lo_anterior(tmp_path):
    casos = _correr(tmp_path, """
        retener = true;
        fetch("/a", {method: "PUT"});
        let hecho = false;
        const espera = encolar(function () { hecho = true; return 7; });
        await tiempo();
        const antes = hecho;
        await soltar();
        estado.extra = {antes: antes, despues: hecho, valor: await espera};
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {extra: estado.extra}); };
    """, grupo="cola")
    assert casos["extra"] == {"antes": False, "despues": True, "valor": 7}


def test_f116_r24_solo_en_la_ficha_editable_y_antes_de_las_vias():
    js = _app_js()
    instalar = js.index("instalarColaEscrituras();")
    assert 'document.getElementById("autoguardado-estado")' in js[instalar - 200:instalar]
    # Antes de enganchar ninguna vía de la ficha y del deshacer global.
    assert instalar < js.index("wireConciliaEdit();") < js.index("function wireUndoGlobal")


# =================================================================== #
# R27 · salir con escrituras en curso pide confirmación
# =================================================================== #
@con_node
def test_f116_r27_beforeunload_solo_con_escrituras_en_curso(tmp_path):
    casos = _correr(tmp_path, """
        function salir() {
            const ev = new Event("beforeunload");
            ev.returnValue = "sin tocar";
            (window._oyentes.beforeunload || []).forEach(function (f) { f(ev); });
            return {prevenido: ev.defaultPrevented, valor: ev.returnValue};
        }
        const quieta = salir();
        retener = true;
        fetch("/a", {method: "PATCH"});
        const enVuelo = salir();
        await soltar();
        estado.extra = {quieta: quieta, enVuelo: enVuelo, despues: salir()};
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {extra: estado.extra}); };
    """, grupo="cola")
    assert casos["extra"] == {
        "quieta": {"prevenido": False, "valor": "sin tocar"},
        "enVuelo": {"prevenido": True, "valor": ""},
        "despues": {"prevenido": False, "valor": "sin tocar"},
    }


# =================================================================== #
# R7–R10 · cabecera: al salir, solo lo cambiado, sin recargar
# =================================================================== #
@con_node
@pytest.mark.parametrize("campo, escrito, cuerpo", [
    ("fecha", "28-10-26", {"fecha": "2026-10-28"}),
    ("numero", " B-7 ", {"numero_albaran": "B-7"}),
    ("forma", "", {"forma_pago": None}),
    ("notas", "revisar portes", {"review_notes": "revisar portes"}),
])
def test_f116_r7_al_salir_guarda_solo_ese_campo(tmp_path, campo, escrito, cuerpo):
    casos = _correr(tmp_path, _salir(campo, escrito), grupo="cabecera")
    assert casos["peticiones"] == [_cab(cuerpo)]
    assert casos["recargas"] == 0 and casos["href"] is None and casos["alertas"] == []


@con_node
@pytest.mark.parametrize("campo, escrito", [
    ("fecha", "08/10/2026"), ("fecha", "8-10-26"), ("numero", "  A-1 "), ("forma", "giro"),
    ("notas", "  "),
])
def test_f116_r7_sin_cambio_no_envia(tmp_path, campo, escrito):
    casos = _correr(tmp_path, _salir(campo, escrito), grupo="cabecera")
    assert casos["peticiones"] == []


@con_node
def test_f116_r7_la_fecha_vieja_dd_mm_se_compara_normalizada(tmp_path):
    casos = _correr(tmp_path, 'fecha.dataset.guardado = "08/10/2026";\n' + _salir("fecha", "08/10/2026"), grupo="cabecera")
    assert casos["peticiones"] == []


@con_node
def test_f116_r8_elegir_en_el_calendario_guarda(tmp_path):
    casos = _correr(tmp_path, """
        cal.value = "2026-10-05";
        cal.dispatchEvent(new Event("change"));
    """, grupo="cabecera")
    assert casos["peticiones"] == [_cab({"fecha": "2026-10-05"})]
    assert casos["fecha"]["guardado"] == "2026-10-05"


@con_node
@pytest.mark.parametrize("escrito", ["31/02/2026", "abc"])
def test_f116_r9_fecha_no_admitida_no_envia_y_marca(tmp_path, escrito):
    casos = _correr(tmp_path, _salir("fecha", escrito) + """
        estado.roja = fecha.classList.contains("campo-no-valido") && !fechaError.hidden;
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {roja: estado.roja}); };
    """, grupo="cabecera")
    assert casos["peticiones"] == [] and casos["roja"] is True
    assert casos["alertas"] == []


@con_node
def test_f116_r10_bien_actualiza_lo_guardado_marca_y_avisa(tmp_path):
    casos = _correr(tmp_path, _salir("fecha", "28-10-26") + "await dejar();\n"
                    + _salir("fecha", "28/10/2026"), grupo="cabecera")
    assert casos["peticiones"] == [_cab({"fecha": "2026-10-28"})]  # el 2.º, sin cambio
    assert casos["fecha"] == {"guardado": "2026-10-28", "ok": True, "mal": False,
                              "title": "Guardado automáticamente"}
    assert casos["aviso"] == "Fecha guardado"
    assert casos["eventos"] == 1


@con_node
def test_f116_r10_al_volver_a_teclear_se_quita_la_marca(tmp_path):
    casos = _correr(tmp_path, _salir("numero", "B-7") + """
        await dejar();
        numero.dispatchEvent(new Event("input", {bubbles: true}));
    """, grupo="cabecera")
    assert casos["numero"]["ok"] is False and casos["numero"]["guardado"] == "B-7"


@con_node
def test_f116_r11_fallo_marca_sin_alert_y_el_siguiente_reintenta(tmp_path):
    casos = _correr(tmp_path, """
        respuestas["/api/documents/DOC/cabecera"] = {status: 500, detail: "caído"};
    """ + _salir("notas", "nota") + """
        await dejar();
        estado.tras_fallo = {notas: marcas(notas), aviso: estadoEl.textContent, valor: notas.value};
        delete respuestas["/api/documents/DOC/cabecera"];
    """ + _salir("notas", "nota"), preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {tras_fallo: estado.tras_fallo}); };
    """, grupo="cabecera")
    assert casos["tras_fallo"] == {
        "notas": {"guardado": "", "ok": False, "mal": True, "title": "caído"},
        "aviso": "No se pudo guardar notas de revisión: caído", "valor": "nota"}
    assert casos["peticiones"] == [_cab({"review_notes": "nota"})] * 2
    assert casos["notas"]["ok"] is True and casos["notas"]["mal"] is False
    assert casos["alertas"] == []


@con_node
def test_f116_r11_error_de_red(tmp_path):
    casos = _correr(tmp_path, 'respuestas["/api/documents/DOC/cabecera"] = "red";\n'
                    + _salir("forma", "contado"), grupo="cabecera")
    assert casos["forma"]["mal"] is True and casos["forma"]["guardado"] == "giro"
    assert casos["aviso"] == "No se pudo guardar forma de pago: error de red"


@con_node
def test_f116_r11_lo_que_se_vuelve_a_dejar_como_estaba_tambien_viaja(tmp_path):
    """Cambiar y volver a lo de antes mientras el primero está en la Cola: el
    segundo se compara con lo encolado, no con lo guardado (si no, quedaría
    guardado el valor intermedio)."""
    casos = _correr(tmp_path, "retener = true;\n" + _salir("forma", "contado")
                    + _salir("forma", "giro") + "await soltar();\n", grupo="cabecera")
    assert casos["peticiones"] == [_cab({"forma_pago": "contado"}), _cab({"forma_pago": "giro"})]
    assert casos["forma"]["guardado"] == "giro"


@con_node
def test_f116_r12_sin_estado_no_hay_autoguardado_de_cabecera(tmp_path):
    casos = _correr(tmp_path, _salir("fecha", "28/10/2026") + _salir("notas", "x"),
                    preparacion="estadoEl.parentNode.removeChild(estadoEl);", grupo="cabecera")
    assert casos["peticiones"] == []


@con_node
def test_f116_r12_sin_estado_no_hay_autoguardado_de_lineas(tmp_path):
    casos = _correr(tmp_path, _salir("f1.cant", "6") + 'cal.value = "2026-10-05";\n'
                    + 'cal.dispatchEvent(new Event("change"));\n',
                    preparacion="estadoEl.parentNode.removeChild(estadoEl);")
    assert casos["peticiones"] == []


@con_node
def test_f116_r26_un_409_no_se_reintenta_solo(tmp_path):
    casos = _correr(tmp_path, """
        respuestas["/api/documents/DOC/cabecera"] = {status: 409,
            detail: "Albarán aprobado: desapruébalo para editar"};
    """ + _salir("numero", "B-7") + "await dejar(); await dejar();\n", grupo="cabecera")
    assert casos["peticiones"] == [_cab({"numero_albaran": "B-7"})]
    assert casos["numero"]["title"] == "Albarán aprobado: desapruébalo para editar"
    assert casos["aviso"] == ("No se pudo guardar número albarán: Albarán aprobado: "
                              "desapruébalo para editar")


def test_f116_r9_se_engancha_despues_de_la_fecha_de_f108():
    js = _app_js()
    assert js.index("wireFechaAlbaran();") < js.index("wireAutoguardadoCabecera();")


# =================================================================== #
# R13–R17 · líneas: al salir de cada celda, sin bloquear
# =================================================================== #
@con_node
def test_f116_r13_al_salir_de_una_celda_guarda_sin_bloquear(tmp_path):
    casos = _correr(tmp_path, _salir("f1.cant", "6"))
    assert casos["peticiones"] == [_fila(12, {"cantidad": 6})]
    assert casos["recargas"] == 0 and casos["alertas"] == []


@con_node
def test_f116_r13_sin_cambios_no_envia(tmp_path):
    casos = _correr(tmp_path, _salir("f1.cant", "8,0") + _salir("f2.part", "02.03"))
    assert casos["peticiones"] == []


@con_node
def test_f116_r13_todos_los_cambiados_de_la_fila(tmp_path):
    casos = _correr(tmp_path, 'f2.part.value = "05.01";\n' + _salir("f2.cant", "4"))
    assert casos["peticiones"] == [_fila(13, {"codigo_partida": "05.01", "cantidad": 4})]


@con_node
def test_f116_r14_el_cuerpo_se_arma_cuando_le_toca(tmp_path):
    casos = _correr(tmp_path, """
        partidasListas = false;
    """ + _salir("f1.cant", "6") + """
        await tiempo();
        estado.antes = resumen();
        f1.cant.value = "7";
        soltarPartidas();
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {antes: estado.antes}); };
    """)
    assert casos["antes"] == []
    assert casos["peticiones"] == [_fila(12, {"cantidad": 7})]
    assert casos["f1"]["defecto"] == "7"


@con_node
def test_f116_r15_partida_fuera_de_la_lista_no_envia_nada_de_la_fila(tmp_path):
    casos = _correr(tmp_path, 'f1.cant.value = "6";\n' + _salir("f1.part", "zzzz") + """
        await dejar();
        estado.roja = f1.part.classList.contains("partida-invalida");
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {roja: estado.roja}); };
    """)
    assert casos["peticiones"] == [] and casos["roja"] is True
    assert casos["alertas"] == []


@con_node
def test_f116_r16_bien_consolida_sin_bloquear_y_lo_tecleado_despues_sigue(tmp_path):
    casos = _correr(tmp_path, "retener = true;\n" + _salir("f1.cant", "6") + """
        await dejar();
        f1.cant.value = "9";
        await soltar();
        estado.siguen = _camposCambiados(f1.tr, ITEMS);
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {siguen: estado.siguen}); };
    """)
    assert casos["peticiones"] == [_fila(12, {"cantidad": 6})]
    assert casos["f1"] == {"defecto": "6", "valor": "9", "auto": "1", "marca": True,
                           "title": "Guardada automáticamente, sin bloquear", "rojo": False,
                           "desactivada": False}
    assert casos["siguen"] == {"cantidad": 9}
    assert casos["aviso"] == "Línea 1 guardada"
    assert casos["eventos"] == 1


@con_node
def test_f116_r16_el_numero_es_el_de_la_tabla(tmp_path):
    casos = _correr(tmp_path, _salir("f2.cant", "4"))
    assert casos["aviso"] == "Línea 2 guardada"


@con_node
def test_f116_r17_fallo_en_rojo_sin_alert_y_reintenta(tmp_path):
    url = "/api/documents/DOC/lines/12/conciliacion/campos"
    casos = _correr(tmp_path, f"""
        respuestas[{json.dumps(url)}] = {{status: 422, detail: "no es un número"}};
    """ + _salir("f1.cant", "6") + """
        await dejar();
        estado.tras_fallo = foto(f1);
        estado.aviso_fallo = estadoEl.textContent;
    """ + f"delete respuestas[{json.dumps(url)}];\n" + _salir("f1.cant", "6"), preparacion="""
        const _e = estado;
        estado = function () {
            return Object.assign(_e(), {tras_fallo: estado.tras_fallo, aviso_fallo: estado.aviso_fallo});
        };
    """)
    assert casos["tras_fallo"] == {"defecto": "8", "valor": "6", "auto": None, "marca": False,
                                   "title": "no es un número", "rojo": True, "desactivada": False}
    assert casos["aviso_fallo"] == "No se pudo guardar la línea 1: no es un número"
    assert casos["peticiones"] == [_fila(12, {"cantidad": 6})] * 2
    assert casos["f1"]["rojo"] is False and casos["f1"]["auto"] == "1"
    assert casos["alertas"] == []


@con_node
def test_f116_r26_un_409_de_linea_no_se_reintenta_solo(tmp_path):
    url = "/api/documents/DOC/lines/12/conciliacion/campos"
    casos = _correr(tmp_path, f"""
        respuestas[{json.dumps(url)}] = {{status: 409, detail: "La valoración ha cambiado"}};
    """ + _salir("f1.cant", "6") + "await dejar(); await dejar();\n")
    assert casos["peticiones"] == [_fila(12, {"cantidad": 6})]
    assert casos["f1"]["title"] == "La valoración ha cambiado"


@con_node
def test_f116_r20_enter_sigue_siendo_guardar_y_bloquear(tmp_path):
    casos = _correr(tmp_path, """
        f1.cant.focus();
        f1.cant.value = "6";
        tecla(f1.cant, "Enter");
    """)
    assert casos["peticiones"] == [_fila(12, {"cantidad": 6}, bloquear=True)]
    assert casos["recargas"] == 1


def test_f116_r13_enviar_fila_es_la_unica_que_construye_la_url():
    js = _app_js()
    url = "/conciliacion/campos`"  # la plantilla de la URL (no los comentarios)
    assert js.count(url) == js.count(url, *_rango(js, "enviarFila")) == 1
    cuerpo = _funcion_js(js, "enviarFila")
    assert "?bloquear=1" in cuerpo


def _rango(js, nombre):
    inicio = js.index(f"function {nombre}(")
    return inicio, inicio + len(_funcion_js(js, nombre))


def test_f116_r13_se_engancha_despues_de_los_combos_de_partida():
    js = _app_js()
    assert js.index("wirePartidaCombos();") < js.index("wireAutoguardadoFilas();")


# =================================================================== #
# R21–R23, R25 · los botones siguen igual (y esperan a la Cola)
# =================================================================== #
@con_node
def test_f116_r21_r25_guardar_de_la_fila_tras_salir_de_la_celda(tmp_path):
    casos = _correr(tmp_path, _salir("f1.cant", "6") + "f1.guardar.click();\n")
    assert casos["peticiones"] == [_fila(12, {"cantidad": 6}), _fila(12, {}, bloquear=True)]
    assert casos["recargas"] == 1


@con_node
def test_f116_r21_guardar_de_la_fila_sin_cambios_bloquea_igual(tmp_path):
    casos = _correr(tmp_path, "f2.guardar.click();\n")
    assert casos["peticiones"] == [_fila(13, {}, bloquear=True)]


@con_node
def test_f116_r22_guardar_bloquea_las_autoguardadas_y_las_pendientes(tmp_path):
    casos = _correr(tmp_path, _salir("f1.cant", "6") + """
        await dejar();
        f2.cant.value = "4";
        await guardarCabecera(false);
    """)
    pet = casos["peticiones"]
    assert pet[:3] == [_fila(12, {"cantidad": 6}), _fila(12, {}, bloquear=True),
                       _fila(13, {"cantidad": 4}, bloquear=True)]
    assert len(pet) == 4 and pet[3].startswith("PUT /api/documents/DOC?buscar_si_cambia=1 ")


@con_node
def test_f116_r22_sin_ninguna_de_las_dos_no_manda_filas(tmp_path):
    casos = _correr(tmp_path, "await guardarCabecera(false);\n")
    assert len(casos["peticiones"]) == 1 and casos["peticiones"][0].startswith("PUT ")


@con_node
def test_f116_r22_la_autoguardada_y_bloqueada_no_se_reenvia_al_reintentar(tmp_path):
    url = "/api/documents/DOC/lines/13/conciliacion/campos?bloquear=1"
    casos = _correr(tmp_path, _salir("f1.cant", "6") + f"""
        await dejar();
        f2.cant.value = "4";
        respuestas[{json.dumps(url)}] = {{status: 500, detail: "caído"}};
        await guardarCabecera(true);
        delete respuestas[{json.dumps(url)}];
        peticiones.length = 0;
        await guardarCabecera(true);
    """)
    pet = casos["peticiones"]
    assert pet[0] == _fila(13, {"cantidad": 4}, bloquear=True)
    assert all("/lines/12/" not in p for p in pet)


@con_node
def test_f116_r23_r25_guardar_y_aprobar_con_el_cursor_en_la_fecha(tmp_path):
    casos = _correr(tmp_path, "retener = true;\n" + _salir("fecha", "28/10/2026") + """
        const flujo = guardarCabecera(true);
        await dejar();
        estado.antes = resumen();
        await soltar();
        await flujo;
        await soltar();
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {antes: estado.antes}); };
    """)
    assert casos["antes"] == [_cab({"fecha": "2026-10-28"})]
    pet = casos["peticiones"]
    assert pet[0] == _cab({"fecha": "2026-10-28"})
    assert len(pet) == 2 and pet[1].startswith('PUT /api/documents/DOC {"')
    assert json.loads(pet[1].split(" ", 2)[2])["fecha"] == "2026-10-28"
    assert casos["href"] == "/documents/DOC?msg=ok"


@con_node
def test_f116_r23_guardar_y_aprobar_espera_al_autoguardado_de_una_fila(tmp_path):
    casos = _correr(tmp_path, "retener = true;\n" + _salir("f1.cant", "6") + """
        const flujo = guardarCabecera(true);
        await dejar();
        estado.antes = resumen();
        await soltar();
        await flujo;
        await soltar();
    """, preparacion="""
        const _e = estado;
        estado = function () { return Object.assign(_e(), {antes: estado.antes}); };
    """)
    assert casos["antes"] == [_fila(12, {"cantidad": 6})]
    pet = casos["peticiones"]
    assert pet[:2] == [_fila(12, {"cantidad": 6}), _fila(12, {}, bloquear=True)]
    assert pet[2] == "GET /api/documents/DOC"  # el aviso vigente: se guardó una fila
    assert pet[3].startswith('PUT /api/documents/DOC {"')


def test_f116_r22_guardar_todas_elige_con_filas_para_guardar_tras_la_cola():
    from test_f065_f1_js import _bloque

    todas = _bloque(_app_js(), 'saveAllLinesBtn.addEventListener("click"', "if (addLineBtn)")
    assert "filasParaGuardar(" in todas
    assert todas.index("await encolar(") < todas.index("No hay cambios en las líneas")


def test_f116_r23_guardar_de_la_fila_espera_a_la_cola():
    from test_f065_f1_js import _bloque

    fila_guardar = _bloque(_app_js(), 'saveBtn.addEventListener("click"',
                           'getElementById("save-all-lines-btn")')
    assert fila_guardar.index("await encolar(") < fila_guardar.index("_camposCambiados(tr")


# =================================================================== #
# R28 · el deshacer global
# =================================================================== #
@con_node
def test_f116_r28_etiqueta_cabecera(tmp_path):
    from test_f065_f1_js import _ejecutar

    casos = _ejecutar(tmp_path, ["etiquetaAccion"], """
        console.log(JSON.stringify([etiquetaAccion("cabecera"), etiquetaAccion("linea_edit")]));
    """)
    assert casos == ["Cabecera", "Línea"]


def test_f116_r28_el_widget_se_refresca_con_cada_autoguardado():
    js = _app_js()
    widget = js[js.index("function wireUndoGlobal"):]
    widget = widget[:widget.index("})();")]
    assert 'document.addEventListener("autoguardado", refrescar)' in widget


@con_node
def test_f116_r28_solo_los_que_van_bien_avisan_al_widget(tmp_path):
    casos = _correr(tmp_path, """
        respuestas["/api/documents/DOC/cabecera"] = {status: 500, detail: "caído"};
    """ + _salir("numero", "B-7") + _salir("f1.cant", "6"))
    assert casos["eventos"] == 1
