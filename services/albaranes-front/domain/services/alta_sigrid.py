# domain/services/alta_sigrid.py
"""¿Ofrece sv4 «Solicitar alta en Sigrid» o «Reintentar adjunto»? (F-053 R30).
Puro, sin E/S.

Un documento aprobado, activo y con ``approved_at_utc`` ≥ DESDE, cuyo alta
falta, está en un estado repetible (``no_admitido``, ``revisar``, ``error``,
``simulado``, ``anulado``) o lleva en ``incierto``/``en_curso`` más que la
Espera desde el último intento. Las reglas de estado y de Espera son las de
``ruesma_comun.alta_sigrid``, las mismas con las que sv9 decide si procesa
(R5–R8): si sv4 ofrece el botón, sv9 no ignorará el mensaje.

«Reintentar adjunto» (v8, O1 = a; R23): mismas condiciones del documento y un
alta ``registrado`` en modo ``real`` cuyo PDF no está colgado. Publica
``accion="alta"``, que sv9 trata como ``solo_adjunto`` (R7).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from ruesma_comun.alta_sigrid import (
    ESTADOS_ALTA_REPETIBLES,
    espera_pasada,
    leer_instante_utc,
)

from domain.models.alta_sigrid_models import AltaSigridVista, ConfigAltaSigrid

#: Estados en los que la grabación pudo quedarse a medias: solo tras la Espera.
ESTADOS_TRAS_LA_ESPERA = frozenset({"en_curso", "incierto"})

#: F-077 R14: fases del panel «Alta en Sigrid» de la ficha.
FASE_EN_CURSO = "en_curso"
FASE_SIN_RESPUESTA = "sin_respuesta"
FASE_RESULTADO = "resultado"

#: F-077 R14 (decisión del humano en la PARADA 1: «la escritura en Sigrid es
#: rápida»): sin respuesta de sv9 en este tiempo desde la aprobación, error de
#: tiempo. Constante de dominio: nadie ha pedido ajustarla.
TOPE_RESPUESTA_ALTA = timedelta(minutes=5)


def _instante(texto: str | None) -> datetime | None:
    try:
        return leer_instante_utc(texto)
    except ValueError:
        return None


def _documento_admite_alta(
    *, aprobado: bool, activo: bool, approved_at_utc: str | None, config: ConfigAltaSigrid,
) -> bool:
    """Feature activa y documento aprobado, activo y aprobado desde DESDE (R6)."""
    if not config.activa or not aprobado or not activo:
        return False
    aprobado_en = _instante(approved_at_utc)
    return not (aprobado_en is None or config.desde is None or aprobado_en < config.desde)


def puede_solicitar_alta(
    *,
    aprobado: bool,
    activo: bool,
    approved_at_utc: str | None,
    alta: AltaSigridVista | None,
    config: ConfigAltaSigrid,
    ahora: datetime,
) -> bool:
    if not _documento_admite_alta(aprobado=aprobado, activo=activo,
                                  approved_at_utc=approved_at_utc, config=config):
        return False
    if alta is None or alta.estado in ESTADOS_ALTA_REPETIBLES:
        return True
    if alta.estado in ESTADOS_TRAS_LA_ESPERA:
        return espera_pasada(_instante(alta.ultimo_intento_at_utc), ahora, config.espera)
    return False


def puede_reintentar_adjunto(
    *,
    aprobado: bool,
    activo: bool,
    approved_at_utc: str | None,
    alta: AltaSigridVista | None,
    config: ConfigAltaSigrid,
) -> bool:
    if not _documento_admite_alta(aprobado=aprobado, activo=activo,
                                  approved_at_utc=approved_at_utc, config=config):
        return False
    return (
        alta is not None
        and alta.estado == "registrado"
        and alta.modo == "real"
        and alta.adjunto_estado != "colgado"
    )


def fase_alta(
    *,
    aprobado: bool,
    activo: bool,
    approved_at_utc: str | None,
    alta: AltaSigridVista | None,
    config: ConfigAltaSigrid,
    ahora: datetime,
) -> str:
    """F-077 R14: ¿está sv9 procesando el alta de la aprobación vigente?

    Esperando = el documento admite alta (R6) y, o no hay fila, o la fila es de
    una aprobación anterior (instante nulo, ilegible o anterior al del merge)
    en un estado que sv9 vuelve a procesar (``ESTADOS_ALTA_REPETIBLES``), o es
    de la vigente (mismo instante) y sigue ``en_curso``. Esperando y dentro del
    tope => ``en_curso``; pasado el tope => ``sin_respuesta``. En cualquier otro
    caso la fila es la respuesta (``resultado``): también una anterior en
    ``ya_en_sigrid``, ``registrado`` o ``incierto``, porque sv9 ignora la
    aprobación nueva (F-053 R7) y la ficha no se quedaría nunca «en curso».
    Los instantes se comparan como instantes UTC, no como texto.
    """
    if not _documento_admite_alta(aprobado=aprobado, activo=activo,
                                  approved_at_utc=approved_at_utc, config=config):
        return FASE_RESULTADO
    aprobado_en = _instante(approved_at_utc)
    if alta is None:
        esperando = True
    else:
        de_la_alta = _instante(alta.approved_at_utc)
        if de_la_alta is None or de_la_alta < aprobado_en:
            esperando = alta.estado in ESTADOS_ALTA_REPETIBLES
        else:
            esperando = de_la_alta == aprobado_en and alta.estado == "en_curso"
    if not esperando:
        return FASE_RESULTADO
    if ahora - aprobado_en < TOPE_RESPUESTA_ALTA:
        return FASE_EN_CURSO
    return FASE_SIN_RESPUESTA


def motivos_linea_vista(
    alta: AltaSigridVista | None, posiciones: dict[int, int],
) -> list[dict[str, str]]:
    """F-077 R24, R25: los motivos de línea del alta que no tienen fila en la
    tabla del panel, listos para pintar: ``linea`` («Línea N» con la posición de
    esa línea valorada en la ficha, o «Línea (ref. X)» si no está), ``texto``,
    ``detalle`` y ``codigo``. ``referencia_linea`` es el id de la línea valorada."""
    if alta is None:
        return []
    vista: list[dict[str, str]] = []
    for motivo in alta.motivos_linea_sueltos:
        referencia = str(motivo.get("referencia_linea"))
        try:
            posicion = posiciones.get(int(referencia))
        except ValueError:
            posicion = None
        vista.append({
            "linea": f"Línea {posicion}" if posicion is not None else f"Línea (ref. {referencia})",
            "texto": motivo["texto"],
            "detalle": str(motivo.get("detalle") or ""),
            "codigo": str(motivo.get("codigo") or ""),
        })
    return vista
