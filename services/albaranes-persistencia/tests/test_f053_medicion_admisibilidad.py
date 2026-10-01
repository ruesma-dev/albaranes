# tests/test_f053_medicion_admisibilidad.py
"""F-053 · script de medición de admisibilidad (solo lectura).

Datos falsos; ni red ni BBDD: se prueban las funciones puras del script y que
sus dos consultas son solo SELECT.
"""
from __future__ import annotations

import csv

from scripts import medir_admisibilidad_f053 as m

CABECERA = {
    "approved": True, "obra_codigo": "0404", "proveedor_cif": "B00000000",
    "numero_albaran": "A-1", "fecha": "2026-09-01",
    "valoracion_status": "ok", "valoracion_contrato": "CT-1",
}


def _fila(doc: str, lv_id: int | None, **linea) -> dict:
    base = {
        "document_id": doc, **CABECERA, "lv_id": lv_id,
        "cantidad_albaran": 2.0, "cantidad_convertida": 2.0,
        "importe_calculado": 10.0,
        "matched_contrato_line_id": 10, "derived_contrato_line_id": None,
        "codigo_partida_final": "16.01", "partida_action": "existing_matched",
        "cl_sigrid_ide": 555, "cl_contrato": "CT-1", "cl_partida": "16.01",
    }
    base.update(linea)
    return base


def _evaluar(*filas, merge=()):
    (alb,) = m.agrupar(list(filas), list(merge))
    return m.evaluar(alb)


def test_f053_medicion_solo_cuentan_lineas_con_importe():
    ev = _evaluar(_fila("d1", 1),
                  _fila("d1", 2, importe_calculado=0.0, codigo_partida_final=None),
                  _fila("d1", 3, importe_calculado=None, partida_action=None,
                        codigo_partida_final=None))
    assert ev["lineas_con_importe"] == 1 and ev["lineas_sin_importe"] == 2
    assert ev["casa_misma_partida"] == 1 and ev["sin_partida_ni_almacen"] == 0
    assert ev["registrable_a"] is True and ev["registrable_b"] is True


def test_f053_medicion_partida_distinta_solo_b():
    ev = _evaluar(_fila("d1", 1, codigo_partida_final="15.01"))
    assert ev["casa_partida_distinta"] == 1
    assert ev["registrable_a"] is False and ev["registrable_b"] is True


def test_f053_medicion_sin_casar_con_partida_solo_b_y_necesitan_producto():
    ev = _evaluar(_fila("d1", 1, matched_contrato_line_id=None),
                  _fila("d1", 2, derived_contrato_line_id=7),
                  _fila("d1", 3, cl_contrato="OTRO"),
                  _fila("d1", 4, cl_sigrid_ide=None))
    assert ev["partida_sin_casar"] == 4 and ev["necesitan_producto"] == 4
    assert ev["registrable_a"] is False and ev["registrable_b"] is True


def test_f053_medicion_almacen_casa_solo_con_linea_sin_partida():
    ev = _evaluar(
        _fila("d1", 1, codigo_partida_final=None,
              partida_action="almacen_sin_partida", cl_partida=" "),
        _fila("d1", 2, codigo_partida_final="",
              partida_action="almacen_elegido"),
        _fila("d1", 3, codigo_partida_final=None, matched_contrato_line_id=None,
              partida_action="alm_acopio"),
    )
    assert ev["almacen"] == 3 and ev["almacen_sin_casar"] == 1
    assert ev["casa_misma_partida"] == 1 and ev["casa_partida_distinta"] == 1
    assert ev["registrable_a"] is False and ev["registrable_b"] is True


def test_f053_medicion_sin_partida_ni_almacen_no_es_registrable():
    ev = _evaluar(_fila("d1", 1, codigo_partida_final=None,
                        partida_action="no_action"),
                  _fila("d1", 2, matched_contrato_line_id=None,
                        codigo_partida_final="  ", partida_action=None))
    assert ev["sin_partida_ni_almacen"] == 2
    assert ev["registrable_a"] is False and ev["registrable_b"] is False


def test_f053_medicion_negativas_entran_en_b_y_no_en_a():
    ev = _evaluar(_fila("d1", 1),
                  _fila("d1", 2, cantidad_convertida=-1.0, importe_calculado=-5.0))
    assert ev["lineas_negativas"] == 1
    assert ev["registrable_a"] is False and ev["registrable_b"] is True


def test_f053_medicion_importe_sin_cantidad_bloquea():
    ev = _evaluar(_fila("d1", 1, cantidad_convertida=None, cantidad_albaran=None))
    assert ev["lineas_sin_cantidad"] == 1
    assert ev["registrable_a"] is False and ev["registrable_b"] is False


def test_f053_medicion_cabecera_incompleta_bloquea():
    for campo, valor in (("obra_codigo", ""), ("proveedor_cif", None),
                         ("numero_albaran", " "), ("fecha", "2026-02-30"),
                         ("fecha", "01/09/2026")):
        ev = _evaluar(_fila("d1", 1, **{campo: valor}))
        assert ev["cabecera_completa"] is False, (campo, valor)
        assert ev["registrable_a"] is False and ev["registrable_b"] is False


def test_f053_medicion_no_valorado_no_es_registrable():
    ev = _evaluar(_fila("d1", 1, valoracion_status="partial"))
    assert ev["valorado"] is False
    assert ev["registrable_a"] is False and ev["registrable_b"] is False


def test_f053_medicion_sin_lineas_valoradas_usa_las_del_merge():
    filas = [_fila("d1", None, valoracion_status="no_contract",
                   valoracion_contrato=None)]
    merge = [
        {"document_id": "d1", "linea_id": 1, "cantidad": 3, "precio_neto": 9.0,
         "codigo_imputacion": "16.01"},
        {"document_id": "d1", "linea_id": 2, "cantidad": 1, "precio_neto": 4.0,
         "codigo_imputacion": None},
        {"document_id": "d1", "linea_id": 3, "cantidad": 1, "precio_neto": 0,
         "codigo_imputacion": None},
        {"document_id": "otro", "linea_id": 4, "cantidad": 1, "precio_neto": 1,
         "codigo_imputacion": "1"},
    ]
    ev = _evaluar(*filas, merge=merge)
    assert ev["origen_lineas"] == "merge" and ev["con_contrato"] is False
    assert ev["lineas_con_importe"] == 2 and ev["lineas_sin_importe"] == 1
    assert ev["partida_sin_casar"] == 1 and ev["sin_partida_ni_almacen"] == 1
    assert ev["registrable_b"] is False


def test_f053_medicion_resumen_y_csv(tmp_path):
    evs = [_evaluar(_fila("d1", 1)),
           _evaluar(_fila("d2", 1, codigo_partida_final="15.01")),
           _evaluar(_fila("d3", 1, codigo_partida_final=None, partida_action=None))]
    res = m.resumir(evs)
    assert res["albaranes"] == 3 and res["valorado"] == 3
    assert res["registrable_a"] == 1 and res["pct_registrable_a"] == 33.3
    assert res["registrable_b"] == 2 and res["pct_registrable_b"] == 66.7
    texto = m.formatear_resumen(res, todos=False)
    assert "(a) registrables con sigrid-api tal cual: 1 (33.3 %)" in texto
    assert "(b) registrables con el criterio del humano: 2 (66.7 %)" in texto
    ruta = tmp_path / "salida.csv"
    m.escribir_csv(str(ruta), evs)
    assert ruta.read_bytes().startswith(b"\xef\xbb\xbf")
    filas = list(csv.DictReader(ruta.open(encoding="utf-8-sig"), delimiter=";"))
    assert [f["document_id"] for f in filas] == ["d1", "d2", "d3"]


def test_f053_medicion_consultas_solo_lectura():
    for sql in (m.SQL_LINEAS_VALORADAS, m.SQL_LINEAS_MERGE):
        palabras = set(sql.upper().split())
        assert sql.strip().upper().startswith("SELECT")
        assert not palabras & {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
                               "TRUNCATE", "CREATE", "GRANT"}
