# tests/f075_bbdd.py
"""F-075 · BBDD SQLite para los tests del importe en sv4 (no es una suite).

Reutiliza el DDL de ``f053_sv4_bbdd`` (ORM de sv4 + tablas de valoración de
sv6) y siembra documentos con todas las combinaciones de importe:

==========  =====================================  ==================  =========
documento   líneas del merge (``precio_neto``)     valoración          se ve
==========  =====================================  ==================  =========
``ALB``     100, 50                                ninguna             150 albarán
``CON``     None, None                             ok 60 (con filas)   60 contrato
``DIS``     100                                    ok 70 (con filas)   100 albarán ≠
``PAR``     40, None                               ninguna             40 albarán, 1 de 2
``NADA``    None                                   ninguna             —
``VACIA``   None                                   no_contract vacía   —
``APR``     1000 (aprobado)                        ninguna             1000 albarán
``BORR``    5 (en la papelera)                     ninguna             (no sale)
==========  =====================================  ==================  =========
"""
from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from tests.f053_sv4_bbdd import _VALORACION, _merge, repositorio  # noqa: F401

ALB, CON, DIS, PAR, NADA, VACIA, APR, BORR = (
    "f075-alb", "f075-con", "f075-dis", "f075-par", "f075-nada", "f075-vacia", "f075-apr", "f075-borr",
)

#: documento ⇒ (obra, CIF, líneas, valoración (status, total, con_filas) o None, aprobado, activo)
SIEMBRA = {
    ALB: ("0686", "B11111111", [100.0, 50.0], None, False, True),
    CON: ("0686", "B22222222", [None, None], ("ok", 60.0, True), False, True),
    DIS: ("0678", "B22222222", [100.0], ("ok", 70.0, True), False, True),
    PAR: ("0678", "B11111111", [40.0, None], None, False, True),
    NADA: ("0678", "B33333333", [None], None, False, True),
    VACIA: ("0686", "B33333333", [None], ("no_contract", 0.0, False), False, True),
    APR: ("0686", "B11111111", [1000.0], None, True, True),
    BORR: ("0686", "B11111111", [5.0], None, False, False),
}


def construir(siembra: dict | None = None):
    from infrastructure.database.orm_models import Base

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    linea_id, fila_id = 1000, 5000
    with Session(motor) as s:
        for sentencia in _VALORACION:
            s.execute(text(sentencia))
        for doc, (obra, cif, netos, valoracion, aprobado, activo) in (siembra or SIEMBRA).items():
            _merge(s, doc, obra_codigo=obra, proveedor_cif=cif, proveedor_nombre=f"PROV {cif}",
                   approved=aprobado, is_active=activo, source_sha256=f"sha-{doc}",
                   confidence_pct_calc=50.0, created_at_utc=f"2026-10-15T08:00:00+00:00")
            for i, neto in enumerate(netos):
                linea_id += 1
                s.execute(text(
                    "INSERT INTO albaran_lines_merge (id, document_id, provider_origin, line_index, "
                    "concepto, cantidad, precio_neto) VALUES (:id, :d, 'merge', :i, 'LINEA', 1.0, :n)"),
                    {"id": linea_id, "d": doc, "i": i, "n": neto})
            if valoracion is not None:
                status, total, con_filas = valoracion
                s.execute(text(
                    "INSERT INTO albaran_valuations (id, document_id, status, total_valorado, "
                    "review_required) VALUES (:v, :d, :st, :t, 0)"),
                    {"v": f"val-{doc}", "d": doc, "st": status, "t": total})
                if con_filas:
                    fila_id += 1
                    s.execute(text(
                        "INSERT INTO albaran_line_valuations (id, valuation_id, importe_calculado, "
                        "line_kind) VALUES (:id, :v, :t, 'from_albaran')"),
                        {"id": fila_id, "v": f"val-{doc}", "t": total})
        s.commit()
    return motor
