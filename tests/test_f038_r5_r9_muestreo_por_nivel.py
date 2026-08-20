# tests/test_f038_r5_r9_muestreo_por_nivel.py
"""F-038 · R5–R9: cuánto cuesta una campaña lo decide el nivel de rigor.

Una campaña completa sobre una feature grande evalúa decenas de mutantes y
obliga a analizar por escrito cada superviviente, que es lo caro. El tope y la
semilla dejan de ser algo que hay que acordarse de teclear y pasan a vivir en
`harness/rigor.json`, por nivel: `estandar` muestreado y reproducible,
`critico` sin tope.
"""

from __future__ import annotations

from harness.rigor import cargar_rigor, max_mutantes_nivel, semilla_nivel

RIGOR = {
    "nivel_por_defecto": "estandar",
    "niveles": {
        "documental": {"fase_red": False, "cobertura": False, "mutacion": False},
        "estandar": {
            "fase_red": True,
            "cobertura": True,
            "mutacion": True,
            "max_mutantes": 20,
            "semilla": 20260820,
        },
        "critico": {
            "fase_red": True,
            "cobertura": True,
            "mutacion": True,
            "max_mutantes": None,
            "semilla": None,
        },
    },
}


def test_f038_r5_el_nivel_estandar_declara_tope_y_semilla_en_rigor_json() -> None:
    assert max_mutantes_nivel("estandar", RIGOR) == 20
    assert semilla_nivel("estandar", RIGOR) == 20260820


def test_f038_r5_el_nivel_critico_no_tiene_tope_en_rigor_json() -> None:
    """`None` es «sin tope»: en `critico` se evalúa todo lo generado."""
    assert max_mutantes_nivel("critico", RIGOR) is None
    assert semilla_nivel("critico", RIGOR) is None


def test_f038_r5_un_nivel_sin_las_claves_de_rigor_no_revienta() -> None:
    """Las claves son OPCIONALES: un `rigor.json` viejo sigue funcionando."""
    assert max_mutantes_nivel("documental", RIGOR) is None
    assert semilla_nivel("documental", RIGOR) is None


def test_f038_r5_un_nivel_que_no_existe_en_rigor_json_no_impone_tope() -> None:
    assert max_mutantes_nivel("inventado", RIGOR) is None
    assert semilla_nivel("inventado", RIGOR) is None


def test_f038_r5_un_tope_absurdo_del_rigor_json_se_trata_como_ausencia() -> None:
    """Misma doctrina que `workers_mutacion`: mejor el defecto que una campaña rara."""
    malos = {
        "niveles": {
            "cero": {"max_mutantes": 0},
            "negativo": {"max_mutantes": -3},
            "booleano": {"max_mutantes": True},
            "texto": {"max_mutantes": "20"},
        }
    }
    for nivel in malos["niveles"]:
        assert max_mutantes_nivel(nivel, malos) is None, nivel


def test_f038_r5_una_semilla_de_rigor_no_entera_se_trata_como_ausencia() -> None:
    malos = {"niveles": {"booleana": {"semilla": True}, "texto": {"semilla": "x"}}}
    for nivel in malos["niveles"]:
        assert semilla_nivel(nivel, malos) is None, nivel


def test_f038_r5_la_semilla_cero_es_una_semilla_valida_en_rigor_json() -> None:
    """A diferencia del tope, `0` no significa nada especial en una semilla."""
    assert semilla_nivel("cero", {"niveles": {"cero": {"semilla": 0}}}) == 0


def test_f038_r5_el_rigor_json_del_repositorio_declara_el_tope_de_estandar() -> None:
    """El tope y la semilla viven en el fichero, no cableados en el código."""
    rigor = cargar_rigor()

    assert max_mutantes_nivel("estandar", rigor) == 20
    assert semilla_nivel("estandar", rigor) == 20260820, "semilla fija: reproducible"
    assert max_mutantes_nivel("critico", rigor) is None, "critico se mide entero"


def test_f038_r8_el_nivel_por_defecto_del_rigor_json_es_estandar() -> None:
    """R8: quien no declara `rigor` ya no arrastra el nivel más caro."""
    assert cargar_rigor()["nivel_por_defecto"] == "estandar"
