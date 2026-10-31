# tests/test_f106_aprobar.py
"""F-106 R16, R32 b: no se aprueba con filas que no cuadran (ficha ni listado).

La fila de producción de AC26/30435 (48 × 11,20 −7 % con I 104,16) se aprobó y
sv9 la dio de alta como 48 × 2,17. Con F-106, sv4 no deja aprobar: lo que se ve
en la ficha es lo que se da de alta. Las no comparables no cuentan; estar en
almacén no es motivo (pero una de almacén que no cuadra sí lo es: sv9 la
rechazaría igual); «≠ albarán» (R13) no bloquea.

Repositorio real sobre SQLite (``f065_bbdd``). Sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from f065_bbdd import DOC, construir, documento, ejecutar, repositorio
from test_f106_fila import FILA, cecois

from domain.models.review_models import LineasIncompletasError, MergeDocumentUpdatePayload

AVISO = "Líneas que no cuadran (cantidad × precio × (1 − dto) ≠ importe): "


def _aprobar(motor):
    return repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")


def test_f106_r16_r32b_la_fila_de_produccion_no_se_aprueba_desde_el_listado():
    motor = cecois(q=48.0)

    with pytest.raises(LineasIncompletasError) as error:
        _aprobar(motor)

    # Orden de la ficha: 701, 702, 703 y la 704 (CECOIS) es la cuarta.
    assert error.value.no_cuadran == [4]
    assert error.value.aviso == AVISO + "4"
    assert documento(motor)["approved"] in (0, False)


def test_f106_r16_tampoco_desde_guardar_y_aprobar_de_la_ficha(monkeypatch):
    motor = cecois(q=48.0)
    repo = repositorio(motor)
    monkeypatch.setattr(repo, "get_document_detail", lambda document_id: "detalle")

    with pytest.raises(LineasIncompletasError) as error:
        repo.update_document_y_transicion(
            document_id=DOC, payload=MergeDocumentUpdatePayload(approved=True, numero_albaran="Z"))

    assert error.value.aviso == AVISO + "4"
    assert documento(motor)["approved"] in (0, False)
    assert documento(motor)["numero_albaran"] != "Z"


def test_f106_r16_cuadrada_se_aprueba():
    motor = cecois(q=48.0, importe=499.97, source="calculated")
    assert _aprobar(motor) is True


def test_f106_r16_tras_recalcular_el_precio_se_aprueba():
    from test_f106_fila import _patch

    motor = cecois(q=48.0)
    _patch(motor, cuadrar="precio")
    assert _aprobar(motor) is True


def test_f106_r16_borde_de_dos_centimos():
    motor = cecois(q=48.0, importe=499.99, source="calculated")
    assert _aprobar(motor) is True
    motor = cecois(q=48.0, importe=500.0, source="calculated")
    with pytest.raises(LineasIncompletasError):
        _aprobar(motor)


def test_f106_r16_no_comparable_no_cuenta():
    motor = cecois(q=48.0)
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = NULL "
             "WHERE id = :v", v=FILA)
    assert _aprobar(motor) is True


def test_f106_r16_importe_cero_no_es_a_registrar():
    motor = cecois(q=48.0, importe=0.0)
    assert _aprobar(motor) is True


def test_f106_r16_almacen_que_cuadra_no_bloquea_y_almacen_que_no_cuadra_si():
    motor = cecois()
    ejecutar(motor, "UPDATE albaran_line_valuations SET codigo_partida_final = NULL, "
             "partida_action = 'almacen_elegido' WHERE id = :v", v=FILA)
    assert _aprobar(motor) is True

    motor = cecois(q=48.0)
    ejecutar(motor, "UPDATE albaran_line_valuations SET codigo_partida_final = NULL, "
             "partida_action = 'almacen_elegido' WHERE id = :v", v=FILA)
    with pytest.raises(LineasIncompletasError) as error:
        _aprobar(motor)
    assert error.value.no_cuadran == [4]


def test_f106_r16_distinto_del_albaran_no_bloquea():
    # R13: 48 × 11,20 × 0,93 = 499,97 cuadra aunque el papel diga 104,16.
    motor = cecois(q=48.0, importe=499.97, source="calculated")
    assert _aprobar(motor) is True


def test_f106_r16_junto_a_otros_motivos_y_varias_posiciones():
    motor = cecois(q=48.0)
    # La 12 (2.ª) no cuadra: 10 × 115 = 1150 ≠ 999.
    ejecutar(motor, "UPDATE albaran_line_valuations SET importe_calculado = 999 WHERE id = 12")
    # La 11 (1.ª) sin importe.
    ejecutar(motor, "UPDATE albaran_line_valuations SET importe_calculado = NULL WHERE id = 11")
    with pytest.raises(LineasIncompletasError) as error:
        _aprobar(motor)
    assert error.value.posiciones == [1]
    assert error.value.no_cuadran == [2, 4]
    assert error.value.aviso == "Líneas sin cantidad o importe: 1. " + AVISO + "2, 4"


def test_f106_r16_el_metafire_de_f065_se_sigue_aprobando():
    # Regresión: el documento de F-065 cuadra entero.
    assert _aprobar(construir()) is True
