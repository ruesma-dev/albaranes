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


# ------------------------------------------------------------------ #
# T3 · pipeline: la rama no_contract usa el builder (R5, R8, R9, R10)
# ------------------------------------------------------------------ #
class _Repositorio:
    def __init__(self, *, obra="0686", existente=False):
        self.obra = obra
        self.existente = existente
        self.guardados = []

    def get_by_document_id(self, *, document_id):
        if not self.existente:
            return None
        from domain.ports.valuation_repository import ExistingValuationSummary

        return ExistingValuationSummary(
            valuation_id="val-viejo", document_id=document_id, contrato_codigo=None, status="no_contract",
            total_valorado=0.0, total_lines=0, review_required=True, created_at_utc="x", updated_at_utc=None,
        )

    def obra_del_documento(self, *, document_id):
        return self.obra

    def replace_valuation(self, *, header, lines):
        self.guardados.append((header, list(lines)))
        return PersistedValuation(
            valuation_id="val-1", document_id=header.document_id, status=header.status,
            total_valorado=header.total_valorado, total_lines=header.total_lines,
            review_required=header.review_required,
        )


class _Sv5:
    def __init__(self, envelope):
        self.envelope = envelope
        self.llamadas = 0

    def value(self, *, document_id, codigo_contrato):
        self.llamadas += 1
        return self.envelope


class _BuilderQueNoSeUsa:
    def build(self, **_):
        raise AssertionError("la valoración directa no pasa por el ValuationBuilder")


class _Ia4QueNoSeUsa:
    def conciliar(self, **_):
        raise AssertionError("la valoración directa no llama a IA4")


def _pipeline(envelope, repo, *, normalizador=None):
    return RunValuationPipeline(
        ia_client=_Sv5(envelope), repository=repo, builder=_BuilderQueNoSeUsa(),
        conciliacion_client=_Ia4QueNoSeUsa(), normalizador=normalizador,
    )


def test_f075_pipeline_no_contract_con_importes_persiste_la_valoracion_directa():
    envelope = _sobre(_linea(1, neto=100.0, precio=50.0, partida="CI.4.18"), _linea(2, neto=20.0, descripcion="PORTES"))
    repo = _Repositorio()
    resultado = _pipeline(envelope, repo).run(RunValuationRequest(document_id=DOC, codigo_contrato=None))
    ((cabecera, lineas),) = repo.guardados
    assert cabecera.status == "no_contract" and cabecera.prompt_key == "valoracion_directa_albaran"
    assert cabecera.total_valorado == 120.0 and cabecera.total_lines == 2
    assert json.loads(cabecera.raw_ia_envelope_json)["status"] == "no_contract"
    assert [l.derived_contrato_line_record.origen for l in lineas] == ["nueva_no_match"] * 2
    assert [l.derived_contrato_line_record.codigo_contrato for l in lineas] == ["", ""]
    # F-078: la fila guarda lo que se ve (el concepto del papel).
    assert [l.descripcion_linea for l in lineas] == ["TUBO PVC 110", "PORTES"]
    assert resultado.status == "no_contract" and resultado.duplicate is False
    assert resultado.total_valorado == 120.0 and resultado.total_lines == 2
    assert resultado.review_required is False
    assert resultado.review_reasons == ["valoracion_directa_albaran"]
    assert esta_valorado(cabecera.status, [l.importe_calculado for l in lineas]) is True


def test_f075_pipeline_no_contract_parcial_no_queda_valorada():
    envelope = _sobre(_linea(1, neto=100.0), _linea(2, precio=3.0, importe=6.0))
    repo = _Repositorio()
    resultado = _pipeline(envelope, repo).run(RunValuationRequest(document_id=DOC))
    ((cabecera, lineas),) = repo.guardados
    assert len(lineas) == 2 and lineas[1].review_reasons == ["sin_importe_en_albaran"]
    assert resultado.review_required is True
    assert esta_valorado(cabecera.status, [l.importe_calculado for l in lineas]) is False


def test_f075_pipeline_r8_no_contract_sin_importes_persiste_la_cabecera_vacia():
    envelope = _sobre(_linea(1, precio=3.0, importe=6.0))
    repo = _Repositorio()
    _pipeline(envelope, repo).run(RunValuationRequest(document_id=DOC))
    ((cabecera, lineas),) = repo.guardados
    assert lineas == []
    assert cabecera.prompt_key is None
    assert cabecera.total_valorado == 0.0
    assert cabecera.review_reasons == ["no_contract_selected"]


def test_f075_pipeline_r10_force_rehace_la_valoracion_directa():
    envelope = _sobre(_linea(1, neto=10.0))
    repo = _Repositorio(existente=True)
    sv5 = _Sv5(envelope)
    pipeline = RunValuationPipeline(ia_client=sv5, repository=repo, builder=_BuilderQueNoSeUsa())
    pipeline.run(RunValuationRequest(document_id=DOC, force=True))
    assert sv5.llamadas == 1
    ((cabecera, lineas),) = repo.guardados
    assert cabecera.prompt_key == "valoracion_directa_albaran" and len(lineas) == 1


def test_f075_pipeline_anota_la_partida_normalizada_de_f076():
    envelope = _sobre(_linea(1, neto=10.0, partida="CI.04.18"), _linea(2, neto=1.0, partida="ZZ.99"))
    repo = _Repositorio()
    normalizador = NormalizadorPartidas(partidas=PuertoFalso(), alm_codigo_partida="ALM", activo=True)
    _pipeline(envelope, repo, normalizador=normalizador).run(RunValuationRequest(document_id=DOC))
    ((cabecera, (normalizada, fuera)),) = repo.guardados
    assert normalizada.codigo_partida_final == "CI.4.18"
    assert normalizada.derived_contrato_line_record.codigo_partida == "CI.4.18"
    assert normalizada.codigo_partida_albaran == "CI.04.18"  # la leída vuelve (regla 6)
    assert "partida_normalizada:CI.04.18>CI.4.18" in normalizada.review_reasons
    assert normalizada.review_required is False
    assert fuera.review_required is True and "partida_fuera_de_lista" in fuera.review_reasons
    assert cabecera.review_required is True
    assert "partida_fuera_de_lista" in cabecera.review_reasons
    assert cabecera.review_reasons[0] == "valoracion_directa_albaran"


# ------------------------------------------------------------------ #
# T4 · R12: con contrato, aviso si el valorado se aparta del albarán
# ------------------------------------------------------------------ #
def _sobre_con_contrato(netos, *, sinteticas=()):
    from tests.f076_sobres import linea_contrato, sobre

    envelope = sobre(
        [(i + 1, "CI.4.18", 501) for i in range(len(netos))],
        contrato=[linea_contrato(501, "CI.4.18")], sinteticas=sinteticas,
    )
    lineas = [
        l.model_copy(update={"precio_neto_albaran": neto})
        for l, neto in zip(envelope.context.lineas_albaran, netos)
    ]
    return envelope.model_copy(update={"context": envelope.context.model_copy(update={"lineas_albaran": lineas})})


def _valorar_con_contrato(envelope):
    from tests.f027_escenarios import construir_builder

    repo = _Repositorio()
    RunValuationPipeline(ia_client=_Sv5(envelope), repository=repo, builder=construir_builder()).run(
        RunValuationRequest(document_id=DOC, codigo_contrato="CTSU26/0313"),
    )
    ((cabecera, lineas),) = repo.guardados
    return cabecera, lineas


def test_f075_r12_con_sintetica_el_valorado_se_aparta_y_va_a_revision():
    envelope = _sobre_con_contrato([20.0], sinteticas=[(1, "otro")])
    cabecera, lineas = _valorar_con_contrato(envelope)
    from tests.f027_escenarios import construir_builder

    esperado, _ = construir_builder().build(envelope=envelope, existing_document_already_valued=False)
    assert cabecera.total_valorado == esperado.total_valorado != 20.0  # R12 no toca importes
    motivo = f"valorado_distinto_de_albaran:{cabecera.total_valorado:.2f}!=20.00"
    assert motivo in cabecera.review_reasons
    assert cabecera.review_required is True
    assert cabecera.status == "ok"


def test_f075_r12_si_cuadra_no_hay_motivo():
    cabecera, _ = _valorar_con_contrato(_sobre_con_contrato([20.0, 20.0]))
    assert cabecera.total_valorado == 40.0
    assert not any(m.startswith("valorado_distinto_de_albaran") for m in cabecera.review_reasons)


def test_f075_r12_sin_importes_leidos_no_hay_motivo():
    cabecera, _ = _valorar_con_contrato(_sobre_con_contrato([None], sinteticas=[(1, "otro")]))
    assert not any(m.startswith("valorado_distinto_de_albaran") for m in cabecera.review_reasons)


def test_f075_r12_parcial_compara_con_lo_leido():
    # Una línea con importe leído y otra sin él: el valorado (con el contrato
    # en la segunda) se aparta del importe del albarán (solo la primera).
    cabecera, _ = _valorar_con_contrato(_sobre_con_contrato([20.0, None]))
    assert cabecera.total_valorado == 40.0
    assert "valorado_distinto_de_albaran:40.00!=20.00" in cabecera.review_reasons
    assert cabecera.review_required is True


def test_f075_r12_funcion_pura_no_cambia_nada_mas():
    from application.services.valoracion_directa import anotar_valorado_distinto
    from domain.models.valuation_records import ValuationHeaderRecord

    cab = ValuationHeaderRecord(
        document_id=DOC, contrato_codigo="C", status="ok", provider_ia=None, model_name=None, prompt_key=None,
        total_valorado=10.0, total_lines=1, lines_matched_exact=1, lines_matched_semantic=0,
        lines_matched_price_only=0, lines_unmatched=0, review_required=False, review_reasons=["x"],
    )
    reasons_antes = cab.review_reasons
    anotar_valorado_distinto(cab, _sobre(_linea(1, neto=10.004), status="ok"))
    assert cab.review_reasons == ["x"] and cab.review_required is False
    anotar_valorado_distinto(cab, _sobre(_linea(1, neto=10.01), status="ok"))
    assert cab.review_reasons == ["x", "valorado_distinto_de_albaran:10.00!=10.01"]
    assert reasons_antes == ["x"]  # lista nueva
    assert cab.review_required is True and cab.total_valorado == 10.0
    anotar_valorado_distinto(cab, _sobre(_linea(1, neto=10.01), status="ok"))
    assert cab.review_reasons.count("valorado_distinto_de_albaran:10.00!=10.01") == 1
