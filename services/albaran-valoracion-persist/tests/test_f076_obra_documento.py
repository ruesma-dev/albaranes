# tests/test_f076_obra_documento.py
"""F-076 T7 · sv6 lee la obra del merge (solo lectura) y el puerto de la lista.

``SqlAlchemyValuationRepository.obra_del_documento`` hace UN ``SELECT`` sobre
``albaran_documents_merge`` (tabla de sv3, design §4): ``obra_codigo`` por
``id``; sin fila ⇒ ``None``. SQLite en memoria con la tabla reducida a lo que
se lee: sin BBDD real.
"""
from __future__ import annotations

import inspect

import pytest
from domain.ports.partidas_obra_port import PartidasObraPort
from domain.ports.valuation_repository import ValuationRepository
from infrastructure.database.sqlalchemy_valuation_repository import (
    SQL_OBRA_DEL_DOCUMENTO,
    SqlAlchemyValuationRepository,
)
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


class _Fabrica:
    """``SessionFactory`` mínima sobre un SQLite en memoria compartido."""

    def __init__(self) -> None:
        self.engine = create_engine("sqlite://", poolclass=StaticPool,
                                    connect_args={"check_same_thread": False})
        with self.engine.begin() as conexion:
            conexion.execute(text(
                "CREATE TABLE albaran_documents_merge (id TEXT PRIMARY KEY, obra_codigo TEXT, obra_nombre TEXT)"
            ))
            conexion.execute(text(
                "INSERT INTO albaran_documents_merge (id, obra_codigo, obra_nombre) VALUES "
                "('doc-0678', '0678', 'OBRA'), ('doc-686', ' 686 ', 'OBRA'), ('doc-sin', NULL, 'OBRA')"
            ))

    def create_session(self) -> Session:
        return Session(self.engine)


@pytest.fixture
def repo() -> SqlAlchemyValuationRepository:
    return SqlAlchemyValuationRepository(_Fabrica())  # type: ignore[arg-type]


def test_f076_t7_obra_del_documento(repo):
    assert repo.obra_del_documento(document_id="doc-0678") == "0678"


def test_f076_t7_la_obra_sale_tal_cual_la_canoniza_la_cache(repo):
    """sv6 no reescribe el merge ni canoniza aquí: lo hace la caché (comun)."""
    assert repo.obra_del_documento(document_id="doc-686") == " 686 "


@pytest.mark.parametrize("documento", ["doc-sin", "no-existe"])
def test_f076_t7_sin_obra_o_sin_fila_none(repo, documento):
    assert repo.obra_del_documento(document_id=documento) is None


def test_f076_t7_no_inicializa_el_schema_ni_escribe(repo):
    """Lectura pura de una tabla de sv3: no lanza el DDL de sv6."""
    repo.obra_del_documento(document_id="doc-0678")
    assert repo.is_initialized is False
    fuente = inspect.getsource(SqlAlchemyValuationRepository.obra_del_documento)
    assert "initialize" not in fuente
    assert "SQL_OBRA_DEL_DOCUMENTO" in fuente
    assert SQL_OBRA_DEL_DOCUMENTO == "SELECT obra_codigo FROM albaran_documents_merge WHERE id = :document_id"
    for verbo in ("INSERT", "UPDATE", "DELETE", "commit("):
        assert verbo not in fuente


def test_f076_t7_el_puerto_declara_obra_del_documento():
    assert "obra_del_documento" in ValuationRepository.__abstractmethods__


def test_f076_t7_puerto_de_la_lista_lo_cumple_la_cache_de_comun():
    from ruesma_comun.sigrid import CachePartidasObra

    cache = CachePartidasObra(lambda *a: ([], []), ttl_s=1, max_obras=1, ttl_fallo_s=1)
    assert isinstance(cache, PartidasObraPort)
    assert not isinstance(object(), PartidasObraPort)
