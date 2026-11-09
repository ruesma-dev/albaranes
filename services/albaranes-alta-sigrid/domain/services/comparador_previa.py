# domain/services/comparador_previa.py
"""Comparación de la previa con lo aprobado (F-053, R17; en ``idempotente``, R15).

Puro. Casa la respuesta por ``referencia_linea``, nunca por posición
(contrato §3.1). Motivos de ``previsto`` (cualquiera ⇒ ``revisar``):

- ``importe_distinto``: el ``total`` de la línea difiere de su
  ``importe_calculado`` en MÁS de la tolerancia (0,05 € justos valen).
- ``lineas_distintas``: falta o sobra una línea.
- ``partida_distinta``: la ``partida`` de la previa no es la pedida, también
  nula frente a no nula (sin partida = almacén).
- ``dto_distinto`` (F-110 R11): una línea pedida con ``dto`` cuya línea de la
  previa no trae ``dto``, no es un número legible o difiere del pedido en MÁS
  de 0,005. Las pedidas sin ``dto`` no lo comparan aunque la previa lo traiga
  (R12; sigrid-api lo copia del ``ctrpro`` en algunas vinculadas).
- ``aviso_bloqueante``: un aviso de cabecera o de línea con ``codigo`` en
  ``ALTA_SIGRID_AVISOS_BLOQUEANTES``. Los demás se guardan y se enseñan.

En ``idempotente`` el albarán YA está en Sigrid: solo se mira si lo que hay
coincide con lo pedido; si no, ``registrado_distinto`` (H18), que deja el alta
``registrado`` (se corrige anulando, R28), nunca ``revisar``. Ni la partida ni el
``dto`` (sigrid-api lo devuelve nulo en ``idempotente``) se comparan ahí.

Los importes se comparan en ``Decimal`` desde su texto para que el borde de la
tolerancia no dependa del redondeo binario (10,05 − 10,00 es 0,05, no 0,0500…1).
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from decimal import Decimal
from typing import Any

from domain.models.alta_models import LineaPeticion, Motivo, PeticionAlbaran, RespuestaAlta

ESTADO_IDEMPOTENTE = "idempotente"

#: (F-110 R11) Diferencia máxima entre el ``dto`` pedido y el de la previa.
TOLERANCIA_DTO = Decimal("0.005")


def _decimal(valor: Any) -> Decimal:
    return Decimal(str(valor))


def _partida(valor: Any) -> str | None:
    texto = "" if valor is None else str(valor).strip()
    return texto or None


def _fuera_de_tolerancia(total: Any, importe: float, tolerancia_eur: float) -> bool:
    if total is None:
        return True
    return abs(_decimal(total) - _decimal(importe)) > _decimal(tolerancia_eur)


def _detalle_importe(importe: float, total: Any) -> str:
    return f"aprobado {importe}, Sigrid {total}"


def _numero_es(valor: float) -> str:
    """«7», «7,46»: sin ceros finales y con coma decimal."""
    return f"{valor:.6f}".rstrip("0").rstrip(".").replace(".", ",")


def _dto_legible(valor: Any) -> float | None:
    """El ``dto`` de la previa si es un número JSON finito (no booleano ni texto)."""
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    return float(valor) if math.isfinite(valor) else None


def _dto_distinto(pedida: LineaPeticion, devuelta: Mapping[str, Any]) -> Motivo | None:
    """(F-110 R11) ``dto_distinto`` si se pidió ``dto`` y la previa no lo
    aplica (ausente, ilegible o a más de 0,005); ``None`` en otro caso."""
    if pedida.dto is None:
        return None
    sigrid = _dto_legible(devuelta.get("dto"))
    if sigrid is not None and abs(_decimal(sigrid) - _decimal(pedida.dto)) <= TOLERANCIA_DTO:
        return None
    texto = "—" if sigrid is None else _numero_es(sigrid)
    return Motivo(
        "dto_distinto", f"pedido {_numero_es(pedida.dto)}, Sigrid {texto}",
        pedida.referencia_linea,
    )


def _avisos_bloqueantes(
    avisos: Iterable[dict[str, Any]], bloqueantes: frozenset[str], referencia: str | None,
) -> list[Motivo]:
    motivos = []
    for aviso in avisos:
        codigo = str(aviso.get("codigo") or "")
        if codigo in bloqueantes:
            detalle = f"{codigo}: {aviso.get('mensaje') or ''}".strip()
            motivos.append(Motivo("aviso_bloqueante", detalle, referencia))
    return motivos


def comparar(
    peticion: PeticionAlbaran,
    respuesta: RespuestaAlta,
    importes: Mapping[str, float],
    tolerancia_eur: float,
    avisos_bloqueantes: frozenset[str],
) -> list[Motivo]:
    """Motivos de R17 (``previsto``) o de R15 (``idempotente``)."""
    pedidas = {l.referencia_linea: l for l in peticion.lineas}
    devueltas = {
        str(l.get("referencia_linea")): l for l in respuesta.lineas
        if l.get("referencia_linea") is not None
    }
    idempotente = respuesta.estado == ESTADO_IDEMPOTENTE
    codigo_lineas = "registrado_distinto" if idempotente else "lineas_distintas"
    codigo_importe = "registrado_distinto" if idempotente else "importe_distinto"

    motivos: list[Motivo] = []
    for ref in pedidas:
        if ref not in devueltas:
            motivos.append(Motivo(codigo_lineas, "falta en Sigrid", ref))
    for ref in devueltas:
        if ref not in pedidas:
            motivos.append(Motivo(codigo_lineas, "sobra en Sigrid", ref))

    for ref, pedida in pedidas.items():
        devuelta = devueltas.get(ref)
        if devuelta is None:
            continue
        importe = float(importes[ref])
        total = devuelta.get("total")
        if _fuera_de_tolerancia(total, importe, tolerancia_eur):
            motivos.append(Motivo(codigo_importe, _detalle_importe(importe, total), ref))
        if idempotente:
            continue
        if _partida(devuelta.get("partida")) != _partida(pedida.partida):
            motivos.append(Motivo(
                "partida_distinta",
                f"pedida {pedida.partida}, Sigrid {devuelta.get('partida')}",
                ref,
            ))
        dto = _dto_distinto(pedida, devuelta)
        if dto is not None:
            motivos.append(dto)
        motivos.extend(_avisos_bloqueantes(devuelta.get("avisos") or (), avisos_bloqueantes, ref))

    if not idempotente:
        motivos.extend(_avisos_bloqueantes(respuesta.avisos, avisos_bloqueantes, None))
    return motivos
