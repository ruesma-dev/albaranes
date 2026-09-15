# tests/test_f045_r2_inputs_final.py
"""F-045 · R2: `INPUTS` y `RESULTADO_FINAL`.

`RESULTADO_FINAL` es la referencia MAESTRA: cómo debe quedar el albarán al
acabar el proceso. Ahí sí van la obra y el CIF del proveedor identificado, que
es justo lo que NO se le exige a la extracción (R13).

`INPUTS` es otra cosa: es la ENTRADA que se le da a la valoración, no una
expectativa. Por eso ahí no se escribe nunca un `?`: el sentinela significa
«no compares», y en una entrada no hay nada que comparar —viajaría como texto
literal dentro de la carga que lee sv5—.
"""

from __future__ import annotations

from evals.revision import reparto, vocabulario
from evals.revision.modelos import FilaPlana

VOCAB = vocabulario.cargar()

BASE = {
    "codigo_albaran": "0025146",
    "tipo_albaran": "RESIDUOS",
    "cif": "B82899550",
    "nombre_empresa": "SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L.",
    "codigo_obra": "691",
    "fecha": "2024-11-05",
    "codigo_contrato": "CTSU24/0402",
    "partida": "CI.03A.7",
    "origen_linea": "EN ALBARAN",
    "origen_contrato": "CONTRATO",
    "concepto": "CONTENEDOR DE RESIDUOS 6 M3",
    "cantidad": 1,
    "unidad": "UD",
    "precio_unitario": 136,
    "origen_precio": "CONTRATO",
    "importe": 136,
    "origen_importe": "CONTRATO",
    "descuento": None,
    "ler": "17 09 04",
    "comentarios": None,
}


def fila(numero=2, **cambios):
    valores = dict(BASE)
    valores.update(cambios)
    return FilaPlana(numero_fila=numero, valores=valores)


def tablas_de(*filas, fichero=""):
    casos = reparto.agrupar_por_albaran(list(filas) or [fila()], VOCAB)
    reparto.asignar_casos_id(casos, {})
    casos[0].fichero = fichero
    return reparto.repartir(casos[0], VOCAB)


# --- RESULTADO_FINAL, tabla 1 ----------------------------------------------


def test_f045_r2_la_obra_y_el_cif_se_le_exigen_al_resultado_final():
    generales = tablas_de()["FINAL"]["datos_generales"][0]
    assert generales["obra"] == "691"
    assert generales["cif"] == "B82899550"
    assert generales["contrato_elegido"] == "CTSU24/0402"


def test_f045_r2_el_numero_de_albaran_tampoco_se_compara_en_el_final():
    """El código del humano (0025146) no es el literal impreso (SS-0025146)."""
    assert tablas_de()["FINAL"]["datos_generales"][0]["numero_albaran"] == "?"


def test_f045_r2_el_total_valorado_es_la_suma_de_los_importes():
    tablas = tablas_de(
        fila(2),
        fila(3, origen_linea="DEDUCIDA", origen_contrato="NUEVA",
             concepto="INCREMENTO LER 170904", importe=77),
    )
    assert tablas["FINAL"]["datos_generales"][0]["total_valorado_esperado"] == 213


def test_f045_r2_un_importe_sin_afirmar_deja_el_total_sin_comparar():
    """Sumar sobre un hueco daría un total falso con pinta de bueno."""
    tablas = tablas_de(fila(2), fila(3, importe=None))
    assert tablas["FINAL"]["datos_generales"][0]["total_valorado_esperado"] == "?"


def test_f045_r2_hay_una_sola_fila_de_datos_generales_por_caso():
    tablas = tablas_de(fila(2), fila(3, concepto="OTRA LINEA"))
    assert len(tablas["FINAL"]["datos_generales"]) == 1


# --- INPUTS -----------------------------------------------------------------


def test_f045_r2_inputs_declara_la_familia_de_documento_no_la_pestana():
    caso = tablas_de()["INPUTS"]["caso"][0]
    assert caso["tipologia"] == "residuos"
    assert caso["origen"] == "manual"
    assert caso["contrato_codigo"] == "CTSU24/0402"


def test_f045_r2_inputs_manda_a_ia4_solo_si_hay_lineas_nuevas():
    assert tablas_de()["INPUTS"]["caso"][0]["ia_destino"] == "IA3"
    con_nueva = tablas_de(fila(2, origen_contrato="NUEVA"))
    assert con_nueva["INPUTS"]["caso"][0]["ia_destino"] == "ambas"


def test_f045_r2_inputs_no_escribe_jamas_un_interrogante():
    """En una entrada el sentinela `?` viajaría como texto literal a sv5."""
    tablas = tablas_de(fila(2, partida=None, precio_unitario=None, importe=None))
    for filas in tablas["INPUTS"].values():
        for registro in filas:
            assert "?" not in [v for v in registro.values() if isinstance(v, str)]


def test_f045_r2_las_lineas_de_entrada_son_las_impresas():
    tablas = tablas_de(fila(2), fila(3, origen_linea="DEDUCIDA", origen_contrato="NUEVA"))
    lineas = tablas["INPUTS"]["lineas_albaran"]
    assert len(lineas) == 1
    assert lineas[0]["descripcion"] == "CONTENEDOR DE RESIDUOS 6 M3"
    assert lineas[0]["cantidad"] == 1


def test_f045_r2_la_entrada_no_trae_el_precio_que_no_imprime_el_papel():
    """Si el unitario sale del contrato, dárselo a la valoración es hacerle
    el trabajo: la entrada es lo que llega, no lo que hay que decidir."""
    linea = tablas_de()["INPUTS"]["lineas_albaran"][0]
    assert linea["precio_unitario"] is None
    del_albaran = tablas_de(fila(2, origen_precio="ALBARAN", precio_unitario=0.647))
    assert del_albaran["INPUTS"]["lineas_albaran"][0]["precio_unitario"] == 0.647


def test_f045_r2_no_se_alimentan_las_lineas_de_contrato():
    """Design §3: la revisión manual no las trae, y lo que no alimenta no toca."""
    assert "contrato_lineas" not in reparto.TABLAS["INPUTS"]
    assert "condiciones" not in reparto.TABLAS["INPUTS"]
    assert "sinteticas_prohibidas" not in reparto.TABLAS["IA3"]
