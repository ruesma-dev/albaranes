# tests/test_f073_incidencia_0694.py
"""F-073 · R18 — el albarán de la incidencia 0694, por las tres rutas.

Correo «0694» del 2026-10-15: la IA leyó el CIF de Ruesma (A81873903), sv3
lo descartó (F-063) y buscó por nombre «FEYMACO, S.A.» / «TEYMACO, S.A.».
HIERROS RODRIGO y FEYMACO empataban a 0,50 y el atajo elegía el primero.
Con F-073 el merge acaba con FEYMACO, origen ``deterministic`` y su
contrato. Pipeline real con el doble de sigrid-api; sin red ni BBDD.
"""
from __future__ import annotations

import pytest
from doble_sigrid_api import (
    CIF_FEYMACO,
    CIF_HIERROS_RODRIGO,
    CIF_RUESMA,
    CONTRATO_FEYMACO_F073,
    NOMBRES_LEIDOS_F073,
    RAZ_FEYMACO_REAL,
    RAZ_HIERROS_RODRIGO,
    DobleSigridApi,
    fixture_f073,
)
from test_f063_cif_propio import RUTAS, _cifs_preguntados, _merge, _ruta

OBRA = "0694"


@pytest.mark.parametrize("leido", NOMBRES_LEIDOS_F073)
@pytest.mark.parametrize("ruta", RUTAS)
def test_f073_r18_el_albaran_de_la_incidencia_acaba_con_feymaco_y_su_contrato(ruta, leido):
    doble = DobleSigridApi(fixture_f073())
    merge = _merge(ruta, CIF_RUESMA, leido, OBRA)

    _ruta(ruta, merge, doble, CIF_RUESMA, leido, OBRA)

    assert (merge.cif, merge.origen) == (CIF_FEYMACO, "deterministic")
    assert merge.rastro[-1] == (CIF_FEYMACO, OBRA, "encontrados")
    assert [c.codigo_contrato for c in merge.contratos] == [CONTRATO_FEYMACO_F073]
    # La búsqueda de contratos se hizo con FEYMACO, nunca con HIERROS ni el cliente.
    assert {p["parameters"][0] for p in doble.peticiones_con("AS contrato_ide")} == {CIF_FEYMACO}
    assert CIF_RUESMA not in _cifs_preguntados(doble)
    # Solo el motivo del descarte del CIF propio (F-063): no hay empate.
    assert merge.lista_motivos() == [f"proveedor_cif_propio:{CIF_RUESMA}"]


def test_f073_r18_control_con_el_criterio_de_antes_las_dos_razones_empataban():
    """Control: con ``_match_score`` (atajo y paso 2 antes de F-073) las dos
    razones del fixture sacan 0,50, y la agregada llega por CIF (A19… antes
    que A28…): ganaba HIERROS RODRIGO."""
    from application.services.header_resolver_service import _match_score, _norm

    for leido in NOMBRES_LEIDOS_F073:
        assert _match_score(_norm(leido), _norm(RAZ_HIERROS_RODRIGO)) == 0.5
        assert _match_score(_norm(leido), _norm(RAZ_FEYMACO_REAL)) == 0.5
    resumenes = DobleSigridApi(fixture_f073()).cliente().fetch_contratos_resumen_por_obra(codigo_obra=OBRA)
    assert [r.cif for r in resumenes] == [CIF_HIERROS_RODRIGO, CIF_FEYMACO]
