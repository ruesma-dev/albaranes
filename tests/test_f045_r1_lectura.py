# tests/test_f045_r1_lectura.py
"""F-045 · R1: de la tabla plana a `FilaPlana`, localizando por NOMBRE.

El Excel es del humano: añade columnas, las mueve y arrastra una errata en el
encabezado («codigo alabran»). Leer por posición convertiría cualquiera de las
tres cosas en un reparto silenciosamente equivocado.

El `.xlsx` se fabrica en el propio test: ni red, ni BBDD, ni el fichero real
—que lleva precios de proveedor y no se versiona—.
"""

from __future__ import annotations

import openpyxl
import pytest

from evals.revision import lectura

ENCABEZADOS = [
    "codigo alabran",
    "Tipo de albaran (hormigon, residuos, etc..)",
    "cif",
    "nombre empresa (el bueno, con el que se guarda en sigrid)",
    "codigo obra",
    "fecha",
    "codigo contrato",
    "partida",
    "linea esta en albaran o deducida (por ejemplo incremento por año)",
    "linea  en contrato de sigrid o nueva",
    "concepto",
    "cantidad",
    "unidad",
    "precio unitario",
    "unitario viene en albaran o valorado en contrato?",
    "importe",
    "importe viene en albaran o valorado en contrato?",
    "descuento",
    "LER o codigo linea o producto",
    "Comentarios",
]

FILA = [
    "0000168", "RESIDUOS", "B82899550", "SALMEDINA, S.L.", "687",
    "2024-07-03", "CTSU24/0228", "CI.03A.7", "EN ALBARAN", "CONTRATO",
    "CAMBIO CONTENEDOR 6M3", 1, "UD", 120, "CONTRATO", 120, "CONTRATO",
    None, "17 02 01", None,
]


def fabricar(tmp_path, encabezados=None, filas=None, nombre="fuente.xlsx"):
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(list(encabezados if encabezados is not None else ENCABEZADOS))
    for fila in filas if filas is not None else [FILA]:
        hoja.append(list(fila))
    ruta = tmp_path / nombre
    libro.save(ruta)
    libro.close()
    return ruta


def test_f045_r1_lee_una_fila_con_sus_veinte_columnas(tmp_path):
    filas = lectura.leer(fabricar(tmp_path))
    assert len(filas) == 1
    fila = filas[0]
    assert fila.numero_fila == 2
    assert fila.texto("codigo_albaran") == "0000168"
    assert fila.texto("tipo_albaran") == "RESIDUOS"
    assert fila.texto("origen_contrato") == "CONTRATO"
    assert fila.texto("ler") == "17 02 01"
    assert fila.vacia("comentarios")


def test_f045_r1_las_columnas_se_localizan_por_nombre_no_por_posicion(tmp_path):
    """Columna nueva intercalada: el reparto no se mueve ni un milímetro."""
    encabezados = ["revisado por"] + ENCABEZADOS[:3] + ["nota interna"] + ENCABEZADOS[3:]
    valores = ["pablo"] + FILA[:3] + ["lo que sea"] + FILA[3:]
    fila = lectura.leer(fabricar(tmp_path, encabezados, [valores]))[0]
    assert fila.texto("cif") == "B82899550"
    assert fila.texto("nombre_empresa") == "SALMEDINA, S.L."
    assert fila.texto("concepto") == "CAMBIO CONTENEDOR 6M3"


def test_f045_r1_la_fecha_llega_como_AAAA_MM_DD(tmp_path):
    import datetime as dt

    valores = list(FILA)
    valores[5] = dt.datetime(2024, 7, 3)
    fila = lectura.leer(fabricar(tmp_path, filas=[valores]))[0]
    assert fila.texto("fecha") == "2024-07-03"


def test_f045_r1_las_filas_en_blanco_no_son_filas(tmp_path):
    filas = lectura.leer(fabricar(tmp_path, filas=[FILA, [None] * 20, FILA]))
    assert [f.numero_fila for f in filas] == [2, 4]


def test_f045_r1_falta_una_columna_obligatoria_y_lo_dice(tmp_path):
    encabezados = [e for e in ENCABEZADOS if e != "cif"]
    valores = [v for i, v in enumerate(FILA) if i != 2]
    with pytest.raises(lectura.ErrorLectura) as fallo:
        lectura.leer(fabricar(tmp_path, encabezados, [valores]))
    assert "cif" in str(fallo.value)


def test_f045_r1_el_origen_no_existe_y_lo_dice_sin_reventar(tmp_path):
    with pytest.raises(lectura.ErrorLectura) as fallo:
        lectura.leer(tmp_path / "no-esta.xlsx")
    assert "no-esta.xlsx" in str(fallo.value)
