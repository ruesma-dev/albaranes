# tests/f065_bbdd.py
"""F-065 · BBDD SQLite en memoria de la fase 1: el albarán de METALFIRE.

Mismo esquema que ``f053_sv4_bbdd`` (tablas del ORM de sv4, las de
valoración de sv6 con la columna ``bloqueada`` de F-065 R17,
``contrato_lines_derived`` y ``undo_log``). Sin red ni BBDD real.

El documento ``DOC`` (contrato ``CTSU25/0359``):

- blancas (lo leído): 701 puerta EI2-60 ×8 (920 €), 702 puerta EI2-90 ×10
  (1150 €) y 703 portes ×1 (50 €);
- filas (lo que se aprueba): 11 Contrato (casa con la 501) 8 ud a 115 €,
  12 Contrato (502) 10 ud a 115 €, 13 Nueva (derivada 601) 1 portes a 50 €
  sin ``cantidad_convertida`` y con su descripción «PORTES» (F-078 R17: una
  sin vincular sin descripción no se aprueba); total 2120 €;
- líneas de contrato 501, 502 y 503 (puerta EI2-120, la que se «trae»).
"""
from __future__ import annotations

from typing import Any

from f053_sv4_bbdd import _VALORACION, DDL_ALTAS, Fabrica, _merge
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DOC = "f065-doc-0000-0000-000000000359"
DOC_AJENO = "f065-doc-0000-0000-000000000999"
VAL = "f065-val-1"
VAL_AJENO = "f065-val-2"
CONTRATO = "CTSU25/0359"

#: (F-115 R9, R13) La cabecera que manda la ficha al guardar (CIF, obra y
#: contrato elegido); ver ``f053_sv4_bbdd.CABECERA``.
#: (F-108 R11) Con su fecha y su número, como la de ``f053_sv4_bbdd``.
CABECERA = {"proveedor_cif": "B12345678", "obra_codigo": "0404",
            "selected_contrato_codigo": CONTRATO, "fecha": "2026-10-08",
            "numero_albaran": "A-1"}

COLUMNAS = (
    "id", "valuation_id", "merge_line_id", "matched_contrato_line_id",
    "derived_contrato_line_id", "precio_unitario_final", "precio_unitario_agreement",
    "unidad_contrato", "factor_conversion", "cantidad_albaran", "cantidad_convertida",
    "importe_calculado", "importe_source", "descuento_albaran_aplicado",
    "codigo_externo", "codigo_partida_final", "partida_action", "line_kind",
    "parent_merge_line_id", "descripcion_linea", "review_required",
    "review_reasons_json", "producto_sigrid", "bloqueada",
)


def linea(sesion: Session, **campos: Any) -> None:
    fila = {
        "valuation_id": VAL, "merge_line_id": None, "matched_contrato_line_id": None,
        "derived_contrato_line_id": None, "precio_unitario_final": 115.0,
        "precio_unitario_agreement": "agree", "unidad_contrato": "UD",
        "factor_conversion": 1.0, "cantidad_albaran": 1.0, "cantidad_convertida": 1.0,
        "importe_calculado": 115.0, "importe_source": "declared_albaran",
        "descuento_albaran_aplicado": None, "codigo_externo": None,
        "codigo_partida_final": "01.01", "partida_action": "existing_matched",
        "line_kind": "from_albaran", "parent_merge_line_id": None,
        "descripcion_linea": None, "review_required": True,
        "review_reasons_json": '["ia_match_trusted"]', "producto_sigrid": None,
        "bloqueada": False,
    }
    fila.update(campos)
    columnas = ", ".join(fila)
    marcas = ", ".join(f":{c}" for c in fila)
    sesion.execute(
        text(f"INSERT INTO albaran_line_valuations ({columnas}) VALUES ({marcas})"), fila,
    )


def construir(*, aprobado: bool = False, con_altas: bool = False, status: str = "ok"):
    """Motor SQLite con el albarán de METALFIRE (``DOC``) y uno ajeno."""
    from infrastructure.database.orm_models import Base

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    with Session(motor) as s:
        for sentencia in _VALORACION:
            s.execute(text(sentencia))
        if con_altas:
            s.execute(text(DDL_ALTAS))
        # (F-115 R13) La valoración es del contrato CONTRATO: el albarán lo tiene
        # seleccionado (datos coherentes; aprobar con otro contrato es un 409).
        _merge(s, DOC, approved=aprobado, approved_by="ana" if aprobado else None,
               approved_at_utc="2026-10-09T09:00:00+00:00" if aprobado else None,
               selected_contrato_codigo=CONTRATO)
        _merge(s, DOC_AJENO, selected_contrato_codigo=CONTRATO)
        s.execute(text(
            "INSERT INTO albaran_contratos_merge (id, document_id, codigo_contrato, "
            "fetched_at_utc) VALUES (1, :d, :c, 't')"), {"d": DOC, "c": CONTRATO})
        for cid, desc, partida in (
            (501, "PUERTA CORTAFUEGOS EI2-60", "01.01"),
            (502, "PUERTA CORTAFUEGOS EI2-90", "01.02"),
            (503, "PUERTA CORTAFUEGOS EI2-120", "01.03"),
        ):
            s.execute(text(
                "INSERT INTO albaran_contrato_lines_merge (id, contrato_id, codigo_contrato, "
                "codigo_producto, descripcion_linea, unidad_medida, precio_unitario, "
                "codigo_partida, fetched_at_utc, sigrid_ide) VALUES "
                "(:id, 1, :c, 'PCF', :d, 'UD', 115.0, :p, 't', :ide)"),
                {"id": cid, "c": CONTRATO, "d": desc, "p": partida, "ide": 900000 + cid})
        for lid, idx, concepto, cantidad, precio, neto in (
            (701, 1, "PUERTA EI2-60", 8.0, 115.0, 920.0),
            (702, 2, "PUERTA EI2-90", 10.0, 115.0, 1150.0),
            (703, 3, "PORTES", 1.0, 50.0, 50.0),
        ):
            s.execute(text(
                "INSERT INTO albaran_lines_merge (id, document_id, provider_origin, "
                "line_index, concepto, cantidad, precio, precio_neto) VALUES "
                "(:id, :d, 'merge', :i, :c, :q, :p, :n)"),
                {"id": lid, "d": DOC, "i": idx, "c": concepto, "q": cantidad, "p": precio,
                 "n": neto})
        s.execute(text(
            "INSERT INTO albaran_lines_merge (id, document_id, provider_origin, line_index, "
            "concepto, cantidad) VALUES (801, :d, 'merge', 1, 'AJENA', 3.0)"), {"d": DOC_AJENO})
        s.execute(text(
            "INSERT INTO albaran_valuations (id, document_id, contrato_codigo, status, "
            "total_valorado, review_required) VALUES "
            "(:v1, :d1, :c, :st, 2120.0, 1), (:v2, :d2, :c, 'ok', 30.0, 0)"),
            {"v1": VAL, "d1": DOC, "c": CONTRATO, "st": status, "v2": VAL_AJENO,
             "d2": DOC_AJENO})
        s.execute(text(
            "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, "
            "codigo_contrato, descripcion_linea, unidad_medida, precio_unitario, "
            "codigo_partida, origen) VALUES "
            "(601, :v, :c, 'PORTES', 'UD', 50.0, '03.01', 'nueva_no_match')"),
            {"v": VAL, "c": CONTRATO})
        linea(s, id=11, merge_line_id=701, matched_contrato_line_id=501,
              cantidad_albaran=8.0, cantidad_convertida=8.0, importe_calculado=920.0)
        linea(s, id=12, merge_line_id=702, matched_contrato_line_id=502,
              cantidad_albaran=10.0, cantidad_convertida=10.0, importe_calculado=1150.0,
              codigo_partida_final="01.02")
        linea(s, id=13, merge_line_id=703, derived_contrato_line_id=601,
              precio_unitario_final=50.0, factor_conversion=None, cantidad_albaran=1.0,
              cantidad_convertida=None, importe_calculado=50.0, codigo_partida_final="03.01",
              partida_action="new_line_created", descripcion_linea="PORTES")
        linea(s, id=21, valuation_id=VAL_AJENO, merge_line_id=801,
              matched_contrato_line_id=501, cantidad_albaran=3.0, cantidad_convertida=3.0,
              importe_calculado=30.0, precio_unitario_final=10.0)
        s.commit()
    return motor


def repositorio(motor):
    from infrastructure.database.review_repository import AlbaranReviewRepository

    repo = AlbaranReviewRepository(Fabrica(motor))  # type: ignore[arg-type]
    repo.initialize = lambda: True  # type: ignore[method-assign]
    repo._undo_table_ready = True  # type: ignore[attr-defined]
    return repo


def fila(motor, vid: int) -> dict[str, Any]:
    with Session(motor) as s:
        return dict(s.execute(
            text(f"SELECT {', '.join(COLUMNAS)} FROM albaran_line_valuations WHERE id = :id"),
            {"id": vid},
        ).mappings().one())


def filas(motor, valuation_id: str = VAL) -> list[dict[str, Any]]:
    with Session(motor) as s:
        return [dict(r) for r in s.execute(
            text(f"SELECT {', '.join(COLUMNAS)} FROM albaran_line_valuations "
                 "WHERE valuation_id = :v ORDER BY id"),
            {"v": valuation_id},
        ).mappings().all()]


def total(motor, valuation_id: str = VAL) -> float:
    with Session(motor) as s:
        return s.execute(
            text("SELECT total_valorado FROM albaran_valuations WHERE id = :v"),
            {"v": valuation_id},
        ).scalar_one()


def ejecutar(motor, sql: str, **parametros: Any) -> None:
    with Session(motor) as s:
        s.execute(text(sql), parametros)
        s.commit()


def documento(motor, document_id: str = DOC) -> dict[str, Any]:
    with Session(motor) as s:
        return dict(s.execute(
            text("SELECT approved, approved_at_utc, approved_by, numero_albaran "
                 "FROM albaran_documents_merge WHERE id = :id"),
            {"id": document_id},
        ).mappings().one())


def motor_con_valoracion(*, document_id: str, valuation_id: str, total: float = 0.0):
    """Motor con un documento pendiente y su valoración vacía (sin líneas):
    para los tests que siembran sus propias filas (F-019, F-036)."""
    from infrastructure.database.orm_models import Base

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    with Session(motor) as s:
        for sentencia in _VALORACION:
            s.execute(text(sentencia))
        _merge(s, document_id)
        s.execute(text(
            "INSERT INTO albaran_valuations (id, document_id, status, total_valorado, "
            "updated_at_utc) VALUES (:v, :d, 'ok', :t, '2026-08-18T13:24:26Z')"),
            {"v": valuation_id, "d": document_id, "t": total})
        s.commit()
    return motor


def fila_nueva(motor, *, valuation_id: str, id: int, **campos: Any) -> None:
    """Una fila Nueva (con su derivada ``id + 5000`` al mismo precio)."""
    with Session(motor) as s:
        s.execute(text(
            "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, "
            "descripcion_linea, unidad_medida, precio_unitario, codigo_partida, origen) "
            "VALUES (:id, :v, 'LINEA', 'UD', :pu, '01.01', 'nueva_no_match')"),
            {"id": id + 5000, "v": valuation_id,
             "pu": campos.get("precio_unitario_final", 115.0)})
        linea(s, id=id, valuation_id=valuation_id, derived_contrato_line_id=id + 5000,
              **campos)
        s.commit()
