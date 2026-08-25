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
from domain.models.valuation_envelope import LineValuationDto
from tests.f036_escenarios_residuos import (
    CONTENEDOR_6,
    CONTRATO_SALMEDINA,
    INCREMENTO_170802,
    EscenarioResiduos,
    LineaResiduos,
    sinteticas_de,
    valorar,
)


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


# =================================================================== #
# T16 · R16 y R18 — el recorrido del builder inyecta (y no duplica)
# =================================================================== #

def _sintetica_de_ia3(
    descripcion: str,
    *,
    rol: str = "incremento_residuos",
    parent: int = 700,
) -> LineValuationDto:
    """Una sintetica que IA3 hubiera traido en el sobre (dedupe R18)."""
    return LineValuationDto(
        merge_line_id=None,
        line_kind="synthetic_modifier",
        parent_merge_line_id=parent,
        modifier_source="gestion_residuos",
        descripcion_linea=descripcion,
        rol_linea=rol,
        match_method="no_match",
        match_confidence_pct=80.0,
    )


def test_f036_r16_la_sintetica_del_ler_se_inyecta_en_la_valoracion():
    """De 1 linea de albaran salen 2 records: contenedor + incremento."""
    _, registros = valorar(EscenarioResiduos())
    sinteticas = sinteticas_de(registros)

    assert len(sinteticas) == 1
    syn = sinteticas[0]
    assert syn.modifier_source == "gestion_residuos"
    assert syn.rol_linea == "incremento_residuos"
    assert syn.descripcion_linea == "INCREMENTO LER 170802"
    assert syn.parent_merge_line_id == 700
    assert syn.matched_contrato_line_id == INCREMENTO_170802.contrato_line_id
    assert syn.precio_unitario_final == pytest.approx(51.0)


def test_f036_r16_sin_codigo_ler_no_se_inventa_ninguna_sintetica():
    """Sin LER no hay incremento que reclamar."""
    escenario = EscenarioResiduos(
        lineas=(LineaResiduos(codigo_ler=None),),
    )
    _, registros = valorar(escenario)

    assert sinteticas_de(registros) == []


def test_f036_r16_el_recorrido_solo_mira_lineas_de_residuos():
    """Un LER en una linea de hormigon no dispara la red de residuos."""
    escenario = EscenarioResiduos(
        lineas=(
            LineaResiduos(tipo_familia="hormigon", codigo_ler="170802"),
        ),
    )
    _, registros = valorar(escenario)

    assert sinteticas_de(registros) == []


def test_f036_r18_no_se_duplica_si_ia3_ya_emitio_el_mismo_rol():
    """Dedupe por rol: `incremento_residuos` para esa misma base."""
    escenario = EscenarioResiduos(
        sinteticas_ia=(
            _sintetica_de_ia3("RECARGO POR TIPO DE RESIDUO"),
        ),
    )
    _, registros = valorar(escenario)

    assert len(sinteticas_de(registros)) == 1


def test_f036_r18_no_se_duplica_si_ia3_ya_nombro_ese_ler():
    """Dedupe por clave: el codigo LER en la descripcion, con otro rol."""
    escenario = EscenarioResiduos(
        sinteticas_ia=(
            _sintetica_de_ia3(
                "INCREMENTO LER 170802", rol="incremento_otro",
            ),
        ),
    )
    _, registros = valorar(escenario)

    assert len(sinteticas_de(registros)) == 1


def test_f036_r18_una_sintetica_de_OTRA_base_no_bloquea_la_inyeccion():
    """El dedupe es POR LINEA BASE, no por documento.

    La sintetica del sobre cuelga de otra base (999): la nuestra se
    emite igual, de modo que salen las DOS. Si el dedupe mirase el
    documento entero, la linea 700 se quedaria sin su incremento.
    """
    escenario = EscenarioResiduos(
        sinteticas_ia=(
            _sintetica_de_ia3("INCREMENTO LER 170802", parent=999),
        ),
    )
    _, registros = valorar(escenario)
    sinteticas = sinteticas_de(registros)

    assert len(sinteticas) == 2
    padres = sorted(s.parent_merge_line_id for s in sinteticas)
    assert padres == [700, 999]


def test_f036_r21_una_regla_ficticia_se_emite_sin_tocar_el_recorrido():
    """La prueba de que la lista es el punto de enganche de F-006.

    Se anade una regla NUEVA a `REGLAS_SINTETICAS_RESIDUOS` y su
    sintetica sale en la valoracion sin haber cambiado una linea del
    builder. Es exactamente lo que hara el canon de vertedero.
    """
    from application.services import residuos_incrementos as ri

    def _regla_canon(*, ctx, base, contrato_lines):
        return ri.dto_red_residuos(
            base=base,
            rol="canon_vertedero",
            descripcion="CANON DE VERTEDERO (regla ficticia)",
            motivo="regla de prueba",
            etiqueta="canon ficticio",
            tarifa=None,
        )

    ri.REGLAS_SINTETICAS_RESIDUOS.append(_regla_canon)
    try:
        _, registros = valorar(EscenarioResiduos())
    finally:
        ri.REGLAS_SINTETICAS_RESIDUOS.remove(_regla_canon)

    descripciones = [s.descripcion_linea for s in sinteticas_de(registros)]
    assert "INCREMENTO LER 170802" in descripciones
    assert "CANON DE VERTEDERO (regla ficticia)" in descripciones
