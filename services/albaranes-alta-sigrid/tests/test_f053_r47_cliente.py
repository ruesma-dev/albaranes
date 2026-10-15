# tests/test_f053_r47_cliente.py
"""F-053 v8 · T42 · el cliente de sigrid-api con el usuario por documento.

``httpx.MockTransport``: ni red ni sigrid-api reales.

- R47 / R33: ``buscar_usuario(cod)`` por ``sql/read`` con el SQL exacto de
  sigrid-api (``SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?``); devuelve el
  ``cod`` de la FILA (el de Sigrid, no el pedido), ``None`` sin filas;
  ``truncated`` comprobado.
- R24: la lectura reintenta ante fallos transitorios y, agotados, lanza.
- R22: ``adjuntar_pdf`` lleva el ``usu`` de cada llamada (ya no uno fijo).
"""
from __future__ import annotations

import inspect

import httpx
import pytest
from ruesma_comun.sigrid import SigridRespuestaTruncada

from domain.ports.sigrid_alta_port import SigridAltaPort
from infrastructure.sigrid.sigrid_api_alta_client import (
    SQL_BUSCAR_USUARIO,
    SigridApiAltaClient,
    SigridLecturaError,
)
from tests.test_f053_cliente_sigrid import (
    ADJUNTO_COLGADO,
    BASE,
    CLAVE,
    PDF,
    Servidor,
    _cliente,
    _json,
    _lectura,
)


def _usuarios(*cods) -> httpx.Response:
    return _lectura([[c] for c in cods], columnas=("cod",))


def test_f053_r47_cliente_buscar_usuario_cuerpo_exacto_y_cod_de_sigrid():
    servidor = Servidor(_usuarios("pgris"))
    assert _cliente(servidor).buscar_usuario("PGris") == "pgris"
    (peticion,) = servidor.peticiones
    assert peticion.method == "POST" and str(peticion.url) == f"{BASE}/api/sql/read"
    assert peticion.headers["x-functions-key"] == CLAVE
    cuerpo = servidor.cuerpos()[0]
    assert SQL_BUSCAR_USUARIO == "SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?"
    assert cuerpo["sql"] == SQL_BUSCAR_USUARIO
    assert cuerpo["parameters"] == ["PGris"]
    assert cuerpo["database"] == "ruesma"
    assert cuerpo["max_rows"] == 2 and isinstance(cuerpo["timeout_seconds"], int)


def test_f053_r47_cliente_sin_filas_es_none():
    assert _cliente(Servidor(_usuarios())).buscar_usuario("nadie") is None


@pytest.mark.parametrize("cod, esperado", [
    ("pgris   ", "pgris"),   # CHAR con relleno: se recorta
    ("", None),
    ("   ", None),
    (None, None),
])
def test_f053_r47_cliente_cod_recortado_y_vacio_es_none(cod, esperado):
    assert _cliente(Servidor(_usuarios(cod))).buscar_usuario("pgris") == esperado


def test_f053_r47_cliente_truncado_no_se_tolera():
    servidor = Servidor(_lectura([["pgris"]], columnas=("cod",), truncado=True))
    with pytest.raises(SigridRespuestaTruncada):
        _cliente(servidor).buscar_usuario("pgris")


def test_f053_r47_cliente_reintenta_y_luego_contesta():
    servidor = Servidor(httpx.ConnectError("caido"), _json(503, {}), _usuarios("pgris"))
    assert _cliente(servidor).buscar_usuario("pgris") == "pgris"
    assert len(servidor.peticiones) == 3


@pytest.mark.parametrize("respuestas", [
    (_json(500, {}), _json(500, {}), _json(500, {})),
    (httpx.ConnectTimeout("t"), httpx.ConnectTimeout("t"), httpx.ConnectTimeout("t")),
    (_json(400, {"ok": False}),),
    (_json(200, {"ok": False, "error": "x"}),),
])
def test_f053_r47_cliente_lectura_caida_lanza(respuestas):
    servidor = Servidor(*respuestas)
    with pytest.raises(SigridLecturaError):
        _cliente(servidor).buscar_usuario("pgris")
    assert len(servidor.peticiones) == len(respuestas)


def test_f053_r22_adjunto_lleva_el_usu_de_cada_llamada():
    servidor = Servidor(_json(200, ADJUNTO_COLGADO), _json(200, ADJUNTO_COLGADO))
    cliente = _cliente(servidor)
    cliente.adjuntar_pdf(1, "a.pdf", PDF, usu="ana")
    cliente.adjuntar_pdf(1, "a.pdf", PDF, usu="pgris")
    assert [c["usu"] for c in servidor.cuerpos()] == ["ana", "pgris"]


def test_f053_r22_el_cliente_ya_no_tiene_usuario_fijo():
    parametros = inspect.signature(SigridApiAltaClient.__init__).parameters
    assert "usuario" not in parametros
    assert "usu" in inspect.signature(SigridApiAltaClient.adjuntar_pdf).parameters


def test_f053_r33_buscar_usuario_es_del_puerto_y_va_por_sql_read():
    assert "buscar_usuario" in SigridAltaPort.__abstractmethods__
    servidor = Servidor(_usuarios("pgris"))
    _cliente(servidor).buscar_usuario("pgris")
    assert servidor.rutas() == ["/api/sql/read"]
