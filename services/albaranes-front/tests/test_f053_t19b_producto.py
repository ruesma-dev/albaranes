# tests/test_f053_t19b_producto.py
"""F-053 · T19b · producto Sigrid de las líneas sin vincular, en sv4 (R40–R43).

- R41: el administrativo elige un producto admitido (o «por defecto» =
  ``NULL``) en una sin vincular: se guarda en
  ``albaran_line_valuations.producto_sigrid`` con su entrada de deshacer. Si
  la línea no es del documento, es vinculada o el código no es admitido, no
  cambia nada (el portal responde 400). Con alta bloqueante, tampoco (R25).
- R40, R43: la lectura da a cada línea su producto efectivo: vinculada, el de
  su línea de contrato (sin selector); sin vincular a registrar, el elegido o
  el por defecto según la familia (``producto_efectivo`` de comun), con
  selector; sin importe, sin selector.

Repositorio real sobre SQLite (``f053_sv4_bbdd``). Sin red.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from domain.models.alta_sigrid_models import AlbaranBloqueadoError, ConfigAltaSigrid
from f053_sv4_bbdd import DOC, DOC_AJENO, construir, foto, poner_alta, repositorio

ACTIVA = ConfigAltaSigrid(desde=datetime(2026, 10, 1, tzinfo=UTC))
CLASIFICACION = {"familia": "generico", "mixto": False}


def _producto(motor, lv_id):
    with Session(motor) as s:
        return s.execute(
            text("SELECT producto_sigrid FROM albaran_line_valuations WHERE id = :i"),
            {"i": lv_id},
        ).scalar()


def _servicio(motor, config=ACTIVA):
    from application.services.review_service import ReviewService

    return ReviewService(repositorio(motor), "revisor", None, config)


# ------------------------------------------------------------------ #
# Repositorio: guardar_producto_sigrid
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("producto", ["XA9999", None])
def test_f053_r41_repositorio_guarda_en_una_sin_vincular(producto):
    motor = construir(aprobado=False)
    assert repositorio(motor).guardar_producto_sigrid(
        document_id=DOC, valuation_line_id=12, producto=producto) == "guardado"
    assert _producto(motor, 12) == producto


@pytest.mark.parametrize("lv_id, motivo", [
    (11, "vinculada"),      # casa con la 501 del contrato CT/1, con sigrid_ide
    (21, "linea_ajena"),    # es de DOC_AJENO
    (999, "linea_ajena"),   # no existe
])
def test_f053_r41_repositorio_rechaza_sin_cambiar_nada(lv_id, motivo):
    motor = construir()
    antes = foto(motor)
    assert repositorio(motor).guardar_producto_sigrid(
        document_id=DOC, valuation_line_id=lv_id, producto="XA9999") == motivo
    assert foto(motor) == antes


@pytest.mark.parametrize("estado", ["en_curso", "incierto", "registrado"])
def test_f053_r41_repositorio_con_alta_bloqueante_no_cambia_nada(estado):
    motor = construir(aprobado=True)
    poner_alta(motor, estado)
    antes = foto(motor)
    with pytest.raises(AlbaranBloqueadoError):
        repositorio(motor).guardar_producto_sigrid(
            document_id=DOC, valuation_line_id=12, producto="XA9999")
    assert foto(motor) == antes


def test_f053_r41_repositorio_llama_al_cerrojo():
    import inspect

    from infrastructure.database.review_repository import AlbaranReviewRepository

    fuente = inspect.getsource(AlbaranReviewRepository.guardar_producto_sigrid)
    assert "self._exigir_desbloqueado(session, document_id)" in fuente


def test_f053_r41_una_linea_de_otro_contrato_es_sin_vincular():
    """La vinculada exige el contrato de la valoración (comun)."""
    motor = construir()
    with Session(motor) as s:
        s.execute(text("UPDATE albaran_valuations SET contrato_codigo = 'CT/2' WHERE id = 'f053-val-1'"))
        s.commit()
    assert repositorio(motor).guardar_producto_sigrid(
        document_id=DOC, valuation_line_id=11, producto="QA9999") == "guardado"


# ------------------------------------------------------------------ #
# Servicio: elegir_producto_sigrid (validación y deshacer)
# ------------------------------------------------------------------ #
def test_f053_r41_servicio_guarda_y_deja_deshacer():
    motor = construir()
    servicio = _servicio(motor)

    assert servicio.elegir_producto_sigrid(
        document_id=DOC, valuation_line_id=12, producto=" XA9999 ") == "guardado"

    assert _producto(motor, 12) == "XA9999"
    with Session(motor) as s:
        entrada = s.execute(text(
            "SELECT action, document_id, payload FROM undo_log")).mappings().one()
    assert entrada["action"] == "producto" and entrada["document_id"] == DOC
    assert '"producto_sigrid": null' in entrada["payload"]


@pytest.mark.parametrize("producto", [None, ""])
def test_f053_r41_servicio_por_defecto_es_null(producto):
    motor = construir()
    servicio = _servicio(motor)
    servicio.elegir_producto_sigrid(document_id=DOC, valuation_line_id=12, producto="QA9999")
    assert servicio.elegir_producto_sigrid(
        document_id=DOC, valuation_line_id=12, producto=producto) == "guardado"
    assert _producto(motor, 12) is None


@pytest.mark.parametrize("producto", ["ZZ0001", "ma9999", "MA9999X"])
def test_f053_r41_servicio_producto_no_admitido_no_cambia_nada(producto):
    motor = construir()
    antes = foto(motor)
    assert _servicio(motor).elegir_producto_sigrid(
        document_id=DOC, valuation_line_id=12, producto=producto) == "no_admitido"
    assert foto(motor) == antes


@pytest.mark.parametrize("lv_id, motivo", [(11, "vinculada"), (21, "linea_ajena")])
def test_f053_r41_servicio_rechazos_sin_entrada_de_deshacer(lv_id, motivo):
    motor = construir()
    antes = foto(motor)
    assert _servicio(motor).elegir_producto_sigrid(
        document_id=DOC, valuation_line_id=lv_id, producto="XA9999") == motivo
    assert foto(motor) == antes


def test_f053_r41_servicio_con_desde_vacia_no_cambia_nada():
    motor = construir()
    antes = foto(motor)
    assert _servicio(motor, ConfigAltaSigrid()).elegir_producto_sigrid(
        document_id=DOC, valuation_line_id=12, producto="XA9999") == "apagada"
    assert foto(motor) == antes


def test_f053_r41_el_deshacer_restaura_el_producto():
    motor = construir()
    servicio = _servicio(motor)
    servicio.elegir_producto_sigrid(document_id=DOC, valuation_line_id=12, producto="QA9999")
    servicio.elegir_producto_sigrid(document_id=DOC, valuation_line_id=12, producto="XA9999")
    with Session(motor) as s:
        payload = s.execute(text(
            "SELECT payload FROM undo_log ORDER BY id DESC LIMIT 1")).scalar()
    import json

    repo = repositorio(motor)
    with Session(motor) as s:
        for instantanea in json.loads(payload)["restore"]:
            repo._undo_apply_restore(s, instantanea)
        s.commit()
    assert _producto(motor, 12) == "QA9999"


# ------------------------------------------------------------------ #
# Lectura: producto efectivo por línea (R40, R43)
# ------------------------------------------------------------------ #
def test_f053_r41_lectura_de_productos_por_linea():
    motor = construir()
    with Session(motor) as s:
        s.execute(text("UPDATE albaran_line_valuations SET producto_sigrid = 'MA9999' WHERE id = 11"))
        s.execute(text("UPDATE albaran_line_valuations SET producto_sigrid = 'XA9999' WHERE id = 14"))
        s.commit()

    productos = _servicio(motor).productos_sigrid(DOC, CLASIFICACION)

    assert set(productos) == {11, 12, 13, 14}
    vinculada = productos[11]
    assert vinculada.vinculada and not vinculada.seleccionable
    assert vinculada.codigo == "HA25" and vinculada.por_defecto is False  # R43
    maquinaria = productos[12]
    assert not maquinaria.vinculada and maquinaria.seleccionable
    assert (maquinaria.codigo, maquinaria.por_defecto, maquinaria.elegido) == ("QA9999", True, None)
    assert maquinaria.nombre == "Alquiler de maquinaria"
    sin_importe = productos[13]
    assert not sin_importe.a_registrar and not sin_importe.seleccionable
    elegida = productos[14]
    assert (elegida.codigo, elegida.por_defecto, elegida.elegido) == ("XA9999", False, "XA9999")


def test_f053_r41_lectura_familia_del_documento_si_la_linea_no_la_trae():
    motor = construir()
    productos = _servicio(motor).productos_sigrid(
        DOC, {"familia": "alquiler_maquinaria", "mixto": False})
    assert productos[14].codigo == "QA9999"  # manual, sin línea del albarán
    productos = _servicio(motor).productos_sigrid(
        DOC, {"familia": "alquiler_maquinaria", "mixto": True})
    assert productos[14].codigo == "MA9999"  # mixto: solo manda la de la línea


def test_f053_r41_lectura_con_desde_vacia_no_lee_nada():
    motor = construir()
    assert _servicio(motor, ConfigAltaSigrid()).productos_sigrid(DOC, CLASIFICACION) == {}


def test_f053_r41_lectura_de_documento_ajeno_solo_trae_las_suyas():
    motor = construir()
    assert set(_servicio(motor).productos_sigrid(DOC_AJENO, CLASIFICACION)) == {21}
