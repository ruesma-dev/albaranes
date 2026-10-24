# tests/test_f053_servicio_real.py
"""F-053 · T11 · modo real: grabación única y adjunto (R20–R23; R9 en vuelo).

- R20: tras una previa limpia, la MISMA petición con ``commit=true`` UNA sola
  vez; ``creado``/``idempotente`` ⇒ ``registrado`` con ``con_ide`` y ``cod``.
- R21: 5xx, tiempo agotado o conexión en la grabación ⇒ ``incierto``, sin
  reintento.
- R9: una excepción con la grabación en vuelo ⇒ ``incierto``.
- R22: con el alta ``registrado`` en real, se adjunta el PDF (colgado = ok y
  committed o idempotente, lo decide el cliente).
- R23: si el adjunto falla, sigue ``registrado`` con el adjunto en error; un
  nuevo mensaje de alta SOLO reintenta el adjunto.
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
    ErrorAlta,
    EstadoAlta,
    ModoAlta,
    Motivo,
    PeticionAlbaran,
    RespuestaAlta,
    ResultadoAdjunto,
    TipoFallo,
)
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, USU, DOCUMENT_ID, HOY, datos, sin_vincular, vinculada
from tests.f053_fakes import (
    AHORA,
    DESDE,
    ESPERA,
    PdfFalso,
    RepoFalso,
    SigridFalso,
    previa_ok,
)

D = datos(vinculada(1), sin_vincular(2))


def _peticion() -> PeticionAlbaran:
    peticion = validar_y_construir(D, CONFIG, HOY, USU)
    assert isinstance(peticion, PeticionAlbaran)
    return peticion


def _servicio(repo, sigrid, pdf=None, modo=ModoAlta.REAL):
    return AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=pdf or PdfFalso(), config=CONFIG, usuario_respaldo=USU, modo=modo,
        desde=DESDE, espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset({"producto_sin_historico"}), reloj=lambda: AHORA,
    )


def _procesar(sigrid, *, repo=None, pdf=None, modo=ModoAlta.REAL, alta=None):
    repo = repo or RepoFalso()
    doc = repo.anadir(D, alta=alta)
    resultado = _servicio(repo, sigrid, pdf, modo).procesar(doc, AccionAlta.ALTA)
    return repo, doc, resultado


def _sigrid(grabacion, previa=None, **extra) -> SigridFalso:
    return SigridFalso(previa=previa or previa_ok(_peticion()), grabacion=grabacion, **extra)


CREADO = previa_ok(_peticion(), estado="creado", con_ide=9123461, cod="AC26/16004")


# ------------------------------------------------------------------ #
# R20 · grabación única
# ------------------------------------------------------------------ #
def test_f053_r20_previa_limpia_y_una_sola_grabacion_registrado():
    sigrid = _sigrid(CREADO)
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.REGISTRADO
    guardado = repo.ultimo(doc)
    assert (guardado.sigrid_con_ide, guardado.sigrid_cod) == (9123461, "AC26/16004")
    assert guardado.modo == "real"
    assert sigrid.commits() == [False, True]
    previa, grabacion = [c[1] for c in sigrid.llamadas if c[0] == "alta_albaran"]
    assert previa == grabacion == _peticion()  # la MISMA petición


def test_f053_r20_grabacion_idempotente_tambien_registrado():
    sigrid = _sigrid(previa_ok(_peticion(), estado="idempotente", con_ide=5, cod="AC26/5"))
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.REGISTRADO
    assert repo.ultimo(doc).sigrid_con_ide == 5


def test_f053_r20_previa_con_motivos_no_graba():
    sigrid = _sigrid(CREADO, previa=previa_ok(_peticion(), totales={"1": 1.0}))
    _, _, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.REVISAR
    assert sigrid.commits() == [False]


@pytest.mark.parametrize("codigo", ["colision_de_clave", "escritura_albaranes_deshabilitada",
                                    "filas_afectadas_inesperadas"])
def test_f053_r20_grabacion_rechazada_es_error(codigo):
    sigrid = _sigrid(ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo=codigo))
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.ERROR
    assert repo.ultimo(doc).motivos[0].codigo == codigo
    assert sigrid.commits() == [False, True]
    assert "adjuntar_pdf" not in sigrid.operaciones()


def test_f053_r20_grabacion_que_responde_previsto_es_error():
    sigrid = _sigrid(previa_ok(_peticion()))  # estado previsto
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.ERROR
    assert [m.codigo for m in repo.ultimo(doc).motivos] == ["respuesta_inesperada"]


def test_f053_r20_grabacion_con_estado_desconocido_es_incierto():
    sigrid = _sigrid(RespuestaAlta(estado="raro"))
    _, _, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.INCIERTO


def test_f053_r20_lo_creado_distinto_de_lo_pedido_queda_registrado_distinto():
    creado = previa_ok(_peticion(), estado="creado", totales={"2": 1.0})
    repo, doc, resultado = _procesar(_sigrid(creado))
    assert resultado.estado is EstadoAlta.REGISTRADO
    assert [(m.codigo, m.referencia_linea) for m in repo.ultimo(doc).motivos] == [
        ("registrado_distinto", "2"),
    ]


# ------------------------------------------------------------------ #
# R21 · fallo transitorio en la grabación
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("tipo", [TipoFallo.SERVIDOR, TipoFallo.TIEMPO_AGOTADO, TipoFallo.CONEXION])
def test_f053_r21_fallo_transitorio_en_grabacion_incierto_sin_reintento(tipo):
    sigrid = _sigrid(ErrorAlta(tipo=tipo, status=502 if tipo is TipoFallo.SERVIDOR else None))
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.INCIERTO
    assert sigrid.commits() == [False, True]
    guardada = repo.ultimo(doc).peticion  # para retomarla igual (F-069 R16: + resolucion)
    assert {k: v for k, v in guardada.items() if k != "resolucion"} == _peticion().a_dict()


# ------------------------------------------------------------------ #
# R9 · excepción con la grabación en vuelo
# ------------------------------------------------------------------ #
def test_f053_r9_excepcion_durante_la_grabacion_deja_incierto():
    sigrid = _sigrid(CREADO, fallar_en={"grabacion"})
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.INCIERTO
    assert repo.estado(doc) is EstadoAlta.INCIERTO
    assert [m.codigo for m in repo.ultimo(doc).motivos] == ["excepcion"]


def test_f053_r9_excepcion_en_la_previa_deja_error():
    sigrid = _sigrid(CREADO, fallar_en={"previa"})
    _repo, _doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.ERROR
    assert sigrid.commits() == [False]


def test_f053_r9_si_no_se_puede_guardar_registrado_queda_incierto():
    repo = RepoFalso(fallar_al_guardar={EstadoAlta.REGISTRADO})
    _, doc, resultado = _procesar(_sigrid(CREADO), repo=repo)
    assert resultado.estado is EstadoAlta.INCIERTO
    assert repo.estado(doc) is EstadoAlta.INCIERTO


# ------------------------------------------------------------------ #
# R22 · adjunto
# ------------------------------------------------------------------ #
def test_f053_r22_adjunta_el_pdf_al_registrado():
    pdf = PdfFalso(contenido=b"%PDF-1.7 de mentira")
    sigrid = _sigrid(CREADO, adjunto=ResultadoAdjunto(True, gra_ide=777))
    repo, doc, resultado = _procesar(sigrid, pdf=pdf)
    assert resultado.estado is EstadoAlta.REGISTRADO
    adjuntos = [c for c in sigrid.llamadas if c[0] == "adjuntar_pdf"]
    assert adjuntos == [("adjuntar_pdf", 9123461, f"ALB-{DOCUMENT_ID}.pdf", b"%PDF-1.7 de mentira",
                         "USU_ALTA")]
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.REGISTRADO
    assert guardado.adjunto_estado is AdjuntoEstado.COLGADO and guardado.sigrid_gra_ide == 777
    assert guardado.sigrid_con_ide == 9123461


def test_f053_r22_previa_idempotente_en_real_tambien_adjunta():
    sigrid = SigridFalso(previa=previa_ok(_peticion(), estado="idempotente", con_ide=42))
    repo, doc, _ = _procesar(sigrid)
    assert ("adjuntar_pdf", 42) == sigrid.llamadas[-1][:2]
    assert repo.ultimo(doc).adjunto_estado is AdjuntoEstado.COLGADO
    assert sigrid.commits() == [False]


def test_f053_r22_en_simulacion_no_se_adjunta_nunca():
    sigrid = SigridFalso(previa=previa_ok(_peticion(), estado="idempotente", con_ide=42))
    repo, doc, _ = _procesar(sigrid, modo=ModoAlta.SIMULACION)
    assert "adjuntar_pdf" not in sigrid.operaciones()
    assert repo.ultimo(doc).adjunto_estado is None


# ------------------------------------------------------------------ #
# R23 · fallo del adjunto y reintento solo del adjunto
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("como", ["no_colgado", "excepcion", "sin_pdf"])
def test_f053_r23_fallo_del_adjunto_sigue_registrado(como):
    sigrid = _sigrid(CREADO, adjunto=ResultadoAdjunto(False, codigo="usuario_no_valido",
                                                      mensaje="usu"))
    pdf = PdfFalso(sin_ruta=como == "sin_pdf")
    if como == "excepcion":
        sigrid.fallar_en.add("adjuntar_pdf")
    if como == "sin_pdf":
        sigrid.adjunto = ResultadoAdjunto(True, gra_ide=1)
    repo, doc, resultado = _procesar(sigrid, pdf=pdf)
    assert resultado.estado is EstadoAlta.REGISTRADO
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.REGISTRADO
    assert guardado.adjunto_estado is AdjuntoEstado.ERROR
    assert guardado.sigrid_con_ide == 9123461
    assert "adjunto_no_colgado" in [m.codigo for m in guardado.motivos]


def test_f053_r23_nuevo_mensaje_solo_reintenta_el_adjunto():
    alta = AltaActual(
        estado=EstadoAlta.REGISTRADO, modo="real", sigrid_con_ide=9123461, sigrid_cod="AC26/16004",
        adjunto_estado=AdjuntoEstado.ERROR, motivos=(Motivo("adjunto_no_colgado", "x"),),
        peticion=_peticion().a_dict(), ultimo_intento_at_utc=AHORA - timedelta(days=1),
    )
    sigrid = SigridFalso(adjunto=ResultadoAdjunto(True, gra_ide=888))
    repo, doc, resultado = _procesar(sigrid, alta=alta)
    assert resultado.decision is Decision.SOLO_ADJUNTO
    assert sigrid.operaciones() == ["adjuntar_pdf"]
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.REGISTRADO and guardado.sigrid_cod == "AC26/16004"
    assert guardado.adjunto_estado is AdjuntoEstado.COLGADO and guardado.sigrid_gra_ide == 888
    assert guardado.motivos == ()
    assert guardado.peticion == alta.peticion


def test_f053_r23_solo_adjunto_en_simulacion_no_hace_nada():
    alta = AltaActual(estado=EstadoAlta.REGISTRADO, sigrid_con_ide=1, adjunto_estado=None)
    sigrid = SigridFalso()
    repo, _doc, resultado = _procesar(sigrid, alta=alta, modo=ModoAlta.SIMULACION)
    assert resultado.decision is Decision.SOLO_ADJUNTO
    assert sigrid.llamadas == [] and repo.guardados == []
