# tests/test_f076_aviso_partida.py
"""F-076 T5b · el aviso ✓/⚠ de la partida compara por la clave de comun (R23–R25).

Con F-076, sv6 deja la partida de la línea de contrato o derivada casada en la
forma de la lista de la obra (``CI.4.18``) y conserva la leída (``CI.04.18``,
regla 6). El aviso de la fila compara esas dos: sin este cambio, cada línea
normalizada saldría ⚠. Ahora compara con ``ruesma_comun.sigrid.normalizar_partida``
(la misma clave con la que sv6 normaliza, sin copia):

- misma clave ⇒ ✓; clave distinta ⇒ ⚠; una de las dos vacía ⇒ sin icono (R23);
- misma clave pero distinta literalmente ⇒ nota «Normalizada: X → Y» en el
  ``title`` de la casilla de partida (R24);
- los avisos de cantidad, unitario e importe no cambian (R25).

Sin BBDD: ``_build_display_lines`` es estático y recibe los modelos ya hechos.
"""
from __future__ import annotations

import re

import pytest

from domain.models.review_models import (
    ConciliacionDisplay,
    LineValuationPayload,
    MergeLinePayload,
    ValuationPayload,
    coincide_partida,
)
from infrastructure.database.review_repository import AlbaranReviewRepository


# ------------------------------------------------------------------ #
# La función pura (dominio de sv4)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("declarada", "esperada", "resultado"),
    [
        ("CI.04.18", "CI.4.18", (True, "CI.04.18")),
        (" CI.04.18 ", "CI.4.18", (True, "CI.04.18")),
        ("CI.03A.02", "CI.03A.2", (True, "CI.03A.02")),
        ("ci.4.18", "CI.4.18", (True, "ci.4.18")),
        ("CI.4.18", "CI.4.18", (True, None)),
        (" CI.4.18 ", "CI.4.18 ", (True, None)),
        ("CI.14.18", "CI.4.18", (False, None)),
        ("03.02", "03.02.01", (False, None)),
        (None, "CI.4.18", (None, None)),
        ("   ", "CI.4.18", (None, None)),
        ("CI.04.18", None, (None, None)),
        ("CI.04.18", "", (None, None)),
        (None, None, (None, None)),
    ],
)
def test_f076_r23_coincide_partida(declarada, esperada, resultado):
    assert coincide_partida(declarada, esperada) == resultado


@pytest.mark.parametrize(
    ("declarada", "esperada", "resultado"),
    [("-", "-", (True, None)), ("-", ".", (False, None)), ("./", "CI.4.18", (False, None))],
)
def test_f076_r23_sin_clave_compara_literal_como_hoy(declarada, esperada, resultado):
    """Texto no vacío pero sin nada alfanumérico: ni clave ni ✓ por accidente."""
    assert coincide_partida(declarada, esperada) == resultado


def test_f076_r23_usa_la_clave_de_comun_sin_copia():
    from pathlib import Path

    from domain.models import review_models

    fuente = Path(review_models.__file__).read_text(encoding="utf-8")
    assert "from ruesma_comun.sigrid import normalizar_partida" in fuente
    assert "lstrip(\"0\")" not in fuente and "NFKC" not in fuente


# ------------------------------------------------------------------ #
# La fila de conciliación (repositorio)
# ------------------------------------------------------------------ #
def _conc(casada: str | None, **campos) -> ConciliacionDisplay:
    base = {
        "kind": "assigned",
        "codigo_partida": casada,
        "codigo_partida_casada": casada,
        "estado_partida": "partida",
        "descripcion": "COSTES INDIRECTOS",
        "unidad": "UD",
        "unitario": 10.0,
        "unitario_contrato": 10.0,
        "descripcion_partida": "Costes indirectos de obra",
    }
    base.update(campos)
    return ConciliacionDisplay(**base)


def _valoracion(*lineas: LineValuationPayload) -> ValuationPayload:
    return ValuationPayload(
        valuation_id="val-f076",
        status="completed",
        lines_by_merge_line_id={ln.merge_line_id: ln for ln in lineas if ln.merge_line_id is not None},
        synthetic_lines=[ln for ln in lineas if ln.merge_line_id is None],
    )


def _linea(id_: int, merge_line_id: int | None, final: str | None, **campos) -> LineValuationPayload:
    base = {
        "valuation_line_id": id_,
        "merge_line_id": merge_line_id,
        "codigo_partida_final": final,
        "precio_unitario_final": 10.0,
        "cantidad_albaran": 2.0,
        "importe_calculado": 20.0,
    }
    base.update(campos)
    return LineValuationPayload(**base)


def _fila_con_blanca(leida: str | None, casada: str | None, *, precio=10.0, precio_neto=20.0):
    (fila,) = AlbaranReviewRepository._build_display_lines(
        merge_lines=[MergeLinePayload(id=701, codigo_imputacion=leida, concepto="CI", cantidad=2.0,
                                      precio=precio, precio_neto=precio_neto)],
        valuation=_valoracion(_linea(17, 701, casada)),
        conciliation_by_valuation_line_id={17: _conc(casada)},
    )
    return fila.concilia


def _fila_sin_blanca(final: str | None, casada: str | None):
    filas = AlbaranReviewRepository._build_display_lines(
        merge_lines=[],
        valuation=_valoracion(_linea(18, None, final, line_kind="manual")),
        conciliation_by_valuation_line_id={18: _conc(casada)},
    )
    (fila,) = [f for f in filas if f.valuation_line_id == 18]
    return fila.concilia


def test_f076_r23_leida_normalizada_es_coincidente():
    """Leída ``CI.04.18`` frente a la casada ``CI.4.18``: hoy ⚠ (False), debe ser ✓."""
    conc = _fila_con_blanca("CI.04.18", "CI.4.18")
    assert conc.agree_partida is True
    assert conc.partida_normalizada_desde == "CI.04.18"


def test_f076_r23_clave_distinta_sigue_aviso():
    conc = _fila_con_blanca("CI.14.18", "CI.4.18")
    assert conc.agree_partida is False
    assert conc.partida_normalizada_desde is None


def test_f076_r23_iguales_literalmente_sin_nota():
    conc = _fila_con_blanca("CI.4.18", "CI.4.18")
    assert conc.agree_partida is True
    assert conc.partida_normalizada_desde is None


@pytest.mark.parametrize(("leida", "casada"), [(None, "CI.4.18"), ("  ", "CI.4.18"), ("CI.04.18", None)])
def test_f076_r23_una_vacia_sin_icono(leida, casada):
    conc = _fila_con_blanca(leida, casada)
    assert conc.agree_partida is None
    assert conc.partida_normalizada_desde is None


def test_f076_r23_sin_linea_del_albaran_compara_la_final():
    conc = _fila_sin_blanca("CI.04.18", "CI.4.18")
    assert conc.agree_partida is True
    assert conc.partida_normalizada_desde == "CI.04.18"
    distinta = _fila_sin_blanca("CI.14.18", "CI.4.18")
    assert (distinta.agree_partida, distinta.partida_normalizada_desde) == (False, None)
    igual = _fila_sin_blanca("CI.4.18", "CI.4.18")
    assert (igual.agree_partida, igual.partida_normalizada_desde) == (True, None)


def test_f076_r23_almacen_sin_icono():
    (fila,) = AlbaranReviewRepository._build_display_lines(
        merge_lines=[MergeLinePayload(id=701, codigo_imputacion="CI.04.18", concepto="CI", cantidad=2.0)],
        valuation=_valoracion(_linea(17, 701, None)),
        conciliation_by_valuation_line_id={17: _conc("CI.4.18", estado_partida="almacen", codigo_partida=None)},
    )
    assert fila.concilia.agree_partida is None
    assert fila.concilia.partida_normalizada_desde is None


# ------------------------------------------------------------------ #
# R25 · los demás avisos no cambian
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("leida", ["CI.04.18", "CI.4.18", "CI.14.18", None])
@pytest.mark.parametrize(
    ("precio", "precio_neto", "esperado"),
    [(10.0, 20.0, (True, True, True)), (12.0, 24.0, (True, False, False)), (None, None, (True, None, None))],
)
def test_f076_r25_otros_avisos_igual(leida, precio, precio_neto, esperado):
    conc = _fila_con_blanca(leida, "CI.4.18", precio=precio, precio_neto=precio_neto)
    assert (conc.agree_cantidad, conc.agree_unitario, conc.agree_importe) == esperado


def test_f076_r25_sinteticas_otros_avisos_igual():
    for final in ("CI.04.18", "CI.4.18", "CI.14.18"):
        conc = _fila_sin_blanca(final, "CI.4.18")
        assert (conc.agree_cantidad, conc.agree_unitario, conc.agree_importe) == (True, True, True)


# ------------------------------------------------------------------ #
# R24 · la nota en el ``title`` de la casilla de partida (render real)
# ------------------------------------------------------------------ #
def _casilla_partida(html: str) -> str:
    inicio = html.index('class="concilia-td" data-col="partida"')
    return html[inicio:html.index("</td>", inicio)]


def _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion, *, editable):
    """``editable=False``: la fila guardada (bloqueada, F-065 R13) sale en solo
    lectura; es la rama de los ``<span>`` de la casilla (L750 y L752)."""
    return _casilla_partida(render_detalle(documento_detalle(
        lineas_valoracion=[linea_valorada(codigo_partida_final="CI.4.18", bloqueada=not editable)],
        display=[fila_detalle(conciliacion=conciliacion)],
    )))


@pytest.mark.parametrize("editable", [True, False])
def test_f076_r24_title_nota_normalizada(render_detalle, documento_detalle, fila_detalle, linea_valorada, editable):
    conciliacion = _fila_con_blanca("CI.04.18", "CI.4.18").model_dump()
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=editable)
    assert "cedit-warn" not in casilla and "concilia-price-warn" not in casilla
    (title,) = re.findall(r'title="([^"]*)"', casilla)
    assert title == "Costes indirectos de obra · Normalizada: CI.04.18 → CI.4.18"


@pytest.mark.parametrize("editable", [True, False])
def test_f076_r24_sin_descripcion_solo_la_nota(render_detalle, documento_detalle, fila_detalle, linea_valorada,
                                               editable):
    conciliacion = {**_fila_con_blanca("CI.04.18", "CI.4.18").model_dump(), "descripcion_partida": None}
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=editable)
    assert re.findall(r'title="([^"]*)"', casilla) == ["Normalizada: CI.04.18 → CI.4.18"]


@pytest.mark.parametrize("leida", ["CI.4.18", "CI.14.18"])
@pytest.mark.parametrize("editable", [True, False])
def test_f076_r24_literal_o_aviso_sin_nota(render_detalle, documento_detalle, fila_detalle, linea_valorada,
                                           leida, editable):
    conciliacion = _fila_con_blanca(leida, "CI.4.18").model_dump()
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=editable)
    assert "Normalizada" not in casilla
    assert re.findall(r'title="([^"]*)"', casilla) == ["Costes indirectos de obra"]
    if leida == "CI.14.18":
        assert ("cedit-warn" if editable else "concilia-price-warn") in casilla


def test_f076_r24_la_nota_va_escapada(render_detalle, documento_detalle, fila_detalle, linea_valorada):
    conciliacion = {**_fila_con_blanca("CI.04.18", "CI.4.18").model_dump(),
                    "partida_normalizada_desde": '"><b>x'}
    casilla = _render(render_detalle, documento_detalle, fila_detalle, linea_valorada, conciliacion,
                      editable=True)
    assert "<b>" not in casilla and "&#34;&gt;&lt;b&gt;x" in casilla
