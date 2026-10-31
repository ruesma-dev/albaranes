# tests/test_f053_t21b_valorado.py
"""F-053 · T21b · no se aprueba un albarán sin valorar (R37, R38).

«Valorado» = ``ruesma_comun.valoracion.esta_valorado``: valoración de sv6 en
``ok`` o manual completa (cabecera ``manual``/``no_contract`` con alguna línea
con importe ≠ 0 y ninguna con importe nulo). Por los DOS caminos de R1
(«Aprobar» del listado y el PUT con ``approved=true``), con DESDE vacía o no
(el repositorio no mira DESDE), se rechaza sin cambiar nada. Solo cuenta el
PASO a aprobado: guardar uno ya aprobado no se rechaza (R2). Los botones
salen deshabilitados en la ficha y en el listado.

Repositorio real sobre SQLite y plantillas reales.
"""
from __future__ import annotations

import pytest
from f053_sv4_bbdd import CABECERA, DOC, construir, foto, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session

from domain.models.alta_sigrid_models import AVISO_SIN_VALORAR, AlbaranSinValorarError
from domain.models.review_models import MergeDocumentUpdatePayload


def _importes(motor, **por_linea):
    with Session(motor) as s:
        for lv_id, importe in por_linea.items():
            s.execute(text("UPDATE albaran_line_valuations SET importe_calculado = :i WHERE id = :id"),
                      {"i": importe, "id": int(lv_id[1:])})
        s.commit()


def _aprobar(repo):
    return repo.set_approved(document_id=DOC, approved=True, approved_by="ana")


def _guardar_y_aprobar(repo, monkeypatch):
    monkeypatch.setattr(repo, "get_document_detail", lambda document_id: "detalle")
    return repo.update_document_y_transicion(
        document_id=DOC,
        payload=MergeDocumentUpdatePayload(approved=True, approved_by="ana",
                                           numero_albaran="CAMBIADO", **CABECERA),
    )


NO_VALORADOS = {
    "partial": {}, "failed": {}, "pending": {},
    "manual_con_un_nulo": {"l12": None},
    "no_contract_todo_cero": {"l11": 0.0, "l12": 0.0, "l13": 0.0, "l14": 0.0},
}


@pytest.mark.parametrize("caso", sorted(NO_VALORADOS))
@pytest.mark.parametrize("camino", ["listado", "guardar"])
def test_f053_r37_no_valorado_no_se_aprueba_y_nada_cambia(monkeypatch, caso, camino):
    status = caso.split("_")[0] if caso.startswith(("manual", "no_contract")) else caso
    status = "no_contract" if caso.startswith("no_contract") else status
    motor = construir(status=status)
    _importes(motor, **NO_VALORADOS[caso])
    repo = repositorio(motor)
    antes = foto(motor)

    with pytest.raises(AlbaranSinValorarError) as error:
        _aprobar(repo) if camino == "listado" else _guardar_y_aprobar(repo, monkeypatch)

    assert error.value.aviso == AVISO_SIN_VALORAR == "No se puede aprobar un albarán sin valorar"
    assert foto(motor) == antes


@pytest.mark.parametrize("camino", ["listado", "guardar"])
def test_f053_r37_sin_valoracion_no_se_aprueba(monkeypatch, camino):
    motor = construir()
    with Session(motor) as s:
        s.execute(text("DELETE FROM albaran_line_valuations"))
        s.execute(text("DELETE FROM albaran_valuations"))
        s.commit()
    repo = repositorio(motor)
    with pytest.raises(AlbaranSinValorarError):
        _aprobar(repo) if camino == "listado" else _guardar_y_aprobar(repo, monkeypatch)


@pytest.mark.parametrize("status", ["ok", "manual", "no_contract"])
@pytest.mark.parametrize("camino", ["listado", "guardar"])
def test_f053_r37_valorado_se_aprueba(monkeypatch, status, camino):
    """``ok`` de sv6, o manual / sin contrato completa (todas con importe,
    alguna ≠ 0: la 13 vale 0 y no lo impide)."""
    motor = construir(status=status)
    repo = repositorio(motor)
    if camino == "listado":
        assert _aprobar(repo) is True
    else:
        assert _guardar_y_aprobar(repo, monkeypatch) == ("detalle", True)
    with Session(motor) as s:
        assert s.execute(text("SELECT approved FROM albaran_documents_merge WHERE id = :d"),
                         {"d": DOC}).scalar() in (1, True)


def test_f053_r37_guardar_uno_ya_aprobado_sin_valorar_lo_rechaza_f065_r4(monkeypatch):
    """Antes no se rechazaba (no PASABA a aprobado). Con F-065 R4 un aprobado
    es de solo lectura: el rechazo es por aprobado, no por sin valorar."""
    from domain.models.review_models import AlbaranAprobadoError

    motor = construir(status="partial", aprobado=True)
    with pytest.raises(AlbaranAprobadoError):
        _guardar_y_aprobar(repositorio(motor), monkeypatch)


def test_f053_r37_aprobar_uno_ya_aprobado_sin_valorar_no_se_rechaza():
    motor = construir(status="failed", aprobado=True)
    assert _aprobar(repositorio(motor)) is False


# ------------------------------------------------------------------ #
# «Valorado» en la ficha y en el listado (botones)
# ------------------------------------------------------------------ #
def _valoracion(status, importes):
    from domain.models.review_models import LineValuationPayload, ValuationPayload

    lineas = [LineValuationPayload(valuation_line_id=i, merge_line_id=i, importe_calculado=v)
              for i, v in enumerate(importes, start=1)]
    return ValuationPayload(valuation_id="v", status=status,
                            lines_by_merge_line_id={l.merge_line_id: l for l in lineas[:-1]},
                            synthetic_lines=lineas[-1:])


@pytest.mark.parametrize("status, importes, esperado", [
    ("ok", [None], True),
    ("manual", [10.0, 0.0], True),
    ("manual", [10.0, None], False),   # el nulo está entre las sintéticas
    ("no_contract", [None, 5.0], False),
    ("partial", [10.0], False),
])
def test_f053_r37_ficha_sabe_si_esta_valorado(documento_detalle, status, importes, esperado):
    documento = documento_detalle()
    documento.valuation = _valoracion(status, importes)
    assert documento.valorado is esperado


def test_f053_r37_ficha_sin_valoracion_no_esta_valorado(documento_detalle):
    assert documento_detalle().valorado is False


def _boton_aprobar(html):
    import re

    encontrado = re.search(r'<button[^>]*id="approve-btn"[^>]*>', html)
    assert encontrado
    return encontrado.group(0)


def test_f053_r37_ficha_boton_deshabilitado_sin_valorar(render_detalle, documento_detalle):
    boton = _boton_aprobar(render_detalle(documento_detalle()))
    assert "disabled" in boton
    assert "sin valorar" in boton


def test_f053_r37_ficha_boton_habilitado_valorado(render_detalle, documento_detalle):
    documento = documento_detalle()
    documento.valuation = _valoracion("ok", [10.0])
    assert "disabled" not in _boton_aprobar(render_detalle(documento))


def test_f053_r37_ficha_ya_aprobada_no_ofrece_aprobar(render_detalle, documento_detalle):
    """Antes el botón salía habilitado; con F-065 R5 un aprobado es de solo
    lectura: no hay «Guardar y aprobar», sino «Desaprobar para editar»."""
    documento = documento_detalle()
    documento.approved = True
    html = render_detalle(documento)
    assert 'id="approve-btn"' not in html
    assert "Desaprobar para editar" in html


def test_f053_r37_listado_marca_valorado(monkeypatch):
    """El repositorio dice en cada fila del listado si está valorado."""
    from domain.models.review_models import DocumentListFilters

    motor = construir(status="partial")
    repo = repositorio(motor)
    monkeypatch.setattr(repo, "_compute_and_persist_confianza", lambda **_: None)
    resultado = repo.list_documents(DocumentListFilters(approved="all"))
    valorados = {item.id: item.valorado for item in resultado.items}
    assert valorados[DOC] is False
    assert valorados["f053-doc-0000-0000-000000000002"] is True  # ok


def _listado_html(monkeypatch, *, aprobado, valorado, alta_estado=None):
    from fastapi.testclient import TestClient

    from config.settings import Settings
    from domain.models.review_models import DocumentListItem, PaginatedDocuments
    from interface_adapters.web import app as modulo_app

    item = DocumentListItem(
        id=DOC, source_filename="a.pdf", provider_origin="merge",
        created_at_utc="2026-10-08T08:00:00+00:00", approved=aprobado, valorado=valorado,
        alta_estado=alta_estado,
    )

    class _Servicio:
        def initialize(self):
            return True

        def list_documents(self, filters):
            return PaginatedDocuments(items=[item], total=1, page=1, page_size=25,
                                      total_pages=1, approved_count=0, pending_count=1,
                                      review_required_count=0)

    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: _Servicio())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes)).get("/documents?approved=all").text


def test_f053_r37_listado_boton_aprobar_deshabilitado_sin_valorar(monkeypatch):
    import re

    html = _listado_html(monkeypatch, aprobado=False, valorado=False)
    boton = re.search(r'<button[^>]*>Aprobar</button>', html).group(0)
    assert "disabled" in boton and "sin valorar" in boton


def test_f053_r37_listado_boton_aprobar_habilitado_valorado(monkeypatch):
    import re

    html = _listado_html(monkeypatch, aprobado=False, valorado=True)
    boton = re.search(r'<button[^>]*>Aprobar</button>', html).group(0)
    assert "disabled" not in boton
