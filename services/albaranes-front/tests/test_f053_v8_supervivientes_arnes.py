# tests/test_f053_v8_supervivientes_arnes.py
"""F-053 v8 · T50 (pasada 2) · los 3 supervivientes de la campaña de la
herramienta (``progress/mutacion_F-053_v8_arnes.md``), cerrados con tests de
conducta. Sin BBDD ni colas: ``build_app`` real con dobles.

- #1 ``alta_puede_reintentar_adjunto`` vale ``False`` por defecto: con DESDE
  vacía, o en las vistas de proveedor, la ficha NO ofrece «Reintentar adjunto».
- #2 sin cabecera, lo que se publica al «Solicitar alta» lleva
  ``DEFAULT_REVIEWER`` recortado (el servicio no lo rellena en ese camino).
- #3 las rutas de formulario del alta no salen en el OpenAPI, como el resto de
  rutas de formulario de la ficha.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from test_f053_t20_rutas import DOC, _Orq, _RepoAlta
from test_f053_t21_panel import DESDE, _alta, _RepoFicha

from application.services.review_service import ReviewService
from config.settings import Settings
from domain.models.alta_sigrid_models import ConfigAltaSigrid
from interface_adapters.web import app as modulo_app


# ------------------------------------------------------------------ #
# #1 · el defecto del modelo es «no se ofrece»
# ------------------------------------------------------------------ #
def test_f053_r30_sin_desde_la_ficha_no_ofrece_reintentar_adjunto(documento_detalle):
    documento = documento_detalle()
    documento.approved = True
    alta = _alta("registrado", "real", adjunto_estado="error")
    servicio = ReviewService(_RepoFicha(documento, alta), "r", None, ConfigAltaSigrid())
    assert servicio.get_document(documento.id).alta_puede_reintentar_adjunto is False


def test_f053_r30_vista_de_proveedor_no_ofrece_reintentar_adjunto(documento_detalle):
    documento = documento_detalle()
    documento.approved = True
    documento.view_mode = "openai"
    alta = _alta("registrado", "real", adjunto_estado="error")
    servicio = ReviewService(_RepoFicha(documento, alta), "r", None,
                             ConfigAltaSigrid(desde=DESDE))
    ficha = servicio.get_document(documento.id, view_mode="openai")
    assert ficha.alta_puede_reintentar_adjunto is False


# ------------------------------------------------------------------ #
# #2 · DEFAULT_REVIEWER recortado también en «Solicitar alta»
# ------------------------------------------------------------------ #
class _RepoAltaApp(_RepoAlta):
    def initialize(self):
        return True


class _Publicador:
    def publicar(self, nombre_cola, mensaje):
        return True


def _app(monkeypatch, servicio, defecto):
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: _Publicador())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x",
                                       default_reviewer=defecto)
    return modulo_app.build_app(ajustes)


@pytest.mark.parametrize("defecto, cabecera, esperado", [
    (" revisor-local ", None, "revisor-local"),
    ("revisor-local", None, "revisor-local"),
    (" revisor-local ", "ana@ruesma.es", "ana@ruesma.es"),
    ("   ", None, None),
    (None, None, None),
])
def test_f053_r30_solicitar_alta_publica_el_revisor_recortado(monkeypatch, defecto, cabecera,
                                                              esperado):
    orq = _Orq()
    servicio = ReviewService(_RepoAltaApp(None), defecto, orq,
                             ConfigAltaSigrid(desde=datetime(2026, 10, 1, tzinfo=UTC)))
    cliente = TestClient(_app(monkeypatch, servicio, defecto), follow_redirects=False)
    cabeceras = {} if cabecera is None else {"X-MS-CLIENT-PRINCIPAL-NAME": cabecera}
    respuesta = cliente.post(f"/documents/{DOC}/alta-sigrid/solicitar", headers=cabeceras)
    assert respuesta.status_code == 303
    assert orq.pedidas == [{"document_id": DOC, "accion": "alta", "solicitado_por": esperado}]


# ------------------------------------------------------------------ #
# #3 · las rutas de formulario del alta no se publican en el OpenAPI
# ------------------------------------------------------------------ #
def test_f053_r30_rutas_de_formulario_del_alta_fuera_del_openapi(monkeypatch):
    app = _app(monkeypatch, ReviewService(_RepoAltaApp(None), "r", _Orq(), ConfigAltaSigrid()),
               "r")
    rutas = set(TestClient(app).get("/openapi.json").json()["paths"])
    for accion in ("solicitar", "verificar-anulacion", "reintentar-adjunto"):
        assert f"/documents/{{document_id}}/alta-sigrid/{accion}" not in rutas
    assert "/api/documents/{document_id}" in rutas   # el OpenAPI sí lleva la API
