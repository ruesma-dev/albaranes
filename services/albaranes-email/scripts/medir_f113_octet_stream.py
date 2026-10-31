# scripts/medir_f113_octet_stream.py
"""Medición de F-113: ¿cuántos adjuntos entraron con un MIME genérico?

Script puntual de SOLO LECTURA (R20; la ejecución real es la MANUAL T9/T11,
D-6). Cuenta en ``workflow_runs`` las filas de intake de sv1
(``correlation_key`` ``email:%``) cuyo ``payload_json`` trae un
``attachment_content_type`` genérico o vacío, por ``current_state`` y por día
de ``started_at_utc``, y lista los ``document_id`` que siguen en
``email_received`` con más de 1 h.

- Una transacción con ``SET TRANSACTION READ ONLY`` y solo ``SELECT``; la
  sesión, además, con ``default_transaction_read_only=on``.
- Credenciales SOLO de las ``PG_*`` del entorno, sin valor por defecto de
  servidor; nunca se imprimen. OJO: el ``.env`` de los servicios apunta a
  local; para medir Azure, las ``PG_*`` de Azure van en la consola.
- No imprime ``subject``, ``from_address`` ni ``attachment_filename``.
- Los mensajes de ``q-extraccion-poison`` se cuentan aparte, a mano, con
  ``az storage message peek`` (solo lectura).

Uso (lo ejecuta el humano o el líder)::

    cd services\\albaranes-email
    python -m scripts.medir_f113_octet_stream [--csv salida.csv]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from sqlalchemy import text

#: Los MIME genéricos del glosario de F-113, sin el vacío (va aparte en la SQL).
GENERICOS: tuple[str, ...] = (
    "application/octet-stream",
    "binary/octet-stream",
    "application/binary",
    "application/unknown",
    "application/x-unknown",
    "application/download",
    "application/force-download",
)

#: Opciones de conexión de psycopg: la SESIÓN entera en solo lectura.
OPCIONES_SOLO_LECTURA = {"options": "-c default_transaction_read_only=on"}

_REQUERIDAS = ("PG_HOST", "PG_DB", "PG_USER", "PG_PASSWORD")

_SQL_READ_ONLY = "SET TRANSACTION READ ONLY"

_FILTRO = """
      correlation_key LIKE 'email:%'
  AND (lower(split_part(payload_json::jsonb ->> 'attachment_content_type', ';', 1)) = ANY(:genericos)
       OR trim(coalesce(payload_json::jsonb ->> 'attachment_content_type', '')) = '')"""

_SQL_RESUMEN = f"""
SELECT current_state, substr(started_at_utc, 1, 10) AS dia, count(*) AS n
FROM workflow_runs
WHERE {_FILTRO}
GROUP BY 1, 2
ORDER BY 2, 1"""

_SQL_ATASCADOS = f"""
SELECT document_id, started_at_utc
FROM workflow_runs
WHERE {_FILTRO}
  AND current_state = 'email_received'
  AND started_at_utc::timestamptz < now() - interval '1 hour'
ORDER BY started_at_utc"""


def sql_medicion() -> list[str]:
    """Las sentencias, en orden: solo lectura, resumen y atascados."""
    return [_SQL_READ_ONLY, _SQL_RESUMEN, _SQL_ATASCADOS]


def medir(conexion: Any) -> tuple[list[dict], list[dict]]:
    """Ejecuta las tres sentencias en la transacción abierta de ``conexion``."""
    solo_lectura, resumen, atascados = sql_medicion()
    conexion.execute(text(solo_lectura))
    parametros = {"genericos": list(GENERICOS)}
    filas = [dict(f) for f in conexion.execute(text(resumen), parametros).mappings().all()]
    detalle = [dict(f) for f in conexion.execute(text(atascados), parametros).mappings().all()]
    return filas, detalle


def resumir(filas: list[dict], atascados: list[dict]) -> str:
    """Texto para la consola: total, por estado, por día y estado, atascados."""
    total = sum(int(f["n"]) for f in filas)
    por_estado: Counter = Counter()
    for fila in filas:
        por_estado[str(fila["current_state"])] += int(fila["n"])
    lineas = [
        "F-113 · filas de intake de sv1 con attachment_content_type genérico o vacío",
        f"Total: {total}",
        "",
        "Por estado:",
    ]
    lineas += [f"  {estado}: {n}" for estado, n in sorted(por_estado.items())]
    lineas += ["", "Por día y estado:"]
    lineas += [f"  {f['dia']}  {f['current_state']:<28} {int(f['n']):>6}" for f in filas]
    lineas += ["", f"Siguen en email_received (más de 1 h): {len(atascados)}"]
    lineas += [f"  {a['document_id']}  {a['started_at_utc']}" for a in atascados]
    return "\n".join(lineas)


def escribir_csv(destino: Path, filas: list[dict]) -> None:
    """CSV del resumen por día y estado: UTF-8 BOM y ``;`` (Excel ES)."""
    with Path(destino).open("w", encoding="utf-8-sig", newline="") as fichero:
        escritor = csv.writer(fichero, delimiter=";")
        escritor.writerow(["dia", "current_state", "n"])
        for fila in filas:
            escritor.writerow([fila["dia"], fila["current_state"], int(fila["n"])])


# ------------------------------------------------------------------ #
# Entrada (se sustituye en los tests)
# ------------------------------------------------------------------ #
def _url_desde_entorno() -> str:
    from urllib.parse import quote_plus

    faltan = [v for v in _REQUERIDAS if not os.environ.get(v)]
    if faltan:
        raise KeyError(", ".join(faltan))
    usuario = quote_plus(os.environ["PG_USER"])
    clave = quote_plus(os.environ["PG_PASSWORD"])
    base = quote_plus(os.environ["PG_DB"])
    puerto = os.environ.get("PG_PORT") or "5432"
    return f"postgresql+psycopg://{usuario}:{clave}@{os.environ['PG_HOST']}:{puerto}/{base}"


@contextmanager
def _conectar(url: str) -> Iterator[Any]:  # pragma: no cover - solo con BBDD real (MANUAL)
    from sqlalchemy import create_engine

    motor = create_engine(url, connect_args=OPCIONES_SOLO_LECTURA)
    try:
        with motor.connect() as conexion, conexion.begin():
            yield conexion
    finally:
        motor.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--csv", type=Path, default=None, help="CSV del resumen (UTF-8 BOM, ';')")
    args = parser.parse_args(argv)
    try:
        url = _url_desde_entorno()
    except KeyError as exc:
        print(f"ERROR: faltan variables del entorno: {exc.args[0]}.", file=sys.stderr)
        return 1
    try:
        with _conectar(url) as conexion:
            filas, atascados = medir(conexion)
    except Exception as exc:  # noqa: BLE001 - el mensaje puede llevar la conexión
        print(f"ERROR: {type(exc).__name__}. Detalle omitido: puede contener datos de conexión.",
              file=sys.stderr)
        return 1
    print(resumir(filas, atascados))
    if args.csv is not None:
        escribir_csv(args.csv, filas)
        print(f"\nCSV: {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
