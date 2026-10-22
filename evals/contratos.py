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

import argparse
import base64
import datetime as dt
import hashlib
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx
from ruesma_comun.sigrid import (
    MAX_FILAS_POR_PETICION,
    PoliticaTruncado,
    SigridRespuestaTruncada,
    comprobar_truncado,
)
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from evals.conversor import LIBROS, RUTA_FIXTURES, RUTA_GROUND_TRUTH
from evals.modelos import NO_COMPARAR
from evals.procesos import sv5_documentos
from evals.procesos.sv2_obra import TIMEOUT_SIGRID, faltan_variables_sigrid
from evals.revision import escritura

logger = logging.getLogger(__name__)

#: Raíz del repositorio y destino del informe del importador (R10).
RAIZ_REPO = Path(__file__).resolve().parent.parent
RUTA_INFORME = RAIZ_REPO / "progress" / "import_F-084.md"

#: El libro y las dos pestañas que toca `lineas`.
LIBRO_INPUTS = "INPUTS.xlsx"
PESTANA_CONTRATO = "CONTRATO_LINEAS"
PESTANA_CONDICIONES = "CONDICIONES"
COLUMNA_LINEA_SIGRID = "linea_sigrid"

RUTA_SQL_READ = "/api/sql/read"
INTENTOS_POR_DEFECTO = 3

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


# --- Lectura de sigrid-api (R2–R4) --------------------------------------------


class ErrorUso(RuntimeError):
    """Lo pedido no se puede lanzar tal cual: se para antes de leer nada (código 2)."""


class _Transitorio(Exception):
    """5xx de sigrid-api: se reintenta con espera exponencial."""


_TRANSITORIOS = (_Transitorio, httpx.TimeoutException, httpx.TransportError)


class LectorSigrid:
    """`POST /api/sql/read` de sigrid-api, solo lectura, un contrato por llamada.

    Sin secretos en el log ni en los errores: ni la clave (cabecera
    `x-functions-key`) ni el cuerpo de la respuesta. `transport` es la costura
    de los tests (`httpx.MockTransport`, R25).
    """

    def __init__(
        self,
        *,
        base_url: str,
        clave: str,
        database: str,
        timeout_s: float = TIMEOUT_SIGRID[1],
        intentos: int = INTENTOS_POR_DEFECTO,
        espera_base_s: float = 1.0,
        transport: httpx.BaseTransport | None = None,
        dormir=time.sleep,
    ) -> None:
        self._url = base_url.strip().rstrip("/") + RUTA_SQL_READ
        self._clave = clave.strip()
        self._database = database.strip()
        self._timeout_s = float(timeout_s)
        self._intentos = max(1, int(intentos))
        self._espera_base_s = float(espera_base_s)
        self._transport = transport
        self._dormir = dormir

    def __repr__(self) -> str:  # sin la clave
        return f"LectorSigrid(url={self._url!r}, database={self._database!r})"

    @classmethod
    def desde_entorno(
        cls,
        entorno: dict,
        *,
        intentos: int = INTENTOS_POR_DEFECTO,
        transport: httpx.BaseTransport | None = None,
    ) -> LectorSigrid:
        """(R3) Con las tres variables de sigrid-api o `ErrorUso` que las nombra."""
        faltan = faltan_variables_sigrid(entorno)
        if faltan:
            raise ErrorUso(
                "sigrid-api no está configurado: faltan en el entorno "
                + ", ".join(faltan)
                + ". No se ha pedido nada ni se ha tocado el libro."
            )
        variable, por_defecto = TIMEOUT_SIGRID
        return cls(
            base_url=entorno["SIGRID_API_BASE_URL"],
            clave=entorno["SIGRID_API_FUNCTION_KEY"],
            database=entorno["SIGRID_API_DATABASE"],
            timeout_s=float(entorno.get(variable) or por_defecto),
            intentos=intentos,
            transport=transport,
        )

    def lineas(self, codigo: str) -> tuple[list, list]:
        """(columnas, filas) del contrato; `ErrorContrato` si la lectura falla.

        Una respuesta truncada no se usa nunca (`NO_TOLERA`, R4): un contrato a
        medias valoraría contra la mitad de sus líneas sin decirlo.
        """
        cuerpo = {
            "database": self._database,
            "sql": SQL_LINEAS_CONTRATO,
            "parameters": [codigo],
            "timeout_seconds": int(self._timeout_s),
            "max_rows": MAX_FILAS_POR_PETICION,
        }
        respuesta = self._post(cuerpo, codigo)
        if respuesta.status_code != 200:
            raise ErrorContrato(f"{codigo}: sigrid-api respondió HTTP {respuesta.status_code}")
        try:
            datos = respuesta.json()
        except ValueError as error:
            raise ErrorContrato(f"{codigo}: la respuesta de sigrid-api no es JSON") from error
        if not isinstance(datos, dict) or datos.get("ok") is not True:
            raise ErrorContrato(f"{codigo}: la respuesta de sigrid-api no trae ok=true")
        try:
            comprobar_truncado(
                datos, politica=PoliticaTruncado.NO_TOLERA, etiqueta=codigo, logger=logger
            )
        except SigridRespuestaTruncada as error:
            raise ErrorContrato(
                f"{codigo}: respuesta truncada de sigrid-api (NO_TOLERA)"
            ) from error
        return list(datos.get("columns") or []), list(datos.get("rows") or [])

    def _post(self, cuerpo: dict, codigo: str) -> httpx.Response:
        """Un POST con reintentos ante 5xx, tiempo agotado o fallo de conexión."""
        cabeceras = {"x-functions-key": self._clave, "Content-Type": "application/json"}

        def intento() -> httpx.Response:
            with httpx.Client(timeout=self._timeout_s, transport=self._transport) as cliente:
                respuesta = cliente.post(self._url, json=cuerpo, headers=cabeceras)
            if respuesta.status_code >= 500:
                raise _Transitorio(f"HTTP {respuesta.status_code}")
            return respuesta

        reintentos = Retrying(
            stop=stop_after_attempt(self._intentos),
            wait=wait_exponential(multiplier=self._espera_base_s, max=10),
            retry=retry_if_exception_type(_TRANSITORIOS),
            sleep=self._dormir,
            reraise=True,
        )
        try:
            return reintentos(intento)
        except _TRANSITORIOS as error:
            detalle = str(error) if isinstance(error, _Transitorio) else type(error).__name__
            raise ErrorContrato(
                f"{codigo}: sigrid-api falló tras {self._intentos} intentos ({detalle})"
            ) from error


# --- Subcomando `lineas` -------------------------------------------------------


@dataclass
class ResultadoContrato:
    """Lo que pasó con UN contrato: sus líneas leídas o el motivo del fallo."""

    codigo: str
    casos: list[str]
    lineas: list[dict] = field(default_factory=list)
    motivo: str = ""


@dataclass
class ImportacionLineas:
    """Todo lo que `lineas` decidió, antes de escribir nada."""

    contratos: list[ResultadoContrato]
    filas_contrato: list[dict]
    filas_condiciones: list[dict]
    control: dict[str, tuple[int, int, list]]
    cambia: bool = False
    copia: Path | None = None
    dry_run: bool = False

    @property
    def fallidos(self) -> list[ResultadoContrato]:
        return [contrato for contrato in self.contratos if contrato.motivo]


def _definiciones(pestana: str) -> tuple[escritura.DefTabla, ...]:
    """Las tablas de una pestaña de INPUTS, tal como las declara el conversor.

    Se derivan de `conversor.LIBROS` en vez de copiarse: si las dos
    declaraciones divergieran, el importador escribiría donde el conversor no
    mira (la misma regla que `evals/revision/escritura.py`).
    """
    (libro,) = [definicion for definicion in LIBROS if definicion.fichero == LIBRO_INPUTS]
    return tuple(
        escritura.DefTabla(tabla.titulo, tabla.clave)
        for tabla in libro.tablas_por_pestana[pestana]
    )


def cargar_fase(fixtures: Path, fase: str) -> dict[str, dict]:
    """Los fixtures de una fase, por `caso_id` (los `_*.json` son índices)."""
    carpeta = Path(fixtures) / fase
    if not carpeta.is_dir():
        return {}
    return {
        ruta.stem: json.loads(ruta.read_text(encoding="utf-8"))
        for ruta in sorted(carpeta.glob("*.json"))
        if not ruta.name.startswith("_")
    }


def filtrar(casos: dict[str, dict], pedidos: list[str] | None) -> dict[str, dict]:
    """Los casos pedidos con `--casos`; sin lista, todos."""
    return {caso: datos for caso, datos in casos.items() if not pedidos or caso in pedidos}


def preparar_lineas(
    inputs: dict[str, dict], ia1: dict[str, dict], ia3: dict[str, dict], lector, hoy: dt.date
) -> ImportacionLineas:
    """Lee cada contrato y monta las filas; un contrato que falla, aislado (R4, R5)."""
    resultados = []
    for codigo, caso_ids in contratos_de_casos(inputs).items():
        resultado = ResultadoContrato(codigo=codigo, casos=caso_ids)
        try:
            columnas, filas = lector.lineas(codigo)
            resultado.lineas = filas_de_respuesta(columnas, filas, codigo)
        except ErrorContrato as error:
            resultado.motivo = str(error)
        resultados.append(resultado)

    filas_contrato: list[dict] = []
    control: dict[str, tuple[int, int, list]] = {}
    for resultado in resultados:
        if resultado.motivo:
            continue
        filas_contrato += filas_por_caso(resultado.lineas, resultado.casos, hoy.isoformat())
        for caso_id in resultado.casos:
            esperado = ia3.get(caso_id, {})
            presentes, total = precios_presentes(esperado, resultado.lineas)
            control[caso_id] = (presentes, total, precios_ausentes(esperado, resultado.lineas))
    return ImportacionLineas(
        contratos=resultados,
        filas_contrato=filas_contrato,
        filas_condiciones=condiciones_fecha(inputs, ia1),
        control=control,
    )


def asegurar_columna(ruta: Path, pestana: str, columna: str) -> bool:
    """(R11) Añade `columna` al final de los encabezados si la tabla no la tiene."""
    import openpyxl

    libro = openpyxl.load_workbook(ruta)
    try:
        hoja = libro[pestana]
        (bloque,) = escritura.localizar_bloques(hoja, _definiciones(pestana))
        if columna in (bloque.encabezados or []):
            return False
        ultima = max(
            celda.column for celda in hoja[bloque.fila_encabezados] if celda.value is not None
        )
        hoja.cell(row=bloque.fila_encabezados, column=ultima + 1, value=columna)
        libro.save(ruta)
        return True
    finally:
        libro.close()


def _escribir(ruta: Path, importacion: ImportacionLineas, ejecutar: bool) -> bool:
    """Las dos pestañas, solo las filas de sus casos; si alguna cambia (o cambiaría)."""
    cambia = False
    for pestana, clave, filas in (
        (PESTANA_CONTRATO, "contrato_lineas", importacion.filas_contrato),
        (PESTANA_CONDICIONES, "condiciones", importacion.filas_condiciones),
    ):
        if not filas:
            continue
        cambia = (
            escritura.escribir_pestana(
                ruta,
                pestana,
                _definiciones(pestana),
                {clave: filas},
                {fila["caso_id"] for fila in filas},
                ejecutar=ejecutar,
            )
            or cambia
        )
    return cambia


def aplicar_lineas(ruta: Path, importacion: ImportacionLineas, dry_run: bool) -> ImportacionLineas:
    """(R7, R8) Copia y escribe solo si algo cambia; con `--dry-run`, nada."""
    importacion.dry_run = dry_run
    importacion.cambia = _escribir(ruta, importacion, ejecutar=False)
    if dry_run or not importacion.cambia:
        return importacion
    importacion.copia = escritura.copia_de_seguridad(ruta)
    if importacion.filas_contrato:
        asegurar_columna(ruta, PESTANA_CONTRATO, COLUMNA_LINEA_SIGRID)
    _escribir(ruta, importacion, ejecutar=True)
    return importacion


# --- Informe (R10) ---------------------------------------------------------------

_TITULO_INFORME = "# Importación de contratos del banco de evals — F-084"


def escribir_seccion(ruta: Path, clave: str, lineas: list[str]) -> None:
    """Sustituye (o añade) la sección `clave` del informe sin tocar las demás."""
    inicio, fin = f"<!-- seccion:{clave} -->", f"<!-- /seccion:{clave} -->"
    bloque = "\n".join([inicio, *lineas, fin])
    texto = ruta.read_text(encoding="utf-8") if ruta.is_file() else f"{_TITULO_INFORME}\n"
    if inicio in texto and fin in texto:
        antes, resto = texto.split(inicio, 1)
        _, despues = resto.split(fin, 1)
        texto = f"{antes}{bloque}{despues}"
    else:
        texto = f"{texto.rstrip()}\n\n{bloque}\n"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")


def informe_lineas(importacion: ImportacionLineas, momento: str) -> list[str]:
    """Recuentos, `caso_id` y `num_linea`: ni precios ni descripciones (R10)."""
    if importacion.dry_run:
        estado = "dry-run: el libro no se ha tocado"
    elif not importacion.cambia:
        estado = "sin cambios: el libro no se ha guardado"
    else:
        estado = f"libro escrito; copia previa en `{importacion.copia.name}`"
    lineas = [
        "## Líneas de contrato (`python -m evals.contratos lineas`)",
        "",
        f"- Fecha: {momento}",
        f"- Resultado: {estado}",
        f"- Contratos leídos: {len(importacion.contratos)} · "
        f"fallidos: {len(importacion.fallidos)}",
        f"- Filas de CONTRATO_LINEAS: {len(importacion.filas_contrato)} · "
        f"fechas añadidas a CONDICIONES: {len(importacion.filas_condiciones)}",
        "",
        "| Contrato | Líneas leídas | Casos | Motivo del fallo |",
        "|---|---|---|---|",
    ]
    for contrato in importacion.contratos:
        leidas = "—" if contrato.motivo else str(len(contrato.lineas))
        lineas.append(
            f"| {contrato.codigo} | {leidas} | {', '.join(contrato.casos)} | "
            f"{contrato.motivo or '—'} |"
        )
    lineas += [
        "",
        "Control del contrato vigente (R10): de las líneas IA3 con precio `contrato_db`,",
        "cuántas tienen su precio esperado entre los de las líneas importadas. No",
        "empareja: Sigrid da el precio de hoy y el albarán puede ser de ayer.",
        "",
        "| Caso | Precios de contrato presentes | num_linea sin su precio |",
        "|---|---|---|",
    ]
    for caso_id, (presentes, total, ausentes) in sorted(importacion.control.items()):
        sin_precio = ", ".join(str(numero) for numero in ausentes) or "—"
        lineas.append(f"| {caso_id} | {presentes} de {total} | {sin_precio} |")
    return [*lineas, ""]


# --- Subcomando `documentos` (R29–R31, R34) -------------------------------------


def entrada_de_indice(codigo: str, documento: dict, leido_utc: str) -> dict:
    """(R30) La huella del documento de un contrato, SIN su contenido.

    Tipo, sha256 y tamaño del fichero que queda en la caché local, el motivo si
    no hay documento y la cabecera que sv5 pasa a IA3. Con esto, un clon limpio
    sabe qué documento se usó y puede comprobar que el suyo es el mismo (R33).
    """
    contenido = (
        base64.b64decode(documento["contenido_b64"]) if documento.get("contenido_b64") else b""
    )
    cabecera = documento.get("cabecera") or {}
    return {
        codigo: {
            "tipo": documento.get("tipo") or "ninguno",
            "sha256": hashlib.sha256(contenido).hexdigest() if contenido else None,
            "bytes": len(contenido),
            "motivo": documento.get("motivo") or "",
            **{campo: cabecera.get(campo) for campo in sv5_documentos.CAMPOS_CABECERA},
            "leido_utc": leido_utc,
        }
    }


def contratos_del_banco(inputs: dict[str, dict]) -> list[str]:
    """Los códigos de contrato distintos de los casos, con o sin líneas."""
    codigos = {
        _texto((_tablas(fixture, "caso") or [{}])[0].get("contrato_codigo"))
        for fixture in inputs.values()
    }
    return sorted(codigo for codigo in codigos if codigo)


def guardar_documentos(resultados: list[dict], cache: Path, indice: Path, momento: str) -> dict:
    """Deja cada documento en la caché y actualiza SU entrada del índice."""
    entradas = sv5_documentos.leer_indice(indice)
    for resultado in resultados:
        if resultado.get("contenido_b64"):
            cache.mkdir(parents=True, exist_ok=True)
            destino = cache / sv5_documentos.nombre_en_cache(resultado["codigo"], resultado["tipo"])
            destino.write_bytes(base64.b64decode(resultado["contenido_b64"]))
        entradas.update(entrada_de_indice(resultado["codigo"], resultado, momento))
    indice.parent.mkdir(parents=True, exist_ok=True)
    indice.write_text(
        json.dumps(dict(sorted(entradas.items())), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    return entradas


def informe_documentos(entradas: dict, codigos: list[str], momento: str) -> list[str]:
    """Por contrato: tipo, tamaño y motivo. Ni rutas ni contenido."""
    tipos = [entradas[codigo]["tipo"] for codigo in codigos]
    lineas = [
        "## Documento del contrato (`python -m evals.contratos documentos`)",
        "",
        f"- Fecha: {momento}",
        "- Recuento: "
        + " · ".join(f"{tipo} {tipos.count(tipo)}" for tipo in sv5_documentos.TIPOS),
        "",
        "| Contrato | Tipo | Bytes | Motivo |",
        "|---|---|---|---|",
    ]
    for codigo in codigos:
        entrada = entradas[codigo]
        lineas.append(
            f"| {codigo} | {entrada['tipo']} | {entrada['bytes']} | {entrada['motivo'] or '—'} |"
        )
    return [*lineas, ""]


def ejecutar_documentos(opciones, entorno: dict, lanzar=None) -> int:
    """El subcomando `documentos`: 0 leído, 1 si el subproceso de sv5 murió."""
    faltan = sv5_documentos.faltan_variables(entorno)
    if faltan:
        raise ErrorUso(
            "no se puede leer el documento del contrato: faltan en el entorno "
            + ", ".join(faltan)
            + ". No se ha conectado a nada."
        )
    codigos = contratos_del_banco(
        filtrar(cargar_fase(Path(opciones.fixtures), "inputs"), _pedidos(opciones))
    )
    trabajo = {"contratos": codigos, "max_pdf_mb": sv5_documentos.MAX_PDF_MB}
    try:
        salida = (lanzar or sv5_documentos.ejecutar_en_subproceso)(trabajo, entorno)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"contratos: no se ha leído ningún documento:\n{error}", file=sys.stderr)
        return 1
    momento = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entradas = guardar_documentos(
        salida.get("resultados", []), Path(opciones.cache), Path(opciones.indice), momento
    )
    leidos = [codigo for codigo in codigos if codigo in entradas]
    escribir_seccion(
        Path(opciones.informe), "documentos", informe_documentos(entradas, leidos, momento)
    )
    print(f"documentos: {len(leidos)} contratos · índice en {opciones.indice}")
    return 0


# --- CLI ---------------------------------------------------------------------------


def _analizador() -> argparse.ArgumentParser:
    analizador = argparse.ArgumentParser(
        prog="python -m evals.contratos",
        description="Importa las líneas y el documento del contrato de los casos del banco.",
    )
    ordenes = analizador.add_subparsers(dest="orden", required=True)
    lineas = ordenes.add_parser("lineas", help="líneas de contrato de sigrid-api al libro INPUTS")
    lineas.add_argument("--dry-run", action="store_true", help="no toca el libro: solo el informe")
    lineas.add_argument("--reintentos", type=int, default=INTENTOS_POR_DEFECTO)
    lineas.add_argument("--ground-truth", default=str(RUTA_GROUND_TRUTH))
    documentos = ordenes.add_parser(
        "documentos", help="cabecera y documento del contrato (BBDD albaranes y SharePoint)"
    )
    documentos.add_argument("--cache", default=str(sv5_documentos.RUTA_CACHE))
    documentos.add_argument("--indice", default=str(sv5_documentos.RUTA_INDICE))
    for orden in (lineas, documentos):
        orden.add_argument("--casos", default="", help="lista de caso_id separados por coma")
        orden.add_argument("--fixtures", default=str(RUTA_FIXTURES))
        orden.add_argument("--informe", default=str(RUTA_INFORME))
    return analizador


def _pedidos(opciones) -> list[str] | None:
    return [caso.strip() for caso in opciones.casos.split(",") if caso.strip()] or None


def ejecutar_lineas(opciones, entorno: dict, transport=None) -> int:
    """El subcomando `lineas`: 0 todo bien, 1 algún contrato falló."""
    libro = Path(opciones.ground_truth) / LIBRO_INPUTS
    if not libro.is_file():
        raise ErrorUso(
            f"no existe el libro {libro}: los libros no se versionan, cópialos a esa carpeta."
        )
    lector = LectorSigrid.desde_entorno(entorno, intentos=opciones.reintentos, transport=transport)
    fixtures = Path(opciones.fixtures)
    importacion = preparar_lineas(
        filtrar(cargar_fase(fixtures, "inputs"), _pedidos(opciones)),
        cargar_fase(fixtures, "IA1"),
        cargar_fase(fixtures, "IA3"),
        lector,
        dt.date.today(),
    )
    aplicar_lineas(libro, importacion, opciones.dry_run)
    momento = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    escribir_seccion(Path(opciones.informe), "lineas", informe_lineas(importacion, momento))
    print(
        f"contratos: {len(importacion.contratos)} · fallidos: {len(importacion.fallidos)} · "
        f"informe en {opciones.informe}"
    )
    return 1 if importacion.fallidos else 0


def main(
    argv: list[str] | None = None, entorno: dict | None = None, transport=None, lanzar=None
) -> int:
    """CLI. Códigos: 0 bien, 1 algún contrato (o el subproceso) falló, 2 uso.

    `transport` (sigrid-api) y `lanzar` (subproceso de sv5) son las costuras de
    los tests: sin red ni BBDD (R25).
    """
    opciones = _analizador().parse_args(argv)
    entorno = dict(os.environ) if entorno is None else entorno
    try:
        if opciones.orden == "documentos":
            return ejecutar_documentos(opciones, entorno, lanzar=lanzar)
        return ejecutar_lineas(opciones, entorno, transport=transport)
    except ErrorUso as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
