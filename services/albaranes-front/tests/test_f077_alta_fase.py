# tests/test_f077_alta_fase.py
"""F-077 · B · el panel «Alta en Sigrid»: «Alta en curso…» solo mientras sv9 procesa.

- R14: fase ``en_curso`` / ``sin_respuesta`` / ``resultado`` (función pura con
  ``ahora`` inyectado; instantes comparados como instantes UTC).
- R17: ``no_admitido``, ``revisar`` y ``error`` son un error (``es_error``).
- R18: ``GET /api/documents/{id}/alta-sigrid/fase`` (200 con la fase, 404 sin
  documento; con la feature apagada, ``resultado`` sin leer el alta).
- R15, R16, R17: la plantilla del panel por fase (en curso, error de tiempo,
  resultado malo como error).
- R19: el sondeo cada 3 s de la ficha (node, con reloj y fetch falsos).
- R20: ni pintar ni sondear escriben el alta ni publican.

Sin red ni BBDD: dobles del repositorio y ``TestClient`` sobre ``build_app``.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime, timedelta

import pytest
from config.settings import Settings
from domain.models.alta_sigrid_models import AltaSigridVista, ConfigAltaSigrid
from domain.services import alta_sigrid as dominio
from fastapi.testclient import TestClient
from interface_adapters.web import app as modulo_app

DESDE = datetime(2026, 10, 1, tzinfo=UTC)
APROBADO = "2026-10-16T10:00:00+00:00"
APROBADO_EN = datetime(2026, 10, 16, 10, 0, tzinfo=UTC)
ANTERIOR = "2026-10-15T09:00:00+00:00"
A_1_MIN = APROBADO_EN + timedelta(minutes=1)
A_6_MIN = APROBADO_EN + timedelta(minutes=6)
REPETIBLES = ("no_admitido", "revisar", "error", "simulado", "anulado")
CONFIG = ConfigAltaSigrid(desde=DESDE)


def _alta(estado: str, approved_at_utc: str | None) -> AltaSigridVista:
    return AltaSigridVista(estado=estado, approved_at_utc=approved_at_utc)


def _fase(alta, ahora=A_1_MIN, *, aprobado=True, activo=True, approved_at_utc=APROBADO, config=CONFIG):
    return dominio.fase_alta(aprobado=aprobado, activo=activo, approved_at_utc=approved_at_utc,
                             alta=alta, config=config, ahora=ahora)


# =================================================================== #
# R14 · tabla de casos de la fase
# =================================================================== #
def test_f077_r14_constantes():
    assert (dominio.FASE_EN_CURSO, dominio.FASE_SIN_RESPUESTA, dominio.FASE_RESULTADO) == (
        "en_curso", "sin_respuesta", "resultado")
    assert dominio.TOPE_RESPUESTA_ALTA == timedelta(minutes=5)


def test_f077_r14_sin_fila_en_curso_y_a_los_5_min_sin_respuesta():
    assert _fase(None, A_1_MIN) == "en_curso"
    assert _fase(None, APROBADO_EN) == "en_curso"
    assert _fase(None, APROBADO_EN + timedelta(minutes=5) - timedelta(seconds=1)) == "en_curso"
    assert _fase(None, APROBADO_EN + timedelta(minutes=5)) == "sin_respuesta"
    assert _fase(None, A_6_MIN) == "sin_respuesta"


@pytest.mark.parametrize("estado", REPETIBLES)
@pytest.mark.parametrize("instante", [ANTERIOR, None, "no es una fecha", ""])
def test_f077_r14_repetible_de_una_aprobacion_anterior_espera(estado, instante):
    assert _fase(_alta(estado, instante), A_1_MIN) == "en_curso"
    assert _fase(_alta(estado, instante), A_6_MIN) == "sin_respuesta"


@pytest.mark.parametrize("estado", ["ya_en_sigrid", "registrado", "incierto", "en_curso"])
def test_f077_r14_no_repetible_anterior_es_la_respuesta(estado):
    """sv9 ignora la aprobación nueva (F-053 R7): esa fila es la respuesta."""
    assert _fase(_alta(estado, ANTERIOR), A_1_MIN) == "resultado"
    assert _fase(_alta(estado, ANTERIOR), A_6_MIN) == "resultado"


def test_f077_r14_en_curso_de_la_vigente_espera_hasta_el_tope():
    assert _fase(_alta("en_curso", APROBADO), A_1_MIN) == "en_curso"
    assert _fase(_alta("en_curso", APROBADO), A_6_MIN) == "sin_respuesta"


def test_f077_r14_se_compara_como_instante_no_como_texto():
    """El mismo instante escrito de otra forma (``Z``, otra zona) es la vigente."""
    for texto in ("2026-10-16T10:00:00Z", "2026-10-16T12:00:00+02:00", "2026-10-16 10:00:00"):
        assert _fase(_alta("en_curso", texto), A_1_MIN) == "en_curso"
        assert _fase(_alta("no_admitido", texto), A_1_MIN) == "resultado"
    # Anterior por instante, aunque su texto ordene después.
    assert _fase(_alta("no_admitido", "2026-10-16T11:30:00+02:00"), A_1_MIN) == "en_curso"


@pytest.mark.parametrize("estado", ["no_admitido", "simulado", "registrado", "revisar", "error",
                                    "ya_en_sigrid", "incierto", "anulado"])
def test_f077_r14_resultado_de_la_vigente(estado):
    assert _fase(_alta(estado, APROBADO), A_1_MIN) == "resultado"
    assert _fase(_alta(estado, APROBADO), A_6_MIN) == "resultado"


def test_f077_r14_alta_posterior_a_la_aprobacion_es_resultado():
    assert _fase(_alta("no_admitido", "2026-10-16T10:00:01+00:00"), A_1_MIN) == "resultado"


@pytest.mark.parametrize("campos", [
    {"config": ConfigAltaSigrid()},                     # feature apagada
    {"aprobado": False},                                # sin aprobar
    {"activo": False},                                  # papelera
    {"approved_at_utc": "2026-09-30T23:59:59+00:00"},   # antes de DESDE
    {"approved_at_utc": None},                          # sin instante de aprobación
    {"approved_at_utc": "ilegible"},
])
def test_f077_r14_documento_que_no_admite_alta_es_resultado(campos):
    assert _fase(None, A_1_MIN, **campos) == "resultado"
    assert _fase(_alta("no_admitido", ANTERIOR), A_6_MIN, **campos) == "resultado"


# =================================================================== #
# R17 · los estados malos son un error
# =================================================================== #
@pytest.mark.parametrize("estado, error", [
    ("no_admitido", True), ("revisar", True), ("error", True),
    ("en_curso", False), ("ya_en_sigrid", False), ("simulado", False), ("incierto", False),
    ("registrado", False), ("anulado", False),
])
def test_f077_r17_es_error(estado, error):
    from domain.models.alta_sigrid_models import ESTADOS_ALTA_ERROR

    assert ESTADOS_ALTA_ERROR == frozenset({"no_admitido", "revisar", "error"})
    assert _alta(estado, APROBADO).es_error is error


# =================================================================== #
# R14, R18, R20 · servicio
# =================================================================== #
class _Repo:
    """Solo lo que la fase puede leer; cualquier otra llamada (escribir el
    alta, publicar…) revienta el test (R20)."""

    def __init__(self, *, estado=None, alta=None, documento=None):
        self.estado = estado
        self.alta = alta
        self.documento = documento
        self.lecturas: list[str] = []

    def estado_aprobacion(self, document_id):
        self.lecturas.append("estado_aprobacion")
        return self.estado

    def leer_alta_sigrid(self, document_id):
        self.lecturas.append("leer_alta_sigrid")
        return self.alta

    def get_document_detail(self, document_id, *, view_mode):
        return self.documento

    def lineas_producto_sigrid(self, document_id):
        return []

    def __getattr__(self, nombre):
        raise AssertionError(f"la fase del alta no debe llamar a {nombre}")


class _Orquestador:
    def __getattr__(self, nombre):
        raise AssertionError(f"la fase del alta no publica ({nombre})")


def _servicio(repo, config=CONFIG):
    from application.services.review_service import ReviewService

    return ReviewService(repo, "r", _Orquestador(), config)


def _estado(approved_at_utc=APROBADO, approved=True, is_active=True):
    return {"approved": approved, "approved_at_utc": approved_at_utc, "is_active": is_active}


def test_f077_r18_servicio_fase_con_el_alta_del_repositorio():
    repo = _Repo(estado=_estado(), alta=_alta("no_admitido", ANTERIOR))
    assert _servicio(repo).fase_alta("d", ahora=A_1_MIN) == "en_curso"
    assert _servicio(repo).fase_alta("d", ahora=A_6_MIN) == "sin_respuesta"
    repo.alta = _alta("no_admitido", APROBADO)
    assert _servicio(repo).fase_alta("d", ahora=A_1_MIN) == "resultado"


def test_f077_r18_servicio_sin_documento_es_none():
    assert _servicio(_Repo(estado=None)).fase_alta("no", ahora=A_1_MIN) is None


def test_f077_r18_servicio_feature_apagada_resultado_sin_leer():
    repo = _Repo(estado=_estado())
    assert _servicio(repo, ConfigAltaSigrid()).fase_alta("d", ahora=A_1_MIN) == "resultado"
    assert repo.lecturas == []


def test_f077_r18_servicio_por_defecto_usa_el_reloj():
    ahora = datetime.now(UTC)
    repo = _Repo(estado=_estado((ahora - timedelta(minutes=1)).isoformat()))
    assert _servicio(repo).fase_alta("d") == "en_curso"
    repo.estado = _estado((ahora - timedelta(minutes=6)).isoformat())
    assert _servicio(repo).fase_alta("d") == "sin_respuesta"


def test_f077_r14_get_document_lleva_la_fase(documento_detalle):
    documento = documento_detalle()
    documento.approved = True
    ahora = datetime.now(UTC)
    repo = _Repo(estado=_estado((ahora - timedelta(minutes=1)).isoformat()), documento=documento)
    ficha = _servicio(repo).get_document(documento.id)
    assert ficha.alta_fase == "en_curso"
    repo.alta = _alta("simulado", (ahora - timedelta(minutes=1)).isoformat())
    repo.estado = _estado(repo.alta.approved_at_utc)
    assert _servicio(repo).get_document(documento.id).alta_fase == "resultado"


def test_f077_r14_alta_fase_por_defecto_es_resultado(documento_detalle):
    assert documento_detalle().alta_fase == "resultado"


# =================================================================== #
# R18, R20 · la ruta
# =================================================================== #
class _Publicador:
    def __init__(self):
        self.publicados: list = []

    def publicar(self, nombre_cola, mensaje):
        self.publicados.append((nombre_cola, mensaje))
        return True


class _ServicioFase:
    def __init__(self, fase):
        self.fase = fase
        self.llamadas: list = []

    def initialize(self):
        return True

    def fase_alta(self, document_id, **kwargs):
        self.llamadas.append(("fase_alta", document_id))
        return self.fase

    def __getattr__(self, nombre):
        raise AssertionError(f"la ruta de la fase no debe llamar a {nombre}")


def _cliente(monkeypatch, servicio):
    publicador = _Publicador()
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: publicador)
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes), follow_redirects=False), publicador


@pytest.mark.parametrize("fase", ["en_curso", "sin_respuesta", "resultado"])
def test_f077_r18_ruta_responde_la_fase(monkeypatch, fase):
    servicio = _ServicioFase(fase)
    cliente, publicador = _cliente(monkeypatch, servicio)
    respuesta = cliente.get("/api/documents/DOC-1/alta-sigrid/fase")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"fase": fase}
    assert servicio.llamadas == [("fase_alta", "DOC-1")]
    assert publicador.publicados == []  # R20


def test_f077_r18_ruta_404_sin_documento(monkeypatch):
    cliente, publicador = _cliente(monkeypatch, _ServicioFase(None))
    assert cliente.get("/api/documents/NO/alta-sigrid/fase").status_code == 404
    assert publicador.publicados == []


def test_f077_r20_la_ruta_es_get_y_solo_lectura():
    from pathlib import Path

    fuente = (Path(modulo_app.__file__)).read_text(encoding="utf-8")
    inicio = fuente.index('"/api/documents/{document_id}/alta-sigrid/fase"')
    bloque = fuente[fuente.rindex("@app.", 0, inicio):fuente.index("@app.", inicio)]
    assert bloque.startswith("@app.get(")
    assert "review_service.fase_alta(" in bloque
    for prohibido in ("publicar", "solicitar", "_publicar_feedback", "guardar", "save"):
        assert prohibido not in bloque


# =================================================================== #
# R15, R16, R17 · la plantilla del panel por fase
# =================================================================== #
_ALTA_COMPLETA = {
    "estado": "registrado", "modo": "real", "sigrid_cod": "AC26/0042", "sigrid_con_ide": 42,
    "adjunto_estado": "error", "intentos": 3, "ultimo_intento_at_utc": "2026-10-16T09:00:00+00:00",
    "approved_by": "pgris@ruesma.es", "approved_at_utc": ANTERIOR,
    "peticion": {"usu": "pgris", "lineas": [{"referencia_linea": "900", "producto": "QA9999",
                                              "descripcion": "GRUA 30T", "partida": "03.02",
                                              "cantidad": 2.0, "precio": 60.0}]},
    "respuesta": {"totales": {"totbas": 120.0, "totdoc": 145.2}, "lineas": []},
    "motivos": [{"codigo": "fecha_no_plausible", "detalle": "2025-01-01"},
                {"codigo": "importe_distinto", "detalle": "120 frente a 118", "referencia_linea": "900"}],
    "avisos": [{"codigo": "stock_negativo", "mensaje": "Stock por debajo de cero"}],
}

#: Nada del resultado anterior puede verse con la fase en_curso / sin_respuesta.
_DEL_RESULTADO = ["Estado:", "Registrado en Sigrid", "AC26/0042", "Modo:", "Intentos", "Último intento",
                  "Adjunto", "Usuario de Sigrid", "corrígelo", "fecha_no_plausible", "importe_distinto",
                  "GRUA 30T", "Total de la previa", "Avisos de Sigrid", "stock_negativo",
                  "Sin alta en Sigrid todavía", "alta-sigrid-motivos", "alta-sigrid-lineas"]

_SIN_RESPUESTA = ("Sigrid no ha respondido en 5 minutos. El alta aún puede completarse: recarga la página "
                  "más tarde para ver el resultado.")


def _ficha_alta(documento, fase, alta=None, *, puede=True, adjunto=True):
    documento.approved = True
    documento.alta_sigrid_activa = True
    documento.alta_sigrid = alta
    documento.alta_fase = fase
    documento.alta_puede_solicitar = puede
    documento.alta_puede_reintentar_adjunto = adjunto
    return documento


def _panel(html):
    encontrado = re.search(r'<section[^>]*id="alta-sigrid".*?</section>', html, re.DOTALL)
    return encontrado.group(0) if encontrado else None


def _clases(panel):
    return re.search(r'<section class="([^"]*)"', panel).group(1).split()


@pytest.mark.parametrize("alta", [None, AltaSigridVista(**_ALTA_COMPLETA)])
def test_f077_r15_en_curso_sin_nada_del_resultado_ni_botones(render_detalle, documento_detalle, alta):
    documento = _ficha_alta(documento_detalle(), "en_curso", alta)
    panel = _panel(render_detalle(documento))
    assert "Alta en curso…" in panel
    assert "La ficha se actualizará sola cuando Sigrid responda." in panel
    assert 'data-fase="en_curso"' in panel
    assert f'data-document-id="{documento.id}"' in panel
    for texto in _DEL_RESULTADO:
        assert texto not in panel, texto
    assert "<button" not in panel and "<form" not in panel
    assert "error" not in _clases(panel)


@pytest.mark.parametrize("alta", [None, AltaSigridVista(**_ALTA_COMPLETA)])
@pytest.mark.parametrize("puede", [True, False])
def test_f077_r16_sin_respuesta_error_de_tiempo(render_detalle, documento_detalle, alta, puede):
    panel = _panel(render_detalle(_ficha_alta(documento_detalle(), "sin_respuesta", alta, puede=puede)))
    assert "error" in _clases(panel)
    assert 'data-fase="sin_respuesta"' in panel
    assert _SIN_RESPUESTA in panel
    for texto in _DEL_RESULTADO:
        assert texto not in panel, texto
    assert ("alta-sigrid/solicitar" in panel) is puede
    assert "reintentar-adjunto" not in panel and "verificar-anulacion" not in panel
    assert "Alta en curso" not in panel


@pytest.mark.parametrize("estado", ["no_admitido", "revisar", "error"])
def test_f077_r17_resultado_malo_es_error(render_detalle, documento_detalle, estado):
    alta = AltaSigridVista(**{**_ALTA_COMPLETA, "estado": estado, "approved_at_utc": APROBADO})
    panel = _panel(render_detalle(_ficha_alta(documento_detalle(), "resultado", alta)))
    assert "error" in _clases(panel)
    assert f"Error en el alta en Sigrid: {alta.estado_texto}" in panel
    assert "Estado:" not in panel
    assert 'data-fase="resultado"' in panel
    assert "fecha_no_plausible" in panel  # con sus motivos (D)


@pytest.mark.parametrize("estado", ["simulado", "ya_en_sigrid", "registrado", "incierto", "anulado", "en_curso"])
def test_f077_r17_resto_de_estados_como_hoy(render_detalle, documento_detalle, estado):
    alta = AltaSigridVista(**{**_ALTA_COMPLETA, "estado": estado, "approved_at_utc": APROBADO})
    panel = _panel(render_detalle(_ficha_alta(documento_detalle(), "resultado", alta)))
    assert "error" not in _clases(panel)
    assert "Error en el alta" not in panel
    assert f'Estado: <strong class="alta-sigrid-estado estado-{estado}">{alta.estado_texto}</strong>' in panel
    assert ("warning" in _clases(panel)) is alta.bloqueante


def test_f077_r17_resultado_sin_alta_como_hoy(render_detalle, documento_detalle):
    panel = _panel(render_detalle(_ficha_alta(documento_detalle(), "resultado", None)))
    assert "Sin alta en Sigrid todavía." in panel and "alta-sigrid/solicitar" in panel
    assert "info" in _clases(panel)


# =================================================================== #
# R19 · el sondeo de la ficha, ejecutado con node
# =================================================================== #
_SONDEO = """
    const relojes = [];
    globalThis.setTimeout = function (f, ms) { relojes.push({f: f, ms: ms}); return relojes.length; };
    globalThis.setInterval = function () { throw new Error("nada de setInterval"); };
    const peticiones = [];
    let respuestas = [];
    globalThis.fetch = function (url, init) {
        peticiones.push({url: url, accept: init && init.headers && init.headers.Accept});
        const r = respuestas.shift();
        if (r === "red") { return Promise.reject(new Error("red caída")); }
        return Promise.resolve({
            ok: r.status >= 200 && r.status < 300, status: r.status,
            json: function () {
                return r.json === "ilegible" ? Promise.reject(new Error("x")) : Promise.resolve(r.json);
            },
        });
    };
    function vaciar() { return new Promise(function (r) { setImmediate(r); }); }
    async function disparar() {
        const reloj = relojes.shift();
        reloj.f();
        for (let i = 0; i < 5; i++) { await vaciar(); }
        return reloj.ms;
    }
    function panelCon(fase) {
        const p = el("section", "alert alta-sigrid info", document.body);
        p.id = "alta-sigrid";
        p.dataset.fase = fase;
        p.dataset.documentId = "DOC-1";
        return p;
    }
"""

_con_node = pytest.mark.skipif(shutil.which("node") is None, reason="node no está instalado")


def _sondeo(tmp_path, programa):
    from test_f051_almacen_front import _app_js
    from test_f065_f3bis_front import _ejecutar_dom

    constante = re.search(r"const SONDEO_ALTA_MS = (\d+);", _app_js()).group(0)
    return _ejecutar_dom(tmp_path, ["sondearAltaEnCurso"], constante + "\n" + _SONDEO, programa)


@_con_node
def test_f077_r19_sondea_cada_3_s_y_recarga_una_vez_al_cambiar(tmp_path):
    casos = _sondeo(tmp_path, """
        respuestas = ["red", {status: 500, json: {}}, {status: 200, json: "ilegible"},
                      {status: 200, json: {}}, {status: 200, json: {fase: "en_curso"}},
                      {status: 200, json: {fase: "resultado"}}];
        sondearAltaEnCurso(panelCon("en_curso"));
        const antes = {peticiones: peticiones.length, relojes: relojes.length};
        const esperas = [];
        while (relojes.length) { esperas.push(await disparar()); }
        console.log(JSON.stringify({antes, esperas, peticiones, recargas: window._recargas}));
    """)
    assert casos["antes"] == {"peticiones": 0, "relojes": 1}
    assert casos["esperas"] == [3000] * 6
    assert casos["peticiones"] == [{"url": "/api/documents/DOC-1/alta-sigrid/fase",
                                    "accept": "application/json"}] * 6
    assert casos["recargas"] == 1


@_con_node
@pytest.mark.parametrize("fase", ["sin_respuesta", "resultado"])
def test_f077_r19_cualquier_otra_fase_recarga(tmp_path, fase):
    casos = _sondeo(tmp_path, """
        respuestas = [{status: 200, json: {fase: FASE}}];
        sondearAltaEnCurso(panelCon("en_curso"));
        await disparar();
        console.log(JSON.stringify({recargas: window._recargas, relojes: relojes.length}));
    """.replace("FASE", json.dumps(fase)))
    assert casos == {"recargas": 1, "relojes": 0}


@_con_node
def test_f077_r19_un_404_para_el_sondeo(tmp_path):
    casos = _sondeo(tmp_path, """
        respuestas = [{status: 503, json: {}}, {status: 404, json: {detail: "no"}}];
        sondearAltaEnCurso(panelCon("en_curso"));
        await disparar();
        await disparar();
        console.log(JSON.stringify({recargas: window._recargas, relojes: relojes.length,
                                    peticiones: peticiones.length}));
    """)
    assert casos == {"recargas": 0, "relojes": 0, "peticiones": 2}


@_con_node
@pytest.mark.parametrize("fase", ["sin_respuesta", "resultado", ""])
def test_f077_r19_sin_en_curso_ninguna_consulta(tmp_path, fase):
    casos = _sondeo(tmp_path, """
        sondearAltaEnCurso(panelCon(FASE));
        sondearAltaEnCurso(null);
        console.log(JSON.stringify({relojes: relojes.length, peticiones: peticiones.length}));
    """.replace("FASE", json.dumps(fase)))
    assert casos == {"relojes": 0, "peticiones": 0}


def test_f077_r19_arranca_solo_con_el_panel_y_sin_set_interval():
    from test_f051_almacen_front import _app_js, _funcion_js

    js = _app_js()
    assert "const SONDEO_ALTA_MS = 3000;" in js
    assert 'sondearAltaEnCurso(document.getElementById("alta-sigrid"));' in js
    assert "setInterval" not in _funcion_js(js, "sondearAltaEnCurso")


def test_f077_r18_la_ruta_queda_fuera_del_esquema_openapi(monkeypatch):
    """Superviviente de la campaña (app.py, ``include_in_schema``): la ruta es
    interna del JS de sv4 (design §1) y no se publica en ``/openapi.json``."""
    cliente, _ = _cliente(monkeypatch, _ServicioFase("resultado"))
    rutas = cliente.app.openapi()["paths"]
    assert "/api/documents/{document_id}/alta-sigrid/fase" not in rutas
    assert "/api/documents/{document_id}" in rutas  # el esquema sí lleva las demás
