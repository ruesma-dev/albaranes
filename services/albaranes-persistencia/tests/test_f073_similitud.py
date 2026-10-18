# tests/test_f073_similitud.py
"""F-073 · R2–R8 — el criterio único de nombre de proveedor.

``similitud_razon_social`` (application/services/similitud_proveedor.py)
compara el nombre LEÍDO con una razón social: puntuación como separador,
fuera formas jurídicas, palabras vacías y palabras de un carácter; 1 si el
texto de palabras de uno contiene al del otro; si no, el máximo de las dos
direcciones (fracción de palabras que casan por subcadena, por una letra
de diferencia en palabras de 5+ caracteres o, con 2, por igualdad).
Sin red ni BBDD.
"""
from __future__ import annotations

import itertools

import pytest

from application.services.similitud_proveedor import (
    FORMAS_JURIDICAS,
    PALABRAS_VACIAS,
    distancia_edicion,
    palabras_razon_social,
    similitud_razon_social,
)

RAZ_FEYMACO = "FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)"
RAZ_HIERROS = "HIERROS RODRIGO, S.A."


# ------------------------------------------------------------------ #
# R2 · palabras de un nombre
# ------------------------------------------------------------------ #
def test_f073_r2_listas_cerradas():
    assert FORMAS_JURIDICAS == frozenset(
        "sa sl slu sau sll slne slp scoop coop sc scp scl sccl cb srl sad aie "
        "ute sociedad anonima limitada unipersonal laboral cooperativa".split()
    )
    assert PALABRAS_VACIAS == frozenset(
        "de del la las el los y e en para por con a al".split()
    )


@pytest.mark.parametrize(
    ("texto", "palabras"),
    [
        (RAZ_FEYMACO, ("ferreteria", "maquinaria", "construccion", "feymaco")),
        ("FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.",
         ("ferreteria", "maquinaria", "construccion")),
        ("FEYMACO, S.A.", ("feymaco",)),
        ("Hormigones  Mat SL", ("hormigones", "mat")),
        ("PROVEEDOR OBRA 07", ("proveedor", "obra", "07")),
        ("A&B+C*D_E", ()),
        ("Grúas-Ángel/Martín\\Hijos\"Sur'Norte", ("gruas", "angel", "martin", "hijos", "sur", "norte")),
        ("X;Y:Z[W]{V}", ()),
        ("TALLERES [ESTE] {OESTE};NORTE:SUR", ("talleres", "este", "oeste", "norte", "sur")),
        ("ALFA&BETA+GAMMA*DELTA_EPSILON", ("alfa", "beta", "gamma", "delta", "epsilon")),
    ],
    ids=["feymaco-real", "feymaco-leido", "feymaco-corto", "mat", "numero",
         "solo-letras-sueltas", "acentos-y-signos", "corchetes-sueltos",
         "corchetes-llaves", "and-mas-por-guion-bajo"],
)
def test_f073_r2_palabras(texto, palabras):
    assert palabras_razon_social(texto) == palabras


@pytest.mark.parametrize(
    "forma",
    ["S.A.", "S. A.", "SA", "S.L.U.", "S.COOP.", "SOCIEDAD ANONIMA", "S.L.", "SOCIEDAD LIMITADA LABORAL",
     "SCCL", "C.B.", "U.T.E.", "UTE", "A.I.E.", "S.A.D.", "S.R.L.", "COOPERATIVA", "UNIPERSONAL",
     "SLNE", "SLP", "SCP", "SCL", "SC", "SAU", "SLL"],
)
def test_f073_r2_r3_una_forma_juridica_sola_no_deja_palabras_y_no_casa(forma):
    """P0 (humano, 2026-10-15): una forma jurídica sola no casa con nadie."""
    assert palabras_razon_social(forma) == ()
    assert similitud_razon_social(forma, "ARIDOS ANFERSA, S.L.") == 0.0
    assert similitud_razon_social("ARIDOS ANFERSA, S.L.", forma) == 0.0


@pytest.mark.parametrize("vacia", sorted("de del la las el los y e en para por con a al".split()))
def test_f073_r2_cada_palabra_vacia_se_quita(vacia):
    assert palabras_razon_social(f"ALFA {vacia.upper()} BETA") == ("alfa", "beta")


@pytest.mark.parametrize("forma", sorted(
    "sa sl slu sau sll slne slp scoop coop sc scp scl sccl cb srl sad aie "
    "ute sociedad anonima limitada unipersonal laboral cooperativa".split()
))
def test_f073_r2_cada_forma_juridica_se_quita(forma):
    assert palabras_razon_social(f"ALFA {forma.upper()} BETA") == ("alfa", "beta")


# ------------------------------------------------------------------ #
# R3 · sin palabras ⇒ 0
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("vacio", [None, "", "   ", "S.A.", "Y DE LA", "a b c", ",.;"])
def test_f073_r3_sin_palabras_la_similitud_es_cero(vacio):
    assert similitud_razon_social(vacio, RAZ_FEYMACO) == 0.0
    assert similitud_razon_social(RAZ_FEYMACO, vacio) == 0.0
    assert similitud_razon_social(vacio, vacio) == 0.0


# ------------------------------------------------------------------ #
# R4 · contención ⇒ 1
# ------------------------------------------------------------------ #
def test_f073_r4_contencion_es_uno():
    assert similitud_razon_social("Transportes", "TRANSPORTES PEREZ GARCIA, S.L.") == 1.0
    assert similitud_razon_social("TRANSPORTES PEREZ GARCIA, S.L.", "Transportes") == 1.0
    # El texto de palabras, no las palabras sueltas: «mat» dentro de «materiales».
    assert similitud_razon_social("Hormigones Mat SL", "HORMIGONES MATERIALES, S.A.") == 1.0


# ------------------------------------------------------------------ #
# R5 · direcciones y qué palabra casa
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("leido", "candidato", "esperado"),
    [
        # ≥ 3 caracteres como subcadena del texto del otro.
        ("ZZZ CAN", "CANTERAS ROJAS", 0.5),
        # 2 caracteres: solo igual a una palabra; como subcadena NO.
        ("ZZZ CA", "CANTERAS ROJAS", 0.0),
        ("ZZZ ZQ", "ZQ ROJAS", 0.5),
        # una edición con 5+ caracteres en las dos palabras (sin ser subcadena).
        ("TEYMACO QQQQ", "FEYMACO PEREZ", 0.5),
        ("FEYXMACO QQQQ", "FEYMACO PEREZ", 0.5),
        ("FEMACO QQQQ", "FEYMACO PEREZ", 0.5),
        ("PALXOS ZZZZ", "PALOS PEREZ", 0.5),
        # 4 caracteres en alguna de las dos: no se aproxima.
        ("TEYM QQQQ", "FEYM PEREZ", 0.0),
        ("PALXO ZZZZ", "PALO PEREZ", 0.0),
        ("PALO ZZZZ", "PALXO PEREZ", 0.0),
        # dos ediciones: no casa.
        ("TEYMACA QQQQ", "FEYMACO PEREZ", 0.0),
    ],
    ids=["subcadena-3", "dos-letras-no-subcadena", "dos-letras-igual", "sustitucion",
         "insercion", "borrado", "cinco-y-cinco", "cuatro-y-cuatro", "candidato-con-cuatro",
         "leido-con-cuatro", "dos-ediciones"],
)
def test_f073_r5_que_palabra_casa(leido, candidato, esperado):
    assert similitud_razon_social(leido, candidato) == esperado


def test_f073_r5_maximo_de_las_dos_direcciones():
    # A→B: 1/4 (solo «alfa»); B→A: 1/2. Manda la dirección más alta.
    assert similitud_razon_social("ALFA BETA GAMMA DELTA", "ALFA OMEGA") == 0.5
    assert similitud_razon_social("ALFA OMEGA", "ALFA BETA GAMMA DELTA") == 0.5


# ------------------------------------------------------------------ #
# R6 · casos de referencia, valores exactos
# ------------------------------------------------------------------ #
CASOS_R6 = [
    pytest.param("FEYMACO, S.A.", RAZ_FEYMACO, 1.0, id="feymaco"),
    pytest.param("TEYMACO, S.A.", RAZ_FEYMACO, 1.0, id="teymaco"),
    pytest.param("FEYMACO, S.A.", RAZ_HIERROS, 0.0, id="feymaco-hierros"),
    pytest.param("TEYMACO, S.A.", RAZ_HIERROS, 0.0, id="teymaco-hierros"),
    pytest.param("FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A.", RAZ_FEYMACO, 1.0, id="feymaco-largo"),
    pytest.param("GRUPO OTTO HORPRESOL", "HORPRESOL, S.L.", 1.0, id="horpresol"),
    pytest.param("HORMIGONES DEL EBRO", "EBRO CANTERAS", 0.5, id="ebro"),
    pytest.param("TRANSPORTES MACOTRAN NORTE", "MACOTRAN LOGISTICA GLOBAL", 1 / 3, id="macotran"),
    pytest.param("S.A.", RAZ_FEYMACO, 0.0, id="solo-sa"),
    pytest.param("Hormigones Mat SL", "HORMIGONES Y MATERIALES DEL NORTE, S.A.", 1.0, id="empate-f062"),
    pytest.param("PROVEEDOR OBRA 07", "PROVEEDOR OBRA 00, S.L.", 2 / 3, id="obra-00"),
    pytest.param("PROVEEDOR OBRA 07", "PROVEEDOR OBRA 07, S.L.", 1.0, id="obra-07"),
    pytest.param("HORMIGONES 2000", "HORMIGONES 2001 SL", 0.5, id="numeros"),
]


@pytest.mark.parametrize(("leido", "candidato", "esperado"), CASOS_R6)
def test_f073_r6_casos_de_referencia(leido, candidato, esperado):
    assert similitud_razon_social(leido, candidato) == pytest.approx(esperado, abs=1e-12)


# ------------------------------------------------------------------ #
# R7 · simétrica en todo par
# ------------------------------------------------------------------ #
_NOMBRES = sorted({
    *(p.values[0] for p in CASOS_R6), *(p.values[1] for p in CASOS_R6),
    "Transportes", "TRANSPORTES PEREZ GARCIA, S.L.", "ZZZ CAN", "CANTERAS ROJAS", "ZQ ROJAS",
    "TEYMACO QQQQ", "FEYMACO PEREZ", "RUEDA PEREZ", "RUEDAS QQQQ", "ALFA BETA GAMMA DELTA",
    "ALFA OMEGA", "ARIDOS ANFERSA SL", "ARIDOS DEL SUR, S.L.", "", None,
}, key=lambda s: s or "")


@pytest.mark.parametrize(("a", "b"), list(itertools.combinations(_NOMBRES, 2)))
def test_f073_r7_simetrica(a, b):
    assert similitud_razon_social(a, b) == similitud_razon_social(b, a)


# ------------------------------------------------------------------ #
# R8 · una sola distancia de edición, la de F-062
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("a", "b", "distancia"),
    [
        ("", "", 0), ("", "ABC", 3), ("ABC", "ABC", 0), ("B86056201", "B66056201", 1),
        ("KITTEN", "SITTING", 3), ("ABCD", "ACBD", 2),
        ("feymaco", "teymaco", 1), ("feymaco", "feymacos", 1), ("feymaco", "eymaco", 1),
    ],
)
def test_f073_r8_distancia_edicion(a, b, distancia):
    assert distancia_edicion(a, b) == distancia
    assert distancia_edicion(b, a) == distancia
