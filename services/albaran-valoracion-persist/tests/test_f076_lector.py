# tests/test_f076_lector.py
"""F-076 T6 · configuración de sv6 para sigrid-api y su lector (R17, R18).

- R17: sv6 lee ``SIGRID_API_*`` y ``PARTIDAS_OBRA_*`` con sus valores por defecto.
- R18: el lector usa solo ``POST /api/sql/read``, reintenta con tenacity los
  fallos transitorios (5xx, tiempo agotado, conexión), no reintenta un 4xx y
  no registra la clave ni el cuerpo de la respuesta.

Sin red: ``httpx.MockTransport``.
"""
from __future__ import annotations

import json
import logging

import httpx
import pytest
from infrastructure.sigrid.sigrid_api_lector import SigridApiLector, SigridLecturaError
from ruesma_comun.sigrid import (
    MAX_FILAS_POR_PETICION,
    SQL_PARTIDAS_POR_OBRA,
    LectorSql,
    PoliticaTruncado,
    SigridRespuestaTruncada,
    leer_partidas_obra,
)

_CLAVE = "clave-secreta-de-test-f076"
_SECRETO_EN_CUERPO = "TEXTO-DEL-CUERPO-QUE-NO-DEBE-SALIR"
_COLUMNAS = ["ide", "padide", "cod", "res"]
_FILAS = [[1, None, "CI", "Costes indirectos"], [2, 1, "CI.4.18", _SECRETO_EN_CUERPO]]


class _Api:
    """sigrid-api falsa: responde en orden lo que se le programe."""

    def __init__(self, *respuestas) -> None:
        self.respuestas = list(respuestas)
        self.peticiones: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        siguiente = self.respuestas.pop(0)
        if isinstance(siguiente, Exception):
            raise siguiente
        return siguiente


def _ok(filas=None, truncated=False, ok=True) -> httpx.Response:
    return httpx.Response(200, json={"ok": ok, "columns": _COLUMNAS, "rows": _FILAS if filas is None else filas,
                                     "truncated": truncated})


def _lector(api: _Api, **kw) -> SigridApiLector:
    return SigridApiLector(
        base_url="https://sigrid.invalid/", function_key=_CLAVE, database="db-test", timeout_s=12.0,
        espera_base_s=0.0, transport=httpx.MockTransport(api), **kw,
    )


def _leer(lector, max_rows=500_000, politica=PoliticaTruncado.NO_TOLERA):
    return lector(SQL_PARTIDAS_POR_OBRA, ["0678"], "partidas_obra_0678", politica, max_rows)


# ------------------------------------------------------------------ #
# R18 · solo sql/read, con la clave en la cabecera
# ------------------------------------------------------------------ #
def test_f076_r18_post_a_sql_read_con_cuerpo_y_cabecera():
    api = _Api(_ok())
    columnas, filas = _leer(_lector(api))
    assert (columnas, filas) == (_COLUMNAS, _FILAS)
    (peticion,) = api.peticiones
    assert peticion.method == "POST"
    assert str(peticion.url) == "https://sigrid.invalid/api/sql/read"
    assert peticion.headers["x-functions-key"] == _CLAVE
    assert json.loads(peticion.content) == {
        "database": "db-test", "sql": SQL_PARTIDAS_POR_OBRA, "parameters": ["0678"],
        "timeout_seconds": 12, "max_rows": 500_000,
    }


def test_f076_r18_es_un_lector_sql_de_comun():
    api = _Api(_ok())
    lector: LectorSql = _lector(api)
    lista = leer_partidas_obra(lector, "678")
    assert lista is not None and lista.codigos == ("CI.4.18",) and lista.no_hojas == ("CI",)
    assert json.loads(api.peticiones[0].content)["max_rows"] == MAX_FILAS_POR_PETICION


@pytest.mark.parametrize(
    "transitorio",
    [httpx.Response(503, text="caido"), httpx.Response(500), httpx.ReadTimeout("lento"),
     httpx.ConnectError("sin red")],
    ids=["503", "500", "timeout", "conexion"],
)
def test_f076_r18_reintenta_los_transitorios(transitorio):
    api = _Api(transitorio, _ok())
    assert _leer(_lector(api))[1] == _FILAS
    assert len(api.peticiones) == 2


def test_f076_r18_agotados_los_intentos_falla():
    api = _Api(httpx.Response(503), httpx.Response(502), httpx.Response(504))
    with pytest.raises(SigridLecturaError):
        _leer(_lector(api))
    assert len(api.peticiones) == 3


def test_f076_r18_tres_intentos_por_defecto():
    api = _Api(httpx.ConnectError("x"), httpx.ConnectError("x"), httpx.ConnectError("x"), _ok())
    with pytest.raises(SigridLecturaError):
        _leer(_lector(api))
    assert len(api.peticiones) == 3


@pytest.mark.parametrize("estado", [400, 401, 403, 404, 422])
def test_f076_r18_un_4xx_no_se_reintenta(estado):
    api = _Api(httpx.Response(estado, text=_SECRETO_EN_CUERPO), _ok())
    with pytest.raises(SigridLecturaError) as exc:
        _leer(_lector(api))
    assert len(api.peticiones) == 1
    assert str(estado) in str(exc.value)
    assert _SECRETO_EN_CUERPO not in str(exc.value)


@pytest.mark.parametrize(
    "respuesta",
    [_ok(ok=False), httpx.Response(200, text="no es json"), httpx.Response(200, json=[1, 2])],
    ids=["ok_false", "no_json", "no_dict"],
)
def test_f076_r18_respuesta_no_valida_lanza(respuesta):
    with pytest.raises(SigridLecturaError):
        _leer(_lector(_Api(respuesta)))


def test_f076_r18_truncado_con_no_tolera_lanza():
    with pytest.raises(SigridRespuestaTruncada) as exc:
        _leer(_lector(_Api(_ok(truncated=True))))
    assert exc.value.etiqueta == "partidas_obra_0678"


def test_f076_r18_truncado_con_tolera_devuelve_las_filas():
    assert _leer(_lector(_Api(_ok(truncated=True))), politica=PoliticaTruncado.TOLERA)[1] == _FILAS


def test_f076_r18_sin_columnas_ni_filas():
    api = _Api(httpx.Response(200, json={"ok": True}))
    assert _leer(_lector(api)) == ([], [])


def test_f076_r18_el_log_no_lleva_la_clave_ni_el_cuerpo(caplog):
    api = _Api(httpx.Response(503, text=_SECRETO_EN_CUERPO), _ok(), httpx.Response(400, text=_SECRETO_EN_CUERPO))
    with caplog.at_level(logging.DEBUG):
        lector = _lector(api)
        _leer(lector)
        with pytest.raises(SigridLecturaError):
            _leer(lector)
    texto = "\n".join(r.getMessage() for r in caplog.records)
    assert "partidas_obra_0678" in texto and "200" in texto  # etiqueta, estado
    assert "filas=2" in texto
    assert _CLAVE not in texto
    assert _SECRETO_EN_CUERPO not in texto
    assert _CLAVE not in repr(lector)


@pytest.mark.parametrize(
    "faltante", [{"base_url": ""}, {"function_key": ""}, {"database": ""}],
)
def test_f076_r18_exige_url_clave_y_base(faltante):
    datos = {"base_url": "https://sigrid.invalid", "function_key": _CLAVE, "database": "db"}
    datos.update(faltante)
    with pytest.raises(ValueError):
        SigridApiLector(**datos)


# ------------------------------------------------------------------ #
# R17 · configuración
# ------------------------------------------------------------------ #
_VARIABLES_R17 = (
    "SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE", "SIGRID_API_TIMEOUT_S",
    "PARTIDAS_OBRA_NORMALIZAR_ENABLED", "PARTIDAS_OBRA_TTL_S", "PARTIDAS_OBRA_MAX_OBRAS",
    "PARTIDAS_OBRA_FALLO_TTL_S",
)


def _ajustes(monkeypatch, **entorno):
    from config.settings import Settings

    for nombre in _VARIABLES_R17:
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)
    return Settings(_env_file=None, PG_USER="u", PG_PASSWORD="p")


def test_f076_r17_valores_por_defecto(monkeypatch):
    ajustes = _ajustes(monkeypatch)
    assert ajustes.sigrid_api_base_url is None
    assert ajustes.sigrid_api_function_key is None
    assert ajustes.sigrid_api_database is None
    assert ajustes.sigrid_api_timeout_s == 30.0
    assert ajustes.partidas_obra_normalizar_enabled is True
    assert ajustes.partidas_obra_ttl_s == 21600
    assert ajustes.partidas_obra_max_obras == 64
    assert ajustes.partidas_obra_fallo_ttl_s == 300
    assert ajustes.sigrid_api_configurada is False


def test_f076_r17_lee_el_entorno(monkeypatch):
    ajustes = _ajustes(
        monkeypatch, SIGRID_API_BASE_URL="https://sigrid.invalid", SIGRID_API_FUNCTION_KEY=_CLAVE,
        SIGRID_API_DATABASE="db", SIGRID_API_TIMEOUT_S="45", PARTIDAS_OBRA_NORMALIZAR_ENABLED="false",
        PARTIDAS_OBRA_TTL_S="60", PARTIDAS_OBRA_MAX_OBRAS="8", PARTIDAS_OBRA_FALLO_TTL_S="5",
    )
    assert (ajustes.sigrid_api_base_url, ajustes.sigrid_api_function_key, ajustes.sigrid_api_database) == (
        "https://sigrid.invalid", _CLAVE, "db")
    assert ajustes.sigrid_api_timeout_s == 45.0
    assert ajustes.partidas_obra_normalizar_enabled is False
    assert (ajustes.partidas_obra_ttl_s, ajustes.partidas_obra_max_obras, ajustes.partidas_obra_fallo_ttl_s) == (
        60, 8, 5)
    assert ajustes.sigrid_api_configurada is True


@pytest.mark.parametrize(
    "faltante", ["SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY", "SIGRID_API_DATABASE"],
)
def test_f076_r17_sin_url_clave_o_base_no_esta_configurada(monkeypatch, faltante):
    entorno = {"SIGRID_API_BASE_URL": "https://sigrid.invalid", "SIGRID_API_FUNCTION_KEY": _CLAVE,
               "SIGRID_API_DATABASE": "db"}
    entorno[faltante] = "   "
    assert _ajustes(monkeypatch, **entorno).sigrid_api_configurada is False


@pytest.mark.parametrize("intentos", [1, 0, -3])
def test_f076_t16_con_un_intento_no_reintenta(intentos):
    api = _Api(httpx.Response(503), _ok())
    with pytest.raises(SigridLecturaError):
        _leer(_lector(api, intentos=intentos))
    assert len(api.peticiones) == 1
