# tests/test_f080_empate_solo_entre_empatados.py
"""F-080 · R1–R12 — tras un empate por nombre, la familia solo elige entre
los empatados.

El paso por puntos de hoy no cambia (sobre todos los candidatos de la obra,
mínimo 3 y margen 2), pero tras un empate por nombre su ganador solo se
acepta si es uno de los empatados (clave de CIF normalizada). Si gana un
ajeno, revisión con ``proveedor_nombre_ambiguo`` y la nota de R11 de F-073.
Casos de ``specs/F-080-empate-solo-entre-empatados/design.md`` §1. Sin red
ni BBDD.
"""
from __future__ import annotations

import inspect
import logging
import random

import pytest

from application.services import header_resolver_service as modulo
from f062_dobles import pasada
from test_f073_eleccion import _ClienteRed, _paso1, _RepoConLineas, _resumen

_PREFIJO = "[AVISO] Proveedor"
_MOTIVO = "proveedor_nombre_ambiguo"
_LEIDO = "HORMIGONES"

_SUR = "HORMIGONES DEL SUR, S.L."
_NORTE = "HORMIGONES DEL NORTE, S.L."
_ARIDOS = "ARIDOS PEPE, S.L."

_LINEAS_H4 = ["HORMIGON HA-25", "MORTERO M-5"]
_LINEAS_P1 = [*_LINEAS_H4, "ACERO CORRUGADO B500S"]

# Puntos de cada caso entre paréntesis (design §1).
# H4: SUR (2), NORTE (2) empatados; ARIDOS (6).
_OBRA_H4 = [
    _resumen("B1", _SUR, "GASOLEO A"),
    _resumen("B2", _NORTE, "GASOLEO A"),
    _resumen("B9", _ARIDOS, "HORMIGON HA-25 MORTERO M-5"),
]
# P1: SUR (7), NORTE (2) empatados; ARIDOS (9, hormigón+mortero+acero).
_OBRA_P1 = [
    _resumen("B1", _SUR, "HORMIGON HA-25"),
    _resumen("B2", _NORTE, "GASOLEO A"),
    _resumen("B9", _ARIDOS, "HORMIGON HA-25 MORTERO M-5 ACERO CORRUGADO"),
]
# Ajeno cerca: SUR (7), NORTE (2); ARIDOS (6).
_OBRA_CERCA = [
    _resumen("B1", _SUR, "HORMIGON HA-25"),
    _resumen("B2", _NORTE, "GASOLEO A"),
    _resumen("B9", _ARIDOS, "HORMIGON HA-25 MORTERO M-5"),
]
# Ajeno lejos (línea solo de hormigón): SUR (7), NORTE (2); ARIDOS (3).
_OBRA_LEJOS = [
    _resumen("B1", _SUR, "HORMIGON HA-25"),
    _resumen("B2", _NORTE, "GASOLEO A"),
    _resumen("B9", _ARIDOS, "HORMIGON HA-25"),
]
# Penalización (línea solo de hormigón): SUR sin familias (4), NORTE gasóleo (2).
_OBRA_PENALIZACION = [
    _resumen("B1", _SUR, ""),
    _resumen("B2", _NORTE, "GASOLEO A"),
]


def _nota_r11(n, listado, leido=_LEIDO, obra="0694"):
    return (
        f"{_PREFIJO} sin CIF: el nombre leído '{leido}' casa por igual con {n} proveedores "
        f"con contrato en la obra {obra}: {listado}. Elige el proveedor arriba y pulsa "
        "\"Guardar y volver a buscar\"."
    )


_NOTA_H4 = _nota_r11(2, f"B1 — {_SUR}; B2 — {_NORTE}")


def _nota_deducido(cif, nombre, familias, n, leido=_LEIDO, obra="0694"):
    """La nota de ``det_familia_obra`` de hoy, sin cambios (R1)."""
    return (
        f"{_PREFIJO} {cif} — {nombre} deducido AUTOMATICAMENTE por familia de producto "
        f"({familias}) entre {n} proveedor(es) con contrato en la obra {obra} "
        f"(nombre leido: '{leido}'). Verificar que es el correcto."
    )


def _mensajes(caplog):
    return [r.getMessage() for r in caplog.records]


def _sin_deducido(repo):
    assert not any("deducido AUTOMATICAMENTE" in n for n in repo.lineas_notas())


def _en_revision_r11(decision, repo, nota):
    assert decision == (None, "deterministic")
    assert repo.marcas == [(_MOTIVO, nota, _PREFIJO)]
    assert repo.review_required is True
    assert repo.lista_motivos() == [_MOTIVO]
    assert repo.lineas_notas() == [nota]
    assert repo.cif is None


# ------------------------------------------------------------------ #
# R1 · el ganador por puntos es un empatado: se deduce como hoy
# ------------------------------------------------------------------ #
def test_f080_r1_el_empatado_que_gana_con_margen_se_deduce_como_hoy(caplog):
    """Ajeno lejos: SUR (7) saca 4 a ARIDOS (3)."""
    with caplog.at_level(logging.INFO, logger=modulo.logger.name):
        decision, repo = _paso1(_OBRA_LEJOS, _LEIDO, conceptos=["HORMIGON HA-25"])
    assert decision == ("B1", "det_familia_obra")
    assert repo.marcas == []
    assert repo.review_required is False
    assert repo.motivos is None
    assert repo.lineas_notas() == [_nota_deducido("B1", _SUR, "hormigon", 3)]
    mensajes = _mensajes(caplog)
    assert any("B1 DEDUCIDO por familia+obra" in m for m in mensajes)
    assert not any("AJENO" in m for m in mensajes)


# ------------------------------------------------------------------ #
# R2, R3 · el ganador por puntos es un ajeno: revisión con la nota de R11
# ------------------------------------------------------------------ #
def test_f080_r3_el_caso_de_h4_va_a_revision_con_la_nota_de_los_dos_hormigones():
    decision, repo = _paso1(_OBRA_H4, _LEIDO, conceptos=_LINEAS_H4)
    _en_revision_r11(decision, repo, _NOTA_H4)
    assert "casa por igual con 2 proveedores" in _NOTA_H4
    assert "B9" not in _NOTA_H4
    _sin_deducido(repo)


def test_f080_r2_con_el_tope_la_nota_lleva_los_empatados_en_orden_de_puntos_y_cif():
    """P1 con ``nota_max_candidatos=1``: sale SUR (7) y no NORTE (2); la
    nota sigue diciendo 2."""
    decision, repo = _paso1(_OBRA_P1, _LEIDO, conceptos=_LINEAS_P1, nota_max_candidatos=1)
    _en_revision_r11(decision, repo, _nota_r11(2, f"B1 — {_SUR}"))


def test_f080_r2_dos_pasadas_no_duplican_motivo_ni_nota():
    repo = _RepoConLineas(_LINEAS_H4)
    _paso1(_OBRA_H4, _LEIDO, repo=repo)
    _paso1(_OBRA_H4, _LEIDO, repo=repo)
    assert repo.lista_motivos() == [_MOTIVO]
    assert repo.lineas_notas() == [_NOTA_H4]


def test_f080_r2_la_nota_sustituye_al_aviso_deducido_de_una_pasada_anterior():
    """Un merge que una pasada de antes de F-080 dio a ARIDOS: la nota
    «deducido AUTOMATICAMENTE» se sustituye por la de R11."""
    repo = _RepoConLineas(_LINEAS_H4)
    repo.notas = (
        f"{_nota_deducido('B9', _ARIDOS, 'hormigon,mortero', 3)}\n"
        "otra nota"
    )
    decision, repo = _paso1(_OBRA_H4, _LEIDO, repo=repo)
    assert decision == (None, "deterministic")
    assert repo.lineas_notas() == ["otra nota", _NOTA_H4]
    _sin_deducido(repo)


# ------------------------------------------------------------------ #
# R4 · la familia separa a los empatados, pero un ajeno saca más
# ------------------------------------------------------------------ #
def test_f080_r4_p1_ni_el_empatado_de_7_ni_el_ajeno_de_9():
    decision, repo = _paso1(_OBRA_P1, _LEIDO, conceptos=_LINEAS_P1)
    _en_revision_r11(decision, repo, _nota_r11(2, f"B1 — {_SUR}; B2 — {_NORTE}"))
    _sin_deducido(repo)


# ------------------------------------------------------------------ #
# R5 · sin ganador por puntos: R11 de F-073 sin cambios (P3)
# ------------------------------------------------------------------ #
def test_f080_r5_ajeno_cerca_sin_margen_va_a_revision_como_hoy():
    """SUR (7) frente a ARIDOS (6): margen 1, sin ganador."""
    decision, repo = _paso1(_OBRA_CERCA, _LEIDO, conceptos=_LINEAS_H4)
    _en_revision_r11(decision, repo, _nota_r11(2, f"B1 — {_SUR}; B2 — {_NORTE}"))


def test_f080_r5_p3_dos_empatados_igualados_arriba_van_a_revision_con_todos():
    """P3: B2 y B3 empatan a 7 por familia, B1 queda en 2; nota con los
    tres en orden (-puntos, CIF)."""
    obra = [
        _resumen("B1", "HORMIGONES UNO, S.L.", "GASOLEO A"),
        _resumen("B3", "HORMIGONES TRES, S.L.", "HORMIGON HA-25"),
        _resumen("B2", "HORMIGONES DOS, S.L.", "HORMIGON HM-20"),
        _resumen("B9", _ARIDOS, "HORMIGON HA-25"),
    ]
    decision, repo = _paso1(obra, _LEIDO, conceptos=["HORMIGON HA-25"])
    _en_revision_r11(decision, repo, _nota_r11(
        3, "B2 — HORMIGONES DOS, S.L.; B3 — HORMIGONES TRES, S.L.; B1 — HORMIGONES UNO, S.L.",
    ))


# ------------------------------------------------------------------ #
# R6 · el log del ajeno descartado
# ------------------------------------------------------------------ #
def test_f080_r6_log_del_ajeno_descartado_y_sin_deducido(caplog):
    with caplog.at_level(logging.INFO, logger=modulo.logger.name):
        _paso1(_OBRA_H4, _LEIDO, conceptos=_LINEAS_H4)
    mensajes = _mensajes(caplog)
    [linea] = [m for m in mensajes if "AJENO" in m]
    assert linea == (
        "[header-resolver] proveedor NO deducido por familia+obra: el ganador por "
        "puntos B9 (6 puntos) es AJENO al empate por nombre (2 empatados) obra=0694"
    )
    assert not any("DEDUCIDO por familia+obra" in m for m in mensajes)


def test_f080_r6_el_log_del_ajeno_es_info(caplog):
    with caplog.at_level(logging.INFO, logger=modulo.logger.name):
        _paso1(_OBRA_P1, _LEIDO, conceptos=_LINEAS_P1)
    [registro] = [r for r in caplog.records if "AJENO" in r.getMessage()]
    assert registro.levelno == logging.INFO
    assert "B9 (9 puntos)" in registro.getMessage()


def test_f080_r6_sin_ajeno_ganador_no_sale_el_log(caplog):
    """Sin ganador por puntos (ajeno cerca) no hay ajeno que descartar."""
    with caplog.at_level(logging.INFO, logger=modulo.logger.name):
        _paso1(_OBRA_CERCA, _LEIDO, conceptos=_LINEAS_H4)
    assert not any("AJENO" in m for m in _mensajes(caplog))


# ------------------------------------------------------------------ #
# R7 · el orden de llegada no cambia nada
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(("obra", "lineas"), [(_OBRA_H4, _LINEAS_H4), (_OBRA_P1, _LINEAS_P1)], ids=["H4", "P1"])
@pytest.mark.parametrize("semilla", [1, 2, 3, 4, 5])
def test_f080_r7_misma_decision_y_nota_con_cualquier_orden(obra, lineas, semilla):
    referencia = _paso1(obra, _LEIDO, conceptos=lineas)
    barajada = list(obra)
    random.Random(semilla).shuffle(barajada)
    for orden in (barajada, list(reversed(obra))):
        otra = _paso1(orden, _LEIDO, conceptos=lineas)
        assert otra[0] == referencia[0] == (None, "deterministic")
        assert otra[1].marcas == referencia[1].marcas
        assert otra[1].marcas[0][1] == _nota_r11(2, f"B1 — {_SUR}; B2 — {_NORTE}")


# ------------------------------------------------------------------ #
# R8 · la pertenencia va por la clave de CIF normalizada
# ------------------------------------------------------------------ #
def test_f080_r8_una_grafia_distinta_del_empatado_cuenta_como_empatado():
    """La fila « b1 » (6 puntos) es del mismo CIF que el empatado «B1»:
    gana y se deduce con el CIF de la fila ganadora, como hoy."""
    obra = [
        _resumen("B1", _SUR, "GASOLEO A"),
        _resumen("B2", _NORTE, "GASOLEO A"),
        _resumen(" b1 ", _ARIDOS, "HORMIGON HA-25 MORTERO M-5"),
    ]
    decision, repo = _paso1(obra, _LEIDO, conceptos=_LINEAS_H4)
    assert decision == (" b1 ", "det_familia_obra")
    assert repo.marcas == []
    assert repo.motivos is None
    [nota] = repo.lineas_notas()
    assert nota.startswith(f"{_PREFIJO}  b1  — {_ARIDOS} deducido AUTOMATICAMENTE")


@pytest.mark.parametrize(
    ("cif", "esperado"),
    [("B1", True), (" b1 ", True), ("b-1", True), ("B2", True), ("B9", False), (None, False), ("", False)],
)
def test_f080_r8_es_empatado_por_clave(cif, esperado):
    from application.services.similitud_proveedor import CandidatoNombre, EleccionPorNombre

    eleccion = EleccionPorNombre(
        elegido=None,
        empatados=(CandidatoNombre("B1", _SUR, 1.0), CandidatoNombre("B2", _NORTE, 1.0)),
        segunda=1.0,
        mejor=CandidatoNombre("B1", _SUR, 1.0),
    )
    assert modulo._es_empatado(cif, eleccion) is esperado


def test_f080_r8_sin_empatados_nadie_es_empatado():
    from application.services.similitud_proveedor import EleccionPorNombre

    vacia = EleccionPorNombre(elegido=None, empatados=(), segunda=0.0, mejor=None)
    assert modulo._es_empatado("B1", vacia) is False
    assert modulo._es_empatado(None, vacia) is False


# ------------------------------------------------------------------ #
# R9 · por resolve_merge_document, con empate también en el paso 2
# ------------------------------------------------------------------ #
class _ClienteConGlobal(_ClienteRed):
    """El cliente de F-073 con ``search_proveedores`` = los tres de la obra."""

    def search_proveedores(self):
        return [(r.cif, r.nombre) for r in self.obra]


def test_f080_r9_h4_entero_queda_sin_cif_con_motivo_y_la_nota_del_paso1():
    repo = _RepoConLineas(_LINEAS_H4, nombre=_LEIDO)
    pasada(_ClienteConGlobal(_OBRA_H4), repo)
    assert repo.cif is None
    assert repo.resoluciones == [(None, None, "deterministic")]
    assert repo.review_required is True
    assert repo.lista_motivos() == [_MOTIVO]
    assert repo.lineas_notas() == [_NOTA_H4]


# ------------------------------------------------------------------ #
# R10, R11 · lo que no cambia
# ------------------------------------------------------------------ #
def test_f080_r10_sin_empate_porque_nadie_llega_el_ajeno_sigue_pudiendo_ganar():
    """Leído «ZZZZ»: nadie llega a ``min_score``. ARIDOS (6) frente a los
    de gasóleo (−2): se deduce, como hoy."""
    decision, repo = _paso1(_OBRA_H4, "ZZZZ", conceptos=_LINEAS_H4)
    assert decision == ("B9", "det_familia_obra")
    assert repo.marcas == []
    assert repo.lineas_notas() == [_nota_deducido("B9", _ARIDOS, "hormigon,mortero", 3, leido="ZZZZ")]


def test_f080_r10_sin_empate_y_sin_ganador_la_nota_no_deducible_sin_motivo():
    obra = [_resumen("B1", "ALFA, S.L.", "HORMIGON HA-25"), _resumen("B9", "BETA, S.L.", "HORMIGON HM-20")]
    decision, repo = _paso1(obra, "ZZZZ", conceptos=["HORMIGON HA-25"])
    assert decision == (None, "deterministic")
    assert repo.marcas == []
    assert repo.motivos is None
    [nota] = repo.lineas_notas()
    assert nota.startswith(f"{_PREFIJO} sin CIF: no deducible con seguridad.")


def test_f080_r11_el_atajo_por_nombre_elige_sin_mirar_los_puntos():
    """«HORMIGONES DEL SUR» casa 1,0 con SUR y 0,5 con NORTE: elige por
    nombre aunque ARIDOS tenga más puntos."""
    decision, repo = _paso1(_OBRA_H4, "HORMIGONES DEL SUR", conceptos=_LINEAS_H4)
    assert decision == ("B1", "deterministic")
    assert repo.marcas == []
    assert repo.notas in (None, "")


# ------------------------------------------------------------------ #
# R12 · las reglas de puntos no cambian
# ------------------------------------------------------------------ #
def test_f080_r12_constantes_de_puntos_y_margen_por_defecto():
    assert modulo._PUNTOS_MINIMOS == 3
    assert modulo._MARGEN_MINIMO == 2
    assert modulo._PUNTOS_NOMBRE_MAX == 4
    assert modulo._PUNTOS_POR_FAMILIA == 3
    assert modulo._PENALIZACION_OTRA_FAMILIA == 2
    parametros = inspect.signature(modulo.HeaderResolverService.__init__).parameters
    assert parametros["margen_nombre"].default == 0.25
    # Sin parámetro nuevo para F-080 (D4: sin interruptor). No se fija la
    # lista entera: F-049 toca el constructor en otra rama.
    assert not any("empat" in p or "ajeno" in p for p in parametros)


def test_f080_r12_empatado_sin_familias_frente_a_otra_familia_se_deduce():
    """Penalización: SUR sin familias (4) frente a NORTE de gasóleo (2)."""
    decision, repo = _paso1(_OBRA_PENALIZACION, _LEIDO, conceptos=["HORMIGON HA-25"])
    assert decision == ("B1", "det_familia_obra")
    assert repo.marcas == []
    assert repo.lineas_notas() == [_nota_deducido("B1", _SUR, "-", 2)]
