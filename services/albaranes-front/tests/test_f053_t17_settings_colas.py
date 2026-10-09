# tests/test_f053_t17_settings_colas.py
"""F-053 · T17 · configuración del alta en sv4 y adaptador de colas.

- Settings (design §7): ``ALTA_SIGRID_DESDE_UTC`` (vacía = feature apagada),
  ``ALTA_SIGRID_ESPERA_INCIERTO_MIN`` (15) y ``ALTA_SIGRID_PRODUCTO_POR_DEFECTO``
  (leído con ``ruesma_comun.alta_sigrid.leer_mapeo``), con el mismo valor que sv9.
- R44: con el mapeo mal formado sv4 NO arranca y deja el motivo en el log, sin
  volcar los valores del entorno (lección H1 de la fase 1: secretos nunca en logs).
- Colas: ``notify_document_approved`` devuelve si publicó y
  ``solicitar_alta_sigrid(document_id, accion)`` publica ``MensajeFeedback`` en
  ``q-feedback`` con su ``accion`` (R1, R28, R30, R32).

Sin red ni BBDD: publicador falso.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError
from ruesma_comun.alta_sigrid import MAPEO_PRODUCTO_POR_DEFECTO
from ruesma_comun.colas import COLA_FEEDBACK
from ruesma_comun.colas.mensajes import MensajeFeedback

SECRETOS = {"PG_PASSWORD": "clave-pg-secreta", "PG_ADMIN_PASSWORD": "clave-admin-secreta"}


def _settings(**entorno):
    from config.settings import Settings

    return Settings(_env_file=None, **{**SECRETOS, **entorno})


# ------------------------------------------------------------------ #
# Settings
# ------------------------------------------------------------------ #
def test_f053_r44_defectos_feature_apagada():
    ajustes = _settings()
    assert ajustes.alta_sigrid_desde is None
    assert ajustes.alta_sigrid_espera == timedelta(minutes=15)
    assert ajustes.mapeo_producto == MAPEO_PRODUCTO_POR_DEFECTO
    config = ajustes.config_alta_sigrid
    assert config.activa is False
    assert config.desde is None and config.espera == timedelta(minutes=15)
    assert dict(config.mapeo) == MAPEO_PRODUCTO_POR_DEFECTO


def test_f053_r44_desde_espera_y_mapeo_leidos():
    ajustes = _settings(
        ALTA_SIGRID_DESDE_UTC="2026-10-08T07:00:00+02:00",
        ALTA_SIGRID_ESPERA_INCIERTO_MIN="30",
        ALTA_SIGRID_PRODUCTO_POR_DEFECTO='{"*": "MA9999", "residuos": "XA9999"}',
    )
    config = ajustes.config_alta_sigrid
    assert config.activa is True
    assert config.desde == datetime(2026, 10, 8, 5, 0, tzinfo=UTC)
    assert config.espera == timedelta(minutes=30)
    assert dict(config.mapeo) == {"*": "MA9999", "residuos": "XA9999"}
    assert config.admitidos == frozenset({"MA9999", "XA9999"})


def test_f053_r44_desde_sin_zona_es_utc():
    ajustes = _settings(ALTA_SIGRID_DESDE_UTC="2026-10-08T07:00:00")
    assert ajustes.alta_sigrid_desde == datetime(2026, 10, 8, 7, 0, tzinfo=UTC)


@pytest.mark.parametrize("variable", [
    "ALTA_SIGRID_DESDE_UTC", "ALTA_SIGRID_ESPERA_INCIERTO_MIN",
    "ALTA_SIGRID_PRODUCTO_POR_DEFECTO",
])
def test_f053_r44_variable_vacia_vale_su_defecto(variable):
    """Como en sv9 (``env_ignore_empty``): ``X=`` es el defecto, no un error."""
    ajustes = _settings(**{variable: ""})
    assert ajustes.config_alta_sigrid.activa is False
    assert ajustes.alta_sigrid_espera == timedelta(minutes=15)
    assert ajustes.mapeo_producto == MAPEO_PRODUCTO_POR_DEFECTO


@pytest.mark.parametrize("mapeo, motivo", [
    ("{no es json", "no es JSON"),
    ('["MA9999"]', "objeto JSON"),
    ('{"residuos": "XA9999"}', "'*'"),
    ('{"*": ""}', "texto no vacío"),
])
def test_f053_r44_mapeo_mal_formado_no_arranca(mapeo, motivo):
    with pytest.raises(ValidationError) as error:
        _settings(ALTA_SIGRID_PRODUCTO_POR_DEFECTO=mapeo)
    assert motivo in str(error.value)


@pytest.mark.parametrize("variable, valor", [
    ("ALTA_SIGRID_DESDE_UTC", "ayer por la tarde"),
    ("ALTA_SIGRID_ESPERA_INCIERTO_MIN", "-1"),
])
def test_f053_r44_desde_o_espera_ilegibles_no_arrancan(variable, valor):
    with pytest.raises(ValidationError):
        _settings(**{variable: valor})


def test_f053_r44_main_no_arranca_y_dice_el_motivo_sin_secretos(monkeypatch, caplog):
    import main as modulo_main

    for clave, valor in SECRETOS.items():
        monkeypatch.setenv(clave, valor)
    monkeypatch.setenv("ALTA_SIGRID_PRODUCTO_POR_DEFECTO", '{"residuos": "XA9999"}')
    monkeypatch.setattr(modulo_main, "load_dotenv", lambda *a, **k: None)
    arrancado = []
    monkeypatch.setattr(modulo_main, "build_app", lambda s: arrancado.append(s))
    monkeypatch.setattr(modulo_main.uvicorn, "run", lambda *a, **k: arrancado.append(a))

    with caplog.at_level(logging.ERROR):
        codigo = modulo_main.main()

    assert codigo == 2
    assert arrancado == []
    texto = caplog.text
    assert "ALTA_SIGRID_PRODUCTO_POR_DEFECTO" in texto and "'*'" in texto
    for valor in SECRETOS.values():
        assert valor not in texto


# ------------------------------------------------------------------ #
# Colas
# ------------------------------------------------------------------ #
class _Publicador:
    def __init__(self, resultado=True):
        self.resultado = resultado
        self.publicados: list[tuple[str, object]] = []

    def publicar(self, nombre_cola, mensaje):
        self.publicados.append((nombre_cola, mensaje))
        return self.resultado


def _cliente(resultado=True):
    from infrastructure.colas.colas_orchestrator_client import (
        ColasOrchestratorClient,
    )

    publicador = _Publicador(resultado)
    return ColasOrchestratorClient(publicador=publicador), publicador


@pytest.mark.parametrize("resultado", [True, False])
def test_f053_colas_aprobado_devuelve_si_publico(resultado):
    cliente, publicador = _cliente(resultado)

    publicado = cliente.notify_document_approved(
        document_id="d1", approved_by="ana", approved_at_utc="2026-10-08T07:00:00Z",
        review_notes=None,
    )

    assert publicado is resultado
    ((cola, mensaje),) = publicador.publicados
    assert cola == COLA_FEEDBACK
    assert isinstance(mensaje, MensajeFeedback)
    assert (mensaje.document_id, mensaje.approved_by, mensaje.accion) == ("d1", "ana", "alta")


@pytest.mark.parametrize("accion", ["alta", "verificar_anulacion"])
@pytest.mark.parametrize("resultado", [True, False])
def test_f053_colas_solicitar_alta_sigrid(accion, resultado):
    cliente, publicador = _cliente(resultado)

    publicado = cliente.solicitar_alta_sigrid(
        document_id="d1", accion=accion, solicitado_por="luis",
    )

    assert publicado is resultado
    ((cola, mensaje),) = publicador.publicados
    assert cola == COLA_FEEDBACK
    assert isinstance(mensaje, MensajeFeedback)
    assert (mensaje.document_id, mensaje.approved_by, mensaje.accion) == ("d1", "luis", accion)


def test_f053_colas_accion_desconocida_no_publica():
    cliente, publicador = _cliente()
    with pytest.raises(ValueError):
        cliente.solicitar_alta_sigrid(document_id="d1", accion="borrar", solicitado_por=None)
    assert publicador.publicados == []


def test_f053_colas_el_puerto_declara_las_dos_operaciones():
    from domain.ports.orchestrator_port import OrchestratorClient

    assert "solicitar_alta_sigrid" in OrchestratorClient.__abstractmethods__
    assert "notify_document_approved" in OrchestratorClient.__abstractmethods__
