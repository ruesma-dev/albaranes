# tests/test_f083_medidor.py
"""F-083 · R8–R10: el medidor que entra como `call_logger` de los clientes de comun."""

from __future__ import annotations

import datetime as dt
import inspect
import json
from decimal import Decimal
from types import SimpleNamespace as NS

import pytest

from evals.costes import cargar_tabla
from evals.procesos.medidor import MedidorDeUso, registros_de_fichero

HOY = dt.date(2026, 10, 19)

#: Lo que nunca puede acabar en un registro: el texto del prompt o de la respuesta.
CENTINELA = "CENTINELA-B12345678-ACME-SA"


@pytest.fixture
def medidor():
    return MedidorDeUso("candidato", cargar_tabla(), HOY)


def _resumen(duracion=1500):
    return {
        "model": "gpt-5.4",
        "instructions": f"instrucciones {CENTINELA}",
        "user_text": f"texto {CENTINELA}",
        "duration_ms": duracion,
    }


def _respuesta_openai(**extra):
    return NS(
        model="gpt-5.4-2026-03-05",
        status="completed",
        incomplete_details=None,
        output_text=f'{{"proveedor": "{CENTINELA}"}}',
        usage=NS(input_tokens=10_000, input_tokens_details=NS(cached_tokens=0),
                 output_tokens=3_000),
        **extra,
    )


def test_f083_r8_misma_firma_que_el_logger_de_comun():
    from ruesma_comun.llm.llm_call_logger import LlmCallLogger

    nuestra = inspect.signature(MedidorDeUso.log_call)
    suya = inspect.signature(LlmCallLogger.log_call)
    assert list(nuestra.parameters) == list(suya.parameters)
    assert MedidorDeUso("x", None, HOY).enabled is True


def test_f083_r8_registra_una_llamada_valida(medidor):
    medidor.caso("GEN-001")
    medidor.log_call(
        provider="openai",
        model="gpt-5.4",
        request_summary=_resumen(),
        response_payload={"raw_sdk_response": _respuesta_openai(), "parsed_pydantic": {}},
    )
    (registro,) = medidor.registros
    assert registro == {
        "caso_id": "GEN-001",
        "etiqueta": "candidato",
        "proveedor": "openai",
        "modelo_pedido": "gpt-5.4",
        "modelo_servido": "gpt-5.4-2026-03-05",
        "duracion_ms": 1500,
        "entrada": 10_000,
        "lectura_cache": 0,
        "escritura_cache": 0,
        "salida": 3_000,
        "uso_incompleto": False,
        # 10.000 × 2,5 + 3.000 × 15 = 70.000 / 1e6.
        "coste_usd": "0.07",
        "motivo_parada": "completed",
        "fallo": False,
        "con_respuesta": True,
    }
    assert medidor.gasto_usd() == Decimal("0.07")


def test_f083_r10_respuesta_que_no_valida_cuenta_su_coste(medidor):
    """Error de parseo: el cliente pasa la respuesta del SDK tal cual."""
    medidor.log_call(
        provider="openai",
        model="gpt-5.4",
        request_summary=_resumen(),
        response_payload=_respuesta_openai(),
        error=f"PARSE ERROR: ValidationError: {CENTINELA}",
    )
    (registro,) = medidor.registros
    assert registro["fallo"] is True and registro["con_respuesta"] is True
    assert registro["coste_usd"] == "0.07"


def test_f083_r10_fallo_sin_respuesta_cuesta_cero(medidor):
    medidor.log_call(
        provider="claude",
        model="claude-opus-5-5",
        request_summary=_resumen(duracion=200),
        response_payload=None,
        error=f"BadRequestError: {CENTINELA}",
    )
    (registro,) = medidor.registros
    assert registro["fallo"] is True and registro["con_respuesta"] is False
    assert registro["coste_usd"] == "0"
    assert registro["uso_incompleto"] is False
    assert registro["modelo_servido"] is None
    assert medidor.gasto_usd() == 0


def test_f083_r8_nunca_guarda_texto_de_prompt_ni_respuesta(medidor, tmp_path):
    medidor = MedidorDeUso("candidato", cargar_tabla(), HOY, fichero=tmp_path / "r.jsonl")
    medidor.caso("GEN-001")
    for payload, error in (
        ({"raw_sdk_response": _respuesta_openai(), "parsed_pydantic": {"x": CENTINELA}}, None),
        (_respuesta_openai(), f"PARSE ERROR: {CENTINELA}"),
        (None, f"APIError: {CENTINELA}"),
    ):
        medidor.log_call(provider="openai", model="gpt-5.4", request_summary=_resumen(),
                         response_payload=payload, error=error)
    assert CENTINELA not in json.dumps(medidor.registros)
    assert CENTINELA not in (tmp_path / "r.jsonl").read_text(encoding="utf-8")


def test_f083_r8_payload_roto_no_propaga(medidor):
    class Explota:
        def __getattr__(self, nombre):
            raise RuntimeError("roto")

    medidor.caso("GEN-002")
    assert medidor.log_call(
        provider="openai", model="gpt-5.4", request_summary=None, response_payload=Explota()
    ) is None
    (registro,) = medidor.registros
    assert registro["fallo_medidor"] is True
    assert registro["caso_id"] == "GEN-002"
    assert registro["coste_usd"] == "0"
    assert medidor.gasto_usd() == 0


def test_f083_r8_modelo_que_no_esta_en_la_tabla_no_propaga(medidor):
    medidor.log_call(provider="openai", model="gpt-9", request_summary=_resumen(),
                     response_payload={"raw_sdk_response": _respuesta_openai()})
    (registro,) = medidor.registros
    assert registro["fallo_medidor"] is True and registro["modelo_pedido"] == "gpt-9"


def test_f083_r8_duracion_que_no_es_entero(medidor):
    resumen = {**_resumen(), "duration_ms": "mucho"}
    medidor.log_call(provider="openai", model="gpt-5.4", request_summary=resumen,
                     response_payload={"raw_sdk_response": _respuesta_openai()})
    assert medidor.registros[0]["duracion_ms"] is None


def test_f083_r8_sin_caso_fijado(medidor):
    medidor.log_call(provider="openai", model="gpt-5.4", request_summary=_resumen(),
                     response_payload={"raw_sdk_response": _respuesta_openai()})
    assert medidor.registros[0]["caso_id"] is None


def test_f083_r8_payload_dict_sin_respuesta_del_sdk(medidor):
    medidor.log_call(provider="openai", model="gpt-5.4", request_summary=_resumen(),
                     response_payload={"usage": {"input_tokens": 10, "output_tokens": 1}})
    assert medidor.registros[0]["entrada"] == 10


def test_f083_r8_gasto_acumula_y_se_vuelca_al_fichero(tmp_path):
    ruta = tmp_path / "sub" / "registros.jsonl"
    medidor = MedidorDeUso("preparación", cargar_tabla(), HOY, fichero=ruta)
    for caso in ("GEN-001", "GEN-002"):
        medidor.caso(caso)
        medidor.log_call(provider="openai", model="gpt-5.4", request_summary=_resumen(),
                         response_payload={"raw_sdk_response": _respuesta_openai()})
    assert medidor.gasto_usd() == Decimal("0.14")
    leidos = registros_de_fichero(ruta)
    assert [r["caso_id"] for r in leidos] == ["GEN-001", "GEN-002"]
    assert leidos == medidor.registros


def test_f083_r8_fichero_que_no_se_puede_escribir_no_propaga(tmp_path):
    ocupado = tmp_path / "soy_un_fichero"
    ocupado.write_text("x", encoding="utf-8")
    medidor = MedidorDeUso("candidato", cargar_tabla(), HOY, fichero=ocupado / "r.jsonl")
    medidor.log_call(provider="openai", model="gpt-5.4", request_summary=_resumen(),
                     response_payload={"raw_sdk_response": _respuesta_openai()})
    assert len(medidor.registros) == 1


def test_f083_r26_registros_de_fichero_tolera_lineas_rotas_y_ausencia(tmp_path):
    assert registros_de_fichero(tmp_path / "no_existe.jsonl") == []
    ruta = tmp_path / "r.jsonl"
    ruta.write_text('{"caso_id": "A"}\n{roto\n\n{"caso_id": "B"}\n[1]\n', encoding="utf-8")
    assert registros_de_fichero(ruta) == [{"caso_id": "A"}, {"caso_id": "B"}]
