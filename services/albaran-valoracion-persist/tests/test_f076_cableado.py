# tests/test_f076_cableado.py
"""F-076 T11 · los dos puntos de entrada de sv6 cablean el normalizador.

``interface_adapters/composition.py`` (worker de la cola) y
``interface_adapters/api/app.py`` (HTTP) construyen el pipeline con el mismo
``NormalizadorPartidas``: lector de sigrid-api y caché por proceso SOLO si hay
URL, clave y base de datos; si no, puerto ``None`` y WARNING al arrancar
(R11, R17). Interruptor apagado ⇒ ni lector ni caché (R12). Sin BBDD: la
fábrica de sesiones y el repositorio se sustituyen por dobles.
"""
from __future__ import annotations

import logging

import pytest
from application.services.normalizador_partidas import NormalizadorPartidas
from infrastructure.sigrid.sigrid_api_lector import SigridApiLector
from ruesma_comun.sigrid import CachePartidasObra

_CLAVE = "clave-de-test-cableado"


def _ajustes(monkeypatch, **entorno):
    from config.settings import Settings

    for nombre in ("SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE",
                   "PARTIDAS_OBRA_NORMALIZAR_ENABLED", "PARTIDAS_OBRA_TTL_S", "PARTIDAS_OBRA_MAX_OBRAS",
                   "PARTIDAS_OBRA_FALLO_TTL_S", "SIGRID_API_TIMEOUT_S", "ALM_CODIGO_PARTIDA"):
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)
    return Settings(_env_file=None, PG_USER="u", PG_PASSWORD="p", SCHEMA_DRIFT_CHECK_ENABLED="false")


_CONFIGURADO = {"SIGRID_API_BASE_URL": "https://sigrid.invalid", "SIGRID_API_FUNCTION_KEY": _CLAVE,
                "SIGRID_API_DATABASE": "db-test"}


def test_f076_t11_configurado_lector_y_cache(monkeypatch):
    from interface_adapters.composition import construir_normalizador_partidas

    ajustes = _ajustes(monkeypatch, **_CONFIGURADO, PARTIDAS_OBRA_TTL_S="60", PARTIDAS_OBRA_MAX_OBRAS="8",
                       PARTIDAS_OBRA_FALLO_TTL_S="5", SIGRID_API_TIMEOUT_S="20", ALM_CODIGO_PARTIDA="ACOPIO")
    normalizador = construir_normalizador_partidas(ajustes)
    assert isinstance(normalizador, NormalizadorPartidas)
    assert normalizador._activo is True
    assert normalizador._alm == "ACOPIO"
    cache = normalizador._partidas
    assert isinstance(cache, CachePartidasObra)
    assert (cache._ttl_s, cache._max_obras, cache._ttl_fallo_s) == (60, 8, 5)
    lector = cache._lector
    assert isinstance(lector, SigridApiLector)
    assert (lector._base_url, lector._database, lector._timeout_s) == ("https://sigrid.invalid", "db-test", 20.0)


@pytest.mark.parametrize("faltante", ["SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE"])
def test_f076_t11_sin_configuracion_puerto_none_y_warning(monkeypatch, caplog, faltante):
    from interface_adapters.composition import construir_normalizador_partidas

    entorno = dict(_CONFIGURADO)
    del entorno[faltante]
    with caplog.at_level(logging.WARNING, logger="interface_adapters.composition"):
        normalizador = construir_normalizador_partidas(_ajustes(monkeypatch, **entorno))
    assert normalizador._partidas is None and normalizador._activo is True
    avisos = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert any("partidas_obra_no_disponibles" in a for a in avisos)
    assert all(_CLAVE not in a for a in avisos)


def test_f076_t11_apagado_sin_lector(monkeypatch, caplog):
    from interface_adapters.composition import construir_normalizador_partidas

    with caplog.at_level(logging.WARNING):
        normalizador = construir_normalizador_partidas(
            _ajustes(monkeypatch, **_CONFIGURADO, PARTIDAS_OBRA_NORMALIZAR_ENABLED="false"))
    assert normalizador._activo is False and normalizador._partidas is None
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


class _RepoFalso:
    is_initialized = True

    def __init__(self, *_args, **_kwargs):
        pass

    def initialize(self):
        return None


@pytest.fixture
def sin_bbdd(monkeypatch):
    import importlib.util

    from interface_adapters import composition

    modulos = [composition]
    if importlib.util.find_spec("fastapi") is not None:
        from interface_adapters.api import app as modulo_app

        modulos.append(modulo_app)
    for modulo in modulos:
        monkeypatch.setattr(modulo, "SessionFactory", lambda **_: object())
        monkeypatch.setattr(modulo, "SqlAlchemyValuationRepository", _RepoFalso)


def test_f076_t11_el_worker_cablea_el_normalizador(monkeypatch, sin_bbdd):
    from interface_adapters.composition import build_run_valuation_pipeline

    pipeline = build_run_valuation_pipeline(_ajustes(monkeypatch, **_CONFIGURADO))
    assert isinstance(pipeline._normalizador, NormalizadorPartidas)
    assert isinstance(pipeline._normalizador._partidas, CachePartidasObra)


def test_f076_t11_la_api_cablea_el_normalizador_fuente():
    """Siempre corre (el intérprete del arnés no trae FastAPI): ``build_app``
    pasa al pipeline el normalizador de ``composition``, el mismo del worker."""
    import ast
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1] / "interface_adapters" / "api" / "app.py").read_text(
        encoding="utf-8")
    arbol = ast.parse(fuente)
    llamadas = [n for n in ast.walk(arbol) if isinstance(n, ast.Call) and getattr(n.func, "id", "") ==
                "RunValuationPipeline"]
    assert len(llamadas) == 1
    (kw,) = [k for k in llamadas[0].keywords if k.arg == "normalizador"]
    assert ast.unparse(kw.value) == "construir_normalizador_partidas(settings)"
    assert "from interface_adapters.composition import construir_normalizador_partidas" in fuente


def test_f076_t11_la_api_cablea_el_normalizador(monkeypatch, sin_bbdd):
    pytest.importorskip("fastapi")
    from interface_adapters.api import app as modulo_app

    capturado = {}
    original = modulo_app.RunValuationPipeline

    def _espia(**kwargs):
        capturado.update(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(modulo_app, "RunValuationPipeline", _espia)
    modulo_app.build_app(_ajustes(monkeypatch))
    normalizador = capturado["normalizador"]
    assert isinstance(normalizador, NormalizadorPartidas)
    assert normalizador._partidas is None  # sin SIGRID_API_*: valora como siempre
