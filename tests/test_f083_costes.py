# tests/test_f083_costes.py
"""F-083 · R4–R7, R10, R15: uso normalizado de los tres SDK, precio vigente y coste."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from types import SimpleNamespace as NS

import pytest

from evals import costes
from evals.costes import (
    Partida,
    Precio,
    TablaCaducada,
    Uso,
    cargar_tabla,
    coste_usd,
    estimar,
    modelo_servido,
    motivo_parada,
    precio_vigente,
    uso_de_respuesta,
)

HOY = dt.date(2026, 10, 19)


@pytest.fixture(scope="module")
def tabla():
    return cargar_tabla()


# --- R5: uso normalizado -------------------------------------------------------


def test_f083_r5_anthropic():
    respuesta = NS(
        usage=NS(
            input_tokens=1000,
            cache_read_input_tokens=200,
            cache_creation_input_tokens=50,
            output_tokens=300,
        )
    )
    assert uso_de_respuesta("claude", respuesta) == Uso(1000, 200, 50, 300, False)


def test_f083_r5_openai_resta_la_cache_de_la_entrada():
    respuesta = NS(
        usage=NS(input_tokens=1000, input_tokens_details=NS(cached_tokens=400), output_tokens=700)
    )
    assert uso_de_respuesta("openai", respuesta) == Uso(600, 400, 0, 700, False)


def test_f083_r5_gemini_suma_el_pensamiento_a_la_salida():
    respuesta = NS(
        usage_metadata=NS(
            prompt_token_count=1000,
            cached_content_token_count=100,
            candidates_token_count=300,
            thoughts_token_count=500,
        )
    )
    assert uso_de_respuesta("gemini", respuesta) == Uso(900, 100, 0, 800, False)


def test_f083_r5_acepta_diccionarios():
    respuesta = {"usage": {"input_tokens": 10, "input_tokens_details": {"cached_tokens": 4},
                           "output_tokens": 5}}
    assert uso_de_respuesta("openai", respuesta) == Uso(6, 4, 0, 5, False)


def test_f083_r5_gemini_sin_cache_ni_pensamiento_no_es_incompleto():
    """La API de Gemini omite esos dos campos cuando valen 0."""
    respuesta = NS(usage_metadata=NS(prompt_token_count=10, candidates_token_count=3))
    assert uso_de_respuesta("gemini", respuesta) == Uso(10, 0, 0, 3, False)


def test_f083_r5_anthropic_sin_campos_de_cache_no_es_incompleto():
    respuesta = NS(usage=NS(input_tokens=10, output_tokens=3, cache_read_input_tokens=None))
    assert uso_de_respuesta("claude", respuesta) == Uso(10, 0, 0, 3, False)


def test_f083_r5_openai_sin_detalle_de_cache_no_es_incompleto():
    respuesta = NS(usage=NS(input_tokens=10, output_tokens=3))
    assert uso_de_respuesta("openai", respuesta) == Uso(10, 0, 0, 3, False)


# --- R6: uso incompleto ---------------------------------------------------------


@pytest.mark.parametrize(
    ("proveedor", "respuesta", "esperado"),
    [
        ("claude", NS(), Uso(0, 0, 0, 0, True)),
        ("claude", NS(usage=NS(input_tokens=10)), Uso(10, 0, 0, 0, True)),
        ("claude", NS(usage=NS(output_tokens=7)), Uso(0, 0, 0, 7, True)),
        ("openai", NS(usage=None), Uso(0, 0, 0, 0, True)),
        ("openai", NS(usage=NS(input_tokens=10)), Uso(10, 0, 0, 0, True)),
        ("openai", NS(usage=NS(output_tokens=4)), Uso(0, 0, 0, 4, True)),
        ("gemini", NS(usage_metadata=NS(prompt_token_count=8)), Uso(8, 0, 0, 0, True)),
        ("gemini", NS(usage_metadata=NS(candidates_token_count=6)), Uso(0, 0, 0, 6, True)),
        ("gemini", None, Uso(0, 0, 0, 0, True)),
        ("mistral", NS(usage=NS(input_tokens=1, output_tokens=1)), Uso(0, 0, 0, 0, True)),
    ],
)
def test_f083_r6_campo_ausente_cuenta_cero_y_marca_incompleto(proveedor, respuesta, esperado):
    assert uso_de_respuesta(proveedor, respuesta) == esperado


def test_f083_r6_un_valor_que_no_es_entero_es_incompleto():
    respuesta = NS(usage=NS(input_tokens="mucho", output_tokens=3))
    assert uso_de_respuesta("claude", respuesta) == Uso(0, 0, 0, 3, True)


def test_f083_r6_un_booleano_no_es_un_recuento():
    respuesta = NS(usage=NS(input_tokens=True, output_tokens=3))
    assert uso_de_respuesta("claude", respuesta).incompleto is True


def test_f083_r6_cache_mayor_que_la_entrada_no_da_negativos():
    respuesta = NS(usage=NS(input_tokens=5, input_tokens_details=NS(cached_tokens=9),
                            output_tokens=1))
    uso = uso_de_respuesta("openai", respuesta)
    assert uso.entrada == 0 and uso.lectura_cache == 9 and uso.incompleto is True


def test_f083_uso_total_de_entrada():
    assert Uso(10, 20, 30, 1).entrada_total == 60


# --- modelo servido y motivo de parada (R8, R9) ---------------------------------


def test_f083_r9_modelo_servido_por_proveedor():
    assert modelo_servido("claude", NS(model="claude-opus-5-5")) == "claude-opus-5-5"
    assert modelo_servido("openai", {"model": "gpt-6-luna-2026-09-01"}) == "gpt-6-luna-2026-09-01"
    assert modelo_servido("gemini", NS(model_version="gemini-3.8-flash")) == "gemini-3.8-flash"
    assert modelo_servido("gemini", NS(model="no-es-este")) is None
    assert modelo_servido("claude", NS()) is None
    assert modelo_servido("mistral", NS(model="x")) is None


def test_f083_r8_motivo_de_parada():
    assert motivo_parada("claude", NS(stop_reason="max_tokens")) == "max_tokens"
    assert motivo_parada("openai", NS(status="completed", incomplete_details=None)) == "completed"
    incompleta = NS(status="incomplete", incomplete_details=NS(reason="max_output_tokens"))
    assert motivo_parada("openai", incompleta) == "incomplete:max_output_tokens"
    enum = NS(name="STOP")
    assert motivo_parada("gemini", NS(candidates=[NS(finish_reason=enum)])) == "STOP"
    assert motivo_parada("gemini", NS(candidates=[NS(finish_reason="SAFETY")])) == "SAFETY"
    assert motivo_parada("gemini", NS(candidates=[])) is None
    assert motivo_parada("gemini", NS()) is None
    assert motivo_parada("claude", NS()) is None
    assert motivo_parada("mistral", NS(stop_reason="x")) is None


def test_f083_r8_el_motivo_se_recorta():
    assert len(motivo_parada("claude", NS(stop_reason="x" * 500))) == costes.TOPE_TEXTO


# --- R4: precio vigente ---------------------------------------------------------


def test_f083_r4_hasta_vigente_hasta_inclusive_rige_el_actual(tabla):
    argon = tabla.modelo("gemini-4-argon")
    assert precio_vigente(argon, dt.date(2026, 11, 30)).entrada == Decimal(2)


def test_f083_r4_despues_rige_el_siguiente(tabla):
    argon = tabla.modelo("gemini-4-argon")
    assert precio_vigente(argon, dt.date(2026, 12, 1)).entrada == Decimal(4)


def test_f083_r4_sin_siguiente_la_tabla_esta_caducada(tabla):
    precio = Precio(Decimal(1), Decimal(0), Decimal(0), Decimal(2),
                    vigente_hasta=dt.date(2026, 10, 18))
    modelo = costes.Modelo(
        id="x", proveedor="openai", precio=precio, fuente="https://x", fecha_consulta=HOY,
        imagen=True, pdf=None, herramienta_forzada=None, papel="candidato",
    )
    with pytest.raises(TablaCaducada, match="x.*2026-10-18"):
        precio_vigente(modelo, HOY)


def test_f083_r4_la_cadena_de_siguientes_se_recorre(tabla):
    final = Precio(Decimal(9), Decimal(0), Decimal(0), Decimal(9))
    medio = Precio(Decimal(5), Decimal(0), Decimal(0), Decimal(5),
                   vigente_hasta=dt.date(2026, 12, 31), siguiente=final)
    primero = Precio(Decimal(1), Decimal(0), Decimal(0), Decimal(1),
                     vigente_hasta=dt.date(2026, 11, 30), siguiente=medio)
    modelo = tabla.modelo("gpt-5.4")
    modelo = costes.Modelo(**{**modelo.__dict__, "precio": primero})
    assert precio_vigente(modelo, dt.date(2027, 1, 1)).entrada == Decimal(9)
    assert precio_vigente(modelo, dt.date(2026, 12, 1)).entrada == Decimal(5)


def test_f083_r4_sin_vigente_hasta_no_caduca(tabla):
    assert precio_vigente(tabla.modelo("gpt-5.4"), dt.date(2099, 1, 1)).entrada == Decimal("2.5")


# --- R7: coste ------------------------------------------------------------------


def test_f083_r7_coste_suma_cada_clase_por_su_precio(tabla):
    # opus 5.5: 4 · 0,20 · 5 · 20 por millón.
    uso = Uso(entrada=1_000_000, lectura_cache=1_000_000, escritura_cache=1_000_000,
              salida=1_000_000)
    assert coste_usd(tabla.modelo("claude-opus-5-5"), uso, HOY) == Decimal("29.20")


def test_f083_r7_coste_de_una_llamada_tipica(tabla):
    uso = Uso(entrada=10_000, lectura_cache=0, escritura_cache=0, salida=3_000)
    # 10.000 × 2,5 + 3.000 × 15 = 25.000 + 45.000 = 70.000 / 1e6
    assert coste_usd(tabla.modelo("gpt-5.4"), uso, HOY) == Decimal("0.07")


def test_f083_r7_tramo_largo_por_encima_del_umbral(tabla):
    gpt = tabla.modelo("gpt-5.5")
    justo = Uso(entrada=272_000, lectura_cache=0, escritura_cache=0, salida=1_000_000)
    encima = Uso(entrada=271_000, lectura_cache=1_001, escritura_cache=0, salida=1_000_000)
    # En el umbral: tarifa normal (5 / 30).
    assert coste_usd(gpt, justo, HOY) == Decimal("1.36") + Decimal(30)
    # Por encima (la caché cuenta como entrada): tramo largo (10 / 1 / 45).
    assert coste_usd(gpt, encima, HOY) == Decimal("2.71") + Decimal("0.001001") + Decimal(45)


def test_f083_r7_tramo_largo_cuenta_la_escritura_de_cache(tabla):
    haiku = tabla.modelo("claude-haiku-5-5")
    uso = Uso(entrada=100_000, lectura_cache=0, escritura_cache=1, salida=0)
    assert coste_usd(haiku, uso, HOY) == Decimal("0.05") + Decimal("0.000000625")


def test_f083_r7_coste_con_el_precio_siguiente(tabla):
    uso = Uso(entrada=1_000_000, lectura_cache=0, escritura_cache=0, salida=0)
    assert coste_usd(tabla.modelo("gemini-4-argon"), uso, dt.date(2026, 12, 1)) == Decimal(4)


def test_f083_r10_uso_vacio_cuesta_cero(tabla):
    assert coste_usd(tabla.modelo("gpt-5.5"), Uso(0, 0, 0, 0, True), HOY) == 0


# --- R15: estimación ---------------------------------------------------------------


def test_f083_r15_estimacion_por_defecto_con_margen(tabla):
    estimacion = estimar([Partida("gpt-5.4", "candidato", "IA1", 10)], tabla, {}, HOY)
    linea = estimacion.lineas[0]
    # 10.000 × 1,5 = 15.000 de entrada y 3.000 × 1,5 = 4.500 de salida por llamada.
    assert (linea.entrada, linea.salida) == (15000, 4500)
    assert linea.origen == "por defecto ×1.5"
    # Por llamada: 15.000 × 2,5 + 4.500 × 15 = 105.000 / 1e6 = 0,105; × 10 llamadas.
    assert linea.usd == Decimal("1.05")
    assert estimacion.total == Decimal("1.05")


def test_f083_r15_estimacion_con_tokens_medidos(tabla):
    medidos = {("IA1", "gpt-5.4"): (2000, 1000)}
    estimacion = estimar(
        [Partida("gpt-5.4", "candidato", "IA1", 2), Partida("gpt-5.5", "candidato", "IA1", 1)],
        tabla,
        medidos,
        HOY,
    )
    medido, por_defecto = estimacion.lineas
    assert medido.origen == "medido" and (medido.entrada, medido.salida) == (2000, 1000)
    # 2 × (2.000 × 2,5 + 1.000 × 15) / 1e6 = 0,04.
    assert medido.usd == Decimal("0.04")
    # gpt-5.5: 15.000 × 5 + 4.500 × 30 = 210.000 / 1e6.
    assert por_defecto.usd == Decimal("0.21")
    assert estimacion.total == Decimal("0.25")


def test_f083_r15_la_preparacion_usa_los_tokens_de_su_fase(tabla):
    estimacion = estimar([Partida("claude-opus-4-8", "preparación", "IA3", 1)], tabla, {}, HOY)
    linea = estimacion.lineas[0]
    assert (linea.entrada, linea.salida, linea.etiqueta) == (18000, 6000, "preparación")


def test_f083_r15_estimar_con_tabla_caducada_para(tabla):
    argon = tabla.modelo("gemini-4-argon")
    sin_siguiente = costes.Modelo(
        **{**argon.__dict__, "precio": Precio(**{**argon.precio.__dict__, "siguiente": None})}
    )
    caducada = costes.Tabla({"gemini-4-argon": sin_siguiente}, tabla.referencias, tabla.estimacion)
    with pytest.raises(TablaCaducada, match="gemini-4-argon"):
        estimar([Partida("gemini-4-argon", "candidato", "IA1", 1)], caducada, {},
                dt.date(2026, 12, 1))
