# tests/test_evals_normalizacion_numero_partida.py
"""Corrector de evals · número de albarán y partida comparados normalizados.

Chore del banco de IA1 (2026-10-22). La T14 de F-083 dejó el número de
albarán a «?» casi en todo el libro porque el humano escribe el código sin el
prefijo de serie y el papel lo trae con él («0000168» en la tabla,
«SS-0000168» impreso). Compararlo tal cual daba rojos falsos; no compararlo
escondía los fallos de verdad (FER-001: leído 2139543, real 2139643).

- `numero_albaran`: solo dígitos, sin ceros a la izquierda.
- `codigo_imputacion` (la partida que lee IA1): mayúsculas y sin ceros a la
  izquierda en cada segmento, «CI.04.18» ≡ «CI.4.18». Además es LAXA en IA1:
  el aviso enseña cuántas partidas salen mal sin tumbar el caso.
- `proveedor_nombre` es LAXO: en producción el nombre lo pone sv3 desde Sigrid
  (F-062/F-063/F-073); el CIF sigue siendo crítico.
"""

import pytest

from evals.comparador import (
    comparar,
    normalizar_numero_albaran,
    normalizar_partida,
)
from evals.criticidad import cargar_criticidad


@pytest.fixture(scope="module")
def criticidad():
    return cargar_criticidad()


# --- Número de albarán ------------------------------------------------------


@pytest.mark.parametrize(
    "valor, normalizado",
    [
        ("SS-0000168", "168"),
        ("0000168", "168"),
        ("168", "168"),
        (168, "168"),
        (168.0, "168"),
        ("2.115.714", "2115714"),
        ("2026/01/007378", "202601007378"),
        ("H132525", "132525"),
        ("0", "0"),
        ("SIN NUMERO", None),
    ],
)
def test_evals_numero_albaran_se_normaliza_a_digitos_sin_ceros(valor, normalizado):
    assert normalizar_numero_albaran(valor) == normalizado


def test_evals_numero_albaran_con_prefijo_o_ceros_es_el_mismo(criticidad):
    esperado = {"numero_albaran": "0000168"}

    assert comparar(esperado, {"numero_albaran": "SS-0000168"}, criticidad) == []
    assert comparar(esperado, {"numero_albaran": "168"}, criticidad) == []
    assert comparar({"numero_albaran": "2.115.714"}, {"numero_albaran": "2115714"}, criticidad) == []


def test_evals_numero_albaran_mal_leido_sigue_siendo_fallo_critico(criticidad):
    """El caso FER-001: un dígito cambiado es un fallo, no ruido."""
    discrepancias = comparar(
        {"numero_albaran": "2139643"}, {"numero_albaran": "2.139.543"}, criticidad
    )

    assert [(d.campo, d.severidad) for d in discrepancias] == [("numero_albaran", "fallo")]


def test_evals_numero_albaran_no_leido_es_fallo(criticidad):
    discrepancias = comparar({"numero_albaran": "2139643"}, {"numero_albaran": None}, criticidad)

    assert [d.severidad for d in discrepancias] == ["fallo"]


def test_evals_numero_albaran_sin_digitos_se_compara_como_texto(criticidad):
    assert comparar({"numero_albaran": "ABC"}, {"numero_albaran": "abc"}, criticidad) == []
    assert len(comparar({"numero_albaran": "ABC"}, {"numero_albaran": "ABD"}, criticidad)) == 1


def test_evals_numero_albaran_se_normaliza_tambien_dentro_de_una_tabla(criticidad):
    """El camino real del informe: `IA1.cabeceras[...]numero_albaran`."""
    esperado = {"cabeceras": [{"numero_albaran": "0003935"}]}
    obtenido = {"cabeceras": [{"numero_albaran": "SS-0003935"}]}

    assert comparar(esperado, obtenido, criticidad) == []


# --- Partida (codigo_imputacion) --------------------------------------------


@pytest.mark.parametrize(
    "valor, normalizado",
    [
        ("CI.04.18", "CI.4.18"),
        ("CI.4.18", "CI.4.18"),
        ("ci.04.18", "CI.4.18"),
        ("P5.22.01.03.07", "P5.22.1.3.7"),
        ("CI.03A.7", "CI.3A.7"),
        (" P4.03.05 ", "P4.3.5"),
        ("05.00", "5.0"),
        (5.01, "5.1"),
        ("16.01.", "16.1."),
    ],
)
def test_evals_partida_se_normaliza_por_segmento(valor, normalizado):
    assert normalizar_partida(valor) == normalizado


def test_evals_partida_con_ceros_o_minusculas_es_la_misma(criticidad):
    esperado = {"codigo_imputacion": "CI.4.18"}

    assert comparar(esperado, {"codigo_imputacion": "CI.04.18"}, criticidad) == []
    assert comparar(esperado, {"codigo_imputacion": "ci.4.18"}, criticidad) == []


def test_evals_partida_distinta_en_ia1_es_aviso_no_fallo(criticidad):
    discrepancias = comparar(
        {"codigo_imputacion": "P5.22.01.03.07"}, {"codigo_imputacion": "22.01.03.07"}, criticidad
    )

    assert [(d.campo, d.severidad) for d in discrepancias] == [("codigo_imputacion", "aviso")]


def test_evals_la_normalizacion_de_partida_no_toca_la_partida_final(criticidad):
    """Solo la lectura de IA1 se relaja; la partida valorada sigue exigiéndose exacta."""
    discrepancias = comparar(
        {"codigo_partida_final": "CI.4.18"}, {"codigo_partida_final": "CI.04.18"}, criticidad
    )

    assert [d.severidad for d in discrepancias] == ["fallo"]


# --- Criticidad del proveedor ----------------------------------------------


def test_evals_proveedor_nombre_es_laxo_y_el_cif_critico(criticidad):
    assert criticidad.severidad("IA1.cabeceras[].proveedor_nombre") == "aviso"
    assert criticidad.severidad("IA1.cabeceras[].proveedor_cif") == "fallo"
    assert criticidad.clasificar("proveedor_nombre").regla == "ajuste 'laxos'"


def test_evals_codigo_imputacion_es_laxo(criticidad):
    assert criticidad.severidad("IA1.lineas[1].codigo_imputacion") == "aviso"
    assert criticidad.clasificar("codigo_imputacion").regla == "ajuste 'laxos'"
