# scripts/medir_empleados_f069.py
"""Medición de SOLO LECTURA para F-069 (R25–R27): ¿cuántos de los que aprueban
tienen un único empleado de alta con su correo en Sigrid, y qué empleado les
correspondería a las altas que el pipeline ya escribió?

Mide lo mismo que hará sv9, con su misma consulta y su misma clasificación (las
importa): ``SQL_EMPLEADOS_POR_CORREO``, ``empleados_de_filas``,
``correo_ruesma`` y ``clasificar_empleados_correo``. Clases por Quien aprobó:
``unico``, ``ambiguo``, ``de_baja``, ``sin_empleado`` y ``sin_correo``. Si la
Lista (``ALTA_SIGRID_EQUIVALENCIAS_USUARIO``) está en el entorno, la aplica
primero, como sv9 (R9); vacía es lo normal.

Solo lecturas: ``POST /api/sql/read`` de sigrid-api con sentencias ``SELECT``
(el lector rechaza cualquier otra) y ``SELECT`` en PostgreSQL dentro de una
transacción de solo lectura. No usa el cliente de sv9 (F-053 R33).

Salida (``--salida``, por defecto ``progress``): ``medicion_F-069.md`` (resumen)
y ``medicion_F-069.csv`` (UTF-8 con BOM, ``;``). Solo Logins (la parte antes de
la @), ``ide`` de Sigrid y códigos de albarán: nunca correos completos, nombres
ni DNI. Tampoco imprime credenciales ni el servidor.

Credenciales SOLO del entorno de la consola (el ``.env`` de los servicios apunta
a local): ``SIGRID_API_BASE_URL``, ``SIGRID_API_FUNCTION_KEY``,
``SIGRID_API_DATABASE`` (``ruesma``), ``PG_HOST``, ``PG_PORT`` (5432), ``PG_DB``
(``albaranes``), ``PG_USER``, ``PG_PASSWORD`` y ``PG_SSLMODE`` (``prefer``).
Lo ejecuta el líder o el humano, desde la raíz del repositorio:

    python services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py --salida progress/
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RAIZ_SV9 = Path(__file__).resolve().parents[1]
if str(RAIZ_SV9) not in sys.path:
    sys.path.insert(0, str(RAIZ_SV9))

import httpx  # noqa: E402
import psycopg  # noqa: E402
from tenacity import (  # noqa: E402
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from domain.services.usuario_sigrid import (  # noqa: E402
    AVISO_EMPLEADO_CORREO_AMBIGUO,
    AVISO_EMPLEADO_CORREO_DE_BAJA,
    AVISO_EMPLEADO_CORREO_SIN_EMPLEADO,
    VARIABLE_LISTA,
    Equivalencia,
    clasificar_empleados_correo,
    correo_ruesma,
    entrada_de,
    leer_equivalencias,
)
from infrastructure.sigrid.sigrid_api_alta_client import (  # noqa: E402
    MAX_FILAS_EMPLEADO_LISTA,
    MAX_FILAS_EMPLEADOS_CORREO,
    RUTA_SQL_READ,
    SQL_EMPLEADO_DE_ALTA,
    SQL_EMPLEADOS_POR_CORREO,
    empleados_de_filas,
)

#: Clases de un Quien aprobó (R25), en el orden en que se informan.
CLASES = ("unico", "ambiguo", "de_baja", "sin_empleado", "sin_correo")
_CLASE_DE_AVISO = {
    AVISO_EMPLEADO_CORREO_AMBIGUO: "ambiguo",
    AVISO_EMPLEADO_CORREO_DE_BAJA: "de_baja",
    AVISO_EMPLEADO_CORREO_SIN_EMPLEADO: "sin_empleado",
}

#: PostgreSQL (design §7): quien aprobó y las altas ya escritas por el pipeline.
SQL_PG_APROBADORES = "SELECT DISTINCT approved_by FROM albaran_documents_merge WHERE approved"
SQL_PG_ALTAS = (
    "SELECT sigrid_con_ide, sigrid_cod, approved_by, peticion_json::json->>'usu' "
    "FROM albaran_altas_sigrid WHERE estado = 'registrado' AND sigrid_con_ide IS NOT NULL "
    "ORDER BY sigrid_con_ide"
)
#: Parámetros por lectura de ``dbo.dca`` (R26).
LOTE_DCA = 500

COLUMNAS_CSV = ("tipo", "login", "clase", "empide_correo", "con_ide", "cod", "usu",
                "empide_actual", "empide_que_corresponde", "difiere")
NOMBRE_SALIDA = "medicion_F-069"

INTENTOS = 3


def sql_empide_dca(n: int) -> str:
    """El ``empide`` actual de ``n`` albaranes de compra (``dca.ide`` = ``con.ide``)."""
    return f"SELECT d.ide, d.empide FROM dbo.dca d WHERE d.ide IN ({', '.join('?' * n)})"


# ---------------------------------------------------------------------- #
# Puro
# ---------------------------------------------------------------------- #
@dataclass(frozen=True)
class Medida:
    """Un Quien aprobó medido: su Login (``None`` sin Correo de Ruesma), su clase,
    el ``ide`` del empleado si la clase es ``unico`` y lo que tardó la consulta."""

    login: str | None
    clase: str
    empide_correo: int | None
    segundos: float | None = None


@dataclass(frozen=True)
class AltaEscrita:
    """Un alta ``registrado`` del pipeline con su empleado actual y el de R9–R12."""

    con_ide: int
    cod: str
    login: str | None
    usu: str | None
    empide_actual: int | None
    empide_que_corresponde: int | None

    @property
    def difiere(self) -> bool:
        """Con nulo sigrid-api pone su defecto: no hay nada que corregir."""
        return (self.empide_que_corresponde is not None
                and self.empide_que_corresponde != self.empide_actual)


def _login(correo: str | None) -> str | None:
    return None if correo is None else correo.split("@")[0]


def clase_de(correo: str | None, filas: list[dict]) -> tuple[str, int | None]:
    """La clase de R25 con la clasificación de sv9: ``(clase, ide)``."""
    if correo is None:
        return "sin_correo", None
    ide, aviso = clasificar_empleados_correo(empleados_de_filas(filas))
    if ide is not None:
        return "unico", ide
    return _CLASE_DE_AVISO[aviso.codigo], None


def empide_que_corresponde(medida: Medida | None, empide_lista: int | None = None) -> int | None:
    """R9–R12: la Entrada de alta (ya comprobada) primero, luego el único
    empleado del correo y, si no, nulo (el defecto de sigrid-api)."""
    if empide_lista is not None:
        return empide_lista
    if medida is not None and medida.clase == "unico":
        return medida.empide_correo
    return None


def _celda(valor: Any) -> Any:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "sí" if valor else "no"
    return valor


def filas_csv(medidas: list[Medida], altas: list[AltaEscrita]) -> list[dict[str, Any]]:
    """Una fila por Quien aprobó con Correo de Ruesma, una por los que no lo
    tienen (sin Login) y una por alta escrita. Sin correos."""
    filas = [dict.fromkeys(COLUMNAS_CSV, "") | {
        "tipo": "aprobador", "login": _celda(m.login), "clase": m.clase,
        "empide_correo": _celda(m.empide_correo),
    } for m in medidas]
    filas += [dict.fromkeys(COLUMNAS_CSV, "") | {
        "tipo": "alta", "login": _celda(a.login), "con_ide": a.con_ide, "cod": a.cod,
        "usu": _celda(a.usu), "empide_actual": _celda(a.empide_actual),
        "empide_que_corresponde": _celda(a.empide_que_corresponde),
        "difiere": _celda(a.difiere),
    } for a in altas]
    return filas


def resumen(medidas: list[Medida], altas: list[AltaEscrita], *, entradas_lista: int) -> str:
    """Resumen en Markdown con Logins e ``ide``; nunca correos."""
    total = len(medidas)
    cuentas = Counter(m.clase for m in medidas)

    def pct(n: int) -> str:
        return f"{100.0 * n / total:.1f}".replace(".", ",") if total else "0,0"

    tiempos = [m.segundos for m in medidas if m.segundos is not None]
    lineas = [
        "# F-069 · medición de empleados de quien aprueba (solo lectura)",
        "",
        f"Generado: {datetime.now(UTC):%Y-%m-%d %H:%M} UTC. Entradas en la Lista: {entradas_lista}.",
        f"Quien aprobó distintos: {total} (merges aprobados y altas del pipeline).",
        "",
        "| Clase | Quien aprobó | % |",
        "|---|---|---|",
        *(f"| {c} | {cuentas[c]} | {pct(cuentas[c])} |" for c in CLASES),
        "",
        "## Por Login",
        "",
        "| Login | Clase | empide del correo |",
        "|---|---|---|",
        *(f"| {m.login} | {m.clase} | {_celda(m.empide_correo)} |"
          for m in sorted((m for m in medidas if m.login), key=lambda m: m.login)),
        "",
        f"Sin Correo de Ruesma (no se listan): {cuentas['sin_correo']}.",
        "",
        "## Tiempo de la consulta por correo",
        "",
    ]
    if tiempos:
        lineas.append(f"Consultas: {len(tiempos)}; media {sum(tiempos) / len(tiempos):.2f} s; "
                      f"máxima {max(tiempos):.2f} s.")
    else:
        lineas.append("Consultas: 0.")
    difieren = [a for a in altas if a.difiere]
    lineas += [
        "",
        "## Altas ya escritas por el pipeline (`registrado` con `sigrid_con_ide`)",
        "",
        (f"Altas: {len(altas)}; difieren del empleado que les correspondería: {len(difieren)} "
         "(con nulo, sigrid-api pone su defecto y no se cuenta como diferencia)."),
        "",
        "| con.ide | cod | Login | usu | dca.empide actual | le correspondería | difiere |",
        "|---|---|---|---|---|---|---|",
        *(f"| {a.con_ide} | {a.cod} | {_celda(a.login)} | {_celda(a.usu)} | "
          f"{_celda(a.empide_actual)} | {_celda(a.empide_que_corresponde)} | "
          f"{_celda(a.difiere)} |" for a in altas),
    ]
    return "\n".join(lineas) + "\n"


def escribir_csv(ruta: Path, filas: list[dict[str, Any]]) -> None:
    """UTF-8 con BOM y ``;`` (Excel en español)."""
    with open(ruta, "w", encoding="utf-8-sig", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=list(COLUMNAS_CSV), delimiter=";")
        escritor.writeheader()
        escritor.writerows(filas)


# ---------------------------------------------------------------------- #
# E/S
# ---------------------------------------------------------------------- #
class _Transitorio(Exception):
    """5xx de sigrid-api: se reintenta."""


class LectorSigrid:
    """``POST /api/sql/read`` y nada más: solo ``SELECT``, ``truncated`` = fallo."""

    def __init__(self, *, base_url: str, clave: str, database: str, timeout_s: float = 60.0,
                 transport: httpx.BaseTransport | None = None, espera_base_s: float = 1.0,
                 ) -> None:
        self._url = f"{base_url.rstrip('/')}{RUTA_SQL_READ}"
        self._clave = clave
        self._database = database
        self._timeout = float(timeout_s)
        self._transport = transport
        self._espera = float(espera_base_s)

    def __repr__(self) -> str:  # sin la clave
        return f"LectorSigrid(database={self._database!r})"

    def _post(self, cuerpo: dict[str, Any]) -> httpx.Response:
        cabeceras = {"x-functions-key": self._clave, "Content-Type": "application/json"}
        with httpx.Client(timeout=self._timeout, transport=self._transport) as cliente:
            respuesta = cliente.post(self._url, json=cuerpo, headers=cabeceras)
        if respuesta.status_code >= 500:
            raise _Transitorio(f"HTTP {respuesta.status_code}")
        return respuesta

    def leer(self, sql: str, parametros: list[Any], max_filas: int) -> list[dict]:
        if not sql.startswith("SELECT "):
            raise ValueError("el script solo lanza sentencias SELECT")
        cuerpo = {"database": self._database, "sql": sql, "parameters": parametros,
                  "timeout_seconds": int(self._timeout), "max_rows": max_filas}
        reintentos = Retrying(
            stop=stop_after_attempt(INTENTOS),
            wait=wait_exponential(multiplier=self._espera, max=30),
            retry=retry_if_exception_type(
                (_Transitorio, httpx.TimeoutException, httpx.TransportError)),
            reraise=True,
        )
        try:
            respuesta = reintentos(self._post, cuerpo)
        except (_Transitorio, httpx.TimeoutException, httpx.TransportError) as exc:
            raise RuntimeError(f"sql/read sin respuesta: {exc}") from exc
        if respuesta.status_code != 200:
            raise RuntimeError(f"sql/read HTTP {respuesta.status_code}")
        try:
            datos = respuesta.json()
        except ValueError:
            datos = None
        if not isinstance(datos, dict) or datos.get("ok") is not True:
            raise RuntimeError("sql/read: respuesta no válida")
        if datos.get("truncated"):
            raise RuntimeError("sql/read: respuesta truncada (sube max_rows o trocea)")
        columnas = [str(c).lower() for c in datos.get("columns") or []]
        return [dict(zip(columnas, fila, strict=False)) for fila in datos.get("rows") or []]


def leer_postgres(conexion: Any) -> tuple[list[str | None], list[tuple]]:
    """Las dos lecturas de PostgreSQL (solo ``SELECT``)."""
    with conexion.cursor() as cursor:
        cursor.execute(SQL_PG_APROBADORES)
        aprobadores = [fila[0] for fila in cursor.fetchall()]
        cursor.execute(SQL_PG_ALTAS)
        altas = [tuple(fila) for fila in cursor.fetchall()]
    return aprobadores, altas


def _lotes(valores: list[int], tamano: int) -> Iterable[list[int]]:
    for inicio in range(0, len(valores), tamano):
        yield valores[inicio:inicio + tamano]


def medir(
    lector: LectorSigrid, aprobadores: list[str | None], altas_pg: list[tuple],
    equivalencias: Mapping[str, Equivalencia],
) -> tuple[list[Medida], list[AltaEscrita]]:
    """Clasifica cada Quien aprobó distinto (R25) y calcula el empleado de cada
    alta escrita (R26). Un correo con varias grafías es un solo Quien aprobó."""
    distintos = list(dict.fromkeys([*aprobadores, *(fila[2] for fila in altas_pg)]))
    por_correo: dict[str, Medida] = {}
    medidas: list[Medida] = []
    for approved_by in distintos:
        correo = correo_ruesma(approved_by)
        if correo is None:
            medidas.append(Medida(None, "sin_correo", None))
            continue
        if correo in por_correo:
            continue
        inicio = time.perf_counter()
        filas = lector.leer(SQL_EMPLEADOS_POR_CORREO, [correo], MAX_FILAS_EMPLEADOS_CORREO)
        clase, ide = clase_de(correo, filas)
        por_correo[correo] = Medida(_login(correo), clase, ide, time.perf_counter() - inicio)
        medidas.append(por_correo[correo])

    # R9: el empide de la Entrada solo cuenta si es un empleado de alta.
    lista_de_alta: dict[int, bool] = {}
    for approved_by in distintos:
        entrada = entrada_de(approved_by, equivalencias)
        if entrada is not None and entrada.empide is not None and entrada.empide not in lista_de_alta:
            lista_de_alta[entrada.empide] = bool(lector.leer(
                SQL_EMPLEADO_DE_ALTA, [entrada.empide], MAX_FILAS_EMPLEADO_LISTA))

    actuales: dict[int, int | None] = {}
    for lote in _lotes([int(fila[0]) for fila in altas_pg], LOTE_DCA):
        for fila in lector.leer(sql_empide_dca(len(lote)), lote, len(lote)):
            empide = fila.get("empide")
            actuales[int(fila["ide"])] = None if empide is None else int(empide)

    altas: list[AltaEscrita] = []
    for con_ide, cod, approved_by, usu in altas_pg:
        correo = correo_ruesma(approved_by)
        entrada = entrada_de(approved_by, equivalencias)
        empide_lista = (entrada.empide if entrada is not None and entrada.empide is not None
                        and lista_de_alta.get(entrada.empide) else None)
        altas.append(AltaEscrita(
            con_ide=int(con_ide), cod=str(cod or ""), login=_login(correo), usu=usu,
            empide_actual=actuales.get(int(con_ide)),
            empide_que_corresponde=empide_que_corresponde(por_correo.get(correo), empide_lista),
        ))
    return medidas, altas


_conectar_por_defecto: Callable[..., Any] = psycopg.connect

_OBLIGATORIAS = ("SIGRID_API_BASE_URL", "SIGRID_API_FUNCTION_KEY", "PG_HOST", "PG_USER",
                 "PG_PASSWORD")


def main(argv: list[str] | None = None, *, conectar: Callable[..., Any] | None = None,
         transport: httpx.BaseTransport | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--salida", default="progress",
                        help="carpeta de medicion_F-069.md y medicion_F-069.csv")
    args = parser.parse_args(argv)

    faltan = [nombre for nombre in _OBLIGATORIAS if not os.environ.get(nombre, "").strip()]
    if faltan:
        print(f"Faltan variables de entorno: {', '.join(faltan)}", file=sys.stderr)
        return 2
    try:
        equivalencias = leer_equivalencias(os.environ.get(VARIABLE_LISTA))
    except ValueError as exc:
        print(f"Lista no válida: {exc}", file=sys.stderr)
        return 2

    lector = LectorSigrid(
        base_url=os.environ["SIGRID_API_BASE_URL"], clave=os.environ["SIGRID_API_FUNCTION_KEY"],
        database=os.environ.get("SIGRID_API_DATABASE") or "ruesma", transport=transport,
    )
    conexion = (conectar or _conectar_por_defecto)(
        host=os.environ["PG_HOST"], port=int(os.environ.get("PG_PORT") or 5432),
        dbname=os.environ.get("PG_DB") or "albaranes", user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"], sslmode=os.environ.get("PG_SSLMODE") or "prefer",
    )
    try:
        conexion.read_only = True
        aprobadores, altas_pg = leer_postgres(conexion)
        medidas, altas = medir(lector, aprobadores, altas_pg, equivalencias)
    finally:
        conexion.close()

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    texto = resumen(medidas, altas, entradas_lista=len(equivalencias))
    (salida / f"{NOMBRE_SALIDA}.md").write_text(texto, encoding="utf-8")
    escribir_csv(salida / f"{NOMBRE_SALIDA}.csv", filas_csv(medidas, altas))
    print(texto)
    print(f"Escritos {NOMBRE_SALIDA}.md y {NOMBRE_SALIDA}.csv en {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
