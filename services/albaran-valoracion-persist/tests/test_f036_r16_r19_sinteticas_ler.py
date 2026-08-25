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
from application.services.residuos_incrementos import RAZON_SIN_CANTIDAD
from domain.models.contexto_linea import ContextoLinea
from domain.models.valuation_envelope import LineValuationDto
from tests.f036_escenarios_residuos import (
    CONTENEDOR_6,
    CONTRATO_SALMEDINA,
    CONTRATO_SIN_INCREMENTOS,
    INCREMENTO_170802,
    EscenarioResiduos,
    LineaResiduos,
    base_de,
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
    # Sin descripcion no hay nada que decidir.
    assert es_linea_incremento_ler(None) is None
    assert es_linea_incremento_ler("") is None


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


# =================================================================== #
# T17 · R17 — sin tarifa en el contrato, la sintetica se emite IGUAL
# =================================================================== #

def _escenario_sin_tarifa() -> EscenarioResiduos:
    """El contrato solo tarifa el contenedor: ningun INCREMENTO LER."""
    return EscenarioResiduos(contrato=tuple(CONTRATO_SIN_INCREMENTOS))


def test_f036_r17_la_sintetica_se_emite_aunque_el_contrato_no_tarife_ese_ler():
    """Decision del humano (2026-08-22): "siempre debe crear la
    sintetica; ya pondra el revisor el importe a mano".

    La alternativa —no emitirla— se descarto a proposito: dejaba el
    incremento invisible y sin nadie a quien reclamarlo.
    """
    _, registros = valorar(_escenario_sin_tarifa())
    sinteticas = sinteticas_de(registros)

    assert len(sinteticas) == 1
    syn = sinteticas[0]
    assert syn.descripcion_linea == "INCREMENTO LER 170802"
    assert syn.match_method == "no_match"
    assert syn.matched_contrato_line_id is None


def test_f036_r17_la_sintetica_sin_tarifa_sale_sin_precio_ni_importe():
    """Es la "forma C" de la red M1, no una divergencia de residuos."""
    _, registros = valorar(_escenario_sin_tarifa())
    syn = sinteticas_de(registros)[0]

    assert syn.precio_unitario_final is None
    assert syn.importe_calculado is None


def test_f036_r17_la_sintetica_sin_tarifa_lleva_su_razon_y_va_a_revision():
    """La linea existe JUSTAMENTE para que el revisor la complete."""
    _, registros = valorar(_escenario_sin_tarifa())
    syn = sinteticas_de(registros)[0]

    assert "residuos_ler_sin_tarifa_en_contrato" in syn.review_reasons
    assert syn.review_required is True


def test_f036_r17_el_total_del_documento_no_se_mueve():
    """El invariante de SS-0000168 / SS-0003935 / SS-0025146.

    Esos tres albaranes GANAN una linea sin precio y pasan a
    `review_required`, y eso es lo querido (riesgo 3 del design). Lo
    que no puede moverse es su TOTAL: una linea sin importe suma 0.
    """
    cabecera, registros = valorar(_escenario_sin_tarifa())

    assert cabecera.total_valorado == pytest.approx(120.0)
    assert len(registros) == 2
    assert cabecera.review_required is True


# =================================================================== #
# T18 · R19 — la cantidad se hereda del nº de CONTENEDORES
# =================================================================== #

def test_f036_r19_la_sintetica_hereda_el_numero_de_contenedores():
    """NUNCA los m3 del albaran.

    La base son 6 m3 = 1 contenedor. Si la sintetica heredara los 6 m3
    el incremento saldria a 6 x 51 = 306 EUR: seis veces lo que cobra
    el gestor. En residuos la cantidad VALORADA es el nº de
    contenedores y vive en `cantidad_convertida`, no en la cantidad
    cruda del albaran.
    """
    _, registros = valorar(EscenarioResiduos())
    syn = sinteticas_de(registros)[0]

    assert syn.cantidad_albaran == pytest.approx(1.0)
    assert syn.cantidad_convertida == pytest.approx(1.0)
    assert syn.importe_calculado == pytest.approx(51.0)


def test_f036_r19_el_total_de_ss_0000589_son_171_euros():
    """El numero del administrativo: 120 del contenedor + 51 del LER."""
    cabecera, registros = valorar(EscenarioResiduos())
    base = base_de(registros)

    assert base.importe_calculado == pytest.approx(120.0)
    assert cabecera.total_valorado == pytest.approx(171.0)


def test_f036_r19_con_dos_contenedores_el_incremento_va_por_contenedor():
    """12 m3 = 2 contenedores: 2 x 120 + 2 x 51 = 342 EUR."""
    escenario = EscenarioResiduos(
        lineas=(LineaResiduos(volumen_m3=12.0, cantidad=12.0),),
    )
    cabecera, registros = valorar(escenario)
    syn = sinteticas_de(registros)[0]

    assert base_de(registros).cantidad_convertida == pytest.approx(2.0)
    assert syn.cantidad_convertida == pytest.approx(2.0)
    assert cabecera.total_valorado == pytest.approx(342.0)


def test_f036_r19_la_herencia_normal_no_cambia_fuera_de_residuos():
    """La regla es de residuos: el resto sigue heredando como siempre.

    Una sintetica de hormigon hereda `cantidad_albaran` del padre (los
    m3 del albaran), que ahi SI es la cantidad valorada.
    """
    escenario = EscenarioResiduos(
        lineas=(
            LineaResiduos(
                tipo_familia="hormigon",
                codigo_ler=None,
                volumen_m3=None,
                cantidad=8.0,
            ),
        ),
        sinteticas_ia=(
            _sintetica_de_ia3(
                "INCREMENTO POR CONSISTENCIA FLUIDA",
                rol="incremento_consistencia",
            ),
        ),
    )
    _, registros = valorar(escenario)
    syn = sinteticas_de(registros)[0]

    assert syn.cantidad_albaran == pytest.approx(8.0)


# ------------------------------------------------------------------- #
# R19 por el OTRO camino: la base de residuos SIN contenedores
# calculables (`residuos_sin_volumen_m3`). Encontrado por el reviewer
# en la review de los bloques B/C/D: la herencia de contenedores solo
# actuaba con `cantidad_convertida is not None`, asi que este caso caia
# al fallback de `cantidad_albaran` y valoraba el incremento sobre los
# m3 crudos — exactamente lo que R19 prohibe, por otra rama.
# ------------------------------------------------------------------- #

def _escenario_sin_contenedores() -> EscenarioResiduos:
    """Base de residuos que NO permite calcular contenedores.

    Ni `volumen_m3` ni `contenedores` en el contexto: es el caso
    `residuos_sin_volumen_m3` de `residuos_container_calc`. La linea
    del albaran sigue trayendo sus 6 m3 crudos en `cantidad`.
    """
    return EscenarioResiduos(
        lineas=(LineaResiduos(volumen_m3=None, contenedores=None),),
    )


def test_f036_r19_sin_contenedores_la_sintetica_no_hereda_los_m3():
    """R19 no admite excepciones: NUNCA los m3, ni en este camino.

    Heredar `cantidad_albaran` aqui daba 6 UD x 51 = 306,00 EUR de
    incremento (total 1026,00), seis veces el recargo real. Como no hay
    forma de saber cuantos contenedores son, la cantidad se deja SIN
    inventar en vez de inventarla mal.
    """
    _, registros = valorar(_escenario_sin_contenedores())
    syn = sinteticas_de(registros)[0]

    assert base_de(registros).cantidad_convertida is None
    assert syn.cantidad_albaran is None
    assert syn.cantidad_convertida is None
    assert syn.importe_calculado is None


def test_f036_r19_sin_contenedores_la_sintetica_dice_por_que_y_va_a_revision():
    """Una linea sin cantidad tiene que explicarse, no aparecer muda.

    El revisor ve el incremento del LER, ve que no lleva numero y lee
    el motivo: la base no permitio calcular contenedores. Ponerle 306
    EUR lo hubiera dejado sin nada que revisar.
    """
    _, registros = valorar(_escenario_sin_contenedores())
    syn = sinteticas_de(registros)[0]

    assert RAZON_SIN_CANTIDAD in syn.review_reasons
    assert syn.review_required is True


def test_f036_r19_sin_contenedores_el_total_no_incluye_el_incremento():
    """Sin cantidad no hay importe, y sin importe no suma al total.

    El importe de la BASE (720,00 = 6 m3 x 120) es un fallback
    preexistente de `importe_calculator` ajeno a F-036: aqui se fija
    solo que la sintetica no anade sus 306 EUR fantasma.
    """
    cabecera, registros = valorar(_escenario_sin_contenedores())

    assert cabecera.total_valorado == pytest.approx(
        base_de(registros).importe_calculado
    )


def test_f036_r16_una_linea_sin_merge_line_id_no_rompe_el_recorrido():
    """Guarda defensiva, hermana de la de las otras dos redes.

    Una linea `from_albaran` sin `merge_line_id` no tiene base a la que
    colgar una sintetica: se salta en silencio y el resto del documento
    se valora igual.
    """
    huerfana = LineValuationDto(
        merge_line_id=None,
        line_kind="from_albaran",
        match_method="no_match",
        descripcion_linea="LINEA SIN IDENTIFICAR",
    )
    escenario = EscenarioResiduos(sinteticas_ia=(huerfana,))
    cabecera, registros = valorar(escenario)

    assert len(sinteticas_de(registros)) == 1
    assert cabecera.total_valorado == pytest.approx(171.0)
