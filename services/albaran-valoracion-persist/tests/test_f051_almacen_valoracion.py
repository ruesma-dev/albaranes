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


# =================================================================== #
# Apoyo del builder: el ValuationBuilder real con el matcher encendido
# =================================================================== #

def builder(*, almacen_sin_partida: bool = True, destinadas=None):
    """El cableado de ``composition.py`` con los ajustes de F-051.

    ``destinadas=None`` no pasa el parámetro nuevo del builder: es como
    se construye hoy (y como lo construyen los tests de otras features).
    """
    from pathlib import Path

    from application.services.importe_calculator import ImporteCalculator
    from application.services.price_reconciler import PriceReconciler
    from application.services.unit_category_guard import UnitCategoryGuard
    from application.services.unit_converter import UnitConverter
    from application.services.valuation_builder import ValuationBuilder
    from infrastructure.units.yaml_unit_registry import YamlUnitRegistry
    from tests.conftest import TOLERANCIA_IMPORTE_PCT, TOLERANCIA_PRECIO_PCT

    registro = YamlUnitRegistry(str(
        Path(__file__).resolve().parents[1] / "config" / "unit_registry.yaml"
    ))
    extra = {} if destinadas is None else {"familias_destinadas": destinadas}
    return ValuationBuilder(
        unit_category_guard=UnitCategoryGuard(unit_registry=registro),
        price_reconciler=PriceReconciler(tolerance_pct=TOLERANCIA_PRECIO_PCT),
        partida_matcher=matcher(almacen_sin_partida),
        unit_converter=UnitConverter(registry=registro),
        importe_calculator=ImporteCalculator(
            tolerance_pct=TOLERANCIA_IMPORTE_PCT,
        ),
        **extra,
    )


def linea(
    merge_line_id,
    *,
    partida=None,
    matched=5101,
    precio=12.5,
    familia=None,
    rol=None,
    ref_linea_base=None,
    descripcion="ARIDO 20/40",
    unidad="TN",
):
    """Una línea del albarán: (línea IA, contexto) para el sobre.

    ``line_index`` = ``merge_line_id - 701``: la 701 es la línea 0.
    """
    from domain.models.contexto_linea import ContextoLinea
    from domain.models.valuation_envelope import AlbaranLineContextDto

    ctx = None
    if familia is not None or rol is not None or ref_linea_base is not None:
        ctx = ContextoLinea(
            tipo_familia=familia, rol_linea=rol, ref_linea_base=ref_linea_base,
        )
    contexto = AlbaranLineContextDto(
        merge_line_id=merge_line_id,
        line_index=merge_line_id - 701,
        descripcion=descripcion,
        unidad_medida=unidad,
        unidad_categoria="mass" if unidad == "TN" else "count",
        cantidad=2.0,
        codigo_partida_albaran=partida,
        contexto_linea=ctx,
    )
    ia = _linea_ia(merge_line_id, matched=matched, precio=precio)
    if unidad != "TN":
        ia.unidad_categoria_albaran = "count"
    return ia, contexto


def sintetica(parent_merge_line_id, *, precio=3.0):
    from domain.models.valuation_envelope import LineValuationDto

    return LineValuationDto(
        merge_line_id=None,
        line_kind="synthetic_modifier",
        parent_merge_line_id=parent_merge_line_id,
        modifier_source="recargo_test",
        modifier_reason="recargo de prueba",
        descripcion_linea="RECARGO",
        match_method="no_match",
        precio_unitario_pdf_inferido=precio,
    )


def valorar(lineas, *, contrato=(CL_ARIDO_0302, CL_PORTE_0302),
            sinteticas=(), clasificacion=None, **opciones):
    from domain.models.valuation_envelope import (
        DocumentoValoracionDto,
        ValuationContextDto,
        ValuationEnvelope,
        ValuationEnvelopeMeta,
    )

    sobre = ValuationEnvelope(
        status="ok",
        meta=ValuationEnvelopeMeta(
            document_id="doc-f051", codigo_contrato=CONTRATO,
            numero_albaran="F051",
        ),
        data=DocumentoValoracionDto(
            lineas=[ia for ia, _ in lineas] + list(sinteticas),
        ),
        context=ValuationContextDto(
            lineas_albaran=[ctx for _, ctx in lineas],
            lineas_contrato=[_cl(c) for c in contrato],
            clasificacion=clasificacion,
        ),
    )
    _cabecera, registros = builder(**opciones).build(
        envelope=sobre, existing_document_already_valued=False,
    )
    return registros


def _por_merge(registros, merge_line_id):
    return next(r for r in registros if r.merge_line_id == merge_line_id)


def _clasificacion(familia):
    from ruesma_comun.contratos import ClasificacionAlbaran

    return ClasificacionAlbaran(
        familia=familia, confianza_pct=90.0, motivo="leído por IA1",
    )


DESTINADAS = frozenset(
    {"hormigon", "mortero", "combustible", "alquiler_maquinaria", "residuos"},
)


# =================================================================== #
# R1, R2 · en el builder: almacén sin tocar la valoración
# =================================================================== #

def test_f051_r1_builder_linea_sin_partida_queda_en_almacen():
    registro = valorar([linea(701)])[0]

    assert registro.codigo_partida_final is None
    assert registro.partida_action == "almacen_sin_partida"
    assert "almacen_sin_partida_en_albaran" in registro.review_reasons


def test_f051_r2_builder_conserva_casado_precio_e_importe():
    nuevo = valorar([linea(701)])[0]
    antes = valorar([linea(701)], almacen_sin_partida=False)[0]

    assert antes.codigo_partida_final == "03.02"  # hoy: la del contrato
    assert nuevo.matched_contrato_line_id == 5101
    assert nuevo.derived_contrato_line_record is None
    assert nuevo.precio_unitario_final == antes.precio_unitario_final == 12.5
    assert nuevo.importe_calculado == antes.importe_calculado
    assert nuevo.review_required is antes.review_required is False


# =================================================================== #
# R3 · sin match de la IA: derivada de respaldo, marca conservada
# =================================================================== #

def test_f051_r3_sin_match_crea_nueva_no_match_y_conserva_la_marca():
    registro = valorar([linea(701, matched=None, precio=None)])[0]

    assert registro.partida_action == "almacen_sin_partida"
    assert registro.codigo_partida_final is None
    assert registro.matched_contrato_line_id is None
    derivada = registro.derived_contrato_line_record
    assert derivada is not None
    assert derivada.origen == "nueva_no_match"
    assert derivada.codigo_partida is None


# =================================================================== #
# R4, R5 · revisión NO bloqueante solo en familias destinadas
# =================================================================== #

@pytest.mark.parametrize("familia", ["mortero", "combustible"])
def test_f051_r4_familia_destinada_en_la_linea_va_a_revision(familia):
    registro = valorar(
        [linea(701, familia=familia)], destinadas=DESTINADAS,
    )[0]

    assert registro.review_required is True
    assert "partida_ausente_familia_destinada" in registro.review_reasons
    # Sigue en almacén: la revisión no rellena partida (D2).
    assert registro.codigo_partida_final is None
    assert registro.partida_action == "almacen_sin_partida"


def test_f051_r4_familia_destinada_heredada_del_documento():
    """La familia es la EFECTIVA: la del documento si la línea no trae."""
    registro = valorar(
        [linea(701)], destinadas=DESTINADAS,
        clasificacion=_clasificacion("combustible"),
    )[0]

    assert registro.review_required is True
    assert "partida_ausente_familia_destinada" in registro.review_reasons


def test_f051_r4_con_partida_impresa_no_hay_motivo_aunque_sea_destinada():
    registro = valorar(
        [linea(701, partida="03.02", familia="mortero")],
        destinadas=DESTINADAS,
    )[0]

    assert "partida_ausente_familia_destinada" not in registro.review_reasons
    assert registro.codigo_partida_final == "03.02"


def test_f051_r4_interruptor_apagado_no_marca_revision_por_familia():
    registro = valorar(
        [linea(701, familia="mortero")], destinadas=DESTINADAS,
        almacen_sin_partida=False,
    )[0]

    assert "partida_ausente_familia_destinada" not in registro.review_reasons
    assert registro.partida_action == "existing_matched"


@pytest.mark.parametrize("familia", ["generico", "otro", None])
def test_f051_r5_familia_no_destinada_no_va_a_revision(familia):
    registro = valorar(
        [linea(701, familia=familia)], destinadas=DESTINADAS,
    )[0]

    assert registro.review_required is False
    assert "partida_ausente_familia_destinada" not in registro.review_reasons
    assert registro.codigo_partida_final is None


def test_f051_r5_sin_parametro_el_builder_no_marca_ninguna_familia():
    """Construido como hoy (sin ``familias_destinadas``): ninguna."""
    registro = valorar([linea(701, familia="mortero")])[0]

    assert "partida_ausente_familia_destinada" not in registro.review_reasons


# =================================================================== #
# R7 · complementarias y sintéticas siguen heredando de su base
# =================================================================== #

def _porte(merge_line_id=702):
    return linea(
        merge_line_id, matched=5103, rol="transporte", ref_linea_base=0,
        descripcion="PORTE", unidad="UD", precio=40.0,
    )


def test_f051_r7_complementaria_de_base_en_almacen_hereda_null():
    registros = valorar([linea(701), _porte()])
    porte = _por_merge(registros, 702)

    assert _por_merge(registros, 701).partida_action == "almacen_sin_partida"
    assert porte.partida_action == "inherited_from_base_line"
    assert porte.codigo_partida_final is None


def test_f051_r7_complementaria_sin_partida_hereda_la_de_su_base():
    """Excepción (c) del humano: el porte sin marca sigue a su base."""
    registros = valorar([linea(701, partida="03.02"), _porte()])
    porte = _por_merge(registros, 702)

    assert porte.partida_action == "inherited_from_base_line"
    assert porte.codigo_partida_final == "03.02"


def test_f051_r7_sintetica_de_base_en_almacen_hereda_null():
    registros = valorar([linea(701)], sinteticas=[sintetica(701)])
    sint = next(r for r in registros if r.line_kind == "synthetic_modifier")

    assert sint.partida_action == "inherited_from_base_line"
    assert sint.codigo_partida_final is None


def test_f051_r7_sintetica_de_base_con_partida_hereda_la_partida():
    registros = valorar(
        [linea(701, partida="03.02")], sinteticas=[sintetica(701)],
    )
    sint = next(r for r in registros if r.line_kind == "synthetic_modifier")

    assert sint.codigo_partida_final == "03.02"


# =================================================================== #
# R28 · una hermana con partida no se la pasa a la que no la trae
# =================================================================== #

def test_f051_r28_hermana_con_partida_no_se_copia():
    registros = valorar(
        [
            linea(701, partida="03.02"),
            linea(702),
            linea(703, partida="04.05", matched=5102),
        ],
        contrato=(CL_ARIDO_0302, CL_ARIDO_0405, CL_PORTE_0302),
    )

    assert _por_merge(registros, 701).codigo_partida_final == "03.02"
    sin = _por_merge(registros, 702)
    assert sin.codigo_partida_final is None
    assert sin.partida_action == "almacen_sin_partida"
    assert _por_merge(registros, 703).codigo_partida_final == "04.05"


# =================================================================== #
# R8, R9 · cableado: los dos puntos de entrada leen los dos ajustes
# =================================================================== #

@pytest.mark.parametrize(
    "fichero",
    ["interface_adapters/composition.py", "interface_adapters/api/app.py"],
)
def test_f051_r8_r9_worker_y_api_cablean_los_ajustes(fichero):
    """El worker (q-valoracion) y la API HTTP construyen el builder igual.

    Se lee el fuente como texto porque construirlos exige BBDD (y la API,
    FastAPI); lo que se protege es que ninguno se quede sin el ajuste.
    """
    from pathlib import Path

    fuente = (Path(__file__).resolve().parents[1] / fichero).read_text(
        encoding="utf-8",
    )
    assert "almacen_sin_partida=settings.almacen_sin_partida_enabled" in fuente
    assert "familias_destinadas_de_csv(\n            settings.familias_destinadas" in fuente
