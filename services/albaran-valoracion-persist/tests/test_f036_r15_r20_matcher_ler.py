# tests/test_f036_r15_r20_matcher_ler.py
"""F-036 · la linea BASE no puede valorarse con la tarifa del INCREMENTO.

R15 — guarda anti-incremento (medido en SS-0003967)
---------------------------------------------------
Cuando el contexto de linea se pierde (D2), sv5 valora el albaran de
residuos con el prompt generico `valuation_es`, que no sabe nada de
contenedores. Ahi la linea de contrato "INCREMENTO LER 170604 ..."
contiene el LER LITERAL que la IA ve en la linea del albaran, asi que
gana por similitud textual (`exact_concept`) a la linea de contenedor,
que solo casa por significado. Resultado medido en la BBDD el
2026-08-22: `precio_unitario_final = 90` (el del INCREMENTO) e importe
540 EUR en un albaran de 210.

Aguas abajo no lo corrige nadie: `partida_matcher` RESPETA el match de
la IA ("ia_match_trusted"). La guarda de R15 vive en el builder: una
linea `from_albaran` de residuos casada con un incremento por LER
pierde el match, va a revision y deja constancia.

R20 — el predicado por LER del ModifierContractMatcher
-------------------------------------------------------
El predicado del rol `incremento_residuos` era `"RESIDUOS" in d`: con
dos incrementos LER distintos en el contrato casaba el primero que
pasara. Si la sintetica nombra un LER, se exige ESE codigo; si no lo
nombra (el "INCREMENTO POR GESTION DE RESIDUOS EN HORMIGON"), se
mantiene el predicado de siempre.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest
from domain.models.valuation_envelope import LineValuationDto
from tests.f036_escenarios_residuos import (
    CONTENEDOR_6,
    INCREMENTO_170802,
    INCREMENTO_170904,
    EscenarioResiduos,
    LineaResiduos,
    base_de,
    valorar,
)

# =================================================================== #
# T15 · R15 — la base casada con un incremento pierde el match
# =================================================================== #

def _escenario_base_casada_con_incremento() -> EscenarioResiduos:
    """Lo que produce D2: IA3 casa la base con el INCREMENTO LER."""
    return EscenarioResiduos(
        lineas=(
            LineaResiduos(
                matched_contrato_line_id=INCREMENTO_170802.contrato_line_id,
                precio_contrato_db=INCREMENTO_170802.precio_unitario,
                match_method="exact_concept",
            ),
        ),
    )


def test_f036_r15_la_base_de_residuos_pierde_el_match_con_el_incremento():
    """El match se ANULA: un incremento no es lo que se factura."""
    _, registros = valorar(_escenario_base_casada_con_incremento())
    base = base_de(registros)

    assert base.matched_contrato_line_id is None


def test_f036_r15_la_base_desmatchada_va_a_revision_con_su_razon():
    """La anulacion es visible para el revisor (R23 la pinta en sv4)."""
    _, registros = valorar(_escenario_base_casada_con_incremento())
    base = base_de(registros)

    assert base.review_required is True
    assert "residuos_base_casada_con_incremento" in base.review_reasons


def test_f036_r15_la_base_desmatchada_no_se_queda_con_el_precio_del_incremento():
    """Anular el match es anularlo entero, precio incluido.

    Es el mismo criterio que el guard determinista de ANO
    (`_sanear_matches_incremento_year`): id a null, precio a null,
    match_method a `no_match`. Si el precio del incremento sobrevive,
    la linea sigue valorada a 51 EUR/contenedor y la guarda no habria
    servido de nada.
    """
    _, registros = valorar(_escenario_base_casada_con_incremento())
    base = base_de(registros)

    assert base.precio_unitario_contrato_db is None
    assert base.precio_unitario_final != pytest.approx(
        INCREMENTO_170802.precio_unitario
    )


def test_f036_r15_el_contenedor_bien_casado_no_se_toca():
    """La guarda es quirurgica: la linea correcta sigue valorada.

    1 contenedor x 120 EUR. Si esta prueba cae, la guarda esta
    desmatchando lineas buenas.
    """
    _, registros = valorar(EscenarioResiduos())
    base = base_de(registros)

    assert base.matched_contrato_line_id == CONTENEDOR_6.contrato_line_id
    assert "residuos_base_casada_con_incremento" not in base.review_reasons
    assert base.cantidad_convertida == pytest.approx(1.0)
    assert base.importe_calculado == pytest.approx(120.0)


def test_f036_r15_una_linea_que_no_es_de_residuos_no_la_toca_la_guarda():
    """La guarda solo mira lineas `tipo_familia='residuos'`.

    El "INCREMENTO POR GESTION DE RESIDUOS EN HORMIGON" del contrato de
    una hormigonera NO es un incremento por LER, y ademas la familia es
    otra: nada que anular.
    """
    escenario = EscenarioResiduos(
        lineas=(
            LineaResiduos(
                tipo_familia="hormigon",
                codigo_ler=None,
                volumen_m3=None,
                cantidad=8.0,
                unidad="M3",
                matched_contrato_line_id=CONTENEDOR_6.contrato_line_id,
                precio_contrato_db=120.0,
            ),
        ),
    )
    _, registros = valorar(escenario)
    base = base_de(registros)

    assert base.matched_contrato_line_id == CONTENEDOR_6.contrato_line_id
    assert "residuos_base_casada_con_incremento" not in base.review_reasons


# =================================================================== #
# T19 · R20 — el predicado por codigo LER
# =================================================================== #

def _matcher():
    from application.services.modifier_contract_matcher import (
        ModifierContractMatcher,
    )

    return ModifierContractMatcher(enabled=True)


def _sintetica(descripcion: str, rol: str = "incremento_residuos"):
    return LineValuationDto(
        merge_line_id=None,
        line_kind="synthetic_modifier",
        parent_merge_line_id=700,
        modifier_source="gestion_residuos",
        descripcion_linea=descripcion,
        rol_linea=rol,
        match_method="no_match",
    )


def test_f036_r20_el_predicado_elige_el_incremento_del_ler_correcto():
    """Dos incrementos LER en el contrato: casa el que nombra la sintetica."""
    resultado = _matcher().match(
        synthetic_line=_sintetica("INCREMENTO LER 170904"),
        base_partida=INCREMENTO_170904.codigo_partida,
        contrato_lines=[CONTENEDOR_6, INCREMENTO_170802, INCREMENTO_170904],
    )

    assert resultado.matched_line is not None
    assert (
        resultado.matched_line.contrato_line_id
        == INCREMENTO_170904.contrato_line_id
    )


def test_f036_r20_el_predicado_no_casa_un_ler_que_el_contrato_no_tarifa():
    """Sin la linea de ESE LER no hay match (mejor null que el de al lado)."""
    resultado = _matcher().match(
        synthetic_line=_sintetica("INCREMENTO LER 170504"),
        base_partida=INCREMENTO_170802.codigo_partida,
        contrato_lines=[CONTENEDOR_6, INCREMENTO_170802, INCREMENTO_170904],
    )

    assert resultado.matched_line is None


def test_f036_r20_el_incremento_de_residuos_del_hormigon_sigue_casando():
    """Sin LER en la descripcion se mantiene el predicado `RESIDUOS`.

    Es el caso de la M-de-residuos del hormigon (contrato CTSU24/0476:
    "INCREMENTO POR GESTION DE RESIDUOS EN HORMIGON"), que no va por
    LER y no puede perder su match por culpa de F-036.
    """
    incremento_hormigon = INCREMENTO_170802.model_copy(
        update={
            "contrato_line_id": 9100,
            "descripcion": "INCREMENTO POR GESTION DE RESIDUOS EN HORMIGON",
            "precio_unitario": 0.75,
        }
    )
    resultado = _matcher().match(
        synthetic_line=_sintetica("INCREMENTO POR GESTION DE RESIDUOS"),
        base_partida=incremento_hormigon.codigo_partida,
        contrato_lines=[incremento_hormigon],
    )

    assert resultado.matched_line is not None
    assert resultado.matched_line.contrato_line_id == 9100
