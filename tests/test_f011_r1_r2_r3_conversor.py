# tests/test_f011_r1_r2_r3_conversor.py
"""F-011 · R1, R2, R3 y R4 — Conversor xlsx → fixtures JSON.

R1: un fichero JSON por caso y por libro, versionable.
R2: convenios de celda (vacío, `?`, `REVISIÓN`, fechas, descuentos, decimales).
R3: tablas localizadas por su fila de título, tolerando blancos y pestañas sin
casos.
R4: el barrido de datos sensibles aborta la conversión SIN escribir nada.
"""

import datetime as dt
import json

import pytest

from evals.conversor import ErrorDatosSensibles, convertir
from evals.modelos import ESPERA_REVISION, NO_COMPARAR


def _leer(directorio, destino, caso_id):
    ruta = directorio / destino / f"{caso_id}.json"
    return json.loads(ruta.read_text(encoding="utf-8"))


@pytest.fixture
def ground_truth_con_casos(tmp_path, constructor_gt):
    return constructor_gt(
        tmp_path / "ground_truth",
        filas={
            ("IA1_extraccion.xlsx", "Hormigon", 0): [
                [
                    "HOR-001",
                    "HOR-001.pdf",
                    "HORMIGONES DEL NORTE S.L.",
                    "B12345678",
                    dt.date(2026, 3, 4),
                    "A-2201",
                    "OBR-77",
                    "Nave 3",
                    "",  # forma_pago no aparece en el albarán → null
                    "caso base",
                ]
            ],
            ("IA1_extraccion.xlsx", "Hormigon", 1): [
                [
                    "HOR-001",
                    1,
                    "HA-25/B/20/IIa",
                    8,
                    "m3",
                    "72,50",
                    "10%;5%",
                    580,
                    "?",  # no lo sé → no se compara
                    "",
                ]
            ],
            ("IA2_contexto.xlsx", "Hormigon", 0): [
                ["HOR-001", 1, "resistencia", "25", ""]
            ],
            ("IA3_valoracion.xlsx", "Hormigon", 0): [
                [
                    "HOR-001",
                    1,
                    "exact_concept",
                    "P-100",
                    "01.02.03",
                    72.5,
                    "contrato_db",
                    580.0,
                    "NO",
                    "",
                ]
            ],
            ("IA3_valoracion.xlsx", "Hormigon", 2): [
                ["HOR-001", "aditivo", "el mortero no lleva aditivo", ""]
            ],
            ("IA4_conciliacion.xlsx", "Hormigon", 0): [
                ["HOR-001", 2, "NO", "", "", "el año no casa", ""]
            ],
            ("INPUTS.xlsx", "CASOS", 0): [
                ["HOR-001", "Hormigon", "ambas", "manual", "CT-24/1", "caso base"]
            ],
            ("INPUTS.xlsx", "CONTRATO_LINEAS", 0): [
                ["HOR-001", "P-100", "HA-25", "m3", 72.5, "01.02.03", ""]
            ],
            ("INPUTS.xlsx", "CONDICIONES", 0): [
                ["HOR-001", "anio_contrato", "2025", ""]
            ],
            ("RESULTADO_FINAL.xlsx", "Hormigon", 0): [
                [
                    "HOR-001",
                    "HOR-001.pdf",
                    "OBR-77",
                    "HORMIGONES DEL NORTE S.L.",
                    "B12345678",
                    dt.date(2026, 3, 4),
                    "A-2201",
                    "CT-24/1",
                    580.0,
                    "NO",
                    "",
                    "",
                ]
            ],
            ("RESULTADO_FINAL.xlsx", "Hormigon", 1): [
                [
                    "HOR-001",
                    1,
                    "HA-25/B/20/IIa",
                    8,
                    "m3",
                    "SI",
                    "P-100",
                    "REVISIÓN",  # lo correcto es que el sistema no invente
                    72.5,
                    "contrato",
                    580.0,
                    "NO",
                    "",
                ]
            ],
            ("RESULTADO_FINAL.xlsx", "Hormigon", 2): [
                ["HOR-001", 1, "INCREMENTO AÑO 2025", 8, 2.5, "01.02.03", 20.0, ""]
            ],
        },
    )


def test_f011_r1_genera_un_fixture_por_caso_y_libro(ground_truth_con_casos, tmp_path):
    destino = tmp_path / "fixtures"

    informe = convertir(ground_truth_con_casos, destino)

    for subdirectorio in ("IA1", "IA2", "IA3", "IA4", "inputs", "final"):
        assert (destino / subdirectorio / "HOR-001.json").is_file(), subdirectorio
    assert informe.casos_por_fase["IA1"] == 1
    assert informe.casos_por_fase["FINAL"] == 1


def test_f011_r1_el_fixture_lleva_su_trazabilidad(ground_truth_con_casos, tmp_path):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    fixture = _leer(destino, "IA1", "HOR-001")

    assert fixture["caso_id"] == "HOR-001"
    assert fixture["fase"] == "IA1"
    assert fixture["tipologia"] == "Hormigon"
    assert fixture["libro"] == "IA1_extraccion.xlsx"
    assert len(fixture["sha256_libro"]) == 64


def test_f011_r3_las_tablas_se_localizan_por_su_titulo(
    ground_truth_con_casos, tmp_path
):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    ia1 = _leer(destino, "IA1", "HOR-001")
    ia3 = _leer(destino, "IA3", "HOR-001")
    final = _leer(destino, "final", "HOR-001")

    assert set(ia1["tablas"]) == {"cabeceras", "lineas"}
    assert set(ia3["tablas"]) == {
        "lineas_valoradas",
        "sinteticas_esperadas",
        "sinteticas_prohibidas",
    }
    assert set(final["tablas"]) == {
        "datos_generales",
        "lineas",
        "lineas_anadidas",
    }
    assert ia3["tablas"]["sinteticas_esperadas"] == []
    assert ia3["tablas"]["sinteticas_prohibidas"][0]["concepto_vetado"] == "aditivo"


def test_f011_r3_pestana_de_tipologia_sin_casos_no_es_un_error(
    ground_truth_vacio, tmp_path
):
    destino = tmp_path / "fixtures"

    informe = convertir(ground_truth_vacio, destino)

    assert sum(informe.casos_por_fase.values()) == 0
    assert informe.hallazgos == []
    assert (destino / "IA1" / "_indice.json").is_file()


def test_f011_r2_celda_vacia_espera_null(ground_truth_con_casos, tmp_path):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    cabecera = _leer(destino, "IA1", "HOR-001")["tablas"]["cabeceras"][0]

    assert cabecera["forma_pago"] is None


def test_f011_r2_interrogacion_no_se_compara(ground_truth_con_casos, tmp_path):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    linea = _leer(destino, "IA1", "HOR-001")["tablas"]["lineas"][0]

    assert linea["codigo_imputacion"] == NO_COMPARAR


def test_f011_r2_revision_es_un_resultado_esperado(ground_truth_con_casos, tmp_path):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    linea = _leer(destino, "final", "HOR-001")["tablas"]["lineas"][0]

    assert linea["partida_final"] == ESPERA_REVISION


def test_f011_r2_fechas_en_iso(ground_truth_con_casos, tmp_path):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    cabecera = _leer(destino, "IA1", "HOR-001")["tablas"]["cabeceras"][0]

    assert cabecera["fecha"] == "2026-03-04"


def test_f011_r2_descuentos_es_una_lista(ground_truth_con_casos, tmp_path):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    linea = _leer(destino, "IA1", "HOR-001")["tablas"]["lineas"][0]

    assert linea["descuentos"] == ["10%", "5%"]


def test_f011_r2_decimal_con_coma_se_normaliza(ground_truth_con_casos, tmp_path):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    linea = _leer(destino, "IA1", "HOR-001")["tablas"]["lineas"][0]

    assert linea["precio_unitario"] == pytest.approx(72.5)


def test_f011_r2_los_encabezados_humanos_se_traducen_a_claves_estables(
    ground_truth_con_casos, tmp_path
):
    destino = tmp_path / "fixtures"
    convertir(ground_truth_con_casos, destino)

    generales = _leer(destino, "final", "HOR-001")["tablas"]["datos_generales"][0]
    linea = _leer(destino, "final", "HOR-001")["tablas"]["lineas"][0]
    anadida = _leer(destino, "final", "HOR-001")["tablas"]["lineas_anadidas"][0]

    assert generales["numero_albaran"] == "A-2201"
    assert generales["requiere_revision"] == "NO"
    assert linea["num_linea"] == 1
    assert linea["linea_contrato"] == "P-100"
    assert linea["precio_source"] == "contrato"
    assert linea["linea_a_revision"] == "NO"
    assert anadida["num_linea_base"] == 1


def test_f011_r4_un_dato_sensible_aborta_la_conversion_sin_escribir_nada(
    tmp_path, constructor_gt
):
    ground_truth = constructor_gt(
        tmp_path / "ground_truth",
        filas={
            ("IA1_extraccion.xlsx", "Hormigon", 0): [
                [
                    "HOR-002",
                    "HOR-002.pdf",
                    "HORMIGONES DEL NORTE S.L.",
                    "B12345678",
                    dt.date(2026, 3, 4),
                    "A-2202",
                    "OBR-77",
                    "Nave 3",
                    "",
                    "pedidos@proveedor.es lo confirmó",
                ]
            ]
        },
    )
    destino = tmp_path / "fixtures"

    with pytest.raises(ErrorDatosSensibles) as error:
        convertir(ground_truth, destino)

    mensaje = str(error.value)
    assert "IA1_extraccion.xlsx" in mensaje
    assert "Hormigon" in mensaje
    assert "correo" in mensaje
    assert not destino.exists(), "no se escribe ningún fixture si el barrido salta"
