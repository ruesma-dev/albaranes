# tests/test_f052_paginacion_cliente.py
"""F-052 T4 · ``header_and_lines`` y ``search_proveedores`` paginan
(R11–R13). Sobre el doble de sigrid-api, sin red.

Son las dos únicas consultas del cliente de contratos de sv3 que pueden
pasar de una página (design §3): las líneas de un contrato alimentan la
valoración y el UPSERT por ``sigrid_ide`` (todas o ninguna) y la lista
global de proveedores ya tiene 3.543 filas.
"""
from __future__ import annotations

import pytest

from doble_sigrid_api import (
    CIF_GRANDE_0668,
    CIF_SALMEDINA,
    CONTRATO_SALMEDINA,
    TOTAL_PROVEEDORES_GLOBAL,
    DobleSigridApi,
    fixture_por_defecto,
)
from ruesma_comun.sigrid import SigridRespuestaTruncada

_ORDER_BY_LINEAS = "ORDER BY con_ctr.cod, ctr.ide, ctrpro.pos, ctrpro.ide"
_ORDER_BY_PROVEEDORES = "ORDER BY prv.cif, prv.raz"


def _peticiones_lineas(doble: DobleSigridApi) -> list[dict]:
    return doble.peticiones_con("AS contrato_ide")


def _peticiones_proveedores(doble: DobleSigridApi) -> list[dict]:
    return doble.peticiones_con("prv.cif IS NOT NULL AND con.emp = 1")


# ------------------------------------------------------------------ #
# R11 · fetch_contratos trae TODAS las líneas, agrupadas y en orden
# ------------------------------------------------------------------ #
def test_f052_r11_fetch_contratos_1200_lineas_agrupadas_en_orden():
    doble = DobleSigridApi()
    contratos = doble.cliente().fetch_contratos(
        cif_proveedor=CIF_GRANDE_0668, codigo_obra_normalizado="0668",
    )
    assert [c.codigo_contrato for c in contratos] == ["CTGR25/0001", "CTGR25/0002"]
    assert [len(c.lines) for c in contratos] == [500, 700]
    for c in contratos:
        assert [ln.linea for ln in c.lines] == list(range(1, len(c.lines) + 1))
    ides = [ln.sigrid_ide for c in contratos for ln in c.lines]
    assert len(set(ides)) == 1200

    peticiones = _peticiones_lineas(doble)
    assert [p["parameters"] for p in peticiones] == [
        [CIF_GRANDE_0668, "0668", 0, 1000],
        [CIF_GRANDE_0668, "0668", 1000, 1000],
    ]
    for p in peticiones:
        assert _ORDER_BY_LINEAS in p["sql"]
        assert p["sql"].rstrip().endswith("OFFSET ? ROWS FETCH NEXT ? ROWS ONLY")
        assert p["max_rows"] == 1001


def test_f052_r11_caso_normal_una_sola_llamada():
    doble = DobleSigridApi()
    contratos = doble.cliente().fetch_contratos(
        cif_proveedor=CIF_SALMEDINA, codigo_obra_normalizado="0691",
    )
    assert [c.codigo_contrato for c in contratos] == [CONTRATO_SALMEDINA]
    assert len(contratos[0].lines) == 5
    assert len(_peticiones_lineas(doble)) == 1


def test_f052_r11_pagina_lineas_configurable():
    doble = DobleSigridApi()
    contratos = doble.cliente(pagina_lineas=100).fetch_contratos(
        cif_proveedor=CIF_GRANDE_0668, codigo_obra_normalizado="0668",
    )
    assert sum(len(c.lines) for c in contratos) == 1200
    peticiones = _peticiones_lineas(doble)
    assert len(peticiones) == 13
    assert peticiones[-1]["parameters"][-2:] == [1200, 100]
    assert {p["max_rows"] for p in peticiones} == {101}


# ------------------------------------------------------------------ #
# R12 · search_proveedores devuelve la lista global completa
# ------------------------------------------------------------------ #
def test_f052_r12_search_proveedores_devuelve_los_3543():
    doble = DobleSigridApi()
    proveedores = doble.cliente().search_proveedores()
    assert len(proveedores) == TOTAL_PROVEEDORES_GLOBAL
    assert proveedores == sorted(fixture_por_defecto().proveedores_global)
    [peticion] = _peticiones_proveedores(doble)
    assert _ORDER_BY_PROVEEDORES in peticion["sql"]
    assert peticion["parameters"] == [0, 5000]
    assert peticion["max_rows"] == 5001


def test_f052_r12_hallazgo_el_max_rows_pedido_llega_a_sigrid_api():
    """Antes de F-052, ``search_proveedores(max_rows=5000)`` recibía el
    parámetro pero ``_post_sql_read`` enviaba ``self._max_rows`` (1.000):
    la lista global se cortaba a 1.000 en silencio."""
    doble = DobleSigridApi()
    proveedores = doble.cliente().search_proveedores(max_rows=5000)
    [peticion] = _peticiones_proveedores(doble)
    assert peticion["max_rows"] > 5000
    assert len(proveedores) == TOTAL_PROVEEDORES_GLOBAL


def test_f052_r12_search_proveedores_pagina_si_la_pagina_es_menor():
    doble = DobleSigridApi()
    proveedores = doble.cliente().search_proveedores(max_rows=1000)
    assert len(proveedores) == TOTAL_PROVEEDORES_GLOBAL
    assert [p["parameters"] for p in _peticiones_proveedores(doble)] == [
        [0, 1000], [1000, 1000], [2000, 1000], [3000, 1000],
    ]


# ------------------------------------------------------------------ #
# R13 · tope de páginas → excepción
# ------------------------------------------------------------------ #
def test_f052_r13_fetch_contratos_tope_de_paginas_lanza():
    doble = DobleSigridApi()
    cliente = doble.cliente(pagina_lineas=100, max_paginas=3)
    with pytest.raises(SigridRespuestaTruncada) as info:
        cliente.fetch_contratos(cif_proveedor=CIF_GRANDE_0668, codigo_obra_normalizado="0668")
    assert info.value.etiqueta == "header_and_lines"
    assert info.value.filas == 300
    assert len(_peticiones_lineas(doble)) == 3


def test_f052_r13_search_proveedores_tope_de_paginas_lanza():
    doble = DobleSigridApi()
    with pytest.raises(SigridRespuestaTruncada) as info:
        doble.cliente(max_paginas=3).search_proveedores(max_rows=1000)
    assert info.value.etiqueta == "search_proveedores"
    assert len(_peticiones_proveedores(doble)) == 3
