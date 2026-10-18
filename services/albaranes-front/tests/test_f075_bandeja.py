# tests/test_f075_bandeja.py
"""F-075 R19–R22, R25 · la bandeja enseña una sola columna «Importe».

«Manda el albarán y pisa» (humano, 2026-10-15; v2-P7 una columna): el importe
del albarán (suma de ``precio_neto``, sin IVA) si trae importes; si no, el
valorado; «—» si ninguno. Marca ≠ si el valorado se aparta del albarán.
Orden, filtro mín/máx y la tarjeta «Importe pendiente» usan esa misma cifra.

Repositorio real sobre SQLite (``tests/f075_bbdd.py``). Sin red.
"""
from __future__ import annotations

import logging

import pytest
from domain.models.review_models import DocumentListFilters, DocumentListItem
from tests.f075_bbdd import (
    ALB,
    APR,
    BORR,
    CON,
    DIS,
    NADA,
    PAR,
    VACIA,
    construir,
    repositorio,
)


@pytest.fixture()
def repo():
    return repositorio(construir())


def _items(repo, **filtros):
    filtros.setdefault("approved", "all")
    filtros.setdefault("page_size", 100)
    return {i.id: i for i in repo.list_documents(DocumentListFilters(**filtros)).items}


# ------------------------------------------------------------------ #
# R19 · qué cifra y qué rótulo
# ------------------------------------------------------------------ #
def test_f075_r19_importe_mostrado_y_origen(repo):
    items = _items(repo)
    vistos = {d: (items[d].importe_mostrado, items[d].importe_origen) for d in items}
    assert vistos == {
        ALB: (150.0, "albaran"),
        CON: (60.0, "contrato"),
        DIS: (100.0, "albaran"),
        PAR: (40.0, "albaran"),
        NADA: (None, None),
        VACIA: (None, None),  # una cabecera no_contract sin filas no es un valorado
        APR: (1000.0, "albaran"),
    }
    assert BORR not in items


def test_f075_r19_rotulo_del_origen(repo):
    items = _items(repo)
    assert items[ALB].importe_rotulo == "albarán · sin IVA"
    assert items[CON].importe_rotulo == "contrato"
    assert items[NADA].importe_rotulo is None


def test_f075_r19_parcial_dice_cuantas_faltan(repo):
    items = _items(repo)
    assert items[PAR].importe_parcial_texto == "1 de 2 sin importe"
    assert items[ALB].importe_parcial_texto is None
    assert items[CON].importe_parcial_texto is None  # sin importes no es parcial


# ------------------------------------------------------------------ #
# R20 · marca ≠
# ------------------------------------------------------------------ #
def test_f075_r20_marca_distinto_si_el_valorado_se_aparta(repo):
    items = _items(repo)
    assert items[DIS].importe_distinto is True
    assert items[DIS].importe_distinto_texto == "Albarán 100,00 € · Valorado 70,00 €"
    for d in (ALB, CON, PAR, NADA, VACIA, APR):
        assert items[d].importe_distinto is False
        assert items[d].importe_distinto_texto is None


def test_f075_r20_modelo_puro_umbral_de_un_centimo():
    base = dict(id="x", source_filename="a.pdf", provider_origin="merge", created_at_utc="t")
    casi = DocumentListItem(**base, importe_albaran=100.004, lineas_albaran=1, lineas_con_importe=1,
                            total_valorado=100.0)
    assert casi.importe_distinto is False
    lejos = DocumentListItem(**base, importe_albaran=100.01, lineas_albaran=1, lineas_con_importe=1,
                             total_valorado=100.0)
    assert lejos.importe_distinto is True


# ------------------------------------------------------------------ #
# R21 · orden y filtro sobre la misma cifra
# ------------------------------------------------------------------ #
def test_f075_r21_ordenar_por_importe(repo):
    asc = [i.id for i in repo.list_documents(DocumentListFilters(
        approved="all", sort_by="importe", sort_dir="asc", page_size=100)).items]
    assert asc[:5] == [PAR, CON, DIS, ALB, APR]
    assert set(asc[5:]) == {NADA, VACIA}  # sin importe, al final
    desc = [i.id for i in repo.list_documents(DocumentListFilters(
        approved="all", sort_by="importe", sort_dir="desc", page_size=100)).items]
    assert desc[:5] == [APR, ALB, DIS, CON, PAR]
    assert set(desc[5:]) == {NADA, VACIA}


def test_f075_r21_sort_by_importe_es_valido():
    assert DocumentListFilters(sort_by="importe").sort_by == "importe"


def test_f075_r21_filtro_min_max_sobre_el_importe_mostrado(repo):
    # ALB no tiene valoración: antes quedaba fuera de cualquier filtro de importe.
    assert set(_items(repo, min_importe=100.0, max_importe=150.0)) == {ALB, DIS}
    assert set(_items(repo, min_importe=500.0)) == {APR}
    assert set(_items(repo, max_importe=60.0)) == {PAR, CON}


# ------------------------------------------------------------------ #
# R22 · tarjeta «Importe pendiente»
# ------------------------------------------------------------------ #
def test_f075_r22_importe_pendiente_suma_la_misma_cifra(repo):
    resultado = repo.list_documents(DocumentListFilters(approved="all"))
    # activos no aprobados: 150 + 60 + 100 + 40 (APR aprobado, BORR en la papelera)
    assert resultado.importe_pendiente_aprobar == 350.0


# ------------------------------------------------------------------ #
# R25 · si la consulta del importe falla, la bandeja se pinta igual
# ------------------------------------------------------------------ #
def test_f075_r25_fallo_en_la_consulta_del_importe(repo, monkeypatch, caplog):
    import infrastructure.database.review_repository as modulo

    monkeypatch.setattr(modulo, "_SQL_IMPORTES_LEIDOS_DOCS", "SELECT nada FROM no_existe WHERE x IN :ids")
    with caplog.at_level(logging.WARNING):
        items = _items(repo)
    assert len(items) == 7
    # Sin saber si el albarán trae importes no se pinta ninguna cifra: «—»
    # (pintar el valorado como «contrato» contradiría «manda el albarán»).
    assert all(i.importe_mostrado is None and i.importe_origen is None for i in items.values())
    assert all(i.importe_distinto is False for i in items.values())
    assert any("importe" in r.getMessage() for r in caplog.records if r.levelno >= logging.WARNING)


# ------------------------------------------------------------------ #
# R19–R21 · lo que pinta la plantilla
# ------------------------------------------------------------------ #
def _listado_html(monkeypatch, items, *, query="approved=all"):
    from config.settings import Settings
    from domain.models.review_models import PaginatedDocuments
    from fastapi.testclient import TestClient
    from interface_adapters.web import app as modulo_app

    class _Servicio:
        def initialize(self):
            return True

        def list_documents(self, filters):
            return PaginatedDocuments(items=items, total=len(items), page=1, page_size=25, total_pages=1,
                                      approved_count=0, pending_count=len(items), review_required_count=0,
                                      importe_pendiente_aprobar=350.0)

    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository", lambda *_: object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())
    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: _Servicio())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x")
    return TestClient(modulo_app.build_app(ajustes)).get(f"/documents?{query}").text


def _item(doc, **campos):
    return DocumentListItem(id=doc, source_filename="a.pdf", provider_origin="merge",
                            created_at_utc="2026-10-15T08:00:00+00:00", **campos)


def _celda(html, doc):
    import re

    fila = html[html.index(f'data-id="{doc}"') if f'data-id="{doc}"' in html else html.index(doc):]
    return re.search(r'<td class="num-cell" data-col="importe">(.*?)</td>', fila, re.DOTALL).group(1)


def test_f075_r19_r20_plantilla_pinta_cifra_rotulo_parcial_y_marca(monkeypatch):
    html = _listado_html(monkeypatch, [
        _item("d-dis", importe_albaran=100.0, lineas_albaran=2, lineas_con_importe=1, total_valorado=70.0),
        _item("d-con", total_valorado=60.0),
        _item("d-nada"),
    ])
    dis = _celda(html, "d-dis")
    assert "100,00" in dis and "albarán · sin IVA" in dis and "1 de 2 sin importe" in dis
    assert 'class="importe-distinto" title="Albarán 100,00 € · Valorado 70,00 €">≠<' in dis
    con = _celda(html, "d-con")
    assert "60,00" in con and "contrato" in con and "≠" not in con
    assert _celda(html, "d-nada").strip() == "—"


def test_f075_r21_cabecera_importe_ordenable(monkeypatch):
    html = _listado_html(monkeypatch, [_item("d-1")], query="approved=all&sort_by=importe&sort_dir=asc")
    assert "sort_by=importe" in html
    assert ">Importe</a><span class=\"sort-arrow\">▲</span>" in html
    assert "Importe valorado" not in html


# ------------------------------------------------------------------ #
# T13 · R20 la marca ≠ también cuando el pie no cuadra (motivo de sv3)
# ------------------------------------------------------------------ #
def test_f075_pie_r20_marca_con_el_motivo_de_sv3_sin_recalcular():
    item = _item("d", importe_albaran=100.0, lineas_albaran=1, lineas_con_importe=1,
                 review_reasons_json='["pie_no_cuadra:100.00!=110.00"]')
    assert item.pie_no_cuadra == 110.0
    assert item.importe_distinto is True
    assert item.importe_distinto_texto == "Albarán 100,00 € · Pie 110,00 €"


def test_f075_pie_r20_texto_completo_con_valorado_y_pie():
    item = _item("d", importe_albaran=100.0, lineas_albaran=1, lineas_con_importe=1, total_valorado=70.0,
                 review_reasons_json='["otro", "pie_no_cuadra:100.00!=110.00"]')
    assert item.importe_distinto_texto == "Albarán 100,00 € · Valorado 70,00 € · Pie 110,00 €"


def test_f075_pie_r20_motivo_ilegible_o_ausente_no_marca():
    for motivos in (None, "[]", '["pie_no_cuadra:basura"]', "no-json"):
        item = _item("d", importe_albaran=100.0, lineas_albaran=1, lineas_con_importe=1,
                     review_reasons_json=motivos)
        assert item.pie_no_cuadra is None and item.importe_distinto is False


def test_f075_pie_r20_la_bandeja_lee_el_motivo_del_merge():
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    motor = construir()
    with Session(motor) as s:
        s.execute(text("UPDATE albaran_documents_merge SET review_reasons_json = "
                       "'[\"pie_no_cuadra:150.00!=160.00\"]' WHERE id = :d"), {"d": ALB})
        s.commit()
    items = _items(repositorio(motor))
    assert items[ALB].importe_distinto is True
    assert items[ALB].importe_distinto_texto == "Albarán 150,00 € · Pie 160,00 €"


# ------------------------------------------------------------------ #
# T16 · supervivientes de la campaña (progress/mutacion_F-075.md)
# ------------------------------------------------------------------ #
def test_f075_t16_sin_lineas_leidas_cero_lineas():
    assert _item("d").lineas_albaran == 0 and _item("d").lineas_con_importe == 0
    motor = construir({"f075-vacio": ("0686", "B4", [], None, False, True)})
    (item,) = repositorio(motor).list_documents(DocumentListFilters(approved="all")).items
    assert (item.lineas_albaran, item.lineas_con_importe, item.importe_albaran) == (0, 0, None)


def test_f075_t16_los_fallos_del_importe_dejan_la_traza_del_error(repo, monkeypatch, caplog):
    import infrastructure.database.review_repository as modulo

    monkeypatch.setattr(modulo, "_SQL_IMPORTES_LEIDOS_DOCS", "SELECT nada FROM no_existe WHERE x IN :ids")
    monkeypatch.setattr(modulo, "sql_importe_mostrado", lambda alias: "columna_que_no_existe")
    with caplog.at_level(logging.WARNING):
        resultado = repo.list_documents(DocumentListFilters(approved="all"))
    assert resultado.importe_pendiente_aprobar == 0.0
    avisos = [r for r in caplog.records if r.levelno == logging.WARNING and "[bandeja]" in r.getMessage()]
    assert len(avisos) == 2
    assert all(r.exc_info for r in avisos)  # con exc_info=False, el registro guarda False
