# tests/test_f077_aviso_partida.py
"""F-077 · C · el ⚠ de la partida, solo con lectura del albarán y con tooltip.

- R21: la casilla en ``cedit-warn`` y el ⚠ de solo lectura solo en filas con
  línea del albarán (``from_albaran``) de origen Contrato con
  ``agree_partida`` false; nunca en sintéticas, ``manual``, ``reparto`` ni
  Nueva.
- R22: donde hay ⚠, el ``title`` lleva «No coincide con la partida leída en el
  albarán (<leída>)» tras la descripción de la partida. Separador « · », el
  mismo de la nota «Normalizada» de F-076 (decisión al fusionar F-076: el
  ``title`` queda «descripción · [nota F-076] · [aviso F-077]»).
- R23: ``agree_partida`` y el ✓ no cambian; el aviso «Partida no válida…» de
  F-065 R27 v5 sustituye el ``title`` y, al corregir, vuelve el de R22.
"""
from __future__ import annotations

import re

import pytest
from domain.models import review_models
from domain.models.review_models import (
    ConciliacionDisplay,
    LineValuationPayload,
    MergeLinePayload,
    ValuationPayload,
)
from infrastructure.database.review_repository import AlbaranReviewRepository
from test_f065_f1_js import con_node
from test_f065_f3bis_front import _COMBO_V4, _GUARDAR, _ejecutar_dom, _fila_guardar

_AVISO = "No coincide con la partida leída en el albarán (CI.14.18)"


# ------------------------------------------------------------------ #
# R21, R22 · la función pura
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("agree", "kind", "leida", "esperado"),
    [
        (False, "assigned", "CI.14.18", _AVISO),
        (False, "assigned", "  CI.14.18  ", _AVISO),       # recortada
        (False, "derived", "CI.14.18", None),               # Nueva: la insignia ya lo dice
        (False, "assigned", None, None),                    # sin lectura del albarán
        (False, "assigned", "   ", None),
        (True, "assigned", "CI.14.18", None),
        (None, "assigned", "CI.14.18", None),
        (False, None, "CI.14.18", None),
    ],
)
def test_f077_r21_aviso_partida_texto(agree, kind, leida, esperado):
    assert review_models.aviso_partida_texto(agree, kind=kind, leida=leida) == esperado


# ------------------------------------------------------------------ #
# R21 · el repositorio: con blanca sí, sin blanca nunca
# ------------------------------------------------------------------ #
def _conc(casada: str | None, **campos) -> ConciliacionDisplay:
    base = {
        "kind": "assigned",
        "codigo_partida": casada,
        "codigo_partida_casada": casada,
        "estado_partida": "partida",
        "descripcion": "COSTES INDIRECTOS",
        "unitario": 10.0,
        "unitario_contrato": 10.0,
        "descripcion_partida": "Costes indirectos de obra",
    }
    base.update(campos)
    return ConciliacionDisplay(**base)


def _valoracion(*lineas: LineValuationPayload) -> ValuationPayload:
    return ValuationPayload(
        valuation_id="val-f077",
        status="completed",
        lines_by_merge_line_id={ln.merge_line_id: ln for ln in lineas if ln.merge_line_id is not None},
        synthetic_lines=[ln for ln in lineas if ln.merge_line_id is None],
    )


def _linea(id_: int, merge_line_id: int | None, final: str | None, **campos) -> LineValuationPayload:
    base = {"valuation_line_id": id_, "merge_line_id": merge_line_id, "codigo_partida_final": final,
            "precio_unitario_final": 10.0, "cantidad_albaran": 2.0, "importe_calculado": 20.0}
    base.update(campos)
    return LineValuationPayload(**base)


def _con_blanca(leida, casada, **conc):
    (fila,) = AlbaranReviewRepository._build_display_lines(
        merge_lines=[MergeLinePayload(id=701, codigo_imputacion=leida, concepto="CI", cantidad=2.0)],
        valuation=_valoracion(_linea(17, 701, casada)),
        conciliation_by_valuation_line_id={17: _conc(casada, **conc)},
    )
    return fila.concilia


def _sin_blanca(final, casada, line_kind):
    filas = AlbaranReviewRepository._build_display_lines(
        merge_lines=[],
        valuation=_valoracion(_linea(18, None, final, line_kind=line_kind)),
        conciliation_by_valuation_line_id={18: _conc(casada)},
    )
    (fila,) = [f for f in filas if f.valuation_line_id == 18]
    return fila.concilia


def test_f077_r21_repositorio_contrato_con_lectura_distinta_lleva_aviso():
    conc = _con_blanca("CI.14.18", "CI.4.18")
    assert conc.agree_partida is False
    assert conc.aviso_partida == _AVISO


@pytest.mark.parametrize(("leida", "casada"), [("CI.4.18", "CI.4.18"), ("CI.04.18", "CI.4.18"), (None, "CI.4.18")])
def test_f077_r23_repositorio_sin_aviso_si_coincide_o_no_hay_lectura(leida, casada):
    conc = _con_blanca(leida, casada)
    assert conc.aviso_partida is None


def test_f077_r21_repositorio_nueva_con_lectura_distinta_sin_aviso():
    conc = _con_blanca("CI.14.18", "CI.4.18", kind="derived")
    assert conc.agree_partida is False  # R23: el cálculo no cambia
    assert conc.aviso_partida is None


@pytest.mark.parametrize("line_kind", ["manual", "reparto", "synthetic_modifier", None])
def test_f077_r21_repositorio_sin_blanca_nunca_aviso(line_kind):
    conc = _sin_blanca("CI.14.18", "CI.4.18", line_kind)
    assert conc.agree_partida is False  # R23: el cálculo no cambia
    assert conc.aviso_partida is None


# ------------------------------------------------------------------ #
# R21, R22 · la plantilla (editable y de solo lectura)
# ------------------------------------------------------------------ #
def _casilla_partida(html: str) -> str:
    inicio = html.index('class="concilia-td" data-col="partida"')
    return html[inicio:html.index("</td>", inicio)]


def _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion, *, editable,
            line_kind="from_albaran"):
    merge = 500 if line_kind == "from_albaran" else None
    return _casilla_partida(render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(merge_line_id=merge, codigo_partida_final="CI.4.18",
                                          bloqueada=not editable)],
        display=[fila_detalle(conciliacion=conciliacion, line_kind=line_kind, merge_line_id=merge)],
    )))


@pytest.mark.parametrize("editable", [True, False])
def test_f077_r22_title_con_descripcion_y_aviso(render_detalle, documento_detalle, fila_detalle, linea_valorada,
                                                editable):
    conciliacion = _con_blanca("CI.14.18", "CI.4.18").model_dump()
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=editable)
    assert ("cedit-warn" if editable else "concilia-price-warn") in casilla
    (title,) = re.findall(r'title="([^"]*)"', casilla)
    assert title == "Costes indirectos de obra · " + _AVISO


@pytest.mark.parametrize("editable", [True, False])
def test_f077_r22_sin_descripcion_solo_el_aviso(render_detalle, documento_detalle, fila_detalle, linea_valorada,
                                               editable):
    conciliacion = {**_con_blanca("CI.14.18", "CI.4.18").model_dump(), "descripcion_partida": None}
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=editable)
    assert re.findall(r'title="([^"]*)"', casilla) == [_AVISO]


@pytest.mark.parametrize("line_kind", ["manual", "reparto", "synthetic_modifier"])
@pytest.mark.parametrize("editable", [True, False])
def test_f077_r21_sin_blanca_con_agree_false_sin_aviso(render_detalle, documento_detalle, fila_detalle,
                                                       linea_valorada, editable, line_kind):
    conciliacion = _sin_blanca("CI.14.18", "CI.4.18", line_kind).model_dump()
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=editable, line_kind=line_kind)
    assert "cedit-warn" not in casilla and "concilia-price-warn" not in casilla and "⚠" not in casilla
    assert re.findall(r'title="([^"]*)"', casilla) == ["Costes indirectos de obra"]


@pytest.mark.parametrize("editable", [True, False])
def test_f077_r21_nueva_con_agree_false_sin_aviso(render_detalle, documento_detalle, fila_detalle, linea_valorada,
                                                  editable):
    conciliacion = _con_blanca("CI.14.18", "CI.4.18", kind="derived").model_dump()
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=editable)
    assert "cedit-warn" not in casilla and "concilia-price-warn" not in casilla
    assert re.findall(r'title="([^"]*)"', casilla) == ["Costes indirectos de obra"]


@pytest.mark.parametrize("editable", [True, False])
def test_f077_r23_con_check_ni_aviso_ni_cambio(render_detalle, documento_detalle, fila_detalle, linea_valorada,
                                               editable):
    conciliacion = _con_blanca("CI.4.18", "CI.4.18").model_dump()
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=editable)
    assert "No coincide" not in casilla
    if editable:
        assert "cedit-ok" in casilla
    assert re.findall(r'title="([^"]*)"', casilla) == ["Costes indirectos de obra"]


def test_f077_r22_el_aviso_va_escapado(render_detalle, documento_detalle, fila_detalle, linea_valorada):
    conciliacion = {**_con_blanca("CI.14.18", "CI.4.18").model_dump(), "aviso_partida": '"><b>x'}
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=True)
    assert "<b>" not in casilla and "&#34;&gt;&lt;b&gt;x" in casilla


# ------------------------------------------------------------------ #
# R23 · «Partida no válida…» sustituye el title y, al corregir, vuelve el de R22
# ------------------------------------------------------------------ #
@con_node
def test_f077_r23_marcar_partida_devuelve_el_title_con_el_aviso(tmp_path):
    casos = _ejecutar_dom(tmp_path, _COMBO_V4 + _GUARDAR, _fila_guardar() + """
        part.title = "Cimentación · No coincide con la partida leída en el albarán (01.10)";
    """, """
        lista();
        part.value = "zzzz";
        part.dispatchEvent(new Event("input", {bubbles: true}));
        guardar.click();
        await tiempo();
        const mala = part.title;
        teclear(part, "02.03");
        console.log(JSON.stringify({mala: mala, corregida: part.title}));
    """)

    assert casos == {"mala": "Partida no válida: elige una de la lista (vacía = almacén)",
                     "corregida": "Cimentación · No coincide con la partida leída en el albarán (01.10)"}
