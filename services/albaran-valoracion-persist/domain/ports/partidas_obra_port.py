# domain/ports/partidas_obra_port.py
"""Puerto de la lista de partidas de una obra (F-076).

Lo implementa ``ruesma_comun.sigrid.CachePartidasObra`` (caché por réplica
sobre el lector de sigrid-api). Contrato: ``None`` = no hay lista (obra
vacía, sin configuración, consulta fallida o truncada, obra con 0 hojas) y
nunca lanza: quien lo usa valora como siempre (R11).
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ruesma_comun.sigrid import ListaPartidasObra


@runtime_checkable
class PartidasObraPort(Protocol):
    def lista(self, obra: str | None) -> ListaPartidasObra | None: ...
