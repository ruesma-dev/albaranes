# tests/test_f036_r16_r19_sinteticas_ler.py
"""F-036 D3 · la sintetica del INCREMENTO POR LER (R16-R19, R21).

Hoy los incrementos por LER no se emiten NUNCA: los prompts prohiben a
IA3 emitir sinteticas en residuos (`prompts.yaml`, bloque
`valuation_residuos`) y las dos redes deterministas de sv6
(`_sinteticas_m1_faltantes`, `_sinteticas_codigo_faltantes`) estan
limitadas a hormigon. Confirmado contra la BBDD real en SS-0000589:
contenedor bien valorado (1 x 120) y contrato con el INCREMENTO LER
170802 cargado, pero ninguna segunda linea; faltan los 51 EUR hasta los
171 del administrativo (`progress/explore_F-036.md`, apendice D3).

Este fichero cubre:

  * R21 — la lista `REGLAS_SINTETICAS_RESIDUOS` es el punto de enganche:
    el recorrido de bases NO sabe que reglas hay. F-006 (canon de
    vertedero) anade la suya a la lista sin tocar el builder.
  * R16 — con `codigo_ler` valido se emite SIEMPRE la sintetica.
  * R18 — si IA3 ya emitio una equivalente, no se duplica.
  * R17 — sin tarifa en el contrato se emite IGUAL, sin precio, con la
    razon `residuos_ler_sin_tarifa_en_contrato` y a revision.
  * R19 — la cantidad se hereda del nº de CONTENEDORES de la base,
    nunca de los m3 del albaran.

Sin red, sin BBDD, sin LLM.
"""
from __future__ import annotations

import pytest
from domain.models.contexto_linea import ContextoLinea
from domain.models.valuation_envelope import (
    ContratoLineContextDto,
    LineValuationDto,
)


# ------------------------------------------------------------------ #
# Catalogo minimo del contrato de SALMEDINA (los dos conceptos que
# importan, en la MISMA partida, como estan en Sigrid).
# ------------------------------------------------------------------ #
def _contrato_line(
    contrato_line_id: int,
    descripcion: str,
    precio: float,
    partida: str = "32.01",
) -> ContratoLineContextDto:
    return ContratoLineContextDto(
        contrato_line_id=contrato_line_id,
        codigo_contrato="CTSU25/0100",
        codigo_producto=None,
        descripcion=descripcion,
        unidad_medida="UD",
        precio_unitario=precio,
        codigo_partida=partida,
    )


CONTENEDOR_6 = _contrato_line(
    9001, "MOVIMIENTO DE CONTENEDOR DE 6 M CUBICOS MEZCLA OTROS RESIDUOS", 120.0
)
INCREMENTO_170802 = _contrato_line(
    9002, "INCREMENTO LER 170802 MATERIALES DE CONSTRUCCION A BASE DE YESO", 51.0
)
INCREMENTO_170904 = _contrato_line(
    9003, "INCREMENTO LER 170904 RESIDUOS MEZCLADOS", 16.0
)

CONTRATO_SALMEDINA = [CONTENEDOR_6, INCREMENTO_170802, INCREMENTO_170904]


def _base(merge_line_id: int = 700) -> LineValuationDto:
    """La linea base del albaran, tal como la devuelve IA3."""
    return LineValuationDto(
        merge_line_id=merge_line_id,
        line_kind="from_albaran",
        match_method="semantic",
        matched_contrato_line_id=CONTENEDOR_6.contrato_line_id,
        match_confidence_pct=90.0,
        precio_unitario_contrato_db=CONTENEDOR_6.precio_unitario,
        descripcion_linea="RESIDUOS MEZCLADOS LER 170802",
    )


def _ctx(codigo_ler: str | None = "170802", **kwargs) -> ContextoLinea:
    return ContextoLinea(
        tipo_familia="residuos",
        rol_linea="base",
        codigo_ler=codigo_ler,
        volumen_m3=kwargs.pop("volumen_m3", 6.0),
        **kwargs,
    )


# =================================================================== #
# T14 · R21 — las reglas viven fuera del recorrido
# =================================================================== #

def test_f036_r21_reconoce_la_linea_de_contrato_de_incremento_por_ler():
    """`es_linea_incremento_ler` devuelve el codigo, no un booleano.

    El codigo es lo que se necesita aguas arriba: para la guarda de R15
    basta saber que ES un incremento, pero para casar la sintetica hay
    que saber DE QUE LER (un contrato tarifa varios).
    """
    from application.services.residuos_incrementos import (
        es_linea_incremento_ler,
    )

    assert es_linea_incremento_ler(INCREMENTO_170802.descripcion) == "170802"
    assert es_linea_incremento_ler("Incremento ler 17 09 04") == "170904"


def test_f036_r21_el_contenedor_no_es_un_incremento():
    """La linea que se factura no puede confundirse con el recargo."""
    from application.services.residuos_incrementos import (
        es_linea_incremento_ler,
    )

    assert es_linea_incremento_ler(CONTENEDOR_6.descripcion) is None
    # Un incremento SIN LER (el de gestion de residuos del hormigon)
    # tampoco: no es un incremento POR LER.
    assert es_linea_incremento_ler(
        "INCREMENTO POR GESTION DE RESIDUOS EN HORMIGON"
    ) is None
    # Seis digitos que no existen en el catalogo LER (19 21 no llega):
    # el bug real de Prebetong con el codigo de producto 192137.
    assert es_linea_incremento_ler("INCREMENTO 192137") is None


def test_f036_r21_la_tarifa_se_busca_por_el_ler_concreto():
    """Con dos incrementos en el contrato se elige el del LER pedido."""
    from application.services.residuos_incrementos import (
        tarifa_incremento_ler,
    )

    tarifa = tarifa_incremento_ler(CONTRATO_SALMEDINA, "170802")

    assert tarifa is not None
    assert tarifa.contrato_line_id == INCREMENTO_170802.contrato_line_id
    assert tarifa.precio_unitario == pytest.approx(51.0)


def test_f036_r21_sin_tarifa_para_ese_ler_devuelve_none():
    """El contrato tarifa OTROS LER: no vale el primero que pase."""
    from application.services.residuos_incrementos import (
        tarifa_incremento_ler,
    )

    assert tarifa_incremento_ler(CONTRATO_SALMEDINA, "170504") is None
    assert tarifa_incremento_ler([], "170802") is None


def test_f036_r21_la_regla_del_ler_produce_la_sintetica_completa():
    """La regla es autonoma: devuelve el DTO ya listo para el builder."""
    from application.services.residuos_incrementos import (
        REGLAS_SINTETICAS_RESIDUOS,
    )

    dtos = [
        regla(ctx=_ctx(), base=_base(), contrato_lines=CONTRATO_SALMEDINA)
        for regla in REGLAS_SINTETICAS_RESIDUOS
    ]
    emitidos = [d for d in dtos if d is not None]

    assert len(emitidos) == 1
    dto = emitidos[0]
    assert dto.line_kind == "synthetic_modifier"
    assert dto.modifier_source == "gestion_residuos"
    assert dto.rol_linea == "incremento_residuos"
    assert dto.descripcion_linea == "INCREMENTO LER 170802"
    assert dto.parent_merge_line_id == 700
    assert dto.matched_contrato_line_id == INCREMENTO_170802.contrato_line_id
    assert dto.precio_unitario_contrato_db == pytest.approx(51.0)
    assert dto.match_method == "semantic"


def test_f036_r21_sin_ler_valido_la_regla_no_emite_nada():
    """Sin LER no hay incremento que reclamar (ni se inventa uno)."""
    from application.services.residuos_incrementos import (
        REGLAS_SINTETICAS_RESIDUOS,
    )

    for codigo in (None, "", "192137", "ABC"):
        dtos = [
            regla(
                ctx=_ctx(codigo_ler=codigo),
                base=_base(),
                contrato_lines=CONTRATO_SALMEDINA,
            )
            for regla in REGLAS_SINTETICAS_RESIDUOS
        ]
        assert all(d is None for d in dtos), codigo


def test_f036_r21_la_lista_de_reglas_es_el_punto_de_enganche_de_f006():
    """Hoy UNA regla; el contrato de la lista es lo que importa.

    F-006 (canon de vertedero) anadira la suya a esta lista. Este test
    fija la firma `(ctx, base, contrato_lines) -> LineValuationDto|None`
    para que la regla nueva no tenga que tocar el recorrido del builder.
    """
    from application.services.residuos_incrementos import (
        REGLAS_SINTETICAS_RESIDUOS,
    )

    assert isinstance(REGLAS_SINTETICAS_RESIDUOS, list)
    assert len(REGLAS_SINTETICAS_RESIDUOS) == 1
    assert all(callable(r) for r in REGLAS_SINTETICAS_RESIDUOS)
