# evals/revision/huella.py
"""Qué filas escribió el importador la vez anterior, para poder retirarlas.

La fusión conservadora (R17) **mantiene lo que el importador no genera**, y esa
regla salvó los 7 casos RES escritos a mano. Pero tiene un reverso: cuando el
importador deja de producir una fila que ÉL MISMO escribió antes, esa fila se
queda para siempre.

Pasó de verdad el 2026-09-16. Hasta entonces el incremento por LER se volcaba
como línea de `IA1`; cuando el humano aclaró que **se deduce del contrato** y el
volcado pasó a escribirlo como sintética de `IA3`, las líneas viejas de `IA1`
seguían ahí y el banco exigía la misma cosa por los dos caminos —contradicción
imposible de cumplir—.

De ahí esta huella: un fichero versionado con las CLAVES de las filas que el
importador escribió, tabla por tabla. Lo que está en la huella y ya no se
produce, se retira; lo que no está, se conserva, porque no es suyo.

No guarda valores, solo claves: no lleva precios ni datos de proveedor, y se
lee de un vistazo en un diff.
"""

from __future__ import annotations

import json
from pathlib import Path

#: Junto al mapa de casos, que es el otro fichero de control del volcado.
RUTA_HUELLA = Path(__file__).resolve().parents[1] / "huella_importacion.json"

_DOC = (
    "Claves de las filas que 'python -m evals.revision' escribio en la ultima "
    "importacion, por tabla. GENERADO: no se edita a mano. Sirve para una sola "
    "cosa y no es poca: distinguir lo que escribio el importador -y por tanto "
    "puede retirar cuando deja de producirlo- de lo que escribio el humano a "
    "mano, que no se toca jamas (R17). Sin este fichero el importador conserva "
    "todo, que es el comportamiento de antes."
)


def cargar(ruta: Path | str = RUTA_HUELLA) -> dict[str, list[list[str]]]:
    """La huella de la importación anterior. Sin fichero, huella vacía."""
    camino = Path(ruta)
    if not camino.is_file():
        return {}
    return dict(json.loads(camino.read_text(encoding="utf-8")).get("tablas", {}))


def guardar(
    tablas: dict[str, list[list[str]]], ruta: Path | str = RUTA_HUELLA
) -> None:
    """Determinista: mismas filas, mismo byte."""
    ordenadas = {
        tabla: sorted(claves) for tabla, claves in sorted(tablas.items()) if claves
    }
    texto = json.dumps(
        {"_doc": _DOC, "tablas": ordenadas}, ensure_ascii=False, indent=2, sort_keys=True
    )
    Path(ruta).write_text(texto + "\n", encoding="utf-8")


def claves_de(huella: dict[str, list[list[str]]], tabla: str) -> set[tuple[str, ...]]:
    """Las claves de una tabla, como las compara `escritura.fundir_filas`."""
    return {tuple(str(parte) for parte in clave) for clave in huella.get(tabla, [])}


def anotar(
    tablas_por_fase: dict[str, dict[str, list[dict]]],
    claves_por_tabla: dict[str, tuple[str, ...]],
) -> dict[str, list[list[str]]]:
    """La huella de ESTA importación, a partir de lo que se acaba de repartir."""
    huella: dict[str, list[list[str]]] = {}
    for por_tabla in tablas_por_fase.values():
        for tabla, filas in por_tabla.items():
            campos = claves_por_tabla.get(tabla)
            if not campos:
                continue
            for fila in filas:
                clave = [str(fila.get(campo, "")).strip() for campo in campos]
                huella.setdefault(tabla, []).append(clave)
    return huella
