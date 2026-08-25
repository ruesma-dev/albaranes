# tests/test_f036_r9_r12_contexto_merger.py
"""F-036 D2 · el contexto de residuos ya no se pierde al fusionar.

Diagnostico (progress/explore_F-036.md): `_score_contexto` solo puntuaba
los CINCO campos narrativos. Un contexto que traia el codigo LER, los m3
y el numero de contenedores —y nada mas— puntuaba 0 y se descartaba
ENTERO. Y aun puntuando, un candidato con `tipo_familia` + `rol_linea`
(score 2) le ganaba a otro con las nueve medidas, asi que los m3 se
perdian igual. Por eso R9/R10 (puntuar) y R11/R12 (completar) van
juntos: cada uno arregla una cara del mismo defecto.

Funcion pura: sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest

from application.services.contexto_linea_merger import (
    _CAMPOS_RESIDUOS,
    _score_contexto,
    pick_best_contexto_linea,
)
from domain.models.contexto_linea import ContextoLinea


# ------------------------------------------------------------------ #
# R9 · los nueve campos de residuos puntuan
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("codigo_ler", "170504"),
        ("volumen_m3", 6.0),
        ("peso_toneladas", 1.2),
        ("contenedores", 1.0),
        ("contenedores_entregados", 2.0),
        ("contenedores_retirados", 1.0),
        ("carga_incompleta", True),
        ("m3_no_transportados", 0.5),
        ("exceso_declarado_min", 103.0),
    ],
)
def test_f036_r9_cada_campo_de_residuos_suma_un_punto(campo, valor):
    assert _score_contexto(ContextoLinea(**{campo: valor})) == 1


def test_f036_r9_son_exactamente_los_nueve_campos_del_requisito():
    """La lista es el contrato: si crece, R9 y R11 cambian a la vez."""
    assert _CAMPOS_RESIDUOS == (
        "codigo_ler",
        "volumen_m3",
        "peso_toneladas",
        "contenedores",
        "contenedores_entregados",
        "contenedores_retirados",
        "carga_incompleta",
        "m3_no_transportados",
        "exceso_declarado_min",
    )


def test_f036_r9_los_cinco_narrativos_siguen_puntuando():
    """Ampliar el scorer no puede quitarle valor a lo que ya contaba."""
    ctx = ContextoLinea(
        tipo_familia="residuos",
        rol_linea="base",
        descripcion_extendida="CONTENEDOR RCD 6 m3",
        notas_tiempo="carga 10 min",
        ref_linea_base=0,
    )

    assert _score_contexto(ctx) == 5


def test_f036_r9_carga_incompleta_false_es_un_dato_no_un_hueco():
    """`False` es informacion: el albaran dijo que la carga iba llena."""
    assert _score_contexto(ContextoLinea(carga_incompleta=False)) == 1


def test_f036_r9_un_codigo_ler_en_blanco_no_puntua():
    """Cadena vacia o de espacios = campo sin rellenar."""
    assert _score_contexto(ContextoLinea(codigo_ler="   ")) == 0


def test_f036_r9_todo_relleno_suma_los_catorce():
    ctx = ContextoLinea(
        tipo_familia="residuos",
        rol_linea="base",
        descripcion_extendida="x",
        notas_tiempo="y",
        ref_linea_base=0,
        codigo_ler="170504",
        volumen_m3=6.0,
        peso_toneladas=1.2,
        contenedores=1.0,
        contenedores_entregados=2.0,
        contenedores_retirados=1.0,
        carga_incompleta=True,
        m3_no_transportados=0.5,
        exceso_declarado_min=103.0,
    )

    assert _score_contexto(ctx) == 14


# ------------------------------------------------------------------ #
# R10 · un contexto de SOLO residuos ya no se descarta
# ------------------------------------------------------------------ #
def test_f036_r10_un_contexto_solo_de_residuos_no_se_descarta():
    """El caso real de SALMEDINA: LER + m3 y ni un campo narrativo.

    Antes de F-036 este contexto puntuaba 0, `pick_best` lo descartaba
    y sv3 persistia `contexto_linea = NULL`. Desde ahi todo lo demas
    (tipologia de sv5, calculo de contenedores de sv6) trabajaba a
    ciegas.
    """
    solo_residuos = ContextoLinea(codigo_ler="170504", volumen_m3=6.0)

    elegido = pick_best_contexto_linea(openai_ctx=solo_residuos)

    assert elegido is not None
    assert elegido.codigo_ler == "170504"
    assert elegido.volumen_m3 == 6.0


def test_f036_r10_sin_ningun_campo_sigue_devolviendo_none():
    """Puntuar mas campos no puede resucitar un contexto vacio."""
    assert pick_best_contexto_linea(openai_ctx=ContextoLinea()) is None
    assert pick_best_contexto_linea() is None
# ------------------------------------------------------------------ #
# R11 · el ganador se COMPLETA con las medidas que le faltan
# ------------------------------------------------------------------ #
def test_f036_r11_el_ganador_pobre_conserva_los_m3_del_rico():
    """La segunda cara del defecto (riesgo 2 del diseno).

    OpenAI gana por score con los campos narrativos, pero no leyo los
    m3 ni el LER. Gemini si. Puntuar no basta: hay que completar.
    """
    gana_por_score = ContextoLinea(
        tipo_familia="residuos",
        rol_linea="base",
        descripcion_extendida="RETIRADA DE CONTENEDOR",
        notas_tiempo="—",
        ref_linea_base=0,
    )
    trae_las_medidas = ContextoLinea(
        codigo_ler="170504",
        volumen_m3=6.0,
    )

    elegido = pick_best_contexto_linea(
        openai_ctx=gana_por_score, gemini_ctx=trae_las_medidas
    )

    assert elegido.descripcion_extendida == "RETIRADA DE CONTENEDOR"
    assert elegido.codigo_ler == "170504"
    assert elegido.volumen_m3 == 6.0


def test_f036_r11_un_campo_con_valor_en_el_ganador_no_se_pisa():
    """Completar es rellenar huecos, nunca corregir al ganador."""
    ganador = ContextoLinea(
        tipo_familia="residuos",
        rol_linea="base",
        descripcion_extendida="x",
        codigo_ler="170504",
        volumen_m3=6.0,
    )
    otro = ContextoLinea(codigo_ler="170203", volumen_m3=12.0)

    elegido = pick_best_contexto_linea(openai_ctx=ganador, gemini_ctx=otro)

    assert elegido.codigo_ler == "170504"
    assert elegido.volumen_m3 == 6.0


def test_f036_r11_carga_incompleta_false_del_ganador_no_se_pisa():
    """`False` no es un hueco: no se rellena con el `True` del otro."""
    ganador = ContextoLinea(
        tipo_familia="residuos", rol_linea="base", carga_incompleta=False
    )
    otro = ContextoLinea(carga_incompleta=True)

    elegido = pick_best_contexto_linea(openai_ctx=ganador, gemini_ctx=otro)

    assert elegido.carga_incompleta is False


def test_f036_r11_manda_el_candidato_de_mayor_score():
    """Dos candidatos traen el mismo hueco: gana el de mas score."""
    ganador = ContextoLinea(
        tipo_familia="residuos",
        rol_linea="base",
        descripcion_extendida="x",
        notas_tiempo="y",
        ref_linea_base=0,
    )
    rico = ContextoLinea(codigo_ler="170504", volumen_m3=6.0)
    pobre = ContextoLinea(volumen_m3=99.0)

    elegido = pick_best_contexto_linea(
        openai_ctx=ganador, gemini_ctx=pobre, claude_ctx=rico
    )

    assert elegido.volumen_m3 == 6.0


def test_f036_r11_completar_no_muta_al_ganador():
    """El objeto que llego se queda como estaba: se devuelve una copia."""
    ganador = ContextoLinea(tipo_familia="residuos", rol_linea="base")
    otro = ContextoLinea(volumen_m3=6.0)

    elegido = pick_best_contexto_linea(openai_ctx=ganador, gemini_ctx=otro)

    assert elegido is not ganador
    assert ganador.volumen_m3 is None
    assert elegido.volumen_m3 == 6.0


def test_f036_r11_sin_huecos_que_rellenar_se_devuelve_el_ganador(caplog):
    """Nada que completar: ni copia ni log de relleno."""
    ganador = ContextoLinea(
        tipo_familia="residuos", rol_linea="base", volumen_m3=6.0
    )

    elegido = pick_best_contexto_linea(
        openai_ctx=ganador, gemini_ctx=ContextoLinea(volumen_m3=9.0)
    )

    assert elegido is ganador


def test_f036_r11_queda_en_el_log_que_se_completo_y_desde_quien(caplog):
    """R11 exige traza: sin ella nadie sabe de donde salio el m3."""
    import logging

    ganador = ContextoLinea(tipo_familia="residuos", rol_linea="base")
    gemini = ContextoLinea(codigo_ler="170504", volumen_m3=6.0)

    with caplog.at_level(logging.INFO):
        pick_best_contexto_linea(openai_ctx=ganador, gemini_ctx=gemini)

    traza = " ".join(r.getMessage() for r in caplog.records)
    assert "codigo_ler" in traza
    assert "volumen_m3" in traza
    assert "gemini" in traza


# ------------------------------------------------------------------ #
# R12 · los cinco narrativos NO se fusionan
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("campo", "valor_del_otro"),
    [
        ("tipo_familia", "hormigon"),
        ("rol_linea", "transporte"),
        ("descripcion_extendida", "TEXTO DEL OTRO PROVEEDOR"),
        ("notas_tiempo", "45 min de espera"),
        ("ref_linea_base", 7),
    ],
)
def test_f036_r12_los_narrativos_llegan_integros_del_ganador(
    campo, valor_del_otro,
):
    """Un `rol_linea` de Gemini no encaja con la descripcion de OpenAI.

    Es la razon por la que el modulo elige UN contexto integro en vez de
    fusionar campo a campo, y sigue valiendo: solo se completan las
    MEDIDAS del documento (R11), que no son interpretaciones.
    """
    ganador = ContextoLinea(
        codigo_ler="170504",
        volumen_m3=6.0,
        peso_toneladas=1.2,
        contenedores=1.0,
    )
    otro = ContextoLinea(**{campo: valor_del_otro})

    elegido = pick_best_contexto_linea(openai_ctx=ganador, gemini_ctx=otro)

    assert getattr(elegido, campo) is None


def test_f036_r12_el_orden_canonico_sigue_desempatando():
    """A igual score manda openai → gemini → claude, como siempre."""
    a = ContextoLinea(tipo_familia="residuos", descripcion_extendida="OPENAI")
    b = ContextoLinea(tipo_familia="residuos", descripcion_extendida="GEMINI")

    elegido = pick_best_contexto_linea(openai_ctx=a, gemini_ctx=b)

    assert elegido.descripcion_extendida == "OPENAI"
