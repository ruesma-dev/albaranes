# tests/test_f053_comun.py
"""F-053 · piezas de ``ruesma_comun`` que comparten sv4 y sv9 (T1).

- R32: ``MensajeFeedback.accion`` (``alta`` | ``verificar_anulacion``,
  defecto ``alta``), compatible con los mensajes de antes.
- R38: «valorado» (``ruesma_comun.valoracion.esta_valorado``) y producto
  efectivo de una línea sin vincular (``ruesma_comun.alta_sigrid``).
- R44: el mapeo ``ALTA_SIGRID_PRODUCTO_POR_DEFECTO`` mal formado no se acepta.

Sin red ni BBDD: funciones puras y serialización.
"""
from __future__ import annotations

import json

import pytest

from ruesma_comun import alta_sigrid as a
from ruesma_comun.colas.mensajes import (
    MensajeFeedback,
    MensajeInvalidoError,
    desde_texto,
)
from ruesma_comun.valoracion import esta_valorado

MAPEO = {"alquiler_maquinaria": "QA9999", "medios_auxiliares": "XA9999", "*": "MA9999"}


# ------------------------------------------------------------------ #
# R32 · MensajeFeedback.accion
# ------------------------------------------------------------------ #
def test_f053_r32_accion_por_defecto_es_alta():
    assert MensajeFeedback(document_id="d1").accion == "alta"


def test_f053_r32_mensaje_viejo_sin_accion_se_lee_como_alta():
    viejo = json.dumps({"tipo": "feedback", "document_id": "d1", "approved_by": "ana"})
    leido = desde_texto(viejo, tipo_esperado="feedback")
    assert isinstance(leido, MensajeFeedback)
    assert leido.accion == "alta" and leido.approved_by == "ana"


def test_f053_r32_verificar_anulacion_viaja_y_vuelve():
    mensaje = MensajeFeedback(document_id="d1", accion="verificar_anulacion")
    assert json.loads(mensaje.a_texto())["accion"] == "verificar_anulacion"
    leido = desde_texto(mensaje.a_texto(), tipo_esperado="feedback")
    assert leido.accion == "verificar_anulacion"


def test_f053_r32_accion_desconocida_es_mensaje_invalido():
    cuerpo = json.dumps({"tipo": "feedback", "document_id": "d1", "accion": "borrar"})
    with pytest.raises(MensajeInvalidoError):
        desde_texto(cuerpo, tipo_esperado="feedback")


def test_f053_r32_docstring_nombra_a_sv9_como_consumidor():
    assert "sv9" in (MensajeFeedback.__doc__ or "")


# ------------------------------------------------------------------ #
# R38 · esta_valorado
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("status", "importes", "esperado"),
    [
        ("ok", [10.0, 0.0, None], True),
        ("ok", [], True),
        ("manual", [10.0, 0.0], True),
        ("no_contract", [-3.5], True),
        ("manual", [10.0, None], False),
        ("no_contract", [0.0, 0.0], False),
        ("manual", [], False),
        ("no_contract", [None], False),
        ("partial", [10.0], False),
        ("failed", [10.0], False),
        (None, [10.0], False),
        ("", [10.0], False),
    ],
)
def test_f053_r38_esta_valorado(status, importes, esperado):
    assert esta_valorado(status, importes) is esperado


def test_f053_r38_esta_valorado_acepta_cualquier_iterable():
    assert esta_valorado("manual", (x for x in (1.0, 2.0))) is True


# ------------------------------------------------------------------ #
# R44 · leer_mapeo
# ------------------------------------------------------------------ #
def test_f053_r44_mapeo_valido():
    assert a.leer_mapeo(json.dumps(MAPEO)) == MAPEO


def test_f053_r44_mapeo_por_defecto_es_el_del_diseno():
    assert a.MAPEO_PRODUCTO_POR_DEFECTO == MAPEO
    assert a.leer_mapeo(a.MAPEO_PRODUCTO_POR_DEFECTO_TEXTO) == MAPEO


@pytest.mark.parametrize(
    "texto",
    [
        "{no es json",
        "",
        "[]",
        '"MA9999"',
        "null",
        '{"alquiler_maquinaria": "QA9999"}',
        '{"*": 7}',
        '{"*": "MA9999", "alquiler_maquinaria": null}',
        '{"*": "MA9999", "alquiler_maquinaria": ["QA9999"]}',
        '{"*": "   "}',
    ],
)
def test_f053_r44_mapeo_invalido_lanza_value_error(texto):
    with pytest.raises(ValueError):
        a.leer_mapeo(texto)


def test_f053_r44_mapeo_none_lanza_value_error():
    with pytest.raises(ValueError):
        a.leer_mapeo(None)  # type: ignore[arg-type]


# ------------------------------------------------------------------ #
# R38 · productos_admitidos, producto_efectivo y nombres
# ------------------------------------------------------------------ #
def test_f053_r38_productos_admitidos_son_los_valores_del_mapeo():
    assert a.productos_admitidos(MAPEO) == frozenset({"QA9999", "XA9999", "MA9999"})
    assert a.productos_admitidos({"*": "MA9999", "x": "MA9999"}) == frozenset({"MA9999"})


def test_f053_r38_producto_elegido_gana_siempre():
    assert a.producto_efectivo("XA9999", "alquiler_maquinaria", None, MAPEO) == "XA9999"


def test_f053_r38_elegido_vacio_cuenta_como_por_defecto():
    assert a.producto_efectivo("  ", "alquiler_maquinaria", None, MAPEO) == "QA9999"


def test_f053_r38_por_familia_de_la_linea():
    assert a.producto_efectivo(None, "alquiler_maquinaria", None, MAPEO) == "QA9999"
    assert a.producto_efectivo(None, "hormigon", None, MAPEO) == "MA9999"


def test_f053_r38_por_familia_del_documento():
    clasif = {"familia": "alquiler_maquinaria", "mixto": False}
    assert a.producto_efectivo(None, None, clasif, MAPEO) == "QA9999"


def test_f053_r38_documento_mixto_no_hereda():
    clasif = {"familia": "alquiler_maquinaria", "mixto": True}
    assert a.producto_efectivo(None, None, clasif, MAPEO) == "MA9999"
    # en un mixto manda la de la línea
    assert a.producto_efectivo(None, "alquiler_maquinaria", clasif, MAPEO) == "QA9999"


def test_f053_r38_linea_gana_al_documento():
    clasif = {"familia": "alquiler_maquinaria", "mixto": False}
    assert a.producto_efectivo(None, "otro", clasif, MAPEO) == "MA9999"


def test_f053_r38_sin_clasificacion_y_sin_familia_es_comodin():
    assert a.producto_efectivo(None, None, None, MAPEO) == "MA9999"


def test_f053_r38_familia_sin_clave_en_el_mapeo_es_comodin():
    assert a.producto_efectivo(None, "residuos", None, MAPEO) == "MA9999"
    assert a.producto_efectivo(None, "medios_auxiliares", None, {"*": "MA9999"}) == "MA9999"


def test_f053_r38_familia_medios_auxiliares_si_llega():
    # F-061 aún no la da de alta: cuando la IA la ponga, el mapeo ya la casa.
    assert a.producto_efectivo(None, "medios_auxiliares", None, MAPEO) == "XA9999"


def test_f053_r38_nombres_de_producto():
    assert a.NOMBRES_PRODUCTO == {
        "MA9999": "Suministro de materiales",
        "QA9999": "Alquiler de maquinaria",
        "XA9999": "Alquiler de medios auxiliares",
    }
    assert a.nombre_producto("QA9999") == "Alquiler de maquinaria"
    assert a.nombre_producto("ZZ0001") == "ZZ0001"


# ------------------------------------------------------------------ #
# R45 (D1) · estados bloqueantes del alta, compartidos por sv3, sv4 y sv9
# ------------------------------------------------------------------ #
def test_f053_r45_estados_bloqueantes_del_glosario():
    assert a.ESTADOS_ALTA_BLOQUEANTES == frozenset({"en_curso", "incierto", "registrado"})
