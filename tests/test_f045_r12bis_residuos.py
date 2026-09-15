# tests/test_f045_r12bis_residuos.py
"""F-045 · R12 bis: los tres criterios de valoración de residuos.

Criterios del humano del 2026-09-15 (design §5 ter). Son de VALORACIÓN, no de
extracción, y **ninguno está implementado hoy**: sus casos nacen ROJOS a
propósito y sus arreglos son fichas propias. Lo que aquí se comprueba es que
el ground truth los recoge y que el informe los agrupa aparte, para que un
rojo esperado no se confunda con una regresión.

El alcance del mínimo lo cerró el humano: se aplica a lo que se PESA —canon y
tratamiento—, y el movimiento de contenedor sigue en unidades (1 cambio = 1 UD).
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

PESADA = dict(concepto="RCDS. SUCIOS", cantidad=0.42, unidad="M3",
              precio_unitario=26, importe=10.92, ler="17 09 04")


def fila(numero=2, **cambios):
    valores = dict(BASE)
    valores.update(cambios)
    return FilaPlana(numero_fila=numero, valores=valores)


def caso_de(*filas):
    casos = reparto.agrupar_por_albaran(list(filas) or [fila()], VOCAB)
    reparto.asignar_casos_id(casos, {})
    return casos[0]


# --- Mínimo facturable de 1 en lo que se pesa ------------------------------


def test_f045_r12bis_el_minimo_se_aplica_a_lo_que_se_pesa():
    tablas = reparto.repartir(caso_de(fila(2), fila(3, **PESADA)), VOCAB)
    pesada = tablas["FINAL"]["lineas"][1]
    assert pesada["cantidad_final"] == 1
    # Y la cantidad LEÍDA no se toca: 0,42 es lo que imprime el papel.
    assert tablas["IA1"]["lineas"][1]["cantidad"] == 0.42


def test_f045_r12bis_lo_que_ya_supera_el_minimo_se_queda_como_esta():
    tablas = reparto.repartir(caso_de(fila(2), fila(3, **{**PESADA, "cantidad": 3.10})), VOCAB)
    assert tablas["FINAL"]["lineas"][1]["cantidad_final"] == 3.10


def test_f045_r12bis_el_movimiento_de_contenedor_no_se_toca():
    """1 cambio = 1 UD (§10.6): el mínimo no convierte unidades en toneladas."""
    tablas = reparto.repartir(caso_de(fila(2, cantidad=1, unidad="UD")), VOCAB)
    assert tablas["FINAL"]["lineas"][0]["cantidad_final"] == 1
    tablas = reparto.repartir(caso_de(fila(2, cantidad=2, unidad="UD")), VOCAB)
    assert tablas["FINAL"]["lineas"][0]["cantidad_final"] == 2


def test_f045_r12bis_el_minimo_no_sale_de_residuos():
    """30,38 tn de grava son 30,38 tn: el mínimo es criterio de residuos."""
    tablas = reparto.repartir(
        caso_de(fila(2, tipo_albaran="GRAVA", cif="B29679628",
                     concepto="GRAVA 20/40", cantidad=0.5, unidad="TN")),
        VOCAB,
    )
    assert tablas["FINAL"]["lineas"][0]["cantidad_final"] == 0.5


def test_f045_r12bis_el_minimo_tambien_alcanza_a_la_sintetica_pesada():
    caso = caso_de(
        fila(2),
        fila(3, **PESADA),
        fila(4, origen_linea="DEDUCIDO. INCREM. CAMBIO AÑO", origen_contrato="NUEVA",
             concepto="RCDS. SUCIOS. INCREM. 2025", cantidad=0.42, unidad="M3",
             precio_unitario=4, origen_precio="EN OFERTA", importe=1.68,
             origen_importe="EN OFERTA"),
    )
    tablas = reparto.repartir(caso, VOCAB)
    assert tablas["FINAL"]["lineas_anadidas"][0]["cantidad"] == 1
    assert tablas["IA3"]["sinteticas_esperadas"][0]["cantidad"] == 1


# --- Los tres criterios se declaran, y hoy ninguno está implementado -------


def test_f045_r12bis_el_minimo_marca_el_caso_como_criterio_pendiente():
    criterios = reparto.criterios_residuos(caso_de(fila(2), fila(3, **PESADA)), VOCAB)
    assert "minimo_1_tn" in criterios


def test_f045_r12bis_el_incremento_por_ano_en_residuos_se_declara():
    caso = caso_de(
        fila(2),
        fila(3, origen_linea="DEDUCIDO. INCREM. CAMBIO AÑO", origen_contrato="NUEVA",
             concepto="RCDS. SUCIOS. INCREM. 2025", origen_precio="EN OFERTA",
             origen_importe="EN OFERTA"),
    )
    assert "incremento_por_ano" in reparto.criterios_residuos(caso, VOCAB)


def test_f045_r12bis_el_canon_por_ler_se_declara():
    caso = caso_de(
        fila(2, ler="17 06 04"),
        fila(3, origen_linea="DEDUCIDA", origen_contrato="NUEVA",
             concepto="INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO",
             ler="17 06 04"),
    )
    assert "canon_por_ler" in reparto.criterios_residuos(caso, VOCAB)


def test_f045_r12bis_un_caso_que_no_es_de_residuos_no_declara_criterios():
    caso = caso_de(fila(2, tipo_albaran="HORMIGON", cif="B04685541", unidad="M3", cantidad=0.4))
    assert reparto.criterios_residuos(caso, VOCAB) == []


def test_f045_r12bis_los_tres_criterios_estan_declarados_en_el_vocabulario():
    declarados = VOCAB.criterios_residuos
    assert set(declarados) == {"minimo_1_tn", "incremento_por_ano", "canon_por_ler"}
    for criterio in declarados.values():
        assert criterio["titulo"]
        assert criterio["implementado"] is False
