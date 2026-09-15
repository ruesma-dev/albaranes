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
    COLUMNAS,
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


def recuento_vacios(
    filas: list[FilaPlana], vocab: Vocabulario
) -> dict[str, dict[str, object]]:
    """Cuántas celdas con valor y cuántas vacías hay en cada columna (R14).

    Con el significado de su vacío al lado: sin él, «58 vacías en descuento»
    se lee como ceguera cuando en realidad son 58 líneas sin descuento.
    """
    recuento = {
        columna: {"valor": 0, "vacia": 0, "significado": vocab.politica_vacio(columna)}
        for columna in COLUMNAS
    }
    for fila in filas:
        for columna in COLUMNAS:
            clave = "vacia" if fila.vacia(columna) else "valor"
            recuento[columna][clave] = int(recuento[columna][clave]) + 1
    return recuento


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
    comentario = " | ".join(caso.comentarios) or None

    tablas["IA1"]["cabeceras"].append(_ia1_cabecera(caso, comentario))
    tablas["INPUTS"]["caso"].append(_inputs_caso(caso, comentario))
    tablas["FINAL"]["datos_generales"].append(_final_generales(caso, comentario, vocab))
    for linea in caso.impresas:
        tablas["IA1"]["lineas"].append(_ia1_linea(caso, linea, vocab))
        contexto = _ia2_contexto(caso, linea)
        if contexto is not None:
            tablas["IA2"]["contexto"].append(contexto)
        tablas["IA3"]["lineas_valoradas"].append(_ia3_valorada(caso, linea, vocab))
        tablas["FINAL"]["lineas"].append(_final_linea(caso, linea, vocab))
        tablas["INPUTS"]["lineas_albaran"].append(_inputs_linea(caso, linea, vocab))
        if linea.origen_contrato == "nueva":
            tablas["IA4"]["conciliacion"].append(_ia4_conciliacion(caso, linea, vocab))
    for linea in caso.deducidas:
        tablas["IA3"]["sinteticas_esperadas"].append(_ia3_sintetica(caso, linea, vocab))
        tablas["FINAL"]["lineas_anadidas"].append(_final_anadida(caso, linea, vocab))

    return tablas


def _ia1_cabecera(caso: CasoRevisado, comentario: str | None) -> dict:
    """La cabecera esperada, con las tres cegueras declaradas de R13.

    `numero_albaran`, `obra_codigo` y `obra_nombre` van `?` a propósito: el
    código de la tabla plana es la clave con la que el humano identifica el
    documento (`0000168`), no el literal impreso (`SS-0000168`), y deducir la
    obra no es extraer. Es el mismo criterio con el que están escritos los 7
    casos RES que ya había en el banco.
    """
    return {
        "caso_id": caso.caso_id,
        "fichero_albaran": caso.fichero or None,
        "proveedor_nombre": caso.lineas[0].fila.texto("nombre_empresa") or INTERROGANTE,
        # El CIF correcto es el del proveedor identificado, no siempre el
        # impreso: se le exige al resultado final, no a la lectura.
        "proveedor_cif": INTERROGANTE,
        "fecha": caso.lineas[0].fila.texto("fecha") or INTERROGANTE,
        "numero_albaran": INTERROGANTE,
        "obra_codigo": INTERROGANTE,
        "obra_nombre": INTERROGANTE,
        # No hay columna de forma de pago en la tabla plana. Lo que el Excel no
        # dice, no se compara: `?`, jamás un null afirmado.
        "forma_pago": INTERROGANTE,
        "comentario": comentario,
    }


def _ia2_contexto(caso: CasoRevisado, linea: LineaRevisada) -> dict | None:
    """El LER es contexto de LÍNEA, no dato de cabecera (design §3).

    Solo en residuos y solo si el humano lo afirmó: su vacío significa «no
    aplica a esta familia», y entonces no hay fila que escribir (R12).
    """
    if caso.destino.familia_documento != "residuos" or linea.fila.vacia("ler"):
        return None
    return {
        "caso_id": caso.caso_id,
        "num_linea": linea.num_linea,
        "campo_contexto": "codigo_ler",
        "valor_esperado": _NO_ALFANUMERICO.sub("", normalizar(linea.fila.texto("ler"))),
        "comentario": linea.fila.texto("comentarios") or None,
    }


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


def _ia3_valorada(caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario) -> dict:
    """Lo que el sistema DECIDE sobre una línea impresa (design §3).

    La partida final, el unitario y el importe se le exigen a la valoración
    vengan de donde vengan: el patrón 1 —la partida se lee mal— vive en la
    decisión, no solo en la lectura.
    """
    nueva = linea.origen_contrato == "nueva"
    return {
        "caso_id": caso.caso_id,
        "num_linea": linea.num_linea,
        # Que una línea NUEVA no case es afirmable; con qué método casa una del
        # contrato, no: el Excel no lo dice y suponerlo sería inventar (R11).
        "match_method": "no_match" if nueva else INTERROGANTE,
        "codigo_producto_contrato": None if nueva else _codigo_producto(caso, linea, vocab),
        "codigo_partida_final": celda(linea, "partida", vocab),
        "precio_unitario_final": celda(linea, "precio_unitario", vocab),
        "precio_source": linea.precio_source,
        "importe_calculado": celda(linea, "importe", vocab),
        "review_required": INTERROGANTE,
        "comentario": linea.fila.texto("comentarios") or None,
    }


def _codigo_producto(
    caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario
) -> object | None:
    """La columna de LER/código de producto, salvo en residuos: ahí es el LER.

    En residuos ese valor es contexto de línea y ya viajó a IA2; repetirlo aquí
    como código de contrato sería comparar una cosa contra otra distinta.
    """
    if caso.destino.familia_documento == "residuos":
        return INTERROGANTE
    return celda(linea, "ler", vocab) or INTERROGANTE


def _ia4_conciliacion(
    caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario
) -> dict:
    """Solo las líneas NUEVA llegan a la conciliación: son las que no casan."""
    return {
        "caso_id": caso.caso_id,
        "num_linea": linea.num_linea,
        # El Excel dice a qué precio acabó la línea, no si lo correcto era
        # conciliarla o dejarla a revisión humana. Eso no se supone (R11).
        "concilia": INTERROGANTE,
        "linea_contrato_esperada": INTERROGANTE,
        "precio_unitario_esperado": celda(linea, "precio_unitario", vocab),
        "motivo": None,
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


def _inputs_caso(caso: CasoRevisado, comentario: str | None) -> dict:
    """El registro maestro de la ENTRADA del caso, no una expectativa.

    `tipologia` lleva la familia de DOCUMENTO del catálogo, no la pestaña
    (design §3): la pestaña es organización del banco y las dos no siempre
    coinciden —GASOLEO vive en la pestaña Combustible—.
    """
    primera = caso.lineas[0].fila
    hay_nuevas = any(linea.origen_contrato == "nueva" for linea in caso.impresas)
    return {
        "caso_id": caso.caso_id,
        "tipologia": caso.destino.familia_documento,
        "ia_destino": "ambas" if hay_nuevas else "IA3",
        "origen": "manual",
        "contrato_codigo": primera.texto("codigo_contrato"),
        "descripcion_caso": " · ".join(
            trozo for trozo in (caso.codigo, caso.destino.etiqueta, comentario) if trozo
        ),
    }


def _inputs_linea(caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario) -> dict:
    """La línea tal como LLEGA a la valoración. Aquí nunca se escribe `?`.

    El sentinela significa «no compares», y en una entrada no hay nada que
    comparar: viajaría como texto literal dentro de la carga que lee sv5. Y el
    precio que no imprime el papel tampoco se le da: darle el del contrato es
    hacerle el trabajo que se le está evaluando.
    """
    return {
        "caso_id": caso.caso_id,
        "num_linea": linea.num_linea,
        "descripcion": linea.fila.texto("concepto") or None,
        "cantidad": _numero(linea.fila.bruto("cantidad")),
        "unidad": linea.fila.texto("unidad") or None,
        "precio_unitario": (
            _numero(linea.fila.bruto("precio_unitario")) if linea.precio_impreso else None
        ),
        "descuentos": _descuentos(linea, vocab),
        "importe": (
            _numero(linea.fila.bruto("importe")) if linea.importe_impreso else None
        ),
        "codigo_imputacion": None,
        "observaciones_albaran": None,
    }


def _final_generales(
    caso: CasoRevisado, comentario: str | None, vocab: Vocabulario
) -> dict:
    """La referencia MAESTRA: cómo debe quedar el albarán al acabar."""
    primera = caso.lineas[0].fila
    return {
        "caso_id": caso.caso_id,
        "fichero": caso.fichero or None,
        "obra": primera.texto("codigo_obra") or INTERROGANTE,
        "proveedor": primera.texto("nombre_empresa") or INTERROGANTE,
        "cif": primera.texto("cif") or INTERROGANTE,
        "fecha": primera.texto("fecha") or INTERROGANTE,
        # El código del humano (0025146) no es el literal impreso (SS-0025146).
        "numero_albaran": INTERROGANTE,
        "contrato_elegido": primera.texto("codigo_contrato") or INTERROGANTE,
        "total_valorado_esperado": _total(caso, vocab),
        "requiere_revision": INTERROGANTE,
        "motivo_revision": None,
        "comentario": comentario,
    }


def _total(caso: CasoRevisado, vocab: Vocabulario) -> object:
    """La suma de los importes, o `?` si falta alguno.

    Sumar sobre un hueco daría un total falso con pinta de bueno, y el total
    es lo primero que mira quien audita un caso en rojo.
    """
    importes = [celda(linea, "importe", vocab) for linea in caso.lineas]
    if any(not isinstance(importe, (int, float)) for importe in importes):
        return INTERROGANTE
    total = sum(importes)  # type: ignore[arg-type]
    return int(total) if float(total).is_integer() else round(total, 2)


def _final_linea(caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario) -> dict:
    """La línea impresa como debe quedar al final del proceso (TABLA 2)."""
    casa = linea.origen_contrato == "contrato"
    return {
        "caso_id": caso.caso_id,
        "num_linea": linea.num_linea,
        "descripcion": celda(linea, "concepto", vocab),
        "cantidad_final": _cantidad_final(caso, linea, vocab),
        "unidad_final": celda(linea, "unidad", vocab),
        "casa_con_contrato": "SI" if casa else "NO",
        # Sin línea de contrato con la que casar, la celda va vacía: es un null
        # afirmado. Con ella, el Excel no dice cuál es, así que `?`.
        "linea_contrato": INTERROGANTE if casa else None,
        "partida_final": celda(linea, "partida", vocab),
        "precio_unitario_final": celda(linea, "precio_unitario", vocab),
        "precio_source": linea.precio_source,
        "importe_final": celda(linea, "importe", vocab),
        "linea_a_revision": INTERROGANTE,
        "comentario": linea.fila.texto("comentarios") or None,
    }


# --- Los tres criterios de residuos (R12 bis, design §5 ter) ---------------


def _cantidad_final(
    caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario
) -> object | None:
    """La cantidad con la que se factura, con el mínimo de residuos aplicado.

    **Mínimo facturable de 1 en lo que se PESA** —canon y tratamiento—: 0,42
    factura 1; 3,10 factura 3,10. El movimiento de contenedor NO se toca:
    sigue en unidades, 1 cambio = 1 UD (§10.6 del doc de dominio). La cantidad
    LEÍDA no cambia: el papel imprime 0,42 y eso es lo que se le pide a IA1.
    """
    cantidad = celda(linea, "cantidad", vocab)
    if not _pesa(caso, linea, vocab) or not isinstance(cantidad, (int, float)):
        return cantidad
    return max(cantidad, vocab.minimo_residuos)


def _pesa(caso: CasoRevisado, linea: LineaRevisada, vocab: Vocabulario) -> bool:
    """La línea es de residuos y su unidad no es de conteo: se pesa o se mide."""
    return caso.destino.familia_documento == "residuos" and not vocab.es_unidad_de_conteo(
        linea.fila.texto("unidad")
    )


def criterios_residuos(caso: CasoRevisado, vocab: Vocabulario) -> list[str]:
    """Qué criterios de §5 ter toca este caso. **Ninguno está implementado**.

    Se devuelven para que el informe agrupe esos casos aparte: un rojo
    esperado que se mezcla con los defectos reales deja de ser información.
    Las marcas se buscan en el texto con el que el HUMANO describió la línea
    deducida y su concepto: es leer lo que escribió, no adivinar.
    """
    if caso.destino.familia_documento != "residuos":
        return []
    tocados: list[str] = []
    texto = " ".join(
        normalizar(f"{linea.fila.texto('origen_linea')} {linea.fila.texto('concepto')}")
        for linea in caso.deducidas
    )
    for criterio, definicion in vocab.criterios_residuos.items():
        marcas = definicion["marcas"]
        if marcas:
            if any(normalizar(marca) in texto for marca in marcas):
                tocados.append(criterio)
        elif any(_pesa(caso, linea, vocab) for linea in caso.lineas):
            tocados.append(criterio)
    return tocados
