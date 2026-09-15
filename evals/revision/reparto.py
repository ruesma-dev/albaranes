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

from evals.revision.modelos import (
    DEFECTO_CONOCIDO,
    NO_REGRESION,
    CasoRevisado,
    FilaPlana,
    LineaRevisada,
)
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


# --- Convenios de celda (R11, R12) -----------------------------------------

#: Sentinela `?` de los libros: «no compares este campo en este caso».
INTERROGANTE = "?"

#: Las tablas que este importador alimenta. `INPUTS.CONTRATO_LINEAS`,
#: `INPUTS.CONDICIONES` e `IA3` TABLA 3 quedan fuera a propósito (design §3):
#: la revisión manual no trae líneas de contrato, y lo que no alimenta tampoco
#: lo toca. Sin líneas de contrato los casos nuevos solo son evaluables con
#: LLM; la corrida determinista sigue viviendo de los 7 RES.
TABLAS: dict[str, tuple[str, ...]] = {
    "IA1": ("cabeceras", "lineas"),
    "IA2": ("contexto",),
    "IA3": ("lineas_valoradas", "sinteticas_esperadas"),
    "IA4": ("conciliacion",),
    "INPUTS": ("caso", "lineas_albaran"),
    "FINAL": ("datos_generales", "lineas", "lineas_anadidas"),
}


def _numero(valor: object | None) -> object | None:
    """Los importes y cantidades viajan como número si lo son."""
    if isinstance(valor, bool) or valor is None:
        return valor
    if isinstance(valor, (int, float)):
        return valor
    texto = str(valor).strip().replace(" ", "")
    if not texto:
        return None
    try:
        return float(texto.replace(",", ".")) if texto.count(",") == 1 else float(texto)
    except ValueError:
        return valor


def celda(linea: LineaRevisada, columna: str, vocab: Vocabulario) -> object | None:
    """El valor de una columna aplicando su política de vacío (R11, R12).

    `nulo` = el humano afirma que no hay valor (vacío en el libro, que se
    compara contra `null`); `interrogante` = no lo ha afirmado y se escribe
    `?`, que NO se compara. Nunca un valor supuesto.
    """
    if not linea.fila.vacia(columna):
        return _numero(linea.fila.bruto(columna))
    return None if vocab.politica_vacio(columna) == "nulo" else INTERROGANTE


def _descuentos(linea: LineaRevisada, vocab: Vocabulario) -> object | None:
    """La columna viene en fracción (0,4) y el libro guarda el % impreso (40).

    Sin descuento —vacío o cero— se escribe vacío: es lo mismo que decir «sin
    descuento», y es el factor 1 de la fórmula canónica de ARCHITECTURE §13.
    """
    bruto = _numero(linea.fila.bruto("descuento"))
    if not isinstance(bruto, (int, float)) or not bruto:
        return None
    porcentaje = bruto * vocab.factor_descuento
    return int(porcentaje) if float(porcentaje).is_integer() else porcentaje


def _base(linea: LineaRevisada) -> object:
    """El `num_linea_base` de una sintética, o `?` si no hay impresa delante."""
    return INTERROGANTE if linea.num_linea is None else linea.num_linea


# --- Los dos ejes del vacío (R9, R10) --------------------------------------


def clasificar(casos: list[CasoRevisado]) -> dict[str, list[CasoRevisado]]:
    """Reparte los casos entre no regresión y defecto conocido.

    El comentario del Excel es el diagnóstico de HOY, no el resultado
    esperado. Vacío significa que ese caso salió BIEN y hay que seguir
    comprobando que lo sigue haciendo: son los que avisan de que hemos roto
    algo que funcionaba, y NUNCA producen un `?`. Con texto, el caso es un
    defecto conocido: rojo esperado hasta que exista su arreglo, y se compara
    exactamente igual.
    """
    grupos: dict[str, list[CasoRevisado]] = {NO_REGRESION: [], DEFECTO_CONOCIDO: []}
    for caso in casos:
        grupos[caso.clasificacion].append(caso)
    return grupos


# --- El reparto (design §3, NORMATIVA) -------------------------------------


def repartir(caso: CasoRevisado, vocab: Vocabulario) -> dict[str, dict[str, list[dict]]]:
    """Reparte un caso entre las tablas de los seis libros."""
    tablas: dict[str, dict[str, list[dict]]] = {
        libro: {tabla: [] for tabla in nombres} for libro, nombres in TABLAS.items()
    }
    comentario = " | ".join(caso.comentarios)

    for linea in caso.impresas:
        tablas["IA1"]["lineas"].append(_ia1_linea(caso, linea, vocab))
    for linea in caso.deducidas:
        tablas["IA3"]["sinteticas_esperadas"].append(_ia3_sintetica(caso, linea, vocab))
        tablas["FINAL"]["lineas_anadidas"].append(_final_anadida(caso, linea, vocab))

    del comentario
    return tablas


def _ia1_linea(caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario) -> dict:
    """Solo lo que el papel IMPRIME. Lo que decide el sistema no es de IA1."""
    return {
        "caso_id": caso.caso_id,
        "num_linea": linea.num_linea,
        "descripcion_esperada": celda(linea, "concepto", vocab),
        "cantidad": celda(linea, "cantidad", vocab),
        "unidad": celda(linea, "unidad", vocab),
        # R4: si el unitario sale del contrato o de una oferta, en el papel NO
        # está, y la celda va vacía (null afirmado), nunca `?`.
        "precio_unitario": (
            celda(linea, "precio_unitario", vocab) if linea.precio_impreso else None
        ),
        "descuentos": _descuentos(linea, vocab),
        "importe": celda(linea, "importe", vocab) if linea.importe_impreso else None,
        # D4: la tabla plana no dice si la partida venía impresa en el papel,
        # así que la lectura de la partida no se vigila; su decisión sí, en
        # IA3 y en el FINAL, que es donde vive el patrón 1.
        "codigo_imputacion": INTERROGANTE,
        "comentario": linea.fila.texto("comentarios") or None,
    }


def _ia3_sintetica(caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario) -> dict:
    """Una línea deducida es una sintética que el sistema DEBE emitir."""
    return {
        "caso_id": caso.caso_id,
        "num_linea_base": _base(linea),
        # El Excel dice que la línea se dedujo, no con qué `modifier_source`
        # del catálogo de sv5: entre `year_contract` y `year_albaran` no hay
        # forma de decidir desde la tabla, y suponerlo sería inventar (R11).
        "modifier_source": INTERROGANTE,
        "rol_linea": INTERROGANTE,
        "descripcion_esperada": celda(linea, "concepto", vocab),
        "cantidad": _cantidad_final(caso, linea, vocab),
        "precio_unitario": celda(linea, "precio_unitario", vocab),
        "codigo_partida": celda(linea, "partida", vocab),
        "comentario": linea.fila.texto("comentarios") or None,
    }


def _final_anadida(caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario) -> dict:
    """La misma línea deducida, vista por el administrativo (TABLA 3)."""
    return {
        "caso_id": caso.caso_id,
        "num_linea_base": _base(linea),
        "concepto": celda(linea, "concepto", vocab),
        "cantidad": _cantidad_final(caso, linea, vocab),
        "precio_unitario": celda(linea, "precio_unitario", vocab),
        "partida": celda(linea, "partida", vocab),
        "importe": celda(linea, "importe", vocab),
        "comentario": linea.fila.texto("comentarios") or None,
    }


def _cantidad_final(
    caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario
) -> object | None:
    """La cantidad con la que se factura (de momento, la leída)."""
    return celda(linea, "cantidad", vocab)
