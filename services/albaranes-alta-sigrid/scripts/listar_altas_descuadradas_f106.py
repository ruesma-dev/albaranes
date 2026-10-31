# scripts/listar_altas_descuadradas_f106.py
"""Listado de SOLO LECTURA para F-106 (R18): las altas reales ``registrado`` con
alguna línea que no cuadra o con precio enviado ≠ P × (1 − d).

Para cada alta real (``modo = 'real'``) en ``registrado``, recorre las líneas de
su petición (``peticion_json``: ``referencia_linea`` = id de la fila valorada,
``cantidad`` y ``precio`` enviados) y las compara con su fila de
``albaran_line_valuations`` tal como está hoy:

- **no cuadra**: ``cuadra_linea(Q, P, d, I)`` de comun es ``False`` (Q =
  convertida o, sin ella, la del albarán; la misma regla que sv4 y sv9, R1).
- **precio difiere**: el precio enviado se aparta del neto P × (1 − d) más de lo
  que tolera el cuadre (``TOLERANCIA_CUADRE_EUR``) en el importe de la línea
  (``|enviado − neto| × |cantidad enviada|``): el redondeo a céntimos del importe
  no cuenta como diferencia. Sin descuento aplicable, el neto es P.

Una línea sin fila (revalorada después) o ilegible no se compara. El script NO
corrige nada: el humano decide qué hacer con las listadas (D6).

Solo ``SELECT``, en una conexión de solo lectura que se cierra siempre. En la
salida, códigos de albarán, ``ide`` de Sigrid e ids: ni nombres, ni correos, ni
credenciales, ni el servidor.

Credenciales SOLO del entorno de la consola (el ``.env`` de los servicios apunta
a local): ``PG_HOST``, ``PG_PORT`` (5432), ``PG_DB`` (``albaranes``), ``PG_USER``,
``PG_PASSWORD`` y ``PG_SSLMODE`` (``prefer``). Lo lanza el humano, desde
``services/albaranes-alta-sigrid``:

    python -m scripts.listar_altas_descuadradas_f106 --salida altas_f106.csv

Salida: CSV UTF-8 con BOM, ``;`` y coma decimal (Excel en español).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import psycopg
from ruesma_comun.importes import TOLERANCIA_CUADRE_EUR, clasificar_descuento, cuadra_linea

#: Las altas reales registradas, con su petición.
SQL_PG_ALTAS = (
    "SELECT a.document_id, a.sigrid_con_ide, a.sigrid_cod, a.peticion_json "
    "FROM albaran_altas_sigrid a "
    "WHERE a.estado = 'registrado' AND a.modo = 'real' "
    "ORDER BY a.document_id"
)
#: Las filas valoradas de esas altas, tal como están hoy.
SQL_PG_FILAS = (
    "SELECT v.document_id, lv.id, lv.cantidad_albaran, lv.cantidad_convertida, "
    "lv.precio_unitario_final, lv.descuento_albaran_aplicado, lv.importe_calculado "
    "FROM albaran_altas_sigrid a "
    "JOIN albaran_valuations v ON v.document_id = a.document_id "
    "JOIN albaran_line_valuations lv ON lv.valuation_id = v.id "
    "WHERE a.estado = 'registrado' AND a.modo = 'real' "
    "ORDER BY v.document_id, lv.id"
)
_COLUMNAS_FILA = ("id", "cantidad_albaran", "cantidad_convertida", "precio_unitario_final",
                  "descuento_albaran_aplicado", "importe_calculado")

COLUMNAS_CSV = ("document_id", "con_ide", "cod", "referencia_linea", "cantidad_enviada",
                "precio_enviado", "cantidad", "precio", "descuento", "importe", "precio_neto",
                "no_cuadra", "precio_difiere")
SALIDA_POR_DEFECTO = "altas_f106.csv"


# ---------------------------------------------------------------------- #
# Puro
# ---------------------------------------------------------------------- #
@dataclass(frozen=True)
class Descuadre:
    """Una línea enviada que no cuadra o con precio distinto del neto."""

    referencia_linea: str
    cantidad_enviada: float
    precio_enviado: float
    cantidad: float | None
    precio: float | None
    descuento: float | None
    importe: float | None
    precio_neto: float | None
    no_cuadra: bool
    precio_difiere: bool
    document_id: str | None = None
    con_ide: int | None = None
    cod: str | None = None


def _numero(valor: object) -> float | None:
    if valor is None or isinstance(valor, bool):
        return None
    try:
        numero = float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) else None


def precio_neto(precio: object, descuento: object) -> float | None:
    """P × (1 − d/100) con un descuento aplicable; P sin él. ``None`` sin P."""
    p = _numero(precio)
    if p is None:
        return None
    estado, valor = clasificar_descuento(descuento)
    return p * (1 - valor / 100) if estado == "aplicable" and valor is not None else p


def comparar_alta(lineas: Iterable[Any], filas: Mapping[str, Mapping[str, Any]]) -> list[Descuadre]:
    """(R18) Las líneas de una petición (``lineas``) que no cuadran o cuyo precio
    enviado no es el neto, contra sus filas (por ``referencia_linea``)."""
    salida: list[Descuadre] = []
    for linea in lineas:
        if not isinstance(linea, Mapping):
            continue
        referencia = str(linea.get("referencia_linea"))
        fila = filas.get(referencia)
        cantidad_env = _numero(linea.get("cantidad"))
        precio_env = _numero(linea.get("precio"))
        if fila is None or cantidad_env is None or precio_env is None:
            continue
        q = fila.get("cantidad_convertida")
        if q is None:
            q = fila.get("cantidad_albaran")
        p = fila.get("precio_unitario_final")
        d = fila.get("descuento_albaran_aplicado")
        i = fila.get("importe_calculado")
        no_cuadra = cuadra_linea(q, p, d, i) is False
        neto = precio_neto(p, d)
        difiere = (
            neto is not None
            and abs(abs(precio_env) - abs(neto)) * abs(cantidad_env) > TOLERANCIA_CUADRE_EUR
        )
        if no_cuadra or difiere:
            salida.append(Descuadre(
                referencia_linea=referencia, cantidad_enviada=cantidad_env,
                precio_enviado=precio_env, cantidad=_numero(q), precio=_numero(p),
                descuento=_numero(d), importe=_numero(i), precio_neto=neto,
                no_cuadra=no_cuadra, precio_difiere=difiere,
            ))
    return salida


def _lineas_de_peticion(peticion: object) -> list[Any]:
    """Las ``lineas`` de ``peticion_json`` (texto o ya leído); ``[]`` si es ilegible."""
    if isinstance(peticion, (str, bytes)):
        try:
            peticion = json.loads(peticion)
        except ValueError:
            return []
    if not isinstance(peticion, Mapping):
        return []
    lineas = peticion.get("lineas")
    return list(lineas) if isinstance(lineas, list) else []


def listar(altas: Iterable[tuple], filas: Iterable[tuple]) -> list[Descuadre]:
    """(R18) Los descuadres de todas las altas, en el orden de las altas."""
    por_documento: dict[str, dict[str, dict[str, Any]]] = {}
    for document_id, *valores in filas:
        fila = dict(zip(_COLUMNAS_FILA, valores, strict=True))
        por_documento.setdefault(str(document_id), {})[str(fila["id"])] = fila
    salida: list[Descuadre] = []
    for document_id, con_ide, cod, peticion in altas:
        for descuadre in comparar_alta(
            _lineas_de_peticion(peticion), por_documento.get(str(document_id), {}),
        ):
            salida.append(replace(descuadre, document_id=str(document_id), con_ide=con_ide, cod=cod))
    return salida


def _es(valor: float | None) -> str:
    """Número con coma decimal y hasta 6 decimales, sin ceros de más."""
    if valor is None:
        return ""
    texto = f"{valor:.6f}".rstrip("0").rstrip(".")
    return ("0" if texto == "-0" else texto).replace(".", ",")


def filas_csv(descuadres: Iterable[Descuadre]) -> list[dict[str, str]]:
    return [
        {
            "document_id": d.document_id or "", "con_ide": "" if d.con_ide is None else str(d.con_ide),
            "cod": d.cod or "", "referencia_linea": d.referencia_linea,
            "cantidad_enviada": _es(d.cantidad_enviada), "precio_enviado": _es(d.precio_enviado),
            "cantidad": _es(d.cantidad), "precio": _es(d.precio), "descuento": _es(d.descuento),
            "importe": _es(d.importe), "precio_neto": _es(d.precio_neto),
            "no_cuadra": "sí" if d.no_cuadra else "no",
            "precio_difiere": "sí" if d.precio_difiere else "no",
        }
        for d in descuadres
    ]


def escribir_csv(ruta: Path, filas: list[dict[str, str]]) -> None:
    """UTF-8 con BOM y ``;`` (Excel en español)."""
    with open(ruta, "w", encoding="utf-8-sig", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=list(COLUMNAS_CSV), delimiter=";")
        escritor.writeheader()
        escritor.writerows(filas)


# ---------------------------------------------------------------------- #
# E/S
# ---------------------------------------------------------------------- #
def leer_postgres(conexion: Any) -> tuple[list[tuple], list[tuple]]:
    """Las dos lecturas de PostgreSQL (solo ``SELECT``)."""
    with conexion.cursor() as cursor:
        cursor.execute(SQL_PG_ALTAS)
        altas = [tuple(fila) for fila in cursor.fetchall()]
        cursor.execute(SQL_PG_FILAS)
        filas = [tuple(fila) for fila in cursor.fetchall()]
    return altas, filas


_conectar_por_defecto: Callable[..., Any] = psycopg.connect

_OBLIGATORIAS = ("PG_HOST", "PG_USER", "PG_PASSWORD")


def main(argv: list[str] | None = None, *, conectar: Callable[..., Any] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salida", default=SALIDA_POR_DEFECTO, help="CSV de salida")
    args = parser.parse_args(argv)

    faltan = [nombre for nombre in _OBLIGATORIAS if not os.environ.get(nombre, "").strip()]
    if faltan:
        print(f"Faltan variables de entorno: {', '.join(faltan)}", file=sys.stderr)
        return 2
    conexion = (conectar or _conectar_por_defecto)(
        host=os.environ["PG_HOST"], port=int(os.environ.get("PG_PORT") or 5432),
        dbname=os.environ.get("PG_DB") or "albaranes", user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"], sslmode=os.environ.get("PG_SSLMODE") or "prefer",
    )
    try:
        conexion.read_only = True
        altas, filas = leer_postgres(conexion)
    finally:
        conexion.close()

    descuadres = listar(altas, filas)
    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    escribir_csv(salida, filas_csv(descuadres))
    n_altas = len({d.document_id for d in descuadres})
    lineas = "1 línea descuadrada" if len(descuadres) == 1 else f"{len(descuadres)} líneas descuadradas"
    print(f"Altas reales registradas: {len(altas)} · {lineas} en {n_altas} "
          f"{'alta' if n_altas == 1 else 'altas'}")
    print(f"Escrito {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
