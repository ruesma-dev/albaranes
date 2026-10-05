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
