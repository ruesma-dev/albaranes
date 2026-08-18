# tests/test_f027_r1_r2_r11_r13_builder.py
"""F-027 · R1, R2, R10, R11, R12, R13: el defecto, a traves del builder.

Aqui muere la red
-----------------
``test_f027_r3_r9_conversor.py`` demuestra que ``UnitConverter`` sabe
reinterpretar 30.380 sin unidad contra un contrato en TN. Este fichero
demuestra que ese saber **nunca llegaba a usarse**: el
``ValuationBuilder`` llamaba al conversor con ``cantidad=None`` a
proposito cuando el guard de categoria decia que no (rama ``else`` de
``valuation_builder.py``), asi que la primera guarda de ``convert``
salia por ``no_quantity_in_albaran`` antes de la red.

Los numeros son los medidos en la BBDD local el 2026-08-18 (informe
``progress/revision_resto_lote_20260818.md`` §1, §2 y §4.1): el 58826
valorado en **468.763,40 EUR** contra los 390,99 EUR del administrativo,
y el 58878 en **462.282,80 EUR** contra 385,59 EUR.

Honestidad sobre lo que arregla F-027 (decision D4)
---------------------------------------------------
F-027 quita el factor 1000, **no el error entero**. Con el precio que
hoy elige IA3 —15,43 EUR/TN de caliza en vez de 12,87 de grava— el
58826 queda en 468,76 EUR, no en los 390,99 del ground truth. Esos
77,77 EUR son **F-031** y quedan fuera a proposito (R23), para que la
prueba local pueda distinguir que feature produjo cada euro. Por eso
cada albaran se fija con LOS DOS precios.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest

from tests.f027_escenarios import (
    CATALOGO_MAHORSA,
    CONTRATO_GRAVA_1287,
    Escenario,
    LineaContrato,
    valorar,
)

#: Lo que salio en la BBDD el 2026-08-18. Es el numero que este fichero
#: existe para impedir que vuelva.
IMPORTE_MEDIDO_MAL_58826 = 468763.4
IMPORTE_MEDIDO_MAL_58878 = 462282.8


def _mahorsa(numero: str, cantidad: float) -> Escenario:
    """El albaran de MAHORSA tal como llego: sin unidad, partida propia.

    IA3 caso la linea de CALIZA (15,43 EUR/TN, partida P4.14.01.02.01);
    el albaran trae manuscrita P4.22.01.03.07, asi que el
    ``PartidaMatcher`` genera una linea DERIVADA en la partida del
    albaran (``partida_action='new_line_created'``, derivada 404 en la
    BBDD).
    """
    return Escenario(
        numero_albaran=numero,
        cantidad=cantidad,
        unidad_albaran=None,
        codigo_partida_albaran="P4.22.01.03.07",
        matched_contrato_line_id=25980,
        precio_contrato_db=15.43,
        contrato=CATALOGO_MAHORSA,
    )


def _mahorsa_precio_correcto(numero: str, cantidad: float) -> Escenario:
    """El mismo albaran si F-031 eligiera bien la linea de contrato."""
    return Escenario(
        numero_albaran=numero,
        cantidad=cantidad,
        unidad_albaran=None,
        codigo_partida_albaran="P4.22.01.03.07",
        matched_contrato_line_id=CONTRATO_GRAVA_1287.contrato_line_id,
        precio_contrato_db=CONTRATO_GRAVA_1287.precio_unitario,
        contrato=CATALOGO_MAHORSA,
    )


# --------------------------------------------------------------------- #
# R1, R2, R10 — se convierte SIEMPRE, y el desacuerdo solo marca revision
# --------------------------------------------------------------------- #

def test_f027_r1_el_builder_convierte_aunque_el_guard_diga_que_no():
    """R1: el conversor recibe la cantidad REAL, no ``None``.

    El guard reclasifica (albaran ``unknown`` contra contrato ``mass``)
    y devuelve ``category_match=False``. Eso ya no ciega al conversor:
    la red de plausibilidad se alcanza y reinterpreta 30.380 kg.
    """
    _, linea = valorar(_mahorsa("58826", 30380.0))

    assert linea.unidad_category_match is False
    assert linea.cantidad_convertida == pytest.approx(30.38)
    assert linea.factor_conversion == pytest.approx(0.001)
    assert "cantidad_sin_unidad_reinterpretada_kg_a_tn" in linea.review_reasons


def test_f027_r2_el_desacuerdo_de_categoria_sigue_mandando_a_revision():
    """R2: ``category_match=False`` marca revision, no anula la cantidad.

    Convertir bien y marcar revision domina estrictamente a valorar mal
    y marcar revision. Lo que NO puede pasar es que la linea deje de ir
    a revision.
    """
    _, linea = valorar(_mahorsa("58826", 30380.0))

    assert linea.review_required is True
    assert "unit_category_partially_unknown" in linea.review_reasons


def test_f027_r10_una_linea_con_cantidad_no_puede_decir_que_no_la_tiene():
    """R10: ``no_quantity_in_albaran`` vuelve a significar lo que dice.

    En la BBDD del 2026-08-18 esa linea llevaba el motivo TENIENDO
    ``cantidad_albaran = 30380``. Es el hallazgo H-2 del informe de
    hormigones y el objeto de F-025; aqui desaparece como consecuencia
    directa de R1, sin renombrar ni anadir ningun motivo (R22).
    """
    _, linea = valorar(_mahorsa("58826", 30380.0))

    assert linea.cantidad_albaran == pytest.approx(30380.0)
    assert "no_quantity_in_albaran" not in linea.review_reasons
    # Y tampoco el fallback a la cantidad cruda, que es su consecuencia.
    assert "importe_using_albaran_quantity_fallback" not in linea.review_reasons


# --------------------------------------------------------------------- #
# R11, R12 — los dos albaranes de MAHORSA, con sus numeros
# --------------------------------------------------------------------- #

def test_f027_r11_el_58826_no_vale_468763_euros():
    """R11: 30.380 kg a 15,43 EUR/TN son 468,76 EUR, no 468.763,40."""
    _, linea = valorar(_mahorsa("58826", 30380.0))

    assert linea.importe_calculado != pytest.approx(IMPORTE_MEDIDO_MAL_58826)
    assert linea.importe_calculado == pytest.approx(468.76)


def test_f027_r11_el_58826_con_el_precio_correcto_da_el_numero_del_gt():
    """R11: con 12,87 EUR/TN sale exactamente el 390,99 del administrativo.

    Fija que el unico euro que falta despues de F-027 es el del precio
    (F-031), no el de la unidad.
    """
    _, linea = valorar(_mahorsa_precio_correcto("58826", 30380.0))

    assert linea.cantidad_convertida == pytest.approx(30.38)
    assert linea.importe_calculado == pytest.approx(390.99)


def test_f027_r12_el_58878_no_vale_462282_euros():
    """R12: 29.960 kg a 15,43 EUR/TN son 462,28 EUR."""
    _, linea = valorar(_mahorsa("58878", 29960.0))

    assert linea.importe_calculado != pytest.approx(IMPORTE_MEDIDO_MAL_58878)
    assert linea.cantidad_convertida == pytest.approx(29.96)
    assert linea.factor_conversion == pytest.approx(0.001)
    assert linea.importe_calculado == pytest.approx(462.28)


def test_f027_r12_el_58878_con_el_precio_correcto_da_38559():
    """R12: con 12,87 EUR/TN, los 385,59 EUR del administrativo."""
    _, linea = valorar(_mahorsa_precio_correcto("58878", 29960.0))

    assert linea.importe_calculado == pytest.approx(385.59)


# --------------------------------------------------------------------- #
# R13 — el TOTAL del documento, que es lo que ve el revisor
# --------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "numero, cantidad, medido_mal",
    [
        ("58826", 30380.0, IMPORTE_MEDIDO_MAL_58826),
        ("58878", 29960.0, IMPORTE_MEDIDO_MAL_58878),
    ],
)
def test_f027_r13_el_total_del_documento_esta_en_centenas_de_euros(
    numero, cantidad, medido_mal,
):
    """R13: ``albaran_valuations.total_valorado``, no la linea suelta.

    Leccion de F-019 R25: los tests que solo miran la linea dejan pasar
    el agregado, que es justo la columna que llega a la bandeja.
    """
    cabecera, _ = valorar(_mahorsa(numero, cantidad))

    assert cabecera.total_valorado != pytest.approx(medido_mal)
    assert cabecera.total_valorado <= 500.0


# --------------------------------------------------------------------- #
# R8 a traves del builder — la guarda de cantidad ausente sigue viva
# --------------------------------------------------------------------- #

def test_f027_r8_sin_linea_de_albaran_la_cantidad_sigue_siendo_ausente():
    """Una linea sin cantidad leida conserva ``no_quantity_in_albaran``.

    F-027 elimina la rama que pasaba ``cantidad=None`` a proposito, no
    la guarda que protege del caso real de cantidad ausente.
    """
    _, linea = valorar(
        Escenario(
            numero_albaran="sin-cantidad",
            cantidad=None,
            unidad_albaran=None,
            codigo_partida_albaran="P4.22.01.03.07",
            matched_contrato_line_id=25980,
            precio_contrato_db=15.43,
            contrato=CATALOGO_MAHORSA,
        )
    )

    assert linea.cantidad_albaran is None
    assert linea.cantidad_convertida is None
    assert linea.factor_conversion is None
    assert "no_quantity_in_albaran" in linea.review_reasons
    assert linea.review_required is True


def test_f027_r8_una_linea_sin_contexto_de_albaran_no_inventa_cantidad():
    """El caso que de verdad ejercita ``if albaran_line else None``.

    El test anterior tiene contexto de albaran con ``cantidad=None``; en
    este NO HAY contexto: la linea de IA3 apunta a un ``merge_line_id``
    que no viaja en ``context.lineas_albaran`` (sobre incompleto o
    desincronizado). Entonces ``albaran_line`` es ``None`` y la
    expresion condicional de la llamada al conversor es la unica que
    decide.

    Lo escribio la campana de mutacion: el mutante que cambiaba ese
    ``else None`` por ``else 0.0`` sobrevivia a los 109 tests. Con 0.0
    la linea se valoraria en 0,00 EUR con ``importe_source='calculated'``
    —un importe INVENTADO con pinta de calculado— en vez de quedarse sin
    importe y pedir revision.
    """
    from domain.models.valuation_envelope import (
        DocumentoValoracionDto,
        LineValuationDto,
        ValuationContextDto,
        ValuationEnvelope,
        ValuationEnvelopeMeta,
    )

    from tests.f027_escenarios import construir_builder, construir_envelope

    envelope = construir_envelope(_mahorsa("58826", 30380.0))
    # Se conserva el catalogo de contrato y se vacia el contexto del
    # albaran: la linea de IA3 queda apuntando al vacio.
    huerfana = ValuationEnvelope(
        status="ok",
        meta=ValuationEnvelopeMeta(
            document_id="doc-sin-contexto",
            codigo_contrato="CTSU25/0085",
            numero_albaran="58826-sin-contexto",
        ),
        data=DocumentoValoracionDto(
            lineas=[
                LineValuationDto(**envelope.data.lineas[0].model_dump()),
            ],
        ),
        context=ValuationContextDto(
            lineas_albaran=[],
            lineas_contrato=envelope.context.lineas_contrato,
        ),
    )

    _, registros = construir_builder().build(
        envelope=huerfana, existing_document_already_valued=False,
    )
    linea = registros[0]

    assert linea.cantidad_albaran is None
    assert linea.cantidad_convertida is None
    assert linea.factor_conversion is None
    assert "no_quantity_in_albaran" in linea.review_reasons
    # Sin cantidad no hay importe: ni 0,00 EUR ni nada parecido.
    assert linea.importe_calculado is None
    assert linea.importe_source == "none"
    assert linea.review_required is True


# --------------------------------------------------------------------- #
# D2 y D3 — los dos riesgos ASUMIDOS del diseno, fijados con test propio
#
# No son efectos colaterales: son decisiones. Se escriben aqui para que
# se lean como tales, y para que cambiarlas obligue a tocar un test.
# --------------------------------------------------------------------- #

def test_f027_d2_se_convierte_aunque_ia3_declare_desacuerdo_de_categoria():
    """D2: si la IA dice ``category_match=false`` pero KG->TN es real,
    se convierte igualmente — y la linea sigue yendo a revision.

    Riesgo asumido y deliberado: antes se respetaba ciegamente ese
    juicio, y respetarlo es exactamente lo que producia el x1000.
    Convertir bien y marcar revision domina a valorar mal y marcar
    revision.
    """
    _, linea = valorar(
        Escenario(
            numero_albaran="58826-ia-en-desacuerdo",
            cantidad=30380.0,
            unidad_albaran="KG",
            codigo_partida_albaran="P4.22.01.03.07",
            matched_contrato_line_id=25980,
            precio_contrato_db=15.43,
            contrato=CATALOGO_MAHORSA,
            unidad_category_match_ia=False,
        )
    )

    assert linea.unidad_category_match is False
    assert "ia_unit_category_mismatch" in linea.review_reasons
    assert linea.cantidad_convertida == pytest.approx(30.38)
    assert linea.importe_calculado == pytest.approx(468.76)
    assert linea.review_required is True


def test_f027_d3_mil_unidades_legitimas_contra_un_contrato_en_tn_se_dividen():
    """D3: el umbral de 1000 tambien reinterpretaria un albaran legitimo.

    Riesgo aceptado y acotado: ningun albaran real trae >= 1000 TN (un
    camion lleva 25-30), y el caso SIEMPRE sale marcado para revision,
    asi que ningun importe reinterpretado llega mudo al revisor. Los dos
    umbrales son parametros del constructor de ``UnitConverter``: si el
    riesgo se materializara, se ajustan sin tocar codigo.

    Este test NO celebra el comportamiento: lo deja escrito para que
    cambiarlo sea una decision explicita y no un descuido.
    """
    _, linea = valorar(
        Escenario(
            numero_albaran="1200-tn-de-verdad",
            cantidad=1200.0,
            unidad_albaran=None,
            codigo_partida_albaran="P4.22.01.03.07",
            matched_contrato_line_id=25980,
            precio_contrato_db=15.43,
            contrato=CATALOGO_MAHORSA,
        )
    )

    assert linea.cantidad_convertida == pytest.approx(1.2)
    assert linea.factor_conversion == pytest.approx(0.001)
    assert "cantidad_sin_unidad_reinterpretada_kg_a_tn" in linea.review_reasons
    # La contrapartida que hace aceptable el riesgo.
    assert linea.review_required is True


# --------------------------------------------------------------------- #
# La red del conversor tambien alcanza al nivel de AVISO (R4) desde el
# builder: implausible pero no seguro, la cantidad no se toca.
# --------------------------------------------------------------------- #

def test_f027_r4_desde_el_builder_la_cantidad_implausible_solo_se_avisa():
    _, linea = valorar(
        Escenario(
            numero_albaran="500-sin-unidad",
            cantidad=500.0,
            unidad_albaran=None,
            codigo_partida_albaran="P4.22.01.03.07",
            matched_contrato_line_id=25980,
            precio_contrato_db=15.43,
            contrato=CATALOGO_MAHORSA,
        )
    )

    assert linea.cantidad_convertida == pytest.approx(500.0)
    assert linea.factor_conversion == pytest.approx(1.0)
    assert "cantidad_tn_implausible_revisar" in linea.review_reasons
    assert linea.review_required is True


# --------------------------------------------------------------------- #
# Contrato sin unidad de medida: no hay destino, no hay conversion.
# --------------------------------------------------------------------- #

def test_f027_r1_sin_unidad_de_destino_la_cantidad_pasa_con_factor_1():
    """Un contrato sin unidad no puede fijar destino: factor 1 y aviso.

    Sigue habiendo conversion (con la cantidad real), lo que cambia es
    que no hay nada a que convertir.
    """
    sin_unidad = LineaContrato(
        contrato_line_id=25980,
        descripcion="ARIDO CALIZA MACHAQUEO T-20/40-C EN 12620:2002H",
        unidad_medida=None,
        precio_unitario=15.43,
        codigo_partida="P4.14.01.02.01",
    )
    _, linea = valorar(
        Escenario(
            numero_albaran="contrato-sin-unidad",
            cantidad=30380.0,
            unidad_albaran=None,
            codigo_partida_albaran="P4.14.01.02.01",
            matched_contrato_line_id=25980,
            precio_contrato_db=15.43,
            contrato=(sin_unidad,),
        )
    )

    assert linea.cantidad_convertida == pytest.approx(30380.0)
    assert linea.factor_conversion == pytest.approx(1.0)
    assert "no_contract_unit_assumed_same" in linea.review_reasons
