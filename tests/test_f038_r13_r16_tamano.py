# tests/test_f038_r13_r16_tamano.py
"""F-038 · R13–R16: los topes de tamaño del papeleo.

Cada línea de spec se paga tres veces: la escribe el spec-author, la lee el
implementer y la relee el reviewer. El arnés no decía nada del tamaño y por eso
los agentes escribían cuanto se les ocurría. Los topes viven en
`harness/rigor.json` —nunca cableados en el código— y los mide
`python -m harness.tamano`.
"""

from __future__ import annotations

from harness.rigor import topes_tamano

CLAVES = ("requirements", "design", "impl", "review")


def test_f038_r13_los_topes_viven_en_el_rigor_json_y_no_en_el_codigo() -> None:
    rigor = {"tamano": {"requirements": 120, "design": 200, "impl": 150, "review": 100}}

    assert topes_tamano(rigor) == {
        "requirements": 120,
        "design": 200,
        "impl": 150,
        "review": 100,
    }


def test_f038_r13_un_rigor_json_sin_bloque_tamano_no_declara_topes() -> None:
    """Sin bloque, la puerta se declara N/A: un arnés viejo no se rompe."""
    assert topes_tamano({"niveles": {}}) == {}


def test_f038_r13_el_doc_del_bloque_de_rigor_no_es_un_tope() -> None:
    """`$doc` es documentación del propio JSON, como en el resto del fichero."""
    assert topes_tamano({"tamano": {"$doc": "explicación", "impl": 150}}) == {"impl": 150}


def test_f038_r13_un_tope_absurdo_del_rigor_json_se_descarta() -> None:
    rigor = {"tamano": {"impl": 0, "review": -1, "design": True, "requirements": "120"}}

    assert topes_tamano(rigor) == {}
