# tests/test_f045_r2_r13_ia1_ia2.py
"""F-045 · R2 y R13: qué le toca a la EXTRACCIÓN y qué no.

R13 es contraintuitivo y por eso tiene test propio: el número de albarán y la
obra van `?` en IA1. El código de la tabla plana es la CLAVE con la que el
humano identifica el documento (`0000168`), no el literal impreso
(`SS-0000168`): compararlos daría un rojo falso en todos los casos. Y deducir
la obra no es extraer —el papel a menudo no la trae—, así que la obra se le
exige al resultado final, no a IA1.

Mismo criterio que los 7 casos RES que ya estaban en el banco.
"""

from __future__ import annotations

from evals.revision import reparto, vocabulario
from evals.revision.modelos import FilaPlana

VOCAB = vocabulario.cargar()

BASE = {
    "codigo_albaran": "0000168",
    "tipo_albaran": "RESIDUOS",
    "cif": "B82899550",
    "nombre_empresa": "SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L.",
    "codigo_obra": "687",
    "fecha": "2024-07-03",
    "codigo_contrato": "CTSU24/0228",
    "partida": "CI.03A.7",
    "origen_linea": "EN ALBARAN",
    "origen_contrato": "CONTRATO",
    "concepto": "CAMBIO CONTENEDOR 6M3",
    "cantidad": 1,
    "unidad": "UD",
    "precio_unitario": 120,
    "origen_precio": "CONTRATO",
    "importe": 120,
    "origen_importe": "CONTRATO",
    "descuento": None,
    "ler": "17 02 01",
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


# --- IA1, cabeceras ---------------------------------------------------------


def test_f045_r13_numero_de_albaran_y_obra_van_interrogante_en_ia1():
    cabecera = tablas_de()["IA1"]["cabeceras"][0]
    assert cabecera["numero_albaran"] == "?"
    assert cabecera["obra_codigo"] == "?"
    assert cabecera["obra_nombre"] == "?"


def test_f045_r13_el_cif_tampoco_se_le_exige_a_la_extraccion():
    """El CIF correcto es el del proveedor identificado, no el impreso."""
    assert tablas_de()["IA1"]["cabeceras"][0]["proveedor_cif"] == "?"


def test_f045_r2_la_razon_social_y_la_fecha_si_son_de_ia1():
    cabecera = tablas_de()["IA1"]["cabeceras"][0]
    assert cabecera["proveedor_nombre"] == "SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L."
    assert cabecera["fecha"] == "2024-07-03"


def test_f045_r2_hay_exactamente_una_cabecera_por_caso():
    cabeceras = tablas_de(fila(2), fila(3, concepto="INCREMENTO LER"))["IA1"]["cabeceras"]
    assert len(cabeceras) == 1
    assert cabeceras[0]["caso_id"] == "RES-001"


def test_f045_r2_la_forma_de_pago_no_esta_en_la_tabla_plana():
    """Lo que el Excel no dice, no se compara: `?`, jamás un null afirmado."""
    assert tablas_de()["IA1"]["cabeceras"][0]["forma_pago"] == "?"


def test_f045_r2_el_fichero_del_albaran_sale_del_emparejado():
    assert tablas_de(fichero="RES-001.pdf")["IA1"]["cabeceras"][0]["fichero_albaran"] == "RES-001.pdf"
    assert tablas_de()["IA1"]["cabeceras"][0]["fichero_albaran"] is None


# --- IA1, líneas: el precio del contrato NO está en el papel (R4) ----------


def test_f045_r4_el_unitario_de_contrato_deja_ia1_vacia_no_interrogante():
    linea = tablas_de()["IA1"]["lineas"][0]
    assert linea["precio_unitario"] is None
    assert linea["importe"] is None


def test_f045_r4_el_unitario_del_albaran_si_va_a_ia1():
    linea = tablas_de(
        fila(2, origen_precio="ALBARAN", precio_unitario=0.647,
             origen_importe="ALBARAN", importe=19.41)
    )["IA1"]["lineas"][0]
    assert linea["precio_unitario"] == 0.647
    assert linea["importe"] == 19.41


# --- IA2: el LER es contexto de LÍNEA -------------------------------------


def test_f045_r2_el_ler_va_a_ia2_con_seis_digitos_sin_espacios():
    contexto = tablas_de()["IA2"]["contexto"]
    assert contexto == [
        {
            "caso_id": "RES-001",
            "num_linea": 1,
            "campo_contexto": "codigo_ler",
            "valor_esperado": "170201",
            "comentario": None,
        }
    ]


def test_f045_r2_sin_ler_no_hay_fila_de_ia2():
    """R12: el vacío del LER dice «no aplica», no «no lo sé»."""
    assert tablas_de(fila(2, ler=None))["IA2"]["contexto"] == []


def test_f045_r2_el_ler_de_una_familia_que_no_es_residuos_no_va_a_ia2():
    fuera = tablas_de(
        fila(2, tipo_albaran="FERRETERIA", cif="A28733558", ler="ART-1234")
    )
    assert fuera["IA2"]["contexto"] == []


def test_f045_r2_una_linea_deducida_no_genera_contexto_de_ia2():
    tablas = tablas_de(fila(2, origen_linea="DEDUCIDA INCREMENTO POR AÑO"))
    assert tablas["IA2"]["contexto"] == []
