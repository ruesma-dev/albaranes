# tests/test_f106_edicion.py
"""F-106 fase B · sv4: cada vía que escribe una fila registra su edición.

- R20: PATCH (campos cambiados, con ``importe`` y el P despejado), «Origen ✎»,
  almacén y «almacén a todas», producto Sigrid, bloquear y desbloquear: la
  edición se escribe en la misma transacción; la primera vez, con ``calculado``.
- R21: las filas que crea sv4 nacen con ``fila_entera``; Dividir registra
  además la Q nueva de la original.
- R28: un PATCH sobre una fila que ya no existe es 409.
- R29: la ficha enseña «✋» con el detalle campo a campo.
- R30: «Volver a lo calculado» restaura, borra la edición y desbloquea, con
  deshacer; 409 en aprobado; una ``fila_entera`` no lo tiene. El aviso de
  revalorar dice que se conservan.

Repositorio real sobre SQLite (``f065_bbdd``). Sin red ni BBDD real.
"""
from __future__ import annotations

import pytest
from f065_bbdd import DOC, ejecutar, fila, repositorio
from test_f106_fila import FILA, _cliente, _patch, cecois

from ruesma_comun.edicion_manual import leer_edicion


def _json(motor, vid=FILA):
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    with Session(motor) as s:
        return s.execute(text("SELECT edicion_manual_json FROM albaran_line_valuations WHERE id = :v"),
                         {"v": vid}).scalar()


def _edicion(motor, vid=FILA):
    return leer_edicion(_json(motor, vid))


# =================================================================== #
# R20 · PATCH
# =================================================================== #
def test_f106_r20_patch_cantidad_guarda_campo_y_calculado():
    motor = cecois()
    _patch(motor, {"cantidad": 48.0})

    e = _edicion(motor)
    assert e.campos == {"cantidad": {"cantidad_albaran": 48.0, "cantidad_convertida": 48.0}}
    assert e.calculado["importe_calculado"] == 104.16
    assert e.calculado["precio_unitario_final"] == 11.2
    assert e.fila_entera is False


def test_f106_r20_patch_importe_guarda_el_importe_y_no_el_precio_despejado():
    motor = cecois(q=48.0, importe=499.97, source="calculated")
    _patch(motor, {"importe": 104.16})

    e = _edicion(motor)
    # El P despejado (2,333333 ≠ 11,20) es un precio cambiado: Contrato → Nueva
    # (R8), y sv6 tiene que recrear su derivada (R27).
    assert list(e.campos) == ["importe", "origen"]
    assert e.campos["importe"] == {"importe_calculado": 104.16}


def test_f106_r20_recalcular_precio_guarda_el_importe():
    motor = cecois(q=48.0)
    _patch(motor, cuadrar="precio")
    assert list(_edicion(motor).campos) == ["importe", "origen"]


def test_f106_r20_recalcular_importe_guarda_la_cantidad():
    """«Recalcular importe» es como cambiar Q (R9): queda la Q y sv6 rehace I."""
    motor = cecois(q=48.0)
    _patch(motor, cuadrar="importe")
    assert list(_edicion(motor).campos) == ["cantidad"]


def test_f106_r20_contrato_a_nueva_guarda_el_origen():
    motor = cecois()
    _patch(motor, {"precio_unitario": 12.0})

    e = _edicion(motor)
    assert e.campos["origen"] == {"tipo": "nueva"}
    assert e.campos["precio_unitario"] == {"precio_unitario_final": 12.0}


def test_f106_r20_guardar_bloquea_y_lo_registra():
    motor = cecois()
    repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, campos={"cantidad": 48.0}, bloquear=True)
    assert _edicion(motor).campos["bloqueada"] == {"bloqueada": True}


def test_f106_r20_guardar_sin_cambios_registra_solo_el_bloqueo():
    motor = cecois()
    repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, campos={}, bloquear=True)
    assert list(_edicion(motor).campos) == ["bloqueada"]


def test_f106_r20_patch_sin_nada_no_crea_edicion():
    motor = cecois()
    repositorio(motor).update_line_conciliacion(document_id=DOC, valuation_line_id=FILA, campos={})
    assert _json(motor) is None


def test_f106_r20_la_segunda_edicion_conserva_el_primer_calculado():
    motor = cecois()
    _patch(motor, {"cantidad": 48.0})
    _patch(motor, {"descuento": 10.0})

    e = _edicion(motor)
    assert list(e.campos) == ["cantidad", "descuento"]
    assert e.calculado["cantidad_convertida"] == 10.0


# =================================================================== #
# R20 · el resto de vías
# =================================================================== #
def test_f106_r20_bloquear_y_desbloquear():
    motor = cecois()
    repo = repositorio(motor)
    repo.bloquear_linea(document_id=DOC, valuation_line_id=FILA)
    assert _edicion(motor).campos == {"bloqueada": {"bloqueada": True}}
    repo.desbloquear_linea(document_id=DOC, valuation_line_id=FILA)
    assert _edicion(motor).campos == {"bloqueada": {"bloqueada": False}}


@pytest.mark.parametrize("todas", [False, True])
def test_f106_r20_almacen_y_almacen_a_todas(todas):
    motor = cecois()
    repositorio(motor).asignar_almacen(document_id=DOC, valuation_line_ids=None if todas else [FILA])
    assert _edicion(motor).campos["codigo_partida"] == {
        "codigo_partida_final": None, "partida_action": "almacen_elegido"}
    if todas:
        assert _edicion(motor, 11) is not None


def test_f106_r20_producto_sigrid():
    motor = cecois()
    ejecutar(motor, "UPDATE albaran_line_valuations SET matched_contrato_line_id = NULL WHERE id = :v", v=FILA)
    assert repositorio(motor).guardar_producto_sigrid(
        document_id=DOC, valuation_line_id=FILA, producto="MAT") == "guardado"
    assert _edicion(motor).campos["producto_sigrid"] == {"producto_sigrid": "MAT"}


def test_f106_r20_origen_a_nueva():
    motor = cecois()
    repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, mode="nueva", descripcion="TUBO", precio_unitario=9.0)
    assert _edicion(motor).campos["origen"] == {"tipo": "nueva"}


def test_f106_r20_origen_a_otra_linea_de_contrato():
    motor = cecois()
    repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=FILA, mode="contract_line", matched_contrato_line_id=501)
    assert _edicion(motor).campos["origen"] == {"tipo": "contrato", "linea": 501}


# =================================================================== #
# R21 · filas que crea sv4
# =================================================================== #
def _nuevas(motor, antes):
    from f065_bbdd import filas

    return [f for f in filas(motor) if f["id"] not in antes]


def _ids(motor):
    from f065_bbdd import filas

    return {f["id"] for f in filas(motor)}


def test_f106_r21_anadir_linea_nace_entera():
    motor = cecois()
    antes = _ids(motor)
    repositorio(motor).add_standalone_valuation_line(document_id=DOC)
    (nueva,) = _nuevas(motor, antes)
    assert leer_edicion(_json(motor, nueva["id"])).fila_entera is True


def test_f106_r21_traer_lineas_del_contrato_nacen_enteras():
    motor = cecois()
    antes = _ids(motor)
    repositorio(motor).add_valuation_lines_from_contrato(document_id=DOC, lineas=[(501, 2.0)])
    (nueva,) = _nuevas(motor, antes)
    assert leer_edicion(_json(motor, nueva["id"])).fila_entera is True


def test_f106_r21_mas_a_sigrid_nace_entera():
    from sqlalchemy import text
    from sqlalchemy.orm import Session

    motor = cecois()
    with Session(motor) as s:
        s.execute(text("INSERT INTO albaran_lines_merge (id, document_id, provider_origin, line_index, "
                       "concepto, cantidad, precio, precio_neto) VALUES (705, :d, 'merge', 5, 'CODO', "
                       "2, 3, 6)"), {"d": DOC})
        s.commit()
    antes = _ids(motor)
    assert repositorio(motor).add_conciliacion_for_merge_line(
        document_id=DOC, merge_line_id=705, mode="contract_line", matched_contrato_line_id=501)
    (nueva,) = _nuevas(motor, antes)
    assert leer_edicion(_json(motor, nueva["id"])).fila_entera is True


def test_f106_r21_dividir_partes_enteras_y_la_original_con_su_q():
    from domain.models.review_models import ParteDivision

    motor = cecois()
    antes = _ids(motor)
    hecha = repositorio(motor).dividir_linea(
        document_id=DOC, valuation_line_id=FILA,
        partes=[ParteDivision(cantidad=6.0, codigo_partida="01.04"),
                ParteDivision(cantidad=4.0, codigo_partida="01.04")])
    assert hecha is not None
    (parte,) = _nuevas(motor, antes)
    assert leer_edicion(_json(motor, parte["id"])).fila_entera is True
    original = _edicion(motor)
    assert original.campos["cantidad"]["cantidad_convertida"] == 6.0
    assert original.fila_entera is False


# =================================================================== #
# R28 · fila que ya no existe
# =================================================================== #
def test_f106_r28_patch_sobre_fila_desaparecida_es_409():
    from domain.models.review_models import ValoracionCambiadaError

    motor = cecois()
    with pytest.raises(ValoracionCambiadaError) as error:
        _patch(motor, {"cantidad": 2.0}, vid=99999)
    assert error.value.aviso == "La valoración ha cambiado: recarga la ficha"


def test_f106_r28_la_app_lo_da_como_409(monkeypatch):
    from domain.models.review_models import ValoracionCambiadaError
    from test_f106_fila import RUTA, _Servicio

    cliente = _cliente(monkeypatch, _Servicio(error=ValoracionCambiadaError(DOC)))
    r = cliente.patch(RUTA, json={"cantidad": 2})
    assert r.status_code == 409
    assert r.json()["detail"] == "La valoración ha cambiado: recarga la ficha"


# =================================================================== #
# R29 · «✋» en la ficha
# =================================================================== #
def _concilia(motor, vid=FILA):
    detalle = repositorio(motor).get_document_detail(DOC)
    return next(d for d in detalle.display_lines if d.valuation_line_id == vid).concilia


def test_f106_r29_la_vista_lleva_el_detalle_campo_a_campo():
    from domain.models.review_models import texto_edicion

    motor = cecois()
    _patch(motor, {"cantidad": 48.0, "descuento": 10.0})
    c = _concilia(motor)
    assert c.edicion_texto == texto_edicion(_edicion(motor))
    assert c.edicion_texto == "Cantidad: 48 (calculado 10)\nDescuento: 10 (calculado 7)"
    assert c.fila_entera is False


def test_f106_r29_texto_de_cada_campo():
    from domain.models.review_models import texto_edicion
    from ruesma_comun.edicion_manual import EdicionManual

    e = EdicionManual(
        campos={"precio_unitario": {"precio_unitario_final": 2.333333},
                "codigo_partida": {"codigo_partida_final": None, "partida_action": "almacen_elegido"},
                "unidad": {"unidad_contrato": "M"}, "bloqueada": {"bloqueada": True},
                "origen": {"tipo": "nueva"}},
        calculado={"precio_unitario_final": 11.2, "codigo_partida_final": "01.04", "unidad_contrato": "UD"},
    )
    assert texto_edicion(e) == (
        "Precio: 2,333333 (calculado 11,20)\nPartida: almacén (calculado 01.04)\n"
        "Unidad: M (calculado UD)\nGuardada\nOrigen: Nueva")


def test_f106_r29_texto_de_los_campos_del_importe_y_los_demas():
    from domain.models.review_models import texto_edicion
    from ruesma_comun.edicion_manual import EdicionManual

    e = EdicionManual(
        campos={"cantidad": {"cantidad_albaran": 48.0, "cantidad_convertida": None},
                "importe": {"importe_calculado": 1234.5},
                "descuento": {"descuento_albaran_aplicado": 12.5},
                "descripcion": {"descripcion_linea": "  "},
                "codigo_externo": {"codigo_externo": "X9"},
                "bloqueada": {"bloqueada": False},
                "origen": {"tipo": "contrato", "linea": 505}},
        calculado={"cantidad_albaran": 5.0, "cantidad_convertida": 10.0, "importe_calculado": None,
                   "descuento_albaran_aplicado": 7.0, "descripcion_linea": "TUBO PVC 110"},
    )
    # Cantidad: la convertida o, sin ella, la del albarán; sin valor, «—».
    assert texto_edicion(e).splitlines() == [
        "Cantidad: 48 (calculado 10)", "Importe: 1.234,50 (calculado —)",
        "Descuento: 12,5 (calculado 7)", "Descripción: — (calculado TUBO PVC 110)",
        "Código externo: X9 (calculado —)", "Desbloqueada", "Origen: línea 505"]


def test_f106_r29_fila_entera_es_anadida_a_mano():
    from domain.models.review_models import texto_edicion
    from ruesma_comun.edicion_manual import EdicionManual

    assert texto_edicion(EdicionManual(campos={}, calculado={}, fila_entera=True)) == "✋ añadida a mano"


def test_f106_r29_sin_edicion_nada():
    c = _concilia(cecois())
    assert (c.edicion_texto, c.fila_entera) == (None, False)


def test_f106_r29_plantilla_mano_y_boton(render_detalle, documento_detalle, linea_valorada, fila_detalle):
    import re

    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"edicion_texto": "Cantidad: 48 (calculado 10)"})],
    ))
    mano = re.search(r'<span[^>]*js-edicion-manual[^>]*>[^<]*</span>', html).group(0)
    assert ">✋<" in mano and 'title="Cantidad: 48 (calculado 10)"' in mano
    assert re.search(r'<button[^>]*js-volver-calculado[^>]*>', html)


def test_f106_r29_r30_plantilla_fila_entera_sin_boton(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"edicion_texto": "✋ añadida a mano", "fila_entera": True})],
    ))
    assert ">✋ añadida a mano<" in html
    assert "js-volver-calculado" not in html


# =================================================================== #
# R30 · Volver a lo calculado
# =================================================================== #
def test_f106_r30_restaura_borra_y_desbloquea():
    motor = cecois()
    repo = repositorio(motor)
    repo.update_line_conciliacion(document_id=DOC, valuation_line_id=FILA,
                                  campos={"cantidad": 48.0}, bloquear=True)

    assert repo.volver_a_calculado(document_id=DOC, valuation_line_id=FILA) is True

    f = fila(motor, FILA)
    assert (f["cantidad_convertida"], f["importe_calculado"]) == (10.0, 104.16)
    assert f["importe_source"] == "declared_albaran"
    assert _json(motor) is None and f["bloqueada"] in (0, False)


def test_f106_r30_nueva_vuelve_a_su_linea_de_contrato():
    motor = cecois()
    repo = repositorio(motor)
    _patch(motor, {"precio_unitario": 12.0})
    assert fila(motor, FILA)["matched_contrato_line_id"] is None

    repo.volver_a_calculado(document_id=DOC, valuation_line_id=FILA)

    f = fila(motor, FILA)
    assert (f["matched_contrato_line_id"], f["derived_contrato_line_id"]) == (504, None)
    assert f["precio_unitario_final"] == 11.2


def test_f106_r30_si_la_linea_ya_no_existe_se_queda_nueva():
    motor = cecois()
    _patch(motor, {"precio_unitario": 12.0})
    ejecutar(motor, "DELETE FROM albaran_contrato_lines_merge WHERE id = 504")

    repositorio(motor).volver_a_calculado(document_id=DOC, valuation_line_id=FILA)

    f = fila(motor, FILA)
    assert f["matched_contrato_line_id"] is None and f["derived_contrato_line_id"] is not None


def test_f106_r30_recalcula_el_total():
    from f065_bbdd import total

    motor = cecois()
    _patch(motor, {"cantidad": 48.0})
    repositorio(motor).volver_a_calculado(document_id=DOC, valuation_line_id=FILA)
    assert total(motor) == pytest.approx(2120 + 104.16)


def test_f106_r30_sin_edicion_o_fila_entera_no_hay_nada_que_restaurar():
    motor = cecois()
    repo = repositorio(motor)
    assert repo.volver_a_calculado(document_id=DOC, valuation_line_id=FILA) is False
    antes = _ids(motor)
    repo.add_standalone_valuation_line(document_id=DOC)
    (nueva,) = _nuevas(motor, antes)
    assert repo.volver_a_calculado(document_id=DOC, valuation_line_id=nueva["id"]) is False


def test_f106_r30_aprobado_es_409():
    from domain.models.review_models import AlbaranAprobadoError

    motor = cecois()
    _patch(motor, {"cantidad": 48.0})
    ejecutar(motor, "UPDATE albaran_documents_merge SET approved = 1 WHERE id = :d", d=DOC)
    with pytest.raises(AlbaranAprobadoError):
        repositorio(motor).volver_a_calculado(document_id=DOC, valuation_line_id=FILA)


def test_f106_r30_el_servicio_deja_deshacer():
    from application.services.review_service import ReviewService
    from test_f106_fila import _deshacer

    motor = cecois()
    _patch(motor, {"cantidad": 48.0})
    servicio = ReviewService(repositorio(motor), "ana")
    assert servicio.volver_a_calculado(document_id=DOC, valuation_line_id=FILA) is True
    assert fila(motor, FILA)["cantidad_convertida"] == 10.0

    _deshacer(motor)

    f = fila(motor, FILA)
    assert f["cantidad_convertida"] == 48.0 and _json(motor) is not None


def test_f106_r30_ruta(monkeypatch):
    class _Volver:
        def __init__(self, resultado):
            self.resultado = resultado
            self.llamadas = []

        def initialize(self):
            return True

        def volver_a_calculado(self, **kwargs):
            self.llamadas.append(kwargs)
            return self.resultado

    servicio = _Volver(True)
    r = _cliente(monkeypatch, servicio).post("/api/documents/DOC/lines/14/volver-a-calculado")
    assert r.status_code == 200 and servicio.llamadas == [{"document_id": "DOC", "valuation_line_id": 14}]
    r = _cliente(monkeypatch, _Volver(False)).post("/api/documents/DOC/lines/14/volver-a-calculado")
    assert r.status_code == 404


def test_f106_r30_aviso_de_revalorar_conserva(tmp_path):
    from test_f065_f1_js import _ejecutar

    casos = _ejecutar(tmp_path, ["avisoRevalorar"], """
        console.log(JSON.stringify([avisoRevalorar(0), avisoRevalorar(1), avisoRevalorar(3)]));
    """)
    assert casos == [None, "Revalorar conserva 1 línea puesta a mano. ¿Continuar?",
                     "Revalorar conserva 3 líneas puestas a mano. ¿Continuar?"]


def test_f106_r30_js_el_boton_llama_a_la_ruta():
    from test_f051_almacen_front import _app_js, _funcion_js

    cuerpo = _funcion_js(_app_js(), "wireVolverACalculado")
    assert "/volver-a-calculado" in cuerpo and "window.location.reload()" in cuerpo
    assert "wireVolverACalculado();" in _app_js()


def test_f106_r22_sv4_usa_la_de_comun():
    from domain.models import review_models

    assert review_models.es_fila_manual.__module__ == "ruesma_comun.edicion_manual"


def test_f106_r22_una_fila_con_edicion_cuenta_como_tocada():
    motor = cecois()
    _patch(motor, {"cantidad": 48.0})
    detalle = repositorio(motor).get_document_detail(DOC)
    assert detalle.n_filas_manuales >= 1
