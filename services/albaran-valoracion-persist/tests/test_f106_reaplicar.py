# tests/test_f106_reaplicar.py
"""F-106 fase B · sv6: revalorar conserva lo editado a mano (R19, R23–R28, R32 c).

``replace_valuation`` lee las filas con edición de la valoración anterior (y las
legadas que ``es_fila_manual`` da por tocadas), calcula las nuevas como hoy y,
antes de confirmar:

- R24, R25: con pareja (``merge_line_id``; sintéticas por padre y
  ``modifier_source`` si hay una sola) aplica la edición con ``aplicar_edicion``;
- R26: sin pareja, conserva la fila entera si su blanca existe o es una
  ``fila_entera`` sin blanca; si no, se pierde (``ediciones_perdidas:N``);
- R27: una legada cuenta como ``fila_entera``; origen Nueva recrea su derivada
  ``manual_override``; una línea que no es del contrato nuevo pasa a Nueva con
  ``front_contrato_cambiado``;
- R28: total y contadores con las filas finales; si algo falla, rollback.

BBDD SQLite en memoria con las tablas de sv6 (ORM) y tablas mínimas de sv3. Sin red.
"""
from __future__ import annotations

import json

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from domain.models.valuation_records import (
    DerivedContratoLineRecord,
    LineValuationRecord,
    ValuationHeaderRecord,
)
from infrastructure.database.orm_valuation_models import Base
from infrastructure.database.sqlalchemy_valuation_repository import SqlAlchemyValuationRepository
from ruesma_comun.edicion_manual import leer_edicion, registrar_edicion

DOC = "doc-f106"
ALTER = "ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS edicion_manual_json TEXT"


class _Fabrica:
    def __init__(self, motor) -> None:
        self.motor = motor

    def create_session(self) -> Session:
        return Session(self.motor, expire_on_commit=False)


def _motor():
    motor = create_engine("sqlite://", poolclass=StaticPool,
                          connect_args={"check_same_thread": False})
    md = MetaData()
    Table("albaran_documents_merge", md, Column("id", String(36), primary_key=True))
    Table("albaran_lines_merge", md, Column("id", Integer, primary_key=True),
          Column("document_id", String(36)))
    Table("albaran_contrato_lines_merge", md, Column("id", Integer, primary_key=True),
          Column("codigo_contrato", String(64)))
    for tabla in Base.metadata.sorted_tables:
        if tabla.name not in md.tables:
            tabla.to_metadata(md)
    md.create_all(motor)
    with motor.begin() as c:
        # La columna propia de sv4 (la crea sv4 al arrancar).
        c.execute(text("ALTER TABLE albaran_line_valuations ADD COLUMN codigo_externo VARCHAR(64)"))
        c.execute(text("INSERT INTO albaran_documents_merge (id) VALUES (:d)"), {"d": DOC})
        for mid in (701, 702, 704):
            c.execute(text("INSERT INTO albaran_lines_merge (id, document_id) VALUES (:i, :d)"),
                      {"i": mid, "d": DOC})
        for cid, contrato in ((504, "C1"), (505, "C1"), (600, "C2")):
            c.execute(text("INSERT INTO albaran_contrato_lines_merge (id, codigo_contrato) VALUES (:i, :c)"),
                      {"i": cid, "c": contrato})
    return motor


def _repo(motor):
    repo = SqlAlchemyValuationRepository(_Fabrica(motor))
    repo._initialized = True
    return repo


def _linea(merge_line_id, *, matched=504, precio=11.2, cantidad=10.0, importe=None, dto=7.0,
           derivada=None, **extra):
    importe = round(cantidad * precio * (1 - (dto or 0) / 100), 2) if importe is None else importe
    campos = dict(
        merge_line_id=merge_line_id, matched_contrato_line_id=matched,
        derived_contrato_line_record=derivada,
        precio_unitario_contrato_db=precio, precio_unitario_pdf_inferido=None,
        precio_unitario_final=precio, precio_unitario_source="contrato_db",
        precio_unitario_agreement="agree", unidad_albaran="UD", unidad_contrato="UD",
        unidad_categoria="unidad", unidad_category_match=True,
        cantidad_albaran=cantidad, cantidad_convertida=cantidad, factor_conversion=1.0,
        importe_calculado=importe, importe_albaran_declarado=None,
        importe_source="calculated", codigo_partida_albaran="01.04",
        codigo_partida_final="01.04", partida_action="existing_matched",
        match_confidence_pct=90.0, match_method="exact_concept", review_required=False,
        descripcion_linea="TUBO PVC 110", descuento_albaran_aplicado=dto,
    )
    campos.update(extra)
    return LineValuationRecord(**campos)


def _cabecera(contrato="C1", status="ok", lineas=()):
    return ValuationHeaderRecord(
        document_id=DOC, contrato_codigo=contrato, status=status, provider_ia=None,
        model_name=None, prompt_key=None,
        total_valorado=sum(x.importe_calculado or 0 for x in lineas), total_lines=len(lineas),
        lines_matched_exact=len(lineas), lines_matched_semantic=0, lines_matched_price_only=0,
        lines_unmatched=0, review_required=False,
    )


def _valorar(motor, lineas, **cabecera):
    lineas = list(lineas)
    return _repo(motor).replace_valuation(header=_cabecera(lineas=lineas, **cabecera), lines=lineas)


def _filas(motor):
    with motor.connect() as c:
        return [dict(r) for r in c.execute(text(
            "SELECT * FROM albaran_line_valuations ORDER BY id")).mappings().all()]


def _fila(motor, merge_line_id):
    return next(f for f in _filas(motor) if f["merge_line_id"] == merge_line_id)


def _cab(motor):
    with motor.connect() as c:
        return dict(c.execute(text("SELECT * FROM albaran_valuations")).mappings().one())


def _derivada(motor, did):
    with motor.connect() as c:
        return dict(c.execute(text("SELECT * FROM contrato_lines_derived WHERE id = :i"),
                              {"i": did}).mappings().one())


def _editar(motor, merge_line_id, campos, **columnas):
    """Lo que hace sv4: escribe las columnas y registra la edición."""
    antes = _fila(motor, merge_line_id)
    despues = {**antes, **columnas}
    edicion = registrar_edicion(antes.get("edicion_manual_json"), fila_antes=antes,
                                fila_despues=despues, campos=campos)
    asignaciones = ", ".join(f"{c} = :{c}" for c in columnas)
    with motor.begin() as c:
        c.execute(text(f"UPDATE albaran_line_valuations SET {asignaciones + ', ' if asignaciones else ''}"
                       "edicion_manual_json = :e WHERE id = :i"),
                  {**columnas, "e": edicion, "i": antes["id"]})


def _base(motor, **cabecera):
    _valorar(motor, [_linea(701, matched=505, precio=5.0, dto=None), _linea(704)], **cabecera)


# =================================================================== #
# R19 · la columna
# =================================================================== #
def test_f106_r19_ddl_alter_idempotente():
    from infrastructure.database.schema_contribution import get_ddl_statements

    sentencias = [s for _, s in get_ddl_statements()]
    assert ALTER in sentencias
    creada = next(i for i, s in enumerate(sentencias) if "CREATE TABLE IF NOT EXISTS albaran_line_valuations" in s)
    assert sentencias.index(ALTER) > creada


def test_f106_r19_orm_columna_nula():
    from infrastructure.database.orm_valuation_models import AlbaranLineValuationOrm

    columna = AlbaranLineValuationOrm.__table__.columns["edicion_manual_json"]
    assert columna.nullable and str(columna.type) == "TEXT"


def test_f106_r19_valorar_sin_ediciones_la_deja_nula():
    motor = _motor()
    _base(motor)
    _base(motor)
    assert [f["edicion_manual_json"] for f in _filas(motor)] == [None, None]


# =================================================================== #
# R24, R25 · con pareja
# =================================================================== #
def test_f106_r25_r32c_cantidad_editada_sobrevive_con_el_precio_nuevo():
    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"cantidad"}, cantidad_albaran=48.0, cantidad_convertida=48.0,
            importe_calculado=499.97)

    _valorar(motor, [_linea(701, matched=505, precio=5.0, dto=None), _linea(704, precio=12.0)])

    f = _fila(motor, 704)
    assert (f["cantidad_convertida"], f["precio_unitario_final"]) == (48.0, 12.0)
    assert f["importe_calculado"] == pytest.approx(535.68)
    edicion = leer_edicion(f["edicion_manual_json"])
    assert edicion.calculado["precio_unitario_final"] == 12.0
    assert edicion.calculado["cantidad_convertida"] == 10.0
    assert list(edicion.campos) == ["cantidad"]


def test_f106_r25_r32c_importe_editado_despeja_el_precio():
    motor = _motor()
    _valorar(motor, [_linea(704, cantidad=48.0, importe=104.16)])
    _editar(motor, 704, {"importe"}, importe_calculado=104.16, precio_unitario_final=2.333333)

    _valorar(motor, [_linea(704, cantidad=48.0)])

    f = _fila(motor, 704)
    assert f["importe_calculado"] == 104.16
    assert f["precio_unitario_final"] == pytest.approx(2.333333)
    assert f["descuento_albaran_aplicado"] == 7.0


def test_f106_r25_partida_y_codigo_externo_se_reaplican():
    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"codigo_partida", "codigo_externo"}, codigo_partida_final=None,
            partida_action="almacen_elegido", codigo_externo="X1")

    _base(motor)

    f = _fila(motor, 704)
    assert (f["codigo_partida_final"], f["partida_action"], f["codigo_externo"]) == (
        None, "almacen_elegido", "X1")


def test_f106_r24_sintetica_por_padre_y_modificador_si_hay_una():
    motor = _motor()
    sintetica = dict(line_kind="synthetic_modifier", parent_merge_line_id=704,
                     modifier_source="ia3")
    _valorar(motor, [_linea(704), _linea(None, precio=3.0, dto=None, **sintetica)])
    sid = next(f for f in _filas(motor) if f["line_kind"] == "synthetic_modifier")["id"]
    antes = next(f for f in _filas(motor) if f["id"] == sid)
    edicion = registrar_edicion(None, fila_antes=antes, fila_despues={**antes, "unidad_contrato": "M"},
                                campos={"unidad"})
    with motor.begin() as c:
        c.execute(text("UPDATE albaran_line_valuations SET unidad_contrato = 'M', "
                       "edicion_manual_json = :e WHERE id = :i"), {"e": edicion, "i": sid})

    _valorar(motor, [_linea(704), _linea(None, precio=4.0, dto=None, **sintetica)])

    nueva = next(f for f in _filas(motor) if f["line_kind"] == "synthetic_modifier")
    assert (nueva["unidad_contrato"], nueva["precio_unitario_final"]) == ("M", 4.0)
    assert len(_filas(motor)) == 2


# =================================================================== #
# R26 · sin pareja
# =================================================================== #
def test_f106_r26_sin_pareja_con_blanca_se_conserva_entera():
    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"cantidad"}, cantidad_albaran=48.0, cantidad_convertida=48.0,
            importe_calculado=499.97)

    _valorar(motor, [_linea(701, matched=505, precio=5.0, dto=None)])

    f = _fila(motor, 704)
    assert (f["cantidad_convertida"], f["importe_calculado"]) == (48.0, 499.97)
    assert leer_edicion(f["edicion_manual_json"]) is not None


def test_f106_r26_sin_blanca_se_pierde_y_la_cabecera_lo_dice():
    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"cantidad"}, cantidad_albaran=48.0, cantidad_convertida=48.0)
    with motor.begin() as c:
        c.execute(text("DELETE FROM albaran_lines_merge WHERE id = 704"))

    _valorar(motor, [_linea(701, matched=505, precio=5.0, dto=None)])

    assert [f["merge_line_id"] for f in _filas(motor)] == [701]
    assert "ediciones_perdidas:1" in json.loads(_cab(motor)["review_reasons_json"])


@pytest.mark.parametrize("status", ["failed", "no_contract"])
def test_f106_r26_valoracion_sin_filas_conserva_las_editadas(status):
    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"unidad"}, unidad_contrato="M")

    _valorar(motor, [], status=status, contrato=None if status == "no_contract" else "C1")

    filas = _filas(motor)
    assert [f["merge_line_id"] for f in filas] == [704]
    assert filas[0]["unidad_contrato"] == "M"


def test_f106_r26_fila_entera_sin_blanca_se_conserva():
    motor = _motor()
    _base(motor)
    with Session(motor) as s:
        vid = s.execute(text("SELECT id FROM albaran_valuations")).scalar_one()
        s.execute(text(
            "INSERT INTO albaran_line_valuations (valuation_id, merge_line_id, precio_unitario_final, "
            "precio_unitario_source, precio_unitario_agreement, unidad_categoria, unidad_category_match, "
            "cantidad_albaran, cantidad_convertida, importe_calculado, importe_source, partida_action, "
            "match_confidence_pct, match_method, review_required, created_at_utc, line_kind, "
            "descripcion_linea, edicion_manual_json) VALUES (:v, NULL, 3.0, 'manual', 'manual', 'unidad', 1, "
            "2.0, 2.0, 6.0, 'calculated', 'existing_matched', 0, 'none', 0, 't', 'manual', 'PORTE', :e)"),
            {"v": vid, "e": registrar_edicion(None, fila_antes=None, fila_despues={}, campos=set(),
                                              fila_entera=True)})
        s.commit()

    _base(motor)

    manual = [f for f in _filas(motor) if f["line_kind"] == "manual"]
    assert len(manual) == 1 and manual[0]["descripcion_linea"] == "PORTE"
    assert manual[0]["importe_calculado"] == 6.0


# =================================================================== #
# R27 · legadas y origen
# =================================================================== #
def test_f106_r27_legada_bloqueada_cuenta_como_fila_entera():
    motor = _motor()
    _base(motor)
    with motor.begin() as c:
        c.execute(text("UPDATE albaran_line_valuations SET bloqueada = 1, cantidad_convertida = 30, "
                       "cantidad_albaran = 30 WHERE merge_line_id = 704"))

    _base(motor)

    filas = [f for f in _filas(motor) if f["merge_line_id"] == 704]
    assert len(filas) == 1
    assert (filas[0]["cantidad_convertida"], filas[0]["bloqueada"]) == (30.0, 1)


def test_f106_r27_origen_nueva_recrea_su_derivada_manual_override():
    motor = _motor()
    _base(motor)
    with Session(motor) as s:
        vid = s.execute(text("SELECT id FROM albaran_valuations")).scalar_one()
        s.execute(text(
            "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, source_document_id, "
            "codigo_contrato, descripcion_linea, unidad_medida, precio_unitario, codigo_partida, origen, "
            "created_at_utc) VALUES (640, :v, :d, 'C1', 'TUBO PVC 110', 'UD', 2.333333, '01.04', "
            "'manual_override', 't')"), {"v": vid, "d": DOC})
        s.commit()
    _editar(motor, 704, {"importe", "origen"}, importe_calculado=104.16, precio_unitario_final=2.333333,
            matched_contrato_line_id=None, derived_contrato_line_id=640)

    _base(motor)

    f = _fila(motor, 704)
    assert f["matched_contrato_line_id"] is None
    derivada = _derivada(motor, f["derived_contrato_line_id"])
    assert derivada["origen"] == "manual_override"
    assert derivada["precio_unitario"] == pytest.approx(f["precio_unitario_final"])
    assert f["importe_calculado"] == 104.16


def test_f106_r27_contrato_cambiado_pasa_a_nueva_con_su_precio():
    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"cantidad", "origen"}, cantidad_albaran=48.0, cantidad_convertida=48.0)

    _valorar(motor, [_linea(704, matched=600, precio=13.0)], contrato="C2")

    f = _fila(motor, 704)
    assert f["matched_contrato_line_id"] is None
    derivada = _derivada(motor, f["derived_contrato_line_id"])
    assert (derivada["origen"], derivada["codigo_contrato"]) == ("manual_override", "C2")
    assert derivada["precio_unitario"] == 13.0
    assert "front_contrato_cambiado" in json.loads(f["review_reasons_json"])


def test_f106_r27_origen_del_mismo_contrato_se_queda_en_su_linea():
    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"origen"}, matched_contrato_line_id=505)

    _base(motor)

    f = _fila(motor, 704)
    assert (f["matched_contrato_line_id"], f["derived_contrato_line_id"]) == (505, None)


# =================================================================== #
# R28 · total, contadores y rollback
# =================================================================== #
def test_f106_r28_total_y_contadores_con_las_filas_finales():
    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"cantidad"}, cantidad_albaran=48.0, cantidad_convertida=48.0)

    _valorar(motor, [_linea(701, matched=505, precio=5.0, dto=None), _linea(704, precio=12.0)])

    cab = _cab(motor)
    assert cab["total_valorado"] == pytest.approx(50.0 + 535.68)
    assert cab["total_lines"] == 2


def test_f106_r28_si_falla_queda_la_valoracion_anterior(monkeypatch):
    from infrastructure.database import sqlalchemy_valuation_repository as modulo

    motor = _motor()
    _base(motor)
    _editar(motor, 704, {"cantidad"}, cantidad_albaran=48.0, cantidad_convertida=48.0)
    antes = _filas(motor)

    def _rompe(*_a, **_k):
        raise RuntimeError("boom")

    monkeypatch.setattr(modulo, "aplicar_edicion", _rompe)
    with pytest.raises(RuntimeError):
        _base(motor)
    assert _filas(motor) == antes
