# application/services/fecha_recepcion.py
"""Fecha de recepción del correo como referencia del AÑO del albarán (F-112).

En producción, 19 de 158 albaranes (12 %) tenían la fecha a más de un año de
su correo: IA1 leía mal la última cifra del año (o lo sacaba del «R.D.
553/2020» impreso) e IA2 lo confirmaba. F-112 le da a las dos IAs el día en
que el albarán llegó al buzón para que lean mejor el año. **La fecha la lee
la IA**: nada en sv2 corrige ``cabecera.fecha``; esto solo pinta texto.

- ``fecha_recepcion_de``: el día de ``ContextoCorreo.recibido_utc`` en
  Europe/Madrid (D2 = b; un correo de las 23:30 UTC del 31-12 es del 01-01).
- ``render_fecha_recepcion``: el bloque de ``{fecha_recepcion}`` (task de IA1).
- ``render_revision_fecha``: el bloque de ``{revision_fecha}`` (prompts de IA2).

La Regla del año vive en UNA constante (``REGLA_DEL_ANIO``) que usan los dos
bloques, con cualquier fecha (R28): el cambio de año no es solo cosa de enero.

Seguridad (R5): al prompt solo llega ``date.isoformat()`` de una fecha ya
validada; ningún otro carácter de ``recibido_utc``.

Puro: sin I/O. ``ZoneInfo`` necesita ``tzdata`` en Windows y en el contenedor
(R30, ``infra/manifests/sv2/requirements.txt``).
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from ruesma_comun.correo import ContextoCorreo

#: Marcador del task de fase 1 (IA1).
MARCADOR_FECHA_RECEPCION = "{fecha_recepcion}"

#: Marcador de los cuatro prompts de fase 2 (IA2).
MARCADOR_REVISION_FECHA = "{revision_fecha}"

#: Zona en la que se cuenta el día de recepción (D2 = b).
ZONA_RECEPCION = ZoneInfo("Europe/Madrid")

#: La Regla del año: la MISMA para IA1 e IA2 y para cualquier fecha (R28).
REGLA_DEL_ANIO = (
    "La fecha de un albarán es IGUAL o algo ANTERIOR a la de recepción (días o semanas), "
    "nunca muy posterior. NO es «el año del correo»: es el año que deja el día y el mes "
    "del papel en la recepción o poco antes. Si el día y el mes del papel caen DESPUÉS "
    "del día y el mes de la recepción, el año es el ANTERIOR al de la recepción "
    "(28-12 con correo del 03-01 ⇒ el año anterior; 02-01 con correo del 05-01 ⇒ el "
    "mismo año). Si el papel trae un año legible y plausible (la fecha queda entre un "
    "año antes de la recepción y pocos días después), ese año manda: no inventes otro. "
    "El año NUNCA sale de una referencia normativa impresa (R.D. 553/2020, Orden, Ley, "
    "norma): es el de la fecha del documento. Si el año que lees no es plausible, "
    "vuelve a mirarlo: casi siempre es una cifra mal leída (la última, sobre todo); si "
    "aun así el papel dice sin ninguna duda ese año, devuélvelo tal cual."
)

#: Texto de ``{fecha_recepcion}`` sin fecha de recepción (R4).
NOTA_SIN_RECEPCION = (
    "(Sin fecha de recepción del correo en esta ejecución: lee la fecha solo "
    "del papel, como siempre.)"
)

#: Texto de ``{revision_fecha}`` sin fecha de recepción (R18).
NOTA_REVISION_SIN_RECEPCION = (
    "(Sin fecha de recepción del correo: revisa cabecera.fecha solo contra el "
    "papel, como siempre.)"
)


def fecha_recepcion_de(correo: ContextoCorreo | None) -> date | None:
    """Día de recepción del correo en Europe/Madrid, o ``None`` (R1, R2).

    ``recibido_utc`` es el ``receivedDateTime`` de Graph: fecha-hora ISO con
    ``Z`` o con desfase; sin zona se toma como UTC. Una fecha sola se
    devuelve tal cual. Cualquier otra cosa (vacío, texto, una fecha con algo
    detrás) da ``None``: sin referencia, como hoy, y sin excepción.
    """
    if correo is None:
        return None
    texto = getattr(correo, "recibido_utc", None)
    if not isinstance(texto, str) or not texto.strip():
        return None
    texto = texto.strip()
    try:
        if len(texto) == 10:
            return date.fromisoformat(texto)
        instante = datetime.fromisoformat(texto)
    except ValueError:
        return None
    if instante.tzinfo is None:
        instante = instante.replace(tzinfo=timezone.utc)
    return instante.astimezone(ZONA_RECEPCION).date()


def render_fecha_recepcion(fecha: date | None) -> str:
    """Bloque de ``{fecha_recepcion}`` para el task de IA1 (R3, R4, R5)."""
    if fecha is None:
        return NOTA_SIN_RECEPCION
    return (
        f"FECHA DE RECEPCIÓN DEL CORREO: {fecha.isoformat()}. Es el día en que este "
        "albarán llegó al buzón, NO la fecha del albarán. Úsala SOLO para leer el AÑO "
        f"de cabecera.fecha. {REGLA_DEL_ANIO}\n"
        "El día y el mes salen SIEMPRE del papel. Si el papel no trae fecha, "
        "cabecera.fecha es null: NUNCA copies esta fecha como fecha del albarán."
    )


def render_revision_fecha(fecha: date | None) -> str:
    """Bloque de ``{revision_fecha}`` para los prompts de IA2 (R17, R18)."""
    if fecha is None:
        return NOTA_REVISION_SIN_RECEPCION
    return (
        f"FECHA DE RECEPCIÓN DEL CORREO: {fecha.isoformat()}. Revisa SIEMPRE "
        "cabecera.fecha de la fase 1 contra el documento y contra esta fecha, sea cual "
        f"sea la familia y aunque nada más cambie. {REGLA_DEL_ANIO}\n"
        "Si la fecha de fase 1 no cumple esa regla y el papel admite el año correcto, "
        "corrige SOLO el año (día y mes, los del papel) y añade un razonamiento con "
        'campo "cabecera.fecha" y patron_aplicado "anio_fecha_recepcion". Si la fase 1 '
        "leyó mal el día o el mes, corrígelos con lo que diga el papel. Si el papel trae "
        "un año legible y plausible, no lo toques. Nunca pongas la fecha de recepción "
        "como fecha del albarán."
    )
