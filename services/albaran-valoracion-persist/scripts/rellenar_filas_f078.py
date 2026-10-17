# scripts/rellenar_filas_f078.py
"""Relleno de F-078: cada fila valorada guarda lo que la ficha enseña.

Principio del humano (2026-10-16): «Lo que está en la tabla es lo que debería
estar guardado en BBDD». Las filas de ``albaran_line_valuations`` anteriores a
F-078 dejan huecos que la ficha de sv4 rellenaba sacándolos de otra tabla (la
línea de contrato, la derivada o la blanca). Este script aplica a lo ya
guardado la regla común ``ruesma_comun.linea_valorada.fila_a_guardar``
(concepto, unidad, precio, ``unidad_albaran`` y ``cantidad_convertida``), la
misma con la que sv6 guarda las filas nuevas y sv4 las que crea o reapunta.

- **Por defecto solo lee**, dentro de una transacción ``READ ONLY``: informa,
  por columna, ``line_kind`` y estado del documento (aprobado / pendiente),
  cuántas filas cambiarían, y lista sus ``id`` (R21). Nunca textos de
  proveedor: solo ids y nombres de columna.
- **Con ``--aplicar``** escribe, en UNA transacción, solo las columnas que
  difieren; al final vuelve a leer y exige 0 pendientes (si no, ``ROLLBACK`` y
  código de salida ≠ 0). Idempotente: una segunda pasada da 0 (R22).
- Se salta las filas de documentos en la papelera (``is_active`` falso) y las
  de documentos con alta bloqueante (``ESTADOS_ALTA_BLOQUEANTES``); incluye
  aprobados y pendientes (R23).
- No toca ``contrato_lines_derived``, importes, partidas, ``producto_sigrid``
  ni ``bloqueada``.
- Lee la conexión del ``.env`` de sv6 (o de ``--env``) y no imprime la cadena
  de conexión ni ninguna credencial (R24). Lanzarlo con ``--aplicar`` contra
  producción es MANUAL del humano, con autorización expresa.

Uso (lo ejecuta el humano)::

    cd services\\albaran-valoracion-persist
    .\\.venv\\Scripts\\python.exe -m scripts.rellenar_filas_f078            # solo lectura
    .\\.venv\\Scripts\\python.exe -m scripts.rellenar_filas_f078 --aplicar  # escribe
    .\\.venv\\Scripts\\python.exe -m scripts.rellenar_filas_f078 --env otro.env
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from ruesma_comun.alta_sigrid import ESTADOS_ALTA_BLOQUEANTES
from ruesma_comun.linea_valorada import (
    CamposFila,
    LineaDeLaFila,
    cambios_a_guardar,
)
from sqlalchemy import bindparam, inspect, text

#: Las columnas de la fila que decide ``fila_a_guardar``, en el orden del informe.
COLUMNAS = (
    "descripcion_linea", "unidad_contrato", "unidad_albaran", "precio_unitario_final",
    "cantidad_albaran", "cantidad_convertida", "factor_conversion",
)

TABLA_ALTAS = "albaran_altas_sigrid"

_SELECT = """
SELECT lv.id, lv.line_kind, d.approved,
       lv.descripcion_linea, lv.unidad_contrato, lv.unidad_albaran,
       lv.precio_unitario_final, lv.cantidad_albaran, lv.cantidad_convertida,
       lv.factor_conversion,
       cl.id AS cl_id, cl.descripcion_linea AS cl_descripcion,
       cl.unidad_medida AS cl_unidad, cl.precio_unitario AS cl_precio,
       dv.id AS d_id, dv.descripcion_linea AS d_descripcion,
       dv.unidad_medida AS d_unidad, dv.precio_unitario AS d_precio,
       l.concepto AS concepto_blanca
FROM albaran_line_valuations lv
JOIN albaran_valuations v ON v.id = lv.valuation_id
JOIN albaran_documents_merge d ON d.id = v.document_id
LEFT JOIN albaran_contrato_lines_merge cl ON cl.id = lv.matched_contrato_line_id
LEFT JOIN contrato_lines_derived dv ON dv.id = lv.derived_contrato_line_id
LEFT JOIN albaran_lines_merge l ON l.id = lv.merge_line_id
WHERE d.is_active
"""

_SIN_ALTA_BLOQUEANTE = """
  AND NOT EXISTS (
    SELECT 1 FROM albaran_altas_sigrid a
    WHERE a.document_id = d.id AND a.estado IN :bloqueantes
  )
"""

_ORDEN = "ORDER BY lv.id"


class RellenoIncompleto(RuntimeError):
    """Tras escribir quedan filas pendientes: se deshace todo."""


@dataclass(frozen=True)
class Cambio:
    """Lo que cambiaría en una fila: sus columnas con el valor nuevo."""

    id: int
    line_kind: str
    aprobado: bool
    columnas: Mapping[str, Any]


def _linea_de_la_fila(fila: Mapping[str, Any]) -> LineaDeLaFila | None:
    """Su línea: la de contrato si la tiene; si no, su derivada (el orden con
    el que la ficha de sv4 decide Contrato / Nueva)."""
    if fila["cl_id"] is not None:
        return LineaDeLaFila(
            es_contrato=True, descripcion=fila["cl_descripcion"],
            unidad=fila["cl_unidad"], precio_unitario=fila["cl_precio"],
        )
    if fila["d_id"] is not None:
        return LineaDeLaFila(
            es_contrato=False, descripcion=fila["d_descripcion"],
            unidad=fila["d_unidad"], precio_unitario=fila["d_precio"],
        )
    return None


def leer_filas(conexion: Any) -> list[dict[str, Any]]:
    """Las filas de documentos activos sin alta bloqueante, con su línea y el
    concepto de su blanca. La tabla de altas puede no existir (local)."""
    sql = _SELECT
    parametros: dict[str, Any] = {}
    if inspect(conexion).has_table(TABLA_ALTAS):
        sql += _SIN_ALTA_BLOQUEANTE
        parametros["bloqueantes"] = sorted(ESTADOS_ALTA_BLOQUEANTES)
    consulta = text(sql + _ORDEN)
    if parametros:
        consulta = consulta.bindparams(bindparam("bloqueantes", expanding=True))
    return [dict(f) for f in conexion.execute(consulta, parametros).mappings()]


def decidir(filas: Iterable[Mapping[str, Any]]) -> list[Cambio]:
    """Para cada fila, ``fila_a_guardar``; solo las que cambian."""
    cambios: list[Cambio] = []
    for fila in filas:
        columnas = cambios_a_guardar(
            CamposFila(**{c: fila[c] for c in COLUMNAS}),
            _linea_de_la_fila(fila),
            fila["concepto_blanca"],
        )
        if columnas:
            cambios.append(Cambio(
                id=int(fila["id"]),
                line_kind=str(fila["line_kind"] or "from_albaran"),
                aprobado=bool(fila["approved"]),
                columnas=columnas,
            ))
    return cambios


def resumir(cambios: Iterable[Cambio]) -> Counter:
    """Filas que cambian por (columna, ``line_kind``, aprobado/pendiente)."""
    contador: Counter = Counter()
    for cambio in cambios:
        estado = "aprobado" if cambio.aprobado else "pendiente"
        for columna in cambio.columnas:
            contador[(columna, cambio.line_kind, estado)] += 1
    return contador


def formatear_informe(total_filas: int, cambios: list[Cambio]) -> str:
    """Totales e ids, sin ningún texto de proveedor ni dato de conexión."""
    lineas = [
        f"Filas revisadas (documentos activos sin alta bloqueante): {total_filas}",
        f"Filas que cambiarían: {len(cambios)}",
    ]
    contador = resumir(cambios)
    for columna in COLUMNAS:
        de_columna = {k: n for k, n in contador.items() if k[0] == columna}
        total = sum(de_columna.values())
        if not total:
            continue
        lineas.append(f"  {columna}: {total}")
        for (_, kind, estado), n in sorted(de_columna.items()):
            lineas.append(f"    {kind} · {estado}: {n}")
        ids = [c.id for c in cambios if columna in c.columnas]
        lineas.append("    ids: " + ", ".join(str(i) for i in ids))
    return "\n".join(lineas)


def aplicar_cambios(conexion: Any, cambios: Iterable[Cambio]) -> int:
    """Un UPDATE por fila con SOLO las columnas que cambian. Devuelve cuántas."""
    hechas = 0
    for cambio in cambios:
        sets = ", ".join(f"{c} = :{c}" for c in cambio.columnas)
        conexion.execute(
            text(f"UPDATE albaran_line_valuations SET {sets} WHERE id = :id"),  # noqa: S608
            {**cambio.columnas, "id": cambio.id},
        )
        hechas += 1
    return hechas


def solo_lectura(conexion: Any) -> None:
    """La transacción en curso, ``READ ONLY`` (PostgreSQL; SQLite no lo tiene)."""
    if conexion.dialect.name == "postgresql":
        conexion.execute(text("SET TRANSACTION READ ONLY"))


def ejecutar(conexion: Any, *, aplicar: bool) -> str:
    """Una pasada dentro de la transacción abierta en ``conexion``. Sin
    ``aplicar``, solo lee. Con ``aplicar``, escribe y vuelve a contar; si queda
    algo pendiente lanza :class:`RellenoIncompleto` (el llamador deshace)."""
    if not aplicar:
        solo_lectura(conexion)
    filas = leer_filas(conexion)
    cambios = decidir(filas)
    informe = formatear_informe(len(filas), cambios)
    if not aplicar:
        return informe + "\nSolo lectura: no se ha escrito nada (usa --aplicar para escribir)."
    hechas = aplicar_cambios(conexion, cambios)
    pendientes = decidir(leer_filas(conexion))
    if pendientes:
        raise RellenoIncompleto(
            f"Tras escribir quedan {len(pendientes)} filas pendientes: "
            + ", ".join(str(c.id) for c in pendientes)
        )
    return informe + f"\nEscritas {hechas} filas. Releído: 0 pendientes."


def _motor(env: str | None):
    from config.settings import Settings
    from sqlalchemy import create_engine

    ajustes = Settings(_env_file=env) if env else Settings()
    return create_engine(ajustes.database_url)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--aplicar", action="store_true",
                        help="escribir (por defecto, solo lectura)")
    parser.add_argument("--env", help="otro .env de sv6 (por defecto, el suyo)")
    args = parser.parse_args(argv)
    try:
        motor = _motor(args.env)
        try:
            with motor.connect() as conexion, conexion.begin():
                informe = ejecutar(conexion, aplicar=args.aplicar)
        finally:
            motor.dispose()
    except RellenoIncompleto as exc:
        print(f"ERROR: {exc}. No se ha escrito nada (ROLLBACK).", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - el mensaje puede llevar la conexión
        print(
            f"ERROR: {type(exc).__name__}. Detalle omitido: puede contener datos "
            "de conexión. No se ha escrito nada.",
            file=sys.stderr,
        )
        return 1
    print(informe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
