# tests/test_f019_r23_formula_canonica.py
"""F-019 · R23: una sola formula del importe en todo sv4.

El defecto del round trip 2 no fue un despiste aislado: la formula
``cantidad x precio`` estaba escrita CUATRO veces en
``review_repository.py`` y solo UNA de las cuatro aplicaba el descuento.
Arreglar la copia culpable y dejar las otras tres habria repetido el
incidente con otro boton del front.

Este fichero vigila las dos mitades de R23:

  1. que la formula canonica (``_importe_de_linea``) sea correcta;
  2. que NADIE en el modulo vuelva a multiplicar precio por cantidad por
     su cuenta — el guardian estructural del final.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from infrastructure.database.review_repository import (
    _importe_de_linea,
    _sanear_descuento,
)


# ------------------------------------------------------------------ #
# La formula
# ------------------------------------------------------------------ #
def test_f019_r23_la_formula_aplica_el_descuento():
    """La linea del incidente: 108 x 0,543 con 40 % = 35,19 EUR."""
    assert _importe_de_linea(
        precio_unitario=0.543, cantidad=108.0, descuento_pct=40.0
    ) == pytest.approx(35.19)


def test_f019_r23_la_formula_sin_descuento_es_cantidad_por_precio():
    assert _importe_de_linea(
        precio_unitario=0.543, cantidad=108.0, descuento_pct=None
    ) == pytest.approx(58.64)


@pytest.mark.parametrize(
    ("precio", "cantidad"),
    [(None, 10.0), (2.5, None), (None, None)],
)
def test_f019_r23_sin_precio_o_sin_cantidad_no_hay_importe(precio, cantidad):
    assert (
        _importe_de_linea(
            precio_unitario=precio, cantidad=cantidad, descuento_pct=40.0
        )
        is None
    )


def test_f019_r23_el_importe_se_redondea_a_dos_decimales():
    # 108 x 0,543 x 0,6 = 35.1864
    assert _importe_de_linea(
        precio_unitario=0.543, cantidad=108.0, descuento_pct=40.0
    ) == 35.19


def test_f019_r23_descuento_del_100_deja_la_linea_a_cero():
    """100 % es un descuento legitimo: la linea no se cobra."""
    assert _importe_de_linea(
        precio_unitario=5.0, cantidad=3.0, descuento_pct=100.0
    ) == 0.0


@pytest.mark.parametrize("descuento", [-5.0, 100.1, 1000.0])
def test_f019_r23_descuento_fuera_de_rango_se_ignora(descuento):
    """Igual que ``ImporteCalculator._sanitize_descuento`` en sv6."""
    assert _sanear_descuento(descuento) is None
    assert _importe_de_linea(
        precio_unitario=5.0, cantidad=3.0, descuento_pct=descuento
    ) == pytest.approx(15.0)


@pytest.mark.parametrize("descuento", [None, 0.0, "no es un numero"])
def test_f019_r23_descuento_ausente_o_ilegible_no_descuenta(descuento):
    assert _sanear_descuento(descuento) is None


def test_f019_r23_el_descuento_en_rango_si_se_aplica():
    assert _sanear_descuento(40.0) == pytest.approx(40.0)
    assert _sanear_descuento(0.5) == pytest.approx(0.5)


@pytest.mark.parametrize(
    ("precio", "cantidad"),
    [("no es un numero", 10.0), (2.5, "tampoco"), (object(), 3.0)],
)
def test_f019_r23_un_valor_ilegible_no_produce_importe(precio, cantidad):
    """Basura en la columna no se convierte en un importe inventado.

    La BBDD guarda estos campos como DOUBLE PRECISION, pero el importe
    es dinero: ante un valor que no se puede multiplicar, la respuesta
    correcta es «no hay importe», no un numero cualquiera ni una
    excepcion que tumbe el guardado del revisor.
    """
    assert (
        _importe_de_linea(
            precio_unitario=precio, cantidad=cantidad, descuento_pct=None
        )
        is None
    )


# ------------------------------------------------------------------ #
# La comparacion que decide si una fila cambia (R24)
# ------------------------------------------------------------------ #
def _iguales(a, b):
    from infrastructure.database.review_repository import (
        AlbaranReviewRepository,
    )

    return AlbaranReviewRepository._num_iguales(a, b)


def test_f019_r24_dos_nulos_son_iguales():
    assert _iguales(None, None) is True


@pytest.mark.parametrize(("a", "b"), [(None, 1.0), (1.0, None)])
def test_f019_r24_un_nulo_frente_a_un_numero_no_lo_es(a, b):
    assert _iguales(a, b) is False


def test_f019_r24_el_ruido_binario_no_cuenta_como_cambio():
    """35.19 y 35.190000000000005 son el mismo importe."""
    assert _iguales(35.19, 35.190000000000005) is True


def test_f019_r24_medio_centimo_ya_es_un_cambio():
    assert _iguales(35.19, 35.20) is False


def test_f019_r24_un_valor_ilegible_cuenta_como_cambio():
    """Ante un valor que no se puede comparar, se reescribe la fila.

    Preferimos recalcular de mas que dejar basura persistida.
    """
    assert _iguales("no es un numero", 35.19) is False


# ------------------------------------------------------------------ #
# El guardian estructural
# ------------------------------------------------------------------ #
#: Multiplicacion suelta de un precio por una cantidad. Cualquier
#: variante de ``float(precio_algo) * float(cantidad_algo)``.
_MULTIPLICACION_SUELTA = re.compile(
    r"float\(\s*[\w\.\[\]\"']*(?:precio|pu|importe_unit)[\w\.\[\]\"']*\s*\)"
    r"\s*\*\s*"
    r"float\(\s*[\w\.\[\]\"']*(?:cantidad|cant)[\w\.\[\]\"']*\s*\)",
    re.IGNORECASE,
)


def test_f019_r23_nadie_multiplica_precio_por_cantidad_fuera_de_la_formula():
    """Guardian: el importe de una linea se pide a ``_importe_de_linea``.

    Este test es la red que faltaba. El fallo de produccion del
    2026-08-18 fue exactamente esto: tres copias de la formula sin el
    factor del descuento repartidas por el fichero. Si alguien vuelve a
    escribir la multiplicacion a mano, se entera aqui y no en la BBDD.

    Si el aviso es un falso positivo, la solucion NO es relajar el
    patron: es llamar a ``_importe_de_linea``, que hace lo mismo y ademas
    bien.
    """
    modulo = (
        Path(__file__).resolve().parents[1]
        / "infrastructure"
        / "database"
        / "review_repository.py"
    )
    lineas = modulo.read_text(encoding="utf-8").splitlines()

    # La unica multiplicacion legitima vive dentro de la propia formula:
    # se excluye su cuerpo, desde su ``def`` hasta el siguiente nivel
    # superior (``def`` o ``class`` sin indentar).
    dentro_de_la_formula: set[int] = set()
    en_la_formula = False
    for numero, linea in enumerate(lineas, start=1):
        if linea.startswith("def _importe_de_linea"):
            en_la_formula = True
        elif en_la_formula and linea[:1] not in ("", " ", "\t", ")"):
            en_la_formula = False
        if en_la_formula:
            dentro_de_la_formula.add(numero)
    assert dentro_de_la_formula, "no se encontro _importe_de_linea en el modulo"

    culpables = [
        (numero, linea.strip())
        for numero, linea in enumerate(lineas, start=1)
        if _MULTIPLICACION_SUELTA.search(linea)
        and numero not in dentro_de_la_formula
    ]

    assert not culpables, (
        "multiplicacion precio x cantidad fuera de _importe_de_linea "
        f"(se pierde el descuento): {culpables}"
    )


def test_f019_r23_el_guardian_detecta_de_verdad_el_patron():
    """Prueba de control: sin esto, el guardian podria ser un adorno.

    Un test que solo comprueba «no hay coincidencias» pasa igual con un
    patron roto. Aqui se verifica que el patron SI reconoce la linea
    exacta que habia en el codigo antes del fix.
    """
    linea_del_bug = (
        "            nuevo_importe = round(float(pu) * float(cantidad_efectiva), 2)"
    )
    assert _MULTIPLICACION_SUELTA.search(linea_del_bug)

    otra_del_bug = "                base = float(new_precio) * float(new_cantidad)"
    assert _MULTIPLICACION_SUELTA.search(otra_del_bug)
