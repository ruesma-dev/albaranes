# tests/test_f110_ficha.py
"""F-110 · T10 · la ficha de sv4 con la guarda del descuento (R14–R16).

- R14: ``Settings`` lee ``ALTA_SIGRID_ENVIAR_DTO`` con la función de comun
  (solo el literal ``true``); ``ConfigAltaSigrid`` y el repositorio la reciben.
- R15: «A Sigrid» usa ``linea_a_sigrid`` con ``con_descuento`` = la guarda: con
  ``dto``, «A Sigrid: 12 × 0,645 € −7 %»; visible si el precio a Sigrid difiere
  de P en más de 0,000001 o el ``dto`` a Sigrid difiere de d. Apagada, el texto
  y la visibilidad de F-106.
- R16: la ficha marca la guarda con ``data-alta-dto`` (en el precio, junto a
  ``data-factor-alta``) para que el JS repinte con la misma regla.

Dominio puro, repositorio real sobre SQLite (``f065_bbdd``) y la plantilla real.
"""
from __future__ import annotations

import re

import pytest
from f065_bbdd import DOC, Fabrica
from test_f106_fila import FILA, cecois

from domain.models.review_models import a_sigrid_de_fila

VARIABLE = "ALTA_SIGRID_ENVIAR_DTO"


# =================================================================== #
# R14 · Settings
# =================================================================== #
def _ajustes(monkeypatch, valor=None):
    from config.settings import Settings

    monkeypatch.delenv(VARIABLE, raising=False)
    if valor is not None:
        monkeypatch.setenv(VARIABLE, valor)
    return Settings(_env_file=None, PG_PASSWORD="x", PG_ADMIN_PASSWORD="x")


def test_f110_r14_apagada_por_defecto(monkeypatch):
    ajustes = _ajustes(monkeypatch)
    assert ajustes.enviar_dto is False
    assert ajustes.config_alta_sigrid.enviar_dto is False


def test_f110_r14_encendida_solo_con_el_literal(monkeypatch):
    ajustes = _ajustes(monkeypatch, "true")
    assert ajustes.enviar_dto is True
    assert ajustes.config_alta_sigrid.enviar_dto is True


@pytest.mark.parametrize("valor", ["True", " true", "1", "false", ""])
def test_f110_r14_otros_valores_apagada(monkeypatch, valor):
    assert _ajustes(monkeypatch, valor).enviar_dto is False


def test_f110_r14_lee_con_la_funcion_de_comun(monkeypatch):
    import config.settings as modulo

    vistos = []
    monkeypatch.setattr(modulo, "enviar_dto_activo", lambda v: vistos.append(v) or True)
    assert _ajustes(monkeypatch, "x").enviar_dto is True
    assert vistos == ["x"]


def test_f110_r14_config_alta_nace_apagada():
    from domain.models.alta_sigrid_models import ConfigAltaSigrid

    assert ConfigAltaSigrid().enviar_dto is False


@pytest.mark.parametrize("valor, activo", [("true", True), ("false", False)])
def test_f110_r14_build_app_pasa_la_guarda_al_repositorio(monkeypatch, valor, activo):
    from config.settings import Settings
    from interface_adapters.web import app as modulo_app

    recibido = []
    monkeypatch.setattr(modulo_app, "SessionFactory", lambda **_: object())
    monkeypatch.setattr(modulo_app, "AlbaranReviewRepository",
                        lambda *a: recibido.append(a) or object())
    monkeypatch.setattr(modulo_app, "WorkflowRunsPurger", lambda *_: object())

    class _Servicio:
        def initialize(self):
            return True

    monkeypatch.setattr(modulo_app, "ReviewService", lambda *_: _Servicio())
    monkeypatch.setattr(modulo_app, "construir_publicador", lambda **_: object())
    ajustes = Settings.model_construct(pg_password="x", pg_admin_password="x",
                                       alta_sigrid_enviar_dto=valor)
    modulo_app.build_app(ajustes)
    ((_fabrica, guarda),) = recibido
    assert guarda is activo


# =================================================================== #
# R15 · A Sigrid (dominio)
# =================================================================== #
def _cecois(**cambios):
    base = {"vinculada": False, "cantidad_albaran": 12.0, "cantidad_convertida": None,
            "precio": 0.645, "descuento": 7.0, "importe": 7.20}
    base.update(cambios)
    return base


def test_f110_r15_cecois_con_la_guarda():
    a = a_sigrid_de_fila(**_cecois(), con_descuento=True)
    assert (a.texto, a.difiere, a.factor) == ("A Sigrid: 12 × 0,645 € −7 %", False, 1.0)


def test_f110_r15_cecois_sin_la_guarda_es_f106():
    a = a_sigrid_de_fila(**_cecois())
    assert (a.texto, a.difiere) == ("A Sigrid: 12 × 0,60 €", True)
    assert a_sigrid_de_fila(**_cecois(), con_descuento=False) == a


def test_f110_r15_precio_despejado_se_ve():
    a = a_sigrid_de_fila(**_cecois(cantidad_albaran=10.0, precio=26.796, importe=249.21),
                         con_descuento=True)
    assert (a.texto, a.difiere) == ("A Sigrid: 10 × 26,796774 € −7 %", True)


def test_f110_r15_dto_redondeado_distinto_de_d_se_ve():
    a = a_sigrid_de_fila(**_cecois(cantidad_albaran=10.0, precio=10.0, descuento=7.456,
                                   importe=92.54), con_descuento=True)
    assert (a.texto, a.difiere) == ("A Sigrid: 10 × 10,00 € −7,46 %", True)


def test_f110_r15_sin_descuento_con_la_guarda_como_f106():
    con = a_sigrid_de_fila(**_cecois(descuento=None, precio=0.6), con_descuento=True)
    sin = a_sigrid_de_fila(**_cecois(descuento=None, precio=0.6))
    assert con == sin
    assert (con.texto, con.difiere) == ("A Sigrid: 12 × 0,60 €", False)


def test_f110_r15_descuento_invalido_no_cuenta_como_diferencia():
    a = a_sigrid_de_fila(**_cecois(descuento=150.0, precio=0.6), con_descuento=True)
    assert (a.texto, a.difiere) == ("A Sigrid: 12 × 0,60 €", False)


def test_f110_r15_descuento_que_redondea_a_cero_se_ve():
    """d 0,004 va sin ``dto`` (a Sigrid 0 %): difiere de la ficha."""
    a = a_sigrid_de_fila(**_cecois(cantidad_albaran=10.0, precio=10.0, descuento=0.004,
                                   importe=100.0), con_descuento=True)
    assert (a.texto, a.difiere) == ("A Sigrid: 10 × 10,00 €", True)


def test_f110_r15_cien_por_cien_sin_a_sigrid():
    assert a_sigrid_de_fila(**_cecois(descuento=100.0), con_descuento=True) is None


def test_f110_r15_borde_de_la_tolerancia_del_precio():
    """P con 7 decimales: a Sigrid va a 6 (0,6450004 → 0,645), dentro de 1e-6."""
    a = a_sigrid_de_fila(**_cecois(precio=0.6450004), con_descuento=True)
    assert (a.texto, a.difiere) == ("A Sigrid: 12 × 0,645 € −7 %", False)


def test_f110_r15_devolucion():
    a = a_sigrid_de_fila(**_cecois(cantidad_albaran=-1.0, precio=18.0, descuento=10.0,
                                   importe=-16.2), con_descuento=True)
    assert (a.texto, a.difiere, a.factor) == ("A Sigrid: -1 × 18,00 € −10 %", False, 1.0)


# =================================================================== #
# R15 · repositorio (la vista de la ficha)
# =================================================================== #
def _repositorio(motor, enviar_dto):
    from infrastructure.database.review_repository import AlbaranReviewRepository

    repo = AlbaranReviewRepository(Fabrica(motor), enviar_dto)  # type: ignore[arg-type]
    repo.initialize = lambda: True  # type: ignore[method-assign]
    repo._undo_table_ready = True  # type: ignore[attr-defined]
    return repo


def _detalle(enviar_dto):
    return _repositorio(cecois(), enviar_dto).get_document_detail(DOC)


def _concilia(detalle):
    return next(d for d in detalle.display_lines if d.valuation_line_id == FILA).concilia


def test_f110_r15_repositorio_con_la_guarda():
    detalle = _detalle(True)
    c = _concilia(detalle)
    assert (c.a_sigrid, c.a_sigrid_difiere) == ("A Sigrid: 10 × 11,20 € −7 %", False)
    assert detalle.alta_enviar_dto is True


def test_f110_r15_repositorio_sin_la_guarda_es_f106():
    detalle = _detalle(False)
    c = _concilia(detalle)
    assert (c.a_sigrid, c.a_sigrid_difiere) == ("A Sigrid: 10 × 10,416 €", True)
    assert detalle.alta_enviar_dto is False


def test_f110_r15_repositorio_nace_apagado():
    from f065_bbdd import repositorio

    assert _concilia(repositorio(cecois()).get_document_detail(DOC)).a_sigrid == (
        "A Sigrid: 10 × 10,416 €")


# =================================================================== #
# R16 · plantilla
# =================================================================== #
def _precio_input(html):
    return re.search(r'<input[^>]*data-field="precio_unitario"[^>]*>', html).group(0)


@pytest.mark.parametrize("guarda", [True, False])
def test_f110_r16_data_alta_dto_en_el_precio(
    guarda, render_detalle, documento_detalle, linea_valorada, fila_detalle,
):
    documento = documento_detalle(
        lineas_valoracion=[linea_valorada()],
        display=[fila_detalle(conciliacion={"a_sigrid": "A Sigrid: 6 × 20,00 € −7 %",
                                             "factor_alta": 1.0})],
    ).model_copy(update={"alta_enviar_dto": guarda})
    entrada = _precio_input(render_detalle(documento))
    assert 'data-factor-alta="1.0"' in entrada
    assert ('data-alta-dto="1"' in entrada) is guarda
    assert "data-alta-dto" in entrada or not guarda
