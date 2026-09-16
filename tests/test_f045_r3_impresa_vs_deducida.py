# tests/test_f045_r3_impresa_vs_deducida.py
"""F-045 · R3: lo impreso es de la EXTRACCIÓN; lo deducido, de la VALORACIÓN.

El Excel mezcla las dos cosas en la misma fila y separarlas es el trabajo. Una
línea deducida —un incremento por cambio de año, una carga incompleta— NO
existe en el papel: escribirla en IA1 le exigiría a la extracción que la
invente, y el rojo resultante no diría nada de nadie.
"""

from __future__ import annotations

from evals.revision import reparto, vocabulario
from evals.revision.modelos import FilaPlana

VOCAB = vocabulario.cargar()

BASE = {
    "codigo_albaran": "24346",
    "tipo_albaran": "RESIDUOS",
    "cif": "B93649002",
    "nombre_empresa": "CARGA Y TRANSPORTE DE CUBAS, S.L.",
    "codigo_obra": "669",
    "fecha": "2025-09-09",
    "codigo_contrato": "CTSB23/0964",
    "partida": "CI.03A.7",
    "origen_linea": "EN ALBARAN",
    "origen_contrato": "EN CONTRATO",
    "concepto": "CONTENEDOR DE 8M3",
    "cantidad": 1,
    "unidad": "UD",
    "precio_unitario": 90,
    "origen_precio": "DE CONTRATO",
    "importe": 90,
    "origen_importe": "DE CONTRATO",
    "descuento": 0,
    "ler": None,
    "comentarios": None,
}


def fila(numero, **cambios):
    valores = dict(BASE)
    valores.update(cambios)
    return FilaPlana(numero_fila=numero, valores=valores)


def repartir(filas):
    casos = reparto.agrupar_por_albaran(filas, VOCAB)
    reparto.asignar_casos_id(casos, {})
    return reparto.repartir(casos[0], VOCAB), casos[0]


def test_f045_r3_la_linea_deducida_no_aparece_en_ia1():
    tablas, _ = repartir(
        [
            fila(2),
            fila(3, concepto="RCDS. SUCIOS", cantidad=3, unidad="M3", precio_unitario=26,
                 importe=78, origen_linea="EN ALBARAN 189502"),
            fila(4, origen_linea="DEDUCIDO. INCREM. CAMBIO AÑO", origen_contrato="NUEVA",
                 concepto="RCDS. SUCIOS. INCREM. 2025", cantidad=3, unidad="M3",
                 precio_unitario=4, origen_precio="EN OFERTA", importe=12,
                 origen_importe="EN OFERTA"),
        ]
    )
    conceptos_ia1 = [f["descripcion_esperada"] for f in tablas["IA1"]["lineas"]]
    assert conceptos_ia1 == ["CONTENEDOR DE 8M3", "RCDS. SUCIOS"]
    assert "RCDS. SUCIOS. INCREM. 2025" not in conceptos_ia1


def test_f045_r3_la_linea_deducida_es_una_sintetica_esperada():
    tablas, _ = repartir(
        [fila(2), fila(3, origen_linea="DEDUCIDA INCREMENTO POR AÑO",
                       origen_contrato="NUEVA", concepto="INCREM. PRECIO 2026",
                       cantidad=1, precio_unitario=6, importe=6,
                       origen_precio="OFERTA", origen_importe="OFERTA")]
    )
    sinteticas = tablas["IA3"]["sinteticas_esperadas"]
    assert len(sinteticas) == 1
    assert sinteticas[0]["descripcion_esperada"] == "INCREM. PRECIO 2026"
    # Cuelga de la línea impresa que la precede: es su num_linea_base.
    assert sinteticas[0]["num_linea_base"] == 1
    assert tablas["FINAL"]["lineas_anadidas"][0]["concepto"] == "INCREM. PRECIO 2026"


def test_f045_r3_las_impresas_se_numeran_1_2_3_y_la_deducida_no_gasta_numero():
    tablas, _ = repartir(
        [
            fila(2),
            fila(3, origen_linea="DEDUCIDA INCREMENTO POR AÑO", origen_contrato="NUEVA"),
            fila(4, concepto="RCDS. VOLUMINOSOS"),
        ]
    )
    assert [f["num_linea"] for f in tablas["IA1"]["lineas"]] == [1, 2]


def test_f045_r3_una_deducida_sin_linea_impresa_delante_no_inventa_base():
    """R11: si la fila no permite decidir sobre qué línea va, `?`, no un 1."""
    tablas, _ = repartir(
        [fila(2, origen_linea="DEDUCIDA INCREMENTO POR AÑO", origen_contrato="NUEVA")]
    )
    assert tablas["IA1"]["lineas"] == []
    assert tablas["IA3"]["sinteticas_esperadas"][0]["num_linea_base"] == "?"


def test_f045_r3_en_albaran_con_cola_libre_sigue_siendo_impresa():
    tablas, _ = repartir([fila(2, origen_linea='EN ALBARAN PERO DEDUCE AUMENTO POR "JIB"')])
    assert len(tablas["IA1"]["lineas"]) == 1
