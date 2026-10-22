# evals/contratos.py
"""Líneas y documento del contrato de los casos del banco (F-084).

    python -m evals.contratos lineas     [--dry-run] [--casos A,B]
    python -m evals.contratos documentos [--casos A,B]

El banco valoraba sin contrato: 52 de los 59 casos de `INPUTS` no traían ni
una línea (hueco de F-045) y la IA3 recibía `lineas_contrato: []`. Este módulo
lo cierra **por el libro** `INPUTS.xlsx`, no por los fixtures: el conversor
regenera los JSON desde los libros y pisaría cualquier cosa escrita a mano.

- `lineas` lee de sigrid-api (solo `POST /api/sql/read`, un `SELECT` por
  código de contrato) las líneas del contrato y las escribe en la pestaña
  `CONTRATO_LINEAS` del libro, con copia de seguridad y fusión conservadora
  (`evals/revision/escritura.py`). Los casos que ya tienen líneas (los 7 RES,
  escritos a mano con sus señuelos) no se tocan (R6).
- `documentos` lee en solo lectura la cabecera del contrato que sv3 dejó en la
  BBDD `albaranes` y su documento en SharePoint, con la SQL y el descargador
  de sv5 (`evals/procesos/sv5_documentos.py`), y deja el documento en la caché
  local no versionada y su huella en el índice versionado.

Los dos los lanza el humano, con sus credenciales en la consola. Ninguno
escribe en ningún sistema: solo el libro, la caché y el índice locales.
El informe (`progress/import_F-084.md`) lleva recuentos, `caso_id` y
`num_linea`: ni precios ni descripciones del contrato (R10).
"""

from __future__ import annotations

from evals.modelos import NO_COMPARAR

#: (R2) La consulta de Sigrid, solo lectura y parametrizada por código. Mismas
#: uniones que `_SQL_HEADER_AND_LINES` de sv3, para que cada columna signifique
#: lo que acaba en `albaran_contrato_lines_merge`; `ORDER BY` estable. La SQL
#: de cada cliente de Sigrid no se comparte (D2 de F-052).
SQL_LINEAS_CONTRATO = """\
SELECT
    ctr.ide         AS contrato_ide,
    ctrpro.ide      AS linea_sigrid,
    con_pro.cod     AS codigo_producto,
    ctrpro.res      AS descripcion_recurso,
    ctrpro.unimed   AS unidad,
    ctrpro.pre      AS precio_unitario,
    obrparpar.cod   AS codigo_partida
FROM ctr
JOIN con AS con_ctr      ON ctr.ide = con_ctr.ide
JOIN ctrpro              ON ctrpro.docide = ctr.ide
LEFT JOIN pro            ON ctrpro.proide = pro.ide
LEFT JOIN con AS con_pro ON pro.ide = con_pro.ide
LEFT JOIN obrparpar      ON ctrpro.paride = obrparpar.ide
WHERE con_ctr.cod = ? AND con_ctr.emp = 1
ORDER BY ctr.ide, ctrpro.pos, ctrpro.ide"""

#: Columnas de `CONTRATO_LINEAS` que salen de cada fila de Sigrid.
COLUMNAS_LINEA = (
    "codigo_producto",
    "descripcion_recurso",
    "unidad",
    "precio_unitario",
    "codigo_partida",
    "linea_sigrid",
)

#: Lo que el banco espera de un precio «de contrato» en IA3 (R10).
PRECIO_DE_CONTRATO = "contrato_db"


class ErrorContrato(RuntimeError):
    """UN contrato no se puede importar; los demás siguen (R4, R5)."""


# --- Parte pura del subcomando `lineas` --------------------------------------


def _tablas(fixture: dict, nombre: str) -> list[dict]:
    return list((fixture or {}).get("tablas", {}).get(nombre, []))


def _texto(dato: object | None) -> str:
    """El valor como texto limpio; el sentinela `?` cuenta como vacío."""
    if dato is None or dato == NO_COMPARAR:
        return ""
    return str(dato).strip()


def contratos_de_casos(inputs: dict[str, dict]) -> dict[str, list[str]]:
    """(R1, R6) Código de contrato → casos SIN líneas de contrato que lo usan.

    Un caso que ya tiene líneas en INPUTS no entra: son los 7 RES escritos a
    mano, con señuelos que Sigrid no tiene. Una consulta por código distinto,
    no por caso: diez casos del mismo contrato son una sola lectura.
    """
    por_codigo: dict[str, list[str]] = {}
    for caso_id, fixture in sorted(inputs.items()):
        if _tablas(fixture, "contrato_lineas"):
            continue
        caso = (_tablas(fixture, "caso") or [{}])[0]
        codigo = _texto(caso.get("contrato_codigo"))
        if codigo:
            por_codigo.setdefault(codigo, []).append(caso_id)
    return dict(sorted(por_codigo.items()))


def filas_de_respuesta(columnas: list[str], filas: list[list], codigo: str) -> list[dict]:
    """(R1, R5) Las filas de sigrid-api como líneas de `CONTRATO_LINEAS`.

    El código tiene que casar con UN contrato (`ctr.ide`): con ninguno no hay
    nada que importar y con dos no se sabe cuál es el del caso. En los dos
    casos falla ESE contrato, con su motivo, y no se escribe nada de él.
    """
    registros = [dict(zip(columnas, fila)) for fila in filas]
    if not registros:
        raise ErrorContrato(
            f"{codigo}: ningún contrato con líneas con ese código en Sigrid (emp = 1)"
        )
    ides = {registro.get("contrato_ide") for registro in registros}
    if len(ides) > 1:
        raise ErrorContrato(f"{codigo}: {len(ides)} contratos (ctr.ide) con ese código")
    return [{columna: registro.get(columna) for columna in COLUMNAS_LINEA} for registro in registros]


def filas_por_caso(lineas: list[dict], caso_ids: list[str], fecha_import: str) -> list[dict]:
    """(R1) Una fila por línea y caso, con la marca de dónde salió."""
    comentario = f"importada de sigrid-api el {fecha_import} (F-084)"
    return [
        {"caso_id": caso_id, **linea, "comentario": comentario}
        for caso_id in caso_ids
        for linea in lineas
    ]


def condiciones_fecha(inputs: dict[str, dict], ia1: dict[str, dict]) -> list[dict]:
    """(R9) `fecha_albaran` en CONDICIONES para los casos que no la declaran.

    Sale de `IA1.cabeceras.fecha` del mismo caso; sin ella no se escribe nada.
    Nunca pisa una fecha que el caso ya trae (la escribió el humano).
    """
    filas = []
    for caso_id, fixture in sorted(inputs.items()):
        campos = {_texto(fila.get("campo")) for fila in _tablas(fixture, "condiciones")}
        if "fecha_albaran" in campos:
            continue
        cabecera = (_tablas(ia1.get(caso_id, {}), "cabeceras") or [{}])[0]
        fecha = _texto(cabecera.get("fecha"))
        if not fecha:
            continue
        filas.append(
            {
                "caso_id": caso_id,
                "campo": "fecha_albaran",
                "valor": fecha,
                "comentario": "fecha de IA1.cabeceras (F-084)",
            }
        )
    return filas


def _precio(dato: object | None) -> float | None:
    if isinstance(dato, bool):
        return None
    try:
        return round(float(str(dato).replace(",", ".")), 4)
    except (TypeError, ValueError):
        return None


def _esperadas_de_contrato(ia3: dict) -> list[tuple[int, float]]:
    """(num_linea, precio) de las líneas IA3 que esperan un precio de contrato."""
    esperadas = []
    for fila in _tablas(ia3, "lineas_valoradas"):
        precio = _precio(fila.get("precio_unitario_final"))
        if fila.get("precio_source") != PRECIO_DE_CONTRATO or precio is None:
            continue
        esperadas.append((fila.get("num_linea"), precio))
    return esperadas


def precios_presentes(ia3: dict, lineas: list[dict]) -> tuple[int, int]:
    """(R10) De las líneas IA3 `contrato_db`, cuántas tienen su precio esperado
    entre los de las líneas importadas, y cuántas son.

    Es un CONTROL del contrato vigente (Sigrid da el precio de hoy, el
    albarán puede ser de ayer), no un emparejamiento: no dice qué línea casa
    con cuál, solo si el precio que el humano espera existe en el contrato.
    """
    importados = {_precio(linea.get("precio_unitario")) for linea in lineas}
    esperadas = _esperadas_de_contrato(ia3)
    return sum(1 for _, precio in esperadas if precio in importados), len(esperadas)


def precios_ausentes(ia3: dict, lineas: list[dict]) -> list:
    """(R10) Los `num_linea` de IA3 `contrato_db` cuyo precio no está en el contrato."""
    importados = {_precio(linea.get("precio_unitario")) for linea in lineas}
    return [numero for numero, precio in _esperadas_de_contrato(ia3) if precio not in importados]
