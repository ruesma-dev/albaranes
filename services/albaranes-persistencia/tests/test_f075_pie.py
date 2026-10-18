# tests/test_f075_pie.py
"""F-075 · el pie del albarán en sv3: se guarda (R15, ``-k r15``) y se usa
como control (R16–R18, ``-k "r16 or r17 or r18"``).

El pie son cuatro cifras impresas: ``base_imponible``, ``tipo_iva_pct``,
``cuota_iva`` y ``total_albaran``. Es un control, nunca una fuente de
importes. Sin red ni BBDD (salvo SQLite en memoria donde se dice).
"""
from __future__ import annotations

import pytest

from domain.models.extraction_models import CabeceraAlbaran, ExtractionEnvelope

PIE = ("base_imponible", "tipo_iva_pct", "cuota_iva", "total_albaran")

_META = {
    "prompt_key": "albaran_factura_es", "schema": "albaran_v2", "source_filename": "a.pdf",
    "source_mime_type": "application/pdf", "source_sha256": "0" * 64, "model": "m",
    "processed_at_utc": "2026-10-18T10:00:00Z",
}


def _envelope(cabecera: dict, lineas=None) -> ExtractionEnvelope:
    return ExtractionEnvelope.model_validate({
        "meta": dict(_META),
        "data": {"cabecera": {"proveedor_nombre": "DISCOIN", "numero_albaran": "A-1", **cabecera},
                 "lineas": lineas or [{"concepto": "TUBO", "cantidad": 2, "precio_neto": 100.0}]},
    })


# ------------------------------------------------------------------ #
# R15 · esquema: ORM, DDL y modelo de cabecera
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("columna", PIE)
def test_f075_r15_el_orm_tiene_las_cuatro_columnas_en_las_dos_tablas(columna):
    from sqlalchemy import Float

    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm, AlbaranDocumentOrm

    for orm in (AlbaranDocumentOrm, AlbaranDocumentMergeOrm):
        col = orm.__table__.columns[columna]
        assert isinstance(col.type, Float) and col.nullable


@pytest.mark.parametrize("columna", PIE)
def test_f075_r15_el_ddl_las_anade_idempotente_en_las_dos_tablas(columna):
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    for tabla in ("albaran_documents", "albaran_documents_merge"):
        sentencia = f"ALTER TABLE {tabla} ADD COLUMN IF NOT EXISTS {columna} DOUBLE PRECISION"
        assert sentencia in _PHASE2_DDL, sentencia


def test_f075_r15_el_ddl_va_antes_de_la_tabla_de_altas():
    """Las ALTER del pie van con las de la cabecera, no tras la tabla nueva."""
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    altas = next(i for i, s in enumerate(_PHASE2_DDL) if "albaran_altas_sigrid (" in s)
    pies = [i for i, s in enumerate(_PHASE2_DDL) if "base_imponible" in s]
    assert pies and max(pies) < altas


def test_f075_r15_la_cabecera_admite_el_pie_y_sigue_cerrada():
    cab = CabeceraAlbaran(base_imponible=100.0, tipo_iva_pct=21, cuota_iva=21.0, total_albaran=121.0)
    assert (cab.base_imponible, cab.tipo_iva_pct, cab.cuota_iva, cab.total_albaran) == (100.0, 21.0, 21.0, 121.0)
    assert CabeceraAlbaran().total_albaran is None
    with pytest.raises(Exception):
        CabeceraAlbaran(subtotal=3.0)


def test_f075_r15_el_normalizador_deja_el_pie_como_numero():
    from application.services.albaran_normalizer import AlbaranNormalizer

    cab = AlbaranNormalizer().normalize_header(CabeceraAlbaran.model_construct(
        base_imponible="1.234,56", tipo_iva_pct="21", cuota_iva=None, total_albaran="abc",
    ))
    assert cab.base_imponible == 1234.56
    assert cab.tipo_iva_pct == 21.0
    assert cab.cuota_iva is None and cab.total_albaran is None


def test_f075_r15_fusion_por_proveedor_como_los_demas_campos_de_cabecera():
    from application.services.albaran_confidence_service import AlbaranConfidenceService
    from domain.models.extraction_models import ProviderExtractionEnvelope

    openai = _envelope({"base_imponible": 100.0, "total_albaran": 121.0})
    gemini = ProviderExtractionEnvelope.model_validate({
        "meta": dict(_META),
        "data": {"cabecera": {"proveedor_nombre": "DISCOIN", "base_imponible": 99.0, "cuota_iva": 21.0},
                 "lineas": [{"concepto": "TUBO", "cantidad": 2, "precio_neto": 100.0}]},
    })
    cab = AlbaranConfidenceService().build_merge_analysis(openai=openai, gemini=gemini).merged_envelope.data.cabecera
    # gemini primero; lo que no trae, de openai (coalesce, como forma_pago).
    assert (cab.base_imponible, cab.cuota_iva, cab.total_albaran, cab.tipo_iva_pct) == (99.0, 21.0, 121.0, None)


def test_f075_r15_el_pie_no_cambia_la_confianza():
    from application.services.albaran_confidence_service import AlbaranConfidenceService

    servicio = AlbaranConfidenceService()
    sin = servicio.build_merge_analysis(openai=_envelope({}), gemini=None)
    con = servicio.build_merge_analysis(
        openai=_envelope({"base_imponible": 100.0, "tipo_iva_pct": 21.0, "cuota_iva": 21.0,
                          "total_albaran": 121.0}), gemini=None)
    assert con.document_confidence_pct == sin.document_confidence_pct
    assert con.review_reasons == sin.review_reasons


@pytest.mark.parametrize("merge", [True, False])
def test_f075_r15_se_persiste_en_las_dos_tablas(merge):
    from domain.models.persistence_models import StoredFile
    from infrastructure.database.orm_models import (
        AlbaranDocumentMergeOrm,
        AlbaranDocumentOrm,
        AlbaranLineMergeOrm,
        AlbaranLineOrm,
    )
    from infrastructure.database.sqlalchemy_albaran_repository import SqlAlchemyAlbaranRepository

    envelope = _envelope({"base_imponible": 100.0, "tipo_iva_pct": 21.0, "cuota_iva": 21.0,
                          "total_albaran": 121.0})
    documento = SqlAlchemyAlbaranRepository(session_factory=None)._build_document_orm(
        orm_document_cls=AlbaranDocumentMergeOrm if merge else AlbaranDocumentOrm,
        orm_line_cls=AlbaranLineMergeOrm if merge else AlbaranLineOrm,
        document_id="doc-f075", provider_origin="openai", provider_envelope=envelope, context={},
        email_ctx={}, document_ctx={},
        stored_file=StoredFile(drive_id="d", item_id="i", relative_path="r", web_url=None, share_url=None),
        ia_input_payload={}, ia_output_payload={}, ia_input_relative_path=None, ia_input_web_url=None,
        ia_output_relative_path=None, ia_output_web_url=None, raw_lines=envelope.data.lineas,
        document_confidence_pct=90.0, review_required=False, review_reasons=[], comparison_summary={},
        line_results=None,
    )
    assert (documento.base_imponible, documento.tipo_iva_pct, documento.cuota_iva,
            documento.total_albaran) == (100.0, 21.0, 21.0, 121.0)
