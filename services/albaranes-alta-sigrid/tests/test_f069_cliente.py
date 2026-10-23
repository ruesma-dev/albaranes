# tests/test_f069_cliente.py
"""F-069 · T3 · las dos lecturas nuevas de ``dbo.emp`` (R9, R10, R13).

``httpx.MockTransport``: ni red ni sigrid-api reales.

- ``buscar_empleados_por_correo(correo)``: ``sql/read`` con el SQL de design §7
  (``CAST`` de ``traele``, que es ``text``; ``ISNULL(fecbaj, 0)``; los de alta
  primero; ``TOP (3)``), el parámetro recortado y en minúsculas, ``max_rows`` 3
  y ``truncated`` comprobado.
- ``empleado_de_alta(ide)``: ``sql/read`` por ``ide`` y de alta, ``max_rows`` 2.
- R24 / R13: reintentos ante fallos transitorios y, agotados, lanza (el
  servicio lo traduce en ``empleado_lectura_fallida``).
- R33: son del puerto (ahora siete operaciones) y van solo por ``sql/read``.
Los ``ide`` y correos son ficticios.
"""
from __future__ import annotations

import logging

import httpx
import pytest
from ruesma_comun.sigrid import SigridRespuestaTruncada

from domain.models.alta_models import EmpleadoSigrid
from domain.ports.sigrid_alta_port import SigridAltaPort
from infrastructure.sigrid.sigrid_api_alta_client import (
    SQL_EMPLEADO_DE_ALTA,
    SQL_EMPLEADOS_POR_CORREO,
    SigridLecturaError,
)
from tests.f053_fakes import Explota, SigridFalso
from tests.test_f053_cliente_sigrid import BASE, CLAVE, Servidor, _cliente, _json, _lectura

CORREO = "login1@ruesma.es"


def _empleados(*filas) -> httpx.Response:
    return _lectura([list(f) for f in filas], columnas=("IDE", "FECBAJ"))


def _ides(*ides) -> httpx.Response:
    return _lectura([[i] for i in ides], columnas=("ide",))


# ------------------------------------------------------------------ #
# SQL exacto (design §7)
# ------------------------------------------------------------------ #
def test_f069_cliente_sql_de_design():
    assert SQL_EMPLEADO_DE_ALTA == (
        "SELECT TOP (1) ide FROM dbo.emp WHERE ide = ? AND ISNULL(fecbaj, 0) = 0"
    )
    assert SQL_EMPLEADOS_POR_CORREO == (
        "SELECT TOP (3) ide, ISNULL(fecbaj, 0) AS fecbaj FROM dbo.emp WHERE "
        "LOWER(LTRIM(RTRIM(CAST(traele AS varchar(512))))) = ? ORDER BY CASE WHEN "
        "ISNULL(fecbaj, 0) = 0 THEN 0 ELSE 1 END, ide"
    )
    for sql in (SQL_EMPLEADO_DE_ALTA, SQL_EMPLEADOS_POR_CORREO):
        assert sql.startswith("SELECT ") and sql.count("?") == 1


# ------------------------------------------------------------------ #
# R10 · empleados del correo
# ------------------------------------------------------------------ #
def test_f069_cliente_r10_correo_cuerpo_exacto_y_filas():
    servidor = Servidor(_empleados((1000001, 0), (2000001, 20240131)))
    empleados = _cliente(servidor).buscar_empleados_por_correo("  Login1@Ruesma.ES ")
    assert empleados == [EmpleadoSigrid(1000001, True), EmpleadoSigrid(2000001, False)]
    (peticion,) = servidor.peticiones
    assert peticion.method == "POST" and str(peticion.url) == f"{BASE}/api/sql/read"
    assert peticion.headers["x-functions-key"] == CLAVE
    cuerpo = servidor.cuerpos()[0]
    assert cuerpo["sql"] == SQL_EMPLEADOS_POR_CORREO
    assert cuerpo["parameters"] == [CORREO]
    assert cuerpo["database"] == "ruesma"
    assert cuerpo["max_rows"] == 3 and isinstance(cuerpo["timeout_seconds"], int)


@pytest.mark.parametrize("fecbaj, de_alta", [
    (0, True), (None, True), ("0", True), (20240131, False), ("20240131", False), (1, False),
])
def test_f069_cliente_r10_de_alta_es_fecbaj_cero_o_nulo(fecbaj, de_alta):
    servidor = Servidor(_empleados((1000001, fecbaj)))
    (empleado,) = _cliente(servidor).buscar_empleados_por_correo(CORREO)
    assert empleado == EmpleadoSigrid(1000001, de_alta)


def test_f069_cliente_r10_sin_filas_es_lista_vacia():
    assert _cliente(Servidor(_empleados())).buscar_empleados_por_correo(CORREO) == []


def test_f069_cliente_r10_ide_como_texto_se_convierte():
    servidor = Servidor(_empleados(("1000001", 0)))
    assert _cliente(servidor).buscar_empleados_por_correo(CORREO) == [
        EmpleadoSigrid(1000001, True),
    ]


def test_f069_cliente_r10_truncado_no_se_tolera():
    servidor = Servidor(_lectura([[1, 0]], columnas=("ide", "fecbaj"), truncado=True))
    with pytest.raises(SigridRespuestaTruncada):
        _cliente(servidor).buscar_empleados_por_correo(CORREO)


def test_f069_cliente_r18_el_correo_no_va_al_log(caplog):
    caplog.set_level(logging.DEBUG)
    _cliente(Servidor(_empleados((1000001, 0)))).buscar_empleados_por_correo(CORREO)
    assert "login1" not in caplog.text.lower()


# ------------------------------------------------------------------ #
# R9 · empleado de la Lista
# ------------------------------------------------------------------ #
def test_f069_cliente_r9_empleado_de_alta_cuerpo_exacto():
    servidor = Servidor(_ides(1234567))
    assert _cliente(servidor).empleado_de_alta(1234567) is True
    cuerpo = servidor.cuerpos()[0]
    assert cuerpo["sql"] == SQL_EMPLEADO_DE_ALTA
    assert cuerpo["parameters"] == [1234567]
    assert cuerpo["max_rows"] == 2
    assert servidor.rutas() == ["/api/sql/read"]


def test_f069_cliente_r9_sin_filas_no_es_de_alta():
    assert _cliente(Servidor(_ides())).empleado_de_alta(1234567) is False


def test_f069_cliente_r9_truncado_no_se_tolera():
    servidor = Servidor(_lectura([[1], [2], [3]], columnas=("ide",), truncado=True))
    with pytest.raises(SigridRespuestaTruncada):
        _cliente(servidor).empleado_de_alta(1)


# ------------------------------------------------------------------ #
# R13 / R24 · reintentos y lectura caída
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("operacion, respuesta", [
    ("correo", _empleados((1000001, 0))),
    ("lista", _ides(1000001)),
])
def test_f069_cliente_r13_reintenta_y_luego_contesta(operacion, respuesta):
    servidor = Servidor(httpx.ConnectError("caido"), _json(503, {}), respuesta)
    cliente = _cliente(servidor)
    if operacion == "correo":
        assert cliente.buscar_empleados_por_correo(CORREO) == [EmpleadoSigrid(1000001, True)]
    else:
        assert cliente.empleado_de_alta(1000001) is True
    assert len(servidor.peticiones) == 3


@pytest.mark.parametrize("respuestas", [
    (_json(500, {}), _json(500, {}), _json(500, {})),
    (httpx.ConnectTimeout("t"), httpx.ConnectTimeout("t"), httpx.ConnectTimeout("t")),
    (_json(400, {"ok": False}),),
    (_json(200, {"ok": False, "error": "x"}),),
])
@pytest.mark.parametrize("operacion", ["correo", "lista"])
def test_f069_cliente_r13_lectura_caida_lanza(respuestas, operacion):
    servidor = Servidor(*respuestas)
    cliente = _cliente(servidor)
    with pytest.raises(SigridLecturaError):
        if operacion == "correo":
            cliente.buscar_empleados_por_correo(CORREO)
        else:
            cliente.empleado_de_alta(1)
    assert len(servidor.peticiones) == len(respuestas)


@pytest.mark.parametrize("operacion, etiqueta", [
    ("correo", "f069-empleado-correo"), ("lista", "f069-empleado-lista"),
])
def test_f069_cliente_r13_el_error_lleva_su_etiqueta(operacion, etiqueta):
    cliente = _cliente(Servidor(_json(400, {"ok": False})))
    with pytest.raises(SigridLecturaError, match=etiqueta):
        if operacion == "correo":
            cliente.buscar_empleados_por_correo(CORREO)
        else:
            cliente.empleado_de_alta(1)


# ------------------------------------------------------------------ #
# R33 · puerto y doble
# ------------------------------------------------------------------ #
def test_f069_cliente_r33_son_del_puerto():
    abstractos = SigridAltaPort.__abstractmethods__
    assert {"buscar_empleados_por_correo", "empleado_de_alta"} <= abstractos
    assert len(abstractos) == 7


def test_f069_cliente_el_doble_registra_y_falla():
    alta = EmpleadoSigrid(1000001, True)
    sigrid = SigridFalso(empleados_por_correo={CORREO: [alta]}, empleados_de_alta={1234567})
    assert sigrid.buscar_empleados_por_correo(CORREO) == [alta]
    assert sigrid.buscar_empleados_por_correo("otro@ruesma.es") == []
    assert sigrid.empleado_de_alta(1234567) is True
    assert sigrid.empleado_de_alta(7) is False
    assert sigrid.llamadas == [
        ("buscar_empleados_por_correo", CORREO), ("buscar_empleados_por_correo", "otro@ruesma.es"),
        ("empleado_de_alta", 1234567), ("empleado_de_alta", 7),
    ]
    caido = SigridFalso(fallar_en={"buscar_empleados_por_correo", "empleado_de_alta"})
    with pytest.raises(Explota):
        caido.buscar_empleados_por_correo(CORREO)
    with pytest.raises(Explota):
        caido.empleado_de_alta(1)
