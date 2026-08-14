# domain/ports/obras_activas_provider.py
"""Puerto de la lista de OBRAS ACTIVAS que se inyecta en el prompt de IA1.

La primera fase de extracción se inventaba códigos de obra (caso de
referencia: 0937). Darle la lista cerrada de obras y prohibirle salirse
de ella convierte el problema en uno de elección, no de invención.

``None`` significa «lista NO disponible en esta ejecución» (proveedor
apagado, sin credenciales, error de sigrid-api o lista vacía) y NO es un
error: la extracción sigue exactamente como antes (R2).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ObraActiva:
    """Una obra tal y como se le presenta a la IA: código y nombre."""

    codigo: str
    nombre: str | None


class ObrasActivasProvider(Protocol):
    def obtener(self) -> list[ObraActiva] | None: ...
