# tests/test_f063_cifs_propios.py
"""F-063 · R1, R2 — CIF propios: el de Construcciones Ruesma nunca es el
proveedor de un albarán.

Incidencia del 2026-10-08: la IA leyó A81873903 (Construcciones Ruesma, el
cliente impreso en el albarán de FEYMACO) como CIF del proveedor.
"""
from __future__ import annotations

import pytest
from ruesma_comun.proveedores import (
    CIFS_PROPIOS_POR_DEFECTO,
    cifs_propios,
    es_cif_propio,
)

RUESMA = "A81873903"


# ------------------------------------------------------------------ #
# R1 · la lista
# ------------------------------------------------------------------ #
def test_f063_r1_por_defecto_solo_construcciones_ruesma():
    assert CIFS_PROPIOS_POR_DEFECTO == {RUESMA: "Construcciones Ruesma"}
    assert cifs_propios(None) == frozenset({RUESMA})
    assert cifs_propios("") == frozenset({RUESMA})
    assert cifs_propios("  , ;  ") == frozenset({RUESMA})


def test_f063_r1_la_configuracion_amplia_normalizando_y_con_cualquier_separador():
    assert cifs_propios("b-12345678, esb87654321;C11111111  d22222222") == frozenset({
        RUESMA, "B12345678", "B87654321", "C11111111", "D22222222",
    })


def test_f063_r1_la_configuracion_nunca_quita_el_de_ruesma():
    assert RUESMA in cifs_propios("B12345678")
    assert cifs_propios(RUESMA) == frozenset({RUESMA})


def test_f063_r1_devuelve_un_conjunto_inmutable():
    assert isinstance(cifs_propios(None), frozenset)


# ------------------------------------------------------------------ #
# R2 · la comparación
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("valor", [RUESMA, "a-81873903", "ESA81873903", " A81873903 ", "a 81.873.903"])
def test_f063_r2_el_cif_de_ruesma_es_propio_en_cualquier_forma(valor):
    assert es_cif_propio(valor, cifs_propios(None)) is True


@pytest.mark.parametrize("valor", [None, "", "   ", "A28733558", "A8187390", "A818739031"])
def test_f063_r2_lo_demas_no_es_propio(valor):
    assert es_cif_propio(valor, cifs_propios(None)) is False


def test_f063_r2_respeta_la_lista_que_recibe():
    assert es_cif_propio("b12345678", frozenset({"B12345678"})) is True
    assert es_cif_propio(RUESMA, frozenset({"B12345678"})) is False
