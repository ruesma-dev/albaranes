# tests/test_f065_f2_origen.py
"""F-065 · fase 2 · R24–R28: origen «Contrato» / Nueva y partida de la obra.

- R24: la ficha llama «Contrato» al origen que decía «Sigrid» (solo textos).
- R25, R26: cambiar la partida (salvo vaciarla o poner la de su línea de
  contrato), el precio o la unidad de una fila Contrato la hace Nueva, sin
  confirmación; descripción, cantidad, descuento o código externo, no.
- R27: el combo de partida ofrece «Almacén» y las partidas hoja de la obra;
  obra sin partidas ⇒ solo «Almacén»; Sigrid no responde ⇒ solo «Almacén» y el
  aviso; solo admite valores de la lista; elegir solo cambia la partida.
- R28: «Origen ✎» es la única vía de reapuntar: elegir una línea de contrato
  copia su partida y su precio; «Nueva», con los valores actuales.

Más las decisiones del humano del 2026-10-11 (review de la fase 1): «Solo volver
a buscar» confirma como R22 (O1); el almacén nunca impide aprobar y una fila sin
línea de contrato ni derivada sí (O2); el total con ROUND en todas las
escrituras (O3); aprobar un aprobado no reescribe nada (O5).

Repositorio real sobre SQLite (``f065_bbdd``), plantilla real y JS con node.
"""
from __future__ import annotations

import re

import pytest
from f053_sv4_bbdd import foto
from f065_bbdd import (
    DOC,
    construir,
    documento,
    ejecutar,
    fila,
    linea,
    repositorio,
    total,
)
from sqlalchemy import text
from sqlalchemy.orm import Session
from test_f051_almacen_front import _app_js, _funcion_js
from test_f065_f1_js import _bloque, _ejecutar, con_node


def _editar(motor, vid, **campos):
    return repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, campos=campos,
    )


def _es_contrato(f):
    return f["matched_contrato_line_id"] is not None and f["derived_contrato_line_id"] is None


def _derivada(motor, did):
    with Session(motor) as s:
        return dict(s.execute(text(
            "SELECT descripcion_linea, unidad_medida, precio_unitario, codigo_partida, origen "
            "FROM contrato_lines_derived WHERE id = :id"), {"id": did}).mappings().one())


# =================================================================== #
# R25, R26 · dominio: cambia_origen
# =================================================================== #
@pytest.mark.parametrize(("es_contrato", "casada", "cambios", "esperado"), [
    (True, "01.01", {"codigo_partida": "02.02"}, True),
    (True, "01.01", {"codigo_partida": None}, False),          # vaciar = almacén (R26, P10)
    (True, "01.01", {"codigo_partida": "01.01"}, False),       # la de su línea de contrato
    (True, " 01.01 ", {"codigo_partida": "01.01"}, False),
    (True, None, {"codigo_partida": "01.01"}, True),
    (True, "01.01", {"precio_unitario": 120.0}, True),
    (True, "01.01", {"unidad": "M2"}, True),
    (True, "01.01", {"descripcion": "X", "cantidad": 3.0, "descuento": 5.0,
                     "codigo_externo": "E"}, False),
    (True, "01.01", {}, False),
    (False, "01.01", {"codigo_partida": "02.02", "precio_unitario": 1.0}, False),
])
def test_f065_r25_dominio_cambia_origen(es_contrato, casada, cambios, esperado):
    from domain.models.review_models import cambia_origen

    assert cambia_origen(es_contrato=es_contrato, partida_casada=casada,
                         cambios=cambios) is esperado


# =================================================================== #
# R25, R26 · repositorio
# =================================================================== #
@pytest.mark.parametrize("campos", [
    {"codigo_partida": "09.09"}, {"precio_unitario": 120.0}, {"unidad": "M2"},
])
def test_f065_r25_partida_precio_o_unidad_hacen_nueva_la_fila_contrato(campos):
    motor = construir()

    _editar(motor, 11, **campos)

    f = fila(motor, 11)
    assert f["matched_contrato_line_id"] is None
    derivada = _derivada(motor, f["derived_contrato_line_id"])
    assert derivada["origen"] == "manual_override"
    assert derivada["codigo_partida"] == campos.get("codigo_partida", "01.01")
    assert derivada["precio_unitario"] == campos.get("precio_unitario", 115.0)
    assert derivada["unidad_medida"] == campos.get("unidad", "UD")


@pytest.mark.parametrize("campos", [
    {"codigo_partida": ""}, {"descripcion": "PUERTA IZQ"}, {"cantidad": 6.0},
    {"descuento": 10.0}, {"codigo_externo": "E-1"},
])
def test_f065_r26_lo_demas_no_cambia_el_origen(campos):
    motor = construir()

    _editar(motor, 11, **campos)

    f = fila(motor, 11)
    assert _es_contrato(f) and f["matched_contrato_line_id"] == 501


def test_f065_r26_volver_a_la_partida_de_su_linea_sigue_siendo_contrato():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET codigo_partida_final = NULL WHERE id = 11")

    _editar(motor, 11, codigo_partida="01.01")

    f = fila(motor, 11)
    assert _es_contrato(f) and f["codigo_partida_final"] == "01.01"


def test_f065_r26_el_repositorio_decide_con_cambia_origen():
    import inspect

    from infrastructure.database.review_repository import AlbaranReviewRepository

    assert "cambia_origen(" in inspect.getsource(AlbaranReviewRepository.update_line_conciliacion)


# =================================================================== #
# R28 · «Origen ✎»: línea de contrato o Nueva
# =================================================================== #
def test_f065_r28_elegir_otra_linea_de_contrato_copia_su_partida_y_su_precio():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_contrato_lines_merge SET precio_unitario = 130, "
             "unidad_medida = 'U' WHERE id = 503")
    ejecutar(motor, "UPDATE albaran_line_valuations SET descripcion_linea = 'OVERRIDE' "
             "WHERE id = 11")

    assert repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=11, mode="contract_line",
        matched_contrato_line_id=503)

    f = fila(motor, 11)
    assert _es_contrato(f) and f["matched_contrato_line_id"] == 503
    assert f["codigo_partida_final"] == "01.03"
    assert f["precio_unitario_final"] == pytest.approx(130.0)
    assert f["unidad_contrato"] == "U"
    assert f["descripcion_linea"] is None
    assert f["importe_calculado"] == pytest.approx(8 * 130.0)
    assert total(motor) == pytest.approx(1040 + 1150 + 50)


def test_f065_r28_nueva_conserva_los_valores_actuales_de_la_fila():
    """No los de la blanca (concepto «PUERTA EI2-60», precio 115 leído): los de
    la fila tal como la enseña la ficha."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = 120, "
             "importe_calculado = 960, codigo_partida_final = '07.07' WHERE id = 11")

    assert repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=11, mode="nueva")

    f = fila(motor, 11)
    assert f["matched_contrato_line_id"] is None
    derivada = _derivada(motor, f["derived_contrato_line_id"])
    assert derivada == {
        "descripcion_linea": "PUERTA CORTAFUEGOS EI2-60", "unidad_medida": "UD",
        "precio_unitario": 120.0, "codigo_partida": "07.07", "origen": "manual_override",
    }
    assert f["precio_unitario_final"] == pytest.approx(120.0)
    assert f["importe_calculado"] == pytest.approx(960.0)
    assert f["importe_source"] == "declared_albaran"


# =================================================================== #
# R24 · «Contrato» en la ficha
# =================================================================== #
def test_f065_r24_plantilla_dice_contrato(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()], display=[fila_detalle()]))
    celda = re.search(r'<td[^>]*data-col="origen"[^>]*>.*?</td>', html, re.DOTALL).group(0)

    assert "Contrato ✎" in celda and "Sigrid" not in celda
    assert 'data-sort-value="Contrato"' in celda


def test_f065_r24_plantilla_de_solo_lectura_dice_contrato(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    doc = documento_detalle(lineas_valoracion=[linea_valorada()], display=[fila_detalle()])
    html = render_detalle(doc.model_copy(update={"approved": True}))
    celda = re.search(r'<td[^>]*data-col="origen"[^>]*>.*?</td>', html, re.DOTALL).group(0)

    assert ">Contrato<" in celda and "Sigrid" not in celda


def test_f065_r27_plantilla_sin_partidas_del_contrato_ni_aviso_de_casada(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    """El combo ya no usa las partidas del contrato ni el aviso «pasará a NUEVA»."""
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"codigo_partida_casada": "01.01"})]))

    assert 'id="partidas-json"' not in html
    assert "data-partida-casada" not in html


# =================================================================== #
# R27 · combo de partidas de la obra (JS)
# =================================================================== #
_RESPUESTA = """
const RESP = {ok: true, items: [
    {codigo: "01.01", descripcion: "Cimentación", descripcion_agregada: "Estructura › Cimentación"},
    {codigo: "02.03", descripcion: "Puertas", descripcion_agregada: "Carpintería › Puertas cortafuegos"},
]};
"""


@con_node
def test_f065_r27_js_partidas_de_la_respuesta(tmp_path):
    casos = _ejecutar(tmp_path, ["_normLine", "partidasDeRespuesta"], _RESPUESTA + """
        console.log(JSON.stringify({
            ok: partidasDeRespuesta(RESP),
            sin_partidas: partidasDeRespuesta({ok: true, items: []}),
            caido: partidasDeRespuesta({ok: false, error: "x", items: []}),
            nada: partidasDeRespuesta(null),
        }));
    """)

    assert casos["ok"]["error"] is False
    assert [i["code"] for i in casos["ok"]["items"]] == ["01.01", "02.03"]
    assert casos["ok"]["items"][1]["label"] == "02.03 · Carpintería › Puertas cortafuegos"
    assert casos["sin_partidas"] == {"items": [], "error": False}
    assert casos["caido"] == {"items": [], "error": True}
    assert casos["nada"] == {"items": [], "error": True}


@con_node
def test_f065_r27_js_opciones_almacen_primero_y_filtro(tmp_path):
    casos = _ejecutar(tmp_path, ["_normLine", "partidasDeRespuesta", "opcionesPartida"],
                      _RESPUESTA + """
        const items = partidasDeRespuesta(RESP).items;
        function codigos(lista) { return lista.map(function (o) { return o.almacen ? "ALM" : o.code; }); }
        console.log(JSON.stringify({
            todas: codigos(opcionesPartida(items, "")),
            por_codigo: codigos(opcionesPartida(items, "02.0")),
            por_descripcion: codigos(opcionesPartida(items, "carpinteria cortafuegos")),
            sin_coincidencia: codigos(opcionesPartida(items, "zzz")),
            sin_partidas: codigos(opcionesPartida([], "")),
        }));
    """)

    assert casos == {
        "todas": ["ALM", "01.01", "02.03"],
        "por_codigo": ["ALM", "02.03"],
        "por_descripcion": ["ALM", "02.03"],
        "sin_coincidencia": ["ALM"],
        "sin_partidas": ["ALM"],
    }


@con_node
def test_f065_r27_js_solo_admite_valores_de_la_lista(tmp_path):
    casos = _ejecutar(tmp_path, ["_normLine", "partidasDeRespuesta", "partidaValida"],
                      _RESPUESTA + """
        const items = partidasDeRespuesta(RESP).items;
        console.log(JSON.stringify([
            partidaValida("01.01", items), partidaValida(" 02.03 ", items),
            partidaValida("", items), partidaValida("  ", items),
            partidaValida("09.99", items), partidaValida("01", items),
        ]));
    """)

    assert casos == [True, True, True, True, False, False]


@con_node
def test_f065_r27_js_teclado_flechas(tmp_path):
    casos = _ejecutar(tmp_path, ["siguienteActivo"], """
        console.log(JSON.stringify([
            siguienteActivo(-1, "ArrowDown", 3), siguienteActivo(0, "ArrowDown", 3),
            siguienteActivo(2, "ArrowDown", 3), siguienteActivo(2, "ArrowUp", 3),
            siguienteActivo(0, "ArrowUp", 3), siguienteActivo(1, "x", 3),
        ]));
    """)

    assert casos == [0, 1, 2, 1, 0, 1]


def test_f065_r27_el_combo_de_partida_es_el_de_la_obra():
    js = _app_js()
    combo = _funcion_js(js, "attachPartidaCombo")
    cargar = _funcion_js(js, "cargarPartidasObra")

    assert "attachPartidaCombo(inp)" in _funcion_js(js, "wirePartidaCombos")
    assert "/api/sigrid/partidas?obra=" in cargar and "partidasDeRespuesta(" in cargar
    assert "No se pudieron cargar las partidas" in combo
    for tecla in ('"ArrowDown"', '"ArrowUp"', '"Enter"', '"Escape"'):
        assert tecla in combo
    assert "partidaValida(" in combo
    assert "elegirAlmacen(input)" in combo
    assert ".js-concilia-select" not in combo  # elegir una partida no reapunta
    assert "PARTIDAS_FALLBACK" not in js and "partidas-json" not in js
    assert "function attachInputCombo(" not in js and "function loadPartidas(" not in js


def test_f065_r27_el_combo_de_partida_va_antes_que_el_enter_de_guardar():
    """Con el panel abierto, Enter elige la partida (no guarda la fila)."""
    js = _app_js()
    combo = _funcion_js(js, "attachPartidaCombo")

    assert "stopImmediatePropagation()" in combo
    assert js.index("wirePartidaCombos();") < js.index("wireConciliaEdit();")


# =================================================================== #
# R25, R28 · sin confirm de NUEVA; concepto como texto
# =================================================================== #
def test_f065_r25_guardar_ya_no_pregunta_si_pasa_a_nueva():
    js = _app_js()

    assert "pasará a NUEVA" not in js
    assert "function cambiaIdentidad(" not in js


def test_f065_r28_el_concepto_es_un_texto_sin_combo():
    js = _app_js()

    assert "function wireConceptoCombos(" not in js
    assert "function attachContratoLineCombo(" not in js
    assert "initConciliaCombos();" in js  # «Origen ✎» sigue reapuntando


# =================================================================== #
# O1 (humano 2026-10-11) · «Solo volver a buscar» confirma como R22
# =================================================================== #
def test_f065_o1_solo_volver_a_buscar_confirma_antes():
    bloque = _bloque(_app_js(), "async function handleRefetchOnly()", "setButtonsDisabled(true);")

    assert "confirmarRevalorar()" in bloque


# =================================================================== #
# O2 y almacén (humano 2026-10-11) · aprobar
# =================================================================== #
def test_f065_almacen_nunca_impide_aprobar_aunque_esten_todas():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET codigo_partida_final = NULL, "
             "partida_action = 'almacen_elegido'")

    assert repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")


def test_f065_o2_una_fila_sin_linea_de_contrato_ni_derivada_impide_aprobar():
    from domain.models.review_models import LineasIncompletasError

    motor = construir()
    with Session(motor) as s:
        linea(s, id=29, merge_line_id=None, line_kind="manual", importe_calculado=12.0)
        s.commit()
    antes = foto(motor)

    with pytest.raises(LineasIncompletasError) as error:
        repositorio(motor).set_approved(document_id=DOC, approved=True, approved_by="ana")

    assert error.value.aviso == (
        "Hay 1 línea sin línea de contrato ni Nueva que la ficha no enseña: revalora el albarán")
    assert foto(motor) == antes


def test_f065_o2_las_dos_cosas_a_la_vez():
    from domain.models.review_models import LineasIncompletasError

    error = LineasIncompletasError(DOC, [2, 4], huerfanas=3)

    assert error.aviso == (
        "Líneas sin cantidad o importe: 2, 4. Hay 3 líneas sin línea de contrato ni Nueva "
        "que la ficha no enseña: revalora el albarán")


# =================================================================== #
# O3 · el total con ROUND en reapuntar, borrar y casar una blanca
# =================================================================== #
_RUIDO = (549.34, 882.62, 818.64, 863.26, 278.86)


def _con_ruido(motor):
    with Session(motor) as s:
        for i, imp in enumerate(_RUIDO):
            linea(s, id=40 + i, merge_line_id=None, line_kind="manual",
                  derived_contrato_line_id=601, importe_calculado=imp)
        s.commit()


@pytest.mark.parametrize("operacion", ["reapuntar", "borrar", "casar_blanca"])
def test_f065_o3_el_total_se_redondea_en_todas_las_escrituras(operacion):
    motor = construir()
    _con_ruido(motor)
    repo = repositorio(motor)
    if operacion == "reapuntar":
        repo.set_line_conciliacion(document_id=DOC, valuation_line_id=11,
                                   mode="contract_line", matched_contrato_line_id=501)
    elif operacion == "borrar":
        repo.remove_line_valuation(document_id=DOC, valuation_line_id=13)
    else:
        ejecutar(motor, "DELETE FROM albaran_line_valuations WHERE id = 13")
        repo.add_conciliacion_for_merge_line(document_id=DOC, merge_line_id=703, mode="nueva")

    assert total(motor) == round(total(motor), 2)
    assert total(motor) == round(sum(f["importe_calculado"] or 0 for f in _filas(motor)), 2)


def _filas(motor):
    from f065_bbdd import filas

    return filas(motor)


def test_f065_o3_las_escrituras_usan_el_total_redondeado():
    import inspect

    from infrastructure.database.review_repository import AlbaranReviewRepository

    for metodo in ("set_line_conciliacion", "remove_line_valuation",
                   "add_conciliacion_for_merge_line"):
        fuente = inspect.getsource(getattr(AlbaranReviewRepository, metodo))
        assert "self._recalcular_total_in_session(session, " in fuente, metodo
        assert "SUM(importe_calculado)" not in fuente, metodo


# =================================================================== #
# O5 · aprobar un aprobado no reescribe nada
# =================================================================== #
def test_f065_o5_aprobar_un_aprobado_es_un_no_op_real():
    motor = construir(aprobado=True)
    antes = foto(motor)

    assert repositorio(motor).set_approved(
        document_id=DOC, approved=True, approved_by="otra") is False

    assert foto(motor) == antes
    assert documento(motor)["approved_by"] == "ana"


# --- R28 · bordes de «Origen ✎» ---------------------------------------- #
def test_f065_r28_nueva_con_otro_precio_recalcula_el_importe():
    motor = construir()

    assert repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=11, mode="nueva", precio_unitario=100.0,
        descripcion="PUERTA A MEDIDA")

    f = fila(motor, 11)
    derivada = _derivada(motor, f["derived_contrato_line_id"])
    assert (derivada["precio_unitario"], derivada["descripcion_linea"]) == (
        100.0, "PUERTA A MEDIDA")
    assert f["importe_calculado"] == pytest.approx(800.0)
    assert f["importe_source"] == "calculated"
    assert total(motor) == pytest.approx(800 + 1150 + 50)


def test_f065_r28_nueva_desde_una_nueva_toma_los_valores_de_su_derivada():
    """Fila 13 (Nueva, derivada 601 «PORTES», UD, 50 €) sin override propio."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET unidad_contrato = NULL, "
             "precio_unitario_final = NULL WHERE id = 13")

    repositorio(motor).set_line_conciliacion(document_id=DOC, valuation_line_id=13, mode="nueva")

    f = fila(motor, 13)
    assert f["derived_contrato_line_id"] not in (None, 601)
    derivada = _derivada(motor, f["derived_contrato_line_id"])
    assert derivada == {"descripcion_linea": "PORTES", "unidad_medida": "UD",
                        "precio_unitario": 50.0, "codigo_partida": "03.01",
                        "origen": "manual_override"}
    assert f["importe_calculado"] == pytest.approx(50.0)
    assert f["importe_source"] == "declared_albaran"


def test_f065_r28_linea_de_contrato_con_precio_propio():
    motor = construir()

    repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=12, mode="contract_line",
        matched_contrato_line_id=503, precio_unitario=110.0)

    f = fila(motor, 12)
    assert (f["matched_contrato_line_id"], f["precio_unitario_final"]) == (503, 110.0)
    assert f["importe_calculado"] == pytest.approx(1100.0)


@pytest.mark.parametrize("mode, linea_id", [("contract_line", None), ("contract_line", 999),
                                            ("otro", None)])
def test_f065_r28_reapuntar_mal_no_cambia_nada(mode, linea_id):
    motor = construir()
    antes = foto(motor)

    assert repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=11, mode=mode,
        matched_contrato_line_id=linea_id) is False

    assert foto(motor) == antes


def test_f065_r28_reapuntar_una_fila_ajena_no_cambia_nada():
    motor = construir()
    antes = foto(motor)

    assert repositorio(motor).set_line_conciliacion(
        document_id=DOC, valuation_line_id=21, mode="nueva") is False

    assert foto(motor) == antes
