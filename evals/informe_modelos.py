# evals/informe_modelos.py
"""Informes del comparador de modelos (F-083): el resumen versionable y el detalle.

Puro: recibe lo medido y devuelve texto. El resumen versionable
(`progress/comparar_modelos_F-083.md`) NO lleva valores de albarán: solo
caso_id, recuentos, tokens, tiempos y costes (R29). Cada invocación añade su
sección y dos clases de líneas que se leen de vuelta:

- `GASTO: <fecha> · <fase> · <usd>`, el gasto real de la invocación: su suma
  es el gasto acumulado de la feature que vigila `--tope-total-usd` (R18);
- `TOKENS: <fase> · <modelo> · <entrada> · <salida>`, los tokens medios por
  llamada: la estimación de la invocación siguiente los usa en vez de los de
  por defecto (R15).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, Decimal

from evals.decision import Metricas, Recomendacion
from evals.modelos import ResultadoCaso

#: Cabecera del resumen versionable cuando aún no existe.
CABECERA = (
    "<!-- progress/comparar_modelos_F-083.md -->\n"
    "# F-083 · Comparador de modelos por fase\n\n"
    "Generado por `python -m evals.comparar_modelos`, una sección por invocación. "
    "**Sin valores de albarán**: solo caso_id, recuentos, tokens, tiempos y costes. "
    "El detalle con valores está en la carpeta que cita cada sección, que git ignora. "
    "Las líneas `GASTO:` suman el gasto real de la feature (`--tope-total-usd`) y las "
    "`TOKENS:` alimentan la estimación de la invocación siguiente.\n"
)

#: Líneas base de F-075 T17 (2026-10-18): solo referencia histórica (R28).
LINEAS_BASE_F075 = "IA1 141 · IA2 2 · IA3 408 · IA4 27 · E2E 537"

_ADVERTENCIA_BASE = (
    "no registran el modelo (probablemente los defectos del runner, `gemini-2.5-flash` y "
    "`gpt-5`, e IA3/IA4 con gemini), así que no son comparables: la comparación válida es "
    "con la referencia medida en esta misma invocación"
)

_SEIS_DECIMALES = Decimal("0.000001")

_GASTO = re.compile(r"^GASTO: \S+ · \S+ · (\d+(?:\.\d+)?)[ \t]*$", re.MULTILINE)
_TOKENS = re.compile(r"^TOKENS: (\S+) · (\S+) · (\d+) · (\d+)[ \t]*$", re.MULTILINE)


def gasto_acumulado(texto: str) -> Decimal:
    """La suma de las líneas `GASTO:` del resumen versionable (R18)."""
    return sum((Decimal(usd) for usd in _GASTO.findall(texto)), Decimal(0))


def tokens_medidos(texto: str) -> dict[tuple[str, str], tuple[int, int]]:
    """Tokens medios por (fase, modelo); manda la última sección que los midió."""
    return {
        (fase, modelo): (int(entrada), int(salida))
        for fase, modelo, entrada, salida in _TOKENS.findall(texto)
    }


def servido_difiere(pedido: str, servido: str) -> bool:
    """El modelo servido no es el pedido ni una instantánea suya (`-2026-09-01`) (R9)."""
    return re.fullmatch(re.escape(pedido) + r"(-\d.*)?", servido) is None


@dataclass
class Seccion:
    """Todo lo que el informe necesita de una invocación, ya medido."""

    fecha: str
    fase: str
    commit: str
    casos: list[str]
    omitidos: dict[str, str]
    repeticiones: int
    referencia: str
    referencia_anadida: bool
    preparacion: str | None
    metricas: dict[str, Metricas]
    recomendacion: Recomendacion
    gasto_real: Decimal
    salida: str
    metricas_e2e: dict[str, Metricas] = field(default_factory=dict)
    metricas_preparacion: Metricas | None = None
    #: (modelo, repetición, caso_id, motivo sin valores).
    errores: list[tuple[str, int, str, str]] = field(default_factory=list)
    cortado: bool = False


def _fallos(metricas: Metricas) -> str:
    if metricas.repeticiones > 1:
        return f"{metricas.fallos:.2f} ({metricas.fallos_min}–{metricas.fallos_max})"
    return str(int(metricas.fallos))


def _servidos(metricas: Metricas) -> str:
    if not metricas.modelos_servidos:
        return "no informado"
    return ", ".join(
        f"{servido} ⚠ difiere del pedido" if servido_difiere(metricas.modelo, servido) else servido
        for servido in metricas.modelos_servidos
    )


def _paradas(metricas: Metricas) -> str:
    return ", ".join(f"{motivo} ×{n}" for motivo, n in sorted(metricas.motivos_parada.items())) or "—"


def _tabla(metricas: dict[str, Metricas]) -> list[str]:
    lineas = [
        "| Modelo | Casos | ERROR | NO_EJECUTADO | Verdes | Fallos críticos | Avisos | "
        "t medio s | t máx s | Tokens entrada | Tokens salida | USD/albarán | USD total | "
        "Uso incompleto | Modelo servido | Parada |",
        "|---|" + "---|" * 15,
    ]
    for m in metricas.values():
        celdas = [
            f"`{m.modelo}`", m.casos, m.errores, m.no_ejecutados, m.verdes, _fallos(m), m.avisos,
            f"{m.tiempo_medio_s:.1f}", f"{m.tiempo_max_s:.1f}",
            math.ceil(m.tokens_entrada_medios), math.ceil(m.tokens_salida_medios),
            f"{m.coste_por_albaran:.4f}", f"{m.coste_total:.4f}", m.uso_incompleto,
            _servidos(m), _paradas(m),
        ]
        lineas.append("| " + " | ".join(str(c) for c in celdas) + " |")
    return lineas


def _tabla_e2e(metricas: dict[str, Metricas]) -> list[str]:
    lineas = ["| Modelo | Casos | ERROR | NO_EJECUTADO | Verdes | Fallos críticos | Avisos |",
              "|---|" + "---|" * 6]
    for m in metricas.values():
        celdas = [f"`{m.modelo}`", m.casos, m.errores, m.no_ejecutados, m.verdes, _fallos(m),
                  m.avisos]
        lineas.append("| " + " | ".join(str(c) for c in celdas) + " |")
    return lineas


def _recomendacion(seccion: Seccion) -> list[str]:
    r = seccion.recomendacion
    titulo = "### Recomendación" + (f" · {r.etiqueta_provisional}" if r.provisional else "")
    if r.veredicto == "sin datos":
        veredicto = (
            "- **sin datos**: la referencia no tiene resultado completo en esta invocación "
            "(ERROR o NO_EJECUTADO), y sin ella no se decide nada"
        )
    elif r.veredicto == "cambiar":
        veredicto = f"- **cambiar** a `{r.recomendado}` (referencia `{seccion.referencia}`)"
    else:
        veredicto = f"- **mantener** `{seccion.referencia}`"
        if r.recomendado != seccion.referencia:
            veredicto += (
                f" (el más barato de la banda es `{r.recomendado}`, sin mejora ni ahorro claros)"
            )
    lineas = [titulo, "", veredicto]
    if r.elegibles:
        lineas.append(
            "- Elegibles: " + ", ".join(f"`{m}`" for m in r.elegibles)
            + " · banda de empate: " + ", ".join(f"`{m}`" for m in r.banda)
        )
    lineas += [f"- AVISO: {aviso}" for aviso in r.avisos]
    return lineas


def _tokens(fase: str, metricas: Metricas) -> str | None:
    if not metricas.tokens_entrada_medios and not metricas.tokens_salida_medios:
        return None
    return (
        f"TOKENS: {fase} · {metricas.modelo} · {math.ceil(metricas.tokens_entrada_medios)} · "
        f"{math.ceil(metricas.tokens_salida_medios)}"
    )


def render_versionable(seccion: Seccion) -> str:
    """La sección de una invocación, SIN valores de albarán (R29)."""
    repeticiones = f"{seccion.repeticiones} repetici{'ón' if seccion.repeticiones == 1 else 'ones'}"
    cabecera = f"- Commit `{seccion.commit or '?'}` · referencia `{seccion.referencia}`"
    if seccion.referencia_anadida:
        cabecera += " (añadida: no se había pedido)"
    lineas = [f"## {seccion.fecha} · {seccion.fase} · {len(seccion.casos)} casos × {repeticiones}",
              "", cabecera]
    if seccion.omitidos:
        detalle = ", ".join(f"{c}: {m}" for c, m in sorted(seccion.omitidos.items()))
        lineas.append(f"- Omitidos: {len(seccion.omitidos)} ({detalle})")
    lineas.append(f"- Detalle con valores (git lo ignora): `{seccion.salida}`")
    if seccion.cortado:
        lineas.append(
            "- **CORTADO** por `--tope-usd`: lo pendiente quedó NO_EJECUTADO y no se llamó más"
        )
    lineas += ["", *_tabla(seccion.metricas)]
    prep = seccion.metricas_preparacion
    if prep is not None:
        lineas += ["", f"- Preparación ({prep.fase}, una vez): `{prep.modelo}` · "
                       f"{prep.llamadas} llamadas · {prep.coste_total:.4f} USD"]
    if seccion.metricas_e2e:
        lineas += ["", "### E2E", "", *_tabla_e2e(seccion.metricas_e2e)]
    lineas += ["", *_recomendacion(seccion), "", "### Casos con ERROR (sin valores)", ""]
    lineas += [
        f"- `{modelo}` r{rep} · {caso} · {motivo}" for modelo, rep, caso, motivo in seccion.errores
    ] or ["(ninguno)"]
    lineas += [
        "",
        f"Líneas base de F-075 (histórico): {LINEAS_BASE_F075}. Advertencia: {_ADVERTENCIA_BASE}.",
        "",
    ]
    tokens = [_tokens(seccion.fase, m) for m in seccion.metricas.values()]
    if prep is not None:
        tokens.append(_tokens(prep.fase, prep))
    lineas += [linea for linea in tokens if linea]
    gasto = seccion.gasto_real.quantize(_SEIS_DECIMALES, rounding=ROUND_CEILING)
    lineas.append(f"GASTO: {seccion.fecha} · {seccion.fase} · {gasto}")
    return "\n".join(lineas) + "\n"


def anadir_seccion(texto: str, seccion: str) -> str:
    """El resumen con la sección nueva al final; con la cabecera si estaba vacío."""
    base = texto if texto.strip() else CABECERA
    return base.rstrip("\n") + "\n\n" + seccion


def render_detalle(seccion: Seccion, casos: dict[str, list[list[ResultadoCaso]]]) -> str:
    """El detalle CON valores (las discrepancias), para la carpeta ignorada."""
    lineas = [
        "# Comparador de modelos · detalle CON valores (no versionar)",
        "",
        f"{seccion.fecha} · {seccion.fase} · commit `{seccion.commit or '?'}`",
        "",
    ]
    for modelo, repeticiones in casos.items():
        for indice, resultados in enumerate(repeticiones, start=1):
            for caso in resultados:
                cola = f" · {caso.motivo}" if caso.motivo else ""
                lineas.append(f"- `{modelo}` r{indice} · {caso.caso_id} · {caso.estado}{cola}")
                lineas += [f"  - {d.descripcion()}" for d in caso.discrepancias]
    return "\n".join(lineas) + "\n"
