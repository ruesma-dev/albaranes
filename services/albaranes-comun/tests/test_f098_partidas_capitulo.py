# tests/test_f098_partidas_capitulo.py
"""F-098 · partidas por capítulo y con su código completo, en comun (R1–R13).

Los árboles son los medidos en T0 (``progress/explore_F-098_T0.md``), recortados
a lo que prueba cada requisito (design §3.1): filas ``(ide, padide, cod, res)``
escritas a mano, sin red ni BBDD. Los cod son los de Sigrid.

- **cod**: ``obrparpar.cod`` tal cual (lo que se guarda y se manda).
- **capítulo**: la raíz de la cadena de la hoja (R2).
- **código completo**: el que ve el humano (R3): ``CD.99.01.64`` para el cod
  ``99.01.64`` de CD.

Se accede al módulo por atributo (``P.codigo_completo``) para que, antes de
existir el código, cada test falle por separado (fase RED), no la colección.
"""
from __future__ import annotations

import pytest
from ruesma_comun.sigrid import partidas as P

_COLUMNAS = ["ide", "padide", "cod", "res"]

# ------------------------------------------------------------------ #
# Árboles de T0 (design §3.1)
# ------------------------------------------------------------------ #
# 0686: ANT. › 98.01, 98.02; CD › 99 › 99.01 › 99.01.64; CD › 21 › 21.02 ›
# 21.02.21; CI › CI.4.18; CP (padre nulo) › CP.1.1.
FILAS_0686 = [
    [1, 0, "ANT.", "AJUSTES ALMACÉN"],
    [2, 1, "98.01", "Anticipos"],
    [3, 1, "98.02", "Anulación de imputaciones"],
    [10, 0, "CD", "COSTES DIRECTOS"],
    [11, 10, "99", "VARIOS"],
    [12, 11, "99.01", "VARIOS OBRA"],
    [13, 12, "99.01.64", "Material de obra"],
    [15, 10, "21", "ACABADOS"],
    [16, 15, "21.02", "ALICATADOS"],
    [14, 16, "21.02.21", "Alicatado cocina"],
    [20, 0, "CI", "COSTES INDIRECTOS"],
    [21, 20, "CI.4.18", "Costes indirectos de obra"],
    [30, None, "CP", "COSTES PROPORCIONALES"],
    [31, 30, "CP.1.1", "Proporcional"],
]

# 0692: CD › CD1 › 01.01; CD › CD2 › CD2.01; CI › CI.1.1, CI.6.1;
# CI.F2 › CI.01.01, CI.6.1; CP › CP.1.1.
FILAS_0692 = [
    [1, 0, "CD", "COSTES DIRECTOS"],
    [2, 1, "CD1", "DEMOLICIONES"],
    [3, 2, "01.01", "Demolición"],
    [4, 1, "CD2", "FASE 2"],
    [5, 4, "CD2.01", "Fase 2 uno"],
    [6, 0, "CI", "COSTES INDIRECTOS"],
    [7, 6, "CI.1.1", "Personal"],
    [8, 6, "CI.6.1", "Varios CI"],
    [9, 0, "CI.F2", "COSTES INDIRECTOS FASE 2"],
    [10, 9, "CI.01.01", "Personal fase 2"],
    [11, 9, "CI.6.1", "Varios fase 2"],
    [12, 0, "CP", "COSTES PROPORCIONALES"],
    [13, 12, "CP.1.1", "Proporcional"],
]

# 0693: CD › 37 › 37.01, 37-.01; CI_F1 › CI_F1.01.01; CI_F2 › CI_F2.01.01;
# CP › CP.1.1 (no hay CI).
FILAS_0693 = [
    [1, 0, "CD", "COSTES DIRECTOS"],
    [2, 1, "37", "PRECIOS NUEVOS"],
    [3, 2, "37.01", "Precio nuevo"],
    [4, 2, "37-.01", "Precio nuevo bis"],
    [5, 0, "CI_F1", "CI FASE 1"],
    [6, 5, "CI_F1.01.01", "Personal fase 1"],
    [7, 0, "CI_F2", "CI FASE 2"],
    [8, 7, "CI_F2.01.01", "Personal fase 2"],
    [9, 0, "CP", "COSTES PROPORCIONALES"],
    [10, 9, "CP.1.1", "Proporcional"],
]

# 0696: CD › P4 › P4.01 › P4.01.01; P4.08.05 dos veces bajo dos subcapítulos
# distintos de P4; P4.22 › P4.22.01.03.07; CD › P5 › P5.02.01.01; CI; CP.
FILAS_0696 = [
    [1, 0, "CD", "COSTES DIRECTOS"],
    [2, 1, "P4", "PARCELA 4"],
    [3, 2, "P4.01", "Movimiento de tierras"],
    [4, 3, "P4.01.01", "Excavación"],
    [5, 2, "P4.08", "Carpintería"],
    [6, 5, "P4.08.05", "Puerta a"],
    [7, 2, "P4.80", "Carpintería bis"],
    [8, 7, "P4.08.05", "Puerta b"],
    [9, 2, "P4.22", "Instalaciones"],
    [17, 9, "P4.22.01.03.07", "Tubería"],
    [11, 1, "P5", "PARCELA 5"],
    [12, 11, "P5.02.01.01", "Cimentación"],
    [13, 0, "CI", "COSTES INDIRECTOS"],
    [14, 13, "CI.1.1", "Personal"],
    [15, 0, "CP", "COSTES PROPORCIONALES"],
    [16, 15, "CP.1.1", "Proporcional"],
]

# 0711: CD1 › CD2.
FILAS_0711 = [
    [1, 0, "CD1", "ANTICIPOS"],
    [2, 1, "CD2", "Anticipo"],
]


def lista_de(obra: str, filas) -> P.ListaPartidasObra:
    return P.ListaPartidasObra.desde_filas(obra, _COLUMNAS, filas)


def hoja(lista: P.ListaPartidasObra, cod: str, descripcion: str | None = None) -> P.PartidaObra:
    (encontrada,) = [
        h for h in lista.hojas if h.codigo == cod and (descripcion is None or h.descripcion == descripcion)
    ]
    return encontrada


# ------------------------------------------------------------------ #
# R1 · cada hoja lleva ide, capítulo, su descripción y el código completo
# ------------------------------------------------------------------ #
def test_f098_r1_hoja_lleva_ide_capitulo_y_completo():
    h = hoja(lista_de("0686", FILAS_0686), "99.01.64")
    assert h.codigo == "99.01.64"
    assert h.descripcion == "Material de obra"
    assert h.descripcion_agregada == "COSTES DIRECTOS › VARIOS › VARIOS OBRA › Material de obra"
    assert h.ide == 13
    assert h.capitulo == "CD"
    assert h.capitulo_descripcion == "COSTES DIRECTOS"
    assert h.codigo_completo == "CD.99.01.64"


def test_f098_r1_campos_nuevos_al_final_y_con_defecto():
    """Quien construye la hoja con los tres campos de siempre no se rompe; sin
    capítulo, el código completo es el cod (R3 a)."""
    h = P.PartidaObra(codigo="CI.4.18", descripcion=None, descripcion_agregada=None)
    assert (h.ide, h.capitulo, h.capitulo_descripcion) == (None, None, None)
    assert h.codigo_completo == "CI.4.18"
    h2 = P.PartidaObra("X", "d", "a", 7, "CD", "COSTES", "CD.X")
    assert (h2.ide, h2.capitulo, h2.capitulo_descripcion, h2.codigo_completo) == (7, "CD", "COSTES", "CD.X")


def test_f098_r1_campos_nuevos_no_cambian_la_igualdad_de_f076():
    """R5: los tests de F-076 comparan hojas con los tres campos de siempre."""
    a = P.PartidaObra("99.01.64", "M", "R", 13, "CD", "COSTES DIRECTOS", "CD.99.01.64")
    b = P.PartidaObra("99.01.64", "M", "R")
    assert a == b
    assert hash(a) == hash(b)
    assert a != P.PartidaObra("99.01.65", "M", "R")


def test_f098_r1_hoja_inmutable():
    h = hoja(lista_de("0686", FILAS_0686), "99.01.64")
    with pytest.raises(AttributeError):
        h.codigo_completo = "otro"  # type: ignore[misc]


# ------------------------------------------------------------------ #
# R2 · capítulo = raíz de la cadena (sin bajar de nivel)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("filas", "cod", "capitulo", "descripcion"),
    [
        (FILAS_0686, "98.01", "ANT.", "AJUSTES ALMACÉN"),
        (FILAS_0686, "99.01.64", "CD", "COSTES DIRECTOS"),
        (FILAS_0686, "21.02.21", "CD", "COSTES DIRECTOS"),
        (FILAS_0686, "CI.4.18", "CI", "COSTES INDIRECTOS"),
        (FILAS_0686, "CP.1.1", "CP", "COSTES PROPORCIONALES"),  # padre nulo
        (FILAS_0692, "01.01", "CD", "COSTES DIRECTOS"),  # CD › CD1 › 01.01: CD, no CD1
        (FILAS_0692, "CD2.01", "CD", "COSTES DIRECTOS"),
        (FILAS_0692, "CI.01.01", "CI.F2", "COSTES INDIRECTOS FASE 2"),
        (FILAS_0693, "CI_F1.01.01", "CI_F1", "CI FASE 1"),
        (FILAS_0693, "CI_F2.01.01", "CI_F2", "CI FASE 2"),
        (FILAS_0696, "P4.01.01", "CD", "COSTES DIRECTOS"),
        (FILAS_0711, "CD2", "CD1", "ANTICIPOS"),
    ],
)
def test_f098_r2_capitulo_es_la_raiz(filas, cod, capitulo, descripcion):
    h = hoja(lista_de("0000", filas), cod)
    assert (h.capitulo, h.capitulo_descripcion) == (capitulo, descripcion)


def test_f098_r2_0693_sin_ci():
    capitulos = {h.capitulo for h in lista_de("0693", FILAS_0693).hojas}
    assert capitulos == {"CD", "CI_F1", "CI_F2", "CP"}


def test_f098_r2_hoja_raiz_es_su_propio_capitulo():
    lista = lista_de("0000", [[1, 0, "CD", "TOTAL PRESUPUESTO"], [2, None, "LEV", "Levantamiento"]])
    assert [(h.codigo, h.capitulo, h.capitulo_descripcion, h.codigo_completo) for h in lista.hojas] == [
        ("CD", "CD", "TOTAL PRESUPUESTO", "CD"),
        ("LEV", "LEV", "Levantamiento", "LEV"),
    ]


def test_f098_r2_padre_que_no_esta_entre_las_filas_es_raiz():
    lista = lista_de("0000", [[1, 99, "X", "Cap huérfano"], [2, 1, "X.1", "Hoja"]])
    h = hoja(lista, "X.1")
    assert (h.capitulo, h.codigo_completo) == ("X", "X.1")


def test_f098_r2_padide_cero_en_texto_es_sin_padre():
    lista = lista_de("0000", [[1, "0", "CD", "COSTES"], [2, 1, "01", "Hoja"]])
    assert hoja(lista, "01").capitulo == "CD"


def test_f098_r2_ciclo_para_en_el_ultimo_no_repetido():
    # A(1) › B(2) › A(1): la hoja C cuelga de A; la subida 3→1→2→(1 repetido).
    filas = [[1, 2, "A", "a"], [2, 1, "B", "b"], [3, 1, "C", "c"]]
    h = hoja(lista_de("0000", filas), "C")
    assert (h.capitulo, h.capitulo_descripcion, h.codigo_completo) == ("B", "b", "B.C")


def test_f098_r2_ciclo_sobre_si_mismo():
    filas = [[1, 1, "A", "a"], [2, 1, "A.1", "hoja"]]
    lista = lista_de("0000", filas)
    assert hoja(lista, "A.1").capitulo == "A"


def test_f098_r2_capitulo_sin_cod_es_none():
    filas = [[1, None, None, "Capítulo sin código"], [2, 1, "A.1", "Hoja a"]]
    h = hoja(lista_de("0000", filas), "A.1")
    assert (h.capitulo, h.capitulo_descripcion, h.codigo_completo) == (None, None, "A.1")


def test_f098_r2_ide_sale_de_la_fila():
    lista = lista_de("0696", FILAS_0696)
    assert sorted(h.ide for h in lista.hojas if h.codigo == "P4.08.05") == [6, 8]


# ------------------------------------------------------------------ #
# R3 · código completo (a) → (d)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("capitulo", "cod", "completo"),
    [
        # (a) sin capítulo
        (None, "99.01.64", "99.01.64"),
        # (b) el cod ya empieza por el capítulo seguido de límite
        ("CI", "CI.4.18", "CI.4.18"),
        ("CD", "CD2.01", "CD2.01"),  # letra ↔ dígito
        ("CI0", "CI0.01.01", "CI0.01.01"),
        ("CI_F1", "CI_F1.01.01", "CI_F1.01.01"),
        ("CD", "CD", "CD"),  # fin del cod
        ("CI", "ci.4.18", "ci.4.18"),  # se compara sin mayúsculas; se enseña tal cual
        ("ANT.", "ANT.98", "ANT.98"),  # el capítulo termina en no alfanumérico
        ("98", "98.01", "98.01"),
        ("CI", "CI-4", "CI-4"),
        ("C1", "C1A", "C1A"),  # dígito ↔ letra
        # (c) P9: la raíz alfabética del capítulo seguida de fin o de no letra
        ("CI.F2", "CI.01.01", "CI.01.01"),
        ("CD1", "CD2", "CD2"),
        ("CD1", "CD", "CD"),
        ("CI_F1", "CI.6.1", "CI.6.1"),
        # (d) capítulo + cod
        ("CD", "99.01.64", "CD.99.01.64"),
        ("CD", "P4.01.01", "CD.P4.01.01"),
        ("CD", "CDX.01", "CD.CDX.01"),  # letra tras letra: no hay límite
        ("CD", "CDX", "CD.CDX"),
        ("ANT.", "98.01", "ANT.98.01"),  # nunca ANT..98.01
        ("CD1", "CDX", "CD1.CDX"),  # raíz CD seguida de letra: no vale (c)
        ("CI.F2", "CIX.01", "CI.F2.CIX.01"),
        ("98", "981.01", "98.981.01"),  # dígito tras dígito, raíz vacía
        ("98", "A.1", "98.A.1"),
        ("CD", " 99.01 ", "CD. 99.01 "),  # se compone con el cod tal cual
        ("CD", "01.64", "CD.01.64"),
    ],
)
def test_f098_r3_codigo_completo(capitulo, cod, completo):
    assert P.codigo_completo(capitulo, cod) == completo


def test_f098_r3_comparar_es_nfkc_mayusculas_y_sin_espacios_exteriores():
    # «ＣＩ» de ancho completo es «CI» tras NFKC; los espacios exteriores no cuentan.
    assert P.codigo_completo(" ci ", "ＣＩ.4.18") == "ＣＩ.4.18"
    assert P.codigo_completo("CD ", "99.01") == "CD .99.01"


def test_f098_r3_capitulo_vacio_es_sin_capitulo():
    assert P.codigo_completo("", "99.01") == "99.01"
    assert P.codigo_completo("   ", "99.01") == "99.01"


@pytest.mark.parametrize(
    ("antes", "despues", "limite"),
    [
        ("D", None, True),
        ("D", "", True),
        (".", "1", True),
        ("D", ".", True),
        ("D", "2", True),
        ("1", "A", True),
        ("D", "X", False),
        ("1", "2", False),
    ],
)
def test_f098_r3_hay_limite(antes, despues, limite):
    assert P._hay_limite(antes, despues) is limite


@pytest.mark.parametrize(
    ("capitulo", "raiz"),
    [("CI.F2", "CI"), ("CD1", "CD"), ("ANT.", "ANT"), ("98", ""), ("CI_F1", "CI"), (" ci0 ", "CI"), ("CD", "CD")],
)
def test_f098_r3_raiz_alfabetica(capitulo, raiz):
    assert P._raiz_alfabetica(capitulo) == raiz


@pytest.mark.parametrize(
    ("filas", "cod", "completo"),
    [
        (FILAS_0686, "99.01.64", "CD.99.01.64"),
        (FILAS_0686, "21.02.21", "CD.21.02.21"),
        (FILAS_0686, "98.01", "ANT.98.01"),
        (FILAS_0686, "CI.4.18", "CI.4.18"),
        (FILAS_0686, "CP.1.1", "CP.1.1"),
        (FILAS_0692, "01.01", "CD.01.01"),
        (FILAS_0692, "CD2.01", "CD2.01"),
        (FILAS_0692, "CI.01.01", "CI.01.01"),
        (FILAS_0692, "CI.1.1", "CI.1.1"),
        (FILAS_0693, "CI_F1.01.01", "CI_F1.01.01"),
        (FILAS_0693, "37-.01", "CD.37-.01"),
        (FILAS_0696, "P4.01.01", "CD.P4.01.01"),
        (FILAS_0696, "P5.02.01.01", "CD.P5.02.01.01"),
        (FILAS_0711, "CD2", "CD2"),
    ],
)
def test_f098_r3_completo_en_los_arboles_de_t0(filas, cod, completo):
    assert hoja(lista_de("0000", filas), cod).codigo_completo == completo


def test_f098_r3_cd_ci_cp_no_cambian_con_p9():
    """Para un capítulo de solo letras, (c) da lo mismo que (b)."""
    for capitulo in ("CD", "CI", "CP"):
        for cod in ("CD2.01", "CI.4.18", "CP.1.1", "CDX", "P4.01.01", "99.01.64", "CI", "C1"):
            sin_c = cod if (cod.upper().startswith(capitulo) and P._hay_limite(
                capitulo[-1], cod[len(capitulo)] if len(cod) > len(capitulo) else None)) else f"{capitulo}.{cod}"
            assert P.codigo_completo(capitulo, cod) == sin_c


# ------------------------------------------------------------------ #
# R4 · capítulos de la lista
# ------------------------------------------------------------------ #
def test_f098_r4_capitulos_0686():
    assert lista_de("0686", FILAS_0686).capitulos == (
        P.CapituloObra("ANT.", "AJUSTES ALMACÉN", 2),
        P.CapituloObra("CD", "COSTES DIRECTOS", 2),
        P.CapituloObra("CI", "COSTES INDIRECTOS", 1),
        P.CapituloObra("CP", "COSTES PROPORCIONALES", 1),
    )


def test_f098_r4_capitulos_0692_con_ci_f2():
    assert [(c.codigo, c.n_hojas) for c in lista_de("0692", FILAS_0692).capitulos] == [
        ("CD", 2), ("CI", 2), ("CI.F2", 2), ("CP", 1),
    ]


def test_f098_r4_sin_capitulo_al_final():
    filas = [
        [1, None, None, "Sin código"], [2, 1, "A.1", "a"], [3, 1, "A.2", "b"],
        [4, 0, "ZZ", "Último"], [5, 4, "ZZ.1", "z"],
        [6, 0, "AA", "Primero"], [7, 6, "AA.1", "x"],
    ]
    assert lista_de("0000", filas).capitulos == (
        P.CapituloObra("AA", "Primero", 1),
        P.CapituloObra("ZZ", "Último", 1),
        P.CapituloObra(None, None, 2),
    )


def test_f098_r4_capitulo_sin_hojas_no_sale():
    # El capítulo «VACIO» no tiene hojas: es él mismo hoja sin cod... no; aquí
    # VACIO tiene un hijo sin cod, que no es hoja (fuera), así que VACIO no
    # cuenta como capítulo con hojas.
    filas = [[1, 0, "CD", "C"], [2, 1, "01", "h"], [3, 0, "VACIO", "v"], [4, 3, None, "sin cod"]]
    assert [c.codigo for c in lista_de("0000", filas).capitulos] == ["CD"]


def test_f098_r4_lista_vacia_sin_capitulos():
    assert lista_de("0000", []).capitulos == ()
    assert P.ListaPartidasObra("0000", (), ()).capitulos == ()


def test_f098_r4_capitulo_inmutable():
    c = P.CapituloObra("CD", "C", 1)
    with pytest.raises(AttributeError):
        c.n_hojas = 2  # type: ignore[misc]


# ------------------------------------------------------------------ #
# R5 · lo de F-076 no cambia
# ------------------------------------------------------------------ #
def test_f098_r5_hojas_no_hojas_y_orden_como_f076():
    lista = lista_de("0686", FILAS_0686)
    assert lista.codigos == ("21.02.21", "98.01", "98.02", "99.01.64", "CI.4.18", "CP.1.1")
    assert lista.no_hojas == ("21", "21.02", "99", "99.01", "ANT.", "CD", "CI", "CP")
    assert lista.hojas == tuple(P.hojas_de_filas(_COLUMNAS, FILAS_0686))


def test_f098_r5_constructor_posicional_de_f076():
    lista = P.ListaPartidasObra("0678", (P.PartidaObra("A", None, None),), ("X",))
    assert lista.no_hojas_completos == ()
    assert lista.codigos == ("A",)


def test_f098_r5_no_hojas_completos():
    """Los completos de los no hoja que difieren de su cod (para la guarda R8)."""
    assert lista_de("0686", FILAS_0686).no_hojas_completos == ("CD.21", "CD.21.02", "CD.99", "CD.99.01")
    assert lista_de("0696", FILAS_0696).no_hojas_completos == (
        "CD.P4", "CD.P4.01", "CD.P4.08", "CD.P4.22", "CD.P4.80", "CD.P5",
    )
    assert lista_de("0692", FILAS_0692).no_hojas_completos == ()


def test_f098_r5_no_hoja_sin_cod_no_entra_en_completos():
    filas = [[1, None, None, "Sin cod"], [2, 1, None, "Sub sin cod"], [3, 2, "A.1", "Hoja"]]
    assert lista_de("0000", filas).no_hojas_completos == ()


# ------------------------------------------------------------------ #
# R12 · cod repetido entre hojas
# ------------------------------------------------------------------ #
def test_f098_r12_cod_repetido():
    l0692 = lista_de("0692", FILAS_0692)
    assert l0692.cod_repetido("CI.6.1") is True
    assert l0692.cod_repetido("CI.1.1") is False
    assert l0692.cod_repetido("NO.EXISTE") is False
    assert lista_de("0696", FILAS_0696).cod_repetido("P4.08.05") is True
    assert lista_de("0696", FILAS_0696).cod_repetido("P4.01.01") is False


def test_f098_r12_cod_repetido_es_literal():
    """``ci.6.1`` no es el cod ``CI.6.1``: la marca es del cod tal cual."""
    assert lista_de("0692", FILAS_0692).cod_repetido("ci.6.1") is False


# ------------------------------------------------------------------ #
# R6 · casar por el cod y por el código completo, en toda la lista
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("filas", "lectura", "motivo", "cod"),
    [
        (FILAS_0686, "CD.99.01.64", "completa", "99.01.64"),
        (FILAS_0686, "cd 99.1.64", "completa", "99.01.64"),
        (FILAS_0686, "CD-99-01-64", "completa", "99.01.64"),
        (FILAS_0686, " CD.21.02.21 ", "completa", "21.02.21"),
        (FILAS_0686, "ANT.98.01", "completa", "98.01"),
        (FILAS_0686, "ANT 98.1", "completa", "98.01"),
        (FILAS_0686, "98.1", "normalizada", "98.01"),
        (FILAS_0686, "ci.04.18", "normalizada", "CI.4.18"),
        (FILAS_0696, "CD.P4.01.01", "completa", "P4.01.01"),
        (FILAS_0696, "cd p4 1 1", "completa", "P4.01.01"),
        (FILAS_0692, "CD.01.01", "completa", "01.01"),
        (FILAS_0692, "cd2.1", "normalizada", "CD2.01"),
    ],
)
def test_f098_r6_casa_por_el_completo(filas, lectura, motivo, cod):
    caso = P.casar_partida(lista_de("0000", filas), lectura, "ALM")
    assert (caso.motivo, caso.codigos_lista) == (motivo, (cod,))
    assert caso.validada is True


@pytest.mark.parametrize(
    ("filas", "lectura"),
    [
        (FILAS_0692, "CI.1.01"),  # CI.1.1 de CI y CI.01.01 de CI.F2
        (FILAS_0692, "ci 1 1"),
        (FILAS_0693, "CD.37.01"),  # 37.01 y 37-.01 de CD
        (FILAS_0693, "37.1"),  # ya era ambigua en F-076, por el cod
    ],
)
def test_f098_r6_dos_candidatas_ambigua(filas, lectura):
    caso = P.casar_partida(lista_de("0000", filas), lectura, "ALM")
    assert (caso.motivo, caso.codigos_lista) == ("ambigua", ())


def test_f098_r6_ci_f2_con_su_prefijo_no_tiene_completo():
    """P9: el completo de ``CI.01.01`` de CI.F2 es ``CI.01.01``; una lectura
    ``CI.F2.01.01`` no casa (R-3, aceptado)."""
    caso = P.casar_partida(lista_de("0692", FILAS_0692), "CI.F2.01.01", "ALM")
    assert caso.motivo == "fuera_de_lista"


def test_f098_r6_normalizada_gana_a_completa_del_mismo_cod():
    """Un cod que casa por su propio cod es ``normalizada``; uno que casa solo
    por su completo, ``completa``."""
    lista = lista_de("0000", [[1, 0, "CD", "TOTAL"], [2, 0, "X", "x"], [3, 2, "01", "h"]])
    assert P.casar_partida(lista, "cd", None).motivo == "normalizada"
    assert P.casar_partida(lista, "x.1", None).motivo == "completa"


def test_f098_r6_por_cod_y_por_completo_a_la_vez_es_normalizada():
    """Dos hojas con el MISMO cod: una casa por su cod y la otra por su
    completo; es una sola candidata y casa por el cod (normalizada)."""
    filas = [[1, 0, "CD", "COSTES"], [2, 1, "CD.1", "h1"], [3, 0, "Z", "Z"], [4, 3, "CD.1", "h2"]]
    lista = lista_de("0000", filas)
    # «CD.1» en CD: completo CD.1 (b). «CD.1» en Z: completo Z.CD.1.
    caso = P.casar_partida(lista, "cd 1", None)
    assert (caso.motivo, caso.codigos_lista) == ("normalizada", ("CD.1",))
    caso = P.casar_partida(lista, "Z.CD.01", None)
    assert (caso.motivo, caso.codigos_lista) == ("completa", ("CD.1",))


def test_f098_r6_mismo_cod_por_cod_y_por_completo_de_otra_hoja_no_es_ambigua():
    """Dos hojas con el MISMO cod no son dos candidatas (F-076)."""
    lista = lista_de("0696", FILAS_0696)
    caso = P.casar_partida(lista, "CD.P4.8.5", None)
    assert (caso.motivo, caso.codigos_lista) == ("completa", ("P4.08.05",))


def test_f098_r6_completa_esta_en_los_motivos():
    assert P.MOTIVO_COMPLETA == "completa"
    assert "completa" in P.MOTIVOS_PARTIDA
    assert "completa" in P.MOTIVOS_CASADOS
    assert "completa" not in P.MOTIVOS_NO_CASADOS


def test_f098_r6_compuesta_con_partes_completas():
    caso = P.casar_partida(lista_de("0686", FILAS_0686), "CD.99.01.64/CI.4.18", None)
    assert (caso.motivo, caso.codigos_lista) == ("compuesta", ("99.01.64", "CI.4.18"))


def test_f098_r6_compuesta_con_parte_ambigua_por_completo():
    caso = P.casar_partida(lista_de("0693", FILAS_0693), "CD.37.01/CP.1.1", None)
    assert caso.motivo == "ambigua"


def test_f098_r6_hoja_sin_completo_distinto_no_duplica_candidatas():
    """Una hoja cuyo completo es su cod (CI.4.18) entra una sola vez."""
    caso = P.casar_partida(lista_de("0686", FILAS_0686), "CI.04.18", None)
    assert (caso.motivo, caso.codigos_lista) == ("normalizada", ("CI.4.18",))


def test_f098_r6_hoja_construida_a_mano_casa_por_su_cod():
    """Sin capítulo (hojas de F-076 construidas a mano) el completo es el cod."""
    lista = P.ListaPartidasObra("0678", (P.PartidaObra("CI.4.18", None, None),), ())
    assert P.casar_partida(lista, "CI.04.18", None).motivo == "normalizada"


# ------------------------------------------------------------------ #
# R7 · la exacta gana aunque otra hoja tenga ese código completo
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("filas", "lectura"),
    [(FILAS_0692, "CI.01.01"), (FILAS_0696, "P4.22.01.03.07"), (FILAS_0686, "99.01.64"), (FILAS_0692, "CD2.01")],
)
def test_f098_r7_exacta(filas, lectura):
    caso = P.casar_partida(lista_de("0000", filas), lectura, None)
    assert (caso.motivo, caso.codigos_lista) == ("exacta", (lectura,))


def test_f098_r7_exacta_frente_al_completo_de_otra_hoja():
    # La hoja «CD.01» (raíz) y la hoja «01» de CD, cuyo completo es «CD.01».
    filas = [[1, 0, "CD.01", "raíz"], [2, 0, "CD", "COSTES"], [3, 2, "01", "h"]]
    lista = lista_de("0000", filas)
    caso = P.casar_partida(lista, "CD.01", None)
    assert (caso.motivo, caso.codigos_lista) == ("exacta", ("CD.01",))
    # Sin la exacta, las dos candidatas son ambiguas.
    assert P.casar_partida(lista, "cd.1", None).motivo == "ambigua"


# ------------------------------------------------------------------ #
# R8 · resolver: completa ⇒ normalizada; guarda de no hoja con completos
# ------------------------------------------------------------------ #
def test_f098_r8_resolver_completa_es_normalizada():
    r = P.resolver_partida_obra(lista_de("0686", FILAS_0686), "CD.99.01.64", "ALM")
    assert (r.codigo, r.motivo, r.leida, r.cambia) == ("99.01.64", "normalizada", "CD.99.01.64", True)


@pytest.mark.parametrize(
    ("filas", "lectura"),
    [(FILAS_0686, "CD.99.01"), (FILAS_0686, "CD.99"), (FILAS_0696, "CD.P4"), (FILAS_0696, "cd.p4.1")],
)
def test_f098_r8_no_hoja_por_su_completo_es_fuera_de_lista(filas, lectura):
    r = P.resolver_partida_obra(lista_de("0000", filas), lectura, "ALM")
    assert (r.codigo, r.motivo) == (lectura, "fuera_de_lista")


def test_f098_r8_la_guarda_mira_los_completos_de_los_no_hoja():
    """Una hoja cuya clave choca con el completo de un no hoja: sin la guarda
    casaría (normalizada); con ella, ``fuera_de_lista``."""
    filas = FILAS_0686 + [[40, 0, "CD.99.01", "Hoja raíz con forma de subcapítulo"]]
    lista = lista_de("0686", filas)
    assert P.casar_partida(lista, "cd 99 1", None).motivo == "normalizada"
    r = P.resolver_partida_obra(lista, "cd 99 1", None)
    assert (r.codigo, r.motivo) == ("cd 99 1", "fuera_de_lista")
    # La exacta sigue ganando a la guarda (F-076).
    assert P.resolver_partida_obra(lista, "CD.99.01", None).motivo == "exacta"


def test_f098_r8_la_guarda_mira_tambien_ante_una_completa():
    """Una lectura que casa como ``completa`` y choca con un no hoja."""
    filas = [
        [1, 0, "CD", "COSTES"], [2, 1, "99", "VARIOS"], [3, 2, "99.1", "hoja"],
        [4, 0, "CI", "CI"], [5, 4, "CD.99", "no hoja de CI con forma"], [6, 5, "CD.99.9", "x"],
    ]
    lista = lista_de("0000", filas)
    # «CD.99» es no hoja (cod, de CI) y también el completo del no hoja 99 de CD.
    assert P.casar_partida(lista, "CD.99.1", None).motivo == "completa"
    assert P.resolver_partida_obra(lista, "CD.99.1", None).motivo == "normalizada"
    assert P.resolver_partida_obra(lista, "cd.99", None).motivo == "fuera_de_lista"


def test_f098_r8_la_guarda_de_f076_por_el_cod_sigue():
    filas = FILAS_0686 + [[41, 0, "99.1", "Hoja raíz con la clave del no hoja 99.01"]]
    lista = lista_de("0686", filas)
    assert P.casar_partida(lista, "99.001", None).motivo == "normalizada"
    r = P.resolver_partida_obra(lista, "99.001", None)
    assert r.motivo == "fuera_de_lista"


# ------------------------------------------------------------------ #
# R9 · nunca quitar ni añadir un prefijo por parecido
# ------------------------------------------------------------------ #
def test_f098_r9_leida_sin_prefijo_no_casa_con_hoja_que_lo_lleva():
    lista = lista_de("0000", [[1, 0, "CD", "C"], [2, 1, "CD.99.01.64", "hoja con prefijo"]])
    assert P.casar_partida(lista, "99.01.64", None).motivo == "fuera_de_lista"


@pytest.mark.parametrize(
    "lectura", ["01.64", "CI.99.01.64", "CD.99.01", "99.01", "CD.1.64", "D.99.01.64", "CD99.01.64"],
)
def test_f098_r9_sin_parecidos_0686(lectura):
    assert P.casar_partida(lista_de("0686", FILAS_0686), lectura, None).motivo == "fuera_de_lista"


def test_f098_r9_ci_1_01_en_0692_no_elige():
    lista = lista_de("0692", FILAS_0692)
    caso = P.casar_partida(lista, "CI.1.01", None)
    assert caso.codigos_lista == ()
    r = P.resolver_partida_obra(lista, "CI.1.01", None)
    assert (r.codigo, r.motivo) == ("CI.1.01", "ambigua")


def test_f098_r9_cd2_01_de_la_0692_nunca_2_01():
    lista = lista_de("0692", FILAS_0692)
    assert P.resolver_partida_obra(lista, "CD2.01", None).codigo == "CD2.01"
    assert P.casar_partida(lista, "2.01", None).motivo == "fuera_de_lista"
