# tests/test_f053_r47_servicio.py
"""F-053 v8 · T43 · el ``usu`` del alta sale de quien aprobó (R47, R48).

Fakes de los tres puertos; sin red ni BBDD.

- R47: petición nueva ⇒ ``usu`` = el ``cod`` que devuelve Sigrid para la parte
  local del correo ``@ruesma.es`` de ``approved_by`` (el guardado en R5, que
  llega en la reclamación); si no casa, o ``approved_by`` no es correo de
  Ruesma, el Respaldo (sin leer ``dbo.usu`` en este último caso).
- R48: lectura de ``dbo.usu`` caída, o Respaldo vacío cuando hace falta ⇒
  ``error`` ``usuario_no_resuelto`` sin buscar altas a mano ni previa.
- R15: un ``incierto`` retomado reenvía SU petición (con su ``usu``) sin leer
  ``dbo.usu``.
- R22: el adjunto (también ``solo_adjunto``) usa el ``usu`` de la petición
  guardada, no el Respaldo.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from application.alta_sigrid_service import MOTIVO_USUARIO, AltaSigridService
from domain.models.alta_models import (
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    Decision,
    EstadoAlta,
    EstadoDocumento,
    ModoAlta,
    PeticionAlbaran,
    ResultadoAdjunto,
)
from domain.services.reclamacion import decidir
from domain.services.validador_alta import ConfigAlta, validar_y_construir
from tests.f053_datos import CONFIG, HOY, MAPEO, datos, sin_vincular, vinculada
from tests.f053_fakes import (
    AHORA,
    APROBADO,
    DESDE,
    ESPERA,
    PdfFalso,
    RepoFalso,
    SigridFalso,
    previa_ok,
)

RESPALDO = "pgris"
D = datos(vinculada(1), sin_vincular(2))


def _peticion(usu: str) -> PeticionAlbaran:
    peticion = validar_y_construir(D, CONFIG, HOY, usu)
    assert isinstance(peticion, PeticionAlbaran)
    return peticion


def _sigrid(**campos) -> SigridFalso:
    return SigridFalso(previa=previa_ok(_peticion("x")), **campos)


def _procesar(sigrid, *, approved_by="ana@ruesma.es", respaldo=RESPALDO,
              modo=ModoAlta.SIMULACION, alta=None, d=D):
    repo = RepoFalso()
    doc = repo.anadir(d, alta=alta, approved_by=approved_by)
    servicio = AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=PdfFalso(), config=CONFIG, usuario_respaldo=respaldo,
        modo=modo, desde=DESDE, espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset(), reloj=lambda: AHORA,
    )
    resultado = servicio.procesar(doc, AccionAlta.ALTA)
    return repo, doc, resultado


def _usu_pedido(sigrid: SigridFalso) -> list[str]:
    return [c[1].usu for c in sigrid.llamadas if c[0] == "alta_albaran"]


# ------------------------------------------------------------------ #
# R47 · de dónde sale usu
# ------------------------------------------------------------------ #
def test_f053_r47_casa_con_dbo_usu_y_manda_el_cod_de_sigrid():
    sigrid = _sigrid(usuarios={"ana": "ANA"})
    repo, doc, resultado = _procesar(sigrid, approved_by="  Ana@Ruesma.ES ")
    assert resultado.estado is EstadoAlta.SIMULADO
    assert sigrid.llamadas[0] == ("buscar_usuario", "Ana")
    # F-069 R14: tras el usu, el empleado (dbo.emp), antes de las altas a mano.
    assert sigrid.operaciones() == ["buscar_usuario", "buscar_empleados_por_correo",
                                    "buscar_albaranes", "alta_albaran"]
    assert _usu_pedido(sigrid) == ["ANA"]
    assert repo.ultimo(doc).peticion["usu"] == "ANA"


def test_f053_r47_correo_de_ruesma_que_no_casa_usa_el_respaldo():
    sigrid = _sigrid(usuarios={})
    repo, doc, _ = _procesar(sigrid, approved_by="nombre.apellido@ruesma.es")
    assert sigrid.llamadas[0] == ("buscar_usuario", "nombre.apellido")
    assert _usu_pedido(sigrid) == [RESPALDO]
    assert repo.ultimo(doc).peticion["usu"] == RESPALDO


@pytest.mark.parametrize("approved_by", [None, "", "reviewer", "ana@gmail.com",
                                         "x_gmail.com#EXT#@ruesmaxx.onmicrosoft.com"])
def test_f053_r47_sin_correo_de_ruesma_respaldo_sin_leer_dbo_usu(approved_by):
    sigrid = _sigrid(usuarios={"ana": "ana", "reviewer": "reviewer"})
    _, _, resultado = _procesar(sigrid, approved_by=approved_by)
    assert resultado.estado is EstadoAlta.SIMULADO
    assert "buscar_usuario" not in sigrid.operaciones()
    assert _usu_pedido(sigrid) == [RESPALDO]


def test_f053_r47_respaldo_con_espacios_se_recorta():
    sigrid = _sigrid()
    _procesar(sigrid, approved_by="reviewer", respaldo="  pgris \n")
    assert _usu_pedido(sigrid) == ["pgris"]


def test_f053_r47_respaldo_vacio_no_importa_si_casa():
    sigrid = _sigrid(usuarios={"ana": "ana"})
    _, _, resultado = _procesar(sigrid, respaldo="")
    assert resultado.estado is EstadoAlta.SIMULADO
    assert _usu_pedido(sigrid) == ["ana"]


def test_f053_r47_la_reclamacion_lleva_el_approved_by_del_merge():
    documento = EstadoDocumento(activo=True, aprobado=True, approved_at_utc=APROBADO,
                                approved_by="ana@ruesma.es")
    reclamacion = decidir(documento, None, accion=AccionAlta.ALTA, ahora=AHORA,
                          desde=DESDE, espera=ESPERA)
    assert reclamacion.decision is Decision.PROCESAR
    assert reclamacion.approved_by == "ana@ruesma.es"
    ignorada = decidir(None, None, accion=AccionAlta.ALTA, ahora=AHORA, desde=DESDE,
                       espera=ESPERA)
    assert ignorada.approved_by is None


def test_f053_r12_validar_y_construir_recibe_usu_y_config_ya_no_lo_lleva():
    assert "usu" not in ConfigAlta.__dataclass_fields__
    config = ConfigAlta(empide=None, mapeo=MAPEO)
    assert validar_y_construir(D, config, HOY, "luis").usu == "luis"


# ------------------------------------------------------------------ #
# R48 · sin usuario no se sigue
# ------------------------------------------------------------------ #
def _sin_usuario(repo, doc, resultado, sigrid, operaciones):
    assert resultado.estado is EstadoAlta.ERROR
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.ERROR
    assert [m.codigo for m in guardado.motivos] == [MOTIVO_USUARIO]
    assert sigrid.operaciones() == operaciones
    assert sigrid.commits() == []


def test_f053_r48_lectura_de_dbo_usu_caida_es_error_sin_previa():
    sigrid = _sigrid(fallar_en={"buscar_usuario"})
    repo, doc, resultado = _procesar(sigrid)
    _sin_usuario(repo, doc, resultado, sigrid, ["buscar_usuario"])
    assert "Explota" in repo.ultimo(doc).motivos[0].detalle


@pytest.mark.parametrize("respaldo", ["", "   "])
def test_f053_r48_respaldo_vacio_y_sin_casar_es_error(respaldo):
    sigrid = _sigrid(usuarios={})
    repo, doc, resultado = _procesar(sigrid, respaldo=respaldo)
    _sin_usuario(repo, doc, resultado, sigrid, ["buscar_usuario"])
    assert "ALTA_SIGRID_USUARIO_RESPALDO" in repo.ultimo(doc).motivos[0].detalle


def test_f053_r48_respaldo_vacio_sin_correo_es_error_sin_llamar_a_nadie():
    sigrid = _sigrid()
    repo, doc, resultado = _procesar(sigrid, approved_by="reviewer", respaldo="")
    _sin_usuario(repo, doc, resultado, sigrid, [])


def test_f053_r48_sin_usuario_no_sigue_ni_deja_un_fallo_inesperado(caplog):
    """T50 (mutante 25): tras guardar el ``error`` el flujo TERMINA; no sigue a
    validar sin ``usu`` (que acabaría en «fallo inesperado» en el log)."""
    sigrid = _sigrid(fallar_en={"buscar_usuario"})
    caplog.set_level("INFO")
    repo, doc, resultado = _procesar(sigrid)
    _sin_usuario(repo, doc, resultado, sigrid, ["buscar_usuario"])
    assert "fallo inesperado" not in caplog.text
    assert [r.levelname for r in caplog.records if r.levelname in ("ERROR", "CRITICAL")] == []


def test_f053_r48_se_resuelve_antes_de_validar():
    """design §5.3: el usuario va antes que la validación local."""
    sigrid = _sigrid(fallar_en={"buscar_usuario"})
    no_admitido = datos(vinculada(1), obra_codigo=None)
    repo, doc, resultado = _procesar(sigrid, d=no_admitido)
    _sin_usuario(repo, doc, resultado, sigrid, ["buscar_usuario"])


# ------------------------------------------------------------------ #
# R15 · un incierto retomado conserva su usu
# ------------------------------------------------------------------ #
def test_f053_r15_incierto_retomado_reenvia_su_usu_sin_leer_dbo_usu():
    guardada = _peticion("luis").a_dict()
    incierto = AltaActual(estado=EstadoAlta.INCIERTO, modo="simulacion", peticion=guardada,
                          ultimo_intento_at_utc=AHORA - ESPERA * 2)
    sigrid = _sigrid(usuarios={"ana": "ana"})
    _, _, resultado = _procesar(sigrid, alta=incierto)
    assert resultado.estado is EstadoAlta.SIMULADO
    assert "buscar_usuario" not in sigrid.operaciones()
    assert _usu_pedido(sigrid) == ["luis"]


# ------------------------------------------------------------------ #
# R22 · el adjunto usa el usu de la petición
# ------------------------------------------------------------------ #
def _adjuntos(sigrid):
    return [c for c in sigrid.llamadas if c[0] == "adjuntar_pdf"]


def test_f053_r22_el_adjunto_va_con_el_usu_resuelto():
    peticion = _peticion("x")
    creado = replace(previa_ok(peticion), estado="creado")
    sigrid = SigridFalso(previa=previa_ok(peticion), grabacion=creado,
                         usuarios={"ana": "ana"})
    _, _, resultado = _procesar(sigrid, modo=ModoAlta.REAL)
    assert resultado.estado is EstadoAlta.REGISTRADO
    (adjunto,) = _adjuntos(sigrid)
    assert adjunto[-1] == "ana"


def _registrado_sin_adjunto(peticion: dict | None) -> AltaActual:
    return AltaActual(estado=EstadoAlta.REGISTRADO, modo="real", sigrid_con_ide=9123461,
                      sigrid_cod="AC26/1", adjunto_estado=AdjuntoEstado.ERROR,
                      peticion=peticion)


def test_f053_r22_solo_adjunto_usa_el_usu_de_la_peticion_guardada():
    sigrid = SigridFalso(usuarios={"ana": "ana"})
    repo, doc, resultado = _procesar(
        sigrid, modo=ModoAlta.REAL, alta=_registrado_sin_adjunto(_peticion("luis").a_dict()),
    )
    assert resultado.decision is Decision.SOLO_ADJUNTO
    assert sigrid.operaciones() == ["adjuntar_pdf"]
    assert _adjuntos(sigrid)[0][-1] == "luis"
    assert repo.ultimo(doc).adjunto_estado is AdjuntoEstado.COLGADO


@pytest.mark.parametrize("peticion", [None, {}, {"usu": ""}, {"usu": "  "}])
def test_f053_r22_solo_adjunto_sin_usu_guardado_no_llama_y_queda_en_error(peticion):
    sigrid = SigridFalso(adjunto=ResultadoAdjunto(True, gra_ide=1))
    repo, doc, _ = _procesar(sigrid, modo=ModoAlta.REAL,
                             alta=_registrado_sin_adjunto(peticion))
    assert _adjuntos(sigrid) == []
    guardado = repo.ultimo(doc)
    assert guardado.estado is EstadoAlta.REGISTRADO
    assert guardado.adjunto_estado is AdjuntoEstado.ERROR
    assert [m.codigo for m in guardado.motivos] == ["adjunto_no_colgado"]
    assert guardado.motivos[0].detalle.startswith(MOTIVO_USUARIO)
