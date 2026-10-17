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


# ------------------------------------------------------------------ #
# T9 · anotar tras el build (R9, R10)
# ------------------------------------------------------------------ #
def _valorar(lineas, *, contrato=(), puerto=None, sinteticas=()):
    """Normaliza, construye con el builder real y anota: (n, cabecera, registros)."""
    from tests.f027_escenarios import construir_builder

    n = _normalizador(puerto or PuertoFalso()).normalizar(
        envelope=sobre(lineas, contrato=contrato, sinteticas=sinteticas), obra="0678")
    cabecera, registros = construir_builder().build(envelope=n.envelope, existing_document_already_valued=False)
    antes = [(r.review_required, list(r.review_reasons), r.importe_calculado, r.codigo_partida_final,
              r.matched_contrato_line_id, r.partida_action) for r in registros]
    cabecera_antes = (cabecera.review_required, list(cabecera.review_reasons))
    NormalizadorPartidas.anotar(cabecera, registros, n)
    return n, cabecera, registros, antes, cabecera_antes


def _por_merge(registros):
    return {r.merge_line_id: r for r in registros if r.line_kind == "from_albaran"}


def test_f076_r9_normalizada_motivo_y_leida_conservada_sin_revision():
    from tests.f076_sobres import linea_contrato

    _n, cabecera, registros, antes, cabecera_antes = _valorar(
        [(1, "CI.04.18", 501)], contrato=[linea_contrato(501, "CI.4.18")])
    (fila,) = registros
    assert fila.codigo_partida_albaran == "CI.04.18"  # regla 6: lo leído
    assert fila.codigo_partida_final == "CI.4.18"  # la decisión, de la lista
    assert "partida_normalizada:CI.04.18>CI.4.18" in fila.review_reasons
    assert fila.review_required == antes[0][0]
    assert (cabecera.review_required, cabecera.review_reasons) == cabecera_antes


def test_f076_r9_exacta_con_espacios_devuelve_la_leida_sin_motivo():
    _n, _c, registros, antes, _ca = _valorar([(1, " CI.4.18 ")])
    (fila,) = registros
    assert fila.codigo_partida_albaran == " CI.4.18 "
    assert fila.codigo_partida_final == "CI.4.18"
    assert fila.review_reasons == antes[0][1]


def test_f076_r9_exacta_sin_cambios_no_anota():
    _n, cabecera, registros, antes, cabecera_antes = _valorar([(1, "CI.4.18")])
    (fila,) = registros
    assert (fila.codigo_partida_albaran, fila.review_reasons) == ("CI.4.18", antes[0][1])
    assert (cabecera.review_required, cabecera.review_reasons) == cabecera_antes


@pytest.mark.parametrize(
    ("lectura", "puerto", "motivo"),
    [
        ("CI.14.18", None, "partida_fuera_de_lista"),
        ("3.2", None, "partida_fuera_de_lista"),
        ("ci-04-18", PuertoFalso(lista_obra("CI.04.18", "CI.4.18")), "partida_ambigua_en_obra"),
    ],
    ids=["sin_candidata", "no_hoja", "ambigua"],
)
def test_f076_r10_fuera_de_lista_o_ambigua_a_revision(lectura, puerto, motivo):
    _n, cabecera, registros, _antes, _ca = _valorar([(1, lectura), (2, lectura)], puerto=puerto)
    for fila in registros:
        assert fila.codigo_partida_albaran == lectura
        assert motivo in fila.review_reasons
        assert fila.review_required is True
    assert cabecera.review_required is True
    assert cabecera.review_reasons.count(motivo) == 1
    assert "at_least_one_line_requires_review" in cabecera.review_reasons


def test_f076_r10_la_partida_no_cambia():
    _n, _c, registros, antes, _ca = _valorar([(1, "CI.14.18")])
    assert registros[0].codigo_partida_final == antes[0][3]


def test_f076_r9_r10_no_toca_importes_casado_ni_accion():
    from tests.f076_sobres import linea_contrato

    _n, _c, registros, antes, _ca = _valorar(
        [(1, "CI.04.18", 501), (2, "CI.14.18"), (3, None), (4, "ALM")],
        contrato=[linea_contrato(501, "CI.4.18")])
    despues = [(r.importe_calculado, r.codigo_partida_final, r.matched_contrato_line_id, r.partida_action)
               for r in registros]
    assert despues == [a[2:] for a in antes]


def test_f076_r9_lineas_sin_lectura_y_sinteticas_no_se_anotan():
    _n, _c, registros, antes, _ca = _valorar(
        [(1, None), (2, "ALM"), (3, "CI.04.18")], sinteticas=[(3, "recargo")])
    for fila, previo in zip(registros, antes):
        if fila.line_kind != "from_albaran" or fila.merge_line_id in (1, 2):
            assert fila.review_reasons == previo[1]
            assert not any(m.startswith("partida_") for m in fila.review_reasons)


def test_f076_r11_anotar_motivo_de_cabecera_sin_revision_y_sin_duplicar():
    from tests.f027_escenarios import construir_builder

    original = sobre([(1, "CI.04.18")])
    n = NormalizadorPartidas.degradada(original)
    cabecera, registros = construir_builder().build(envelope=n.envelope, existing_document_already_valued=False)
    revision = cabecera.review_required
    NormalizadorPartidas.anotar(cabecera, registros, n)
    NormalizadorPartidas.anotar(cabecera, registros, n)
    assert cabecera.review_reasons.count(MOTIVO_PARTIDAS_NO_DISPONIBLES) == 1
    assert cabecera.review_required is revision
    assert registros[0].codigo_partida_albaran == "CI.04.18"


def test_f076_r9_anotar_dos_veces_no_duplica():
    from tests.f027_escenarios import construir_builder

    n = _normalizador(PuertoFalso()).normalizar(envelope=sobre([(1, "CI.04.18"), (2, "CI.14.18")]), obra="0678")
    cabecera, registros = construir_builder().build(envelope=n.envelope, existing_document_already_valued=False)
    NormalizadorPartidas.anotar(cabecera, registros, n)
    NormalizadorPartidas.anotar(cabecera, registros, n)
    por = _por_merge(registros)
    assert por[1].review_reasons.count("partida_normalizada:CI.04.18>CI.4.18") == 1
    assert por[2].review_reasons.count("partida_fuera_de_lista") == 1
    assert cabecera.review_reasons.count("partida_fuera_de_lista") == 1
