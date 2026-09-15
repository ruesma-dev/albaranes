# evals/revision/escritura.py
"""Escribe los libros de ground truth. Infraestructura: aquí vive openpyxl.

Tres cosas que este módulo hace a propósito:

1. **Copia antes de escribir** (R16). Los libros los rellena una persona y no
   se versionan: si el importador los estropea, no hay `git checkout` que
   valga. La copia va a `ground_truth/copias/` con la fecha en el nombre.
2. **Las tablas se localizan por su fila de título**, no por coordenadas:
   el humano añade y quita filas y las posiciones se mueven. Mismo criterio
   que `evals/conversor.py`, que es quien luego las lee.
3. **Fusión conservadora, no volcado** (R17, R8). El importador actualiza las
   filas de SUS casos, pero nunca degrada a `?` una celda que ya tenía valor
   afirmado, y deja intactas las filas que no genera. El banco ya tenía 7
   casos escritos a mano con mucho más detalle del que cabe en la tabla plana
   —`match_method` semántico, el número real del albarán, el volumen en m3—;
   un volcado a pelo los habría barrido en la primera pasada.
"""

from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path

#: Dónde se deja la copia de seguridad previa (R16).
NOMBRE_COPIAS = "copias"

#: Pestaña de la que se copia la estructura de una tipología nueva.
PLANTILLA = "Generico-Suministros"


class ErrorEscritura(RuntimeError):
    """El libro no tiene la forma que el contrato de datos declara."""


def copia_de_seguridad(ruta: Path | str, momento: dt.datetime | None = None) -> Path:
    """`IA1_extraccion.xlsx` → `copias/IA1_extraccion.xlsx.20260915-1830.xlsx`."""
    origen = Path(ruta)
    if not origen.is_file():
        raise ErrorEscritura(f"no existe el libro '{origen}'.")
    sello = (momento or dt.datetime.now()).strftime("%Y%m%d-%H%M")
    destino = origen.parent / NOMBRE_COPIAS / f"{origen.name}.{sello}.xlsx"
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)
    return destino


def asegurar_pestanas(libro, pestanas: tuple[str, ...], plantilla: str = PLANTILLA) -> list[str]:
    """Crea las pestañas que falten copiando la estructura de la plantilla.

    `Grava` y `Ferreteria` no existían en los libros: se crean copiando
    `Generico-Suministros`, que trae las mismas tablas y encabezados y ningún
    caso. Sin plantilla NO se inventa nada: un libro con una pestaña de
    estructura improvisada rompería el conversor más tarde y más lejos.
    """
    creadas: list[str] = []
    for pestana in pestanas:
        if pestana in libro.sheetnames:
            continue
        if plantilla not in libro.sheetnames:
            raise ErrorEscritura(
                f"falta la pestaña '{pestana}' y no está la plantilla "
                f"'{plantilla}' de la que copiar su estructura."
            )
        copia = libro.copy_worksheet(libro[plantilla])
        copia.title = pestana
        creadas.append(pestana)
    return creadas
