# tests/test_f052_rastro_busqueda.py
"""F-052 T9–T10 · rastro de la búsqueda de contratos (R20, R21).

sv3 es dueño del schema de ``albaran_documents_merge``: añade con DDL
idempotente las cuatro columnas ``contratos_busqueda_*`` (CIF, obra,
resultado y fecha de la última búsqueda) y las sella al terminar
``ContratoEnrichmentService.enrich_merge_document``. sv4 solo las lee.

Sin red ni BBDD: sesión y repositorio dobles.
"""
from __future__ import annotations

import inspect
import re
from datetime import datetime, timedelta, timezone

import pytest

#: (columna, tipo) de design §4. Todas nullable.
_COLUMNAS_RASTRO = (
    ("contratos_busqueda_cif", "VARCHAR(64)"),
    ("contratos_busqueda_obra", "VARCHAR(32)"),
    ("contratos_busqueda_resultado", "VARCHAR(16)"),
    ("contratos_busqueda_at_utc", "VARCHAR(64)"),
)


def _sentencias_del_rastro() -> list[str]:
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    return [s for s in _PHASE2_DDL if "contratos_busqueda_" in s]


# ------------------------------------------------------------------ #
# R20 · DDL idempotente, ORM y schema exportado dicen lo mismo
# ------------------------------------------------------------------ #
def test_f052_r20_el_ddl_anade_las_cuatro_columnas_al_merge():
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    for columna, tipo in _COLUMNAS_RASTRO:
        esperado = (
            "ALTER TABLE albaran_documents_merge "
            f"ADD COLUMN IF NOT EXISTS {columna} {tipo}"
        )
        assert esperado in _PHASE2_DDL, f"falta el ALTER de {columna}"


def test_f052_r20_el_ddl_del_rastro_es_idempotente_y_solo_toca_el_merge():
    sentencias = _sentencias_del_rastro()
    assert len(sentencias) == 4
    for sentencia in sentencias:
        assert sentencia.startswith("ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS ")
        for prohibido in ("DROP", "RENAME", "NOT NULL", "DEFAULT", "DELETE", "UPDATE"):
            assert prohibido not in sentencia, f"{prohibido} en {sentencia}"


def test_f052_r20_schema_contribution_exporta_el_ddl_del_rastro():
    """sv7 aplica el schema de sv3 desde ``schema_contribution``."""
    from infrastructure.database.schema_contribution import get_ddl_statements

    exportadas = {sql for _, sql in get_ddl_statements()}
    for sentencia in _sentencias_del_rastro():
        assert sentencia in exportadas, sentencia


def test_f052_r20_el_orm_del_merge_espeja_las_columnas_del_ddl():
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    columnas = AlbaranDocumentMergeOrm.__table__.columns
    for nombre, tipo in _COLUMNAS_RASTRO:
        assert nombre in columnas, f"el ORM no declara {nombre}"
        assert columnas[nombre].nullable, f"{nombre} debe admitir NULL"
        longitud = int(re.search(r"\((\d+)\)", tipo).group(1))
        assert columnas[nombre].type.length == longitud, f"{nombre}: ORM y DDL difieren"


def test_f052_r20_la_tabla_raw_no_lleva_el_rastro():
    from infrastructure.database.orm_models import AlbaranDocumentOrm

    columnas = AlbaranDocumentOrm.__table__.columns
    for nombre, _ in _COLUMNAS_RASTRO:
        assert nombre not in columnas, f"{nombre} se coló en la tabla raw"


def test_f052_r20_el_puerto_declara_sellar_busqueda_contratos():
    from domain.ports.contrato_merge_repository_port import ContratoMergeRepository

    firma = inspect.signature(ContratoMergeRepository.sellar_busqueda_contratos)
    assert list(firma.parameters)[1:] == ["document_id", "cif", "obra", "resultado"]
    assert all(
        p.kind is inspect.Parameter.KEYWORD_ONLY
        for nombre, p in firma.parameters.items() if nombre != "self"
    )


# --- Repositorio: UPDATE del rastro con una sesión doble ------------- #
class _Sesion:
    def __init__(self) -> None:
        self.sentencias: list[tuple[str, dict]] = []
        self.confirmada = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sentencia, parametros=None):
        self.sentencias.append((str(sentencia), dict(parametros or {})))

    def commit(self):
        self.confirmada = True


class _Fabrica:
    generation = 1

    def __init__(self) -> None:
        self.sesion = _Sesion()

    def ensure_database_and_engine(self):
        pass

    def create_session(self):
        return self.sesion


def _repositorio():
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )

    fabrica = _Fabrica()
    repositorio = SqlAlchemyAlbaranRepository(session_factory=fabrica)
    repositorio._initialized_generation = fabrica.generation  # sin crear tablas
    return repositorio, fabrica.sesion


@pytest.mark.parametrize("resultado", ["encontrados", "ninguno", "error", "sin_datos"])
def test_f052_r20_el_repositorio_sella_las_cuatro_columnas(resultado):
    repositorio, sesion = _repositorio()
    antes = datetime.now(timezone.utc)

    repositorio.sellar_busqueda_contratos(
        document_id="doc-1", cif="B82899550", obra="0691", resultado=resultado,
    )

    [(sql, parametros)] = sesion.sentencias
    assert sesion.confirmada
    assert re.sub(r"\s+", " ", sql).strip() == (
        "UPDATE albaran_documents_merge "
        "SET contratos_busqueda_cif = :cif, contratos_busqueda_obra = :obra, "
        "contratos_busqueda_resultado = :resultado, "
        "contratos_busqueda_at_utc = :at_utc WHERE id = :doc_id"
    )
    at_utc = datetime.fromisoformat(parametros.pop("at_utc"))
    assert at_utc.utcoffset() == timedelta(0)
    assert antes <= at_utc <= datetime.now(timezone.utc)
    assert parametros == {
        "cif": "B82899550", "obra": "0691", "resultado": resultado, "doc_id": "doc-1",
    }


def test_f052_r20_el_repositorio_sella_sin_datos_con_nulos():
    repositorio, sesion = _repositorio()
    repositorio.sellar_busqueda_contratos(
        document_id="doc-1", cif=None, obra=None, resultado="sin_datos",
    )
    [(_, parametros)] = sesion.sentencias
    assert (parametros["cif"], parametros["obra"]) == (None, None)


@pytest.mark.parametrize("resultado", ["", "ok", "ENCONTRADOS", None])
def test_f052_r20_el_repositorio_rechaza_un_resultado_desconocido(resultado):
    repositorio, sesion = _repositorio()
    with pytest.raises(ValueError, match="resultado"):
        repositorio.sellar_busqueda_contratos(
            document_id="doc-1", cif="B1", obra="0691", resultado=resultado,
        )
    assert sesion.sentencias == []
