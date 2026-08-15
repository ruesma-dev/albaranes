# tests/test_f003_descuento_cascada.py
"""F-003 · Descuento efectivo en cascada, determinista (R3).

La IA transcribe TODAS las columnas de descuento (DTO1, DTO2...) y jamas
las combina: combinar es aritmetica, y la aritmetica la hace codigo
determinista, no un modelo. Aqui vive esa aritmetica.

Formula: (1 - PROD(1 - di/100)) x 100. Dos descuentos del 10 % no son un
20 %: son un 19 %.

Sin red ni BBDD: funcion pura.
"""
from __future__ import annotations

import pytest

from application.services.descuento_cascada import (
    descuento_efectivo,
    resolver_descuento,
)


# ---------------------------------------------------------------------
# R3 · La cascada
# ---------------------------------------------------------------------


def test_f003_r3_dos_descuentos_iguales_no_se_suman() -> None:
    """10 % y 10 % = 19 %, no 20 %."""
    assert descuento_efectivo([10.0, 10.0]) == pytest.approx(19.0)


def test_f003_r3_cascada_de_tres_descuentos() -> None:
    # 1 - 0.95*0.98*0.99 = 1 - 0.92169 = 0.07831
    assert descuento_efectivo([5.0, 2.0, 1.0]) == pytest.approx(7.831, abs=1e-4)


def test_f003_r3_un_solo_descuento_se_devuelve_tal_cual() -> None:
    assert descuento_efectivo([12.5]) == pytest.approx(12.5)


def test_f003_r3_sin_descuentos_el_efectivo_es_cero() -> None:
    assert descuento_efectivo([]) == 0.0


def test_f003_r3_los_ceros_no_alteran_la_cascada() -> None:
    assert descuento_efectivo([0.0, 5.0, 0.0]) == pytest.approx(5.0)


def test_f003_r3_los_nulos_se_ignoran() -> None:
    """Una columna de descuento vacia no es un descuento del 0 %: no
    existe, y en cualquier caso no altera el producto."""
    assert descuento_efectivo([5.0, None, 2.0]) == pytest.approx(6.9)


def test_f003_r3_el_efectivo_se_redondea_a_cuatro_decimales() -> None:
    valor = descuento_efectivo([3.33, 3.33])
    assert valor == round(valor, 4)


def test_f003_r3_un_descuento_del_cien_por_cien_anula_la_linea() -> None:
    assert descuento_efectivo([100.0, 10.0]) == pytest.approx(100.0)


def test_f003_r3_el_orden_de_los_descuentos_no_cambia_el_resultado() -> None:
    """El producto es conmutativo: dos lecturas del mismo documento con
    las columnas en distinto orden dan el mismo efectivo."""
    assert descuento_efectivo([5.0, 2.0]) == pytest.approx(
        descuento_efectivo([2.0, 5.0])
    )


def test_f003_r3_valores_no_numericos_se_ignoran() -> None:
    assert descuento_efectivo(["", "5"]) == pytest.approx(5.0)


# ---------------------------------------------------------------------
# R3 · Cuando se aplica la derivacion (y cuando NO)
# ---------------------------------------------------------------------


def test_f003_r3_con_varios_descuentos_y_descuento_nulo_se_deriva() -> None:
    assert resolver_descuento(None, [5.0, 2.0]) == pytest.approx(6.9)


def test_f003_r3_un_descuento_leido_manda_sobre_la_derivacion() -> None:
    """Si la IA transcribio el descuento unico, se respeta: transcribir
    manda sobre calcular."""
    assert resolver_descuento(7.0, [5.0, 2.0]) == pytest.approx(7.0)


def test_f003_r3_con_una_sola_columna_no_hay_nada_que_derivar() -> None:
    assert resolver_descuento(None, [5.0]) == pytest.approx(5.0)


def test_f003_r3_sin_lista_de_descuentos_se_respeta_lo_que_haya() -> None:
    assert resolver_descuento(None, None) is None
    assert resolver_descuento(3.0, None) == pytest.approx(3.0)


def test_f003_r3_lista_vacia_no_inventa_un_descuento() -> None:
    assert resolver_descuento(None, []) is None


def test_f003_r3_descuento_cero_leido_no_se_pisa_con_la_cascada() -> None:
    """0.0 es un descuento LEIDO, no un hueco: no dispara la derivacion."""
    assert resolver_descuento(0.0, [5.0, 2.0]) == pytest.approx(0.0)
