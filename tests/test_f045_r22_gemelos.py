# tests/test_f045_r22_gemelos.py
"""F-045 · R22: el mismo albarán en PDF y en imagen son DOS casos.

No es un choque de duplicados: es el único experimento del banco que aísla el
FORMATO. Leer píxeles rinde peor que leer caracteres, la rama de imágenes de
sv2 es de julio de 2026 y hoy no la mide nadie. Con el mismo ground truth y
distinta entrada, un fallo que solo aparece en el gemelo de imagen es un
hallazgo de formato, no de extracción.

Por eso **no se deduplica**, y por eso van hermanados por `gemelo_de`: sin ese
hilo, `HOR-012-IMG` en rojo parece un caso suelto más.
"""

from __future__ import annotations

from evals.revision import albaranes, reparto, vocabulario
from evals.revision.modelos import FilaPlana

VOCAB = vocabulario.cargar()


def test_f045_r22_pdf_e_imagen_del_mismo_codigo_dan_dos_casos():
    plan = albaranes.emparejar(
        {"H132525": "HOR-012"}, ["HORPRESOL_H132525.pdf", "H132525.png"]
    )
    assert plan.fallos == []
    assert [(c.caso_id, c.destino, c.formato) for c in plan.copias] == [
        ("HOR-012", "HOR-012.pdf", "pdf"),
        ("HOR-012-IMG", "HOR-012-IMG.png", "imagen"),
    ]


def test_f045_r22_el_gemelo_de_imagen_apunta_a_su_hermano():
    plan = albaranes.emparejar({"H132525": "HOR-012"}, ["A_H132525.pdf", "B_H132525.jpg"])
    por_caso = {c.caso_id: c for c in plan.copias}
    assert por_caso["HOR-012"].gemelo_de == ""
    assert por_caso["HOR-012-IMG"].gemelo_de == "HOR-012"


def test_f045_r22_una_imagen_sola_no_es_un_gemelo():
    """Sin PDF con el que compararla, la imagen ES el caso, sin sufijo."""
    plan = albaranes.emparejar({"H132525": "HOR-012"}, ["H132525.png"])
    assert [(c.caso_id, c.destino) for c in plan.copias] == [("HOR-012", "HOR-012.png")]


def test_f045_r22_dos_imagenes_del_mismo_codigo_si_son_un_choque():
    """El par que aísla el formato es UNO de cada; dos PNG es un duplicado."""
    plan = albaranes.emparejar({"H132525": "HOR-012"}, ["A_H132525.png", "B_H132525.jpg"])
    assert [f.tipo for f in plan.fallos] == ["codigo_duplicado"]
    assert plan.copias == []


def test_f045_r22_el_gemelo_hereda_el_mismo_ground_truth():
    fila = FilaPlana(
        numero_fila=2,
        valores={"codigo_albaran": "H132525", "tipo_albaran": "HORMIGON",
                 "cif": "B04685541", "origen_linea": "EN ALBARAN",
                 "origen_contrato": "EN CONTRATO", "origen_precio": "DE CONTRATO",
                 "origen_importe": "DE CONTRATO", "concepto": "HA-25", "cantidad": 8,
                 "unidad": "M3", "precio_unitario": 72.5, "importe": 580,
                 "partida": "P5.14.01", "codigo_obra": "693"},
    )
    casos = reparto.agrupar_por_albaran([fila], VOCAB)
    reparto.asignar_casos_id(casos, {})
    gemelos = reparto.crear_gemelos(casos, {"HOR-001": "imagen"})

    assert [c.caso_id for c in gemelos] == ["HOR-001-IMG"]
    original = reparto.repartir(casos[0], VOCAB)
    copia = reparto.repartir(gemelos[0], VOCAB)
    assert gemelos[0].gemelo_de == "HOR-001"
    # Mismo ground truth línea a línea, solo cambia a qué caso pertenece.
    assert copia["IA1"]["lineas"][0]["cantidad"] == original["IA1"]["lineas"][0]["cantidad"]
    assert copia["FINAL"]["datos_generales"][0]["obra"] == "693"
    assert copia["IA1"]["cabeceras"][0]["caso_id"] == "HOR-001-IMG"


def test_f045_r22_sin_gemelos_no_se_crea_ningun_caso_extra():
    fila = FilaPlana(
        numero_fila=2,
        valores={"codigo_albaran": "H132525", "tipo_albaran": "HORMIGON",
                 "cif": "B04685541", "origen_linea": "EN ALBARAN",
                 "origen_contrato": "EN CONTRATO", "origen_precio": "DE CONTRATO",
                 "origen_importe": "DE CONTRATO"},
    )
    casos = reparto.agrupar_por_albaran([fila], VOCAB)
    reparto.asignar_casos_id(casos, {})
    assert reparto.crear_gemelos(casos, {}) == []
