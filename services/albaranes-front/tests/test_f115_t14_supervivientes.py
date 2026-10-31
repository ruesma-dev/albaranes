# tests/test_f115_t14_supervivientes.py
"""F-115 T14 · mata el superviviente de la campaña de mutación.

Mutante 2 (``busqueda_contratos.py``, ``cambio_de_cabecera``): ``vista is not
None`` -> ``vista is None``. Ningún test pedía «obra» (mismo CIF que el rastro,
otra obra), así que el aviso «Obra cambiada…» de R11/R15 no estaba fijado.
"""
from __future__ import annotations

from application.services.busqueda_contratos import (
    CAMBIO_OBRA,
    CAMBIO_PROVEEDOR,
    cambio_de_cabecera,
)
from domain.models.review_models import BusquedaContratosVista


def _vista(cif):
    return BusquedaContratosVista(estado="desfasada", cif=cif, obra="0686")


def test_f115_r15_mismo_cif_que_el_rastro_es_cambio_de_obra():
    assert cambio_de_cabecera("a-11111111", _vista("A11111111")) == CAMBIO_OBRA


def test_f115_r11_otro_cif_es_cambio_de_proveedor():
    assert cambio_de_cabecera("B22222222", _vista("A11111111")) == CAMBIO_PROVEEDOR


def test_f115_r11_sin_rastro_o_sin_cif_en_el_rastro_es_proveedor():
    assert cambio_de_cabecera("A11111111", None) == CAMBIO_PROVEEDOR
    assert cambio_de_cabecera("A11111111", _vista(None)) == CAMBIO_PROVEEDOR
