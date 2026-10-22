# tests/test_f084_contratos.py
"""F-084 · A y B — Líneas y documento del contrato (`python -m evals.contratos`).

R1–R11 (líneas de sigrid-api al libro INPUTS) y R29–R31, R34 (documento y
cabecera del contrato). Sin red ni BBDD (R25): sigrid-api con
`httpx.MockTransport`, la BBDD y SharePoint con dobles y los libros en
`tmp_path`, construidos por el `constructor_gt` de `conftest.py`.
"""

from __future__ import annotations

import json
from pathlib import Path

import openpyxl
import pytest

from evals import conversor
from evals.revision import escritura

RAIZ = Path(__file__).resolve().parent.parent

_INPUTS = "INPUTS.xlsx"
#: Índices de tabla dentro de cada pestaña de INPUTS (una por pestaña).
_CASOS = (_INPUTS, "CASOS", 0)
_LINEAS = (_INPUTS, "LINEAS_ALBARAN", 0)
_CONTRATO = (_INPUTS, "CONTRATO_LINEAS", 0)
_CONDICIONES = (_INPUTS, "CONDICIONES", 0)


def _encabezados(ruta: Path, pestana: str) -> list[str]:
    libro = openpyxl.load_workbook(ruta)
    try:
        hoja = libro[pestana]
        return [c.value for c in hoja[2] if c.value is not None]
    finally:
        libro.close()


# --- R11 · identidad de una fila de CONTRATO_LINEAS ---------------------------


def test_f084_r11_la_clave_de_contrato_lineas_incluye_linea_sigrid():
    assert escritura.CLAVES_DE_TABLA["contrato_lineas"] == (
        "caso_id",
        "codigo_producto",
        "linea_sigrid",
    )


def test_f084_r11_dos_lineas_con_el_mismo_producto_no_se_funden():
    """Un contrato de Sigrid repite producto en dos posiciones: son dos filas."""
    existentes = [
        {"caso_id": "GEN-001", "codigo_producto": "P1", "linea_sigrid": 11, "precio_unitario": 1},
    ]
    nuevas = [
        {"caso_id": "GEN-001", "codigo_producto": "P1", "linea_sigrid": 11, "precio_unitario": 1},
        {"caso_id": "GEN-001", "codigo_producto": "P1", "linea_sigrid": 12, "precio_unitario": 2},
    ]
    fundidas = escritura.fundir_filas(
        existentes, nuevas, escritura.CLAVES_DE_TABLA["contrato_lineas"]
    )

    assert [(f["linea_sigrid"], f["precio_unitario"]) for f in fundidas] == [(11, 1), (12, 2)]


def test_f084_r11_el_conversor_lleva_linea_sigrid_al_fixture(tmp_path, constructor_gt):
    """El conversor lee por encabezado: la columna nueva llega sola al JSON."""
    ground_truth = constructor_gt(
        tmp_path / "gt",
        filas={
            _CASOS: [["GEN-001", "Generico-Suministros", "IA3", "manual", "CTSU26/0058", "x"]],
            _LINEAS: [["GEN-001", 1, "TORNILLO", 10, "UD", 1.5, None, 15, None, None]],
            _CONTRATO: [["GEN-001", "P1", "TORNILLO", "UD", 1.5, "CI.1", "importado", 4711]],
        },
    )
    libro = openpyxl.load_workbook(ground_truth / _INPUTS)
    libro["CONTRATO_LINEAS"].cell(row=2, column=8, value="linea_sigrid")
    libro.save(ground_truth / _INPUTS)

    fixtures = tmp_path / "fixtures"
    conversor.main(["--ground-truth", str(ground_truth), "--fixtures", str(fixtures)])
    caso = json.loads((fixtures / "inputs" / "GEN-001.json").read_text(encoding="utf-8"))

    assert caso["tablas"]["contrato_lineas"][0]["linea_sigrid"] == 4711

