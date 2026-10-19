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


# --- T5 · bucle medido de un bloque (medidor.procesar) ------------------------------

import os
from decimal import Decimal

from evals.procesos import medidor as medidor_mod
from evals.procesos import sv2_modelos


class _MedidorDoble:
    """Gasta `por_caso` USD en cada caso que se llama."""

    def __init__(self, por_caso="1"):
        self.por_caso = Decimal(por_caso)
        self.gastado = Decimal(0)
        self.casos: list = []
        self.registros: list = []

    def caso(self, caso_id):
        self.casos.append(caso_id)

    def gasto_usd(self):
        return self.gastado


def _llamar_que_gasta(medidor, rompe=()):
    def llamar(caso):
        medidor.gastado += medidor.por_caso
        if caso["caso_id"] in rompe:
            raise ValueError(f"respuesta con el CIF B12345678 de {caso['caso_id']}")
        return {"documento": {"caso": caso["caso_id"]}}

    return llamar


def test_f083_sv2_r24_un_caso_que_falla_no_para_a_los_demas():
    medidor = _MedidorDoble("0")
    casos = [{"caso_id": c} for c in ("A", "B", "C")]
    resultados = medidor_mod.procesar(
        casos, _llamar_que_gasta(medidor, rompe={"B"}), medidor, Decimal(10), "IA1"
    )
    assert resultados[0] == {"caso_id": "A", "documento": {"caso": "A"}}
    assert resultados[1]["caso_id"] == "B"
    assert resultados[1]["error"]["fase"] == "IA1"
    assert resultados[1]["error"]["tipo"] == "ValueError"
    assert "B12345678" not in str(resultados[1])
    assert resultados[2] == {"caso_id": "C", "documento": {"caso": "C"}}
    assert medidor.casos == ["A", "B", "C", None]


def test_f083_sv2_r19_mira_el_presupuesto_antes_de_cada_caso():
    medidor = _MedidorDoble("1")
    casos = [{"caso_id": c} for c in ("A", "B", "C", "D")]
    resultados = medidor_mod.procesar(casos, _llamar_que_gasta(medidor), medidor, "2", "IA1")
    assert [("no_ejecutado" in r) for r in resultados] == [False, False, True, True]
    assert resultados[2] == {"caso_id": "C", "no_ejecutado": True}
    assert medidor.gastado == 2


def test_f083_sv2_r19_se_puede_pasar_como_mucho_en_un_caso():
    medidor = _MedidorDoble("1.5")
    casos = [{"caso_id": c} for c in ("A", "B", "C")]
    resultados = medidor_mod.procesar(casos, _llamar_que_gasta(medidor), medidor, Decimal(2), "IA3")
    assert [("no_ejecutado" in r) for r in resultados] == [False, False, True]
    assert medidor.gastado == 3


def test_f083_sv2_r19_presupuesto_agotado_no_llama_a_nada():
    medidor = _MedidorDoble("1")
    resultados = medidor_mod.procesar(
        [{"caso_id": "A"}], _llamar_que_gasta(medidor), medidor, Decimal(0), "IA1"
    )
    assert resultados == [{"caso_id": "A", "no_ejecutado": True}]
    assert medidor.gastado == 0 and medidor.casos == [None]


# --- T5 · sv2_modelos: la llamada de cada fase -------------------------------------


class _ServicioSv2:
    def __init__(self):
        self.llamadas = []

    def extract_phase_1(self, *, attachments, provider, prompt_key):
        self.llamadas.append(("IA1", attachments, provider, prompt_key))
        return NS(parsed=NS(model_dump=lambda: {"cabecera": {"numero_albaran": "A-1"}}))

    def review_phase_2(self, *, attachments, provider, prompt_key, phase_1_json):
        self.llamadas.append(("IA2", attachments, provider, prompt_key, phase_1_json))
        revisado = {"documento_revisado": {"lineas": [{"contexto_linea": {"bombeo": True}}]}}
        if phase_1_json.get("sin_revisado"):
            revisado = {"documento_revisado": None}
        return NS(parsed=NS(model_dump=lambda: revisado))


def _adjuntos(ruta):
    return [f"adjunto:{ruta.name}"]


@pytest.mark.parametrize("fase", ["IA1", "prep_IA1"])
def test_f083_sv2_r20_ia1_con_el_prompt_y_el_preprocesado_de_produccion(fase):
    servicio = _ServicioSv2()
    llamar = sv2_modelos.llamador(fase, servicio, _adjuntos, "gemini")
    salida = llamar({"caso_id": "GEN-001", "fichero": "x/GEN-001.pdf", "tipologia": "Generico"})
    assert salida == {"documento": {"cabecera": {"numero_albaran": "A-1"}}}
    assert servicio.llamadas == [("IA1", ["adjunto:GEN-001.pdf"], "gemini", "albaran_factura_es")]


def test_f083_sv2_r21_ia2_parte_de_la_ia1_de_preparacion():
    servicio = _ServicioSv2()
    llamar = sv2_modelos.llamador("IA2", servicio, _adjuntos, "openai")
    ia1 = {"cabecera": {}}
    salida = llamar({"caso_id": "HOR-001", "fichero": "x/HOR-001.pdf", "tipologia": "Hormigon",
                     "ia1": ia1})
    assert salida == {"documento": {"lineas": [{"contexto_linea": {"bombeo": True}}]}}
    (llamada,) = servicio.llamadas
    assert llamada == ("IA2", ["adjunto:HOR-001.pdf"], "openai",
                       "albaran_revision_fase2_hormigon", ia1)


def test_f083_sv2_r21_sin_documento_revisado_vale_el_de_ia1():
    servicio = _ServicioSv2()
    llamar = sv2_modelos.llamador("IA2", servicio, _adjuntos, "openai")
    ia1 = {"sin_revisado": True}
    salida = llamar({"caso_id": "RES-001", "fichero": "RES-001.pdf", "tipologia": "Residuos",
                     "ia1": ia1})
    assert salida == {"documento": ia1}


def test_f083_sv2_fase_desconocida():
    with pytest.raises(ValueError, match="IA9"):
        sv2_modelos.llamador("IA9", _ServicioSv2(), _adjuntos, "openai")


def _trabajo_sv2(fase="IA1", herramienta=None, proveedor="openai", modelo="gpt-6-luna"):
    return {
        "fase": fase,
        "modelo": {"id": modelo, "proveedor": proveedor, "herramienta_forzada": herramienta},
        "casos": [{"caso_id": "GEN-001", "fichero": "GEN-001.pdf", "tipologia": ""}],
        "presupuesto_usd": "5",
        "fecha": "2026-10-19",
    }


def test_f083_sv2_ejecutar_trabajo_mide_con_el_modelo_del_bloque(tmp_path):
    montados = []

    def montar(modelo_id, proveedor, forzar, medidor):
        montados.append((modelo_id, proveedor, forzar, medidor.etiqueta))
        servicio = _ServicioSv2()
        original = servicio.extract_phase_1

        def extract_phase_1(**kwargs):
            medidor.log_call(
                provider=proveedor, model=modelo_id, request_summary={"duration_ms": 10},
                response_payload={"raw_sdk_response": NS(model=modelo_id, usage=NS(
                    input_tokens=1000, output_tokens=100))},
            )
            return original(**kwargs)

        servicio.extract_phase_1 = extract_phase_1
        return servicio

    trabajo = {**_trabajo_sv2(), "registros": str(tmp_path / "r.jsonl")}
    salida = sv2_modelos.ejecutar_trabajo(trabajo, montar=montar, adjuntos=_adjuntos)
    assert montados == [("gpt-6-luna", "openai", True, "candidato")]
    assert salida["resultados"] == [
        {"caso_id": "GEN-001", "documento": {"cabecera": {"numero_albaran": "A-1"}}}
    ]
    (registro,) = salida["registros"]
    assert registro["caso_id"] == "GEN-001" and registro["modelo_servido"] == "gpt-6-luna"
    assert medidor_mod.registros_de_fichero(tmp_path / "r.jsonl") == salida["registros"]


@pytest.mark.parametrize(
    ("herramienta", "forzar"), [(None, True), (True, True), (False, False)]
)
def test_f083_sv2_forzar_herramienta_sale_de_la_tabla(herramienta, forzar):
    montados = []

    def montar(modelo_id, proveedor, forzar_herramienta, medidor):
        montados.append(forzar_herramienta)
        return _ServicioSv2()

    sv2_modelos.ejecutar_trabajo(
        _trabajo_sv2(herramienta=herramienta, proveedor="claude", modelo="claude-opus-5-5"),
        montar=montar, adjuntos=_adjuntos,
    )
    assert montados == [forzar]


def test_f083_sv2_la_preparacion_se_etiqueta_como_tal():
    etiquetas = []

    def montar(modelo_id, proveedor, forzar, medidor):
        etiquetas.append(medidor.etiqueta)
        return _ServicioSv2()

    sv2_modelos.ejecutar_trabajo(_trabajo_sv2(fase="prep_IA1"), montar=montar, adjuntos=_adjuntos)
    assert etiquetas == ["preparación"]


def test_f083_sv2_el_error_de_ia2_se_atribuye_a_ia2():
    class Roto(_ServicioSv2):
        def review_phase_2(self, **kwargs):
            raise RuntimeError("roto")

    trabajo = _trabajo_sv2(fase="IA2")
    trabajo["casos"][0]["ia1"] = {}
    salida = sv2_modelos.ejecutar_trabajo(trabajo, montar=lambda *a: Roto(), adjuntos=_adjuntos)
    assert salida["resultados"][0]["error"]["fase"] == "IA2"


def test_f083_sv2_subproceso_real_sin_casos():
    """El subproceso arranca sv2 de verdad (sin red: no hay casos que llamar)."""
    trabajo = {**_trabajo_sv2(), "casos": []}
    entorno = {**os.environ, "OPENAI_API_KEY": "clave-de-prueba"}
    salida = medidor_mod.lanzar("evals.procesos.sv2_modelos", trabajo, "sv2", entorno=entorno)
    assert salida == {"resultados": [], "registros": []}


def test_f083_sv2_subproceso_sin_clave_muere_con_codigo():
    entorno = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    trabajo = {**_trabajo_sv2(), "casos": []}
    with pytest.raises(RuntimeError, match="código 1"):
        medidor_mod.lanzar("evals.procesos.sv2_modelos", trabajo, "sv2", entorno=entorno)


# --- T6 · sv5_modelos: IA3, IA4 y la preparación de IA3 --------------------------

from evals.procesos import sv5_modelos

_LINEA_VALORADA = {
    "merge_line_id": 1,
    "line_kind": "from_albaran",
    "matched_contrato_line_id": 7,
    "precio_unitario_contrato_db": 5.0,
}


def _contexto():
    return {"document_id": "RES-001", "codigo_contrato": "C-1", "lineas_albaran": [
        {"merge_line_id": 1, "descripcion": "x"}], "lineas_contrato": [
        {"contrato_line_id": 7, "codigo_producto": "P1"}]}


@pytest.mark.parametrize("fase", ["IA3", "prep_IA3"])
def test_f083_sv5_r22_ia3_monta_el_envelope_con_las_lineas_valoradas(fase):
    """Aviso del líder (2026-10-19): el envelope SÍ lleva las líneas que valora el modelo."""
    vistos = []

    def valorar(contexto):
        vistos.append(contexto["document_id"])
        return [dict(_LINEA_VALORADA)]

    llamar = sv5_modelos.llamador(fase, valorar, None, "openai", "gpt-6-luna")
    salida = llamar({"caso_id": "RES-001", "contexto": _contexto()})
    envelope = salida["envelope"]
    assert vistos == ["RES-001"]
    assert envelope["data"]["lineas"] == [_LINEA_VALORADA]
    assert envelope["meta"]["primary_provider"] == "openai"
    assert envelope["meta"]["model"] == "gpt-6-luna"
    assert envelope["context"]["lineas_contrato"] == _contexto()["lineas_contrato"]


def test_f083_sv5_r23_ia4_concilia_sobre_el_envelope_de_preparacion():
    vistos = []

    def conciliar(envelope, contexto):
        vistos.append((envelope["meta"]["model"], contexto["document_id"]))
        return [{"line_ref": 1, "matched_contrato_line_id": 7}]

    llamar = sv5_modelos.llamador("IA4", None, conciliar, "claude", "claude-opus-5-5")
    envelope = {"meta": {"model": "claude-opus-4-8"}, "data": {"lineas": []}}
    salida = llamar({"caso_id": "RES-001", "contexto": _contexto(), "envelope": envelope})
    assert salida == {"conciliaciones": [{"line_ref": 1, "matched_contrato_line_id": 7}]}
    assert vistos == [("claude-opus-4-8", "RES-001")]


def test_f083_sv5_fase_desconocida():
    with pytest.raises(ValueError, match="IA1"):
        sv5_modelos.llamador("IA1", None, None, "claude", "x")


def _trabajo_sv5(fase="IA3", herramienta=True, proveedor="claude", modelo="claude-opus-4-8"):
    return {
        "fase": fase,
        "modelo": {"id": modelo, "proveedor": proveedor, "herramienta_forzada": herramienta},
        "casos": [{"caso_id": "RES-001", "contexto": _contexto()}],
        "presupuesto_usd": "5",
        "fecha": "2026-10-19",
    }


@pytest.mark.parametrize(
    ("fase", "etiqueta", "herramienta", "forzar"),
    [
        ("IA3", "candidato", True, True),
        ("prep_IA3", "preparación", True, True),
        ("IA3", "candidato", False, False),
    ],
)
def test_f083_sv5_ejecutar_trabajo(fase, etiqueta, herramienta, forzar):
    montados = []

    def montar(modelo_id, proveedor, forzar_herramienta, medidor):
        montados.append((modelo_id, proveedor, forzar_herramienta, medidor.etiqueta))
        return (lambda contexto: [dict(_LINEA_VALORADA)]), None

    salida = sv5_modelos.ejecutar_trabajo(
        _trabajo_sv5(fase=fase, herramienta=herramienta), montar=montar
    )
    assert montados == [("claude-opus-4-8", "claude", forzar, etiqueta)]
    assert salida["resultados"][0]["envelope"]["data"]["lineas"] == [_LINEA_VALORADA]
    assert salida["registros"] == []


def test_f083_sv5_r24_el_error_de_ia4_se_atribuye_a_ia4():
    def conciliar(envelope, contexto):
        raise RuntimeError("roto")

    trabajo = _trabajo_sv5(fase="IA4")
    trabajo["casos"][0]["envelope"] = {"meta": {}}
    salida = sv5_modelos.ejecutar_trabajo(trabajo, montar=lambda *a: (None, conciliar))
    assert salida["resultados"][0]["error"]["fase"] == "IA4"


def test_f083_sv5_subproceso_real_sin_casos():
    trabajo = {**_trabajo_sv5(), "casos": []}
    entorno = {**os.environ, "ANTHROPIC_API_KEY": "clave-de-prueba"}
    salida = medidor_mod.lanzar("evals.procesos.sv5_modelos", trabajo, "sv5", entorno=entorno)
    assert salida == {"resultados": [], "registros": []}
