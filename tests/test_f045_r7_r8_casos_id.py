# tests/test_f045_r7_r8_casos_id.py
"""F-045 · R7 y R8: el caso_id es estable y el mapa devuelve al papel.

Sin el mapa, un eval en rojo no se audita: nadie sabe qué PDF mirar. Y sin
estabilidad, reimportar el Excel duplicaría el banco entero cada vez que el
humano añade una fila.
"""

from __future__ import annotations

import json

import pytest

from evals.revision import mapa as mapa_mod
from evals.revision import reparto, vocabulario
from evals.revision.modelos import FilaPlana

VOCAB = vocabulario.cargar()


def fila(numero, codigo, tipo="RESIDUOS", cif="B82899550", **extra):
    valores = {
        "codigo_albaran": codigo,
        "tipo_albaran": tipo,
        "cif": cif,
        "origen_linea": "EN ALBARAN",
        "origen_contrato": "CONTRATO",
        "origen_precio": "CONTRATO",
        "origen_importe": "CONTRATO",
    }
    valores.update(extra)
    return FilaPlana(numero_fila=numero, valores=valores)


# --- Clave natural y normalización -----------------------------------------


def test_f045_r7_normalizar_codigo_quita_puntuacion_y_respeta_los_ceros():
    assert reparto.normalizar_codigo("2.115.714") == "2115714"
    assert reparto.normalizar_codigo("2026/01/007378") == "202601007378"
    assert reparto.normalizar_codigo(" mc/26-442903 ") == "MC26442903"
    # Manda el código del papel: SS-0801977 no es SS-0001977, y un normalizador
    # que se comiera los ceros los confundiría (precedente real del proyecto).
    assert reparto.normalizar_codigo("0001977") != reparto.normalizar_codigo("1977")


def test_f045_r7_la_clave_natural_lleva_cif_y_codigo():
    """Dos proveedores pueden numerar su albarán igual; el CIF los separa."""
    uno = reparto.clave_natural(fila(2, "250012", cif="B93649002"))
    otro = reparto.clave_natural(fila(3, "250012", cif="B04685541"))
    assert uno != otro


# --- Agrupado ---------------------------------------------------------------


def test_f045_r7_las_filas_del_mismo_albaran_son_un_caso():
    casos = reparto.agrupar_por_albaran(
        [fila(2, "0000168"), fila(3, "0000168"), fila(4, "0003935")], VOCAB
    )
    assert [c.codigo for c in casos] == ["0000168", "0003935"]
    assert len(casos[0].lineas) == 2


# --- Asignación de caso_id (R7) --------------------------------------------


def test_f045_r7_el_caso_id_lleva_el_prefijo_de_su_pestana():
    casos = reparto.agrupar_por_albaran(
        [fila(2, "H98634", tipo="HORMIGON", cif="B04685541"),
         fila(3, "58826", tipo="GRAVA", cif="B29679628")],
        VOCAB,
    )
    reparto.asignar_casos_id(casos, {})
    assert casos[0].caso_id == "HOR-001"
    assert casos[1].caso_id == "GRA-001"


def test_f045_r7_el_numero_continua_el_del_mapa_no_lo_reinicia():
    mapa = {"RES-001": {"clave": "X/1", "codigo": "1", "pestana": "Residuos"},
            "RES-007": {"clave": "X/7", "codigo": "7", "pestana": "Residuos"}}
    casos = reparto.agrupar_por_albaran([fila(2, "0000168")], VOCAB)
    reparto.asignar_casos_id(casos, mapa)
    assert casos[0].caso_id == "RES-008"


# --- Reimportar NO crea casos nuevos (R8) ----------------------------------


def test_f045_r8_reimportar_reutiliza_el_caso_id():
    filas = [fila(2, "0000168"), fila(3, "0003935")]
    casos = reparto.agrupar_por_albaran(filas, VOCAB)
    mapa, nuevos = reparto.asignar_casos_id(casos, {})
    assert nuevos == ["RES-001", "RES-002"]

    otra_vez = reparto.agrupar_por_albaran(filas, VOCAB)
    mapa2, nuevos2 = reparto.asignar_casos_id(otra_vez, mapa)
    assert [c.caso_id for c in otra_vez] == ["RES-001", "RES-002"]
    assert nuevos2 == []
    assert mapa2 == mapa


def test_f045_r8_el_codigo_con_otra_puntuacion_es_el_mismo_albaran():
    mapa, _ = reparto.asignar_casos_id(
        reparto.agrupar_por_albaran([fila(2, "2.115.714", tipo="FERRETERIA")], VOCAB), {}
    )
    casos = reparto.agrupar_por_albaran([fila(2, "2115714", tipo="FERRETERIA")], VOCAB)
    reparto.asignar_casos_id(casos, mapa)
    assert casos[0].caso_id == "FER-001"


# --- El mapa versionado (R7) -----------------------------------------------


def test_f045_r7_el_mapa_versionado_trae_los_siete_casos_ya_sembrados():
    mapa = mapa_mod.cargar()
    assert set(mapa) >= {f"RES-00{n}" for n in range(1, 8)}
    # El código del humano NO es el literal impreso: 0000168, no SS-0000168.
    assert mapa["RES-001"]["codigo"] == "0000168"
    for caso_id, registro in mapa.items():
        assert set(registro) >= {"codigo", "clave", "nombre_original", "formato",
                                 "gemelo_de", "pestana"}, caso_id


def test_f045_r7_el_mapa_se_guarda_y_se_relee_igual(tmp_path):
    ruta = tmp_path / "mapa_casos.json"
    original = mapa_mod.cargar()
    mapa_mod.guardar(original, ruta)
    assert mapa_mod.cargar(ruta) == original
    # Determinista: mismo contenido, mismo byte.
    primera = ruta.read_bytes()
    mapa_mod.guardar(mapa_mod.cargar(ruta), ruta)
    assert ruta.read_bytes() == primera
    assert json.loads(ruta.read_text(encoding="utf-8"))["casos"]["RES-001"]


def test_f045_r7_el_mapa_no_admite_dos_casos_para_el_mismo_albaran():
    mapa = mapa_mod.cargar()
    claves = [registro["clave"] for registro in mapa.values()]
    assert len(claves) == len(set(claves))


def test_f045_r7_un_codigo_vacio_no_genera_caso():
    with pytest.raises(reparto.ErrorReparto):
        reparto.agrupar_por_albaran([fila(2, "   ")], VOCAB)
