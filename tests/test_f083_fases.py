# tests/test_f083_fases.py
"""F-083 · R20–R24 y T4: cómo se mide cada fase, sin LLM ni red.

Los subprocesos de sv2 y sv5 se prueban por su parte pura (`procesar` y el
llamador de cada fase) con dobles del servicio; el runner, por las dos
funciones que se extraen sin cambiar su comportamiento (R36).
"""

from __future__ import annotations

import copy
import sys
import types
from types import SimpleNamespace as NS

import pytest

from evals import runner
from evals.conversor import RUTA_FIXTURES
from evals.criticidad import cargar_criticidad
from evals.modelos import ERROR, OMITIDO, ROJO, VERDE
from evals.procesos import sv2_extraccion, sv5_valoracion, sv6_build

# --- T4 · runner.comparar_sv2 ----------------------------------------------------


def _fixture_ia1():
    return {
        "tablas": {
            "cabeceras": [{"proveedor_nombre": "ACME", "numero_albaran": "A-1",
                           "caso_id": "GEN-001"}],
            "lineas": [{"num_linea": 1, "cantidad": 2, "importe": 10.0}],
        }
    }


def _documento(numero="A-1", cantidad=2):
    return {
        "cabecera": {"proveedor_nombre": "ACME", "numero_albaran": numero},
        "lineas": [{"concepto": "x", "cantidad": cantidad, "precio_neto": 10.0}],
    }


def test_f083_runner_comparar_sv2_ia1_sin_discrepancias():
    no_observables: list[str] = []
    discrepancias = runner.comparar_sv2(
        "IA1", _fixture_ia1(), _documento(), "GEN-001", cargar_criticidad(), no_observables
    )
    assert [d for d in discrepancias if d.severidad == "fallo"] == []
    assert "caso_id" in no_observables


def test_f083_runner_comparar_sv2_ia1_detecta_el_fallo():
    discrepancias = runner.comparar_sv2(
        "IA1", _fixture_ia1(), _documento(cantidad=3), "GEN-001", cargar_criticidad()
    )
    fallos = [d.campo for d in discrepancias if d.severidad == "fallo"]
    assert fallos == ["IA1.lineas[1].cantidad"]


def test_f083_runner_comparar_sv2_ia2():
    fixture = {"tablas": {"contexto": [
        {"num_linea": 1, "campo_contexto": "bombeo", "valor_esperado": True}
    ]}}
    documento = {"lineas": [{"contexto_linea": {"bombeo": False}}]}
    discrepancias = runner.comparar_sv2("IA2", fixture, documento, "HOR-001", cargar_criticidad())
    assert [d.campo.lower() for d in discrepancias] == ["ia2.contexto[1/bombeo].valor_esperado"]


def test_f083_runner_comparar_sv2_es_lo_que_usa_el_runner(monkeypatch):
    """El runner evalúa IA1/IA2 a través de la función pública."""
    llamadas = []
    original = runner.comparar_sv2

    def espia(*args, **kwargs):
        llamadas.append(args[0])
        return original(*args, **kwargs)

    monkeypatch.setattr(runner, "comparar_sv2", espia)
    fases = {"IA1": (runner.ResultadoFase("IA1"), {"GEN-001": _fixture_ia1()}, ["gemini"])}
    monkeypatch.setattr(
        sv2_extraccion,
        "ejecutar_en_subproceso",
        lambda trabajo: {"resultados": [
            {"caso_id": "GEN-001", "proveedores": {"gemini": {"ia1": _documento(), "ia2": None}}}
        ]},
    )
    runner._evaluar_sv2([{"caso_id": "GEN-001"}], ["gemini"], fases, cargar_criticidad(), [])
    assert llamadas == ["IA1"]
    assert fases["IA1"][0].casos[0].estado == VERDE


# --- T4 · runner.evaluar_valoracion ------------------------------------------------


def _envelopes_estimulados(casos):
    inputs = runner.cargar_fixtures(RUTA_FIXTURES, "inputs")
    ia3 = runner.cargar_fixtures(RUTA_FIXTURES, "IA3")
    ia4 = runner.cargar_fixtures(RUTA_FIXTURES, "IA4")
    envelopes = {}
    for caso in casos:
        envelope = sv6_build.construir_envelope_estimulado(inputs[caso], ia3.get(caso, {"tablas": {}}))
        if caso in ia4:
            sv5_valoracion.aplicar_conciliacion(
                envelope, sv5_valoracion.conciliaciones_desde_ground_truth(ia4[caso], envelope)
            )
        envelopes[caso] = envelope
    return envelopes


def _resumen(fase):
    return [(c.caso_id, c.estado, len(c.fallos), len(c.avisos)) for c in fase.casos]


def test_f083_runner_evaluar_valoracion_coincide_con_el_modo_determinista():
    """Con los envelopes del modo determinista, IA3 y E2E salen igual (sv6 real)."""
    casos = ["FER-001", "GEN-001", "HOR-005"]
    deterministas, _ = runner.corrida_determinista(RUTA_FIXTURES, casos)
    fases, no_observables = runner.evaluar_valoracion(
        _envelopes_estimulados(casos),
        {},
        runner.cargar_fixtures(RUTA_FIXTURES, "IA3"),
        {},
        runner.cargar_fixtures(RUTA_FIXTURES, "final"),
        cargar_criticidad(),
    )
    por_nombre = {fase.nombre: fase for fase in fases}
    det = {fase.nombre: fase for fase in deterministas}
    assert [f.nombre for f in fases] == ["IA3", "IA4", "E2E"]
    assert _resumen(por_nombre["IA3"]) == _resumen(det["IA3"])
    assert _resumen(por_nombre["E2E"]) == _resumen(det["E2E"])
    assert all(c.estado == OMITIDO for c in por_nombre["IA4"].casos)
    assert isinstance(no_observables, list)


def test_f083_runner_evaluar_valoracion_con_build_inyectado():
    envelopes = {"A": {"data": {"lineas": []}}, "B": {"data": {"lineas": []}}}
    trabajos = []

    def build(trabajo):
        trabajos.append([c["caso_id"] for c in trabajo["casos"]])
        return {"resultados": [{"caso_id": "A", "error": {"motivo": "roto"}}]}

    fases, _ = runner.evaluar_valoracion(
        envelopes, {}, {"A": {}, "B": {}}, {}, {}, cargar_criticidad(), build=build
    )
    ia3, ia4, e2e = fases
    assert trabajos == [["A", "B"]]
    assert [(c.caso_id, c.estado) for c in ia3.casos] == [("A", ERROR), ("B", ERROR)]
    assert "ERROR en el build de sv6 · roto" == ia3.casos[0].motivo
    assert ia3.casos[1].motivo == "sv6 no devolvió resultado"
    assert [c.estado for c in e2e.casos] == [ERROR, ERROR]
    assert [c.estado for c in ia4.casos] == [OMITIDO, OMITIDO]


def test_f083_runner_evaluar_valoracion_build_que_muere():
    def muere(trabajo):
        raise RuntimeError("sv6 murió")

    fases, _ = runner.evaluar_valoracion(
        {"A": {}}, {}, {"A": {}}, {}, {}, cargar_criticidad(), build=muere
    )
    ia3, _, e2e = fases
    assert ia3.motivo.startswith("el subproceso de sv6 murió")
    assert e2e.casos[0].estado == ERROR


def test_f083_runner_evaluar_valoracion_ia4_compara_las_conciliaciones():
    envelope = {
        "context": {"lineas_contrato": [{"contrato_line_id": 7, "codigo_producto": "P1"}]},
        "data": {"lineas": []},
    }
    ia4 = {"A": {"tablas": {"conciliacion": [
        {"num_linea": 1, "concilia": True, "linea_contrato_esperada": "P1",
         "precio_unitario_esperado": 5.0}
    ]}}}
    bien = [{"line_ref": 1, "matched_contrato_line_id": 7, "precio_unitario_contrato_db": 5.0}]
    mal = [{"line_ref": 1, "matched_contrato_line_id": None, "precio_unitario_contrato_db": None}]
    for conciliaciones, estado in ((bien, VERDE), (mal, ROJO)):
        fases, _ = runner.evaluar_valoracion(
            {"A": copy.deepcopy(envelope)}, {"A": conciliaciones}, {}, ia4, {},
            cargar_criticidad(), build=lambda t: {"resultados": [{"caso_id": "A"}]},
        )
        assert fases[1].casos[0].estado == estado


def test_f083_runner_evaluar_valoracion_agrega_a_las_fases_que_le_pasan():
    previas = (runner.ResultadoFase("IA3"), runner.ResultadoFase("IA4"), runner.ResultadoFase("E2E"))
    previas[0].casos.append(runner.ResultadoCaso.con_error("Z", "IA3", "falló sv5"))
    fases, _ = runner.evaluar_valoracion(
        {"A": {}}, {}, {}, {}, {}, cargar_criticidad(),
        fases=previas, build=lambda t: {"resultados": [{"caso_id": "A"}]},
    )
    assert fases[0] is previas[0]
    assert [c.caso_id for c in fases[0].casos] == ["Z", "A"]


def test_f083_runner_corrida_valoracion_real_delega(monkeypatch):
    llamadas = []
    original = runner.evaluar_valoracion

    def espia(*args, **kwargs):
        llamadas.append(sorted(args[0]))
        return original(*args, **kwargs)

    monkeypatch.setattr(runner, "evaluar_valoracion", espia)
    monkeypatch.setattr(
        sv5_valoracion,
        "ejecutar_en_subproceso",
        lambda trabajo: {"resultados": [{"caso_id": "A", "envelope": {}, "conciliaciones": []}]},
    )
    monkeypatch.setattr(sv6_build, "ejecutar_en_subproceso",
                        lambda trabajo: {"resultados": [{"caso_id": "A"}]})
    runner._corrida_valoracion_real({"A": {}}, {}, {}, {}, cargar_criticidad(), ["gemini"])
    assert llamadas == [["A"]]


# --- T4 · fábricas de clientes con modelo, medidor y herramienta -------------------


class _Cliente:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


@pytest.fixture
def clientes_falsos(monkeypatch):
    from ruesma_comun.llm import (
        claude_messages_client,
        gemini_genai_client,
        openai_responses_client,
    )

    for modulo, nombre in (
        (claude_messages_client, "ClaudeMessagesVisionClient"),
        (gemini_genai_client, "GeminiGenAiVisionClient"),
        (openai_responses_client, "OpenAIResponsesVisionClient"),
    ):
        monkeypatch.setattr(modulo, nombre, type(nombre, (_Cliente,), {}))
    spec = types.ModuleType("spec_falsa")
    spec.ProviderClientSpec = lambda **kwargs: NS(**kwargs)
    monkeypatch.setitem(sys.modules, "application.services.albaran_extraction_service", spec)
    monkeypatch.setitem(sys.modules, "application.services.valuation_extraction_service", spec)
    for variable in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.setenv(variable, f"clave-{variable}")
    for variable in ("ANTHROPIC_MODEL", "GEMINI_MODEL", "OPENAI_MODEL"):
        monkeypatch.delenv(variable, raising=False)


@pytest.mark.parametrize(
    ("fabrica", "herramienta"),
    [
        (sv2_extraccion._especificacion, "emit_albaran_extraction"),
        (sv5_valoracion._clientes_reales, "emit_valuation_result"),
    ],
)
def test_f083_runner_fabricas_sin_argumentos_nuevos_como_hoy(clientes_falsos, fabrica, herramienta):
    claude = fabrica("claude")
    assert claude.model_name == "claude-sonnet-4-5"
    assert claude.client.kwargs == {"api_key": "clave-ANTHROPIC_API_KEY", "tool_name": herramienta}
    gemini = fabrica("gemini")
    assert gemini.client.args == ("clave-GEMINI_API_KEY",) and gemini.client.kwargs == {}
    assert gemini.model_name == "gemini-2.5-flash"
    openai = fabrica("openai")
    assert openai.client.args == ("clave-OPENAI_API_KEY",) and openai.client.kwargs == {}
    assert openai.provider == "openai" and openai.model_name == "gpt-5"


@pytest.mark.parametrize(
    "fabrica", [sv2_extraccion._especificacion, sv5_valoracion._clientes_reales]
)
def test_f083_runner_fabricas_con_modelo_y_medidor(clientes_falsos, fabrica):
    medidor = object()
    luna = fabrica("openai", modelo="gpt-6-luna", call_logger=medidor)
    assert luna.model_name == "gpt-6-luna"
    assert luna.client.kwargs == {"call_logger": medidor}
    argon = fabrica("gemini", modelo="gemini-4-argon", call_logger=medidor)
    assert argon.client.kwargs == {"call_logger": medidor}
    opus = fabrica("claude", modelo="claude-opus-4-8", call_logger=medidor)
    assert opus.client.kwargs["call_logger"] is medidor
    assert "forzar_herramienta" not in opus.client.kwargs
    opus55 = fabrica("claude", modelo="claude-opus-5-5", forzar_herramienta=False)
    assert opus55.client.kwargs["forzar_herramienta"] is False
    assert "call_logger" not in opus55.client.kwargs


def test_f083_runner_fabrica_toma_el_modelo_del_entorno_si_no_se_pide(clientes_falsos, monkeypatch):
    monkeypatch.setenv("OPENAI_MODEL", "gpt-5.4")
    assert sv2_extraccion._especificacion("openai").model_name == "gpt-5.4"
    assert sv2_extraccion._especificacion("openai", modelo="gpt-5.5").model_name == "gpt-5.5"
