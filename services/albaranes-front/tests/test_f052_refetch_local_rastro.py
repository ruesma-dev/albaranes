# tests/test_f052_refetch_local_rastro.py
"""F-052 R22 · el re-fetch local de sv4 (modo solo-front) sella el rastro.

``LocalContratoRefetchClient`` busca contratos en Sigrid sin sv3 ni colas.
Tras F-052 deja el mismo rastro que sv3 (R21) en las cuatro columnas
``contratos_busqueda_*`` del merge, con CIF y obra normalizados:

- ``sin_datos``: faltaba el CIF o la obra no valida (no se consulta).
- ``error``: la consulta lanzó (incluido un truncado) o no se pudieron
  guardar los contratos (misma extensión de R21 que en sv3).
- ``ninguno``: consulta correcta, 0 contratos.
- ``encontrados``: 1 o más.

Best-effort: si el sellado falla, el outcome no cambia.

Sin red ni BBDD real (dobles y SQLite en memoria).
"""
from __future__ import annotations

import logging
from datetime import datetime

import pytest
from domain.models.review_models import (
    BUSQUEDA_ENCONTRADOS,
    BUSQUEDA_ERROR,
    BUSQUEDA_NINGUNO,
    BUSQUEDA_SIN_DATOS,
)
from infrastructure.sigrid.local_refetch_client import (
    LocalContratoRefetchClient,
)
from ruesma_comun.sigrid import SigridRespuestaTruncada
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DOC_ID = "f052-doc-0000-0000-0000-000026122"


class _Contrato:
    def __init__(self, codigo):
        self.codigo_contrato = codigo


class _RepositorioFalso:
    def __init__(self, *, cif="B82899550", obra="0691", falla_replace=None,
                 falla_sello=None):
        self._cif = cif
        self._obra = obra
        self._falla_replace = falla_replace
        self._falla_sello = falla_sello
        self.sellos: list[tuple] = []

    def get_merge_cif_and_obra(self, *, document_id):
        return self._cif, self._obra

    def replace_contratos_and_select(self, *, document_id, contratos):
        if self._falla_replace is not None:
            raise self._falla_replace
        return contratos[0].codigo_contrato if len(contratos) == 1 else None

    def sellar_busqueda_contratos(self, *, document_id, cif, obra, resultado):
        if self._falla_sello is not None:
            raise self._falla_sello
        self.sellos.append((document_id, cif, obra, resultado))


class _SigridFalso:
    def __init__(self, contratos=(), lanza=None):
        self._contratos = list(contratos)
        self._lanza = lanza
        self.llamadas = 0

    def fetch_contratos(self, *, cif_proveedor, codigo_obra_normalizado):
        self.llamadas += 1
        if self._lanza is not None:
            raise self._lanza
        return self._contratos


def _refetch(repo, sigrid):
    cliente = LocalContratoRefetchClient(sigrid_client=sigrid, repository=repo)
    return cliente.refetch(document_id=DOC_ID)


# ------------------------------------------------------------------ #
# Una salida, un sello
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("cif", "obra", "sello"),
    [
        (None, "0691", (DOC_ID, None, "0691", BUSQUEDA_SIN_DATOS)),
        ("  ", "691", (DOC_ID, None, "0691", BUSQUEDA_SIN_DATOS)),
        ("B82899550", "abc", (DOC_ID, "B82899550", None, BUSQUEDA_SIN_DATOS)),
        ("b 82899550", None, (DOC_ID, "B82899550", None, BUSQUEDA_SIN_DATOS)),
    ],
    ids=["sin_cif", "cif_en_blanco", "obra_invalida", "sin_obra"],
)
def test_f052_r22_sin_datos_sella_sin_datos(cif, obra, sello):
    repo = _RepositorioFalso(cif=cif, obra=obra)
    sigrid = _SigridFalso()
    outcome = _refetch(repo, sigrid)
    assert outcome.status == "skipped_missing_data"
    assert sigrid.llamadas == 0
    assert repo.sellos == [sello]


@pytest.mark.parametrize(
    "excepcion",
    [SigridRespuestaTruncada("header_and_lines", 1001), RuntimeError("HTTP 500")],
    ids=["truncado", "http"],
)
def test_f052_r22_consulta_que_lanza_sella_error(excepcion):
    repo = _RepositorioFalso()
    outcome = _refetch(repo, _SigridFalso(lanza=excepcion))
    assert outcome.status == "sigrid_error"
    assert repo.sellos == [(DOC_ID, "B82899550", "0691", BUSQUEDA_ERROR)]


def test_f052_r22_cero_contratos_sella_ninguno():
    repo = _RepositorioFalso()
    outcome = _refetch(repo, _SigridFalso())
    assert outcome.status == "no_results"
    assert repo.sellos == [(DOC_ID, "B82899550", "0691", BUSQUEDA_NINGUNO)]


@pytest.mark.parametrize("n", [1, 3])
def test_f052_r22_contratos_encontrados_sella_encontrados(n):
    repo = _RepositorioFalso()
    contratos = [_Contrato(f"CTSU24/04{i:02d}") for i in range(n)]
    outcome = _refetch(repo, _SigridFalso(contratos))
    assert outcome.count == n
    assert repo.sellos == [(DOC_ID, "B82899550", "0691", BUSQUEDA_ENCONTRADOS)]


def test_f052_r22_cif_y_obra_se_sellan_normalizados():
    """``B 82899550`` / ``691`` ⇒ ``B82899550`` / ``0691``, como sv3."""
    repo = _RepositorioFalso(cif=" b 82899550 ", obra="691")
    _refetch(repo, _SigridFalso())
    assert repo.sellos == [(DOC_ID, "B82899550", "0691", BUSQUEDA_NINGUNO)]


def test_f052_r22_fallo_guardando_los_contratos_sella_error_y_propaga():
    """Extensión de R21 (igual que sv3): el documento se queda sin los
    contratos nuevos; ni ``encontrados`` ni ``ninguno`` serían verdad. El
    error sigue subiendo al endpoint como hasta ahora."""
    repo = _RepositorioFalso(falla_replace=RuntimeError("BBDD caída"))
    with pytest.raises(RuntimeError, match="BBDD caída"):
        _refetch(repo, _SigridFalso([_Contrato("CTSU24/0402")]))
    assert repo.sellos == [(DOC_ID, "B82899550", "0691", BUSQUEDA_ERROR)]


def test_f052_r22_documento_inexistente_no_sella():
    repo = _RepositorioFalso(cif=None, obra=None)
    with pytest.raises(KeyError):
        _refetch(repo, _SigridFalso())
    assert repo.sellos == []


# ------------------------------------------------------------------ #
# Best-effort
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("repo_kw", "sigrid", "status"),
    [
        ({"cif": None}, _SigridFalso(), "skipped_missing_data"),
        ({}, _SigridFalso(lanza=RuntimeError("x")), "sigrid_error"),
        ({}, _SigridFalso(), "no_results"),
        ({}, _SigridFalso([_Contrato("A")]), "found_single"),
    ],
    ids=["sin_datos", "error", "ninguno", "encontrados"],
)
def test_f052_r22_fallo_del_sellado_no_cambia_el_outcome(
    caplog, repo_kw, sigrid, status,
):
    repo = _RepositorioFalso(falla_sello=RuntimeError("columna ausente"),
                             **repo_kw)
    with caplog.at_level(logging.ERROR):
        outcome = _refetch(repo, sigrid)
    assert outcome.status == status
    assert any("rastro" in r.getMessage() and r.exc_info
               for r in caplog.records)


def test_f052_r22_repositorio_sin_el_metodo_no_rompe_el_refetch():
    class _Viejo(_RepositorioFalso):
        sellar_busqueda_contratos = None  # type: ignore[assignment]

    outcome = _refetch(_Viejo(), _SigridFalso())
    assert outcome.status == "no_results"


# ------------------------------------------------------------------ #
# El repositorio de sv4 escribe las cuatro columnas
# ------------------------------------------------------------------ #
class _FactoriaSqlite:
    def __init__(self, motor):
        self._motor = motor

    def create_session(self):
        return Session(self._motor)


@pytest.fixture
def repo_sqlite(monkeypatch):
    from infrastructure.database.orm_models import Base
    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    motor = create_engine("sqlite://")
    Base.metadata.create_all(motor)
    with Session(motor) as sesion:
        sesion.execute(text(
            "INSERT INTO albaran_documents_merge (id, provider_origin, "
            "source_filename, source_mime_type, source_sha256, prompt_key, "
            "schema_name, model_name, raw_extraction_json, created_at_utc, "
            "is_active, approved) VALUES (:id, 'merge', 'f.pdf', 'a/p', :sha, "
            "'p', 's', 'm', '{}', '2026-09-29', 1, 0)"
        ), {"id": DOC_ID, "sha": "0" * 64})
        sesion.commit()
    repo = AlbaranReviewRepository(_FactoriaSqlite(motor))
    monkeypatch.setattr(repo, "initialize", lambda: True)
    yield repo, motor
    motor.dispose()


def _fila(motor):
    with Session(motor) as sesion:
        return sesion.execute(text(
            "SELECT contratos_busqueda_cif, contratos_busqueda_obra, "
            "contratos_busqueda_resultado, contratos_busqueda_at_utc "
            "FROM albaran_documents_merge WHERE id = :id"
        ), {"id": DOC_ID}).one()


def test_f052_r22_el_repositorio_escribe_el_rastro_con_fecha_utc(repo_sqlite):
    repo, motor = repo_sqlite
    repo.sellar_busqueda_contratos(
        document_id=DOC_ID, cif="B82899550", obra="0691",
        resultado=BUSQUEDA_ENCONTRADOS,
    )
    cif, obra, resultado, at_utc = _fila(motor)
    assert (cif, obra, resultado) == ("B82899550", "0691", BUSQUEDA_ENCONTRADOS)
    assert datetime.fromisoformat(at_utc).utcoffset().total_seconds() == 0


def test_f052_r22_el_repositorio_rechaza_un_resultado_desconocido(repo_sqlite):
    repo, motor = repo_sqlite
    with pytest.raises(ValueError, match="desconocido"):
        repo.sellar_busqueda_contratos(
            document_id=DOC_ID, cif="B82899550", obra="0691",
            resultado="buscando",
        )
    assert _fila(motor) == (None, None, None, None)


@pytest.mark.parametrize("obra", ["12", "1234"])
def test_f052_cr_c1_local_sella_sin_datos_como_sv3(obra):
    """CR-C1: obra que sv3 no admite ⇒ no se consulta y se sella sin_datos."""
    repo = _RepositorioFalso(obra=obra)
    sigrid = _SigridFalso()
    outcome = _refetch(repo, sigrid)
    assert outcome.status == "skipped_missing_data"
    assert sigrid.llamadas == 0
    assert repo.sellos == [(DOC_ID, "B82899550", None, BUSQUEDA_SIN_DATOS)]
