# tests/test_f110_peticion.py
"""F-110 · T6 · la petición de sv9 con el descuento de la línea (R6–R10, R22).

- R6: con la guarda apagada, la petición (``a_dict``) es la de F-106 con y sin
  descuentos: precio neto y sin la clave ``dto``.
- R7, R9: encendida, las líneas «con descuento» llevan el precio de comun (P o
  el bruto despejado) y ``dto`` justo detrás de ``precio``; las vinculadas
  igual. Las que no tienen descuento aplicable, sin la clave.
- R8: si la línea con ``dto`` no cuadra a Sigrid (o el precio no se despeja),
  ``no_admitido`` con ``linea_no_cuadra`` y el detalle «a Sigrid: …», sin
  llamar a sigrid-api; detrás del motivo de F-106 R17 y sin repetirlo.
- R10: ``desde_dict`` lee la petición con y sin ``dto``; un ``incierto`` se
  retoma con la petición guardada sea cual sea la guarda.
- Aviso 1 de sigrid-api (2026-10-30): el modo clásico y ``albaran-directo``
  ignoran ``dto`` sin error; el bruto con ``dto`` solo puede ir por el modo
  extendido (``lineas`` + ``referencia_externa``, ruta ``sigrid/albaran``).

Sin red ni BBDD (``tests/f053_datos.py`` y ``tests/f053_fakes.py``).
"""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import timedelta

import httpx
import pytest

from application.alta_sigrid_service import AltaSigridService
from domain.models.alta_models import (
    AccionAlta,
    AltaActual,
    EstadoAlta,
    LineaAlta,
    LineaPeticion,
    ModoAlta,
    Motivo,
    PeticionAlbaran,
)
from domain.services.validador_alta import ConfigAlta, validar_y_construir
from infrastructure.sigrid.sigrid_api_alta_client import RUTA_ALBARAN, SigridApiAltaClient
from tests.f053_datos import CONFIG, HOY, MAPEO, USU, datos, sin_vincular, vinculada
from tests.f053_fakes import AHORA, DESDE, ESPERA, PdfFalso, RepoFalso, SigridFalso, previa_ok

ENCENDIDA = ConfigAlta(mapeo=MAPEO, enviar_dto=True)
APAGADA = ConfigAlta(mapeo=MAPEO, enviar_dto=False)


def _cecois(id_: int = 7, **cambios) -> LineaAlta:
    """CECOIS A 26018351: 12 × 0,645 −7 % = 7,20, sin vincular."""
    base = sin_vincular(
        id_, cantidad_albaran=12.0, cantidad_convertida=None, importe_calculado=7.20,
        precio_unitario_final=0.645, descuento_albaran_aplicado=7.0,
    )
    return replace(base, **cambios)


def _sin_dto(id_: int = 8, **cambios) -> LineaAlta:
    base = sin_vincular(id_, precio_unitario_final=4.4, descuento_albaran_aplicado=None)
    return replace(base, **cambios)


def _peticion(*lineas: LineaAlta, config: ConfigAlta = ENCENDIDA) -> PeticionAlbaran:
    resultado = validar_y_construir(datos(*lineas), config, HOY, USU)
    assert isinstance(resultado, PeticionAlbaran), resultado
    return resultado


def _linea(*lineas: LineaAlta, config: ConfigAlta = ENCENDIDA) -> dict:
    (linea,) = _peticion(*lineas, config=config).a_dict()["lineas"]
    return linea


# ------------------------------------------------------------------- R6
def test_f110_r6_apagada_es_la_peticion_de_f106():
    linea = _linea(_cecois(), config=APAGADA)
    assert linea == {
        "referencia_linea": "7", "producto": "MA9999",
        "descripcion": "SACO CEMENTO CEM II 25 KG", "unidad": "UD",
        "cantidad": 12.0, "precio": 0.6, "partida": "03.04.02",
    }


def test_f110_r6_apagada_identica_con_y_sin_descuentos():
    lineas = (_cecois(1), _sin_dto(2), vinculada(3, precio_unitario_final=68.4))
    assert _peticion(*lineas, config=APAGADA).a_dict() == _peticion(*lineas, config=CONFIG).a_dict()
    assert all("dto" not in l for l in _peticion(*lineas, config=APAGADA).a_dict()["lineas"])


def test_f110_r6_config_de_f053_esta_apagada():
    assert CONFIG.enviar_dto is False


# ------------------------------------------------------------- R7 · R22
def test_f110_r7_cecois_bruto_y_dto_tras_el_precio():
    linea = _linea(_cecois())
    assert list(linea) == [
        "referencia_linea", "producto", "descripcion", "unidad", "cantidad", "precio", "dto",
        "partida",
    ]
    assert (linea["cantidad"], linea["precio"], linea["dto"]) == (12.0, 0.645, 7.0)


def test_f110_r7_sin_descuento_sin_la_clave():
    peticion = _peticion(_cecois(1), _sin_dto(2))
    primera, segunda = peticion.a_dict()["lineas"]
    assert primera["dto"] == 7.0
    assert "dto" not in segunda and segunda["precio"] == 4.4


@pytest.mark.parametrize("cambios, esperado", [
    # (b) 1 × 151,20 −7 % = 140,62
    ({"cantidad_albaran": 1.0, "importe_calculado": 140.62, "precio_unitario_final": 151.2},
     (1.0, 151.2, 7.0)),
    # (c) un céntimo de más ⇒ despejado
    ({"cantidad_albaran": 10.0, "importe_calculado": 249.21, "precio_unitario_final": 26.796},
     (10.0, 26.796774, 7.0)),
    # (e) devolución −1 × 18,00 −10 % = −16,20
    ({"cantidad_albaran": -1.0, "importe_calculado": -16.2, "precio_unitario_final": 18.0,
      "descuento_albaran_aplicado": 10.0}, (-1.0, 18.0, 10.0)),
    # (h) d 7,456 ⇒ dto 7,46
    ({"cantidad_albaran": 10.0, "importe_calculado": 92.54, "precio_unitario_final": 10.0,
      "descuento_albaran_aplicado": 7.456}, (10.0, 10.0, 7.46)),
])
def test_f110_r22_casos_sin_vincular(cambios, esperado):
    linea = _linea(_cecois(**cambios))
    assert (linea["cantidad"], linea["precio"], linea["dto"]) == esperado


@pytest.mark.parametrize("descuento", [None, 0.0, -5.0, 150.0])
def test_f110_r22g_descuento_no_aplicable_va_como_hoy(descuento):
    linea = _linea(_cecois(
        cantidad_albaran=10.0, importe_calculado=100.0, precio_unitario_final=10.0,
        descuento_albaran_aplicado=descuento,
    ))
    assert "dto" not in linea and linea["precio"] == 10.0


def test_f110_r9_r22d_vinculada_feymaco_con_dto():
    linea = _linea(vinculada(
        3, cantidad_albaran=108.0, cantidad_convertida=108.0, importe_calculado=35.19,
        precio_unitario_final=0.543, descuento_albaran_aplicado=40.0,
    ))
    assert linea == {
        "referencia_linea": "3", "ctrpro_ide": 700101, "cantidad": 108.0, "precio": 0.543,
        "dto": 40.0, "partida": "03.02.01",
    }


def test_f110_r9_vinculada_con_conversion_despeja_con_la_convertida():
    linea = _linea(vinculada(
        3, cantidad_albaran=48.0, cantidad_convertida=4.0, importe_calculado=93.0,
        precio_unitario_final=2.083333, descuento_albaran_aplicado=7.0,
    ))
    assert (linea["cantidad"], linea["precio"], linea["dto"]) == (4.0, 25.0, 7.0)


# -------------------------------------------------------------------- R8
DETALLE_F = "a Sigrid: 100000 × 0,132712 × (1 − 7 %) = 12342,22 ≠ 12342,17"


def _caso_f() -> LineaAlta:
    """(f) Qa 100000, Qc 1000 (sin vincular), P 13,27115, d 7, I 12342,17: cuadra
    con Qc (F-106 R17 no lo para), no a Sigrid con Qa."""
    return _cecois(cantidad_albaran=100000.0, cantidad_convertida=1000.0,
                   importe_calculado=12342.17, precio_unitario_final=13.27115)


def test_f110_r8_r22f_no_cuadra_a_sigrid():
    assert validar_y_construir(datos(_caso_f()), ENCENDIDA, HOY, USU) == [
        Motivo("linea_no_cuadra", DETALLE_F, "7"),
    ]


def test_f110_r8_apagada_no_lo_mira():
    assert isinstance(validar_y_construir(datos(_caso_f()), APAGADA, HOY, USU), PeticionAlbaran)


def test_f110_r8_precio_no_despejable():
    """d 100 % con un importe dentro de la tolerancia de F-106 (0 frente a 0,01)."""
    linea = _cecois(cantidad_albaran=10.0, importe_calculado=0.01, precio_unitario_final=10.0,
                    descuento_albaran_aplicado=100.0)
    assert validar_y_construir(datos(linea), ENCENDIDA, HOY, USU) == [
        Motivo("linea_no_cuadra", "a Sigrid: el precio no se puede despejar con un dto del 100 %", "7"),
    ]


def test_f110_r8_detras_del_de_f106_y_sin_repetirlo():
    """La que ya para F-106 R17 no lleva un segundo ``linea_no_cuadra``; la otra,
    el suyo, en el orden de las líneas."""
    mala_f106 = _cecois(1, precio_unitario_final=11.2, importe_calculado=104.16,
                        cantidad_albaran=48.0)
    resultado = validar_y_construir(datos(mala_f106, replace(_caso_f(), id=2)), ENCENDIDA, HOY, USU)
    assert resultado == [
        Motivo("linea_no_cuadra", "48 × 11,2 × (1 − 7 %) = 499,97 ≠ 104,16", "1"),
        Motivo("linea_no_cuadra", DETALLE_F, "2"),
    ]


def test_f110_r8_sin_cantidad_solo_el_motivo_de_cantidad():
    linea = _cecois(cantidad_albaran=None)
    assert validar_y_construir(datos(linea), ENCENDIDA, HOY, USU) == [
        Motivo("cantidad_no_valida", "", "7"),
    ]


def test_f110_r8_es_de_no_admitido_y_no_llama_a_sigrid():
    sigrid = SigridFalso()
    repo = RepoFalso()
    doc = repo.anadir(datos(_caso_f()))
    resultado = _servicio(repo, sigrid, ENCENDIDA).procesar(doc, AccionAlta.ALTA)
    assert resultado.estado is EstadoAlta.NO_ADMITIDO
    assert [(m.codigo, m.detalle) for m in repo.ultimo(doc).motivos] == [("linea_no_cuadra", DETALLE_F)]
    assert "alta_albaran" not in sigrid.operaciones()


# ------------------------------------------------------------------- R10
def _servicio(repo, sigrid, config, modo=ModoAlta.SIMULACION):
    return AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=PdfFalso(), config=config, usuario_respaldo=USU,
        modo=modo, desde=DESDE, espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset({"producto_sin_historico"}), reloj=lambda: AHORA,
    )


def test_f110_r10_desde_dict_con_y_sin_dto():
    con = _peticion(_cecois(1), _sin_dto(2))
    assert PeticionAlbaran.desde_dict(con.a_dict()) == con
    assert PeticionAlbaran.desde_dict(con.a_dict()).lineas[0].dto == 7.0
    sin = _peticion(_cecois(1), _sin_dto(2), config=APAGADA)
    leida = PeticionAlbaran.desde_dict(json.loads(json.dumps(sin.a_dict())))
    assert leida == sin and all(l.dto is None for l in leida.lineas)


def test_f110_r10_linea_peticion_nace_sin_dto():
    linea = LineaPeticion(referencia_linea="1", cantidad=1.0, precio=2.0)
    assert linea.dto is None and "dto" not in linea.a_dict()


@pytest.mark.parametrize("guardada_con, guarda_ahora", [
    (ENCENDIDA, APAGADA), (APAGADA, ENCENDIDA),
])
def test_f110_r10_incierto_reenvia_la_peticion_guardada(guardada_con, guarda_ahora):
    d = datos(_cecois(1), _sin_dto(2))
    guardada = _peticion(*d.lineas, config=guardada_con)
    alta = AltaActual(estado=EstadoAlta.INCIERTO, ultimo_intento_at_utc=AHORA - timedelta(hours=1),
                      peticion=guardada.a_dict())
    sigrid = SigridFalso(previa=previa_ok(guardada, estado="idempotente"))
    repo = RepoFalso()
    doc = repo.anadir(d, alta=alta)
    _servicio(repo, sigrid, guarda_ahora).procesar(doc, AccionAlta.ALTA)
    enviada = next(c[1] for c in sigrid.llamadas if c[0] == "alta_albaran")
    assert enviada == guardada
    assert enviada.a_dict() == guardada.a_dict()


# ---------------------------------------- aviso 1 · solo el modo extendido
def test_f110_aviso1_el_dto_solo_va_por_el_modo_extendido():
    """sigrid-api elige el modo por las claves: ``lineas`` o
    ``referencia_externa`` ⇒ extendido. El clásico y ``albaran-directo``
    descartan ``dto`` en silencio: la petición con ``dto`` nunca puede ir allí."""
    peticiones: list[httpx.Request] = []

    def servidor(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return httpx.Response(200, json={"estado": "previsto", "lineas": [], "totales": {}})

    cliente = SigridApiAltaClient(
        base_url="https://sigrid.invalid", function_key="clave-de-mentira", database="ruesma",
        transport=httpx.MockTransport(servidor), espera_base_s=0,
    )
    cliente.alta_albaran(_peticion(_cecois(1), _sin_dto(2)), False)
    (request,) = peticiones
    assert request.url.path == RUTA_ALBARAN == "/api/sigrid/albaran"
    cuerpo = json.loads(request.content)
    assert cuerpo["referencia_externa"].startswith("ALB-") and cuerpo["lineas"]
    assert "lineas_recibidas" not in cuerpo
    assert cuerpo["lineas"][0]["dto"] == 7.0 and "dto" not in cuerpo["lineas"][1]


def test_f110_aviso1_la_peticion_siempre_lleva_las_claves_del_extendido():
    for config in (ENCENDIDA, APAGADA):
        cuerpo = _peticion(_cecois(1), config=config).a_dict()
        assert {"lineas", "referencia_externa"} <= set(cuerpo)
        assert "lineas_recibidas" not in cuerpo
