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
    from infrastructure.database.orm_models import (
        AlbaranDocumentMergeOrm,
        AlbaranDocumentOrm,
    )
    from sqlalchemy import Float

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
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )

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


# ------------------------------------------------------------------ #
# R16–R18 · PieGuardService
# ------------------------------------------------------------------ #
class _RepoPie:
    def __init__(self, *, pie=(None, None, None, None), importes=(), rompe_lectura=False,
                 rompe_marca=False):
        self.pie = pie
        self.importes = list(importes)
        self.rompe_lectura = rompe_lectura
        self.rompe_marca = rompe_marca
        self.marcas = []
        self.retiradas = []

    def get_merge_pie_para_guard(self, *, document_id):
        if self.rompe_lectura:
            raise RuntimeError("BBDD caída")
        return self.pie, self.importes

    def marcar_revision_cabecera(self, *, document_id, motivo, nota, nota_prefijo):
        if self.rompe_marca:
            raise RuntimeError("BBDD caída")
        self.marcas.append((document_id, motivo, nota, nota_prefijo))

    def retirar_revision_cabecera(self, *, document_id, motivo_prefijo, nota_prefijo):
        self.retiradas.append((document_id, motivo_prefijo, nota_prefijo))


def _guard(repo, **kw):
    from application.services.pie_guard_service import PieGuardService

    return PieGuardService(repository=repo, **kw)


def test_f075_r16_no_cuadra_marca_revision_con_motivo_y_nota():
    from application.services.pie_guard_service import NOTA_PIE_PREFIJO

    repo = _RepoPie(pie=(110.0, 21.0, 23.1, 133.1), importes=[60.0, 40.0, None])
    _guard(repo).check_merge_document(merge_document_id="m1")
    ((doc, motivo, nota, prefijo),) = repo.marcas
    assert doc == "m1"
    assert motivo == "pie_no_cuadra:100.00!=110.00"
    assert prefijo == NOTA_PIE_PREFIJO == "[AVISO] La suma de las líneas no cuadra con el pie del albarán"
    assert nota.startswith(NOTA_PIE_PREFIJO)
    assert "100,00 €" in nota and "110,00 €" in nota and "varias páginas" in nota
    # (O2) Antes de marcar, se retira el `pie_no_cuadra:*` que hubiera.
    assert repo.retiradas == [("m1", "pie_no_cuadra:", NOTA_PIE_PREFIJO)]


def test_f075_r16_sin_base_compara_con_total_menos_cuota():
    repo = _RepoPie(pie=(None, None, 21.0, 131.0), importes=[100.0])
    _guard(repo).check_merge_document(merge_document_id="m1")
    assert repo.marcas[0][1] == "pie_no_cuadra:100.00!=110.00"


def test_f075_r16_tolerancia_configurable():
    repo = _RepoPie(pie=(100.05, None, None, None), importes=[100.0])
    _guard(repo, tolerancia_eur=0.02).check_merge_document(merge_document_id="m1")
    assert len(repo.marcas) == 1
    repo = _RepoPie(pie=(100.05, None, None, None), importes=[100.0])
    _guard(repo, tolerancia_eur=0.10).check_merge_document(merge_document_id="m1")
    assert repo.marcas == [] and len(repo.retiradas) == 1


@pytest.mark.parametrize(("pie", "importes"), [
    ((100.01, 21.0, 21.0, 121.01), [100.0]),        # cuadra
    ((None, None, None, 121.0), [100.0]),           # solo el total: no comparable
    ((None, None, None, None), [100.0]),            # sin pie
    ((110.0, None, None, None), [None, None]),      # el albarán no trae importes
])
def test_f075_r17_cuadra_o_no_comparable_retira_motivo_y_nota(pie, importes):
    from application.services.pie_guard_service import MOTIVO_PIE, NOTA_PIE_PREFIJO

    repo = _RepoPie(pie=pie, importes=importes)
    _guard(repo).check_merge_document(merge_document_id="m1")
    assert repo.marcas == []
    assert repo.retiradas == [("m1", f"{MOTIVO_PIE}:", NOTA_PIE_PREFIJO)]


def test_f075_r18_best_effort_lectura_rota(caplog):
    import logging

    repo = _RepoPie(rompe_lectura=True)
    with caplog.at_level(logging.ERROR):
        _guard(repo).check_merge_document(merge_document_id="m1")
    assert repo.marcas == [] and repo.retiradas == []
    assert any("m1" in r.getMessage() for r in caplog.records)


def test_f075_r18_best_effort_marca_rota():
    repo = _RepoPie(pie=(110.0, None, None, None), importes=[100.0], rompe_marca=True)
    _guard(repo).check_merge_document(merge_document_id="m1")  # no lanza


def test_f075_r18_deshabilitado_no_hace_nada():
    repo = _RepoPie(pie=(110.0, None, None, None), importes=[100.0])
    _guard(repo, enabled=False).check_merge_document(merge_document_id="m1")
    assert repo.marcas == [] and repo.retiradas == []


def test_f075_r18_el_pipeline_lo_llama_junto_al_guard_de_fecha():
    """En los tres puntos (nuevo, duplicado, reenrich), tras el de fecha."""
    import re
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1] / "application" / "pipelines"
              / "persist_albaran_pipeline.py").read_text(encoding="utf-8")
    fecha = [m.start() for m in re.finditer(r"self\._check_fecha_guard_safely\(", fuente)]
    pie = [m.start() for m in re.finditer(r"self\._check_pie_guard_safely\(", fuente)]
    assert len(fecha) == len(pie) == 3
    for f, siguiente_f in zip(fecha, fecha[1:] + [len(fuente)]):
        assert any(f < p < siguiente_f for p in pie)


def test_f075_r18_pipeline_sin_servicio_o_con_fallo_no_rompe():
    from application.pipelines.persist_albaran_pipeline import PersistAlbaranPipeline

    PersistAlbaranPipeline(repository=None, document_storage=None, normalizer=None)._check_pie_guard_safely(
        merge_document_id="m1")

    class _Roto:
        def check_merge_document(self, **_):
            raise RuntimeError("x")

    PersistAlbaranPipeline(repository=None, document_storage=None, normalizer=None,
                           pie_guard_service=_Roto())._check_pie_guard_safely(merge_document_id="m1")


def test_f075_r16_ajuste_por_defecto_de_la_tolerancia():
    from config.settings import Settings

    assert Settings.model_fields["pie_tolerancia_eur"].default == 0.02
    assert Settings.model_fields["pie_tolerancia_eur"].alias == "PIE_TOLERANCIA_EUR"


# ------------------------------------------------------------------ #
# R16, R17 · el repositorio real (SQLite)
# ------------------------------------------------------------------ #
_MOTIVOS_SEMBRADOS = '["fecha_albaran_fuera_de_rango:2023-01-01", "pie_no_cuadra:100.00!=110.00"]'
_NOTAS_SEMBRADAS = "[AVISO] Fecha x\n[AVISO] La suma de las líneas no cuadra con el pie del albarán: y"


@pytest.fixture()
def repo_sqlite(tmp_path):
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    engine = create_engine(f"sqlite:///{tmp_path / 'pie.db'}")
    with engine.begin() as con:
        con.execute(text(
            "CREATE TABLE albaran_documents_merge (id TEXT PRIMARY KEY, base_imponible REAL, "
            "tipo_iva_pct REAL, cuota_iva REAL, total_albaran REAL, review_required BOOLEAN, "
            "review_reasons_json TEXT, review_notes TEXT)"))
        con.execute(text(
            "CREATE TABLE albaran_lines_merge (id INTEGER PRIMARY KEY, document_id TEXT, "
            "line_index INTEGER, precio_neto REAL)"))
        con.execute(text(
            "INSERT INTO albaran_documents_merge VALUES ('m1', 110.0, 21.0, 23.1, 133.1, 1, :m, :n)"),
            {"m": _MOTIVOS_SEMBRADOS, "n": _NOTAS_SEMBRADAS})
        con.execute(text(
            "INSERT INTO albaran_lines_merge (document_id, line_index, precio_neto) VALUES "
            "('m1', 1, 40.0), ('m1', 0, 60.0), ('m1', 2, NULL)"))

    class _Fabrica:
        generation = 1

        def ensure_database_and_engine(self):
            return None

        def create_session(self):
            return Session(engine)

    repo = SqlAlchemyAlbaranRepository(_Fabrica())
    repo._initialized_generation = 1
    return repo, engine


def test_f075_r16_repo_lee_el_pie_y_los_importes(repo_sqlite):
    repo, _ = repo_sqlite
    pie, importes = repo.get_merge_pie_para_guard(document_id="m1")
    assert pie == (110.0, 21.0, 23.1, 133.1)
    assert importes == [60.0, 40.0, None]
    assert repo.get_merge_pie_para_guard(document_id="no") == ((None, None, None, None), [])


def test_f075_r17_repo_retira_motivo_y_nota_sin_bajar_la_revision(repo_sqlite):
    import json

    from application.services.pie_guard_service import MOTIVO_PIE, NOTA_PIE_PREFIJO
    from sqlalchemy import text

    repo, engine = repo_sqlite
    repo.retirar_revision_cabecera(document_id="m1", motivo_prefijo=f"{MOTIVO_PIE}:",
                                   nota_prefijo=NOTA_PIE_PREFIJO)
    with engine.connect() as con:
        revision, motivos, notas = con.execute(text(
            "SELECT review_required, review_reasons_json, review_notes FROM albaran_documents_merge")).one()
    assert revision in (1, True)
    assert json.loads(motivos) == ["fecha_albaran_fuera_de_rango:2023-01-01"]
    assert "La suma de las líneas" not in notas and "[AVISO] Fecha" in notas
    repo.retirar_revision_cabecera(document_id="no-existe", motivo_prefijo="x", nota_prefijo="y")


# ------------------------------------------------------------------ #
# T16 · supervivientes de la campaña (progress/mutacion_F-075.md)
# ------------------------------------------------------------------ #
def test_f075_t16_el_pipeline_llama_al_guard_del_pie():
    from application.pipelines.persist_albaran_pipeline import PersistAlbaranPipeline

    llamadas = []

    class _Espia:
        def check_merge_document(self, *, merge_document_id):
            llamadas.append(merge_document_id)

    PersistAlbaranPipeline(repository=None, document_storage=None, normalizer=None,
                           pie_guard_service=_Espia())._check_pie_guard_safely(merge_document_id="m1")
    assert llamadas == ["m1"]


def test_f075_t16_sin_servicio_solo_lo_dice_el_log(caplog):
    import logging

    from application.pipelines.persist_albaran_pipeline import PersistAlbaranPipeline

    with caplog.at_level(logging.INFO):
        PersistAlbaranPipeline(repository=None, document_storage=None, normalizer=None)._check_pie_guard_safely(
            merge_document_id="m1")
    assert any("SKIP" in r.getMessage() for r in caplog.records)
    assert not any(r.levelno >= logging.ERROR for r in caplog.records)


def test_f075_t16_el_pie_que_no_coincide_entre_ias_no_cambia_la_confianza():
    """Peso 0 y no crítico: ni un conflicto entre proveedores mueve la confianza ni
    manda a revisión (con peso o crítico, sí)."""
    from application.services.albaran_confidence_service import AlbaranConfidenceService
    from domain.models.extraction_models import ProviderExtractionEnvelope

    def _gemini(cabecera):
        return ProviderExtractionEnvelope.model_validate({
            "meta": dict(_META),
            "data": {"cabecera": {"proveedor_nombre": "DISCOIN", "numero_albaran": "A-1", **cabecera},
                     "lineas": [{"concepto": "TUBO", "cantidad": 2, "precio_neto": 100.0}]},
        })

    servicio = AlbaranConfidenceService()
    pie_openai = {"base_imponible": 100.0, "tipo_iva_pct": 21.0, "cuota_iva": 21.0, "total_albaran": 121.0}
    pie_gemini = {"base_imponible": 50.0, "tipo_iva_pct": 10.0, "cuota_iva": 5.0, "total_albaran": 55.0}
    sin = servicio.build_merge_analysis(openai=_envelope({}), gemini=_gemini({}))
    con = servicio.build_merge_analysis(openai=_envelope(pie_openai), gemini=_gemini(pie_gemini))
    assert con.document_confidence_pct == sin.document_confidence_pct
    assert con.comparison_summary["header"]["score"] == sin.comparison_summary["header"]["score"]
    assert con.review_reasons == sin.review_reasons
    assert con.review_required == sin.review_required


def test_f075_t16_el_guard_del_pie_viene_encendido():
    from config.settings import Settings

    assert Settings.model_fields["pie_guard_enabled"].default is True
    assert Settings.model_fields["pie_guard_enabled"].alias == "PIE_GUARD_ENABLED"


# ------------------------------------------------------------------ #
# Pasada 2 · O2 de la review: un pie que sigue sin cuadrar con otra suma deja UN motivo
# ------------------------------------------------------------------ #
class _RepoConMotivos(_RepoPie):
    """Aplica de verdad las dos operaciones sobre una lista de motivos."""

    def __init__(self, motivos, **kw):
        super().__init__(**kw)
        self.motivos = list(motivos)
        self.orden = []

    def marcar_revision_cabecera(self, *, document_id, motivo, nota, nota_prefijo):
        self.orden.append("marcar")
        if motivo not in self.motivos:
            self.motivos.append(motivo)

    def retirar_revision_cabecera(self, *, document_id, motivo_prefijo, nota_prefijo):
        self.orden.append("retirar")
        self.motivos = [m for m in self.motivos if not m.startswith(motivo_prefijo)]


def test_f075_r16_o2_al_cambiar_la_suma_queda_solo_el_motivo_nuevo():
    repo = _RepoConMotivos(["fecha_albaran_fuera_de_rango:2023-01-01", "pie_no_cuadra:90.00!=110.00"],
                           pie=(110.0, None, None, None), importes=[100.0])
    _guard(repo).check_merge_document(merge_document_id="m1")
    assert repo.motivos == ["fecha_albaran_fuera_de_rango:2023-01-01", "pie_no_cuadra:100.00!=110.00"]
    assert repo.orden == ["retirar", "marcar"]
