# domain/models/alta_sigrid_models.py
"""Alta en Sigrid vista desde sv4 (F-053, R1–R4, R25–R31, R37, R40–R41).

sv4 **lee** ``albaran_altas_sigrid`` (la escribe solo sv9, R34) para:

- bloquear el documento mientras el alta sea bloqueante (R25, R26): las
  operaciones que escriben lanzan :class:`AlbaranBloqueadoError` dentro de su
  transacción, con el merge bloqueado, y el portal lo traduce a 409 o a un
  aviso, sin cambiar nada;
- no aprobar lo no valorado (R37, :class:`AlbaranSinValorarError`);
- pintar el panel del alta, el estado en el listado y el producto de cada
  línea (R29–R31, R40).

La configuración (:class:`ConfigAltaSigrid`) lleva DESDE, la Espera y el mapeo
de productos con el MISMO valor que sv9 (design §7). DESDE vacía = feature
apagada: sv4 se comporta como antes de F-053 (R3), salvo R37, que vale siempre.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field, computed_field

from ruesma_comun.alta_sigrid import (
    ESTADOS_ALTA_BLOQUEANTES,
    MAPEO_PRODUCTO_POR_DEFECTO,
    nombre_producto,
    productos_admitidos,
)

#: R37: aviso al intentar aprobar un albarán no valorado.
AVISO_SIN_VALORAR = "No se puede aprobar un albarán sin valorar"

#: R4: la aprobación se mantiene, pero el alta no se pidió.
AVISO_ALTA_NO_PEDIDA = (
    "el alta en Sigrid no se pudo pedir: pulsa «Solicitar alta en Sigrid» en la ficha"
)


#: R29, R31: cómo se lee cada estado del alta en el portal.
ETIQUETAS_ESTADO_ALTA: dict[str, str] = {
    "en_curso": "En curso",
    "no_admitido": "No admitido",
    "ya_en_sigrid": "Ya estaba en Sigrid",
    "simulado": "Simulado (no grabado)",
    "revisar": "A revisar",
    "error": "Error",
    "incierto": "Incierto (pendiente de confirmar)",
    "registrado": "Registrado en Sigrid",
    "anulado": "Anulado",
}


def etiqueta_estado_alta(estado: str | None) -> str | None:
    """Texto del estado; uno desconocido se enseña tal cual."""
    if estado is None:
        return None
    return ETIQUETAS_ESTADO_ALTA.get(estado, estado)


def aviso_bloqueo(cod: str | None) -> str:
    """R25: «Registrado en Sigrid como {cod}: corrígelo en Sigrid y pulsa
    "Ya lo he anulado en Sigrid"» (sin ``cod`` si no lo hay)."""
    limpio = (cod or "").strip()
    sujeto = f"Registrado en Sigrid como {limpio}" if limpio else "Registrado en Sigrid"
    return f'{sujeto}: corrígelo en Sigrid y pulsa "Ya lo he anulado en Sigrid"'


class AlbaranBloqueadoError(Exception):
    """R25/R26: el documento tiene un alta bloqueante; no se cambia nada."""

    def __init__(self, document_id: str, estado: str, cod: str | None) -> None:
        self.document_id = document_id
        self.estado = estado
        self.cod = cod
        super().__init__(aviso_bloqueo(cod))

    @property
    def aviso(self) -> str:
        return aviso_bloqueo(self.cod)


class AlbaranSinValorarError(Exception):
    """R37: no se aprueba un albarán no valorado; no se cambia nada."""

    def __init__(self, document_id: str) -> None:
        self.document_id = document_id
        super().__init__(AVISO_SIN_VALORAR)

    @property
    def aviso(self) -> str:
        return AVISO_SIN_VALORAR


@dataclass(frozen=True)
class ConfigAltaSigrid:
    """DESDE, Espera y mapeo de productos (los mismos valores que sv9)."""

    desde: datetime | None = None
    espera: timedelta = timedelta(minutes=15)
    mapeo: Mapping[str, str] = field(
        default_factory=lambda: dict(MAPEO_PRODUCTO_POR_DEFECTO),
    )

    @property
    def activa(self) -> bool:
        """DESDE no vacía (R3)."""
        return self.desde is not None

    @property
    def admitidos(self) -> frozenset[str]:
        """Productos que se pueden elegir en una sin vincular (R41)."""
        return productos_admitidos(self.mapeo)


@dataclass(frozen=True)
class ResultadoAprobacion:
    """Lo que pasó al aprobar (R1–R4).

    ``paso_a_aprobado``: el documento no estaba aprobado y ahora sí.
    ``alta_pedida``: ``None`` si no tocaba pedirla (ya estaba aprobado o DESDE
    vacía); ``True``/``False`` si se publicó o no en ``q-feedback``.
    """

    paso_a_aprobado: bool
    alta_pedida: bool | None = None

    @property
    def aviso(self) -> str | None:
        """R4: aviso cuando el alta tocaba y no se pudo pedir."""
        return AVISO_ALTA_NO_PEDIDA if self.alta_pedida is False else None


class ProductoOpcion(BaseModel):
    """Una opción del selector de producto (R40)."""

    codigo: str
    nombre: str


class ProductoLinea(BaseModel):
    """Producto Sigrid de una línea valorada (R40, R41, R43).

    Vinculada: el producto de su línea de contrato, sin selector. Sin
    vincular a registrar: el elegido o, si no hay, el por defecto según la
    familia (``producto_efectivo`` de comun), con selector. Sin vincular sin
    importe: no se registra, sin selector (R13).
    """

    valuation_line_id: int
    vinculada: bool
    a_registrar: bool
    elegido: str | None = None
    codigo: str | None = None
    #: El que llevaría sin elegir nada (familia + mapeo); ``None`` en vinculadas.
    defecto: str | None = None
    por_defecto: bool = False

    @computed_field  # type: ignore[prop-decorator]
    @property
    def nombre(self) -> str | None:
        return nombre_producto(self.codigo) if self.codigo else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def seleccionable(self) -> bool:
        return not self.vinculada and self.a_registrar


class AltaSigridVista(BaseModel):
    """Una fila de ``albaran_altas_sigrid``, para pintarla (R29)."""

    estado: str
    modo: str | None = None
    sigrid_con_ide: int | None = None
    sigrid_cod: str | None = None
    adjunto_estado: str | None = None
    motivos: list[dict[str, Any]] = Field(default_factory=list)
    avisos: list[dict[str, Any]] = Field(default_factory=list)
    peticion: dict[str, Any] | None = None
    respuesta: dict[str, Any] | None = None
    intentos: int = 0
    approved_at_utc: str | None = None
    ultimo_intento_at_utc: str | None = None
    actualizado_at_utc: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def bloqueante(self) -> bool:
        return self.estado in ESTADOS_ALTA_BLOQUEANTES

    @computed_field  # type: ignore[prop-decorator]
    @property
    def estado_texto(self) -> str:
        return etiqueta_estado_alta(self.estado) or self.estado

    @computed_field  # type: ignore[prop-decorator]
    @property
    def aviso(self) -> str | None:
        """R25: el aviso del bloqueo, si lo es."""
        return aviso_bloqueo(self.sigrid_cod) if self.bloqueante else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def simulacion(self) -> bool:
        return self.modo == "simulacion"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def lineas(self) -> list[dict[str, Any]]:
        """Líneas de la petición con lo que devolvió la previa (por
        ``referencia_linea``): producto, partida, cantidad, precio y total."""
        pedidas = (self.peticion or {}).get("lineas") or []
        devueltas = {
            str(linea.get("referencia_linea")): linea
            for linea in ((self.respuesta or {}).get("lineas") or [])
            if isinstance(linea, dict)
        }
        filas: list[dict[str, Any]] = []
        for pedida in pedidas:
            if not isinstance(pedida, dict):
                continue
            referencia = str(pedida.get("referencia_linea"))
            devuelta = devueltas.get(referencia, {})
            filas.append({
                "referencia_linea": referencia,
                "producto": pedida.get("producto"),
                "ctrpro_ide": pedida.get("ctrpro_ide"),
                "descripcion": pedida.get("descripcion") or devuelta.get("descripcion"),
                "partida": pedida.get("partida"),
                "cantidad": pedida.get("cantidad"),
                "precio": pedida.get("precio"),
                "total": devuelta.get("total"),
                "motivos": [
                    m for m in self.motivos
                    if str(m.get("referencia_linea")) == referencia
                ],
            })
        return filas

    def _total(self, clave: str) -> float | None:
        totales = (self.respuesta or {}).get("totales")
        valor = totales.get(clave) if isinstance(totales, dict) else None
        return float(valor) if isinstance(valor, (int, float)) else None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_previa(self) -> float | None:
        """Base imponible de la previa (``totales.totbas``, contrato §2)."""
        return self._total("totbas")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_documento(self) -> float | None:
        """Total con IVA de la previa (``totales.totdoc``)."""
        return self._total("totdoc")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def motivos_documento(self) -> list[dict[str, Any]]:
        """Motivos que no son de una línea concreta."""
        return [m for m in self.motivos if not m.get("referencia_linea")]
