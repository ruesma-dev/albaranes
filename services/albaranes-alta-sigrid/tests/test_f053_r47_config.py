# tests/test_f053_r47_config.py
"""F-053 v8 · T44 (U4, U5) · ``ALTA_SIGRID_USUARIO`` pasa a ``ALTA_SIGRID_USUARIO_RESPALDO``.

- La variable nueva llega al servicio como Respaldo (R47); la vieja ya no se lee.
- Sin defecto en código: vacía si no se pone (y entonces, con DESDE puesta, el
  arranque avisa: las altas sin coincidencia irán a ``error``, R48).
- ``.env.example`` y los scripts de ``infra/`` usan el MISMO nombre que lee
  ``Settings`` (un nombre distinto sería un interruptor silencioso), y el
  valor versionado del Respaldo es ``pgris`` (U5; no es secreto).
Sin red ni BBDD: ``Settings`` desde un entorno de mentira.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest

import main_worker
from config.settings import Settings
from interface_adapters import composition
from tests.test_f053_t3_esqueleto import _settings

RAIZ_SV9 = Path(__file__).resolve().parents[1]
INFRA = RAIZ_SV9.parents[1] / "infra"
NUEVA = "ALTA_SIGRID_USUARIO_RESPALDO"
VIEJA = re.compile(r"ALTA_SIGRID_USUARIO(?!_RESPALDO)")


def test_f053_r47_config_lee_el_respaldo_con_el_nombre_nuevo(monkeypatch):
    ajustes = _settings(monkeypatch, ALTA_SIGRID_USUARIO_RESPALDO="pgris")
    assert ajustes.usuario_respaldo == "pgris"
    assert Settings.model_fields["usuario_respaldo"].alias == NUEVA
    assert "usuario" not in Settings.model_fields


def test_f053_r47_config_el_nombre_viejo_ya_no_se_lee_y_no_hay_defecto(monkeypatch):
    ajustes = _settings(monkeypatch, ALTA_SIGRID_USUARIO="pgris")
    assert ajustes.usuario_respaldo == ""


def test_f053_r47_config_llega_al_servicio_como_respaldo(monkeypatch):
    servicio = composition.construir_servicio(
        _settings(monkeypatch, ALTA_SIGRID_USUARIO_RESPALDO=" pgris "),
        sigrid=object(), pdf=object(),
    )
    assert servicio._respaldo == "pgris"


@pytest.mark.parametrize("desde, respaldo, aviso", [
    ("", "", False),
    ("2026-10-01T00:00:00Z", "", True),
    ("2026-10-01T00:00:00Z", "pgris", False),
])
def test_f053_r47_config_aviso_de_arranque_sin_respaldo(monkeypatch, tmp_path, caplog,
                                                        desde, respaldo, aviso):
    ajustes = _settings(monkeypatch, LOG_DIR=str(tmp_path)).model_copy(
        update={"alta_sigrid_desde_utc": desde, "usuario_respaldo": respaldo})
    monkeypatch.setattr(main_worker, "_cargar_entorno", lambda: None)
    monkeypatch.setattr(main_worker, "Settings", lambda: ajustes)
    monkeypatch.setattr(main_worker, "configure_logging", lambda *a, **k: None)
    monkeypatch.setattr(main_worker, "construir_servicio", lambda s: object())
    monkeypatch.setattr(main_worker, "ejecutar_worker", lambda **k: 0)
    caplog.set_level(logging.INFO)
    assert main_worker.main() == 0
    assert (f"{NUEVA} vacío" in caplog.text) is aviso


def test_f053_r47_config_env_example_con_el_nombre_nuevo():
    texto = (RAIZ_SV9 / ".env.example").read_text(encoding="utf-8")
    assert re.search(rf"^{NUEVA}=$", texto, re.MULTILINE)  # sin valor
    assert not VIEJA.search(texto)


@pytest.mark.parametrize("script", ["00_capps_vars.ps1", "create_capps_sv9.ps1",
                                    "set_alta_sigrid.ps1", "README_capps.md"])
def test_f053_r47_config_infra_usa_el_nombre_nuevo(script):
    texto = (INFRA / script).read_text(encoding="utf-8-sig")
    assert NUEVA in texto
    assert not VIEJA.search(texto)


def test_f053_r47_config_infra_respaldo_pgris_versionado_y_pasado_a_sv9():
    variables = (INFRA / "00_capps_vars.ps1").read_text(encoding="utf-8-sig")
    assert re.search(rf'^\$Global:{NUEVA}\s*=\s*"pgris"', variables, re.MULTILINE)
    par = f'"{NUEVA}=$($Global:{NUEVA})"'
    assert par in (INFRA / "create_capps_sv9.ps1").read_text(encoding="utf-8-sig")
    assert par in (INFRA / "set_alta_sigrid.ps1").read_text(encoding="utf-8-sig")
