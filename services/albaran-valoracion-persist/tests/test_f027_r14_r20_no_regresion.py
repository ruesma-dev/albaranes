# tests/test_f027_r14_r20_no_regresion.py
"""F-027 · R14, R15, R16, R19, R20: lo que ya funciona no se mueve.

Que hace este fichero
---------------------
F-027 quita una rama del ``ValuationBuilder`` que hoy se ejecuta en
**casi todas** las lineas del lote ``alvaro_17082026``: el guard de
categoria devuelve ``False`` en cuanto IA1 no extrae la unidad, que es
lo que pasa en 17 de 17 lineas. Es decir, el cambio toca el camino por
el que salen los importes que hoy estan BIEN.

Estos tests son su contrapeso. Los numeros estan MEDIDOS en la BBDD
local el 2026-08-18 y verificados contra el administrativo
(``progress/revision_hormigones_20260818.md`` §1-§4 y
``progress/revision_resto_lote_20260818.md`` §7):

* **R14** hormigon y mortero sin unidad contra contrato en ``M3``;
* **R15** ferreteria en unidades (Feymaco), con los numeros de F-019;
* **R16** el A261584 de VODALAND, unico total correcto del lote.

Por que no se mueven, medido y no supuesto: en esos casos la cantidad
caia al fallback crudo con factor 1, y tras el cambio el conversor
devuelve **la misma cantidad** con factor 1 y el motivo
``no_albaran_unit_assumed_same``. El numero es identico; lo que cambia
es el motivo, que pasa a ser cierto.

Si alguno de estos tests se pusiera rojo, F-027 habria roto algo que
funcionaba: esa es exactamente su funcion.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest

from tests.f027_escenarios import (
    CATALOGO_MAHORSA,
    Escenario,
    LineaContrato,
    construir_builder,
    valorar,
)

# --------------------------------------------------------------------- #
# R14 — hormigon y mortero: cantidad sin unidad contra un contrato en M3
#
# Las cifras son las de la LINEA BASE de cada albaran. El total del
# documento incluye ademas las sinteticas (incrementos por ano, carga
# incompleta), que F-027 no toca y que tienen sus propias features.
# --------------------------------------------------------------------- #

CONTRATO_HORMIGON = LineaContrato(
    contrato_line_id=25716,
    descripcion="HORMIGON HA-25/B/20/XC2",
    unidad_medida="M3",
    precio_unitario=99.90,
    codigo_partida="P5.03.04",
    codigo_contrato="CTSU24/0518",
)

CONTRATO_MORTERO = LineaContrato(
    contrato_line_id=25939,
    descripcion="MORTERO M-5",
    unidad_medida="M3",
    precio_unitario=70.00,
    codigo_partida="P5.03.09",
    codigo_contrato="CTSU24/0518",
)


HORMIGONES_DEL_LOTE = [
    # 224964 · Sierra Madrid · base 4 m3 x 99,90 (total doc 475,60)
    ("224964", 4.0, CONTRATO_HORMIGON, 399.60),
    # 225137 · Sierra Madrid · base 9 m3 x 99,90 (total doc 980,10)
    ("225137", 9.0, CONTRATO_HORMIGON, 899.10),
    # 1167 · Paz del Barrio · base 8 m3 x 99,90 (total doc 871,20)
    ("1167", 8.0, CONTRATO_HORMIGON, 799.20),
    # 1229 · Paz del Barrio · mortero, base 3 m3 x 70,00
    ("1229", 3.0, CONTRATO_MORTERO, 210.00),
]


def _escenario_hormigon(albaran, cantidad, contrato, partida=None):
    return Escenario(
        numero_albaran=albaran,
        cantidad=cantidad,
        unidad_albaran=None,
        codigo_partida_albaran=partida or contrato.codigo_partida,
        matched_contrato_line_id=contrato.contrato_line_id,
        precio_contrato_db=contrato.precio_unitario,
        contrato=(contrato,),
        descripcion=contrato.descripcion,
        codigo_contrato=contrato.codigo_contrato,
    )


@pytest.mark.parametrize(
    "albaran, cantidad, contrato, importe_medido", HORMIGONES_DEL_LOTE,
)
def test_f027_r14_el_hormigon_en_m3_da_exactamente_el_mismo_importe(
    albaran, cantidad, contrato, importe_medido,
):
    """El caso que hoy sale bien POR SUERTE: contrato y albaran en m3.

    ESTE TEST DEBE ESTAR VERDE ANTES Y DESPUES DEL CAMBIO. Esa es toda
    su funcion: si se pusiera rojo, F-027 habria roto lo que ya
    funcionaba. Por eso solo mira el EURO, que es lo que no puede
    moverse; los metadatos de conversion si cambian, y de eso se ocupa
    el test siguiente.
    """
    _, linea = valorar(_escenario_hormigon(albaran, cantidad, contrato))

    assert linea.importe_calculado == pytest.approx(importe_medido)


@pytest.mark.parametrize(
    "albaran, cantidad, contrato, importe_medido", HORMIGONES_DEL_LOTE,
)
def test_f027_r14_el_hormigon_pasa_a_convertirse_con_factor_1(
    albaran, cantidad, contrato, importe_medido,
):
    """Lo que SI cambia: el motivo, que pasa a ser cierto.

    Antes la cantidad caia al fallback crudo y la linea decia
    ``no_quantity_in_albaran`` teniendo cantidad. Ahora se convierte de
    verdad —a la misma cantidad, con factor 1— y lo dice.
    """
    _, linea = valorar(_escenario_hormigon(albaran, cantidad, contrato))

    assert linea.cantidad_convertida == pytest.approx(cantidad)
    assert linea.factor_conversion == pytest.approx(1.0)
    assert "no_albaran_unit_assumed_same" in linea.review_reasons
    assert "no_quantity_in_albaran" not in linea.review_reasons


def test_f027_r14_el_hormigon_con_partida_cruzada_tampoco_mueve_el_importe():
    """Variante con linea DERIVADA, que es donde R6 cambia el destino.

    La derivada hereda la unidad del contrato (``M3``), asi que el
    destino nuevo y el viejo dan lo mismo. Es el caso real de los cuatro
    albaranes del lote, donde la partida manuscrita se leyo mal y el
    matcher derivo linea. VERDE ANTES Y DESPUES.
    """
    _, linea = valorar(
        # "03.04" es el literal tal como se leyo mal del manuscrito.
        _escenario_hormigon("224964-partida-cruzada", 4.0, CONTRATO_HORMIGON,
                            partida="03.04")
    )

    assert linea.partida_action == "new_line_created"
    assert linea.derived_contrato_line_record.unidad_medida == "M3"
    assert linea.importe_calculado == pytest.approx(399.60)


# --------------------------------------------------------------------- #
# R15 — ferreteria en unidades: los numeros que fijo F-019
#
# Se REUTILIZAN los escenarios de F-019 en vez de copiarlos: si alguien
# cambia alli los importes, este fichero cambia con ellos y la
# comparacion sigue siendo la misma. Copiarlos permitiria que las dos
# verdades divergieran en silencio, que es justo lo que F-019 acaba de
# pagar caro con la formula del importe duplicada entre servicios.
# --------------------------------------------------------------------- #

def test_f027_r15_los_dos_albaranes_de_feymaco_dan_lo_mismo_que_en_f019():
    """139,66 EUR y 19,41 EUR, por el builder entero."""
    from tests.test_f019_r25_r26_total_documento import (
        LINEAS_2137569,
        LINEAS_2139643,
        TOTAL_2137569,
        TOTAL_2139643,
        _construir_envelope,
    )

    builder = construir_builder()

    cabecera_a, lineas_a = builder.build(
        envelope=_construir_envelope("2.137.569", LINEAS_2137569),
        existing_document_already_valued=False,
    )
    cabecera_b, lineas_b = builder.build(
        envelope=_construir_envelope("2.139.643", LINEAS_2139643),
        existing_document_already_valued=False,
    )

    assert cabecera_a.total_valorado == TOTAL_2137569
    assert cabecera_b.total_valorado == TOTAL_2139643

    # Y los cinco importes de linea, uno a uno.
    esperados = [importe for _, _, _, _, _, importe in LINEAS_2137569]
    obtenidos = [linea.importe_calculado for linea in lineas_a]
    assert obtenidos == pytest.approx(esperados)
    assert lineas_b[0].importe_calculado == pytest.approx(19.41)


# --------------------------------------------------------------------- #
# R16 — el testigo elegido a proposito: el unico total correcto del lote
# --------------------------------------------------------------------- #

def test_f027_r16_el_a261584_de_vodaland_sigue_valiendo_3393_euros():
    """377 unidades sin unidad leida contra un contrato en ``UD``.

    Si el cambio moviera algo que hoy esta bien, este es el que lo
    delata: es el unico documento del lote ``alvaro_17082026`` cuyo
    total cuadra con el administrativo al centimo.
    """
    contrato_vodaland = LineaContrato(
        contrato_line_id=26345,
        descripcion="Canal de Plastico Base DN100 H60 modernizado",
        unidad_medida="UD",
        precio_unitario=9.0,
        codigo_partida="P4.22.02.03.01.07",
        codigo_contrato="CTSU26/0058",
        codigo_producto="8050-M",
    )
    cabecera, linea = valorar(
        Escenario(
            numero_albaran="A261584",
            cantidad=377.0,
            unidad_albaran=None,
            codigo_partida_albaran="P4.22.02.03.01.07",
            matched_contrato_line_id=26345,
            precio_contrato_db=9.0,
            contrato=(contrato_vodaland,),
            descripcion=contrato_vodaland.descripcion,
            codigo_contrato="CTSU26/0058",
        )
    )

    assert linea.importe_calculado == pytest.approx(3393.0)
    assert cabecera.total_valorado == pytest.approx(3393.0)
    assert linea.partida_action == "existing_matched"


# --------------------------------------------------------------------- #
# R17 desde el builder — las unidades ambiguas siguen marcando revision
# --------------------------------------------------------------------- #

def test_f027_r17_desde_el_builder_el_saco_convierte_con_factor_1_y_revisa():
    contrato_ud = LineaContrato(
        contrato_line_id=700,
        descripcion="CEMENTO EN SACO",
        unidad_medida="UD",
        precio_unitario=4.0,
        codigo_partida="P1.01",
    )
    _, linea = valorar(
        Escenario(
            numero_albaran="sacos",
            cantidad=5.0,
            unidad_albaran="SACO",
            codigo_partida_albaran="P1.01",
            matched_contrato_line_id=700,
            precio_contrato_db=4.0,
            contrato=(contrato_ud,),
            descripcion="CEMENTO EN SACO",
        )
    )

    assert linea.cantidad_convertida == pytest.approx(5.0)
    assert linea.factor_conversion == pytest.approx(1.0)
    assert "ambiguous_unit_conversion" in linea.review_reasons
    assert linea.review_required is True


# --------------------------------------------------------------------- #
# R19 — los cuatro estados, con su motivo y solo el suyo
#
# El revisor tiene que poder distinguir «se convirtio aplicando la red»
# de «no se pudo convertir» y de «la cantidad falta de verdad». Los
# cuatro motivos ya existian; lo que no ocurria es que llegaran a la
# linea.
# --------------------------------------------------------------------- #

#: Los cuatro motivos de la tabla de R19. Cada estado emite EL SUYO y
#: ninguno de los otros tres.
MOTIVOS_R19 = (
    "cantidad_sin_unidad_reinterpretada_kg_a_tn",
    "cantidad_tn_implausible_revisar",
    "unit_category_mismatch_in_conversion",
    "no_quantity_in_albaran",
)

CONTRATO_M3_PARA_CRUCE = LineaContrato(
    contrato_line_id=900,
    descripcion="HORMIGON HA-25",
    unidad_medida="M3",
    precio_unitario=99.90,
    codigo_partida="P1.01",
)


def _escenario_r19(nombre, cantidad, unidad_albaran, contrato, matched_id,
                   precio):
    return Escenario(
        numero_albaran=nombre,
        cantidad=cantidad,
        unidad_albaran=unidad_albaran,
        codigo_partida_albaran=contrato[0].codigo_partida,
        matched_contrato_line_id=matched_id,
        precio_contrato_db=precio,
        contrato=contrato,
        descripcion=contrato[0].descripcion,
    )


@pytest.mark.parametrize(
    "estado, escenario, motivo, convertida, factor",
    [
        (
            "se convirtio aplicando la red de plausibilidad",
            _escenario_r19(
                "r19-reinterpretada", 30380.0, None, CATALOGO_MAHORSA,
                25972, 12.87,
            ),
            "cantidad_sin_unidad_reinterpretada_kg_a_tn",
            30.38,
            0.001,
        ),
        (
            "magnitud sospechosa pero no se toco",
            _escenario_r19(
                "r19-implausible", 500.0, None, CATALOGO_MAHORSA,
                25972, 12.87,
            ),
            "cantidad_tn_implausible_revisar",
            500.0,
            1.0,
        ),
        (
            "no se pudo convertir: categorias incompatibles",
            _escenario_r19(
                "r19-incompatibles", 108.0, "UD", (CONTRATO_M3_PARA_CRUCE,),
                900, 99.90,
            ),
            "unit_category_mismatch_in_conversion",
            None,
            None,
        ),
        (
            "la cantidad falta de verdad",
            _escenario_r19(
                "r19-sin-cantidad", None, None, CATALOGO_MAHORSA,
                25972, 12.87,
            ),
            "no_quantity_in_albaran",
            None,
            None,
        ),
    ],
)
def test_f027_r19_cada_estado_emite_su_motivo_y_solo_el_suyo(
    estado, escenario, motivo, convertida, factor,
):
    _, linea = valorar(escenario)

    assert motivo in linea.review_reasons, estado
    otros = [m for m in MOTIVOS_R19 if m != motivo]
    for otro in otros:
        assert otro not in linea.review_reasons, f"{estado}: sobra {otro}"

    if convertida is None:
        assert linea.cantidad_convertida is None, estado
        assert linea.factor_conversion is None, estado
    else:
        assert linea.cantidad_convertida == pytest.approx(convertida), estado
        assert linea.factor_conversion == pytest.approx(factor), estado

    assert linea.review_required is True, estado


def test_f027_r19_no_convertible_cae_al_fallback_con_la_cantidad_cruda():
    """R5/R19: cuando no se puede convertir, el importe usa el crudo.

    Es la red de ultimo recurso del ``ImporteCalculator``, que F-027
    conserva entera, y viene con su propio motivo para que se distinga
    de un importe convertido.
    """
    _, linea = valorar(
        _escenario_r19(
            "r19-incompatibles", 108.0, "UD", (CONTRATO_M3_PARA_CRUCE,),
            900, 99.90,
        )
    )

    assert "importe_using_albaran_quantity_fallback" in linea.review_reasons
    assert linea.importe_calculado == pytest.approx(108.0 * 99.90)


# --------------------------------------------------------------------- #
# R20 — rastro NUMERICO, no solo textual
# --------------------------------------------------------------------- #

def test_f027_r20_la_reinterpretacion_deja_las_tres_columnas_coherentes():
    """``cantidad_albaran``, ``cantidad_convertida`` y ``factor_conversion``.

    La ficha de linea de sv4 lee las tres columnas, asi que con esto la
    reinterpretacion es visible en el front sin tocar sv4: el revisor ve
    los 30.380 que ponia el albaran junto a las 30,38 TN valoradas y el
    factor que las une.
    """
    _, linea = valorar(
        Escenario(
            numero_albaran="58826",
            cantidad=30380.0,
            unidad_albaran=None,
            codigo_partida_albaran="P4.22.01.03.07",
            matched_contrato_line_id=25980,
            precio_contrato_db=15.43,
            contrato=CATALOGO_MAHORSA,
        )
    )

    assert linea.cantidad_albaran == pytest.approx(30380.0)
    assert linea.cantidad_convertida == pytest.approx(30.38)
    assert linea.factor_conversion == pytest.approx(0.001)
    # Coherencia aritmetica de las tres: no son tres datos sueltos.
    assert linea.cantidad_albaran * linea.factor_conversion == pytest.approx(
        linea.cantidad_convertida
    )
