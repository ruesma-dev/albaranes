# tests/test_f011_r2_comparador.py
"""F-011 · R2 (aplicado) y R7/R8 — Comparación de lo esperado con lo obtenido.

Aquí se comprueba que los convenios del contrato de datos significan algo en
tiempo de comparación: `?` excluye el campo, `REVISIÓN` es un resultado
esperado legítimo, y la criticidad decide si una diferencia tumba el caso o
solo deja constancia.
"""

import pytest

from evals.comparador import campos_sin_clasificar, comparar
from evals.criticidad import cargar_criticidad
from evals.modelos import ESPERA_REVISION, NO_COMPARAR


@pytest.fixture(scope="module")
def criticidad():
    return cargar_criticidad()


def test_f011_r2_interrogacion_excluye_el_campo_aunque_difiera(criticidad):
    esperado = {"precio_unitario_final": NO_COMPARAR}

    assert comparar(esperado, {"precio_unitario_final": 99.9}, criticidad) == []


def test_f011_r2_revision_se_cumple_si_el_sistema_no_inventa(criticidad):
    esperado = {"partida_final": ESPERA_REVISION}

    assert comparar(esperado, {"partida_final": None}, criticidad) == []
    assert comparar(esperado, {"partida_final": "REVISIÓN"}, criticidad) == []
    assert comparar({"linea_a_revision": ESPERA_REVISION}, {"linea_a_revision": True}, criticidad) == []


def test_f011_r2_revision_falla_si_el_sistema_se_inventa_el_valor(criticidad):
    discrepancias = comparar(
        {"partida_final": ESPERA_REVISION}, {"partida_final": "01.02.03"}, criticidad
    )

    assert len(discrepancias) == 1
    assert discrepancias[0].severidad == "fallo"
    assert "revisión" in discrepancias[0].motivo.lower()


def test_f011_r2_null_esperado_y_valor_obtenido_es_discrepancia(criticidad):
    discrepancias = comparar(
        {"codigo_partida_final": None}, {"codigo_partida_final": "X"}, criticidad
    )

    assert [d.campo for d in discrepancias] == ["codigo_partida_final"]


def test_f011_r7_campo_critico_falla_y_campo_laxo_avisa(criticidad):
    discrepancias = comparar(
        {"codigo_partida_final": "01.02.03", "descripcion": "HA-25"},
        {"codigo_partida_final": "09.09.09", "descripcion": "hormigón 25"},
        criticidad,
    )

    severidades = {d.campo: d.severidad for d in discrepancias}
    assert severidades["codigo_partida_final"] == "fallo"
    assert severidades["descripcion"] == "aviso"


def test_f011_r2_los_numeros_se_comparan_como_numeros(criticidad):
    assert comparar({"cantidad": 8}, {"cantidad": 8.0}, criticidad) == []
    assert comparar({"importe_final": 580.0}, {"importe_final": 580.0000001}, criticidad) == []
    assert comparar({"importe_final": 580.0}, {"importe_final": 581.0}, criticidad) != []


def test_f011_r2_si_y_no_se_comparan_con_booleanos(criticidad):
    assert comparar({"review_required": "NO"}, {"review_required": False}, criticidad) == []
    assert comparar({"review_required": "SI"}, {"review_required": True}, criticidad) == []
    assert comparar({"review_required": "SI"}, {"review_required": False}, criticidad) != []


def test_f011_r2_el_texto_se_compara_sin_mayusculas_ni_espacios(criticidad):
    assert comparar({"unidad": "m3"}, {"unidad": " M3 "}, criticidad) == []


def test_f011_r2_las_listas_se_comparan_elemento_a_elemento(criticidad):
    assert comparar({"descuentos": ["10%", "5%"]}, {"descuentos": ["10%", "5%"]}, criticidad) == []

    discrepancias = comparar(
        {"descuentos": ["10%", "5%"]}, {"descuentos": ["10%"]}, criticidad
    )
    assert len(discrepancias) == 1


def test_f011_r2_un_campo_ausente_en_lo_obtenido_cuenta_como_null(criticidad):
    discrepancias = comparar({"importe_final": 100.0}, {}, criticidad)

    assert discrepancias[0].obtenido is None


def test_f011_r2_las_estructuras_anidadas_llevan_su_camino(criticidad):
    discrepancias = comparar(
        {"lineas": [{"precio_unitario_final": 10.0}]},
        {"lineas": [{"precio_unitario_final": 11.0}]},
        criticidad,
    )

    assert discrepancias[0].campo == "lineas[0].precio_unitario_final"
    assert discrepancias[0].severidad == "fallo"


def test_f011_r2_lo_que_sobra_en_lo_obtenido_no_se_compara(criticidad):
    """El ground truth manda: un campo que el libro no declara no se evalúa."""
    assert comparar({"cantidad": 1}, {"cantidad": 1, "campo_extra": "x"}, criticidad) == []


def test_f011_r8_los_campos_sin_clasificar_se_listan_para_el_informe(criticidad):
    sin_clasificar = campos_sin_clasificar(
        {"cantidad": 1, "invento_sin_declarar": "x"}, criticidad
    )

    assert sin_clasificar == ["invento_sin_declarar"]
