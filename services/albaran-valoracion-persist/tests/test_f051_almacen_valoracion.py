# tests/test_f051_almacen_valoracion.py
"""F-051 · almacén por línea · la valoración (sv6) no inventa partida.

Decisión del humano (D1, PARADA 1 del 2026-10-05): una línea sin partida
«no se asocia a partida»: es ALMACÉN, que se representa con
``codigo_partida_final`` vacío (nunca un literal). sv6 deja rastro de por
qué con ``partida_action = "almacen_sin_partida"``.

Qué partida lleva cada línea lo decide IA1 leyendo el papel (prompt de
sv2); sv6 nunca copia la de la línea de contrato casada ni la de una
hermana (R1, R28). Cualquier familia puede ir a almacén; las familias
destinadas solo añaden una revisión NO bloqueante (R4, R5, D2).

Sin red, sin BBDD y sin LLM: política pura, ``PartidaMatcher`` y el
``ValuationBuilder`` real con sobres armados a mano.
"""
from __future__ import annotations

import pytest

# =================================================================== #
# Política pura (R4, R5, R9)
# =================================================================== #

DEFECTO_DESTINADAS = "hormigon,mortero,combustible,alquiler_maquinaria,residuos"


def test_f051_r9_csv_sin_distinguir_mayusculas_ni_espacios():
    from application.services.almacen_politica import (
        familias_destinadas_de_csv,
    )

    assert familias_destinadas_de_csv(" Hormigon , MORTERO ,residuos ") == (
        frozenset({"hormigon", "mortero", "residuos"})
    )


def test_f051_r9_csv_vacio_o_none_es_ninguna_destinada():
    from application.services.almacen_politica import (
        familias_destinadas_de_csv,
    )

    assert familias_destinadas_de_csv("") == frozenset()
    assert familias_destinadas_de_csv(None) == frozenset()
    assert familias_destinadas_de_csv("  ,  , ") == frozenset()


def test_f051_r9_csv_por_defecto_son_las_cinco_familias():
    from application.services.almacen_politica import (
        familias_destinadas_de_csv,
    )

    assert familias_destinadas_de_csv(DEFECTO_DESTINADAS) == frozenset(
        {"hormigon", "mortero", "combustible", "alquiler_maquinaria",
         "residuos"},
    )


def test_f051_r9_settings_por_defecto_y_desde_el_entorno(monkeypatch):
    """El valor por defecto es el de la spec; el entorno lo cambia."""
    from config.settings import Settings

    for var in ("FAMILIAS_DESTINADAS", "ALMACEN_SIN_PARTIDA_ENABLED"):
        monkeypatch.delenv(var, raising=False)
    defecto = Settings(PG_USER="u", PG_PASSWORD="p", _env_file=None)
    assert defecto.familias_destinadas == DEFECTO_DESTINADAS

    monkeypatch.setenv("FAMILIAS_DESTINADAS", "residuos")
    cambiado = Settings(PG_USER="u", PG_PASSWORD="p", _env_file=None)
    assert cambiado.familias_destinadas == "residuos"


@pytest.mark.parametrize(
    "familia",
    ["hormigon", "mortero", "combustible", "alquiler_maquinaria", "residuos"],
)
def test_f051_r4_familia_destinada_da_motivo_de_revision(familia):
    from application.services.almacen_politica import (
        MOTIVO_FAMILIA_DESTINADA,
        familias_destinadas_de_csv,
        motivo_revision_almacen,
    )

    destinadas = familias_destinadas_de_csv(DEFECTO_DESTINADAS)
    assert motivo_revision_almacen(familia, destinadas) == (
        MOTIVO_FAMILIA_DESTINADA
    )
    assert MOTIVO_FAMILIA_DESTINADA == "partida_ausente_familia_destinada"


def test_f051_r4_la_familia_se_compara_sin_mayusculas_ni_espacios():
    from application.services.almacen_politica import (
        MOTIVO_FAMILIA_DESTINADA,
        motivo_revision_almacen,
    )

    assert motivo_revision_almacen(
        " Hormigon ", frozenset({"hormigon"}),
    ) == MOTIVO_FAMILIA_DESTINADA


@pytest.mark.parametrize("familia", ["generico", "otro", None, ""])
def test_f051_r5_familia_no_destinada_o_sin_familia_no_da_motivo(familia):
    from application.services.almacen_politica import (
        familias_destinadas_de_csv,
        motivo_revision_almacen,
    )

    destinadas = familias_destinadas_de_csv(DEFECTO_DESTINADAS)
    assert motivo_revision_almacen(familia, destinadas) is None


def test_f051_r5_sin_destinadas_nunca_hay_motivo():
    from application.services.almacen_politica import motivo_revision_almacen

    assert motivo_revision_almacen("hormigon", frozenset()) is None


def test_f051_r1_constantes_de_la_politica():
    """Los literales que leen sv4, F-053 y F-049 no cambian de nombre."""
    from application.services.almacen_politica import (
        ACCION_ALMACEN_SIN_PARTIDA,
        MOTIVO_SIN_PARTIDA,
    )

    assert ACCION_ALMACEN_SIN_PARTIDA == "almacen_sin_partida"
    assert MOTIVO_SIN_PARTIDA == "almacen_sin_partida_en_albaran"


# =================================================================== #
# Apoyo: matcher, builder y sobres armados a mano
# =================================================================== #

CONTRATO = "CTSU25/0051"

#: Línea de contrato con partida: la que «inventaba» la partida (hoy, la
#: línea sin partida en el albarán recibía 03.02 por ``ia_match_trusted``).
CL_ARIDO_0302 = dict(
    contrato_line_id=5101,
    descripcion="ARIDO 20/40",
    unidad_medida="TN",
    precio_unitario=12.5,
    codigo_partida="03.02",
)
CL_ARIDO_0405 = dict(
    contrato_line_id=5102,
    descripcion="ARIDO 20/40",
    unidad_medida="TN",
    precio_unitario=12.5,
    codigo_partida="04.05",
)
CL_PORTE_0302 = dict(
    contrato_line_id=5103,
    descripcion="PORTE",
    unidad_medida="UD",
    precio_unitario=40.0,
    codigo_partida="03.02",
)


def _cl(datos):
    from domain.models.valuation_envelope import ContratoLineContextDto

    return ContratoLineContextDto(
        codigo_contrato=CONTRATO, codigo_producto="MA9999", **datos,
    )


def _linea_ia(merge_line_id, matched=None, precio=None, metodo="semantic"):
    from domain.models.valuation_envelope import LineValuationDto

    return LineValuationDto(
        merge_line_id=merge_line_id,
        line_kind="from_albaran",
        match_method=metodo if matched is not None else "no_match",
        matched_contrato_line_id=matched,
        match_confidence_pct=90.0 if matched is not None else 0.0,
        unidad_categoria_albaran="mass",
        unidad_category_match=True,
        precio_unitario_contrato_db=precio,
        descripcion_linea="ARIDO 20/40",
    )


def matcher(almacen_sin_partida: bool = True):
    from application.services.partida_matcher import PartidaMatcher

    if almacen_sin_partida:
        return PartidaMatcher(alm_codigo_partida="ALM", almacen_sin_partida=True)
    return PartidaMatcher(alm_codigo_partida="ALM")


def _match(m, *, partida, matched, contrato=(CL_ARIDO_0302,)):
    return m.match(
        line=_linea_ia(901, matched=matched, precio=12.5),
        codigo_partida_albaran=partida,
        precio_unitario_final=12.5,
        unidad_albaran="TN",
        contrato_lines=[_cl(c) for c in contrato],
        albaran_descripcion="ARIDO 20/40",
        albaran_codigo_producto=None,
    )


# =================================================================== #
# R1, R2 · matcher: sin partida ⇒ almacén, conservando el casado
# =================================================================== #

@pytest.mark.parametrize("partida", [None, "", "   "])
def test_f051_r1_sin_partida_va_a_almacen_y_no_copia_la_del_contrato(partida):
    resultado = _match(matcher(), partida=partida, matched=5101)

    assert resultado.partida_action == "almacen_sin_partida"
    assert resultado.codigo_partida_final is None
    assert resultado.reasons == ["almacen_sin_partida_en_albaran"]
    assert resultado.derived_line is None


def test_f051_r2_conserva_el_id_de_la_linea_que_caso_la_ia():
    resultado = _match(matcher(), partida=None, matched=5101)

    assert resultado.matched_contrato_line_id == 5101


def test_f051_r2_id_de_la_ia_fuera_del_contrato_no_se_conserva():
    """Diseño: el id se conserva SOLO si está entre las líneas del sobre."""
    resultado = _match(matcher(), partida=None, matched=9999)

    assert resultado.partida_action == "almacen_sin_partida"
    assert resultado.matched_contrato_line_id is None


def test_f051_r1_sin_partida_y_sin_match_de_la_ia_tambien_es_almacen():
    resultado = _match(matcher(), partida=None, matched=None)

    assert resultado.partida_action == "almacen_sin_partida"
    assert resultado.matched_contrato_line_id is None
    assert resultado.codigo_partida_final is None
    assert resultado.derived_line is None


# =================================================================== #
# R6 · con partida impresa (y con «ALM») el matcher no cambia
# =================================================================== #

@pytest.mark.parametrize(
    ("partida", "matched", "contrato"),
    [
        # La IA casó en la partida del albarán.
        ("03.02", 5101, (CL_ARIDO_0302,)),
        # La IA casó en otra partida: se re-apunta por descripción.
        ("04.05", 5101, (CL_ARIDO_0302, CL_ARIDO_0405)),
        # La IA casó en otra partida y no hay réplica: derivada.
        ("09.99", 5101, (CL_ARIDO_0302,)),
        # Sin match de la IA pero con partida: derivada.
        ("03.02", None, (CL_ARIDO_0302,)),
        # «ALM» impreso: derivada de acopio.
        ("ALM", 5101, (CL_ARIDO_0302,)),
        (" alm ", None, (CL_ARIDO_0302,)),
    ],
)
def test_f051_r6_con_partida_impresa_el_resultado_es_el_de_siempre(
    partida, matched, contrato,
):
    nuevo = _match(matcher(True), partida=partida, matched=matched,
                   contrato=contrato)
    antes = _match(matcher(False), partida=partida, matched=matched,
                   contrato=contrato)

    assert nuevo == antes
    assert nuevo.partida_action != "almacen_sin_partida"


def test_f051_r6_alm_impreso_sigue_creando_la_derivada_de_acopio():
    resultado = _match(matcher(), partida="ALM", matched=5101)

    assert resultado.partida_action == "alm_new_line_created"
    assert resultado.derived_line is not None
    assert resultado.derived_line.origen == "alm_acopio"
    assert resultado.codigo_partida_final is None


# =================================================================== #
# R8 · interruptor apagado = exactamente como antes de F-051
# =================================================================== #

def test_f051_r8_apagado_copia_la_partida_de_la_linea_casada_como_hoy():
    resultado = _match(matcher(False), partida=None, matched=5101)

    assert resultado.partida_action == "existing_matched"
    assert resultado.codigo_partida_final == "03.02"
    assert resultado.reasons == ["ia_match_trusted"]


def test_f051_r8_apagado_sin_match_ni_partida_es_no_action_como_hoy():
    resultado = _match(matcher(False), partida=None, matched=None)

    assert resultado.partida_action == "no_action"


def test_f051_r8_el_matcher_viene_apagado_por_defecto():
    """Los tests y llamadas existentes no cambian (diseño, sv6)."""
    from application.services.partida_matcher import PartidaMatcher

    resultado = _match(
        PartidaMatcher(alm_codigo_partida="ALM"), partida=None, matched=5101,
    )
    assert resultado.partida_action == "existing_matched"


def test_f051_r8_interruptor_encendido_por_defecto_y_apagable(monkeypatch):
    from config.settings import Settings

    monkeypatch.delenv("ALMACEN_SIN_PARTIDA_ENABLED", raising=False)
    assert Settings(
        PG_USER="u", PG_PASSWORD="p", _env_file=None,
    ).almacen_sin_partida_enabled is True

    monkeypatch.setenv("ALMACEN_SIN_PARTIDA_ENABLED", "false")
    assert Settings(
        PG_USER="u", PG_PASSWORD="p", _env_file=None,
    ).almacen_sin_partida_enabled is False


def test_f051_r8_partida_action_admite_la_marca_nueva():
    from typing import get_args

    from domain.models.valuation_records import PartidaAction

    assert "almacen_sin_partida" in get_args(PartidaAction)
