# tests/test_f045_r5_r6_vocabulario.py
"""F-045 · R5 y R6: el vocabulario traduce, y lo que no reconoce ABORTA.

El valor de estos tests no es que la tabla de `design.md` §5 bis esté copiada
en un JSON: es que una etiqueta nueva —el humano escribe a mano en el Excel—
NO caiga en `generico` por descuido. Caer en `generico` sembraría ground truth
falso sin que nadie lo notara; abortar obliga a decidir.
"""

from __future__ import annotations

import pytest

from evals.revision import vocabulario as voc


@pytest.fixture(scope="module")
def vocab():
    return voc.cargar()


# --- R6: las diez etiquetas del Excel tienen destino ------------------------


@pytest.mark.parametrize(
    "etiqueta,familia,pestana",
    [
        ("HORMIGON", "hormigon", "Hormigon"),
        ("MORTERO", "mortero", "Mortero"),
        ("RESIDUOS", "residuos", "Residuos"),
        ("CONTENEDORES", "residuos", "Residuos"),
        ("GENERICO", "generico", "Generico-Suministros"),
        ("MATERIALES", "generico", "Generico-Suministros"),
        ("CAMION GRUA", "generico", "Alquiler"),
        ("GASOLEO", "combustible", "Combustible"),
        ("FERRETERIA", "ferreteria", "Ferreteria"),
        ("GRAVA", "grava", "Grava"),
    ],
)
def test_f045_r6_cada_etiqueta_tiene_familia_y_pestana(vocab, etiqueta, familia, pestana):
    destino = vocab.etiqueta(etiqueta, fila=2)
    assert destino.familia_documento == familia
    assert destino.pestana == pestana


def test_f045_r6_la_pestana_no_es_la_familia(vocab):
    """GASOLEO: pestaña Combustible, familia `combustible`, prefijo COM."""
    destino = vocab.etiqueta("gasoleo", fila=2)
    assert (destino.pestana, destino.familia_documento) == ("Combustible", "combustible")
    assert destino.prefijo == "COM"
    # CAMION GRUA es el caso inverso: familia generico, pestaña Alquiler.
    grua = vocab.etiqueta("CAMION GRUA", fila=3)
    assert (grua.pestana, grua.familia_documento) == ("Alquiler", "generico")
    assert grua.familia_linea == "alquiler_maquinaria"


def test_f045_r6_tres_familias_aun_no_estan_en_el_catalogo(vocab):
    """Nacen ROJAS a propósito: el catálogo lo amplía F-046, no F-045."""
    pendientes = {
        etiqueta
        for etiqueta in ("GASOLEO", "GRAVA", "FERRETERIA")
        if not vocab.etiqueta(etiqueta, fila=2).en_catalogo
    }
    assert pendientes == {"GASOLEO", "GRAVA", "FERRETERIA"}
    for etiqueta in ("HORMIGON", "MORTERO", "RESIDUOS", "GENERICO", "MATERIALES"):
        assert vocab.etiqueta(etiqueta, fila=2).en_catalogo


def test_f045_r6_el_catalogo_declarado_es_el_de_ruesma_comun(vocab):
    """Si esto se pone rojo es que el catálogo creció (F-046): actualiza el JSON."""
    familias = pytest.importorskip(
        "ruesma_comun.contratos.familias",
        reason="ruesma_comun no instalado en este intérprete",
    )
    assert set(vocab.familias_vigentes) == set(familias.familias_documento())


# --- R5: lo que no se reconoce aborta, y dice la fila -----------------------


def test_f045_r5_etiqueta_desconocida_aborta_y_no_cae_en_generico(vocab):
    with pytest.raises(voc.ErrorVocabulario) as fallo:
        vocab.etiqueta("PINTURA", fila=47)
    assert "PINTURA" in str(fallo.value)
    assert "47" in str(fallo.value)


def test_f045_r5_los_sinonimos_con_ruido_se_reconocen(vocab):
    assert vocab.origen_precio("DE CONTRATO", fila=2).precio_source == "contrato_db"
    assert vocab.origen_precio("CONTRATO", fila=2).precio_source == "contrato_db"
    assert vocab.origen_precio("EN OFERTA", fila=2).precio_source == "oferta"
    assert vocab.origen_precio("OFERTTA", fila=2).precio_source == "oferta"


def test_f045_r5_solo_albaran_a_secas_viene_impreso(vocab):
    """«ALBARAN VALORADO» es un importe calculado, no un importe impreso."""
    assert vocab.origen_precio("ALBARAN", fila=2).impreso is True
    assert vocab.origen_precio("ALBARAN VALORADO", fila=2).impreso is False
    assert vocab.origen_precio("ALBARAN VALORADO", fila=2).precio_source == "albaran"


def test_f045_r5_origen_de_linea_admite_la_cola_que_escribe_el_humano(vocab):
    assert vocab.origen_linea("EN ALBARAN", fila=2) == "impresa"
    assert vocab.origen_linea("EN ALBARAN 189502", fila=2) == "impresa"
    assert vocab.origen_linea('EN ALBARAN PERO DEDUCE AUMENTO POR "JIB"', fila=2) == "impresa"
    assert vocab.origen_linea("DEDUCIDO. INCREM. CAMBIO AÑO", fila=2) == "deducida"
    assert vocab.origen_linea("DEDUCIDA INCREMENTO PRECIO AÑO 2026", fila=2) == "deducida"


def test_f045_r5_origen_de_contrato(vocab):
    assert vocab.origen_contrato("EN CONTRATO", fila=2) == "contrato"
    assert vocab.origen_contrato('CONTRATO "PAPEL"', fila=2) == "contrato"
    assert vocab.origen_contrato("NUEVA", fila=2) == "nueva"
    assert vocab.origen_contrato("OFERTA", fila=2) == "oferta"


def test_f045_r5_origen_de_linea_desconocido_aborta(vocab):
    with pytest.raises(voc.ErrorVocabulario):
        vocab.origen_linea("QUIZAS", fila=9)


# --- R12: la política de vacíos vive en el mismo fichero de datos -----------


def test_f045_r12_cada_columna_declara_que_significa_su_vacio(vocab):
    assert vocab.politica_vacio("descuento") == "nulo"
    assert vocab.politica_vacio("ler") == "sin_fila"
    for columna in ("partida", "precio_unitario", "importe"):
        assert vocab.politica_vacio(columna) == "interrogante"


def test_f045_r12_no_queda_ninguna_columna_sin_politica(vocab):
    from evals.revision import modelos

    sin_declarar = [c for c in modelos.COLUMNAS if c not in vocab.politica_vacios]
    assert sin_declarar == []
