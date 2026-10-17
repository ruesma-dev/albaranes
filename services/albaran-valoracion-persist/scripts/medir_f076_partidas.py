# scripts/medir_f076_partidas.py
"""Medición de F-076: ¿las partidas finales valoradas existen en su obra?

Script puntual de SOLO LECTURA (R22; la ejecución real es la MANUAL T19 del
humano). Para cada línea valorada ``from_albaran`` de un documento activo
clasifica su ``codigo_partida_final`` contra las partidas HOJA de su obra con la
misma regla con la que sv6 normaliza (``ruesma_comun.sigrid.resolver_partida_obra``):

- ``exacta``: existe tal cual;
- ``normalizada``: **normalizable sin normalizar** (difiere solo en ceros,
  mayúsculas o separadores; con F-076 desplegado y revalorado, 0 en pendientes);
- ``fuera_de_lista`` / ``ambigua``: sin candidata segura (deben llevar
  ``partida_fuera_de_lista`` / ``partida_ambigua_en_obra``);
- ``no_aplica``: vacía (almacén) o ``ALM``; ``sin_lista``: no se pudo leer la obra.

Y cuenta los motivos ``partida_*`` que ya llevan las líneas. Todo por estado del
documento (aprobado / pendiente).

- PostgreSQL con ``default_transaction_read_only=on`` en la conexión; si
  ``SHOW transaction_read_only`` no da ``on``, aborta sin leer nada.
- sigrid-api con el lector de sv6 (solo ``sql/read``) y ``NO_TOLERA``.
- Credenciales SOLO de la configuración de sv6 (entorno / su ``.env``); no se
  imprimen nunca, ni precios, ni textos, ni códigos: solo recuentos.

Uso (lo ejecuta el humano)::

    cd services\\albaran-valoracion-persist
    .\\.venv\\Scripts\\python.exe -m scripts.medir_f076_partidas
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from ruesma_comun.obras import canonizar_codigo_obra
from ruesma_comun.sigrid import LectorSql, leer_partidas_obra, resolver_partida_obra
from sqlalchemy import text

#: Opciones de conexión de psycopg: la SESIÓN entera en solo lectura.
OPCIONES_SOLO_LECTURA = {"options": "-c default_transaction_read_only=on"}

SQL_LINEAS = """
SELECT lv.codigo_partida_albaran, lv.codigo_partida_final, lv.review_reasons_json,
       d.obra_codigo, d.approved
FROM albaran_line_valuations lv
JOIN albaran_valuations v ON v.id = lv.valuation_id
JOIN albaran_documents_merge d ON d.id = v.document_id
WHERE d.is_active AND lv.line_kind = 'from_albaran'
"""

ETIQUETAS = {
    "exacta": "existe tal cual",
    "normalizada": "normalizable sin normalizar",
    "fuera_de_lista": "fuera de lista (sin candidata segura)",
    "ambigua": "ambigua en la obra",
    "no_aplica": "vacía (almacén) o ALM",
    "sin_lista": "obra sin lista (vacía, fallo o truncado)",
}
_MOTIVOS = ("partida_normalizada", "partida_fuera_de_lista", "partida_ambigua_en_obra")


class SesionNoSoloLectura(RuntimeError):
    """La conexión no está en solo lectura: no se lee nada."""


@dataclass
class Medicion:
    clases: Counter  # (clase, estado) -> líneas
    motivos: Counter  # (motivo, estado) -> líneas
    obras_sin_lista: int
    lineas: int


def comprobar_solo_lectura(conexion: Any) -> None:
    valor = conexion.execute(text("SHOW transaction_read_only")).scalar()
    if str(valor).strip().lower() != "on":
        raise SesionNoSoloLectura(f"transaction_read_only={valor!r}; se aborta sin leer")


def _motivos_de(fila: dict[str, Any]) -> list[str]:
    try:
        motivos = json.loads(fila.get("review_reasons_json") or "[]")
    except (TypeError, ValueError):
        return []
    encontrados = []
    for motivo in motivos if isinstance(motivos, list) else []:
        for conocido in _MOTIVOS:
            if str(motivo) == conocido or str(motivo).startswith(conocido + ":"):
                encontrados.append(conocido)
    return encontrados


def medir(conexion: Any, lector: LectorSql, *, alm: str) -> Medicion:
    """Lee las líneas (solo lectura comprobada) y las clasifica contra su obra."""
    comprobar_solo_lectura(conexion)
    filas = [dict(f) for f in conexion.execute(text(SQL_LINEAS)).mappings().all()]
    listas: dict[str | None, Any] = {}
    clases: Counter = Counter()
    motivos: Counter = Counter()
    for fila in filas:
        estado = "aprobado" if fila.get("approved") else "pendiente"
        obra = canonizar_codigo_obra(fila.get("obra_codigo"))
        if obra not in listas:
            try:
                lista = leer_partidas_obra(lector, obra)
            except Exception:  # noqa: BLE001 - fallo o truncado: la obra cuenta sin lista
                lista = None
            listas[obra] = lista if lista is not None and lista.hojas else None
        lista = listas[obra]
        if lista is None:
            clase = "sin_lista"
        else:
            clase = resolver_partida_obra(lista, fila.get("codigo_partida_final"), alm).motivo
        clases[(clase, estado)] += 1
        for motivo in _motivos_de(fila):
            motivos[(motivo, estado)] += 1
    sin_lista = sum(1 for lista in listas.values() if lista is None)
    return Medicion(clases=clases, motivos=motivos, obras_sin_lista=sin_lista, lineas=len(filas))


def formatear(medicion: Medicion) -> str:
    lineas = [
        f"Líneas valoradas from_albaran de documentos activos: {medicion.lineas}",
        f"Obras sin lista: {medicion.obras_sin_lista}",
        "",
        "Partida final frente a su obra (pendiente / aprobado):",
    ]
    for clave, etiqueta in ETIQUETAS.items():
        pend = medicion.clases.get((clave, "pendiente"), 0)
        apro = medicion.clases.get((clave, "aprobado"), 0)
        lineas.append(f"  {etiqueta:<42} {pend:>6} / {apro:>6}")
    lineas += ["", "Motivos de F-076 en las líneas (pendiente / aprobado):"]
    for motivo in _MOTIVOS:
        pend = medicion.motivos.get((motivo, "pendiente"), 0)
        apro = medicion.motivos.get((motivo, "aprobado"), 0)
        lineas.append(f"  {motivo:<42} {pend:>6} / {apro:>6}")
    return "\n".join(lineas)


# ------------------------------------------------------------------ #
# Entrada (se sustituyen en los tests)
# ------------------------------------------------------------------ #
def _ajustes():
    from config.settings import Settings

    return Settings()


@contextmanager
def _conectar(ajustes: Any) -> Iterator[Any]:
    from sqlalchemy import create_engine

    motor = create_engine(ajustes.database_url, connect_args=OPCIONES_SOLO_LECTURA)
    try:
        with motor.connect() as conexion, conexion.begin():
            yield conexion
    finally:
        motor.dispose()


def _lector(ajustes: Any) -> LectorSql:
    from infrastructure.sigrid.sigrid_api_lector import SigridApiLector

    return SigridApiLector(
        base_url=ajustes.sigrid_api_base_url or "",
        function_key=ajustes.sigrid_api_function_key or "",
        database=ajustes.sigrid_api_database or "",
        timeout_s=ajustes.sigrid_api_timeout_s,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.parse_args(argv)
    try:
        ajustes = _ajustes()
        if not ajustes.sigrid_api_configurada:
            print("ERROR: faltan SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY o SIGRID_API_DATABASE.",
                  file=sys.stderr)
            return 1
        with _conectar(ajustes) as conexion:
            informe = formatear(medir(conexion, _lector(ajustes), alm=ajustes.alm_codigo_partida))
    except SesionNoSoloLectura as exc:
        print(f"ERROR: {exc}.", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - el mensaje puede llevar la conexión
        print(f"ERROR: {type(exc).__name__}. Detalle omitido: puede contener datos de conexión.",
              file=sys.stderr)
        return 1
    print(informe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
