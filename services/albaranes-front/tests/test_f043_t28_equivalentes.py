# tests/test_f043_t28_equivalentes.py
"""T28 · las guardas que sostienen los cinco equivalentes de sv4.

La campana de mutacion de F-043 dejo cinco supervivientes en sv4 que NO
son huecos de test: son mutantes EQUIVALENTES. Ninguno de estos tests los
mata —por definicion, ningun test puede— y no se han escrito para eso.
Lo que guardan es el INVARIANTE del que depende cada justificacion, para
que el dia que ese invariante caiga no lo haga en silencio.

Los tres de `review_models.py`
------------------------------

    #94  numeros_iguales:31        `a is None or b is None`  -> `and`
    #95  conversion_reproducible:78 `f is None or ca is None or cc is None`
                                     -> `f is None and ca is None or cc is None`
    #96  idem                        -> `f is None or ca is None and cc is None`

Las tres mutaciones abren la guarda de None y dejan pasar un None al
cuerpo de la funcion. Da igual: el cuerpo lo vuelve a atrapar. En
`numeros_iguales`, `float(None)` lanza `TypeError` y el `except
(TypeError, ValueError)` devuelve `False`, que es lo mismo que devolvia
la guarda. En `conversion_reproducible` pasa dos veces: el `try` del
producto atrapa el None de `factor` o de `cantidad_albaran`, y un
`cantidad_convertida` a None cae en la guarda de None de
`numeros_iguales`, que ya devuelve `False`. Comprobado por enumeracion
exhaustiva del espacio que estas funciones distinguen —None, numeros,
numerico-como-texto y basura no convertible—: 81 pares y 2 x 729
ternas, CERO discrepancias entre original y mutante.

El invariante, entonces, es el doble cinturon: la guarda de None no es
la unica defensa, y por eso quitarla no cambia el resultado. Si manana
alguien retira el `try/except` —o lo estrecha a un solo tipo de
excepcion— las tres mutaciones dejan de ser equivalentes y pasan a ser
huecos reales. Los tests de aqui abajo pasan a rojo antes de eso.

Los dos de `review_repository.py`
---------------------------------

    #98   3384  `json.dumps(vigentes, ensure_ascii=False)` -> `True`
    #100  3440  `json.dumps(razones,  ensure_ascii=False)` -> `True`

`ensure_ascii` solo decide si un caracter no ASCII se escribe tal cual o
escapado como `\\uXXXX`. Las dos serializaciones son JSON valido y
parsean al MISMO valor, y todo consumidor de `review_reasons_json` entra
por `json.loads`/`motivos_de_json`. El invariante es ese: la columna se
LEE parseada, nunca comparada como texto.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import json

import pytest
from domain.models.review_models import (
    conversion_reproducible,
    motivos_de_json,
    numeros_iguales,
)

#: Lo que `float()` rechaza. Es el segundo cinturon lo que se mide: sin
#: el `except`, estas entradas reventarian la ficha del revisor.
NO_CONVERTIBLES = ["no-numero", "", object(), [1.0], {"a": 1}]


# ------------------------------------------------------------------ #
# #94 · `numeros_iguales` no depende solo de su guarda de None
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("otro", [0.0, 1.0, -2.5, "7.5"])
def test_t28_numeros_iguales_devuelve_false_con_un_solo_none(otro):
    """El caso que la mutacion #94 deja pasar al cuerpo.

    La guarda `a is None or b is None` y el `except TypeError` del
    cuerpo dan la MISMA respuesta. Mientras las dos esten, la mutacion
    no puede cambiar nada.
    """
    assert numeros_iguales(None, otro) is False
    assert numeros_iguales(otro, None) is False


@pytest.mark.parametrize("basura", NO_CONVERTIBLES)
def test_t28_numeros_iguales_atrapa_lo_que_no_es_numero(basura):
    """El segundo cinturon existe y esta armado: no propaga la excepcion."""
    assert numeros_iguales(basura, 1.0) is False
    assert numeros_iguales(1.0, basura) is False


def test_t28_numeros_iguales_con_los_dos_none_es_true():
    """La primera rama sigue siendo la que decide el caso `None == None`.

    Es lo que deja MUERTA a la segunda guarda para ese caso, y parte de
    por que la mutacion #94 no se nota.
    """
    assert numeros_iguales(None, None) is True


# ------------------------------------------------------------------ #
# #95 y #96 · `conversion_reproducible` tampoco depende solo de la guarda
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("factor", "cantidad_albaran", "cantidad_convertida"),
    [
        (None, 6.0, 1.0),
        (5.0, None, 30.0),
        (5.0, 6.0, None),
        (None, None, 30.0),
        (None, 6.0, None),
        (5.0, None, None),
        (None, None, None),
    ],
)
def test_t28_conversion_no_reproducible_si_falta_cualquiera_de_los_tres(
    factor, cantidad_albaran, cantidad_convertida
):
    """Las siete combinaciones con algun None dan False por DOS caminos.

    Por la guarda de None, y —si la guarda no las atrapa— por el `try`
    del producto o por la guarda de None de `numeros_iguales`. Esa
    redundancia es lo que hace equivalentes a #95 y #96.
    """
    assert (
        conversion_reproducible(
            factor=factor,
            cantidad_albaran=cantidad_albaran,
            cantidad_convertida=cantidad_convertida,
        )
        is False
    )


@pytest.mark.parametrize("basura", NO_CONVERTIBLES)
def test_t28_conversion_no_reproducible_con_un_valor_que_no_es_numero(basura):
    """El `try` del producto tiene que seguir atrapandolo."""
    assert (
        conversion_reproducible(
            factor=basura, cantidad_albaran=6.0, cantidad_convertida=1.0
        )
        is False
    )
    assert (
        conversion_reproducible(
            factor=5.0, cantidad_albaran=basura, cantidad_convertida=1.0
        )
        is False
    )


def test_t28_la_conversion_que_si_se_reproduce_sigue_saliendo_true():
    """La rama util no se ha perdido por el camino."""
    assert (
        conversion_reproducible(
            factor=5.0, cantidad_albaran=6.0, cantidad_convertida=30.0
        )
        is True
    )


# ------------------------------------------------------------------ #
# #98 y #100 · `review_reasons_json` se lee PARSEADA, nunca como texto
# ------------------------------------------------------------------ #
#: Motivos con acentos y con enye: si `ensure_ascii` importara en algun
#: sitio, importaria aqui.
MOTIVOS_CON_ACENTOS = [
    "clasificacion_confianza_baja",
    "revisión manual del año anterior",
    "ñ: cantidad convertida no reproducible",
]


def test_t28_las_dos_serializaciones_de_motivos_se_leen_igual():
    """El invariante que hace equivalentes a #98 y #100.

    `ensure_ascii=False` y `ensure_ascii=True` escriben textos
    DISTINTOS, y aun asi `motivos_de_json` —la unica puerta de entrada
    de esa columna en sv4— devuelve exactamente la misma lista.
    """
    como_esta = json.dumps(MOTIVOS_CON_ACENTOS, ensure_ascii=False)
    escapado = json.dumps(MOTIVOS_CON_ACENTOS, ensure_ascii=True)

    # Que el caso sea REAL: si los dos textos coincidieran, este test no
    # estaria midiendo nada.
    assert como_esta != escapado

    assert motivos_de_json(como_esta) == MOTIVOS_CON_ACENTOS
    assert motivos_de_json(escapado) == MOTIVOS_CON_ACENTOS
    assert motivos_de_json(como_esta) == motivos_de_json(escapado)
