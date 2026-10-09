# tests/test_f053_servicio_duplicados.py
"""F-053 · T9 · sin llamadas a Sigrid lo no admisible; duplicados e idempotencia.

- R10 y R39: ``no_admitido`` / ``revisar`` sin ninguna llamada al puerto de Sigrid.
- R14: alta a mano en Sigrid (mismo CIF normalizado y número, otro ``synckey``)
  ⇒ ``ya_en_sigrid`` en los dos modos, sin previa.
- R15: previa ``idempotente`` ⇒ ``registrado`` sin grabar (con
  ``registrado_distinto`` si los totales difieren); un ``incierto`` pasada la
  Espera se retoma reenviando LA MISMA petición.
"""
from __future__ import annotations

import logging
from dataclasses import replace
from datetime import timedelta

import pytest

from application.alta_sigrid_service import AltaSigridService
from domain.models.alta_models import (
    AccionAlta,
    AlbaranSigrid,
    AltaActual,
    EstadoAlta,
    ModoAlta,
    PeticionAlbaran,
)
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, DOCUMENT_ID, HOY, datos, sin_vincular, vinculada
from tests.f053_fakes import (
    AHORA,
    DESDE,
    ESPERA,
    PdfFalso,
    RepoFalso,
    SigridFalso,
    previa_ok,
)

MODOS = [ModoAlta.SIMULACION, ModoAlta.REAL]


def _servicio(repo, sigrid, modo=ModoAlta.SIMULACION):
    return AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=PdfFalso(), config=CONFIG, modo=modo, desde=DESDE,
        espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset({"producto_sin_historico"}), reloj=lambda: AHORA,
    )


def _procesar(d, sigrid, modo=ModoAlta.SIMULACION, alta=None):
    repo = RepoFalso()
    doc = repo.anadir(d, alta=alta)
    resultado = _servicio(repo, sigrid, modo).procesar(doc, AccionAlta.ALTA)
    return repo, doc, resultado


def _peticion(d) -> PeticionAlbaran:
    peticion = validar_y_construir(d, CONFIG, HOY)
    assert isinstance(peticion, PeticionAlbaran)
    return peticion


# ------------------------------------------------------------------ #
# R10 / R39 · sin llamadas
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("modo", MODOS)
def test_f053_r10_sin_llamadas_no_admitido(modo):
    sigrid = SigridFalso()
    repo, doc, resultado = _procesar(datos(sin_vincular(1), obra_codigo=None,
                                           valoracion_status="partial"), sigrid, modo)
    assert resultado.estado is EstadoAlta.NO_ADMITIDO
    guardado = repo.ultimo(doc)
    assert [m.codigo for m in guardado.motivos] == ["falta_obra", "no_valorado"]
    assert guardado.peticion is None and guardado.modo == modo.value
    assert sigrid.llamadas == []


@pytest.mark.parametrize("modo", MODOS)
def test_f053_r39_sin_llamadas_fecha_no_plausible(modo):
    sigrid = SigridFalso()
    futura = (HOY + timedelta(days=3)).isoformat()
    repo, doc, resultado = _procesar(datos(sin_vincular(1), fecha=futura), sigrid, modo)
    assert resultado.estado is EstadoAlta.REVISAR
    assert [m.codigo for m in repo.ultimo(doc).motivos] == ["fecha_no_plausible"]
    assert sigrid.llamadas == []


def test_f053_r39_sin_llamadas_signo_incoherente():
    sigrid = SigridFalso()
    linea = sin_vincular(4, cantidad_albaran=1.0, importe_calculado=-12.0)
    repo, doc, resultado = _procesar(datos(sin_vincular(1), linea), sigrid)
    assert resultado.estado is EstadoAlta.REVISAR
    assert [(m.codigo, m.referencia_linea) for m in repo.ultimo(doc).motivos] == [
        ("signo_incoherente", "4"),
    ]
    assert sigrid.llamadas == []


@pytest.mark.parametrize("modo", MODOS)
def test_f053_r46_otro_contrato_revisar_sin_llamadas_y_anomalia_en_el_log(modo, caplog):
    caplog.set_level(logging.INFO)
    sigrid = SigridFalso()
    d = datos(vinculada(1), vinculada(2, contrato_linea="CTOTRO/9", importe_calculado=987.65))
    repo, doc, resultado = _procesar(d, sigrid, modo)
    assert resultado.estado is EstadoAlta.REVISAR
    assert [(m.codigo, m.referencia_linea) for m in repo.ultimo(doc).motivos] == [
        ("linea_de_otro_contrato", "2"),
    ]
    assert sigrid.llamadas == []
    (aviso,) = [r for r in caplog.records if "ANOMALIA" in r.getMessage()]
    assert aviso.levelno == logging.WARNING
    texto = aviso.getMessage()
    assert DOCUMENT_ID in texto and "linea=2" in texto
    assert "CTOTRO/9" in texto and "CTSU16/0206" in texto
    assert "987" not in caplog.text and "410" not in caplog.text  # sin precios ni importes


def test_f053_r46_la_anomalia_se_registra_aunque_haya_motivos_de_r10(caplog):
    """El alta queda ``no_admitido`` por R10 (R46 no se evalúa), pero el fallo
    aguas arriba se deja en el log igualmente."""
    caplog.set_level(logging.WARNING)
    d = datos(vinculada(2, contrato_linea="CTOTRO/9"), obra_codigo=None)
    _repo, _doc, resultado = _procesar(d, SigridFalso())
    assert resultado.estado is EstadoAlta.NO_ADMITIDO
    assert "ANOMALIA" in caplog.text and "CTOTRO/9" in caplog.text


def test_f053_r46_sin_anomalia_no_hay_aviso(caplog):
    caplog.set_level(logging.WARNING)
    _procesar(datos(vinculada(1), sin_vincular(2)), SigridFalso())
    assert "ANOMALIA" not in caplog.text


# ------------------------------------------------------------------ #
# R14 · alta a mano
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("modo", MODOS)
def test_f053_r14_alta_a_mano_es_ya_en_sigrid_sin_previa(modo):
    sigrid = SigridFalso(encontrados=[AlbaranSigrid(ide=8800001, cod="AC26/900", fec=20261002),
                                      AlbaranSigrid(ide=8800002, cod="AC26/901")])
    repo, doc, resultado = _procesar(datos(sin_vincular(1)), sigrid, modo)
    assert resultado.estado is EstadoAlta.YA_EN_SIGRID
    guardado = repo.ultimo(doc)
    assert guardado.sigrid_con_ide == 8800001 and guardado.sigrid_cod == "AC26/900"
    assert [m.codigo for m in guardado.motivos] == ["alta_a_mano", "alta_a_mano"]
    assert sigrid.operaciones() == ["buscar_albaranes"]


def test_f053_r14_busca_con_cif_normalizado_numero_y_otra_referencia():
    sigrid = SigridFalso(encontrados=[AlbaranSigrid(ide=1, cod="AC26/1")])
    _procesar(datos(sin_vincular(1), proveedor_cif=" es-b00000000 ",
                    numero_albaran="  ALB-58260 "), sigrid)
    assert sigrid.llamadas == [
        ("buscar_albaranes", "B00000000", "ALB-58260", f"ALB-{DOCUMENT_ID}"),
    ]


def test_f053_r14_sin_alta_a_mano_sigue_con_la_previa():
    d = datos(sin_vincular(1))
    sigrid = SigridFalso(previa=previa_ok(_peticion(d), estado="idempotente"))
    _procesar(d, sigrid)
    assert sigrid.operaciones()[:2] == ["buscar_albaranes", "alta_albaran"]
    assert sigrid.commits() == [False]


def test_f053_r14_la_peticion_se_guarda_antes_de_llamar():
    d = datos(sin_vincular(1))
    sigrid = SigridFalso(encontrados=[AlbaranSigrid(ide=1, cod="AC26/1")])
    repo, _doc, _ = _procesar(d, sigrid)
    primero = repo.guardados[0][1]
    assert primero.estado is EstadoAlta.EN_CURSO
    assert primero.peticion == _peticion(d).a_dict()


# ------------------------------------------------------------------ #
# R15 · idempotente
# ------------------------------------------------------------------ #
def test_f053_r15_previa_idempotente_es_registrado_sin_grabar():
    d = datos(vinculada(1), sin_vincular(2))
    sigrid = SigridFalso(previa=previa_ok(_peticion(d), estado="idempotente",
                                          con_ide=9123461, cod="AC26/16004"))
    repo, doc, resultado = _procesar(d, sigrid)
    assert resultado.estado is EstadoAlta.REGISTRADO
    guardado = repo.ultimo(doc)
    assert (guardado.sigrid_con_ide, guardado.sigrid_cod) == (9123461, "AC26/16004")
    assert guardado.motivos == ()
    assert sigrid.commits() == [False]


def test_f053_r15_idempotente_con_otro_total_es_registrado_distinto():
    d = datos(vinculada(1), sin_vincular(2))
    sigrid = SigridFalso(previa=previa_ok(_peticion(d), estado="idempotente",
                                          totales={"2": 99.0}))
    repo, doc, resultado = _procesar(d, sigrid)
    assert resultado.estado is EstadoAlta.REGISTRADO
    assert [(m.codigo, m.referencia_linea) for m in repo.ultimo(doc).motivos] == [
        ("registrado_distinto", "2"),
    ]


def test_f053_r15_retomar_incierto_reenvia_la_misma_peticion():
    original = datos(sin_vincular(1), sin_vincular(2))
    guardada = _peticion(original)
    # Los datos «cambian» (no deberían: incierto bloquea sv4), y aun así se
    # reenvía lo que se mandó, no una petición nueva.
    cambiados = replace(original, lineas=(sin_vincular(1, importe_calculado=500.0),
                                          sin_vincular(2), sin_vincular(3)))
    alta = AltaActual(estado=EstadoAlta.INCIERTO, ultimo_intento_at_utc=AHORA - timedelta(hours=1),
                      peticion=guardada.a_dict())
    sigrid = SigridFalso(previa=previa_ok(guardada, estado="idempotente"))
    _repo, _doc, resultado = _procesar(cambiados, sigrid, alta=alta)
    enviada = next(c[1] for c in sigrid.llamadas if c[0] == "alta_albaran")
    assert enviada == guardada
    assert resultado.estado is EstadoAlta.REGISTRADO


def test_f053_r15_retomar_incierto_sin_peticion_guardada_la_rehace():
    d = datos(sin_vincular(1))
    alta = AltaActual(estado=EstadoAlta.INCIERTO, ultimo_intento_at_utc=AHORA - timedelta(hours=1))
    sigrid = SigridFalso(previa=previa_ok(_peticion(d), estado="idempotente"))
    _procesar(d, sigrid, alta=alta)
    enviada = next(c[1] for c in sigrid.llamadas if c[0] == "alta_albaran")
    assert enviada == _peticion(d)


def test_f053_r15_peticion_ida_y_vuelta_por_diccionario():
    peticion = _peticion(datos(vinculada(1), sin_vincular(2, codigo_partida_final=None)))
    assert PeticionAlbaran.desde_dict(peticion.a_dict()) == peticion
