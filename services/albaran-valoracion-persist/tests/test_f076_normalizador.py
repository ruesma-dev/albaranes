# tests/test_f076_normalizador.py
"""F-076 T8–T9 · ``NormalizadorPartidas``: normalizar el sobre y anotar.

- R7: con el interruptor encendido, cada línea con lectura se resuelve contra
  la lista de la obra (R5 de comun) y el sobre normalizado es una COPIA; un
  sobre sin lecturas no consulta.
- R11: sin lista ⇒ sobre intacto, WARNING con obra y causa y motivo de cabecera
  ``partidas_obra_no_disponibles`` (sin revisión).
- R12: interruptor apagado ⇒ ni consulta ni cambio.
- R13: lectura vacía o ``ALM`` ⇒ no se toca.

Puerto falso: sin red ni BBDD.
"""
from __future__ import annotations

import logging

import pytest
from application.services.normalizador_partidas import (
    MOTIVO_PARTIDAS_NO_DISPONIBLES,
    NormalizacionSobre,
    NormalizadorPartidas,
)
from ruesma_comun.sigrid import ResolucionPartida
from tests.f076_sobres import LISTA_0678, PuertoFalso, leidas, lista_obra, sobre


def _normalizador(puerto=None, *, activo=True) -> NormalizadorPartidas:
    return NormalizadorPartidas(partidas=puerto, alm_codigo_partida="ALM", activo=activo)


# ------------------------------------------------------------------ #
# R7 · normaliza contra la lista de la obra, sin mutar el original
# ------------------------------------------------------------------ #
def test_f076_r7_normaliza_cada_linea_con_lectura():
    original = sobre([(1, "CI.04.18"), (2, "CI.03A.02"), (3, "CI.4.18"), (4, "CI.14.18"), (5, "ci.4.18")])
    puerto = PuertoFalso()
    n = _normalizador(puerto).normalizar(envelope=original, obra="0678")

    assert puerto.pedidas == ["0678"]
    assert leidas(n.envelope) == {1: "CI.4.18", 2: "CI.03A.2", 3: "CI.4.18", 4: "CI.14.18", 5: "CI.4.18"}
    assert n.por_linea == {
        1: ResolucionPartida("CI.4.18", "normalizada", "CI.04.18"),
        2: ResolucionPartida("CI.03A.2", "normalizada", "CI.03A.02"),
        3: ResolucionPartida("CI.4.18", "exacta", "CI.4.18"),
        4: ResolucionPartida("CI.14.18", "fuera_de_lista", "CI.14.18"),
        5: ResolucionPartida("CI.4.18", "normalizada", "ci.4.18"),
    }
    assert n.motivos_cabecera == ()


def test_f076_r7_el_sobre_original_no_se_muta():
    original = sobre([(1, "CI.04.18")])
    copia_json = original.model_dump_json()
    n = _normalizador(PuertoFalso()).normalizar(envelope=original, obra="0678")
    assert original.model_dump_json() == copia_json
    assert leidas(original) == {1: "CI.04.18"}
    assert n.envelope is not original
    assert n.envelope.context.lineas_albaran[0] is not original.context.lineas_albaran[0]


def test_f076_r7_solo_cambia_la_partida():
    original = sobre([(1, "CI.04.18"), (2, "CI.4.18")])
    n = _normalizador(PuertoFalso()).normalizar(envelope=original, obra="0678")
    antes = original.model_dump()
    despues = n.envelope.model_dump()
    antes["context"]["lineas_albaran"][0]["codigo_partida_albaran"] = "CI.4.18"
    assert despues == antes


def test_f076_r7_sin_cambios_devuelve_el_mismo_sobre():
    original = sobre([(1, "CI.4.18"), (2, "CI.14.18")])
    n = _normalizador(PuertoFalso()).normalizar(envelope=original, obra="0678")
    assert n.envelope is original


def test_f076_r7_sobre_sin_lecturas_no_consulta():
    puerto = PuertoFalso()
    original = sobre([(1, None), (2, "  "), (3, "ALM"), (4, " alm ")])
    n = _normalizador(puerto).normalizar(envelope=original, obra="0678")
    assert puerto.pedidas == []
    assert n == NormalizacionSobre(envelope=original, por_linea={}, motivos_cabecera=())
    assert _normalizador(puerto).necesita_obra(original) is False


def test_f076_r7_necesita_obra_solo_con_lecturas_y_encendido():
    assert _normalizador(PuertoFalso()).necesita_obra(sobre([(1, "CI.04.18")])) is True
    assert _normalizador(PuertoFalso(), activo=False).necesita_obra(sobre([(1, "CI.04.18")])) is False
    assert _normalizador(None).necesita_obra(sobre([(1, "CI.04.18")])) is True  # R11: para el WARNING


def test_f076_r7_choque_con_no_hoja_no_se_normaliza():
    n = _normalizador(PuertoFalso()).normalizar(envelope=sobre([(1, "3.2")]), obra="0678")
    assert leidas(n.envelope) == {1: "3.2"}
    assert n.por_linea[1].motivo == "fuera_de_lista"


def test_f076_r7_ambigua_no_se_toca():
    puerto = PuertoFalso(lista_obra("CI.04.18", "CI.4.18"))
    n = _normalizador(puerto).normalizar(envelope=sobre([(1, "ci-04-18")]), obra="0678")
    assert leidas(n.envelope) == {1: "ci-04-18"}
    assert n.por_linea[1].motivo == "ambigua"


# ------------------------------------------------------------------ #
# R11 · sin lista: como hoy, WARNING y motivo de cabecera
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("puerto", "obra", "causa"),
    [
        (None, "0678", "sin configuración de sigrid-api"),
        (PuertoFalso(None), "0678", "sin lista"),
        (PuertoFalso(), None, "obra vacía"),
        (PuertoFalso(), "   ", "obra vacía"),
    ],
    ids=["sin_configuracion", "sin_lista", "obra_none", "obra_blanca"],
)
def test_f076_r11_sin_lista_sobre_intacto_warning_y_motivo(caplog, puerto, obra, causa):
    original = sobre([(1, "CI.04.18")])
    with caplog.at_level(logging.WARNING, logger="application.services.normalizador_partidas"):
        n = _normalizador(puerto).normalizar(envelope=original, obra=obra)
    assert n == NormalizacionSobre(envelope=original, por_linea={},
                                   motivos_cabecera=(MOTIVO_PARTIDAS_NO_DISPONIBLES,))
    assert MOTIVO_PARTIDAS_NO_DISPONIBLES == "partidas_obra_no_disponibles"
    (aviso,) = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert causa in aviso and "doc-f076" in aviso
    assert f"obra={(obra or '').strip() or None}" in aviso


def test_f076_r11_obra_vacia_no_consulta():
    puerto = PuertoFalso()
    _normalizador(puerto).normalizar(envelope=sobre([(1, "CI.04.18")]), obra="  ")
    assert puerto.pedidas == []


def test_f076_r11_degradada():
    original = sobre([(1, "CI.04.18")])
    assert NormalizadorPartidas.degradada(original) == NormalizacionSobre(
        envelope=original, por_linea={}, motivos_cabecera=(MOTIVO_PARTIDAS_NO_DISPONIBLES,))


# ------------------------------------------------------------------ #
# R12 · interruptor apagado
# ------------------------------------------------------------------ #
def test_f076_r12_apagado_ni_consulta_ni_cambia():
    puerto = PuertoFalso()
    original = sobre([(1, "CI.04.18")])
    n = _normalizador(puerto, activo=False).normalizar(envelope=original, obra="0678")
    assert puerto.pedidas == []
    assert n == NormalizacionSobre(envelope=original, por_linea={}, motivos_cabecera=())


def test_f076_r12_apagado_sin_puerto_tampoco_avisa(caplog):
    with caplog.at_level(logging.WARNING):
        n = _normalizador(None, activo=False).normalizar(envelope=sobre([(1, "CI.04.18")]), obra="0678")
    assert n.motivos_cabecera == ()
    assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


# ------------------------------------------------------------------ #
# R13 · vacía o ALM: no se toca (F-051 intacto)
# ------------------------------------------------------------------ #
def test_f076_r13_vacia_y_alm_no_se_tocan():
    original = sobre([(1, None), (2, ""), (3, "ALM"), (4, "CI.04.18"), (5, "alm")])
    n = _normalizador(PuertoFalso()).normalizar(envelope=original, obra="0678")
    assert leidas(n.envelope) == {1: None, 2: "", 3: "ALM", 4: "CI.4.18", 5: "alm"}
    assert set(n.por_linea) == {4}


def test_f076_r13_alm_configurable():
    n = NormalizadorPartidas(partidas=PuertoFalso(), alm_codigo_partida="ACOPIO", activo=True).normalizar(
        envelope=sobre([(1, "acopio"), (2, "ALM")]), obra="0678")
    assert set(n.por_linea) == {2}
    assert n.por_linea[2].motivo == "fuera_de_lista"
    assert LISTA_0678.obra == "0678"
