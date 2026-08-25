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
"""
from __future__ import annotations

from typing import Any, Optional

from domain.models.contexto_linea import ContextoLinea

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
    """True si el campo trae dato. Ojo: ``False`` y ``0`` SON dato.

    Solo `None` y las cadenas en blanco cuentan como hueco:
    `carga_incompleta=False` significa «el albarán dice que la carga
    iba completa», que es información, no ausencia de ella.
    """
    if valor is None:
        return False
    if isinstance(valor, str):
        return bool(valor.strip())
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
    return candidates[0][2]
