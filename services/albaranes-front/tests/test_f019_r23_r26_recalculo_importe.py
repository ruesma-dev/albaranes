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

F-065 (T6) — DONDE VIVEN AHORA ESTAS GARANTIAS
----------------------------------------------
El recalculo que pisaba los importes era ``_recalc_valuation_importes``,
llamado desde el PUT del documento. F-065 R1 lo retira: guardar la cabecera
ya no toca las lineas (``test_f065_f1_cabecera.py``). Lo que el revisor
cambia de una linea viaja por el PATCH de la fila, que manda SOLO los campos
que cambio (R8). Por eso cada caso de abajo se ejerce ahora contra
``update_line_conciliacion`` (con los mismos numeros medidos): la formula
canonica con el descuento (R23), «lo que no se toca no se toca» (R24) y el
total de la cabecera (R25, R26). La tabla caso viejo -> caso nuevo esta en
``progress/impl_F-065_fase1.md``.
"""
from __future__ import annotations

import pytest
from f065_bbdd import ejecutar, fila, fila_nueva, motor_con_valoracion, repositorio, total

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
IMPORTES_PISADOS = {600: 58.64, 601: 34.22, 602: 92.71, 603: 21.99, 604: 25.20}


def _sembrar(lineas=LINEAS_2137569, total_inicial=TOTAL_CORRECTO):
    """Deja la valoracion tal cual la escribio sv6 (sin conversion de unidad)."""
    motor = motor_con_valoracion(
        document_id=DOCUMENT_ID, valuation_id=VALUATION_ID, total=total_inicial,
    )
    for fila_id, merge_id, concepto, cantidad, unitario, dto, importe in lineas:
        fila_nueva(
            motor, valuation_id=VALUATION_ID, id=fila_id, merge_line_id=merge_id,
            precio_unitario_final=unitario, factor_conversion=None,
            cantidad_albaran=cantidad, cantidad_convertida=None,
            importe_calculado=importe, importe_source="declared_albaran",
            descuento_albaran_aplicado=dto, descripcion_linea=concepto,
            review_reasons_json=None, review_required=False,
        )
    return motor


def _editar(motor, fila_id, **campos):
    return repositorio(motor).update_line_conciliacion(
        document_id=DOCUMENT_ID, valuation_line_id=fila_id, campos=campos,
    )


# ------------------------------------------------------------------ #
# R23 — la formula canonica lleva el descuento
# ------------------------------------------------------------------ #
def test_f019_r23_guardar_sin_tocar_nada_no_infla_el_total():
    """El caso EXACTO del incidente: el revisor cambio algo que no era una
    cantidad (una partida) y guardo. Ahora solo viaja la partida, y el
    importe y el total se quedan como los dejo sv6."""
    motor = _sembrar()

    _editar(motor, 600, codigo_partida="02.02")

    assert total(motor) != pytest.approx(TOTAL_PISADO)
    assert total(motor) == pytest.approx(TOTAL_CORRECTO)


@pytest.mark.parametrize(
    "linea", LINEAS_2137569, ids=[linea[2] for linea in LINEAS_2137569]
)
def test_f019_r23_cada_linea_conserva_su_importe_con_descuento(linea):
    """Linea a linea: guardarla sin cambios no la toca."""
    fila_id, _, concepto, _, _, _, importe_bueno = linea
    motor = _sembrar()

    _editar(motor, fila_id)

    resultado = fila(motor, fila_id)["importe_calculado"]
    assert resultado != pytest.approx(IMPORTES_PISADOS[fila_id]), concepto
    assert resultado == pytest.approx(importe_bueno), concepto


def test_f019_r23_el_descuento_se_aplica_a_la_cantidad_nueva():
    """100 x 0,543 x 0,6 = 32,58. Sin descuento saldrian 54,30."""
    motor = _sembrar()

    _editar(motor, 600, cantidad=100.0)

    linea = fila(motor, 600)
    assert linea["cantidad_albaran"] == pytest.approx(100.0)
    assert linea["importe_calculado"] == pytest.approx(32.58)
    assert linea["importe_calculado"] != pytest.approx(54.30)


def test_f019_r23_sin_descuento_la_formula_no_cambia():
    """Regresion: una linea sin descuento sigue valiendo cantidad x precio."""
    motor = _sembrar(lineas=((600, 370, "SIN DTO", 10.0, 2.5, None, 25.0),),
                     total_inicial=25.0)

    _editar(motor, 600, cantidad=8.0)

    assert fila(motor, 600)["importe_calculado"] == pytest.approx(20.0)


def test_f019_r23_descuento_fuera_de_rango_se_ignora():
    """Misma regla que ``ImporteCalculator._sanitize_descuento`` en sv6:
    fuera de (0, 100] no se aplica, no se inventa un importe negativo."""
    motor = _sembrar(lineas=((600, 370, "DTO ABSURDO", 10.0, 2.5, 150.0, 25.0),),
                     total_inicial=25.0)

    _editar(motor, 600, cantidad=8.0)

    importe = fila(motor, 600)["importe_calculado"]
    assert importe == pytest.approx(20.0)
    assert importe > 0


def test_f019_r23_el_descuento_editado_por_el_revisor_manda():
    """108 x 0,543 al 25 % = 43,98 EUR, no los 35,19 del 40 % viejo."""
    motor = _sembrar()

    _editar(motor, 600, descuento=25.0)

    linea = fila(motor, 600)
    assert linea["importe_calculado"] == pytest.approx(43.98)
    assert linea["descuento_albaran_aplicado"] == pytest.approx(25.0)
    assert linea["importe_source"] == "calculated"


def test_f019_r23_una_linea_ilegible_no_rompe_el_guardado_de_otra():
    """Un precio que no es un numero en OTRA linea no impide guardar esta,
    ni se valora a cualquier cosa: se queda como estaba y el total suma."""
    motor = _sembrar()
    ejecutar(motor, "UPDATE albaran_line_valuations SET precio_unitario_final = 'ilegible' "
             "WHERE id = 600")

    _editar(motor, 601, cantidad=5.0)

    assert fila(motor, 600)["importe_calculado"] == pytest.approx(35.19)
    assert fila(motor, 601)["importe_calculado"] == pytest.approx(10.27)
    assert total(motor) == pytest.approx(TOTAL_CORRECTO - 20.53 + 10.27)


# ------------------------------------------------------------------ #
# R24 — lo que el revisor no ha tocado, no se toca
# ------------------------------------------------------------------ #
def test_f019_r24_una_linea_intacta_conserva_su_importe_source():
    """Editar un campo que no entra en el importe (la descripcion) no
    reetiqueta el importe declarado como calculado."""
    motor = _sembrar()

    _editar(motor, 600, descripcion="PAPEL HIGIENICO")

    for fila_id in (600, 601, 602, 603, 604):
        assert fila(motor, fila_id)["importe_source"] == "declared_albaran"


def test_f019_r24_cambiar_la_cantidad_si_marca_la_linea_como_calculada():
    """Lo contrario tambien: si el revisor interviene, consta."""
    motor = _sembrar()

    _editar(motor, 600, cantidad=100.0)

    assert fila(motor, 600)["importe_source"] == "calculated"
    for fila_id in (601, 602, 603, 604):
        assert fila(motor, fila_id)["importe_source"] == "declared_albaran"


# ------------------------------------------------------------------ #
# R25 / R26 — el total del documento
# ------------------------------------------------------------------ #
def test_f019_r25_el_total_lo_recalcula_sv4_al_guardar_la_fila():
    """El agregado, que es lo que se sumara y lo que ira a Sigrid."""
    motor = _sembrar(total_inicial=0.0)

    _editar(motor, 600, cantidad=100.0)

    assert total(motor) == pytest.approx(32.58 + 20.53 + 55.63 + 13.19 + 15.12)


def test_f019_r26_el_total_recalculado_no_arrastra_ruido_float():
    """El total persistido es una cantidad monetaria de 2 decimales.

    ``sum([549.34, 882.62, 818.64, 863.26, 557.72])`` arrastra cola binaria
    en coma flotante. sv6 ya redondea su total; el de sv4 tambien.
    """
    lineas = tuple(
        (600 + i, 370 + i, f"LINEA {i}", 1.0, importe, None, importe)
        for i, importe in enumerate((549.34, 882.62, 818.64, 863.26, 278.86))
    )
    motor = _sembrar(lineas=lineas, total_inicial=0.0)

    _editar(motor, 604, cantidad=2.0)

    resultado = total(motor)
    assert resultado == 3671.58
    assert resultado == round(resultado, 2)


# ------------------------------------------------------------------ #
# R24 · el caso DIFICIL (round trip 3): sv6 deja a proposito filas
# 'declared_albaran' cuyo importe declarado NO cuadra con
# cantidad x precio x (1 - dto/100) (motivo
# 'declared_vs_calculated_mismatch'; regla 13 de docs/ARCHITECTURE.md).
# ------------------------------------------------------------------ #

#: Cantidad 100, unitario 1,00, dto 40 % => el calculo da 60,00, pero el
#: albaran DECLARA 100,00.
LINEA_DECLARADO_DISCREPANTE = ((600, 370, "DECLARADO != CALCULADO",
                                100.0, 1.0, 40.0, 100.0),)


def test_f019_r24_el_declarado_discrepante_no_se_pisa():
    """Guardar la fila sin cambiar nada de lo que entra en el importe."""
    motor = _sembrar(lineas=LINEA_DECLARADO_DISCREPANTE, total_inicial=100.0)

    _editar(motor, 600, codigo_externo="X-1")

    linea = fila(motor, 600)
    assert linea["importe_calculado"] == pytest.approx(100.0), (
        "R24: el importe declarado fue pisado"
    )
    assert linea["importe_source"] == "declared_albaran"
    assert total(motor) == pytest.approx(100.0)


def test_f019_r24_el_declarado_discrepante_si_cede_si_cambia_la_cantidad():
    """50 x 1,00 x 0,6 = 30,00: la linea ha cambiado."""
    motor = _sembrar(lineas=LINEA_DECLARADO_DISCREPANTE, total_inicial=100.0)

    _editar(motor, 600, cantidad=50.0)

    linea = fila(motor, 600)
    assert linea["importe_calculado"] == pytest.approx(30.0)
    assert linea["importe_source"] == "calculated"


def test_f019_r24_el_declarado_discrepante_si_cede_si_cambia_el_descuento():
    """Y con el descuento igual: 100 x 1,00 x 0,75 = 75,00."""
    motor = _sembrar(lineas=LINEA_DECLARADO_DISCREPANTE, total_inicial=100.0)

    _editar(motor, 600, descuento=25.0)

    linea = fila(motor, 600)
    assert linea["importe_calculado"] == pytest.approx(75.0)
    assert linea["importe_source"] == "calculated"


def test_f019_r24_reenviar_el_mismo_descuento_no_es_un_cambio():
    """Un cliente que reenvia el mismo 40 % y la misma cantidad no esta
    tocando nada."""
    motor = _sembrar(lineas=LINEA_DECLARADO_DISCREPANTE, total_inicial=100.0)

    _editar(motor, 600, descuento=40.0, cantidad=100.0)

    linea = fila(motor, 600)
    assert linea["importe_calculado"] == pytest.approx(100.0)
    assert linea["importe_source"] == "declared_albaran"


@pytest.mark.parametrize("descuento_reenviado", [0.0, None])
def test_f019_r24_cero_y_nulo_son_el_mismo_descuento(descuento_reenviado):
    """Sin descuento es sin descuento, venga como 0 o como NULL."""
    motor = _sembrar(lineas=((600, 370, "SIN DTO DECLARADO", 10.0, 2.5, None, 30.0),),
                     total_inicial=30.0)

    _editar(motor, 600, descuento=descuento_reenviado)

    linea = fila(motor, 600)
    assert linea["importe_calculado"] == pytest.approx(30.0)
    assert linea["importe_source"] == "declared_albaran"
