# tests/test_f003_contexto_importe.py
"""F-003 · El importe LEIDO llega al contexto de valoracion (R4).

Hasta esta feature sv5 RECOMPONIA el importe de cada linea
(``cantidad x COALESCE(precio_neto, precio x (1-dto))``) porque no habia
columna de importe. Ahora sv3 persiste el importe impreso y sv5 lo
expone en dos campos:

  - ``importe_leido``: lo transcrito, null si el documento no lo imprime;
  - ``importe_albaran``: el efectivo = el leido si existe, y si no la
    derivacion de siempre (fallback para las filas anteriores a F-003).

Y el total del albaran viaja al ``meta`` del envelope por la misma via
que ``fecha_albaran``.

Sin red ni BBDD: se ejercitan los mapeos fila->DTO (metodos estaticos) y
el texto del SQL; el pipeline se monta con dobles.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pytest

from application.pipelines.value_albaran_pipeline import ValueAlbaranPipeline
from application.services.unit_category_prefilter import UnitCategoryPrefilter
from domain.models.valuation_context import ContextoValoracion
from domain.ports.valuation_context_repository import (
    RawAlbaranLine,
    ValuationContextRaw,
)
from infrastructure.database import sqlalchemy_valuation_context_repository as repo_mod
from infrastructure.database.sqlalchemy_valuation_context_repository import (
    SqlAlchemyValuationContextRepository,
)


def _fila(**kwargs: Any) -> dict[str, Any]:
    """Fila cruda tal y como la devuelve el SELECT de lineas."""
    base: dict[str, Any] = {
        "merge_line_id": 1,
        "line_index": 1,
        "codigo": "GB",
        "descripcion": "GASOLEO B",
        "unidad_medida": "l",
        "cantidad": 120.55,
        "precio_unitario_albaran": 1.5877,
        "importe_leido": None,
        "importe_albaran": None,
        "codigo_partida_albaran": None,
        "contexto_linea_json": None,
        "descuento_albaran": None,
        "precio_neto_albaran": None,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------
# R4 · El SELECT pide el importe y el total
# ---------------------------------------------------------------------


def _sql(objeto) -> str:
    return " ".join(str(objeto).split())


def test_f003_r4_el_select_de_lineas_lee_la_columna_importe() -> None:
    sql = _sql(repo_mod._SQL_ALBARAN_LINES)

    assert "importe" in sql
    assert "AS importe_leido" in sql


def test_f003_r4_el_importe_efectivo_prefiere_el_leido() -> None:
    """COALESCE(importe, <derivacion de siempre>): lo transcrito manda y
    la derivacion queda SOLO como fallback de filas antiguas."""
    sql = _sql(repo_mod._SQL_ALBARAN_LINES)

    assert re.search(r"COALESCE\(\s*importe\s*,", sql)
    assert "AS importe_albaran" in sql


def test_f003_r4_la_derivacion_antigua_sigue_como_fallback() -> None:
    sql = _sql(repo_mod._SQL_ALBARAN_LINES)

    assert "precio_neto" in sql
    assert "1 - COALESCE(descuento, 0) / 100.0" in sql


def test_f003_r4_el_select_de_cabecera_lee_el_total_y_su_marca() -> None:
    sql = _sql(repo_mod._SQL_DOC_HEADER)

    assert "importe_total" in sql
    assert "importe_total_incluye_iva" in sql


# ---------------------------------------------------------------------
# R4 · Fila -> DTO
# ---------------------------------------------------------------------


def test_f003_r4_la_fila_con_importe_leido_lo_expone() -> None:
    linea = SqlAlchemyValuationContextRepository._build_albaran_line(
        _fila(importe_leido=191.40, importe_albaran=191.40)
    )

    assert linea.importe_leido == pytest.approx(191.40)
    assert linea.importe_albaran == pytest.approx(191.40)


def test_f003_r4_la_fila_antigua_deja_el_leido_a_null() -> None:
    """Documento anterior a F-003: columna NULL. El efectivo sigue
    siendo la derivacion que calcula el propio SELECT."""
    linea = SqlAlchemyValuationContextRepository._build_albaran_line(
        _fila(importe_leido=None, importe_albaran=191.38)
    )

    assert linea.importe_leido is None
    assert linea.importe_albaran == pytest.approx(191.38)


def test_f003_r4_la_fila_sin_la_columna_no_revienta() -> None:
    """Sobre/fila de una version anterior del SELECT: sin clave."""
    fila = _fila()
    del fila["importe_leido"]

    linea = SqlAlchemyValuationContextRepository._build_albaran_line(fila)

    assert linea.importe_leido is None


# ---------------------------------------------------------------------
# R4 · El prefilter propaga el importe leido al DTO del prompt
# ---------------------------------------------------------------------


# ---------------------------------------------------------------------
# R4 · La marca de IVA distingue False de "no se sabe"
# ---------------------------------------------------------------------


@pytest.mark.parametrize("crudo", [False, 0, "false", "f", "0", "no", "N"])
def test_f003_r4_la_marca_de_iva_reconoce_el_falso(crudo) -> None:
    """False (es base imponible: sv6 EXIGE cuadre) no puede degradarse a
    None (no consta: sv6 solo avisa)."""
    assert repo_mod._opt_bool(crudo) is False


@pytest.mark.parametrize("crudo", [True, 1, "true", "t", "1", "yes", "Y"])
def test_f003_r4_la_marca_de_iva_reconoce_el_verdadero(crudo) -> None:
    assert repo_mod._opt_bool(crudo) is True


@pytest.mark.parametrize("crudo", [None, "", "quiza", "  "])
def test_f003_r4_lo_que_no_es_ni_si_ni_no_queda_en_desconocido(crudo) -> None:
    assert repo_mod._opt_bool(crudo) is None


def test_f003_r4_el_prefilter_propaga_el_importe_leido() -> None:
    prefilter = UnitCategoryPrefilter()

    lineas = prefilter.build_albaran_lines(
        [
            RawAlbaranLine(
                merge_line_id=1,
                line_index=1,
                codigo="GB",
                descripcion="GASOLEO B",
                unidad_medida="l",
                cantidad=120.55,
                precio_unitario_albaran=1.5877,
                importe_albaran=191.40,
                codigo_partida_albaran=None,
                importe_leido=191.40,
            )
        ]
    )

    assert lineas[0].importe_leido == pytest.approx(191.40)


def test_f003_r4_el_prefilter_con_linea_antigua_deja_null() -> None:
    prefilter = UnitCategoryPrefilter()

    lineas = prefilter.build_albaran_lines(
        [
            RawAlbaranLine(
                merge_line_id=1,
                line_index=1,
                codigo=None,
                descripcion="ARENA",
                unidad_medida="t",
                cantidad=1.0,
                precio_unitario_albaran=10.0,
                importe_albaran=10.0,
                codigo_partida_albaran=None,
            )
        ]
    )

    assert lineas[0].importe_leido is None


# ---------------------------------------------------------------------
# R4 · El total del albaran viaja en el meta del envelope
# ---------------------------------------------------------------------


@dataclass
class _ResultadoFalso:
    provider: str = "claude"
    model_name: str = "fake-model"
    schema_name: str = "valuation"
    prompt_key: str = "valuation_es"
    debug_payload: dict | None = None

    @property
    def parsed(self):
        class _Parsed:
            @staticmethod
            def model_dump():
                return {"lineas": []}

        return _Parsed()


def _pipeline() -> ValueAlbaranPipeline:
    return ValueAlbaranPipeline(
        context_repository=object(),
        pdf_downloader=object(),
        prefilter=UnitCategoryPrefilter(),
        extraction_service=object(),
        max_pdf_mb=10,
        service_version="test",
    )


def _contexto(**kwargs: Any) -> ContextoValoracion:
    base: dict[str, Any] = {
        "document_id": "doc-1",
        "codigo_contrato": "C-1",
        "nombre_contrato": None,
        "cif_proveedor": None,
        "nombre_proveedor": None,
        "codigo_obra": None,
        "nombre_obra": None,
        "pdf_relative_path": None,
        "pdf_filename": None,
        "lineas_albaran": [],
        "lineas_contrato": [],
        "fecha_albaran": "2026-07-01",
        "numero_albaran": "A-1",
    }
    base.update(kwargs)
    return ContextoValoracion(**base)


def test_f003_r4_el_meta_lleva_el_total_del_albaran() -> None:
    envelope = _pipeline()._build_envelope(
        context=_contexto(
            importe_total_albaran=191.40,
            importe_total_incluye_iva=False,
        ),
        results={"claude": _ResultadoFalso(debug_payload={})},
        pdf_attachment=None,
    )

    assert envelope["meta"]["importe_total_albaran"] == pytest.approx(191.40)
    assert envelope["meta"]["importe_total_incluye_iva"] is False


def test_f003_r4_el_meta_de_un_albaran_sin_total_lleva_nulls() -> None:
    envelope = _pipeline()._build_envelope(
        context=_contexto(),
        results={"claude": _ResultadoFalso(debug_payload={})},
        pdf_attachment=None,
    )

    assert envelope["meta"]["importe_total_albaran"] is None
    assert envelope["meta"]["importe_total_incluye_iva"] is None


def test_f003_r4_el_envelope_sin_contrato_tambien_lleva_el_total() -> None:
    """La rama no_contract construye su meta aparte: no puede quedarse
    atras (sv6 la persiste igual)."""

    @dataclass
    class _Peticion:
        document_id: str = "doc-1"

    envelope = _pipeline()._envelope_no_contract(
        request=_Peticion(),
        raw_ctx=ValuationContextRaw(
            document_id="doc-1",
            codigo_contrato_seleccionado=None,
            contrato=None,
            lineas_albaran=[],
            lineas_contrato=[],
            fecha_albaran="2026-07-01",
            numero_albaran="A-1",
            importe_total_albaran=191.40,
            importe_total_incluye_iva=False,
        ),
    )

    assert envelope["meta"]["importe_total_albaran"] == pytest.approx(191.40)
    assert envelope["meta"]["importe_total_incluye_iva"] is False
