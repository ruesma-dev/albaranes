# tests/test_f053_servicio_entrada.py
"""F-053 · T8 · entrada de sv9: reclamación (R5–R8) y el ``finally`` de R9.

- ``decidir`` (puro) con cada salida: ``ignorar``, ``solo_adjunto``,
  ``a_incierto``, ``procesar`` y ``verificar_anulacion``.
- ``AltaSigridService.procesar`` con dobles de los tres puertos: qué deja en el
  alta cada salida y que, tras R5, ninguna salida (ni por excepción) lo deja en
  ``en_curso``.
"""
from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

import pytest

from application.alta_sigrid_service import AltaSigridService, ResultadoProceso
from domain.models.alta_models import (
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    Decision,
    EstadoAlta,
    EstadoDocumento,
    ModoAlta,
)
from domain.services.reclamacion import decidir
from tests.f053_datos import CONFIG, USU, datos, sin_vincular
from tests.f053_fakes import (
    AHORA,
    APROBADO,
    DESDE,
    ESPERA,
    Explota,
    PdfFalso,
    RepoFalso,
    SigridFalso,
)

DOC_OK = EstadoDocumento(activo=True, aprobado=True, approved_at_utc=APROBADO, approved_by="ana")


def _decidir(documento=DOC_OK, alta=None, accion=AccionAlta.ALTA, desde=DESDE):
    return decidir(documento, alta, accion=accion, ahora=AHORA, desde=desde, espera=ESPERA)


def _alta(estado: EstadoAlta, minutos: float | None = None, **cambios) -> AltaActual:
    ultimo = None if minutos is None else AHORA - timedelta(minutes=minutos)
    return AltaActual(estado=estado, ultimo_intento_at_utc=ultimo, **cambios)


def servicio(repo, sigrid=None, *, modo=ModoAlta.SIMULACION, desde=DESDE, pdf=None):
    return AltaSigridService(
        repo=repo, sigrid=sigrid or SigridFalso(), pdf=pdf or PdfFalso(), config=CONFIG, usuario_respaldo=USU,
        modo=modo, desde=desde, espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset({"producto_sin_historico"}), reloj=lambda: AHORA,
    )


# ------------------------------------------------------------------ #
# decidir · R6 (no se toca nada)
# ------------------------------------------------------------------ #
@pytest.mark.parametrize(
    ("documento", "desde"),
    [
        (DOC_OK, None),
        (None, DESDE),
        (replace(DOC_OK, activo=False), DESDE),
        (replace(DOC_OK, aprobado=False), DESDE),
        (replace(DOC_OK, approved_at_utc=None), DESDE),
        (replace(DOC_OK, approved_at_utc=DESDE - timedelta(seconds=1)), DESDE),
    ],
    ids=["desde_vacia", "no_existe", "papelera", "no_aprobado", "sin_fecha", "antes_de_desde"],
)
def test_f053_r6_decidir_ignora(documento, desde):
    for accion in AccionAlta:
        assert _decidir(documento, None, accion, desde).decision is Decision.IGNORAR


def test_f053_r5_decidir_aprobado_justo_en_desde_se_procesa():
    documento = replace(DOC_OK, approved_at_utc=DESDE)
    assert _decidir(documento).decision is Decision.PROCESAR


# ------------------------------------------------------------------ #
# decidir · R5, R7, R8
# ------------------------------------------------------------------ #
def test_f053_r5_decidir_sin_alta_se_procesa():
    assert _decidir().decision is Decision.PROCESAR


@pytest.mark.parametrize("estado", [EstadoAlta.NO_ADMITIDO, EstadoAlta.REVISAR, EstadoAlta.ERROR,
                                    EstadoAlta.SIMULADO, EstadoAlta.ANULADO])
def test_f053_r5_decidir_estados_que_se_repiten(estado):
    reclamacion = _decidir(alta=_alta(estado, 1))
    assert reclamacion.decision is Decision.PROCESAR
    assert reclamacion.alta.estado is estado


def test_f053_r7_decidir_ya_en_sigrid_se_ignora():
    assert _decidir(alta=_alta(EstadoAlta.YA_EN_SIGRID, 500)).decision is Decision.IGNORAR


def test_f053_r7_decidir_registrado_con_adjunto_colgado_se_ignora():
    alta = _alta(EstadoAlta.REGISTRADO, 500, adjunto_estado=AdjuntoEstado.COLGADO)
    assert _decidir(alta=alta).decision is Decision.IGNORAR


@pytest.mark.parametrize("adjunto", [None, AdjuntoEstado.ERROR])
def test_f053_r23_decidir_registrado_sin_adjunto_solo_adjunto(adjunto):
    alta = _alta(EstadoAlta.REGISTRADO, 500, adjunto_estado=adjunto)
    assert _decidir(alta=alta).decision is Decision.SOLO_ADJUNTO


@pytest.mark.parametrize("estado", [EstadoAlta.EN_CURSO, EstadoAlta.INCIERTO])
@pytest.mark.parametrize("minutos", [0, 5, 14.9])
def test_f053_r7_decidir_bloqueante_sin_pasar_la_espera_se_ignora(estado, minutos):
    assert _decidir(alta=_alta(estado, minutos)).decision is Decision.IGNORAR


@pytest.mark.parametrize("minutos", [15, 16, 600, None])
def test_f053_r8_decidir_en_curso_pasada_la_espera_a_incierto(minutos):
    assert _decidir(alta=_alta(EstadoAlta.EN_CURSO, minutos)).decision is Decision.A_INCIERTO


@pytest.mark.parametrize("minutos", [15, 60, None])
def test_f053_r15_decidir_incierto_pasada_la_espera_se_retoma(minutos):
    assert _decidir(alta=_alta(EstadoAlta.INCIERTO, minutos)).decision is Decision.PROCESAR


def test_f053_r28_decidir_verificar_anulacion_solo_si_registrado():
    accion = AccionAlta.VERIFICAR_ANULACION
    registrado = _alta(EstadoAlta.REGISTRADO, 500, sigrid_con_ide=7)
    assert _decidir(alta=registrado, accion=accion).decision is Decision.VERIFICAR_ANULACION
    for estado in (EstadoAlta.SIMULADO, EstadoAlta.ANULADO, EstadoAlta.INCIERTO):
        assert _decidir(alta=_alta(estado, 500), accion=accion).decision is Decision.IGNORAR
    assert _decidir(alta=None, accion=accion).decision is Decision.IGNORAR


# ------------------------------------------------------------------ #
# Servicio · R5–R8
# ------------------------------------------------------------------ #
def test_f053_r5_procesar_deja_en_curso_con_intento_y_modo():
    repo = RepoFalso()
    doc = repo.anadir(datos(sin_vincular(1)), alta=_alta(EstadoAlta.ERROR, 30, intentos=2))
    servicio(repo).procesar(doc, AccionAlta.ALTA)
    reclamada = repo.tras_reclamar[doc]
    assert reclamada.estado is EstadoAlta.EN_CURSO
    assert reclamada.intentos == 3 and reclamada.modo == "simulacion"
    assert reclamada.ultimo_intento_at_utc == AHORA


def test_f053_r6_desde_vacia_no_toca_nada_ni_reclama():
    repo, sigrid = RepoFalso(), SigridFalso()
    doc = repo.anadir(datos(sin_vincular(1)))
    resultado = servicio(repo, sigrid, desde=None).procesar(doc, AccionAlta.ALTA)
    assert isinstance(resultado, ResultadoProceso)
    assert resultado.decision is Decision.IGNORAR
    assert repo.reclamaciones == [] and repo.altas == {} and sigrid.llamadas == []


@pytest.mark.parametrize("como", ["no_aprobado", "papelera", "antes_de_desde", "no_existe"])
def test_f053_r6_documento_que_no_toca_se_confirma_sin_cambios(como):
    repo, sigrid = RepoFalso(), SigridFalso()
    d = datos(sin_vincular(1))
    if como != "no_existe":
        repo.anadir(d, aprobado=como != "no_aprobado", activo=como != "papelera",
                    approved_at=DESDE - timedelta(days=1) if como == "antes_de_desde" else APROBADO)
    resultado = servicio(repo, sigrid).procesar(d.cabecera.document_id, AccionAlta.ALTA)
    assert resultado.decision is Decision.IGNORAR
    assert repo.altas == {} and repo.guardados == [] and sigrid.llamadas == []


@pytest.mark.parametrize(("estado", "minutos", "adjunto"), [
    (EstadoAlta.YA_EN_SIGRID, 500, None),
    (EstadoAlta.REGISTRADO, 500, AdjuntoEstado.COLGADO),
    (EstadoAlta.EN_CURSO, 3, None),
    (EstadoAlta.INCIERTO, 3, None),
])
def test_f053_r7_se_confirma_sin_cambiar_nada(estado, minutos, adjunto):
    repo, sigrid = RepoFalso(), SigridFalso()
    alta = _alta(estado, minutos, adjunto_estado=adjunto)
    doc = repo.anadir(datos(sin_vincular(1)), alta=alta)
    resultado = servicio(repo, sigrid).procesar(doc, AccionAlta.ALTA)
    assert resultado.decision is Decision.IGNORAR
    assert repo.altas[doc] == alta and repo.guardados == [] and sigrid.llamadas == []


def test_f053_r8_en_curso_caducado_pasa_a_incierto_sin_llamar_a_sigrid():
    repo, sigrid = RepoFalso(), SigridFalso()
    doc = repo.anadir(datos(sin_vincular(1)), alta=_alta(EstadoAlta.EN_CURSO, 40))
    resultado = servicio(repo, sigrid).procesar(doc, AccionAlta.ALTA)
    assert resultado.decision is Decision.A_INCIERTO
    assert repo.estado(doc) is EstadoAlta.INCIERTO
    assert sigrid.llamadas == []


def test_f053_r5_fallo_al_reclamar_se_propaga_para_reencolar():
    repo = RepoFalso(fallar_en={"reclamar"})
    doc = repo.anadir(datos(sin_vincular(1)))
    with pytest.raises(Explota):
        servicio(repo).procesar(doc, AccionAlta.ALTA)


# ------------------------------------------------------------------ #
# Servicio · R9 (excepción antes de grabar)
# ------------------------------------------------------------------ #
def test_f053_r9_excepcion_antes_de_grabar_deja_error_y_no_se_propaga():
    repo, sigrid = RepoFalso(fallar_en={"leer_datos"}), SigridFalso()
    doc = repo.anadir(datos(sin_vincular(1)))
    resultado = servicio(repo, sigrid).procesar(doc, AccionAlta.ALTA)
    assert resultado.decision is Decision.PROCESAR
    assert resultado.estado is EstadoAlta.ERROR
    assert repo.estado(doc) is EstadoAlta.ERROR
    assert [m.codigo for m in repo.ultimo(doc).motivos] == ["excepcion"]
    assert sigrid.llamadas == []


def test_f053_r9_si_ni_siquiera_se_puede_guardar_el_error_no_revienta():
    """Queda en ``en_curso``: R8 lo pasará a ``incierto`` tras la Espera."""
    repo = RepoFalso(fallar_en={"leer_datos"}, fallar_al_guardar={EstadoAlta.ERROR})
    doc = repo.anadir(datos(sin_vincular(1)))
    resultado = servicio(repo).procesar(doc, AccionAlta.ALTA)
    assert resultado.estado is EstadoAlta.ERROR
    assert repo.estado(doc) is EstadoAlta.EN_CURSO
