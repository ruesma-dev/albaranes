# tests/test_f065_f1_bloqueo.py
"""F-065 · fase 1 · R13–R17: guardar una fila la bloquea.

«Guardar» en una fila aplica lo cambiado y la marca ``bloqueada`` en la misma
transacción (también si no cambió nada); una fila bloqueada no se edita, ni se
reapunta, ni pasa a almacén, ni cambia de producto, ni se borra hasta que se
desbloquea (409 «Línea guardada: desbloquéala para editarla»); los masivos se
la saltan y dicen cuántas. La columna ``bloqueada`` la pone sv6 (dueño del
esquema de valoración) y sv4 la añade de forma defensiva (R17).

Repositorio y servicio reales sobre SQLite (``f065_bbdd``) y plantilla real.
"""
from __future__ import annotations

import json
import re

import pytest
from f053_sv4_bbdd import foto
from f065_bbdd import DOC, construir, ejecutar, fila, filas, repositorio
from sqlalchemy import text
from sqlalchemy.orm import Session

AVISO_BLOQUEADA = "Línea guardada: desbloquéala para editarla"


def _bloquear_en_bbdd(motor, *vids):
    for vid in vids:
        ejecutar(motor, "UPDATE albaran_line_valuations SET bloqueada = 1 WHERE id = :v", v=vid)


# =================================================================== #
# R13 · guardar = bloquear
# =================================================================== #
def test_f065_r13_guardar_aplica_y_bloquea_en_la_misma_transaccion():
    motor = construir()

    assert repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"cantidad": 6.0}, bloquear=True)

    f = fila(motor, 11)
    assert f["bloqueada"] in (1, True)
    assert f["cantidad_convertida"] == 6.0


def test_f065_r13_guardar_sin_cambios_tambien_bloquea_y_no_toca_lo_valorado():
    motor = construir()
    antes = fila(motor, 12)

    repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=12, campos={}, bloquear=True)

    despues = fila(motor, 12)
    assert despues["bloqueada"] in (1, True)
    assert {k: v for k, v in despues.items() if k != "bloqueada"} == {
        k: v for k, v in antes.items() if k != "bloqueada"}


def test_f065_r13_editar_sin_bloquear_no_bloquea():
    motor = construir()

    repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"cantidad": 6.0})

    assert fila(motor, 11)["bloqueada"] in (0, False)


def test_f065_r13_bloquear_linea_y_desbloquear_linea():
    motor = construir()
    repo = repositorio(motor)

    assert repo.bloquear_linea(document_id=DOC, valuation_line_id=11) is True
    assert fila(motor, 11)["bloqueada"] in (1, True)
    assert repo.desbloquear_linea(document_id=DOC, valuation_line_id=11) is True
    assert fila(motor, 11)["bloqueada"] in (0, False)


@pytest.mark.parametrize("metodo", ["bloquear_linea", "desbloquear_linea"])
def test_f065_r13_bloquear_una_linea_ajena_no_hace_nada(metodo):
    motor = construir()
    antes = foto(motor)

    assert getattr(repositorio(motor), metodo)(document_id=DOC, valuation_line_id=21) is False

    assert foto(motor) == antes


# =================================================================== #
# R14 · una fila bloqueada no se toca; los masivos se la saltan
# =================================================================== #
EN_LA_FILA = {
    "editar": lambda r: r.update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"cantidad": 1.0}),
    "guardar_otra_vez": lambda r: r.update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={}, bloquear=True),
    "reapuntar": lambda r: r.set_line_conciliacion(
        document_id=DOC, valuation_line_id=11, mode="nueva"),
    "almacen": lambda r: r.asignar_almacen(document_id=DOC, valuation_line_ids=[11]),
    "producto": lambda r: r.guardar_producto_sigrid(
        document_id=DOC, valuation_line_id=11, producto="MA9999"),
    "borrar": lambda r: r.remove_line_valuation(document_id=DOC, valuation_line_id=11),
}


@pytest.mark.parametrize("operacion", sorted(EN_LA_FILA))
def test_f065_r14_tocar_una_fila_bloqueada_responde_409_sin_cambios(operacion):
    from domain.models.review_models import LineaBloqueadaError

    motor = construir()
    _bloquear_en_bbdd(motor, 11)
    antes = foto(motor)

    with pytest.raises(LineaBloqueadaError) as error:
        EN_LA_FILA[operacion](repositorio(motor))

    assert error.value.document_id == DOC and error.value.valuation_line_id == 11
    assert error.value.aviso == AVISO_BLOQUEADA == str(error.value)
    assert foto(motor) == antes


def test_f065_r14_otra_fila_del_mismo_albaran_si_se_edita():
    motor = construir()
    _bloquear_en_bbdd(motor, 11)

    assert repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=12, campos={"cantidad": 7.0})


def test_f065_r14_almacen_a_todas_se_salta_las_bloqueadas():
    motor = construir()
    _bloquear_en_bbdd(motor, 11)

    tocadas = repositorio(motor).asignar_almacen(document_id=DOC, valuation_line_ids=None)

    assert tocadas == [12, 13]
    assert fila(motor, 11)["codigo_partida_final"] == "01.01"


def test_f065_r14_el_servicio_dice_cuantas_se_salto():
    from application.services.review_service import ReviewService

    motor = construir()
    _bloquear_en_bbdd(motor, 11, 12)

    resultado = ReviewService(repositorio(motor), "ana").asignar_almacen_todas_con_saltos(
        document_id=DOC)

    assert (resultado.tocadas, resultado.saltadas) == (1, 2)


def test_f065_r14_el_portal_dice_cuantas_se_salto(monkeypatch):
    from application.services.review_service import ResultadoAlmacenTodas

    class _Servicio:
        def initialize(self):
            return True

        def asignar_almacen_todas_con_saltos(self, *, document_id):
            return ResultadoAlmacenTodas(tocadas=2, saltadas=1)

    from test_f065_f1_cabecera import _cliente

    respuesta = _cliente(monkeypatch, _Servicio()).post(f"/api/documents/{DOC}/almacen-todas")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"ok": True, "document_id": DOC, "lineas": 2, "saltadas": 1}


def test_f065_r14_el_portal_responde_409_en_una_fila_bloqueada(monkeypatch):
    from domain.models.review_models import LineaBloqueadaError

    class _Servicio:
        def initialize(self):
            return True

        def update_line_conciliacion(self, **_):
            raise LineaBloqueadaError(DOC, 11)

    from test_f065_f1_cabecera import _cliente

    respuesta = _cliente(monkeypatch, _Servicio()).patch(
        f"/api/documents/{DOC}/lines/11/conciliacion/campos?bloquear=1", json={"cantidad": 2})

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == AVISO_BLOQUEADA


# =================================================================== #
# R15 · desbloquear (y bloquear) dejan su entrada de «Deshacer»
# =================================================================== #
def _historial(motor):
    with Session(motor) as s:
        return [dict(r) for r in s.execute(text(
            "SELECT action, description, payload FROM undo_log WHERE document_id = :d "
            "ORDER BY id"), {"d": DOC}).mappings().all()]


@pytest.mark.parametrize("metodo, antes, accion", [
    ("bloquear_linea", 0, "bloquear"), ("desbloquear_linea", 1, "desbloquear"),
])
def test_f065_r15_bloquear_y_desbloquear_dejan_entrada_de_deshacer(metodo, antes, accion):
    from application.services.review_service import ReviewService

    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET bloqueada = :b WHERE id = 11", b=antes)

    assert getattr(ReviewService(repositorio(motor), "ana"), metodo)(
        document_id=DOC, valuation_line_id=11) is True

    (entrada,) = _historial(motor)
    assert entrada["action"] == accion
    restaurar = json.loads(entrada["payload"])["restore"]
    assert [r["values"]["bloqueada"] for r in restaurar] == [antes]


def test_f065_r15_guardar_la_fila_deja_una_sola_entrada_que_la_desbloquea():
    from application.services.review_service import ReviewService

    motor = construir()

    ReviewService(repositorio(motor), "ana").update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"cantidad": 6.0}, bloquear=True)

    (entrada,) = _historial(motor)
    linea = next(r["values"] for r in json.loads(entrada["payload"])["restore"]
                 if r["table"] == "albaran_line_valuations")
    assert (linea["bloqueada"], linea["cantidad_convertida"]) in ((0, 8.0), (False, 8.0))


# =================================================================== #
# R16 · aprobar no exige filas bloqueadas
# =================================================================== #
def test_f065_r16_se_aprueba_sin_ninguna_fila_bloqueada():
    motor = construir()

    assert repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")
    assert all(f["bloqueada"] in (0, False) for f in filas(motor))


# =================================================================== #
# R17 · la columna (DDL defensivo de sv4) y la ficha
# =================================================================== #
DDL = ("ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS bloqueada "
       "BOOLEAN NOT NULL DEFAULT FALSE")


def test_f065_r17_ddl_sv4_la_anade_de_forma_defensiva():
    from infrastructure.database.review_repository import AlbaranReviewRepository

    assert DDL in AlbaranReviewRepository._review_schema_statements()


def test_f065_r17_ddl_la_ficha_lee_bloqueada():
    motor = construir()
    _bloquear_en_bbdd(motor, 11)
    repo = repositorio(motor)

    with Session(motor) as s:
        valoracion = repo._load_valuation_in_session(session=s, document_id=DOC)

    assert valoracion.lines_by_valuation_line_id[11].bloqueada is True
    assert valoracion.lines_by_valuation_line_id[12].bloqueada is False


def test_f065_r17_plantilla_fila_bloqueada_en_solo_lectura_con_desbloquear(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(bloqueada=True)], display=[fila_detalle()],
    ))

    fila_html = re.search(r'<tr class="conciliacion-row.*?</tr>', html, re.DOTALL).group(0)
    assert "js-cedit" not in fila_html
    assert "concilia-editable" not in fila_html
    assert 'data-bloqueada="1"' in fila_html
    assert re.search(r'<button[^>]*js-desbloquear[^>]*data-valuation-line-id="900"', fila_html)
    assert "Desbloquear" in fila_html


def test_f065_r17_plantilla_fila_sin_bloquear_editable_sin_desbloquear(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()], display=[fila_detalle()],
    ))

    fila_html = re.search(r'<tr class="conciliacion-row.*?</tr>', html, re.DOTALL).group(0)
    assert "js-cedit" in fila_html and "js-desbloquear" not in fila_html


def test_f065_r17_plantilla_aprobado_no_ofrece_desbloquear(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    doc = documento_detalle(lineas_valoracion=[linea_valorada(bloqueada=True)],
                            display=[fila_detalle()])
    html = render_detalle(doc.model_copy(update={"approved": True}))

    assert "js-desbloquear" not in html


def test_f065_r14_el_resultado_de_almacen_a_todas_no_se_modifica():
    """Inmutable, como ``ResultadoBorradoMultiple`` (mutación, campaña 1)."""
    import dataclasses

    from application.services.review_service import ResultadoAlmacenTodas

    resultado = ResultadoAlmacenTodas(tocadas=1, saltadas=2)
    with pytest.raises(dataclasses.FrozenInstanceError):
        resultado.saltadas = 0  # type: ignore[misc]


def test_f065_r13_el_servicio_sin_bloquear_no_bloquea():
    """Por defecto, editar una fila no la bloquea: solo «Guardar» (R13)."""
    from application.services.review_service import ReviewService

    motor = construir()

    assert ReviewService(repositorio(motor), "ana").update_line_conciliacion(
        document_id=DOC, valuation_line_id=11, campos={"cantidad": 6.0})

    assert fila(motor, 11)["bloqueada"] in (0, False)
    assert fila(motor, 11)["cantidad_convertida"] == 6.0


@pytest.mark.parametrize("ruta, bloquear", [
    ("conciliacion/campos", False), ("conciliacion/campos?bloquear=1", True),
])
def test_f065_r13_el_patch_solo_bloquea_si_se_pide(monkeypatch, ruta, bloquear):
    class _Servicio:
        def __init__(self):
            self.llamadas = []

        def initialize(self):
            return True

        def update_line_conciliacion(self, **kwargs):
            self.llamadas.append(kwargs)
            return True

    from test_f065_f1_cabecera import _cliente

    servicio = _Servicio()

    respuesta = _cliente(monkeypatch, servicio).patch(
        f"/api/documents/{DOC}/lines/11/{ruta}", json={"cantidad": "6"})

    assert respuesta.status_code == 200
    assert servicio.llamadas == [{"document_id": DOC, "valuation_line_id": 11,
                                  "campos": {"cantidad": 6.0}, "bloquear": bloquear}]
