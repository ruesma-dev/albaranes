# domain/ports/alta_repository.py
"""Puerto de la BBDD de albaranes para sv9 (design §3).

sv9 lee merge y valoración y es el ÚNICO que escribe ``albaran_altas_sigrid``
(R34). ``reclamar`` hace R5–R8 en una transacción con la fila del merge
bloqueada (``FOR UPDATE``): lee el documento y el alta, decide con
``domain.services.reclamacion.decidir`` y, si procede, deja el alta en
``en_curso`` (o en ``incierto``, R8) antes de soltar el cerrojo.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from domain.models.alta_models import (
    AccionAlta,
    AltaActual,
    DatosAlta,
    Reclamacion,
    ResultadoAlta,
)


class AltaRepository(ABC):
    @abstractmethod
    def reclamar(
        self,
        document_id: str,
        *,
        accion: AccionAlta,
        ahora: datetime,
        desde: datetime,
        espera: timedelta,
        modo: str,
    ) -> Reclamacion:
        """R5–R8, en una transacción con el merge ``FOR UPDATE``."""

    @abstractmethod
    def leer_datos(self, document_id: str) -> DatosAlta:
        """Cabecera (merge + valoración) y líneas valoradas del documento."""

    @abstractmethod
    def guardar(self, document_id: str, resultado: ResultadoAlta, *, ahora: datetime) -> None:
        """Escribe el resultado y apunta ``{ts, estado, cod, motivos}`` en el historial."""

    @abstractmethod
    def leer_alta(self, document_id: str) -> AltaActual | None:
        """La fila del alta, o ``None`` si no hay."""
