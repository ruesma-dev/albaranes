# ruesma_comun/colas/mensajes.py
"""Contratos de los mensajes que viajan por las colas del sistema.

Regla de oro de la arquitectura: **1 mensaje = 1 albarán = `{document_id}`**
(más los metadatos mínimos para idempotencia/decisión). El binario (PDF)
NUNCA viaja en el mensaje: se referencia por SharePoint vía BBDD.

Serialización: JSON en texto plano (UTF-8), SIN base64. Controlamos los
dos extremos de cada cola, así que no necesitamos la codificación base64
que usan Azure Functions por defecto. Si algún día un consumidor externo
la exigiera, basta con activar ``TextBase64EncodePolicy`` en la conexión.

Cada mensaje lleva ``tipo`` como discriminador defensivo: si un mensaje
acaba en la cola equivocada, el consumidor lo detecta y lo manda a poison
en vez de procesarlo mal.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class MensajeBase(BaseModel):
    """Base común: trazabilidad mínima de cualquier mensaje."""

    tipo: str
    document_id: str
    correlation_key: str | None = None
    emitido_en_utc: str = Field(default_factory=_utc_iso)
    emitido_por: str | None = None  # nombre del servicio emisor

    def a_texto(self) -> str:
        """Serializa a JSON (cuerpo del mensaje de cola)."""
        return self.model_dump_json(exclude_none=True)


class MensajeExtraccion(MensajeBase):
    """q-extraccion → ca-sv2-extraccion.

    El documento YA existe en ``workflow_runs`` (lo creó sv1-intake con
    su ``correlation_key`` UNIQUE) y la página YA está en SharePoint.
    """

    tipo: Literal["extraccion"] = "extraccion"


class MensajePersistencia(MensajeBase):
    """q-persistencia → ca-sv3-persistencia.

    El envelope mergeado (fase1 + patch fase2 + overrides de grounding)
    NO viaja aquí: sv2 lo deja persistido y sv3 lo recupera por
    ``document_id`` (la BBDD es la verdad; el mensaje es el disparador).

    ``force`` (jun 2026) — re-fetch manual de contratos desde el portal
    (sv4). Cuando el revisor edita CIF/obra y pulsa "Volver a buscar",
    sv4 re-publica este mensaje con ``force=True``; sv3 lo propaga como
    ``force_refetch=True`` a su ``ContratoEnrichmentService``, que bypasa
    la caché de contratos y vuelve a consultar Sigrid. Con ``force=False``
    (caso normal del pipeline) el enrichment puede servir de caché.
    """

    tipo: Literal["persistencia"] = "persistencia"
    force: bool = False


class MensajeValoracion(MensajeBase):
    """q-valoracion → ca-valorador (sv5+sv6).

    Lo emiten sv3 (auto-selección de contrato único) y sv4 (el revisor
    selecciona contrato o relanza). Equivale al actual
    ``POST sv6 /v1/valuation/run``.
    """

    tipo: Literal["valoracion"] = "valoracion"
    codigo_contrato: str | None = None
    force: bool = False


class MensajeFeedback(MensajeBase):
    """q-feedback → ca-sv8-aprendizaje.

    Lo emite sv4 al aprobar un documento. sv8 reconstruye los diffs
    IA↔humano leyendo BBDD; aquí solo viaja el disparador.
    """

    tipo: Literal["feedback"] = "feedback"
    approved_by: str | None = None


# ------------------------------------------------------------------ #
# Deserialización defensiva.
# ------------------------------------------------------------------ #
_TIPOS: dict[str, type[MensajeBase]] = {
    "extraccion": MensajeExtraccion,
    "persistencia": MensajePersistencia,
    "valoracion": MensajeValoracion,
    "feedback": MensajeFeedback,
}


class MensajeInvalidoError(ValueError):
    """El cuerpo del mensaje no es un mensaje válido del sistema."""


def desde_texto(cuerpo: str, *, tipo_esperado: str | None = None) -> MensajeBase:
    """Parsea el cuerpo de un mensaje de cola.

    ``tipo_esperado``: si el consumidor de una cola lo indica (p. ej.
    "extraccion") y el mensaje trae otro ``tipo``, se lanza
    :class:`MensajeInvalidoError` para que el runtime lo envíe a poison
    sin intentar procesarlo.
    """
    import json

    try:
        datos = json.loads(cuerpo)
    except Exception as exc:  # noqa: BLE001 — cualquier JSON roto es inválido
        raise MensajeInvalidoError(f"cuerpo no es JSON: {exc}") from exc

    if not isinstance(datos, dict):
        raise MensajeInvalidoError("el cuerpo JSON no es un objeto")

    tipo = datos.get("tipo")
    modelo = _TIPOS.get(str(tipo))
    if modelo is None:
        raise MensajeInvalidoError(f"tipo de mensaje desconocido: {tipo!r}")

    if tipo_esperado is not None and tipo != tipo_esperado:
        raise MensajeInvalidoError(
            f"mensaje de tipo {tipo!r} en cola de {tipo_esperado!r}"
        )

    try:
        return modelo.model_validate(datos)
    except Exception as exc:  # noqa: BLE001
        raise MensajeInvalidoError(f"mensaje {tipo!r} inválido: {exc}") from exc
