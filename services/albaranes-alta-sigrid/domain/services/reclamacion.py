# domain/services/reclamacion.py
"""Qué hace sv9 con un mensaje de ``q-feedback`` (F-053, R5–R8, R23, R28).

Puro: lo llama el repositorio DENTRO de la transacción que bloquea la fila del
merge (``FOR UPDATE``), con lo que acaba de leer del documento y del alta.

- R6: DESDE vacía, documento inexistente, en la papelera, no aprobado o
  aprobado antes de DESDE ⇒ ``ignorar`` (se confirma sin tocar nada).
- ``verificar_anulacion`` (R28): solo si el alta está ``registrado``.
- ``alta``:
  - sin alta, o en ``no_admitido``/``revisar``/``error``/``simulado``/``anulado``
    ⇒ ``procesar`` (R5);
  - ``ya_en_sigrid`` ⇒ ``ignorar`` (R7);
  - ``registrado``: con el adjunto colgado ⇒ ``ignorar`` (R7); si no,
    ``solo_adjunto`` (R23);
  - ``en_curso``/``incierto`` sin pasar la Espera desde el último intento ⇒
    ``ignorar`` (R7); pasada, ``en_curso`` ⇒ ``a_incierto`` (R8) e
    ``incierto`` ⇒ ``procesar`` (se retoma con la misma petición, R15).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from ruesma_comun.alta_sigrid import ESTADOS_ALTA_REPETIBLES, espera_pasada

from domain.models.alta_models import (
    AccionAlta,
    AdjuntoEstado,
    AltaActual,
    Decision,
    EstadoAlta,
    EstadoDocumento,
    Reclamacion,
)

#: Los mismos que ofrece sv4 para «Solicitar alta» (R30): ``comun``.
_REPETIBLES = frozenset(EstadoAlta(e) for e in ESTADOS_ALTA_REPETIBLES)


def paso_la_espera(alta: AltaActual, ahora: datetime, espera: timedelta) -> bool:
    """Sin último intento conocido, la Espera se da por pasada. La regla es
    la de ``comun`` (``espera_pasada``), la misma con la que sv4 ofrece
    «Solicitar alta» (R30)."""
    return espera_pasada(alta.ultimo_intento_at_utc, ahora, espera)


def _motivo_r6(documento: EstadoDocumento | None, desde: datetime | None) -> str:
    if desde is None:
        return "ALTA_SIGRID_DESDE_UTC vacía: feature apagada"
    if documento is None:
        return "el documento no existe"
    if not documento.activo:
        return "el documento está en la papelera"
    if not documento.aprobado:
        return "el documento no está aprobado"
    if documento.approved_at_utc is None or documento.approved_at_utc < desde:
        return "aprobado antes de ALTA_SIGRID_DESDE_UTC"
    return ""


def decidir(
    documento: EstadoDocumento | None,
    alta: AltaActual | None,
    *,
    accion: AccionAlta,
    ahora: datetime,
    desde: datetime | None,
    espera: timedelta,
) -> Reclamacion:
    motivo = _motivo_r6(documento, desde)
    if motivo:
        return Reclamacion(Decision.IGNORAR, alta, motivo)

    if accion is AccionAlta.VERIFICAR_ANULACION:
        if alta is not None and alta.estado is EstadoAlta.REGISTRADO:
            return Reclamacion(Decision.VERIFICAR_ANULACION, alta)
        return Reclamacion(Decision.IGNORAR, alta, "verificar anulación de un alta no registrada")

    if alta is None or alta.estado in _REPETIBLES:
        return Reclamacion(Decision.PROCESAR, alta)
    if alta.estado is EstadoAlta.YA_EN_SIGRID:
        return Reclamacion(Decision.IGNORAR, alta, "ya estaba en Sigrid")
    if alta.estado is EstadoAlta.REGISTRADO:
        if alta.adjunto_estado is AdjuntoEstado.COLGADO:
            return Reclamacion(Decision.IGNORAR, alta, "registrado con el adjunto colgado")
        return Reclamacion(Decision.SOLO_ADJUNTO, alta)
    # en_curso / incierto
    if not paso_la_espera(alta, ahora, espera):
        return Reclamacion(Decision.IGNORAR, alta, f"{alta.estado} sin pasar la Espera")
    if alta.estado is EstadoAlta.EN_CURSO:
        return Reclamacion(Decision.A_INCIERTO, alta, "en_curso pasada la Espera")
    return Reclamacion(Decision.PROCESAR, alta)
