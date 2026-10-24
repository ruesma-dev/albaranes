# tests/test_f098_lista_sv4.py
"""F-098 T8 · la lista de partidas de sv4: caché propia y capítulos (R14, R27, R28).

- R27: sv4 lee la lista por una ``CachePartidasObra`` propia (comun) sobre el
  lector público del cliente (``lector_partidas``), con ``PARTIDAS_OBRA_TTL_S``
  (600), ``PARTIDAS_OBRA_MAX_OBRAS`` (64) y ``PARTIDAS_OBRA_FALLO_TTL_S`` (60).
  Sin ``SIGRID_API_*``: ni cliente ni caché, y todo como hoy.
- R14: ``GET /api/sigrid/partidas`` lee por esa caché (``consultar``) y da, por
  hoja, ``ide``, ``codigo`` (cod), ``codigo_completo``, ``capitulo``,
  ``descripcion``, ``descripcion_agregada`` y ``cod_repetido``, y ``capitulos``
  (``codigo``, ``descripcion``, ``n``); ``ok=false`` si no hay cliente, falta la
  obra, falla o trunca.
- R28: la caché se pasa a ``ReviewService`` (la ficha la usa al pintar).

Sin red: ``httpx.MockTransport`` en lugar del transporte real.
"""
from __future__ import annotations

import json

import httpx
import pytest
from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient

_COLUMNAS = ["ide", "padide", "cod", "res"]
#: La 0686 de T0, recortada (``ANT.``, CD con ``99.01.64``, CI) y un cod
#: repetido en CI para ``cod_repetido``.
_FILAS_0686 = [
    [1, 0, "ANT.", "AJUSTES ALMACÉN"],
    [2, 1, "98.01", "Anticipos"],
    [10, 0, "CD", "COSTES DIRECTOS"],
    [11, 10, "99", "VARIOS"],
    [13, 11, "99.01.64", "Material de obra"],
    [20, 0, "CI", "COSTES INDIRECTOS"],
    [21, 20, "CI.4.18", "Costes indirectos de obra"],
    [22, 20, "CI.6", "Varios"],
    [23, 22, "CI.6.1", "Varios a"],
    [24, 20, "CI.7", "Varios bis"],
    [25, 24, "CI.6.1", "Varios b"],
]


class _SigridApi:
    def __init__(self, *, filas=None, truncated=False, status=200) -> None:
        self.filas = list(_FILAS_0686 if filas is None else filas)
        self.truncated = truncated
        self.status = status
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        cuerpo = json.loads(request.content)
        self.peticiones.append(cuerpo)
        if self.status != 200:
            return httpx.Response(self.status, text="clave-secreta-en-el-error")
        return httpx.Response(200, json={
            "ok": True, "columns": _COLUMNAS, "rows": self.filas, "truncated": self.truncated,
        })


@pytest.fixture
def sigrid(monkeypatch):
    def _instalar(**kw) -> _SigridApi:
        doble = _SigridApi(**kw)
        monkeypatch.setattr(modulo.httpx, "HTTPTransport", lambda *a, **k: httpx.MockTransport(doble))
        return doble

    return _instalar


def _cliente() -> SigridLookupClient:
    return SigridLookupClient(base_url="https://sigrid.invalid", function_key="clave-de-test", database="db-test")


# ------------------------------------------------------------------ #
# R27 · settings y lector público
# ------------------------------------------------------------------ #
def test_f098_r27_settings_por_defecto():
    from config.settings import Settings

    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    assert (ajustes.partidas_obra_ttl_s, ajustes.partidas_obra_max_obras, ajustes.partidas_obra_fallo_ttl_s) == (
        600.0, 64, 60.0,
    )


def test_f098_r27_settings_desde_el_entorno(monkeypatch):
    from config.settings import Settings

    monkeypatch.setenv("PARTIDAS_OBRA_TTL_S", "30")
    monkeypatch.setenv("PARTIDAS_OBRA_MAX_OBRAS", "5")
    monkeypatch.setenv("PARTIDAS_OBRA_FALLO_TTL_S", "7")
    ajustes = Settings(_env_file=None, PG_PASSWORD="x", PG_ADMIN_PASSWORD="x")
    assert (ajustes.partidas_obra_ttl_s, ajustes.partidas_obra_max_obras, ajustes.partidas_obra_fallo_ttl_s) == (
        30.0, 5, 7.0,
    )


def test_f098_r27_lector_partidas_publico_aplica_politica_y_max_rows(sigrid):
    from ruesma_comun.sigrid import MAX_FILAS_POR_PETICION, PoliticaTruncado

    api = sigrid()
    columnas, filas = _cliente().lector_partidas(
        "SELECT 1 FROM obrparpar", ["0686"], "partidas_obra_0686", PoliticaTruncado.NO_TOLERA,
        MAX_FILAS_POR_PETICION,
    )
    assert columnas == _COLUMNAS and len(filas) == len(_FILAS_0686)
    assert api.peticiones[0]["max_rows"] == MAX_FILAS_POR_PETICION
    assert api.peticiones[0]["parameters"] == ["0686"]


def test_f098_r27_lector_partidas_con_truncado_lanza(sigrid):
    from ruesma_comun.sigrid import MAX_FILAS_POR_PETICION, PoliticaTruncado, SigridRespuestaTruncada

    sigrid(truncated=True)
    with pytest.raises(SigridRespuestaTruncada):
        _cliente().lector_partidas("SELECT 1", ["0686"], "x", PoliticaTruncado.NO_TOLERA, MAX_FILAS_POR_PETICION)


def test_f098_r14_partida_option_lleva_los_campos_nuevos(sigrid):
    sigrid()
    partidas = {p.codigo_completo: p for p in _cliente().fetch_partidas_por_obra(codigo_obra="0686")}
    p = partidas["CD.99.01.64"]
    assert (p.ide, p.codigo, p.capitulo, p.cod_repetido) == (13, "99.01.64", "CD", False)
    assert partidas["ANT.98.01"].capitulo == "ANT."
    repetidas = [x for x in _cliente().fetch_partidas_por_obra(codigo_obra="0686") if x.codigo == "CI.6.1"]
    assert [x.cod_repetido for x in repetidas] == [True, True]


def test_f098_r14_partida_option_con_defectos():
    from domain.models.review_models import PartidaOption

    p = PartidaOption(codigo="X")
    assert (p.ide, p.codigo_completo, p.capitulo, p.cod_repetido) == (None, None, None, False)


# ------------------------------------------------------------------ #
# El endpoint y el cableado (``build_app`` con dobles)
# ------------------------------------------------------------------ #
class _PublicadorFalso:
    def publicar(self, nombre_cola, mensaje):
        return True


class _ServicioFalso:
    def __init__(self, *args) -> None:
        self.args = args

    def initialize(self) -> bool:
        return True


def _construir(monkeypatch, **ajustes_extra):
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web import app as modulo_app

    creados: list[_ServicioFalso] = []

    def _servicio(*args):
        creados.append(_ServicioFalso(*args))
        return creados[-1]

    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", _servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: _PublicadorFalso())
    base = {
        "pg_password": "x", "pg_admin_password": "x", "sigrid_api_base_url": "https://sigrid.invalid",
        "sigrid_api_function_key": "clave-de-test", "sigrid_api_database": "db-test",
    }
    base.update(ajustes_extra)
    app = modulo_app.build_app(Settings.model_construct(**base))
    return TestClient(app), app, creados


@pytest.fixture
def portal(monkeypatch):
    def _portal(**extra):
        return _construir(monkeypatch, **extra)

    return _portal


def test_f098_r14_endpoint_con_capitulos_y_campos_nuevos(sigrid, portal):
    sigrid()
    cliente, _app, _ = portal()
    cuerpo = cliente.get("/api/sigrid/partidas", params={"obra": "686"}).json()
    assert cuerpo["ok"] is True
    assert cuerpo["capitulos"] == [
        {"codigo": "ANT.", "descripcion": "AJUSTES ALMACÉN", "n": 1},
        {"codigo": "CD", "descripcion": "COSTES DIRECTOS", "n": 1},
        {"codigo": "CI", "descripcion": "COSTES INDIRECTOS", "n": 3},
    ]
    por_completo = {it["codigo_completo"]: it for it in cuerpo["items"]}
    assert por_completo["CD.99.01.64"] == {
        "ide": 13, "codigo": "99.01.64", "codigo_completo": "CD.99.01.64", "capitulo": "CD",
        "descripcion": "Material de obra", "descripcion_agregada": "COSTES DIRECTOS › VARIOS › Material de obra",
        "cod_repetido": False,
    }
    assert [it["cod_repetido"] for it in cuerpo["items"] if it["codigo"] == "CI.6.1"] == [True, True]
    assert [it["codigo"] for it in cuerpo["items"]] == ["98.01", "99.01.64", "CI.4.18", "CI.6.1", "CI.6.1"]


def test_f098_r27_dos_peticiones_de_la_misma_obra_una_lectura(sigrid, portal):
    api = sigrid()
    cliente, _app, _ = portal()
    primera = cliente.get("/api/sigrid/partidas", params={"obra": "0686"}).json()
    segunda = cliente.get("/api/sigrid/partidas", params={"obra": "686"}).json()
    assert primera == segunda
    assert len(api.peticiones) == 1


def test_f098_r27_ttl_de_settings(sigrid, portal):
    _api = sigrid()
    _cliente_http, app, _ = portal(partidas_obra_ttl_s=0.0, partidas_obra_max_obras=1, partidas_obra_fallo_ttl_s=0.0)
    cache = app.state.partidas_obra
    assert (cache._ttl_s, cache._max_obras, cache._ttl_fallo_s) == (0.0, 1, 0.0)


def test_f098_r27_cache_por_defecto_de_settings(sigrid, portal):
    sigrid()
    _cliente_http, app, _ = portal()
    cache = app.state.partidas_obra
    assert (cache._ttl_s, cache._max_obras, cache._ttl_fallo_s) == (600.0, 64, 60.0)


def test_f098_r14_truncado_ok_false_sin_items(sigrid, portal):
    sigrid(truncated=True)
    cliente, _app, _ = portal()
    cuerpo = cliente.get("/api/sigrid/partidas", params={"obra": "0686"}).json()
    assert cuerpo["ok"] is False
    assert (cuerpo["items"], cuerpo["capitulos"]) == ([], [])


def test_f098_r14_fallo_ok_false_y_el_error_no_lleva_la_excepcion(sigrid, portal):
    sigrid(status=500)
    cliente, _app, _ = portal()
    cuerpo = cliente.get("/api/sigrid/partidas", params={"obra": "0686"}).json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []
    assert "clave-secreta" not in cuerpo["error"] and "500" not in cuerpo["error"]
    assert cuerpo["error"]


def test_f098_r14_fallo_con_lista_caducada_sigue_ok_false(sigrid, portal):
    api = sigrid()
    cliente, app, _ = portal(partidas_obra_ttl_s=0.0)
    assert cliente.get("/api/sigrid/partidas", params={"obra": "0686"}).json()["ok"] is True
    api.status = 500
    cuerpo = cliente.get("/api/sigrid/partidas", params={"obra": "0686"}).json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []


def test_f098_r14_cero_hojas_ok_true_y_vacio(sigrid, portal):
    sigrid(filas=[])
    cliente, _app, _ = portal()
    assert cliente.get("/api/sigrid/partidas", params={"obra": "0686"}).json() == {
        "ok": True, "items": [], "capitulos": [],
    }


@pytest.mark.parametrize("obra", ["", "   "])
def test_f098_r14_sin_obra_ok_false_sin_consultar(sigrid, portal, obra):
    api = sigrid()
    cliente, _app, _ = portal()
    cuerpo = cliente.get("/api/sigrid/partidas", params={"obra": obra}).json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []
    assert api.peticiones == []


def test_f098_r27_sin_sigrid_ni_cliente_ni_cache_como_hoy(sigrid, portal):
    api = sigrid()
    cliente, app, creados = portal(sigrid_api_base_url=None)
    assert app.state.sigrid_lookup_client is None
    assert app.state.partidas_obra is None
    cuerpo = cliente.get("/api/sigrid/partidas", params={"obra": "0686"}).json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []
    assert "SIGRID_API_" in cuerpo["error"]
    assert api.peticiones == []
    (servicio,) = creados
    assert servicio.args[4] is None


def test_f098_r28_la_cache_se_pasa_a_review_service(sigrid, portal):
    sigrid()
    _cliente_http, app, creados = portal()
    (servicio,) = creados
    assert len(servicio.args) == 5
    assert servicio.args[4] is app.state.partidas_obra
    from ruesma_comun.sigrid import CachePartidasObra

    assert isinstance(app.state.partidas_obra, CachePartidasObra)
