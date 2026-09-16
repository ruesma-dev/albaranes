# tests/test_f045_r12bis_incremento_deducido.py
"""F-045 · el incremento por LER se DEDUCE del contrato, no se lee del papel.

Decisión del humano del 2026-09-16, que cierra el ground truth contradictorio
de RES-004: «estan en albaran. con el codigo ler y mirando en el contrato se
deduce si se necesita incremento por ler, ya que en el contrato pone incremento
por codigo ler xxx, o incremento por canon de (material, tipologia) y de ahi se
deduce el ler».

Son **dos líneas distintas, una por fase**:

- la **línea de material** está impresa, con su código LER → `IA1.lineas`;
- el **incremento** no está impreso: sale de mirar el contrato con ese LER →
  sintética esperada de `IA3`, y línea añadida del FINAL.

El Excel marca las dos `EN ALBARAN` porque el humano describe el albarán, no
las fases; el volcado es quien tiene que separarlas. Encaja con el criterio que
ya estaba en `design.md` §5 ter: si el contrato no trae el LER, el incremento
se deduce del **canon**, que es lo mismo por otro nombre.

Esto NO implementa el criterio en sv5/sv6 —sigue sin estar, y sus casos siguen
naciendo rojos a propósito—: solo deja de pedirle a la extracción una línea que
el papel no imprime.
"""

from __future__ import annotations

import pytest

from evals.revision import escritura, reparto, vocabulario
from evals.revision.modelos import FilaPlana

VOCAB = vocabulario.cargar()

BASE = {
    "codigo_albaran": "0003967",
    "tipo_albaran": "RESIDUOS",
    "cif": "B82899550",
    "nombre_empresa": "SALMEDINA TRATAMIENTO DE RESIDUOS INERTES, S.L.",
    "codigo_obra": "687",
    "fecha": "2024-07-10",
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
    "ler": "17 06 04",
    "comentarios": None,
}


def fila(numero, **cambios):
    valores = dict(BASE)
    valores.update(cambios)
    return FilaPlana(numero_fila=numero, valores=valores)


def tablas_de(*filas):
    casos = reparto.agrupar_por_albaran(list(filas), VOCAB)
    reparto.asignar_casos_id(casos, {})
    return reparto.repartir(casos[0], VOCAB)


INCREMENTO = dict(concepto="INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO-E",
                  precio_unitario=90, importe=90)


# --- Las dos líneas, cada una en su fase ---------------------------------


def test_f045_r12bis_el_material_impreso_si_va_a_ia1():
    tablas = tablas_de(fila(2), fila(3, **INCREMENTO))
    assert [f["descripcion_esperada"] for f in tablas["IA1"]["lineas"]] == [
        "CAMBIO CONTENEDOR 6M3"
    ]


def test_f045_r12bis_el_incremento_por_ler_es_una_sintetica_no_una_linea_leida():
    tablas = tablas_de(fila(2), fila(3, **INCREMENTO))
    sinteticas = tablas["IA3"]["sinteticas_esperadas"]
    assert len(sinteticas) == 1
    assert sinteticas[0]["descripcion_esperada"].startswith("INCREMENTO LER 170604")
    assert sinteticas[0]["num_linea_base"] == 1
    assert sinteticas[0]["precio_unitario"] == 90
    assert tablas["FINAL"]["lineas_anadidas"][0]["concepto"].startswith("INCREMENTO LER")


def test_f045_r12bis_el_incremento_tampoco_es_una_linea_valorada_de_ia3():
    """Si estuviera en TABLA 1 se le exigiría dos veces: leída y deducida."""
    tablas = tablas_de(fila(2), fila(3, **INCREMENTO))
    assert len(tablas["IA3"]["lineas_valoradas"]) == 1
    assert len(tablas["FINAL"]["lineas"]) == 1


@pytest.mark.parametrize(
    "concepto",
    ["INCREMENTO LER 170802 MAT. DE CONST.", "INCREMENTO LEER 17 08 02",
     "INCREM. LER 170604", "CANON DE VERTEDERO"],
)
def test_f045_r12bis_se_reconoce_como_lo_escriba_el_humano(concepto):
    tablas = tablas_de(fila(2), fila(3, concepto=concepto))
    assert len(tablas["IA1"]["lineas"]) == 1
    assert len(tablas["IA3"]["sinteticas_esperadas"]) == 1


def test_f045_r12bis_fuera_de_residuos_manda_la_columna_de_origen():
    """En hormigón el incremento por año SÍ puede venir impreso; la regla es de

    residuos, que es donde el humano la ha enunciado."""
    tablas = tablas_de(
        fila(2, tipo_albaran="HORMIGON", cif="B04685541", ler=None),
        fila(3, tipo_albaran="HORMIGON", cif="B04685541", ler=None,
             concepto="INCREMENTO POR AÑO 2025 EN HORMIGON"),
    )
    assert len(tablas["IA1"]["lineas"]) == 2
    assert tablas["IA3"]["sinteticas_esperadas"] == []


def test_f045_r12bis_una_linea_de_material_con_LER_no_se_confunde():
    tablas = tablas_de(fila(2, concepto="RCDS. SUCIOS"), fila(3, **INCREMENTO))
    assert [f["descripcion_esperada"] for f in tablas["IA1"]["lineas"]] == ["RCDS. SUCIOS"]


def test_f045_r12bis_la_regla_vive_en_el_vocabulario_no_en_el_codigo():
    regla = VOCAB.deducidas_por_concepto
    assert regla["familias"] == ["residuos"]
    assert "INCREMENTO" in regla["marcas"] and "CANON" in regla["marcas"]


# --- Y no duplica la sintética que el humano ya había escrito a mano -----


def test_f045_r12bis_la_sintetica_importada_se_funde_con_la_escrita_a_mano():
    """El libro dice `INCREMENTO LER 170604` y el Excel trae el concepto entero.

    Son la MISMA línea: si se escribieran las dos, el banco esperaría dos
    sintéticas donde el sistema emite una, y eso es un rojo que no existe.
    """
    existentes = [
        {"caso_id": "RES-004", "num_linea_base": 1,
         "descripcion_esperada": "INCREMENTO LER 170604", "precio_unitario": 90,
         "comentario": "escrito a mano"}
    ]
    nuevas = [
        {"caso_id": "RES-004", "num_linea_base": 1,
         "descripcion_esperada": "INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO-E",
         "precio_unitario": 90, "comentario": None}
    ]
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea_base", "descripcion_esperada"),
        campo_prefijo="descripcion_esperada",
    )
    assert len(fundidas) == 1
    assert fundidas[0]["precio_unitario"] == 90


def test_f045_r12bis_dos_sinteticas_distintas_del_mismo_caso_no_se_funden():
    """HOR-004 tiene tres, y ninguna es prefijo de otra: son líneas distintas."""
    existentes = [
        {"caso_id": "HOR-004", "num_linea_base": 1,
         "descripcion_esperada": "INCREMENTO POR AÑO 2025 EN HORMIGON"},
    ]
    nuevas = [
        {"caso_id": "HOR-004", "num_linea_base": 1,
         "descripcion_esperada": "INCREMENTO POR AÑO 2026 EN HORMIGON"},
    ]
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea_base", "descripcion_esperada"),
        campo_prefijo="descripcion_esperada",
    )
    assert len(fundidas) == 2


def test_f045_r12bis_ante_dos_candidatos_por_prefijo_no_se_elige_ninguno():
    """Adivinar cuál de los dos es sería peor que dejar la fila nueva aparte."""
    existentes = [
        {"caso_id": "X", "num_linea_base": 1, "descripcion_esperada": "INCREMENTO"},
        {"caso_id": "X", "num_linea_base": 1, "descripcion_esperada": "INCREMENTO LER"},
    ]
    nuevas = [
        {"caso_id": "X", "num_linea_base": 1,
         "descripcion_esperada": "INCREMENTO LER 170604"},
    ]
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea_base", "descripcion_esperada"),
        campo_prefijo="descripcion_esperada",
    )
    assert len(fundidas) == 3


# --- Y el importador retira lo que él mismo escribió y ya no produce -----


def test_f045_r17_una_fila_que_el_importador_dejo_de_producir_se_retira(tmp_path):
    """La otra mitad de la decisión del 2026-09-16.

    Las importaciones anteriores escribieron el incremento como línea de IA1.
    Ahora ya no lo hacen, pero la fusión conservadora **mantiene lo que no
    genera**: sin memoria de lo suyo, esas filas se quedarían para siempre y el
    banco seguiría exigiendo por los dos caminos. La huella dice qué escribió
    el importador la vez anterior, y solo eso se retira.
    """
    from evals.revision import huella

    existentes = [
        {"caso_id": "RES-004", "num_linea": 1, "descripcion_esperada": "CAMBIO CONTENEDOR"},
        {"caso_id": "RES-004", "num_linea": 2, "descripcion_esperada": "INCREMENTO LER 170604"},
        {"caso_id": "RES-004", "num_linea": 3, "descripcion_esperada": "A MANO"},
    ]
    nuevas = [
        {"caso_id": "RES-004", "num_linea": 1, "descripcion_esperada": "CAMBIO CONTENEDOR 6M3"},
    ]
    # La importación anterior escribió las líneas 1 y 2; la 3 la puso el humano.
    previa = {"lineas": [["RES-004", "1"], ["RES-004", "2"]]}
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea"),
        mias=huella.claves_de(previa, "lineas"),
    )
    assert [f["num_linea"] for f in fundidas] == [1, 3]
    assert fundidas[0]["descripcion_esperada"] == "CAMBIO CONTENEDOR 6M3"


def test_f045_r17_sin_huella_no_se_retira_nada(tmp_path):
    """Primera importación, o huella perdida: se conserva todo, como hasta hoy."""
    existentes = [{"caso_id": "RES-004", "num_linea": 2, "descripcion_esperada": "X"}]
    fundidas = escritura.fundir_filas(existentes, [], ("caso_id", "num_linea"), mias=None)
    assert len(fundidas) == 1


def test_f045_r17_lo_que_escribio_el_humano_nunca_se_retira():
    """Aunque el importador ya no produzca esa fila: no era suya."""
    from evals.revision import huella

    existentes = [{"caso_id": "RES-001", "num_linea": 1, "campo_contexto": "volumen_m3"}]
    fundidas = escritura.fundir_filas(
        existentes, [], ("caso_id", "num_linea", "campo_contexto"),
        mias=huella.claves_de({"contexto": [["RES-001", "1", "codigo_ler"]]}, "contexto"),
    )
    assert len(fundidas) == 1


def test_f045_r12bis_la_sintetica_casa_aunque_el_humano_escriba_LEER_y_espacios():
    """RES-007: el libro dice `INCREMENTO LER 170802` y el Excel

    `INCREMENTO LEER 17 08 02`. Ni una es prefijo de la otra, pero hay UNA de
    cada sobre la misma línea base: son la misma, y escribir las dos haría que
    el banco esperase dos sintéticas donde el sistema emite una.
    """
    existentes = [{"caso_id": "RES-007", "num_linea_base": 1,
                   "descripcion_esperada": "INCREMENTO LER 170802", "precio_unitario": 77}]
    nuevas = [{"caso_id": "RES-007", "num_linea_base": 1,
               "descripcion_esperada": "INCREMENTO LEER 17 08 02", "precio_unitario": 77}]
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea_base", "descripcion_esperada"),
        campo_prefijo="descripcion_esperada",
    )
    assert len(fundidas) == 1


def test_f045_r12bis_con_varias_sinteticas_en_la_misma_base_no_se_adivina():
    existentes = [
        {"caso_id": "HOR-004", "num_linea_base": 1, "descripcion_esperada": "INCREM. AÑO 2025"},
        {"caso_id": "HOR-004", "num_linea_base": 1, "descripcion_esperada": "INCREM. AÑO 2026"},
    ]
    nuevas = [{"caso_id": "HOR-004", "num_linea_base": 1,
               "descripcion_esperada": "INCREMENTO POR GESTION DE RESIDUOS"}]
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea_base", "descripcion_esperada"),
        campo_prefijo="descripcion_esperada",
    )
    assert len(fundidas) == 3


def test_f045_r17_una_fila_ya_fusionada_no_se_retira_con_lo_del_humano_dentro():
    """El agujero que abrió la huella el 2026-09-16, y que costó tres casos RES.

    Al fusionar, la fila del humano toma la clave del importador; desde ese
    momento la huella la da por suya. Si se retira, se lleva por delante lo que
    el humano había escrito —aquí `modifier_source`, que el importador siempre
    deja en `?`—. Solo se retira lo que no lleva nada que él no pudiera poner.
    """
    from evals.revision import huella

    existentes = [
        {"caso_id": "RES-004", "num_linea_base": 1, "modifier_source": "gestion_residuos",
         "descripcion_esperada": "INCREMENTO LER 170604 MATERIALES", "precio_unitario": 90},
        {"caso_id": "RES-004", "num_linea_base": 2, "modifier_source": "?",
         "descripcion_esperada": "SOLO DEL IMPORTADOR", "precio_unitario": 5},
    ]
    nuevas = [{"caso_id": "RES-004", "num_linea_base": 9, "modifier_source": "?",
               "descripcion_esperada": "OTRA", "precio_unitario": 1}]
    previa = {"sinteticas_esperadas": [
        ["RES-004", "1", "INCREMENTO LER 170604 MATERIALES"],
        ["RES-004", "2", "SOLO DEL IMPORTADOR"],
    ]}
    fundidas = escritura.fundir_filas(
        existentes, nuevas, ("caso_id", "num_linea_base", "descripcion_esperada"),
        mias=huella.claves_de(previa, "sinteticas_esperadas"),
    )
    quedan = [f["descripcion_esperada"] for f in fundidas]
    assert "INCREMENTO LER 170604 MATERIALES" in quedan  # lleva algo del humano
    assert "SOLO DEL IMPORTADOR" not in quedan           # no lleva nada suyo
