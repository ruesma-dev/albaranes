# tests/test_f053_comun_fase2.py
"""F-053 · fase 2 · lo que sv4 y sv9 deben decidir IGUAL (``ruesma_comun``).

Regla del monorepo: la lógica compartida va a ``comun``, nunca copiada entre
servicios. En la fase 2 sv4 necesita las mismas reglas que sv9 ya aplicaba:

- T17: DESDE se lee igual en los dos (``leer_instante_utc``) y una
  configuración inválida se registra sin valores (``motivos_configuracion``,
  lección H1 de la fase 1: los secretos nunca en el log).
- T19b/T21 (R30, R40, R41, R43): «vinculada», «línea a registrar», «pasó la
  Espera» y los estados desde los que se puede repetir el alta.

Funciones puras, sin E/S.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import BaseModel, ValidationError, field_validator

from ruesma_comun import alta_sigrid as a
from ruesma_comun.configuracion import motivos_configuracion


# ------------------------------------------------------------------ #
# T17 · DESDE y configuración inválida
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("texto, esperado", [
    ("", None),
    ("   ", None),
    (None, None),
    ("2026-10-08T07:00:00+02:00", datetime(2026, 10, 8, 5, 0, tzinfo=UTC)),
    ("2026-10-08T07:00:00Z", datetime(2026, 10, 8, 7, 0, tzinfo=UTC)),
    ("2026-10-08T07:00:00", datetime(2026, 10, 8, 7, 0, tzinfo=UTC)),
    (" 2026-10-08 ", datetime(2026, 10, 8, 0, 0, tzinfo=UTC)),
])
def test_f053_colas_desde_se_lee_en_utc(texto, esperado):
    assert a.leer_instante_utc(texto) == esperado


def test_f053_colas_desde_ilegible_es_value_error():
    with pytest.raises(ValueError):
        a.leer_instante_utc("ayer por la tarde")


class _Conf(BaseModel):
    clave: str
    mapeo: str

    @field_validator("mapeo")
    @classmethod
    def _valida(cls, valor: str) -> str:
        a.leer_mapeo(valor)
        return valor


def test_f053_r44_motivos_configuracion_sin_valores():
    with pytest.raises(ValidationError) as error:
        _Conf(clave="SECRETO-NO-SALE", mapeo='{"x": "y"}')
    texto = motivos_configuracion(error.value)
    assert texto.startswith("mapeo: ")
    assert "'*'" in texto
    assert "SECRETO-NO-SALE" not in texto and '{"x": "y"}' not in texto


def test_f053_r44_motivos_configuracion_obligatorio_ausente():
    with pytest.raises(ValidationError) as error:
        _Conf.model_validate({"mapeo": '{"*": "MA9999"}', "otra": "SECRETO-NO-SALE"})
    texto = motivos_configuracion(error.value)
    assert texto == "clave: Field required"


def test_f053_r44_motivos_configuracion_varios_separados():
    with pytest.raises(ValidationError) as error:
        _Conf.model_validate({})
    assert motivos_configuracion(error.value) == "clave: Field required; mapeo: Field required"


# ------------------------------------------------------------------ #
# R30 · Espera y estados repetibles (los de sv9, R5 y R7)
# ------------------------------------------------------------------ #
AHORA = datetime(2026, 10, 8, 9, 0, tzinfo=UTC)
ESPERA = timedelta(minutes=15)


@pytest.mark.parametrize("ultimo, esperado", [
    (None, True),
    (AHORA - ESPERA, True),
    (AHORA - ESPERA + timedelta(seconds=1), False),
    (AHORA - timedelta(hours=2), True),
    (AHORA, False),
])
def test_f053_r30_espera_pasada(ultimo, esperado):
    assert a.espera_pasada(ultimo, AHORA, ESPERA) is esperado


def test_f053_r30_estados_repetibles():
    assert a.ESTADOS_ALTA_REPETIBLES == frozenset({
        "no_admitido", "revisar", "error", "simulado", "anulado",
    })
    assert not (a.ESTADOS_ALTA_REPETIBLES & a.ESTADOS_ALTA_BLOQUEANTES)


# ------------------------------------------------------------------ #
# R40, R41, R43 · vinculada y línea a registrar
# ------------------------------------------------------------------ #
def _vinculada(**cambios):
    datos = {
        "matched_contrato_line_id": 50, "derived_contrato_line_id": None,
        "sigrid_ide": 700101, "contrato_linea": "CT/1", "contrato_valoracion": "CT/1",
    }
    datos.update(cambios)
    return a.es_linea_vinculada(**datos)


def test_f053_r43_vinculada_del_glosario():
    assert _vinculada() is True
    assert _vinculada(contrato_linea=" CT/1 ", contrato_valoracion="CT/1") is True


@pytest.mark.parametrize("cambio", [
    {"matched_contrato_line_id": None},
    {"derived_contrato_line_id": 9},
    {"sigrid_ide": None},
    {"contrato_valoracion": None},
    {"contrato_valoracion": "  "},
    {"contrato_linea": "CT/2"},
    {"contrato_linea": None},
])
def test_f053_r43_sin_vincular(cambio):
    assert _vinculada(**cambio) is False


@pytest.mark.parametrize("importe, esperado", [
    (None, False), (0.0, False), (1e-10, False), (-1e-10, False),
    (0.01, True), (-0.01, True), (410.4, True),
])
def test_f053_r40_linea_a_registrar(importe, esperado):
    assert a.es_linea_a_registrar(importe) is esperado
