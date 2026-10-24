# tests/test_f076_partidas_sv4.py
"""F-076 T5 · el selector de partidas de sv4 lee la lista desde comun (R15).

- R15: ``/api/sigrid/partidas`` devuelve, para las mismas filas, los MISMOS
  ``items`` que antes de F-076 (``_ITEMS_DE_HOY`` se fijó contra el código de
  sv4 ANTES de delegar: pasa en verde antes y después), sin SQL ni cálculo de
  hojas propios en sv4 (``ruesma_comun.sigrid.leer_partidas_obra``).
- Cambios aceptados (P7): solo partidas de la empresa 1 (``con_obr.emp = 1``)
  y, si la lista llega truncada, ``ok=false`` (``NO_TOLERA`` y 500.000 filas).

Sin red: ``httpx.MockTransport`` en lugar del transporte real.
"""
from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from infrastructure.sigrid import sigrid_lookup_client as modulo
from infrastructure.sigrid.sigrid_lookup_client import SigridLookupClient

_COLUMNAS = ["ide", "padide", "cod", "res"]
# Árbol con todo lo que trata el cálculo de hojas: padre 0 y nulo (= sin
# padre), fila sin ``ide`` (fuera), hoja sin ``cod`` (fuera), capítulo y
# subcapítulo con su ruta, un ``res`` vacío en la ruta, códigos con espacios
# exteriores y un ``ide`` repetido (gana la última fila).
_FILAS = [
    [1, 0, "01", "MOVIMIENTO DE TIERRAS"],
    [2, 1, "01.01", "EXCAVACIÓN"],
    [3, 2, "01.01.01", "Excavación en zanja"],
    [4, 2, " 01.01.02 ", "  Relleno  "],
    [5, None, "02", "ESTRUCTURA"],
    [6, 5, "02.01", None],
    [7, 6, "02.01.01", "Hormigón HA-25"],
    [8, 5, "02.02", ""],
    [None, 5, "02.99", "SIN IDE"],
    [9, 5, None, "HOJA SIN CODIGO"],
    [10, "0", "CI.04.18", "Costes indirectos"],
    [11, 10, "CI.04.18.01", "No es hoja: 10 es su padre"],
    [12, 0, "ALM", "ALMACEN"],
    [7, 6, "02.01.01", "Hormigón HA-25 (repetida)"],
]
# Lo que devolvía sv4 antes de F-076 para esas filas (orden por código).
_ITEMS_DE_HOY = [
    {"codigo": "01.01.01", "descripcion": "Excavación en zanja",
     "descripcion_agregada": "MOVIMIENTO DE TIERRAS › EXCAVACIÓN › Excavación en zanja"},
    {"codigo": "01.01.02", "descripcion": "Relleno",
     "descripcion_agregada": "MOVIMIENTO DE TIERRAS › EXCAVACIÓN › Relleno"},
    {"codigo": "02.01.01", "descripcion": "Hormigón HA-25 (repetida)",
     "descripcion_agregada": "ESTRUCTURA › Hormigón HA-25 (repetida)"},
    {"codigo": "02.02", "descripcion": None, "descripcion_agregada": "ESTRUCTURA"},
    {"codigo": "ALM", "descripcion": "ALMACEN", "descripcion_agregada": "ALMACEN"},
    {"codigo": "CI.04.18.01", "descripcion": "No es hoja: 10 es su padre",
     "descripcion_agregada": "Costes indirectos › No es hoja: 10 es su padre"},
]


class _SigridApi:
    """Responde a la consulta de partidas (sea la SQL de sv4 o la de comun)."""

    def __init__(self, *, filas=None, truncated: bool = False) -> None:
        self.filas = list(_FILAS if filas is None else filas)
        self.truncated = truncated
        self.peticiones: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        cuerpo = json.loads(request.content)
        self.peticiones.append(cuerpo)
        assert "obrparpar" in cuerpo["sql"]
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


def _items(partidas) -> list[dict]:
    return [
        {"codigo": p.codigo, "descripcion": p.descripcion, "descripcion_agregada": p.descripcion_agregada}
        for p in partidas
    ]


# ------------------------------------------------------------------ #
# R15 · mismos items que hoy (verde antes y después de delegar)
# ------------------------------------------------------------------ #
def test_f076_r15_mismos_items_que_hoy_para_las_mismas_filas(sigrid):
    api = sigrid()
    assert _items(_cliente().fetch_partidas_por_obra(codigo_obra="0691")) == _ITEMS_DE_HOY
    assert len(api.peticiones) == 1
    assert api.peticiones[0]["parameters"] == ["0691"]


def test_f076_r15_sin_filas_lista_vacia(sigrid):
    sigrid(filas=[])
    assert _cliente().fetch_partidas_por_obra(codigo_obra="0691") == []


@pytest.mark.parametrize("vacia", ["", "   "])
def test_f076_r15_sin_obra_no_consulta(sigrid, vacia):
    api = sigrid()
    assert _cliente().fetch_partidas_por_obra(codigo_obra=vacia) == []
    assert api.peticiones == []


def test_f076_r15_obra_canonica_de_f070(sigrid):
    api = sigrid()
    _cliente().fetch_partidas_por_obra(codigo_obra=" 686 ")
    assert api.peticiones[0]["parameters"] == ["0686"]


# ------------------------------------------------------------------ #
# R15 · la SQL y el cálculo viven en comun (P7: empresa 1)
# ------------------------------------------------------------------ #
def test_f076_r15_la_sql_es_la_de_comun_con_la_empresa_1(sigrid):
    from ruesma_comun.sigrid import SQL_PARTIDAS_POR_OBRA

    api = sigrid()
    _cliente().fetch_partidas_por_obra(codigo_obra="0691")
    assert api.peticiones[0]["sql"] == SQL_PARTIDAS_POR_OBRA
    assert "con_obr.emp = 1" in api.peticiones[0]["sql"]


def test_f076_r15_sv4_no_guarda_copia_de_la_sql_ni_del_calculo():
    from ruesma_comun.sigrid import SQL_PARTIDAS_POR_OBRA

    # El nombre de siempre sigue existiendo (los tests de F-052 y F-070 lo usan
    # para reconocer la consulta), pero ES la de comun, no una copia.
    assert getattr(modulo, "_SQL_PARTIDAS_POR_OBRA", SQL_PARTIDAS_POR_OBRA) is SQL_PARTIDAS_POR_OBRA
    raiz = Path(__file__).resolve().parents[1]
    fuente = (raiz / "infrastructure/sigrid/sigrid_lookup_client.py").read_text(encoding="utf-8")
    assert "obrparpar" not in fuente.lower()
    assert "parent_ides" not in fuente and "padide" not in fuente


# ------------------------------------------------------------------ #
# R15 · P7: NO_TOLERA y 500.000 filas; truncada ⇒ ok=false
# ------------------------------------------------------------------ #
def test_f076_r15_partidas_piden_500000_filas(sigrid):
    from ruesma_comun.sigrid import MAX_FILAS_POR_PETICION

    api = sigrid()
    _cliente().fetch_partidas_por_obra(codigo_obra="0691")
    assert api.peticiones[0]["max_rows"] == MAX_FILAS_POR_PETICION == 500_000


def test_f076_r15_post_sql_read_por_defecto_el_max_rows_del_cliente(sigrid):
    api = sigrid()
    cliente = _cliente()
    cliente._post_sql_read(sql="SELECT 1 FROM obrparpar", parameters=[], label="x",
                           politica=modulo.PoliticaTruncado.TOLERA)
    cliente._post_sql_read(sql="SELECT 1 FROM obrparpar", parameters=[], label="x",
                           politica=modulo.PoliticaTruncado.TOLERA, max_rows=123)
    assert [p["max_rows"] for p in api.peticiones] == [5000, 123]


def test_f076_r15_lista_truncada_lanza(sigrid):
    from ruesma_comun.sigrid import SigridRespuestaTruncada

    sigrid(truncated=True)
    with pytest.raises(SigridRespuestaTruncada) as exc:
        _cliente().fetch_partidas_por_obra(codigo_obra="0691")
    assert exc.value.etiqueta == "partidas_obra_0691"


# ------------------------------------------------------------------ #
# El endpoint (``build_app`` con dobles: sin BBDD, sin colas, sin .env)
# ------------------------------------------------------------------ #
class _PublicadorFalso:
    def publicar(self, nombre_cola, mensaje):
        return True


class _ServicioFalso:
    def initialize(self) -> bool:
        return True


@pytest.fixture
def portal(monkeypatch):
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web import app as modulo_app

    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: _ServicioFalso())
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: _PublicadorFalso())
    ajustes = Settings.model_construct(
        pg_password="x", pg_admin_password="x", sigrid_api_base_url="https://sigrid.invalid",
        sigrid_api_function_key="clave-de-test", sigrid_api_database="db-test",
    )
    return TestClient(modulo_app.build_app(ajustes))


def test_f076_r15_el_endpoint_sirve_los_items_de_hoy(sigrid, portal):
    sigrid()
    respuesta = portal.get("/api/sigrid/partidas", params={"obra": "0691"})
    assert respuesta.status_code == 200
    # F-098 R14 añade campos por hoja (ide, código completo, capítulo, cod
    # repetido) y los capítulos de la obra; los tres de siempre no cambian.
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is True
    assert [
        {k: it[k] for k in ("codigo", "descripcion", "descripcion_agregada")} for it in cuerpo["items"]
    ] == _ITEMS_DE_HOY


def test_f076_r15_el_endpoint_con_lista_truncada_responde_ok_false(sigrid, portal):
    sigrid(truncated=True)
    cuerpo = portal.get("/api/sigrid/partidas", params={"obra": "0691"}).json()
    assert cuerpo["ok"] is False
    assert cuerpo["items"] == []
