# evals/procesos/canal.py
"""El canal por el que un subproceso de evals devuelve su JSON.

Cada adaptador de `evals/procesos/` corre en su propio intérprete y devuelve el
resultado por stdout. Ese canal NO es nuestro: cualquier librería que el
servicio importe puede escribir ahí (PyMuPDF avisa por stdout de que `fitz`
está deprecado, y el 2026-09-12 eso tumbó la corrida entera con un
`JSONDecodeError: Expecting value: line 1 column 1`, con el JSON intacto en la
línea siguiente). Filtrar ese aviso concreto por su texto solo aplaza el
problema hasta la siguiente librería habladora.

Aquí se arregla por los dos extremos, que son dos barreras independientes:

- **El que escribe blinda su stdout** (`blindar_stdout`): se redirige el
  descriptor 1 al 2 a nivel de sistema operativo, así que a partir de esa
  llamada nadie —ni Python ni una librería en C— puede escribir en el canal
  limpio; el ruido sale por stderr, que es donde el lector ya mira cuando algo
  falla, en vez de perderse.
- **El que lee delimita el JSON** (`leer`): la carga viaja entre dos marcas
  inequívocas, así que sobrevive a lo que se haya colado ANTES de que el
  subproceso ejecutara su primera línea (el aviso de un `sitecustomize`, el
  banner de un intérprete), que es justo lo que el blindaje no puede evitar.
"""

from __future__ import annotations

import json
import os
import sys

#: Delimitadores de la carga. Improbables en la salida de cualquier librería y
#: fáciles de reconocer a ojo cuando alguien lanza el subproceso a mano.
MARCA_INICIO = "<<<EVALS-JSON-INICIO>>>"
MARCA_FIN = "<<<EVALS-JSON-FIN>>>"

#: Copia del descriptor 1 original, la que sigue apuntando al canal limpio.
_FD_LIMPIO: int | None = None


def blindar_stdout() -> None:  # pragma: no cover - solo corre en el subproceso
    """Deja el stdout del proceso fuera del alcance de todos menos de `emitir`.

    Idempotente: llamarla dos veces no pierde el descriptor original.
    """
    global _FD_LIMPIO
    if _FD_LIMPIO is not None:
        return
    sys.stdout.flush()
    _FD_LIMPIO = os.dup(1)
    os.dup2(2, 1)


def emitir(salida: dict) -> None:  # pragma: no cover - solo corre en el subproceso
    """Escribe la carga delimitada en el canal limpio y la vacía del búfer."""
    carga = json.dumps(salida, ensure_ascii=False)
    mensaje = f"\n{MARCA_INICIO}\n{carga}\n{MARCA_FIN}\n".encode("utf-8")
    destino = 1 if _FD_LIMPIO is None else _FD_LIMPIO
    escrito = 0
    while escrito < len(mensaje):
        escrito += os.write(destino, mensaje[escrito:])


def leer(stdout: str, servicio: str) -> dict:
    """Recupera la carga que `emitir` dejó en el stdout del subproceso.

    Se queda con la ÚLTIMA marcada: la que emitió el subproceso al terminar va
    siempre después de cualquier cosa que se haya impreso durante el trabajo.
    """
    inicio = stdout.rfind(MARCA_INICIO)
    if inicio < 0:
        raise RuntimeError(
            f"el subproceso de {servicio} no devolvió JSON delimitado. "
            f"Esto es lo que escribió en stdout:\n{_recorte(stdout)}"
        )
    resto = stdout[inicio + len(MARCA_INICIO) :]
    fin = resto.find(MARCA_FIN)
    if fin < 0:
        raise RuntimeError(
            f"el subproceso de {servicio} devolvió el JSON cortado (falta la "
            f"marca de fin). Esto es lo que llegó:\n{_recorte(resto)}"
        )
    try:
        return json.loads(resto[:fin])
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"el subproceso de {servicio} delimitó algo que no es JSON "
            f"({error}):\n{_recorte(resto[:fin])}"
        ) from error


def _recorte(texto: str, tope: int = 2000) -> str:
    """Lo suficiente para diagnosticar sin volcar megas en el traceback."""
    texto = texto.strip()
    if not texto:
        return "(nada)"
    if len(texto) <= tope:
        return texto
    return f"{texto[:tope]}… (+{len(texto) - tope} caracteres)"
