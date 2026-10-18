# tests/test_f075_ficha.py
"""F-075 · la ficha (vista merge): importe del albarán, valorado y diferencia
(R23), aviso de F-065 R21 con ``ruesma_comun.importes`` (R24), aprobar una
valoración directa (R9) y revalorar sin contrato (R10, ``-k r10``). El pie
(``-k pie``) se añade en T13.

Plantilla real con Jinja2 (``conftest.render_detalle``) y repositorio real
sobre SQLite. Sin red.
"""
from __future__ import annotations

import re

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from domain.models.review_models import (
    DocumentDetailPayload,
    MergeLinePayload,
    ValuationPayload,
)


def _doc(netos, *, valorado=None, con_filas=True, **campos):
    valoracion = None
    if valorado is not None:
        from domain.models.review_models import LineValuationPayload

        filas = {1: LineValuationPayload(valuation_line_id=1, merge_line_id=1, importe_calculado=valorado,
                                         importe_source="declared_albaran")} if con_filas else {}
        valoracion = ValuationPayload(valuation_id="v", status="ok", total_valorado=valorado,
                                      lines_by_merge_line_id=filas)
    return DocumentDetailPayload(
        id="f075-doc", source_filename="a.pdf", provider_origin="merge", model_name="m",
        created_at_utc="2026-10-15T08:00:00Z",
        lines=[MergeLinePayload(id=i + 1, line_index=i, concepto=f"L{i}", precio_neto=n)
               for i, n in enumerate(netos)],
        valuation=valoracion, **campos,
    )


def _bloque(html):
    m = re.search(r'<div class="alert importe-albaran"[^>]*>(.*?)</div>', html, re.S)
    assert m, "no se pinta el bloque del importe"
    return " ".join(m.group(1).split())


# ------------------------------------------------------------------ #
# R23 · el modelo
# ------------------------------------------------------------------ #
def test_f075_r23_importe_leido_de_las_lineas_del_merge():
    doc = _doc([100.0, None, 20.5])
    assert doc.importe_leido.total == 120.5
    assert doc.importe_leido.parcial is True
    assert doc.importe_parcial_texto == "1 de 3 sin importe"
    assert doc.importe_valorado is None and doc.importe_diferencia is None


def test_f075_r23_valorado_y_diferencia():
    doc = _doc([100.0], valorado=130.0)
    assert doc.importe_valorado == 130.0
    assert doc.importe_diferencia == 30.0
    igual = _doc([100.0], valorado=100.004)
    assert igual.importe_diferencia is None


def test_f075_r23_una_valoracion_sin_filas_no_es_un_valorado():
    doc = _doc([100.0], valorado=0.0, con_filas=False)
    assert doc.importe_valorado is None and doc.importe_diferencia is None


def test_f075_r23_sin_importes_no_hay_diferencia():
    doc = _doc([None], valorado=50.0)
    assert doc.importe_leido.trae_importes is False
    assert doc.importe_diferencia is None
    assert doc.importe_parcial_texto is None


# ------------------------------------------------------------------ #
# R23 · lo que pinta la plantilla
# ------------------------------------------------------------------ #
def test_f075_r23_bloque_con_importe_valorado_y_diferencia(render_detalle):
    html = render_detalle(_doc([100.0, None], valorado=130.0))
    bloque = _bloque(html)
    assert "Importe del albarán (sin IVA)" in bloque
    assert "100,00" in bloque and "1 de 2 sin importe" in bloque
    assert "Valorado" in bloque and "130,00" in bloque
    assert "Diferencia" in bloque and "30,00" in bloque


def test_f075_r23_bloque_sin_importes(render_detalle):
    bloque = _bloque(render_detalle(_doc([None, None])))
    assert "el albarán no trae importes" in bloque
    assert "Valorado" not in bloque


def test_f075_r23_bloque_solo_en_la_vista_merge(render_detalle):
    html = render_detalle(_doc([100.0], view_mode="openai", is_editable=False))
    assert 'class="alert importe-albaran"' not in html


def test_f075_r23_pie_de_la_tabla_de_lineas_leidas(render_detalle):
    html = render_detalle(_doc([100.0, 20.5]))
    tabla = html[html.index('id="albaran-lines-table"'):]
    tabla = tabla[:tabla.index("</table>")]
    pie = re.search(r"<tfoot>(.*?)</tfoot>", tabla, re.S).group(1)
    assert "Total leído (sin IVA)" in pie and "120,50" in pie


# ------------------------------------------------------------------ #
# R24 · el aviso de F-065 R21 con ruesma_comun.importes
# ------------------------------------------------------------------ #
def test_f075_r24_aviso_suma_usa_difieren_de_comun(monkeypatch):
    import domain.models.review_models as modelos

    llamadas = []

    def _difieren(a, b, umbral=0.01):
        llamadas.append((a, b))
        return False

    monkeypatch.setattr(modelos, "difieren", _difieren)
    assert modelos.aviso_suma_importes(1.0, 2.0) is None
    assert llamadas == [(1.0, 2.0)]


@pytest.mark.parametrize(("filas", "leida", "aviso"), [
    (100.0, 100.004, False), (100.0, 100.006, True), (None, 1.0, False), (1.0, None, False),
])
def test_f075_r24_aviso_suma_mismo_umbral(filas, leida, aviso):
    from domain.models.review_models import aviso_suma_importes

    assert (aviso_suma_importes(filas, leida) is not None) is aviso


def test_f075_r24_suma_leida_del_detalle_es_importe_albaran_de_comun():
    from tests.f065_bbdd import construir, ejecutar
    from tests.test_f065_f1_aprobar import _detalle

    motor = construir()
    ejecutar(motor, "UPDATE albaran_lines_merge SET precio_neto = NULL WHERE id = 703")
    detalle = _detalle(motor)
    assert detalle.suma_leida == pytest.approx(920.0 + 1150.0)
    assert detalle.importe_leido.parcial is True


# ------------------------------------------------------------------ #
# R9 · una valoración directa completa se aprueba; parcial, no
# ------------------------------------------------------------------ #
DIRECTA = "f075-directa-0000-0000-000000000001"


def _motor_directa(netos):
    """Un merge sin contrato con su valoración directa como la deja sv6."""
    from infrastructure.database.orm_models import Base

    from tests.f053_sv4_bbdd import DDL_ALTAS, _VALORACION, _merge

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    with Session(motor) as s:
        for sentencia in _VALORACION:
            s.execute(text(sentencia))
        s.execute(text(DDL_ALTAS))
        _merge(s, DIRECTA)
        s.execute(text(
            "INSERT INTO albaran_valuations (id, document_id, contrato_codigo, status, total_valorado, "
            "review_required) VALUES ('v-dir', :d, NULL, 'no_contract', :t, 0)"),
            {"d": DIRECTA, "t": sum(n for n in netos if n is not None)})
        for i, neto in enumerate(netos, start=1):
            s.execute(text(
                "INSERT INTO albaran_lines_merge (id, document_id, provider_origin, line_index, concepto, "
                "cantidad, precio_neto) VALUES (:id, :d, 'merge', :i, 'TUBO', 2.0, :n)"),
                {"id": 700 + i, "d": DIRECTA, "i": i, "n": neto})
            s.execute(text(
                "INSERT INTO contrato_lines_derived (id, created_by_valuation_id, source_document_id, "
                "codigo_contrato, descripcion_linea, unidad_medida, precio_unitario, codigo_partida, origen) "
                "VALUES (:id, 'v-dir', :d, '', 'TUBO', 'ml', 5.0, NULL, 'nueva_no_match')"),
                {"id": 900 + i, "d": DIRECTA})
            s.execute(text(
                "INSERT INTO albaran_line_valuations (id, valuation_id, merge_line_id, derived_contrato_line_id, "
                "precio_unitario_final, cantidad_albaran, cantidad_convertida, factor_conversion, "
                "importe_calculado, importe_source, partida_action, line_kind, descripcion_linea, "
                "unidad_albaran, unidad_contrato) VALUES (:id, 'v-dir', :m, :der, 5.0, 2.0, 2.0, 1.0, :n, "
                ":src, 'almacen_sin_partida', 'from_albaran', 'TUBO', 'ml', 'ml')"),
                {"id": 10 + i, "m": 700 + i, "der": 900 + i, "n": neto,
                 "src": "declared_albaran" if neto is not None else "none"})
        s.commit()
    return motor


def test_f075_r9_valoracion_directa_completa_se_aprueba():
    from tests.f053_sv4_bbdd import repositorio

    motor = _motor_directa([10.0, 5.0])
    assert repositorio(motor).set_approved(document_id=DIRECTA, approved=True, approved_by="ana") is True


def test_f075_r9_valoracion_directa_parcial_no_se_aprueba():
    from domain.models.alta_sigrid_models import AlbaranSinValorarError

    from tests.f053_sv4_bbdd import repositorio

    motor = _motor_directa([10.0, None])
    with pytest.raises(AlbaranSinValorarError):
        repositorio(motor).set_approved(document_id=DIRECTA, approved=True, approved_by="ana")


def test_f075_r9_ficha_boton_aprobar_habilitado_o_no(render_detalle):
    from domain.models.review_models import LineValuationPayload

    def _ficha(importes):
        filas = {i: LineValuationPayload(valuation_line_id=i, merge_line_id=i, importe_calculado=imp,
                                         importe_source="declared_albaran" if imp is not None else "none")
                 for i, imp in enumerate(importes, start=1)}
        doc = _doc([10.0, 5.0]).model_copy(update={"valuation": ValuationPayload(
            valuation_id="v-dir", status="no_contract", total_valorado=15.0, lines_by_merge_line_id=filas)})
        html = render_detalle(doc, valuation=doc.valuation)
        return re.search(r'<button[^>]*id="approve-btn"[^>]*>', html).group(0)

    assert "disabled" not in _ficha([10.0, 5.0])
    assert "disabled" in _ficha([10.0, None])
