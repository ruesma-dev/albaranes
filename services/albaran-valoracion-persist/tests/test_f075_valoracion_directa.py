# tests/test_f075_valoracion_directa.py
"""F-075 · valoración directa en sv6 (R5–R9) y aviso con contrato (R12).

Selección por palabra (``tasks.md``):

* ``r5 or r6 or r7 or r8`` — ``ValoracionDirectaBuilder`` con sobres de
  fixture (completo, parcial, sin importes, negativos, partida nula).
* ``pipeline`` — la rama ``no_contract`` del pipeline usa el builder y pasa
  por ``completar_registros`` (F-078) y ``NormalizadorPartidas.anotar`` (F-076).
* ``r12`` — con contrato, motivo ``valorado_distinto_de_albaran`` sin tocar
  importes.

Sin red, sin BBDD y sin LLM.
"""
from __future__ import annotations

import json

import pytest
from application.pipelines.run_valuation_pipeline import (
    RunValuationPipeline,
    RunValuationRequest,
)
from application.services.normalizador_partidas import NormalizadorPartidas
from application.services.valoracion_directa import ValoracionDirectaBuilder
from domain.models.valuation_envelope import (
    AlbaranLineContextDto,
    DocumentoValoracionDto,
    ValuationContextDto,
    ValuationEnvelope,
    ValuationEnvelopeMeta,
)
from domain.ports.valuation_repository import PersistedValuation
from ruesma_comun.valoracion import esta_valorado

from tests.f076_sobres import PuertoFalso

DOC = "dfdc8aab-08e1-49f0-978d-bb906515e748"


def _linea(mid, *, neto=None, precio=None, cantidad=2.0, dto=None, partida=None,
           descripcion="TUBO PVC 110", unidad="ml", importe=None):
    return AlbaranLineContextDto(
        merge_line_id=mid, line_index=mid, descripcion=descripcion, unidad_medida=unidad,
        cantidad=cantidad, precio_unitario_albaran=precio,
        importe_albaran=importe if importe is not None else neto,
        codigo_partida_albaran=partida, descuento_albaran=dto, precio_neto_albaran=neto,
    )


def _sobre(*lineas, status="no_contract"):
    return ValuationEnvelope(
        status=status,
        meta=ValuationEnvelopeMeta(document_id=DOC, codigo_contrato=None),
        data=DocumentoValoracionDto(lineas=[]),
        context=ValuationContextDto(lineas_albaran=list(lineas)),
    )


def _construir(*lineas):
    return ValoracionDirectaBuilder().construir(_sobre(*lineas), DOC)


# ------------------------------------------------------------------ #
# R5 · aplica y cabecera
# ------------------------------------------------------------------ #
def test_f075_r5_aplica_con_algun_importe_leido():
    assert ValoracionDirectaBuilder.aplica(_sobre(_linea(1, neto=10.0), _linea(2))) is True


def test_f075_r5_no_aplica_con_contrato():
    assert ValoracionDirectaBuilder.aplica(_sobre(_linea(1, neto=10.0), status="ok")) is False


def test_f075_r5_usa_el_precio_neto_puro_no_el_importe_derivado():
    # sv5 deriva importe_albaran = cantidad × precio; eso NO es un importe leído (P3).
    assert ValoracionDirectaBuilder.aplica(_sobre(_linea(1, precio=5.0, importe=10.0))) is False


def test_f075_r5_cabecera_de_la_valoracion_directa():
    cabecera, lineas = _construir(
        _linea(1, neto=100.0, precio=50.0), _linea(2, neto=20.5, precio=10.25),
    )
    assert cabecera.document_id == DOC
    assert cabecera.status == "no_contract"
    assert cabecera.contrato_codigo is None
    assert cabecera.provider_ia is None and cabecera.model_name is None
    assert cabecera.prompt_key == "valoracion_directa_albaran"
    assert cabecera.total_valorado == 120.5
    assert cabecera.total_lines == 2 == len(lineas)
    assert (cabecera.lines_matched_exact, cabecera.lines_matched_semantic,
            cabecera.lines_matched_price_only, cabecera.lines_unmatched) == (0, 0, 0, 2)
    assert cabecera.review_required is False
    assert cabecera.review_reasons == ["valoracion_directa_albaran"]
    assert [l.merge_line_id for l in lineas] == [1, 2]


def test_f075_r5_total_suma_solo_los_no_nulos_y_redondea_a_centimos():
    cabecera, _ = _construir(_linea(1, neto=10.004), _linea(2), _linea(3, neto=0.003))
    assert cabecera.total_valorado == 10.01


def test_f075_r5_negativos_suman_con_signo():
    cabecera, lineas = _construir(_linea(1, neto=100.0), _linea(2, neto=-30.0, cantidad=-1.0))
    assert cabecera.total_valorado == 70.0
    assert lineas[1].importe_calculado == -30.0
    assert lineas[1].precio_unitario_final == 30.0  # despejado: -30 / -1


# ------------------------------------------------------------------ #
# R6 · cada línea directa
# ------------------------------------------------------------------ #
def test_f075_r6_linea_completa():
    (_, (fila,)) = _construir(_linea(7, neto=35.19, precio=0.543, cantidad=108.0, dto=40.0, partida="CI.4.18"))
    assert fila.merge_line_id == 7
    assert fila.line_kind == "from_albaran"
    assert fila.importe_calculado == 35.19
    assert fila.importe_albaran_declarado == 35.19
    assert fila.importe_source == "declared_albaran"
    assert fila.cantidad_albaran == fila.cantidad_convertida == 108.0
    assert fila.factor_conversion == 1.0
    assert fila.unidad_albaran == fila.unidad_contrato == "ml"
    assert fila.unidad_category_match is True
    assert fila.precio_unitario_final == 0.543
    assert fila.precio_unitario_source == "albaran_declared"
    assert fila.precio_unitario_agreement == "neither"
    assert fila.precio_unitario_contrato_db is None and fila.precio_unitario_pdf_inferido is None
    assert fila.codigo_partida_albaran == fila.codigo_partida_final == "CI.4.18"
    assert fila.partida_action == "new_line_created"
    assert fila.matched_contrato_line_id is None
    assert fila.match_method == "no_match" and fila.match_confidence_pct == 0.0
    assert fila.descuento_albaran_aplicado == 40.0
    assert fila.review_required is False and fila.review_reasons == []
    derivada = fila.derived_contrato_line_record
    assert derivada.origen == "nueva_no_match"
    assert derivada.codigo_contrato == ""
    assert derivada.codigo_producto is None
    assert derivada.descripcion_linea == "TUBO PVC 110"
    assert derivada.unidad_medida == "ml"
    assert derivada.precio_unitario == 0.543
    assert derivada.codigo_partida == "CI.4.18"


def test_f075_r6_sin_unitario_se_despeja_del_importe_deshaciendo_el_descuento():
    (_, (fila,)) = _construir(_linea(1, neto=35.1864, cantidad=108.0, dto=40.0))
    assert fila.precio_unitario_final == pytest.approx(0.543)
    assert fila.precio_unitario_source == "albaran_calculated"
    assert fila.derived_contrato_line_record.precio_unitario == fila.precio_unitario_final


def test_f075_r6_unitario_cero_cuenta_como_ausente():
    (_, (fila,)) = _construir(_linea(1, neto=20.0, precio=0.0, cantidad=4.0))
    assert fila.precio_unitario_final == 5.0
    assert fila.precio_unitario_source == "albaran_calculated"


def test_f075_r6_sin_importe_ni_cantidad_unitario_nulo():
    (_, (fila,)) = _construir(_linea(1, neto=20.0, cantidad=None))
    assert fila.precio_unitario_final is None
    assert fila.precio_unitario_source == "none"


def test_f075_r6_partida_nula_o_en_blanco_es_almacen():
    _, filas = _construir(_linea(1, neto=1.0, partida=None), _linea(2, neto=1.0, partida="   "))
    for fila in filas:
        assert fila.codigo_partida_final is None
        assert fila.partida_action == "almacen_sin_partida"
        assert fila.derived_contrato_line_record.codigo_partida is None


def test_f075_r6_linea_sin_importe_a_revision():
    cabecera, (con, sin) = _construir(_linea(1, neto=10.0), _linea(2, precio=3.0, importe=6.0))
    assert sin.importe_calculado is None
    assert sin.importe_albaran_declarado is None
    assert sin.importe_source == "none"
    assert sin.review_required is True
    assert sin.review_reasons == ["sin_importe_en_albaran"]
    assert sin.precio_unitario_final == 3.0  # el leído se conserva
    assert con.review_required is False
    assert cabecera.review_required is True
    assert cabecera.review_reasons == ["valoracion_directa_albaran", "at_least_one_line_requires_review"]
    assert cabecera.total_valorado == 10.0


def test_f075_r6_descripcion_en_blanco_va_nula_en_la_derivada():
    (_, (fila,)) = _construir(_linea(1, neto=1.0, descripcion="  "))
    assert fila.derived_contrato_line_record.descripcion_linea is None


def test_f075_r6_cada_linea_lleva_su_propia_lista_de_motivos():
    _, (a, b) = _construir(_linea(1), _linea(2))
    assert a.review_reasons is not b.review_reasons


# ------------------------------------------------------------------ #
# R7 · sin IA ni sintéticas
# ------------------------------------------------------------------ #
def test_f075_r7_sin_sinteticas_ni_ia():
    cabecera, lineas = _construir(_linea(1, neto=1.0), _linea(2, neto=2.0), _linea(3, neto=3.0))
    assert [l.line_kind for l in lineas] == ["from_albaran"] * 3
    assert all(l.parent_merge_line_id is None and l.ia_reasoning is None for l in lineas)
    assert cabecera.provider_ia is None


# ------------------------------------------------------------------ #
# R8 · sin importes no aplica
# ------------------------------------------------------------------ #
def test_f075_r8_sin_ningun_importe_no_aplica():
    assert ValoracionDirectaBuilder.aplica(_sobre(_linea(1), _linea(2))) is False
    assert ValoracionDirectaBuilder.aplica(_sobre()) is False


# ------------------------------------------------------------------ #
# R9 · completa ⇒ «valorada»; parcial ⇒ no
# ------------------------------------------------------------------ #
def test_f075_r9_completa_esta_valorada_y_parcial_no():
    cab, lineas = _construir(_linea(1, neto=10.0), _linea(2, neto=5.0))
    assert esta_valorado(cab.status, [l.importe_calculado for l in lineas]) is True
    cab, lineas = _construir(_linea(1, neto=10.0), _linea(2))
    assert esta_valorado(cab.status, [l.importe_calculado for l in lineas]) is False
