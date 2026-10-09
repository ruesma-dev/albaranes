# tests/f053_sv4_bbdd.py
"""F-053 · BBDD SQLite en memoria para los tests del alta en sv4.

El repositorio real (``AlbaranReviewRepository``) sobre:

- las tablas del ORM de sv4 (merge, líneas, contratos y sus líneas), creadas
  con ``Base.metadata`` más ``sigrid_ide`` y ``contexto_linea_json`` (columnas
  de sv3 que el ORM de sv4 no declara);
- las de valoración de sv6 (las de ``conftest``, más ``producto_sigrid``);
- ``contrato_lines_derived``, ``undo_log`` y ``albaran_altas_sigrid`` (la de
  sv3, que escribe sv9), esta última opcional (``con_altas``).

SQLite no tiene ``FOR UPDATE`` (SQLAlchemy lo omite al compilar para SQLite)
ni ``to_regclass``: lo que se prueba aquí es el COMPORTAMIENTO (qué se rechaza
y que nada cambia). El orden de las dos sentencias y la carrera con sv9 se
prueban con la sesión doble de ``test_f053_t19_cerrojo.py``.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DOC = "f053-doc-0000-0000-000000000001"
DOC_AJENO = "f053-doc-0000-0000-000000000002"
VAL = "f053-val-1"
VAL_AJENO = "f053-val-2"

_VALORACION = (
    """
    CREATE TABLE albaran_valuations (
        id VARCHAR(64) PRIMARY KEY, document_id VARCHAR(64) NOT NULL,
        contrato_codigo VARCHAR(64), status VARCHAR(32), provider_ia VARCHAR(32),
        model_name VARCHAR(100), total_valorado DOUBLE PRECISION, total_lines INTEGER,
        lines_matched_exact INTEGER, lines_matched_semantic INTEGER,
        lines_matched_price_only INTEGER, lines_unmatched INTEGER,
        review_required BOOLEAN NOT NULL DEFAULT 0, review_reasons_json TEXT,
        created_at_utc VARCHAR(64), updated_at_utc VARCHAR(40)
    )
    """,
    """
    CREATE TABLE albaran_line_valuations (
        id INTEGER PRIMARY KEY, valuation_id VARCHAR(64) NOT NULL,
        merge_line_id INTEGER, matched_contrato_line_id INTEGER,
        derived_contrato_line_id INTEGER, precio_unitario_contrato_db DOUBLE PRECISION,
        precio_unitario_pdf_inferido DOUBLE PRECISION, precio_unitario_final DOUBLE PRECISION,
        precio_unitario_source VARCHAR(32), precio_unitario_agreement VARCHAR(32),
        unidad_albaran VARCHAR(32), unidad_contrato VARCHAR(32), unidad_categoria VARCHAR(32),
        unidad_category_match BOOLEAN, factor_conversion DOUBLE PRECISION,
        cantidad_albaran DOUBLE PRECISION, cantidad_convertida DOUBLE PRECISION,
        importe_calculado DOUBLE PRECISION, importe_albaran_declarado DOUBLE PRECISION,
        importe_source VARCHAR(32) NOT NULL DEFAULT 'calculated',
        codigo_partida_albaran VARCHAR(64), codigo_partida_final VARCHAR(64),
        partida_action VARCHAR(32), match_confidence_pct DOUBLE PRECISION,
        match_method VARCHAR(32), descuento_albaran_aplicado DOUBLE PRECISION,
        codigo_externo VARCHAR(64), line_kind VARCHAR(32), parent_merge_line_id INTEGER,
        modifier_source VARCHAR(32), modifier_reason TEXT, descripcion_linea TEXT,
        review_required BOOLEAN NOT NULL DEFAULT 0, review_reasons_json TEXT,
        producto_sigrid VARCHAR(24), created_at_utc VARCHAR(64),
        bloqueada BOOLEAN NOT NULL DEFAULT 0
    )
    """,
    """
    CREATE TABLE contrato_lines_derived (
        id INTEGER PRIMARY KEY, created_by_valuation_id VARCHAR(64),
        source_document_id VARCHAR(64), codigo_contrato VARCHAR(64),
        codigo_producto VARCHAR(64), descripcion_linea TEXT, unidad_medida VARCHAR(32),
        precio_unitario DOUBLE PRECISION, codigo_partida VARCHAR(64), origen VARCHAR(32),
        created_at_utc VARCHAR(40)
    )
    """,
    """
    CREATE TABLE undo_log (
        id INTEGER PRIMARY KEY, created_at_utc VARCHAR(40) NOT NULL,
        action VARCHAR(40) NOT NULL, description TEXT NOT NULL, payload TEXT NOT NULL,
        undone BOOLEAN NOT NULL DEFAULT 0, actor VARCHAR(120), document_id VARCHAR(64)
    )
    """,
    "ALTER TABLE albaran_contrato_lines_merge ADD COLUMN sigrid_ide INTEGER",
    "ALTER TABLE albaran_lines_merge ADD COLUMN contexto_linea_json TEXT",
)

#: El DDL de sv3 (``phase2_ddl``), con tipos de SQLite.
DDL_ALTAS = """
CREATE TABLE albaran_altas_sigrid (
  document_id VARCHAR(36) PRIMARY KEY, estado VARCHAR(24) NOT NULL, modo VARCHAR(12),
  sigrid_con_ide INTEGER, sigrid_cod VARCHAR(24), adjunto_estado VARCHAR(16),
  sigrid_gra_ide INTEGER, motivos_json TEXT, avisos_json TEXT, peticion_json TEXT,
  respuesta_json TEXT, historial_json TEXT, intentos INTEGER NOT NULL DEFAULT 0,
  approved_at_utc VARCHAR(64), approved_by VARCHAR(255), ultimo_intento_at_utc VARCHAR(64),
  creado_at_utc VARCHAR(64) NOT NULL, actualizado_at_utc VARCHAR(64))
"""


class Fabrica:
    """``SessionFactory`` mínima sobre un motor SQLite (una conexión)."""

    def __init__(self, motor) -> None:
        self.engine = motor

    def create_session(self) -> Session:
        return Session(self.engine)


def _merge(sesion: Session, document_id: str, **campos: Any) -> None:
    fila = {
        "id": document_id, "provider_origin": "merge", "source_filename": "a.pdf",
        "source_mime_type": "application/pdf", "source_sha256": f"sha-{document_id}",
        "prompt_key": "p", "schema_name": "s", "model_name": "m",
        "raw_extraction_json": "{}", "created_at_utc": "2026-10-08T08:00:00+00:00",
        "approved": False, "is_active": True, "numero_albaran": "A-1",
        "proveedor_cif": "B12345678", "obra_codigo": "0404", "tipologia": "generico",
        "tipologia_mixta": False,
    }
    fila.update(campos)
    columnas = ", ".join(fila)
    marcas = ", ".join(f":{c}" for c in fila)
    sesion.execute(text(f"INSERT INTO albaran_documents_merge ({columnas}) VALUES ({marcas})"), fila)


def linea_valorada(sesion: Session, **campos: Any) -> None:
    fila = {
        "valuation_id": VAL, "merge_line_id": None, "matched_contrato_line_id": None,
        "derived_contrato_line_id": None, "precio_unitario_final": 10.0,
        "cantidad_albaran": 2.0, "importe_calculado": 20.0, "importe_source": "calculated",
        "codigo_partida_final": "03.02", "line_kind": "from_albaran",
        "descripcion_linea": "ARIDO", "producto_sigrid": None,
    }
    fila.update(campos)
    columnas = ", ".join(fila)
    marcas = ", ".join(f":{c}" for c in fila)
    sesion.execute(text(f"INSERT INTO albaran_line_valuations ({columnas}) VALUES ({marcas})"), fila)


def construir(*, con_altas: bool = True, status: str = "ok", aprobado: bool = False):
    """Motor SQLite con dos documentos (``DOC`` y ``DOC_AJENO``) valorados.

    ``DOC``: líneas 11 (vinculada: casa con la 501 del contrato CT/1, con
    ``sigrid_ide``), 12 (sin vincular, con partida, familia de línea
    ``alquiler_maquinaria``), 13 (sin vincular, importe 0) y 14 (manual,
    sin línea del albarán). ``DOC_AJENO``: línea 21.
    """
    from infrastructure.database.orm_models import Base

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    with Session(motor) as s:
        for sentencia in _VALORACION:
            s.execute(text(sentencia))
        if con_altas:
            s.execute(text(DDL_ALTAS))
        _merge(s, DOC, approved=aprobado,
               approved_at_utc="2026-10-08T09:00:00+00:00" if aprobado else None)
        _merge(s, DOC_AJENO)
        s.execute(text(
            "INSERT INTO albaran_contratos_merge (id, document_id, codigo_contrato, fetched_at_utc) "
            "VALUES (1, :d, 'CT/1', 't')"), {"d": DOC})
        s.execute(text(
            "INSERT INTO albaran_contrato_lines_merge (id, contrato_id, codigo_contrato, "
            "codigo_producto, descripcion_linea, precio_unitario, codigo_partida, "
            "fetched_at_utc, sigrid_ide) VALUES "
            "(501, 1, 'CT/1', 'HA25', 'HORMIGON HA-25', 10.0, '03.02', 't', 700101)"))
        for lid, idx, contexto in (
            (701, 1, None),
            (702, 2, json.dumps({"tipo_familia": "alquiler_maquinaria"})),
            (703, 3, None),
        ):
            s.execute(text(
                "INSERT INTO albaran_lines_merge (id, document_id, provider_origin, line_index, "
                "concepto, cantidad, contexto_linea_json) VALUES "
                "(:id, :d, 'merge', :i, 'LINEA', 2.0, :c)"),
                {"id": lid, "d": DOC, "i": idx, "c": contexto})
        s.execute(text(
            "INSERT INTO albaran_valuations (id, document_id, contrato_codigo, status, "
            "total_valorado, review_required) VALUES "
            "(:v1, :d1, 'CT/1', :st, 60.0, 0), (:v2, :d2, 'CT/1', 'ok', 5.0, 0)"),
            {"v1": VAL, "d1": DOC, "st": status, "v2": VAL_AJENO, "d2": DOC_AJENO})
        linea_valorada(s, id=11, merge_line_id=701, matched_contrato_line_id=501)
        linea_valorada(s, id=12, merge_line_id=702, codigo_partida_final="04.01")
        linea_valorada(s, id=13, merge_line_id=703, importe_calculado=0.0)
        linea_valorada(s, id=14, merge_line_id=None, line_kind="manual",
                       importe_calculado=20.0, codigo_partida_final=None)
        linea_valorada(s, id=21, valuation_id=VAL_AJENO, merge_line_id=None)
        s.commit()
    return motor


def repositorio(motor):
    from infrastructure.database.review_repository import AlbaranReviewRepository

    repo = AlbaranReviewRepository(Fabrica(motor))  # type: ignore[arg-type]
    repo.initialize = lambda: True  # type: ignore[method-assign]
    repo._undo_table_ready = True  # type: ignore[attr-defined]
    return repo


def poner_alta(motor, estado: str, *, document_id: str = DOC, cod: str | None = "AC26/7",
               **campos: Any) -> None:
    fila = {
        "document_id": document_id, "estado": estado, "sigrid_cod": cod,
        "creado_at_utc": "2026-10-08T09:01:00+00:00", "modo": "simulacion",
    }
    fila.update(campos)
    columnas = ", ".join(fila)
    marcas = ", ".join(f":{c}" for c in fila)
    with Session(motor) as s:
        s.execute(text("DELETE FROM albaran_altas_sigrid WHERE document_id = :d"),
                  {"d": document_id})
        s.execute(text(f"INSERT INTO albaran_altas_sigrid ({columnas}) VALUES ({marcas})"), fila)
        s.commit()


def foto(motor) -> dict[str, list[tuple]]:
    """Todas las filas de las tablas que sv4 puede tocar (para «nada cambia»)."""
    tablas = (
        "albaran_documents_merge", "albaran_lines_merge", "albaran_valuations",
        "albaran_line_valuations", "contrato_lines_derived", "undo_log",
    )
    with Session(motor) as s:
        return {
            t: sorted((tuple(r) for r in s.execute(text(f"SELECT * FROM {t}")).all()), key=repr)
            for t in tablas
        }
