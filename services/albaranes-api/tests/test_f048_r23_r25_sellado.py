# tests/test_f048_r23_r25_sellado.py
"""F-048 · R23 y R25: el sello es de sv2 y va sobre el documento FINAL.

- R23: ``origen_datos`` lo escribe el resolver; lo que ponga la IA se pisa.
  ``lectura_correo`` no llega al ``data`` final.
- R25: la precedencia y el cruce se aplican al documento de FASE 2 (IA2
  puede tocar la cabecera): la lectura del PAPEL es la del documento final.
- D3 y aviso A de la review del bloque C1: la lectura del CORREO es SIEMPRE
  la de FASE 1; la que devuelva IA2 en ``documento_revisado`` se ignora.
- El resolver no muta nada de lo que recibe: el envelope de fase 2 ya esta
  persistido cuando se sella (auditoria de lo que dijo cada IA).

Sin red, sin BBDD y sin LLM.
"""
from __future__ import annotations

import copy

import pytest
from application.services.origen_datos_resolver import sellar_origen_datos
from application.services.phase_merge import construir_envelope_final
from domain.models.lectura_correo import LecturaCorreo
from ruesma_comun.contratos import ClasificacionAlbaran
from ruesma_comun.contratos.origen_datos import (
    FUENTE_CORREO,
    MOTIVO_CORREO_UNICO,
    MOTIVO_SIN_CORREO,
    OrigenDatos,
)
from ruesma_comun.correo import construir_contexto_correo

OBRAS = {"945": "0945", "1203": "1203"}
CORREO = construir_contexto_correo("Obra 0945", "Os paso los albaranes. CENTINELA-F048")
LECTURA_IA1 = {"obra_codigos": ["0945"], "evidencia": "Obra 0945"}
LECTURA_IA2 = {"obra_codigos": ["1203"], "evidencia": "IA2 dice 1203"}

# Lo que una IA podria devolver por su cuenta en `origen_datos`: nada de
# esto puede sobrevivir al sello.
ORIGEN_DE_LA_IA = {
    "version": 99,
    "correo_presente": False,
    "correo_sha256": "f" * 64,
    "evidencia": "lo que dice la IA",
    "obra": {"fuente": "papel", "motivo": "correo_ambiguo", "valor_final": "7777", "discrepancia": True},
}


def _env1(obra: str | None, lectura: dict | None = LECTURA_IA1) -> dict:
    return {
        "meta": {"phase": "phase_1"},
        "data": {"cabecera": {"obra_codigo": obra}, "lineas": [], "lectura_correo": lectura},
        "debug": {"d": 1},
    }


def _env2(obra: str | None, lectura: dict | None = LECTURA_IA2, **extra) -> dict:
    revisado = {"cabecera": {"obra_codigo": obra}, "lineas": [], "lectura_correo": lectura, **extra}
    return {
        "meta": {"phase": "phase_2"},
        "data": {"review_status": "ok", "documento_revisado": revisado, "razonamientos": []},
        "debug": {"phase_1_json": {"data": {"lectura_correo": LECTURA_IA1}}},
    }


def _origen(final: dict) -> OrigenDatos:
    return OrigenDatos.model_validate(final["data"]["origen_datos"])


# ---------------------------------------------------------------- #
# R23 — el sello es del resolver.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("correo", [CORREO, None], ids=["con_correo", "sin_correo"])
def test_f048_r23_lo_que_la_ia_ponga_en_origen_datos_se_pisa(correo):
    envelope = {"data": {"cabecera": {"obra_codigo": "0945"}, "origen_datos": ORIGEN_DE_LA_IA}}

    final = sellar_origen_datos(envelope, lectura=LECTURA_IA1, correo=correo, obras_conocidas=OBRAS)

    origen = _origen(final)
    assert origen.version == 1
    assert origen.correo_presente is (correo is not None)
    assert origen.obra.valor_final == "0945"
    assert origen.obra.discrepancia is False
    assert "lo que dice la IA" not in str(final["data"]["origen_datos"])
    assert "f" * 64 not in str(final["data"]["origen_datos"])


@pytest.mark.parametrize("correo", [CORREO, None], ids=["con_correo", "sin_correo"])
@pytest.mark.parametrize("lectura", [LECTURA_IA1, None], ids=["con_lectura", "sin_lectura"])
def test_f048_r23_lectura_correo_no_llega_al_data_final(correo, lectura):
    envelope = {"data": {"cabecera": {"obra_codigo": "0945"}, "lectura_correo": lectura}}

    final = sellar_origen_datos(envelope, lectura=lectura, correo=correo, obras_conocidas=OBRAS)

    assert "lectura_correo" not in final["data"]


def test_f048_r23_la_lectura_vale_como_modelo_o_como_dict():
    envelope = {"data": {"cabecera": {"obra_codigo": "1203"}}}
    como_dict = sellar_origen_datos(envelope, lectura=LECTURA_IA1, correo=CORREO, obras_conocidas=OBRAS)
    como_modelo = sellar_origen_datos(
        envelope, lectura=LecturaCorreo.model_validate(LECTURA_IA1), correo=CORREO, obras_conocidas=OBRAS,
    )

    assert como_dict == como_modelo
    assert _origen(como_modelo).obra.valor_correo == "0945"
    assert _origen(como_modelo).evidencia == "Obra 0945"


@pytest.mark.parametrize("correo", [CORREO, None], ids=["con_correo", "sin_correo"])
def test_f048_r23_el_resolver_no_muta_lo_que_recibe(correo):
    env1, env2 = _env1("1203"), _env2("1203")
    envelope = construir_envelope_final(env_fase1=env1, env_fase2=env2)
    lectura = copy.deepcopy(LECTURA_IA1)
    antes = copy.deepcopy((env1, env2, envelope, lectura))

    final = sellar_origen_datos(envelope, lectura=lectura, correo=correo, obras_conocidas=OBRAS)

    assert (env1, env2, envelope, lectura) == antes
    assert final is not envelope
    assert final["data"] is not envelope["data"]
    # Con correo, la cabecera cambia en la COPIA (0945 manda sobre 1203).
    if correo is not None:
        assert final["data"]["cabecera"]["obra_codigo"] == "0945"
        assert final["data"]["cabecera"] is not envelope["data"]["cabecera"]


def test_f048_r23_el_resto_del_envelope_se_conserva():
    clasificacion = ClasificacionAlbaran(familia="hormigon", confianza_pct=90.0, motivo="m", origen="ia1")
    envelope = construir_envelope_final(
        env_fase1=_env1("1203"), env_fase2=_env2("1203", proveedor="X"), clasificacion=clasificacion,
    )

    final = sellar_origen_datos(envelope, lectura=LECTURA_IA1, correo=CORREO, obras_conocidas=OBRAS)

    assert final["meta"] == envelope["meta"]
    assert final["debug"] == envelope["debug"]
    assert final["data"]["clasificacion"] == envelope["data"]["clasificacion"]
    assert final["data"]["proveedor"] == "X"
    assert final["data"]["lineas"] == []
    esperado = {k: v for k, v in envelope["data"].items() if k not in ("cabecera", "lectura_correo")}
    assert {k: v for k, v in final["data"].items() if k not in ("cabecera", "origen_datos")} == esperado


# ---------------------------------------------------------------- #
# R25 — sobre el documento FINAL; la lectura del correo, la de FASE 1.
# ---------------------------------------------------------------- #
def test_f048_r25_el_papel_es_el_de_fase_2():
    """IA1 leyo 1203 en el papel; IA2 lo corrigio a 0945, que es lo que
    dice el correo: no hay discrepancia. Con el papel de fase 1 la habria."""
    envelope = construir_envelope_final(env_fase1=_env1("1203"), env_fase2=_env2("0945"))

    final = sellar_origen_datos(envelope, lectura=LECTURA_IA1, correo=CORREO, obras_conocidas=OBRAS)

    origen = _origen(final)
    assert origen.obra.valor_papel == "0945"
    assert origen.obra.discrepancia is False
    assert final["data"]["cabecera"]["obra_codigo"] == "0945"


def test_f048_r25_ia2_cambia_la_cabecera_y_hay_discrepancia_con_el_correo():
    envelope = construir_envelope_final(env_fase1=_env1("0945"), env_fase2=_env2("1203"))

    final = sellar_origen_datos(envelope, lectura=LECTURA_IA1, correo=CORREO, obras_conocidas=OBRAS)

    origen = _origen(final)
    assert origen.obra.valor_papel == "1203"
    assert origen.obra.valor_correo == "0945"
    assert origen.obra.discrepancia is True
    assert final["data"]["cabecera"]["obra_codigo"] == "0945"


def test_f048_r25_la_lectura_del_correo_de_ia2_se_ignora():
    """Aviso A: IA2 devuelve OTRA lectura del correo (1203). Cuenta la de
    IA1 (0945), y la de IA2 tampoco llega al data final."""
    envelope = construir_envelope_final(env_fase1=_env1(None), env_fase2=_env2(None, LECTURA_IA2))

    final = sellar_origen_datos(
        envelope, lectura=_env1(None)["data"]["lectura_correo"], correo=CORREO, obras_conocidas=OBRAS,
    )

    origen = _origen(final)
    assert origen.obra.fuente == FUENTE_CORREO
    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert origen.obra.valor_correo == "0945"
    assert origen.evidencia == "Obra 0945"
    assert final["data"]["cabecera"]["obra_codigo"] == "0945"
    assert "lectura_correo" not in final["data"]
    assert "1203" not in str(final["data"])


def test_f048_r25_sin_fase_2_se_sella_el_de_fase_1():
    envelope = construir_envelope_final(env_fase1=_env1("1203"), env_fase2=None)

    final = sellar_origen_datos(envelope, lectura=None, correo=None, obras_conocidas=None)

    assert _origen(final).obra.motivo == MOTIVO_SIN_CORREO
    assert final["data"]["cabecera"]["obra_codigo"] == "1203"
    assert "lectura_correo" not in final["data"]
