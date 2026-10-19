# tests/test_f075_no_contract.py
"""F-075 R5 bis: el sobre ``no_contract`` lleva el importe leído sin derivar.

Sin contrato seleccionado, sv6 hace la valoración directa con el
``precio_neto`` PURO de cada línea (P3: una línea sin importe leído no
suma), no con ``importe_albaran``, que sv5 deriva con la fórmula cuando
falta. Hasta F-075 el sobre ``no_contract`` no llevaba ni el
``precio_neto`` ni el descuento (opción A, decisión del humano del
2026-10-18). Sin red, sin BBDD y sin LLM.
"""
from __future__ import annotations

from application.pipelines.value_albaran_pipeline import (
    ValueAlbaranPipeline,
    _raw_albaran_line_to_dict,
)
from domain.ports.valuation_context_repository import (
    RawAlbaranLine,
    ValuationContextRaw,
)


def _linea(**extra) -> RawAlbaranLine:
    datos = dict(
        merge_line_id=7,
        line_index=0,
        codigo="P-1",
        descripcion="PAPEL HIGIENICO",
        unidad_medida="ud",
        cantidad=108.0,
        precio_unitario_albaran=0.543,
        importe_albaran=35.19,
        codigo_partida_albaran="CI.04.18",
    )
    datos.update(extra)
    return RawAlbaranLine(**datos)


class _Repo:
    def __init__(self, raw: ValuationContextRaw) -> None:
        self._raw = raw

    def load_context(self, *, document_id, codigo_contrato_override=None):
        return self._raw


class _Request:
    document_id = "doc-f075"
    codigo_contrato_override = None


def _pipeline(lineas: list[RawAlbaranLine]) -> ValueAlbaranPipeline:
    raw = ValuationContextRaw(
        document_id="doc-f075",
        codigo_contrato_seleccionado=None,
        contrato=None,
        lineas_albaran=lineas,
    )
    return ValueAlbaranPipeline(
        context_repository=_Repo(raw),
        pdf_downloader=None,
        prefilter=None,
        extraction_service=None,
        max_pdf_mb=10,
        service_version="test",
    )


def test_f075_r5bis_no_contract_lleva_precio_neto_y_descuento():
    linea = _raw_albaran_line_to_dict(_linea(descuento=40.0, precio_neto=35.19))
    assert linea["precio_neto_albaran"] == 35.19
    assert linea["descuento_albaran"] == 40.0
    # Lo de antes, igual.
    assert linea["importe_albaran"] == 35.19
    assert linea["precio_unitario_albaran"] == 0.543
    assert linea["codigo_partida_albaran"] == "CI.04.18"


def test_f075_r5bis_sin_precio_neto_va_nulo_aunque_haya_importe_derivado():
    # sv5 deriva importe_albaran con la fórmula; precio_neto_albaran no.
    linea = _raw_albaran_line_to_dict(_linea(importe_albaran=58.64, precio_neto=None))
    assert linea["precio_neto_albaran"] is None
    assert linea["descuento_albaran"] is None
    assert linea["importe_albaran"] == 58.64


def test_f075_r5bis_el_sobre_no_contract_del_pipeline_los_lleva():
    sobre = _pipeline([
        _linea(precio_neto=35.19, descuento=40.0),
        _linea(merge_line_id=8, line_index=1, precio_neto=None),
    ]).run(_Request())
    assert sobre["status"] == "no_contract"
    lineas = sobre["context"]["lineas_albaran"]
    assert [l["precio_neto_albaran"] for l in lineas] == [35.19, None]
    assert [l["descuento_albaran"] for l in lineas] == [40.0, None]
    assert sobre["data"] == {"lineas": []}
