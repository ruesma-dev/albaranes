# tests/test_f115_disparo_force.py
"""F-115 R7 · con ``force`` (re-fetch de sv4) y sin contrato, se revalora siempre.

Al cambiar el proveedor (o la obra) la selección queda NULL; si el albarán no
trae importes, F-075 R4 haría SKIP y la valoración del contrato anterior
sobreviviría. Con ``force=True`` y sin selección se publica ``q-valoracion``
con ``codigo_contrato=None`` aunque no haya importes, para que sv6 la
sustituya (D7). Con ``force=False`` (pipeline automático), F-075 sin cambios.
Mismos dobles que ``test_f075_disparo.py``.
"""
from __future__ import annotations

import pytest
from application.pipelines.persist_albaran_pipeline import PersistAlbaranPipeline

DOC = "doc-f115-disparo"


class _Trigger:
    def __init__(self):
        self.llamadas = []

    def trigger_async(self, *, document_id, codigo_contrato, force=False):
        self.llamadas.append((document_id, codigo_contrato, force))
        return True


class _Repo:
    def __init__(self, *, con_lineas=False, codigo=None, importes=()):
        self.con_lineas, self.codigo, self.importes = con_lineas, codigo, list(importes)
        self.pedidos = []

    def has_selected_contrato_with_lines(self, *, document_id):
        return self.con_lineas, self.codigo

    def importes_leidos(self, *, document_id):
        self.pedidos.append(document_id)
        return self.importes


def _disparar(repo, *, force):
    trigger = _Trigger()
    PersistAlbaranPipeline(
        repository=repo, document_storage=None, normalizer=None, valuation_trigger=trigger,
    )._trigger_valuation_safely(merge_document_id=DOC, force=force)
    return trigger.llamadas


@pytest.mark.parametrize("importes", [[], [None, None]], ids=["sin_lineas", "sin_importes"])
def test_f115_r7_a_force_sin_contrato_sin_importes_publica_sin_contrato(importes):
    assert _disparar(_Repo(importes=importes), force=True) == [(DOC, None, True)]


def test_f115_r7_force_sin_contrato_con_importes_publica_sin_contrato():
    assert _disparar(_Repo(importes=[12.5]), force=True) == [(DOC, None, True)]


def test_f115_r7_sin_force_sin_importes_sigue_el_skip_de_f075():
    assert _disparar(_Repo(importes=[None]), force=False) == []


def test_f115_r7_force_con_contrato_sin_lineas_sigue_el_skip_m1():
    """Fuera de F-115 (design §8): contrato del proveedor nuevo sin líneas, SKIP."""
    repo = _Repo(codigo="CTB/0001", importes=[None])
    assert _disparar(repo, force=True) == []
    assert repo.pedidos == []


def test_f115_r7_force_con_contrato_con_lineas_como_hoy():
    assert _disparar(_Repo(con_lineas=True, codigo="CTB/0001"), force=True) == [(DOC, "CTB/0001", True)]
