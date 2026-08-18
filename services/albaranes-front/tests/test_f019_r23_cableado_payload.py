# tests/test_f019_r23_cableado_payload.py
"""F-019 R23 · el cableado payload -> recalculo, fijado por test.

Round trip 3 (2026-08-18). El reviewer observo que la linea que conecta
todo el arreglo con la realidad —la que traduce las lineas del formulario
del revisor en los mapas que consume ``_recalc_valuation_importes``— no
la ejecutaba NINGUN test: todos pasaban los mapas a mano al metodo
privado. Si esa traduccion se escribiera mal, el incidente volveria
entero y en silencio.

El matiz que se protege aqui es asimetrico y no es obvio:

  - las CANTIDADES se filtran con ``is not None`` (una linea sin cantidad
    conserva la que ya tenia la fila valorada);
  - los DESCUENTOS **no** se filtran (``None`` significa «el revisor ha
    borrado el descuento» y tiene que llegar).

Escribir el segundo como el primero es un cambio de una palabra que
ningun test veia.

Sin red, sin BBDD, sin LLM: los payloads son modelos Pydantic puros.
"""
from __future__ import annotations

import pytest

from domain.models.review_models import (
    MergeDocumentUpdatePayload,
    MergeLinePayload,
)


def _payload(*lineas: MergeLinePayload) -> MergeDocumentUpdatePayload:
    return MergeDocumentUpdatePayload(lines=list(lineas))


@pytest.fixture
def cableado(repositorio):
    return repositorio


# ------------------------------------------------------------------ #
# Descuentos
# ------------------------------------------------------------------ #
def test_f019_r23_el_descuento_del_payload_llega_al_recalculo(cableado):
    """Lo que el revisor escribe en la linea blanca viaja al importe."""
    resultado = cableado._descuentos_del_payload(
        _payload(MergeLinePayload(id=370, cantidad=108.0, descuento=40.0))
    )

    assert resultado == {370: 40.0}


def test_f019_r23_un_descuento_borrado_llega_como_none(cableado):
    """EL MATIZ: borrar el descuento tiene que tener efecto.

    Si este mapa filtrara los ``None`` —como si filtra el de cantidades—
    el recalculo caeria al descuento anterior guardado en
    ``descuento_albaran_aplicado`` y la linea seguiria descontando para
    siempre, sin que el revisor pudiera evitarlo.
    """
    resultado = cableado._descuentos_del_payload(
        _payload(MergeLinePayload(id=370, cantidad=108.0, descuento=None))
    )

    assert resultado == {370: None}
    assert 370 in resultado, "el descuento borrado no puede desaparecer del mapa"


def test_f019_r23_las_lineas_sin_id_no_entran(cableado):
    """Una linea nueva sin persistir todavia no tiene fila que recalcular."""
    resultado = cableado._descuentos_del_payload(
        _payload(
            MergeLinePayload(id=None, cantidad=1.0, descuento=10.0),
            MergeLinePayload(id=371, cantidad=2.0, descuento=20.0),
        )
    )

    assert resultado == {371: 20.0}


def test_f019_r23_el_payload_vacio_no_recalcula_nada(cableado):
    assert cableado._descuentos_del_payload(_payload()) == {}


# ------------------------------------------------------------------ #
# Cantidades
# ------------------------------------------------------------------ #
def test_f019_r23_la_cantidad_del_payload_llega_al_recalculo(cableado):
    resultado = cableado._cantidades_del_payload(
        _payload(MergeLinePayload(id=370, cantidad=108.0, descuento=40.0))
    )

    assert resultado == {370: 108.0}


def test_f019_r23_una_linea_sin_cantidad_conserva_la_suya(cableado):
    """Al reves que el descuento: sin cantidad, manda la ya guardada.

    Una linea sin cantidad en el formulario no significa «vale 0»; el
    recalculo tiene que caer a ``cantidad_albaran`` de la fila.
    """
    resultado = cableado._cantidades_del_payload(
        _payload(MergeLinePayload(id=370, cantidad=None, descuento=40.0))
    )

    assert resultado == {}


def test_f019_r23_los_dos_mapas_no_se_filtran_igual(cableado):
    """La asimetria, afirmada de frente para que nadie la 'arregle'."""
    payload = _payload(
        MergeLinePayload(id=370, cantidad=None, descuento=None),
    )

    assert cableado._cantidades_del_payload(payload) == {}
    assert cableado._descuentos_del_payload(payload) == {370: None}
