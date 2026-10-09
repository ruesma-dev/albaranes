# tests/test_f053_comparador.py
"""F-053 · T6 · ``comparador_previa.comparar`` (R17 y R15).

Lo que la previa no devuelve tal cual se pidió va a ``revisar`` (R17): importe
fuera de tolerancia, líneas que faltan o sobran, partida distinta (también
nula frente a no nula) y avisos bloqueantes por ``codigo``. En ``idempotente``
solo cuenta ``registrado_distinto`` (R15, H18). Puro: sin red.
"""
from __future__ import annotations

import pytest

from domain.models.alta_models import (
    LineaPeticion,
    Motivo,
    PeticionAlbaran,
    RespuestaAlta,
)
from domain.services.comparador_previa import comparar

BLOQUEANTES = frozenset({"producto_sin_historico"})
TOL = 0.05


def _peticion(*lineas: LineaPeticion) -> PeticionAlbaran:
    return PeticionAlbaran(
        cod_obra="0404", cif_proveedor="B00000000", cod_contrato=None,
        referencia_externa="ALB-d", su_referencia="1", usu="U", fecha_albaran=20261001,
        empide=None, lineas=lineas,
    )


PETICION = _peticion(
    LineaPeticion(referencia_linea="1", cantidad=6.0, precio=68.4, ctrpro_ide=7, partida="03.02.01"),
    LineaPeticion(referencia_linea="2", cantidad=-2.0, precio=9.0, producto="MA9999",
                  descripcion="D", unidad="UD"),
)
IMPORTES = {"1": 410.4, "2": -18.0}


def _linea(ref: str, total: float, partida: str | None, avisos=()) -> dict:
    return {"referencia_linea": ref, "total": total, "partida": partida, "avisos": list(avisos)}


def _respuesta(*lineas: dict, estado: str = "previsto", avisos=()) -> RespuestaAlta:
    return RespuestaAlta(estado=estado, con_ide=9, cod="AC26/1", avisos=tuple(avisos),
                         lineas=tuple(lineas), totales={})


def _ok(**cambios) -> list[dict]:
    lineas = {"1": _linea("1", 410.4, "03.02.01"), "2": _linea("2", -18.0, None)}
    lineas.update(cambios)
    return [l for l in lineas.values() if l is not None]


def _comparar(respuesta: RespuestaAlta) -> list[Motivo]:
    return comparar(PETICION, respuesta, IMPORTES, TOL, BLOQUEANTES)


def test_f053_r17_previa_identica_sin_motivos():
    assert _comparar(_respuesta(*_ok())) == []


@pytest.mark.parametrize(("total", "motivo"), [
    (410.45, False), (410.35, False), (410.46, True), (410.34, True), (0.0, True),
])
def test_f053_r17_importe_distinto_en_el_borde_de_la_tolerancia(total, motivo):
    motivos = _comparar(_respuesta(*_ok(**{"1": _linea("1", total, "03.02.01")})))
    if motivo:
        assert [(m.codigo, m.referencia_linea) for m in motivos] == [("importe_distinto", "1")]
    else:
        assert motivos == []


def test_f053_r17_importe_distinto_en_negativas():
    motivos = _comparar(_respuesta(*_ok(**{"2": _linea("2", -18.10, None)})))
    assert [(m.codigo, m.referencia_linea) for m in motivos] == [("importe_distinto", "2")]
    assert _comparar(_respuesta(*_ok(**{"2": _linea("2", -17.95, None)}))) == []


def test_f053_r17_linea_sin_total_es_importe_distinto():
    linea = {"referencia_linea": "1", "partida": "03.02.01", "avisos": []}
    motivos = _comparar(_respuesta(*_ok(**{"1": linea})))
    assert [m.codigo for m in motivos] == ["importe_distinto"]


def test_f053_r17_lineas_distintas_falta_y_sobra():
    falta = _comparar(_respuesta(*_ok(**{"2": None})))
    assert [(m.codigo, m.referencia_linea) for m in falta] == [("lineas_distintas", "2")]
    sobra = _comparar(_respuesta(*_ok(), _linea("99", 1.0, None)))
    assert [(m.codigo, m.referencia_linea) for m in sobra] == [("lineas_distintas", "99")]


@pytest.mark.parametrize(("ref", "partida_previa"), [
    ("1", "03.02.02"),   # cambiada
    ("1", None),         # pedida con partida, vuelve sin ella
    ("1", ""),           # vacía = sin partida
    ("2", "03.04.02"),   # pedida sin partida, vuelve con ella
])
def test_f053_r17_partida_distinta(ref, partida_previa):
    total = IMPORTES[ref]
    motivos = _comparar(_respuesta(*_ok(**{ref: _linea(ref, total, partida_previa)})))
    assert [(m.codigo, m.referencia_linea) for m in motivos] == [("partida_distinta", ref)]


def test_f053_r17_sin_partida_que_vuelve_vacia_o_nula_no_es_distinta():
    for vacia in (None, "", "  "):
        assert _comparar(_respuesta(*_ok(**{"2": _linea("2", -18.0, vacia)}))) == []


def test_f053_r17_partida_recortada_no_es_distinta():
    assert _comparar(_respuesta(*_ok(**{"1": _linea("1", 410.4, " 03.02.01 ")}))) == []


def test_f053_r17_aviso_bloqueante_de_cabecera_y_de_linea():
    aviso = {"codigo": "producto_sin_historico", "mensaje": "m"}
    cabecera = _comparar(_respuesta(*_ok(), avisos=[aviso]))
    assert [(m.codigo, m.referencia_linea) for m in cabecera] == [("aviso_bloqueante", None)]
    linea = _comparar(_respuesta(*_ok(**{"2": _linea("2", -18.0, None, [aviso])})))
    assert [(m.codigo, m.referencia_linea) for m in linea] == [("aviso_bloqueante", "2")]
    assert linea[0].detalle.startswith("producto_sin_historico")


@pytest.mark.parametrize("codigo", [
    "cod_provisional", "partida_distinta_del_contrato", "sin_partida_en_linea_con_partida",
    "precio_distinto_del_contrato", "supera_pendiente", "servido_negativo",
    "stock_negativo", "iva_de_otro_proveedor",
])
def test_f053_r17_avisos_informativos_no_bloquean(codigo):
    aviso = {"codigo": codigo, "mensaje": "m"}
    assert _comparar(_respuesta(*_ok(**{"1": _linea("1", 410.4, "03.02.01", [aviso])}),
                                avisos=[aviso])) == []


def test_f053_r17_avisos_bloqueantes_configurables():
    aviso = {"codigo": "stock_negativo", "mensaje": "m"}
    respuesta = _respuesta(*_ok(**{"2": _linea("2", -18.0, None, [aviso])}))
    assert comparar(PETICION, respuesta, IMPORTES, TOL, frozenset({"stock_negativo"})) != []
    assert comparar(PETICION, respuesta, IMPORTES, TOL, frozenset()) == []


def test_f053_r17_varios_motivos_a_la_vez():
    motivos = _comparar(_respuesta(
        _linea("1", 500.0, "99.99"),
        avisos=[{"codigo": "producto_sin_historico", "mensaje": "m"}],
    ))
    assert sorted(m.codigo for m in motivos) == [
        "aviso_bloqueante", "importe_distinto", "lineas_distintas", "partida_distinta",
    ]


# ------------------------------------------------------------------ #
# R15 · idempotente: solo registrado_distinto
# ------------------------------------------------------------------ #
def test_f053_r15_distinto_idempotente_igual_sin_motivos():
    assert _comparar(_respuesta(*_ok(), estado="idempotente")) == []


def test_f053_r15_distinto_idempotente_con_otro_total():
    respuesta = _respuesta(*_ok(**{"1": _linea("1", 400.0, "03.02.01")}), estado="idempotente")
    motivos = _comparar(respuesta)
    assert [(m.codigo, m.referencia_linea) for m in motivos] == [("registrado_distinto", "1")]


def test_f053_r15_distinto_idempotente_ignora_partida_y_avisos():
    aviso = {"codigo": "producto_sin_historico", "mensaje": "m"}
    respuesta = _respuesta(*_ok(**{"1": _linea("1", 410.4, "OTRA")}), estado="idempotente",
                           avisos=[aviso])
    assert _comparar(respuesta) == []


def test_f053_r15_distinto_idempotente_con_lineas_que_faltan_o_sobran():
    falta = _comparar(_respuesta(*_ok(**{"2": None}), estado="idempotente"))
    assert [(m.codigo, m.referencia_linea) for m in falta] == [("registrado_distinto", "2")]
    sobra = _comparar(_respuesta(*_ok(), _linea("7", 3.0, None), estado="idempotente"))
    assert [(m.codigo, m.referencia_linea) for m in sobra] == [("registrado_distinto", "7")]
