# infrastructure/sigrid/obras_activas_cache.py
"""Cache TTL en memoria de la lista de obras activas (R3).

Una extraccion no puede costar una consulta a Sigrid: dentro del TTL, N
albaranes producen UNA sola llamada. La cache es por replica (las
replicas KEDA arrancan frias: una llamada por arranque y otra por
expiracion; la query es barata).

Si al expirar el proveedor no devuelve nada, se sirve la lista VIEJA
(stale) antes que quedarse sin lista: una lista de hace seis horas y
media sigue siendo mejor que dejar a la IA inventarse el codigo.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from domain.ports.obras_activas_provider import ObraActiva, ObrasActivasProvider

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[obras-activas][cache]"


class ObrasActivasCacheTTL(ObrasActivasProvider):
    def __init__(
        self,
        provider: ObrasActivasProvider,
        *,
        ttl_s: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._provider = provider
        self._ttl_s = float(ttl_s)
        self._clock = clock
        self._valor: list[ObraActiva] | None = None
        self._obtenido_en: float | None = None

    def obtener(self) -> list[ObraActiva] | None:
        ahora = self._clock()
        if self._obtenido_en is not None and (
            ahora - self._obtenido_en <= self._ttl_s
        ):
            return list(self._valor) if self._valor is not None else None

        try:
            nuevo = self._provider.obtener()
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s el proveedor fallo; se sirve lo cacheado si lo hay.",
                _LOG_PREFIX,
            )
            nuevo = None

        if nuevo is None:
            if self._valor is not None:
                logger.warning(
                    "%s sin lista nueva: se sirve la anterior (%s obras).",
                    _LOG_PREFIX, len(self._valor),
                )
                return list(self._valor)
            return None

        self._valor = list(nuevo)
        self._obtenido_en = ahora
        logger.info(
            "%s lista refrescada: %s obras (ttl_s=%s).",
            _LOG_PREFIX, len(self._valor), self._ttl_s,
        )
        return list(self._valor)
