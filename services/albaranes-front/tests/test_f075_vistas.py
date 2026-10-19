# tests/test_f075_vistas.py
"""F-075 R22 · las vistas «Obras» y «Proveedores» suman el mismo importe por
documento que la bandeja, con SQL portable (PostgreSQL y SQLite).

Antes usaban ``LEFT JOIN LATERAL`` (solo PostgreSQL) sobre el valorado. El
test de equivalencia comprueba que el valorado de la expresión nueva es el de
la última valoración del documento con filas.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
from tests.f075_bbdd import ALB, CON, DIS, NADA, PAR, VACIA, construir, repositorio


@pytest.fixture()
def motor():
    return construir()


def test_f075_r22_obras_suman_el_importe_mostrado(motor):
    obras = {o.obra_codigo: o for o in repositorio(motor).list_obras_resumen()}
    # 0686: ALB 150 + CON 60 + VACIA — + APR 1000 (aprobado también cuenta; BORR no)
    assert obras["0686"].importe == 1210.0
    assert obras["0686"].total_albaranes == 4
    # 0678: DIS 100 + PAR 40 + NADA —
    assert obras["0678"].importe == 140.0
    assert obras["0678"].pendientes == 3


def test_f075_r22_proveedores_suman_el_importe_mostrado(motor):
    provs = {p.proveedor_cif: p for p in repositorio(motor).list_proveedores_resumen()}
    assert provs["B11111111"].importe == 1190.0  # ALB 150 + PAR 40 + APR 1000
    assert provs["B22222222"].importe == 160.0   # CON 60 + DIS 100
    assert provs["B33333333"].importe == 0.0     # NADA y VACIA, sin importe


def test_f075_r22_equivalencia_del_valorado_con_la_ultima_valoracion_con_filas(motor):
    from infrastructure.database.review_repository import sql_valorado_documento

    with Session(motor) as s:
        # Una segunda valoración (id mayor) para CON: manda la última.
        s.execute(text("INSERT INTO albaran_valuations (id, document_id, status, total_valorado, "
                       "review_required) VALUES ('zz-ultima', :d, 'ok', 61.0, 0)"), {"d": CON})
        s.execute(text("INSERT INTO albaran_line_valuations (id, valuation_id, importe_calculado, "
                       "line_kind) VALUES (9999, 'zz-ultima', 61.0, 'from_albaran')"))
        s.commit()
        nuevo = dict(s.execute(text(
            f"SELECT d.id, {sql_valorado_documento('d')} FROM albaran_documents_merge d")).all())
        filas = s.execute(text(
            "SELECT av.document_id, av.id, av.total_valorado FROM albaran_valuations av "
            "WHERE EXISTS (SELECT 1 FROM albaran_line_valuations lv WHERE lv.valuation_id = av.id)")).all()
    esperado: dict[str, float | None] = {d: None for d in nuevo}
    ultima: dict[str, str] = {}
    for doc, vid, total in filas:
        if doc not in ultima or vid > ultima[doc]:
            ultima[doc], esperado[doc] = vid, total
    assert nuevo == esperado
    assert nuevo[CON] == 61.0 and nuevo[DIS] == 70.0
    assert nuevo[VACIA] is None and nuevo[ALB] is None


def test_f075_r22_la_expresion_del_importe_es_la_de_la_bandeja(motor):
    from infrastructure.database.review_repository import sql_importe_mostrado

    with Session(motor) as s:
        vistos = dict(s.execute(text(
            f"SELECT d.id, {sql_importe_mostrado('d')} FROM albaran_documents_merge d")).all())
    assert vistos[ALB] == 150.0 and vistos[CON] == 60.0 and vistos[DIS] == 100.0
    assert vistos[PAR] == 40.0 and vistos[NADA] is None and vistos[VACIA] is None
