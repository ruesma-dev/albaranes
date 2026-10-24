# tests/test_f069_config.py
"""F-069 · T6 · la Lista en la configuración de sv9 y la retirada de
``ALTA_SIGRID_EMPIDE`` (R1–R4).

- R1: ``ALTA_SIGRID_EQUIVALENCIAS_USUARIO`` ausente o vacía es la Lista vacía.
- R2: mal escrita, ``Settings`` no se construye y ``main_worker`` no arranca y
  deja en el log el motivo y la clave (como R44 de F-053).
- R3: al arrancar, el log dice (como información) cuántas Entradas hay; con la
  Lista vacía no hay aviso.
- R4: ``ALTA_SIGRID_EMPIDE`` ya no se lee: ni campo, ni propiedad, ni en el
  código de sv9 ni en ``.env.example``; si queda en el entorno, se ignora.
Sin red ni BBDD: ``Settings`` desde un entorno de mentira.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest
from pydantic import ValidationError

import main_worker
from config.settings import Settings
from domain.services.usuario_sigrid import Equivalencia
from tests.test_f053_t3_esqueleto import _settings

RAIZ_SV9 = Path(__file__).resolve().parents[1]
VARIABLE = "ALTA_SIGRID_EQUIVALENCIAS_USUARIO"
LISTA = '{"login1": {"usu": "login1b"}, "Login2": {"empide": 1234567}}'


# ------------------------------------------------------------------ #
# R1 · Lista ausente, vacía o válida
# ------------------------------------------------------------------ #
def test_f069_r1_config_lista_ausente_es_vacia(monkeypatch):
    assert _settings(monkeypatch).equivalencias == {}


@pytest.mark.parametrize("valor", ["", "   ", "{}"])
def test_f069_r1_config_lista_vacia(monkeypatch, valor):
    assert _settings(monkeypatch, **{VARIABLE: valor}).equivalencias == {}


def test_f069_r1_config_lista_valida_se_interpreta(monkeypatch):
    ajustes = _settings(monkeypatch, **{VARIABLE: LISTA})
    assert ajustes.equivalencias == {
        "login1": Equivalencia(usu="login1b", empide=None),
        "login2": Equivalencia(usu=None, empide=1234567),
    }
    assert Settings.model_fields["alta_sigrid_equivalencias_usuario"].alias == VARIABLE


# ------------------------------------------------------------------ #
# R2 · mal escrita: no arranca y dice por qué
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("valor, trozo", [
    ("{roto", "no es JSON"),
    ("[]", "objeto JSON"),
    ('{"login1@ruesma.es": {"usu": "a"}}', "'login1@ruesma.es'"),
    ('{"login1": {"empide": true}}', "'login1'"),
    ('{"login1": {"usu": "a"}, "LOGIN1": {"usu": "b"}}', "'LOGIN1'"),
])
def test_f069_r2_config_lista_mal_escrita_no_construye(monkeypatch, valor, trozo):
    with pytest.raises(ValidationError) as error:
        _settings(monkeypatch, **{VARIABLE: valor})
    assert VARIABLE in str(error.value) and trozo in str(error.value)


def test_f069_r2_config_main_no_arranca_y_lo_dice(monkeypatch, caplog):
    from tests.test_f053_t3_esqueleto import ENTORNO_MINIMO

    for nombre, valor in {**ENTORNO_MINIMO, VARIABLE: '{"login1": {"empide": 0}}'}.items():
        monkeypatch.setenv(nombre, valor)
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: Settings(_env_file=None))
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **_: pytest.fail("arrancó"))
    caplog.set_level(logging.INFO)
    assert main_worker.main() == 2
    assert "no arranco" in caplog.text
    assert "alta_sigrid_equivalencias_usuario" in caplog.text or VARIABLE in caplog.text
    assert "empide de 'login1'" in caplog.text


# ------------------------------------------------------------------ #
# R3 · log de arranque
# ------------------------------------------------------------------ #
def _arrancar(monkeypatch, tmp_path, caplog, **entorno) -> None:
    ajustes = _settings(monkeypatch, LOG_DIR=str(tmp_path),
                        ALTA_SIGRID_DESDE_UTC="2026-10-01T00:00:00Z",
                        ALTA_SIGRID_USUARIO_RESPALDO="pgris", **entorno)
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: ajustes)
    monkeypatch.setattr(main_worker, "configure_logging", lambda *a, **k: None)
    monkeypatch.setattr(main_worker, "construir_servicio", lambda s: object())
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **k: 0)
    caplog.set_level(logging.INFO)
    assert main_worker.main() == 0


def _registros_lista(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if VARIABLE in r.getMessage()]


def test_f069_r3_log_de_arranque_cuenta_las_entradas(monkeypatch, tmp_path, caplog):
    _arrancar(monkeypatch, tmp_path, caplog, **{VARIABLE: LISTA})
    (registro,) = _registros_lista(caplog)
    assert registro.levelno == logging.INFO
    assert re.search(r"\b2 Entradas\b", registro.getMessage())
    assert "login1" not in registro.getMessage()  # solo el número


def test_f069_r3_lista_vacia_sin_aviso(monkeypatch, tmp_path, caplog):
    _arrancar(monkeypatch, tmp_path, caplog)
    (registro,) = _registros_lista(caplog)
    assert registro.levelno == logging.INFO
    assert re.search(r"\b0 Entradas\b", registro.getMessage())
    assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []


# ------------------------------------------------------------------ #
# R4 · ALTA_SIGRID_EMPIDE ya no se lee
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("valor", ["2425207", "no-es-un-entero"])
def test_f069_r4_empide_del_entorno_se_ignora(monkeypatch, valor):
    ajustes = _settings(monkeypatch, ALTA_SIGRID_EMPIDE=valor)
    assert "alta_sigrid_empide" not in Settings.model_fields
    assert not hasattr(ajustes, "empide")


def test_f069_r4_ningun_codigo_de_sv9_lo_nombra():
    citas = [
        ruta.relative_to(RAIZ_SV9).as_posix()
        for ruta in RAIZ_SV9.rglob("*.py")
        if "tests" not in ruta.relative_to(RAIZ_SV9).parts
        and ".venv" not in ruta.parts
        and "ALTA_SIGRID_EMPIDE" in ruta.read_text(encoding="utf-8")
    ]
    assert citas == []


def test_f069_r4_env_example_sin_empide_y_con_la_lista():
    texto = (RAIZ_SV9 / ".env.example").read_text(encoding="utf-8")
    assert "ALTA_SIGRID_EMPIDE" not in texto
    assert re.search(rf"^{VARIABLE}=$", texto, re.MULTILINE)  # sin valor


# ------------------------------------------------------------------ #
# T9 · la Lista llega al servicio (un parámetro que no llega es un
# interruptor silencioso: lección de F-051)
# ------------------------------------------------------------------ #
def test_f069_r1_config_la_lista_llega_al_servicio(monkeypatch):
    from interface_adapters import composition

    servicio = composition.construir_servicio(
        _settings(monkeypatch, **{VARIABLE: LISTA}), sigrid=object(), pdf=object(),
    )
    assert servicio._equivalencias == {
        "login1": Equivalencia(usu="login1b", empide=None),
        "login2": Equivalencia(usu=None, empide=1234567),
    }
    assert not hasattr(servicio._config, "empide")
