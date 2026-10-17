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


# ------------------------------------------------------------------ #
# R10, R11, R13 · paso 1: el atajo por nombre dentro de la obra
# ------------------------------------------------------------------ #
import logging  # noqa: E402

from application.services import header_resolver_service as modulo_resolver  # noqa: E402

_DOC = "doc-f062"  # el de f062_dobles
_PREFIJO = "[AVISO] Proveedor"
_MOTIVO = "proveedor_nombre_ambiguo"


class _RepoConLineas(RepoRed):
    """El merge en memoria de F-062 con líneas para la familia."""

    def __init__(self, conceptos=(), **kwargs):
        kwargs.setdefault("cif", None)
        kwargs.setdefault("nombre", None)
        kwargs.setdefault("obra", "0694")
        super().__init__(**kwargs)
        self._conceptos = list(conceptos)

    def get_merge_lines_for_scoring(self, *, document_id):
        return [{"codigo": "", "concepto": c, "contexto_linea_json": None} for c in self._conceptos]


def _paso1(obra_resumenes, nombre, *, conceptos=(), repo=None, **kwargs):
    repo = repo or _RepoConLineas(conceptos)
    servicio = resolver(_ClienteRed(obra_resumenes), repo, **kwargs)
    decision = servicio._resolver_por_obra_y_familia(
        proveedor_nombre=nombre, obra_codigo="0694", merge_document_id=_DOC,
    )
    return decision, repo


def _nota_r11(leido, n, listado, obra="0694"):
    return (
        f"{_PREFIJO} sin CIF: el nombre leído '{leido}' casa por igual con {n} proveedores "
        f"con contrato en la obra {obra}: {listado}. Elige el proveedor arriba y pulsa "
        "\"Guardar y volver a buscar\"."
    )


def test_f073_r9_paso1_la_incidencia_elige_feymaco_por_nombre():
    for leido in ("FEYMACO, S.A.", "TEYMACO, S.A."):
        decision, repo = _paso1(
            [_resumen(_CIF_HIERROS, _RAZ_HIERROS, "ACERO CORRUGADO B500S"),
             _resumen(_CIF_FEYMACO, _RAZ_FEYMACO, "HORMIGON HM-20 MORTERO M-5")],
            leido, conceptos=["DISCO CORTE 230 MM"],
        )
        assert decision == (_CIF_FEYMACO, "deterministic")
        assert repo.marcas == []
        assert repo.review_required is False


def test_f073_r9_paso1_control_con_el_criterio_de_hoy_empataban():
    """Control de la incidencia: con ``_match_score`` (el atajo de antes de
    F-073) las dos razones empatan a 0,50, y el primero era HIERROS."""
    from application.services.header_resolver_service import _match_score, _norm

    for leido in ("FEYMACO, S.A.", "TEYMACO, S.A."):
        assert _match_score(_norm(leido), _norm(_RAZ_HIERROS)) == 0.5
        assert _match_score(_norm(leido), _norm(_RAZ_FEYMACO)) == 0.5


def test_f073_r10_p6_empate_por_nombre_que_separa_la_familia_se_deduce_con_aviso():
    """P6 (humano, 2026-10-15): empate a 1 por nombre; la familia lo separa
    (7 puntos frente a 2) y el paso por puntos de hoy lo deduce."""
    decision, repo = _paso1(
        [_resumen("B2", "HORMIGONES DEL NORTE, S.L.", "HORMIGON HA-25"),
         _resumen("B1", "HORMIGONES DEL SUR, S.L.", "CONTENEDOR RCD")],
        "HORMIGONES", conceptos=["CONTENEDOR 6 M3 RCD"],
    )
    assert decision == ("B1", "det_familia_obra")
    assert repo.marcas == []
    [nota] = repo.lineas_notas()
    assert nota.startswith(f"{_PREFIJO} B1 — HORMIGONES DEL SUR, S.L. deducido AUTOMATICAMENTE")


def test_f073_r10_r11_empate_que_los_puntos_no_deciden_va_a_revision_con_la_nota():
    decision, repo = _paso1(
        [_resumen("B2", "HORMIGONES DEL NORTE, S.L.", "HORMIGON HA-25"),
         _resumen("B1", "HORMIGONES DEL SUR, S.L.", "HORMIGON HM-20"),
         _resumen("B9", "TRANSPORTES PEREZ, S.L.", "PORTES")],
        "HORMIGONES", conceptos=["HORMIGON HA-25/B/20/IIa"],
    )
    assert decision == (None, "deterministic")
    nota = _nota_r11("HORMIGONES", 2, "B1 — HORMIGONES DEL SUR, S.L.; B2 — HORMIGONES DEL NORTE, S.L.")
    assert repo.marcas == [(_MOTIVO, nota, _PREFIJO)]
    assert repo.review_required is True
    assert repo.lista_motivos() == [_MOTIVO]
    assert repo.lineas_notas() == [nota]


def test_f073_r11_nota_ordenada_por_puntos_y_cif_y_con_el_tope_de_candidatos():
    """Empatan los cuatro a 1 por nombre; la familia suma a B4 y B3 (7
    puntos) frente a B1 y B2 (2): no decide (B4 y B3 empatan a puntos). La
    nota lleva 3 (``nota_max_candidatos``) en orden (-puntos, cif) y dice 4."""
    decision, repo = _paso1(
        [_resumen("B1", "HORMIGONES UNO, S.L.", "GASOLEO A"),
         _resumen("B4", "HORMIGONES CUATRO, S.L.", "CONTENEDOR RCD"),
         _resumen("B2", "HORMIGONES DOS, S.L.", "GASOLEO A"),
         _resumen("B3", "HORMIGONES TRES, S.L.", "CONTENEDOR RCD")],
        "HORMIGONES", conceptos=["CONTENEDOR 6 M3 RCD"], nota_max_candidatos=3,
    )
    assert decision == (None, "deterministic")
    [(_, nota, _)] = repo.marcas
    assert nota == _nota_r11(
        "HORMIGONES", 4,
        "B3 — HORMIGONES TRES, S.L.; B4 — HORMIGONES CUATRO, S.L.; B1 — HORMIGONES UNO, S.L.",
    )


def test_f073_r11_dos_pasadas_no_duplican_motivo_ni_nota():
    repo = _RepoConLineas(["HORMIGON HA-25"])
    obra = [_resumen("B2", "HORMIGONES DEL NORTE, S.L.", "HORMIGON HA-25"),
            _resumen("B1", "HORMIGONES DEL SUR, S.L.", "HORMIGON HM-20")]
    _paso1(obra, "HORMIGONES", repo=repo)
    _paso1(obra, "HORMIGONES", repo=repo)
    assert repo.lista_motivos() == [_MOTIVO]
    assert len(repo.lineas_notas()) == 1


def test_f073_r11_la_nota_sustituye_a_la_de_otra_pasada_de_proveedor():
    repo = _RepoConLineas(["HORMIGON HA-25"])
    repo.notas = (
        f"{_PREFIJO} sin CIF: no deducible con seguridad. Candidatos con contrato en la obra 0694: X\n"
        "otra nota"
    )
    _paso1([_resumen("B2", "HORMIGONES DEL NORTE, S.L.", "HORMIGON HA-25"),
            _resumen("B1", "HORMIGONES DEL SUR, S.L.", "HORMIGON HM-20")], "HORMIGONES", repo=repo)
    assert repo.lineas_notas()[0] == "otra nota"
    assert repo.lineas_notas()[1].startswith(
        f"{_PREFIJO} sin CIF: el nombre leído 'HORMIGONES' casa por igual",
    )


def test_f073_r11_si_la_marca_falla_no_rompe_y_no_hay_cif():
    class _Falla(_RepoConLineas):
        def marcar_revision_cabecera(self, **kwargs):
            raise RuntimeError("BBDD caida")

    decision, repo = _paso1(
        [_resumen("B2", "HORMIGONES DEL NORTE, S.L.", "HORMIGON HA-25"),
         _resumen("B1", "HORMIGONES DEL SUR, S.L.", "HORMIGON HM-20")],
        "HORMIGONES", repo=_Falla(["HORMIGON HA-25"]),
    )
    assert decision == (None, "deterministic")
    assert repo.notas is None


def test_f073_r11_sin_empate_y_sin_decision_la_nota_de_hoy_sin_motivo():
    """Nadie llega al umbral por nombre y los puntos no deciden: como hoy."""
    decision, repo = _paso1(
        [_resumen("B2", "ALFA, S.L.", "HORMIGON HA-25"), _resumen("B1", "BETA, S.L.", "HORMIGON HM-20")],
        "ZZZZ", conceptos=["HORMIGON HA-25"],
    )
    assert decision == (None, "deterministic")
    assert repo.marcas == []
    [nota] = repo.lineas_notas()
    assert nota.startswith(f"{_PREFIJO} sin CIF: no deducible con seguridad.")


@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_f073_r12_paso1_misma_decision_y_nota_con_cualquier_orden(semilla):
    obra = [_resumen(f"B{i}", f"HORMIGONES {i:02d}, S.L.", "HORMIGON HA-25" if i % 2 else "GASOLEO")
            for i in range(1, 9)]
    referencia = _paso1(obra, "HORMIGONES", conceptos=["HORMIGON HA-25"])
    barajada = list(obra)
    random.Random(semilla).shuffle(barajada)
    otra = _paso1(barajada, "HORMIGONES", conceptos=["HORMIGON HA-25"])
    assert otra[0] == referencia[0] == (None, "deterministic")
    assert otra[1].marcas == referencia[1].marcas
    assert "B1 — HORMIGONES 01, S.L.; B3 — HORMIGONES 03, S.L." in referencia[1].marcas[0][1]


def _mensajes(caplog):
    return [r.getMessage() for r in caplog.records]


def test_f073_r13_log_al_elegir(caplog):
    with caplog.at_level(logging.INFO, logger=modulo_resolver.logger.name):
        _paso1([_resumen(_CIF_HIERROS, _RAZ_HIERROS), _resumen(_CIF_FEYMACO, _RAZ_FEYMACO)], "TEYMACO, S.A.")
    assert any(
        f"elegido cif={_CIF_FEYMACO} similitud=1.00 segunda=0.00 margen=0.25" in m and "obra 0694" in m
        for m in _mensajes(caplog)
    )


def test_f073_r13_log_en_empate_dice_cuantos(caplog):
    with caplog.at_level(logging.INFO, logger=modulo_resolver.logger.name):
        _paso1([_resumen("B2", "HORMIGONES DEL NORTE, S.L."), _resumen("B1", "HORMIGONES DEL SUR, S.L."),
                _resumen("B3", "HORMIGONES DEL ESTE, S.L.")], "HORMIGONES")
    assert any(
        "EMPATE" in m and "mejor cif=B1 similitud=1.00 segunda=1.00 margen=0.25 empatados=3" in m
        for m in _mensajes(caplog)
    )


def test_f073_r13_log_sin_nadie_que_llegue(caplog):
    with caplog.at_level(logging.INFO, logger=modulo_resolver.logger.name):
        _paso1([_resumen("B2", "ALFA, S.L."), _resumen("B1", "BETA, S.L.")], "ZZZZ")
    assert any(
        "nadie llega al umbral" in m and "mejor cif=B1 similitud=0.00 segunda=0.00 umbral=0.50" in m
        for m in _mensajes(caplog)
    )


# ------------------------------------------------------------------ #
# R10, R14 · paso 2: el fallback global por nombre
# ------------------------------------------------------------------ #
class _ClienteGlobal(_ClienteRed):
    def __init__(self, obra, globales):
        super().__init__(obra)
        self.globales = list(globales)

    def search_proveedores(self):
        return list(self.globales)


def _resolver_completo(obra, globales, nombre, *, repo=None, conceptos=()):
    repo = repo or _RepoConLineas(conceptos, nombre=nombre)
    pasada(_ClienteGlobal(obra, globales), repo)
    return repo


def test_f073_r9_paso2_elige_con_margen():
    """Sin candidatos en la obra, el global elige FEYMACO; con el criterio de
    antes (0,50 y 0,50) ganaba el primero de la lista, HIERROS RODRIGO."""
    repo = _resolver_completo(
        [], [(_CIF_HIERROS, _RAZ_HIERROS), (_CIF_FEYMACO, _RAZ_FEYMACO)], "TEYMACO, S.A.",
    )
    assert repo.resoluciones == [(None, _CIF_FEYMACO, "deterministic")]
    assert (repo.cif, repo.origen) == (_CIF_FEYMACO, "deterministic")


def test_f073_r14_paso2_en_empate_no_elige_ni_deja_nota_ni_motivo(caplog):
    with caplog.at_level(logging.INFO, logger=modulo_resolver.logger.name):
        repo = _resolver_completo(
            [], [("B2", "HORMIGONES DEL NORTE, S.L."), ("B1", "HORMIGONES DEL SUR, S.L."),
                 ("B9", "TRANSPORTES PEREZ, S.L.")], "HORMIGONES",
        )
    assert repo.resoluciones == [(None, None, "deterministic")]
    assert repo.cif is None
    assert repo.marcas == []
    assert repo.motivos is None
    assert repo.notas is None
    assert any(
        "global" in m and "EMPATE" in m and "mejor cif=B1 similitud=1.00 segunda=1.00 margen=0.25 empatados=2" in m
        for m in _mensajes(caplog)
    )


def test_f073_r14_la_nota_del_paso1_sobrevive_al_empate_global():
    obra = [_resumen("B2", "HORMIGONES DEL NORTE, S.L.", "HORMIGON HA-25"),
            _resumen("B1", "HORMIGONES DEL SUR, S.L.", "HORMIGON HM-20")]
    globales = [("B1", "HORMIGONES DEL SUR, S.L."), ("B2", "HORMIGONES DEL NORTE, S.L."),
                ("B7", "HORMIGONES DEL OESTE, S.L.")]
    repo = _resolver_completo(obra, globales, "HORMIGONES", conceptos=["HORMIGON HA-25"])
    assert repo.cif is None
    assert repo.lista_motivos() == [_MOTIVO]
    [nota] = repo.lineas_notas()
    assert nota == _nota_r11("HORMIGONES", 2, "B1 — HORMIGONES DEL SUR, S.L.; B2 — HORMIGONES DEL NORTE, S.L.")


def test_f073_r14_paso2_por_debajo_del_umbral_no_elige(caplog):
    with caplog.at_level(logging.INFO, logger=modulo_resolver.logger.name):
        repo = _resolver_completo([], [("B1", "ALFA, S.L."), ("B2", "BETA, S.L.")], "ZZZZ")
    assert repo.cif is None
    assert any("global" in m and "nadie llega al umbral" in m for m in _mensajes(caplog))


def test_f073_r14_paso2_al_elegir_retira_el_aviso_de_proveedor():
    repo = _RepoConLineas((), nombre="TEYMACO, S.A.")
    repo.notas = f"{_PREFIJO} sin CIF: algo viejo"
    _resolver_completo([], [(_CIF_FEYMACO, _RAZ_FEYMACO)], "TEYMACO, S.A.", repo=repo)
    assert repo.cif == _CIF_FEYMACO
    assert repo.notas in (None, "")


def test_f073_r12_paso2_misma_decision_con_cualquier_orden():
    globales = [(f"B{i}", f"HORMIGONES {i:02d}, S.L.") for i in range(1, 30)] + [(_CIF_FEYMACO, _RAZ_FEYMACO)]
    for leido, esperado in (("FEYMACO", _CIF_FEYMACO), ("HORMIGONES", None), ("HORMIGONES 07", "B7")):
        for semilla in (1, 2, 3):
            barajada = list(globales)
            random.Random(semilla).shuffle(barajada)
            assert _resolver_completo([], barajada, leido).cif == esperado


def test_f073_r14_paso2_con_los_3543_proveedores_del_doble():
    """El global de verdad (3.543 del doble de sigrid-api): «SALMEDINA»
    elige, «PROVEEDOR» empata y no elige, y no tarda."""
    import time

    from doble_sigrid_api import CIF_SALMEDINA, DobleSigridApi

    cliente = DobleSigridApi().cliente()
    globales = cliente.search_proveedores()
    assert len(globales) == 3543
    inicio = time.perf_counter()
    for leido, esperado in (("SALMEDINA", CIF_SALMEDINA), ("SALMEDlNA S.L.", CIF_SALMEDINA), ("PROVEEDOR", None)):
        assert _resolver_completo([], globales, leido).cif == esperado
    assert time.perf_counter() - inicio < 10


# ------------------------------------------------------------------ #
# R20 · el margen es un parámetro del constructor, con su defecto
# ------------------------------------------------------------------ #
def test_f073_r20_margen_por_defecto_y_en_el_log_de_instanciado(caplog):
    import inspect

    from application.services.header_resolver_service import HeaderResolverService

    parametro = inspect.signature(HeaderResolverService.__init__).parameters["margen_nombre"]
    assert parametro.kind is inspect.Parameter.KEYWORD_ONLY
    assert parametro.default == MARGEN_NOMBRE_POR_DEFECTO == 0.25
    with caplog.at_level(logging.INFO, logger=modulo_resolver.logger.name):
        resolver(_ClienteRed([]), _RepoConLineas(), margen_nombre=0.4)
    [instanciado] = [m for m in _mensajes(caplog) if "INSTANCIADO" in m]
    assert "margen_nombre=0.4" in instanciado


def test_f073_r20_el_margen_del_constructor_es_el_que_se_aplica():
    """1,0 frente a 0,75: elige con 0,25 (inclusivo) y empata con 0,3."""
    obra = [_resumen("B1", "ALFA BETA GAMMA DELTA"), _resumen("B2", "ALFA BETA GAMMA OMEGA")]
    assert _paso1(obra, "ALFA BETA GAMMA DELTA")[0] == ("B1", "deterministic")
    decision, repo = _paso1(obra, "ALFA BETA GAMMA DELTA", margen_nombre=0.3)
    assert decision == (None, "deterministic")
    assert repo.lista_motivos() == [_MOTIVO]
    globales = [("B1", "ALFA BETA GAMMA DELTA"), ("B2", "ALFA BETA GAMMA OMEGA")]
    assert _resolver_completo([], globales, "ALFA BETA GAMMA DELTA").cif == "B1"
    repo = _RepoConLineas((), nombre="ALFA BETA GAMMA DELTA")
    pasada(_ClienteGlobal([], globales), repo, margen_nombre=0.3)
    assert repo.cif is None


@pytest.mark.parametrize("modulo", ["interface_adapters/composition.py", "interface_adapters/api/app.py"])
def test_f073_r20_las_dos_composiciones_usan_el_defecto(modulo):
    """Sin variable de entorno ni interruptor (P2, P3): las composiciones no
    pasan ``margen_nombre`` y ``config/settings.py`` no tiene un campo."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[1]
    fuente = (raiz / modulo).read_text(encoding="utf-8")
    assert "HeaderResolverService(" in fuente
    assert "margen_nombre" not in fuente
    assert "margen_nombre" not in (raiz / "config" / "settings.py").read_text(encoding="utf-8")
