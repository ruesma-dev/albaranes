# infrastructure/sigrid/obras_activas_cache.py
"""Cache TTL en memoria de la lista de obras (R3 de F-002; F-048, D5).

Una extraccion no puede costar una consulta a Sigrid: dentro del TTL, N
albaranes producen UNA sola llamada. La cache es por replica (las
replicas KEDA arrancan frias: una llamada por arranque y otra por
expiracion; la query es barata).

Si al expirar el proveedor no devuelve nada, se sirve la lista VIEJA
(stale) antes que quedarse sin lista: una lista de hace seis horas y
media sigue siendo mejor que dejar a la IA inventarse el codigo.

(F-048, D5) Lo que se cachea es el CATALOGO entero —las obras activas del
prompt y TODAS las obras con contrato, contra las que se valida el codigo
del correo—, que salen de la MISMA consulta: ``obtener()`` y
``obtener_todas()`` comparten la entrada, la TTL y la politica de lista
vieja. Con un proveedor que solo sepa ``obtener()`` (los dobles de F-002),
el catalogo lleva ``todas = None``.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from domain.ports.obras_activas_provider import (
    CatalogoObras,
    ObraActiva,
    ObrasActivasProvider,
)

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
        self._valor: CatalogoObras | None = None
        self._obtenido_en: float | None = None

    def obtener(self) -> list[ObraActiva] | None:
        """Las obras activas (las del prompt), como en F-002."""
        catalogo = self._catalogo()
        if catalogo is None or not catalogo.activas:
            return None
        return list(catalogo.activas)

    def obtener_todas(self) -> list[ObraActiva] | None:
        """TODAS las obras con contrato; ``None`` si el proveedor no las da."""
        catalogo = self._catalogo()
        if catalogo is None or catalogo.todas is None:
            return None
        return list(catalogo.todas)

    def _catalogo(self) -> CatalogoObras | None:
        ahora = self._clock()
        if self._obtenido_en is not None and (
            ahora - self._obtenido_en <= self._ttl_s
        ):
            return self._valor

        try:
            nuevo = self._pedir_catalogo()
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
                    _LOG_PREFIX, len(self._valor.activas),
                )
            return self._valor

        self._valor = nuevo
        self._obtenido_en = ahora
        logger.info(
            "%s lista refrescada: %s obras activas, %s en total (ttl_s=%s).",
            _LOG_PREFIX, len(nuevo.activas),
            len(nuevo.todas) if nuevo.todas is not None else "?",
            self._ttl_s,
        )
        return nuevo

    def _pedir_catalogo(self) -> CatalogoObras | None:
        """El catalogo del proveedor; si solo sabe ``obtener()``, sin ``todas``."""
        obtener_catalogo = getattr(self._provider, "obtener_catalogo", None)
        if obtener_catalogo is not None:
            return obtener_catalogo()
        activas = self._provider.obtener()
        if activas is None:
            return None
        return CatalogoObras(activas=tuple(activas), todas=None)
