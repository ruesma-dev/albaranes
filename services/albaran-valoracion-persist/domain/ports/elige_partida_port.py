# domain/ports/elige_partida_port.py
"""Puerto de la IA que elige la partida de residuos entre las candidatas (F-111).

Lo implementa ``infrastructure.clients.http_partida_residuos_client`` contra
``POST /v1/albaranes/partida-residuos`` de sv5. Contrato: UNA llamada por
documento con todas sus líneas de residuos con 2 o más candidatas (R34);
devuelve ``line_ref`` ⇒ código elegido (``None`` = la IA no eligió). Puede
lanzar: quien lo usa (``AsignadorPartidaResiduos``) lo convierte en revisión
con ``partida_residuos_ia_fallo`` (R26) y nunca en almacén.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class EligePartidaPort(Protocol):
    def elegir(
        self,
        *,
        document_id: str,
        lineas: list[dict[str, Any]],
        candidatas: list[dict[str, Any]],
    ) -> dict[int, str | None]: ...
