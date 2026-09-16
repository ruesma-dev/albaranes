# evals/revision/mapa.py
"""El mapa versionado `caso_id` ↔ código ↔ nombre ↔ formato ↔ gemelo (R7).

Es lo que permite volver del caso al papel cuando un eval falla. Sin él, un
`HOR-012` en rojo no se audita: nadie sabe qué documento abrir, porque los
originales se renombran a `<caso_id>` y su nombre de proveedor se pierde.

Se versiona (no lleva ni precios ni datos de proveedor: solo códigos de
albarán y nombres de fichero) y se escribe determinista —claves ordenadas, sin
fecha de generación— para que dos importaciones iguales den el mismo byte.
"""

from __future__ import annotations

import json
from pathlib import Path

#: Junto a los fixtures, no dentro del paquete: es dato del banco, no del
#: importador, y se consulta desde fuera cuando un caso sale en rojo.
RUTA_MAPA = Path(__file__).resolve().parents[1] / "mapa_casos.json"

_DOC = (
    "Mapa del banco de evals: de cada caso_id al albaran de papel del que "
    "salio (F-045, R7). GENERADO por 'python -m evals.revision'; se puede "
    "corregir a mano, pero una importacion posterior manda. 'clave' es "
    "CIF/codigo normalizado y es lo que identifica el albaran entre "
    "importaciones; 'codigo' es el que escribe el humano en el Excel, que NO "
    "es el literal impreso (0000168 en la tabla, SS-0000168 en el papel); "
    "'nombre_original' es el fichero tal como llego, antes del renombrado a "
    "<caso_id>; 'gemelo_de' hermana el caso de imagen con el de PDF (R22)."
)

#: Campos que todo registro del mapa declara, aunque vengan vacíos.
CAMPOS = (
    "clave",
    "codigo",
    "nombre_original",
    "formato",
    "gemelo_de",
    "pestana",
    # La familia de DOCUMENTO del catálogo, que no cabe en los libros:
    # `INPUTS.CASOS.tipologia` lleva la pestaña porque es lo que leen sv5 y
    # sv6 (ver `reparto._inputs_caso`). Aquí es donde se consulta.
    "familia_documento",
    # En qué grupo quedó el caso la última vez. Sin esta memoria no hay
    # forma de avisar de que un caso ha cambiado de bando, y cambiar de
    # bando cambia lo que se le exige: un defecto conocido que pasa a no
    # regresión tiene que empezar a salir VERDE.
    "clasificacion",
)


def cargar(ruta: Path | str = RUTA_MAPA) -> dict[str, dict]:
    """El mapa como `{caso_id: registro}`. Sin fichero, mapa vacío."""
    camino = Path(ruta)
    if not camino.is_file():
        return {}
    datos = json.loads(camino.read_text(encoding="utf-8"))
    return dict(datos.get("casos", {}))


def guardar(mapa: dict[str, dict], ruta: Path | str = RUTA_MAPA) -> None:
    """Escribe el mapa ordenado y sin reloj: mismo contenido, mismo byte."""
    completo = {
        caso_id: {campo: registro.get(campo) for campo in CAMPOS}
        for caso_id, registro in sorted(mapa.items())
    }
    texto = json.dumps(
        {"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=True
    )
    Path(ruta).write_text(texto + "\n", encoding="utf-8")


def por_clave(mapa: dict[str, dict]) -> dict[str, str]:
    """Índice inverso `clave natural -> caso_id`, que es como se reutiliza (R8)."""
    return {
        str(registro["clave"]): caso_id
        for caso_id, registro in mapa.items()
        if registro.get("clave")
    }
