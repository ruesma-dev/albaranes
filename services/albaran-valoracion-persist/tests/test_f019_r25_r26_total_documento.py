# tests/test_f019_r25_r26_total_documento.py
"""F-019 · R25-R26: el TOTAL del DOCUMENTO, no la linea suelta.

Por que existe este fichero (round trip 2, 2026-08-18)
------------------------------------------------------
La feature se cerro con 57 tests en verde y aun asi la prueba local del
humano midio ``albaran_valuations.total_valorado = 232,76 EUR`` en el
albaran 2.137.569, que vale 139,66 EUR. El agujero era de forma, no de
fondo: **ningun test comprobaba el agregado**. Todos los de R16/R18
encadenaban ``PriceReconciler`` + ``ImporteCalculator`` a mano, linea a
linea, y ninguno hacia pasar el documento entero por
``ValuationBuilder.build`` para mirar el numero que acaba en la columna.

Aqui se recorre la cadena COMPLETA de sv6 —guard, reconciliador,
matcher, conversor, calculador de importe y cabecera— desde el
``ValuationEnvelope`` tal como lo entrega sv5, y se comprueba el total.

Los numeros son los del lote ``alvaro_17082026`` (ver R16 y R18 de
``specs/F-019-importe-unitario-manda/requirements.md``). El contexto que
se construye reproduce el de la BBDD local medido el 2026-08-18:
``unidad_medida`` NULL en todas las lineas (IA1 no la devolvio),
``match_method='no_match'`` y contrato sin lineas utiles.

Sin red, sin BBDD, sin LLM: el builder es una clase pura y el registro
de unidades lee el YAML versionado del propio servicio.
"""
from __future__ import annotations

import pytest

#: (line_index, concepto, cantidad, precio bruto, dto %, importe leido)
LINEAS_2137569: tuple[tuple[int, str, float, float, float, float], ...] = (
    (0, "PAPEL HIGIENICO (SACO 108)", 108.0, 0.543, 40.0, 35.19),
    (1, "LTS. JABON LIQUIDO PH NEUTRO", 10.0, 3.422, 40.0, 20.53),
    (2, "ROLLO PAPEL IND.", 12.0, 7.726, 40.0, 55.63),
    (3, "KGS ANIL ESPECIAL FEYMACO", 4.0, 5.497, 40.0, 13.19),
    (4, "BOLSA BASURA 52X58", 100.0, 0.252, 40.0, 15.12),
)

#: Linea unica del albaran 2.139.643 (R18).
LINEAS_2139643: tuple[tuple[int, str, float, float, float, float], ...] = (
    (0, "DISCO ESPECIAL ACERO INOX. 115X1X22", 50.0, 0.647, 40.0, 19.41),
)

TOTAL_2137569 = 139.66
TOTAL_2139643 = 19.41

#: Lo que midio la prueba local del humano en la BBDD tras revalorar con
#: la rama de F-019 ya en ejecucion. Es el numero que este fichero
#: existe para impedir que vuelva.
TOTAL_MEDIDO_MAL = 232.76


def _construir_builder():
    """El mismo cableado que ``interface_adapters/composition.py``."""
    from pathlib import Path

    from application.services.importe_calculator import ImporteCalculator
    from application.services.partida_matcher import PartidaMatcher
    from application.services.price_reconciler import PriceReconciler
    from application.services.unit_category_guard import UnitCategoryGuard
    from application.services.unit_converter import UnitConverter
    from application.services.valuation_builder import ValuationBuilder
    from infrastructure.units.yaml_unit_registry import YamlUnitRegistry

    from tests.conftest import TOLERANCIA_IMPORTE_PCT, TOLERANCIA_PRECIO_PCT

    yaml_path = Path(__file__).resolve().parents[1] / "config" / "unit_registry.yaml"
    registro = YamlUnitRegistry(str(yaml_path))

    return ValuationBuilder(
        unit_category_guard=UnitCategoryGuard(unit_registry=registro),
        price_reconciler=PriceReconciler(tolerance_pct=TOLERANCIA_PRECIO_PCT),
        partida_matcher=PartidaMatcher(alm_codigo_partida="ALM"),
        unit_converter=UnitConverter(registry=registro),
        importe_calculator=ImporteCalculator(
            tolerance_pct=TOLERANCIA_IMPORTE_PCT,
        ),
    )


def _construir_envelope(numero_albaran: str, lineas):
    """Envelope de sv5 equivalente al medido en la BBDD el 2026-08-18."""
    from domain.models.valuation_envelope import (
        AlbaranLineContextDto,
        DocumentoValoracionDto,
        LineValuationDto,
        ValuationContextDto,
        ValuationEnvelope,
        ValuationEnvelopeMeta,
    )

    lineas_ia = []
    contexto = []
    for indice, concepto, cantidad, precio, descuento, importe in lineas:
        merge_line_id = 370 + indice
        lineas_ia.append(
            LineValuationDto(
                merge_line_id=merge_line_id,
                line_kind="from_albaran",
                # Medido en la BBDD: la IA no caso ninguna de las cinco.
                match_method="no_match",
                matched_contrato_line_id=None,
                match_confidence_pct=10.0,
                unidad_categoria_albaran="unknown",
                unidad_category_match=False,
                precio_unitario_contrato_db=None,
                precio_unitario_pdf_inferido=None,
                descripcion_linea=concepto,
            )
        )
        contexto.append(
            AlbaranLineContextDto(
                merge_line_id=merge_line_id,
                line_index=indice,
                descripcion=concepto,
                # IA1 no devolvio unidad en ninguna linea del lote.
                unidad_medida=None,
                unidad_categoria="unknown",
                cantidad=cantidad,
                precio_unitario_albaran=precio,
                # Lo que entrega sv5 TRAS F-019: el importe leido tal cual.
                importe_albaran=importe,
                descuento_albaran=descuento,
                precio_neto_albaran=importe,
                codigo_partida_albaran="CI.4.18",
            )
        )

    return ValuationEnvelope(
        status="ok",
        meta=ValuationEnvelopeMeta(
            document_id=f"doc-{numero_albaran}",
            codigo_contrato="CTSU24/0454",
            numero_albaran=numero_albaran,
        ),
        data=DocumentoValoracionDto(lineas=lineas_ia),
        context=ValuationContextDto(lineas_albaran=contexto, lineas_contrato=[]),
    )


@pytest.fixture
def builder():
    return _construir_builder()


def test_f019_r25_el_total_del_2137569_es_13966(builder):
    """El TOTAL del documento persistido vale 139,66 EUR.

    Es el aserto que faltaba: la prueba local del humano midio 232,76
    en esta misma columna con la feature ya cerrada.
    """
    cabecera, _ = builder.build(
        envelope=_construir_envelope("2.137.569", LINEAS_2137569),
        existing_document_already_valued=False,
    )

    assert cabecera.total_valorado != pytest.approx(TOTAL_MEDIDO_MAL)
    # Igualdad EXACTA a proposito: es una cantidad monetaria y va a una
    # columna de dinero (R26). Una suma float de los cinco importes da
    # 139.66000000000003, que no es 139,66.
    assert cabecera.total_valorado == TOTAL_2137569


def test_f019_r25_las_cinco_lineas_del_2137569_y_su_suma(builder):
    """Los cinco importes de linea, y que suman el total de la cabecera."""
    esperado = {
        370 + indice: importe
        for indice, _, _, _, _, importe in LINEAS_2137569
    }

    cabecera, registros = builder.build(
        envelope=_construir_envelope("2.137.569", LINEAS_2137569),
        existing_document_already_valued=False,
    )

    assert len(registros) == 5
    for registro in registros:
        assert registro.importe_calculado == pytest.approx(
            esperado[registro.merge_line_id]
        ), registro.merge_line_id
        assert registro.precio_unitario_source == "albaran_declared"
        assert registro.descuento_albaran_aplicado == pytest.approx(40.0)

    suma = sum(r.importe_calculado for r in registros)
    assert cabecera.total_valorado == pytest.approx(suma)


def test_f019_r25_el_total_del_2139643_es_1941(builder):
    """El segundo albaran del incidente, tambien por el builder entero."""
    cabecera, registros = builder.build(
        envelope=_construir_envelope("2.139.643", LINEAS_2139643),
        existing_document_already_valued=False,
    )

    assert len(registros) == 1
    assert registros[0].importe_calculado == pytest.approx(19.41)
    assert cabecera.total_valorado == TOTAL_2139643


#: Documento cuyos cinco importes suman con ruido de coma flotante:
#: ``sum([549.34, 882.62, 818.64, 863.26, 278.86])`` da
#: ``3392.7200000000003``, no 3392.72. No es rebuscado: un barrido de
#: 20.000 documentos de cinco lineas con importes de dos decimales da
#: ruido en 2.275 (11 %). El de Feymaco no lo tiene por suerte, y por
#: eso hace falta este caso aparte para vigilar R26.
LINEAS_CON_RUIDO_FLOAT: tuple[
    tuple[int, str, float, float, float, float], ...
] = (
    (0, "LINEA A", 1.0, 549.34, 0.0, 549.34),
    (1, "LINEA B", 1.0, 882.62, 0.0, 882.62),
    (2, "LINEA C", 1.0, 818.64, 0.0, 818.64),
    (3, "LINEA D", 1.0, 863.26, 0.0, 863.26),
    (4, "LINEA E", 1.0, 278.86, 0.0, 278.86),
)


def test_f019_r26_el_total_no_arrastra_ruido_de_coma_flotante(builder):
    """El total persistido es una cantidad monetaria de 2 decimales.

    Un total con cola binaria (3392.7200000000003) se pinta bien pero no
    cuadra con el del albaran ni contra Sigrid en ninguna comparacion
    por igualdad.
    """
    cabecera, registros = builder.build(
        envelope=_construir_envelope("X", LINEAS_CON_RUIDO_FLOAT),
        existing_document_already_valued=False,
    )

    # Precondicion del caso: la suma cruda SI tiene ruido, de modo que
    # el test no pasa por vacio si algun dia cambian los importes.
    suma_cruda = sum(r.importe_calculado for r in registros)
    assert suma_cruda != round(suma_cruda, 2), (
        "la fixture ya no reproduce el ruido float que R26 vigila"
    )

    assert cabecera.total_valorado == 3392.72
