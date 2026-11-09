# tests/test_f117_pipeline.py
"""F-117 T5 · el caso real de extremo a extremo (R24–R26).

El albarán de 0719 (contrato CTSB26/0373): 1 línea «grua pk 50 - montar muro y
hormigonar», 9 UD × 60 €, partida leída ``CI.03.08``. La obra tiene
``CI.03A.8`` «CAMION GRUA» y ninguna ``CI.3.8``: sv6 debe valorar con
``CI.03A.8``, conservar la leída y dejar ``partida_equivalente:`` a revisión.

- R24: rama normal (con contrato): IA4 y builder ven la equivalente.
- R25: la regla del sufijo (``04.01.07`` ⇒ ``02.04.01.07``).
- R26: rama de valoración directa (F-075, sin contrato e importe leído).

Builder real (``tests/f027_escenarios.py``); sv5, IA4, repositorio y lista
falsos: sin red ni BBDD.
"""
from __future__ import annotations

import json

import pytest
from application.pipelines.run_valuation_pipeline import (
    RunValuationPipeline,
    RunValuationRequest,
)
from application.services.normalizador_partidas import NormalizadorPartidas
from domain.models.valuation_envelope import (
    AlbaranLineContextDto,
    ContratoLineContextDto,
    DocumentoValoracionDto,
    LineValuationDto,
    ValuationContextDto,
    ValuationEnvelope,
    ValuationEnvelopeMeta,
)
from domain.ports.valuation_repository import PersistedValuation
from tests.f027_escenarios import construir_builder
from tests.f076_sobres import PuertoFalso, lista_obra

DOC = "doc-f117-0719"
CONTRATO = "CTSB26/0373"
DESCRIPCION = "grua pk 50 - montar muro y hormigonar"
#: La lista reducida de 0719 de R24 (más la hoja del sufijo de R25).
LISTA_0719 = lista_obra("CI.03A.1", "CI.03A.8", "CI.03A.13", "CI.03P.9", "CI.1.8", "CI.2.8", "CI.4.8",
                        "02.04.01.07", obra="0719")


class _Repositorio:
    def __init__(self):
        self.guardados = []
        self.obras_pedidas = []

    def get_by_document_id(self, *, document_id):
        return None

    def obra_del_documento(self, *, document_id):
        self.obras_pedidas.append(document_id)
        return "0719"

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

    def value(self, *, document_id, codigo_contrato):
        return self.envelope


class _Ia4:
    """IA4 falsa: apunta las partidas que recibe y no concilia nada."""

    def __init__(self):
        self.partidas = None

    def conciliar(self, *, document_id, lineas_no_casadas, lineas_contrato):
        self.partidas = [p["codigo_partida"] for p in lineas_no_casadas]
        return {"conciliaciones": []}


#: Una línea del contrato de otra partida: hay contrato, IA4 se llama y no casa.
_OTRA_LINEA = ContratoLineContextDto(
    contrato_line_id=901, codigo_contrato=CONTRATO, codigo_producto="QA9999", descripcion="MANO DE OBRA OFICIAL",
    unidad_medida="H", precio_unitario=25.0, codigo_partida="CI.1.8",
)


def _sobre_0719(lectura: str, *, directa: bool = False) -> ValuationEnvelope:
    contexto = AlbaranLineContextDto(
        merge_line_id=1, line_index=0, descripcion=DESCRIPCION, unidad_medida="UD", unidad_categoria="count",
        cantidad=9.0, precio_unitario_albaran=60.0, importe_albaran=540.0, codigo_partida_albaran=lectura,
        precio_neto_albaran=540.0 if directa else None,  # el NETO de la línea (regla 13)
    )
    ia = [] if directa else [LineValuationDto(
        merge_line_id=1, line_kind="from_albaran", match_method="no_match", matched_contrato_line_id=None,
        match_confidence_pct=0.0, unidad_categoria_albaran="count", unidad_category_match=True,
        precio_unitario_contrato_db=None, precio_unitario_pdf_inferido=60.0, descripcion_linea=DESCRIPCION,
    )]
    return ValuationEnvelope(
        status="no_contract" if directa else "ok",
        meta=ValuationEnvelopeMeta(document_id=DOC, codigo_contrato=None if directa else CONTRATO,
                                   numero_albaran="0719-1"),
        data=DocumentoValoracionDto(lineas=ia),
        context=ValuationContextDto(lineas_albaran=[contexto], lineas_contrato=[] if directa else [_OTRA_LINEA]),
    )


def _valorar(envelope, *, equivalente=True, ia4=None):
    repo = _Repositorio()
    normalizador = NormalizadorPartidas(partidas=PuertoFalso(LISTA_0719), alm_codigo_partida="ALM", activo=True,
                                        equivalente=equivalente)
    RunValuationPipeline(
        ia_client=_Sv5(envelope), repository=repo, builder=construir_builder(), conciliacion_client=ia4,
        normalizador=normalizador,
    ).run(RunValuationRequest(document_id=DOC, codigo_contrato=envelope.meta.codigo_contrato))
    ((cabecera, lineas),) = repo.guardados
    return cabecera, lineas


def _comprobar(cabecera, lineas, lectura, cod):
    (fila,) = [r for r in lineas if r.line_kind == "from_albaran"]
    assert fila.codigo_partida_albaran == lectura
    assert fila.codigo_partida_final == cod
    assert f"partida_equivalente:{lectura}>{cod}" in fila.review_reasons
    assert "partida_fuera_de_lista" not in fila.review_reasons
    assert "partida_fuera_de_lista" not in cabecera.review_reasons
    assert fila.review_required is True and cabecera.review_required is True
    assert f"partida_equivalente:{lectura}>{cod}" in cabecera.review_reasons
    assert fila.importe_calculado == pytest.approx(540.0)
    return fila


# ------------------------------------------------------------------ #
# R24 · el albarán de 0719, rama normal
# ------------------------------------------------------------------ #
def test_f117_r24_albaran_de_0719():
    ia4 = _Ia4()
    cabecera, lineas = _valorar(_sobre_0719("CI.03.08"), ia4=ia4)
    _comprobar(cabecera, lineas, "CI.03.08", "CI.03A.8")
    assert ia4.partidas == ["CI.03A.8"]  # IA4 ve la equivalente
    persistido = json.loads(cabecera.raw_ia_envelope_json)
    assert persistido["context"]["lineas_albaran"][0]["codigo_partida_albaran"] == "CI.03A.8"


def test_f117_r24_sin_f117_es_lo_de_hoy():
    """El mismo albarán con el interruptor apagado: fuera de lista, mismo importe."""
    cabecera, lineas = _valorar(_sobre_0719("CI.03.08"), equivalente=False)
    (fila,) = [r for r in lineas if r.line_kind == "from_albaran"]
    assert fila.codigo_partida_final == "CI.03.08"
    assert "partida_fuera_de_lista" in fila.review_reasons
    assert not any(m.startswith("partida_equivalente") for m in fila.review_reasons)
    assert fila.importe_calculado == pytest.approx(540.0)
    assert "partida_fuera_de_lista" in cabecera.review_reasons


# ------------------------------------------------------------------ #
# R25 · la regla del sufijo
# ------------------------------------------------------------------ #
def test_f117_r25_sufijo_de_0719():
    cabecera, lineas = _valorar(_sobre_0719("04.01.07"))
    _comprobar(cabecera, lineas, "04.01.07", "02.04.01.07")


# ------------------------------------------------------------------ #
# R26 · valoración directa (F-075): el mismo rastro
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(("lectura", "cod"), [("CI.03.08", "CI.03A.8"), ("04.01.07", "02.04.01.07")],
                         ids=["letra", "sufijo"])
def test_f117_r26_valoracion_directa(lectura, cod):
    cabecera, lineas = _valorar(_sobre_0719(lectura, directa=True))
    assert cabecera.status == "no_contract" and cabecera.prompt_key == "valoracion_directa_albaran"
    _comprobar(cabecera, lineas, lectura, cod)
