# tests/test_f048_r19_r22_tabla_d5.py
"""F-048 · R17, R19–R22: la tabla de D5, fila a fila, en el resolver de sv2.

``sellar_origen_datos`` cruza las dos lecturas que devolvio IA1 —la del
CORREO (``lectura_correo.obra_codigos``) y la del PAPEL
(``cabecera.obra_codigo`` del documento final)— y sella ``origen_datos``.
No mira el texto del correo (D3): solo las listas de la IA.

| Correo (tras descartar lo que no esta en la lista) | Papel | Resultado |
|---|---|---|
| 1. sin codigo, o fuera de la lista | lo que lea la IA | manda la IA |
| 2. uno de la lista (activa o no) | igual, o sin codigo | manda el correo |
| 3. uno de la lista | distinto | manda el correo + discrepancia |
| 4. varios de la lista | el del papel es uno | el del papel |
| 5. varios de la lista | ninguno, o sin codigo | el del papel, o ninguno |

Y fuera de la tabla: sin lista de obras (cuentan todos, ``validada=None``) y
sin correo (``data`` identico salvo ``origen_datos``, R22).

Sin red, sin BBDD y sin LLM. Textos inventados, con el centinela.
"""
from __future__ import annotations

import copy

import pytest
from application.services.origen_datos_resolver import sellar_origen_datos
from ruesma_comun.contratos.origen_datos import (
    FUENTE_CORREO,
    FUENTE_PAPEL,
    MOTIVO_CORREO_AMBIGUO,
    MOTIVO_CORREO_CONFIRMA_PAPEL,
    MOTIVO_CORREO_FUERA_DE_LISTA,
    MOTIVO_CORREO_SIN_DATO,
    MOTIVO_CORREO_UNICO,
    MOTIVO_IA_SIN_LECTURA_CORREO,
    MOTIVO_SIN_CORREO,
    OrigenDatos,
)
from ruesma_comun.correo import construir_contexto_correo

CENTINELA = "CENTINELA-F048"

# normalizado -> codigo tal como figura en la lista (lo que da
# ``AlbaranExtractionService.obras_conocidas()``). 0320 es una obra NO
# activa (<= 0450): tambien cuenta (D5 revisada, 2026-09-23).
OBRAS = {"945": "0945", "1203": "1203", "320": "0320"}

CORREO = construir_contexto_correo(
    "Albaranes de la semana", f"Buenos dias, os paso los albaranes. {CENTINELA}"
)


def _envelope(papel: str | None = "0945", lectura: dict | None = None) -> dict:
    data: dict = {
        "cabecera": {"numero_albaran": "SS-0003967", "obra_codigo": papel},
        "lineas": [{"concepto": "HA-25", "cantidad": 7.5}],
        "clasificacion": {"familia": "hormigon", "origen": "ia1"},
        "lectura_correo": lectura,
    }
    return {"meta": {"phase": "phase_2"}, "data": data, "debug": {"x": 1}}


def _lectura(*codigos: str, evidencia: str | None = "Va para la obra") -> dict:
    return {"obra_codigos": list(codigos), "evidencia": evidencia}


def _sellar(papel, lectura, *, correo=CORREO, obras=OBRAS) -> tuple[dict, OrigenDatos]:
    final = sellar_origen_datos(
        _envelope(papel, lectura), lectura=lectura, correo=correo, obras_conocidas=obras,
    )
    return final, OrigenDatos.model_validate(final["data"]["origen_datos"])


def _obra_final(final: dict) -> str | None:
    return final["data"]["cabecera"]["obra_codigo"]


# ---------------------------------------------------------------- #
# Fila 1 — el correo no aporta obra: manda la IA con lo del papel.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("papel", ["1203", None], ids=["papel_1203", "papel_sin_codigo"])
def test_f048_r21_fila1_correo_sin_codigo_manda_la_ia(papel):
    final, origen = _sellar(papel, _lectura(evidencia=None))

    assert origen.obra.motivo == MOTIVO_CORREO_SIN_DATO
    assert origen.obra.fuente == FUENTE_PAPEL
    assert _obra_final(final) == papel
    assert origen.obra.valor_final == papel
    assert origen.obra.valor_papel == papel
    assert origen.obra.valor_correo is None
    assert origen.obra.candidatos_correo == []
    assert origen.obra.discrepancia is False
    assert origen.obra.validada is None
    assert origen.correo_presente is True


def test_f048_r17_fila1_sin_lectura_correo_es_ia_sin_lectura():
    """R17: la IA no devolvio el bloque; la extraccion sigue con el papel."""
    final, origen = _sellar("1203", None)

    assert origen.obra.motivo == MOTIVO_IA_SIN_LECTURA_CORREO
    assert origen.obra.fuente == FUENTE_PAPEL
    assert _obra_final(final) == "1203"
    assert origen.obra.valor_papel == "1203"
    assert origen.obra.candidatos_correo == []
    assert origen.obra.discrepancia is False
    assert origen.obra.validada is None
    assert origen.correo_presente is True
    assert origen.evidencia is None


@pytest.mark.parametrize("papel", ["1203", None], ids=["papel_1203", "papel_sin_codigo"])
def test_f048_r21_fila1_codigos_fuera_de_la_lista_manda_la_ia(papel):
    """Un pedido y un telefono no son obras: no cuentan, sin revision."""
    final, origen = _sellar(papel, _lectura("PED-123456", "600123123", evidencia="Pedido PED-123456"))

    assert origen.obra.motivo == MOTIVO_CORREO_FUERA_DE_LISTA
    assert origen.obra.fuente == FUENTE_PAPEL
    assert origen.obra.validada is False
    # Rastro para la medicion (§7): lo leido, tal y como lo leyo IA1.
    assert origen.obra.candidatos_correo == ["PED-123456", "600123123"]
    assert _obra_final(final) == papel
    assert origen.obra.valor_final == papel
    assert origen.obra.valor_correo is None
    assert origen.obra.discrepancia is False
    assert origen.evidencia == "Pedido PED-123456"


# ---------------------------------------------------------------- #
# Filas 2 y 3 — UN codigo de la lista: manda el correo.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("codigo", "papel"),
    [("0945", "0945"), ("0945", None), ("0320", None), ("0320", "0320")],
    ids=["igual", "papel_sin_codigo", "no_activa_sin_papel", "no_activa_igual"],
)
def test_f048_r19_fila2_un_codigo_de_la_lista_manda_el_correo(codigo, papel):
    final, origen = _sellar(papel, _lectura(codigo))

    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert origen.obra.fuente == FUENTE_CORREO
    assert origen.obra.validada is True
    assert _obra_final(final) == codigo
    assert origen.obra.valor_final == codigo
    assert origen.obra.valor_correo == codigo
    assert origen.obra.valor_papel == papel
    assert origen.obra.candidatos_correo == [codigo]
    assert origen.obra.discrepancia is False


@pytest.mark.parametrize(("codigo", "papel"), [("0945", "1203"), ("0320", "0945")])
def test_f048_r19_fila3_papel_distinto_manda_el_correo_con_discrepancia(codigo, papel):
    final, origen = _sellar(papel, _lectura(codigo))

    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert origen.obra.fuente == FUENTE_CORREO
    assert _obra_final(final) == codigo
    assert origen.obra.discrepancia is True
    assert origen.hay_discrepancia is True
    # Las DOS lecturas quedan (R19).
    assert origen.obra.valor_correo == codigo
    assert origen.obra.valor_papel == papel
    assert origen.obra.validada is True


def test_f048_r19_fila3_papel_que_no_es_obra_tambien_discrepa():
    """El papel trae un codigo (aunque no este en la lista): hay dos lecturas distintas."""
    final, origen = _sellar("7777", _lectura("0945"))

    assert _obra_final(final) == "0945"
    assert origen.obra.discrepancia is True
    assert origen.obra.valor_papel == "7777"


# ---------------------------------------------------------------- #
# Fila 4 — varios de la lista y el del papel es uno de ellos.
# ---------------------------------------------------------------- #
def test_f048_r20_fila4_varios_y_el_del_papel_es_uno_confirma_el_papel():
    final, origen = _sellar("1203", _lectura("0945", "1203"))

    assert origen.obra.motivo == MOTIVO_CORREO_CONFIRMA_PAPEL
    assert origen.obra.fuente == FUENTE_PAPEL
    assert _obra_final(final) == "1203"
    assert origen.obra.valor_final == "1203"
    assert origen.obra.valor_papel == "1203"
    assert origen.obra.candidatos_correo == ["0945", "1203"]
    assert origen.obra.discrepancia is False
    assert origen.obra.validada is True


# ---------------------------------------------------------------- #
# Fila 5 — varios de la lista y el papel no casa, o no trae codigo.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("papel", ["0320", "7777", None], ids=["otra_de_la_lista", "no_es_obra", "sin_codigo"])
def test_f048_r20_fila5_varios_sin_casar_es_ambiguo_y_no_impone_ninguno(papel):
    final, origen = _sellar(papel, _lectura("0945", "1203"))

    assert origen.obra.motivo == MOTIVO_CORREO_AMBIGUO
    assert origen.obra.fuente == FUENTE_PAPEL
    # El resolver NO cambia la cabecera (D4 bis).
    assert _obra_final(final) == papel
    assert origen.obra.valor_final == papel
    assert origen.obra.valor_correo is None
    assert origen.obra.candidatos_correo == ["0945", "1203"]
    # La revision la pone sv3 por el motivo, no por la discrepancia.
    assert origen.obra.discrepancia is False
    assert origen.obra.validada is True


# ---------------------------------------------------------------- #
# Sin lista de obras (sigrid-api caido o funcion apagada).
# ---------------------------------------------------------------- #
def test_f048_r18_sin_lista_cuentan_todos_con_validada_null():
    final, origen = _sellar("1203", _lectura("PED-123456"), obras=None)

    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert origen.obra.fuente == FUENTE_CORREO
    assert origen.obra.validada is None
    assert _obra_final(final) == "PED-123456"
    assert origen.obra.discrepancia is True


def test_f048_r18_sin_lista_varios_sigue_la_tabla():
    final, origen = _sellar(None, _lectura("0945", "1203"), obras=None)

    assert origen.obra.motivo == MOTIVO_CORREO_AMBIGUO
    assert origen.obra.validada is None
    assert origen.obra.candidatos_correo == ["0945", "1203"]
    assert _obra_final(final) is None


def test_f048_r18_lista_vacia_no_es_lo_mismo_que_sin_lista():
    """``{}`` es una lista que se consulto y no tiene obras: nada cuenta.

    ``obras_conocidas()`` devuelve ``None`` cuando no hay nada; si algun
    dia llegara un mapa vacio, el correo no puede mandar sin validar.
    """
    final, origen = _sellar("1203", _lectura("0945"), obras={})

    assert origen.obra.motivo == MOTIVO_CORREO_FUERA_DE_LISTA
    assert origen.obra.validada is False
    assert _obra_final(final) == "1203"


# ---------------------------------------------------------------- #
# Sin correo (R22) y lo comun a todas las filas.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("lectura", [None, _lectura("0945")], ids=["sin_lectura", "la_ia_invento_lectura"])
def test_f048_r22_sin_correo_el_data_es_el_de_hoy_salvo_origen_datos(lectura):
    entrada = _envelope("1203", lectura)
    esperado = copy.deepcopy(entrada["data"])
    del esperado["lectura_correo"]

    final = sellar_origen_datos(entrada, lectura=lectura, correo=None, obras_conocidas=OBRAS)
    origen = OrigenDatos.model_validate(final["data"].pop("origen_datos"))

    assert final["data"] == esperado
    assert final["meta"] == entrada["meta"]
    assert final["debug"] == entrada["debug"]
    assert origen.correo_presente is False
    assert origen.correo_sha256 is None
    assert origen.correo_truncado is False
    assert origen.evidencia is None
    assert origen.obra.fuente == FUENTE_PAPEL
    assert origen.obra.motivo == MOTIVO_SIN_CORREO
    assert origen.obra.valor_final == "1203"
    assert origen.obra.valor_papel == "1203"
    assert origen.obra.candidatos_correo == []
    assert origen.obra.discrepancia is False
    assert origen.obra.validada is None


def test_f048_r22_sin_correo_y_sin_cabecera_no_se_inventa_una():
    entrada = {"meta": {}, "data": {"lineas": []}, "debug": {}}

    final = sellar_origen_datos(entrada, lectura=None, correo=None, obras_conocidas=None)

    assert "cabecera" not in final["data"]
    assert final["data"]["origen_datos"]["obra"]["valor_papel"] is None


def test_f048_r24_con_correo_sella_la_huella_y_el_recorte_nunca_el_cuerpo():
    largo = construir_contexto_correo("Obra 0945", f"{CENTINELA} " + "x" * 50, max_caracteres=20)
    evidencia = f"Para la 0945 {'y' * 300}"

    final, origen = _sellar("0945", _lectura("0945", evidencia=evidencia), correo=largo)

    assert origen.correo_presente is True
    assert origen.correo_sha256 == largo.sha256
    assert origen.correo_truncado is True
    assert origen.evidencia == evidencia[:160]
    assert CENTINELA not in str(final["data"]["origen_datos"])
