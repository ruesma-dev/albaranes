# tests/test_f073_eleccion.py
"""F-073 · R9–R14 y R20 — elegir por nombre, nunca en un empate.

``elegir_por_nombre`` agrupa los candidatos por CIF normalizado (cada uno
con su mejor similitud) y elige el mejor solo si llega al umbral Y saca al
segundo CIF el margen (0,25, inclusivo). El resolver lo usa en el atajo del
paso 1 y en el fallback global del paso 2. Sin red ni BBDD.
"""
from __future__ import annotations

import random

import pytest

from application.services.similitud_proveedor import (
    MARGEN_NOMBRE_POR_DEFECTO,
    CandidatoNombre,
    EleccionPorNombre,
    elegir_por_nombre,
)


def _elegir(leido, candidatos, *, umbral=0.5, margen=MARGEN_NOMBRE_POR_DEFECTO) -> EleccionPorNombre:
    return elegir_por_nombre(leido, candidatos, umbral=umbral, margen=margen)


# ------------------------------------------------------------------ #
# R9 · umbral y margen
# ------------------------------------------------------------------ #
def test_f073_r9_margen_por_defecto():
    assert MARGEN_NOMBRE_POR_DEFECTO == 0.25


def test_f073_r9_la_incidencia_elige_feymaco_con_margen():
    eleccion = _elegir("TEYMACO, S.A.", [
        ("A19004589", "HIERROS RODRIGO, S.A."),
        ("A28733558", "FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)"),
    ])
    assert eleccion.elegido == CandidatoNombre(
        cif="A28733558",
        nombre="FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)",
        similitud=1.0,
    )
    assert eleccion.empatados == ()
    assert eleccion.segunda == 0.0
    assert eleccion.mejor == eleccion.elegido


def test_f073_r9_sin_segundo_cuenta_cero():
    eleccion = _elegir("HORMIGONES 2000", [("B1", "HORMIGONES 2001 SL")])
    assert eleccion.elegido.cif == "B1"
    assert eleccion.elegido.similitud == 0.5
    assert eleccion.segunda == 0.0


@pytest.mark.parametrize(
    ("umbral", "elige"),
    [(0.5, True), (0.5000001, False)],
    ids=["umbral-inclusivo", "por-debajo"],
)
def test_f073_r9_umbral_inclusivo(umbral, elige):
    eleccion = _elegir("HORMIGONES 2000", [("B1", "HORMIGONES 2001 SL")], umbral=umbral)
    assert (eleccion.elegido is not None) is elige
    # Por debajo del umbral no es empate: es «nadie casa».
    assert eleccion.empatados == ()
    assert eleccion.mejor.cif == "B1"


def test_f073_r9_margen_inclusivo_exacto():
    # 1,0 frente a 0,75 (3 de 4 palabras): diferencia 0,25 justa ⇒ elige.
    eleccion = _elegir("ALFA BETA GAMMA DELTA", [
        ("B2", "ALFA BETA GAMMA OMEGA"),
        ("B1", "ALFA BETA GAMMA DELTA"),
    ])
    assert eleccion.elegido.cif == "B1"
    assert eleccion.segunda == 0.75


def test_f073_r9_margen_inclusivo_con_coma_flotante():
    """2/3 frente a 5/12: la diferencia es 0,25 en exacto, pero en coma
    flotante sale 0,2499…; con margen 0,25 inclusivo, elige."""
    from application.services import similitud_proveedor as modulo

    assert 2 / 3 - 5 / 12 < 0.25
    eleccion = modulo._decidir(
        [CandidatoNombre("B2", "DOS", 5 / 12), CandidatoNombre("B1", "UNO", 2 / 3)],
        umbral=0.5, margen=0.25,
    )
    assert eleccion.elegido.cif == "B1"
    # Y una diferencia de verdad menor que el margen sigue siendo empate.
    eleccion = modulo._decidir(
        [CandidatoNombre("B2", "DOS", 2 / 3 - 0.2499), CandidatoNombre("B1", "UNO", 2 / 3)],
        umbral=0.5, margen=0.25,
    )
    assert eleccion.elegido is None


def test_f073_r9_sin_margen_no_elige_y_dice_quien_empata():
    # «PROVEEDOR OBRA» casa 1,0 con los tres; nadie saca margen.
    eleccion = _elegir("PROVEEDOR OBRA", [
        ("B3", "PROVEEDOR OBRA 03, S.L."),
        ("B1", "PROVEEDOR OBRA 01, S.L."),
        ("B2", "PROVEEDOR OBRA 02, S.L."),
        ("B9", "OTRA COSA, S.L."),
    ])
    assert eleccion.elegido is None
    assert [c.cif for c in eleccion.empatados] == ["B1", "B2", "B3"]
    assert eleccion.segunda == 1.0
    assert eleccion.mejor.cif == "B1"


def test_f073_r9_empatados_son_los_que_quedan_a_menos_del_margen():
    # 1,0 / 0,8 (4 de 5) / 0,6 (3 de 5) / 0,75 (3 de 4): a MENOS de 0,25 del
    # mejor solo 1,0 y 0,8 (0,75 queda justo en el margen: no empata).
    eleccion = _elegir("ALFA BETA GAMMA DELTA EPSILON", [
        ("B4", "ALFA BETA GAMMA ZZZZ YYYY"),
        ("B2", "ALFA BETA GAMMA DELTA ZZZZ"),
        ("B1", "ALFA BETA GAMMA DELTA EPSILON"),
        ("B3", "ALFA BETA GAMMA ZZZZ"),
    ])
    assert eleccion.elegido is None
    assert [(c.cif, c.similitud) for c in eleccion.empatados] == [
        ("B1", 1.0), ("B2", 0.8),
    ]
    assert eleccion.segunda == 0.8


def test_f073_r9_agrupa_por_cif_normalizado_con_su_mejor_similitud():
    """Dos filas del mismo CIF son un candidato, no un empate."""
    eleccion = _elegir("FEYMACO", [
        ("A28733558", "FERRETERIA FEYMACO, S.A."),
        (" es-a28733558 ", "OTRO NOMBRE, S.A."),
        ("A19004589", "HIERROS RODRIGO, S.A."),
    ])
    assert eleccion.elegido.cif == "A28733558"
    assert eleccion.elegido.similitud == 1.0
    assert eleccion.segunda == 0.0


def test_f073_r9_mismo_cif_con_la_misma_similitud_no_es_empate():
    eleccion = _elegir("PROVEEDOR OBRA", [
        ("B1", "PROVEEDOR OBRA 01, S.L."),
        ("b-1", "PROVEEDOR OBRA 01 BIS, S.L."),
    ])
    assert eleccion.elegido is not None
    assert eleccion.elegido.cif == "B1"


@pytest.mark.parametrize("cif", [None, "", "   "])
def test_f073_r9_un_cif_vacio_se_ignora(cif):
    eleccion = _elegir("FEYMACO", [(cif, "FEYMACO, S.A."), ("B2", "HIERROS RODRIGO")])
    assert eleccion.elegido is None
    assert eleccion.mejor.cif == "B2"
    assert eleccion.mejor.similitud == 0.0


def test_f073_r9_cif_que_no_normaliza_agrupa_por_su_texto():
    """Un CIF que ``normalizar_cif`` deja vacío pero tiene texto (p. ej.
    «Ñ») cuenta por su texto recortado."""
    eleccion = _elegir("FEYMACO", [(" Ñ ", "FEYMACO, S.A."), ("Ñ", "FEYMACO 2, S.A.")])
    assert eleccion.elegido.cif == "Ñ"


def test_f073_r9_sin_candidatos():
    eleccion = _elegir("FEYMACO", [])
    assert eleccion == EleccionPorNombre(elegido=None, empatados=(), segunda=0.0, mejor=None)


def test_f073_r9_sin_nombre_leido_nadie_llega():
    eleccion = _elegir(None, [("B1", "FEYMACO, S.A.")])
    assert eleccion.elegido is None
    assert eleccion.empatados == ()


def test_f073_r9_con_umbral_cero_y_todo_a_cero_es_empate_no_eleccion():
    eleccion = _elegir("ZZZZ", [("B1", "ALFA"), ("B2", "BETA")], umbral=0.0)
    assert eleccion.elegido is None
    assert [c.cif for c in eleccion.empatados] == ["B1", "B2"]


def test_f073_r9_el_cif_que_se_devuelve_es_el_recortado_de_la_fila():
    """Se escribe en el merge el CIF tal como lo da Sigrid (recortado), no
    el normalizado (un ``ESB…`` de 11 caracteres seguiría siendo ``ESB…``)."""
    eleccion = _elegir("FEYMACO", [("  ESA28733558 ", "FEYMACO, S.A."), ("B2", "HIERROS RODRIGO")])
    assert eleccion.elegido.cif == "ESA28733558"


# ------------------------------------------------------------------ #
# R12 · el orden de llegada no cambia nada
# ------------------------------------------------------------------ #
_LISTA_R12 = [
    ("B3", "PROVEEDOR OBRA 03, S.L."),
    ("B1", "PROVEEDOR OBRA 01, S.L."),
    ("b-1", "PROVEEDOR OBRA, S.L."),
    ("B2", "PROVEEDOR OBRA 02, S.L."),
    ("B4", "PROVEEDOR GLOBAL, S.L."),
    ("B5", "OTRA COSA, S.L."),
    ("es-b2", "PROVEEDOR OBRA 02 BIS, S.L."),
]


@pytest.mark.parametrize("leido", ["PROVEEDOR OBRA", "PROVEEDOR OBRA 02", "OTRA COSA", "ZZZZ"])
@pytest.mark.parametrize("semilla", [1, 2, 3, 4, 5])
def test_f073_r12_misma_decision_con_cualquier_orden(leido, semilla):
    referencia = _elegir(leido, _LISTA_R12)
    barajada = list(_LISTA_R12)
    random.Random(semilla).shuffle(barajada)
    assert barajada != _LISTA_R12
    assert _elegir(leido, barajada) == referencia
    assert _elegir(leido, reversed(_LISTA_R12)) == referencia


# ------------------------------------------------------------------ #
# R1, R8 · un solo criterio en sv3
# ------------------------------------------------------------------ #
def test_f073_r1_r8_el_resolver_no_tiene_criterio_propio():
    """Fuera del resolver los dos criterios viejos de proveedor; la obra
    conserva ``_match_score`` (R16)."""
    from application.services import header_resolver_service as modulo
    from application.services import similitud_proveedor as criterio

    for viejo in ("_PUNTUACION_RAZON", "_score_razon_social", "_distancia_edicion"):
        assert not hasattr(modulo, viejo), viejo
    assert modulo.similitud_razon_social is criterio.similitud_razon_social
    assert modulo.distancia_edicion is criterio.distancia_edicion
    assert modulo.elegir_por_nombre is criterio.elegir_por_nombre
    assert hasattr(modulo, "_match_score")


def test_f073_r1_el_script_de_verificacion_de_f052_usa_el_criterio_unico():
    """Decisión del humano (2026-10-17, opción a): el script cuenta como
    sitio de R1."""
    import importlib

    from application.services import similitud_proveedor as criterio

    script = importlib.import_module("scripts.verificar_f052_proveedores_obra")
    assert script.similitud_razon_social is criterio.similitud_razon_social
    assert not hasattr(script, "_score_razon_social")


# ------------------------------------------------------------------ #
# R15 · la red por CIF conserva sus reglas; solo cambia la similitud
# ------------------------------------------------------------------ #
from domain.models.header_resolution_models import ProveedorObraResumen  # noqa: E402
from f062_dobles import RepoRed, pasada, resolver  # noqa: E402

_RAZ_FEYMACO = "FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A. (FEYMACO)"
_RAZ_HIERROS = "HIERROS RODRIGO, S.A."
_CIF_FEYMACO = "A28733558"
_CIF_HIERROS = "A19004589"
_CIF_LEIDO_INEXISTENTE = "B86056201"  # control inválido, no está en prv


def _resumen(cif, nombre, texto="SUMINISTRO VARIOS"):
    return ProveedorObraResumen(cif=cif, nombre=nombre, codigos_contratos=("CT1",), texto=texto)


class _ClienteRed:
    def __init__(self, obra):
        self.obra = list(obra)

    def fetch_proveedor_by_cif(self, *, cif):
        return None

    def fetch_contratos_resumen_por_obra(self, *, codigo_obra):
        return list(self.obra)

    def search_proveedores(self):
        return []


def test_f073_r15_la_propuesta_y_el_candidato_claro_usan_la_similitud_unica():
    """«TEYMACO, S.A.» con un CIF que no existe: hoy no casaba con nadie
    (``_score_razon_social`` = 0); con F-073 casa a 1 con FEYMACO y es el
    candidato claro."""
    cliente = _ClienteRed([_resumen(_CIF_HIERROS, _RAZ_HIERROS), _resumen(_CIF_FEYMACO, _RAZ_FEYMACO)])
    servicio = resolver(cliente, RepoRed(cif=None, nombre=None, obra="0694"))
    puntuados, motivo = servicio._candidatos_puntuados(proveedor_nombre="TEYMACO, S.A.", obra="0694")
    assert [(r.cif, s) for r, s in puntuados] == [(_CIF_HIERROS, 0.0), (_CIF_FEYMACO, 1.0)]
    assert motivo == "propuesta"
    assert servicio._candidato_claro(cif_leido=_CIF_LEIDO_INEXISTENTE, puntuados=puntuados) == (
        puntuados[1][0], "unico",
    )


def test_f073_r15_la_propuesta_sigue_siendo_el_primero_en_empate():
    """P5: la propuesta de F-052 no cambia de regla (el primero en empate)."""
    cliente = _ClienteRed([_resumen("B2", "PROVEEDOR OBRA 02, S.L."), _resumen("B1", "PROVEEDOR OBRA 01, S.L.")])
    servicio = resolver(cliente, RepoRed(cif=None, nombre=None, obra="0691"))
    candidato, motivo, n = servicio._mejor_candidato_por_nombre(
        proveedor_nombre="PROVEEDOR OBRA", obra_codigo_efectiva="0691",
    )
    assert (candidato.cif, motivo, n) == ("B2", "propuesta", 2)


def test_f073_r15_p0_una_forma_juridica_sola_no_corrige_y_es_nadie_casa():
    """P0 (humano, 2026-10-15): sustituye al caso «solo-forma-juridica» de la
    opción B de F-062 (decisión del 2026-10-08). «S.L.» leído como nombre ya
    no casa con «ARIDOS ANFERSA, S.L.»: sin corrección y con el motivo de
    cualquier «nadie casa»."""
    cliente = _ClienteRed([_resumen("B18487421", "ARIDOS ANFERSA, S.L.")])
    repo = RepoRed(cif=_CIF_LEIDO_INEXISTENTE, nombre="S.L.", obra="0720")
    pasada(cliente, repo)
    assert repo.aplicadas == []
    assert repo.cif == _CIF_LEIDO_INEXISTENTE
    assert repo.lista_motivos() == [f"proveedor_cif_no_casa:{_CIF_LEIDO_INEXISTENTE}"]
    [nota] = [n for n in repo.lineas_notas() if n.startswith("[AVISO] Proveedor")]
    assert "ninguno de los 1 proveedores con contrato en la obra 0720 casa" in nota
    assert "PROPUESTA" not in nota
