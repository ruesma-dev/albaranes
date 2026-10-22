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

from evals import contratos

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


# --- T4 · LectorSigrid y subcomando `lineas` (R2–R4, R7, R8, R10) ------------

import hashlib

import httpx
from ruesma_comun.sigrid import MAX_FILAS_POR_PETICION

_ENTORNO = {
    "SIGRID_API_BASE_URL": "https://sigrid.ejemplo.invalid",
    "SIGRID_API_FUNCTION_KEY": "clave-de-prueba",
    "SIGRID_API_DATABASE": "ruesma-pruebas",
}

#: Lo que «devuelve Sigrid» por código: filas, o `"truncada"` / `"500"`.
_SIGRID = {
    "CTSU24/0228": [[7, 701, "C9", "CAMBIO CONTENEDOR 9M3", "UD", 150, "CI.03A.7"]],
    "CTSU25/0317": "truncada",
    "CTSU24/0518": [
        [9, 901, "H25", "TORNILLO HORMIGON", "M3", 72.5, "01.02"],
        [9, 902, "H25", "TORNILLO HORMIGON", "M3", 80, "01.03"],
    ],
}


class _Sigrid:
    """sigrid-api de mentira: `httpx.MockTransport` y registro de peticiones."""

    def __init__(self, respuestas=None):
        self.respuestas = _SIGRID if respuestas is None else respuestas
        self.peticiones: list[httpx.Request] = []
        self.transporte = httpx.MockTransport(self._responder)

    def _responder(self, peticion: httpx.Request) -> httpx.Response:
        self.peticiones.append(peticion)
        codigo = json.loads(peticion.content)["parameters"][0]
        filas = self.respuestas.get(codigo, [])
        if filas == "truncada":
            return httpx.Response(
                200, json={"ok": True, "columns": _COLUMNAS, "rows": [], "truncated": True}
            )
        if filas == "500":
            return httpx.Response(500, json={"ok": False})
        return httpx.Response(
            200, json={"ok": True, "columns": _COLUMNAS, "rows": filas, "truncated": False}
        )


def _sha(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _escenario(tmp_path: Path, constructor_gt) -> tuple[Path, Path]:
    """Libro INPUTS con un RES escrito a mano y tres casos sin contrato, y sus fixtures."""
    ground_truth = constructor_gt(
        tmp_path / "gt",
        filas={
            _CASOS: [
                ["RES-001", "Residuos", "IA3", "manual", "CTSU24/0228", "a mano"],
                ["RES-008", "Residuos", "IA3", "manual", "CTSU24/0228", "sin contrato"],
                ["GEN-002", "Generico-Suministros", "IA3", "manual", "CTSU25/0317", "x"],
                ["HOR-001", "Hormigon", "IA3", "manual", "CTSU24/0518", "x"],
            ],
            _LINEAS: [
                [caso, 1, "LINEA", 1, "UD", None, None, None, None, None]
                for caso in ("RES-001", "RES-008", "GEN-002", "HOR-001")
            ],
            _CONTRATO: [
                ["RES-001", "C1", "CAMBIO CONTENEDOR 6M3", "UD", 120, "CI.03A.7", "a mano"],
                ["RES-001", "C2", "LLEVADA CONTENEDOR 6M3", "UD", 120, "CI.03A.7", "SEÑUELO"],
            ],
            _CONDICIONES: [["RES-001", "fecha_albaran", "2024-07-03", "a mano"]],
        },
    )
    fixtures = tmp_path / "fixtures"
    assert conversor.main(["--ground-truth", str(ground_truth), "--fixtures", str(fixtures)]) == 0
    for fase, caso, tablas in (
        ("IA1", "HOR-001", {"cabeceras": [{"caso_id": "HOR-001", "fecha": "2025-03-04"}]}),
        ("IA3", "HOR-001", {"lineas_valoradas": [
            {"num_linea": 1, "precio_source": "contrato_db", "precio_unitario_final": 72.5},
            {"num_linea": 2, "precio_source": "contrato_db", "precio_unitario_final": 99},
        ]}),
    ):
        (fixtures / fase).mkdir(parents=True, exist_ok=True)
        (fixtures / fase / f"{caso}.json").write_text(
            json.dumps({"caso_id": caso, "tablas": tablas}), encoding="utf-8"
        )
    return ground_truth, fixtures


def _lanzar(ground_truth, fixtures, informe, sigrid, *extra, entorno=None):
    return contratos.main(
        ["lineas", "--ground-truth", str(ground_truth), "--fixtures", str(fixtures),
         "--informe", str(informe), *extra],
        entorno=_ENTORNO if entorno is None else entorno,
        transport=sigrid.transporte,
    )


def _filas(ruta: Path, pestana: str) -> list[list]:
    libro = openpyxl.load_workbook(ruta)
    try:
        return [
            [c.value for c in fila]
            for fila in libro[pestana].iter_rows(min_row=3)
            if any(c.value is not None for c in fila)
        ]
    finally:
        libro.close()


def test_f084_r2_una_lectura_por_contrato_solo_de_lectura_y_parametrizada(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    sigrid = _Sigrid()

    _lanzar(ground_truth, fixtures, tmp_path / "informe.md", sigrid)

    assert len(sigrid.peticiones) == 3
    for peticion in sigrid.peticiones:
        cuerpo = json.loads(peticion.content)
        assert peticion.method == "POST"
        assert str(peticion.url) == "https://sigrid.ejemplo.invalid/api/sql/read"
        assert peticion.headers["x-functions-key"] == "clave-de-prueba"
        assert cuerpo["sql"] == contratos.SQL_LINEAS_CONTRATO
        assert cuerpo["database"] == "ruesma-pruebas"
        assert cuerpo["max_rows"] == MAX_FILAS_POR_PETICION
        assert cuerpo["timeout_seconds"] == 30
    assert sorted(json.loads(p.content)["parameters"][0] for p in sigrid.peticiones) == [
        "CTSU24/0228", "CTSU24/0518", "CTSU25/0317",
    ]


def test_f084_r2_la_sql_es_un_select_con_emp_1_y_orden_estable():
    sql = contratos.SQL_LINEAS_CONTRATO
    primera = sql.lstrip().split()[0].upper()

    assert primera == "SELECT"
    assert "con_ctr.cod = ?" in sql and "con_ctr.emp = 1" in sql
    assert sql.rstrip().endswith("ORDER BY ctr.ide, ctrpro.pos, ctrpro.ide")
    for prohibida in ("INSERT", "UPDATE", "DELETE", "MERGE", "EXEC", "DROP"):
        assert prohibida not in sql.upper()


def test_f084_r2_el_timeout_sale_de_sigrid_api_timeout_s(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    sigrid = _Sigrid()

    _lanzar(ground_truth, fixtures, tmp_path / "i.md", sigrid,
            entorno={**_ENTORNO, "SIGRID_API_TIMEOUT_S": "90"})

    assert {json.loads(p.content)["timeout_seconds"] for p in sigrid.peticiones} == {90}


@pytest.mark.parametrize("falta", sorted(_ENTORNO))
def test_f084_r3_sin_variables_de_sigrid_para_sin_pedir_nada(falta, tmp_path, constructor_gt, capsys):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    antes = _sha(ground_truth / _INPUTS)
    sigrid = _Sigrid()

    codigo = _lanzar(ground_truth, fixtures, tmp_path / "i.md", sigrid,
                     entorno={**_ENTORNO, falta: "  "})

    assert codigo == 2
    assert falta in capsys.readouterr().err
    assert sigrid.peticiones == []
    assert _sha(ground_truth / _INPUTS) == antes


def test_f084_r4_un_contrato_truncado_falla_solo_y_el_resto_sigue(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    informe = tmp_path / "informe.md"

    codigo = _lanzar(ground_truth, fixtures, informe, _Sigrid())

    casos = {fila[0] for fila in _filas(ground_truth / _INPUTS, "CONTRATO_LINEAS")}
    assert codigo == 1
    assert "GEN-002" not in casos
    assert {"RES-001", "RES-008", "HOR-001"} <= casos
    texto = informe.read_text(encoding="utf-8")
    assert "CTSU25/0317" in texto and "truncada" in texto


def test_f084_r4_un_error_http_falla_solo_ese_contrato(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    informe = tmp_path / "informe.md"
    sigrid = _Sigrid({**_SIGRID, "CTSU25/0317": "500"})

    assert _lanzar(ground_truth, fixtures, informe, sigrid, "--reintentos", "1") == 1
    assert "HTTP 500" in informe.read_text(encoding="utf-8")


def test_f084_r1_r11_las_lineas_se_escriben_con_linea_sigrid(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)

    _lanzar(ground_truth, fixtures, tmp_path / "i.md", _Sigrid())

    libro = ground_truth / _INPUTS
    assert _encabezados(libro, "CONTRATO_LINEAS")[-1] == "linea_sigrid"
    hor = [fila for fila in _filas(libro, "CONTRATO_LINEAS") if fila[0] == "HOR-001"]
    assert [(f[1], f[4], f[5], f[7]) for f in hor] == [
        ("H25", 72.5, "01.02", 901), ("H25", 80, "01.03", 902),
    ]


def test_f084_r6_las_filas_de_los_casos_con_lineas_quedan_identicas(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    libro = ground_truth / _INPUTS
    antes_contrato = [f[:7] for f in _filas(libro, "CONTRATO_LINEAS") if f[0] == "RES-001"]
    antes_condiciones = [f for f in _filas(libro, "CONDICIONES") if f[0] == "RES-001"]

    _lanzar(ground_truth, fixtures, tmp_path / "i.md", _Sigrid())

    despues = [f for f in _filas(libro, "CONTRATO_LINEAS") if f[0] == "RES-001"]
    assert [f[:7] for f in despues] == antes_contrato
    assert all(f[7] is None for f in despues)
    assert [f for f in _filas(libro, "CONDICIONES") if f[0] == "RES-001"] == antes_condiciones


def test_f084_r9_la_fecha_de_ia1_entra_en_condiciones(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)

    _lanzar(ground_truth, fixtures, tmp_path / "i.md", _Sigrid())

    filas = [f[:3] for f in _filas(ground_truth / _INPUTS, "CONDICIONES") if f[0] == "HOR-001"]
    assert filas == [["HOR-001", "fecha_albaran", "2025-03-04"]]


def test_f084_r7_copia_antes_de_escribir_y_sin_cambios_no_se_guarda(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    libro = ground_truth / _INPUTS
    copias = ground_truth / escritura.NOMBRE_COPIAS

    _lanzar(ground_truth, fixtures, tmp_path / "i.md", _Sigrid())
    assert len(list(copias.glob("INPUTS.xlsx.*.xlsx"))) == 1
    tras_la_primera = _sha(libro)

    _lanzar(ground_truth, fixtures, tmp_path / "i.md", _Sigrid())

    assert _sha(libro) == tras_la_primera
    assert len(list(copias.glob("INPUTS.xlsx.*.xlsx"))) == 1


def test_f084_r8_dry_run_no_toca_el_libro_y_deja_el_informe(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    libro = ground_truth / _INPUTS
    antes = _sha(libro)
    informe = tmp_path / "informe.md"

    _lanzar(ground_truth, fixtures, informe, _Sigrid(), "--dry-run")

    assert _sha(libro) == antes
    assert not (ground_truth / escritura.NOMBRE_COPIAS).exists()
    assert "dry-run" in informe.read_text(encoding="utf-8")


def test_f084_r10_el_informe_solo_lleva_recuentos_casos_y_num_linea(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    informe = tmp_path / "informe.md"

    _lanzar(ground_truth, fixtures, informe, _Sigrid())

    texto = informe.read_text(encoding="utf-8")
    assert "| CTSU24/0518 | 2 | HOR-001 | — |" in texto
    assert "| HOR-001 | 1 de 2 | 2 |" in texto
    for dato in ("TORNILLO", "72.5", "72,5", "CONTENEDOR", "01.02"):
        assert dato not in texto


def test_f084_r1_casos_filtra_lo_que_se_importa(tmp_path, constructor_gt):
    ground_truth, fixtures = _escenario(tmp_path, constructor_gt)
    sigrid = _Sigrid()

    assert _lanzar(ground_truth, fixtures, tmp_path / "i.md", sigrid, "--casos", "HOR-001") == 0
    assert [json.loads(p.content)["parameters"][0] for p in sigrid.peticiones] == ["CTSU24/0518"]


def test_f084_r1_sin_libro_es_un_error_de_uso(tmp_path, constructor_gt, capsys):
    _, fixtures = _escenario(tmp_path, constructor_gt)

    codigo = _lanzar(tmp_path / "no-existe", fixtures, tmp_path / "i.md", _Sigrid())

    assert codigo == 2
    assert "INPUTS.xlsx" in capsys.readouterr().err


# --- T5 · documento y cabecera del contrato (R29–R31, R34) -------------------

import ast
import base64
import os
import subprocess
import sys

from evals.procesos import sv5_documentos

_REPO_SV5 = (
    RAIZ / "services" / "albaran-valoracion-api" / "infrastructure" / "database"
    / "sqlalchemy_valuation_context_repository.py"
)


def _sql_de_sv5_en_el_fuente() -> str:
    """El texto de `_SQL_CONTRATO_HEADER` leído del fuente de sv5, sin importarlo."""
    arbol = ast.parse(_REPO_SV5.read_text(encoding="utf-8"))
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and getattr(nodo.targets[0], "id", "") == "_SQL_CONTRATO_HEADER":
            return nodo.value.args[0].value
    raise AssertionError("sv5 ya no declara _SQL_CONTRATO_HEADER")


_SQL_SV5 = _sql_de_sv5_en_el_fuente()

_FILA = {
    "id": 31,
    "codigo_contrato": "CTSU24/0454",
    "nombre_contrato": "SUMINISTRO FERRETERIA",
    "cif_proveedor": "A00000000",
    "nombre_proveedor": "FERRETERIA DE PRUEBA SA",
    "codigo_obra": "696",
    "nombre_obra": "OBRA DE PRUEBA",
    "pdf_sharepoint_relative_path": "contratos/CTSU24-0454.pdf",
    "pdf_sharepoint_web_url": "https://ejemplo.invalid/x",
    "md_sharepoint_relative_path": "contratos/CTSU24-0454.md",
}


class _Resultado:
    def __init__(self, fila):
        self._fila = fila

    def mappings(self):
        return self

    def first(self):
        return self._fila


class _Sesion:
    """Doble de la sesión de BBDD: una fila por código, y lo que se le pidió."""

    def __init__(self, filas: dict, rota: set | None = None):
        self.filas = filas
        self.rota = rota or set()
        self.consultas: list[tuple[str, dict]] = []

    def execute(self, sql, parametros):
        self.consultas.append((str(sql), parametros))
        if parametros["codigo_contrato"] in self.rota:
            raise RuntimeError("la BBDD se cayó")
        return _Resultado(self.filas.get(parametros["codigo_contrato"]))


class _Descargador:
    """Doble del descargador de sv5: MD y PDF por ruta, o una excepción."""

    def __init__(self, md=None, pdf=None):
        self.md = md or {}
        self.pdf = pdf or {}
        self.pedidos: list[tuple[str, str]] = []

    def download_markdown_by_relative_path(self, *, relative_path):
        self.pedidos.append(("md", relative_path))
        valor = self.md[relative_path]
        if isinstance(valor, Exception):
            raise valor
        return valor

    def download_by_relative_path(self, *, relative_path):
        self.pedidos.append(("pdf", relative_path))
        valor = self.pdf[relative_path]
        if isinstance(valor, Exception):
            raise valor
        return type("Descargado", (), {"filename": "c.pdf", "mime_type": "application/pdf", "data": valor})()


def _documento(fila=_FILA, md=None, pdf=None, max_pdf_mb=40):
    return sv5_documentos.documento_de_contrato(
        "CTSU24/0454", _Sesion({"CTSU24/0454": fila}), _Descargador(md, pdf), _SQL_SV5, max_pdf_mb
    )


def test_f084_r29_la_sql_del_subproceso_es_la_de_sv5():
    """Se importa en un subproceso con sv5 en `sys.path`, como en la corrida."""
    codigo = (
        "import sys; sys.path.insert(0, sys.argv[1]);"
        "from evals.procesos import sv5_documentos as m; sys.stdout.write(m.sql_contrato())"
    )
    proceso = subprocess.run(
        [sys.executable, "-c", codigo, str(RAIZ / "services" / "albaran-valoracion-api")],
        capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ), check=True,
    )

    assert proceso.stdout == _SQL_SV5
    assert "FROM albaran_contratos_merge" in _SQL_SV5 and "LIMIT 1" in _SQL_SV5


def test_f084_r29_lee_la_fila_del_codigo_con_la_sql_que_recibe():
    sesion = _Sesion({"CTSU24/0454": _FILA})

    sv5_documentos.documento_de_contrato(
        "CTSU24/0454", sesion, _Descargador(md={_FILA["md_sharepoint_relative_path"]: "# C"}),
        _SQL_SV5, 40,
    )

    assert sesion.consultas == [(_SQL_SV5, {"codigo_contrato": "CTSU24/0454"})]


def test_f084_r29_con_md_se_prefiere_el_md():
    documento = _documento(md={_FILA["md_sharepoint_relative_path"]: "  # Contrato\n"},
                           pdf={_FILA["pdf_sharepoint_relative_path"]: b"%PDF"})

    assert documento["tipo"] == "md"
    assert base64.b64decode(documento["contenido_b64"]) == b"# Contrato"
    assert documento["cabecera"] == {
        "nombre_contrato": "SUMINISTRO FERRETERIA", "cif_proveedor": "A00000000",
        "nombre_proveedor": "FERRETERIA DE PRUEBA SA", "codigo_obra": "696",
        "nombre_obra": "OBRA DE PRUEBA",
    }


@pytest.mark.parametrize("md", ["   ", RuntimeError("graph caído")])
def test_f084_r29_md_vacio_o_que_falla_cae_al_pdf(md):
    documento = _documento(md={_FILA["md_sharepoint_relative_path"]: md},
                           pdf={_FILA["pdf_sharepoint_relative_path"]: b"%PDF-1.7"})

    assert documento["tipo"] == "pdf"
    assert base64.b64decode(documento["contenido_b64"]) == b"%PDF-1.7"


def test_f084_r29_sin_ruta_de_md_va_al_pdf():
    documento = _documento(fila={**_FILA, "md_sharepoint_relative_path": None},
                           pdf={_FILA["pdf_sharepoint_relative_path"]: b"%PDF"})

    assert documento["tipo"] == "pdf"


def test_f084_r31_contrato_que_no_esta_en_la_tabla():
    documento = _documento(fila=None)

    assert documento["tipo"] == "ninguno"
    assert "no está en albaran_contratos_merge" in documento["motivo"]
    assert documento["contenido_b64"] is None and documento["cabecera"] == {}


def test_f084_r31_contrato_sin_ruta_de_documento():
    documento = _documento(fila={**_FILA, "md_sharepoint_relative_path": None,
                                 "pdf_sharepoint_relative_path": "  "})

    assert documento["tipo"] == "ninguno"
    assert "sin ruta" in documento["motivo"]
    assert documento["cabecera"]["codigo_obra"] == "696"


def test_f084_r31_la_descarga_del_pdf_falla():
    documento = _documento(fila={**_FILA, "md_sharepoint_relative_path": None},
                           pdf={_FILA["pdf_sharepoint_relative_path"]: TimeoutError("lento")})

    assert documento["tipo"] == "ninguno"
    assert "TimeoutError" in documento["motivo"]


def test_f084_r31_un_pdf_que_pasa_de_max_pdf_mb_no_entra():
    grande = b"x" * (1024 * 1024 + 1)
    documento = _documento(fila={**_FILA, "md_sharepoint_relative_path": None},
                           pdf={_FILA["pdf_sharepoint_relative_path"]: grande}, max_pdf_mb=1)

    assert documento["tipo"] == "ninguno"
    assert "MAX_PDF_MB" in documento["motivo"]
    assert sv5_documentos.MAX_PDF_MB == 40


def test_f084_r31_un_contrato_que_revienta_no_para_a_los_demas():
    sesion = _Sesion({"A": {**_FILA, "md_sharepoint_relative_path": None,
                            "pdf_sharepoint_relative_path": None}}, rota={"B"})

    salida = sv5_documentos.ejecutar_trabajo(
        {"contratos": ["B", "A"], "max_pdf_mb": 40}, sesion=sesion, descargador=_Descargador(),
        sql=_SQL_SV5,
    )

    assert [(r["codigo"], r["tipo"]) for r in salida["resultados"]] == [("B", "ninguno"), ("A", "ninguno")]
    assert "RuntimeError" in salida["resultados"][0]["motivo"]
    assert "la BBDD se cayó" not in salida["resultados"][0]["motivo"]


def test_f084_r30_la_entrada_del_indice_no_lleva_el_contenido():
    contenido = b"# Contrato con precios"
    documento = {"tipo": "md", "motivo": "", "cabecera": dict(_documento(
        md={_FILA["md_sharepoint_relative_path"]: "# C"})["cabecera"]),
        "contenido_b64": base64.b64encode(contenido).decode()}

    entrada = contratos.entrada_de_indice("CTSU24/0454", documento, "2026-10-22T10:00:00Z")

    assert entrada == {"CTSU24/0454": {
        "tipo": "md", "sha256": hashlib.sha256(contenido).hexdigest(), "bytes": len(contenido),
        "motivo": "", "nombre_contrato": "SUMINISTRO FERRETERIA", "cif_proveedor": "A00000000",
        "nombre_proveedor": "FERRETERIA DE PRUEBA SA", "codigo_obra": "696",
        "nombre_obra": "OBRA DE PRUEBA", "leido_utc": "2026-10-22T10:00:00Z",
    }}
    assert "precios" not in json.dumps(entrada)


def test_f084_r30_sin_documento_la_entrada_dice_ninguno_y_su_motivo():
    entrada = contratos.entrada_de_indice(
        "X", {"tipo": "ninguno", "motivo": "sin ruta", "cabecera": {}, "contenido_b64": None}, "t"
    )["X"]

    assert entrada["tipo"] == "ninguno" and entrada["sha256"] is None and entrada["bytes"] == 0
    assert entrada["motivo"] == "sin ruta" and entrada["nombre_obra"] is None


_ENTORNO_DOCS = {
    "PG_HOST": "pg.ejemplo.invalid", "PG_DB": "albaranes", "PG_USER": "lector",
    "PG_PASSWORD": "secreto-de-prueba", "GRAPH_KEY": "{}", "SHAREPOINT_MODE": "drive_id",
    "SHAREPOINT_DRIVE_ID": "drive-de-prueba",
}


def _lanzar_documentos(tmp_path, fixtures, lanzar, entorno=None, *extra):
    return contratos.main(
        ["documentos", "--fixtures", str(fixtures), "--informe", str(tmp_path / "informe.md"),
         "--cache", str(tmp_path / "cache"), "--indice", str(tmp_path / "indice" / "_indice.json"),
         *extra],
        entorno=_ENTORNO_DOCS if entorno is None else entorno,
        lanzar=lanzar,
    )


def _resultado(codigo, tipo, contenido: bytes | None, motivo=""):
    return {"codigo": codigo, "tipo": tipo, "motivo": motivo,
            "cabecera": {"nombre_obra": "OBRA"} if contenido else {},
            "contenido_b64": base64.b64encode(contenido).decode() if contenido else None}


def test_f084_r30_documentos_deja_la_cache_y_el_indice(tmp_path, constructor_gt):
    _, fixtures = _escenario(tmp_path, constructor_gt)
    pedidos = []

    def lanzar(trabajo, entorno):
        pedidos.append((trabajo, entorno))
        return {"resultados": [
            _resultado("CTSU24/0228", "md", b"# Contrato 0228"),
            _resultado("CTSU24/0518", "pdf", b"%PDF-1.7 hormigon"),
            _resultado("CTSU25/0317", "ninguno", None, "sin ruta de documento (md ni pdf)"),
        ]}

    assert _lanzar_documentos(tmp_path, fixtures, lanzar) == 0

    (trabajo, entorno), = pedidos
    assert trabajo == {"contratos": ["CTSU24/0228", "CTSU24/0518", "CTSU25/0317"], "max_pdf_mb": 40}
    assert entorno["PG_PASSWORD"] == "secreto-de-prueba"
    assert (tmp_path / "cache" / "CTSU24_0228.md").read_bytes() == b"# Contrato 0228"
    assert (tmp_path / "cache" / "CTSU24_0518.pdf").read_bytes() == b"%PDF-1.7 hormigon"
    texto = (tmp_path / "indice" / "_indice.json").read_text(encoding="utf-8")
    indice = json.loads(texto)
    assert list(indice) == ["CTSU24/0228", "CTSU24/0518", "CTSU25/0317"]
    assert indice["CTSU24/0518"]["sha256"] == hashlib.sha256(b"%PDF-1.7 hormigon").hexdigest()
    assert indice["CTSU25/0317"]["tipo"] == "ninguno"
    assert "Contrato 0228" not in texto and "hormigon" not in texto
    informe = (tmp_path / "informe.md").read_text(encoding="utf-8")
    assert "| CTSU25/0317 | ninguno | 0 | sin ruta de documento (md ni pdf) |" in informe


def test_f084_r30_documentos_conserva_las_demas_entradas_del_indice(tmp_path, constructor_gt):
    _, fixtures = _escenario(tmp_path, constructor_gt)
    indice = tmp_path / "indice" / "_indice.json"
    indice.parent.mkdir()
    indice.write_text(json.dumps({"OTRO/1": {"tipo": "ninguno"}}), encoding="utf-8")

    _lanzar_documentos(tmp_path, fixtures, lambda t, e: {"resultados": [
        _resultado("CTSU24/0518", "md", b"# x")]}, None, "--casos", "HOR-001")

    assert set(json.loads(indice.read_text(encoding="utf-8"))) == {"OTRO/1", "CTSU24/0518"}


def test_f084_r30_si_el_subproceso_muere_no_se_toca_nada(tmp_path, constructor_gt, capsys):
    _, fixtures = _escenario(tmp_path, constructor_gt)

    def lanzar(trabajo, entorno):
        raise RuntimeError("el subproceso de sv5 falló con código 1")

    assert _lanzar_documentos(tmp_path, fixtures, lanzar) == 1
    assert not (tmp_path / "indice" / "_indice.json").exists()
    assert "código 1" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("cambio", "falta"),
    [
        ({"PG_HOST": ""}, "PG_HOST"),
        ({"PG_PASSWORD": " "}, "PG_PASSWORD"),
        ({"PG_USER": ""}, "PG_USER"),
        ({"PG_DB": ""}, "PG_DB"),
        ({"GRAPH_KEY": ""}, "GRAPH_KEY"),
        ({"SHAREPOINT_DRIVE_ID": ""}, "SHAREPOINT_DRIVE_ID"),
        ({"SHAREPOINT_MODE": "folder_url"}, "SHAREPOINT_FOLDER_URL"),
        ({"SHAREPOINT_MODE": "site_path"}, "SHAREPOINT_HOSTNAME"),
        ({"SHAREPOINT_MODE": "otro"}, "SHAREPOINT_MODE"),
    ],
)
def test_f084_r34_sin_variables_para_antes_de_conectar(cambio, falta, tmp_path, constructor_gt, capsys):
    _, fixtures = _escenario(tmp_path, constructor_gt)
    lanzados = []

    codigo = _lanzar_documentos(
        tmp_path, fixtures, lambda t, e: lanzados.append(t), {**_ENTORNO_DOCS, **cambio}
    )

    assert codigo == 2
    assert falta in capsys.readouterr().err
    assert lanzados == []


def test_f084_r34_sin_sharepoint_mode_vale_el_de_sv5_drive_id():
    entorno = {k: v for k, v in _ENTORNO_DOCS.items() if k != "SHAREPOINT_MODE"}

    assert sv5_documentos.faltan_variables(entorno) == []


def test_f084_r34_la_sesion_se_abre_en_solo_lectura():
    url, argumentos = sv5_documentos.conexion_de_solo_lectura(
        {**_ENTORNO_DOCS, "PG_PASSWORD": "p@ss:word", "PG_PORT": "6432"}
    )

    assert argumentos == {"options": "-c default_transaction_read_only=on"}
    assert url == "postgresql+psycopg://lector:p%40ss%3Aword@pg.ejemplo.invalid:6432/albaranes"


def test_f084_r34_el_subproceso_recibe_el_entorno_por_env_y_no_por_stdin(monkeypatch):
    vistos = {}

    def falso_run(argumentos, **opciones):
        vistos.update(opciones)
        salida = "<<<EVALS-JSON-INICIO>>>\n{\"resultados\": []}\n<<<EVALS-JSON-FIN>>>\n"
        return subprocess.CompletedProcess(argumentos, 0, stdout=salida, stderr="")

    monkeypatch.setattr(sv5_documentos.subprocess, "run", falso_run)
    salida = sv5_documentos.ejecutar_en_subproceso({"contratos": ["A"]}, dict(_ENTORNO_DOCS))

    assert salida == {"resultados": []}
    assert vistos["env"]["PG_PASSWORD"] == "secreto-de-prueba"
    assert "secreto" not in vistos["input"]
    assert os.environ.get("PG_PASSWORD") != "secreto-de-prueba"
