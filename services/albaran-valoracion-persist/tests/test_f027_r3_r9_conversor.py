# tests/test_f027_r3_r9_conversor.py
"""F-027 · R3, R4, R5, R8, R9, R17, R21: el conversor, tal cual es.

Por que existe este fichero
---------------------------
La red de plausibilidad de toneladas de ``UnitConverter`` (>= 1000 sin
unidad contra un contrato en TN se reinterpreta como KG) esta escrita
desde julio de 2026 y **nunca se ha ejecutado en produccion**: el
``ValuationBuilder`` llamaba al conversor con ``cantidad=None`` a
proposito cuando las categorias de unidad no casaban, y la primera
guarda de ``convert`` salia por ``no_quantity_in_albaran`` antes de
llegar a la red. Resultado medido: los albaranes 58826 y 58878 de
MAHORSA valorados en 468.763,40 EUR y 462.282,80 EUR en vez de
centenas de euros.

Este fichero fija el comportamiento del conversor **aislado**, que es
correcto y que F-027 NO cambia (R18). Es la mitad de abajo de la
demostracion: si estos tests pasan y el importe sigue saliendo mal, el
defecto no esta aqui. La otra mitad —que el builder llegue de verdad a
esta red— vive en ``test_f027_r1_r2_r11_r13_builder.py``.

Sin red, sin BBDD, sin LLM: el unico fichero que se lee del disco es
``config/unit_registry.yaml``, dato versionado del propio servicio.
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def conversor():
    """``UnitConverter`` sobre el registro YAML real del servicio."""
    from application.services.unit_converter import UnitConverter
    from infrastructure.units.yaml_unit_registry import YamlUnitRegistry

    yaml_path = (
        Path(__file__).resolve().parents[1] / "config" / "unit_registry.yaml"
    )
    return UnitConverter(registry=YamlUnitRegistry(str(yaml_path)))


# --------------------------------------------------------------------- #
# R3 — la red de plausibilidad: >= 1000 sin unidad contra TN es KG
# --------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "albaran, cantidad, esperada",
    [
        ("58826", 30380.0, 30.38),
        ("58878", 29960.0, 29.96),
    ],
)
def test_f027_r3_cantidad_sin_unidad_contra_tn_se_reinterpreta_como_kg(
    conversor, albaran, cantidad, esperada,
):
    """Los dos albaranes de MAHORSA, con sus cantidades reales."""
    resultado = conversor.convert(
        cantidad=cantidad, unidad_albaran=None, unidad_contrato="TN",
    )

    assert resultado.cantidad_convertida == pytest.approx(esperada), albaran
    assert resultado.factor == pytest.approx(0.001)
    # ambiguous es lo que el builder lleva a review_required: una
    # cantidad reinterpretada NUNCA puede llegar muda al revisor.
    assert resultado.ambiguous is True
    assert resultado.reasons == ["cantidad_sin_unidad_reinterpretada_kg_a_tn"]


def test_f027_r3_el_umbral_de_1000_es_inclusivo(conversor):
    """Justo en el umbral se reinterpreta; un pelo por debajo, no.

    Fija el borde para que un cambio de ``>=`` a ``>`` no pase
    inadvertido (D3: el umbral es una decision, no un detalle).
    """
    en_el_umbral = conversor.convert(
        cantidad=1000.0, unidad_albaran=None, unidad_contrato="TN",
    )
    assert en_el_umbral.cantidad_convertida == pytest.approx(1.0)
    assert en_el_umbral.factor == pytest.approx(0.001)

    justo_debajo = conversor.convert(
        cantidad=999.99, unidad_albaran=None, unidad_contrato="TN",
    )
    assert justo_debajo.cantidad_convertida == pytest.approx(999.99)
    assert justo_debajo.factor == pytest.approx(1.0)


@pytest.mark.parametrize("literal_tn", ["TN", "tn", "Tn.", " t ", "TM", "Ton"])
def test_f027_r3_la_red_reconoce_los_literales_de_tonelada(
    conversor, literal_tn,
):
    """El contrato escribe la tonelada de muchas formas; todas cuentan."""
    resultado = conversor.convert(
        cantidad=30380.0, unidad_albaran=None, unidad_contrato=literal_tn,
    )

    assert resultado.cantidad_convertida == pytest.approx(30.38), literal_tn
    assert resultado.reasons == ["cantidad_sin_unidad_reinterpretada_kg_a_tn"]


def test_f027_r21_la_reinterpretacion_deja_traza_en_el_log(conversor, caplog):
    """R21: el warning del conversor es la traza de operacion.

    Su ausencia en los logs de produccion del 2026-08-18 es, en si
    misma, la prueba de que la red estaba muerta.
    """
    with caplog.at_level("WARNING"):
        conversor.convert(
            cantidad=30380.0, unidad_albaran=None, unidad_contrato="TN",
        )

    mensajes = [r.getMessage() for r in caplog.records]
    assert any(
        "reinterpretada como KG" in m and "30380" in m for m in mensajes
    ), mensajes


# --------------------------------------------------------------------- #
# R4 — implausible pero no seguro: se avisa, no se toca
# --------------------------------------------------------------------- #

def test_f027_r4_cantidad_entre_100_y_1000_solo_avisa(conversor):
    """500 TN es implausible para un camion, pero no imposible: no se toca."""
    resultado = conversor.convert(
        cantidad=500.0, unidad_albaran=None, unidad_contrato="TN",
    )

    assert resultado.cantidad_convertida == pytest.approx(500.0)
    assert resultado.factor == pytest.approx(1.0)
    assert resultado.ambiguous is True
    assert resultado.reasons == ["cantidad_tn_implausible_revisar"]


def test_f027_r4_cantidad_plausible_de_toneladas_no_se_toca_ni_se_avisa(
    conversor,
):
    """12 TN es la carga normal de un camion: ni conversion ni aviso."""
    resultado = conversor.convert(
        cantidad=12.0, unidad_albaran=None, unidad_contrato="TN",
    )

    assert resultado.cantidad_convertida == pytest.approx(12.0)
    assert resultado.factor == pytest.approx(1.0)
    assert resultado.ambiguous is False
    assert resultado.reasons == ["no_albaran_unit_assumed_same"]


# --------------------------------------------------------------------- #
# R5 — el conversor YA se niega a cruzar categorias incompatibles
# --------------------------------------------------------------------- #

def test_f027_r5_unidades_de_categorias_distintas_no_se_convierten(conversor):
    """UD contra M3: devuelve None por su cuenta.

    Es el argumento central del diseno de F-027: anular la cantidad en
    el builder no protegia de nada, porque el conversor ya se protege
    solo. Lo unico que conseguia era cegar el caso ``unknown``, que es
    donde vive la red de plausibilidad.
    """
    resultado = conversor.convert(
        cantidad=108.0, unidad_albaran="UD", unidad_contrato="M3",
    )

    assert resultado.cantidad_convertida is None
    assert resultado.factor is None
    assert "unit_category_mismatch_in_conversion" in resultado.reasons
    assert "category_mismatch:count!=volume" in resultado.reasons


def test_f027_r5_kg_contra_tn_con_ambas_unidades_si_se_convierte(conversor):
    """Misma categoria: la conversion es la del registro, sin red."""
    resultado = conversor.convert(
        cantidad=30380.0, unidad_albaran="KG", unidad_contrato="TN",
    )

    assert resultado.cantidad_convertida == pytest.approx(30.38)
    assert resultado.factor == pytest.approx(0.001)
    assert resultado.reasons == []


# --------------------------------------------------------------------- #
# R8, R9 — la guarda de cantidad ausente sigue protegiendo
# --------------------------------------------------------------------- #

def test_f027_r8_sin_cantidad_no_hay_nada_que_reinterpretar(conversor):
    """``cantidad=None`` sale por la primera guarda, sin tocar la red.

    Es la guarda que F-027 conserva intacta: cuando la cantidad falta
    de verdad, ``no_quantity_in_albaran`` dice la verdad.
    """
    resultado = conversor.convert(
        cantidad=None, unidad_albaran=None, unidad_contrato="TN",
    )

    assert resultado.cantidad_convertida is None
    assert resultado.factor is None
    assert resultado.ambiguous is False
    assert resultado.reasons == ["no_quantity_in_albaran"]


def test_f027_r9_cantidad_cero_es_cantidad_presente(conversor):
    """El 0 pasa la guarda: es un valor, no una ausencia.

    Importa porque la regla de residuos «un movimiento sin cantidad
    vale 1» del builder distingue justamente ese caso aguas abajo.
    """
    resultado = conversor.convert(
        cantidad=0.0, unidad_albaran=None, unidad_contrato="TN",
    )

    assert resultado.cantidad_convertida == pytest.approx(0.0)
    assert resultado.factor == pytest.approx(1.0)
    assert resultado.reasons == ["no_albaran_unit_assumed_same"]


def test_f027_r8_sin_unidad_de_contrato_la_cantidad_se_devuelve_tal_cual(
    conversor,
):
    """Sin unidad de destino no hay conversion posible: factor 1."""
    resultado = conversor.convert(
        cantidad=5.0, unidad_albaran=None, unidad_contrato=None,
    )

    assert resultado.cantidad_convertida == pytest.approx(5.0)
    assert resultado.factor == pytest.approx(1.0)
    assert resultado.reasons == ["no_contract_unit_assumed_same"]


# --------------------------------------------------------------------- #
# R17 — unidades ambiguas: factor 1 y revision
# --------------------------------------------------------------------- #

def test_f027_r17_unidad_ambigua_convierte_con_factor_1_y_marca_revision(
    conversor,
):
    """Un saco no tiene factor estable: se propone 1 y se marca."""
    resultado = conversor.convert(
        cantidad=5.0, unidad_albaran="SACO", unidad_contrato="UD",
    )

    assert resultado.cantidad_convertida == pytest.approx(5.0)
    assert resultado.factor == pytest.approx(1.0)
    assert resultado.ambiguous is True
    assert "ambiguous_unit_conversion" in resultado.reasons
