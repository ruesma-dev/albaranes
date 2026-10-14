# tests/test_f053_r29_panel_usu.py
"""F-053 v8 · T48 (R29, R30) · el panel enseña el ``usu`` y «Reintentar adjunto».

- R29: el usuario de Sigrid con el que se pidió el alta es el ``usu`` de la
  petición guardada (``peticion_json``); se marca «(respaldo)» cuando no es la
  parte local del ``approved_by`` guardado en el alta (sin distinguir
  mayúsculas). Sin petición, nada.
- R30: el botón «Reintentar adjunto» sale solo cuando el servicio dice que
  procede (``alta_puede_reintentar_adjunto``, T47).

Plantillas reales; sin BBDD salvo la SQLite en memoria de ``f053_sv4_bbdd``.
"""
from __future__ import annotations

import re

import pytest
from f053_sv4_bbdd import DOC, construir, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_f053_t21_panel import DESDE, _alta, _con_alta, _panel, _RepoFicha

from domain.models.alta_sigrid_models import AltaSigridVista, ConfigAltaSigrid

BOTON = r'<form[^>]*action="/documents/[^"]+/alta-sigrid/reintentar-adjunto"'


# ------------------------------------------------------------------ #
# Vista: usu y respaldo
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("approved_by, usu, respaldo", [
    ("pgris@ruesma.es", "pgris", False),
    ("PGris@Ruesma.es", "pgris", False),     # sin distinguir mayúsculas
    (" ana@ruesma.es ", "ANA", False),
    ("nombre.apellido@ruesma.es", "pgris", True),
    ("reviewer", "pgris", True),             # DEFAULT_REVIEWER: no es correo
    (None, "pgris", True),
    ("", "pgris", True),
])
def test_f053_r29_usu_y_respaldo(approved_by, usu, respaldo):
    alta = AltaSigridVista(estado="simulado", approved_by=approved_by,
                           peticion={"usu": usu, "lineas": []})
    assert alta.usu == usu
    assert alta.usu_respaldo is respaldo


@pytest.mark.parametrize("peticion", [None, {}, {"usu": ""}, {"lineas": []}])
def test_f053_r29_sin_peticion_no_hay_usu(peticion):
    alta = AltaSigridVista(estado="no_admitido", approved_by="x@ruesma.es", peticion=peticion)
    assert alta.usu is None
    assert alta.usu_respaldo is False


# ------------------------------------------------------------------ #
# Panel
# ------------------------------------------------------------------ #
def _usu(panel):
    encontrado = re.search(r'class="alta-sigrid-usu"[^>]*>(.*?)</span>', panel, re.DOTALL)
    return None if encontrado is None else re.sub(r"\s+", " ", encontrado.group(1)).strip()


def test_f053_r29_panel_usu_de_quien_aprobo(render_detalle, documento_detalle):
    alta = _alta(approved_by="pgris@ruesma.es", peticion={"usu": "pgris", "lineas": []})
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert _usu(panel) == "Usuario de Sigrid: <code>pgris</code>"
    assert "respaldo" not in panel


def test_f053_r29_panel_usu_de_respaldo(render_detalle, documento_detalle):
    alta = _alta(approved_by="nombre.apellido@ruesma.es", peticion={"usu": "pgris",
                                                                    "lineas": []})
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert _usu(panel) == "Usuario de Sigrid: <code>pgris</code> (respaldo)"


def test_f053_r29_panel_sin_peticion_no_dice_usuario(render_detalle, documento_detalle):
    alta = _alta("no_admitido", peticion=None, approved_by="ana@ruesma.es")
    panel = _panel(render_detalle(_con_alta(documento_detalle(), alta)))
    assert _usu(panel) is None
    assert "Usuario de Sigrid" not in panel


@pytest.mark.parametrize("puede", [True, False])
def test_f053_r30_panel_boton_reintentar_adjunto(render_detalle, documento_detalle, puede):
    documento = _con_alta(documento_detalle(), _alta("registrado", "real", adjunto_estado="error"))
    documento.alta_puede_reintentar_adjunto = puede
    panel = _panel(render_detalle(documento))
    assert (re.search(BOTON, panel) is not None) is puede
    assert ("Reintentar adjunto" in panel) is puede


def test_f053_r30_panel_servicio_marca_reintentar_adjunto(documento_detalle):
    from application.services.review_service import ReviewService

    documento = documento_detalle()
    documento.approved = True
    alta = _alta("registrado", "real", adjunto_estado="error")
    servicio = ReviewService(_RepoFicha(documento, alta), "r", None,
                             ConfigAltaSigrid(desde=DESDE))
    ficha = servicio.get_document(documento.id)
    assert ficha.alta_puede_reintentar_adjunto is True
    assert ficha.alta_puede_solicitar is False


# ------------------------------------------------------------------ #
# Repositorio: el approved_by del alta llega a la vista
# ------------------------------------------------------------------ #
def test_f053_r29_repositorio_lee_el_approved_by_del_alta():
    motor = construir()
    with Session(motor) as s:
        s.execute(text(
            "INSERT INTO albaran_altas_sigrid (document_id, estado, intentos, creado_at_utc, "
            "approved_by, peticion_json) VALUES (:d, 'simulado', 1, 't', :a, :p)"),
            {"d": DOC, "a": "ana@ruesma.es", "p": '{"usu": "ana", "lineas": []}'})
        s.commit()
    alta = repositorio(motor).leer_alta_sigrid(DOC)
    assert alta.approved_by == "ana@ruesma.es"
    assert alta.usu == "ana" and alta.usu_respaldo is False
