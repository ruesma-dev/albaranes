# tests/test_f043_familia_efectiva.py
"""F-043 · T22 · las puertas de familia de sv6 abren por familia EFECTIVA.

Toda la maquinaria de familia de este servicio estaba cerrada tras
``contexto_linea.tipo_familia == X``. Ese campo lo rellena la fase 2 por
LINEA y en muchos albaranes no viene: en SS-0003967 el merge real traia
``contexto_linea = NULL`` y NINGUN proveedor puso la familia
(``progress/impl_F-036_bloque_D.md`` §2). Resultado: 540,00 EUR en un
albaran de 210,00.

R25 cambia la puerta, no lo que hay detras: cada una pasa a preguntar
por ``familia_efectiva(tipo_familia_de_la_linea, clasificacion)``, que
vive en el catalogo compartido (R20) y **no mira el papel** — ni LER, ni
producto, ni texto, ni CIF. Lo unico que hace es propagar a la linea la
decision que IA1 tomo sobre el DOCUMENTO.

Las OCHO puertas que este fichero recorre, con su linea original:

| # | Puerta | Familia |
|---|---|---|
| 1 | ``_es_movimiento_residuos`` (:305) | residuos |
| 2 | sinteticas M1 por año (:620) | hormigon |
| 3 | sinteticas por codigo (:704) | hormigon |
| 4 | red de sinteticas del LER (:847) | residuos |
| 5 | guarda anti-incremento (:986) | residuos |
| 6 | calculo de contenedores (:1166) | residuos |
| 7 | aviso de horas de descarga (:1227) | hormigon |
| 8 | padre residuos de una sintetica (:1397) | residuos |

Y los tres limites que NO se cruzan: albaran ``mixto`` no hereda (R19),
linea ``otro`` no hereda (decision del humano, duda 2), y sobre sin
clasificacion se comporta como hoy (R27).

Sin red, sin BBDD y sin LLM: el builder real con sus cinco colaboradores
(``f027_escenarios.construir_builder``) y sobres armados a mano.
"""
from __future__ import annotations

import inspect
import re

import pytest
from ruesma_comun.contratos import ClasificacionAlbaran

from application.services import valuation_builder as modulo_builder
from domain.models.contexto_linea import ContextoLinea
from domain.models.valuation_envelope import (
    AlbaranLineContextDto,
    ContratoLineContextDto,
    DocumentoValoracionDto,
    LineValuationDto,
    ValuationContextDto,
    ValuationEnvelope,
    ValuationEnvelopeMeta,
)
from tests.f027_escenarios import construir_builder
from tests.f036_escenarios_residuos import (
    CONTENEDOR_6,
    CONTRATO_SALMEDINA,
    EscenarioResiduos,
    LineaResiduos,
    base_de,
    linea_contrato,
    sinteticas_de,
    valorar,
)


def clasificacion(familia: str, **extra) -> ClasificacionAlbaran:
    """La clasificacion de DOCUMENTO tal como la entrega sv5."""
    datos = {
        "familia": familia,
        "confianza_pct": 90.0,
        "motivo": f"la IA leyo un albaran de {familia}",
    }
    datos.update(extra)
    return ClasificacionAlbaran(**datos)


# =================================================================== #
# R20 · el criterio vive en UN sitio y sv6 no lo duplica
# =================================================================== #

def test_f043_r20_ninguna_puerta_de_sv6_compara_ya_el_tipo_familia_a_pelo():
    """Ni una comparacion suelta contra ``tipo_familia`` en el builder.

    Es el test que impide que la proxima puerta de familia se escriba
    otra vez "a pelo". Si sv6 recuperara su propia comparacion, la
    herencia del documento dejaria de aplicarse SOLO en esa puerta y el
    fallo aparecerian como un importe raro, no como un error.

    Lo que se busca es la comparacion (``== 'residuos'``,
    ``!= "hormigon"``), no la palabra: el codigo sigue leyendo
    ``tipo_familia`` para PASARSELO a ``familia_efectiva``, que es
    justo lo que se quiere.
    """
    fuente = inspect.getsource(modulo_builder)
    comparaciones = re.findall(
        r"tipo_familia[^\n]{0,40}?(?:==|!=)\s*[\"']", fuente,
    )

    assert comparaciones == [], comparaciones


def test_f043_r20_el_builder_usa_el_familia_efectiva_del_catalogo():
    """El criterio se IMPORTA del catalogo, no se reimplementa aqui."""
    from ruesma_comun.contratos.familias import familia_efectiva

    assert modulo_builder.familia_efectiva is familia_efectiva


# =================================================================== #
# Puertas 4, 5 y 6 · residuos, con la linea SIN tipo_familia
# =================================================================== #

def _residuos_heredado(**kwargs) -> EscenarioResiduos:
    """Albaran de residuos con la familia SOLO en el documento.

    El LER es el 170802 —el de SS-0000589— porque es uno de los dos que
    el catalogo reducido de ``CONTRATO_SALMEDINA`` tarifa (51,00 EUR):
    asi la sintetica del incremento sale con precio y se puede medir el
    importe, no solo su presencia. El caso SS-0003967 completo, con su
    contrato real, es T23.
    """
    base = {
        "descripcion": "RETIRADA MATERIALES A BASE DE YESO",
        "cantidad": 6.0,
        "unidad": "M3",
        "codigo_ler": "170802",
        "volumen_m3": 6.0,
        # LA CLAVE DE LA TAREA: la linea NO trae familia. Antes de
        # F-043 esto apagaba las tres puertas de residuos.
        "tipo_familia": None,
        "rol_linea": None,
    }
    base.update(kwargs)
    return EscenarioResiduos(
        lineas=(LineaResiduos(**base),),
        contrato=tuple(CONTRATO_SALMEDINA),
        clasificacion=clasificacion("residuos"),
    )


def test_f043_r25_la_puerta_de_contenedores_abre_por_la_familia_heredada():
    """Puerta 6 (:1166): se valora 1 contenedor, no los 6 m3.

    Los 6 del albaran son la CAPACIDAD del contenedor. Sin esta puerta
    abierta se valoran como cantidad, que es el defecto D1 del lote de
    SALMEDINA.
    """
    _cabecera, registros = valorar(_residuos_heredado())
    base = base_de(registros)

    assert base.cantidad_convertida == pytest.approx(1.0)


def test_f043_r25_la_red_de_sinteticas_del_ler_abre_por_la_familia_heredada():
    """Puerta 4 (:847): se emite el incremento por LER del contrato."""
    _cabecera, registros = valorar(_residuos_heredado())
    sinteticas = sinteticas_de(registros)

    assert len(sinteticas) == 1
    assert sinteticas[0].descripcion_linea == "INCREMENTO LER 170802"


def test_f043_r25_la_guarda_anti_incremento_abre_por_la_familia_heredada():
    """Puerta 5 (:986): una base casada con un INCREMENTO se anula.

    Es el match REAL que IA3 hizo en SS-0003967 (la 26481). La guarda
    de F-036 R15 lo anula y manda la linea a revision: esa linea tarifa
    el recargo, no la retirada.
    """
    incremento = linea_contrato(
        26481, "INCREMENTO LER 170604 MATERIALES DE AISLAMIENTO", 90.0,
    )
    escenario = EscenarioResiduos(
        lineas=(
            LineaResiduos(
                descripcion="RETIRADA MATERIALES DE AISLAMIENTO",
                cantidad=6.0,
                unidad="M3",
                codigo_ler="170604",
                volumen_m3=6.0,
                tipo_familia=None,
                rol_linea=None,
                matched_contrato_line_id=incremento.contrato_line_id,
                precio_contrato_db=incremento.precio_unitario,
                match_method="exact_concept",
            ),
        ),
        contrato=(CONTENEDOR_6, incremento),
        clasificacion=clasificacion("residuos"),
    )
    _cabecera, registros = valorar(escenario)
    base = base_de(registros)

    assert "residuos_base_casada_con_incremento" in base.review_reasons
    assert base.precio_unitario_contrato_db is None


def test_f043_r25_el_movimiento_sin_cantidad_vale_1_por_la_familia_heredada():
    """Puerta 1 (:305): un porte sin cantidad documenta UN movimiento.

    Sin esta puerta abierta la linea se quedaba con cantidad e importe
    vacios. Se usa ``rol_linea='transporte'`` porque es la senal que la
    puerta mira PRIMERO, y el contexto llega sin familia.
    """
    porte = linea_contrato(9004, "PORTE DE CONTENEDOR", 45.0)
    escenario = EscenarioResiduos(
        lineas=(
            LineaResiduos(
                descripcion="PORTE DE CONTENEDOR",
                cantidad=None,
                unidad="UD",
                codigo_ler=None,
                volumen_m3=None,
                tipo_familia=None,
                rol_linea="transporte",
                matched_contrato_line_id=porte.contrato_line_id,
                precio_contrato_db=porte.precio_unitario,
            ),
        ),
        contrato=(CONTENEDOR_6, porte),
        clasificacion=clasificacion("residuos"),
    )
    _cabecera, registros = valorar(escenario)
    base = base_de(registros)

    assert "movimiento_residuos_sin_cantidad_asumido_1" in base.review_reasons
    assert base.cantidad_convertida == pytest.approx(1.0)
    assert base.importe_calculado == pytest.approx(45.0)


def test_f043_r25_la_sintetica_hereda_los_contenedores_del_padre_heredado():
    """Puerta 8 (:1397): el padre es de residuos por la clasificacion.

    La sintetica del LER hereda 1 CONTENEDOR del padre, no sus 6 m3. Si
    esta puerta no viera la familia heredada, el incremento se cobraria
    seis veces.
    """
    _cabecera, registros = valorar(_residuos_heredado())
    sintetica = sinteticas_de(registros)[0]

    assert sintetica.cantidad_convertida == pytest.approx(1.0)
    assert sintetica.importe_calculado == pytest.approx(51.0)


# =================================================================== #
# Puertas 2, 3 y 7 · hormigon, con la linea SIN tipo_familia
# =================================================================== #

#: Contrato de hormigon: el incremento por año que IA3 suele olvidar y
#: el de consistencia especial que se lee del propio codigo.
INCREMENTO_ANIO_2025 = ContratoLineContextDto(
    contrato_line_id=3101,
    codigo_contrato="CTSU24/0900",
    descripcion="INCREMENTO POR AÑO 2025",
    unidad_medida="M3",
    precio_unitario=2.5,
    codigo_partida="10.01",
)
INCREMENTO_CONSISTENCIA = ContratoLineContextDto(
    contrato_line_id=3102,
    codigo_contrato="CTSU24/0900",
    descripcion="INCREMENTO CONSISTENCIA FLUIDA",
    unidad_medida="M3",
    precio_unitario=3.0,
    codigo_partida="10.01",
)
HORMIGON_HA25 = ContratoLineContextDto(
    contrato_line_id=3100,
    codigo_contrato="CTSU24/0900",
    descripcion="HORMIGON HA-25/F/20/IIa",
    unidad_medida="M3",
    precio_unitario=70.0,
    codigo_partida="10.01",
)


def _valorar_hormigon(
    *,
    familia_linea: str | None,
    clasificacion_documento,
    notas_tiempo: str | None = None,
):
    """Un albaran de hormigon de una linea, contra su contrato."""
    descripcion = "HA-25/F/20/IIa"
    contexto_linea = ContextoLinea(
        tipo_familia=familia_linea,
        rol_linea=None,
        descripcion_extendida=descripcion,
        notas_tiempo=notas_tiempo,
    )
    envelope = ValuationEnvelope(
        status="ok",
        meta=ValuationEnvelopeMeta(
            document_id="doc-hormigon",
            codigo_contrato="CTSU24/0900",
            numero_albaran="HC-1",
            fecha_albaran="2025-03-04",
        ),
        data=DocumentoValoracionDto(
            lineas=[
                LineValuationDto(
                    merge_line_id=810,
                    line_kind="from_albaran",
                    match_method="semantic",
                    matched_contrato_line_id=HORMIGON_HA25.contrato_line_id,
                    match_confidence_pct=95.0,
                    unidad_categoria_albaran="volume",
                    unidad_category_match=True,
                    precio_unitario_contrato_db=HORMIGON_HA25.precio_unitario,
                    descripcion_linea=descripcion,
                )
            ]
        ),
        context=ValuationContextDto(
            lineas_albaran=[
                AlbaranLineContextDto(
                    merge_line_id=810,
                    line_index=0,
                    descripcion=descripcion,
                    unidad_medida="M3",
                    unidad_categoria="volume",
                    cantidad=8.0,
                    precio_unitario_albaran=None,
                    importe_albaran=None,
                    codigo_partida_albaran="10.01",
                    contexto_linea=contexto_linea,
                )
            ],
            lineas_contrato=[
                HORMIGON_HA25,
                INCREMENTO_ANIO_2025,
                INCREMENTO_CONSISTENCIA,
            ],
            clasificacion=clasificacion_documento,
        ),
    )
    return construir_builder().build(
        envelope=envelope, existing_document_already_valued=False,
    )


def _fuentes(registros) -> set:
    return {
        r.modifier_source
        for r in registros
        if r.line_kind == "synthetic_modifier"
    }


def test_f043_r25_las_sinteticas_de_hormigon_abren_por_la_familia_heredada():
    """Puertas 2 (:620) y 3 (:704) con la linea SIN ``tipo_familia``.

    Contrato de 2024 y albaran de 2025: toca el incremento por año. Y
    la designacion HA-25/**F**/20/IIa pide el de consistencia fluida.
    Las dos redes deterministas existen porque IA3 se las olvida.
    """
    _cabecera, registros = _valorar_hormigon(
        familia_linea=None,
        clasificacion_documento=clasificacion("hormigon"),
    )

    assert _fuentes(registros), registros
    assert len(sinteticas_de(registros)) >= 2


def test_f043_r27_sin_clasificacion_el_hormigon_no_gana_ninguna_sintetica():
    """El MISMO sobre sin clasificacion: como hoy, ni una sintetica.

    Es la comparacion que aisla lo que cambio: el unico campo distinto
    respecto al test anterior es ``context.clasificacion``.
    """
    _cabecera, registros = _valorar_hormigon(
        familia_linea=None, clasificacion_documento=None,
    )

    assert sinteticas_de(registros) == []


def test_f043_r25_el_aviso_de_horas_de_descarga_abre_por_familia_heredada():
    """Puerta 7 (:1227): el exceso de tiempo no es computable, y se dice.

    Si IA2 deja constancia de que la hora de fin de descarga vino en
    blanco, el revisor tiene que verlo: sin las horas, los minutos de
    exceso no se pueden calcular y el albaran quedaria valorado de
    menos en silencio.
    """
    _cabecera, registros = _valorar_hormigon(
        familia_linea=None,
        clasificacion_documento=clasificacion("hormigon"),
        notas_tiempo="la hora fin de descarga viene en blanco",
    )
    base = base_de(registros)

    assert "horas_descarga_incompletas" in base.review_reasons


# =================================================================== #
# Los tres limites que NO se cruzan
# =================================================================== #

def test_f043_r19_un_albaran_mixto_no_hereda_familia_a_sus_lineas():
    """Documento ``mixto=True``: la linea se queda SIN familia efectiva.

    En un albaran mezclado, heredar la familia mayoritaria aplicaria
    las reglas de residuos a lineas que no lo son. El sitio donde eso
    se hace visible es sv3, con el motivo
    ``linea_sin_familia_en_albaran_mixto``; aqui lo que toca es NO
    valorar como residuos.
    """
    escenario = _residuos_heredado()
    escenario = EscenarioResiduos(
        lineas=escenario.lineas,
        contrato=escenario.contrato,
        clasificacion=clasificacion("residuos", mixto=True),
    )
    _cabecera, registros = valorar(escenario)

    assert sinteticas_de(registros) == []
    assert base_de(registros).cantidad_convertida is None


def test_f043_r18_una_linea_marcada_otro_no_hereda_la_del_documento():
    """``otro`` es la forma de decir "a esta linea, las reglas no".

    Decision del humano (duda 2): una linea de transporte suelto dentro
    de un albaran de residuos se comeria la regla de contenedores si
    heredara. Lo que la IA dijo de la LINEA gana siempre.
    """
    escenario = EscenarioResiduos(
        lineas=(
            LineaResiduos(
                descripcion="TRANSPORTE",
                cantidad=6.0,
                unidad="M3",
                codigo_ler="170604",
                volumen_m3=6.0,
                tipo_familia="otro",
                rol_linea=None,
            ),
        ),
        contrato=tuple(CONTRATO_SALMEDINA),
        clasificacion=clasificacion("residuos"),
    )
    _cabecera, registros = valorar(escenario)

    assert sinteticas_de(registros) == []
    assert base_de(registros).cantidad_convertida is None


def test_f043_r25_una_clasificacion_generica_no_abre_ninguna_puerta():
    """``generico`` es una familia legitima, y no abre nada.

    Desde la revision del catalogo, ``familia_efectiva`` puede devolver
    ``'generico'`` donde antes devolvia ``None``. Las puertas comparan
    contra ``'residuos'`` y ``'hormigon'``, asi que el efecto es el
    mismo: ninguna abre. Se fija aqui porque es el punto donde un
    cambio del catalogo podria colarse sin que nadie lo note.
    """
    escenario = _residuos_heredado()
    escenario = EscenarioResiduos(
        lineas=escenario.lineas,
        contrato=escenario.contrato,
        clasificacion=clasificacion("generico"),
    )
    _cabecera, registros = valorar(escenario)

    assert sinteticas_de(registros) == []
    assert base_de(registros).cantidad_convertida is None


def test_f043_r27_sin_clasificacion_los_residuos_se_comportan_como_hoy():
    """El mismo sobre sin clasificacion: ninguna regla de residuos.

    La otra mitad de R27, medida en el escenario que de verdad importa.
    """
    escenario = _residuos_heredado()
    escenario = EscenarioResiduos(
        lineas=escenario.lineas,
        contrato=escenario.contrato,
        clasificacion=None,
    )
    _cabecera, registros = valorar(escenario)

    assert sinteticas_de(registros) == []
    assert base_de(registros).cantidad_convertida is None


def test_f043_r21_la_herencia_no_se_escribe_en_el_contexto_de_la_linea():
    """La familia heredada se resuelve en LECTURA, no se persiste (R21).

    Si el builder escribiera la familia dentro de ``contexto_linea``,
    se borraria la diferencia entre "lo dijo la IA de esta linea" y "se
    heredo del documento", y el proximo lector no podria distinguirlas.
    """
    escenario = _residuos_heredado()
    envelope_lineas = escenario.lineas
    _cabecera, _registros = valorar(escenario)

    assert envelope_lineas[0].contexto().tipo_familia is None
