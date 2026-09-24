# evals/procesos/errores.py
"""Cómo se describe el fallo de UN caso sin llevarse los valores del albarán.

Los subprocesos de `evals/procesos/` procesan los casos uno a uno, y una
excepción en uno no puede tumbar la corrida entera: el 2026-09-24 una respuesta
degenerada de IA2 —una racha de ceros hasta cortarse a 59.877 caracteres—
reventó `RevisionAlbaranFase2` con `json_invalid`, el subproceso salió con
código 1 y se perdieron los resultados de los demás casos tras 50 minutos de
pasada facturada, sin que el log dijera siquiera qué caso era.

El motivo que sale de aquí acaba en el informe de la pasada, que se versiona
SIN valores (R31 de F-047). Por eso no se usa `str(error)`: el de pydantic
incluye `input_value`, o sea, el trozo de la respuesta del LLM. Se describe el
error por su FORMA —tipo, ubicación, línea y columna— y nunca por su texto.
"""

from __future__ import annotations

import re
import sys

#: Tope del motivo: cabe en una celda de la tabla del informe.
TOPE_MOTIVO = 200

#: Cuántos errores de pydantic se detallan antes de resumir el resto.
MAX_ERRORES_DETALLADOS = 3

_POSICION = re.compile(r"line (\d+) column (\d+)")


def avisar(servicio: str, texto: str) -> None:
    """Una línea de avance por stderr, al momento: si el proceso muere, se sabe dónde.

    stdout no vale: es el canal limpio de la carga JSON (`canal.py`). Y el
    texto no lleva valores del albarán: quien llama pasa el caso, el
    proveedor y el motivo de `describir_error`, nunca la respuesta del LLM.
    """
    print(f"{servicio}: {texto}", file=sys.stderr, flush=True)


def describir_error(error: BaseException, fase: str) -> dict[str, str]:
    """El fallo de un caso como `{fase, tipo, motivo}`, sin valores del albarán."""
    tipo = type(error).__name__
    return {"fase": fase, "tipo": tipo, "motivo": _recortar(f"{tipo}: {_forma(error)}")}


def _forma(error: BaseException) -> str:
    errores = _errores_de_pydantic(error)
    if errores is not None:
        return _forma_pydantic(errores)
    linea, columna = getattr(error, "lineno", None), getattr(error, "colno", None)
    if isinstance(linea, int) and isinstance(columna, int):
        # json.JSONDecodeError: la posición basta para localizarlo.
        return f"JSON inválido en línea {linea}, columna {columna}"
    estado = getattr(error, "status_code", None)
    if isinstance(estado, int):
        # Errores HTTP de los SDK de los proveedores (429, 500, 503…).
        return f"HTTP {estado}"
    return "sin detalle (el texto de la excepción no se copia: puede llevar valores)"


def _errores_de_pydantic(error: BaseException) -> list[dict] | None:
    """Los errores estructurados de un `ValidationError`, SIN su entrada."""
    metodo = getattr(error, "errors", None)
    if not callable(metodo):
        return None
    try:
        errores = metodo(include_input=False, include_url=False, include_context=False)
    except TypeError:
        return None
    return list(errores) if isinstance(errores, (list, tuple)) else None


def _forma_pydantic(errores: list[dict]) -> str:
    if not errores:
        return "error de validación sin detalle"
    partes = [_un_error(dato) for dato in errores[:MAX_ERRORES_DETALLADOS]]
    resto = len(errores) - MAX_ERRORES_DETALLADOS
    if resto > 0:
        partes.append(f"(+{resto} más)")
    return "; ".join(partes)


def _un_error(dato: dict) -> str:
    """`tipo en ubicación`, y la posición si es JSON roto. Nunca `msg` entero."""
    texto = str(dato.get("type", "desconocido"))
    ubicacion = ".".join(str(parte) for parte in dato.get("loc", ()) or ())
    if ubicacion:
        texto += f" en {ubicacion}"
    posicion = _POSICION.search(str(dato.get("msg", "")))
    if posicion:
        texto += f" (línea {posicion.group(1)}, columna {posicion.group(2)})"
    return texto


def _recortar(texto: str) -> str:
    return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"
