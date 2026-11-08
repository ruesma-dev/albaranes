# tests/test_f117_equivalentes_partida.py
"""F-117 · la partida equivalente en la obra, en comun (R1–R12).

``equivalentes_partida(lista, lectura, alm)`` PROPONE, para una lectura que
``resolver_partida_obra`` da ``fuera_de_lista``, las hojas equivalentes por dos
reglas cerradas (design §3):

- **letra** (R2, R3): la lectura no tiene ningún segmento con letra, la hoja sí,
  y cambiando cada ``03A`` de la hoja por ``3`` los segmentos son los mismos;
- **sufijo** (R4, R5): la lectura tiene 3 o más segmentos y la hoja termina,
  segmento a segmento, en ellos.

Casos de la medición del 2026-11-05 (design §2): ``CI.03.08`` de 0719,
``01.03A.02`` de 0694 (el falso positivo de la letra al revés), ``04.01.07`` de
0719, ``CD.02`` de 0692 (capítulo) y la ambigüedad A/P de 0459. Sin red ni BBDD.

Se accede al módulo por atributo (``P.equivalentes_partida``) para que, antes
de existir el código, cada test falle por separado (fase RED), no la colección.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import ruesma_comun
from ruesma_comun.sigrid import partidas as P

_COLUMNAS = ["ide", "padide", "cod", "res"]


def hojas(*cods: str, no_hojas: tuple[str, ...] = (), obra: str = "0719") -> P.ListaPartidasObra:
    """Lista con esas hojas (sin capítulos: el código completo es el cod)."""
    return P.ListaPartidasObra(
        obra=obra,
        hojas=tuple(P.PartidaObra(codigo=c, descripcion=f"desc {c}", descripcion_agregada=None) for c in cods),
        no_hojas=no_hojas,
    )


def eq(lista: P.ListaPartidasObra, lectura, alm: str | None = "ALM") -> tuple[str, ...]:
    return P.equivalentes_partida(lista, lectura, alm)


#: La 0719 reducida de R24: hojas con letra en el capítulo CI y otras sin ella.
LISTA_0719 = hojas("CI.03A.1", "CI.03A.8", "CI.03A.13", "CI.03P.9", "CI.1.8", "CI.2.8", "CI.4.8",
                   "02.04.01.07", "02.01.01.08")


# ------------------------------------------------------------------ #
# R1 · firma, tipo, orden y sin duplicados
# ------------------------------------------------------------------ #
def test_f117_r1_devuelve_una_tupla_de_cods():
    resultado = eq(LISTA_0719, "CI.03.08")
    assert isinstance(resultado, tuple)
    assert resultado == ("CI.03A.8",)


def test_f117_r1_en_el_orden_de_la_lista():
    lista = hojas("CI.03P.8", "CI.1.8", "CI.03A.8")
    assert eq(lista, "CI.03.08") == ("CI.03P.8", "CI.03A.8")
    lista_al_reves = hojas("CI.03A.8", "CI.03P.8")
    assert eq(lista_al_reves, "CI.03.08") == ("CI.03A.8", "CI.03P.8")


def test_f117_r1_sin_alm_tambien_funciona():
    assert eq(LISTA_0719, "CI.03.08", None) == ("CI.03A.8",)
    assert eq(LISTA_0719, "CI.03.08", "") == ("CI.03A.8",)


# ------------------------------------------------------------------ #
# R2 · regla de la letra (solo en la hoja)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("lectura", ["CI.03.08", "CI.3.8", "CI.03.008", "ci-03-08", " CI 03 08 "])
def test_f117_r2_letra_en_la_hoja(lectura):
    lista = hojas("CI.03A.8", "CI.1.8", "CI.2.8", "CI.4.8")
    assert eq(lista, lectura) == ("CI.03A.8",)


def test_f117_r2_cada_segmento_con_letra_pasa_a_su_numero():
    assert eq(hojas("01A.02B.3"), "1.2.3") == ("01A.02B.3",)
    assert eq(hojas("01A.02B.3"), "1.02B.3") == ()  # la lectura tiene letra: R3


def test_f117_r2_el_numero_sin_ceros_y_el_cero_es_cero():
    assert eq(hojas("CI.003A.8"), "CI.3.8") == ("CI.003A.8",)
    assert eq(hojas("CI.00A.8"), "CI.0.8") == ("CI.00A.8",)
    assert eq(hojas("CI.00A.8"), "CI.00.8") == ("CI.00A.8",)


def test_f117_r2_los_demas_segmentos_deben_coincidir():
    lista = hojas("CI.03A.9", "CD.03A.8", "CI.03A.8.1")
    assert eq(lista, "CI.03.08") == ()


def test_f117_r2_la_hoja_debe_tener_letra():
    # Sin letra en la hoja la regla de la letra no aplica (y la lectura no casa).
    assert eq(hojas("CI.3.9", "CI.4.8"), "CI.03.08") == ()


def test_f117_r2_por_el_codigo_completo_de_la_hoja():
    # CD › 03A.8: su código completo es CD.03A.8 y la lectura CD.03.08 casa con él.
    lista = P.ListaPartidasObra.desde_filas("0719", _COLUMNAS, [
        [1, 0, "CD", "COSTES DIRECTOS"],
        [2, 1, "03A.8", "CAMION GRUA"],
        [3, 1, "03P.9", "OTRA"],
    ])
    assert [h.codigo_completo for h in lista.hojas] == ["CD.03A.8", "CD.03P.9"]
    assert eq(lista, "CD.03.08") == ("03A.8",)


@pytest.mark.parametrize("segmento", ["03A", "12B", "3AB", "0A"])
def test_f117_r2_segmentos_con_letra(segmento):
    assert P.RE_SEGMENTO_CON_LETRA.match(segmento)


@pytest.mark.parametrize("segmento", ["P4", "PJ", "CD2", "03", "A3B", "03A1", "03a"])
def test_f117_r2_no_son_segmentos_con_letra(segmento):
    assert not P.RE_SEGMENTO_CON_LETRA.match(segmento)


def test_f117_r2_lectura_que_empieza_por_letra_no_es_segmento_con_letra():
    # P4 no es «segmento con letra»: la lectura P4.3.1 puede usar la regla.
    assert eq(hojas("P4.03A.1", "P4.4.1"), "P4.3.1") == ("P4.03A.1",)


# ------------------------------------------------------------------ #
# R3 · la letra no se aplica al revés (falso positivo de 0694)
# ------------------------------------------------------------------ #
def test_f117_r3_lectura_con_letra_no_va_a_hoja_sin_letra():
    lista = hojas("01.03.02", "01.04.02", obra="0694")
    assert eq(lista, "01.03A.02") == ()


def test_f117_r3_lectura_con_letra_no_va_a_otra_letra():
    assert eq(hojas("01.03B.02", "01.03.02"), "01.03A.02") == ()


# ------------------------------------------------------------------ #
# R4 · regla del sufijo (3 o más segmentos)
# ------------------------------------------------------------------ #
def test_f117_r4_sufijo_de_la_0719():
    assert eq(LISTA_0719, "04.01.07") == ("02.04.01.07",)
    assert eq(LISTA_0719, "4.1.7") == ("02.04.01.07",)


def test_f117_r4_sufijo_de_tres_exactos():
    assert eq(hojas("9.1.2.3", "1.2.4"), "1.2.3") == ("9.1.2.3",)
    assert eq(hojas("8.9.1.2.3"), "1.2.3") == ("8.9.1.2.3",)


def test_f117_r4_por_segmentos_no_por_caracteres():
    assert eq(hojas("2.4.01.07"), "14.01.07") == ()
    assert eq(hojas("2.14.01.07"), "4.01.07") == ()


def test_f117_r4_la_hoja_tiene_que_ser_mas_larga():
    # Una hoja más corta que termina igual no es un sufijo de la lectura.
    assert eq(hojas("1.7.3"), "9.1.7.3") == ()


def test_f117_r4_con_letra_en_la_lectura_tambien():
    assert eq(hojas("9.01.03A.2"), "01.03A.02") == ("9.01.03A.2",)


# ------------------------------------------------------------------ #
# R5 · sin sufijo con menos de 3 segmentos
# ------------------------------------------------------------------ #
def test_f117_r5_dos_segmentos_no_usan_el_sufijo():
    assert eq(hojas("02.01.07"), "01.07") == ()
    assert eq(hojas("1.7"), "7") == ()


def test_f117_r5_minimo_declarado():
    assert P.MIN_SEGMENTOS_SUFIJO == 3


# ------------------------------------------------------------------ #
# R6 · una sola vez por cod
# ------------------------------------------------------------------ #
def test_f117_r6_dos_reglas_o_dos_formas_de_la_misma_hoja_cuentan_una_vez():
    # El cod casa por la letra y el «completo» por el sufijo: una sola vez.
    hoja = P.PartidaObra("CI.03A.8", "grua", None, codigo_completo="X.CI.3.8")
    lista = P.ListaPartidasObra(obra="0719", hojas=(hoja,), no_hojas=())
    assert eq(lista, "CI.03.08") == ("CI.03A.8",)


def test_f117_r6_dos_hojas_con_el_mismo_cod_cuentan_un_cod():
    lista = P.ListaPartidasObra(obra="0719", no_hojas=(), hojas=(
        P.PartidaObra("CI.03A.8", "grua fase 1", None, capitulo="CI"),
        P.PartidaObra("CI.03A.8", "grua fase 2", None, capitulo="CI.F2"),
    ))
    assert eq(lista, "CI.03.08") == ("CI.03A.8",)


def test_f117_r6_ambigua_de_la_0459():
    lista = hojas(*(f"CI.03{letra}.{n}" for n in range(1, 13) for letra in "AP"), obra="0459")
    assert eq(lista, "CI.03.08") == ("CI.03A.8", "CI.03P.8")


# ------------------------------------------------------------------ #
# R7 · solo para lecturas fuera de lista, nunca compuestas
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    "lectura",
    [None, "", "   ", "ALM", " alm ", "CI.03A.8", "ci.03a.08", "CI.03A.8/CI.4.8", "CI.03.08/CI.03.18",
     "04.01.07 / 1.2"],
    ids=["none", "vacia", "blanca", "alm", "alm_minusculas", "exacta", "normalizada", "compuesta_que_casa",
         "compuesta_fuera", "compuesta_sufijo"],
)
def test_f117_r7_no_fuera_de_lista_o_compuesta(lectura):
    assert eq(LISTA_0719, lectura) == ()


def test_f117_r7_compuesta_aunque_una_hoja_la_contenga():
    # Una hoja (irreal) con «/» que terminaría en la lectura: la compuesta no se busca.
    lista = hojas("9.CI.03.08/CI.4.8")
    assert P.resolver_partida_obra(lista, "CI.03.08/CI.4.8", "ALM").motivo == "fuera_de_lista"
    assert eq(lista, "CI.03.08/CI.4.8") == ()


def test_f117_r7_completa_no_busca():
    # Sin la guarda, «X.CD.03A.8» terminaría en la lectura (sufijo).
    lista = P.ListaPartidasObra.desde_filas("0686", _COLUMNAS, [
        [1, 0, "CD", "COSTES DIRECTOS"],
        [2, 1, "03A.8", "CAMION GRUA"],
        [3, 1, "X.CD.03A.8", "OTRA"],
    ])
    assert P.resolver_partida_obra(lista, "CD.03A.8", "ALM").motivo == "normalizada"
    assert eq(lista, "CD.03A.8") == ()


def test_f117_r7_ambigua_no_busca():
    lista = hojas("CI.04.18", "CI.4.18", "CI.04A.18")
    assert P.resolver_partida_obra(lista, "ci-04-18", "ALM").motivo == "ambigua"
    assert eq(lista, "ci-04-18") == ()


def test_f117_r7_alm_configurable():
    lista = hojas("9.ACOPIO.1.2", "X.1.2.3")
    assert eq(lista, "acopio", "ACOPIO") == ()
    assert eq(lista, "ACOPIO.1.2", "ACOPIO.1.2") == ()
    assert eq(lista, "ACOPIO.1.2", "ALM") == ("9.ACOPIO.1.2",)


# ------------------------------------------------------------------ #
# R8 · una lectura que es un código NO hoja no se cambia por una hoja
# ------------------------------------------------------------------ #
def test_f117_r8_capitulo_cd02_de_la_0692():
    lista = P.ListaPartidasObra.desde_filas("0692", _COLUMNAS, [
        [1, 0, "CD", "COSTES DIRECTOS"],
        [2, 1, "02", "ESTRUCTURA"],
        [3, 2, "02.01", "Cimentación"],
        [4, 1, "CD.2A", "Hoja con letra que sin la guarda casaría"],
    ])
    assert "CD.02" in lista.no_hojas_completos
    assert eq(lista, "CD.02") == ()


def test_f117_r8_no_hoja_por_su_cod():
    lista = hojas("02.04.01.07", no_hojas=("04.01.07",))
    assert eq(lista, "04.01.07") == ()
    assert eq(hojas("02.04.01.07"), "04.01.07") == ("02.04.01.07",)


def test_f117_r8_no_hoja_con_letra():
    lista = hojas("CI.03A.8", no_hojas=("CI.3.8",))
    assert eq(lista, "CI.03.08") == ()


# ------------------------------------------------------------------ #
# R9 · ni distancia, ni prefijo, ni descripción
# ------------------------------------------------------------------ #
def test_f117_r9_ni_prefijo():
    assert eq(hojas("02.04.01.07"), "02.04.01") == ()
    assert eq(hojas("02.04"), "02.04.01.07") == ()


def test_f117_r9_ni_distancia():
    assert eq(hojas("CI.03A.9", "CI.3.9"), "CI.3.8") == ()
    assert eq(hojas("2.04.01.08"), "04.01.07") == ()


def test_f117_r9_ni_descripcion():
    lista = P.ListaPartidasObra(obra="x", no_hojas=(), hojas=(
        P.PartidaObra("CI.1.1", "CI.03.08", "CI.03.08"),
    ))
    assert eq(lista, "CI.03.08") == ()


def test_f117_r9_sin_hojas_no_hay_equivalentes():
    assert eq(hojas(), "CI.03.08") == ()


# ------------------------------------------------------------------ #
# R18 (comun) · nunca algo que no sea un cod de la lista
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("lectura", ["CI.03.08", "04.01.07", "CI.3.1", "CI.3.13", "CI.3.9", "1.8"])
def test_f117_r18_siempre_cods_de_la_lista(lectura):
    resultado = eq(LISTA_0719, lectura)
    assert set(resultado) <= set(LISTA_0719.codigos)
    assert len(resultado) == len(set(resultado))


# ------------------------------------------------------------------ #
# R10 · lo de F-049/F-076/F-098 no cambia
# ------------------------------------------------------------------ #
def test_f117_r10_resolver_y_casar_siguen_igual():
    assert P.resolver_partida_obra(LISTA_0719, "CI.03.08", "ALM") == P.ResolucionPartida(
        "CI.03.08", "fuera_de_lista", "CI.03.08")
    assert P.casar_partida(LISTA_0719, "04.01.07", "ALM") == P.CasePartida("fuera_de_lista")
    assert P.normalizar_partida("CI.03A.08") == "CI.03A.8"
    assert P.misma_partida(LISTA_0719, "CI.03.08", "CI.03A.8") is False
    assert P.mostrar_partida(LISTA_0719, "CI.03.08") == "CI.03.08"


# ------------------------------------------------------------------ #
# R11 · la docstring deja escrita la excepción a H1
# ------------------------------------------------------------------ #
def test_f117_r11_docstring_del_modulo():
    doc = P.__doc__ or ""
    assert "equivalentes_partida" in doc
    assert "F-117" in doc and "2026-11-05" in doc and "H1" in doc
    assert "letra" in doc and "sufijo" in doc
    assert "revisión" in doc


def test_f117_r11_docstring_de_la_funcion():
    doc = P.equivalentes_partida.__doc__ or ""
    assert "letra" in doc and "sufijo" in doc and "revisión" in doc


# ------------------------------------------------------------------ #
# R12 · versión 0.14.0 y exportada desde ruesma_comun.sigrid
# ------------------------------------------------------------------ #
def test_f117_r12_version_0140():
    assert ruesma_comun.__version__ == "0.14.0"
    pyproject = (Path(ruesma_comun.__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'version = "0.14.0"' in pyproject


def test_f117_r12_exportada():
    import ruesma_comun.sigrid as S

    assert S.equivalentes_partida is P.equivalentes_partida
    assert "equivalentes_partida" in S.__all__
