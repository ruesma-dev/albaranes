# scripts/medir_admisibilidad_f053.py
"""Medición de SOLO LECTURA para F-053: ¿qué parte de los albaranes se podría
dar de alta en Sigrid?

Decisión del humano (2026-10-01): «medir antes» de fijar el alcance de F-053.
Lee la PostgreSQL del pipeline con la configuración del ``.env`` de sv3 y
clasifica cada línea y cada albarán. Solo cuentan las **líneas con importe**
(``importe_calculado`` ≠ 0; humano, 2026-10-01): las demás no se registran.

**Valorado** (``esta_valorado``): valoración de sv6 en ``ok`` o valoración
manual completa del administrativo en sv4; un albarán no valorado no se registra.

- (a) **registrable con sigrid-api tal cual**: valorado y con contrato, TODAS
  las líneas con importe casan con una línea del contrato de la valoración con
  su misma partida (o almacén contra una línea de contrato sin partida) y
  ninguna es negativa. Es ``sigrid/albaran`` hoy.
- (b) **registrable con el criterio del humano**: valorado, con o sin partida
  (sin partida = almacén, F-051 v4), casen o no; negativas admitidas. Exige
  F-009 en sigrid-api; las que no casan irían con un producto genérico
  (``necesitan_producto`` dice cuántas).

En los dos casos la cabecera debe traer obra, CIF, número de albarán y fecha
``AAAA-MM-DD`` válida, y cada línea con importe debe tener cantidad ≠ 0.

Solo ejecuta SELECT, dentro de una transacción ``READ ONLY``. No imprime la
cadena de conexión ni ninguna credencial. Lo ejecuta el humano:

    cd services\\albaranes-persistencia
    .\\.venv\\Scripts\\python.exe -m scripts.medir_admisibilidad_f053 [--todos] [--csv salida.csv] [--env otro.env]

**Almacén** (F-051 v4, T0a de F-053): toda línea con la partida final vacía,
tenga o no marca en ``partida_action``. Por eso el script no conoce marcas y
«almacén sin casar» y «sin partida ni almacén» son una sola categoría,
``sin_partida_sin_casar``, que no impide el alta.

**Línea de otro contrato** (R46, decisión D2 del humano, 2026-10-06): línea
valorada casada con una línea de contrato cuyo contrato no es el de la
valoración (o la valoración no tiene). «No debería ocurrir nunca»: en F-053 va
a ``revisar``. Se cuentan todas las valoradas (con importe o sin él) y se dan
los ``document_id``, sin ningún valor; no cambia los veredictos (a) y (b).
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from typing import Iterable, Mapping

#: Categorías de línea, excluyentes, en el orden en que se informan.
CATEGORIAS = (
    "casa_misma_partida",
    "casa_partida_distinta",
    "partida_sin_casar",
    "sin_partida_sin_casar",
)

_RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")

SQL_LINEAS_VALORADAS = """
SELECT d.id AS document_id, d.approved, d.obra_codigo, d.proveedor_cif,
       d.numero_albaran, d.fecha,
       v.status AS valoracion_status, v.contrato_codigo AS valoracion_contrato,
       lv.id AS lv_id, lv.cantidad_albaran, lv.cantidad_convertida,
       lv.importe_calculado,
       lv.matched_contrato_line_id, lv.derived_contrato_line_id,
       lv.codigo_partida_final,
       cl.sigrid_ide AS cl_sigrid_ide, cl.codigo_contrato AS cl_contrato,
       cl.codigo_partida AS cl_partida
FROM albaran_documents_merge d
LEFT JOIN albaran_valuations v ON v.document_id = d.id
LEFT JOIN albaran_line_valuations lv ON lv.valuation_id = v.id
LEFT JOIN albaran_contrato_lines_merge cl ON cl.id = lv.matched_contrato_line_id
WHERE d.is_active AND (:todos OR d.approved)
ORDER BY d.id, lv.id
"""

SQL_LINEAS_MERGE = """
SELECT l.document_id, l.id AS linea_id, l.cantidad, l.precio_neto,
       l.codigo_imputacion
FROM albaran_lines_merge l
JOIN albaran_documents_merge d ON d.id = l.document_id
WHERE d.is_active AND (:todos OR d.approved)
ORDER BY l.document_id, l.id
"""


def _texto(valor: object) -> str | None:
    """Recorta y devuelve ``None`` si queda vacío."""
    if valor is None:
        return None
    limpio = str(valor).strip()
    return limpio or None


def _numero(valor: object) -> float | None:
    return None if valor is None else float(valor)


def normalizar_partida(valor: object) -> str | None:
    """Vacío y nulo son lo mismo; mayúsculas para comparar códigos."""
    limpio = _texto(valor)
    return limpio.upper() if limpio else None


def fecha_valida(valor: object) -> bool:
    """``True`` solo para una fecha ``AAAA-MM-DD`` que exista."""
    limpio = _texto(valor)
    if not limpio or not _RE_FECHA.match(limpio):
        return False
    try:
        date.fromisoformat(limpio)
    except ValueError:
        return False
    return True


@dataclass(frozen=True)
class Linea:
    """Una línea a evaluar, venga de la valoración o del merge."""

    cantidad: float | None
    importe: float | None
    partida: str | None
    casa: bool
    partida_contrato: str | None = None
    otro_contrato: bool = False

    @property
    def almacen(self) -> bool:
        """Sin partida es almacén (F-051 v4), sin mirar marcas."""
        return self.partida is None


@dataclass
class Albaran:
    """Cabecera y líneas de un albarán, ya leídas."""

    document_id: str
    approved: bool
    obra_codigo: str | None
    proveedor_cif: str | None
    numero_albaran: str | None
    fecha: str | None
    valoracion_status: str | None
    valoracion_contrato: str | None
    origen_lineas: str = "valoracion"
    lineas: list[Linea] = field(default_factory=list)


def categoria_linea(linea: Linea) -> str:
    """Clasifica una línea con importe en una de ``CATEGORIAS``."""
    if linea.casa:
        ok = linea.partida == linea.partida_contrato
        return "casa_misma_partida" if ok else "casa_partida_distinta"
    return "sin_partida_sin_casar" if linea.almacen else "partida_sin_casar"


def linea_desde_valoracion(fila: Mapping[str, object]) -> Linea:
    """Traduce una fila de ``SQL_LINEAS_VALORADAS`` (con ``lv_id``)."""
    cantidad = fila.get("cantidad_convertida")
    if cantidad is None:
        cantidad = fila.get("cantidad_albaran")
    partida = normalizar_partida(fila.get("codigo_partida_final"))
    contrato = _texto(fila.get("valoracion_contrato"))
    casa = (
        fila.get("matched_contrato_line_id") is not None
        and fila.get("derived_contrato_line_id") is None
        and fila.get("cl_sigrid_ide") is not None
        and contrato is not None
        and _texto(fila.get("cl_contrato")) == contrato
    )
    contrato_linea = _texto(fila.get("cl_contrato"))
    return Linea(
        cantidad=None if cantidad is None else float(cantidad),
        importe=_numero(fila.get("importe_calculado")),
        partida=partida,
        casa=casa,
        partida_contrato=normalizar_partida(fila.get("cl_partida")),
        otro_contrato=(
            fila.get("matched_contrato_line_id") is not None
            and contrato_linea is not None
            and contrato_linea != contrato
        ),
    )


def linea_desde_merge(fila: Mapping[str, object]) -> Linea:
    """Albarán sin líneas valoradas: partida impresa, sin casar.
    ``precio_neto`` de una línea de albarán es su IMPORTE (ARCHITECTURE, 13)."""
    cantidad = fila.get("cantidad")
    return Linea(
        cantidad=None if cantidad is None else float(cantidad),
        importe=_numero(fila.get("precio_neto")),
        partida=normalizar_partida(fila.get("codigo_imputacion")),
        casa=False,
    )


def agrupar(
    filas_valoradas: Iterable[Mapping[str, object]],
    filas_merge: Iterable[Mapping[str, object]],
) -> list[Albaran]:
    """Junta cabecera y líneas por documento. Sin líneas valoradas, usa las
    del merge (``origen_lineas = "merge"``)."""
    albaranes: dict[str, Albaran] = {}
    for fila in filas_valoradas:
        doc = str(fila["document_id"])
        if doc not in albaranes:
            albaranes[doc] = Albaran(
                document_id=doc,
                approved=bool(fila.get("approved")),
                obra_codigo=_texto(fila.get("obra_codigo")),
                proveedor_cif=_texto(fila.get("proveedor_cif")),
                numero_albaran=_texto(fila.get("numero_albaran")),
                fecha=_texto(fila.get("fecha")),
                valoracion_status=_texto(fila.get("valoracion_status")),
                valoracion_contrato=_texto(fila.get("valoracion_contrato")),
            )
        if fila.get("lv_id") is not None:
            albaranes[doc].lineas.append(
                linea_desde_valoracion(fila)
            )
    sin_valorar = {d for d, a in albaranes.items() if not a.lineas}
    for fila in filas_merge:
        doc = str(fila["document_id"])
        if doc in sin_valorar:
            albaranes[doc].origen_lineas = "merge"
            albaranes[doc].lineas.append(linea_desde_merge(fila))
    return list(albaranes.values())


def con_importe(linea: Linea) -> bool:
    """Se registra solo la línea con importe distinto de cero."""
    return linea.importe is not None and abs(linea.importe) > 1e-9


#: Cabeceras de valoración que puede completar a mano el administrativo en sv4:
#: ``manual`` (la crea sv4 si no había) y ``no_contract`` (la deja sv6 vacía).
ESTADOS_VALORACION_MANUAL = frozenset({"manual", "no_contract"})


def esta_valorado(alb: Albaran) -> bool:
    """Definición de «valorado» de F-053 (humano, 2026-10-01): valoración de
    sv6 en ``ok``, o valoración manual completa del administrativo (cabecera
    ``manual``/``no_contract`` con al menos una línea con importe y ninguna
    línea valorada con importe nulo). ``partial`` y el resto, no. F-053 la
    llevará a ``ruesma_comun``; esta copia es solo para medir."""
    if alb.valoracion_status == "ok":
        return True
    if alb.valoracion_status not in ESTADOS_VALORACION_MANUAL:
        return False
    if alb.origen_lineas != "valoracion" or not alb.lineas:
        return False
    return any(con_importe(l) for l in alb.lineas) and all(
        l.importe is not None for l in alb.lineas
    )


def cabecera_completa(alb: Albaran) -> bool:
    """Obra, CIF, número de albarán y fecha válida."""
    return bool(
        alb.obra_codigo and alb.proveedor_cif and alb.numero_albaran
        and fecha_valida(alb.fecha)
    )


def evaluar(alb: Albaran) -> dict[str, object]:
    """Cuentas por categoría y los dos veredictos de un albarán."""
    con_imp = [l for l in alb.lineas if con_importe(l)]
    negativas = sum(
        1 for l in con_imp if (l.cantidad or 0) < 0 or (l.importe or 0) < 0
    )
    sin_cantidad = sum(1 for l in con_imp if not l.cantidad)
    cuentas = Counter(categoria_linea(l) for l in con_imp)
    almacen = sum(1 for l in con_imp if l.almacen)
    valorado = esta_valorado(alb)
    base = (
        cabecera_completa(alb) and valorado and bool(con_imp)
        and sin_cantidad == 0
    )
    registrable_a = (
        base
        and negativas == 0
        and alb.valoracion_contrato is not None
        and cuentas["casa_misma_partida"] == len(con_imp)
    )
    registrable_b = base
    resultado: dict[str, object] = {
        "document_id": alb.document_id,
        "aprobado": alb.approved,
        "origen_lineas": alb.origen_lineas,
        "valorado": valorado,
        "con_contrato": alb.valoracion_contrato is not None,
        "cabecera_completa": cabecera_completa(alb),
        "lineas_con_importe": len(con_imp),
        "lineas_sin_importe": len(alb.lineas) - len(con_imp),
        "lineas_negativas": negativas,
        "lineas_sin_cantidad": sin_cantidad,
        "necesitan_producto": (
            cuentas["partida_sin_casar"] + cuentas["sin_partida_sin_casar"]
        ),
        "almacen": almacen,
        "lineas_de_otro_contrato": sum(1 for l in alb.lineas if l.otro_contrato),
        "registrable_a": registrable_a,
        "registrable_b": registrable_b,
    }
    for nombre in CATEGORIAS:
        resultado[nombre] = cuentas[nombre]
    return resultado


def resumir(evaluaciones: list[dict[str, object]]) -> dict[str, object]:
    """Agregado: sumas de líneas y porcentajes de albaranes."""
    total = len(evaluaciones)

    def pct(n: int) -> float:
        return round(100.0 * n / total, 1) if total else 0.0

    resumen: dict[str, object] = {"albaranes": total}
    for clave in ("valorado", "con_contrato", "cabecera_completa",
                  "registrable_a", "registrable_b"):
        n = sum(1 for e in evaluaciones if e[clave])
        resumen[clave] = n
        resumen[f"pct_{clave}"] = pct(n)
    resumen["sin_lineas_valoradas"] = sum(
        1 for e in evaluaciones if e["origen_lineas"] == "merge"
    )
    for clave in ("lineas_con_importe", "lineas_sin_importe",
                  "lineas_negativas", "lineas_sin_cantidad", "almacen",
                  "necesitan_producto", "lineas_de_otro_contrato", *CATEGORIAS):
        resumen[clave] = sum(int(e[clave]) for e in evaluaciones)
    resumen["documentos_de_otro_contrato"] = [
        str(e["document_id"]) for e in evaluaciones if e["lineas_de_otro_contrato"]
    ]
    return resumen


def _formato_es(valor: object) -> object:
    """Coma decimal para Excel en español."""
    if isinstance(valor, float):
        return f"{valor}".replace(".", ",")
    return valor


def escribir_csv(ruta: str, evaluaciones: list[dict[str, object]]) -> None:
    """CSV por albarán: UTF-8 con BOM, ``;`` y coma decimal."""
    if not evaluaciones:
        return
    with open(ruta, "w", encoding="utf-8-sig", newline="") as fichero:
        escritor = csv.DictWriter(
            fichero, fieldnames=list(evaluaciones[0]), delimiter=";",
        )
        escritor.writeheader()
        for fila in evaluaciones:
            escritor.writerow({k: _formato_es(v) for k, v in fila.items()})


def formatear_resumen(resumen: Mapping[str, object], todos: bool) -> str:
    """Texto legible del agregado (sin datos de conexión)."""
    ambito = "activos (aprobados o no)" if todos else "aprobados y activos"
    lineas = [
        f"F-053 · medición de admisibilidad · albaranes {ambito}",
        f"Albaranes: {resumen['albaranes']}",
        f"  valorados (ok de sv6 o manual completa): {resumen['valorado']} "
        f"({resumen['pct_valorado']} %)",
        f"  con contrato en la valoración: {resumen['con_contrato']} "
        f"({resumen['pct_con_contrato']} %)",
        f"  cabecera completa: {resumen['cabecera_completa']} "
        f"({resumen['pct_cabecera_completa']} %)",
        f"  sin líneas valoradas (se usan las del merge): "
        f"{resumen['sin_lineas_valoradas']}",
        f"  (a) registrables con sigrid-api tal cual: "
        f"{resumen['registrable_a']} ({resumen['pct_registrable_a']} %)",
        f"  (b) registrables con el criterio del humano: "
        f"{resumen['registrable_b']} ({resumen['pct_registrable_b']} %)",
        f"Líneas con importe: {resumen['lineas_con_importe']} "
        f"(sin importe, no se registran: {resumen['lineas_sin_importe']}; "
        f"negativas: {resumen['lineas_negativas']}; "
        f"con importe y sin cantidad: {resumen['lineas_sin_cantidad']})",
    ]
    for nombre in CATEGORIAS:
        lineas.append(f"  {nombre}: {resumen[nombre]}")
    lineas.append(f"  almacén (casen o no): {resumen['almacen']}")
    lineas.append(
        "  sin casar (irían con un producto genérico de la lista blanca): "
        f"{resumen['necesitan_producto']}"
    )
    lineas.append(
        "Líneas valoradas casadas con una línea de OTRO contrato (R46): "
        f"{resumen['lineas_de_otro_contrato']}"
    )
    if resumen["documentos_de_otro_contrato"]:
        lineas.append(
            "  documentos: " + ", ".join(resumen["documentos_de_otro_contrato"])
        )
    return "\n".join(lineas)


def leer_filas(
    todos: bool, env: str | None = None,
) -> tuple[list[dict], list[dict]]:
    """Las dos consultas, en una transacción de solo lectura. ``env``: otro
    ``.env`` de sv3 (p. ej. el del árbol principal si se lanza desde un
    worktree, que no tiene ``.env``)."""
    from sqlalchemy import create_engine, text

    from config.settings import Settings

    ajustes = Settings(_env_file=env) if env else Settings()
    engine = create_engine(ajustes.database_url)
    try:
        with engine.connect() as conexion, conexion.begin():
            conexion.execute(text("SET TRANSACTION READ ONLY"))
            parametros = {"todos": todos}
            valoradas = [
                dict(f) for f in conexion.execute(
                    text(SQL_LINEAS_VALORADAS), parametros,
                ).mappings()
            ]
            merge = [
                dict(f) for f in conexion.execute(
                    text(SQL_LINEAS_MERGE), parametros,
                ).mappings()
            ]
    finally:
        engine.dispose()
    return valoradas, merge


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--todos", action="store_true",
                        help="incluir también los no aprobados (no borrados)")
    parser.add_argument("--csv", help="ruta del CSV con el detalle por albarán")
    parser.add_argument("--env", help="otro .env de sv3 (por defecto, el suyo)")
    args = parser.parse_args(argv)
    valoradas, merge = leer_filas(args.todos, args.env)
    evaluaciones = [evaluar(a) for a in agrupar(valoradas, merge)]
    print(formatear_resumen(resumir(evaluaciones), args.todos))
    if args.csv:
        escribir_csv(args.csv, evaluaciones)
        print(f"Detalle por albarán: {args.csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
