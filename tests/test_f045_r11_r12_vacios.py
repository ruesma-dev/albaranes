# tests/test_f045_r11_r12_vacios.py
"""F-045 · R11 y R12: qué significa una celda vacía en CADA columna.

El banco es poco laxo a propósito. La ceguera real son unas pocas celdas `?`,
no las filas sin comentario (ese es el otro eje, ver R9). Y hay dos columnas
cuyo vacío el humano SÍ afirma: `descuento` (no hay descuento) y el LER (no
aplica a esa familia). Confundirlas con un `?` dejaría sin vigilar justo lo
que sí sabemos.
"""

from __future__ import annotations

from evals.revision import reparto, vocabulario
from evals.revision.modelos import COLUMNAS, FilaPlana

VOCAB = vocabulario.cargar()

BASE = {
    "codigo_albaran": "2137569",
    "tipo_albaran": "FERRETERIA",
    "cif": "A28733558",
    "nombre_empresa": "FEYMACO",
    "codigo_obra": "696",
    "fecha": "2026-06-01",
    "codigo_contrato": "CTSU24/0454",
    "partida": "P4.36.01",
    "origen_linea": "EN ALBARAN",
    "origen_contrato": "NUEVA",
    "concepto": "papel higienico",
    "cantidad": 54,
    "unidad": "UD",
    "precio_unitario": 0.543,
    "origen_precio": "ALBARAN",
    "importe": 17.59,
    "origen_importe": "ALBARAN VALORADO",
    "descuento": 0.4,
    "ler": None,
    "comentarios": None,
}


def fila(numero=2, **cambios):
    valores = dict(BASE)
    valores.update(cambios)
    return FilaPlana(numero_fila=numero, valores=valores)


def linea_de(**cambios):
    casos = reparto.agrupar_por_albaran([fila(**cambios)], VOCAB)
    reparto.asignar_casos_id(casos, {})
    return casos[0].lineas[0]


# --- R12: la política vive en el fichero de datos, no en el código ---------


def test_f045_r12_todas_las_columnas_declaran_su_politica():
    for columna in COLUMNAS:
        assert VOCAB.politica_vacio(columna) in ("nulo", "sin_fila", "interrogante")


def test_f045_r12_descuento_vacio_es_sin_descuento_y_no_interrogante():
    assert reparto.celda(linea_de(descuento=None), "descuento", VOCAB) is None


def test_f045_r12_el_descuento_se_escribe_en_porcentaje_no_en_fraccion():
    """La fórmula canónica (ARCHITECTURE §13) usa `1 - descuento/100`."""
    tablas = _tablas(descuento=0.4)
    assert tablas["IA1"]["lineas"][0]["descuentos"] == 40
    assert _tablas(descuento=0.08)["IA1"]["lineas"][0]["descuentos"] == 8


def test_f045_r12_un_descuento_de_cero_se_escribe_vacio():
    assert _tablas(descuento=0)["IA1"]["lineas"][0]["descuentos"] is None


# --- R11: sin valor afirmado, `?`; nunca un valor supuesto -----------------


def test_f045_r11_partida_vacia_es_interrogante():
    assert reparto.celda(linea_de(partida=None), "partida", VOCAB) == "?"


def test_f045_r11_precio_e_importe_vacios_son_interrogante():
    linea = linea_de(precio_unitario=None, importe=None)
    assert reparto.celda(linea, "precio_unitario", VOCAB) == "?"
    assert reparto.celda(linea, "importe", VOCAB) == "?"


def test_f045_r11_un_valor_presente_nunca_se_convierte_en_interrogante():
    assert reparto.celda(linea_de(), "cantidad", VOCAB) == 54


# --- El recuento por columna, que es lo que se lee en el informe (R14) -----


def test_f045_r11_el_recuento_separa_valor_de_vacia_por_columna():
    filas = [fila(2), fila(3, partida=None, descuento=None), fila(4, partida="P5.36.01")]
    recuento = reparto.recuento_vacios(filas, VOCAB)
    assert recuento["partida"] == {"valor": 2, "vacia": 1, "significado": "interrogante"}
    assert recuento["descuento"] == {"valor": 2, "vacia": 1, "significado": "nulo"}
    assert recuento["ler"]["significado"] == "sin_fila"


def test_f045_r11_el_recuento_cubre_todas_las_columnas_declaradas():
    recuento = reparto.recuento_vacios([fila(2)], VOCAB)
    assert set(recuento) == set(COLUMNAS)


def _tablas(**cambios):
    casos = reparto.agrupar_por_albaran([fila(**cambios)], VOCAB)
    reparto.asignar_casos_id(casos, {})
    return reparto.repartir(casos[0], VOCAB)
