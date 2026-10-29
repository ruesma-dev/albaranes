# tests/test_f106_ficha.py
"""F-106 R13–R15: lo que la ficha enseña de cada fila.

- R13: «≠ albarán: 104,16» bajo el importe de una fila con blanca cuyo importe ya
  no es el del albarán (informativo; las partes de un reparto no lo llevan).
- R14: la fila que no cuadra, en rojo con su cuenta en el ``title`` y los botones
  «Recalcular importe» y «Recalcular precio» (desactivados si la fila está
  bloqueada o el albarán aprobado).
- R15: «A Sigrid: 48 × 2,17 €» en el ``title`` del precio y visible si difiere de
  P; el precio con los decimales guardados, hasta 6, sin ceros finales y al
  menos 2.

Dominio puro, repositorio real sobre SQLite (``f065_bbdd``) y la plantilla real
con Jinja2 (``render_detalle``). Sin red ni BBDD real.
"""
from __future__ import annotations

import re

import pytest
from f065_bbdd import DOC, repositorio
from test_f106_fila import FILA, _patch, cecois

from domain.models.review_models import (
    a_sigrid_de_fila,
    aviso_importe_albaran,
    precio_es,
    precio_input,
    texto_cuadre,
)

CUADRE_CECOIS = "48 × 11,20 × (1 − 7 %) = 499,97 ≠ 104,16"


# =================================================================== #
# Dominio
# =================================================================== #
@pytest.mark.parametrize(("valor", "entrada", "es"), [
    (120.0, "120.00", "120,00"),
    (11.2, "11.20", "11,20"),
    (2.333333, "2.333333", "2,333333"),
    (115.12345, "115.12345", "115,12345"),
    (2.3333333333, "2.333333", "2,333333"),
    (1234.5, "1234.50", "1.234,50"),
    (-9.0, "-9.00", "-9,00"),
    (-0.5, "-0.50", "-0,50"),          # abono por debajo de 1 €: conserva el signo
    (-0.0000001, "0.00", "0,00"),      # redondea a cero: sin «-0»
    (None, "", "—"),
])
def test_f106_r15_precio_hasta_seis_decimales_sin_ceros_y_al_menos_dos(valor, entrada, es):
    assert precio_input(valor) == entrada
    assert precio_es(valor) == es


def test_f106_r14_texto_de_la_cuenta():
    assert texto_cuadre(cantidad=48.0, precio=11.2, descuento=7.0, importe=104.16) == CUADRE_CECOIS


def test_f106_r14_el_importe_se_redondea_una_sola_vez_a_centimos():
    # 0,3749999 ⇒ 0,37 (redondear antes a milésimas daría 0,375 ⇒ 0,38).
    assert texto_cuadre(cantidad=1.0, precio=1.0, descuento=None, importe=0.3749999).endswith("≠ 0,37")


def test_f106_r14_texto_sin_descuento_aplicable():
    assert texto_cuadre(cantidad=6.0, precio=70.0, descuento=None, importe=410.4) == (
        "6 × 70,00 = 420,00 ≠ 410,40")
    assert texto_cuadre(cantidad=6.0, precio=70.0, descuento=0.0, importe=410.4) == (
        "6 × 70,00 = 420,00 ≠ 410,40")


def test_f106_r14_texto_con_cantidad_decimal():
    assert texto_cuadre(cantidad=2.5, precio=4.0, descuento=12.5, importe=1.0) == (
        "2,5 × 4,00 × (1 − 12,5 %) = 8,75 ≠ 1,00")


@pytest.mark.parametrize(("importe", "albaran", "esperado"), [
    (499.97, 104.16, "≠ albarán: 104,16"),
    (104.16, 104.16, None),
    (104.17, 104.16, "≠ albarán: 104,16"),
    (104.16, None, None),
    (None, 104.16, None),
    (1500.0, 1234.5, "≠ albarán: 1.234,50"),
])
def test_f106_r13_aviso_de_importe_distinto_del_albaran(importe, albaran, esperado):
    assert aviso_importe_albaran(importe, albaran) == esperado


def test_f106_r15_a_sigrid_de_la_fila_de_produccion():
    a = a_sigrid_de_fila(vinculada=True, cantidad_albaran=48.0, cantidad_convertida=48.0,
                         precio=2.333333, importe=104.16)
    assert (a.texto, a.difiere, a.factor) == ("A Sigrid: 48 × 2,17 €", True, 1.0)


def test_f106_r15_a_sigrid_igual_que_p_no_difiere():
    a = a_sigrid_de_fila(vinculada=False, cantidad_albaran=10.0, cantidad_convertida=None,
                         precio=11.2, importe=112.0)
    assert (a.texto, a.difiere) == ("A Sigrid: 10 × 11,20 €", False)


def test_f106_r15_a_sigrid_con_la_cantidad_que_manda_sv9():
    # Sin vincular va la del albarán (6 m³); la ficha edita la convertida (1).
    a = a_sigrid_de_fila(vinculada=False, cantidad_albaran=6.0, cantidad_convertida=1.0,
                         precio=120.0, importe=120.0)
    assert (a.texto, a.difiere, a.factor) == ("A Sigrid: 6 × 20,00 €", True, 6.0)


def test_f106_r15_a_sigrid_negativa_lleva_el_signo_del_importe():
    a = a_sigrid_de_fila(vinculada=False, cantidad_albaran=2.0, cantidad_convertida=None,
                         precio=9.0, importe=-18.0)
    assert (a.texto, a.difiere, a.factor) == ("A Sigrid: -2 × 9,00 €", False, -1.0)


@pytest.mark.parametrize("importe", [0.0, None])
def test_f106_r15_sin_a_sigrid_si_no_es_a_registrar(importe):
    assert a_sigrid_de_fila(vinculada=False, cantidad_albaran=2.0, cantidad_convertida=None,
                            precio=9.0, importe=importe) is None


def test_f106_r15_sin_a_sigrid_sin_cantidad():
    assert a_sigrid_de_fila(vinculada=False, cantidad_albaran=0.0, cantidad_convertida=None,
                            precio=9.0, importe=18.0) is None


# =================================================================== #
# Repositorio (la vista de la ficha)
# =================================================================== #
def _fila_de_la_ficha(motor, vid=FILA):
    detalle = repositorio(motor).get_document_detail(DOC)
    return next(d for d in detalle.display_lines if d.valuation_line_id == vid)


def test_f106_r14_r15_la_fila_de_produccion_en_la_vista():
    c = _fila_de_la_ficha(cecois(q=48.0)).concilia

    assert c.cuadra is False
    assert c.cuadre_texto == CUADRE_CECOIS
    assert c.a_sigrid == "A Sigrid: 48 × 2,17 €"
    assert c.a_sigrid_difiere is True
    assert c.factor_alta == 1.0
    # El importe sigue siendo el del albarán: sin «≠ albarán».
    assert (c.importe_albaran, c.aviso_importe) == (104.16, None)


def test_f106_r13_tras_cambiar_la_cantidad_el_importe_ya_no_es_el_del_albaran():
    motor = cecois()
    _patch(motor, {"cantidad": 48.0})
    c = _fila_de_la_ficha(motor).concilia

    assert c.cuadra is True and c.cuadre_texto is None
    assert c.aviso_importe == "≠ albarán: 104,16"
    # sv9 manda round(499,97 / 48, 6).
    assert c.a_sigrid == "A Sigrid: 48 × 10,416042 €"


def test_f106_r15_tras_despejar_el_precio_a_sigrid_coincide():
    motor = cecois(q=48.0)
    # El importe ya es 104,16: teclearlo igual no es un cambio; el botón, sí.
    _patch(motor, cuadrar="precio")
    c = _fila_de_la_ficha(motor).concilia

    assert c.unitario == pytest.approx(2.333333)
    assert c.cuadra is True
    assert c.a_sigrid == "A Sigrid: 48 × 2,17 €"


def test_f106_r14_la_que_cuadra_no_lleva_cuenta():
    c = _fila_de_la_ficha(cecois()).concilia
    assert (c.cuadra, c.cuadre_texto, c.aviso_importe) == (True, None, None)


def test_f106_r14_no_comparable_ni_rojo_ni_cuenta():
    from f065_bbdd import ejecutar

    motor = cecois(q=48.0)
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = NULL "
             "WHERE id = :v", v=FILA)
    c = _fila_de_la_ficha(motor).concilia
    assert (c.cuadra, c.cuadre_texto) == (None, None)


def test_f106_r14_importe_cero_no_es_a_registrar_ni_rojo():
    c = _fila_de_la_ficha(cecois(q=48.0, importe=0.0)).concilia
    assert (c.cuadra, c.a_sigrid) == (None, None)


def test_f106_r13_las_partes_de_un_reparto_no_llevan_el_aviso():
    from f065_bbdd import linea
    from sqlalchemy.orm import Session

    motor = cecois(q=6.0, importe=62.5, source="calculated")
    with Session(motor) as s:
        linea(s, id=15, line_kind="reparto", merge_line_id=None, parent_merge_line_id=704,
              matched_contrato_line_id=504, precio_unitario_final=11.2,
              descuento_albaran_aplicado=7.0, cantidad_albaran=4.0, cantidad_convertida=4.0,
              importe_calculado=41.66, importe_source="calculated",
              codigo_partida_final="01.04", descripcion_linea="TUBO PVC 110")
        s.commit()
    c = _fila_de_la_ficha(motor).concilia
    assert c.aviso_importe is None and c.importe_albaran is None


# =================================================================== #
# Plantilla
# =================================================================== #
def _aprobado(documento):
    """Aprobado = la tabla en solo lectura (F-065 R4)."""
    return documento.model_copy(update={"approved": True})


def _tr_salmon(html):
    return re.search(r'<tr class="conciliacion-row salmon-row[^"]*"[^>]*>', html).group(0)


def _no_cuadra(**extra):
    return {"cuadra": False, "cuadre_texto": CUADRE_CECOIS, **extra}


def test_f106_r14_plantilla_fila_en_rojo_con_la_cuenta_y_los_botones(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion=_no_cuadra())],
    ))

    tr = _tr_salmon(html)
    assert "fila-no-cuadra" in tr and 'data-cuadra="0"' in tr
    assert f'title="{CUADRE_CECOIS}"' in html
    botones = re.findall(r'<button[^>]*js-cuadrar[^>]*>[^<]*</button>', html)
    assert [re.search(r'data-cuadrar="(\w+)"', b).group(1) for b in botones] == ["importe", "precio"]
    assert ">Recalcular importe<" in botones[0] and ">Recalcular precio<" in botones[1]
    assert not any("disabled" in b for b in botones)


def test_f106_r14_plantilla_botones_desactivados_si_bloqueada(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(bloqueada=True)],
        display=[fila_detalle(conciliacion=_no_cuadra())],
    ))
    botones = re.findall(r'<button[^>]*js-cuadrar[^>]*>', html)
    assert len(botones) == 2 and all("disabled" in b for b in botones)


def test_f106_r14_plantilla_botones_desactivados_si_aprobado(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(_aprobado(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion=_no_cuadra())],
    )))
    botones = re.findall(r'<button[^>]*js-cuadrar[^>]*>', html)
    assert len(botones) == 2 and all("disabled" in b for b in botones)
    assert "fila-no-cuadra" in _tr_salmon(html)


def test_f106_r14_plantilla_la_que_cuadra_sin_rojo_ni_botones(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"cuadra": True})],
    ))
    tr = _tr_salmon(html)
    assert "fila-no-cuadra" not in tr and 'data-cuadra="1"' in tr
    assert "js-cuadrar" not in html


def test_f106_r13_plantilla_aviso_bajo_el_importe(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(importe_calculado=499.97)],
        display=[fila_detalle(conciliacion={"importe_albaran": 104.16,
                                            "aviso_importe": "≠ albarán: 104,16"})],
    ))
    entrada = re.search(r'<input[^>]*data-field="importe"[^>]*>', html).group(0)
    assert 'data-importe-albaran="104.16"' in entrada
    aviso = re.search(r'<span[^>]*js-aviso-importe[^>]*>[^<]*</span>', html).group(0)
    assert ">≠ albarán: 104,16<" in aviso and "hidden" not in aviso
    assert 'title="El importe ya no es el del albarán (104,16 €)"' in aviso


def test_f106_r13_plantilla_sin_aviso_el_hueco_queda_oculto_para_el_js(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"importe_albaran": 120.0})],
    ))
    aviso = re.search(r'<span[^>]*js-aviso-importe[^>]*>', html).group(0)
    assert "hidden" in aviso


def test_f106_r13_plantilla_sin_blanca_no_hay_hueco_de_aviso(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle()],
    ))
    assert "js-aviso-importe" not in html
    assert "data-importe-albaran" not in html


def test_f106_r15_plantilla_a_sigrid_visible_si_difiere(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={
            "unitario": 2.333333, "a_sigrid": "A Sigrid: 48 × 2,17 €",
            "a_sigrid_difiere": True, "factor_alta": 1.0})],
    ))
    entrada = re.search(r'<input[^>]*data-field="precio_unitario"[^>]*>', html).group(0)
    assert 'value="2.333333"' in entrada
    assert "A Sigrid: 48 × 2,17 €" in entrada and 'data-factor-alta="1.0"' in entrada
    visible = re.search(r'<span[^>]*js-a-sigrid[^>]*>[^<]*</span>', html).group(0)
    assert ">A Sigrid: 48 × 2,17 €<" in visible and "hidden" not in visible


def test_f106_r15_plantilla_a_sigrid_igual_solo_en_el_title(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={
            "a_sigrid": "A Sigrid: 1 × 120,00 €", "a_sigrid_difiere": False,
            "factor_alta": 1.0})],
    ))
    entrada = re.search(r'<input[^>]*data-field="precio_unitario"[^>]*>', html).group(0)
    assert "A Sigrid: 1 × 120,00 €" in entrada
    visible = re.search(r'<span[^>]*js-a-sigrid[^>]*>', html).group(0)
    assert "hidden" in visible


def test_f106_r15_plantilla_precio_a_seis_decimales_en_solo_lectura(
    render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    html = render_detalle(_aprobado(documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"unitario": 2.333333})],
    )))
    assert "2,333333 €" in html
