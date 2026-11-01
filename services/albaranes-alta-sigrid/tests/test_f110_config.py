# tests/test_f110_config.py
"""F-110 · T4 · la guarda ``ALTA_SIGRID_ENVIAR_DTO`` en sv9 (R5).

- Solo el literal ``true`` la enciende; cualquier otro valor, vacío o ausente
  la deja apagada. La lectura es la de comun (``enviar_dto_activo``, R14).
- El log de arranque dice si está encendida.
- ``composition`` pasa la guarda a ``ConfigAlta``; ``ConfigAlta`` nace apagada.
- ``.env.example`` la documenta sin valor.

Sin red ni BBDD: ``Settings`` desde un entorno de mentira.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest

import main_worker
from domain.services.validador_alta import ConfigAlta
from interface_adapters import composition
from tests.f053_fakes import PdfFalso, SigridFalso
from tests.test_f053_t3_esqueleto import _settings

RAIZ_SV9 = Path(__file__).resolve().parents[1]
VARIABLE = "ALTA_SIGRID_ENVIAR_DTO"


def _ajustes(monkeypatch, **entorno):
    monkeypatch.delenv(VARIABLE, raising=False)
    return _settings(monkeypatch, **entorno)


# ------------------------------------------------------------------ R5
def test_f110_r5_apagada_por_defecto(monkeypatch):
    ajustes = _ajustes(monkeypatch)
    assert ajustes.alta_sigrid_enviar_dto == "false"
    assert ajustes.enviar_dto is False


def test_f110_r5_encendida_solo_con_el_literal(monkeypatch):
    assert _ajustes(monkeypatch, **{VARIABLE: "true"}).enviar_dto is True


@pytest.mark.parametrize("valor", ["True", "TRUE", " true", "true ", "1", "si", "false", ""])
def test_f110_r5_cualquier_otro_valor_la_deja_apagada(monkeypatch, valor):
    assert _ajustes(monkeypatch, **{VARIABLE: valor}).enviar_dto is False


def test_f110_r5_lee_con_la_funcion_de_comun(monkeypatch):
    import config.settings as modulo

    llamadas = []

    def espia(valor):
        llamadas.append(valor)
        return True

    monkeypatch.setattr(modulo, "enviar_dto_activo", espia)
    assert _ajustes(monkeypatch, **{VARIABLE: "x"}).enviar_dto is True
    assert llamadas == ["x"]


def test_f110_r5_config_alta_nace_apagada():
    assert ConfigAlta(mapeo={"*": "MA9999"}).enviar_dto is False


@pytest.mark.parametrize("valor, activo", [("true", True), ("false", False)])
def test_f110_r5_composition_pasa_la_guarda(monkeypatch, valor, activo):
    ajustes = _ajustes(monkeypatch, **{VARIABLE: valor})
    servicio = composition.construir_servicio(
        ajustes, engine=object(), sigrid=SigridFalso(), pdf=PdfFalso(),  # type: ignore[arg-type]
    )
    assert servicio._config.enviar_dto is activo  # noqa: SLF001
    assert servicio._config.mapeo == ajustes.mapeo_producto  # noqa: SLF001


# ----------------------------------------------------- R5 · log de arranque
def _arrancar(monkeypatch, tmp_path, caplog, **entorno) -> None:
    ajustes = _ajustes(monkeypatch, LOG_DIR=str(tmp_path),
                       ALTA_SIGRID_DESDE_UTC="2026-10-01T00:00:00Z",
                       ALTA_SIGRID_USUARIO_RESPALDO="pgris", **entorno)
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: ajustes)
    monkeypatch.setattr(main_worker, "configure_logging", lambda *a, **k: None)
    monkeypatch.setattr(main_worker, "construir_servicio", lambda s: object())
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **k: 0)
    caplog.set_level(logging.INFO)
    assert main_worker.main() == 0


def _registros(caplog) -> list[logging.LogRecord]:
    return [r for r in caplog.records if VARIABLE in r.getMessage()]


def test_f110_r5_log_dice_apagada(monkeypatch, tmp_path, caplog):
    _arrancar(monkeypatch, tmp_path, caplog)
    (registro,) = _registros(caplog)
    assert registro.levelno == logging.INFO
    assert "apagada" in registro.getMessage()
    assert "encendida" not in registro.getMessage()


def test_f110_r5_log_dice_encendida(monkeypatch, tmp_path, caplog):
    _arrancar(monkeypatch, tmp_path, caplog, **{VARIABLE: "true"})
    (registro,) = _registros(caplog)
    assert "encendida" in registro.getMessage()
    assert "apagada" not in registro.getMessage()


# ------------------------------------------------------- R20 · .env.example
def test_f110_r20_env_example_la_documenta_sin_valor():
    texto = (RAIZ_SV9 / ".env.example").read_text(encoding="utf-8")
    lineas = [l for l in texto.splitlines() if l.startswith(f"{VARIABLE}=")]
    assert lineas == [f"{VARIABLE}="]
    anterior = texto[:texto.index(f"{VARIABLE}=")].splitlines()[-1]
    assert anterior.startswith("#") and "true" in anterior
