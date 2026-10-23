# tests/test_f084_tolerancia_importes.py
"""F-084 · R37 — tolerancia de céntimos en los importes y precios valorados.

Decisión del humano del 2026-10-23 (opción a): el libro anota el importe del
papel en céntimos y sv6 no redondea cuando INPUTS no trae el importe de la
línea, así que el banco tolera 0,05 € en los importes y precios VALORADOS. La
lectura de IA1 (`lineas.importe`, `lineas.precio_unitario`) sigue exacta.

Sin red ni BBDD (R25): el comparador es puro y el determinista usa el
subproceso de sv6 sin llamadas.
"""

from __future__ import annotations

import pytest

from evals import comparador, runner
from evals.conversor import RUTA_FIXTURES
from evals.criticidad import cargar_criticidad

_TOLERADOS = [
    "IA3.lineas_valoradas[1].importe_calculado",
    "IA3.lineas_valoradas[1].precio_unitario_final",
    "FINAL.lineas[1].importe_final",
    "FINAL.lineas[1].precio_unitario_final",
    "FINAL.datos_generales[].total_valorado_esperado",
    "FINAL.lineas_anadidas[1/P5.03.09].importe",
]


def test_f084_r37_la_tolerancia_es_de_cinco_centimos():
    assert comparador.TOLERANCIA_IMPORTE_EUR == 0.05


@pytest.mark.parametrize("campo", _TOLERADOS)
def test_f084_r37_el_redondeo_al_centimo_no_es_un_fallo(campo):
    assert comparador.equivalentes_en(campo, 17.59, 17.5932)
    assert comparador.equivalentes_en(campo, 17.5932, 17.59)


def test_f084_r37_el_total_de_fer_002_con_un_centimo_de_diferencia_pasa():
    assert comparador.equivalentes_en(
        "FINAL.datos_generales[].total_valorado_esperado", 139.65, 139.66
    )


@pytest.mark.parametrize("campo", _TOLERADOS)
def test_f084_r37_once_centimos_siguen_siendo_un_fallo(campo):
    assert not comparador.equivalentes_en(campo, 17.59, 17.70)


@pytest.mark.parametrize("campo", _TOLERADOS)
def test_f084_r37_el_limite_entra_y_un_centimo_mas_no(campo):
    assert comparador.equivalentes_en(campo, 17.59, 17.64)
    assert comparador.equivalentes_en(campo, "17,59", "17,64")
    assert not comparador.equivalentes_en(campo, 17.59, 17.65)
    assert not comparador.equivalentes_en(campo, 17.59, 17.53)


@pytest.mark.parametrize("campo", [
    "IA1.lineas[1].importe",
    "IA1.lineas[1].precio_unitario",
    "IA3.sinteticas_esperadas[1/x].precio_unitario",
    "IA4.conciliacion[1].precio_unitario_esperado",
    "IA3.lineas_valoradas[1].cantidad",
    "FINAL.lineas[1].importe",
])
def test_f084_r37_fuera_de_los_valorados_la_comparacion_sigue_exacta(campo):
    assert not comparador.equivalentes_en(campo, 17.59, 17.5932)


def test_f084_r37_un_valor_ausente_sigue_siendo_un_fallo():
    campo = "IA3.lineas_valoradas[1].importe_calculado"
    assert not comparador.equivalentes_en(campo, 17.59, None)
    assert not comparador.equivalentes_en(campo, 17.59, "no es un número")


def test_f084_r37_comparar_aplica_la_tolerancia_campo_a_campo():
    criticidad = cargar_criticidad()
    discrepancias = comparador.comparar(
        {"importe_calculado": 17.59, "cantidad": 54},
        {"importe_calculado": 17.5932, "cantidad": 54.004},
        criticidad,
        "IA3.lineas_valoradas[1]",
    )
    assert [d.campo for d in discrepancias] == ["IA3.lineas_valoradas[1].cantidad"]


def test_f084_r37_el_determinista_de_fer_002_y_fer_003_no_falla_por_redondeo():
    fases, _ = runner.corrida_determinista(RUTA_FIXTURES, ["FER-002", "FER-003"])

    for fase in fases:
        for caso in fase.casos:
            for fallo in caso.fallos:
                try:
                    diferencia = abs(float(fallo.esperado) - float(fallo.obtenido))
                except (TypeError, ValueError):
                    continue
                assert diferencia > comparador.TOLERANCIA_IMPORTE_EUR, fallo.descripcion()
