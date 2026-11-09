# tests/test_f110_previa.py
"""F-110 · T8 · la previa compara el ``dto`` pedido (R11, R12).

- R11: una línea pedida con ``dto`` cuya línea de la previa no trae ``dto``, no
  es un número legible o difiere en más de 0,005 da ``dto_distinto`` (detalle
  «pedido 7, Sigrid —») ⇒ ``revisar``. 0,005 justos valen.
- R12: las pedidas sin ``dto`` no lo comparan (aunque la previa lo traiga, p. ej.
  copiado del ``ctrpro`` por la R15 de sigrid-api); ``importe_distinto`` y
  ``partida_distinta`` no cambian; en ``idempotente`` no se compara ``dto``
  (sigrid-api lo devuelve nulo).

Puro: ``comparar`` con respuestas construidas a mano (contrato v8.4: la línea
gana ``dto`` y ``precio_bruto`` solo cuando lleva descuento).
"""
from __future__ import annotations

import pytest

from domain.models.alta_models import LineaPeticion, Motivo, PeticionAlbaran, RespuestaAlta
from domain.services.comparador_previa import comparar

CON_DTO = LineaPeticion(referencia_linea="1", cantidad=12.0, precio=0.645, dto=7.0,
                        producto="MA9999", descripcion="x", partida="03.04.02")
SIN_DTO = LineaPeticion(referencia_linea="2", cantidad=10.0, precio=4.4, producto="MA9999",
                        descripcion="y", partida="03.04.02")
IMPORTES = {"1": 7.20, "2": 44.0}


def _peticion(*lineas: LineaPeticion) -> PeticionAlbaran:
    return PeticionAlbaran(
        cod_obra="0404", cif_proveedor="B00000000", cod_contrato=None,
        referencia_externa="ALB-d1", su_referencia="N1", usu="U", fecha_albaran=20261003,
        empide=None, lineas=lineas,
    )


def _devuelta(ref: str, total: float, partida: str | None = "03.04.02", **extra) -> dict:
    return {"referencia_linea": ref, "total": total, "partida": partida, "avisos": [], **extra}


def _comparar(*devueltas: dict, estado: str = "previsto", lineas=(CON_DTO, SIN_DTO)) -> list[Motivo]:
    respuesta = RespuestaAlta(estado=estado, lineas=tuple(devueltas))
    return comparar(_peticion(*lineas), respuesta, IMPORTES, 0.05, frozenset())


# ------------------------------------------------------------------- R11
def test_f110_r11_mismo_dto_sin_motivos():
    assert _comparar(
        _devuelta("1", 7.20, dto=7, precio_bruto=0.645, precio=0.6), _devuelta("2", 44.0),
    ) == []


@pytest.mark.parametrize("dto_sigrid", [7.005, 6.995, 7.0])
def test_f110_r11_borde_de_0005_vale(dto_sigrid):
    assert _comparar(_devuelta("1", 7.20, dto=dto_sigrid), _devuelta("2", 44.0)) == []


@pytest.mark.parametrize("dto_sigrid, texto", [(7.006, "7,006"), (6.99, "6,99"), (0, "0"), (40, "40")])
def test_f110_r11_difiere_mas_de_0005(dto_sigrid, texto):
    assert _comparar(_devuelta("1", 7.20, dto=dto_sigrid), _devuelta("2", 44.0)) == [
        Motivo("dto_distinto", f"pedido 7, Sigrid {texto}", "1"),
    ]


def test_f110_r11_sin_dto_en_la_previa():
    assert _comparar(_devuelta("1", 7.20), _devuelta("2", 44.0)) == [
        Motivo("dto_distinto", "pedido 7, Sigrid —", "1"),
    ]


@pytest.mark.parametrize("ilegible", [None, "7", "siete", True, float("nan"), [7]])
def test_f110_r11_dto_ilegible(ilegible):
    assert _comparar(_devuelta("1", 7.20, dto=ilegible), _devuelta("2", 44.0)) == [
        Motivo("dto_distinto", "pedido 7, Sigrid —", "1"),
    ]


def test_f110_r11_decimales_en_el_detalle():
    pedida = LineaPeticion(referencia_linea="1", cantidad=10.0, precio=10.0, dto=7.46,
                           producto="MA9999", descripcion="x", partida="03.04.02")
    respuesta = RespuestaAlta(estado="previsto", lineas=(_devuelta("1", 92.54, dto=7.5),))
    assert comparar(_peticion(pedida), respuesta, {"1": 92.54}, 0.05, frozenset()) == [
        Motivo("dto_distinto", "pedido 7,46, Sigrid 7,5", "1"),
    ]


def test_f110_r11_junto_a_los_demas_motivos_de_la_linea():
    motivos = _comparar(_devuelta("1", 7.74, partida=None), _devuelta("2", 44.0))
    assert [m.codigo for m in motivos] == ["importe_distinto", "partida_distinta", "dto_distinto"]


def test_f110_r11_una_linea_que_falta_no_da_dto_distinto():
    motivos = _comparar(_devuelta("2", 44.0))
    assert motivos == [Motivo("lineas_distintas", "falta en Sigrid", "1")]


# ------------------------------------------------------------------- R12
def test_f110_r12_pedida_sin_dto_no_compara_aunque_venga():
    assert _comparar(
        _devuelta("1", 7.20, dto=7), _devuelta("2", 44.0, dto=10, precio_bruto=4.888889),
    ) == []


def test_f110_r12_idempotente_no_compara_dto():
    assert _comparar(_devuelta("1", 7.20, dto=None), _devuelta("2", 44.0),
                     estado="idempotente") == []
    assert _comparar(_devuelta("1", 7.20), _devuelta("2", 44.0), estado="idempotente") == []


def test_f110_r12_importe_distinto_intacto():
    assert _comparar(_devuelta("1", 7.26, dto=7), _devuelta("2", 44.0)) == [
        Motivo("importe_distinto", "aprobado 7.2, Sigrid 7.26", "1"),
    ]
    assert _comparar(_devuelta("1", 7.25, dto=7), _devuelta("2", 44.0)) == []


def test_f110_r11_en_el_servicio_va_a_revisar_sin_grabar():
    from domain.models.alta_models import AccionAlta, EstadoAlta, ModoAlta
    from tests.f053_datos import datos
    from tests.f053_fakes import RepoFalso, SigridFalso
    from tests.test_f110_peticion import ENCENDIDA, _cecois, _servicio

    previa = RespuestaAlta(estado="previsto", con_ide=9123457, cod="AC26/16001",
                           lineas=(_devuelta("7", 7.20),), totales={"n_lineas": 1})
    sigrid = SigridFalso(previa=previa)
    repo = RepoFalso()
    doc = repo.anadir(datos(_cecois()))
    resultado = _servicio(repo, sigrid, ENCENDIDA, ModoAlta.REAL).procesar(doc, AccionAlta.ALTA)
    assert resultado.estado is EstadoAlta.REVISAR
    assert [(m.codigo, m.detalle) for m in repo.ultimo(doc).motivos] == [
        ("dto_distinto", "pedido 7, Sigrid —"),
    ]
    assert sigrid.commits() == [False]
