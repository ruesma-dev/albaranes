# tests/test_f027_r6_r7_unidad_destino.py
"""F-027 · R6, R7: la unidad de destino es la de quien pone el precio.

La otra mitad del mismo x1000
-----------------------------
El caso de ``test_f027_r1_r2_r11_r13_builder.py`` necesita que IA1 no
extraiga la unidad. Este NO: aqui el albaran trae ``KG``, el contrato
tarifa en ``TN``, el guard da ``category_match=True`` porque ambas son
masa... y el importe sigue saliendo x1000.

El motivo es una sola expresion del paso 4 del builder: cuando el
``PartidaMatcher`` genera una linea DERIVADA, se convertia hacia
``unidad_albaran``. Pero ``PartidaMatcher._build_derived`` le da a la
derivada la unidad Y EL PRECIO de la linea de contrato que caso la IA
siempre que exista, que es el caso normal. Resultado: ``KG -> KG`` con
factor 1 contra un precio por tonelada.

Dos cosas lo hacen grave:

* esta vivo HOY, sin necesidad de que ninguna IA falle;
* y en este camino la linea **ni siquiera va a revision**
  (``category_match`` es ``True`` y no hay ambiguedad), asi que los
  468.763,40 EUR llegarian mudos a la bandeja.

Es ademas exactamente el escenario que **F-024 activa**: en cuanto IA1
empiece a extraer «KG» en los albaranes de MAHORSA, entraran por aqui.
Arreglar una mitad y dejar la otra seria cerrar F-027 y reabrirla con
F-024.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest

from tests.f027_escenarios import (
    CATALOGO_MAHORSA,
    Escenario,
    LineaContrato,
    valorar,
)

#: El importe que sale hoy por este camino, sin marca de revision.
IMPORTE_MEDIDO_MAL = 468763.4


def _mahorsa_con_unidad_kg(numero: str = "58826-KG") -> Escenario:
    """El 58826 tal como quedara cuando F-024 haga su trabajo.

    Albaran en KG, contrato en TN, partida del albaran distinta de la
    que caso IA3 -> ``partida_action='new_line_created'`` y derivada con
    la unidad del CONTRATO (TN) y su precio (15,43 EUR/TN).
    """
    return Escenario(
        numero_albaran=numero,
        cantidad=30380.0,
        unidad_albaran="KG",
        codigo_partida_albaran="P4.22.01.03.07",
        matched_contrato_line_id=25980,
        precio_contrato_db=15.43,
        contrato=CATALOGO_MAHORSA,
    )


# --------------------------------------------------------------------- #
# R6 — la derivada es quien pone el precio, luego ella fija el destino
# --------------------------------------------------------------------- #

def test_f027_r6_la_derivada_lleva_la_unidad_del_contrato():
    """Precondicion del requisito, medida y no supuesta.

    Si algun dia ``_build_derived`` dejara de heredar la unidad del
    contrato, R6 y R7 dejarian de hablar del mismo caso y este test lo
    dice antes que ellos.
    """
    _, linea = valorar(_mahorsa_con_unidad_kg())

    derivada = linea.derived_contrato_line_record
    assert derivada is not None
    assert linea.partida_action == "new_line_created"
    # La derivada lleva la unidad y el precio del CONTRATO, no los del
    # albaran: es ella quien multiplica.
    assert derivada.unidad_medida == "TN"
    assert derivada.precio_unitario == pytest.approx(15.43)
    assert linea.unidad_albaran == "KG"


def test_f027_r6_se_convierte_hacia_la_unidad_de_la_derivada():
    """R6: destino = ``derived_line.unidad_medida``, no ``unidad_albaran``.

    Con el destino viejo (``KG``) el factor era 1; con el correcto
    (``TN``) es 0,001. El factor persistido es la prueba observable de
    a que unidad se convirtio.
    """
    _, linea = valorar(_mahorsa_con_unidad_kg())

    assert linea.factor_conversion == pytest.approx(0.001)
    assert linea.cantidad_convertida == pytest.approx(30.38)


# --------------------------------------------------------------------- #
# R7 — el euro
# --------------------------------------------------------------------- #

def test_f027_r7_con_kg_leido_el_importe_ya_no_es_de_cientos_de_miles():
    """R7: 30.380 KG a 15,43 EUR/TN son 468,76 EUR."""
    cabecera, linea = valorar(_mahorsa_con_unidad_kg())

    assert linea.importe_calculado != pytest.approx(IMPORTE_MEDIDO_MAL)
    assert linea.importe_calculado == pytest.approx(468.76)
    assert cabecera.total_valorado == pytest.approx(468.76)


def test_f027_r7_la_cantidad_cruda_se_conserva_junto_a_la_convertida():
    """R20 por este camino: los 30.380 KG leidos siguen ahi."""
    _, linea = valorar(_mahorsa_con_unidad_kg())

    assert linea.cantidad_albaran == pytest.approx(30380.0)
    assert linea.cantidad_convertida == pytest.approx(30.38)
    assert linea.unidad_albaran == "KG"
    assert linea.unidad_contrato == "TN"


# --------------------------------------------------------------------- #
# Compatibilidad — el caso para el que se escribio la linea vieja
# --------------------------------------------------------------------- #

def test_f027_r6_derivada_sin_linea_de_contrato_se_comporta_igual_que_antes():
    """Sin linea de contrato de referencia, la derivada hereda la unidad
    del albaran: destino viejo y nuevo COINCIDEN.

    ``_build_derived`` inicializa ``unidad = unidad_albaran`` y solo la
    pisa si la linea casada por la IA trae unidad. Ese es exactamente el
    caso para el que se escribio ``unidad_contrato_para_conversion =
    unidad_albaran``. El cambio de F-027 es un superconjunto correcto,
    no una inversion: aqui no se mueve nada.
    """
    _, linea = valorar(
        Escenario(
            numero_albaran="derivada-sin-ia-match",
            cantidad=30380.0,
            unidad_albaran="KG",
            codigo_partida_albaran="P9.99.SIN.CATALOGO",
            matched_contrato_line_id=None,
            precio_contrato_db=15.43,
            contrato=CATALOGO_MAHORSA,
        )
    )

    derivada = linea.derived_contrato_line_record
    assert derivada is not None
    assert derivada.unidad_medida == "KG"
    # Mismo comportamiento que antes del cambio: factor 1, cantidad cruda.
    assert linea.factor_conversion == pytest.approx(1.0)
    assert linea.cantidad_convertida == pytest.approx(30380.0)


def test_f027_r6_sin_derivada_el_destino_sigue_siendo_la_unidad_de_contrato():
    """Cuando la IA casa una linea en la partida del albaran no hay
    derivada, y el destino es —como siempre— la unidad del contrato.
    """
    en_su_partida = LineaContrato(
        contrato_line_id=25972,
        descripcion="SUMINISTRO DE GRAVA 20/40",
        unidad_medida="TN",
        precio_unitario=12.87,
        codigo_partida="P4.22.01.03.07",
    )
    _, linea = valorar(
        Escenario(
            numero_albaran="sin-derivada",
            cantidad=30380.0,
            unidad_albaran="KG",
            codigo_partida_albaran="P4.22.01.03.07",
            matched_contrato_line_id=25972,
            precio_contrato_db=12.87,
            contrato=(en_su_partida,),
        )
    )

    assert linea.derived_contrato_line_record is None
    assert linea.partida_action == "existing_matched"
    assert linea.unidad_contrato == "TN"
    assert linea.cantidad_convertida == pytest.approx(30.38)
    assert linea.importe_calculado == pytest.approx(390.99)
