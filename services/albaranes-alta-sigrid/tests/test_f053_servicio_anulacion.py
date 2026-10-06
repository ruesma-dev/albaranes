# tests/test_f053_servicio_anulacion.py
"""F-053 · T12 · ``verificar_anulacion`` en sv9 (R28).

El revisor anula en Sigrid el albarán registrado y pulsa «Ya lo he anulado en
Sigrid»: sv4 publica ``accion="verificar_anulacion"`` y sv9 pasa el alta a
``anulado`` SOLO si ``sql/read`` ya no encuentra ese ``con.ide``; si lo
encuentra, la deja ``registrado`` con el aviso «sigue en Sigrid». Tras
``anulado``, «Solicitar alta» repite el alta con la misma referencia (anular
borra el albarán, H9).
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from application.alta_sigrid_service import AltaSigridService
from domain.models.alta_models import (
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    Decision,
    EstadoAlta,
    ModoAlta,
    Motivo,
)
from tests.f053_datos import CONFIG, DOCUMENT_ID, datos, sin_vincular
from tests.f053_fakes import (
    AHORA,
    DESDE,
    ESPERA,
    PdfFalso,
    RepoFalso,
    SigridFalso,
    previa_ok,
)

REGISTRADO = AltaActual(
    estado=EstadoAlta.REGISTRADO, modo="real", sigrid_con_ide=9123461, sigrid_cod="AC26/16004",
    adjunto_estado=AdjuntoEstado.COLGADO, ultimo_intento_at_utc=AHORA - timedelta(days=2),
    motivos=(Motivo("registrado_distinto", "x", "1"),), peticion={"referencia_externa": "x"},
)


def _verificar(alta, sigrid, modo=ModoAlta.REAL, accion=AccionAlta.VERIFICAR_ANULACION):
    repo = RepoFalso()
    doc = repo.anadir(datos(sin_vincular(1)), alta=alta)
    servicio = AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=PdfFalso(), config=CONFIG, modo=modo, desde=DESDE,
        espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset({"producto_sin_historico"}), reloj=lambda: AHORA,
    )
    return repo, doc, servicio, servicio.procesar(doc, accion)


@pytest.mark.parametrize("modo", [ModoAlta.SIMULACION, ModoAlta.REAL])
def test_f053_r28_ya_no_esta_en_sigrid_es_anulado(modo):
    sigrid = SigridFalso(existe=False)
    repo, doc, _, resultado = _verificar(REGISTRADO, sigrid, modo)
    assert resultado.decision is Decision.VERIFICAR_ANULACION
    assert resultado.estado is EstadoAlta.ANULADO
    assert sigrid.llamadas == [("existe_concepto", 9123461)]
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.ANULADO
    assert guardado.sigrid_cod == "AC26/16004"  # se conserva para el historial
    assert guardado.motivos == ()


def test_f053_r28_sigue_en_sigrid_queda_registrado_con_aviso():
    sigrid = SigridFalso(existe=True)
    repo, doc, _, resultado = _verificar(REGISTRADO, sigrid)
    assert resultado.estado is EstadoAlta.REGISTRADO
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.REGISTRADO
    assert guardado.sigrid_con_ide == 9123461 and guardado.peticion == REGISTRADO.peticion
    assert [m.codigo for m in guardado.motivos] == ["registrado_distinto", "sigue_en_sigrid"]
    assert "AC26/16004" in guardado.motivos[-1].detalle
    assert "alta_albaran" not in sigrid.operaciones()


def test_f053_r28_verificar_dos_veces_no_duplica_el_aviso():
    sigrid = SigridFalso(existe=True)
    repo, doc, servicio, _ = _verificar(REGISTRADO, sigrid)
    servicio.procesar(doc, AccionAlta.VERIFICAR_ANULACION)
    assert [m.codigo for m in repo.ultimo(doc).motivos] == ["registrado_distinto", "sigue_en_sigrid"]


@pytest.mark.parametrize("estado", [EstadoAlta.SIMULADO, EstadoAlta.ANULADO, EstadoAlta.ERROR,
                                    EstadoAlta.INCIERTO, EstadoAlta.YA_EN_SIGRID])
def test_f053_r28_ignorada_si_el_alta_no_esta_registrado(estado):
    sigrid = SigridFalso(existe=False)
    alta = AltaActual(estado=estado, ultimo_intento_at_utc=AHORA - timedelta(days=1))
    repo, doc, _, resultado = _verificar(alta, sigrid)
    assert resultado.decision is Decision.IGNORAR
    assert sigrid.llamadas == [] and repo.guardados == [] and repo.altas[doc] == alta


def test_f053_r28_sin_alta_se_ignora():
    sigrid = SigridFalso(existe=False)
    repo, doc, _, resultado = _verificar(None, sigrid)
    assert resultado.decision is Decision.IGNORAR and sigrid.llamadas == []
    assert doc not in repo.altas


def test_f053_r28_si_no_se_puede_comprobar_sigue_registrado():
    sigrid = SigridFalso(fallar_en={"existe_concepto"})
    repo, doc, _, resultado = _verificar(REGISTRADO, sigrid)
    assert resultado.estado is EstadoAlta.REGISTRADO
    assert repo.ultimo(doc).estado is EstadoAlta.REGISTRADO
    assert repo.ultimo(doc).motivos[-1].codigo == "verificacion_fallida"


def test_f053_r28_registrado_sin_con_ide_no_se_da_por_anulado():
    sigrid = SigridFalso(existe=False)
    alta = AltaActual(estado=EstadoAlta.REGISTRADO, sigrid_con_ide=None,
                      ultimo_intento_at_utc=AHORA - timedelta(days=1))
    repo, doc, _, resultado = _verificar(alta, sigrid)
    assert resultado.estado is EstadoAlta.REGISTRADO
    assert sigrid.llamadas == []
    assert repo.ultimo(doc).motivos[-1].codigo == "verificacion_fallida"


def test_f053_r28_tras_anulado_solicitar_alta_repite_con_la_misma_referencia():
    sigrid = SigridFalso(existe=False)
    repo, doc, servicio, _ = _verificar(REGISTRADO, sigrid)
    assert repo.estado(doc) is EstadoAlta.ANULADO
    sigrid.previa = previa_ok([])  # se rellena tras construir: basta con ver la llamada
    servicio.procesar(doc, AccionAlta.ALTA)
    peticion = next(c[1] for c in sigrid.llamadas if c[0] == "alta_albaran")
    assert peticion.referencia_externa == f"ALB-{DOCUMENT_ID}"
