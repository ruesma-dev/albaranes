# application/services/residuos_container_calc.py
"""Cálculo determinista de la valoración por CONTENEDORES (residuos).

En residuos la valoración va por contenedor: el contrato tarifa un
contenedor de X m³, y la cantidad valorada es el NÚMERO de contenedores,
no los m³ del albarán. Los m³ (y el peso en Tn) se conservan como
metadato de la línea para trabajos posteriores.

Regla de negocio CONFIRMADA por Ruesma (jul 2026), con el orden de las
prioridades 2 y 3 INTERCAMBIADO por decisión del humano del 2026-08-19
(F-036 R22): el VOLUMEN manda sobre la resta. Queda así, por PRIORIDAD:

    1) contenedores EXPLICITOS del albaran
       (contexto_linea.contenedores) -> ese numero, tal cual.
    2) num_contenedores = ceil(volumen_m3 / m3_por_contenedor), con
       el tamano elegido por F-111 (ver abajo).
    3) resta unidades LLEVADAS - RETIRADAS
       (contenedores_entregados - contenedores_retirados) cuando
       AMBAS vienen y la resta es >= 1.

Por qué el volumen va ANTES que la resta: la resta describe el
MOVIMIENTO de contenedores (cuántos quedaron en obra), que no tiene por
qué ser lo que se factura; el volumen es un dato impreso del documento.
Un albarán con 12 m³ y "llevadas 2 / retiradas 1" se factura por los 12
m³ —2 contenedores de 6—, no por el 1 de la resta.

TAMAÑO DEL CONTENEDOR (F-111, regla del humano del 2026-10-29). Las
fuentes, por orden (R8): los m³ de las líneas de CONTENEDOR de la tabla
del contrato > el ``contenedor_m3`` que IA3 leyó del contrato > los m³
de la descripción de la línea casada > el estándar. Un tamaño único es
una lista de uno.

- El contrato da tamaños: el MÁS PEQUEÑO de ellos en el que caben los
  m³ (1 contenedor). Si no caben en ninguno (D2): paquetes de 6 si el
  contrato tiene el de 6; si no, paquetes del mayor.
- El contrato no da tamaños: los contenedores son de 3, 6 o 9 m³ y se
  elige el más pequeño en el que caben (≤3 → 3, ≤6 → 6, ≤9 → 9, un
  contenedor); con más de 9 m³, ceil(m³ / 6) contenedores de 6, sin
  mezclar tamaños. Motivo ``residuos_tamano_estandar=<t>m3``.

El PRECIO es siempre el de la línea casada (el precio general del
contrato): cambia la cantidad, no el precio. Si el tamaño elegido no es
el que dice la descripción de la casada, la línea va a revisión con
``residuos_tamano_distinto_de_casada=<elegido>/<casada>`` (R9) sin
cambiar la casada ni su precio.

Si no hay m³ en el albarán ni resta utilizable, se devuelve
``num_contenedores=None`` y la razón ``residuos_sin_volumen_m3`` para
que la línea vaya a revisión (NUNCA se inventa un número de la nada).

Los NOMBRES de las ``reasons`` no cambiaron con el intercambio: hay
código aguas arriba (``valuation_builder``) que los inspecciona por
prefijo.

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

# (F-111 R1, R2) Tamaños estándar cuando el contrato no da ninguno, y el
# del paquete cuando los m³ no caben en el mayor.
_TAMANOS_ESTANDAR = (3.0, 6.0, 9.0)
_TAMANO_PAQUETE = 6.0
# Tolerancia de m³ (la de siempre): diferencias por debajo no cuentan.
_TOLERANCIA_M3 = 0.01
#: (F-111 R3) Motivo sin revisión: ``residuos_tamano_estandar=<t>m3``.
MOTIVO_TAMANO_ESTANDAR = "residuos_tamano_estandar"
#: (F-111 R9) Motivo con revisión: ``residuos_tamano_distinto_de_casada=<e>/<c>``.
MOTIVO_TAMANO_DISTINTO_DE_CASADA = "residuos_tamano_distinto_de_casada"
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
    #: (F-111 R9) La línea debe ir a revisión por el tamaño elegido.
    revision: bool = False


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


def _caben(m3: float, tamano: float) -> bool:
    """Los m³ caben en el contenedor, con la tolerancia de 0,01 m³."""
    return round(m3, 2) <= tamano + _TOLERANCIA_M3 / 2


def _elegir_tamano(tamanos: list[float], m3: float) -> tuple[int, float]:
    """(F-111 R1, R2, R6, R7) ``(nº de contenedores, tamaño)`` para ``m3``.

    ``tamanos`` vacía ⇒ los estándar 3/6/9: el más pequeño en el que caben,
    1 contenedor; si no caben, paquetes de 6. Con tamaños (los del
    contrato) ⇒ el más pequeño en el que caben, 1 contenedor; si no caben
    en ninguno (D2), paquetes de 6 si está el de 6 y, si no, del mayor.
    Nunca mezcla tamaños.
    """
    lista = sorted(tamanos) if tamanos else list(_TAMANOS_ESTANDAR)
    for tamano in lista:
        if _caben(m3, tamano):
            return 1, tamano
    if not tamanos or any(abs(t - _TAMANO_PAQUETE) < _TOLERANCIA_M3 for t in lista):
        paquete = _TAMANO_PAQUETE
    else:
        paquete = lista[-1]
    return int(math.ceil(round(m3, 2) / paquete)), paquete


def _tamanos_del_contrato(contrato_lines: Any) -> list[float]:
    """(F-111 R8) Los m³ de TODAS las líneas «contenedor» de la tabla."""
    tamanos: list[float] = []
    for l in contrato_lines or ():
        desc = getattr(l, "descripcion", None) or getattr(
            l, "descripcion_linea", None
        )
        if not desc or "contenedor" not in str(desc).lower():
            continue
        size = _parse_m3(desc)
        if size and size > 0:
            tamanos.append(size)
    return tamanos


def _tamano_ia(valor_leido: Any) -> Optional[float]:
    """El tamaño si es un número positivo (el de IA3 o el de la casada)."""
    try:
        valor = float(valor_leido)
    except (TypeError, ValueError):
        return None
    return valor if valor > 0 else None


def calcular_contenedores_residuos(
    *,
    contexto_linea: Any,
    contrato_line: Any = None,
    contrato_lines: Any = None,
    contenedor_m3_ia: Optional[float] = None,
) -> ResultadoContenedores:
    """Devuelve el nº de contenedores a valorar para una línea de residuos.

    Prioridad (F-036 R22, decisión del humano del 2026-08-19):
    explícitos > ceil(volumen / tamaño) > resta llevadas-retiradas.
    El volumen manda sobre la resta. Ver docstring del módulo.
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

    # ---- Prioridad 2: ceil(volumen / tamaño de contenedor) --------- #
    # (F-036 R22) El volumen va ANTES que la resta desde el 2026-08-19:
    # la resta describe el movimiento de contenedores, el volumen es un
    # dato impreso del albarán. Ver docstring del módulo.
    if m3 is None or m3 <= 0:
        # ---- Prioridad 3: resta unidades LLEVADAS - RETIRADAS ------ #
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

        # ---- Ni volumen ni resta utilizables: NO se inventa nada ---- #
        return ResultadoContenedores(
            num_contenedores=None,
            volumen_m3=m3,
            contenedor_m3=None,
            reasons=["residuos_sin_volumen_m3"],
        )

    # Tamaño del contenedor (F-111 R8): tabla del contrato > IA3 >
    # descripción de la línea casada > estándar 3/6/9.
    casada_m3 = _tamano_ia(_tamano_contenedor(contrato_line))
    tamanos = _tamanos_del_contrato(contrato_lines)
    if not tamanos:
        ia = _tamano_ia(contenedor_m3_ia)
        if ia is not None:
            tamanos = [ia]
        elif casada_m3 is not None:
            tamanos = [casada_m3]
    num, tam = _elegir_tamano(tamanos, m3)

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
    if not tamanos:
        razon_defecto.append(f"{MOTIVO_TAMANO_ESTANDAR}={tam:g}m3")
    revision = False
    if casada_m3 is not None and abs(casada_m3 - tam) >= _TOLERANCIA_M3:
        razon_defecto.append(
            f"{MOTIVO_TAMANO_DISTINTO_DE_CASADA}={tam:g}/{casada_m3:g}"
        )
        revision = True

    return ResultadoContenedores(
        num_contenedores=num,
        volumen_m3=m3,
        contenedor_m3=tam,
        reasons=razon_defecto + [
            f"residuos_contenedores={num} "
            f"(m3={m3:g} / contenedor={tam:g} m3)"
        ],
        revision=revision,
    )
