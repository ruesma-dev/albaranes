# tests/test_f048_r18_normalizacion.py
"""F-048 · R18 y D9 en el resolver: normalizar y filtrar ANTES de contar.

- Todo codigo (correo, papel y lista) se compara con ``normalizar_codigo``:
  ``945``, ``09-45``, ``09.45`` y ``0945`` son el mismo (D9, «si, normaliza
  todo»). Al fijar la obra, la cabecera se escribe COMO FIGURA EN LA LISTA
  (``0945``), para que la red de obra de sv3 la encuentre (R28); sin lista,
  como la leyo IA1.
- Lo que no esta en la lista se descarta ANTES de contar (D5 revisada, que
  revoca la duda 5 de la v3): tres codigos leidos de los que solo uno es
  obra son un ``correo_unico``.
- Dos formas del mismo codigo cuentan como uno; un codigo que normaliza a
  vacio no cuenta.
- Colisiones de la lista (menor 2 de la review del bloque C1, fila 1 de D5):
  dos obras distintas que normalizan igual salen del mapa de
  ``obras_conocidas()``, asi que un codigo del correo que case con esa clave
  NO cuenta.

Sin red, sin BBDD y sin LLM.
"""
from __future__ import annotations

import logging

import pytest
from application.services.albaran_extraction_service import AlbaranExtractionService
from application.services.origen_datos_resolver import sellar_origen_datos
from application.services.schema_registry import SchemaRegistry
from domain.ports.obras_activas_provider import ObraActiva
from ruesma_comun.contratos.origen_datos import (
    FUENTE_CORREO,
    FUENTE_PAPEL,
    MOTIVO_CORREO_AMBIGUO,
    MOTIVO_CORREO_CONFIRMA_PAPEL,
    MOTIVO_CORREO_FUERA_DE_LISTA,
    MOTIVO_CORREO_SIN_DATO,
    MOTIVO_CORREO_UNICO,
    OrigenDatos,
)
from ruesma_comun.correo import construir_contexto_correo

OBRAS = {"945": "0945", "1203": "1203", "A12": "A-12"}
CORREO = construir_contexto_correo("Albaranes", "Os paso los albaranes. CENTINELA-F048")


def _sellar(papel, *codigos, obras=OBRAS) -> tuple[str | None, OrigenDatos]:
    lectura = {"obra_codigos": list(codigos), "evidencia": "obra"}
    envelope = {"data": {"cabecera": {"obra_codigo": papel}, "lineas": [], "lectura_correo": lectura}}
    final = sellar_origen_datos(envelope, lectura=lectura, correo=CORREO, obras_conocidas=obras)
    return final["data"]["cabecera"]["obra_codigo"], OrigenDatos.model_validate(final["data"]["origen_datos"])


# ---------------------------------------------------------------- #
# Formas del mismo codigo: casan con la lista y se escriben como en ella.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize("leido", ["945", "09-45", "09.45", " 0945 ", "０９４５", "0945"])
def test_f048_r18_el_codigo_del_correo_casa_normalizado_y_se_escribe_como_en_la_lista(leido):
    obra, origen = _sellar(None, leido)

    assert obra == "0945"
    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert origen.obra.valor_final == "0945"
    assert origen.obra.valor_correo == "0945"
    assert origen.obra.candidatos_correo == ["0945"]
    assert origen.obra.validada is True


def test_f048_r18_un_codigo_con_letras_casa_con_su_forma_de_la_lista():
    obra, origen = _sellar(None, "a12")

    assert obra == "A-12"
    assert origen.obra.validada is True


def test_f048_r18_sin_lista_se_escribe_como_lo_leyo_ia1():
    obra, origen = _sellar(None, "945", obras=None)

    assert obra == "945"
    assert origen.obra.valor_correo == "945"
    assert origen.obra.validada is None


@pytest.mark.parametrize(
    ("papel", "correo"),
    [("0945", "945"), ("945", "0945"), ("09-45", "0945"), ("09.45", "945")],
)
def test_f048_r18_papel_y_correo_con_distinta_forma_no_son_discrepancia(papel, correo):
    obra, origen = _sellar(papel, correo)

    assert origen.obra.discrepancia is False
    assert origen.obra.valor_papel == papel
    # Manda el correo, escrito como en la lista.
    assert obra == "0945"
    assert origen.obra.fuente == FUENTE_CORREO


def test_f048_r18_sin_lista_tampoco_hay_discrepancia_por_la_forma():
    obra, origen = _sellar("0945", "945", obras=None)

    assert origen.obra.discrepancia is False
    assert obra == "945"


def test_f048_r18_papel_que_normaliza_a_vacio_es_papel_sin_codigo():
    obra, origen = _sellar("000", "0945")

    assert origen.obra.discrepancia is False
    assert obra == "0945"


# ---------------------------------------------------------------- #
# Se descarta ANTES de contar.
# ---------------------------------------------------------------- #
def test_f048_r18_varios_leidos_y_solo_uno_en_la_lista_es_correo_unico():
    obra, origen = _sellar("1203", "PED-555", "945", "600123123")

    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert obra == "0945"
    # Los descartados cuando otro cuenta no se guardan aparte (D5).
    assert origen.obra.candidatos_correo == ["0945"]
    assert origen.obra.discrepancia is True
    assert origen.obra.valor_papel == "1203"


def test_f048_r18_ninguno_en_la_lista_es_fila_1_aunque_sean_varios():
    obra, origen = _sellar("1203", "PED-555", "600123123", "28001")

    assert origen.obra.motivo == MOTIVO_CORREO_FUERA_DE_LISTA
    assert origen.obra.fuente == FUENTE_PAPEL
    assert origen.obra.validada is False
    assert origen.obra.candidatos_correo == ["PED-555", "600123123", "28001"]
    assert obra == "1203"
    assert origen.obra.discrepancia is False


def test_f048_r18_dos_formas_del_mismo_codigo_cuentan_como_uno():
    obra, origen = _sellar("1203", "0945", "945", "09-45")

    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert origen.obra.candidatos_correo == ["0945"]
    assert obra == "0945"


def test_f048_r18_dos_formas_de_un_codigo_y_el_del_papel_confirman_el_papel():
    """945 y 0945 son uno; con 1203 son dos, y el papel dice 1203."""
    obra, origen = _sellar("1203", "945", "0945", "1203")

    assert origen.obra.motivo == MOTIVO_CORREO_CONFIRMA_PAPEL
    assert origen.obra.candidatos_correo == ["0945", "1203"]
    assert obra == "1203"


def test_f048_r18_el_papel_casa_normalizado_entre_varios():
    obra, origen = _sellar("12-03", "0945", "1203")

    assert origen.obra.motivo == MOTIVO_CORREO_CONFIRMA_PAPEL
    # Varios: la cabecera no se toca, ni siquiera para darle la forma de la lista.
    assert obra == "12-03"


def test_f048_r18_varios_sin_lista_se_deduplican_por_la_forma():
    obra, origen = _sellar(None, "945", "0945", obras=None)

    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert origen.obra.candidatos_correo == ["945"]
    assert obra == "945"


@pytest.mark.parametrize("vacios", [("000",), ("--", " "), ("",)], ids=["ceros", "signos", "cadena_vacia"])
def test_f048_r18_un_codigo_que_normaliza_a_vacio_no_cuenta(vacios):
    obra, origen = _sellar("1203", *vacios)

    assert origen.obra.motivo == MOTIVO_CORREO_SIN_DATO
    assert origen.obra.candidatos_correo == []
    assert obra == "1203"


def test_f048_r18_un_vacio_junto_a_un_codigo_bueno_no_hace_varios():
    obra, origen = _sellar(None, "000", "945")

    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert obra == "0945"


def test_f048_r18_un_null_en_la_lista_de_la_ia_se_ignora():
    obra, origen = _sellar(None, None, "945")

    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert obra == "0945"


# ---------------------------------------------------------------- #
# Colisiones de la lista (fila 1 de D5), con el mapa REAL del servicio.
# ---------------------------------------------------------------- #
class _Proveedor:
    def __init__(self, *codigos: str) -> None:
        self._todas = [ObraActiva(codigo=c, nombre=f"OBRA {c}") for c in codigos]

    def obtener(self):
        return None

    def obtener_todas(self):
        return self._todas


def _obras_conocidas(*codigos: str) -> dict[str, str] | None:
    class _Reglas:
        count = 0
        rule_ids: tuple[str, ...] = ()

        def render_for_prompt(self) -> str:
            return ""

    return AlbaranExtractionService(
        providers=[], prompt_repo=None, schema_registry=SchemaRegistry(),
        revision_rules_repo=_Reglas(), prompt_key_phase_1="albaran_factura_es",
        obras_activas_provider=_Proveedor(*codigos),
    ).obras_conocidas()


@pytest.mark.parametrize("leido", ["9451", "0945-1", "945.1"])
def test_f048_r18_un_codigo_que_casa_con_una_colision_no_cuenta(leido, caplog):
    with caplog.at_level(logging.WARNING):
        obras = _obras_conocidas("0945-1", "9451", "1203")

    obra, origen = _sellar("1203", leido, obras=obras)

    assert origen.obra.motivo == MOTIVO_CORREO_FUERA_DE_LISTA
    assert origen.obra.validada is False
    assert origen.obra.candidatos_correo == [leido]
    assert obra == "1203"
    assert origen.obra.discrepancia is False
    assert any("ambiguos" in r.getMessage() for r in caplog.records)


def test_f048_r18_una_colision_no_convierte_en_varios_a_un_codigo_bueno():
    obras = _obras_conocidas("0945-1", "9451", "1203")

    assert obras is not None
    obra, origen = _sellar(None, "9451", "1203", obras=obras)
    assert origen.obra.motivo == MOTIVO_CORREO_UNICO
    assert obra == "1203"


def test_f048_r18_sin_colision_varios_de_la_lista_siguen_siendo_ambiguos():
    """Control: con la misma lista sin colision, 9451 SI cuenta."""
    obras = _obras_conocidas("9451", "1203")

    obra, origen = _sellar(None, "9451", "1203", obras=obras)

    assert origen.obra.motivo == MOTIVO_CORREO_AMBIGUO
    assert obra is None
