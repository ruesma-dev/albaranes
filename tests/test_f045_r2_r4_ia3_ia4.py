# tests/test_f045_r2_r4_ia3_ia4.py
"""F-045 · R2 y R4: lo que el sistema DECIDE se le exige a la valoración.

La partida final, el precio unitario y el importe se le piden a IA3 y al
resultado final SIEMPRE, vengan de donde vengan: el patrón 1 —la partida se lee
mal— vive en la decisión, no solo en la lectura. Y cuando el unitario no está
impreso, IA1 va vacía (null afirmado, R4) y el dato viaja entero a IA3: es la
separación extracción/valoración que pidió el humano.
"""

from __future__ import annotations

from evals.revision import reparto, vocabulario
from evals.revision.modelos import FilaPlana

VOCAB = vocabulario.cargar()

BASE = {
    "codigo_albaran": "2139643",
    "tipo_albaran": "FERRETERIA",
    "cif": "A28733558",
    "nombre_empresa": "FEYMACO",
    "codigo_obra": "696",
    "fecha": "2026-06-05",
    "codigo_contrato": "CTSU24/0454",
    "partida": "CI.4.18",
    "origen_linea": "EN ALBARAN",
    "origen_contrato": "NUEVA",
    "concepto": "DISCO ESPECIAL ACERO INOX 115x1x22",
    "cantidad": 50,
    "unidad": "UD",
    "precio_unitario": 0.647,
    "origen_precio": "ALBARAN",
    "importe": 19.41,
    "origen_importe": "ALBARAN VALORADO",
    "descuento": 0.4,
    "ler": None,
    "comentarios": None,
}


def fila(numero=2, **cambios):
    valores = dict(BASE)
    valores.update(cambios)
    return FilaPlana(numero_fila=numero, valores=valores)


def tablas_de(*filas):
    casos = reparto.agrupar_por_albaran(list(filas) or [fila()], VOCAB)
    reparto.asignar_casos_id(casos, {})
    return reparto.repartir(casos[0], VOCAB)


# --- IA3, tabla 1 -----------------------------------------------------------


def test_f045_r2_la_partida_final_se_le_exige_siempre_a_la_valoracion():
    valorada = tablas_de()["IA3"]["lineas_valoradas"][0]
    assert valorada["codigo_partida_final"] == "CI.4.18"
    assert valorada["precio_unitario_final"] == 0.647
    assert valorada["importe_calculado"] == 19.41


def test_f045_r2_precio_source_traduce_el_origen_del_unitario():
    assert tablas_de()["IA3"]["lineas_valoradas"][0]["precio_source"] == "albaran"
    de_contrato = tablas_de(fila(2, origen_precio="DE CONTRATO"))
    assert de_contrato["IA3"]["lineas_valoradas"][0]["precio_source"] == "contrato_db"
    de_oferta = tablas_de(fila(2, origen_precio="EN OFERTA"))
    assert de_oferta["IA3"]["lineas_valoradas"][0]["precio_source"] == "oferta"


def test_f045_r2_una_linea_nueva_no_casa_con_ninguna_del_contrato():
    valorada = tablas_de()["IA3"]["lineas_valoradas"][0]
    assert valorada["match_method"] == "no_match"
    assert valorada["codigo_producto_contrato"] is None


def test_f045_r2_una_linea_en_contrato_casa_pero_el_excel_no_dice_como():
    """R11: el Excel dice que casa, no con qué `match_method`. No se supone."""
    valorada = tablas_de(fila(2, origen_contrato="EN CONTRATO"))["IA3"]["lineas_valoradas"][0]
    assert valorada["match_method"] == "?"
    assert valorada["codigo_producto_contrato"] == "?"


def test_f045_r2_el_codigo_de_producto_sale_de_su_columna_fuera_de_residuos():
    valorada = tablas_de(
        fila(2, origen_contrato="EN CONTRATO", ler="ART-1234")
    )["IA3"]["lineas_valoradas"][0]
    assert valorada["codigo_producto_contrato"] == "ART-1234"


def test_f045_r2_en_residuos_ese_codigo_es_el_LER_y_no_va_a_ia3():
    valorada = tablas_de(
        fila(2, tipo_albaran="RESIDUOS", cif="B82899550",
             origen_contrato="EN CONTRATO", ler="17 08 02")
    )["IA3"]["lineas_valoradas"][0]
    assert valorada["codigo_producto_contrato"] == "?"


def test_f045_r2_la_deducida_no_es_una_linea_valorada():
    tablas = tablas_de(fila(2), fila(3, origen_linea="DEDUCIDA INCREMENTO POR AÑO"))
    assert len(tablas["IA3"]["lineas_valoradas"]) == 1


# --- IA4: solo las líneas que no casan llegan a la conciliación -----------


def test_f045_r2_la_linea_nueva_pasa_a_ia4():
    conciliacion = tablas_de()["IA4"]["conciliacion"]
    assert len(conciliacion) == 1
    assert conciliacion[0]["num_linea"] == 1
    assert conciliacion[0]["precio_unitario_esperado"] == 0.647
    # El Excel no dice si lo correcto es conciliar o dejarla a revisión.
    assert conciliacion[0]["concilia"] == "?"


def test_f045_r2_una_linea_del_contrato_no_pasa_por_ia4():
    assert tablas_de(fila(2, origen_contrato="EN CONTRATO"))["IA4"]["conciliacion"] == []


def test_f045_r4_el_unitario_de_oferta_sale_de_ia1_y_entra_en_ia3():
    tablas = tablas_de(fila(2, origen_precio="EN OFERTA", origen_importe="EN OFERTA"))
    assert tablas["IA1"]["lineas"][0]["precio_unitario"] is None
    assert tablas["IA3"]["lineas_valoradas"][0]["precio_unitario_final"] == 0.647
    assert tablas["IA3"]["lineas_valoradas"][0]["precio_source"] == "oferta"
