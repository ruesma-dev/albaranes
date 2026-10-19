# tests/test_f083_decision.py
"""F-083 · R27, R30–R35: métricas por modelo y criterio de recomendación.

Un test por umbral y por frontera: los umbrales (P6) viven en `decision.py`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from evals import decision
from evals.decision import NO_EJECUTADO, Metricas, medir, recomendar
from evals.modelos import ERROR, OMITIDO, Discrepancia, ResultadoCaso

REF = "ref"


def _m(modelo, fallos=10, coste="1", tiempo="10", errores=0, no_ejecutados=0, casos=5):
    return Metricas(
        modelo=modelo,
        fase="IA1",
        repeticiones=1,
        casos=casos,
        errores=errores,
        no_ejecutados=no_ejecutados,
        fallos=Decimal(fallos),
        coste_por_albaran=Decimal(coste),
        tiempo_medio_s=Decimal(tiempo),
    )


def _rec(*metricas, repeticiones=1):
    return recomendar({m.modelo: m for m in metricas}, REF, repeticiones)


# --- R30: elegibles y «sin datos» ----------------------------------------------------


def test_f083_r30_sin_referencia_no_hay_datos():
    r = _rec(_m("a"))
    assert r.veredicto == "sin datos" and r.recomendado is None and r.elegibles == []


@pytest.mark.parametrize("cambio", [{"errores": 1}, {"no_ejecutados": 1}, {"casos": 0}])
def test_f083_r30_referencia_incompleta_no_hay_datos(cambio):
    r = _rec(_m(REF, **cambio), _m("a", fallos=0))
    assert r.veredicto == "sin datos" and r.recomendado is None


def test_f083_r30_un_error_o_un_no_ejecutado_no_es_elegible():
    r = _rec(_m(REF), _m("a", fallos=0, errores=1), _m("b", fallos=0, no_ejecutados=1))
    assert r.elegibles == [REF]
    assert r.recomendado == REF and r.veredicto == "mantener"


def test_f083_r30_frontera_fallos_iguales_a_la_referencia_es_elegible():
    r = _rec(_m(REF, fallos=10), _m("igual", fallos=10), _m("peor", fallos=11))
    assert r.elegibles == [REF, "igual"]


# --- R31: banda de empate ----------------------------------------------------------------


def test_f083_r31_banda_minima_de_dos_fallos():
    r = _rec(_m(REF, fallos=10), _m("a", fallos=0), _m("b", fallos=2), _m("c", fallos=3))
    assert r.banda == ["a", "b"]


def test_f083_r31_banda_del_cinco_por_ciento_con_muchos_fallos():
    # mejor 100 ⇒ banda hasta 105.
    r = _rec(_m(REF, fallos=200), _m("a", fallos=100), _m("b", fallos=105), _m("c", fallos=106))
    assert r.banda == ["a", "b"]


def test_f083_r31_el_cinco_por_ciento_manda_solo_si_supera_dos():
    # mejor 41 ⇒ 5 % = 2,05 ⇒ banda hasta 43,05.
    r = _rec(_m(REF, fallos=50), _m("a", fallos=41), _m("b", fallos="43.05"),
             _m("c", fallos="43.06"))
    assert r.banda == ["a", "b"]


# --- R32: recomendado ----------------------------------------------------------------------


def test_f083_r32_el_mas_barato_de_la_banda():
    r = _rec(_m(REF, fallos=10, coste="1"), _m("a", fallos=9, coste="0.5"),
             _m("b", fallos=10, coste="0.4"))
    assert r.recomendado == "b"


def test_f083_r32_empate_de_coste_decide_el_tiempo():
    # b cuesta un 4 % más que a (empate) y tarda menos.
    r = _rec(_m(REF, coste="2", tiempo="10"), _m("a", coste="1", tiempo="9"),
             _m("b", coste="1.04", tiempo="5"))
    assert r.recomendado == "b"


def test_f083_r32_frontera_cinco_por_ciento_exacto_no_es_empate():
    r = _rec(_m(REF, coste="2", tiempo="10"), _m("a", coste="1", tiempo="9"),
             _m("b", coste="1.05", tiempo="5"))
    assert r.recomendado == "a"


def test_f083_r32_coste_cero():
    r = _rec(_m(REF, coste="0", tiempo="3"), _m("a", coste="0", tiempo="1"))
    assert r.recomendado == "a"


# --- R33: cambiar o mantener ----------------------------------------------------------------


def test_f083_r33_mejora_clara_cambia():
    # La referencia (100) queda fuera de la banda de a (90 + 4,5): a es el recomendado.
    r = _rec(_m(REF, fallos=100, coste="1"), _m("a", fallos=90, coste="1.5"))
    assert r.banda == ["a"]
    assert r.recomendado == "a" and r.veredicto == "cambiar"


def test_f083_r33_frontera_mejora_coste_un_poco_mas_caro_mantiene():
    r = _rec(_m(REF, fallos=100, coste="1"), _m("a", fallos=90, coste="1.51"))
    assert r.recomendado == "a" and r.veredicto == "mantener"


def test_f083_r33_frontera_mejora_de_fallos_justa():
    # 91 > 0,9 × 100: no es mejora clara, y más caro no es ahorro.
    r = _rec(_m(REF, fallos=100, coste="1"), _m("a", fallos=91, coste="1.2"))
    assert r.recomendado == "a" and r.veredicto == "mantener"


def test_f083_r33_frontera_mejora_fallos_insuficiente_mantiene():
    # 9,1 > 0,9 × 10 y además más caro: ni mejora ni ahorro.
    r = _rec(_m(REF, fallos=10, coste="1"), _m("a", fallos="9.1", coste="0.99"))
    assert r.recomendado == "a" and r.veredicto == "mantener"


def test_f083_r33_ahorro_claro_cambia():
    r = _rec(_m(REF, fallos=10, coste="1"), _m("a", fallos=10, coste="0.7"))
    assert r.veredicto == "cambiar"


def test_f083_r33_frontera_ahorro_insuficiente_mantiene():
    r = _rec(_m(REF, fallos=10, coste="1"), _m("a", fallos=10, coste="0.71"))
    assert r.recomendado == "a" and r.veredicto == "mantener"


def test_f083_r33_recomendado_la_referencia_mantiene():
    r = _rec(_m(REF, fallos=10, coste="0.1"), _m("a", fallos=10, coste="1"))
    assert r.recomendado == REF and r.veredicto == "mantener"


# --- R34: latencia ----------------------------------------------------------------------------


def test_f083_r34_aviso_si_tarda_mas_del_doble():
    r = _rec(_m(REF, coste="1", tiempo="10"), _m("a", coste="0.5", tiempo="20.1"))
    assert r.recomendado == "a"
    assert any("tarda" in aviso for aviso in r.avisos)


def test_f083_r34_frontera_el_doble_justo_no_avisa():
    r = _rec(_m(REF, coste="1", tiempo="10"), _m("a", coste="0.5", tiempo="20"))
    assert r.avisos == []


def test_f083_r34_sin_tiempos_no_avisa():
    r = _rec(_m(REF, coste="1", tiempo="0"), _m("a", coste="0.5", tiempo="0"))
    assert r.avisos == []


# --- R35: provisional ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("repeticiones", "provisional", "etiqueta"),
    [(1, True, "provisional (1 repetición)"), (2, True, "provisional (2 repeticiones)"),
     (3, False, "")],
)
def test_f083_r35_provisional_hasta_tres_repeticiones(repeticiones, provisional, etiqueta):
    r = _rec(_m(REF), repeticiones=repeticiones)
    assert r.provisional is provisional and r.etiqueta_provisional == etiqueta


def test_f083_r35_sin_datos_tambien_lleva_la_marca():
    assert _rec(repeticiones=1).provisional is True


# --- R27: métricas de un modelo ---------------------------------------------------------------


def _caso(caso_id, fallos=0, avisos=0, estado=None):
    if estado is not None:
        return ResultadoCaso(caso_id=caso_id, fase="IA1", estado=estado, motivo="x")
    discrepancias = [Discrepancia(f"c{i}", 1, 2, "fallo") for i in range(fallos)]
    discrepancias += [Discrepancia(f"a{i}", 1, 2, "aviso") for i in range(avisos)]
    return ResultadoCaso.desde_discrepancias(caso_id, "IA1", discrepancias)


def _registro(caso, repeticion, coste, ms, entrada=100, salida=10, **extra):
    return {"caso_id": caso, "repeticion": repeticion, "etiqueta": "candidato",
            "coste_usd": coste, "duracion_ms": ms, "entrada": entrada, "lectura_cache": 0,
            "escritura_cache": 0, "salida": salida, "con_respuesta": True,
            "uso_incompleto": False, "modelo_servido": "x-1", "motivo_parada": "stop", **extra}


def test_f083_r27_metricas_de_una_repeticion():
    casos = [[_caso("A", fallos=2, avisos=1), _caso("B"), _caso("C", estado=ERROR),
              _caso("D", estado=NO_EJECUTADO), _caso("E", estado=OMITIDO)]]
    registros = [
        _registro("A", 1, "0.10", 1000, entrada=300, salida=30),
        _registro("A", 1, "0.20", 3000, lectura_cache=100, salida=10),
        _registro("B", 1, "0.30", 2000, uso_incompleto=True, modelo_servido="x-2"),
        _registro("C", 1, "0", 500, con_respuesta=False, modelo_servido=None,
                  motivo_parada=None),
        {**_registro("C", 1, "0", None), "etiqueta": "preparación"},
    ]
    m = medir("x", "IA1", casos, registros)
    assert (m.casos, m.errores, m.no_ejecutados, m.verdes) == (2, 1, 1, 1)
    assert (m.fallos, m.fallos_min, m.fallos_max, m.avisos) == (2, 2, 2, 1)
    # A: 1 + 3 = 4 s; B: 2 s; C: 0,5 s (sin respuesta). Medio 6,5 / 3, máximo 4.
    assert m.tiempo_max_s == Decimal(4)
    assert m.tiempo_medio_s == Decimal("6.5") / 3
    assert m.llamadas == 4
    # Solo las llamadas con respuesta, con la caché: (300 + 200 + 100) / 3. Una
    # llamada sin respuesta no mide tokens: bajaría la estimación siguiente (R15).
    assert m.tokens_entrada_medios == Decimal(600) / 3
    assert m.tokens_salida_medios == Decimal(50) / 3
    assert m.coste_total == Decimal("0.60")
    # Casos con respuesta: A y B.
    assert m.coste_por_albaran == Decimal("0.30")
    assert m.uso_incompleto == 1
    assert m.modelos_servidos == ["x-1", "x-2"]
    assert m.motivos_parada == {"stop": 3}


def test_f083_r27_media_y_rango_con_varias_repeticiones():
    casos = [[_caso("A", fallos=1)], [_caso("A", fallos=4)], [_caso("A", fallos=2)]]
    m = medir("x", "IA1", casos, [])
    assert m.repeticiones == 3
    assert (m.fallos, m.fallos_min, m.fallos_max) == (Decimal(7) / 3, 1, 4)
    assert m.casos == 3
    assert m.coste_por_albaran == 0 and m.tiempo_medio_s == 0 and m.tiempo_max_s == 0
    assert m.tokens_entrada_medios == 0 and m.tokens_salida_medios == 0


def test_f083_r27_el_mismo_caso_en_dos_repeticiones_son_dos_albaranes():
    casos = [[_caso("A")], [_caso("A")]]
    registros = [_registro("A", 1, "1", 1000), _registro("A", 2, "3", 3000)]
    m = medir("x", "IA1", casos, registros)
    assert m.coste_por_albaran == Decimal(2)
    assert m.tiempo_medio_s == Decimal(2) and m.tiempo_max_s == Decimal(3)


def test_f083_r27_fallo_del_medidor_cuenta_aparte():
    registros = [{"caso_id": "A", "repeticion": 1, "etiqueta": "candidato", "coste_usd": "0",
                  "fallo_medidor": True}]
    m = medir("x", "IA1", [[_caso("A")]], registros)
    assert m.fallos_medidor == 1 and m.llamadas == 1


def test_f083_umbrales_declarados():
    assert decision.BANDA_MINIMA == 2
    assert decision.BANDA_RELATIVA == Decimal("0.05")
    assert decision.EMPATE_COSTE == Decimal("0.05")
    assert decision.MEJORA_FALLOS == Decimal("0.9")
    assert decision.MEJORA_COSTE == Decimal("1.5")
    assert decision.AHORRO_COSTE == Decimal("0.7")
    assert decision.LATENCIA == 2
    assert decision.REPETICIONES_FIRMES == 3
