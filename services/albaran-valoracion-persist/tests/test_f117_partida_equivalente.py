# tests/test_f117_partida_equivalente.py
"""F-117 T3 · ``NormalizadorPartidas`` propone la partida equivalente (R13–R23).

- R13: lectura ``fuera_de_lista`` con UNA equivalente ⇒ se valora con su cod
  (la copia del sobre lo lleva en ``codigo_partida_albaran``).
- R14, R15: ``anotar`` devuelve la leída, añade
  ``partida_equivalente:<leída>><cod>`` sin ``partida_fuera_de_lista`` y manda
  la línea y la cabecera a revisión (no bloqueante).
- R16: dos o más ⇒ como hoy y ``partida_equivalente_ambigua:<c1>,<c2>…``.
- R17–R23: ninguna equivalente, interruptores, sin lista, sin duplicar, log,
  líneas sin lectura.

Puerto falso y builder real (``tests/f027_escenarios.py``): sin red ni BBDD.
"""
from __future__ import annotations

import logging

import pytest
from application.services import normalizador_partidas as modulo
from application.services.normalizador_partidas import NormalizacionSobre, NormalizadorPartidas
from tests.f076_sobres import PuertoFalso, leidas, linea_contrato, lista_obra, sobre

#: La 0719 reducida: letra (CI.03A.8), sufijo (02.04.01.07) y hojas sin letra.
LISTA_0719 = lista_obra("CI.03A.8", "CI.1.8", "CI.4.8", "CI.4.18", "02.04.01.07", obra="0719")
#: La ambigüedad de la 0459: CI.03A.8 y CI.03P.8.
LISTA_0459 = lista_obra("CI.03A.8", "CI.03P.8", "CI.4.8", obra="0459")


def _normalizador(puerto=None, *, activo=True, equivalente=True) -> NormalizadorPartidas:
    return NormalizadorPartidas(
        partidas=puerto if puerto is not None else PuertoFalso(LISTA_0719),
        alm_codigo_partida="ALM", activo=activo, equivalente=equivalente,
    )


def _valorar(lineas, *, contrato=(), puerto=None, equivalente=True, activo=True):
    """Normaliza, construye con el builder real y anota: (n, cabecera, registros)."""
    from tests.f027_escenarios import construir_builder

    n = _normalizador(puerto, equivalente=equivalente, activo=activo).normalizar(
        envelope=sobre(lineas, contrato=contrato), obra="0719")
    cabecera, registros = construir_builder().build(envelope=n.envelope, existing_document_already_valued=False)
    NormalizadorPartidas.anotar(cabecera, registros, n)
    return n, cabecera, registros


def _por_merge(registros):
    return {r.merge_line_id: r for r in registros if r.line_kind == "from_albaran"}


class _Espia:
    """Sustituye a ``equivalentes_partida`` en el módulo y apunta las lecturas."""

    def __init__(self, real):
        self.real = real
        self.lecturas = []

    def __call__(self, lista, lectura, alm):
        self.lecturas.append(lectura)
        return self.real(lista, lectura, alm)


@pytest.fixture
def espia(monkeypatch):
    e = _Espia(modulo.equivalentes_partida)
    monkeypatch.setattr(modulo, "equivalentes_partida", e)
    return e


def _prohibida(*_a, **_k):
    raise AssertionError("no se debe buscar equivalente")


# ------------------------------------------------------------------ #
# R13 · una equivalente ⇒ se valora con ella
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(("lectura", "cod"), [("CI.03.08", "CI.03A.8"), ("04.01.07", "02.04.01.07")],
                         ids=["letra", "sufijo"])
def test_f117_r13_una_equivalente_se_aplica_en_la_copia(lectura, cod):
    original = sobre([(1, lectura), (2, "CI.04.18"), (3, "CI.14.18")])
    copia_json = original.model_dump_json()
    n = _normalizador().normalizar(envelope=original, obra="0719")
    assert leidas(n.envelope) == {1: cod, 2: "CI.4.18", 3: "CI.14.18"}
    assert n.equivalencias == {1: (cod,)}
    assert n.por_linea[1].motivo == "fuera_de_lista" and n.por_linea[1].leida == lectura
    assert original.model_dump_json() == copia_json
    assert n.envelope is not original


def test_f117_r13_solo_equivalentes_tambien_copia():
    original = sobre([(1, "CI.03.08")])
    n = _normalizador().normalizar(envelope=original, obra="0719")
    assert n.envelope is not original
    assert leidas(n.envelope) == {1: "CI.03A.8"}
    assert leidas(original) == {1: "CI.03.08"}


def test_f117_r13_la_regla_casa_con_la_linea_de_contrato_de_esa_partida():
    _n, _c, registros = _valorar([(1, "CI.03.08", 501)], contrato=[linea_contrato(501, "CI.03A.8")])
    (fila,) = registros
    assert fila.partida_action == "existing_matched"
    assert fila.matched_contrato_line_id == 501
    assert fila.codigo_partida_final == "CI.03A.8"


def test_f117_r13_por_defecto_apagada():
    """Quien construye el normalizador como en F-076 (sin ``equivalente``) no cambia."""
    n = NormalizadorPartidas(partidas=PuertoFalso(LISTA_0719), alm_codigo_partida="ALM", activo=True).normalizar(
        envelope=sobre([(1, "CI.03.08")]), obra="0719")
    assert leidas(n.envelope) == {1: "CI.03.08"}
    assert n.equivalencias == {}


# ------------------------------------------------------------------ #
# R14, R15 · rastro y revisión
# ------------------------------------------------------------------ #
def test_f117_r14_r15_anotar_una_equivalente():
    _n, cabecera, registros = _valorar([(1, "CI.03.08")])
    (fila,) = registros
    assert fila.codigo_partida_albaran == "CI.03.08"  # leída ≠ decisión
    assert fila.codigo_partida_final == "CI.03A.8"
    assert "partida_equivalente:CI.03.08>CI.03A.8" in fila.review_reasons
    assert "partida_fuera_de_lista" not in fila.review_reasons
    assert fila.review_required is True
    assert cabecera.review_required is True
    assert "partida_equivalente:CI.03.08>CI.03A.8" in cabecera.review_reasons
    assert "at_least_one_line_requires_review" in cabecera.review_reasons
    assert "partida_fuera_de_lista" not in cabecera.review_reasons


def test_f117_r14_la_leida_sin_espacios_exteriores_en_el_motivo():
    _n, _c, registros = _valorar([(1, "  CI.03.08 ")])
    (fila,) = registros
    assert fila.codigo_partida_albaran == "  CI.03.08 "
    assert "partida_equivalente:CI.03.08>CI.03A.8" in fila.review_reasons


def test_f117_r14_prefijos_declarados():
    assert modulo.PREFIJO_PARTIDA_EQUIVALENTE == "partida_equivalente:"
    assert modulo.PREFIJO_EQUIVALENTE_AMBIGUA == "partida_equivalente_ambigua:"


def test_f117_r15_solo_la_linea_equivalente_va_a_revision():
    _n, _cabecera, registros = _valorar([(1, "CI.03.08"), (2, "CI.4.18")])
    por = _por_merge(registros)
    assert por[1].review_required is True
    assert not any(m.startswith("partida_") for m in por[2].review_reasons)


# ------------------------------------------------------------------ #
# R16 · dos o más ⇒ revisión con las candidatas, sin tocar el sobre
# ------------------------------------------------------------------ #
def test_f117_r16_ambigua_no_toca_el_sobre():
    original = sobre([(1, "CI.03.08")])
    n = _normalizador(PuertoFalso(LISTA_0459)).normalizar(envelope=original, obra="0459")
    assert n.envelope is original
    assert n.equivalencias == {1: ("CI.03A.8", "CI.03P.8")}


def test_f117_r16_ambigua_a_revision_con_las_candidatas():
    _n, cabecera, registros = _valorar([(1, "CI.03.08")], puerto=PuertoFalso(LISTA_0459))
    (fila,) = registros
    assert fila.codigo_partida_albaran == "CI.03.08"
    assert fila.codigo_partida_final == "CI.03.08"
    assert "partida_fuera_de_lista" in fila.review_reasons
    assert "partida_equivalente_ambigua:CI.03A.8,CI.03P.8" in fila.review_reasons
    assert not any(m.startswith("partida_equivalente:") for m in fila.review_reasons)
    assert fila.review_required is True and cabecera.review_required is True
    assert "partida_fuera_de_lista" in cabecera.review_reasons


@pytest.mark.parametrize(
    ("n_hojas", "esperado"),
    [(5, "CI.03A.8,CI.03B.8,CI.03C.8,CI.03D.8,CI.03E.8"),
     (6, "CI.03A.8,CI.03B.8,CI.03C.8,CI.03D.8,CI.03E.8,+1"),
     (7, "CI.03A.8,CI.03B.8,CI.03C.8,CI.03D.8,CI.03E.8,+2")],
    ids=["cinco", "seis", "siete"],
)
def test_f117_r16_a_lo_sumo_cinco_cods(n_hojas, esperado):
    lista = lista_obra(*(f"CI.03{letra}.8" for letra in "ABCDEFG"[:n_hojas]))
    _n, _c, registros = _valorar([(1, "CI.03.08")], puerto=PuertoFalso(lista))
    (fila,) = registros
    assert f"partida_equivalente_ambigua:{esperado}" in fila.review_reasons


# ------------------------------------------------------------------ #
# R17 · ninguna equivalente ⇒ exactamente como hoy
# ------------------------------------------------------------------ #
def test_f117_r17_sin_equivalente_como_hoy():
    lineas = [(1, "CI.14.18"), (2, "CI.04.18"), (3, None)]
    n_con, cab_con, lin_con = _valorar(lineas)
    n_sin, cab_sin, lin_sin = _valorar(lineas, equivalente=False)
    assert [vars(r) for r in lin_con] == [vars(r) for r in lin_sin]
    assert (cab_con.review_required, cab_con.review_reasons) == (cab_sin.review_required, cab_sin.review_reasons)
    assert n_con.equivalencias == {}
    assert leidas(n_con.envelope) == leidas(n_sin.envelope)


# ------------------------------------------------------------------ #
# R18 · nunca vacía, almacén ni algo que no sea un cod de la lista
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("lectura", ["CI.03.08", "04.01.07", "CI.3.18", "CI.03.04"])
def test_f117_r18_lo_aplicado_es_un_cod_de_la_lista(lectura):
    n = _normalizador().normalizar(envelope=sobre([(1, lectura)]), obra="0719")
    (aplicado,) = leidas(n.envelope).values()
    assert aplicado == lectura or aplicado in LISTA_0719.codigos
    for cods in n.equivalencias.values():
        assert set(cods) <= set(LISTA_0719.codigos)


# ------------------------------------------------------------------ #
# R19 · PARTIDA_EQUIVALENTE_ENABLED=false ⇒ como hoy, sin llamar
# ------------------------------------------------------------------ #
def test_f117_r19_apagada_no_llama_y_valora_como_hoy(monkeypatch):
    lineas = [(1, "CI.03.08"), (2, "04.01.07")]
    _n_hoy, cab_hoy, lin_hoy = _valorar(lineas, equivalente=False)
    monkeypatch.setattr(modulo, "equivalentes_partida", _prohibida)
    n, cabecera, registros = _valorar(lineas, equivalente=False)
    assert n.equivalencias == {}
    assert [vars(r) for r in registros] == [vars(r) for r in lin_hoy]
    assert cabecera.review_reasons == cab_hoy.review_reasons
    for fila in registros:
        assert "partida_fuera_de_lista" in fila.review_reasons


def test_f117_r19_ajuste_por_defecto_encendido(monkeypatch):
    from config.settings import Settings

    monkeypatch.delenv("PARTIDA_EQUIVALENTE_ENABLED", raising=False)
    assert Settings(_env_file=None, PG_USER="u", PG_PASSWORD="p", SCHEMA_DRIFT_CHECK_ENABLED="false").partida_equivalente_enabled is True
    monkeypatch.setenv("PARTIDA_EQUIVALENTE_ENABLED", "false")
    assert Settings(_env_file=None, PG_USER="u", PG_PASSWORD="p", SCHEMA_DRIFT_CHECK_ENABLED="false").partida_equivalente_enabled is False


@pytest.mark.parametrize(("valor", "esperado"), [(None, True), ("false", False), ("true", True)])
def test_f117_r19_el_cableado_pasa_el_interruptor(monkeypatch, valor, esperado):
    from config.settings import Settings
    from interface_adapters.composition import construir_normalizador_partidas

    for nombre in ("SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE",
                   "PARTIDAS_OBRA_NORMALIZAR_ENABLED", "PARTIDA_EQUIVALENTE_ENABLED"):
        monkeypatch.delenv(nombre, raising=False)
    if valor is not None:
        monkeypatch.setenv("PARTIDA_EQUIVALENTE_ENABLED", valor)
    ajustes = Settings(_env_file=None, PG_USER="u", PG_PASSWORD="p", SCHEMA_DRIFT_CHECK_ENABLED="false")
    assert construir_normalizador_partidas(ajustes)._equivalente is esperado


# ------------------------------------------------------------------ #
# R20 · sin F-076 encendido o sin lista, no se buscan
# ------------------------------------------------------------------ #
def test_f117_r20_normalizar_apagado_no_busca(monkeypatch):
    monkeypatch.setattr(modulo, "equivalentes_partida", _prohibida)
    original = sobre([(1, "CI.03.08")])
    n = _normalizador(activo=False).normalizar(envelope=original, obra="0719")
    assert n == NormalizacionSobre(envelope=original)


@pytest.mark.parametrize("obra", [None, "0719"], ids=["sin_obra", "sin_lista"])
def test_f117_r20_sin_lista_no_busca(monkeypatch, obra):
    monkeypatch.setattr(modulo, "equivalentes_partida", _prohibida)
    original = sobre([(1, "CI.03.08")])
    n = _normalizador(PuertoFalso(None)).normalizar(envelope=original, obra=obra)
    assert n == NormalizadorPartidas.degradada(original)
    assert n.equivalencias == {}


# ------------------------------------------------------------------ #
# R21 · anotar dos veces no duplica
# ------------------------------------------------------------------ #
def test_f117_r21_anotar_dos_veces_no_duplica():
    n, cabecera, registros = _valorar([(1, "CI.03.08"), (2, "CI.03.08")])
    _n2, cab_amb, reg_amb = _valorar([(1, "CI.03.08")], puerto=PuertoFalso(LISTA_0459))
    NormalizadorPartidas.anotar(cabecera, registros, n)
    NormalizadorPartidas.anotar(cab_amb, reg_amb, _n2)
    for fila in registros:
        assert fila.review_reasons.count("partida_equivalente:CI.03.08>CI.03A.8") == 1
        assert fila.codigo_partida_albaran == "CI.03.08"
    assert cabecera.review_reasons.count("partida_equivalente:CI.03.08>CI.03A.8") == 1
    assert cabecera.review_reasons.count("at_least_one_line_requires_review") == 1
    (amb,) = reg_amb
    assert amb.review_reasons.count("partida_equivalente_ambigua:CI.03A.8,CI.03P.8") == 1
    assert amb.review_reasons.count("partida_fuera_de_lista") == 1


# ------------------------------------------------------------------ #
# R22 · el log INFO cuenta equivalentes y ambiguas
# ------------------------------------------------------------------ #
def test_f117_r22_log_info(caplog):
    lista = lista_obra("CI.03A.8", "CI.03A.9", "CI.03P.9", "02.04.01.07")
    with caplog.at_level(logging.INFO, logger="application.services.normalizador_partidas"):
        _normalizador(PuertoFalso(lista)).normalizar(
            envelope=sobre([(1, "CI.03.08"), (2, "04.01.07"), (3, "CI.03.09"), (4, "CI.14.18")]), obra="0719")
    (mensaje,) = [r.getMessage() for r in caplog.records if "[partidas-obra]" in r.getMessage()]
    assert "equivalentes=2" in mensaje and "ambiguas=1" in mensaje
    assert "lecturas=4" in mensaje and "cambiadas=2" in mensaje


def test_f117_r22_log_sin_equivalentes(caplog):
    with caplog.at_level(logging.INFO, logger="application.services.normalizador_partidas"):
        _normalizador().normalizar(envelope=sobre([(1, "CI.14.18")]), obra="0719")
    (mensaje,) = [r.getMessage() for r in caplog.records if "[partidas-obra]" in r.getMessage()]
    assert "equivalentes=0" in mensaje and "ambiguas=0" in mensaje


# ------------------------------------------------------------------ #
# R23 · solo se mira la lectura fuera de lista
# ------------------------------------------------------------------ #
def test_f117_r23_solo_lecturas_fuera_de_lista(espia):
    original = sobre([(1, None), (2, ""), (3, "ALM"), (4, "CI.4.18"), (5, "CI.04.18"), (6, "CI.03.08"),
                      (7, "CI.14.18")])
    n = _normalizador().normalizar(envelope=original, obra="0719")
    assert espia.lecturas == ["CI.03.08", "CI.14.18"]
    assert leidas(n.envelope) == {1: None, 2: "", 3: "ALM", 4: "CI.4.18", 5: "CI.4.18", 6: "CI.03A.8",
                                  7: "CI.14.18"}


def test_f117_r23_lineas_sin_lectura_no_se_anotan():
    _n, _c, registros = _valorar([(1, None), (2, "ALM"), (3, "CI.03.08")])
    por = _por_merge(registros)
    for mid in (1, 2):
        assert not any(m.startswith("partida_") for m in por[mid].review_reasons)
    assert por[1].codigo_partida_albaran is None and por[2].codigo_partida_albaran == "ALM"


def test_f117_t4_normalizacion_lleva_equivalencias_inmutable():
    n = NormalizacionSobre(envelope=sobre([(1, "CI.03.08")]))
    assert n.equivalencias == {}
    with pytest.raises(AttributeError):
        n.equivalencias = {}  # type: ignore[misc]
