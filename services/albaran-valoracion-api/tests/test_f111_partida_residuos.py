# tests/test_f111_partida_residuos.py
"""F-111 R31–R33 · IA elige la partida de residuos entre las candidatas.

``POST /v1/albaranes/partida-residuos``: sv6 manda las líneas de residuos sin
partida de un documento y las hojas candidatas del capítulo de gestión de
residuos de la obra; la IA (el proveedor y modelo de IA4) elige POR SIGNIFICADO
una de ellas o ``null``. La respuesta solo vale si el código es de una
candidata. Proveedor falso: sin red ni LLM.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from pydantic import BaseModel

try:
    import fastapi  # noqa: F401
except ModuleNotFoundError:  # el .venv de la raíz no trae FastAPI (ver F-085)
    _fa = types.ModuleType("fastapi")

    class _FastAPI:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def get(self, ruta):
            return lambda funcion: funcion

        def post(self, ruta):
            return lambda funcion: funcion

    class _HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = "") -> None:
            super().__init__(detail)
            self.status_code = status_code

    _fa.FastAPI = _FastAPI
    _fa.HTTPException = _HTTPException
    sys.modules["fastapi"] = _fa

from application.services.partida_residuos_service import (  # noqa: E402
    PartidaResiduosService,
    SinProveedorIA,
)
from application.services.schema_registry import SchemaRegistry  # noqa: E402
from application.services.valuation_extraction_service import ProviderClientSpec  # noqa: E402
from domain.models.partida_residuos_models import (  # noqa: E402
    DocumentoPartidaResiduos,
    EleccionPartida,
    PartidaResiduosRequest,
)
from infrastructure.prompts.yaml_prompt_repository import YamlPromptRepository  # noqa: E402
from interface_adapters.api import app as modulo  # noqa: E402

PROMPTS_YAML = Path(__file__).resolve().parents[1] / "config" / "prompts.yaml"

CANDIDATAS = [
    {"codigo": "32.01", "descripcion": "GRD010 Gestión de residuos",
     "descripcion_agregada": "COSTES DIRECTOS › GESTIÓN RESIDUOS › GRD010 Gestión de residuos"},
    {"codigo": "37.06.01", "descripcion": "OPERARIO EXCLUSIVO PARA CLASIFICACIÓN",
     "descripcion_agregada": "COSTES DIRECTOS › SEGURIDAD › GESTIÓN DE RESIDUOS › OPERARIO"},
]
LINEAS = [
    {"line_ref": 10, "descripcion": "CONTENEDOR MADERA 8 M3", "codigo_ler": "170201"},
    {"line_ref": 11, "descripcion": "CONTENEDOR MEZCLA", "codigo_ler": "170904"},
]


class _Cliente:
    """Proveedor falso: devuelve lo que se le diga y apunta la llamada."""

    def __init__(self, respuesta=None, error: Exception | None = None) -> None:
        self.respuesta = respuesta
        self.error = error
        self.llamadas: list[dict] = []

    def extract_document(self, *, model, instructions, user_text, attachment, response_model):
        self.llamadas.append(
            {"model": model, "instructions": instructions, "user_text": user_text,
             "attachment": attachment, "response_model": response_model}
        )
        if self.error is not None:
            raise self.error
        return self.respuesta


def _servicio(cliente: _Cliente | None, *, proveedores=None) -> PartidaResiduosService:
    if proveedores is None:
        proveedores = [ProviderClientSpec(provider="openai", model_name="gpt-x", client=cliente)]
    return PartidaResiduosService(
        providers=proveedores,
        prompt_repo=YamlPromptRepository(PROMPTS_YAML),
        schema_registry=SchemaRegistry(),
    )


def _doc(*elecciones) -> DocumentoPartidaResiduos:
    return DocumentoPartidaResiduos(
        elecciones=[EleccionPartida(**e) for e in elecciones]
    )


# ------------------------------------------------------------------ #
# R31 · contrato de entrada y salida, una elección por línea
# ------------------------------------------------------------------ #
def test_f111_r31_una_eleccion_por_linea_en_el_orden_de_entrada():
    cliente = _Cliente(_doc(
        {"line_ref": 11, "codigo": "32.01", "confianza_pct": 80, "razon_corta": "mezcla"},
        {"line_ref": 10, "codigo": "32.01", "confianza_pct": 90, "razon_corta": "madera"},
    ))
    res = _servicio(cliente).elegir(lineas=LINEAS, candidatas=CANDIDATAS)
    assert [e.line_ref for e in res.elecciones] == [10, 11]
    assert [e.codigo for e in res.elecciones] == ["32.01", "32.01"]
    assert res.elecciones[0].confianza_pct == 90
    assert res.elecciones[0].razon_corta == "madera"
    assert len(cliente.llamadas) == 1  # una llamada por documento (R34)


def test_f111_r31_la_peticion_del_endpoint():
    body = PartidaResiduosRequest(document_id="d1", lineas=LINEAS, candidatas=CANDIDATAS)
    assert body.lineas[0].line_ref == 10
    assert body.lineas[0].codigo_ler == "170201"
    assert body.candidatas[1].codigo == "37.06.01"
    vacia = PartidaResiduosRequest(document_id="d2")
    assert vacia.lineas == [] and vacia.candidatas == []


def test_f111_r31_el_esquema_esta_registrado():
    assert SchemaRegistry().get("documento_partida_residuos") is DocumentoPartidaResiduos


def test_f111_r31_el_texto_lleva_lineas_y_candidatas():
    cliente = _Cliente(_doc())
    _servicio(cliente).elegir(lineas=LINEAS, candidatas=CANDIDATAS)
    llamada = cliente.llamadas[0]
    assert llamada["model"] == "gpt-x"
    assert llamada["attachment"] is None
    assert llamada["response_model"] is DocumentoPartidaResiduos
    assert "37.06.01" in llamada["user_text"]
    assert "CONTENEDOR MADERA 8 M3" in llamada["user_text"]
    assert "170201" in llamada["user_text"]
    assert "ELIGE POR SIGNIFICADO" in llamada["instructions"].upper()


# ------------------------------------------------------------------ #
# R32 · solo entre las candidatas; nunca inventa
# ------------------------------------------------------------------ #
def test_f111_r32_un_codigo_que_no_es_candidata_vale_null():
    cliente = _Cliente(_doc(
        {"line_ref": 10, "codigo": "99.99", "confianza_pct": 95, "razon_corta": "inventada"},
        {"line_ref": 11, "codigo": " 37.06.01 ", "confianza_pct": 70, "razon_corta": "x"},
    ))
    res = _servicio(cliente).elegir(lineas=LINEAS, candidatas=CANDIDATAS)
    assert res.elecciones[0].codigo is None
    assert res.elecciones[0].confianza_pct == 0
    assert "99.99" in res.elecciones[0].razon_corta
    assert res.elecciones[1].codigo == "37.06.01"


def test_f111_r32_null_de_la_ia_se_respeta():
    cliente = _Cliente(_doc(
        {"line_ref": 10, "codigo": None, "confianza_pct": 30, "razon_corta": "dos iguales"},
    ))
    res = _servicio(cliente).elegir(lineas=LINEAS[:1], candidatas=CANDIDATAS)
    assert res.elecciones[0].codigo is None
    assert res.elecciones[0].razon_corta == "dos iguales"


def test_f111_r32_linea_sin_respuesta_o_ajena():
    cliente = _Cliente(_doc(
        {"line_ref": 99, "codigo": "32.01", "confianza_pct": 90, "razon_corta": "otra"},
    ))
    res = _servicio(cliente).elegir(lineas=LINEAS, candidatas=CANDIDATAS)
    assert [e.line_ref for e in res.elecciones] == [10, 11]
    assert all(e.codigo is None for e in res.elecciones)
    assert all(e.razon_corta == "sin_respuesta_de_la_ia" for e in res.elecciones)


def test_f111_r32_respuesta_como_otro_modelo_se_valida():
    class _Otro(BaseModel):
        elecciones: list[dict]

    cliente = _Cliente(_Otro(elecciones=[
        {"line_ref": 10, "codigo": "32.01", "confianza_pct": 50, "razon_corta": "ok"},
    ]))
    res = _servicio(cliente).elegir(lineas=LINEAS[:1], candidatas=CANDIDATAS)
    assert res.elecciones[0].codigo == "32.01"


def test_f111_r32_el_prompt_dice_que_elige_por_significado_y_no_inventa():
    spec = YamlPromptRepository(PROMPTS_YAML).get("partida_residuos_es")
    texto = " ".join(f"{spec.system} {spec.task} {spec.schema_hint}".split()).lower()
    assert spec.schema == "documento_partida_residuos"
    assert "por significado" in texto
    assert "solo entre las candidatas" in texto
    assert "codigo = null si ninguna encaja" in texto
    assert "si dos encajan igual" in texto
    assert "nunca inventes codigos" in texto


def test_f111_r32_sin_lineas_no_llama_a_la_ia():
    cliente = _Cliente(_doc())
    res = _servicio(cliente).elegir(lineas=[], candidatas=CANDIDATAS)
    assert res.elecciones == []
    assert cliente.llamadas == []


# ------------------------------------------------------------------ #
# R33 · proveedor de IA4; sin proveedor, 503
# ------------------------------------------------------------------ #
def test_f111_r33_usa_el_primer_proveedor_de_ia4():
    primero, segundo = _Cliente(_doc()), _Cliente(_doc())
    proveedores = [
        ProviderClientSpec(provider="openai", model_name="m1", client=primero),
        ProviderClientSpec(provider="claude", model_name="m2", client=segundo),
    ]
    _servicio(None, proveedores=proveedores).elegir(lineas=LINEAS, candidatas=CANDIDATAS)
    assert len(primero.llamadas) == 1 and segundo.llamadas == []


def test_f111_r33_sin_proveedor_lanza_sin_proveedor():
    with pytest.raises(SinProveedorIA):
        _servicio(None, proveedores=[]).elegir(lineas=LINEAS, candidatas=CANDIDATAS)


def test_f111_r33_endpoint_sin_proveedor_responde_503():
    body = PartidaResiduosRequest(document_id="d1", lineas=LINEAS, candidatas=CANDIDATAS)
    with pytest.raises(Exception) as exc:
        modulo.atender_partida_residuos(_servicio(None, proveedores=[]), body)
    assert exc.value.status_code == 503


def test_f111_r33_endpoint_fallo_del_proveedor_responde_500():
    body = PartidaResiduosRequest(document_id="d1", lineas=LINEAS, candidatas=CANDIDATAS)
    with pytest.raises(Exception) as exc:
        modulo.atender_partida_residuos(_servicio(_Cliente(error=RuntimeError("caído"))), body)
    assert exc.value.status_code == 500


def test_f111_r31_endpoint_devuelve_las_elecciones():
    body = PartidaResiduosRequest(document_id="d1", lineas=LINEAS[:1], candidatas=CANDIDATAS)
    cliente = _Cliente(_doc(
        {"line_ref": 10, "codigo": "32.01", "confianza_pct": 90, "razon_corta": "madera"},
    ))
    assert modulo.atender_partida_residuos(_servicio(cliente), body) == {
        "elecciones": [
            {"line_ref": 10, "codigo": "32.01", "confianza_pct": 90.0, "razon_corta": "madera"}
        ]
    }


def test_f111_r31_build_app_registra_la_ruta(monkeypatch):
    """La ruta existe y llega al servicio de IA4 (con dobles de la infra)."""
    rutas: dict[str, object] = {}

    class _App:
        def __init__(self, **kwargs) -> None:
            pass

        def get(self, ruta):
            return lambda f: f

        def post(self, ruta):
            def registrar(f):
                rutas[ruta] = f
                return f
            return registrar

    class _Nada:
        def __init__(self, *args, **kwargs) -> None:
            pass

    for nombre in ("SessionFactory", "SqlAlchemyValuationContextRepository",
                   "SharePointContratoPdfDownloader", "ValueAlbaranPipeline",
                   "ValuationExtractionService", "ConciliacionService"):
        monkeypatch.setattr(modulo, nombre, _Nada)
    recibidos = {}

    class _Servicio:
        def __init__(self, *, providers, **kwargs) -> None:
            recibidos["ia4"] = [p.provider for p in providers]

        def elegir(self, *, lineas, candidatas):
            recibidos["lineas"] = lineas
            return DocumentoPartidaResiduos(elecciones=[])

    monkeypatch.setattr(modulo, "FastAPI", _App)
    monkeypatch.setattr(modulo, "PartidaResiduosService", _Servicio)
    cliente = _Cliente(_doc())
    monkeypatch.setattr(
        modulo, "construir_proveedores",
        lambda *a, **k: [
            ProviderClientSpec(provider="claude", model_name="c", client=cliente),
            ProviderClientSpec(provider="openai", model_name="o", client=cliente),
        ],
    )

    class _Settings:
        prompts_yaml_path = str(PROMPTS_YAML)
        database_url = graph_key = sharepoint_mode = sharepoint_hostname = None
        sharepoint_site_path = sharepoint_drive_name = sharepoint_drive_id = None
        sharepoint_folder_url = None
        http_timeout_s = 1
        llm_max_retries = llm_backoff_base_s = llm_backoff_cap_s = 1
        ia_logging_enabled = False
        ia_logging_dir = None
        prompt_key = "valuation_es"
        ia3_provider = "openai"
        ia4_provider = "openai"
        anthropic_forzar_herramienta = True
        ia4_prompt_key = "conciliacion_es"
        max_pdf_mb = 1
        service_version = "t"
        enabled_llm_providers = []

    modulo.build_app(_Settings())
    assert "/v1/albaranes/partida-residuos" in rutas
    assert recibidos["ia4"] == ["openai"]
    body = PartidaResiduosRequest(document_id="d1", lineas=LINEAS[:1], candidatas=CANDIDATAS)
    assert rutas["/v1/albaranes/partida-residuos"](body) == {"elecciones": []}
    assert recibidos["lineas"][0]["line_ref"] == 10


def test_f111_t12_el_texto_conserva_las_tildes():
    cliente = _Cliente(_doc())
    _servicio(cliente).elegir(
        lineas=[{"line_ref": 1, "descripcion": "Clasificación", "codigo_ler": None}],
        candidatas=CANDIDATAS,
    )
    texto = cliente.llamadas[0]["user_text"]
    assert "GESTIÓN RESIDUOS" in texto
    assert "Clasificación" in texto
