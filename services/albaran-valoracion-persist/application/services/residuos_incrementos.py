# application/services/residuos_incrementos.py
"""Reglas deterministas de las lineas SINTETICAS de residuos (F-036 D3).

Que problema resuelve
---------------------
Los contratos de gestion de residuos tarifan DOS cosas por cada
retirada: el MOVIMIENTO del contenedor ("MOVIMIENTO DE CONTENEDOR DE 6 M
CUBICOS ...") y un INCREMENTO por el codigo LER del residuo
("INCREMENTO LER 170802 ..."). El albaran solo documenta la retirada, asi
que el incremento no es una linea del documento: hay que INYECTARLO.

Hasta F-036 no lo inyectaba nadie. Los prompts prohiben a IA3 emitir
sinteticas en residuos (y deben seguir prohibiendolo: el numero no lo
calcula una IA) y las dos redes deterministas de sv6
(``_sinteticas_m1_faltantes``, ``_sinteticas_codigo_faltantes``) estan
limitadas a hormigon. Medido en SS-0000589: 120 EUR valorados contra 171
del administrativo; los 51 que faltan son exactamente el incremento del
LER 170802, que SI estaba cargado en el contrato.

El contrato de este modulo (R21)
--------------------------------
``REGLAS_SINTETICAS_RESIDUOS`` es una lista de reglas con la firma::

    regla(*, ctx, base, contrato_lines) -> LineValuationDto | None

donde ``ctx`` es el ``ContextoLinea`` de la linea base, ``base`` su
``LineValuationDto`` y ``contrato_lines`` el catalogo de Sigrid. Una
regla devuelve la sintetica que toca emitir, o ``None`` si no aplica.

El RECORRIDO de las lineas base vive en el builder
(``_sinteticas_residuos_faltantes``) y NO sabe que reglas hay: itera la
lista. Ese es el punto de enganche de **F-006** (canon de vertedero),
que anadira su regla aqui sin tocar el builder.

Modulo PURO: sin red, sin BBDD, sin LLM. El catalogo LER es el
compartido (``ruesma_comun.ler``, R14): aqui no se redefine.

Nota de implementacion (desviacion documentada del design)
----------------------------------------------------------
El design situaba la fabrica del DTO (``_dto_red_residuos``) en
``valuation_builder.py``. No puede vivir alli: el builder importa este
modulo (las reglas y la guarda de R15), asi que un import en sentido
contrario cierra un ciclo. La fabrica vive aqui, junto a las reglas que
la usan, que ademas es lo que hace cierto R21: una regla nueva se
escribe ENTERA en este fichero.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from domain.models.valuation_envelope import LineValuationDto
from ruesma_comun.ler import normalizar_ler

from application.services.designacion_hormigon import normalizar_texto

logger = logging.getLogger(__name__)

#: ``rol_linea`` canonico de la sintetica del incremento por LER. Es el
#: mismo rol que usa el ``ModifierContractMatcher`` en su predicado.
ROL_INCREMENTO_RESIDUOS = "incremento_residuos"

#: ``modifier_source`` de la sintetica. YA existe en el ``Literal`` de
#: sv5 y en el record de sv6, asi que esta red NO estrena un valor nuevo
#: (los cinco sitios de docs/ARCHITECTURE.md regla 10 quedan intactos).
FUENTE_GESTION_RESIDUOS = "gestion_residuos"

#: Razon que lleva la sintetica cuando el contrato no tarifa ese LER
#: (R17). La linea se emite IGUAL, sin precio, para que el revisor lo
#: ponga a mano: un incremento invisible no se le reclama a nadie.
RAZON_SIN_TARIFA = "residuos_ler_sin_tarifa_en_contrato"

#: Grafia con la que Sigrid escribe estas lineas ("INCREMENTO LER
#: 170604 ..."). Se compara sobre el texto normalizado, asi que cubre
#: INCREMENTO / INCREMENTOS / INCREMENT. Si aparece otra grafia real, se
#: anade AQUI: es el unico sitio que decide que es un incremento.
_TOKENS_INCREMENTO = ("INCREMENT",)


def es_linea_incremento_ler(descripcion: str | None) -> str | None:
    """Codigo LER si la descripcion es una linea de INCREMENTO por LER.

    Devuelve el codigo (6 digitos, sin separadores) y no un booleano
    porque quien pregunta necesita saber DE QUE LER: un contrato tarifa
    varios incrementos y hay que casar el correcto.

    Exige las dos cosas: el token de incremento Y un LER que exista en
    el catalogo (``ruesma_comun.ler``). Con una sola no basta:

      * "MOVIMIENTO DE CONTENEDOR DE 6 M CUBICOS ..." nombra el
        contenedor que SI se factura;
      * "INCREMENTO POR GESTION DE RESIDUOS EN HORMIGON" es el recargo
        del hormigon, que no va por LER;
      * "INCREMENTO 192137" lleva seis digitos que NO son un LER (el
        capitulo 19 llega al subcapitulo 13); es el codigo de producto
        de Prebetong que ya provoco un bug real en sv2.
    """
    texto = normalizar_texto(descripcion)
    if not texto:
        return None
    if not any(token in texto for token in _TOKENS_INCREMENTO):
        return None
    return normalizar_ler(texto)


def tarifa_incremento_ler(contrato_lines: Any, codigo_ler: str | None):
    """Primera linea de contrato que tarifa el incremento de ESE LER.

    ``None`` si el contrato no lo tarifa — caso real y frecuente, que NO
    impide emitir la sintetica (R17).
    """
    ler = normalizar_ler(codigo_ler)
    if not ler or not contrato_lines:
        return None
    for cl in contrato_lines:
        if es_linea_incremento_ler(getattr(cl, "descripcion", None)) == ler:
            return cl
    return None


def dto_red_residuos(
    *,
    base: LineValuationDto,
    rol: str,
    descripcion: str,
    motivo: str,
    etiqueta: str,
    tarifa: Any,
) -> LineValuationDto:
    """DTO sintetico de la red de residuos (espejo de ``_dto_red_codigo``).

    Con tarifa: precio del contrato y ``match_method='semantic'``. Sin
    tarifa: se emite IGUAL, sin precio y con ``match_method='no_match'``
    — la "forma C" con la que ya trabajan las redes M1 y de codigo, no
    una divergencia de esta feature (R17).
    """
    logger.info(
        "[builder][red-residuos] base merge=%s %s tarifa=%s "
        "(IA3 tiene prohibido emitir sinteticas en residuos).",
        base.merge_line_id, etiqueta,
        "si" if tarifa is not None else "no",
    )
    return LineValuationDto(
        merge_line_id=None,
        line_kind="synthetic_modifier",
        parent_merge_line_id=base.merge_line_id,
        modifier_source=FUENTE_GESTION_RESIDUOS,
        modifier_reason=(
            f"Red determinista de residuos: {motivo}; IA3 no puede "
            "emitir sinteticas en residuos."
        ),
        descripcion_linea=descripcion,
        rol_linea=rol,
        match_method="semantic" if tarifa is not None else "no_match",
        matched_contrato_line_id=(
            tarifa.contrato_line_id if tarifa is not None else None
        ),
        match_confidence_pct=90.0 if tarifa is not None else 0.0,
        precio_unitario_contrato_db=(
            tarifa.precio_unitario if tarifa is not None else None
        ),
        razon_corta=(
            f"Incremento por {etiqueta} generado por red determinista "
            "de residuos"
            + (
                "" if tarifa is not None
                else "; el contrato no tarifa ese LER (importe a poner "
                     "por el revisor)"
            )
        ),
    )


def regla_incremento_ler(
    *,
    ctx: Any,
    base: LineValuationDto,
    contrato_lines: Any,
) -> LineValuationDto | None:
    """R16/R17 — el incremento que el contrato cobra por el codigo LER.

    Se emite SIEMPRE que la base traiga un LER valido, tarifado o no
    (decision del humano del 2026-08-22: "siempre debe crear la
    sintetica; ya pondra el revisor el importe a mano").
    """
    ler = normalizar_ler(getattr(ctx, "codigo_ler", None))
    if not ler:
        return None
    return dto_red_residuos(
        base=base,
        rol=ROL_INCREMENTO_RESIDUOS,
        descripcion=f"INCREMENTO LER {ler}",
        motivo=f"la linea base declara el LER {ler}",
        etiqueta=f"LER {ler}",
        tarifa=tarifa_incremento_ler(contrato_lines, ler),
    )


#: Reglas que producen las sinteticas de residuos. El recorrido de
#: lineas base (builder) itera esta lista y no conoce ninguna en
#: concreto: anadir una regla NO obliga a tocarlo (R21).
REGLAS_SINTETICAS_RESIDUOS: list[Callable[..., LineValuationDto | None]] = [
    regla_incremento_ler,
]
