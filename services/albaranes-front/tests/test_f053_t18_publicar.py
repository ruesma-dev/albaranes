# tests/test_f053_t18_publicar.py
"""F-053 · T18 · sv4 pide el alta en Sigrid al pasar a aprobado (R1–R4).

- R1: CUANDO un documento no aprobado pasa a aprobado, por «Aprobar» del
  listado (``approve_document``) o por el PUT con ``approved=true``
  (``guardar``), y DESDE no está vacía, se publica UNA vez el alta.
- R2: guardar o aprobar uno YA aprobado no publica.
- R3: con DESDE vacía, nada se publica.
- R4: si la publicación falla (o el cliente lanza), la aprobación se mantiene
  y el resultado avisa de que el alta no se pidió.

El «paso a aprobado» lo decide el repositorio dentro de su transacción (ver
T19); aquí un doble devuelve lo que diría. Sin red ni BBDD.
"""
from __future__ import annotations

from datetime import UTC, datetime

import pytest

from domain.models.alta_sigrid_models import (
    AVISO_ALTA_NO_PEDIDA,
    ConfigAltaSigrid,
    ResultadoAprobacion,
)
from domain.models.review_models import DocumentDetailPayload, MergeDocumentUpdatePayload

DOC = "f053-t18-doc"
ACTIVA = ConfigAltaSigrid(desde=datetime(2026, 10, 1, tzinfo=UTC))
APAGADA = ConfigAltaSigrid(desde=None)


def _detalle(aprobado: bool) -> DocumentDetailPayload:
    return DocumentDetailPayload(
        id=DOC, source_filename="x.pdf", provider_origin="merge", model_name="—",
        created_at_utc="2026-10-08T08:00:00+00:00", approved=aprobado,
    )


class _Repo:
    """Doble: ``paso`` es lo que el repositorio diría del paso a aprobado."""

    def __init__(self, paso: bool):
        self.paso = paso
        self.aprobaciones: list[tuple] = []
        self.guardados: list[MergeDocumentUpdatePayload] = []
        self.undo: list[dict] = []

    def set_approved(self, *, document_id, approved, approved_by):
        self.aprobaciones.append((document_id, approved, approved_by))
        return self.paso if approved else False

    def update_document_y_transicion(self, *, document_id, payload):
        self.guardados.append(payload)
        return _detalle(payload.approved), (self.paso and payload.approved)

    def snapshot_row(self, *, table, row_id):
        return {"table": table, "values": {"id": row_id}}

    def valuation_header_id(self, *, document_id):
        return None

    def doc_label(self, *, document_id):
        return "alb T18"

    def record_undo(self, **kwargs):
        self.undo.append(kwargs)


class _Orquestador:
    def __init__(self, publica: bool = True, lanza: Exception | None = None):
        self.publica = publica
        self.lanza = lanza
        self.aprobados: list[dict] = []

    def notify_document_approved(self, **kwargs):
        self.aprobados.append(kwargs)
        if self.lanza is not None:
            raise self.lanza
        return self.publica


def _servicio(repo, orquestador, config=ACTIVA, reviewer="revisor"):
    from application.services.review_service import ReviewService

    return ReviewService(repo, reviewer, orquestador, config)


def _guardar(servicio, aprobado=True):
    return servicio.guardar(
        document_id=DOC,
        payload=MergeDocumentUpdatePayload(approved=aprobado, approved_by="ana"),
        refetch_client=None,
    )


# ------------------------------------------------------------------ #
# R1 · los dos caminos publican una vez
# ------------------------------------------------------------------ #
def test_f053_r1_aprobar_del_listado_publica_el_alta():
    repo, orq = _Repo(paso=True), _Orquestador()

    resultado = _servicio(repo, orq).approve_document(document_id=DOC, approved_by="ana")

    assert repo.aprobaciones == [(DOC, True, "ana")]
    assert len(orq.aprobados) == 1
    assert orq.aprobados[0]["document_id"] == DOC
    assert orq.aprobados[0]["approved_by"] == "ana"
    assert resultado == ResultadoAprobacion(paso_a_aprobado=True, alta_pedida=True)
    assert resultado.aviso is None


def test_f053_r1_aprobar_sin_revisor_usa_el_de_defecto():
    repo, orq = _Repo(paso=True), _Orquestador()
    _servicio(repo, orq, reviewer="defecto").approve_document(document_id=DOC, approved_by=None)
    assert repo.aprobaciones == [(DOC, True, "defecto")]
    assert orq.aprobados[0]["approved_by"] == "defecto"


def test_f053_r1_guardar_y_aprobar_publica_el_alta():
    repo, orq = _Repo(paso=True), _Orquestador()

    resultado = _guardar(_servicio(repo, orq))

    assert len(orq.aprobados) == 1
    assert orq.aprobados[0]["document_id"] == DOC
    assert orq.aprobados[0]["approved_by"] == "ana"
    assert resultado.aprobacion == ResultadoAprobacion(paso_a_aprobado=True, alta_pedida=True)
    assert resultado.detail.approved is True
    assert resultado.busqueda is None


def test_f053_r1_save_document_compatible_tambien_publica():
    repo, orq = _Repo(paso=True), _Orquestador()
    detalle = _servicio(repo, orq).save_document(
        document_id=DOC, payload=MergeDocumentUpdatePayload(approved=True),
    )
    assert detalle.approved is True
    assert len(orq.aprobados) == 1
    assert orq.aprobados[0]["approved_by"] == "revisor"


# ------------------------------------------------------------------ #
# R2 · ya aprobado: no publica
# ------------------------------------------------------------------ #
def test_f053_r2_aprobar_uno_ya_aprobado_no_publica():
    repo, orq = _Repo(paso=False), _Orquestador()
    resultado = _servicio(repo, orq).approve_document(document_id=DOC, approved_by="ana")
    assert orq.aprobados == []
    assert resultado == ResultadoAprobacion(paso_a_aprobado=False, alta_pedida=None)


@pytest.mark.parametrize("aprobado", [True, False])
def test_f053_r2_guardar_uno_ya_aprobado_o_sin_aprobar_no_publica(aprobado):
    repo, orq = _Repo(paso=False), _Orquestador()
    resultado = _guardar(_servicio(repo, orq), aprobado=aprobado)
    assert orq.aprobados == []
    assert resultado.aprobacion.alta_pedida is None


def test_f053_r2_desaprobar_no_publica():
    repo, orq = _Repo(paso=True), _Orquestador()
    _servicio(repo, orq).unapprove_document(document_id=DOC)
    assert repo.aprobaciones == [(DOC, False, None)]
    assert orq.aprobados == []


# ------------------------------------------------------------------ #
# R3 · DESDE vacía: como hoy
# ------------------------------------------------------------------ #
def test_f053_r3_con_desde_vacia_aprobar_no_publica():
    repo, orq = _Repo(paso=True), _Orquestador()
    resultado = _servicio(repo, orq, config=APAGADA).approve_document(
        document_id=DOC, approved_by="ana",
    )
    assert repo.aprobaciones == [(DOC, True, "ana")]
    assert orq.aprobados == []
    assert resultado == ResultadoAprobacion(paso_a_aprobado=True, alta_pedida=None)


def test_f053_r3_con_desde_vacia_guardar_y_aprobar_no_publica():
    repo, orq = _Repo(paso=True), _Orquestador()
    resultado = _guardar(_servicio(repo, orq, config=APAGADA))
    assert orq.aprobados == []
    assert resultado.aprobacion.alta_pedida is None


def test_f053_r3_sin_configuracion_es_feature_apagada():
    """Un ``ReviewService`` construido como antes de F-053 no publica nada."""
    from application.services.review_service import ReviewService

    repo, orq = _Repo(paso=True), _Orquestador()
    servicio = ReviewService(repo, "revisor")
    resultado = servicio.approve_document(document_id=DOC, approved_by="ana")
    assert resultado.alta_pedida is None


# ------------------------------------------------------------------ #
# R4 · falla la publicación: la aprobación se queda y se avisa
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("orquestador", [
    _Orquestador(publica=False),
    _Orquestador(lanza=RuntimeError("cola caída")),
    None,
], ids=["no_publica", "lanza", "sin_cliente"])
def test_f053_r4_fallo_al_publicar_mantiene_la_aprobacion_y_avisa(orquestador):
    repo = _Repo(paso=True)

    resultado = _servicio(repo, orquestador).approve_document(document_id=DOC, approved_by="ana")

    assert repo.aprobaciones == [(DOC, True, "ana")]
    assert resultado == ResultadoAprobacion(paso_a_aprobado=True, alta_pedida=False)
    assert resultado.aviso == AVISO_ALTA_NO_PEDIDA


def test_f053_r4_fallo_al_publicar_tras_guardar_y_aprobar():
    repo, orq = _Repo(paso=True), _Orquestador(publica=False)
    resultado = _guardar(_servicio(repo, orq))
    assert len(repo.guardados) == 1 and resultado.detail.approved is True
    assert resultado.aprobacion.alta_pedida is False
    assert resultado.aprobacion.aviso == AVISO_ALTA_NO_PEDIDA


def test_f053_r4_el_aviso_dice_como_pedirla():
    assert "Solicitar alta en Sigrid" in AVISO_ALTA_NO_PEDIDA
