# tests/test_f019_r27_formula_compartida.py
"""F-019 R27 · sv6 usa la formula canonica de ruesma_comun, no una copia.

Round trip 3 (2026-08-18). El reviewer senalo que, una vez unificada la
formula DENTRO de sv4, seguian existiendo dos copias ENTRE servicios
—``ImporteCalculator`` en sv6 y ``_importe_de_linea`` en sv4— y que
CLAUDE.md (LIMITE DE SERVICIO) lo prohibe: «la logica compartida va a
services/albaranes-comun, nunca copiada entre servicios».

Y no era teorico: las dos copias YA divergian en como trataban un
descuento ilegible (sv4 devolvia None, sv6 reventaba con ValueError).

Estos tests fijan que sv6 CONSUME la funcion compartida y que conserva
su POLITICA propia encima (el motivo auditable, el 0 explicito y la
precedencia del declarado, que no se mueven a comun).

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest

from ruesma_comun.importes import importe_de_linea


def test_f019_r27_sv6_no_tiene_su_propia_formula():
    """El modulo de sv6 usa la funcion de comun, no una homonima suya.

    Identidad, no igualdad: si alguien vuelve a escribir la formula aqui
    dentro, este test cae aunque la copia sea correcta el primer dia.
    """
    from application.services import importe_calculator

    assert importe_calculator.importe_de_linea is importe_de_linea


@pytest.mark.parametrize(
    ("cantidad", "precio", "descuento", "esperado"),
    [
        (108.0, 0.543, 40.0, 35.19),
        (50.0, 0.647, 40.0, 19.41),
        (10.0, 2.5, None, 25.0),
        (3.0, 5.0, 100.0, 0.0),
    ],
)
def test_f019_r27_el_importe_de_sv6_coincide_con_el_de_comun(
    calculador_importe, cantidad, precio, descuento, esperado,
):
    """Lo que calcula sv6 es exactamente lo que da la formula compartida."""
    resultado = calculador_importe.compute(
        cantidad_convertida=cantidad,
        precio_unitario_final=precio,
        importe_albaran_declarado=None,
        descuento_pct=descuento,
    )

    assert resultado.importe_calculado == pytest.approx(esperado)
    assert resultado.importe_calculado == importe_de_linea(
        cantidad=cantidad, precio_unitario=precio, descuento_pct=descuento,
    )


def test_f019_r27_un_descuento_ilegible_ya_no_revienta(calculador_importe):
    """Antes lanzaba ValueError en mitad de una valoracion por cola.

    ``float('x')`` sin proteger. Ahora el descuento se ignora, la linea
    se valora sin el y queda la traza de que llego algo ilegible.
    """
    resultado = calculador_importe.compute(
        cantidad_convertida=10.0,
        precio_unitario_final=2.5,
        importe_albaran_declarado=None,
        descuento_pct="no es un numero",  # type: ignore[arg-type]
    )

    assert resultado.importe_calculado == pytest.approx(25.0)
    assert any(
        r.startswith("descuento_fuera_de_rango_ignorado")
        for r in resultado.reasons
    )


def test_f019_r27_sv6_conserva_su_politica_del_cero_explicito(
    calculador_importe,
):
    """El 0 % del albaran se persiste como 0, no como NULL.

    Es POLITICA de sv6 y por eso NO se movio a comun: sv4 persiste NULL
    en el mismo caso. `comun` decide los rangos; cada servicio decide
    que guarda.
    """
    resultado = calculador_importe.compute(
        cantidad_convertida=10.0,
        precio_unitario_final=2.5,
        importe_albaran_declarado=None,
        descuento_pct=0.0,
    )

    assert resultado.descuento_aplicado == 0.0
    assert resultado.importe_calculado == pytest.approx(25.0)


def test_f019_r27_un_precio_ilegible_no_revienta_la_valoracion(
    calculador_importe,
):
    """Mismo criterio para la cantidad y el precio: se degrada, no se cae.

    Con importe declarado, la linea se salva con el declarado; es la
    misma rama que ya existia para cantidad o precio ausentes.
    """
    resultado = calculador_importe.compute(
        cantidad_convertida="ilegible",  # type: ignore[arg-type]
        precio_unitario_final=2.5,
        importe_albaran_declarado=30.0,
    )

    assert resultado.importe_calculado == pytest.approx(30.0)
    assert resultado.importe_source == "declared_albaran"
    assert "no_calc_possible_using_declared" in resultado.reasons


def test_f019_r27_la_precedencia_del_declarado_sigue_siendo_de_sv6(
    calculador_importe,
):
    """Regresion: mover la aritmetica a comun no mueve la politica.

    Declarado 100,00 frente a un calculo de 60,00: manda el declarado y
    queda el motivo de revision. Es la regla de jul 2026 y es de sv6.
    """
    resultado = calculador_importe.compute(
        cantidad_convertida=100.0,
        precio_unitario_final=1.0,
        importe_albaran_declarado=100.0,
        descuento_pct=40.0,
    )

    assert resultado.importe_calculado == pytest.approx(100.0)
    assert resultado.importe_source == "declared_albaran"
    assert any(
        r.startswith("declared_vs_calculated_mismatch")
        for r in resultado.reasons
    )
