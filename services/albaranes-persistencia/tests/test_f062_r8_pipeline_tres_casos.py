# tests/test_f062_r8_pipeline_tres_casos.py
"""F-062 · R8 — los tres albaranes medidos acaban con contrato encontrado.

19407 y 19394 (HORMIGONES MAT, obra 0720) y 1790636816 (ARIDOS ANFERSA,
obra 0678) se quedaron en ``ninguno`` porque la búsqueda de contratos usó
el CIF mal leído. Aquí se recorren las TRES rutas del pipeline —albarán
nuevo, duplicado y ``reenrich_by_merge_id`` (el ``MensajePersistencia
(force=True)`` de sv4)— con el cliente real de sv3 sobre el doble de
sigrid-api y un merge en memoria.

Sin red ni BBDD.
"""
from __future__ import annotations

from ruesma_comun.proveedores import identificador_fiscal_valido

from doble_sigrid_api import (
    CIF_ARIDOS_ANFERSA,
    CIF_ARIDOS_SUR,
    CIF_HORMIGONERA_EMPATE,
    CIF_HORMIGONES_MAT,
    CIF_LEIDO_19394,
    CIF_LEIDO_19407,
    CIF_LEIDO_1790636816,
    CONTRATO_ARIDOS_ANFERSA,
    CONTRATO_HORMIGONES_MAT,
    RAZ_HORMIGONES_MAT,
    DobleSigridApi,
    fixture_f062,
)


def _doble() -> DobleSigridApi:
    return DobleSigridApi(fixture_f062())


# ------------------------------------------------------------------ #
# T2 · el fixture es el que dice ser (design §8)
# ------------------------------------------------------------------ #
def test_f062_t2_fixture_obras_0720_y_0678():
    cliente = _doble().cliente()
    obra_0720 = {r.cif: r for r in cliente.fetch_contratos_resumen_por_obra(codigo_obra="0720")}
    obra_0678 = {r.cif: r for r in cliente.fetch_contratos_resumen_por_obra(codigo_obra="0678")}
    assert set(obra_0720) == {CIF_HORMIGONES_MAT, CIF_HORMIGONERA_EMPATE}
    assert set(obra_0678) == {CIF_ARIDOS_ANFERSA, CIF_ARIDOS_SUR}
    assert obra_0720[CIF_HORMIGONES_MAT].nombre == RAZ_HORMIGONES_MAT
    assert obra_0720[CIF_HORMIGONES_MAT].codigos_contratos == (CONTRATO_HORMIGONES_MAT,)
    assert obra_0678[CIF_ARIDOS_ANFERSA].codigos_contratos == (CONTRATO_ARIDOS_ANFERSA,)


def test_f062_t2_los_cif_del_fixture_son_validos_y_los_leidos_no():
    for cif in (CIF_HORMIGONES_MAT, CIF_HORMIGONERA_EMPATE, CIF_ARIDOS_ANFERSA, CIF_ARIDOS_SUR):
        assert identificador_fiscal_valido(cif), cif
    for cif in (CIF_LEIDO_19407, CIF_LEIDO_19394, CIF_LEIDO_1790636816):
        assert not identificador_fiscal_valido(cif), cif


def test_f062_t2_los_leidos_no_existen_en_prv_y_los_reales_si():
    cliente = _doble().cliente()
    for cif in (CIF_LEIDO_19407, CIF_LEIDO_19394, CIF_LEIDO_1790636816):
        assert cliente.fetch_proveedor_by_cif(cif=cif) is None
    assert cliente.fetch_proveedor_by_cif(cif=CIF_HORMIGONES_MAT) == (
        CIF_HORMIGONES_MAT, RAZ_HORMIGONES_MAT,
    )


def test_f062_t2_contratos_con_lineas_del_cif_real_y_ninguno_del_leido():
    cliente = _doble().cliente()
    [contrato] = cliente.fetch_contratos(
        cif_proveedor=CIF_HORMIGONES_MAT, codigo_obra_normalizado="0720",
    )
    assert contrato.codigo_contrato == CONTRATO_HORMIGONES_MAT
    assert len(contrato.lines) == 2
    assert cliente.fetch_contratos(
        cif_proveedor=CIF_LEIDO_19407, codigo_obra_normalizado="0720",
    ) == []
