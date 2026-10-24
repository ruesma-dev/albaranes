# domain/ports/sigrid_alta_port.py
"""Puerto de sigrid-api para sv9: SOLO estas siete operaciones (R33).

- ``buscar_albaranes``, ``existe_concepto``, ``buscar_usuario`` (v8, R47),
  ``buscar_empleados_por_correo`` y ``empleado_de_alta`` (F-069, R9–R10):
  ``POST /api/sql/read``.
- ``alta_albaran``: ``POST /api/sigrid/albaran`` en modo extendido (contrato
  §2). Devuelve la respuesta del 200 o el fallo, nunca lanza por un 4xx/5xx,
  un tiempo agotado o un fallo de conexión: el estado lo decide el
  clasificador. Con ``commit=True`` (grabación) no se reintenta nunca (R20).
- ``adjuntar_pdf``: ``POST /api/sigrid/concepto-grafico`` (R22), con el
  ``usu`` de la petición del documento (v8).

Nunca ``sql/write``, ni el modo clásico, ni ``albaran-directo``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.models.alta_models import (
    AlbaranSigrid,
    EmpleadoSigrid,
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
        del proveedor (comparada normalizada, v8) y otro ``synckey`` que
        ``referencia_externa`` (R14)."""

    @abstractmethod
    def existe_concepto(self, ide: int) -> bool:
        """¿Sigue en Sigrid el albarán de compra ``con.ide``? (R28)."""

    @abstractmethod
    def buscar_usuario(self, cod: str) -> str | None:
        """El ``cod`` de ``dbo.usu`` que casa con ``cod`` (el de Sigrid, no el
        pedido), o ``None`` si no existe (R47). Lanza si la lectura falla
        tras los reintentos (R24, R48)."""

    @abstractmethod
    def buscar_empleados_por_correo(self, correo: str) -> list[EmpleadoSigrid]:
        """Los de ``dbo.emp`` cuyo ``traele`` (recortado y en minúsculas) es
        ``correo``, los de alta primero y como mucho tres (F-069 R10). Lanza si
        la lectura falla tras los reintentos (R13)."""

    @abstractmethod
    def empleado_de_alta(self, ide: int) -> bool:
        """¿Es ``ide`` un empleado de alta de ``dbo.emp``? (F-069 R9). Lanza si
        la lectura falla tras los reintentos (R13)."""

    @abstractmethod
    def alta_albaran(self, peticion: PeticionAlbaran, commit: bool) -> RespuestaAlta | ErrorAlta:
        """Previa (``commit=False``) o grabación única (``commit=True``)."""

    @abstractmethod
    def adjuntar_pdf(
        self, con_ide: int, nombre: str, contenido: bytes, *, usu: str,
    ) -> ResultadoAdjunto:
        """Cuelga el PDF del albarán registrado (``contip`` 14, ``gratipide`` 0)
        a nombre de ``usu`` (el de la petición, R22)."""
