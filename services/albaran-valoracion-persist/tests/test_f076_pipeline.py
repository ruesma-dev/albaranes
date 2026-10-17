# tests/test_f076_pipeline.py
"""F-076 T10 · ``RunValuationPipeline`` normaliza la partida antes de valorar.

- R7: tras recibir el sobre de sv5 (también con ``force``) y ANTES de IA4, de la
  rama ``no_contract`` y de las reglas, sv6 lee la obra del merge, pide la lista
  y resuelve la lectura de cada línea.
- R8: con ``exacta``/``normalizada`` las reglas trabajan con la partida de la
  lista: casan con la línea de contrato de esa partida, crean la derivada con
  ella y la heredan las sintéticas.
- R14: el sobre persistido es el que se valoró.
- Una excepción al normalizar ⇒ WARNING y el sobre original con
  ``partidas_obra_no_disponibles``: la valoración nunca falla por la lista.

Builder real (``tests/f027_escenarios.py``), sv5, IA4 y repositorio falsos.
"""
from __future__ import annotations

import json
import logging

import pytest
from application.pipelines.run_valuation_pipeline import (
    RunValuationPipeline,
    RunValuationRequest,
)
from application.services.normalizador_partidas import NormalizadorPartidas
from domain.ports.valuation_repository import (
    ExistingValuationSummary,
    PersistedValuation,
)
from tests.f027_escenarios import construir_builder
from tests.f076_sobres import PuertoFalso, PuertoRoto, leidas, linea_contrato, sobre


class _Repositorio:
    def __init__(self, *, obra="0678", existente=False, rompe_obra=False):
        self.obra = obra
        self.existente = existente
        self.rompe_obra = rompe_obra
        self.guardados = []
        self.obras_pedidas = []

    def get_by_document_id(self, *, document_id):
        if not self.existente:
            return None
        return ExistingValuationSummary(
            valuation_id="val-viejo", document_id=document_id, contrato_codigo=None, status="ok",
            total_valorado=0.0, total_lines=1, review_required=False, created_at_utc="x", updated_at_utc=None,
        )

    def obra_del_documento(self, *, document_id):
        self.obras_pedidas.append(document_id)
        if self.rompe_obra:
            raise RuntimeError("BBDD caída")
        return self.obra

    def replace_valuation(self, *, header, lines):
        self.guardados.append((header, list(lines)))
        return PersistedValuation(
            valuation_id="val-1", document_id=header.document_id, status=header.status,
            total_valorado=header.total_valorado, total_lines=header.total_lines,
            review_required=header.review_required,
        )


class _Sv5:
    def __init__(self, envelope):
        self.envelope = envelope

    def value(self, *, document_id, codigo_contrato):
        return self.envelope


class _Ia4:
    """IA4 falsa: registra lo que recibe y no concilia nada."""

    def __init__(self):
        self.pendientes = None

    def conciliar(self, *, document_id, lineas_no_casadas, lineas_contrato):
        self.pendientes = lineas_no_casadas
        return {"conciliaciones": []}


def _pipeline(envelope, repo, *, puerto=None, activo=True, ia4=None, normalizador=True):
    return RunValuationPipeline(
        ia_client=_Sv5(envelope), repository=repo, builder=construir_builder(), conciliacion_client=ia4,
        normalizador=(NormalizadorPartidas(partidas=puerto if puerto is not None else PuertoFalso(),
                                           alm_codigo_partida="ALM", activo=activo)
                      if normalizador else None),
    )


def _guardado(repo):
    ((cabecera, lineas),) = repo.guardados
    return cabecera, lineas


# ------------------------------------------------------------------ #
# R7, R8 · la línea casa con la de contrato de la partida de la lista
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("force", [False, True])
def test_f076_r8_casa_con_la_linea_de_contrato_de_la_partida_normalizada(force):
    envelope = sobre([(1, "CI.04.18", 501)], contrato=[linea_contrato(501, "CI.4.18")])
    repo = _Repositorio(existente=force)
    _pipeline(envelope, repo).run(RunValuationRequest(document_id="doc-f076", force=force))

    cabecera, (fila,) = _guardado(repo)
    assert repo.obras_pedidas == ["doc-f076"]
    assert fila.partida_action == "existing_matched"
    assert fila.matched_contrato_line_id == 501
    assert fila.codigo_partida_final == "CI.4.18"
    assert fila.codigo_partida_albaran == "CI.04.18"
    assert "partida_normalizada:CI.04.18>CI.4.18" in fila.review_reasons
    assert "partida_fuera_de_lista" not in cabecera.review_reasons


def test_f076_r8_sin_f076_la_misma_linea_sale_nueva():
    """La regresión que arregla F-076: sin normalizar, ``CI.04.18`` ≠ ``CI.4.18``."""
    envelope = sobre([(1, "CI.04.18", 501)], contrato=[linea_contrato(501, "CI.4.18")])
    repo = _Repositorio()
    _pipeline(envelope, repo, normalizador=False).run(RunValuationRequest(document_id="doc-f076"))
    _cabecera, (fila,) = _guardado(repo)
    assert fila.partida_action == "new_line_created"
    assert fila.codigo_partida_final == "CI.04.18"
    assert repo.obras_pedidas == []


def test_f076_r8_sin_linea_de_contrato_la_derivada_lleva_la_de_la_lista():
    envelope = sobre([(1, "CI.04.18")], contrato=[linea_contrato(501, "01.05.07", descripcion="MORTERO")])
    repo = _Repositorio()
    _pipeline(envelope, repo).run(RunValuationRequest(document_id="doc-f076"))
    _cabecera, (fila,) = _guardado(repo)
    assert fila.partida_action == "new_line_created"
    assert fila.codigo_partida_final == "CI.4.18"
    assert fila.derived_contrato_line_record is not None
    assert fila.derived_contrato_line_record.codigo_partida == "CI.4.18"
    assert fila.codigo_partida_albaran == "CI.04.18"


def test_f076_r8_la_sintetica_hereda_la_de_la_lista():
    envelope = sobre([(1, "CI.04.18", 501)], contrato=[linea_contrato(501, "CI.4.18")],
                     sinteticas=[(1, "recargo")])
    repo = _Repositorio()
    _pipeline(envelope, repo).run(RunValuationRequest(document_id="doc-f076"))
    _cabecera, lineas = _guardado(repo)
    (sintetica,) = [r for r in lineas if r.line_kind == "synthetic_modifier"]
    assert sintetica.codigo_partida_final == "CI.4.18"
    assert not any(m.startswith("partida_normalizada") for m in sintetica.review_reasons)


def test_f076_r7_ia4_recibe_la_partida_normalizada():
    envelope = sobre([(1, "CI.04.18")], contrato=[linea_contrato(501, "CI.4.18")])
    ia4 = _Ia4()
    _pipeline(envelope, _Repositorio(), ia4=ia4).run(RunValuationRequest(document_id="doc-f076"))
    assert [p["codigo_partida"] for p in ia4.pendientes] == ["CI.4.18"]


def test_f076_r7_sin_lecturas_no_lee_la_obra_ni_consulta():
    puerto = PuertoFalso()
    repo = _Repositorio()
    _pipeline(sobre([(1, None), (2, "ALM")]), repo, puerto=puerto).run(RunValuationRequest(document_id="doc-f076"))
    assert repo.obras_pedidas == [] and puerto.pedidas == []
    cabecera, _lineas = _guardado(repo)
    assert "partidas_obra_no_disponibles" not in cabecera.review_reasons


def test_f076_r12_apagado_no_lee_la_obra():
    repo = _Repositorio()
    puerto = PuertoFalso()
    _pipeline(sobre([(1, "CI.04.18")]), repo, puerto=puerto, activo=False).run(
        RunValuationRequest(document_id="doc-f076"))
    assert repo.obras_pedidas == [] and puerto.pedidas == []
    _cabecera, (fila,) = _guardado(repo)
    assert fila.codigo_partida_final == "CI.04.18"


def test_f076_r10_fuera_de_lista_a_revision_en_la_cabecera():
    repo = _Repositorio()
    _pipeline(sobre([(1, "CI.14.18")]), repo).run(RunValuationRequest(document_id="doc-f076"))
    cabecera, (fila,) = _guardado(repo)
    assert fila.codigo_partida_final == "CI.14.18"
    assert fila.review_required is True and "partida_fuera_de_lista" in fila.review_reasons
    assert cabecera.review_required is True and "partida_fuera_de_lista" in cabecera.review_reasons


# ------------------------------------------------------------------ #
# R14 · el sobre persistido es el que se valoró
# ------------------------------------------------------------------ #
def test_f076_r14_el_sobre_persistido_es_el_normalizado():
    envelope = sobre([(1, "CI.04.18", 501)], contrato=[linea_contrato(501, "CI.4.18")])
    repo = _Repositorio()
    _pipeline(envelope, repo).run(RunValuationRequest(document_id="doc-f076"))
    cabecera, _lineas = _guardado(repo)
    persistido = json.loads(cabecera.raw_ia_envelope_json)
    assert [ln["codigo_partida_albaran"] for ln in persistido["context"]["lineas_albaran"]] == ["CI.4.18"]
    assert leidas(envelope) == {1: "CI.04.18"}  # el de sv5, intacto


def test_f076_r14_no_contract_persiste_el_sobre_normalizado():
    envelope = sobre([(1, "CI.04.18")], status="no_contract")
    repo = _Repositorio()
    _pipeline(envelope, repo).run(RunValuationRequest(document_id="doc-f076"))
    cabecera, lineas = _guardado(repo)
    assert lineas == [] and cabecera.status == "no_contract"
    persistido = json.loads(cabecera.raw_ia_envelope_json)
    assert persistido["context"]["lineas_albaran"][0]["codigo_partida_albaran"] == "CI.4.18"
    assert repo.obras_pedidas == ["doc-f076"]


# ------------------------------------------------------------------ #
# R11 · la valoración nunca falla por la lista
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("repo", "puerto"),
    [(_Repositorio(rompe_obra=True), PuertoFalso()), (_Repositorio(), PuertoRoto())],
    ids=["obra_falla", "puerto_lanza"],
)
def test_f076_r11_una_excepcion_al_normalizar_valora_con_el_original(caplog, repo, puerto):
    envelope = sobre([(1, "CI.04.18", 501)], contrato=[linea_contrato(501, "CI.4.18")])
    with caplog.at_level(logging.WARNING, logger="application.pipelines.run_valuation_pipeline"):
        resultado = _pipeline(envelope, repo, puerto=puerto).run(RunValuationRequest(document_id="doc-f076"))
    assert resultado.duplicate is False
    cabecera, (fila,) = _guardado(repo)
    assert fila.codigo_partida_final == "CI.04.18" and fila.partida_action == "new_line_created"
    assert "partidas_obra_no_disponibles" in cabecera.review_reasons
    assert any("doc-f076" in r.getMessage() for r in caplog.records if r.levelno == logging.WARNING)
    assert json.loads(cabecera.raw_ia_envelope_json)["context"]["lineas_albaran"][0][
        "codigo_partida_albaran"] == "CI.04.18"


def test_f076_r11_sin_lista_como_hoy_con_motivo_sin_revision():
    envelope = sobre([(1, "CI.4.18", 501)], contrato=[linea_contrato(501, "CI.4.18")])
    con, sin = _Repositorio(), _Repositorio()
    _pipeline(envelope, con, normalizador=False).run(RunValuationRequest(document_id="doc-f076"))
    _pipeline(envelope, sin, puerto=PuertoFalso(None)).run(RunValuationRequest(document_id="doc-f076"))
    (cab_hoy, lin_hoy), (cab_sin, lin_sin) = _guardado(con), _guardado(sin)
    assert [vars(r) for r in lin_sin] == [vars(r) for r in lin_hoy]
    assert cab_sin.review_reasons == [*cab_hoy.review_reasons, "partidas_obra_no_disponibles"]
    assert cab_sin.review_required is cab_hoy.review_required


def test_f076_r7_sin_normalizador_el_pipeline_es_el_de_siempre():
    """Quien construye el pipeline sin normalizador (tests de otras features) valora como antes."""
    envelope = sobre([(1, "CI.04.18")])
    repo = _Repositorio()
    _pipeline(envelope, repo, normalizador=False).run(RunValuationRequest(document_id="doc-f076"))
    cabecera, (fila,) = _guardado(repo)
    assert fila.codigo_partida_albaran == "CI.04.18"
    assert "partidas_obra_no_disponibles" not in cabecera.review_reasons


def test_f076_t10_completar_registros_sigue_siendo_lo_ultimo_que_asigna_las_lineas():
    """Nota de F-078: todo ``replace_valuation`` con líneas recibe lo que devolvió
    ``completar_registros`` (lo comprueba su test); anotar no reasigna ``lines``."""
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1] / "application" / "pipelines"
              / "run_valuation_pipeline.py").read_text(encoding="utf-8")
    i_completar = fuente.index("lines = completar_registros(")
    i_anotar = fuente.index("NormalizadorPartidas.anotar(")
    i_replace = fuente.index("replace_valuation(\n            header=header_with_envelope")
    assert i_completar < i_anotar < i_replace
