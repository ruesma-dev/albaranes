# domain/ports/sigrid_alta_port.py
"""Puerto de sigrid-api para sv9: SOLO estas cuatro operaciones (R33).

- ``buscar_albaranes`` y ``existe_concepto``: ``POST /api/sql/read``.
- ``alta_albaran``: ``POST /api/sigrid/albaran`` en modo extendido (contrato
  §2). Devuelve la respuesta del 200 o el fallo, nunca lanza por un 4xx/5xx,
  un tiempo agotado o un fallo de conexión: el estado lo decide el
  clasificador. Con ``commit=True`` (grabación) no se reintenta nunca (R20).
- ``adjuntar_pdf``: ``POST /api/sigrid/concepto-grafico`` (R22).

Nunca ``sql/write``, ni el modo clásico, ni ``albaran-directo``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models.alta_models import (
    AlbaranSigrid,
    ErrorAlta,
    PeticionAlbaran,
    RespuestaAlta,
    ResultadoAdjunto,
)


class SigridAltaPort(ABC):
    @abstractmethod
    def buscar_albaranes(
        self, cif: str, referencia: str, referencia_externa: str,
    ) -> list[AlbaranSigrid]:
        """Albaranes de compra (``con.tip`` 14) con ese CIF y esa referencia
        del proveedor y otro ``synckey`` que ``referencia_externa`` (R14)."""

    @abstractmethod
    def existe_concepto(self, ide: int) -> bool:
        """¿Sigue en Sigrid el albarán de compra ``con.ide``? (R28)."""

    @abstractmethod
    def alta_albaran(self, peticion: PeticionAlbaran, commit: bool) -> RespuestaAlta | ErrorAlta:
        """Previa (``commit=False``) o grabación única (``commit=True``)."""

    @abstractmethod
    def adjuntar_pdf(self, con_ide: int, nombre: str, contenido: bytes) -> ResultadoAdjunto:
        """Cuelga el PDF del albarán registrado (``contip`` 14, ``gratipide`` 0)."""
