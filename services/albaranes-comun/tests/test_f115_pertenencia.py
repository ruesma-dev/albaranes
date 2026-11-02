# tests/test_f115_pertenencia.py
"""F-115 · R1: ¿el contrato es del albarán (mismo proveedor y misma obra)?

Una fila de ``albaran_contratos_merge`` es del albarán si su CIF y su obra
coinciden con los del merge, normalizados con ``normalizar_cif`` y
``canonizar_codigo_obra``. Un lado del contrato vacío (fila legada) no
descalifica; un lado del albarán vacío, sí (D2).
"""
from __future__ import annotations

import pytest

from ruesma_comun.contratos import contrato_es_del_albaran as reexportada
from ruesma_comun.contratos.pertenencia import contrato_es_del_albaran


def _es(contrato_cif, contrato_obra, albaran_cif, albaran_obra) -> bool:
    return contrato_es_del_albaran(
        contrato_cif=contrato_cif,
        contrato_obra=contrato_obra,
        albaran_cif=albaran_cif,
        albaran_obra=albaran_obra,
    )


def test_f115_r1_reexportada_desde_contratos():
    assert reexportada is contrato_es_del_albaran


@pytest.mark.parametrize(
    ("contrato_cif", "contrato_obra", "albaran_cif", "albaran_obra"),
    [
        ("B123", "0686", "B123", "0686"),
        ("b-123", "0686", "B123", "0686"),
        ("B123", "686", "b 123", "0686"),
        ("ESB66056201", " 0686 ", "B66056201", "686"),
        ("B123", "var", "B123", "VAR"),
    ],
)
def test_f115_r1_mismo_proveedor_y_obra_en_cualquier_formato(
    contrato_cif, contrato_obra, albaran_cif, albaran_obra
):
    assert _es(contrato_cif, contrato_obra, albaran_cif, albaran_obra) is True


def test_f115_r1_otro_proveedor_no_es_del_albaran():
    assert _es("A111", "0686", "B123", "0686") is False


def test_f115_r1_otra_obra_no_es_del_albaran():
    assert _es("B123", "0700", "B123", "0686") is False


@pytest.mark.parametrize(
    ("contrato_cif", "contrato_obra"),
    [(None, "0686"), ("", "0686"), ("  ", "686"), ("B123", None), ("B123", " "), (None, None)],
)
def test_f115_r1_fila_legada_sin_un_lado_no_descalifica(contrato_cif, contrato_obra):
    assert _es(contrato_cif, contrato_obra, "B123", "0686") is True


def test_f115_r1_fila_legada_sin_cif_pero_con_otra_obra_si_descalifica():
    assert _es(None, "0700", "B123", "0686") is False


def test_f115_r1_fila_legada_sin_obra_pero_con_otro_cif_si_descalifica():
    assert _es("A111", None, "B123", "0686") is False


@pytest.mark.parametrize(
    ("albaran_cif", "albaran_obra"),
    [(None, "0686"), ("", "0686"), ("-", "0686"), ("B123", None), ("B123", "  ")],
)
def test_f115_r1_albaran_sin_cif_o_sin_obra_no_tiene_contratos(albaran_cif, albaran_obra):
    assert _es("B123", "0686", albaran_cif, albaran_obra) is False
    assert _es(None, None, albaran_cif, albaran_obra) is False


def test_f115_r1_solo_argumentos_por_nombre():
    with pytest.raises(TypeError):
        contrato_es_del_albaran("B123", "0686", "B123", "0686")  # type: ignore[misc]


def test_f115_t2_version_0110():
    from pathlib import Path

    import ruesma_comun

    # F-110 sube a 0.12.0 (su test exige la exacta): desde 0.11.0, nunca menos,
    # como hicieron F-098, F-106 y F-113. Paquete y pyproject, iguales.
    assert tuple(int(x) for x in ruesma_comun.__version__.split(".")) >= (0, 11, 0)
    pyproject = (Path(ruesma_comun.__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{ruesma_comun.__version__}"' in pyproject
