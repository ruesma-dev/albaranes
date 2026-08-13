# tests/test_f011_r5_determinismo.py
"""F-011 · R5 — El conversor produce salida determinista.

El mismo Excel tiene que dar byte a byte el mismo JSON: si no, cada corrida
ensucia el diff de git con ruido y nadie vuelve a mirar un cambio de fixtures.
Por eso no hay timestamps: la trazabilidad va por el sha256 del libro origen,
que solo cambia cuando cambia el libro.
"""

import datetime as dt
import json

from evals.conversor import convertir

_FILAS = {
    ("IA1_extraccion.xlsx", "Residuos", 0): [
        [
            "RES-001",
            "RES-001.pdf",
            "GESTIÓN DE RESIDUOS S.A.",
            "A87654321",
            dt.date(2026, 1, 15),
            "R-99",
            "OBR-12",
            "Derribo",
            "contado",
            "",
        ]
    ],
    ("IA1_extraccion.xlsx", "Residuos", 1): [
        ["RES-001", 1, "Contenedor 6 m3", 1, "ud", 120.0, "", 120.0, "", ""],
        ["RES-001", 2, "Canon de vertedero", 3.2, "tn", 12.0, "", 38.4, "", ""],
    ],
}


def test_f011_r5_dos_corridas_producen_los_mismos_bytes(tmp_path, constructor_gt):
    ground_truth = constructor_gt(tmp_path / "gt", filas=_FILAS)

    convertir(ground_truth, tmp_path / "a")
    convertir(ground_truth, tmp_path / "b")

    primera = (tmp_path / "a" / "IA1" / "RES-001.json").read_bytes()
    segunda = (tmp_path / "b" / "IA1" / "RES-001.json").read_bytes()
    assert primera == segunda
    indice_a = (tmp_path / "a" / "IA1" / "_indice.json").read_bytes()
    indice_b = (tmp_path / "b" / "IA1" / "_indice.json").read_bytes()
    assert indice_a == indice_b


def test_f011_r5_reconvertir_sobre_el_mismo_destino_no_cambia_nada(
    tmp_path, constructor_gt
):
    ground_truth = constructor_gt(tmp_path / "gt", filas=_FILAS)
    destino = tmp_path / "fixtures"

    convertir(ground_truth, destino)
    antes = (destino / "IA1" / "RES-001.json").read_bytes()
    convertir(ground_truth, destino)

    assert (destino / "IA1" / "RES-001.json").read_bytes() == antes


def test_f011_r5_las_claves_van_ordenadas_y_el_texto_sin_escapar(
    tmp_path, constructor_gt
):
    ground_truth = constructor_gt(tmp_path / "gt", filas=_FILAS)

    convertir(ground_truth, tmp_path / "fixtures")

    texto = (tmp_path / "fixtures" / "IA1" / "RES-001.json").read_text(
        encoding="utf-8"
    )
    fixture = json.loads(texto)
    assert list(fixture) == sorted(fixture)
    assert "GESTIÓN DE RESIDUOS S.A." in texto, "UTF-8 sin escapes \\uXXXX"
    assert texto.endswith("\n")


def test_f011_r5_el_sha256_del_libro_es_la_trazabilidad(tmp_path, constructor_gt):
    """El fixture apunta a QUÉ libro salió, no a cuándo se convirtió."""
    ground_truth = constructor_gt(tmp_path / "gt", filas=_FILAS)

    convertir(ground_truth, tmp_path / "fixtures")

    fixture = json.loads(
        (tmp_path / "fixtures" / "IA1" / "RES-001.json").read_text(encoding="utf-8")
    )
    indice = json.loads(
        (tmp_path / "fixtures" / "IA1" / "_indice.json").read_text(encoding="utf-8")
    )
    assert fixture["sha256_libro"] == indice["sha256_libro"]
    assert indice["casos"] == ["RES-001"]


def test_f011_r5_un_caso_borrado_del_excel_desaparece_de_los_fixtures(
    tmp_path, constructor_gt
):
    """Si no, quedarían fixtures huérfanos que el runner seguiría evaluando."""
    destino = tmp_path / "fixtures"
    convertir(constructor_gt(tmp_path / "gt1", filas=_FILAS), destino)
    assert (destino / "IA1" / "RES-001.json").is_file()

    convertir(constructor_gt(tmp_path / "gt2"), destino)

    assert not (destino / "IA1" / "RES-001.json").exists()
