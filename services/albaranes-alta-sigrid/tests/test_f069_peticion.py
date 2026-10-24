# tests/test_f069_peticion.py
"""F-069 · T10 · la ``resolucion`` en la petición guardada (R15–R18, R20).

- R16: ``peticion_json`` lleva, junto al cuerpo, ``resolucion`` = orígenes de
  ``usu`` y ``empide`` y los Avisos (``codigo``, ``detalle``).
- R15: un ``incierto`` retomado reenvía SU petición sin resolver nada y
  conserva su ``resolucion`` (y no se la inventa si no la tenía).
- R17: ``resolucion`` nunca viaja a sigrid-api: ni en la previa, ni en la
  grabación, ni al retomar. Con el cliente REAL sobre ``httpx.MockTransport``.
- R18: el log lleva ``usu``, ``empide``, orígenes y códigos; nunca el correo.
- R20: el adjunto (y «Reintentar adjunto») va con el ``usu`` guardado.
"""
from __future__ import annotations

import json
import logging
from dataclasses import replace

import httpx
import pytest

from application.alta_sigrid_service import AltaSigridService
from domain.models.alta_models import (
    CLAVE_RESOLUCION,
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    AvisoResolucion,
    Decision,
    EmpleadoSigrid,
    EstadoAlta,
    ModoAlta,
    OrigenEmpleado,
    OrigenUsuario,
    Resolucion,
)
from domain.services.usuario_sigrid import leer_equivalencias
from infrastructure.sigrid import sigrid_api_alta_client as cliente
from infrastructure.sigrid.sigrid_api_alta_client import SigridApiAltaClient
from tests import f069_servicio as f
from tests.f053_datos import CONFIG
from tests.f053_fakes import AHORA, DESDE, ESPERA, PdfFalso, RepoFalso, SigridFalso, previa_ok
from tests.test_f053_cliente_sigrid import ADJUNTO_COLGADO

CORREO = "login1@ruesma.es"
ALTA = EmpleadoSigrid(1000001, True)


def test_f069_r16_clave_y_forma_de_la_resolucion():
    assert CLAVE_RESOLUCION == "resolucion"
    resolucion = Resolucion(
        usu="login1", origen_usu=OrigenUsuario.CORREO, empide=None,
        origen_empide=OrigenEmpleado.DEFECTO_SIGRID_API,
        avisos=(AvisoResolucion("empleado_correo_sin_empleado", "x"),
                AvisoResolucion("defecto_sigrid_api", "y")),
    )
    assert resolucion.a_dict() == {
        "usu": "correo", "empide": "defecto_sigrid_api",
        "avisos": [{"codigo": "empleado_correo_sin_empleado", "detalle": "x"},
                   {"codigo": "defecto_sigrid_api", "detalle": "y"}],
    }
    with pytest.raises(AttributeError):
        resolucion.usu = "otro"  # type: ignore[misc]


# ------------------------------------------------------------------ #
# R16 · se guarda junto al cuerpo
# ------------------------------------------------------------------ #
def test_f069_r16_peticion_guardada_lleva_la_resolucion():
    sigrid = f.sigrid(usuarios={"login1": "login1"}, empleados_por_correo={CORREO: [ALTA]})
    repo, doc, _ = f.procesar(sigrid)
    guardada = repo.ultimo(doc).peticion
    assert guardada[CLAVE_RESOLUCION] == {"usu": "correo", "empide": "correo", "avisos": []}
    assert guardada["usu"] == "login1" and guardada["empide"] == ALTA.ide
    cuerpo = {k: v for k, v in guardada.items() if k != CLAVE_RESOLUCION}
    assert cuerpo == f.pedidos(sigrid, "a_dict")[0]()


def test_f069_r16_avisos_de_usu_y_de_empide_en_orden():
    sigrid = f.sigrid(usuarios={})
    repo, doc, _ = f.procesar(sigrid, lista='{"login1": {"usu": "login1b", "empide": 7}}')
    resolucion = repo.ultimo(doc).peticion[CLAVE_RESOLUCION]
    assert resolucion["usu"] == "respaldo" and resolucion["empide"] == "defecto_sigrid_api"
    assert [a["codigo"] for a in resolucion["avisos"]] == [
        "usuario_lista_no_existe", "empleado_lista_no_valido", "empleado_correo_sin_empleado",
        "defecto_sigrid_api",
    ]
    assert all(set(a) == {"codigo", "detalle"} for a in resolucion["avisos"])
    assert all("@" not in a["detalle"] for a in resolucion["avisos"])


def test_f069_r16_la_resolucion_se_guarda_ya_en_en_curso():
    sigrid = f.sigrid(usuarios={"login1": "login1"})
    repo, doc, _ = f.procesar(sigrid)
    en_curso = [r for d, r in repo.guardados if r.estado is EstadoAlta.EN_CURSO]
    assert en_curso and CLAVE_RESOLUCION in en_curso[0].peticion


def test_f069_r16_los_avisos_no_son_motivos():
    sigrid = f.sigrid(usuarios={})
    repo, doc, resultado = f.procesar(sigrid)
    assert resultado.estado is EstadoAlta.SIMULADO
    assert repo.ultimo(doc).motivos == ()


# ------------------------------------------------------------------ #
# R15 · incierto retomado
# ------------------------------------------------------------------ #
RESOLUCION_GUARDADA = {"usu": "lista", "empide": "lista", "avisos": [
    {"codigo": "usuario_lista_no_existe", "detalle": "z"}]}


def _incierto(peticion: dict) -> AltaActual:
    return AltaActual(estado=EstadoAlta.INCIERTO, modo="simulacion", peticion=peticion,
                      ultimo_intento_at_utc=AHORA - ESPERA * 2)


def test_f069_r15_incierto_retomado_no_resuelve_y_conserva_la_resolucion():
    guardada = {**replace(f.peticion("luis"), empide=4242).a_dict(),
                CLAVE_RESOLUCION: RESOLUCION_GUARDADA}
    sigrid = f.sigrid(usuarios={"login1": "login1"}, empleados_por_correo={CORREO: [ALTA]})
    repo, doc, resultado = f.procesar(sigrid, alta=_incierto(guardada),
                                      lista='{"login1": {"usu": "x", "empide": 9}}')
    assert resultado.estado is EstadoAlta.SIMULADO
    assert sigrid.operaciones() == ["buscar_albaranes", "alta_albaran"]
    assert f.pedidos(sigrid, "usu") == ["luis"] and f.pedidos(sigrid, "empide") == [4242]
    assert repo.ultimo(doc).peticion == guardada


def test_f069_r15_incierto_anterior_a_f069_no_se_inventa_la_resolucion():
    guardada = f.peticion("luis").a_dict()
    sigrid = f.sigrid(usuarios={"login1": "login1"})
    repo, doc, _ = f.procesar(sigrid, alta=_incierto(guardada))
    assert repo.ultimo(doc).peticion == guardada
    assert CLAVE_RESOLUCION not in repo.ultimo(doc).peticion


# ------------------------------------------------------------------ #
# R17 · nunca a sigrid-api (cliente real, transporte simulado)
# ------------------------------------------------------------------ #
class SigridApiDeMentira:
    """sigrid-api de mentira que responde por ruta y por SQL."""

    def __init__(self, peticion_previa):
        self.previa = {"ok": True, **previa_ok(peticion_previa).a_dict()}
        self.peticiones: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        cuerpo = json.loads(request.content)
        if request.url.path == "/api/sql/read":
            sql = cuerpo["sql"]
            if sql == cliente.SQL_BUSCAR_USUARIO:
                filas, columnas = [["login1"]], ["cod"]
            elif sql == cliente.SQL_EMPLEADOS_POR_CORREO:
                filas, columnas = [[1000001, 0]], ["ide", "fecbaj"]
            elif sql == cliente.SQL_EMPLEADO_DE_ALTA:
                filas, columnas = [[cuerpo["parameters"][0]]], ["ide"]
            else:
                filas, columnas = [], ["ide", "cod", "fec"]
            return httpx.Response(200, json={"ok": True, "columns": columnas, "rows": filas,
                                              "row_count": len(filas), "truncated": False})
        if request.url.path == "/api/sigrid/albaran":
            estado = "creado" if cuerpo["commit"] else "previsto"
            return httpx.Response(200, json={**self.previa, "estado": estado})
        return httpx.Response(200, json=ADJUNTO_COLGADO)


def _con_cliente_real(*, alta=None, lista=""):
    servidor = SigridApiDeMentira(f.peticion())
    sigrid = SigridApiAltaClient(base_url="https://sigrid.invalid", function_key="k",
                                 database="ruesma", espera_base_s=0,
                                 transport=httpx.MockTransport(servidor))
    repo = RepoFalso()
    doc = repo.anadir(f.D, alta=alta, approved_by=CORREO)
    servicio = AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=PdfFalso(), config=CONFIG, usuario_respaldo="pgris",
        modo=ModoAlta.REAL, desde=DESDE, espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset(), reloj=lambda: AHORA,
        equivalencias=leer_equivalencias(lista),
    )
    resultado = servicio.procesar(doc, AccionAlta.ALTA)
    return servidor, repo, doc, resultado


def _cuerpos_albaran(servidor) -> list[dict]:
    return [json.loads(p.content) for p in servidor.peticiones
            if p.url.path == "/api/sigrid/albaran"]


def test_f069_r17_la_resolucion_no_viaja_en_la_previa_ni_en_la_grabacion():
    servidor, repo, doc, resultado = _con_cliente_real(lista='{"login1": {"empide": 77}}')
    assert resultado.estado is EstadoAlta.REGISTRADO
    assert CLAVE_RESOLUCION in repo.ultimo(doc).peticion
    cuerpos = _cuerpos_albaran(servidor)
    assert [c["commit"] for c in cuerpos] == [False, True]
    assert [c["empide"] for c in cuerpos] == [77, 77]
    for peticion in servidor.peticiones:
        assert b"resolucion" not in peticion.content
        assert b"login1@ruesma.es" not in peticion.content or peticion.url.path == "/api/sql/read"


def test_f069_r17_ni_al_retomar_un_incierto():
    guardada = {**f.peticion("luis").a_dict(), CLAVE_RESOLUCION: RESOLUCION_GUARDADA}
    incierto = replace(_incierto(guardada), modo="real")
    servidor, repo, doc, resultado = _con_cliente_real(alta=incierto)
    assert resultado.estado is EstadoAlta.REGISTRADO
    cuerpos = _cuerpos_albaran(servidor)
    assert cuerpos and all(CLAVE_RESOLUCION not in c for c in cuerpos)
    assert all(c["usu"] == "luis" for c in cuerpos)
    assert repo.ultimo(doc).peticion[CLAVE_RESOLUCION] == RESOLUCION_GUARDADA
    for peticion in servidor.peticiones:
        assert b"resolucion" not in peticion.content


# ------------------------------------------------------------------ #
# R18 · log
# ------------------------------------------------------------------ #
def test_f069_r18_log_con_usu_empide_origenes_y_codigos_sin_correo(caplog):
    caplog.set_level(logging.DEBUG)
    sigrid = f.sigrid(usuarios={"login1": "login1"},
                      empleados_por_correo={CORREO: [ALTA, replace(ALTA, ide=1000002)]})
    f.procesar(sigrid, approved_by="Login1@Ruesma.es")
    (linea,) = [r.getMessage() for r in caplog.records if "origen_usu=" in r.getMessage()]
    for trozo in ("usu=login1", "origen_usu=correo", "empide=None",
                  "origen_empide=defecto_sigrid_api", "empleado_correo_ambiguo",
                  "defecto_sigrid_api"):
        assert trozo in linea
    texto = caplog.text.lower()
    assert "login1@ruesma.es" not in texto and "@ruesma" not in texto
    assert "cod_obra" not in texto and "lineas" not in linea


def test_f069_r18_el_incierto_retomado_no_vuelve_a_escribir_la_resolucion(caplog):
    caplog.set_level(logging.INFO)
    guardada = {**f.peticion("luis").a_dict(), CLAVE_RESOLUCION: RESOLUCION_GUARDADA}
    f.procesar(f.sigrid(), alta=_incierto(guardada))
    assert not [r for r in caplog.records if "origen_usu=" in r.getMessage()]


# ------------------------------------------------------------------ #
# R20 · el adjunto, con el usu guardado
# ------------------------------------------------------------------ #
def test_f069_r20_el_adjunto_va_con_el_usu_de_la_peticion_con_resolucion():
    creado = replace(previa_ok(f.peticion()), estado="creado")
    sigrid = SigridFalso(previa=previa_ok(f.peticion()), grabacion=creado,
                         usuarios={"login1b": "LOGIN1B"})
    repo, doc, resultado = f.procesar(sigrid, lista='{"login1": {"usu": "login1b"}}',
                                      modo=ModoAlta.REAL)
    assert resultado.estado is EstadoAlta.REGISTRADO
    (adjunto,) = [c for c in sigrid.llamadas if c[0] == "adjuntar_pdf"]
    assert adjunto[-1] == "LOGIN1B"


def test_f069_r20_reintentar_adjunto_usa_el_usu_guardado_sin_resolver():
    guardada = {**f.peticion("luis").a_dict(), CLAVE_RESOLUCION: RESOLUCION_GUARDADA}
    alta = AltaActual(estado=EstadoAlta.REGISTRADO, modo="real", sigrid_con_ide=9123461,
                      sigrid_cod="AC26/1", adjunto_estado=AdjuntoEstado.ERROR, peticion=guardada)
    sigrid = SigridFalso(usuarios={"login1": "login1"})
    repo, doc, resultado = f.procesar(sigrid, alta=alta, modo=ModoAlta.REAL,
                                      lista='{"login1": {"usu": "otro"}}')
    assert resultado.decision is Decision.SOLO_ADJUNTO
    assert sigrid.operaciones() == ["adjuntar_pdf"]
    assert sigrid.llamadas[0][-1] == "luis"
    assert repo.ultimo(doc).peticion == guardada
