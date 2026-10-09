# tests/test_f065_bloqueada_ddl.py
"""F-065 · R17 (T2) · columna ``bloqueada`` de las líneas valoradas.

sv6 es el dueño de ``albaran_line_valuations``: añade con DDL idempotente
``bloqueada BOOLEAN NOT NULL DEFAULT FALSE``. La marca la pone sv4 al guardar
una fila (guardar = bloquear); sv6 no la escribe, así que el replace al
revalorar inserta las filas con el defecto (``false``): conservar lo
bloqueado al revalorar es F-058. Ninguna lógica de sv6 cambia: solo DDL y ORM.

Sin BBDD: texto del DDL, metadatos del ORM y el constructor de filas.
"""
from __future__ import annotations

import inspect

ALTER = (
    "ALTER TABLE albaran_line_valuations "
    "ADD COLUMN IF NOT EXISTS bloqueada BOOLEAN NOT NULL DEFAULT FALSE"
)


def _ddl() -> list[tuple[str, str]]:
    from infrastructure.database.schema_contribution import get_ddl_statements

    return get_ddl_statements()


def test_f065_r17_ddl_alter_idempotente_de_bloqueada():
    assert [sql for _, sql in _ddl() if "bloqueada" in sql] == [ALTER]


def test_f065_r17_ddl_el_alter_va_despues_del_create_de_la_tabla():
    sqls = [sql for _, sql in _ddl()]
    i_create = next(
        i for i, s in enumerate(sqls)
        if "CREATE TABLE IF NOT EXISTS albaran_line_valuations" in s
    )
    assert sqls.index(ALTER) > i_create


def test_f065_r17_orm_declara_bloqueada_no_nula_con_defecto_en_bbdd():
    from infrastructure.database.orm_valuation_models import AlbaranLineValuationOrm

    columna = AlbaranLineValuationOrm.__table__.columns["bloqueada"]
    assert columna.nullable is False
    assert str(columna.server_default.arg).lower() == "false"


def test_f065_r17_el_replace_no_escribe_bloqueada():
    """El replace de sv6 no la nombra: la fila nueva coge el defecto."""
    from infrastructure.database.sqlalchemy_valuation_repository import (
        SqlAlchemyValuationRepository,
    )

    assert "bloqueada" not in inspect.getsource(SqlAlchemyValuationRepository)


def test_f065_r17_la_fila_nueva_del_replace_no_trae_valor_de_bloqueada():
    """Sin valor en la fila, el INSERT la omite y la BBDD pone ``false``."""
    from domain.models.valuation_records import LineValuationRecord
    from infrastructure.database.sqlalchemy_valuation_repository import (
        SqlAlchemyValuationRepository,
    )

    linea = LineValuationRecord(
        merge_line_id=1, matched_contrato_line_id=None,
        derived_contrato_line_record=None,
        precio_unitario_contrato_db=None, precio_unitario_pdf_inferido=None,
        precio_unitario_final=None, precio_unitario_source="none",
        precio_unitario_agreement="none", unidad_albaran="UD",
        unidad_contrato=None, unidad_categoria="unidad",
        unidad_category_match=True, cantidad_albaran=1.0,
        cantidad_convertida=None, factor_conversion=None,
        importe_calculado=10.0, importe_albaran_declarado=None,
        importe_source="none", codigo_partida_albaran=None,
        codigo_partida_final=None, partida_action="almacen_sin_partida",
        match_confidence_pct=0.0, match_method="none", review_required=False,
    )
    fila = SqlAlchemyValuationRepository._build_line_orm(
        valuation_id="v1", line=linea, derived_contrato_line_id=None,
        created_at_utc="2026-10-09T00:00:00Z",
    )
    assert fila.bloqueada is None


def test_f065_r17_ddl_en_sqlite_las_filas_nacen_desbloqueadas():
    """La columna del ORM, creada en una BBDD, deja ``false`` a quien no la da."""
    from sqlalchemy import create_engine, text

    from infrastructure.database.orm_valuation_models import AlbaranLineValuationOrm

    motor = create_engine("sqlite://")
    columna = AlbaranLineValuationOrm.__table__.columns["bloqueada"]
    with motor.begin() as c:
        c.execute(text(
            "CREATE TABLE t (id INTEGER PRIMARY KEY, bloqueada BOOLEAN NOT NULL DEFAULT "
            f"{columna.server_default.arg})"))
        c.execute(text("INSERT INTO t (id) VALUES (1)"))
        assert c.execute(text("SELECT bloqueada FROM t")).scalar_one() in (0, False)
