# application/services/residuos_container_calc.py
"""Cálculo determinista de la valoración por CONTENEDORES (residuos).

En residuos la valoración va por contenedor: el contrato tarifa un
contenedor de X m³, y la cantidad valorada es el NÚMERO de contenedores,
no los m³ del albarán. Los m³ (y el peso en Tn) se conservan como
metadato de la línea para trabajos posteriores.

Regla de negocio CONFIRMADA por Ruesma (jul 2026), por PRIORIDAD:

    1) contenedores EXPLICITOS del albaran
       (contexto_linea.contenedores) -> ese numero, tal cual.
    2) resta unidades LLEVADAS - RETIRADAS
       (contenedores_entregados - contenedores_retirados) cuando
       AMBAS vienen y la resta es >= 1.
    3) num_contenedores = ceil(volumen_m3 / m3_por_contenedor), con
       el tamano elegido asi: si los m3 del albaran COINCIDEN con un
       tamano del contrato, ESE (8 m3 con contenedores de 6 y 8 ->
       el de 8, 1 ud); si no coinciden con ninguno -> 6 m3 (el
       contenedor ESTANDAR: 7 m3 con contenedores de 6 y 8 -> 2 de
       6); un unico tamano en contrato -> ese; y ante CUALQUIER
       duda restante -> 6 m3 por defecto.

donde ``m3_por_contenedor_contrato`` se lee de la descripción de la línea
de contrato casada (p.ej. "CONTENEDOR RCD 6 M3" → 6). Si no hay m³ en el
albarán o no se detecta el tamaño de contenedor, se devuelve
``num_contenedores=None`` y una razón para que la línea vaya a revisión
(NUNCA se inventa un número de la nada; el 6 m3 por defecto solo se
aplica cuando HAY volumen que repartir).

Esta función es PURA (sin I/O), fácil de testear.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Optional

# Captura la cifra de m³ en textos tipo "6 m3", "6m³", "7 M3", "6,5 mc".
# Deliberadamente permisiva; es un punto a afinar con descripciones reales.
_M3_REGEX = re.compile(r"(\d+(?:[.,]\d+)?)\s*m\s*[3³c]", re.IGNORECASE)

# Contenedor ESTANDAR (jul 2026): valor por defecto ante cualquier
# duda sobre el tamano (regla de negocio Ruesma).
_CONTENEDOR_ESTANDAR_M3 = 6.0
# Volumen maximo PLAUSIBLE de un albaran de contenedores (jul 2026,
# caso real: IA2 puso las 29 Tn como volumen y salieron contenedores
# fantasma). Por encima se sigue calculando pero se marca revision:
# probablemente el numero es un PESO colado en el campo de volumen.
_VOLUMEN_MAX_PLAUSIBLE_M3 = 16.0


@dataclass(frozen=True)
class ResultadoContenedores:
    num_contenedores: Optional[int]
    volumen_m3: Optional[float]
    contenedor_m3: Optional[float]
    reasons: list[str] = field(default_factory=list)


def _parse_m3(texto: Optional[str]) -> Optional[float]:
    if not texto:
        return None
    m = _M3_REGEX.search(str(texto))
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", "."))
    except ValueError:
        return None


def _tamano_contenedor(contrato_line: Any) -> Optional[float]:
    """m³ por contenedor, leídos de la línea de contrato casada."""
    if contrato_line is None:
        return None
    # Prioridad: descripción (p.ej. "CONTENEDOR RCD 6 M3"), luego unidad.
    return (
        _parse_m3(getattr(contrato_line, "descripcion", None))
        or _parse_m3(getattr(contrato_line, "unidad_medida", None))
    )


def _elegir_contenedor(contrato_lines: Any, m3: float) -> Optional[float]:
    """m³ por contenedor eligiendo de las líneas de contrato (determinista).

    Regla de negocio (jul 2026): si hay un contenedor cuyo tamaño
    COINCIDE con los m³ del albarán, usa ese; si no coincide ninguno y
    el contrato tiene el de 6 m³, usa el 6 (estándar); un único tamaño
    en contrato → ese; varios sin exacto y sin 6 → None (caerá al de
    la línea casada / IA y, en última instancia, al 6 por defecto).
    """
    if not contrato_lines:
        return None
    contenedores: list[float] = []
    for l in contrato_lines:
        desc = getattr(l, "descripcion", None) or getattr(
            l, "descripcion_linea", None
        )
        if not desc or "contenedor" not in str(desc).lower():
            continue
        size = _parse_m3(desc)
        if size and size > 0:
            contenedores.append(size)
    if not contenedores:
        return None
    for size in contenedores:
        if abs(size - m3) < 0.01:      # tamaño exacto -> ese
            return size
    unicos = set(contenedores)
    if len(unicos) == 1:               # un solo tipo -> ese
        return next(iter(unicos))
    if any(                            # sin exacto -> 6 (estándar)
        abs(s - _CONTENEDOR_ESTANDAR_M3) < 0.01 for s in unicos
    ):
        return _CONTENEDOR_ESTANDAR_M3
    return None                        # varios, sin exacto ni 6


def calcular_contenedores_residuos(
    *,
    contexto_linea: Any,
    contrato_line: Any = None,
    contrato_lines: Any = None,
    contenedor_m3_ia: Optional[float] = None,
) -> ResultadoContenedores:
    """Devuelve el nº de contenedores a valorar para una línea de residuos.

    Prioridad (jul 2026): explícitos > resta llevadas-retiradas >
    ceil(volumen / tamaño). Ver docstring del módulo.
    """
    def _num(campo: str) -> Optional[float]:
        v = getattr(contexto_linea, campo, None)
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    m3 = _num("volumen_m3")

    # ---- Prioridad 1: número de contenedores EXPLÍCITO ------------- #
    explicitos = _num("contenedores")
    if explicitos is not None and explicitos >= 1:
        num = int(round(explicitos))
        return ResultadoContenedores(
            num_contenedores=num,
            volumen_m3=m3,
            contenedor_m3=None,
            reasons=[f"residuos_contenedores_explicitos={num}"],
        )

    # ---- Prioridad 2: resta unidades LLEVADAS - RETIRADAS ---------- #
    entregados = _num("contenedores_entregados")
    retirados = _num("contenedores_retirados")
    if entregados is not None and retirados is not None:
        resta = entregados - retirados
        if resta >= 1:
            num = int(round(resta))
            return ResultadoContenedores(
                num_contenedores=num,
                volumen_m3=m3,
                contenedor_m3=None,
                reasons=[
                    f"residuos_contenedores_resta={num} "
                    f"(llevadas {entregados:g} - retiradas "
                    f"{retirados:g})"
                ],
            )

    # ---- Prioridad 3: ceil(volumen / tamaño de contenedor) --------- #
    if m3 is None or m3 <= 0:
        return ResultadoContenedores(
            num_contenedores=None,
            volumen_m3=m3,
            contenedor_m3=None,
            reasons=["residuos_sin_volumen_m3"],
        )

    # Prioridad: el tamaño que fijó la IA leyendo el contrato (regla
    # exacto/por-defecto). Fallback: parseo de la descripción de la línea
    # de contrato casada (por si la IA no lo emite).
    # Prioridad del tamaño de contenedor:
    #   1) escaneo DETERMINISTA de las líneas de contrato (regla exacto/
    #      por-defecto) -> lo más fiable si están estructuradas;
    #   2) el que fijó la IA leyendo el PDF (contenedor_m3_ia);
    #   3) regex sobre la descripción de la línea de contrato casada.
    tam = _elegir_contenedor(contrato_lines, m3)
    if (tam is None or tam <= 0) and contenedor_m3_ia is not None:
        try:
            tam = float(contenedor_m3_ia)
        except (TypeError, ValueError):
            tam = None
    if tam is None or tam <= 0:
        tam = _tamano_contenedor(contrato_line)
    razon_defecto: list[str] = []
    if m3 > _VOLUMEN_MAX_PLAUSIBLE_M3:
        # Sanity (jul 2026): un albaran de contenedores rara vez
        # declara mas de ~16 m3 (2 contenedores de 8). Numeros como
        # 29 suelen ser TONELADAS coladas en el campo de volumen.
        # Se calcula igual (mejor un numero trazable que nada) pero
        # la linea va a revision con la sospecha explicada.
        razon_defecto.append(
            f"residuos_volumen_implausible={m3:g}m3"
            " (posible peso en Tn colado en volumen; revisar)"
        )
    if tam is None or tam <= 0:
        # Regla de negocio (jul 2026): ante CUALQUIER duda sobre el
        # tamaño, el contenedor estándar de 6 m³. Con volumen sobre
        # la mesa NUNCA se deja la línea sin número.
        tam = _CONTENEDOR_ESTANDAR_M3
        razon_defecto.append("residuos_tamano_defecto_6m3")

    num = int(math.ceil(m3 / tam))
    return ResultadoContenedores(
        num_contenedores=num,
        volumen_m3=m3,
        contenedor_m3=tam,
        reasons=razon_defecto + [
            f"residuos_contenedores={num} "
            f"(m3={m3:g} / contenedor={tam:g} m3)"
        ],
    )
