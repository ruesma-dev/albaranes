# domain/ports/obra_merge_repository_port.py
from __future__ import annotations

from typing import Protocol


class ObraMergeRepository(Protocol):
    """Puerto mínimo para el servicio de enriquecimiento.

    ``SqlAlchemyAlbaranRepository`` lo cumple por duck-typing al exponer
    estos métodos. No hace falta herencia explícita.

    (ago 2026, F-002) Ampliado con la RED DE OBRA: una obra que la IA se
    inventa (caso 0937) no puede quedar persistida como si existiera. El
    servicio necesita poder DESCARTARLA dejando el documento a revisión, y
    RETIRAR ese aviso cuando un re-enriquecimiento posterior la valide.
    """

    def get_merge_obra_codigo(self, *, document_id: str) -> str | None: ...

    def update_merge_obra_fields(
        self,
        *,
        document_id: str,
        obra_nombre: str | None,
        obra_direccion: str | None,
    ) -> None: ...

    def descartar_obra_no_valida(
        self,
        *,
        document_id: str,
        codigo_leido: str | None,
        motivo: str,
    ) -> None:
        """Deja el merge SIN obra y marcado a revisión.

        ``obra_codigo`` y ``obra_codigo_origen`` pasan a NULL; se añade
        ``motivo`` a ``review_reasons_json`` (sin duplicar) y una nota con
        prefijo ``[AVISO] Obra``. ``obra_nombre`` / ``obra_direccion``
        leídos NO se borran: ayudan al revisor a localizar la obra buena.
        """
        ...

    def retirar_revision_obra(self, *, document_id: str) -> None:
        """Quita la nota ``[AVISO] Obra`` y los motivos ``obra_*``.

        ``review_required`` NO se recalcula: puede haber otros motivos
        vivos y el cierre de la revisión es del revisor (decisión D7).
        """
        ...
