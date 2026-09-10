# tests/test_f036_r14_catalogo_ler_exhaustivo.py
"""F-036 R14 · el catalogo LER, capitulo a capitulo y subcapitulo a subcapitulo.

POR QUE EXISTE ESTE FICHERO
---------------------------
La campana de mutacion de F-043 (2026-09-10, `progress/mutacion_F-043.md`)
dejo 82 supervivientes en las lineas 51-70 de `ruesma_comun/ler.py`: TODO
el diccionario `_CAPITULOS_LER`. `test_f036_r14_ler.py` lo comprueba con
seis sondeos sueltos (170504, 170904, 200301, 010101 validos; 192137,
990101, 175004 invalidos), asi que cambiar el subcapitulo 3 del capitulo
01, o borrar el capitulo 09 entero, no rompia ningun test.

No son mutantes equivalentes: cada uno cambia lo que `es_ler_valido`
responde para codigos reales. Y `es_ler_valido` decide dinero — es la
guarda que impide que un codigo de producto de seis digitos ("192137",
el MORTERO de Prebetong) dispare la regla dura "LER -> residuos" y
enrute la fase 2 con el prompt equivocado.

EL METODO
---------
La tabla de abajo es una TRANSCRIPCION INDEPENDIENTE de la Decision
2014/955/UE, escrita aqui a proposito en vez de importar
`_CAPITULOS_LER`. Importarla convertiria el test en una tautologia: si
alguien se equivoca al teclear el catalogo, el test se equivocaria con
el. Dos copias que se comparan entre si es justo lo que se quiere para
un dato normativo que no lo decide este sistema.

El barrido cubre el rango 0-21 en capitulo Y subcapitulo, de modo que
tambien caza el desplazamiento de una CLAVE (un `19:` que pasa a `20:`
borra el capitulo 19, porque la clave 20 ya existe mas abajo y gana la
ultima).

Modulo puro: sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest
from ruesma_comun.ler import es_ler_valido, ler_creible

#: Decision 2014/955/UE: capitulo -> subcapitulos que EXISTEN.
#: Transcrito a mano; NO se importa de `ruesma_comun.ler` a proposito.
CATALOGO_NORMATIVO: dict[int, frozenset[int]] = {
    1: frozenset({1, 3, 4, 5}),
    2: frozenset({1, 2, 3, 4, 5, 6, 7}),
    3: frozenset({1, 2, 3}),
    4: frozenset({1, 2}),
    5: frozenset({1, 6, 7}),
    6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),
    7: frozenset({1, 2, 3, 4, 5, 6, 7}),
    8: frozenset({1, 2, 3, 4, 5}),
    9: frozenset({1}),
    10: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}),
    11: frozenset({1, 2, 3, 5}),
    12: frozenset({1, 3}),
    13: frozenset({1, 2, 3, 4, 5, 7, 8}),
    14: frozenset({6}),
    15: frozenset({1, 2}),
    16: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11}),
    17: frozenset({1, 2, 3, 4, 5, 6, 8, 9}),
    18: frozenset({1, 2}),
    19: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13}),
    20: frozenset({1, 2, 3}),
}

#: El barrido va mas alla del ultimo capitulo (20) y del subcapitulo mas
#: alto (14) para cazar tambien lo que se sale del catalogo.
RANGO = range(0, 22)


def _codigo(capitulo: int, subcapitulo: int) -> str:
    """Los seis digitos de un LER: capitulo, subcapitulo y residuo."""
    return f"{capitulo:02d}{subcapitulo:02d}01"


@pytest.mark.parametrize("capitulo", RANGO)
def test_f036_r14_el_capitulo_tiene_exactamente_sus_subcapitulos(capitulo):
    """Para CADA capitulo, el si y el no de cada subcapitulo del rango.

    Un solo `assert` por capitulo con el detalle de las discrepancias:
    asi el fallo dice que subcapitulos sobran o faltan, no solo el
    primero que se salio.
    """
    esperados = CATALOGO_NORMATIVO.get(capitulo, frozenset())

    sobran = [s for s in RANGO
              if s not in esperados and es_ler_valido(_codigo(capitulo, s))]
    faltan = [s for s in RANGO
              if s in esperados and not es_ler_valido(_codigo(capitulo, s))]

    assert (sobran, faltan) == ([], []), (
        f"capitulo {capitulo:02d}: se aceptan subcapitulos que no existen "
        f"en la Decision 2014/955/UE {sobran}; se rechazan subcapitulos "
        f"que si existen {faltan}."
    )


def test_f036_r14_el_catalogo_cubre_los_veinte_capitulos():
    """Ningun capitulo del 1 al 20 puede quedarse sin subcapitulos.

    Si una clave se desplaza (el `19:` que pasa a `20:`), el capitulo
    de origen desaparece entero. El test de arriba ya lo caza; este lo
    dice con el nombre para que el fallo se lea de un vistazo.
    """
    mudos = [
        c for c in range(1, 21)
        if not any(es_ler_valido(_codigo(c, s)) for s in RANGO)
    ]
    assert mudos == [], f"capitulos sin ningun subcapitulo valido: {mudos}"


# ------------------------------------------------------------------ #
# `ler_creible` — los dos huecos que la mutacion dejo al descubierto
# ------------------------------------------------------------------ #
def test_f036_r14_la_grafia_con_espacios_no_necesita_contexto():
    """"17 05 04" a secas basta: es la grafia canonica LER.

    Los tests que ya habia siempre traian ademas una palabra de
    contexto ("RCD 17 05 04"), asi que la rama del SEPARADOR nunca se
    ejercitaba sola: leer el grupo equivocado de la regex —los digitos
    en vez del separador— pasaba desapercibido.
    """
    assert ler_creible("17 05 04") == "170504"
    assert ler_creible("17 09 04 retirada") == "170904"


def test_f036_r14_seis_digitos_fuera_del_catalogo_no_son_ler_ni_con_contexto():
    """El bug de Prebetong, tambien sobre TEXTO LIBRE.

    `normalizar_ler("referencia 192137")` ya estaba cubierto, y
    `ler_creible("referencia 192137")` tambien — pero ese texto lo
    rechazaba la defensa de forma-fecha (ni espacios ni contexto de
    residuos), no la validacion contra el catalogo. Con contexto, o con
    la grafia de espacios, la unica guarda que queda es el catalogo:

        19 21 no existe (el capitulo 19 llega al subcapitulo 13).
    """
    assert ler_creible("residuo 192137") is None
    assert ler_creible("19 21 37") is None
    assert ler_creible("LER 19 21 37 contenedor") is None
