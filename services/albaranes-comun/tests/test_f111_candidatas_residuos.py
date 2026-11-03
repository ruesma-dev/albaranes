# tests/test_f111_candidatas_residuos.py
"""F-111 R17–R19 · reconocer las hojas del capítulo de gestión de residuos.

Las rutas son las medidas en producción en solo lectura (``progress/spec_F-111.md``
§2): 0686 «GESTIÓN RESIDUOS (SEGÚN EGRC)», 0694 «PLAN DE GESTIÓN DE RESIDUOS»,
0669 con dos capítulos iguales, 0711 «INSTALACION SANEAMIENTO RESIDUAL» (no es
residuos) y las hojas de ajuste (``32.99``, ``23.03``). Sin red.
"""
from __future__ import annotations

from pathlib import Path

import ruesma_comun
import ruesma_comun.sigrid.partidas as P
from ruesma_comun.sigrid import candidatas_residuos

_COLUMNAS = ["ide", "padide", "cod", "res"]


def _lista(obra: str, filas) -> P.ListaPartidasObra:
    return P.ListaPartidasObra.desde_filas(obra, _COLUMNAS, filas)


#: 0686: el capítulo cuelga de CD en nivel 1; 32.99 es de ajuste; 37.06 es otro
#: «GESTIÓN DE RESIDUOS» dentro de seguridad; 05.01 es de otra cosa.
FILAS_0686 = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (10, 1, "32", "GESTIÓN RESIDUOS (SEGÚN EGRC)"),
    (11, 10, "32.01", "GRD010 Gestión de residuos"),
    (12, 10, "32.99", "Ajuste decimales"),
    (20, 1, "37", "SEGURIDAD Y SALUD"),
    (21, 20, "37.06", "GESTIÓN DE RESIDUOS"),
    (22, 21, "37.06.01", "OPERARIO EXCLUSIVO PARA CLASIFICACIÓN"),
    (30, 1, "05", "ESTRUCTURA"),
    (31, 30, "05.01", "HORMIGÓN HA-25"),
]

#: 0694: «PLAN DE GESTIÓN DE RESIDUOS», con su hoja de ajuste 23.03.
FILAS_0694 = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (2, 1, "23", "PLAN DE GESTIÓN DE RESIDUOS"),
    (3, 2, "23.01", "Gestión de residuos de construcción"),
    (4, 2, "23.03", "AJUSTE DECIMALES"),
]

#: 0711: «RESIDUAL» no es residuos; «TRATAMIENTO DE RESIDUOS» es una hoja suelta
#: (sin «GESTION» en un antecesor); «GESTIÓN DE RESIDUOS» como HOJA no cuenta
#: (R17 pide un ANTECESOR).
FILAS_0711 = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (2, 1, "14", "INSTALACION SANEAMIENTO RESIDUAL"),
    (3, 2, "14.01", "Gestión de aguas residuales"),
    (4, 1, "15", "VARIOS"),
    (5, 4, "15.01", "TRATAMIENTO DE RESIDUOS"),
    (6, 4, "15.02", "GESTIÓN DE RESIDUOS"),
    (7, 1, "16", "GESTION ADMINISTRATIVA"),
    (8, 7, "16.01", "CONTENEDOR RESIDUOS 45 LITROS"),
]

#: 0669: dos capítulos «GESTION DE RESIDUOS» en niveles distintos.
FILAS_0669 = [
    (1, 0, "CD", "COSTES DIRECTOS"),
    (2, 1, "102", "FASE 2"),
    (3, 2, "102.08", "GESTION DE RESIDUOS"),
    (4, 3, "102.08.01", "GESTION DE RESIDUOS"),
    (5, 1, "31", "gestión de los residuos en obra/RSD-01"),
    (6, 5, "31.01", "GESTION DE RESIDUOS"),
]


def _codigos(lista) -> tuple[str, ...]:
    return tuple(h.codigo for h in candidatas_residuos(lista))


def test_f111_r17_0686_dos_candidatas_sin_el_ajuste():
    assert _codigos(_lista("0686", FILAS_0686)) == ("32.01", "37.06.01")


def test_f111_r17_0694_plan_de_gestion_una_candidata():
    assert _codigos(_lista("0694", FILAS_0694)) == ("23.01",)


def test_f111_r17_0711_residual_y_hojas_sueltas_no_son_candidatas():
    assert _codigos(_lista("0711", FILAS_0711)) == ()


def test_f111_r17_0669_dos_capitulos_con_tildes_y_minusculas():
    assert _codigos(_lista("0669", FILAS_0669)) == ("102.08.01", "31.01")


def test_f111_r17_devuelve_las_hojas_de_la_lista():
    lista = _lista("0694", FILAS_0694)
    (unica,) = candidatas_residuos(lista)
    assert unica is lista.hojas[0]
    assert isinstance(unica, P.PartidaObra)


def test_f111_r17_gestion_y_residuo_en_el_mismo_antecesor():
    """«GESTION» en un nivel y «RESIDUOS» en otro no es el capítulo."""
    filas = [
        (1, 0, "CD", "GESTION DE OBRA"),
        (2, 1, "01", "RESIDUOS VARIOS"),
        (3, 2, "01.01", "Contenedor"),
    ]
    assert _codigos(_lista("0001", filas)) == ()


def test_f111_r17_residuo_en_singular_y_gestion_con_tilde():
    filas = [
        (1, 0, "CD", "COSTES DIRECTOS"),
        (2, 1, "02", "Gestión del residuo"),
        (3, 2, "02.01", "Canon de vertido"),
    ]
    assert _codigos(_lista("0002", filas)) == ("02.01",)


def test_f111_r17_la_palabra_debe_empezar_por_residuo():
    filas = [
        (1, 0, "CD", "COSTES DIRECTOS"),
        (2, 1, "02", "GESTION DE NORESIDUOS"),
        (3, 2, "02.01", "x"),
        (4, 1, "03", "INGESTION RESIDUOS"),
        (5, 4, "03.01", "y"),
    ]
    assert _codigos(_lista("0003", filas)) == ()


def test_f111_r17_hoja_sin_descripcion_bajo_el_capitulo():
    filas = [
        (1, 0, "CD", "COSTES DIRECTOS"),
        (2, 1, "32", "GESTIÓN RESIDUOS"),
        (3, 2, "32.01", None),
    ]
    assert _codigos(_lista("0004", filas)) == ("32.01",)


def test_f111_r17_hoja_raiz_sin_antecesores():
    filas = [(1, 0, "32", "GESTIÓN DE RESIDUOS")]
    assert _codigos(_lista("0005", filas)) == ()


def test_f111_r17_lee_descripcion_agregada():
    """Una hoja construida a mano (sin filas) también se reconoce."""
    hoja = P.PartidaObra("9.1", "Canon", "CD › GESTIÓN DE RESIDUOS › Canon")
    otra = P.PartidaObra("9.2", "Canon", None)
    sola = P.PartidaObra("9.3", None, None)
    lista = P.ListaPartidasObra(obra="x", hojas=(hoja, otra, sola), no_hojas=())
    assert candidatas_residuos(lista) == (hoja,)


# R18 · fuera las hojas de ajuste
def test_f111_r18_fuera_las_hojas_de_ajuste():
    assert P.PREFIJO_AJUSTE == "AJUSTE"
    hojas = {h.codigo for h in _lista("0686", FILAS_0686).hojas}
    assert "32.99" in hojas  # está en la lista, pero no es candidata
    assert "32.99" not in _codigos(_lista("0686", FILAS_0686))
    assert "23.03" not in _codigos(_lista("0694", FILAS_0694))


def test_f111_r18_ajuste_solo_al_principio():
    filas = [
        (1, 0, "CD", "COSTES DIRECTOS"),
        (2, 1, "32", "GESTIÓN RESIDUOS"),
        (3, 2, "32.01", "Gestión con ajuste de precios"),
        (4, 2, "32.02", "  ajuste  final"),
    ]
    assert _codigos(_lista("0006", filas)) == ("32.01",)


# R19 · no elige; sin lista ⇒ vacía
def test_f111_r19_sin_lista_o_sin_hojas_tupla_vacia():
    assert candidatas_residuos(None) == ()
    assert candidatas_residuos(P.ListaPartidasObra(obra="x", hojas=(), no_hojas=())) == ()


def test_f111_r19_no_cambia_casar_partida():
    lista = _lista("0686", FILAS_0686)
    assert P.casar_partida(lista, "32.01", "ALM").motivo == P.MOTIVO_EXACTA
    assert P.resolver_partida_obra(lista, "", "ALM").motivo == P.RESOLUCION_NO_APLICA


def test_f111_r35_el_patron_esta_congelado():
    assert P.PATRON_CAPITULO_RESIDUOS.search("GESTION DE RESIDUOS")
    assert not P.PATRON_CAPITULO_RESIDUOS.search("SANEAMIENTO RESIDUAL")


def test_f111_t5_version_0130():
    assert ruesma_comun.__version__ == "0.13.0"
    pyproject = (Path(ruesma_comun.__file__).resolve().parents[1] / "pyproject.toml").read_text(
        encoding="utf-8"
    )
    assert 'version = "0.13.0"' in pyproject


def test_f111_t12_ruta_que_no_acaba_en_la_hoja_no_pierde_antecesores():
    """Si el último tramo no es la hoja, todos los tramos son antecesores."""
    hoja = P.PartidaObra("9.1", "Canon", "CD › GESTIÓN DE RESIDUOS")
    lista = P.ListaPartidasObra(obra="x", hojas=(hoja,), no_hojas=())
    assert candidatas_residuos(lista) == (hoja,)
