# tests/test_f065_f1_fila.py
"""F-065 · fase 1 · R6–R12: editar una fila guarda solo lo que cambió, con
cantidades coherentes y el precio aplicado.

Q de una fila = ``cantidad_convertida ?? cantidad_albaran``: la que enseña y
edita la ficha, en la unidad del precio (``importe = precio × Q × (1 − dto)``).
Lo tecleado YA es la convertida; lo que se deriva es la del albarán (R6).

Dominio puro (``cantidades_tras_editar``, ``es_fila_manual``, el cuerpo del
PATCH) y repositorio real sobre SQLite (``f065_bbdd``). Sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from f065_bbdd import DOC, construir, ejecutar, fila, linea, repositorio, total
from pydantic import ValidationError
from sqlalchemy.orm import Session


# =================================================================== #
# Dominio · cantidades_tras_editar (R6, R7)
# =================================================================== #
@pytest.mark.parametrize(
    ("q", "ca", "cc", "factor", "esperado"),
    [
        # R7: sin cantidad nueva, ninguna cambia.
        (None, 6.0, 1.0, None, (6.0, 1.0)),
        (None, 10.0, None, None, (10.0, None)),
        # (a) reproducible y factor ≠ 0: la del albarán se deriva (t → kg).
        (3000.0, 2.0, 2000.0, 1000.0, (3.0, 3000.0)),
        (6.0, 8.0, 8.0, 1.0, (6.0, 6.0)),
        # (b) sin conversión: las dos son Q.
        (8.0, 10.0, None, None, (8.0, 8.0)),
        (8.0, 10.0, None, 1.0, (8.0, 8.0)),
        # (c) el resto: la del albarán se conserva (contenedores, legadas).
        (2.0, 6.0, 1.0, None, (6.0, 2.0)),
        (2.0, 6.0, 1.0, 1.0, (6.0, 2.0)),
        (3.0, 2000.0, None, 1000.0, (2000.0, 3.0)),
        (4.0, 5.0, 0.0, 0.0, (5.0, 4.0)),
    ],
    ids=["r7_contenedor", "r7_sin_conversion", "a_kg", "a_factor_uno", "b_sin_factor",
         "b_factor_uno", "c_contenedores", "c_factor_uno_no_reproducible", "c_legada",
         "c_factor_cero"],
)
def test_f065_r6_dominio_cantidades_tras_editar(q, ca, cc, factor, esperado):
    from domain.models.review_models import cantidades_tras_editar

    assert cantidades_tras_editar(
        q_nueva=q, cantidad_albaran=ca, cantidad_convertida=cc, factor=factor,
    ) == pytest.approx(esperado)


# =================================================================== #
# Dominio · es_fila_manual (definición de requirements, R22)
# =================================================================== #
@pytest.mark.parametrize(
    ("campos", "esperado"),
    [
        ({}, False),
        ({"line_kind": "manual"}, True),
        ({"line_kind": "reparto"}, True),
        ({"line_kind": "synthetic_modifier"}, False),
        ({"bloqueada": True}, True),
        ({"derivada_origen": "manual_override"}, True),
        ({"derivada_origen": "nueva_no_match"}, False),
        ({"precio_unitario_agreement": "manual"}, True),
        ({"precio_unitario_agreement": "agree"}, False),
        ({"partida_action": "almacen_elegido"}, True),
        ({"partida_action": "almacen_sin_partida"}, False),
    ],
)
def test_f065_r22_dominio_es_fila_manual(campos, esperado):
    from domain.models.review_models import es_fila_manual

    base = {"line_kind": "from_albaran", "bloqueada": False, "derivada_origen": None,
            "precio_unitario_agreement": None, "partida_action": None}
    base.update(campos)
    assert es_fila_manual(**base) is esperado


# =================================================================== #
# Dominio · el cuerpo del PATCH: ausente = no cambia, null = vaciar (R8)
# =================================================================== #
@pytest.mark.parametrize(
    ("cuerpo", "campos"),
    [
        ({}, {}),
        ({"cantidad": "6"}, {"cantidad": 6.0}),
        ({"cantidad": "1.234,5"}, {"cantidad": 1234.5}),
        ({"cantidad": 7}, {"cantidad": 7.0}),
        ({"descuento": None}, {"descuento": None}),
        ({"descuento": ""}, {"descuento": None}),
        ({"codigo_partida": ""}, {"codigo_partida": None}),
        ({"codigo_partida": " 01.02 "}, {"codigo_partida": "01.02"}),
        ({"descripcion": "X", "importe": 3}, {"descripcion": "X"}),
    ],
)
def test_f065_r8_dominio_campos_presentes(cuerpo, campos):
    from domain.models.review_models import ConciliacionEditBody

    assert ConciliacionEditBody(**cuerpo).campos() == campos


def test_f065_r8_dominio_un_numero_ilegible_es_un_error_no_un_vaciado():
    """Antes un «abc» se convertía en None (= «no viene»); con R8 None es
    «vaciar», así que un número ilegible tiene que dar 422, no borrar."""
    from domain.models.review_models import ConciliacionEditBody

    with pytest.raises(ValidationError):
        ConciliacionEditBody(cantidad="abc")


# =================================================================== #
# Repositorio · R6 y R7
# =================================================================== #
def _editar(motor, vid, bloquear=False, **campos):
    return repositorio(motor).update_line_conciliacion(
        document_id=DOC, valuation_line_id=vid, campos=campos, bloquear=bloquear,
    )


def test_f065_r6_cantidad_en_fila_sin_conversion_fija_las_dos():
    motor = construir()

    assert _editar(motor, 11, cantidad=6.0) is True

    f = fila(motor, 11)
    assert (f["cantidad_albaran"], f["cantidad_convertida"]) == (6.0, 6.0)
    assert f["importe_calculado"] == pytest.approx(690.0)
    assert f["importe_source"] == "calculated"
    assert total(motor) == pytest.approx(690 + 1150 + 50)


def test_f065_r6_cantidad_en_fila_reproducible_deriva_la_del_albaran():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET factor_conversion = 1000, "
             "cantidad_albaran = 2, cantidad_convertida = 2000, precio_unitario_final = 0.05, "
             "importe_calculado = 100 WHERE id = 11")

    _editar(motor, 11, cantidad=3000.0)

    f = fila(motor, 11)
    assert (f["cantidad_albaran"], f["cantidad_convertida"]) == pytest.approx((3.0, 3000.0))
    assert f["importe_calculado"] == pytest.approx(150.0)


def test_f065_r6_cantidad_en_fila_de_contenedores_conserva_la_del_albaran():
    """SALMEDINA: 6 m³ declarados, 1 contenedor a 120 €. La administrativa
    pone 2 contenedores: la del albarán (6 m³) se queda, el importe es 240 €
    (nunca 6 × 120 = 720)."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET factor_conversion = NULL, "
             "cantidad_albaran = 6, cantidad_convertida = 1, precio_unitario_final = 120, "
             "importe_calculado = 120 WHERE id = 11")

    _editar(motor, 11, cantidad=2.0)

    f = fila(motor, 11)
    assert (f["cantidad_albaran"], f["cantidad_convertida"]) == (6.0, 2.0)
    assert f["importe_calculado"] == pytest.approx(240.0)


def test_f065_r7_sin_cantidad_conserva_las_dos_y_calcula_con_q():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET factor_conversion = NULL, "
             "cantidad_albaran = 6, cantidad_convertida = 1, precio_unitario_final = 120, "
             "importe_calculado = 120 WHERE id = 11")

    _editar(motor, 11, descuento=10.0)

    f = fila(motor, 11)
    assert (f["cantidad_albaran"], f["cantidad_convertida"]) == (6.0, 1.0)
    assert f["importe_calculado"] == pytest.approx(108.0)
    assert f["descuento_albaran_aplicado"] == pytest.approx(10.0)


# =================================================================== #
# Repositorio · R8: solo lo que cambió; nada cambia ⇒ nada se escribe
# =================================================================== #
_VALORADO = ("importe_calculado", "importe_source", "descuento_albaran_aplicado",
             "review_required", "precio_unitario_final", "matched_contrato_line_id",
             "derived_contrato_line_id", "codigo_partida_final", "unidad_contrato")


@pytest.mark.parametrize("campos", [
    {}, {"cantidad": 8.0}, {"cantidad": 8.0, "descuento": None},
    {"precio_unitario": 115.0, "codigo_partida": "01.01", "unidad": "UD"},
], ids=["vacio", "misma_cantidad", "mismos_cantidad_y_dto", "mismos_identitarios"])
def test_f065_r8_sin_cambios_no_escribe_lo_valorado(campos):
    motor = construir()
    antes = fila(motor, 11)

    assert _editar(motor, 11, **campos) is True

    despues = fila(motor, 11)
    assert {k: despues[k] for k in _VALORADO} == {k: antes[k] for k in _VALORADO}
    assert total(motor) == pytest.approx(2120.0)


def test_f065_r8_cambiar_solo_el_codigo_externo_no_reetiqueta_el_importe():
    """Lo declarado por el albarán no pasa a «calculado» porque se edite un
    campo que no entra en el importe (F-019 R24, ahora en la fila)."""
    motor = construir()

    _editar(motor, 11, codigo_externo="EXT-1")

    f = fila(motor, 11)
    assert f["codigo_externo"] == "EXT-1"
    assert f["importe_source"] == "declared_albaran"
    assert f["importe_calculado"] == pytest.approx(920.0)


def test_f065_r8_descuento_a_null_lo_vacia():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descuento_albaran_aplicado = 10, "
             "importe_calculado = 828 WHERE id = 11")

    _editar(motor, 11, descuento=None)

    f = fila(motor, 11)
    assert f["descuento_albaran_aplicado"] is None
    assert f["importe_calculado"] == pytest.approx(920.0)


def test_f065_r8_cantidad_a_null_la_vacia():
    motor = construir()

    _editar(motor, 11, cantidad=None)

    f = fila(motor, 11)
    assert (f["cantidad_albaran"], f["cantidad_convertida"], f["importe_calculado"]) == (
        None, None, None)
    assert total(motor) == pytest.approx(1150 + 50)


def test_f065_r8_descuento_cero_y_nulo_son_lo_mismo():
    motor = construir()
    antes = fila(motor, 11)

    _editar(motor, 11, descuento=0.0)

    assert fila(motor, 11)["importe_source"] == antes["importe_source"]


def test_f065_r8_solo_se_toca_la_fila_editada():
    motor = construir()
    antes = {vid: fila(motor, vid) for vid in (12, 13, 21)}

    _editar(motor, 11, cantidad=6.0, descripcion="OTRA")

    assert {vid: fila(motor, vid) for vid in (12, 13, 21)} == antes


def test_f065_r8_linea_de_otro_documento_no_se_toca():
    motor = construir()
    antes = fila(motor, 21)

    assert _editar(motor, 21, cantidad=1.0) is False

    assert fila(motor, 21) == antes


# =================================================================== #
# R9 · precio aplicado
# =================================================================== #
def _mapa(motor):
    repo = repositorio(motor)
    with Session(motor) as s:
        valoracion = repo._load_valuation_in_session(session=s, document_id=DOC)
        return repo._load_conciliation_map_in_session(session=s, valuation=valoracion)


def test_f065_r9_la_ficha_pinta_el_precio_aplicado_en_filas_contrato():
    """sv6 deja la fila casada con el precio declarado (120) aunque el del
    contrato sea 115: la ficha pinta 120 y guarda el 115 aparte (title)."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = 120 "
             "WHERE id = 11")

    conc = _mapa(motor)[11]

    assert conc.unitario == pytest.approx(120.0)
    assert conc.unitario_contrato == pytest.approx(115.0)
    assert conc.price_agreement == "disagree"


def test_f065_r9_en_filas_nuevas_el_precio_es_el_de_la_derivada():
    conc = _mapa(construir())[13]

    assert conc.unitario == pytest.approx(50.0)


def test_f065_r9_guardar_sin_tocar_el_precio_no_cambia_precio_ni_origen():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = 120 "
             "WHERE id = 11")

    _editar(motor, 11, cantidad=6.0)

    f = fila(motor, 11)
    assert f["precio_unitario_final"] == pytest.approx(120.0)
    assert f["matched_contrato_line_id"] == 501
    assert f["derived_contrato_line_id"] is None
    assert f["importe_calculado"] == pytest.approx(720.0)


def test_f065_r9_plantilla_precio_aplicado_y_el_del_contrato_en_el_title(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    import re

    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"unitario": 120.0, "unitario_contrato": 115.0})],
    ))

    entrada = re.search(r'<input[^>]*data-field="precio_unitario"[^>]*>', html).group(0)
    assert 'value="120.0000"' in entrada
    assert "115" in entrada and "title=" in entrada


# =================================================================== #
# R10 · una fila Contrato editada queda con cantidad_convertida
# =================================================================== #
def test_f065_r10_editar_una_fila_legada_sin_convertida_la_completa():
    """El PATCH viejo dejaba ``cantidad_convertida`` a NULL: sv9 la daría por
    ``cantidad_sin_convertir``. Cualquier guardado la completa con Q."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET cantidad_albaran = 6, "
             "cantidad_convertida = NULL, importe_calculado = 690 WHERE id = 11")

    _editar(motor, 11, descripcion="PUERTA EI2-60 IZQ")

    f = fila(motor, 11)
    assert (f["cantidad_albaran"], f["cantidad_convertida"]) == (6.0, 6.0)
    assert f["importe_calculado"] == pytest.approx(690.0)


def test_f065_r10_guardar_sin_cambios_tambien_completa_la_convertida():
    motor = construir()

    _editar(motor, 13)

    f = fila(motor, 13)
    assert f["cantidad_convertida"] == 1.0
    assert f["importe_source"] == "declared_albaran"


# =================================================================== #
# R11 · lo que cambia el administrativo pisa lo valorado
# =================================================================== #
def test_f065_r11_editar_pisa_el_declarado_y_sale_de_revision():
    motor = construir()

    _editar(motor, 11, cantidad=6.0)

    f = fila(motor, 11)
    assert f["importe_source"] == "calculated"
    assert f["review_required"] in (0, False)


def test_f065_r11_descuento_fuera_de_rango_no_se_aplica():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET descuento_albaran_aplicado = 150 "
             "WHERE id = 11")

    _editar(motor, 11, cantidad=8.5)

    assert fila(motor, 11)["importe_calculado"] == pytest.approx(977.5)


def test_f065_r11_el_total_no_arrastra_ruido_float():
    motor = construir()
    with Session(motor) as s:
        for i, imp in enumerate((549.34, 882.62, 818.64, 863.26, 278.86)):
            linea(s, id=40 + i, merge_line_id=None, line_kind="manual",
                  derived_contrato_line_id=601, importe_calculado=imp)
        s.commit()

    _editar(motor, 13, cantidad=2.0)

    esperado = round(920 + 1150 + 100 + 549.34 + 882.62 + 818.64 + 863.26 + 278.86, 2)
    assert total(motor) == esperado
    assert total(motor) == round(total(motor), 2)


# =================================================================== #
# R12 · la celda de importe enseña lo guardado
# =================================================================== #
def test_f065_r12_plantilla_el_importe_es_el_guardado_tambien_si_es_reproducible(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    import re

    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(
            factor_conversion=1.0, cantidad_albaran=8.0, cantidad_convertida=8.0,
            precio_unitario_final=2.5, importe_calculado=19.99)],
        display=[fila_detalle(cantidad=8.0, conciliacion={"unitario": 2.5})],
    ))

    celda = re.search(r'<td[^>]*data-col="importe"[^>]*>.*?</td>', html, re.DOTALL).group(0)
    assert 'value="19.99"' in celda
    assert "20.00" not in celda


def test_f065_r8_dominio_un_numero_no_finito_es_un_error():
    from domain.models.review_models import ConciliacionEditBody

    for texto in ("inf", "nan", "-inf"):
        with pytest.raises(ValidationError):
            ConciliacionEditBody(precio_unitario=texto)


def test_f065_r8_dominio_un_texto_a_null_se_vacia():
    from domain.models.review_models import ConciliacionEditBody

    assert ConciliacionEditBody(descripcion=None, codigo_externo="  ").campos() == {
        "codigo_externo": None, "descripcion": None}


def test_f065_r8_un_campo_desconocido_no_cuenta_como_cambio():
    """El ``importe`` (u otra clave) no es un campo de la fila: no hay cambio."""
    motor = construir()
    antes = fila(motor, 11)

    assert _editar(motor, 11, importe=1.0) is True

    assert fila(motor, 11) == antes


def test_f065_r8_una_fila_sin_linea_de_contrato_ni_derivada_no_se_edita():
    motor = construir()
    with Session(motor) as s:
        linea(s, id=29, merge_line_id=None, line_kind="manual")
        s.commit()
    antes = fila(motor, 29)

    assert _editar(motor, 29, cantidad=3.0) is False

    assert fila(motor, 29) == antes


# --- mutación (campaña 1): lo igual no es un cambio ------------------ #
@pytest.mark.parametrize(("a", "b", "igual"), [
    (None, None, True), (1.0, None, False), (None, 1.0, False),
    (1e-9, 0.0, False), (5e-10, 0.0, True), ("x", 1.0, False), (2, 2.0, True),
])
def test_f065_r8_mismo_numero(a, b, igual):
    from infrastructure.database.review_repository import _mismo_numero

    assert _mismo_numero(a, b) is igual


def test_f065_r8_la_misma_descripcion_no_es_un_cambio():
    """La de la línea de contrato que pinta la ficha, reenviada tal cual."""
    motor = construir()

    _editar(motor, 11, descripcion=" PUERTA CORTAFUEGOS EI2-60 ")

    f = fila(motor, 11)
    assert f["review_required"] in (1, True)
    assert f["descripcion_linea"] is None


def test_f065_r8_el_mismo_codigo_externo_no_es_un_cambio():
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET codigo_externo = 'EXT-1' WHERE id = 11")

    _editar(motor, 11, codigo_externo="EXT-1")

    assert fila(motor, 11)["review_required"] in (1, True)


def test_f065_r8_editar_otra_cosa_en_almacen_no_toca_la_marca_de_almacen():
    """F-051 R19: en almacén, guardar otro campo no reescribe la marca."""
    motor = construir()
    ejecutar(motor, "UPDATE albaran_line_valuations SET codigo_partida_final = NULL, "
             "partida_action = 'almacen_sin_partida' WHERE id = 11")

    _editar(motor, 11, cantidad=6.0)

    f = fila(motor, 11)
    assert f["partida_action"] == "almacen_sin_partida"
    assert f["codigo_partida_final"] is None


def test_f065_r8_cambiar_el_precio_o_la_unidad_de_una_fila_contrato_la_hace_nueva():
    """Regla de F-051 que sigue vigente en la fase 1 (la fase 2 la revisa):
    precio o unidad distintos convierten la fila Contrato en Nueva."""
    for campos in ({"precio_unitario": 120.0}, {"unidad": "M2"}):
        motor = construir()

        _editar(motor, 11, **campos)

        f = fila(motor, 11)
        assert f["matched_contrato_line_id"] is None, campos
        assert f["derived_contrato_line_id"] is not None, campos


def test_f065_r8_la_descripcion_de_una_fila_contrato_se_guarda_aparte():
    """Distinta de la de su línea de contrato: override; igual: sin override."""
    motor = construir()

    _editar(motor, 11, descripcion="PUERTA EI2-60 IZQUIERDA")
    assert fila(motor, 11)["descripcion_linea"] == "PUERTA EI2-60 IZQUIERDA"

    _editar(motor, 11, descripcion="PUERTA CORTAFUEGOS EI2-60")
    f = fila(motor, 11)
    assert f["descripcion_linea"] is None
    assert f["matched_contrato_line_id"] == 501


# --- R9: los avisos ✓/⚠ siguen comparando con el precio del contrato -- #
def _blanca(**campos):
    from domain.models.review_models import MergeLinePayload

    return MergeLinePayload(**{"id": 701, "cantidad": 8.0, "precio": 115.0,
                               "precio_neto": 920.0, **campos})


def _avisos(blanca, unitario_contrato):
    from domain.models.review_models import (
        ConciliacionDisplay,
        LineValuationPayload,
        ValuationPayload,
    )
    from infrastructure.database.review_repository import AlbaranReviewRepository

    linea_v = LineValuationPayload(valuation_line_id=11, merge_line_id=701,
                                   precio_unitario_final=120.0)
    valoracion = ValuationPayload(valuation_id="v", status="ok",
                                  lines_by_merge_line_id={701: linea_v})
    conc = ConciliacionDisplay(kind="assigned", unitario=120.0,
                               unitario_contrato=unitario_contrato)
    (fila_display,) = AlbaranReviewRepository._build_display_lines(
        merge_lines=[blanca], valuation=valoracion,
        conciliation_by_valuation_line_id={11: conc},
    )
    return fila_display.concilia.agree_unitario, fila_display.concilia.agree_importe


@pytest.mark.parametrize(("blanca", "contrato", "esperado"), [
    ({}, 115.0, (True, True)),
    ({"precio": 120.0, "precio_neto": 960.0}, 115.0, (False, False)),
    ({"cantidad": None}, 115.0, (True, None)),
    ({}, None, (None, None)),
], ids=["cuadra", "no_cuadra", "sin_cantidad", "sin_precio_de_contrato"])
def test_f065_r9_los_avisos_comparan_con_el_precio_del_contrato(blanca, contrato, esperado):
    """La ficha pinta el precio aplicado (120), pero ✓/⚠ siguen contra el del
    contrato (115): lo declarado (8 × 115 = 920) cuadra con el contrato."""
    assert _avisos(_blanca(**blanca), contrato) == esperado
