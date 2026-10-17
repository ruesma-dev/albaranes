# tests/test_f077_guardar_y_aprobar_js.py
"""F-077 · A · «Guardar y aprobar» y «Guardar» guardan antes las filas con cambios.

El JS de ``static/app.js`` se EJECUTA con node sobre ``tests/dom_falso.js``
(patrón de ``test_f065_f3bis_front.py``): una ficha con dos filas editables,
``#save-btn``, ``#approve-btn`` con ``data-aviso-suma``, y ``fetch``,
``alert``, ``confirm`` y ``location`` falsos que registran todo.

- R1: PATCH de cada fila con cambios, en orden, y luego el PUT de cabecera.
- R2: sin filas con cambios, ningún PATCH (y la confirmación con lo pintado).
- R3: partida cambiada fuera de la lista ⇒ nada enviado, en rojo y aviso.
- R4: un PATCH que falla ⇒ para, fila en rojo, aviso, sin PUT ni recarga.
- R5: las guardadas antes del fallo se consolidan (un reintento no las reenvía).
- R6–R9: aviso de suma vigente, cancelar, fallo de la lectura y del PUT.
- R10: botones desactivados durante el flujo; un segundo clic no repite nada.
- R11: el servidor sigue validando al aprobar (F-065 R20, F-078 R17).
- R12: una sola petición PATCH de fila en ``app.js``.
- R13: nunca más «Hay N líneas con cambios sin guardar».
"""
from __future__ import annotations

import json

import pytest
from test_f051_almacen_front import _app_js
from test_f065_f1_js import con_node
from test_f065_f3bis_front import _ejecutar_dom

#: Lo que ``guardarCabecera`` necesita de ``app.js`` (sacado tal cual).
_FUNCIONES = ["parseNumEs", "numerosIguales", "partidaParaEnviar", "_camposCambiados", "partidaValida",
              "marcarPartida", "partidasMalas", "filasConCambios", "motivoDeRespuesta", "enviarFila",
              "consolidarFila", "marcarFilaNoGuardada", "limpiarFilasNoGuardadas", "guardarFilasPendientes",
              "avisoSumaVigente", "collectSelectedContratoCodigo", "collectPayload", "sendSave",
              "guardarCabecera"]

AVISO_PINTADO = "La suma de las líneas (100,00 €) no cuadra con la del albarán (90,00 €). ¿Aprobar igualmente?"
AVISO_GET = "La suma de las líneas (80,00 €) no cuadra con la del albarán (90,00 €). ¿Aprobar igualmente?"
PARTIDAS_MALAS = "Hay partidas no válidas (en rojo): elige una de la lista o déjala vacía (almacén)."

# Dos filas editables (vid 12 y 13), los botones de la cabecera y los dobles.
_ESCENA = """
    const tbody = el("tbody", "", document.body);
    var linesBody = tbody;
    var documentId = "DOC";
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
        return {tr: tr, part: part, cant: cant, guardar: guardar};
    }
    const f1 = fila("12", "01.01", "8");
    const f2 = fila("13", "02.03", "5");
    const saveBtn = el("button", "btn", document.body);
    saveBtn.id = "save-btn";
    const approveBtn = el("button", "btn success", document.body);
    approveBtn.id = "approve-btn";
    approveBtn.dataset.avisoSuma = AVISO_PINTADO;
    const ITEMS = ["01.01", "02.03", "05.01"].map(function (c) { return {code: c, label: c, norm: c}; });
    function cargarPartidasObra() { return Promise.resolve({items: ITEMS, error: false}); }
    const peticiones = [];
    const alertas = [];
    const confirmaciones = [];
    let respuestaConfirm = true;
    const fallos = {};
    let getFalla = false;
    let avisoGet = "";
    let putFalla = null;
    let botonesDuranteElPatch = null;
    globalThis.fetch = function (url, init) {
        const metodo = (init && init.method) || "GET";
        peticiones.push({metodo: metodo, url: url, cuerpo: init && init.body ? JSON.parse(init.body) : null});
        let r;
        if (metodo === "PATCH") {
            if (botonesDuranteElPatch === null) {
                botonesDuranteElPatch = {guardar: saveBtn.disabled, aprobar: approveBtn.disabled};
            }
            const vid = url.split("/lines/")[1].split("/")[0];
            const f = fallos[vid];
            if (f === "red") { return Promise.reject(new TypeError("Failed to fetch")); }
            r = f ? {ok: false, status: f.status, statusText: "Conflict", cuerpo: {detail: f.detail}}
                  : {ok: true, status: 200, cuerpo: {ok: true}};
        } else if (metodo === "GET") {
            if (getFalla) { return Promise.reject(new TypeError("Failed to fetch")); }
            r = {ok: true, status: 200, cuerpo: {id: "DOC", aviso_suma: avisoGet || null}};
        } else {
            r = putFalla ? {ok: false, status: 409, statusText: "Conflict", cuerpo: {detail: putFalla}}
                         : {ok: true, status: 200, cuerpo: {redirect_url: "/documents/DOC?msg=ok"}};
        }
        return Promise.resolve({ok: r.ok, status: r.status, statusText: r.statusText || "",
                                json: function () { return Promise.resolve(r.cuerpo); }});
    };
    function alert(m) { alertas.push(m); }
    window.alert = alert;
    window.confirm = function (m) { confirmaciones.push(m); return respuestaConfirm; };
    function resumen() {
        return peticiones.map(function (p) {
            return p.metodo + " " + p.url + (p.cuerpo ? " " + JSON.stringify(p.cuerpo) : "");
        });
    }
    function estado() {
        return {peticiones: resumen(), alertas: alertas, confirmaciones: confirmaciones,
                recargas: window._recargas, href: window.location.href || null,
                guardarActivo: !saveBtn.disabled, aprobarActivo: !approveBtn.disabled};
    }
"""

_PATCH = "PATCH /api/documents/DOC/lines/{vid}/conciliacion/campos?bloquear=1 {cuerpo}"
_GET = "GET /api/documents/DOC"
_PUT_APROBAR = 'PUT /api/documents/DOC {"approved":true'
_PUT_GUARDAR = 'PUT /api/documents/DOC?buscar_si_cambia=1 {"approved":false'


def _patch(vid, cuerpo):
    return _PATCH.format(vid=vid, cuerpo=json.dumps(cuerpo, separators=(",", ":")))


def _put(peticion, aprobar):
    """El PUT de cabecera: misma URL y ``approved``; el resto del cuerpo, el de hoy."""
    metodo, url, cuerpo = peticion.split(" ", 2)
    datos = json.loads(cuerpo)
    esperado = "/api/documents/DOC" if aprobar else "/api/documents/DOC?buscar_si_cambia=1"
    return metodo == "PUT" and url == esperado and datos["approved"] is aprobar and "lines" not in datos


def _correr(tmp_path, programa, preparacion=""):
    js = _app_js()
    faltan = [f for f in _FUNCIONES if f"function {f}(" not in js]
    assert not faltan, f"faltan en app.js: {faltan}"
    return _ejecutar_dom(tmp_path, _FUNCIONES, "const AVISO_PINTADO = " + json.dumps(AVISO_PINTADO) + ";\n"
                         + "const AVISO_GET = " + json.dumps(AVISO_GET) + ";\n" + _ESCENA + preparacion,
                         programa + "\nconsole.log(JSON.stringify(estado()));")


# =================================================================== #
# R1 · primero las filas, después la cabecera
# =================================================================== #
@con_node
def test_f077_r1_guardar_y_aprobar_guarda_las_filas_y_despues_aprueba(tmp_path):
    casos = _correr(tmp_path, """
        f1.cant.value = "6";
        f2.cant.value = "4";
        await guardarCabecera(true);
    """)
    pet = casos["peticiones"]
    assert pet[:3] == [_patch(12, {"cantidad": 6}), _patch(13, {"cantidad": 4}), _GET]
    assert len(pet) == 4 and _put(pet[3], True)
    assert casos["alertas"] == [] and casos["confirmaciones"] == []  # aviso vigente vacío
    assert casos["href"] == "/documents/DOC?msg=ok"


@con_node
def test_f077_r1_guardar_de_la_cabecera_guarda_las_filas_y_la_cabecera_sin_aprobar(tmp_path):
    casos = _correr(tmp_path, """
        f2.part.value = "05.01";
        await guardarCabecera(false);
    """)
    pet = casos["peticiones"]
    assert pet[0] == _patch(13, {"codigo_partida": "05.01"})
    assert len(pet) == 2 and _put(pet[1], False)
    assert casos["confirmaciones"] == []


# =================================================================== #
# R2 · sin filas con cambios, como hoy
# =================================================================== #
@con_node
@pytest.mark.parametrize("aprobar", [True, False])
def test_f077_r2_sin_cambios_ningun_patch(tmp_path, aprobar):
    casos = _correr(tmp_path, f"await guardarCabecera({json.dumps(aprobar)});")
    pet = casos["peticiones"]
    assert len(pet) == 1 and _put(pet[0], aprobar)
    assert casos["confirmaciones"] == ([AVISO_PINTADO] if aprobar else [])


# =================================================================== #
# R3 · una partida cambiada fuera de la lista para todo
# =================================================================== #
@con_node
@pytest.mark.parametrize("aprobar", [True, False])
def test_f077_r3_partida_mala_nada_enviado(tmp_path, aprobar):
    casos = _correr(tmp_path, f"""
        f1.cant.value = "6";
        f2.part.value = "zzzz";
        await guardarCabecera({json.dumps(aprobar)});
        estado.roja = f2.part.classList.contains("partida-invalida");
    """, preparacion="""
        const _estado = estado;
        estado = function () { return Object.assign(_estado(), {roja: estado.roja}); };
    """)
    assert casos["peticiones"] == []
    assert casos["alertas"] == [PARTIDAS_MALAS]
    assert casos["roja"] is True
    assert casos["guardarActivo"] and casos["aprobarActivo"]


# =================================================================== #
# R4 · un PATCH que falla para todo
# =================================================================== #
_FOTO_FILA = """
    const _estado = estado;
    estado = function () {
        return Object.assign(_estado(), {
            f1: {rojo: f1.tr.classList.contains("fila-no-guardada"), defecto: f1.cant.defaultValue,
                 sucia: f1.cant.classList.contains("cedit-dirty"), bloqueada: f1.cant.disabled && f1.part.disabled,
                 boton: f1.guardar.disabled},
            f2: {rojo: f2.tr.classList.contains("fila-no-guardada"), title: f2.tr.title || null,
                 defecto: f2.cant.defaultValue, bloqueada: f2.cant.disabled},
        });
    };
"""


@con_node
@pytest.mark.parametrize("aprobar, cola", [(True, "No se ha aprobado el albarán."),
                                           (False, "No se ha guardado la cabecera.")])
def test_f077_r4_falla_la_segunda_fila(tmp_path, aprobar, cola):
    casos = _correr(tmp_path, f"""
        fallos["13"] = {{status: 409, detail: "Línea guardada: desbloquéala para editarla"}};
        f1.cant.value = "6";
        f2.cant.value = "4";
        await guardarCabecera({json.dumps(aprobar)});
    """, preparacion=_FOTO_FILA)
    assert casos["peticiones"] == [_patch(12, {"cantidad": 6}), _patch(13, {"cantidad": 4})]
    assert casos["alertas"] == ["No se pudo guardar una línea (en rojo): Línea guardada: desbloquéala para "
                                "editarla. " + cola]
    assert casos["f2"] == {"rojo": True, "title": "Línea guardada: desbloquéala para editarla",
                           "defecto": "5", "bloqueada": False}
    assert casos["recargas"] == 0 and casos["href"] is None
    assert casos["guardarActivo"] and casos["aprobarActivo"]


@con_node
def test_f077_r4_error_de_red_en_la_primera(tmp_path):
    casos = _correr(tmp_path, """
        fallos["12"] = "red";
        f1.cant.value = "6";
        f2.cant.value = "4";
        await guardarCabecera(true);
    """, preparacion=_FOTO_FILA)
    assert casos["peticiones"] == [_patch(12, {"cantidad": 6})]
    assert casos["alertas"] == ["No se pudo guardar una línea (en rojo): error de red. No se ha aprobado el "
                                "albarán."]
    assert casos["f1"]["rojo"] is True and casos["f2"]["rojo"] is False


@con_node
def test_f077_r4_el_motivo_de_un_422_es_la_lista_de_detail(tmp_path):
    casos = _correr(tmp_path, """
        fallos["12"] = {status: 422, detail: [{loc: ["body", "cantidad"], msg: "no es un número"},
                                             {msg: "otro"}]};
        f1.cant.value = "6";
        await guardarCabecera(false);
    """)
    assert casos["alertas"] == ["No se pudo guardar una línea (en rojo): body.cantidad: no es un número | otro. "
                                "No se ha guardado la cabecera."]


# =================================================================== #
# R5 · lo guardado queda consolidado: el reintento no lo reenvía
# =================================================================== #
@con_node
def test_f077_r5_las_guardadas_se_consolidan_y_el_reintento_no_las_reenvia(tmp_path):
    casos = _correr(tmp_path, """
        fallos["13"] = {status: 500, detail: "caído"};
        f1.cant.value = "6";
        f1.cant.classList.add("cedit-dirty");
        f2.cant.value = "4";
        await guardarCabecera(true);
        const tras_fallo = estado();
        delete fallos["13"];
        peticiones.length = 0;
        await guardarCabecera(true);
        estado.tras_fallo = tras_fallo;
    """, preparacion=_FOTO_FILA + """
        const _estado2 = estado;
        estado = function () { return Object.assign(_estado2(), {tras_fallo: estado.tras_fallo}); };
    """)
    assert casos["tras_fallo"]["f1"] == {"rojo": False, "defecto": "6", "sucia": False, "bloqueada": True,
                                         "boton": True}
    pet = casos["peticiones"]
    assert pet[:2] == [_patch(13, {"cantidad": 4}), _GET] and len(pet) == 3 and _put(pet[2], True)
    assert casos["f2"]["rojo"] is False  # al reintentar se limpia el rojo


# =================================================================== #
# R6 · R7 · R8 · R9 · la confirmación de la suma y los fallos tras guardar
# =================================================================== #
@con_node
def test_f077_r6_con_filas_guardadas_el_aviso_es_el_vigente(tmp_path):
    casos = _correr(tmp_path, """
        avisoGet = AVISO_GET;
        f1.cant.value = "6";
        await guardarCabecera(true);
    """)
    assert casos["confirmaciones"] == [AVISO_GET]
    assert _put(casos["peticiones"][-1], True)


@con_node
def test_f077_r7_cancelar_con_filas_guardadas_recarga_sin_aprobar(tmp_path):
    casos = _correr(tmp_path, """
        avisoGet = AVISO_GET;
        respuestaConfirm = false;
        f1.cant.value = "6";
        await guardarCabecera(true);
    """)
    assert casos["peticiones"] == [_patch(12, {"cantidad": 6}), _GET]
    assert casos["recargas"] == 1


@con_node
def test_f077_r7_cancelar_sin_filas_guardadas_no_hace_nada_mas(tmp_path):
    casos = _correr(tmp_path, """
        respuestaConfirm = false;
        await guardarCabecera(true);
    """)
    assert casos["peticiones"] == [] and casos["recargas"] == 0
    assert casos["confirmaciones"] == [AVISO_PINTADO]
    assert casos["guardarActivo"] and casos["aprobarActivo"]


@con_node
def test_f077_r8_si_falla_la_lectura_del_aviso_no_aprueba_y_recarga(tmp_path):
    casos = _correr(tmp_path, """
        getFalla = true;
        f1.cant.value = "6";
        await guardarCabecera(true);
    """)
    assert casos["peticiones"] == [_patch(12, {"cantidad": 6}), _GET]
    assert casos["alertas"] == ["No se pudo comprobar la suma de las líneas: recarga y vuelve a aprobar."]
    assert casos["recargas"] == 1 and casos["confirmaciones"] == []


@con_node
def test_f077_r9_falla_el_put_tras_guardar_filas_recarga(tmp_path):
    casos = _correr(tmp_path, """
        putFalla = "Líneas sin descripción: 3";
        f1.cant.value = "6";
        await guardarCabecera(true);
    """)
    assert casos["alertas"] == ["Error al guardar: Líneas sin descripción: 3"]
    assert casos["recargas"] == 1


@con_node
def test_f077_r9_falla_el_put_sin_filas_guardadas_como_hoy(tmp_path):
    casos = _correr(tmp_path, """
        putFalla = "Líneas sin cantidad o importe: 2";
        respuestaConfirm = true;
        await guardarCabecera(true);
    """)
    assert casos["alertas"] == ["Error al guardar: Líneas sin cantidad o importe: 2"]
    assert casos["recargas"] == 0 and casos["href"] is None
    assert casos["guardarActivo"] and casos["aprobarActivo"]


# =================================================================== #
# R10 · botones desactivados; un segundo clic no repite nada
# =================================================================== #
@con_node
def test_f077_r10_doble_clic_un_solo_flujo(tmp_path):
    casos = _correr(tmp_path, """
        f1.cant.value = "6";
        const a = guardarCabecera(true);
        const b = guardarCabecera(true);
        await a;
        await b;
        estado.durante = botonesDuranteElPatch;
    """, preparacion="""
        const _estado = estado;
        estado = function () { return Object.assign(_estado(), {durante: estado.durante}); };
    """)
    pet = casos["peticiones"]
    assert pet[:2] == [_patch(12, {"cantidad": 6}), _GET] and len(pet) == 3
    assert casos["durante"] == {"guardar": True, "aprobar": True}


@con_node
def test_f077_r10_al_parar_respeta_el_aprobar_desactivado_de_la_plantilla(tmp_path):
    """Sin valorar, la plantilla pinta «Guardar y aprobar» desactivado: parar no lo activa."""
    casos = _correr(tmp_path, """
        approveBtn.disabled = true;
        f2.part.value = "zzzz";
        await guardarCabecera(false);
    """)
    assert casos["guardarActivo"] is True and casos["aprobarActivo"] is False


def test_f077_r10_los_botones_llaman_a_guardar_cabecera():
    js = _app_js()
    assert 'saveBtn.addEventListener("click", function () { guardarCabecera(false); })' in js
    assert 'approveBtn.addEventListener("click", function () { guardarCabecera(true); })' in js


# =================================================================== #
# R11 · el servidor sigue validando el PUT de aprobar
# =================================================================== #
def test_f077_r11_el_servidor_sigue_rechazando_aprobar_con_filas_incompletas():
    from f065_bbdd import DOC, construir, ejecutar, repositorio

    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = NULL WHERE id = 13")
    with pytest.raises(LineasIncompletasError) as error:
        repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")
    assert "Líneas sin descripción: 3" in error.value.aviso  # F-078 R17, la fila 13 («PORTES»)


# =================================================================== #
# R12 · R13 · una sola petición de PATCH de fila y adiós al aviso de F-065 R19
# =================================================================== #
def test_f077_r12_una_sola_peticion_patch_de_fila():
    js = _app_js()
    assert js.count("conciliacion/campos?bloquear=1") == 1
    assert js.count("b.detail.map(") + js.count("cuerpo.detail.map(") <= 1  # el motivo, una vez


def test_f077_r13_ya_no_avisa_de_filas_con_cambios_sin_guardar():
    """Ni «Guardar» ni «Guardar y aprobar» avisan ya «Hay N líneas con cambios sin
    guardar» (F-065 R19). El único uso que queda de ese aviso es la confirmación
    de «Dividir» (F-065 R29: dividir recarga la ficha), fuera del alcance de
    F-077 (design §8: wireDividir no se toca)."""
    from test_f051_almacen_front import _funcion_js

    js = _app_js()
    guardar = _funcion_js(js, "guardarCabecera") + _funcion_js(js, "guardarFilasPendientes")
    assert "avisoFilasSinGuardar" not in guardar and "contarFilasConCambios" not in guardar
    assert "con cambios sin guardar" not in guardar
    fuera_de_dividir = js
    for nombre in ("wireDividir", "avisoFilasSinGuardar", "contarFilasConCambios"):
        fuera_de_dividir = fuera_de_dividir.replace(_funcion_js(js, nombre), "")
    assert fuera_de_dividir.count("avisoFilasSinGuardar(") == 0
    assert fuera_de_dividir.count("contarFilasConCambios(") == 0
    assert "partidasInvalidas" not in js  # solo la usaba el aviso de F-065 R19
