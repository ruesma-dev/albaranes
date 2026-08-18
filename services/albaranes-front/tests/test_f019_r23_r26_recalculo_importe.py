# tests/test_f019_r23_r26_recalculo_importe.py
"""F-019 · R23-R26: sv4 no puede pisar el importe que escribio sv6.

El fallo, medido (round trip 2, 2026-08-18)
-------------------------------------------
Con la rama de F-019 ya en ejecucion, sv5 y sv6 valoraron el albaran
Feymaco 2.137.569 CORRECTAMENTE: cinco lineas a 35,19 / 20,53 / 55,63 /
13,19 / 15,12 EUR, ``importe_source='declared_albaran'``, total
139,66 EUR. Seis minutos despues, el revisor guardo el documento desde
el front y ``albaran_valuations.updated_at_utc`` paso de 13:24:26 a
13:30:31 con estos valores:

    total_valorado          232,76   (= 58,64+34,22+92,71+21,99+25,20)
    importe_calculado        58,64   (= 108 x 0,543, SIN el 40 % de dto)
    importe_source       calculated  (era 'declared_albaran')
    descuento_albaran_aplicado  40   (intacto: el UPDATE no lo toca)

La contradiccion aparente —descuento 40 registrado y no aplicado— es la
firma del culpable: ``_recalc_valuation_importes`` reescribe importe y
fuente pero no toca ni el descuento ni los motivos, que siguen siendo
los que dejo sv6. El albaran 2.139.643 se salvo por no haberse abierto
en el front: conserva 19,41 EUR y ``declared_albaran``.

Los numeros de este fichero son los MEDIDOS en la BBDD local, no
reconstruidos.
"""
from __future__ import annotations

import pytest
from sqlalchemy import text

VALUATION_ID = "97bfe72e-a7a4-48ff-a6bc-2ccb9cb59f3b"
DOCUMENT_ID = "99b4adcc-fe03-4d4c-a115-b2aa40ed9e6f"

#: (id, merge_line_id, concepto, cantidad, unitario, dto, importe bueno)
#: Tal como sv6 las dejo en la BBDD a las 13:24:26.
LINEAS_2137569 = (
    (600, 370, "PAPEL HIGIENICO (SACO 108)", 108.0, 0.543, 40.0, 35.19),
    (601, 371, "LTS. JABON LIQUIDO PH NEUTRO", 10.0, 3.422, 40.0, 20.53),
    (602, 372, "ROLLO PAPEL IND.", 12.0, 7.726, 40.0, 55.63),
    (603, 373, "KGS ANIL ESPECIAL FEYMACO", 4.0, 5.497, 40.0, 13.19),
    (604, 374, "BOLSA BASURA 52X58", 100.0, 0.252, 40.0, 15.12),
)

TOTAL_CORRECTO = 139.66

#: Lo que midio el humano tras guardar desde el front.
TOTAL_PISADO = 232.76
IMPORTES_PISADOS = {370: 58.64, 371: 34.22, 372: 92.71, 373: 21.99, 374: 25.20}


def _sembrar(sesion, lineas=LINEAS_2137569, total=TOTAL_CORRECTO):
    """Deja la valoracion tal cual la escribio sv6."""
    sesion.execute(
        text(
            "INSERT INTO albaran_valuations "
            "(id, document_id, total_valorado, updated_at_utc) "
            "VALUES (:id, :doc, :tot, '2026-08-18T13:24:26Z')"
        ),
        {"id": VALUATION_ID, "doc": DOCUMENT_ID, "tot": total},
    )
    for fila_id, merge_id, _, cantidad, unitario, dto, importe in lineas:
        sesion.execute(
            text(
                "INSERT INTO albaran_line_valuations ("
                "  id, valuation_id, merge_line_id, precio_unitario_final, "
                "  factor_conversion, cantidad_albaran, cantidad_convertida, "
                "  importe_calculado, importe_albaran_declarado, "
                "  importe_source, descuento_albaran_aplicado) "
                "VALUES (:id, :vid, :mid, :pu, NULL, :ca, NULL, "
                "        :imp, :decl, 'declared_albaran', :dto)"
            ),
            {
                "id": fila_id,
                "vid": VALUATION_ID,
                "mid": merge_id,
                "pu": unitario,
                "ca": cantidad,
                "imp": importe,
                "decl": importe,
                "dto": dto,
            },
        )
    sesion.flush()


def _leer_lineas(sesion):
    filas = sesion.execute(
        text(
            "SELECT merge_line_id, importe_calculado, importe_source, "
            "       cantidad_albaran, descuento_albaran_aplicado "
            "FROM albaran_line_valuations WHERE valuation_id = :v"
        ),
        {"v": VALUATION_ID},
    ).mappings().all()
    return {int(f["merge_line_id"]): f for f in filas}


def _leer_total(sesion):
    return sesion.execute(
        text("SELECT total_valorado FROM albaran_valuations WHERE id = :v"),
        {"v": VALUATION_ID},
    ).scalar_one()


# ------------------------------------------------------------------ #
# R23 — la formula canonica lleva el descuento
# ------------------------------------------------------------------ #
def test_f019_r23_guardar_sin_tocar_nada_no_infla_el_total(
    repositorio, sesion,
):
    """El caso EXACTO del incidente: guardar sin cambiar cantidades.

    El revisor abrio el 2.137.569, cambio algo que no era una cantidad
    (una partida) y guardo. El recalculo recorrio las cinco lineas
    igualmente y las dejo en 232,76 EUR.
    """
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    assert _leer_total(sesion) != pytest.approx(TOTAL_PISADO)
    assert _leer_total(sesion) == pytest.approx(TOTAL_CORRECTO)


@pytest.mark.parametrize(
    "linea", LINEAS_2137569, ids=[linea[2] for linea in LINEAS_2137569]
)
def test_f019_r23_cada_linea_conserva_su_importe_con_descuento(
    repositorio, sesion, linea,
):
    """Linea a linea, con el numero equivocado que midio el humano."""
    _, merge_id, concepto, _, _, _, importe_bueno = linea
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    resultado = _leer_lineas(sesion)[merge_id]
    assert resultado["importe_calculado"] != pytest.approx(
        IMPORTES_PISADOS[merge_id]
    ), concepto
    assert resultado["importe_calculado"] == pytest.approx(
        importe_bueno
    ), concepto


def test_f019_r23_el_descuento_se_aplica_a_la_cantidad_nueva(
    repositorio, sesion,
):
    """Si el revisor SI cambia la cantidad, manda la suya — con descuento.

    100 x 0,543 x 0,6 = 32,58. Sin descuento saldrian 54,30.
    """
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={370: 100.0},
    )

    linea = _leer_lineas(sesion)[370]
    assert linea["cantidad_albaran"] == pytest.approx(100.0)
    assert linea["importe_calculado"] == pytest.approx(32.58)
    assert linea["importe_calculado"] != pytest.approx(54.30)


def test_f019_r23_sin_descuento_la_formula_no_cambia(repositorio, sesion):
    """Regresion: una linea sin descuento sigue valiendo cantidad x precio."""
    _sembrar(
        sesion,
        lineas=((600, 370, "SIN DTO", 10.0, 2.5, None, 25.0),),
        total=25.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={370: 8.0},
    )

    assert _leer_lineas(sesion)[370]["importe_calculado"] == pytest.approx(
        20.0
    )


def test_f019_r23_descuento_fuera_de_rango_se_ignora(repositorio, sesion):
    """Un descuento absurdo no debe convertir el importe en basura.

    Misma regla que ``ImporteCalculator._sanitize_descuento`` en sv6:
    fuera de (0, 100] no se aplica, no se inventa un importe negativo.
    """
    _sembrar(
        sesion,
        lineas=((600, 370, "DTO ABSURDO", 10.0, 2.5, 150.0, 25.0),),
        total=25.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={370: 8.0},
    )

    importe = _leer_lineas(sesion)[370]["importe_calculado"]
    assert importe == pytest.approx(20.0)
    assert importe > 0


def test_f019_r23_el_descuento_editado_por_el_revisor_manda(
    repositorio, sesion,
):
    """Si el revisor corrige el descuento, el importe lo recoge.

    Antes el descuento nuevo se guardaba en la linea blanca y el importe
    valorado se quedaba con el anterior: 108 x 0,543 al 25 % = 43,98 EUR,
    no los 35,19 del 40 % viejo.
    """
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
        new_line_discounts={370: 25.0},
    )

    linea = _leer_lineas(sesion)[370]
    assert linea["importe_calculado"] == pytest.approx(43.98)
    assert linea["descuento_albaran_aplicado"] == pytest.approx(25.0)
    assert linea["importe_source"] == "calculated"


def test_f019_r23_una_linea_ilegible_no_rompe_el_guardado(
    repositorio, sesion,
):
    """Un precio que no es un numero se salta; el resto se recalcula.

    SQLite acepta texto en una columna DOUBLE y la BBDD real tampoco
    garantiza que no haya llegado basura por otra via. El guardado del
    revisor no puede caerse por eso, ni valorar la linea a cualquier
    cosa: se deja como estaba y el total suma las demas.
    """
    _sembrar(sesion)
    sesion.execute(
        text(
            "UPDATE albaran_line_valuations "
            "SET precio_unitario_final = 'ilegible' WHERE merge_line_id = 370"
        )
    )
    sesion.flush()

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    # La linea rota conserva su importe anterior, sin inventar nada.
    assert _leer_lineas(sesion)[370]["importe_calculado"] == pytest.approx(
        35.19
    )
    assert _leer_total(sesion) == pytest.approx(TOTAL_CORRECTO)


# ------------------------------------------------------------------ #
# R24 — lo que el revisor no ha tocado, no se toca
# ------------------------------------------------------------------ #
def test_f019_r24_una_linea_intacta_conserva_su_importe_source(
    repositorio, sesion,
):
    """No degradar 'declared_albaran' a 'calculated' porque si.

    El albaran DECLARA 35,19 EUR. Que el revisor guarde el documento sin
    tocar esa linea no es motivo para reetiquetar el dato como calculado
    por nosotros: es la misma regla de jul 2026 que sostiene
    ``ImporteCalculator`` (lo leido en el albaran no se pisa).
    """
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    for linea in _leer_lineas(sesion).values():
        assert linea["importe_source"] == "declared_albaran"


def test_f019_r24_cambiar_la_cantidad_si_marca_la_linea_como_calculada(
    repositorio, sesion,
):
    """Lo contrario tambien: si el revisor interviene, consta."""
    _sembrar(sesion)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={370: 100.0},
    )

    lineas = _leer_lineas(sesion)
    assert lineas[370]["importe_source"] == "calculated"
    # Las otras cuatro no las ha tocado nadie.
    for merge_id in (371, 372, 373, 374):
        assert lineas[merge_id]["importe_source"] == "declared_albaran"


# ------------------------------------------------------------------ #
# R25 / R26 — el total del documento
# ------------------------------------------------------------------ #
def test_f019_r25_el_total_lo_recalcula_sv4_y_vale_13966(
    repositorio, sesion,
):
    """El agregado, que es lo que se sumara y lo que ira a Sigrid."""
    _sembrar(sesion, total=0.0)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    assert _leer_total(sesion) == pytest.approx(TOTAL_CORRECTO)


def test_f019_r26_el_total_recalculado_no_arrastra_ruido_float(
    repositorio, sesion,
):
    """El total persistido es una cantidad monetaria de 2 decimales.

    ``sum([549.34, 882.62, 818.64, 863.26, 278.86])`` da
    3392.7200000000003 en coma flotante. sv6 ya redondea su total
    (``ValuationBuilder._build_header``); el ``SUM()`` de sv4 no lo
    hacia, asi que el mismo documento acababa con un total distinto
    segun quien lo hubiera escrito el ultimo.
    """
    lineas = tuple(
        (600 + i, 370 + i, f"LINEA {i}", 1.0, importe, None, importe)
        for i, importe in enumerate(
            (549.34, 882.62, 818.64, 863.26, 278.86)
        )
    )
    _sembrar(sesion, lineas=lineas, total=0.0)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    total = _leer_total(sesion)
    assert total == 3392.72
    assert total == round(total, 2)


# ------------------------------------------------------------------ #
# R24 · el caso DIFICIL (round trip 3)
#
# El reviewer demostro con una sonda que el guardian de R24 decidia por
# el RESULTADO (importe guardado vs importe recalculado) y no por las
# ENTRADAS (cantidad y descuento). Una linea que sv6 dejo en
# 'declared_albaran' con un importe declarado que NO coincide con
# cantidad x precio x (1 - dto/100) se pisaba en el primer guardado
# aunque el revisor no la tocara.
#
# Y sv6 produce esas filas A PROPOSITO: ImporteCalculator.compute
# devuelve el importe DECLARADO cuando declarado y calculado discrepan,
# dejando el motivo 'declared_vs_calculated_mismatch'
# (importe_calculator.py:150-170). Es la regla de jul 2026 y la regla 13
# de docs/ARCHITECTURE.md: si ambos existen y discrepan, gana el
# declarado y la linea va a revision.
#
# Los tests anteriores no lo veian porque las cinco lineas del Feymaco
# 2.137.569 cuadran al centimo: ahi resultado y entradas dicen lo mismo.
# ------------------------------------------------------------------ #

#: Linea del reviewer: cantidad 100, unitario 1,00, dto 40 % => el
#: recalculo da 60,00, pero el albaran DECLARA 100,00 (redondeos del
#: proveedor, descuentos en cascada... basta con que difiera medio
#: centimo).
LINEA_DECLARADO_DISCREPANTE = ((600, 370, "DECLARADO != CALCULADO",
                                100.0, 1.0, 40.0, 100.0),)


def test_f019_r24_el_declarado_discrepante_no_se_pisa(repositorio, sesion):
    """El caso dificil: declarado != recalculado y el revisor no toca nada.

    Es la sonda del reviewer. Antes devolvia
    {'importe_calculado': 60.0, 'importe_source': 'calculated'}.
    """
    _sembrar(sesion, lineas=LINEA_DECLARADO_DISCREPANTE, total=100.0)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
    )

    linea = _leer_lineas(sesion)[370]
    assert linea["importe_calculado"] == pytest.approx(100.0), (
        "R24: el importe declarado fue pisado"
    )
    assert linea["importe_source"] == "declared_albaran"
    assert _leer_total(sesion) == pytest.approx(100.0)


def test_f019_r24_el_declarado_discrepante_si_cede_si_cambia_la_cantidad(
    repositorio, sesion,
):
    """Lo contrario: en cuanto el revisor toca la cantidad, manda el calculo.

    50 x 1,00 x 0,6 = 30,00. El declarado del albaran ya no describe esta
    linea, porque la linea ha cambiado.
    """
    _sembrar(sesion, lineas=LINEA_DECLARADO_DISCREPANTE, total=100.0)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={370: 50.0},
    )

    linea = _leer_lineas(sesion)[370]
    assert linea["importe_calculado"] == pytest.approx(30.0)
    assert linea["importe_source"] == "calculated"


def test_f019_r24_el_declarado_discrepante_si_cede_si_cambia_el_descuento(
    repositorio, sesion,
):
    """Y con el descuento igual: 100 x 1,00 x 0,75 = 75,00."""
    _sembrar(sesion, lineas=LINEA_DECLARADO_DISCREPANTE, total=100.0)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
        new_line_discounts={370: 25.0},
    )

    linea = _leer_lineas(sesion)[370]
    assert linea["importe_calculado"] == pytest.approx(75.0)
    assert linea["importe_source"] == "calculated"


def test_f019_r24_reenviar_el_mismo_descuento_no_es_un_cambio(
    repositorio, sesion,
):
    """El front reenvia el descuento en cada guardado; eso no es tocarlo.

    Si reenviar el mismo 40 % contara como cambio, el guardian de R24 no
    protegeria nada en la practica: el payload SIEMPRE trae descuento.
    """
    _sembrar(sesion, lineas=LINEA_DECLARADO_DISCREPANTE, total=100.0)

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
        new_line_discounts={370: 40.0},
    )

    linea = _leer_lineas(sesion)[370]
    assert linea["importe_calculado"] == pytest.approx(100.0)
    assert linea["importe_source"] == "declared_albaran"


@pytest.mark.parametrize("descuento_reenviado", [0.0, None])
def test_f019_r24_cero_y_nulo_son_el_mismo_descuento(
    repositorio, sesion, descuento_reenviado,
):
    """Sin descuento es sin descuento, venga como 0 o como NULL.

    sv6 persiste NULL cuando no hay descuento y el front puede reenviar
    0. Si los dos no se compararan ya saneados, cada guardado veria un
    cambio inexistente y pisaria la fila.
    """
    _sembrar(
        sesion,
        lineas=((600, 370, "SIN DTO DECLARADO", 10.0, 2.5, None, 30.0),),
        total=30.0,
    )

    repositorio._recalc_valuation_importes(
        session=sesion,
        document_id=DOCUMENT_ID,
        new_line_quantities={},
        new_line_discounts={370: descuento_reenviado},
    )

    linea = _leer_lineas(sesion)[370]
    assert linea["importe_calculado"] == pytest.approx(30.0)
    assert linea["importe_source"] == "declared_albaran"
