# tests/test_f075_disparo.py
"""F-075 R3, R4 · sv3 dispara la valoración sin contrato si el albarán trae importes.

- R3: sin contrato seleccionado (código nulo) y con algún importe leído
  (``precio_neto``) ⇒ ``trigger_async(codigo_contrato=None)``.
- R4: sin importes ⇒ SKIP, como hoy. M1 (humano, 2026-10-18): con contrato
  seleccionado SIN líneas ⇒ SKIP, como hoy (sv5 tomaría ese contrato del
  merge y no daría ``no_contract``).
- Best-effort: una excepción al leer los importes se registra y no publica.

Sin red. El SQL de ``importes_leidos`` se ejecuta tal cual sobre SQLite.
"""
from __future__ import annotations

import logging

import pytest
from application.pipelines.persist_albaran_pipeline import PersistAlbaranPipeline
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DOC = "dfdc8aab-08e1-49f0-978d-bb906515e748"


class _Trigger:
    def __init__(self, acepta=True):
        self.llamadas = []
        self.acepta = acepta

    def trigger_async(self, *, document_id, codigo_contrato, force=False):
        self.llamadas.append((document_id, codigo_contrato, force))
        return self.acepta


class _Repo:
    def __init__(self, *, con_lineas=False, codigo=None, importes=(), rompe=False):
        self.con_lineas = con_lineas
        self.codigo = codigo
        self.importes = list(importes)
        self.rompe = rompe
        self.pedidos = []

    def has_selected_contrato_with_lines(self, *, document_id):
        return self.con_lineas, self.codigo

    def importes_leidos(self, *, document_id):
        self.pedidos.append(document_id)
        if self.rompe:
            raise RuntimeError("BBDD caída")
        return self.importes


def _pipeline(repo, trigger):
    return PersistAlbaranPipeline(
        repository=repo, document_storage=None, normalizer=None, valuation_trigger=trigger,
    )


def test_f075_r3_sin_contrato_con_importes_publica_con_contrato_nulo():
    repo, trigger = _Repo(importes=[10.0, None]), _Trigger()
    _pipeline(repo, trigger)._trigger_valuation_safely(merge_document_id=DOC, force=True)
    assert trigger.llamadas == [(DOC, None, True)]
    assert repo.pedidos == [DOC]


def test_f075_r3_con_contrato_con_lineas_como_hoy_sin_leer_importes():
    repo, trigger = _Repo(con_lineas=True, codigo="CTSU26/0313", importes=[10.0]), _Trigger()
    _pipeline(repo, trigger)._trigger_valuation_safely(merge_document_id=DOC)
    assert trigger.llamadas == [(DOC, "CTSU26/0313", False)]
    assert repo.pedidos == []


def test_f075_r4_sin_importes_no_publica(caplog):
    repo, trigger = _Repo(importes=[None, None]), _Trigger()
    with caplog.at_level(logging.INFO):
        _pipeline(repo, trigger)._trigger_valuation_safely(merge_document_id=DOC)
    assert trigger.llamadas == []
    assert any("SKIP" in r.getMessage() and DOC in r.getMessage() for r in caplog.records)


def test_f075_r4_sin_lineas_no_publica():
    repo, trigger = _Repo(importes=[]), _Trigger()
    _pipeline(repo, trigger)._trigger_valuation_safely(merge_document_id=DOC)
    assert trigger.llamadas == []


def test_f075_r4_m1_contrato_seleccionado_sin_lineas_no_publica_ni_lee_importes():
    repo, trigger = _Repo(con_lineas=False, codigo="CTSU26/0001", importes=[10.0]), _Trigger()
    _pipeline(repo, trigger)._trigger_valuation_safely(merge_document_id=DOC)
    assert trigger.llamadas == []
    assert repo.pedidos == []


def test_f075_r3_excepcion_al_leer_importes_no_publica(caplog):
    repo, trigger = _Repo(rompe=True), _Trigger()
    with caplog.at_level(logging.ERROR):
        _pipeline(repo, trigger)._trigger_valuation_safely(merge_document_id=DOC)
    assert trigger.llamadas == []
    assert any(DOC in r.getMessage() for r in caplog.records if r.levelno >= logging.ERROR)


def test_f075_r3_excepcion_al_publicar_no_rompe(caplog):
    class _TriggerRoto(_Trigger):
        def trigger_async(self, **kw):
            raise RuntimeError("cola caída")

    _pipeline(_Repo(importes=[1.0]), _TriggerRoto())._trigger_valuation_safely(merge_document_id=DOC)


# ------------------------------------------------------------------ #
# El SQL real de ``importes_leidos`` (SQLite)
# ------------------------------------------------------------------ #
class _Fabrica:
    generation = 1

    def __init__(self, engine):
        self.engine = engine

    def ensure_database_and_engine(self):
        return None

    def create_session(self):
        return Session(self.engine)


@pytest.fixture()
def repo_sqlite(tmp_path):
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )

    engine = create_engine(f"sqlite:///{tmp_path / 'f075.db'}")
    with engine.begin() as con:
        con.execute(text(
            "CREATE TABLE albaran_lines_merge (id INTEGER PRIMARY KEY, document_id TEXT, "
            "line_index INTEGER, precio_neto REAL)"
        ))
        con.execute(text(
            "INSERT INTO albaran_lines_merge (document_id, line_index, precio_neto) VALUES "
            "(:d, 2, NULL), (:d, 0, 10.5), (:d, 1, -3.0), ('otro', 0, 99.0)"
        ), {"d": DOC})
    repo = SqlAlchemyAlbaranRepository(_Fabrica(engine))
    repo._initialized_generation = 1
    return repo


def test_f075_r3_importes_leidos_en_orden_y_solo_del_documento(repo_sqlite):
    assert repo_sqlite.importes_leidos(document_id=DOC) == [10.5, -3.0, None]
    assert repo_sqlite.importes_leidos(document_id="no-existe") == []


def test_f075_r11_con_contrato_y_lineas_publica_su_codigo_como_hoy():
    """R11: con contrato seleccionado con líneas, el disparo no cambia (ni lee los importes)."""
    for importes in ([10.0], [None], []):
        repo, trigger = _Repo(con_lineas=True, codigo="CTSU26/0313", importes=importes), _Trigger()
        _pipeline(repo, trigger)._trigger_valuation_safely(merge_document_id=DOC, force=True)
        assert trigger.llamadas == [(DOC, "CTSU26/0313", True)]
        assert repo.pedidos == []
