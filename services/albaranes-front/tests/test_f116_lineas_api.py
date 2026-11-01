# tests/test_f116_lineas_api.py
"""F-116 · C · R18: el PATCH de fila SIN ``?bloquear=1`` (el del autoguardado)
aplica la fila con el recálculo de F-106, registra su edición y su deshacer
«Editar línea», y NO bloquea.

Ya era así antes de F-116 (design §1.1): estos tests lo fijan. Repositorio y
servicio reales sobre SQLite (el albarán de CECOIS de ``test_f106_fila``) y
``build_app`` real. Sin red ni BBDD.

R19 (sv6 conserva al revalorar una fila con edición y sin bloquear) lo fija el
test existente ``services/albaran-valoracion-persist/tests/test_f106_reaplicar.py::
test_f106_r25_r32c_cantidad_editada_sobrevive_con_el_precio_nuevo``: su edición
es solo ``{"cantidad"}``, sin ``bloqueada``, sobre una fila sin bloquear.
"""
from __future__ import annotations

import pytest
from f065_bbdd import DOC, fila, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_f106_fila import FILA, cecois

from ruesma_comun.edicion_manual import leer_edicion


def _edicion(motor):
    with Session(motor) as s:
        return leer_edicion(s.execute(text(
            "SELECT edicion_manual_json FROM albaran_line_valuations WHERE id = :v"),
            {"v": FILA}).scalar())


def _undo(motor) -> list[str]:
    with Session(motor) as s:
        return list(s.execute(text("SELECT description FROM undo_log ORDER BY id")).scalars())


def _servicio(motor):
    from application.services.review_service import ReviewService

    return ReviewService(repositorio(motor), "ana")


def test_f116_r18_sin_bloquear_aplica_recalcula_y_no_bloquea():
    motor = cecois()

    assert _servicio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, campos={"cantidad": 48.0}) is True

    f = fila(motor, FILA)
    assert f["bloqueada"] in (0, False)
    assert f["cantidad_convertida"] == 48.0
    # F-106 R5: cantidad ⇒ importe (48 × 11,20 − 7 %).
    assert f["importe_calculado"] == pytest.approx(499.97)


def test_f116_r18_sin_bloquear_registra_la_edicion_sin_bloqueada():
    motor = cecois()

    _servicio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, campos={"cantidad": 48.0})

    edicion = _edicion(motor)
    assert list(edicion.campos) == ["cantidad"]
    assert "bloqueada" not in edicion.campos


def test_f116_r18_sin_bloquear_deja_su_deshacer_editar_linea():
    from test_f106_fila import _deshacer

    motor = cecois()
    antes = fila(motor, FILA)

    _servicio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, campos={"cantidad": 48.0})

    (descripcion,) = _undo(motor)
    assert descripcion.startswith("Editar línea · ")
    _deshacer(motor)
    assert fila(motor, FILA) == antes


def test_f116_r18_con_bloquear_si_bloquea_contraste():
    """El otro comportamiento, independiente: el del botón «Guardar»."""
    motor = cecois()

    _servicio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, campos={"cantidad": 48.0}, bloquear=True)

    assert fila(motor, FILA)["bloqueada"] in (1, True)
    assert "bloqueada" in _edicion(motor).campos
    assert _undo(motor)[0].startswith("Guardar línea · ")


# --- la ruta, de punta a punta ---------------------------------------- #
class _PublicadorFalso:
    def publicar(self, nombre_cola, mensaje):
        return True


@pytest.fixture
def portal(monkeypatch):
    """``build_app`` real con servicio y repositorio reales sobre un SQLite de
    UNA conexión (la ruta corre en otro hilo)."""
    import f065_bbdd
    from config.settings import Settings
    from fastapi.testclient import TestClient
    from interface_adapters.web import app as modulo_app
    from sqlalchemy import create_engine
    from sqlalchemy.pool import StaticPool

    monkeypatch.setattr(f065_bbdd, "create_engine", lambda url: create_engine(
        url, poolclass=StaticPool, connect_args={"check_same_thread": False}))
    motor = cecois()
    servicio = _servicio(motor)
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: _PublicadorFalso())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes), follow_redirects=False), motor


URL = f"/api/documents/{DOC}/lines/{FILA}/conciliacion/campos"


def test_f116_r18_ruta_sin_bloquear_no_bloquea(portal):
    cliente, motor = portal

    r = cliente.patch(URL, json={"cantidad": "48"})

    assert r.status_code == 200, r.text
    f = fila(motor, FILA)
    assert f["bloqueada"] in (0, False) and f["cantidad_convertida"] == 48.0
    assert "bloqueada" not in _edicion(motor).campos
    assert _undo(motor)[0].startswith("Editar línea · ")


def test_f116_r18_ruta_con_bloquear_bloquea(portal):
    cliente, motor = portal

    r = cliente.patch(URL + "?bloquear=1", json={})

    assert r.status_code == 200, r.text
    assert fila(motor, FILA)["bloqueada"] in (1, True)
