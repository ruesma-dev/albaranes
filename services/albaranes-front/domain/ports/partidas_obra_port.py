# domain/ports/partidas_obra_port.py
"""Puerto de la lista de partidas de una obra en sv4 (F-098).

Lo implementa ``ruesma_comun.sigrid.CachePartidasObra`` (caché por réplica
sobre el lector de sigrid-api, ``app.py``), como el de sv6 (F-076). Contrato:

- ``lista(obra)``: la lista con hojas o ``None`` (sin obra, consulta fallida o
  truncada, 0 hojas); nunca lanza. La usa la ficha (``ReviewService``).
- ``consultar(obra)``: ``(lista, ok)``; la usa el selector
  (``/api/sigrid/partidas``) para distinguir «sin partidas» de «no se pudo
  leer». Nunca lanza.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ruesma_comun.sigrid import ListaPartidasObra


@runtime_checkable
class PartidasObraPort(Protocol):
    def lista(self, obra: str | None) -> ListaPartidasObra | None: ...

    def consultar(self, obra: str | None) -> tuple[ListaPartidasObra | None, bool]: ...
