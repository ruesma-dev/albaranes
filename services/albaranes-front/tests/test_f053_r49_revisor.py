# tests/test_f053_r49_revisor.py
"""F-053 v8 · T46 · R49: quién aprobó lo dice Easy Auth, por los dos caminos.

``approved_by`` = la cabecera ``X-MS-CLIENT-PRINCIPAL-NAME`` (la inyecta la
plataforma y el navegador no la puede poner); solo si no llega (local), el
formulario («Aprobar» del listado) o el cuerpo (PUT de la ficha) y, sin ellos,
``DEFAULT_REVIEWER``. Lo que se publica en ``q-feedback`` lleva lo mismo (y
sv9 sacará de ahí el ``usu`` de Sigrid, R47).

``build_app`` real con un ``ReviewService`` real sobre los dobles de T18
(repositorio y cliente de colas): sin BBDD ni colas.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from test_f053_t18_publicar import ACTIVA, _Orquestador, _Repo

from application.services.review_service import ReviewService
from config.settings import Settings
from interface_adapters.web import app as modulo_app

DOC = "f053-t18-doc"
CABECERA = "X-MS-CLIENT-PRINCIPAL-NAME"
DEFECTO = "revisor-local"


class _RepoR49(_Repo):
    def initialize(self):
        return True


class _Publicador:
    def publicar(self, nombre_cola, mensaje):
        return True


def _cliente(monkeypatch):
    repo, orq = _RepoR49(paso=True), _Orquestador()
    servicio = ReviewService(repo, DEFECTO, orq, ACTIVA)
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: servicio)
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: _Publicador())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x",
                                       default_reviewer=DEFECTO)
    cliente = TestClient(modulo_app.build_app(ajustes), follow_redirects=False)
    return cliente, repo, orq


def _aprobar_listado(cliente, *, cabecera=None, formulario=None):
    datos = {} if formulario is None else {"approved_by": formulario}
    cabeceras = {} if cabecera is None else {CABECERA: cabecera}
    return cliente.post(f"/documents/{DOC}/approve", data=datos, headers=cabeceras)


def _aprobar_ficha(cliente, *, cabecera=None, cuerpo=None):
    payload = {"approved": True}
    if cuerpo is not None:
        payload["approved_by"] = cuerpo
    cabeceras = {} if cabecera is None else {CABECERA: cabecera}
    return cliente.put(f"/api/documents/{DOC}", json=payload, headers=cabeceras)


# ------------------------------------------------------------------ #
# Listado (POST /documents/{id}/approve)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("cabecera, formulario, esperado", [
    ("ana@ruesma.es", "falso@ruesma.es", "ana@ruesma.es"),   # manda la cabecera
    ("  ana@ruesma.es ", "", "ana@ruesma.es"),
    (None, "pepe@ruesma.es", "pepe@ruesma.es"),               # local: el formulario
    (None, "  pepe  ", "pepe"),
    ("   ", "pepe", "pepe"),                                  # cabecera en blanco = no llega
    (None, "", DEFECTO),                                      # local sin nada
    (None, None, DEFECTO),
    (None, "   ", DEFECTO),                                   # T50 (mutante 38): solo espacios
])
def test_f053_r49_listado(monkeypatch, cabecera, formulario, esperado):
    cliente, repo, orq = _cliente(monkeypatch)
    respuesta = _aprobar_listado(cliente, cabecera=cabecera, formulario=formulario)
    assert respuesta.status_code == 303
    assert repo.aprobaciones == [(DOC, True, esperado)]
    assert [a["approved_by"] for a in orq.aprobados] == [esperado]


# ------------------------------------------------------------------ #
# Ficha (PUT /api/documents/{id})
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("cabecera, cuerpo, esperado", [
    ("ana@ruesma.es", "falso@ruesma.es", "ana@ruesma.es"),   # manda la cabecera
    ("ana@ruesma.es", None, "ana@ruesma.es"),                 # la ficha no manda nada
    (" ana@ruesma.es ", "", "ana@ruesma.es"),
    (None, "pepe@ruesma.es", "pepe@ruesma.es"),               # local: el cuerpo
    ("", "pepe@ruesma.es", "pepe@ruesma.es"),
    (None, None, DEFECTO),                                    # local sin nada
    (None, "", DEFECTO),
    (None, "   ", DEFECTO),                                   # T50 (mutante 38): solo espacios
])
def test_f053_r49_ficha(monkeypatch, cabecera, cuerpo, esperado):
    cliente, repo, orq = _cliente(monkeypatch)
    respuesta = _aprobar_ficha(cliente, cabecera=cabecera, cuerpo=cuerpo)
    assert respuesta.status_code == 200, respuesta.text
    assert [p.approved_by for p in repo.guardados] == [esperado]
    assert [a["approved_by"] for a in orq.aprobados] == [esperado]


def test_f053_r49_ficha_sin_aprobar_no_publica_ni_cambia_nada_mas(monkeypatch):
    """Guardar sin aprobar: la cabecera no aprueba nada (el repositorio solo
    escribe ``approved_by`` al aprobar) y no se publica."""
    cliente, repo, orq = _cliente(monkeypatch)
    respuesta = cliente.put(f"/api/documents/{DOC}", json={"approved": False},
                            headers={CABECERA: "ana@ruesma.es"})
    assert respuesta.status_code == 200
    assert [p.approved for p in repo.guardados] == [False]
    assert orq.aprobados == []
