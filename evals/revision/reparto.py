# evals/revision/reparto.py
"""El núcleo: de filas planas a las tablas de los seis libros. Puro.

Ni openpyxl ni disco: `dict` in, `dict` out. Aquí vive la tabla de reparto de
`design.md` §3, que es normativa y la validó el humano el 2026-09-15.

La idea que ordena todo el módulo: **el Excel mezcla en una sola fila lo que
el papel imprime y lo que el sistema decide**, y separarlo es justamente el
trabajo. Lo impreso se le exige a la EXTRACCIÓN (IA1/IA2); lo decidido, a la
VALORACIÓN (IA3/IA4) y al resultado final. Pedirle a IA1 un precio que solo
está en el contrato sería un rojo permanente que no dice nada de nadie.
"""

from __future__ import annotations

import re

from evals.revision.modelos import CasoRevisado, FilaPlana, LineaRevisada
from evals.revision.vocabulario import ErrorVocabulario, Vocabulario, normalizar

_NO_ALFANUMERICO = re.compile(r"[^0-9A-Z]+")
_NUMERO_CASO = re.compile(r"^(?P<prefijo>[A-Z]+)-(?P<numero>\d+)")


class ErrorReparto(RuntimeError):
    """La fila plana no permite construir ni siquiera la identidad del caso."""


def normalizar_codigo(texto: object | None) -> str:
    """`2.115.714` → `2115714`; `MC/26-442903` → `MC26442903`.

    Se quita la puntuación y **se respetan los ceros a la izquierda**: el
    precedente del proyecto es `SS-0801977` leído donde el papel decía
    `SS-0001977`, y un normalizador que se comiera los ceros los confundiría.
    """
    if texto is None:
        return ""
    return _NO_ALFANUMERICO.sub("", normalizar(texto))


def clave_natural(fila: FilaPlana) -> str:
    """CIF + código normalizado: dos proveedores pueden numerar igual."""
    codigo = normalizar_codigo(fila.texto("codigo_albaran"))
    if not codigo:
        raise ErrorReparto(
            f"fila {fila.numero_fila}: sin código de albarán no hay caso al que "
            f"pertenezca la línea."
        )
    return f"{normalizar_codigo(fila.texto('cif'))}/{codigo}"


# --- De filas a casos -------------------------------------------------------


def _interpretar(fila: FilaPlana, vocab: Vocabulario, num_linea: int | None,
                 contador: int) -> tuple[LineaRevisada, int]:
    """Traduce los tres ejes de origen de UNA fila y le da su número de línea."""
    origen_linea = vocab.origen_linea(fila.texto("origen_linea"), fila.numero_fila)
    precio = vocab.origen_precio(fila.texto("origen_precio"), fila.numero_fila)
    importe = vocab.origen_precio(fila.texto("origen_importe"), fila.numero_fila)
    if origen_linea == "impresa":
        contador += 1
        propio: int | None = contador
    else:
        # Una deducida cuelga de la última impresa: es su `num_linea_base`.
        propio = num_linea
    return (
        LineaRevisada(
            fila=fila,
            origen_linea=origen_linea,
            origen_contrato=vocab.origen_contrato(
                fila.texto("origen_contrato"), fila.numero_fila
            ),
            precio_source=precio.precio_source,
            precio_impreso=precio.impreso,
            importe_source=importe.precio_source,
            importe_impreso=importe.impreso,
            num_linea=propio,
        ),
        contador,
    )


def agrupar_por_albaran(
    filas: list[FilaPlana], vocab: Vocabulario
) -> list[CasoRevisado]:
    """Una fila por línea; un caso por albarán. Respeta el orden del Excel.

    Las filas cuyo vocabulario no se reconoce se acumulan y hacen abortar la
    importación entera al final (R5): media importación es peor que ninguna.
    """
    casos: dict[str, CasoRevisado] = {}
    contadores: dict[str, int] = {}
    ultimo: dict[str, int | None] = {}

    for fila in filas:
        clave = clave_natural(fila)
        try:
            destino = vocab.etiqueta(fila.texto("tipo_albaran"), fila.numero_fila)
            linea, contador = _interpretar(
                fila, vocab, ultimo.get(clave), contadores.get(clave, 0)
            )
        except ErrorVocabulario:
            continue  # ya acumulado; se listan todos juntos en `comprobar`
        caso = casos.get(clave)
        if caso is None:
            caso = CasoRevisado(
                codigo=fila.texto("codigo_albaran"), clave=clave, destino=destino
            )
            casos[clave] = caso
        caso.lineas.append(linea)
        contadores[clave] = contador
        if linea.es_impresa:
            ultimo[clave] = linea.num_linea

    vocab.comprobar()
    return list(casos.values())


# --- caso_id estable (R7, R8) ----------------------------------------------


def asignar_casos_id(
    casos: list[CasoRevisado], mapa: dict[str, dict]
) -> tuple[dict[str, dict], list[str]]:
    """Reutiliza el `caso_id` del mapa y numera solo lo nuevo.

    Devuelve el mapa actualizado y los `caso_id` creados en esta pasada. Que
    reimportar NO cree casos nuevos es lo que hace del banco algo reejecutable:
    el Excel del humano cambia cada semana.
    """
    actualizado = {caso_id: dict(registro) for caso_id, registro in mapa.items()}
    conocidos = {
        str(registro.get("clave")): caso_id
        for caso_id, registro in actualizado.items()
        if registro.get("clave")
    }
    siguiente = _ultimos_numeros(actualizado)
    nuevos: list[str] = []

    for caso in casos:
        caso_id = conocidos.get(caso.clave)
        if caso_id is None:
            prefijo = caso.destino.prefijo
            siguiente[prefijo] = siguiente.get(prefijo, 0) + 1
            caso_id = f"{prefijo}-{siguiente[prefijo]:03d}"
            conocidos[caso.clave] = caso_id
            nuevos.append(caso_id)
        caso.caso_id = caso_id
        registro = actualizado.setdefault(caso_id, {})
        registro.update(
            {
                "clave": caso.clave,
                "codigo": caso.codigo,
                "pestana": caso.destino.pestana,
                "gemelo_de": caso.gemelo_de or None,
            }
        )
        registro.setdefault("nombre_original", "")
        registro.setdefault("formato", "")
    return actualizado, nuevos


def _ultimos_numeros(mapa: dict[str, dict]) -> dict[str, int]:
    """El número más alto ya usado por prefijo: numerar nunca reinicia."""
    ultimos: dict[str, int] = {}
    for caso_id in mapa:
        casado = _NUMERO_CASO.match(caso_id)
        if casado:
            prefijo = casado.group("prefijo")
            numero = int(casado.group("numero"))
            ultimos[prefijo] = max(ultimos.get(prefijo, 0), numero)
    return ultimos
