# tests/test_f114_endpoint.py
"""F-114 · ``GET /api/sigrid/proveedores/todos?q=`` (R12–R14, R21).

``build_app`` con dobles (sin BBDD, sin colas, sin .env; patrón de
``test_f076_partidas_sv4.py``) y el cliente de Sigrid cambiado por uno falso
que apunta lo que se le pide. Nombres y CIF inventados.
"""
from __future__ import annotations

import pytest

from domain.models.review_models import BusquedaProveedores, ProveedorOption


class _PublicadorFalso:
    def publicar(self, nombre_cola, mensaje):
        return True


class _ServicioFalso:
    def initialize(self) -> bool:
        return True


class _ClienteFalso:
    def __init__(self, *, resultado=None, error=None):
        self.resultado = resultado
        self.error = error
        self.busquedas: list[str] = []
        self.obras: list[str] = []

    def buscar_proveedores(self, *, texto):
        self.busquedas.append(texto)
        if self.error:
            raise self.error
        return self.resultado

    def fetch_proveedores_por_obra(self, *, codigo_obra):
        self.obras.append(codigo_obra)
        return [ProveedorOption(cif="B00000001", nombre="ALFA SL")]


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
    app = modulo_app.build_app(ajustes)
    cliente_http = TestClient(app)

    def _con(cliente):
        app.state.sigrid_lookup_client = cliente
        return cliente_http

    return _con


_RESULTADO = BusquedaProveedores(
    items=[
        ProveedorOption(cif="B00000001", nombre="ALFA SL", fichas=1),
        ProveedorOption(cif="B00000002", nombre="BETA SA", fichas=2),
    ],
    mas=True,
)


def test_f114_r12_responde_items_con_fichas_y_mas(portal):
    falso = _ClienteFalso(resultado=_RESULTADO)
    respuesta = portal(falso).get("/api/sigrid/proveedores/todos", params={"q": " alfa "})
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "ok": True,
        "items": [
            {"cif": "B00000001", "nombre": "ALFA SL", "fichas": 1},
            {"cif": "B00000002", "nombre": "BETA SA", "fichas": 2},
        ],
        "mas": True,
    }
    assert falso.busquedas == ["alfa"]


@pytest.mark.parametrize("q", ["", "ab", "  ab  "])
def test_f114_r13_q_corto_no_llama(portal, q):
    falso = _ClienteFalso(resultado=_RESULTADO)
    respuesta = portal(falso).get("/api/sigrid/proveedores/todos", params={"q": q})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []
    assert "3" in cuerpo["error"]
    assert falso.busquedas == []


def test_f114_r13_sin_q_no_llama(portal):
    falso = _ClienteFalso(resultado=_RESULTADO)
    cuerpo = portal(falso).get("/api/sigrid/proveedores/todos").json()
    assert cuerpo["ok"] is False and falso.busquedas == []


def test_f114_r14_sin_cliente(portal):
    respuesta = portal(None).get("/api/sigrid/proveedores/todos", params={"q": "alfa"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []
    assert "SIGRID_API_" in cuerpo["error"]


def test_f114_r14_excepcion_del_cliente(portal):
    falso = _ClienteFalso(error=RuntimeError("sigrid-api respondio 500"))
    respuesta = portal(falso).get("/api/sigrid/proveedores/todos", params={"q": "alfa"})
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["ok"] is False and cuerpo["items"] == []
    assert "sigrid-api respondio 500" in cuerpo["error"]


def test_f114_r21_la_lista_de_la_obra_no_cambia(portal):
    falso = _ClienteFalso()
    cuerpo = portal(falso).get("/api/sigrid/proveedores", params={"obra": "0686"}).json()
    assert cuerpo == {"ok": True, "items": [{"cif": "B00000001", "nombre": "ALFA SL"}]}
    assert falso.obras == ["0686"]


def test_f114_t7_el_endpoint_va_fuera_del_esquema_openapi(portal):
    """Superviviente 1 de T7: uso interno del JS, como los demás lookups."""
    rutas = portal(None).get("/openapi.json").json()["paths"]
    assert "/api/sigrid/proveedores/todos" not in rutas
    assert "/api/sigrid/proveedores" not in rutas
