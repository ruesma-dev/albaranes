# tests/test_f111_pipeline.py
"""F-111 T10 · el pipeline asigna la partida de residuos antes de valorar.

- R20: tras ``_normalizar_partidas`` (F-076) y antes de la valoración directa,
  de IA4 y del build; ``anotar`` en las dos ramas que persisten.
- R27: cualquier excepción ⇒ el sobre tal cual y las líneas buscadas a revisión
  con ``partida_residuos_sin_lista``; la valoración no falla.
- R29: ``PARTIDA_RESIDUOS_ENABLED=false`` (o sin asignador) ⇒ como antes.
- R30: la obra se lee UNA vez por valoración, también con F-076 leyéndola.

Builder real con F-051 encendido, sv5, IA4, repositorio y puerto falsos.
"""
from __future__ import annotations

import logging

import pytest

from application.pipelines.run_valuation_pipeline import (
    RunValuationPipeline,
    RunValuationRequest,
)
from application.services.normalizador_partidas import NormalizadorPartidas
from application.services.partida_matcher import PartidaMatcher
from application.services.partida_residuos import (
    MOTIVO_SIN_CAPITULO,
    MOTIVO_SIN_LISTA,
    AsignadorPartidaResiduos,
)
from domain.ports.valuation_repository import PersistedValuation
from ruesma_comun.sigrid import ListaPartidasObra
from tests.f027_escenarios import construir_builder
from tests.f036_escenarios_residuos import EscenarioResiduos, LineaResiduos, construir_envelope

_COLUMNAS = ["ide", "padide", "cod", "res"]
FILAS_0686 = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (10, 1, "32", "GESTIÓN RESIDUOS (SEGÚN EGRC)"),
    (11, 10, "32.01", "GRD010 Gestión de residuos"),
    (30, 1, "05", "ESTRUCTURA"),
    (31, 30, "05.01", "HORMIGÓN"),
]
LISTA_0686 = ListaPartidasObra.desde_filas("0686", _COLUMNAS, FILAS_0686)
SIN_CAPITULO = ListaPartidasObra.desde_filas("0700", _COLUMNAS, FILAS_0686[3:])


class _Repo:
    def __init__(self, *, obra="0686", rompe_obra=False):
        self.obra = obra
        self.rompe_obra = rompe_obra
        self.guardados = []
        self.obras_pedidas = []

    def get_by_document_id(self, *, document_id):
        return None

    def obra_del_documento(self, *, document_id):
        self.obras_pedidas.append(document_id)
        if self.rompe_obra:
            raise RuntimeError("BBDD caída")
        return self.obra

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


class _Puerto:
    def __init__(self, lista=LISTA_0686, *, rompe=False):
        self._lista = lista
        self.rompe = rompe
        self.pedidas = []

    def lista(self, obra):
        self.pedidas.append(obra)
        if self.rompe:
            raise RuntimeError("caché rota")
        return self._lista


class _Ia4:
    def __init__(self):
        self.pendientes = None

    def conciliar(self, *, document_id, lineas_no_casadas, lineas_contrato):
        self.pendientes = lineas_no_casadas
        return {"conciliaciones": []}


def _envelope(*lineas, partidas=None, status="ok", contrato_con_partida=False):
    """(F-111 parte C) Por defecto el contrato va SIN partidas (paso 3, la parte B)."""
    env = construir_envelope(EscenarioResiduos(lineas=tuple(lineas) or (LineaResiduos(),)))
    for i, ctx in enumerate(env.context.lineas_albaran):
        ctx.codigo_partida_albaran = (partidas or {}).get(i)
    if not contrato_con_partida:
        # Copias: las líneas de contrato son objetos compartidos del módulo de escenarios.
        env.context.lineas_contrato = [
            c.model_copy(update={"codigo_partida": None}) for c in env.context.lineas_contrato
        ]
    env.status = status
    return env


def _pipeline(envelope, repo, *, puerto=None, activo=True, asignador=True, normalizador=False, ia4=None):
    builder = construir_builder()
    builder._partida_matcher = PartidaMatcher(alm_codigo_partida="ALM", almacen_sin_partida=True)
    puerto = puerto if puerto is not None else _Puerto()
    return RunValuationPipeline(
        ia_client=_Sv5(envelope), repository=repo, builder=builder, conciliacion_client=ia4,
        normalizador=(NormalizadorPartidas(partidas=puerto, alm_codigo_partida="ALM", activo=True)
                      if normalizador else None),
        asignador_residuos=(AsignadorPartidaResiduos(partidas=puerto, elector=None,
                                                     alm_codigo_partida="ALM", activo=activo)
                            if asignador else None),
    )


def _guardado(repo):
    ((cabecera, lineas),) = repo.guardados
    return cabecera, lineas


def _base(lineas, merge_line_id=700):
    return next(l for l in lineas if l.line_kind == "from_albaran" and l.merge_line_id == merge_line_id)


def test_f111_r20_la_linea_sin_partida_va_a_la_del_capitulo():
    repo, puerto = _Repo(), _Puerto()
    _pipeline(_envelope(), repo, puerto=puerto).run(RunValuationRequest(document_id="doc-1"))
    cabecera, lineas = _guardado(repo)
    base = _base(lineas)
    assert base.codigo_partida_final == "32.01"
    assert base.partida_action != "almacen_sin_partida"
    assert base.codigo_partida_albaran is None
    assert "partida_residuos:32.01" in base.review_reasons
    assert repo.obras_pedidas == ["doc-1"]
    assert puerto.pedidas == ["0686"]
    # El sobre persistido es el que se valoró (como F-076 R14).
    assert '"codigo_partida_albaran":"32.01"' in cabecera.raw_ia_envelope_json


def test_f111_r20_ia4_recibe_la_partida_asignada():
    ia4 = _Ia4()
    linea = LineaResiduos(matched_contrato_line_id=None, precio_contrato_db=None, match_method="no_match")
    _pipeline(_envelope(linea), _Repo(), ia4=ia4).run(RunValuationRequest(document_id="doc-1"))
    assert ia4.pendientes and ia4.pendientes[0]["codigo_partida"] == "32.01"


def test_f111_r30_la_obra_se_lee_una_vez_con_f076_tambien():
    repo, puerto = _Repo(), _Puerto()
    env = _envelope(LineaResiduos(merge_line_id=700), LineaResiduos(merge_line_id=701), partidas={1: "05.01"})
    _pipeline(env, repo, puerto=puerto, normalizador=True).run(RunValuationRequest(document_id="doc-1"))
    assert repo.obras_pedidas == ["doc-1"]
    _cab, lineas = _guardado(repo)
    assert _base(lineas, 700).codigo_partida_final == "32.01"
    assert _base(lineas, 701).codigo_partida_albaran == "05.01"


def test_f111_r30_sin_residuos_sin_partida_no_se_lee_la_obra():
    repo = _Repo()
    _pipeline(_envelope(partidas={0: "32.01"}), repo).run(RunValuationRequest(document_id="doc-1"))
    assert repo.obras_pedidas == []


def test_f111_r25_sin_capitulo_a_revision_y_no_a_almacen():
    repo = _Repo()
    _pipeline(_envelope(), repo, puerto=_Puerto(SIN_CAPITULO)).run(RunValuationRequest(document_id="doc-1"))
    cabecera, lineas = _guardado(repo)
    base = _base(lineas)
    assert base.partida_action != "almacen_sin_partida"
    assert base.codigo_partida_final is None
    assert MOTIVO_SIN_CAPITULO in base.review_reasons
    assert base.review_required is True and cabecera.review_required is True
    assert MOTIVO_SIN_CAPITULO in cabecera.review_reasons


def test_f111_r27_una_excepcion_no_rompe_la_valoracion(caplog):
    repo = _Repo()
    with caplog.at_level(logging.WARNING):
        resultado = _pipeline(_envelope(), repo, puerto=_Puerto(rompe=True)).run(
            RunValuationRequest(document_id="doc-1")
        )
    assert resultado.status == "ok"
    _cab, lineas = _guardado(repo)
    base = _base(lineas)
    assert MOTIVO_SIN_LISTA in base.review_reasons
    assert base.partida_action != "almacen_sin_partida"
    assert any("partida de residuos" in r.getMessage() for r in caplog.records)


def test_f111_r27_si_no_se_puede_leer_la_obra_sin_lista():
    repo = _Repo(rompe_obra=True)
    _pipeline(_envelope(), repo).run(RunValuationRequest(document_id="doc-1"))
    _cab, lineas = _guardado(repo)
    assert MOTIVO_SIN_LISTA in _base(lineas).review_reasons


def test_f111_r27_con_f076_la_obra_rota_degrada_las_dos():
    repo = _Repo(rompe_obra=True)
    env = _envelope(LineaResiduos(merge_line_id=700), LineaResiduos(merge_line_id=701), partidas={1: "05.01"})
    _pipeline(env, repo, normalizador=True).run(RunValuationRequest(document_id="doc-1"))
    cabecera, lineas = _guardado(repo)
    assert MOTIVO_SIN_LISTA in _base(lineas, 700).review_reasons
    assert "partidas_obra_no_disponibles" in cabecera.review_reasons
    assert repo.obras_pedidas == ["doc-1"]


@pytest.mark.parametrize("como", ["apagado", "sin_asignador"])
def test_f111_r29_apagado_valora_como_antes(como):
    repo = _Repo()
    pipeline = (_pipeline(_envelope(), repo, activo=False) if como == "apagado"
                else _pipeline(_envelope(), repo, asignador=False))
    pipeline.run(RunValuationRequest(document_id="doc-1"))
    _cab, lineas = _guardado(repo)
    assert _base(lineas).partida_action == "almacen_sin_partida"
    assert repo.obras_pedidas == []


def _directo():
    linea = LineaResiduos(matched_contrato_line_id=None, precio_contrato_db=None, match_method="no_match")
    env = _envelope(linea, status="no_contract")
    env.context.lineas_albaran[0].precio_neto_albaran = 139.0
    env.context.lineas_albaran[0].importe_albaran = 139.0
    return env


def test_f111_r20_valoracion_directa_con_la_partida_asignada():
    repo = _Repo()
    _pipeline(_directo(), repo).run(RunValuationRequest(document_id="doc-1"))
    _cab, lineas = _guardado(repo)
    base = _base(lineas)
    assert base.codigo_partida_final == "32.01"
    assert "partida_residuos:32.01" in base.review_reasons
    assert base.codigo_partida_albaran is None


def test_f111_r25_valoracion_directa_sin_capitulo_no_queda_en_almacen():
    repo = _Repo()
    _pipeline(_directo(), repo, puerto=_Puerto(SIN_CAPITULO)).run(RunValuationRequest(document_id="doc-1"))
    _cab, lineas = _guardado(repo)
    base = _base(lineas)
    assert base.partida_action == "no_action"
    assert base.codigo_partida_final is None
    assert MOTIVO_SIN_CAPITULO in base.review_reasons


def test_f111_t10_anotar_va_antes_de_persistir_en_las_dos_ramas():
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1] / "application" / "pipelines"
              / "run_valuation_pipeline.py").read_text(encoding="utf-8")
    assert fuente.count("AsignadorPartidaResiduos.anotar(") == 2
    i_completar = fuente.index("lines = completar_registros(")
    i_anotar = fuente.index("AsignadorPartidaResiduos.anotar(header")
    i_replace = fuente.index("replace_valuation(\n            header=header_with_envelope")
    assert i_completar < i_anotar < i_replace


# ------------------------------------------------------------------ #
# T10 · cableado: PARTIDA_RESIDUOS_ENABLED y la caché compartida (R29, R30)
# ------------------------------------------------------------------ #
_CLAVE = "clave-de-test-f111"
_CONFIGURADO = {"SIGRID_API_BASE_URL": "https://sigrid.invalid", "SIGRID_API_FUNCTION_KEY": _CLAVE,
                "SIGRID_API_DATABASE": "db-test"}


def _ajustes(monkeypatch, **entorno):
    from config.settings import Settings

    for nombre in ("SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE",
                   "PARTIDAS_OBRA_NORMALIZAR_ENABLED", "PARTIDA_RESIDUOS_ENABLED",
                   "VALUATION_API_BASE_URL"):
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)
    return Settings(_env_file=None, PG_USER="u", PG_PASSWORD="p", SCHEMA_DRIFT_CHECK_ENABLED="false")


def test_f111_r29_partida_residuos_encendida_por_defecto(monkeypatch):
    assert _ajustes(monkeypatch).partida_residuos_enabled is True
    assert _ajustes(monkeypatch, PARTIDA_RESIDUOS_ENABLED="false").partida_residuos_enabled is False


def test_f111_r30_el_asignador_comparte_la_cache_de_f076(monkeypatch):
    from infrastructure.clients.http_partida_residuos_client import HttpPartidaResiduosClient
    from interface_adapters.composition import (
        construir_asignador_partida_residuos,
        construir_normalizador_partidas,
    )
    from ruesma_comun.sigrid import CachePartidasObra

    ajustes = _ajustes(monkeypatch, VALUATION_API_BASE_URL="http://sv5:8002", **_CONFIGURADO)
    asignador = construir_asignador_partida_residuos(ajustes)
    normalizador = construir_normalizador_partidas(ajustes)
    assert asignador._activo is True
    assert isinstance(asignador._partidas, CachePartidasObra)
    assert asignador._partidas is normalizador._partidas
    assert isinstance(asignador._elector, HttpPartidaResiduosClient)
    assert asignador._elector._url == "http://sv5:8002/v1/albaranes/partida-residuos"


def test_f111_r30_con_f076_apagado_el_asignador_tiene_su_cache(monkeypatch):
    from interface_adapters.composition import construir_asignador_partida_residuos
    from ruesma_comun.sigrid import CachePartidasObra

    ajustes = _ajustes(monkeypatch, PARTIDAS_OBRA_NORMALIZAR_ENABLED="false", **_CONFIGURADO)
    assert isinstance(construir_asignador_partida_residuos(ajustes)._partidas, CachePartidasObra)


def test_f111_r27_sin_sigrid_api_puerto_none_y_aviso(monkeypatch, caplog):
    from interface_adapters.composition import construir_asignador_partida_residuos

    with caplog.at_level(logging.WARNING, logger="interface_adapters.composition"):
        asignador = construir_asignador_partida_residuos(_ajustes(monkeypatch))
    assert asignador._partidas is None and asignador._activo is True
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert any(MOTIVO_SIN_LISTA in a for a in avisos)


def test_f111_r29_apagado_sin_puerto_ni_cliente(monkeypatch, caplog):
    from interface_adapters.composition import construir_asignador_partida_residuos

    with caplog.at_level(logging.WARNING):
        asignador = construir_asignador_partida_residuos(
            _ajustes(monkeypatch, PARTIDA_RESIDUOS_ENABLED="false", **_CONFIGURADO)
        )
    assert asignador._activo is False
    assert asignador._partidas is None and asignador._elector is None
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


def test_f111_t10_el_worker_y_la_api_cablean_el_asignador(monkeypatch):
    import ast
    from pathlib import Path

    from interface_adapters import composition

    class _Repo:
        is_initialized = True

        def __init__(self, *_a, **_k):
            pass

        def initialize(self):
            return None

    monkeypatch.setattr(composition, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(composition, "SqlAlchemyValuationRepository", _Repo)
    pipeline = composition.build_run_valuation_pipeline(_ajustes(monkeypatch, **_CONFIGURADO))
    assert isinstance(pipeline._asignador_residuos, AsignadorPartidaResiduos)
    assert pipeline._asignador_residuos._partidas is pipeline._normalizador._partidas

    fuente = (Path(__file__).resolve().parents[1] / "interface_adapters" / "api" / "app.py").read_text(
        encoding="utf-8")
    (llamada,) = [n for n in ast.walk(ast.parse(fuente)) if isinstance(n, ast.Call)
                  and getattr(n.func, "id", "") == "RunValuationPipeline"]
    (kw,) = [k for k in llamada.keywords if k.arg == "asignador_residuos"]
    assert ast.unparse(kw.value) == "construir_asignador_partida_residuos(settings)"


def test_f111_r38_el_pipeline_toma_la_partida_del_contrato():
    """(F-111 parte C) El contrato trae 32.01, del capítulo de residuos: paso 1."""
    repo, puerto = _Repo(), _Puerto()
    _pipeline(_envelope(contrato_con_partida=True), repo, puerto=puerto).run(
        RunValuationRequest(document_id="doc-1")
    )
    _cab, lineas = _guardado(repo)
    base = _base(lineas)
    assert base.codigo_partida_final == "32.01"
    assert "partida_residuos_contrato:32.01" in base.review_reasons
    assert base.codigo_partida_albaran is None
    assert puerto.pedidas == ["0686"]
