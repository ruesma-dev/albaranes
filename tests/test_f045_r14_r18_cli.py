# tests/test_f045_r14_r18_cli.py
"""F-045 · R14 y R18: la corrida completa y su informe.

R18 es la que sostiene todo lo demás: el Excel del humano cambia cada semana,
así que importar tiene que poder repetirse. Dos pasadas seguidas sobre el
mismo origen dejan los mismos libros y el mismo mapa —salvo la copia de
seguridad, que lleva la hora en el nombre—.

Y R14 es lo que evita el falso verde: el informe dice cuántas celdas llevan
valor, cuántas `?` y cuántas vacías, cómo se reparten los casos entre no
regresión y defecto conocido, y qué se quedó fuera **con nombre y apellidos**.
"""

from __future__ import annotations

import json

import openpyxl
import pytest

from evals import conversor
from evals.revision import __main__ as cli

# Encabezados de cada tabla, en el orden en que los escribe el importador. Las
# claves snake_case son lo que `conversor.clave_de_encabezado` produce a partir
# de los encabezados escritos para personas de los libros de verdad.
CABECERAS: dict[str, list[str]] = {
    "cabeceras": ["caso_id", "fichero_albaran", "proveedor_nombre", "proveedor_cif",
                  "fecha", "numero_albaran", "obra_codigo", "obra_nombre",
                  "forma_pago", "comentario"],
    "lineas": ["caso_id", "num_linea", "descripcion_esperada", "cantidad", "unidad",
               "precio_unitario", "descuentos", "importe", "codigo_imputacion",
               "comentario"],
    "contexto": ["caso_id", "num_linea", "campo_contexto", "valor_esperado", "comentario"],
    "lineas_valoradas": ["caso_id", "num_linea", "match_method",
                         "codigo_producto_contrato", "codigo_partida_final",
                         "precio_unitario_final", "precio_source", "importe_calculado",
                         "review_required", "comentario"],
    "sinteticas_esperadas": ["caso_id", "num_linea_base", "modifier_source", "rol_linea",
                             "descripcion_esperada", "cantidad", "precio_unitario",
                             "codigo_partida", "comentario"],
    "sinteticas_prohibidas": ["caso_id", "concepto_vetado", "motivo_veto", "comentario"],
    "conciliacion": ["caso_id", "num_linea", "concilia", "linea_contrato_esperada",
                     "precio_unitario_esperado", "motivo", "comentario"],
    "caso": ["caso_id", "tipologia", "ia_destino", "origen", "contrato_codigo",
             "descripcion_caso"],
    "lineas_albaran": ["caso_id", "num_linea", "descripcion", "cantidad", "unidad",
                       "precio_unitario", "descuentos", "importe", "codigo_imputacion",
                       "observaciones_albaran"],
    "contrato_lineas": ["caso_id", "codigo_producto", "descripcion_recurso", "unidad",
                        "precio_unitario", "codigo_partida", "comentario"],
    "condiciones": ["caso_id", "campo", "valor", "comentario"],
    "datos_generales": ["caso_id", "fichero", "obra", "proveedor", "cif", "fecha",
                        "numero_albaran", "contrato_elegido", "total_valorado_esperado",
                        "requiere_revision", "motivo_revision", "comentario"],
    "lineas_anadidas": ["caso_id", "num_linea_base", "concepto", "cantidad",
                        "precio_unitario", "partida", "importe", "comentario"],
}

ENCABEZADOS_PLANOS = [
    "codigo alabran", "Tipo de albaran", "cif", "nombre empresa", "codigo obra",
    "fecha", "codigo contrato", "partida", "linea esta en albaran o deducida",
    "linea  en contrato de sigrid o nueva", "concepto", "cantidad", "unidad",
    "precio unitario", "unitario viene en albaran o valorado en contrato?",
    "importe", "importe viene en albaran o valorado en contrato?", "descuento",
    "LER o codigo linea o producto", "Comentarios",
]

FILAS = [
    ["H132525", "HORMIGON", "B04685541", "HORPRESOL, S.L.", "693", "2026-03-11",
     "CTSU23/0386", "P5.14.01", "EN ALBARAN", "EN CONTRATO", "HA-25/B/20/IIa", 8,
     "M3", 72.5, "DE CONTRATO", 580, "DE CONTRATO", None, None, None],
    ["H132525", "HORMIGON", "B04685541", "HORPRESOL, S.L.", "693", "2026-03-11",
     "CTSU23/0386", "P5.14.01", "DEDUCIDA INCREMENTO POR ANIO", "NUEVA",
     "INCREM. PRECIO 2026", 8, "M3", 3, "EN OFERTA", 24, "EN OFERTA", None, None,
     "No ha cogido la linea."],
    ["0000168", "RESIDUOS", "B82899550", "SALMEDINA, S.L.", "687", "2024-07-03",
     "CTSU24/0228", "CI.03A.7", "EN ALBARAN", "CONTRATO", "CAMBIO CONTENEDOR 6M3",
     1, "UD", 120, "CONTRATO", 120, "CONTRATO", None, "17 02 01", None],
    # Lo que se PESA: aquí muerde el mínimo facturable de 1 (design §5 ter).
    ["0000168", "RESIDUOS", "B82899550", "SALMEDINA, S.L.", "687", "2024-07-03",
     "CTSU24/0228", "CI.03A.7", "EN ALBARAN", "CONTRATO", "RCDS. SUCIOS",
     0.42, "M3", 26, "CONTRATO", 10.92, "CONTRATO", None, "17 02 01", None],
]


@pytest.fixture
def entorno(tmp_path):
    """Un Excel de revisión, seis libros vacíos y una carpeta de entrada."""
    origen = tmp_path / "evals_summary.xlsx"
    libro = openpyxl.Workbook()
    hoja = libro.active
    hoja.append(ENCABEZADOS_PLANOS)
    for fila in FILAS:
        hoja.append(fila)
    libro.save(origen)
    libro.close()

    ground_truth = tmp_path / "ground_truth"
    ground_truth.mkdir()
    for definicion in conversor.LIBROS:
        libro = openpyxl.Workbook()
        libro.remove(libro.active)
        for pestana, tablas in definicion.tablas_por_pestana.items():
            hoja = libro.create_sheet(pestana)
            for tabla in tablas:
                hoja.append([f"{tabla.titulo} - lo que sea"])
                hoja.append(CABECERAS[tabla.clave])
                hoja.append([])
                hoja.append([])
        libro.save(ground_truth / definicion.fichero)
        libro.close()

    entrada = tmp_path / "albaranes"
    entrada.mkdir()
    return {
        "origen": origen,
        "ground_truth": ground_truth,
        "originales": entrada,
        "mapa": tmp_path / "mapa_casos.json",
        "informe": tmp_path / "import.md",
    }


def correr(entorno, *extra):
    return cli.main(
        [
            "--origen", str(entorno["origen"]),
            "--ground-truth", str(entorno["ground_truth"]),
            "--originales", str(entorno["originales"]),
            "--mapa", str(entorno["mapa"]),
            "--informe", str(entorno["informe"]),
            *extra,
        ]
    )


def contenido(directorio):
    volcado = {}
    for ruta in sorted(directorio.glob("*.xlsx")):
        libro = openpyxl.load_workbook(ruta)
        volcado[ruta.name] = {
            hoja: [[c.value for c in fila] for fila in libro[hoja].iter_rows()]
            for hoja in libro.sheetnames
        }
        libro.close()
    return volcado


# --- La corrida completa ----------------------------------------------------


def test_f045_r14_la_corrida_escribe_los_libros_y_termina_en_cero(entorno):
    assert correr(entorno) == 0
    libro = openpyxl.load_workbook(entorno["ground_truth"] / "IA1_extraccion.xlsx")
    hoja = libro["Hormigon"]
    filas = [[c.value for c in f] for f in hoja.iter_rows() if f[0].value == "HOR-001"]
    assert len(filas) == 2  # la cabecera y la única línea impresa
    libro.close()


def test_f045_r14_el_informe_trae_el_recuento_y_el_reparto(entorno):
    correr(entorno)
    texto = entorno["informe"].read_text(encoding="utf-8")
    assert "no regresión" in texto and "defecto conocido" in texto
    assert "HOR-001" in texto
    assert "`?`" in texto


def test_f045_r14_el_informe_lista_uno_a_uno_lo_que_se_quedo_fuera(entorno):
    """Sin ni un documento en la carpeta, los dos casos salen con su nombre."""
    correr(entorno)
    texto = entorno["informe"].read_text(encoding="utf-8")
    assert "fila_sin_fichero" in texto
    assert "HOR-001" in texto and "RES-001" in texto


def test_f045_r14_el_informe_declara_los_criterios_de_residuos_pendientes(entorno):
    correr(entorno)
    assert "minimo_1_tn" in entorno["informe"].read_text(encoding="utf-8")


def test_f045_r14_se_copia_cada_libro_antes_de_escribirlo(entorno):
    correr(entorno)
    copias = {ruta.name.split(".xlsx")[0] for ruta in
              (entorno["ground_truth"] / "copias").glob("*.xlsx")}
    # Los cinco que el importador toca. IA4 no: no hay ninguna línea NUEVA en
    # este Excel de prueba, así que no hay nada que conciliar.
    assert copias == {
        "IA1_extraccion", "IA2_contexto", "IA3_valoracion", "INPUTS",
        "RESULTADO_FINAL",
    }


def test_f045_r18_la_segunda_pasada_no_deja_ni_una_copia_mas(entorno):
    """Si el libro no cambia no se guarda: guardarlo le movería el sha256 y

    dejaría todos sus fixtures «modificados» sin que hubiera cambiado un dato.
    """
    correr(entorno)
    antes = sorted(p.name for p in (entorno["ground_truth"] / "copias").glob("*.xlsx"))
    correr(entorno)
    despues = sorted(p.name for p in (entorno["ground_truth"] / "copias").glob("*.xlsx"))
    assert despues == antes


def test_f045_r14_el_mapa_queda_escrito_con_los_casos_nuevos(entorno):
    correr(entorno)
    mapa = json.loads(entorno["mapa"].read_text(encoding="utf-8"))["casos"]
    assert set(mapa) == {"HOR-001", "RES-001"}
    assert mapa["HOR-001"]["codigo"] == "H132525"


# --- R18: dos pasadas dejan lo mismo ---------------------------------------


def test_f045_r18_dos_pasadas_dejan_los_mismos_libros_y_el_mismo_mapa(entorno):
    correr(entorno)
    antes = contenido(entorno["ground_truth"])
    mapa_antes = entorno["mapa"].read_text(encoding="utf-8")

    correr(entorno)
    assert contenido(entorno["ground_truth"]) == antes
    assert entorno["mapa"].read_text(encoding="utf-8") == mapa_antes


def test_f045_r18_en_seco_no_se_toca_ni_un_libro_ni_el_mapa(entorno):
    antes = (entorno["ground_truth"] / "IA1_extraccion.xlsx").read_bytes()
    assert correr(entorno, "--dry-run") == 0
    assert (entorno["ground_truth"] / "IA1_extraccion.xlsx").read_bytes() == antes
    assert not entorno["mapa"].exists()
    assert entorno["informe"].exists()


# --- R5: lo desconocido aborta sin escribir nada ---------------------------


def test_f045_r5_una_etiqueta_desconocida_aborta_la_corrida(entorno):
    libro = openpyxl.load_workbook(entorno["origen"])
    libro.active["B2"] = "PINTURA"
    libro.save(entorno["origen"])
    libro.close()
    antes = (entorno["ground_truth"] / "IA1_extraccion.xlsx").read_bytes()
    assert correr(entorno) == 1
    assert (entorno["ground_truth"] / "IA1_extraccion.xlsx").read_bytes() == antes


def test_f045_r14_un_origen_que_no_existe_no_revienta(entorno, tmp_path):
    entorno["origen"] = tmp_path / "no-esta.xlsx"
    assert correr(entorno) == 1
