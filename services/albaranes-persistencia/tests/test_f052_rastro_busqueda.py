# tests/test_f052_rastro_busqueda.py
"""F-052 T9–T10 · rastro de la búsqueda de contratos (R20, R21).

sv3 es dueño del schema de ``albaran_documents_merge``: añade con DDL
idempotente las cuatro columnas ``contratos_busqueda_*`` (CIF, obra,
resultado y fecha de la última búsqueda) y las sella al terminar
``ContratoEnrichmentService.enrich_merge_document``. sv4 solo las lee.

Sin red ni BBDD: sesión y repositorio dobles.
"""
from __future__ import annotations

import inspect
import re
from datetime import datetime, timedelta, timezone

import pytest

#: (columna, tipo) de design §4. Todas nullable.
_COLUMNAS_RASTRO = (
    ("contratos_busqueda_cif", "VARCHAR(64)"),
    ("contratos_busqueda_obra", "VARCHAR(32)"),
    ("contratos_busqueda_resultado", "VARCHAR(16)"),
    ("contratos_busqueda_at_utc", "VARCHAR(64)"),
)


def _sentencias_del_rastro() -> list[str]:
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    return [s for s in _PHASE2_DDL if "contratos_busqueda_" in s]


# ------------------------------------------------------------------ #
# R20 · DDL idempotente, ORM y schema exportado dicen lo mismo
# ------------------------------------------------------------------ #
def test_f052_r20_el_ddl_anade_las_cuatro_columnas_al_merge():
    from infrastructure.database.phase2_ddl import _PHASE2_DDL

    for columna, tipo in _COLUMNAS_RASTRO:
        esperado = (
            "ALTER TABLE albaran_documents_merge "
            f"ADD COLUMN IF NOT EXISTS {columna} {tipo}"
        )
        assert esperado in _PHASE2_DDL, f"falta el ALTER de {columna}"


def test_f052_r20_el_ddl_del_rastro_es_idempotente_y_solo_toca_el_merge():
    sentencias = _sentencias_del_rastro()
    assert len(sentencias) == 4
    for sentencia in sentencias:
        assert sentencia.startswith("ALTER TABLE albaran_documents_merge ADD COLUMN IF NOT EXISTS ")
        for prohibido in ("DROP", "RENAME", "NOT NULL", "DEFAULT", "DELETE", "UPDATE"):
            assert prohibido not in sentencia, f"{prohibido} en {sentencia}"


def test_f052_r20_schema_contribution_exporta_el_ddl_del_rastro():
    """sv7 aplica el schema de sv3 desde ``schema_contribution``."""
    from infrastructure.database.schema_contribution import get_ddl_statements

    exportadas = {sql for _, sql in get_ddl_statements()}
    for sentencia in _sentencias_del_rastro():
        assert sentencia in exportadas, sentencia


def test_f052_r20_el_orm_del_merge_espeja_las_columnas_del_ddl():
    from infrastructure.database.orm_models import AlbaranDocumentMergeOrm

    columnas = AlbaranDocumentMergeOrm.__table__.columns
    for nombre, tipo in _COLUMNAS_RASTRO:
        assert nombre in columnas, f"el ORM no declara {nombre}"
        assert columnas[nombre].nullable, f"{nombre} debe admitir NULL"
        longitud = int(re.search(r"\((\d+)\)", tipo).group(1))
        assert columnas[nombre].type.length == longitud, f"{nombre}: ORM y DDL difieren"


def test_f052_r20_la_tabla_raw_no_lleva_el_rastro():
    from infrastructure.database.orm_models import AlbaranDocumentOrm

    columnas = AlbaranDocumentOrm.__table__.columns
    for nombre, _ in _COLUMNAS_RASTRO:
        assert nombre not in columnas, f"{nombre} se coló en la tabla raw"


def test_f052_r20_el_puerto_declara_sellar_busqueda_contratos():
    from domain.ports.contrato_merge_repository_port import ContratoMergeRepository

    firma = inspect.signature(ContratoMergeRepository.sellar_busqueda_contratos)
    assert list(firma.parameters)[1:] == ["document_id", "cif", "obra", "resultado"]
    assert all(
        p.kind is inspect.Parameter.KEYWORD_ONLY
        for nombre, p in firma.parameters.items() if nombre != "self"
    )


# --- Repositorio: UPDATE del rastro con una sesión doble ------------- #
class _Sesion:
    def __init__(self) -> None:
        self.sentencias: list[tuple[str, dict]] = []
        self.confirmada = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sentencia, parametros=None):
        self.sentencias.append((str(sentencia), dict(parametros or {})))

    def commit(self):
        self.confirmada = True


class _Fabrica:
    generation = 1

    def __init__(self) -> None:
        self.sesion = _Sesion()

    def ensure_database_and_engine(self):
        pass

    def create_session(self):
        return self.sesion


def _repositorio():
    from infrastructure.database.sqlalchemy_albaran_repository import (
        SqlAlchemyAlbaranRepository,
    )

    fabrica = _Fabrica()
    repositorio = SqlAlchemyAlbaranRepository(session_factory=fabrica)
    repositorio._initialized_generation = fabrica.generation  # sin crear tablas
    return repositorio, fabrica.sesion


@pytest.mark.parametrize("resultado", ["encontrados", "ninguno", "error", "sin_datos"])
def test_f052_r20_el_repositorio_sella_las_cuatro_columnas(resultado):
    repositorio, sesion = _repositorio()
    antes = datetime.now(timezone.utc)

    repositorio.sellar_busqueda_contratos(
        document_id="doc-1", cif="B82899550", obra="0691", resultado=resultado,
    )

    [(sql, parametros)] = sesion.sentencias
    assert sesion.confirmada
    assert re.sub(r"\s+", " ", sql).strip() == (
        "UPDATE albaran_documents_merge "
        "SET contratos_busqueda_cif = :cif, contratos_busqueda_obra = :obra, "
        "contratos_busqueda_resultado = :resultado, "
        "contratos_busqueda_at_utc = :at_utc WHERE id = :doc_id"
    )
    at_utc = datetime.fromisoformat(parametros.pop("at_utc"))
    assert at_utc.utcoffset() == timedelta(0)
    assert antes <= at_utc <= datetime.now(timezone.utc)
    assert parametros == {
        "cif": "B82899550", "obra": "0691", "resultado": resultado, "doc_id": "doc-1",
    }


def test_f052_r20_el_repositorio_sella_sin_datos_con_nulos():
    repositorio, sesion = _repositorio()
    repositorio.sellar_busqueda_contratos(
        document_id="doc-1", cif=None, obra=None, resultado="sin_datos",
    )
    [(_, parametros)] = sesion.sentencias
    assert (parametros["cif"], parametros["obra"]) == (None, None)


@pytest.mark.parametrize("resultado", ["", "ok", "ENCONTRADOS", None])
def test_f052_r20_el_repositorio_rechaza_un_resultado_desconocido(resultado):
    repositorio, sesion = _repositorio()
    with pytest.raises(ValueError, match="resultado"):
        repositorio.sellar_busqueda_contratos(
            document_id="doc-1", cif="B1", obra="0691", resultado=resultado,
        )
    assert sesion.sentencias == []


# ------------------------------------------------------------------ #
# R21 · enrich_merge_document sella el rastro en cada salida
# ------------------------------------------------------------------ #
DOC = "doc-f052-rastro"


def _contrato(codigo: str):
    from domain.models.contrato_models import ContratoEnrichmentResult

    return ContratoEnrichmentResult(
        codigo_contrato=codigo, nombre_contrato=None, fecha_alta_contrato=None,
        fecha_contrato=None, vigencia_desde=None, vigencia_hasta=None,
        importe_total=None, cif_proveedor="B82899550",
        nombre_proveedor="SALMEDINA, S.L.", codigo_obra="0691", nombre_obra=None,
        gra_rep_ide=None, pdf_sharepoint_relative_path="contratos/c.pdf",
    )


class _RepoEnrich:
    """Lo que ``enrich_merge_document`` usa del repositorio."""

    def __init__(
        self, cif: str | None = "B82899550", obra: str | None = "0691", *,
        falla_sellado: bool = False, falla_replace: bool = False,
    ) -> None:
        self._cif, self._obra = cif, obra
        self._falla_sellado = falla_sellado
        self._falla_replace = falla_replace
        self.sellos: list[tuple[str, str | None, str | None, str]] = []
        self.guardados: list[list] = []

    def get_merge_cif_and_obra(self, *, document_id):
        return self._cif, self._obra

    def get_merge_fecha(self, *, document_id):
        return "2026-09-01"

    def append_review_note(self, *, document_id, nota):
        pass

    def remove_review_note_prefix(self, *, document_id, prefijo):
        pass

    def replace_contratos(self, *, document_id, contratos):
        if self._falla_replace:
            raise RuntimeError("BBDD caída guardando contratos")
        self.guardados.append(list(contratos))

    def get_existing_pdf_paths(self, *, document_id):
        return {}

    def get_selected_contrato_codigo(self, *, document_id):
        return None

    def set_selected_contrato(self, *, document_id, codigo_contrato, origen=None):
        pass

    def get_merge_lines_for_scoring(self, *, document_id):
        return []

    def update_merge_proveedor_nombre(self, *, document_id, nombre_proveedor):
        return True

    def sellar_busqueda_contratos(self, *, document_id, cif, obra, resultado):
        if self._falla_sellado:
            raise RuntimeError("BBDD caída sellando el rastro")
        self.sellos.append((document_id, cif, obra, resultado))


class _ClienteContratos:
    def __init__(self, contratos=(), error: Exception | None = None) -> None:
        self._contratos = list(contratos)
        self._error = error
        self.llamadas: list[tuple[str, str]] = []

    def fetch_contratos(self, *, cif_proveedor, codigo_obra_normalizado):
        self.llamadas.append((cif_proveedor, codigo_obra_normalizado))
        if self._error is not None:
            raise self._error
        return list(self._contratos)


class _CacheConHit:
    def find_active_contrato(self, *, codigo_obra, cif_proveedor, fecha_albaran_yyyymmdd):
        return _contrato("CACHE/0001")

    def get_pdf_paths_for_codigos(self, **_):  # pragma: no cover - solo en miss
        return {}

    def upsert_contratos(self, *, contratos):  # pragma: no cover - solo en miss
        pass


def _servicio(cliente, repo, **kwargs):
    from application.services.contrato_enrichment_service import (
        ContratoEnrichmentService,
    )

    return ContratoEnrichmentService(client=cliente, repository=repo, **kwargs)


def _enriquecer(cliente, repo, **kwargs) -> int:
    return _servicio(cliente, repo, **kwargs).enrich_merge_document(merge_document_id=DOC)


@pytest.mark.parametrize(
    "cif,obra,sellado",
    [
        (None, "0691", (None, "0691")),
        (" b 82899550 ", "OBRA-X", ("B82899550", None)),
        ("   ", None, (None, None)),
    ],
)
def test_f052_r21_sin_datos_sella_sin_datos_y_no_consulta(cif, obra, sellado):
    cliente = _ClienteContratos([_contrato("C1")])
    repo = _RepoEnrich(cif, obra)
    assert _enriquecer(cliente, repo) == 0
    assert repo.sellos == [(DOC, *sellado, "sin_datos")]
    assert cliente.llamadas == []


def test_f052_r21_cache_hit_sella_encontrados_sin_ir_a_sigrid():
    cliente = _ClienteContratos(error=AssertionError("no debe llamarse"))
    repo = _RepoEnrich(" b82899550", "691")
    assert _enriquecer(cliente, repo, cache=_CacheConHit()) == 1
    assert repo.sellos == [(DOC, "B82899550", "0691", "encontrados")]
    assert cliente.llamadas == []


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(RuntimeError("sigrid-api HTTP 500"), id="http"),
        pytest.param(None, id="truncado"),
    ],
)
def test_f052_r21_la_consulta_lanza_sella_error(error):
    from ruesma_comun.sigrid import SigridRespuestaTruncada

    error = error or SigridRespuestaTruncada("header_and_lines", 20000)
    repo = _RepoEnrich()
    assert _enriquecer(_ClienteContratos(error=error), repo) == 0
    assert repo.sellos == [(DOC, "B82899550", "0691", "error")]
    assert repo.guardados == []


def test_f052_r13_fetch_contratos_truncado_por_tope_de_paginas_sella_error():
    """R13 de punta a punta con el cliente real: 1.200 líneas, páginas de
    500 y tope de 2 páginas → ``SigridRespuestaTruncada`` → rastro ``error``."""
    from doble_sigrid_api import CIF_GRANDE_0668, DobleSigridApi

    doble = DobleSigridApi()
    repo = _RepoEnrich(CIF_GRANDE_0668, "0668")
    cliente = doble.cliente(pagina_lineas=500, max_paginas=2)
    assert _enriquecer(cliente, repo) == 0
    assert repo.sellos == [(DOC, CIF_GRANDE_0668, "0668", "error")]
    assert repo.guardados == []


def test_f052_r21_cero_contratos_sella_ninguno():
    repo = _RepoEnrich()
    assert _enriquecer(_ClienteContratos([]), repo) == 0
    assert repo.sellos == [(DOC, "B82899550", "0691", "ninguno")]


@pytest.mark.parametrize("n", [1, 3])
def test_f052_r21_con_contratos_sella_encontrados(n):
    repo = _RepoEnrich()
    contratos = [_contrato(f"C{i}") for i in range(n)]
    assert _enriquecer(_ClienteContratos(contratos), repo) == n
    assert repo.sellos == [(DOC, "B82899550", "0691", "encontrados")]


def test_f052_r21_con_el_cliente_real_salmedina_encontrados_y_normalizado():
    from doble_sigrid_api import CIF_SALMEDINA, DobleSigridApi

    repo = _RepoEnrich(" b82899550 ", "691")
    assert _enriquecer(DobleSigridApi().cliente(), repo) == 1
    assert repo.sellos == [(DOC, CIF_SALMEDINA, "0691", "encontrados")]


def test_f052_r21_fallo_guardando_los_contratos_sella_error():
    """La consulta funcionó pero los contratos no se guardaron: el
    documento se queda sin ellos y el rastro no puede decir ni
    ``encontrados`` ni ``ninguno`` (decisión del implementer, ver
    ``progress/impl_F-052.md``)."""
    repo = _RepoEnrich(falla_replace=True)
    assert _enriquecer(_ClienteContratos([_contrato("C1")]), repo) == 0
    assert repo.sellos == [(DOC, "B82899550", "0691", "error")]


def test_f052_r21_servicio_desactivado_no_busca_ni_sella():
    repo = _RepoEnrich()
    assert _enriquecer(_ClienteContratos([_contrato("C1")]), repo, enabled=False) == 0
    assert repo.sellos == []


_SALIDAS = [
    pytest.param({"cif": None}, {}, {}, 0, id="sin_datos"),
    pytest.param({}, {"contratos": [_contrato("C1")]}, {"cache": _CacheConHit()}, 1, id="cache"),
    pytest.param({}, {"error": RuntimeError("x")}, {}, 0, id="error"),
    pytest.param({}, {"contratos": []}, {}, 0, id="ninguno"),
    pytest.param({}, {"contratos": [_contrato("C1"), _contrato("C2")]}, {}, 2, id="encontrados"),
    pytest.param({"falla_replace": True}, {"contratos": [_contrato("C1")]}, {}, 0, id="fallo-guardando"),
]


@pytest.mark.parametrize("repo_kw,cliente_kw,servicio_kw,esperado", _SALIDAS)
def test_f052_r21_fallo_del_sellado_no_cambia_el_valor_devuelto(
    repo_kw, cliente_kw, servicio_kw, esperado, caplog,
):
    repo = _RepoEnrich(**repo_kw, falla_sellado=True)
    with caplog.at_level("ERROR"):
        assert _enriquecer(_ClienteContratos(**cliente_kw), repo, **servicio_kw) == esperado
    assert repo.sellos == []
    assert any("rastro" in r.getMessage() for r in caplog.records if r.exc_info)


@pytest.mark.parametrize("repo_kw,cliente_kw,servicio_kw,esperado", _SALIDAS)
def test_f052_r21_un_solo_sello_por_busqueda(repo_kw, cliente_kw, servicio_kw, esperado):
    repo = _RepoEnrich(**repo_kw)
    assert _enriquecer(_ClienteContratos(**cliente_kw), repo, **servicio_kw) == esperado
    assert len(repo.sellos) == 1


def test_f052_r21_repositorio_sin_el_metodo_no_rompe():
    """Repositorios antiguos (o de otro servicio) sin ``sellar_...``."""

    class _RepoAntiguo(_RepoEnrich):
        sellar_busqueda_contratos = None

    assert _enriquecer(_ClienteContratos([_contrato("C1")]), _RepoAntiguo()) == 1
