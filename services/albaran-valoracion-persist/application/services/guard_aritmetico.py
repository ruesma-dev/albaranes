# application/services/guard_aritmetico.py
"""Guard aritmético de los albaranes valorados (F-003, R6–R8).

Cuando un albarán viene con precios e importes impresos, el pipeline
puede CONTRASTAR su aritmética, no rehacerla. La regla de negocio es
una sola y no admite matices:

    si no cuadra, se persiste LO LEÍDO y se manda a revisión;
    jamás se sustituye por el calculado ni por un valor inventado.

Tres comprobaciones, todas deterministas y puras:

  - **Línea** (R6): ``precio × cantidad × (1 − dto/100) ≈ importe_leido``.
  - **Total** (R7): Σ de los importes de las líneas ``from_albaran``
    (las sintéticas M1–M7 no están impresas: no suman) contra el total
    del documento. Con total BASE, el descuadre exige revisión; con
    total CON IVA —o de marca desconocida— solo deja aviso: los
    importes de línea son base imponible y el descuadre es esperado.
  - **Línea única** (R8, caso ORE OIL): un documento de una sola línea
    sin importe impreso y con total base → el total ES el importe de esa
    línea.

La tolerancia es siempre ``IMPORTE_TOLERANCE_PCT``, la misma que usa el
``ImporteCalculator``: no se inventan umbrales nuevos.

Módulo puro: sin BBDD, sin red, sin estado.
"""
from __future__ import annotations

import logging
from typing import Any, Iterable, Optional

logger = logging.getLogger(__name__)

# Decimales con los que se escriben los números en los motivos. Los
# motivos los lee un humano en el portal: 191.4 dice más que
# 191.39999999999998.
_DECIMALES_MOTIVO = 2


def _num(valor: Any) -> Optional[float]:
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _cuadra(a: float, b: float, tolerance_pct: float) -> bool:
    """¿Están ``a`` y ``b`` dentro de la tolerancia porcentual?

    Misma semántica que ``ImporteCalculator._close_enough``: el
    porcentaje se mide sobre el mayor de los dos, para que la
    comparación sea simétrica. El ``1e-9`` del denominador cubre el
    caso 0 contra 0 sin necesidad de una rama aparte.
    """
    denominador = max(abs(a), abs(b), 1e-9)
    return abs(a - b) / denominador * 100.0 <= float(tolerance_pct)


def _fmt(valor: float) -> str:
    return f"{round(valor, _DECIMALES_MOTIVO)}"


def verificar_linea(
    *,
    precio_declarado: Optional[float],
    cantidad: Optional[float],
    descuento_pct: Optional[float],
    importe_leido: Optional[float],
    tolerance_pct: float,
) -> list[str]:
    """Motivos del descuadre de UNA línea. Lista vacía = todo bien.

    No es computable (y por tanto no dice nada) si falta el importe
    leído, el precio declarado o la cantidad: sin los tres no hay
    aritmética que contrastar, y callar es mejor que sospechar de una
    línea que nadie ha declarado.

    Un importe leído de 0 cuenta como AUSENTE, igual que en el
    ``ImporteCalculator`` y el ``PriceReconciler``: una celda vacía que
    el OCR devuelve como cero no puede mandar una línea a revisión.
    """
    leido = _num(importe_leido)
    precio = _num(precio_declarado)
    cant = _num(cantidad)
    if leido is None or precio is None or cant is None:
        return []
    if leido == 0.0:
        return []

    descuento = _num(descuento_pct) or 0.0
    if descuento < 0.0 or descuento > 100.0:
        # Un descuento imposible ya lo avisa el ImporteCalculator; aquí
        # se ignora en vez de producir un descuadre fantasma.
        descuento = 0.0

    calculado = cant * precio * (1.0 - descuento / 100.0)
    if _cuadra(calculado, leido, tolerance_pct):
        return []

    logger.info(
        "[guard-aritmetico] línea descuadrada: calculado=%s leído=%s "
        "(precio=%s cantidad=%s dto=%s%%). Manda el leído.",
        calculado, leido, precio, cant, descuento,
    )
    return [f"guard_aritmetico_linea:{_fmt(calculado)}!={_fmt(leido)}"]


def verificar_total(
    *,
    suma_from_albaran: Optional[float],
    importe_total: Optional[float],
    incluye_iva: Optional[bool],
    tolerance_pct: float,
) -> tuple[list[str], bool]:
    """Motivos del descuadre del TOTAL y si fuerzan revisión.

    Devuelve ``(motivos, exige_revision)``:

      - total ausente o 0 (celda vacía leída como cero) → sin motivos;
      - total BASE (``incluye_iva=False``) que no cuadra → motivo
        ``guard_aritmetico_total`` y revisión;
      - total CON IVA, o de marca desconocida, que no cuadra → solo
        aviso ``guard_aritmetico_total_con_iva``, SIN revisión.
    """
    total = _num(importe_total)
    if total is None or total == 0.0:
        return [], False

    suma = _num(suma_from_albaran) or 0.0
    if _cuadra(suma, total, tolerance_pct):
        return [], False

    if incluye_iva is False:
        logger.info(
            "[guard-aritmetico] total base descuadrado: suma=%s total=%s. "
            "La valoración va a revisión.",
            suma, total,
        )
        return (
            [f"guard_aritmetico_total:{_fmt(suma)}!={_fmt(total)}"],
            True,
        )

    # Total con IVA (o sin marca): comparar una suma de bases contra él
    # descuadra POR DISEÑO. Se deja constancia y nada más.
    return (
        [f"guard_aritmetico_total_con_iva:{_fmt(suma)}!={_fmt(total)}"],
        False,
    )


def importe_efectivo_linea_unica(
    *,
    lineas_albaran: Iterable[Any],
    importe_total: Optional[float],
    incluye_iva: Optional[bool],
) -> Optional[tuple[int, float]]:
    """Caso ORE OIL (R8): el total del documento ES el importe de la
    única línea.

    Devuelve ``(merge_line_id, importe)`` o ``None``. Solo actúa con:
    exactamente UNA línea, sin importe leído, y total BASE presente. Con
    un total que incluye IVA no se inyecta nada: los importes de línea
    del pipeline son base imponible y meter ahí un total con IVA sería
    inventarse un número.
    """
    total = _num(importe_total)
    if total is None or total == 0.0 or incluye_iva is not False:
        return None

    lineas = list(lineas_albaran)
    if len(lineas) != 1:
        return None

    unica = lineas[0]
    if getattr(unica, "importe_leido", None) is not None:
        return None

    merge_line_id = getattr(unica, "merge_line_id", None)
    if merge_line_id is None:
        return None

    logger.info(
        "[guard-aritmetico] documento de una sola línea sin importe "
        "impreso: se le asigna el total del albarán (%s).",
        total,
    )
    return int(merge_line_id), total
