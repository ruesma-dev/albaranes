# application/services/contexto_linea_merger.py
"""Utilidad para fusionar los ``contexto_linea`` que vienen de los 3
proveedores LLM (OpenAI, Gemini, Claude) en un único contexto final
que se persiste en ``albaran_lines_merge``.

Regla: elegimos el contexto "más rico" (más campos rellenos). En caso
de empate, aplicamos el orden canónico del sistema
(openai → gemini → claude).

Preferimos seleccionar UN contexto íntegro (el del proveedor que mejor
lo ha capturado) en lugar de hacer merge campo-a-campo, porque los
campos están correlacionados semánticamente: un ``rol_linea`` puesto
por OpenAI encaja con la ``descripcion_extendida`` de OpenAI, no con
la de Claude. Fusionarlos podría producir contextos incoherentes.

(F-036 R11/R12) Ese argumento vale para los CINCO campos narrativos
—``tipo_familia``, ``rol_linea``, ``descripcion_extendida``,
``notas_tiempo``, ``ref_linea_base``—, que son INTERPRETACIONES de la
línea y siguen llegando íntegros del ganador. NO vale para las nueve
MEDIDAS de ``_CAMPOS_RESIDUOS`` (código LER, m³, Tn, nº de
contenedores...): son hechos impresos en el documento, no lecturas de
uno u otro modelo, y dos proveedores que leen el mismo PDF no producen
un m³ incoherente con un LER. Por eso el ganador se COMPLETA con las
medidas que le falten, tomadas del candidato de mayor score que sí las
traiga, y nunca se le sobrescribe ninguna que ya tenga.

El motivo es un defecto real: puntuar las medidas (R9) arregla solo la
primera cara —el contexto que se descartaba entero por sacar 0—, pero
no que un candidato con ``tipo_familia`` + ``rol_linea`` le gane por
score a otro que trae los m³. Sin el relleno, los m³ se perdían igual.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from domain.models.contexto_linea import ContextoLinea

logger = logging.getLogger(__name__)

_LOG = "[contexto_merger]"

# Orden canónico del sistema. El índice de cada proveedor es el que
# desempata a igualdad de score y el que da nombre al log de R11.
_PROVEEDORES = ("openai", "gemini", "claude")

# (F-036 R9) Las nueve MEDIDAS que el documento de residuos trae por
# línea. Hasta F-036 ninguna puntuaba: un contexto con el código LER,
# los m³ y el nº de contenedores —y ni un campo narrativo— sacaba 0 y
# se descartaba entero, así que sv3 persistía `contexto_linea = NULL`.
# Desde ahí, la tipología de sv5 y el cálculo de contenedores de sv6
# trabajaban a ciegas. Esta tupla es también la lista EXACTA de campos
# que `_completar_campos_objetivos` puede rellenar (R11).
_CAMPOS_RESIDUOS: tuple[str, ...] = (
    "codigo_ler",
    "volumen_m3",
    "peso_toneladas",
    "contenedores",
    "contenedores_entregados",
    "contenedores_retirados",
    "carga_incompleta",
    "m3_no_transportados",
    "exceso_declarado_min",
)


def _tiene_valor(valor: Any) -> bool:
    """True si el campo trae dato. El ``bool`` y el 0 numérico NO son lo mismo.

    Cuentan como hueco `None`, las cadenas en blanco y el **cero de las
    siete medidas numéricas**. Un 0 ahí es «no lo sé», no «vale cero»:
    no existen retiradas de 0 m³ ni contenedores de 0 toneladas, así que
    el único 0 que llega es el de un proveedor que no supo leer el
    número. Contarlo como dato hacía dos daños: inflaba el score de un
    contexto vacío y, sobre todo, tapaba el hueco de R11 e impedía
    rellenarlo desde el proveedor que sí traía los 6 m³ (encontrado en
    la review de los bloques B/C/D de F-036).

    `carga_incompleta` es la excepción, y por eso el ``bool`` se
    comprueba ANTES que el número (en Python `False == 0`):
    `carga_incompleta=False` significa «el albarán dice que la carga iba
    completa», que es información, no ausencia de ella.
    """
    if valor is None:
        return False
    if isinstance(valor, bool):
        return True
    if isinstance(valor, str):
        return bool(valor.strip())
    if isinstance(valor, (int, float)):
        return valor != 0
    return True


def _score_contexto(ctx: Optional[ContextoLinea]) -> int:
    """Cuenta cuántos campos informativos tiene el contexto. 0 si None."""
    if ctx is None:
        return 0
    score = 0
    if ctx.tipo_familia is not None:
        score += 1
    if ctx.rol_linea is not None:
        score += 1
    if ctx.descripcion_extendida and ctx.descripcion_extendida.strip():
        score += 1
    if ctx.notas_tiempo and ctx.notas_tiempo.strip():
        score += 1
    if ctx.ref_linea_base is not None:
        score += 1
    # (R9, R10) Las nueve medidas de residuos suman igual que las
    # narrativas: un contexto que SOLO las trae puntúa > 0 y ya no se
    # descarta.
    for campo in _CAMPOS_RESIDUOS:
        if _tiene_valor(getattr(ctx, campo, None)):
            score += 1
    return score


def _completar_campos_objetivos(
    ganador: ContextoLinea,
    candidatos: list[tuple[int, int, ContextoLinea]],
) -> ContextoLinea:
    """Rellena las medidas de residuos que le faltan al ganador. **R11.**

    ``candidatos`` viene YA ordenado (score DESC, orden canónico ASC) y
    sin el ganador: para cada campo de ``_CAMPOS_RESIDUOS`` que el
    ganador no traiga, se coge el del primer candidato que lo tenga, o
    sea, el de mayor score.

    Nunca sobrescribe: un campo con valor en el ganador se respeta,
    aunque otro proveedor traiga otro distinto. Los cinco campos
    narrativos no se tocan (**R12**). Si no hay nada que rellenar
    devuelve el propio ganador, sin copiar.
    """
    rellenos: dict[str, Any] = {}
    procedencia: list[str] = []

    for campo in _CAMPOS_RESIDUOS:
        if _tiene_valor(getattr(ganador, campo, None)):
            continue
        for _score, order, ctx in candidatos:
            valor = getattr(ctx, campo, None)
            if _tiene_valor(valor):
                rellenos[campo] = valor
                procedencia.append(f"{campo}<-{_PROVEEDORES[order]}")
                break

    if not rellenos:
        return ganador

    logger.info(
        "%s contexto_linea completado con %d medida(s) de residuos: %s",
        _LOG,
        len(rellenos),
        ", ".join(procedencia),
    )
    return ganador.model_copy(update=rellenos)


def pick_best_contexto_linea(
    *,
    openai_ctx: Optional[ContextoLinea] = None,
    gemini_ctx: Optional[ContextoLinea] = None,
    claude_ctx: Optional[ContextoLinea] = None,
) -> Optional[ContextoLinea]:
    """Elige el contexto_linea más completo de los tres proveedores.

    Devuelve ``None`` si ninguno aporta información útil. Tolera
    silenciosamente proveedores deshabilitados (basta con no pasar
    el argumento o pasar ``None``).

    (F-036 R11) El elegido se devuelve COMPLETADO con las medidas de
    residuos que no traiga y sí tenga otro candidato. Ver la cabecera
    del módulo para el porqué.
    """
    candidates: list[tuple[int, int, ContextoLinea]] = []

    for order, ctx in enumerate((openai_ctx, gemini_ctx, claude_ctx)):
        score = _score_contexto(ctx)
        if score > 0 and ctx is not None:
            candidates.append((score, order, ctx))

    if not candidates:
        return None

    # Score DESC, orden canónico ASC.
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return _completar_campos_objetivos(candidates[0][2], candidates[1:])
