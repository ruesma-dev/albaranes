# evals/informe.py
"""Render del informe de una corrida y su lectura por la puerta del arnés.

El informe cumple dos papeles a la vez y por eso tiene dos capas:

- **Para una persona**: tablas por fase, caso a caso, con los fallos críticos y
  los avisos laxos campo a campo. Los libros IA1–IA4 son evals de fase: sirven
  para localizar EN QUÉ FASE se rompe lo que el extremo-a-extremo detecta.
- **Para la puerta** (`harness/rutas_sensibles.py`): cuatro líneas parseables
  —`MODO:`, `FASES:`, `PROVEEDORES:` y `VEREDICTO:`— para no tener que leer
  Markdown con expresiones regulares frágiles.
"""

from __future__ import annotations

from evals.modelos import (
    NO_EVALUABLE,
    OMITIDO,
    ResultadoFase,
    ResultadoPasada,
)

#: Modos de corrida. Solo `completa` vale como evidencia para la puerta (R24).
MODO_COMPLETA = "completa"
MODO_DETERMINISTA = "determinista"

#: Partes que tiene que traer una pasada completa (R9): las cuatro fases MÁS
#: el extremo-a-extremo. Sin una de ellas no es una pasada completa, por mucho
#: que se haya lanzado con `--con-llm`.
PARTES_PASADA_COMPLETA: tuple[str, ...] = ("IA1", "IA2", "IA3", "IA4", "E2E")

_ETIQUETA_MODO = "MODO:"
_ETIQUETA_FASES = "FASES:"
_ETIQUETA_PROVEEDORES = "PROVEEDORES:"
_ETIQUETA_VEREDICTO = "VEREDICTO:"

_AVISO_SIN_CLASIFICAR = (
    "Se han tratado como críticos (R8). Clasifícalos en evals/criticidad.json "
    "para que el informe deje de avisar:"
)

_NOMBRE_LARGO = {
    "IA1": "IA1 · extracción genérica (sv2)",
    "IA2": "IA2 · contexto por tipología (sv2)",
    "IA3": "IA3 · valoración contra contrato (sv5)",
    "IA4": "IA4 · conciliación de líneas sin match (sv5)",
    "E2E": "Extremo a extremo · RESULTADO_FINAL (sv5 → build de sv6)",
}


def _cabecera(pasada: ResultadoPasada) -> list[str]:
    titulo = f"Evals de IA — {pasada.feature}" if pasada.feature else "Evals de IA"
    proveedores = sorted(
        {proveedor for fase in pasada.fases for proveedor in fase.proveedores}
    )
    modo_legible = (
        "pasada completa (con llamadas LLM reales)"
        if pasada.modo == MODO_COMPLETA
        else "determinista (sin ninguna llamada LLM ni de red)"
    )
    return [
        f"# {titulo}",
        "",
        f"- Fecha: {pasada.fecha or '(sin fecha)'}",
        f"- Commit HEAD: {pasada.commit or '(sin commit)'}",
        f"- Feature: {pasada.feature or '(corrida manual)'}",
        f"- Modo: {modo_legible}",
        "",
        "Líneas parseables por la puerta del arnés:",
        "",
        "```",
        f"{_ETIQUETA_MODO} {pasada.modo}",
        f"{_ETIQUETA_FASES} {','.join(fase.nombre for fase in pasada.fases)}",
        f"{_ETIQUETA_PROVEEDORES} {','.join(proveedores) or '(ninguno)'}",
        "```",
        "",
    ]


def _bloque_fase(fase: ResultadoFase) -> list[str]:
    lineas = [
        f"## {_NOMBRE_LARGO.get(fase.nombre, fase.nombre)} — {fase.veredicto()}",
        "",
        f"- Casos evaluados: {len(fase.evaluados)} · omitidos: {len(fase.omitidos)}",
        f"- Proveedores invocados: {', '.join(fase.proveedores) or '(ninguno)'}",
    ]
    if fase.motivo:
        lineas.append(f"- Motivo: {fase.motivo}")
    lineas += ["", "| Caso | Estado | Fallos críticos | Avisos laxos | Motivo |", "|---|---|---|---|---|"]

    if not fase.casos:
        lineas.append("| (sin casos en los fixtures) | NO_EVALUABLE | — | — | — |")
    for caso in fase.casos:
        fallos = "—" if caso.estado == OMITIDO else str(len(caso.fallos))
        avisos = "—" if caso.estado == OMITIDO else str(len(caso.avisos))
        lineas.append(
            f"| {caso.caso_id} | {caso.estado} | {fallos} | {avisos} | "
            f"{caso.motivo or '—'} |"
        )

    detalle = [
        f"- {caso.caso_id} · "
        f"{'FALLO' if discrepancia.severidad == 'fallo' else 'AVISO'} · "
        f"{discrepancia.descripcion()}"
        for caso in fase.casos
        for discrepancia in caso.discrepancias
    ]
    if detalle:
        lineas += ["", "Detalle campo a campo:", "", *detalle]
    lineas.append("")
    return lineas


def render(pasada: ResultadoPasada, sin_clasificar: list[str] | None = None) -> str:
    """Escribe el informe completo de una corrida (R15)."""
    lineas = ["<!-- informe generado por evals/informe.py -->", ""]
    lineas += _cabecera(pasada)

    for fase in pasada.fases:
        lineas += _bloque_fase(fase)

    if sin_clasificar:
        lineas += [
            "## Campos sin clasificar en evals/criticidad.json",
            "",
            _AVISO_SIN_CLASIFICAR,
            "",
            *[f"- `{campo}`" for campo in sin_clasificar],
            "",
        ]

    lineas += [
        "## Veredicto",
        "",
        _explicacion_veredicto(pasada),
        "",
        f"{_ETIQUETA_VEREDICTO} {pasada.veredicto()}",
    ]
    return "\n".join(lineas) + "\n"


def _explicacion_veredicto(pasada: ResultadoPasada) -> str:
    veredicto = pasada.veredicto()
    if veredicto == NO_EVALUABLE:
        return (
            "Alguna parte de la corrida no tenía ni un caso en los fixtures. "
            "Un informe sin casos no es evidencia: NO_EVALUABLE, nunca VERDE."
        )
    if veredicto == "ROJO":
        rojas = [
            fase.nombre for fase in pasada.fases if fase.veredicto() == "ROJO"
        ]
        return f"Hay fallos críticos en: {', '.join(rojas)}."
    return "Sin fallos críticos. Los avisos laxos, si los hay, no impiden el verde."


# --- Lectura del informe (la usa la puerta del arnés) ------------------------


def _valor_de(texto: str, etiqueta: str) -> str:
    for linea in texto.splitlines():
        despojada = linea.strip()
        if despojada.startswith(etiqueta):
            return despojada[len(etiqueta) :].strip()
    return ""


def parsear_veredicto(texto: str) -> str:
    """Veredicto declarado en el informe; cadena vacía si no lo declara."""
    return _valor_de(texto, _ETIQUETA_VEREDICTO)


def es_pasada_completa(texto: str) -> bool:
    """¿El informe corresponde a una pasada completa (R9)?

    Exige las dos cosas: modo `completa` Y las cinco partes. Un informe
    determinista, o uno al que le falte el extremo-a-extremo, no vale como
    evidencia para la puerta por mucho que salga VERDE.
    """
    if _valor_de(texto, _ETIQUETA_MODO) != MODO_COMPLETA:
        return False
    partes = {
        parte.strip() for parte in _valor_de(texto, _ETIQUETA_FASES).split(",")
    }
    return all(exigida in partes for exigida in PARTES_PASADA_COMPLETA)
