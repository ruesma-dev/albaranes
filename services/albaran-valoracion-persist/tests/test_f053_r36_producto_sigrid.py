# tests/test_f053_r36_producto_sigrid.py
"""F-053 · R36 y R42 (T2b) · columna ``producto_sigrid`` de las líneas valoradas.

sv6 es el dueño de ``albaran_line_valuations``: añade con DDL idempotente la
columna ``producto_sigrid VARCHAR(24)`` (producto genérico de Sigrid que el
administrativo elige en sv4 para una línea sin vincular; ``NULL`` = por
defecto). Nula y sin defecto: el replace de sv6 inserta la fila sin ella, así
que al revalorar el producto elegido se pierde (R42; conservarlo es F-058).
Ninguna lógica de sv6 cambia: solo DDL y ORM.

Sin BBDD: texto del DDL, metadatos del ORM y el constructor de filas del
repositorio.
"""
from __future__ import annotations

import inspect
import re

ALTER = (
    "ALTER TABLE albaran_line_valuations "
    "ADD COLUMN IF NOT EXISTS producto_sigrid VARCHAR(24)"
)


def _ddl() -> list[tuple[str, str]]:
    from infrastructure.database.schema_contribution import get_ddl_statements

    return get_ddl_statements()


def test_f053_r36_alter_idempotente_de_producto_sigrid():
    sentencias = [sql for _, sql in _ddl() if "producto_sigrid" in sql]
    assert sentencias == [ALTER]


def test_f053_r36_el_alter_va_despues_del_create_de_la_tabla():
    sqls = [sql for _, sql in _ddl()]
    i_create = next(
        i for i, s in enumerate(sqls)
        if "CREATE TABLE IF NOT EXISTS albaran_line_valuations" in s
    )
    assert sqls.index(ALTER) > i_create


def test_f053_r36_orm_declara_producto_sigrid_nula_y_sin_defecto():
    from infrastructure.database.orm_valuation_models import (
        AlbaranLineValuationOrm,
    )

    columna = AlbaranLineValuationOrm.__table__.columns["producto_sigrid"]
    assert columna.nullable is True
    assert columna.type.length == 24
    assert columna.default is None and columna.server_default is None


def test_f053_r42_el_replace_no_escribe_producto_sigrid():
    """El replace de sv6 construye la fila sin la columna: queda NULL."""
    from infrastructure.database.sqlalchemy_valuation_repository import (
        SqlAlchemyValuationRepository,
    )

    fuente = inspect.getsource(SqlAlchemyValuationRepository)
    assert "producto_sigrid" not in fuente


def test_f053_r42_fila_nueva_del_replace_lleva_producto_sigrid_nulo():
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
        created_at_utc="2026-10-06T00:00:00Z",
    )
    assert fila.producto_sigrid is None


def test_f053_drift_toda_columna_del_orm_de_lineas_esta_en_el_ddl():
    """Sin drift: cada columna que el ORM espera la crea o la añade el DDL."""
    from infrastructure.database.orm_valuation_models import (
        AlbaranLineValuationOrm,
    )

    texto = "\n".join(sql for _, sql in _ddl() if "albaran_line_valuations" in sql)
    for columna in AlbaranLineValuationOrm.__table__.columns:
        assert re.search(rf"\b{columna.name}\b", texto), columna.name
