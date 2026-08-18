# tests/test_f019_r16_r17_feymaco.py
"""F-019 · R16-R17: el albaran Feymaco 2.137.569, linea a linea.

Ferreteria, contrato CTSU24/0454, 40 % de descuento en las cinco lineas.
Total impreso: **139,66 EUR**. En la prueba local del 2026-08-18
(``progress/prueba_local_feymaco_20260818.md``) el pipeline lo valoro en
**6.238,14 EUR**.

Este fichero cubre el tramo sv6 de la cadena: encadena
``PriceReconciler`` (que decide el unitario) con ``ImporteCalculator``
(que decide el importe) partiendo del **importe efectivo que sv5 entrega
tras F-019**, es decir el ``precio_neto`` leido tal cual.

COMENTARIO CRUZADO: la fixture de las cinco lineas se repite, con los
mismos numeros, en la suite de sv5
(``services/albaran-valoracion-api/tests/test_f019_r4_r7_importe_select.py``).
Es deliberado: son los dos tramos de la MISMA cadena y sv5 y sv6 no
pueden importarse en la misma sesion de pytest (paquetes homonimos de
primer nivel). Si estos numeros cambian, hay que cambiarlos en los dos
sitios.

Sin red, sin BBDD, sin LLM: las dos clases son puras.
"""
from __future__ import annotations

import pytest

#: (n, concepto, cantidad, precio declarado, dto %, importe efectivo sv5)
LINEAS_2137569: tuple[tuple[int, str, float, float, float, float], ...] = (
    (1, "PAPEL HIGIENICO (SACO 108)", 108.0, 0.543, 40.0, 35.19),
    (2, "LTS. JABON LIQUIDO PH NEUTRO", 10.0, 3.422, 40.0, 20.53),
    (3, "ROLLO PAPEL IND.", 12.0, 7.726, 40.0, 55.63),
    (4, "KGS ANIL ESPECIAL FEYMACO", 4.0, 5.497, 40.0, 13.19),
    (5, "BOLSA BASURA 52X58", 100.0, 0.252, 40.0, 15.12),
)

#: Total impreso en el albaran.
TOTAL_CORRECTO = 139.66

#: Total que producia el pipeline antes de F-019.
TOTAL_INFLADO = 6238.14

#: Precio de contrato de la linea 1 en el momento de la prueba local.
#: Se pasa a proposito en TODOS los casos: el contrato no debe pisar
#: nada de lo leido.
PRECIO_CONTRATO_RUIDOSO = 4000.0


def _valorar_linea(reconciliador, calculador_importe, linea):
    """Reproduce el tramo sv6: reconcilia el precio y calcula el importe."""
    _, _, cantidad, precio, descuento, importe_efectivo = linea

    reconciliacion = reconciliador.reconcile(
        precio_1a=PRECIO_CONTRATO_RUIDOSO,
        precio_1b=None,
        precio_albaran_declarado=precio,
        cantidad_albaran=cantidad,
        importe_albaran=importe_efectivo,
        line_already_valued=False,
        descuento_pct=descuento,
    )
    importe = calculador_importe.compute(
        cantidad_convertida=cantidad,
        cantidad_albaran=cantidad,
        precio_unitario_final=reconciliacion.final_price,
        importe_albaran_declarado=importe_efectivo,
        descuento_pct=descuento,
    )
    return reconciliacion, importe


@pytest.mark.parametrize(
    "linea", LINEAS_2137569, ids=[linea[1] for linea in LINEAS_2137569]
)
def test_f019_r16_cada_linea_conserva_su_unitario_y_su_importe(
    reconciliador, calculador_importe, linea,
):
    """Cada linea sale con el unitario y el importe del papel."""
    numero, concepto, cantidad, precio, _, importe_efectivo = linea
    reconciliacion, importe = _valorar_linea(
        reconciliador, calculador_importe, linea,
    )

    assert reconciliacion.final_price == pytest.approx(precio), concepto
    assert reconciliacion.source == "albaran_declared", concepto
    assert importe.importe_calculado == pytest.approx(importe_efectivo), (
        f"linea {numero} ({concepto})"
    )
    # El precio del contrato (4.000 EUR/ud) no entra por ningun lado.
    assert reconciliacion.final_price != pytest.approx(
        PRECIO_CONTRATO_RUIDOSO
    )
    assert importe.importe_calculado < cantidad * PRECIO_CONTRATO_RUIDOSO


def test_f019_r16_el_total_del_albaran_es_13966_euros(
    reconciliador, calculador_importe,
):
    """La suma de las cinco lineas: 139,66 EUR, no 6.238,14 EUR."""
    importes = [
        _valorar_linea(reconciliador, calculador_importe, linea)[1]
        .importe_calculado
        for linea in LINEAS_2137569
    ]

    total = round(sum(importes), 2)
    assert total == pytest.approx(TOTAL_CORRECTO)
    assert total != pytest.approx(TOTAL_INFLADO)


def test_f019_r17_el_derivado_confirma_al_declarado_sin_marcar_revision(
    reconciliador, calculador_importe,
):
    """Corregido el importe efectivo, el punto 2 de la cadena cuadra solo.

    Linea 1: 35,19 / (108 x 0,6) = 0,543055..., que frente al declarado
    0,543 son 0,010 % de diferencia — muy dentro de PRICE_TOLERANCE_PCT
    (2 %). Por tanto ``agreement != "mismatch"`` y la linea NO va a
    revision por este motivo.
    """
    linea = LINEAS_2137569[0]
    _, _, cantidad, precio, descuento, importe_efectivo = linea

    derivado = importe_efectivo / (cantidad * (1 - descuento / 100))
    assert derivado == pytest.approx(0.543055, abs=1e-6)

    reconciliacion, _ = _valorar_linea(
        reconciliador, calculador_importe, linea,
    )

    assert reconciliacion.agreement != "mismatch"
    assert reconciliacion.final_price == pytest.approx(precio)
    assert "albaran_unitario_manda_derivado_coincide" in reconciliacion.reasons


def test_f019_r17_ninguna_linea_queda_marcada_por_mismatch(
    reconciliador, calculador_importe,
):
    """Equivalente unitario del punto 3 de la verificacion MANUAL: en
    ``albaran_valuation_lines`` no debe quedar
    ``unitario_declarado_vs_derivado_mismatch`` en ``review_reasons``."""
    for linea in LINEAS_2137569:
        reconciliacion, _ = _valorar_linea(
            reconciliador, calculador_importe, linea,
        )

        assert reconciliacion.agreement != "mismatch", linea[1]
        assert not [
            motivo for motivo in reconciliacion.reasons
            if motivo.startswith("unitario_declarado_vs_derivado_mismatch")
        ], linea[1]


def test_f019_r16_con_el_importe_inflado_la_linea_1_habria_ido_a_revision(
    reconciliador, calculador_importe,
):
    """Contraprueba: si sv5 volviera a inflar el importe (108 x 35,19),
    el unitario leido seguiria mandando —ya no se fabrica el 58,65— y
    ademas la linea saldria marcada para revision."""
    reconciliacion = reconciliador.reconcile(
        precio_1a=PRECIO_CONTRATO_RUIDOSO,
        precio_1b=None,
        precio_albaran_declarado=0.543,
        cantidad_albaran=108.0,
        importe_albaran=108.0 * 35.19,
        line_already_valued=False,
        descuento_pct=40.0,
    )

    assert reconciliacion.final_price == pytest.approx(0.543)
    assert reconciliacion.agreement == "mismatch"
