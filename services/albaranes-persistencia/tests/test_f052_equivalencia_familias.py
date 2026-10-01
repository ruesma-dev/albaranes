# tests/test_f052_equivalencia_familias.py
"""F-052 T6 · el texto agregado da las MISMAS familias que el texto por
líneas (R4).

Antes de F-052 el texto de familia de cada proveedor era la
concatenación, línea a línea, de nombre de contrato, descripción de
línea y código de producto no vacíos. La consulta agregada trae esos
valores recortados, distintos y ordenados. Para ``familias_de_texto``
tiene que dar igual: aquí se fija en Python sobre el fixture del doble.
Que la SQL real cumple esa semántica lo comprueba R30 (MANUAL, T21).
"""
from __future__ import annotations

import pytest
from application.services.familia_detector import familias_de_texto
from doble_sigrid_api import DobleSigridApi, Fixture, Linea, fixture_por_defecto


def _texto_por_lineas(lineas: list[Linea]) -> dict[str, str]:
    """El texto de hoy: por línea, los tres campos no vacíos (``strip``),
    en orden de llegada, unidos por espacio."""
    partes: dict[str, list[str]] = {}
    for ln in lineas:
        destino = partes.setdefault(ln.cif, [])
        for valor in (ln.res_ctr, ln.res_lin, ln.cod_pro):
            limpio = (valor or "").strip()
            if limpio:
                destino.append(limpio)
    return {cif: " ".join(v) for cif, v in partes.items()}


def _familias(texto: str | None) -> set[str]:
    # Igual que el resolver: familias_de_texto((r.texto or "").lower())
    return familias_de_texto((texto or "").lower())


def _familias_agregadas(fixture: Fixture, obra: str) -> dict[str, set[str]]:
    resumenes = DobleSigridApi(fixture).cliente().fetch_contratos_resumen_por_obra(codigo_obra=obra)
    return {r.cif: _familias(r.texto) for r in resumenes}


@pytest.mark.parametrize("obra", ["0691", "0668"])
def test_f052_r4_mismas_familias_por_cif_en_todo_el_fixture(obra):
    fixture = fixture_por_defecto()
    por_lineas = {cif: _familias(t) for cif, t in _texto_por_lineas(fixture.de_obra(obra)).items()}
    agregadas = _familias_agregadas(fixture, obra)
    assert set(agregadas) == set(por_lineas)
    diferencias = {
        cif: (por_lineas[cif], agregadas[cif])
        for cif in por_lineas if agregadas[cif] != por_lineas[cif]
    }
    assert diferencias == {}


def test_f052_r4_el_fixture_no_es_trivial():
    """Sin señal de familia la equivalencia no probaría nada."""
    por_lineas = _texto_por_lineas(fixture_por_defecto().de_obra("0691"))
    con_familia = [cif for cif, t in por_lineas.items() if _familias(t)]
    assert len(con_familia) >= 60
    assert len({f for t in por_lineas.values() for f in _familias(t)}) >= 5


def _caso(*valores_por_linea: tuple[str | None, str | None, str | None]) -> Fixture:
    lineas = tuple(
        Linea("0001", "B1", "PRUEBA, S.L.", 1, "C1/01", res_ctr, 100 + i, i + 1, res_lin, cod_pro)
        for i, (res_ctr, res_lin, cod_pro) in enumerate(valores_por_linea)
    )
    return Fixture(lineas=lineas, proveedores_global=())


@pytest.mark.parametrize(
    "fixture,esperadas",
    [
        pytest.param(
            _caso(*[("SUMINISTRO", "HORMIGON HA-25/B/20", "P1")] * 6, ("SUMINISTRO", "GASOLEO A", None)),
            {"hormigon", "combustible"},
            id="duplicados",
        ),
        pytest.param(
            _caso((None, "ACERO CORRUGADO B500S", None), (None, "ALQUILER GRUA", "P2"), ("OBRA", "PORTES", None)),
            {"acero", "maquinaria"},
            id="orden-directo",
        ),
        pytest.param(
            _caso(("OBRA", "PORTES", None), (None, "ALQUILER GRUA", "P2"), (None, "ACERO CORRUGADO B500S", None)),
            {"acero", "maquinaria"},
            id="orden-invertido",
        ),
        pytest.param(
            _caso(("   ", "  MORTERO M-7,5  ", ""), (None, "", None), ("", "   CONTENEDOR RCD", "  ")),
            {"mortero", "residuos"},
            id="espacios-y-vacios",
        ),
    ],
)
def test_f052_r4_casos_dirigidos(fixture, esperadas):
    por_lineas = _familias(_texto_por_lineas(fixture.lineas)["B1"])
    agregadas = _familias_agregadas(fixture, "0001")["B1"]
    assert por_lineas == esperadas
    assert agregadas == esperadas
