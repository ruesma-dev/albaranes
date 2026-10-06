# tests/test_f054_cableado.py
"""R27 (F-054, T8): ``main.py`` construye el extractor y lo inyecta.

``main.main()`` se ejecuta con ``Settings``, Graph, el engine, el almacen,
el publicador y ``PollingPipeline`` sustituidos por dobles: no se toca red,
buzon, BBDD ni Azure. Y el pipeline no instancia ni importa la
implementacion del extractor: solo conoce su puerto.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from infrastructure.document.mime_documento_extractor import (
    NIVEL_MAXIMO_ANIDAMIENTO,
    MimeDocumentoExtractor,
)

RAIZ_SV1 = Path(__file__).resolve().parents[1]


class _PipelineEspia:
    construido: dict | None = None
    arrancado_con: object | None = None

    def __init__(self, **kwargs: object) -> None:
        type(self).construido = kwargs

    def run_forever(self, settings: object) -> None:
        type(self).arrancado_con = settings


@pytest.fixture
def modulo_main(monkeypatch):
    modulo = importlib.import_module("main")
    settings = SimpleNamespace(
        log_dir="logs-de-prueba",
        log_level="INFO",
        mailbox_address="buzon@ejemplo.test",
        poll_interval_s=60,
        source_folder="inbox",
        graph_key="clave-inventada",
        graph_timeout_s=5,
        database_url="postgresql://ejemplo.test/inventada",
        correo_max_caracteres=1234,
    )
    nulo = lambda *a, **k: SimpleNamespace()
    monkeypatch.setattr(modulo, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(modulo, "Settings", lambda: settings)
    monkeypatch.setattr(modulo, "configure_logging", lambda *a, **k: None)
    monkeypatch.setattr(modulo, "GraphTokenProvider", nulo)
    monkeypatch.setattr(modulo, "GraphMailClient", nulo)
    monkeypatch.setattr(modulo, "create_engine", nulo)
    monkeypatch.setattr(modulo, "crear_tablas", lambda *a, **k: None)
    monkeypatch.setattr(modulo, "SessionFactoryDesdeEngine", nulo)
    monkeypatch.setattr(modulo, "RepositorioWorkflows", nulo)
    monkeypatch.setattr(modulo, "construir_almacen_desde_entorno", nulo)
    monkeypatch.setattr(modulo, "construir_publicador", nulo)
    monkeypatch.setattr(modulo, "IntakeColaClient", nulo)
    monkeypatch.setattr(modulo, "PollingPipeline", _PipelineEspia)
    _PipelineEspia.construido = None
    _PipelineEspia.arrancado_con = None
    return modulo, settings


def test_f054_r27_main_inyecta_el_extractor_mime_en_el_pipeline(modulo_main):
    modulo, settings = modulo_main

    assert modulo.main() == 0

    kwargs = _PipelineEspia.construido
    assert kwargs is not None
    assert isinstance(kwargs["extractor_correo"], MimeDocumentoExtractor)
    assert kwargs["extractor_correo"].nivel_maximo == NIVEL_MAXIMO_ANIDAMIENTO == 5
    assert kwargs["correo_max_caracteres"] == 1234
    assert _PipelineEspia.arrancado_con is settings


def test_f054_r27_el_extractor_es_obligatorio_en_el_pipeline():
    from application.pipelines.polling_pipeline import PollingPipeline

    with pytest.raises(TypeError, match="extractor_correo"):
        PollingPipeline(mailbox=None, orchestrator=None, pdf_splitter=None)


def test_f054_r27_el_pipeline_no_importa_ni_instancia_el_extractor_mime():
    fuente = (RAIZ_SV1 / "application" / "pipelines" / "polling_pipeline.py").read_text(encoding="utf-8")
    modulos = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.ImportFrom):
            modulos.add(nodo.module or "")
        elif isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)

    assert not any(m.startswith("infrastructure.document.mime_") for m in modulos)
    assert "domain.ports.extractor_correo_adjunto" in modulos
    assert "MimeDocumentoExtractor" not in fuente
