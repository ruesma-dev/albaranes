# domain/services/alta_sigrid.py
"""¿Ofrece sv4 «Solicitar alta en Sigrid»? (F-053 R30). Puro, sin E/S.

Un documento aprobado, activo y con ``approved_at_utc`` ≥ DESDE, cuyo alta
falta, está en un estado repetible (``no_admitido``, ``revisar``, ``error``,
``simulado``, ``anulado``) o lleva en ``incierto``/``en_curso`` más que la
Espera desde el último intento. Las reglas de estado y de Espera son las de
``ruesma_comun.alta_sigrid``, las mismas con las que sv9 decide si procesa
(R5–R8): si sv4 ofrece el botón, sv9 no ignorará el mensaje.
"""
from __future__ import annotations

from datetime import datetime

from ruesma_comun.alta_sigrid import (
    ESTADOS_ALTA_REPETIBLES,
    espera_pasada,
    leer_instante_utc,
)

from domain.models.alta_sigrid_models import AltaSigridVista, ConfigAltaSigrid

#: Estados en los que la grabación pudo quedarse a medias: solo tras la Espera.
ESTADOS_TRAS_LA_ESPERA = frozenset({"en_curso", "incierto"})


def _instante(texto: str | None) -> datetime | None:
    try:
        return leer_instante_utc(texto)
    except ValueError:
        return None


def puede_solicitar_alta(
    *,
    aprobado: bool,
    activo: bool,
    approved_at_utc: str | None,
    alta: AltaSigridVista | None,
    config: ConfigAltaSigrid,
    ahora: datetime,
) -> bool:
    if not config.activa or not aprobado or not activo:
        return False
    aprobado_en = _instante(approved_at_utc)
    if aprobado_en is None or config.desde is None or aprobado_en < config.desde:
        return False
    if alta is None or alta.estado in ESTADOS_ALTA_REPETIBLES:
        return True
    if alta.estado in ESTADOS_TRAS_LA_ESPERA:
        return espera_pasada(_instante(alta.ultimo_intento_at_utc), ahora, config.espera)
    return False
