# tests/test_f053_servicio_previa.py
"""F-053 · T10 · previa y simulación (R16, R17, R18, R19, R35).

- R16: se guardan la petición y, de la respuesta, SOLO ``estado``, ``con_ide``,
  ``cod``, ``avisos``, ``lineas`` y ``totales`` (nunca ``cabecera`` ni ``filas``).
- R17: lo que la previa no devuelve tal cual se pidió ⇒ ``revisar``.
- R18: un 400 de la previa lleva el alta al estado de la tabla, con sus motivos
  (también los de ``details.lineas``).
- R19: en simulación, previa limpia ⇒ ``simulado`` y NUNCA ``commit=true``.
"""
from __future__ import annotations

import json

import pytest

from application.alta_sigrid_service import AltaSigridService
from domain.models.alta_models import (
    AccionAlta,
    ErrorAlta,
    EstadoAlta,
    ModoAlta,
    PeticionAlbaran,
    RespuestaAlta,
    TipoFallo,
)
from domain.services.validador_alta import validar_y_construir
from tests.f053_datos import CONFIG, USU, HOY, datos, sin_vincular, vinculada
from tests.f053_fakes import (
    AHORA,
    DESDE,
    ESPERA,
    PdfFalso,
    RepoFalso,
    SigridFalso,
    previa_ok,
)

D = datos(vinculada(1), sin_vincular(2, codigo_partida_final=None))


def _peticion() -> PeticionAlbaran:
    peticion = validar_y_construir(D, CONFIG, HOY, USU)
    assert isinstance(peticion, PeticionAlbaran)
    return peticion


def _procesar(sigrid, modo=ModoAlta.SIMULACION):
    repo = RepoFalso()
    doc = repo.anadir(D)
    servicio = AltaSigridService(
        repo=repo, sigrid=sigrid, pdf=PdfFalso(), config=CONFIG, usuario_respaldo=USU, modo=modo, desde=DESDE,
        espera=ESPERA, tolerancia_eur=0.05,
        avisos_bloqueantes=frozenset({"producto_sin_historico"}), reloj=lambda: AHORA,
    )
    resultado = servicio.procesar(doc, AccionAlta.ALTA)
    return repo, doc, resultado


def _cuerpo_completo(peticion: PeticionAlbaran) -> dict:
    """Un 200 como el de sigrid-api, con lo que NO debe guardarse."""
    base = previa_ok(peticion).a_dict()
    return {
        **base, "ok": True, "committed": False, "dry_run": True,
        "cabecera": {"entcif": "B00000000", "banco": "ES00 0000 IBAN-DE-MENTIRA"},
        "filas": {"dca": {"cpacue": "IBAN-DE-MENTIRA"}, "dcapro": [{}], "log": {}},
        "warnings": ["DRY-RUN"], "contrato": {"ctride": 1}, "movimientos": [{"almcan": 1}],
        "estados_contrato": {"estser_before": 0},
    }


# ------------------------------------------------------------------ #
# R16 · qué se guarda
# ------------------------------------------------------------------ #
def test_f053_r16_se_guarda_la_peticion_y_solo_lo_de_r16():
    peticion = _peticion()
    sigrid = SigridFalso(previa=RespuestaAlta.desde_cuerpo(_cuerpo_completo(peticion)))
    repo, doc, _ = _procesar(sigrid)
    guardado = repo.ultimo(doc)
    # F-069 R16: junto al cuerpo va la resolucion (que nunca se manda, R17).
    assert "resolucion" in guardado.peticion
    assert {k: v for k, v in guardado.peticion.items() if k != "resolucion"} == peticion.a_dict()
    assert set(guardado.respuesta) == {"estado", "con_ide", "cod", "avisos", "lineas", "totales"}
    texto = json.dumps([guardado.peticion, guardado.respuesta, list(guardado.avisos)])
    for prohibido in ("IBAN", "banco", "cpacue", "cabecera", "filas", "movimientos"):
        assert prohibido not in texto


def test_f053_r35_ni_la_clave_ni_el_pdf_en_lo_guardado():
    sigrid = SigridFalso(previa=previa_ok(_peticion()))
    repo, _doc, _ = _procesar(sigrid)
    texto = json.dumps([r.peticion for _, r in repo.guardados] +
                       [r.respuesta for _, r in repo.guardados])
    assert "x-functions-key" not in texto and "clave" not in texto and "%PDF" not in texto


# ------------------------------------------------------------------ #
# R19 · simulación
# ------------------------------------------------------------------ #
def test_f053_r19_previa_limpia_en_simulacion_es_simulado():
    sigrid = SigridFalso(previa=previa_ok(_peticion(), cod="AC26/16001", con_ide=9123457,
                                          avisos=[{"codigo": "cod_provisional", "mensaje": "m"}]))
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.SIMULADO
    guardado = repo.ultimo(doc)
    assert guardado.sigrid_cod == "AC26/16001"  # «se habría creado como…»
    assert guardado.sigrid_con_ide is None       # provisional: no se guarda
    assert guardado.modo == "simulacion"
    assert [a["codigo"] for a in guardado.avisos] == ["cod_provisional"]
    assert sigrid.commits() == [False]


@pytest.mark.parametrize("previa", [
    "limpia", "revisar", "idempotente", "rechazo", "servidor",
])
def test_f053_r19_en_simulacion_nunca_commit_true(previa):
    peticion = _peticion()
    respuestas = {
        "limpia": previa_ok(peticion),
        "revisar": previa_ok(peticion, totales={"1": 1.0}),
        "idempotente": previa_ok(peticion, estado="idempotente"),
        "rechazo": ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="obra_no_encontrada"),
        "servidor": ErrorAlta(tipo=TipoFallo.SERVIDOR, status=503),
    }
    sigrid = SigridFalso(previa=respuestas[previa], grabacion=previa_ok(peticion, estado="creado"))
    _procesar(sigrid)
    assert sigrid.commits() == [False]
    assert ("adjuntar_pdf" in sigrid.operaciones()) is False


# ------------------------------------------------------------------ #
# R17 · revisar
# ------------------------------------------------------------------ #
def test_f053_r17_previa_distinta_es_revisar_con_sus_motivos():
    sigrid = SigridFalso(previa=previa_ok(_peticion(), totales={"1": 400.0},
                                          partidas={"2": "03.99"}))
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.REVISAR
    assert sorted((m.codigo, m.referencia_linea) for m in repo.ultimo(doc).motivos) == [
        ("importe_distinto", "1"), ("partida_distinta", "2"),
    ]
    assert repo.ultimo(doc).respuesta is not None


def test_f053_r17_aviso_bloqueante_es_revisar():
    aviso = {"codigo": "producto_sin_historico", "mensaje": "sin dcapro previa"}
    sigrid = SigridFalso(previa=previa_ok(_peticion(), avisos=[aviso]))
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.REVISAR
    assert [m.codigo for m in repo.ultimo(doc).motivos] == ["aviso_bloqueante"]


# ------------------------------------------------------------------ #
# R18 · 400 de la previa
# ------------------------------------------------------------------ #
def _lineas(*codigos: str) -> tuple[dict, ...]:
    return tuple({"indice": i, "referencia_linea": str(i + 1), "codigo": c, "mensaje": f"m{i}"}
                 for i, c in enumerate(codigos))


@pytest.mark.parametrize(("error", "estado"), [
    (ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="lineas_no_validas",
               lineas=_lineas("partida_no_encontrada", "analitica_no_resuelta"),
               mensaje="Hay líneas…"), EstadoAlta.NO_ADMITIDO),
    (ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="lineas_no_validas",
               lineas=_lineas("partida_no_encontrada", "naturaleza_no_valida")), EstadoAlta.ERROR),
    (ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="referencia_en_conflicto"),
     EstadoAlta.REVISAR),
    (ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="proveedor_sin_albaran_previo"),
     EstadoAlta.NO_ADMITIDO),
    (ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, mensaje="Solicitud invalida."), EstadoAlta.ERROR),
    (ErrorAlta(tipo=TipoFallo.SERVIDOR, status=500), EstadoAlta.ERROR),
    (ErrorAlta(tipo=TipoFallo.TIEMPO_AGOTADO), EstadoAlta.ERROR),
])
@pytest.mark.parametrize("modo", [ModoAlta.SIMULACION, ModoAlta.REAL])
def test_f053_r18_previa_rechazada_va_a_su_estado(error, estado, modo):
    sigrid = SigridFalso(previa=error)
    repo, doc, resultado = _procesar(sigrid, modo)
    assert resultado.estado is estado
    guardado = repo.ultimo(doc)
    assert guardado.respuesta == error.a_dict()
    assert sigrid.commits() == [False]  # tras una previa fallida, nunca se graba


def test_f053_r18_motivos_de_cada_linea_del_400():
    error = ErrorAlta(tipo=TipoFallo.RECHAZO, status=400, codigo="lineas_no_validas",
                      lineas=_lineas("partida_no_encontrada"), mensaje="Hay líneas…")
    repo, doc, _ = _procesar(SigridFalso(previa=error))
    assert [(m.codigo, m.detalle, m.referencia_linea) for m in repo.ultimo(doc).motivos] == [
        ("lineas_no_validas", "Hay líneas…", None), ("partida_no_encontrada", "m0", "1"),
    ]


def test_f053_r18_previa_con_estado_desconocido_es_error():
    sigrid = SigridFalso(previa=RespuestaAlta(estado="raro"))
    repo, doc, resultado = _procesar(sigrid)
    assert resultado.estado is EstadoAlta.ERROR
    assert [m.codigo for m in repo.ultimo(doc).motivos] == ["respuesta_inesperada"]
