# tests/test_f045_r9_r10_clasificacion.py
"""F-045 · R9 y R10: el comentario dice qué falla HOY, no qué se espera.

Es el eje que más fácil se malinterpreta, y malinterpretarlo tira los casos
más valiosos del banco. Corrección del humano (2026-09-15): «celda vacia EN
COMENTARIOS no es que no se compare. es que ha salido ok en las pruebas. pero
hay que seguir validando en los evals que sigue saliendo bien».

Así que un comentario vacío NO produce jamás un `?`: produce un caso de **no
regresión**, que se compara igual y hoy debe salir VERDE. El `?` solo lo
produce un VALOR ESPERADO ausente, que es el otro eje.
"""

from __future__ import annotations

from evals.revision import reparto, vocabulario
from evals.revision.modelos import DEFECTO_CONOCIDO, NO_REGRESION, FilaPlana

VOCAB = vocabulario.cargar()

BASE = {
    "codigo_albaran": "225137",
    "tipo_albaran": "HORMIGON",
    "cif": "B04685541",
    "nombre_empresa": "HORPRESOL, S.L.",
    "codigo_obra": "693",
    "fecha": "2026-03-11",
    "codigo_contrato": "CTSU23/0386",
    "partida": "P5.14.01",
    "origen_linea": "EN ALBARAN",
    "origen_contrato": "EN CONTRATO",
    "concepto": "HA-25/B/20/IIa",
    "cantidad": 8,
    "unidad": "M3",
    "precio_unitario": 72.5,
    "origen_precio": "DE CONTRATO",
    "importe": 580,
    "origen_importe": "DE CONTRATO",
    "descuento": None,
    "ler": None,
    "comentarios": None,
}


def fila(numero, **cambios):
    valores = dict(BASE)
    valores.update(cambios)
    return FilaPlana(numero_fila=numero, valores=valores)


def casos_de(filas):
    casos = reparto.agrupar_por_albaran(filas, VOCAB)
    reparto.asignar_casos_id(casos, {})
    return casos


def test_f045_r9_comentario_vacio_es_un_caso_de_no_regresion():
    caso = casos_de([fila(2)])[0]
    assert caso.clasificacion == NO_REGRESION


def test_f045_r9_el_comentario_vacio_no_produce_ni_un_interrogante():
    """El vacío del comentario y el del valor son cosas distintas (D3)."""
    tablas = reparto.repartir(casos_de([fila(2)])[0], VOCAB)
    linea = tablas["IA1"]["lineas"][0]
    assert linea["cantidad"] == 8
    assert linea["comentario"] is None
    assert reparto.INTERROGANTE not in (linea["cantidad"], linea["descripcion_esperada"])


def test_f045_r10_comentario_con_texto_es_defecto_conocido_y_se_copia():
    caso = casos_de([fila(2, comentarios="falta P5 al inicio de la partida.")])[0]
    assert caso.clasificacion == DEFECTO_CONOCIDO
    tablas = reparto.repartir(caso, VOCAB)
    assert tablas["IA1"]["lineas"][0]["comentario"] == "falta P5 al inicio de la partida."


def test_f045_r10_el_valor_se_compara_igual_aunque_haya_comentario():
    """Un defecto conocido no deja de comprobarse: por eso está en el banco."""
    caso = casos_de([fila(2, comentarios="la partida ha puesto RJ.14 en lugar de P5.14")])[0]
    tablas = reparto.repartir(caso, VOCAB)
    assert tablas["IA1"]["lineas"][0]["cantidad"] == 8


def test_f045_r10_basta_una_linea_comentada_para_que_el_caso_sea_defecto():
    caso = casos_de([fila(2), fila(3, comentarios="No ha cogido la linea.")])[0]
    assert caso.clasificacion == DEFECTO_CONOCIDO


def test_f045_r9_r10_clasificar_reparte_los_casos_en_los_dos_grupos():
    casos = casos_de(
        [
            fila(2),
            fila(3, codigo_albaran="225225", comentarios="No ha cogido la linea."),
            fila(4, codigo_albaran="224964"),
        ]
    )
    grupos = reparto.clasificar(casos)
    assert [c.caso_id for c in grupos[NO_REGRESION]] == ["HOR-001", "HOR-003"]
    assert [c.caso_id for c in grupos[DEFECTO_CONOCIDO]] == ["HOR-002"]


def test_f045_r9_los_comentarios_repetidos_del_mismo_caso_no_se_duplican():
    caso = casos_de([fila(2, comentarios="misma nota"), fila(3, comentarios="misma nota")])[0]
    assert caso.comentarios == ["misma nota"]
