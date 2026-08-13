# tests/test_f011_r6_ausencias.py
"""F-011 · R6 — Falta un libro o una pestaña: se falla, no se convierte a medias.

Unos fixtures parciales son peores que ninguno: el runner los daría por buenos
y el informe saldría VERDE evaluando la mitad del banco de casos.
"""

import pytest

from evals.conversor import ErrorConversion, convertir


def test_f011_r6_libro_ausente_falla_nombrandolo(tmp_path, constructor_gt):
    ground_truth = constructor_gt(
        tmp_path / "gt", omitir_libros=("RESULTADO_FINAL.xlsx",)
    )

    with pytest.raises(ErrorConversion) as error:
        convertir(ground_truth, tmp_path / "fixtures")

    assert "RESULTADO_FINAL.xlsx" in str(error.value)


def test_f011_r6_pestana_ausente_falla_nombrandola(tmp_path, constructor_gt):
    ground_truth = constructor_gt(
        tmp_path / "gt", omitir_pestanas=(("INPUTS.xlsx", "CONTRATO_LINEAS"),)
    )

    with pytest.raises(ErrorConversion) as error:
        convertir(ground_truth, tmp_path / "fixtures")

    mensaje = str(error.value)
    assert "INPUTS.xlsx" in mensaje
    assert "CONTRATO_LINEAS" in mensaje


def test_f011_r6_no_se_escriben_fixtures_parciales(tmp_path, constructor_gt):
    ground_truth = constructor_gt(
        tmp_path / "gt", omitir_libros=("IA4_conciliacion.xlsx",)
    )
    destino = tmp_path / "fixtures"

    with pytest.raises(ErrorConversion):
        convertir(ground_truth, destino)

    assert not destino.exists()


def test_f011_r6_directorio_de_ground_truth_inexistente_falla(tmp_path):
    with pytest.raises(ErrorConversion) as error:
        convertir(tmp_path / "no-existe", tmp_path / "fixtures")

    assert "no-existe" in str(error.value)


def test_f011_r6_tabla_ausente_en_una_pestana_falla(tmp_path, constructor_gt):
    """Una pestaña sin su TABLA 3 no es «cero casos»: es el contrato roto."""
    ground_truth = constructor_gt(tmp_path / "gt")
    import openpyxl

    ruta = ground_truth / "IA3_valoracion.xlsx"
    libro = openpyxl.load_workbook(ruta)
    hoja = libro["Mortero"]
    for fila in hoja.iter_rows():
        for celda in fila:
            if isinstance(celda.value, str) and celda.value.startswith("TABLA 3"):
                celda.value = "OTRA COSA"
    libro.save(ruta)

    with pytest.raises(ErrorConversion) as error:
        convertir(ground_truth, tmp_path / "fixtures")

    mensaje = str(error.value)
    assert "Mortero" in mensaje
    assert "TABLA 3" in mensaje


def test_f011_r6_fila_con_datos_y_sin_caso_id_falla(tmp_path, constructor_gt):
    ground_truth = constructor_gt(
        tmp_path / "gt",
        filas={
            ("IA1_extraccion.xlsx", "Bombeo", 1): [
                ["", 1, "Bombeo de hormigón", 20, "m3", 5.0, "", 100.0, "", ""]
            ]
        },
    )

    with pytest.raises(ErrorConversion) as error:
        convertir(ground_truth, tmp_path / "fixtures")

    assert "caso_id" in str(error.value)
    assert "Bombeo" in str(error.value)
