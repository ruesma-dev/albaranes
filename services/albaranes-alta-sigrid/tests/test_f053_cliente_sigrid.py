# tests/test_f053_cliente_sigrid.py
"""F-053 · T13 · ``SigridApiAltaClient`` contra un sigrid-api simulado.

``httpx.MockTransport``: ni red ni sigrid-api reales. Se comprueba:

- R33: solo ``sql/read``, ``sigrid/albaran`` (modo extendido) y
  ``concepto-grafico``; cuerpos exactos (con ``usu``; nunca
  ``lineas_recibidas``, ``almacen`` ni ``naturaleza``) y ``truncated``.
- Lectura de ``details.codigo`` y ``details.lineas`` de un 400.
- R24: reintento con espera creciente en lecturas, previa y adjunto ante
  fallos transitorios; NINGUNO en la grabación, que va con 240 s de timeout.
- R35: la clave nunca en los logs (ni el PDF).
"""
from __future__ import annotations

import base64
import hashlib
import inspect
import json
import logging

import httpx
import pytest
from ruesma_comun.sigrid import SigridRespuestaTruncada

from domain.models.alta_models import (
    AlbaranSigrid,
    ErrorAlta,
    LineaPeticion,
    PeticionAlbaran,
    RespuestaAlta,
    TipoFallo,
)
from infrastructure.sigrid import sigrid_api_alta_client as modulo
from infrastructure.sigrid.sigrid_api_alta_client import SigridApiAltaClient

CLAVE = "CLAVE-SECRETA-DE-PRUEBA-1234"
BASE = "https://sigrid.invalid"

PETICION = PeticionAlbaran(
    cod_obra="0404", cif_proveedor="B00000000", cod_contrato="CTSU16/0206",
    referencia_externa="ALB-d1", su_referencia="ALB-58260", usu="USU_ALTA",
    fecha_albaran=20261003, empide=None,
    lineas=(
        LineaPeticion(referencia_linea="90201", cantidad=6.0, precio=68.4, ctrpro_ide=700101,
                      partida="03.02.01"),
        LineaPeticion(referencia_linea="90204", cantidad=1.0, precio=30.0, producto="MA9999",
                      descripcion="PORTES", unidad="UD"),
    ),
)


class Servidor:
    """sigrid-api de mentira: respuestas en cola por ruta y registro de peticiones."""

    def __init__(self, *respuestas):
        self.respuestas = list(respuestas)
        self.peticiones: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        respuesta = self.respuestas.pop(0)
        if isinstance(respuesta, Exception):
            raise respuesta
        return respuesta

    def cuerpos(self) -> list[dict]:
        return [json.loads(p.content) for p in self.peticiones]

    def rutas(self) -> list[str]:
        return [p.url.path for p in self.peticiones]


def _json(status: int, cuerpo) -> httpx.Response:
    return httpx.Response(status, json=cuerpo)


def _cliente(servidor: Servidor, **extra) -> SigridApiAltaClient:
    return SigridApiAltaClient(
        base_url=BASE + "/", function_key=CLAVE, database="ruesma", usuario="USU_ALTA",
        transport=httpx.MockTransport(servidor), espera_base_s=0, **extra,
    )


def _lectura(filas, columnas=("ide", "cod", "fec"), truncado=False) -> httpx.Response:
    return _json(200, {"ok": True, "database": "ruesma", "columns": list(columnas),
                       "rows": filas, "row_count": len(filas), "truncated": truncado})


PREVISTO = {
    "ok": True, "estado": "previsto", "committed": False, "dry_run": True, "con_ide": 9, "cod": "AC26/1",
    "avisos": [{"codigo": "cod_provisional", "mensaje": "m"}],
    "lineas": [{"referencia_linea": "90201", "total": 410.4}],
    "totales": {"totdoc": 1.0}, "cabecera": {"ban": "X"}, "filas": {},
}


# ------------------------------------------------------------------ #
# R33 · sql/read
# ------------------------------------------------------------------ #
def test_f053_r33_buscar_albaranes_cuerpo_exacto():
    servidor = Servidor(_lectura([[8800001, "AC26/900", 20261002], [8800002, "AC26/901", None]]))
    encontrados = _cliente(servidor).buscar_albaranes("B00000000", "ALB-58260", "ALB-d1")
    assert encontrados == [AlbaranSigrid(8800001, "AC26/900", 20261002),
                           AlbaranSigrid(8800002, "AC26/901", None)]
    (peticion,) = servidor.peticiones
    assert peticion.method == "POST" and str(peticion.url) == f"{BASE}/api/sql/read"
    assert peticion.headers["x-functions-key"] == CLAVE
    cuerpo = json.loads(peticion.content)
    assert cuerpo["database"] == "ruesma"
    assert cuerpo["sql"] == (
        "SELECT c.ide, c.cod, c.fec FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide "
        "WHERE c.tip = 14 AND d.entcif = ? AND d.entref = ? AND ISNULL(d.synckey, '') <> ?"
    )
    assert cuerpo["parameters"] == ["B00000000", "ALB-58260", "ALB-d1"]
    assert isinstance(cuerpo["max_rows"], int) and isinstance(cuerpo["timeout_seconds"], int)


def test_f053_r33_buscar_sin_resultados_es_lista_vacia():
    assert _cliente(Servidor(_lectura([]))).buscar_albaranes("B1", "N", "ALB-d") == []


def test_f053_r33_buscar_truncado_no_se_tolera():
    servidor = Servidor(_lectura([[1, "AC26/1", None]], truncado=True))
    with pytest.raises(SigridRespuestaTruncada):
        _cliente(servidor).buscar_albaranes("B1", "N", "ALB-d")


def test_f053_r33_existe_concepto():
    servidor = Servidor(_lectura([[9123461]], columnas=("ide",)), _lectura([], columnas=("ide",)))
    cliente = _cliente(servidor)
    assert cliente.existe_concepto(9123461) is True
    assert cliente.existe_concepto(9123461) is False
    cuerpo = servidor.cuerpos()[0]
    assert cuerpo["sql"] == "SELECT ide FROM dbo.con WHERE ide = ? AND tip = 14"
    assert cuerpo["parameters"] == [9123461]


def test_f053_r33_lectura_con_ok_false_o_4xx_lanza():
    for respuesta in (_json(200, {"ok": False, "error": "x"}), _json(400, {"ok": False})):
        with pytest.raises(RuntimeError):
            _cliente(Servidor(respuesta)).existe_concepto(1)


# ------------------------------------------------------------------ #
# R33 · sigrid/albaran
# ------------------------------------------------------------------ #
@pytest.mark.parametrize("commit", [False, True])
def test_f053_r33_alta_albaran_cuerpo_exacto(commit):
    servidor = Servidor(_json(200, {**PREVISTO, "estado": "creado" if commit else "previsto"}))
    _cliente(servidor).alta_albaran(PETICION, commit)
    (peticion,) = servidor.peticiones
    assert str(peticion.url) == f"{BASE}/api/sigrid/albaran"
    assert peticion.headers["x-functions-key"] == CLAVE
    cuerpo = json.loads(peticion.content)
    assert cuerpo == {"database": "ruesma", **PETICION.a_dict(), "commit": commit}
    assert cuerpo["usu"] == "USU_ALTA"
    for prohibida in ("lineas_recibidas", "naturaleza", "almacen"):
        assert prohibida not in cuerpo
        assert all(prohibida not in linea for linea in cuerpo["lineas"])


def test_f053_r33_200_se_reduce_a_lo_de_r16():
    respuesta = _cliente(Servidor(_json(200, PREVISTO))).alta_albaran(PETICION, False)
    assert isinstance(respuesta, RespuestaAlta)
    assert respuesta.estado == "previsto" and respuesta.con_ide == 9 and respuesta.cod == "AC26/1"
    assert set(respuesta.a_dict()) == {"estado", "con_ide", "cod", "avisos", "lineas", "totales"}


def test_f053_r33_400_con_details_codigo_y_lineas():
    cuerpo = {"ok": False, "error": "Hay líneas que no se pueden dar de alta.", "details": {
        "type": "AlbaranCompraError", "codigo": "lineas_no_validas",
        "lineas": [{"indice": 0, "referencia_linea": "90201", "codigo": "partida_ambigua",
                    "mensaje": "m"}]}}
    error = _cliente(Servidor(_json(400, cuerpo))).alta_albaran(PETICION, False)
    assert error == ErrorAlta(
        tipo=TipoFallo.RECHAZO, status=400, codigo="lineas_no_validas",
        lineas=({"indice": 0, "referencia_linea": "90201", "codigo": "partida_ambigua",
                 "mensaje": "m"},),
        mensaje="Hay líneas que no se pueden dar de alta.",
    )


def test_f053_r33_400_sin_codigo_y_400_no_json():
    sin_codigo = _cliente(Servidor(_json(400, {"ok": False, "error": "Solicitud invalida.",
                                               "details": {"validation": []}})))
    error = sin_codigo.alta_albaran(PETICION, False)
    assert error.tipo is TipoFallo.RECHAZO and error.codigo is None and error.status == 400
    texto = _cliente(Servidor(httpx.Response(400, text="nope")))
    assert texto.alta_albaran(PETICION, False).codigo is None


@pytest.mark.parametrize(("status", "tipo"), [
    (401, TipoFallo.AUTORIZACION), (403, TipoFallo.AUTORIZACION), (404, TipoFallo.CLIENTE),
])
def test_f053_r33_otros_4xx(status, tipo):
    error = _cliente(Servidor(_json(status, {"error": "x"}))).alta_albaran(PETICION, False)
    assert isinstance(error, ErrorAlta) and error.tipo is tipo and error.status == status


def test_f053_r33_200_que_no_es_json_u_ok_false_es_respuesta_invalida():
    for respuesta in (httpx.Response(200, text="<html>"), _json(200, {"ok": False}), _json(200, [])):
        error = _cliente(Servidor(respuesta)).alta_albaran(PETICION, True)
        assert isinstance(error, ErrorAlta) and error.tipo is TipoFallo.RESPUESTA_INVALIDA


# ------------------------------------------------------------------ #
# R24 · reintentos
# ------------------------------------------------------------------ #
def test_f053_r24_previa_reintenta_ante_5xx_y_tiempo_agotado():
    servidor = Servidor(_json(503, {}), httpx.ReadTimeout("lento"), _json(200, PREVISTO))
    respuesta = _cliente(servidor).alta_albaran(PETICION, False)
    assert isinstance(respuesta, RespuestaAlta)
    assert len(servidor.peticiones) == 3


def test_f053_r24_previa_agota_los_reintentos_y_devuelve_el_fallo():
    servidor = Servidor(_json(502, {}), _json(502, {}), _json(502, {}))
    error = _cliente(servidor, intentos=3).alta_albaran(PETICION, False)
    assert error.tipo is TipoFallo.SERVIDOR and error.status == 502
    assert len(servidor.peticiones) == 3


def test_f053_r24_previa_no_reintenta_un_400():
    servidor = Servidor(_json(400, {"details": {"codigo": "obra_no_encontrada"}}))
    _cliente(servidor).alta_albaran(PETICION, False)
    assert len(servidor.peticiones) == 1


@pytest.mark.parametrize("fallo", [
    _json(500, {}), httpx.ReadTimeout("lento"), httpx.ConnectError("caido"),
])
def test_f053_r24_la_grabacion_no_se_reintenta_nunca(fallo):
    servidor = Servidor(fallo, _json(200, {**PREVISTO, "estado": "creado"}))
    error = _cliente(servidor).alta_albaran(PETICION, True)
    assert isinstance(error, ErrorAlta)
    assert len(servidor.peticiones) == 1
    esperado = {500: TipoFallo.SERVIDOR}.get(getattr(fallo, "status_code", None))
    if isinstance(fallo, httpx.ReadTimeout):
        esperado = TipoFallo.TIEMPO_AGOTADO
    if isinstance(fallo, httpx.ConnectError):
        esperado = TipoFallo.CONEXION
    assert error.tipo is esperado


def test_f053_r24_timeout_de_240_s_en_la_grabacion_y_menor_en_la_previa():
    servidor = Servidor(_json(200, PREVISTO), _json(200, {**PREVISTO, "estado": "creado"}))
    cliente = _cliente(servidor)
    cliente.alta_albaran(PETICION, False)
    cliente.alta_albaran(PETICION, True)
    previa, grabacion = (p.extensions["timeout"]["read"] for p in servidor.peticiones)
    assert grabacion == 240.0
    assert previa < 230.0


def test_f053_r24_lecturas_reintentan():
    servidor = Servidor(httpx.ConnectError("caido"), _json(500, {}), _lectura([]))
    assert _cliente(servidor).buscar_albaranes("B1", "N", "ALB-d") == []
    assert len(servidor.peticiones) == 3


def test_f053_r24_lectura_que_agota_los_reintentos_lanza():
    servidor = Servidor(_json(500, {}), _json(500, {}), _json(500, {}))
    with pytest.raises(RuntimeError):
        _cliente(servidor).existe_concepto(1)
    assert len(servidor.peticiones) == 3


# ------------------------------------------------------------------ #
# R22 / R33 · concepto-grafico
# ------------------------------------------------------------------ #
PDF = b"%PDF-1.4 contenido de mentira"


def _respuesta_adjunto(*, committed: bool, idempotente: bool, ide_documental: int | None,
                       ide_negocio: int | None) -> dict:
    """Forma REAL de ``AttachConceptoGraficoResponse`` en sigrid-api ``13fd99d``
    (``domain/models/concepto_grafico_models.py``: ``GraficoPreview`` :115, con
    ``ide_documental`` :123 e ``ide_negocio`` :124, SIN ``ide``; la respuesta,
    :156). El ``gra`` que enlaza ``rcg`` con el concepto es el de NEGOCIO
    (``EnlacePreview.gra``); en la idempotente solo viene ese
    (``application/use_cases/attach_concepto_grafico_use_case.py`` :404 y :406;
    en la grabación, :556-:557 y :564)."""
    return {
        "ok": True, "committed": committed, "dry_run": False, "idempotente": idempotente,
        "database": "ruesma", "database_documental": "ruesma_doc",
        "concepto": {"ide": 9123461, "tip": 14, "emp": 2425207, "cod": "AC26/1", "res": None},
        "grafico": {
            "ide_documental": ide_documental, "ide_negocio": ide_negocio, "cod": "G1",
            "emp": 2425207, "nom": "ALB-d1.pdf", "fec": 20261006, "usu": "USU_ALTA",
            "res": "ALB-d1.pdf", "gratipide": 0, "vin": 1, "bytes": len(PDF),
            "sha256": hashlib.sha256(PDF).hexdigest(), "content_type": "application/pdf",
            "fila_documental": {}, "fila_negocio": {},
        },
        "enlace": {"ide": 31, "con": 9123461, "gra": ide_negocio, "pos": None, "cla": 0,
                   "feclee": 0, "fecalt": 0},
        "filas_afectadas": 3 if committed else 0, "avisos": [],
    }


ADJUNTO_COLGADO = _respuesta_adjunto(committed=True, idempotente=False, ide_documental=880011,
                                     ide_negocio=4455)


def test_f053_r22_adjunto_cuerpo_exacto_y_colgado():
    servidor = Servidor(_json(200, _respuesta_adjunto(
        committed=True, idempotente=False, ide_documental=880011, ide_negocio=4455)))
    resultado = _cliente(servidor).adjuntar_pdf(9123461, "ALB-d1.pdf", PDF)
    # Se guarda el gra de NEGOCIO, no el documental.
    assert resultado.colgado is True and resultado.gra_ide == 4455
    (peticion,) = servidor.peticiones
    assert str(peticion.url) == f"{BASE}/api/sigrid/concepto-grafico"
    cuerpo = json.loads(peticion.content)
    assert cuerpo == {
        "database": "ruesma", "conide": 9123461, "contip": 14, "gratipide": 0,
        "res": "ALB-d1.pdf", "nom": "ALB-d1.pdf", "usu": "USU_ALTA",
        "contenido_base64": base64.b64encode(PDF).decode("ascii"),
        "sha256": hashlib.sha256(PDF).hexdigest(), "commit": True,
    }


def test_f053_r22_adjunto_idempotente_cuenta_como_colgado():
    servidor = Servidor(_json(200, _respuesta_adjunto(
        committed=False, idempotente=True, ide_documental=None, ide_negocio=7)))
    resultado = _cliente(servidor).adjuntar_pdf(1, "a.pdf", PDF)
    assert resultado.colgado is True and resultado.gra_ide == 7


@pytest.mark.parametrize("cuerpo", [
    # Forma real sin escribir nada (ni grabado ni idempotente).
    _respuesta_adjunto(committed=False, idempotente=False, ide_documental=None, ide_negocio=None),
    # Defensivo: un 200 con ok=false no es la forma del contrato.
    {"ok": False, "committed": True},
])
def test_f053_r22_adjunto_sin_escribir_no_esta_colgado(cuerpo):
    assert _cliente(Servidor(_json(200, cuerpo))).adjuntar_pdf(1, "a.pdf", PDF).colgado is False


def test_f053_r22_adjunto_rechazado():
    servidor = Servidor(_json(400, {"ok": False, "error": "usuario", "details": {
        "codigo": "usuario_no_valido"}}))
    resultado = _cliente(servidor).adjuntar_pdf(1, "a.pdf", PDF)
    assert resultado.colgado is False and resultado.codigo == "usuario_no_valido"
    assert len(servidor.peticiones) == 1


def test_f053_r24_adjunto_reintenta_ante_5xx_y_luego_se_rinde():
    servidor = Servidor(_json(500, {}), _json(200, ADJUNTO_COLGADO))
    assert _cliente(servidor).adjuntar_pdf(1, "a.pdf", PDF).colgado is True
    agotado = Servidor(_json(500, {}), _json(500, {}), _json(500, {}))
    resultado = _cliente(agotado).adjuntar_pdf(1, "a.pdf", PDF)
    assert resultado.colgado is False and len(agotado.peticiones) == 3


def test_f053_r22_nombre_largo_recortado_en_res_y_nom():
    servidor = Servidor(_json(200, ADJUNTO_COLGADO))
    _cliente(servidor).adjuntar_pdf(1, "N" * 300 + ".pdf", PDF)
    cuerpo = servidor.cuerpos()[0]
    assert len(cuerpo["res"]) == 48 and len(cuerpo["nom"]) == 255


# ------------------------------------------------------------------ #
# R33 y R35 · qué rutas y qué se loguea
# ------------------------------------------------------------------ #
def test_f053_r33_solo_las_tres_rutas_permitidas():
    servidor = Servidor(_lectura([]), _lectura([], columnas=("ide",)), _json(200, PREVISTO),
                        _json(200, {**PREVISTO, "estado": "creado"}),
                        _json(200, ADJUNTO_COLGADO))
    cliente = _cliente(servidor)
    cliente.buscar_albaranes("B1", "N", "ALB-d")
    cliente.existe_concepto(1)
    cliente.alta_albaran(PETICION, False)
    cliente.alta_albaran(PETICION, True)
    cliente.adjuntar_pdf(1, "a.pdf", PDF)
    assert set(servidor.rutas()) == {
        "/api/sql/read", "/api/sigrid/albaran", "/api/sigrid/concepto-grafico",
    }
    fuente = inspect.getsource(modulo)
    for prohibido in ("sql/write", "albaran-directo", "lineas_recibidas"):
        assert prohibido not in fuente


def test_f053_r35_la_clave_y_el_pdf_nunca_en_los_logs(caplog):
    caplog.set_level(logging.DEBUG)
    servidor = Servidor(_json(503, {"error": CLAVE}), _json(200, PREVISTO), _json(500, {}),
                        _json(400, {"error": "x"}), _lectura([]),
                        _json(200, ADJUNTO_COLGADO))
    cliente = _cliente(servidor)
    cliente.alta_albaran(PETICION, False)
    cliente.alta_albaran(PETICION, True)
    cliente.alta_albaran(PETICION, False)
    cliente.buscar_albaranes("B1", "N", "ALB-d")
    cliente.adjuntar_pdf(1, "a.pdf", PDF)
    texto = caplog.text + repr(cliente)
    assert CLAVE not in texto
    assert base64.b64encode(PDF).decode("ascii") not in texto and "%PDF" not in texto


def test_f053_r35_sin_clave_no_se_construye():
    with pytest.raises(ValueError):
        SigridApiAltaClient(base_url=BASE, function_key="", database="ruesma", usuario="U")
