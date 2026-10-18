# tests/test_f078_fila_completa.py
"""F-078 · R4, R5, R19 · sv6 guarda en cada fila lo que la ficha va a enseñar.

``completar_registros`` aplica ``ruesma_comun.linea_valorada.fila_a_guardar`` a
cada registro antes del ``replace_valuation``: concepto, unidad, precio,
``unidad_albaran`` y ``cantidad_convertida`` (R4); nada más (R5). Su línea es la
de contrato del sobre o, si no, su derivada; el concepto de su blanca, el del
sobre por ``merge_line_id`` (una sintética no hereda el de su base).

El pipeline lo llama antes de todo ``replace_valuation`` con líneas (T3).

Sin red, sin BBDD y sin LLM: registros y sobres armados a mano, el
``ValuationBuilder`` real (cableado de ``f027_escenarios``) y dobles del
cliente de sv5 y del repositorio.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import pytest

CONTRATO = "CTSU24/0176"


# ------------------------------------------------------------------ #
# Construcción de sobres y registros
# ------------------------------------------------------------------ #
def _sobre(*, blancas=(), contrato=(), lineas_ia=()):
    from domain.models.valuation_envelope import (
        AlbaranLineContextDto,
        ContratoLineContextDto,
        DocumentoValoracionDto,
        ValuationContextDto,
        ValuationEnvelope,
        ValuationEnvelopeMeta,
    )

    return ValuationEnvelope(
        status="ok",
        meta=ValuationEnvelopeMeta(document_id="doc-f078", codigo_contrato=CONTRATO),
        data=DocumentoValoracionDto(lineas=list(lineas_ia)),
        context=ValuationContextDto(
            lineas_albaran=[
                AlbaranLineContextDto(
                    merge_line_id=mid, line_index=i, descripcion=desc,
                    unidad_medida=uni, cantidad=3.0,
                )
                for i, (mid, desc, uni) in enumerate(blancas)
            ],
            lineas_contrato=[
                ContratoLineContextDto(
                    contrato_line_id=cid, codigo_contrato=CONTRATO, descripcion=desc,
                    unidad_medida=uni, precio_unitario=precio, codigo_partida=partida,
                )
                for cid, desc, uni, precio, partida in contrato
            ],
        ),
    )


def _derivada(descripcion, unidad="UD", precio=3.2, origen="missing_partida"):
    from domain.models.valuation_records import DerivedContratoLineRecord

    return DerivedContratoLineRecord(
        codigo_contrato=CONTRATO, codigo_producto=None, descripcion_linea=descripcion,
        unidad_medida=unidad, precio_unitario=precio, codigo_partida="01.05.07",
        origen=origen,
    )


def _registro(**campos):
    from domain.models.valuation_records import LineValuationRecord

    base = dict(
        merge_line_id=701, matched_contrato_line_id=None, derived_contrato_line_record=None,
        precio_unitario_contrato_db=None, precio_unitario_pdf_inferido=None,
        precio_unitario_final=None, precio_unitario_source="none",
        precio_unitario_agreement="neither", unidad_albaran=None, unidad_contrato=None,
        unidad_categoria="unknown", unidad_category_match=True, cantidad_albaran=3.0,
        cantidad_convertida=None, factor_conversion=1.0, importe_calculado=301.8,
        importe_albaran_declarado=None, importe_source="calculated",
        codigo_partida_albaran="01.05.07", codigo_partida_final="01.05.07",
        partida_action="existing_matched", match_confidence_pct=90.0,
        match_method="semantic", review_required=True,
        review_reasons=["ia_match_trusted"], descuento_albaran_aplicado=None,
    )
    base.update(campos)
    return LineValuationRecord(**base)


def _completar(registros, sobre):
    from application.services.fila_completa import completar_registros

    return completar_registros(list(registros), sobre)


CL_MORTERO = (501, "MORTERO M-5", "m3", 100.6, "01.05.07")
CL_FERRETERIA = (502, "MATERIAL DE FERRETERIA", "UD", 3.2, "02.01")


# ------------------------------------------------------------------ #
# R4 · Contrato, Nueva, sintéticas
# ------------------------------------------------------------------ #
def test_f078_r4_contrato_sin_descripcion_guarda_la_de_su_linea_y_su_unidad():
    sobre = _sobre(blancas=[(701, "Mortero M-5", None)], contrato=[CL_MORTERO])
    (fila,) = _completar(
        [_registro(matched_contrato_line_id=501, precio_unitario_final=100.6)], sobre,
    )
    assert fila.descripcion_linea == "MORTERO M-5"
    assert fila.unidad_contrato == "m3"
    assert fila.unidad_albaran == "m3"            # sin conversión: la que se ve
    assert fila.cantidad_convertida == 3.0         # sin conversión: Q
    assert fila.precio_unitario_final == 100.6


def test_f078_r4_contrato_sin_precio_toma_el_de_su_linea():
    sobre = _sobre(blancas=[(701, "Mortero M-5", "M3")], contrato=[CL_MORTERO])
    (fila,) = _completar([_registro(matched_contrato_line_id=501)], sobre)
    assert fila.precio_unitario_final == 100.6
    assert fila.unidad_albaran == "m3"


def test_f078_r4_contrato_conserva_la_unidad_del_papel_y_la_descripcion_propia():
    sobre = _sobre(blancas=[(701, "Mortero M-5", "M3")], contrato=[CL_MORTERO])
    (fila,) = _completar([_registro(
        matched_contrato_line_id=501, unidad_albaran="M3", descripcion_linea="PROPIA",
        cantidad_convertida=3.0,
    )], sobre)
    assert (fila.descripcion_linea, fila.unidad_albaran) == ("PROPIA", "M3")


def test_f078_r19_nueva_de_sv6_desde_linea_de_contrato_guarda_el_concepto_del_papel():
    """P1 = (b): derivada ``missing_partida`` «MATERIAL DE FERRETERIA» (la de la línea
    de contrato), blanca «DISCO C/ACERO 230 BOSCH» ⇒ se guarda el del papel."""
    sobre = _sobre(blancas=[(701, "DISCO C/ACERO 230 BOSCH", None)],
                   contrato=[CL_FERRETERIA])
    (fila,) = _completar([_registro(
        derived_contrato_line_record=_derivada("MATERIAL DE FERRETERIA"),
        partida_action="new_line_created", precio_unitario_final=3.2,
    )], sobre)
    assert fila.descripcion_linea == "DISCO C/ACERO 230 BOSCH"
    assert fila.unidad_contrato == "UD"
    assert fila.unidad_albaran == "UD"
    # La derivada no se toca.
    assert fila.derived_contrato_line_record.descripcion_linea == "MATERIAL DE FERRETERIA"


def test_f078_r19_nueva_sin_linea_de_contrato_con_blanca_guarda_el_papel():
    sobre = _sobre(blancas=[(701, "Puesta de contenedor de 6 m3", "UD")])
    (fila,) = _completar([_registro(
        derived_contrato_line_record=_derivada("CONTENEDOR 6 M3", origen="nueva_no_match"),
        precio_unitario_final=None,
    )], sobre)
    assert fila.descripcion_linea == "Puesta de contenedor de 6 m3"
    assert fila.precio_unitario_final == 3.2       # el de su derivada


def test_f078_r4_sintetica_casada_toma_la_de_su_linea_no_la_de_la_base():
    sobre = _sobre(blancas=[(701, "HORMIGON HA-25", "M3")], contrato=[CL_MORTERO])
    (fila,) = _completar([_registro(
        merge_line_id=None, parent_merge_line_id=701, line_kind="synthetic_modifier",
        matched_contrato_line_id=501, descripcion_linea=None,
    )], sobre)
    assert fila.descripcion_linea == "MORTERO M-5"


def test_f078_r4_sintetica_derivada_guarda_la_de_su_derivada():
    """Sin blanca: la de su derivada («— AÑO 2026»), nunca el concepto de la base."""
    sobre = _sobre(blancas=[(701, "HORMIGON HA-25", "M3")])
    (fila,) = _completar([_registro(
        merge_line_id=None, parent_merge_line_id=701, line_kind="synthetic_modifier",
        derived_contrato_line_record=_derivada("INCREMENTO — AÑO 2026", unidad="M3",
                                               origen="nueva_no_match"),
        descripcion_linea="INCREMENTO AÑO", unidad_contrato="M3", unidad_albaran="M3",
        cantidad_convertida=None,
    )], sobre)
    assert fila.descripcion_linea == "INCREMENTO — AÑO 2026"
    assert fila.cantidad_convertida == 3.0


def test_f078_r4_sintetica_sin_linea_conserva_su_descripcion():
    sobre = _sobre(blancas=[(701, "HORMIGON HA-25", "M3")])
    (fila,) = _completar([_registro(
        merge_line_id=None, parent_merge_line_id=701, line_kind="synthetic_modifier",
        descripcion_linea="RECARGO", unidad_contrato="M3",
    )], sobre)
    assert fila.descripcion_linea == "RECARGO"
    assert fila.unidad_albaran == "M3"


def test_f078_r4_sin_linea_ni_descripcion_guarda_el_concepto_de_su_blanca():
    """P9: ni la fila ni su línea tienen texto ⇒ el de su blanca."""
    sobre = _sobre(blancas=[(701, "PORTES", None)])
    (fila,) = _completar([_registro(partida_action="no_action")], sobre)
    assert fila.descripcion_linea == "PORTES"


def test_f078_r4_casada_que_no_esta_en_el_sobre_usa_su_derivada():
    sobre = _sobre(blancas=[(701, "", None)])
    (fila,) = _completar([_registro(
        matched_contrato_line_id=999, derived_contrato_line_record=_derivada("DERIVADA"),
    )], sobre)
    assert fila.descripcion_linea == "DERIVADA"


@pytest.mark.parametrize("factor", [None, 1000.0])
def test_f078_r4_con_conversion_no_toca_unidad_albaran_ni_convertida(factor):
    sobre = _sobre(blancas=[(701, "ACERO", "T")], contrato=[CL_FERRETERIA])
    (fila,) = _completar([_registro(
        matched_contrato_line_id=502, factor_conversion=factor, unidad_albaran=None,
        cantidad_convertida=None,
    )], sobre)
    assert fila.unidad_albaran is None
    assert fila.cantidad_convertida is None
    assert fila.descripcion_linea == "MATERIAL DE FERRETERIA"


# ------------------------------------------------------------------ #
# R5 · nada más cambia
# ------------------------------------------------------------------ #
_CINCO = {
    "descripcion_linea", "unidad_contrato", "unidad_albaran", "precio_unitario_final",
    "cantidad_convertida",
}


def test_f078_r5_solo_cambian_los_cinco_campos_y_el_registro_de_entrada_no_se_toca():
    sobre = _sobre(blancas=[(701, "Mortero M-5", None)], contrato=[CL_MORTERO])
    entrada = _registro(
        matched_contrato_line_id=501, importe_calculado=301.8, codigo_partida_final="",
        partida_action="almacen_sin_partida", review_required=True,
        review_reasons=["partida_ausente"], cantidad_albaran=3.0, factor_conversion=1.0,
    )
    copia = dataclasses.replace(entrada)
    (salida,) = _completar([entrada], sobre)

    assert entrada == copia
    distintos = {
        f.name for f in dataclasses.fields(entrada)
        if getattr(entrada, f.name) != getattr(salida, f.name)
    }
    assert distintos == _CINCO
    assert salida.importe_calculado == 301.8
    assert salida.codigo_partida_final == ""
    assert salida.partida_action == "almacen_sin_partida"
    assert salida.review_reasons == ["partida_ausente"]


def test_f078_r5_precio_lleno_y_cantidades_con_conversion_no_cambian():
    sobre = _sobre(blancas=[(701, "ACERO", "T")], contrato=[CL_FERRETERIA])
    entrada = _registro(
        matched_contrato_line_id=502, precio_unitario_final=2.0, factor_conversion=1000.0,
        cantidad_albaran=3.0, cantidad_convertida=3000.0, unidad_albaran="T",
        unidad_contrato="KG",
    )
    (salida,) = _completar([entrada], sobre)
    assert salida.precio_unitario_final == 2.0
    assert (salida.cantidad_albaran, salida.cantidad_convertida) == (3.0, 3000.0)
    assert salida.unidad_albaran == "T"
    assert salida.unidad_contrato == "UD"        # la de su línea (lo que se ve)


def test_f078_r4_conserva_el_orden_y_el_numero_de_registros():
    sobre = _sobre(blancas=[(701, "A", None), (702, "B", None)], contrato=[CL_MORTERO])
    entrada = [_registro(merge_line_id=702), _registro(merge_line_id=701)]
    salida = _completar(entrada, sobre)
    assert [r.merge_line_id for r in salida] == [702, 701]
    assert [r.descripcion_linea for r in salida] == ["B", "A"]


# ------------------------------------------------------------------ #
# R4 · con el builder real (cualquier builder: el paso va después)
# ------------------------------------------------------------------ #
def test_f078_r4_registros_del_builder_real_salen_completos():
    from tests.f027_escenarios import (
        CATALOGO_MAHORSA,
        Escenario,
        construir_builder,
        construir_envelope,
    )

    escenario = Escenario(
        numero_albaran="F078", cantidad=24.5, unidad_albaran="TN",
        codigo_partida_albaran="P4.22.01.03.07", matched_contrato_line_id=25972,
        precio_contrato_db=12.87, contrato=CATALOGO_MAHORSA,
    )
    sobre = construir_envelope(escenario)
    _cabecera, registros = construir_builder().build(
        envelope=sobre, existing_document_already_valued=False,
    )
    (antes,) = registros
    (despues,) = _completar(registros, sobre)
    assert antes.descripcion_linea is None
    assert despues.descripcion_linea == "SUMINISTRO DE GRAVA 20/40"
    assert despues.unidad_contrato == "TN"
    assert despues.importe_calculado == antes.importe_calculado


# ------------------------------------------------------------------ #
# T3 · el pipeline completa antes de persistir
# ------------------------------------------------------------------ #
class _Repositorio:
    def __init__(self):
        self.guardados = []

    def get_by_document_id(self, *, document_id):
        return None

    def replace_valuation(self, *, header, lines):
        from domain.ports.valuation_repository import PersistedValuation

        self.guardados.append((header, list(lines)))
        return PersistedValuation(
            valuation_id="val-1", document_id=header.document_id, status=header.status,
            total_valorado=header.total_valorado, total_lines=header.total_lines,
            review_required=header.review_required,
        )


class _Sv5:
    def __init__(self, sobre):
        self._sobre = sobre

    def value(self, *, document_id, codigo_contrato):
        return self._sobre


class _Builder:
    def __init__(self, registros):
        self._registros = registros

    def build(self, *, envelope, existing_document_already_valued):
        from domain.models.valuation_records import ValuationHeaderRecord

        cabecera = ValuationHeaderRecord(
            document_id="doc-f078", contrato_codigo=CONTRATO, status="ok",
            provider_ia=None, model_name=None, prompt_key=None, total_valorado=301.8,
            total_lines=len(self._registros), lines_matched_exact=0,
            lines_matched_semantic=1, lines_matched_price_only=0, lines_unmatched=0,
            review_required=False,
        )
        return cabecera, list(self._registros)


def test_f078_pipeline_persiste_los_registros_completados():
    from application.pipelines.run_valuation_pipeline import (
        RunValuationPipeline,
        RunValuationRequest,
    )

    sobre = _sobre(blancas=[(701, "Mortero M-5", None)], contrato=[CL_MORTERO])
    repositorio = _Repositorio()
    RunValuationPipeline(
        ia_client=_Sv5(sobre), repository=repositorio,
        builder=_Builder([_registro(matched_contrato_line_id=501)]),
    ).run(RunValuationRequest(document_id="doc-f078"))

    ((_cabecera, lineas),) = repositorio.guardados
    (fila,) = lineas
    assert fila.descripcion_linea == "MORTERO M-5"
    assert (fila.unidad_albaran, fila.cantidad_convertida) == ("m3", 3.0)


def test_f078_pipeline_todo_replace_valuation_con_lineas_va_tras_completar_registros():
    """R4 «de cualquier builder»: cada ``replace_valuation`` del pipeline que lleva
    líneas (no ``lines=[]``) recibe lo que devolvió ``completar_registros``. Quien
    añada otra rama de persistencia (F-075) tiene que pasar por el mismo paso."""
    fuente = (
        Path(__file__).resolve().parents[1]
        / "application" / "pipelines" / "run_valuation_pipeline.py"
    ).read_text(encoding="utf-8")
    llamadas = [m.start() for m in re.finditer(r"replace_valuation\(", fuente)]
    assert llamadas, "el pipeline ya no persiste con replace_valuation"
    con_lineas = 0
    for inicio in llamadas:
        argumentos = fuente[inicio:fuente.index(")", inicio)]
        if re.search(r"lines\s*=\s*\[\s*\]", argumentos):
            continue
        con_lineas += 1
        lineas = re.search(r"lines\s*=\s*(\w+)", argumentos)
        assert lineas is not None, argumentos
        anterior = fuente[:inicio]
        asignacion = list(re.finditer(rf"\b{lineas.group(1)}\s*=\s*([^\n]+)", anterior))
        assert asignacion, f"{lineas.group(1)} no se asigna antes de persistir"
        assert "completar_registros(" in asignacion[-1].group(1), asignacion[-1].group(0)
    assert con_lineas >= 1
