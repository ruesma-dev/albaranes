# tests/test_f111_cliente.py
"""F-111 R33, R34 · cliente HTTP de sv6 contra ``POST /v1/albaranes/partida-residuos``.

Transporte simulado (``httpx.MockTransport``): sin red. Una llamada por
documento; 5xx y fallos de transporte se reintentan; un 404 (sv5 sin el
endpoint nuevo) o una respuesta rota es un fallo que el asignador convierte en
``partida_residuos_ia_fallo``.
"""
from __future__ import annotations

import json

import httpx
import pytest

from domain.ports.elige_partida_port import EligePartidaPort
from infrastructure.clients.http_partida_residuos_client import (
    RUTA_PARTIDA_RESIDUOS,
    HttpPartidaResiduosClient,
    PartidaResiduosError,
)

LINEAS = [{"line_ref": 1, "descripcion": "MADERA", "codigo_ler": "170201"}]
CANDIDATAS = [{"codigo": "32.01", "descripcion": "GRD", "descripcion_agregada": "CD › GR › GRD"}]


def _cliente(manejador, **kw) -> HttpPartidaResiduosClient:
    return HttpPartidaResiduosClient(
        base_url="http://sv5:8002/",
        timeout_s=5,
        espera_base_s=0,
        transport=httpx.MockTransport(manejador),
        **kw,
    )


def test_f111_r34_una_llamada_con_todo_el_documento():
    peticiones: list[httpx.Request] = []

    def manejador(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return httpx.Response(200, json={"elecciones": [
            {"line_ref": 1, "codigo": "32.01", "confianza_pct": 90, "razon_corta": "x"},
            {"line_ref": 2, "codigo": None, "confianza_pct": 0, "razon_corta": "y"},
        ]})

    resultado = _cliente(manejador).elegir(
        document_id="doc-1", lineas=LINEAS, candidatas=CANDIDATAS,
    )
    assert resultado == {1: "32.01", 2: None}
    assert len(peticiones) == 1
    assert str(peticiones[0].url) == "http://sv5:8002" + RUTA_PARTIDA_RESIDUOS
    assert RUTA_PARTIDA_RESIDUOS == "/v1/albaranes/partida-residuos"
    assert peticiones[0].method == "POST"
    assert json.loads(peticiones[0].content) == {
        "document_id": "doc-1", "lineas": LINEAS, "candidatas": CANDIDATAS,
    }


def test_f111_r33_un_5xx_se_reintenta_y_luego_vale():
    llamadas = []

    def manejador(request):
        llamadas.append(1)
        if len(llamadas) < 3:
            return httpx.Response(503, text="sin proveedor")
        return httpx.Response(200, json={"elecciones": [
            {"line_ref": 1, "codigo": "32.01", "confianza_pct": 1, "razon_corta": "x"},
        ]})

    assert _cliente(manejador).elegir(document_id="d", lineas=LINEAS, candidatas=CANDIDATAS) == {
        1: "32.01"
    }
    assert len(llamadas) == 3


def test_f111_r33_5xx_persistente_falla_tras_los_intentos():
    llamadas = []

    def manejador(request):
        llamadas.append(1)
        return httpx.Response(500, text="caído")

    with pytest.raises(PartidaResiduosError, match="500"):
        _cliente(manejador, intentos=2).elegir(document_id="d", lineas=LINEAS, candidatas=CANDIDATAS)
    assert len(llamadas) == 2


def test_f111_r33_404_falla_sin_reintentar():
    llamadas = []

    def manejador(request):
        llamadas.append(1)
        return httpx.Response(404, text="Not Found")

    with pytest.raises(PartidaResiduosError, match="404"):
        _cliente(manejador).elegir(document_id="d", lineas=LINEAS, candidatas=CANDIDATAS)
    assert len(llamadas) == 1


def test_f111_r33_error_de_transporte_se_reintenta():
    llamadas = []

    def manejador(request):
        llamadas.append(1)
        raise httpx.ConnectError("sin red", request=request)

    with pytest.raises(PartidaResiduosError):
        _cliente(manejador, intentos=3).elegir(document_id="d", lineas=LINEAS, candidatas=CANDIDATAS)
    assert len(llamadas) == 3


@pytest.mark.parametrize(
    "respuesta",
    [
        httpx.Response(200, text="no es json"),
        httpx.Response(200, json={"otra": []}),
        httpx.Response(200, json={"elecciones": [{"codigo": "32.01"}]}),
        httpx.Response(200, json=[1, 2]),
    ],
)
def test_f111_r33_respuesta_rota_es_un_fallo(respuesta):
    with pytest.raises(PartidaResiduosError):
        _cliente(lambda request: respuesta).elegir(
            document_id="d", lineas=LINEAS, candidatas=CANDIDATAS,
        )


def test_f111_r33_sin_url_no_se_construye():
    with pytest.raises(ValueError):
        HttpPartidaResiduosClient(base_url="  ", timeout_s=1)


def test_f111_r33_el_cliente_cumple_el_puerto():
    assert isinstance(_cliente(lambda r: httpx.Response(200)), EligePartidaPort)


def test_f111_r33_un_intento_minimo_y_codigo_vacio_es_null():
    llamadas = []

    def manejador(request):
        llamadas.append(1)
        return httpx.Response(200, json={"elecciones": [
            {"line_ref": 1, "codigo": "  ", "confianza_pct": 1, "razon_corta": "x"},
        ]})

    assert _cliente(manejador, intentos=0).elegir(
        document_id="d", lineas=LINEAS, candidatas=CANDIDATAS,
    ) == {1: None}
    assert len(llamadas) == 1
