# tests/test_f062_r8_pipeline_tres_casos.py
"""F-062 · R8 — los tres albaranes medidos acaban con contrato encontrado.

19407 y 19394 (HORMIGONES MAT, obra 0720) y 1790636816 (ARIDOS ANFERSA,
obra 0678) se quedaron en ``ninguno`` porque la búsqueda de contratos usó
el CIF mal leído. Aquí se recorren las TRES rutas del pipeline —albarán
nuevo, duplicado y ``reenrich_by_merge_id`` (el ``MensajePersistencia
(force=True)`` de sv4)— con el cliente real de sv3 sobre el doble de
sigrid-api y un merge en memoria.

Sin red ni BBDD.
"""
from __future__ import annotations

from doble_sigrid_api import (
    CIF_ARIDOS_ANFERSA,
    CIF_ARIDOS_SUR,
    CIF_HORMIGONERA_EMPATE,
    CIF_HORMIGONES_MAT,
    CIF_LEIDO_19394,
    CIF_LEIDO_19407,
    CIF_LEIDO_1790636816,
    CONTRATO_ARIDOS_ANFERSA,
    CONTRATO_HORMIGONES_MAT,
    RAZ_HORMIGONES_MAT,
    DobleSigridApi,
    fixture_f062,
)
from ruesma_comun.proveedores import identificador_fiscal_valido


def _doble() -> DobleSigridApi:
    return DobleSigridApi(fixture_f062())


# ------------------------------------------------------------------ #
# T2 · el fixture es el que dice ser (design §8)
# ------------------------------------------------------------------ #
def test_f062_t2_fixture_obras_0720_y_0678():
    cliente = _doble().cliente()
    obra_0720 = {r.cif: r for r in cliente.fetch_contratos_resumen_por_obra(codigo_obra="0720")}
    obra_0678 = {r.cif: r for r in cliente.fetch_contratos_resumen_por_obra(codigo_obra="0678")}
    assert set(obra_0720) == {CIF_HORMIGONES_MAT, CIF_HORMIGONERA_EMPATE}
    assert set(obra_0678) == {CIF_ARIDOS_ANFERSA, CIF_ARIDOS_SUR}
    assert obra_0720[CIF_HORMIGONES_MAT].nombre == RAZ_HORMIGONES_MAT
    assert obra_0720[CIF_HORMIGONES_MAT].codigos_contratos == (CONTRATO_HORMIGONES_MAT,)
    assert obra_0678[CIF_ARIDOS_ANFERSA].codigos_contratos == (CONTRATO_ARIDOS_ANFERSA,)


def test_f062_t2_los_cif_del_fixture_son_validos_y_los_leidos_no():
    for cif in (CIF_HORMIGONES_MAT, CIF_HORMIGONERA_EMPATE, CIF_ARIDOS_ANFERSA, CIF_ARIDOS_SUR):
        assert identificador_fiscal_valido(cif), cif
    for cif in (CIF_LEIDO_19407, CIF_LEIDO_19394, CIF_LEIDO_1790636816):
        assert not identificador_fiscal_valido(cif), cif


def test_f062_t2_los_leidos_no_existen_en_prv_y_los_reales_si():
    cliente = _doble().cliente()
    for cif in (CIF_LEIDO_19407, CIF_LEIDO_19394, CIF_LEIDO_1790636816):
        assert cliente.fetch_proveedor_by_cif(cif=cif) is None
    assert cliente.fetch_proveedor_by_cif(cif=CIF_HORMIGONES_MAT) == (
        CIF_HORMIGONES_MAT, RAZ_HORMIGONES_MAT,
    )


def test_f062_t2_contratos_con_lineas_del_cif_real_y_ninguno_del_leido():
    cliente = _doble().cliente()
    [contrato] = cliente.fetch_contratos(
        cif_proveedor=CIF_HORMIGONES_MAT, codigo_obra_normalizado="0720",
    )
    assert contrato.codigo_contrato == CONTRATO_HORMIGONES_MAT
    assert len(contrato.lines) == 2
    assert cliente.fetch_contratos(
        cif_proveedor=CIF_LEIDO_19407, codigo_obra_normalizado="0720",
    ) == []


# ------------------------------------------------------------------ #
# R8 · las tres rutas del pipeline (T9)
# ------------------------------------------------------------------ #
import hashlib

import pytest
from doble_sigrid_api import RAZ_ARIDOS_ANFERSA
from f062_dobles import DOC, RepoRed, resolver

from application.pipelines.persist_albaran_pipeline import (
    PersistAlbaranPipeline,
    PersistAlbaranRequest,
)
from application.services.albaran_normalizer import AlbaranNormalizer
from application.services.contrato_enrichment_service import (
    ContratoEnrichmentService,
)
from domain.models.persistence_models import ExistingDocument, StoredFile

CASOS = [
    pytest.param(CIF_LEIDO_19407, "Hormigones Mat SL", "0720", CIF_HORMIGONES_MAT,
                 RAZ_HORMIGONES_MAT, CONTRATO_HORMIGONES_MAT, id="19407"),
    pytest.param(CIF_LEIDO_19394, "Hormigones Mat SL", "0720", CIF_HORMIGONES_MAT,
                 RAZ_HORMIGONES_MAT, CONTRATO_HORMIGONES_MAT, id="19394"),
    pytest.param(CIF_LEIDO_1790636816, "ARIDOS ANFERSA SL", "0678", CIF_ARIDOS_ANFERSA,
                 RAZ_ARIDOS_ANFERSA, CONTRATO_ARIDOS_ANFERSA, id="1790636816"),
]

_PDF = b"%PDF-1.4 albaran F-062"
_SHA256 = hashlib.sha256(_PDF).hexdigest()


class MergeEnMemoria(RepoRed):
    """El merge de un albarán: lo que escribe el resolver (``RepoRed``) y
    lo que leen y escriben la búsqueda de contratos y el pipeline."""

    def __init__(self, *, existe: bool, **kwargs) -> None:
        super().__init__(**kwargs)
        self.existe = existe
        self.contratos: list = []
        self.seleccionado: str | None = None
        self.rastro: list[tuple[str | None, str | None, str]] = []
        self.guardados = 0

    # --- pipeline ---------------------------------------------------- #
    def get_by_sha256(self, source_sha256: str):
        if not self.existe:
            return None
        return ExistingDocument(document_id=DOC, source_sha256=source_sha256,
                                sharepoint_url=None, stored_lines=1)

    def save(self, *, envelope, context, stored_file):
        self.guardados += 1
        cab = envelope.data.cabecera
        self.cif, self.nombre, self.obra = cab.proveedor_cif, cab.proveedor_nombre, cab.obra_codigo
        self.origen = None
        self.existe = True
        return ExistingDocument(document_id=DOC, source_sha256=_SHA256,
                                sharepoint_url=None, stored_lines=1)

    # --- búsqueda de contratos -------------------------------------- #
    def get_merge_cif_and_obra(self, *, document_id: str):
        return self.cif, self.obra

    def get_existing_pdf_paths(self, *, document_id: str):
        return {}

    def get_selected_contrato_codigo(self, *, document_id: str):
        return self.seleccionado

    def replace_contratos(self, *, document_id: str, contratos) -> None:
        self.contratos = list(contratos)

    def set_selected_contrato(self, *, document_id: str, codigo_contrato: str, origen=None) -> None:
        self.seleccionado = codigo_contrato

    def update_merge_proveedor_nombre(self, *, document_id: str, nombre_proveedor: str) -> bool:
        self.nombre = nombre_proveedor
        return True

    def sellar_busqueda_contratos(self, *, document_id: str, cif, obra, resultado) -> None:
        self.rastro.append((cif, obra, resultado))


class _Almacen:
    def upload(self, **_kwargs) -> StoredFile:
        return StoredFile(drive_id="d", item_id="i", relative_path="input/x.pdf",
                          web_url=None, share_url=None)


def _envelope(cif: str, nombre: str, obra: str) -> dict:
    return {
        "meta": {
            "prompt_key": "albaran_revision_fase2", "schema": "albaran_v2",
            "source_filename": "albaran.pdf", "source_mime_type": "application/pdf",
            "source_sha256": _SHA256, "model": "gpt-5.2",
            "processed_at_utc": "2026-10-07T08:00:00+00:00",
        },
        "data": {
            "cabecera": {"proveedor_cif": cif, "proveedor_nombre": nombre, "obra_codigo": obra,
                         "numero_albaran": "19407", "fecha": "2026-10-06"},
            "lineas": [{"concepto": "HORMIGON HA-25/B/20/IIa", "cantidad": 6.0}],
        },
        "debug": {},
    }


def _pipeline(merge: MergeEnMemoria, doble: DobleSigridApi, **kwargs) -> PersistAlbaranPipeline:
    cliente = doble.cliente()
    return PersistAlbaranPipeline(
        repository=merge,
        document_storage=_Almacen(),
        normalizer=AlbaranNormalizer(),
        header_resolver_service=resolver(cliente, merge, **kwargs),
        contrato_enrichment_service=ContratoEnrichmentService(client=cliente, repository=merge),
    )


def _request(cif, nombre, obra, *, force=False) -> PersistAlbaranRequest:
    return PersistAlbaranRequest(
        filename="albaran.pdf", mime_type="application/pdf", file_bytes=_PDF,
        extraction_envelope=_envelope(cif, nombre, obra), context={}, force_refetch=force,
    )


def _asserts_encontrado(merge, doble, real, raz, contrato, obra):
    assert (merge.cif, merge.nombre, merge.origen) == (real, raz, "deterministic")
    assert merge.rastro[-1] == (real, obra, "encontrados")
    assert [c.codigo_contrato for c in merge.contratos] == [contrato]
    assert merge.seleccionado == contrato
    # La búsqueda de contratos de ESA pasada usó el CIF aplicado, nunca el leído.
    cifs_buscados = {p["parameters"][0] for p in doble.peticiones_con("AS contrato_ide")}
    assert cifs_buscados == {real}
    assert merge.review_required is True


@pytest.mark.parametrize(("leido", "nombre", "obra", "real", "raz", "contrato"), CASOS)
def test_f062_r8_albaran_nuevo_acaba_en_encontrados(leido, nombre, obra, real, raz, contrato):
    doble = DobleSigridApi(fixture_f062())
    merge = MergeEnMemoria(existe=False, cif=None, nombre=None, obra=None)

    resultado = _pipeline(merge, doble).run(_request(leido, nombre, obra))

    assert (resultado.duplicate, resultado.contratos_count) == (False, 1)
    assert resultado.selected_contrato_codigo == contrato
    assert merge.guardados == 1
    _asserts_encontrado(merge, doble, real, raz, contrato, obra)


@pytest.mark.parametrize(("leido", "nombre", "obra", "real", "raz", "contrato"), CASOS)
def test_f062_r8_duplicado_acaba_en_encontrados(leido, nombre, obra, real, raz, contrato):
    doble = DobleSigridApi(fixture_f062())
    merge = MergeEnMemoria(existe=True, cif=leido, nombre=nombre, obra=obra, origen="ia")

    resultado = _pipeline(merge, doble).run(_request(leido, nombre, obra))

    assert (resultado.duplicate, resultado.contratos_count) == (True, 1)
    assert merge.guardados == 0
    _asserts_encontrado(merge, doble, real, raz, contrato, obra)


@pytest.mark.parametrize(("leido", "nombre", "obra", "real", "raz", "contrato"), CASOS)
def test_f062_r8_reenrich_desde_sv4_acaba_en_encontrados(leido, nombre, obra, real, raz, contrato):
    """«Solo volver a buscar» / «Guardar y volver a buscar»: el
    ``MensajePersistencia(force=True)`` que corrige un documento antiguo."""
    doble = DobleSigridApi(fixture_f062())
    merge = MergeEnMemoria(existe=True, cif=leido, nombre=nombre, obra=obra, origen="ia")
    merge.rastro.append((leido, obra, "ninguno"))  # lo que quedó la primera vez

    assert _pipeline(merge, doble).reenrich_by_merge_id(merge_document_id=DOC, force_refetch=True)

    _asserts_encontrado(merge, doble, real, raz, contrato, obra)


@pytest.mark.parametrize(("leido", "nombre", "obra", "real", "raz", "contrato"), CASOS)
def test_f062_r8_con_la_correccion_apagada_sigue_en_ninguno(leido, nombre, obra, real, raz, contrato):
    """El control de la vuelta atrás: sin F-062, los tres casos medidos se
    quedan como los encontró el humano."""
    doble = DobleSigridApi(fixture_f062())
    merge = MergeEnMemoria(existe=True, cif=leido, nombre=nombre, obra=obra, origen="ia")

    _pipeline(merge, doble, correccion_enabled=False).reenrich_by_merge_id(
        merge_document_id=DOC, force_refetch=True,
    )

    assert merge.cif == leido
    assert merge.rastro[-1] == (leido, obra, "ninguno")
    assert merge.contratos == []
