# tests/test_f053_r36_altas_sigrid_ddl.py
"""F-053 · R36 (T2) · DDL de ``albaran_altas_sigrid`` en sv3.

sv3 es el dueño del schema del merge y crea la tabla del alta en Sigrid (una
fila por documento; solo la escribe sv9, sv4 la lee). DDL idempotente
(``CREATE ... IF NOT EXISTS``) en ``phase2_ddl._PHASE2_DDL``, que es lo que sv3
aplica al arrancar (API y worker), y exportado por ``schema_contribution``.

Sin BBDD: se inspecciona el texto de las sentencias.
"""
from __future__ import annotations

import re

#: Columnas de design §6, con su tipo y restricciones, en orden.
COLUMNAS = (
    ("document_id", "VARCHAR(36) PRIMARY KEY REFERENCES albaran_documents_merge(id) ON DELETE CASCADE"),
    ("estado", "VARCHAR(24) NOT NULL"),
    ("modo", "VARCHAR(12)"),
    ("sigrid_con_ide", "INTEGER"),
    ("sigrid_cod", "VARCHAR(24)"),
    ("adjunto_estado", "VARCHAR(16)"),
    ("sigrid_gra_ide", "INTEGER"),
    ("motivos_json", "TEXT"),
    ("avisos_json", "TEXT"),
    ("peticion_json", "TEXT"),
    ("respuesta_json", "TEXT"),
    ("historial_json", "TEXT"),
    ("intentos", "INTEGER NOT NULL DEFAULT 0"),
    ("approved_at_utc", "VARCHAR(64)"),
    ("approved_by", "VARCHAR(255)"),
    ("ultimo_intento_at_utc", "VARCHAR(64)"),
    ("creado_at_utc", "VARCHAR(64) NOT NULL"),
    ("actualizado_at_utc", "VARCHAR(64)"),
)


def _sentencias_alta() -> list[str]:
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    return [s for s in _PHASE2_DDL if "albaran_altas_sigrid" in s]


def _normalizar(sql: str) -> str:
    return re.sub(r"\s+", " ", sql).strip()


def test_f053_r36_crea_la_tabla_con_las_columnas_del_diseno():
    creates = [s for s in _sentencias_alta() if s.lstrip().startswith("CREATE TABLE")]
    assert len(creates) == 1
    sql = _normalizar(creates[0])
    assert sql.startswith("CREATE TABLE IF NOT EXISTS albaran_altas_sigrid (")
    cuerpo = sql[sql.index("(") + 1: sql.rindex(")")]
    definiciones = [d.strip() for d in cuerpo.split(", ") if d.strip()]
    assert definiciones == [f"{c} {t}" for c, t in COLUMNAS]


def test_f053_r36_indice_por_estado():
    assert (
        "CREATE INDEX IF NOT EXISTS ix_albaran_altas_sigrid_estado "
        "ON albaran_altas_sigrid (estado)"
    ) in [_normalizar(s) for s in _sentencias_alta()]


def test_f053_r36_ddl_idempotente_y_sin_tocar_otras_tablas():
    sentencias = _sentencias_alta()
    assert len(sentencias) == 2
    for sql in sentencias:
        assert "IF NOT EXISTS" in sql
        for prohibido in ("DROP", "RENAME", "DELETE FROM", "UPDATE ", "ALTER TABLE"):
            assert prohibido not in sql.upper(), prohibido


def test_f053_r36_la_tabla_va_despues_de_crear_el_merge():
    """La FK apunta al merge: el DDL del alta se aplica tras ``initialize()``
    (que crea el merge) y no antes que las columnas del propio merge."""
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    indices = [i for i, s in enumerate(_PHASE2_DDL) if "albaran_altas_sigrid" in s]
    assert indices == sorted(indices)
    assert "CREATE TABLE" in _PHASE2_DDL[indices[0]]


def test_f053_r36_schema_contribution_exporta_la_tabla_y_es_suya():
    from infrastructure.database.schema_contribution import (
        get_ddl_statements,
        get_owned_table_names,
    )

    exportadas = {sql for _, sql in get_ddl_statements()}
    for sentencia in _sentencias_alta():
        assert sentencia in exportadas
    assert "albaran_altas_sigrid" in get_owned_table_names()


def test_f053_r36_sv3_no_escribe_la_tabla():
    """R34: solo sv9 escribe en la tabla. sv3 solo la crea."""
    import pathlib

    raiz = pathlib.Path(__file__).resolve().parents[1]
    for fichero in raiz.rglob("*.py"):
        if ".venv" in fichero.parts or "tests" in fichero.parts:
            continue
        texto = fichero.read_text(encoding="utf-8", errors="ignore")
        for patron in ("INSERT INTO albaran_altas_sigrid", "UPDATE albaran_altas_sigrid",
                       "DELETE FROM albaran_altas_sigrid"):
            assert patron not in texto, f"{fichero}: {patron}"
