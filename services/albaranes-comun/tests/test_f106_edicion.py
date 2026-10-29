# tests/test_f106_edicion.py
"""F-106 fase B · comun: lo editado a mano en una fila, guardado y reaplicado.

- R20: ``registrar_edicion`` guarda lo que el revisor cambió (campo a campo, con
  las columnas que ese campo escribió) y, la primera vez, en ``calculado`` la fila
  tal como la dejó sv6. Fusiona con lo previo; desbloquear registra
  ``bloqueada: false`` y no borra nada.
- R21: las filas que crea sv4 nacen con ``fila_entera``.
- R22: ``es_fila_manual`` vive en comun; una fila con edición cuenta como tocada.
- R25: ``aplicar_edicion`` sustituye en la fila nueva los campos editados,
  recalcula con ``recalcular_fila`` y deja en ``calculado`` lo que sv6 calculó.

Dominio puro, sin BBDD.
"""
from __future__ import annotations

import json
import logging

import pytest

from ruesma_comun.edicion_manual import (
    EdicionManual,
    aplicar_edicion,
    es_fila_manual,
    leer_edicion,
    registrar_edicion,
)


def _fila(**cambios):
    """La fila CECOIS tal como la deja sv6: 10 × 11,20 −7 % = 104,16."""
    base = {
        "cantidad_albaran": 10.0, "cantidad_convertida": 10.0, "factor_conversion": 1.0,
        "precio_unitario_final": 11.2, "descuento_albaran_aplicado": 7.0,
        "importe_calculado": 104.16, "importe_source": "declared_albaran",
        "codigo_partida_final": "01.04", "partida_action": "existing_matched",
        "unidad_contrato": "UD", "descripcion_linea": "TUBO PVC 110",
        "codigo_externo": None, "producto_sigrid": None, "bloqueada": False,
        "matched_contrato_line_id": 504, "derived_contrato_line_id": None,
        "precio_unitario_source": "contract_db", "precio_unitario_agreement": "match",
    }
    base.update(cambios)
    return base


CALCULADO = {
    "cantidad_albaran": 10.0, "cantidad_convertida": 10.0, "precio_unitario_final": 11.2,
    "descuento_albaran_aplicado": 7.0, "importe_calculado": 104.16,
    "importe_source": "declared_albaran", "codigo_partida_final": "01.04",
    "partida_action": "existing_matched", "unidad_contrato": "UD",
    "descripcion_linea": "TUBO PVC 110", "matched_contrato_line_id": 504,
    "derived_contrato_line_id": None,
    "precio_unitario_source": "contract_db", "precio_unitario_agreement": "match",
}


def _json(texto):
    return json.loads(texto)


# =================================================================== #
# R20 · registrar
# =================================================================== #
def test_f106_r20_primera_vez_guarda_lo_cambiado_y_lo_calculado():
    antes = _fila()
    despues = _fila(cantidad_albaran=48.0, cantidad_convertida=48.0, importe_calculado=499.97,
                    importe_source="calculated")
    datos = _json(registrar_edicion(None, fila_antes=antes, fila_despues=despues, campos={"cantidad"}))

    assert datos == {
        "v": 1,
        "campos": {"cantidad": {"cantidad_albaran": 48.0, "cantidad_convertida": 48.0}},
        "calculado": CALCULADO,
        "fila_entera": False,
    }


def test_f106_r20_fusiona_y_conserva_el_primer_calculado():
    antes = _fila()
    primera = registrar_edicion(None, fila_antes=antes,
                                fila_despues=_fila(cantidad_convertida=48.0, cantidad_albaran=48.0),
                                campos={"cantidad"})
    # La segunda vez la fila ya no es la de sv6: el calculado no cambia.
    segunda = registrar_edicion(primera, fila_antes=_fila(cantidad_convertida=48.0),
                                fila_despues=_fila(codigo_partida_final=None, partida_action="almacen_elegido"),
                                campos={"codigo_partida"})
    datos = _json(segunda)

    assert datos["calculado"] == CALCULADO
    assert list(datos["campos"]) == ["cantidad", "codigo_partida"]
    assert datos["campos"]["codigo_partida"] == {"codigo_partida_final": None,
                                                 "partida_action": "almacen_elegido"}


def test_f106_r20_campos_en_el_orden_de_la_regla():
    datos = _json(registrar_edicion(
        None, fila_antes=_fila(), fila_despues=_fila(bloqueada=True, descuento_albaran_aplicado=10.0,
                                                     unidad_contrato="M"),
        campos={"bloqueada", "unidad", "descuento"},
    ))
    assert list(datos["campos"]) == ["descuento", "unidad", "bloqueada"]


@pytest.mark.parametrize(("previo", "nuevo", "queda"), [
    ("precio_unitario", "importe", "importe"),
    ("importe", "precio_unitario", "precio_unitario"),
])
def test_f106_r20_precio_o_importe_el_ultimo_que_se_tecleo(previo, nuevo, queda):
    primera = registrar_edicion(None, fila_antes=_fila(), fila_despues=_fila(), campos={previo})
    datos = _json(registrar_edicion(primera, fila_antes=_fila(), fila_despues=_fila(), campos={nuevo}))
    assert [c for c in datos["campos"] if c in ("precio_unitario", "importe")] == [queda]


def test_f106_r20_importe_y_precio_a_la_vez_manda_el_importe():
    datos = _json(registrar_edicion(None, fila_antes=_fila(), fila_despues=_fila(),
                                    campos={"importe", "precio_unitario"}))
    assert list(datos["campos"]) == ["importe"]


def test_f106_r20_desbloquear_registra_false_y_no_borra():
    primera = registrar_edicion(None, fila_antes=_fila(), fila_despues=_fila(cantidad_convertida=48.0),
                                campos={"cantidad"})
    bloqueada = registrar_edicion(primera, fila_antes=_fila(), fila_despues=_fila(bloqueada=True),
                                  campos={"bloqueada"})
    suelta = _json(registrar_edicion(bloqueada, fila_antes=_fila(), fila_despues=_fila(bloqueada=False),
                                     campos={"bloqueada"}))
    assert suelta["campos"]["bloqueada"] == {"bloqueada": False}
    assert "cantidad" in suelta["campos"]


@pytest.mark.parametrize(("despues", "origen"), [
    ({"matched_contrato_line_id": None, "derived_contrato_line_id": 640}, {"tipo": "nueva"}),
    ({"matched_contrato_line_id": 505, "derived_contrato_line_id": None}, {"tipo": "contrato", "linea": 505}),
    # Sin línea ni derivada (sin vincular) también es Nueva, nunca «contrato» sin línea.
    ({"matched_contrato_line_id": None, "derived_contrato_line_id": None}, {"tipo": "nueva"}),
])
def test_f106_r20_origen(despues, origen):
    datos = _json(registrar_edicion(None, fila_antes=_fila(), fila_despues=_fila(**despues),
                                    campos={"origen"}))
    assert datos["campos"]["origen"] == origen


def test_f106_r20_campo_desconocido_es_un_error():
    with pytest.raises(ValueError):
        registrar_edicion(None, fila_antes=_fila(), fila_despues=_fila(), campos={"total"})


def test_f106_r20_previa_rota_empieza_de_cero():
    datos = _json(registrar_edicion("{roto", fila_antes=_fila(), fila_despues=_fila(), campos={"unidad"}))
    assert datos["calculado"] == CALCULADO and list(datos["campos"]) == ["unidad"]


# =================================================================== #
# R21 · fila entera
# =================================================================== #
def test_f106_r21_fila_entera_sin_calculado():
    datos = _json(registrar_edicion(None, fila_antes=None, fila_despues=_fila(), campos=set(),
                                    fila_entera=True))
    assert datos == {"v": 1, "campos": {}, "calculado": {}, "fila_entera": True}


def test_f106_r21_una_edicion_por_defecto_no_es_fila_entera():
    edicion = EdicionManual(campos={"unidad": {"unidad_contrato": "M"}}, calculado={"unidad_contrato": "UD"})
    assert edicion.fila_entera is False
    assert json.loads(edicion.a_json())["fila_entera"] is False


def test_f106_r20_el_json_se_guarda_legible():
    # Sin escapar, como el resto de JSON de las filas (ensure_ascii=False).
    edicion = EdicionManual(campos={"descripcion": {"descripcion_linea": "CODO Ø110"}},
                            calculado={"descripcion_linea": "CODO 110"})
    assert "Ø110" in edicion.a_json()


def test_f106_leer_sin_la_marca_no_es_fila_entera():
    texto = json.dumps({"v": 1, "campos": {"unidad": {"unidad_contrato": "M"}},
                        "calculado": {"unidad_contrato": "UD"}})
    assert leer_edicion(texto).fila_entera is False


def test_f106_r21_la_edicion_es_inmutable():
    # La comparten sv4, sv6 y sv9: nadie la cambia por debajo de los demás.
    edicion = EdicionManual(campos={}, calculado={}, fila_entera=True)
    with pytest.raises(AttributeError):
        edicion.fila_entera = False  # type: ignore[misc]


def test_f106_r21_la_fila_entera_lo_sigue_siendo_al_editarla():
    primera = registrar_edicion(None, fila_antes=None, fila_despues=_fila(), campos=set(), fila_entera=True)
    datos = _json(registrar_edicion(primera, fila_antes=_fila(), fila_despues=_fila(unidad_contrato="M"),
                                    campos={"unidad"}))
    assert datos["fila_entera"] is True and datos["calculado"] == {}


# =================================================================== #
# leer_edicion
# =================================================================== #
@pytest.mark.parametrize("texto", [None, "", "   "])
def test_f106_leer_sin_edicion(texto, caplog):
    # Vacío es «sin edición», no un JSON roto: no avisa.
    with caplog.at_level(logging.WARNING):
        assert leer_edicion(texto) is None
    assert caplog.records == []


@pytest.mark.parametrize("texto", ["{roto", "[]", '{"v": 2, "campos": {}, "calculado": {}}',
                                   '{"v": 1, "campos": [], "calculado": {}}', "42"])
def test_f106_leer_rota_o_de_otra_version_es_none_y_avisa(texto, caplog):
    with caplog.at_level(logging.WARNING):
        assert leer_edicion(texto) is None
    assert caplog.records


def test_f106_leer_edicion_valida():
    texto = registrar_edicion(None, fila_antes=_fila(), fila_despues=_fila(unidad_contrato="M"),
                              campos={"unidad"})
    assert leer_edicion(texto) == EdicionManual(
        campos={"unidad": {"unidad_contrato": "M"}}, calculado=CALCULADO, fila_entera=False,
    )


# =================================================================== #
# R25 · aplicar
# =================================================================== #
def _editada(campos, despues, fila_entera=False):
    return leer_edicion(registrar_edicion(None, fila_antes=_fila(), fila_despues=_fila(**despues),
                                          campos=campos, fila_entera=fila_entera))


def test_f106_r25_cantidad_editada_recalcula_el_importe_con_el_precio_nuevo():
    edicion = _editada({"cantidad"}, {"cantidad_albaran": 48.0, "cantidad_convertida": 48.0})
    # La revaloración trae otro precio (12): el importe sale de la Q editada.
    nueva = _fila(precio_unitario_final=12.0, importe_calculado=111.6)
    fila = aplicar_edicion(nueva, edicion)

    assert (fila["cantidad_convertida"], fila["precio_unitario_final"]) == (48.0, 12.0)
    assert fila["importe_calculado"] == pytest.approx(535.68)
    assert fila["importe_source"] == "calculated"
    datos = _json(fila["edicion_manual_json"])
    assert datos["calculado"]["precio_unitario_final"] == 12.0
    assert datos["calculado"]["importe_calculado"] == 111.6
    assert datos["campos"] == edicion.campos


def test_f106_r25_importe_editado_despeja_el_precio_y_el_dto_se_queda():
    edicion = _editada({"importe"}, {"importe_calculado": 104.16})
    fila = aplicar_edicion(_fila(cantidad_albaran=48.0, cantidad_convertida=48.0, importe_calculado=499.97), edicion)
    assert fila["importe_calculado"] == 104.16
    assert fila["precio_unitario_final"] == pytest.approx(2.333333)
    assert fila["descuento_albaran_aplicado"] == 7.0


def test_f106_r25_importe_no_despejable_se_queda_como_se_edito():
    edicion = _editada({"importe"}, {"importe_calculado": 50.0})
    fila = aplicar_edicion(_fila(cantidad_albaran=0.0, cantidad_convertida=0.0), edicion)
    assert (fila["importe_calculado"], fila["precio_unitario_final"]) == (50.0, 11.2)


def test_f106_r25_sin_convertida_recalcula_con_la_cantidad_del_albaran():
    # Q = convertida ?? albarán: 48 × 12 −7 % = 535,68.
    edicion = _editada({"cantidad"}, {"cantidad_albaran": 48.0, "cantidad_convertida": None})
    fila = aplicar_edicion(_fila(precio_unitario_final=12.0, importe_calculado=111.6), edicion)
    assert fila["importe_calculado"] == pytest.approx(535.68)


def test_f106_r25_partida_vacia_es_almacen():
    edicion = _editada({"codigo_partida"}, {"codigo_partida_final": None, "partida_action": "almacen_elegido"})
    fila = aplicar_edicion(_fila(), edicion)
    assert (fila["codigo_partida_final"], fila["partida_action"]) == (None, "almacen_elegido")
    # Sin Q, P, d ni I editados el importe es el de sv6.
    assert (fila["importe_calculado"], fila["importe_source"]) == (104.16, "declared_albaran")


def test_f106_r25_el_resto_de_campos_se_sustituye():
    edicion = _editada({"unidad", "descripcion", "codigo_externo", "producto_sigrid", "bloqueada"},
                       {"unidad_contrato": "M", "descripcion_linea": "TUBO 125", "codigo_externo": "X1",
                        "producto_sigrid": "MAT", "bloqueada": True})
    fila = aplicar_edicion(_fila(), edicion)
    assert [fila[c] for c in ("unidad_contrato", "descripcion_linea", "codigo_externo",
                              "producto_sigrid", "bloqueada")] == ["M", "TUBO 125", "X1", "MAT", True]


def test_f106_r25_el_origen_no_lo_aplica_comun():
    edicion = _editada({"origen"}, {"matched_contrato_line_id": None, "derived_contrato_line_id": 640})
    fila = aplicar_edicion(_fila(), edicion)
    assert (fila["matched_contrato_line_id"], fila["derived_contrato_line_id"]) == (504, None)


def test_f106_r25_no_toca_la_fila_de_entrada():
    edicion = _editada({"cantidad"}, {"cantidad_convertida": 48.0})
    nueva = _fila()
    aplicar_edicion(nueva, edicion)
    assert nueva == _fila()


def test_f106_r25_fila_entera_conserva_su_marca():
    edicion = _editada(set(), {}, fila_entera=True)
    fila = aplicar_edicion(_fila(), edicion)
    assert _json(fila["edicion_manual_json"])["fila_entera"] is True


# =================================================================== #
# R22 · es_fila_manual en comun
# =================================================================== #
_LIMPIA = {"line_kind": "from_albaran", "bloqueada": False, "derivada_origen": None,
           "precio_unitario_agreement": "agree", "partida_action": "existing_matched"}


@pytest.mark.parametrize(("cambio", "esperado"), [
    ({}, False),
    ({"line_kind": "manual"}, True),
    ({"line_kind": "reparto"}, True),
    ({"bloqueada": True}, True),
    ({"derivada_origen": "manual_override"}, True),
    ({"precio_unitario_agreement": "manual"}, True),
    ({"partida_action": "almacen_elegido"}, True),
    ({"edicion_manual_json": '{"v": 1, "campos": {}, "calculado": {}, "fila_entera": false}'}, True),
    ({"edicion_manual_json": "{roto"}, False),
    ({"edicion_manual_json": None}, False),
])
def test_f106_r22_es_fila_manual(cambio, esperado):
    assert es_fila_manual(**{**_LIMPIA, **cambio}) is esperado


def test_f106_r22_sv4_la_reexporta():
    import ruesma_comun.edicion_manual as comun

    assert comun.es_fila_manual.__module__ == "ruesma_comun.edicion_manual"
