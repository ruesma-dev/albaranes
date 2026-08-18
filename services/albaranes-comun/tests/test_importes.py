# tests/test_importes.py
"""F-019 · la formula canonica del importe, compartida por sv4 y sv6.

Vive en ruesma_comun porque la escriben DOS servicios. Estos tests son
el contrato que los dos consumen: si cambian aqui, cambian en los dos a
la vez, que es exactamente lo que no ocurria cuando cada uno tenia su
copia (ver la cabecera de ruesma_comun/importes.py).

Funcion pura: sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest

from ruesma_comun.importes import (
    clasificar_descuento,
    factor_descuento,
    importe_de_linea,
)


# ------------------------------------------------------------------ #
# La formula
# ------------------------------------------------------------------ #
def test_la_linea_del_incidente_feymaco():
    """108 ud x 0,543 EUR con 40 % = 35,19 EUR.

    Sin el descuento salen 58,64: el numero que aparecio en la BBDD el
    2026-08-18 y que costo dos round trips.
    """
    assert importe_de_linea(
        cantidad=108.0, precio_unitario=0.543, descuento_pct=40.0
    ) == pytest.approx(35.19)


def test_sin_descuento_es_cantidad_por_precio():
    assert importe_de_linea(
        cantidad=108.0, precio_unitario=0.543
    ) == pytest.approx(58.64)


def test_el_importe_se_redondea_a_dos_decimales():
    # 108 x 0,543 x 0,6 = 35.1864
    assert importe_de_linea(
        cantidad=108.0, precio_unitario=0.543, descuento_pct=40.0
    ) == 35.19


def test_el_descuento_del_100_deja_la_linea_a_cero():
    """100 % es un descuento legitimo: la linea no se cobra."""
    assert importe_de_linea(
        cantidad=3.0, precio_unitario=5.0, descuento_pct=100.0
    ) == 0.0


@pytest.mark.parametrize(
    ("cantidad", "precio"),
    [(None, 1.0), (1.0, None), (None, None)],
)
def test_sin_cantidad_o_sin_precio_no_hay_importe(cantidad, precio):
    assert (
        importe_de_linea(
            cantidad=cantidad, precio_unitario=precio, descuento_pct=40.0
        )
        is None
    )


@pytest.mark.parametrize(
    ("cantidad", "precio"),
    [("x", 1.0), (1.0, "x"), (object(), 1.0), (1.0, object())],
)
def test_un_valor_ilegible_no_produce_importe_ni_excepcion(cantidad, precio):
    """Basura en el dato no se convierte en un importe inventado.

    Ni tumba el proceso: al otro lado hay una valoracion por cola y el
    guardado de un revisor.
    """
    assert (
        importe_de_linea(cantidad=cantidad, precio_unitario=precio) is None
    )


def test_un_texto_numerico_si_vale():
    """El dato puede llegar como texto desde el JSON de una IA."""
    assert importe_de_linea(
        cantidad="10", precio_unitario="2.5", descuento_pct="40"
    ) == pytest.approx(15.0)


# ------------------------------------------------------------------ #
# La clasificacion del descuento
# ------------------------------------------------------------------ #
def test_descuento_ausente():
    assert clasificar_descuento(None) == ("ausente", None)


def test_descuento_cero_consta_pero_no_descuenta():
    """'El albaran dice 0 %' no es lo mismo que 'el albaran no dice nada'.

    Cada servicio persiste una cosa distinta en cada caso, asi que la
    distincion no puede perderse aqui.
    """
    assert clasificar_descuento(0.0) == ("cero", 0.0)
    assert factor_descuento(0.0) == 1.0


@pytest.mark.parametrize("valor", [40.0, 0.5, 100.0])
def test_descuento_aplicable(valor):
    estado, normalizado = clasificar_descuento(valor)
    assert estado == "aplicable"
    assert normalizado == pytest.approx(valor)


@pytest.mark.parametrize("valor", [-5.0, 100.1, 1000.0])
def test_descuento_fuera_de_rango_es_invalido_y_conserva_el_valor_leido(valor):
    """Se devuelve el numero leido: hace falta para dejar traza de que llego."""
    estado, normalizado = clasificar_descuento(valor)
    assert estado == "invalido"
    assert normalizado == pytest.approx(valor)
    assert factor_descuento(valor) == 1.0


@pytest.mark.parametrize("valor", ["no es un numero", object(), float("nan")])
def test_descuento_ilegible_es_invalido_sin_valor(valor):
    """Incluido NaN, que se cuela por comparaciones y no lanza nada."""
    assert clasificar_descuento(valor) == ("invalido", None)
    assert factor_descuento(valor) == 1.0


@pytest.mark.parametrize("valor", [-5.0, 150.0, "x", None])
def test_un_descuento_no_aplicable_nunca_da_importe_negativo(valor):
    importe = importe_de_linea(
        cantidad=3.0, precio_unitario=5.0, descuento_pct=valor
    )
    assert importe == pytest.approx(15.0)
    assert importe > 0
