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


# --- T3 · parte pura del subcomando `lineas` ---------------------------------

from evals import contratos  # noqa: E402  (el módulo nace en T3)

_COLUMNAS = [
    "contrato_ide",
    "linea_sigrid",
    "codigo_producto",
    "descripcion_recurso",
    "unidad",
    "precio_unitario",
    "codigo_partida",
]


def _caso(caso_id: str, contrato: str | None, lineas: int = 0, condiciones=None) -> dict:
    return {
        "caso_id": caso_id,
        "tipologia": "Generico-Suministros",
        "tablas": {
            "caso": [{"caso_id": caso_id, "contrato_codigo": contrato}],
            "contrato_lineas": [
                {"caso_id": caso_id, "codigo_producto": f"C{n}", "precio_unitario": 1}
                for n in range(lineas)
            ],
            "condiciones": condiciones or [],
            "lineas_albaran": [],
        },
    }


def test_f084_r1_un_contrato_por_codigo_con_sus_casos_sin_lineas():
    inputs = {
        "GEN-002": _caso("GEN-002", "CTSU25/0317"),
        "GEN-003": _caso("GEN-003", "CTSU25/0317"),
        "HOR-001": _caso("HOR-001", "CTSU24/0518"),
        "SIN-001": _caso("SIN-001", None),
    }

    assert contratos.contratos_de_casos(inputs) == {
        "CTSU24/0518": ["HOR-001"],
        "CTSU25/0317": ["GEN-002", "GEN-003"],
    }


def test_f084_r6_los_casos_con_lineas_no_se_importan():
    inputs = {
        "RES-001": _caso("RES-001", "CTSU24/0228", lineas=6),
        "RES-008": _caso("RES-008", "CTSU24/0228"),
        "RES-006": _caso("RES-006", "CTSU24/0402", lineas=1),
    }

    assert contratos.contratos_de_casos(inputs) == {"CTSU24/0228": ["RES-008"]}


def test_f084_r1_el_codigo_en_interrogante_o_vacio_no_cuenta():
    inputs = {"A": _caso("A", "@@NO_COMPARAR@@"), "B": _caso("B", "  ")}

    assert contratos.contratos_de_casos(inputs) == {}


def test_f084_r1_filas_de_respuesta_traduce_las_columnas_de_sigrid():
    filas = [
        [7, 101, "P1", "TORNILLO M8", "UD", 0.25, "CI.1"],
        [7, 102, None, "PORTE", "PA", 30, None],
    ]

    lineas = contratos.filas_de_respuesta(_COLUMNAS, filas, "CTSU26/0058")

    assert lineas == [
        {"codigo_producto": "P1", "descripcion_recurso": "TORNILLO M8", "unidad": "UD",
         "precio_unitario": 0.25, "codigo_partida": "CI.1", "linea_sigrid": 101},
        {"codigo_producto": None, "descripcion_recurso": "PORTE", "unidad": "PA",
         "precio_unitario": 30, "codigo_partida": None, "linea_sigrid": 102},
    ]


def test_f084_r5_ningun_contrato_con_ese_codigo_es_un_error_del_contrato():
    with pytest.raises(contratos.ErrorContrato, match="ningún contrato"):
        contratos.filas_de_respuesta(_COLUMNAS, [], "CTSU26/0058")


def test_f084_r5_mas_de_un_ctr_ide_es_un_error_del_contrato():
    filas = [[7, 101, "P1", "X", "UD", 1, None], [8, 201, "P1", "X", "UD", 1, None]]

    with pytest.raises(contratos.ErrorContrato, match="2 contratos"):
        contratos.filas_de_respuesta(_COLUMNAS, filas, "CTSU26/0058")


def test_f084_r1_filas_por_caso_repite_las_lineas_en_cada_caso():
    lineas = [{"codigo_producto": "P1", "descripcion_recurso": "X", "unidad": "UD",
               "precio_unitario": 1, "codigo_partida": None, "linea_sigrid": 101}]

    filas = contratos.filas_por_caso(lineas, ["GEN-002", "GEN-003"], "2026-10-22")

    assert [f["caso_id"] for f in filas] == ["GEN-002", "GEN-003"]
    assert all(f["linea_sigrid"] == 101 and f["codigo_producto"] == "P1" for f in filas)
    assert filas[0]["comentario"] == "importada de sigrid-api el 2026-10-22 (F-084)"
    assert set(filas[0]) == {
        "caso_id", "codigo_producto", "descripcion_recurso", "unidad",
        "precio_unitario", "codigo_partida", "linea_sigrid", "comentario",
    }


def _ia1(caso_id: str, fecha) -> dict:
    return {"caso_id": caso_id, "tablas": {"cabeceras": [{"caso_id": caso_id, "fecha": fecha}]}}


def test_f084_r9_la_fecha_que_falta_sale_de_ia1():
    inputs = {"FER-001": _caso("FER-001", "CTSU24/0454")}

    filas = contratos.condiciones_fecha(inputs, {"FER-001": _ia1("FER-001", "2026-06-05")})

    assert filas == [{"caso_id": "FER-001", "campo": "fecha_albaran", "valor": "2026-06-05",
                      "comentario": "fecha de IA1.cabeceras (F-084)"}]


def test_f084_r9_nunca_pisa_una_fecha_existente():
    condiciones = [{"caso_id": "RES-001", "campo": "fecha_albaran", "valor": "2024-07-03"}]
    inputs = {"RES-001": _caso("RES-001", "CTSU24/0228", condiciones=condiciones)}

    assert contratos.condiciones_fecha(inputs, {"RES-001": _ia1("RES-001", "2030-01-01")}) == []


@pytest.mark.parametrize("ia1", [{}, {"X": _ia1("X", "@@NO_COMPARAR@@")}, {"X": _ia1("X", None)}])
def test_f084_r9_sin_fecha_en_ia1_no_se_escribe_nada(ia1):
    assert contratos.condiciones_fecha({"X": _caso("X", "C")}, ia1) == []


def _ia3(*filas) -> dict:
    return {"tablas": {"lineas_valoradas": [
        {"num_linea": n, "precio_source": fuente, "precio_unitario_final": precio}
        for n, fuente, precio in filas
    ]}}


def test_f084_r10_cuenta_las_lineas_contrato_db_con_su_precio_importado():
    ia3 = _ia3((1, "contrato_db", 120), (2, "contrato_db", 95.5), (3, "albaran", 7), (4, "contrato_db", "@@NO_COMPARAR@@"))
    lineas = [{"precio_unitario": 120.0}, {"precio_unitario": 30}]

    assert contratos.precios_presentes(ia3, lineas) == (1, 2)
    assert contratos.precios_ausentes(ia3, lineas) == [2]


def test_f084_r10_sin_lineas_contrato_db_no_hay_nada_que_controlar():
    assert contratos.precios_presentes(_ia3((1, "albaran", 1)), []) == (0, 0)
    assert contratos.precios_presentes({}, [{"precio_unitario": 1}]) == (0, 0)
