# tests/test_f115_seleccion_ajena.py
"""F-115 R2–R6, R8 · la búsqueda de contratos no conserva un contrato ajeno.

Al empezar ``enrich_merge_document`` (cualquier vía), si el contrato
seleccionado no es del proveedor y la obra actuales del merge (R1 de comun),
se pone a NULL la selección y su origen, se retira la nota de auto-selección
de ese código y se registra un INFO (R2, R3); también en las ramas
``sin_datos`` y ``error`` (R4). Un fallo al retirar se registra y el
enriquecimiento sigue (R5). El proveedor nuevo con 1 contrato o con elección
del selector queda seleccionado; con 0 o varios sin elección, NULL (R6).
``reenrich_by_merge_id`` no toca líneas ni blobs (R8).

Casos (a)–(f) de R22. Sin red: repositorio en memoria y, para el SQL de los
dos métodos nuevos, SQLite en un fichero temporal.
"""
from __future__ import annotations

import logging

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

DOC = "doc-f115"
CIF_A, CIF_B, OBRA = "A11111111", "B22222222", "0686"
NOTA_AUTO_A = (
    "[AVISO] Contrato CTA/0001 elegido AUTOMATICAMENTE entre 2 candidatos "
    "(criterio deterministico por familia/palabras). Verificar que es el correcto."
)
OTRA_NOTA = "[NOTA] Revisado por teléfono con el proveedor."


def _contrato(codigo: str, cif: str = CIF_B, obra: str = OBRA, nombre: str | None = None):
    from domain.models.contrato_models import ContratoEnrichmentResult

    return ContratoEnrichmentResult(
        codigo_contrato=codigo, nombre_contrato=nombre, fecha_alta_contrato=None,
        fecha_contrato=None, vigencia_desde=None, vigencia_hasta=None,
        importe_total=None, cif_proveedor=cif, nombre_proveedor="PROVEEDOR B, S.L.",
        codigo_obra=obra, nombre_obra=None, gra_rep_ide=None,
        pdf_sharepoint_relative_path="contratos/c.pdf",
    )


class _RepoMem:
    """Merge en memoria con lo que ``enrich_merge_document`` usa.

    ``filas`` = (document_id, codigo_contrato, cif_proveedor, codigo_obra)
    de ``albaran_contratos_merge``. Los dos métodos nuevos imitan el SQL
    real (las filas del documento; si no hay, las de ese código en
    cualquier documento).
    """

    def __init__(self, *, cif=CIF_B, obra=OBRA, seleccion="CTA/0001", origen="auto_multiple",
                 notas=f"{OTRA_NOTA}\n{NOTA_AUTO_A}", filas=None, falla_pertenencia=False):
        self.cif, self.obra = cif, obra
        self.seleccion, self.origen, self.notas = seleccion, origen, notas
        self.filas = list(filas if filas is not None else [(DOC, "CTA/0001", CIF_A, OBRA)])
        self.falla_pertenencia = falla_pertenencia
        self.limpiezas: list[str] = []
        self.sellos: list[str] = []

    # --- nuevos (F-115) ------------------------------------------- #
    def get_pertenencia_seleccion(self, *, document_id):
        if self.falla_pertenencia:
            raise RuntimeError("BBDD caída leyendo la selección")
        codigo = self.seleccion
        if codigo is None:
            return None, []
        propias = [(c, o) for d, k, c, o in self.filas if d == document_id and k == codigo]
        if propias:
            return codigo, propias
        return codigo, [(c, o) for _, k, c, o in self.filas if k == codigo][:20]

    def clear_selected_contrato(self, *, document_id):
        self.limpiezas.append(document_id)
        self.seleccion, self.origen = None, None

    # --- existentes ------------------------------------------------ #
    def get_merge_cif_and_obra(self, *, document_id):
        return self.cif, self.obra

    def get_merge_fecha(self, *, document_id):
        return "2026-10-01"

    def append_review_note(self, *, document_id, nota):
        if nota not in (self.notas or ""):
            self.notas = f"{self.notas}\n{nota}" if self.notas else nota

    def remove_review_note_prefix(self, *, document_id, prefijo):
        if not self.notas:
            return
        lineas = [ln for ln in self.notas.splitlines() if not ln.strip().startswith(prefijo)]
        self.notas = "\n".join(lineas).strip() or None

    def replace_contratos(self, *, document_id, contratos):
        for c in contratos:
            self.filas.append((document_id, c.codigo_contrato, c.cif_proveedor, c.codigo_obra))

    def get_existing_pdf_paths(self, *, document_id):
        return {}

    def get_selected_contrato_codigo(self, *, document_id):
        return self.seleccion

    def set_selected_contrato(self, *, document_id, codigo_contrato, origen=None):
        self.seleccion = codigo_contrato
        if origen is not None:
            self.origen = origen

    def get_merge_lines_for_scoring(self, *, document_id):
        return []

    def update_merge_proveedor_nombre(self, *, document_id, nombre_proveedor):
        return True

    def sellar_busqueda_contratos(self, *, document_id, cif, obra, resultado):
        self.sellos.append(resultado)


class _Cliente:
    def __init__(self, contratos=(), error: Exception | None = None):
        self.contratos, self.error = list(contratos), error
        self.llamadas = 0

    def fetch_contratos(self, *, cif_proveedor, codigo_obra_normalizado):
        self.llamadas += 1
        if self.error is not None:
            raise self.error
        return [c for c in self.contratos if c.cif_proveedor == cif_proveedor]


def _enriquecer(repo, cliente, **kwargs) -> int:
    from application.services.contrato_enrichment_service import ContratoEnrichmentService

    servicio = ContratoEnrichmentService(client=cliente, repository=repo, **kwargs)
    return servicio.enrich_merge_document(merge_document_id=DOC, force_refetch=True)


# ------------------------------------------------------------------ #
# R2, R3, R6 · casos (a), (b), (c)
# ------------------------------------------------------------------ #
def test_f115_r2_r6_a_proveedor_b_sin_contratos_deja_la_seleccion_nula():
    repo = _RepoMem()
    assert _enriquecer(repo, _Cliente([])) == 0
    assert (repo.seleccion, repo.origen) == (None, None)
    assert repo.limpiezas == [DOC]
    assert repo.sellos == ["ninguno"]


def test_f115_r3_retira_solo_la_nota_de_auto_seleccion_de_ese_codigo(caplog):
    otra_auto = "[AVISO] Contrato CTZ/0009 elegido AUTOMATICAMENTE entre 3 candidatos."
    repo = _RepoMem(notas=f"{OTRA_NOTA}\n{NOTA_AUTO_A}\n{otra_auto}")
    with caplog.at_level(logging.INFO):
        _enriquecer(repo, _Cliente([]))
    assert repo.notas == f"{OTRA_NOTA}\n{otra_auto}"
    assert any(
        r.levelno == logging.INFO and DOC in r.getMessage() and "CTA/0001" in r.getMessage()
        for r in caplog.records
    )


def test_f115_r6_b_proveedor_b_con_dos_sin_eleccion_deja_nula():
    repo = _RepoMem()
    cliente = _Cliente([_contrato("CTB/0001"), _contrato("CTB/0002")])
    assert _enriquecer(repo, cliente) == 2
    assert (repo.seleccion, repo.origen) == (None, None)
    assert NOTA_AUTO_A not in (repo.notas or "")


def test_f115_r6_c_proveedor_b_con_uno_queda_el_de_b():
    repo = _RepoMem()
    assert _enriquecer(repo, _Cliente([_contrato("CTB/0001")])) == 1
    assert (repo.seleccion, repo.origen) == ("CTB/0001", "auto_unico")
    assert repo.limpiezas == [DOC]


def test_f115_r2_cambio_de_obra_mismo_proveedor_retira_el_de_la_obra_anterior():
    """R15/D2: se conserva el proveedor y cambia el contrato."""
    repo = _RepoMem(cif=CIF_A, obra="0700", filas=[(DOC, "CTA/0001", CIF_A, OBRA)])
    cliente = _Cliente([_contrato("CTA/0700", cif=CIF_A, obra="0700")])
    assert _enriquecer(repo, cliente) == 1
    assert repo.seleccion == "CTA/0700"
    assert repo.limpiezas == [DOC]


def test_f115_r2_cache_hit_tambien_retira_antes():
    class _CacheHit:
        def find_active_contrato(self, *, codigo_obra, cif_proveedor, fecha_albaran_yyyymmdd):
            return _contrato("CTB/CACHE")

    repo = _RepoMem()
    from application.services.contrato_enrichment_service import ContratoEnrichmentService

    servicio = ContratoEnrichmentService(client=_Cliente(error=AssertionError("no")), repository=repo,
                                         cache=_CacheHit())
    assert servicio.enrich_merge_document(merge_document_id=DOC) == 1
    assert repo.limpiezas == [DOC]
    assert repo.seleccion == "CTB/CACHE"


# ------------------------------------------------------------------ #
# R4 · también en sin_datos y en error · caso (d)
# ------------------------------------------------------------------ #
def test_f115_r4_d_sigrid_en_error_deja_nula():
    repo = _RepoMem()
    assert _enriquecer(repo, _Cliente(error=RuntimeError("sigrid-api HTTP 500"))) == 0
    assert repo.seleccion is None
    assert repo.sellos == ["error"]


@pytest.mark.parametrize(("cif", "obra"), [(None, OBRA), (CIF_B, None), ("  ", "X-RARA")])
def test_f115_r4_sin_datos_tambien_retira(cif, obra):
    repo = _RepoMem(cif=cif, obra=obra)
    assert _enriquecer(repo, _Cliente([_contrato("CTB/0001")])) == 0
    assert repo.seleccion is None
    assert repo.sellos == ["sin_datos"]


# ------------------------------------------------------------------ #
# Lo que NO se retira · casos (e), (f) y selección sin filas
# ------------------------------------------------------------------ #
def test_f115_r19_e_mismo_cif_con_otro_formato_no_retira():
    repo = _RepoMem(cif="b-22222222", obra="686", filas=[(DOC, "CTB/0001", CIF_B, OBRA)],
                    seleccion="CTB/0001", notas=None)
    cliente = _Cliente([_contrato("CTB/0001"), _contrato("CTB/0002")])
    # el cliente filtra por el CIF limpio que pide el servicio
    cliente.contratos = [_contrato("CTB/0001", cif="B-22222222"), _contrato("CTB/0002", cif="B-22222222")]
    _enriquecer(repo, cliente)
    assert repo.limpiezas == []
    assert repo.seleccion == "CTB/0001"


def test_f115_r2_f_fila_legada_sin_cif_no_retira():
    repo = _RepoMem(filas=[(DOC, "CTA/0001", None, OBRA)])
    _enriquecer(repo, _Cliente([]))
    assert repo.limpiezas == []
    assert repo.seleccion == "CTA/0001"


def test_f115_r2_sin_ninguna_fila_de_ese_codigo_no_se_sabe_y_no_retira():
    repo = _RepoMem(filas=[])
    _enriquecer(repo, _Cliente([]))
    assert repo.limpiezas == []
    assert repo.seleccion == "CTA/0001"


def test_f115_r2_sin_filas_en_el_documento_mira_las_de_otro_documento():
    repo = _RepoMem(filas=[("otro-doc", "CTA/0001", CIF_A, OBRA)])
    _enriquecer(repo, _Cliente([]))
    assert repo.limpiezas == [DOC]


def test_f115_r2_una_fila_del_albaran_basta_aunque_otra_sea_ajena():
    repo = _RepoMem(filas=[(DOC, "CTA/0001", CIF_A, OBRA), (DOC, "CTA/0001", CIF_B, OBRA)])
    _enriquecer(repo, _Cliente([]))
    assert repo.limpiezas == []


def test_f115_r2_sin_seleccion_no_limpia_nada():
    repo = _RepoMem(seleccion=None)
    _enriquecer(repo, _Cliente([]))
    assert repo.limpiezas == []


def test_f115_r2_enriquecimiento_apagado_no_toca_nada():
    repo = _RepoMem()
    from application.services.contrato_enrichment_service import ContratoEnrichmentService

    servicio = ContratoEnrichmentService(client=_Cliente([]), repository=repo, enabled=False)
    assert servicio.enrich_merge_document(merge_document_id=DOC) == 0
    assert repo.limpiezas == []
    assert repo.seleccion == "CTA/0001"


# ------------------------------------------------------------------ #
# R5 · best-effort
# ------------------------------------------------------------------ #
def test_f115_r5_fallo_al_leer_la_pertenencia_se_registra_y_sigue(caplog):
    repo = _RepoMem(falla_pertenencia=True)
    with caplog.at_level(logging.ERROR):
        assert _enriquecer(repo, _Cliente([_contrato("CTB/0001")])) == 1
    assert repo.seleccion == "CTB/0001"
    assert any(r.levelno >= logging.ERROR and DOC in r.getMessage() for r in caplog.records)


def test_f115_r5_fallo_al_limpiar_se_registra_y_sigue(caplog):
    class _RepoRoto(_RepoMem):
        def clear_selected_contrato(self, *, document_id):
            raise RuntimeError("BBDD caída limpiando")

    repo = _RepoRoto()
    with caplog.at_level(logging.ERROR):
        assert _enriquecer(repo, _Cliente([])) == 0
    assert repo.sellos == ["ninguno"]
    assert any(r.levelno >= logging.ERROR for r in caplog.records)


# ------------------------------------------------------------------ #
# Repositorio real: SQL de los dos métodos nuevos sobre SQLite
# ------------------------------------------------------------------ #
class _Fabrica:
    generation = 1

    def __init__(self, engine):
        self.engine = engine

    def ensure_database_and_engine(self):
        return None

    def create_session(self):
        return Session(self.engine)


@pytest.fixture()
def repo_sqlite(tmp_path):
    from infrastructure.database.sqlalchemy_albaran_repository import SqlAlchemyAlbaranRepository

    engine = create_engine(f"sqlite:///{tmp_path / 'f115.db'}")
    with engine.begin() as con:
        con.execute(text(
            "CREATE TABLE albaran_documents_merge (id TEXT PRIMARY KEY, "
            "selected_contrato_codigo TEXT, selected_contrato_origen TEXT, review_notes TEXT)"
        ))
        con.execute(text(
            "CREATE TABLE albaran_contratos_merge (id INTEGER PRIMARY KEY, document_id TEXT, "
            "codigo_contrato TEXT, cif_proveedor TEXT, codigo_obra TEXT)"
        ))
        con.execute(text(
            "INSERT INTO albaran_documents_merge VALUES "
            "(:d, 'CTA/0001', 'auto_multiple', 'n'), ('d2', 'CTX/0001', 'manual', NULL), "
            "('d3', NULL, NULL, NULL), ('d4', 'CTZ/0404', 'manual', NULL)"
        ), {"d": DOC})
        con.execute(text(
            "INSERT INTO albaran_contratos_merge (document_id, codigo_contrato, cif_proveedor, codigo_obra) "
            "VALUES (:d, 'CTA/0001', 'A11111111', '0686'), (:d, 'CTB/0001', 'B22222222', '0686'), "
            "('otro', 'CTX/0001', 'X1', '0700'), ('otro2', 'CTX/0001', NULL, '0700'), "
            "('otro', 'CTA/0001', 'NO-DEBE-SALIR', '0000')"
        ), {"d": DOC})
    repo = SqlAlchemyAlbaranRepository(_Fabrica(engine))
    repo._initialized_generation = 1
    return repo, engine


def test_f115_r2_repo_pertenencia_lee_las_filas_del_documento(repo_sqlite):
    repo, _ = repo_sqlite
    assert repo.get_pertenencia_seleccion(document_id=DOC) == ("CTA/0001", [("A11111111", "0686")])


def test_f115_r2_repo_pertenencia_sin_filas_propias_lee_las_de_otros_documentos(repo_sqlite):
    repo, _ = repo_sqlite
    codigo, filas = repo.get_pertenencia_seleccion(document_id="d2")
    assert codigo == "CTX/0001"
    assert sorted(filas, key=str) == sorted([("X1", "0700"), (None, "0700")], key=str)


def test_f115_r2_repo_pertenencia_sin_seleccion_o_sin_documento(repo_sqlite):
    repo, _ = repo_sqlite
    assert repo.get_pertenencia_seleccion(document_id="d3") == (None, [])
    assert repo.get_pertenencia_seleccion(document_id="no-existe") == (None, [])
    assert repo.get_pertenencia_seleccion(document_id="d4") == ("CTZ/0404", [])


def test_f115_r2_repo_clear_pone_a_nulo_codigo_y_origen_solo_de_ese_documento(repo_sqlite):
    repo, engine = repo_sqlite
    repo.clear_selected_contrato(document_id=DOC)
    with engine.connect() as con:
        filas = dict(
            (r[0], (r[1], r[2], r[3]))
            for r in con.execute(text(
                "SELECT id, selected_contrato_codigo, selected_contrato_origen, review_notes "
                "FROM albaran_documents_merge"
            ))
        )
    assert filas[DOC] == (None, None, "n")
    assert filas["d2"] == ("CTX/0001", "manual", None)


def test_f115_r2_el_puerto_declara_los_dos_metodos():
    import inspect

    from domain.ports.contrato_merge_repository_port import ContratoMergeRepository

    for nombre in ("get_pertenencia_seleccion", "clear_selected_contrato"):
        firma = inspect.signature(getattr(ContratoMergeRepository, nombre))
        assert list(firma.parameters)[1:] == ["document_id"]
        assert firma.parameters["document_id"].kind is inspect.Parameter.KEYWORD_ONLY


# ------------------------------------------------------------------ #
# R8 · el re-enriquecimiento no toca líneas, ni blobs, ni IA
# ------------------------------------------------------------------ #
def test_f115_r8_reenrich_no_toca_lineas_ni_blobs_ni_extraccion():
    from application.pipelines.persist_albaran_pipeline import PersistAlbaranPipeline
    from application.services.contrato_enrichment_service import ContratoEnrichmentService

    usados: set[str] = set()

    class _RepoVigilado(_RepoMem):
        def __getattribute__(self, nombre):
            if not nombre.startswith("_") and nombre not in ("filas", "cif", "obra", "seleccion",
                                                             "origen", "notas", "limpiezas", "sellos",
                                                             "falla_pertenencia"):
                usados.add(nombre)
            return object.__getattribute__(self, nombre)

        def has_selected_contrato_with_lines(self, *, document_id):
            return False, self.seleccion

        def importes_leidos(self, *, document_id):
            return [10.0]

    class _Prohibido:
        def __getattr__(self, nombre):
            raise AssertionError(f"no debe usarse: {nombre}")

    class _Trigger:
        def __init__(self):
            self.llamadas = []

        def trigger_async(self, *, document_id, codigo_contrato, force=False):
            self.llamadas.append((codigo_contrato, force))
            return True

    repo = _RepoVigilado()
    servicio = ContratoEnrichmentService(client=_Cliente([]), repository=repo)
    trigger = _Trigger()
    pipeline = PersistAlbaranPipeline(
        repository=repo, document_storage=_Prohibido(), normalizer=_Prohibido(),
        contrato_enrichment_service=servicio, valuation_trigger=trigger,
    )
    assert pipeline.reenrich_by_merge_id(merge_document_id=DOC, force_refetch=True) is True
    assert not any("line" in n and n not in ("get_merge_lines_for_scoring", "has_selected_contrato_with_lines")
                   for n in usados), usados
    assert "clear_selected_contrato" in usados
    assert trigger.llamadas == [(None, True)]


def test_f115_r5_repositorio_anterior_sin_el_metodo_es_no_op_sin_errores(caplog):
    """Mocks y repositorios anteriores a F-115: ni excepción ni ERROR."""
    class _RepoViejo(_RepoMem):
        get_pertenencia_seleccion = None  # type: ignore[assignment]

    repo = _RepoViejo()
    with caplog.at_level(logging.ERROR):
        assert _enriquecer(repo, _Cliente([])) == 0
    assert repo.seleccion == "CTA/0001"
    assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
