# scripts/verificar_f052_proveedores_obra.py
"""F-052 · verificación MANUAL, de SOLO LECTURA, contra sigrid-api.

Usa el cliente de contratos de sv3 (``SigridApiContratoClient``) construido
como en ``interface_adapters/composition.py``, con la configuración del
``.env`` de sv3. Solo lanza ``SELECT`` por ``/api/sql/read``: no escribe en
Sigrid ni en PostgreSQL. Nunca imprime la clave ni la URL de sigrid-api.

Se ejecuta desde la raíz de sv3 (``services\\albaranes-persistencia``):

R29 (T20) · la consulta agregada de la obra N veces seguidas (filas,
``truncated``, bytes, segundos y si el CIF está dentro), el score del nombre
leído frente a los candidatos (el de la red por nombre del resolver) y
``fetch_contratos`` del CIF en la obra::

    python scripts\\verificar_f052_proveedores_obra.py --obra 0691 --cif B82899550 --nombre "SALMEDINA" --repeticiones 5

R30 (T21) · por obra, familias por CIF del texto agregado frente al texto
por líneas (la consulta antigua, sin tope) y CIF de la agregada frente a la
lista ``DISTINCT`` de ``fetch_proveedores_por_obra``::

    python scripts\\verificar_f052_proveedores_obra.py --comparar-familias --obra 0691 --obra 0696

design §8 (T23) · obras con más de 1.000 líneas en la consulta antigua (las
que pudieron quedar mal resueltas antes de F-052)::

    python scripts\\verificar_f052_proveedores_obra.py --listar-obras-grandes

Termina con ``RESULTADO ...: OK`` (código 0) o ``FALLA`` con los motivos
(código 1). Argumentos inválidos: código 2, sin consultar nada.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

_RAIZ_SV3 = Path(__file__).resolve().parents[1]
if str(_RAIZ_SV3) not in sys.path:
    sys.path.insert(0, str(_RAIZ_SV3))

from application.services.familia_detector import familias_de_texto
from application.services.header_resolver_service import (
    _score_razon_social,
)
from infrastructure.sigrid import (
    sigrid_api_contrato_client as modulo_cliente,
)
from infrastructure.sigrid.sigrid_api_contrato_client import (
    SigridApiContratoClient,
)
from pydantic import ValidationError
from ruesma_comun.obras import normalizar_codigo_obra
from ruesma_comun.sigrid import MAX_FILAS_POR_PETICION, PoliticaTruncado

#: Tiempo máximo aceptable de la consulta agregada (design §10: si pasara
#: de 15 s, se abre feature para cachear).
LIMITE_SEGUNDOS = 15.0

#: La consulta de resumen por obra de ANTES de F-052 (una fila por línea de
#: contrato), sin tope: la referencia del texto por líneas (R30).
_SQL_LINEAS_OBRA = (
    "SELECT prv.cif        AS cif, "
    "       prv.raz        AS nombre, "
    "       con_ctr.cod    AS codigo_contrato, "
    "       con_ctr.res    AS nombre_contrato, "
    "       ctrpro.res     AS descripcion_linea, "
    "       con_pro.cod    AS codigo_producto "
    "FROM ctr "
    "JOIN con AS con_ctr       ON ctr.ide     = con_ctr.ide "
    "JOIN con AS con_obr       ON ctr.obride  = con_obr.ide "
    "JOIN prv                  ON ctr.entide  = prv.ide "
    "LEFT JOIN ctrpro          ON ctrpro.docide = ctr.ide "
    "LEFT JOIN pro             ON ctrpro.proide = pro.ide "
    "LEFT JOIN con AS con_pro  ON pro.ide       = con_pro.ide "
    "WHERE con_obr.cod = ? "
    "  AND con_ctr.emp = 1"
)

#: Obras con más de 1.000 filas en esa consulta antigua (design §8).
_SQL_OBRAS_GRANDES = (
    "SELECT con_obr.cod AS obra, COUNT(*) AS lineas, "
    "       COUNT(DISTINCT prv.cif) AS proveedores "
    "FROM ctr "
    "JOIN con AS con_ctr ON ctr.ide    = con_ctr.ide "
    "JOIN con AS con_obr ON ctr.obride = con_obr.ide "
    "JOIN prv            ON ctr.entide = prv.ide "
    "LEFT JOIN ctrpro    ON ctrpro.docide = ctr.ide "
    "WHERE con_ctr.emp = 1 "
    "GROUP BY con_obr.cod "
    "HAVING COUNT(*) > 1000 "
    "ORDER BY COUNT(*) DESC, con_obr.cod"
)

_CAMPOS_TEXTO = ("nombre_contrato", "descripcion_linea", "codigo_producto")


# ------------------------------------------------------------------ #
# Medición de cada petición HTTP
# ------------------------------------------------------------------ #
@dataclass(frozen=True)
class Medicion:
    """Lo que devolvió sigrid-api en una petición."""

    filas: int | None
    truncated: bool | None
    bytes: int
    segundos: float
    sql: str = field(default="", compare=False)


def _transporte_real() -> httpx.BaseTransport:
    # Igual que el cliente de sv3 sin transporte inyectado.
    return httpx.HTTPTransport(retries=1)


class TransporteQueMide(httpx.BaseTransport):
    """Transporte que el cliente de sv3 usa tal cual y que anota, por
    petición, filas, ``truncated``, bytes y segundos. No altera ni la
    petición ni la respuesta. Un transporte interno nuevo por petición,
    como hace el cliente sin transporte inyectado."""

    def __init__(
        self,
        *,
        fabrica: Callable[[], httpx.BaseTransport] = _transporte_real,
        reloj: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._fabrica = fabrica
        self._reloj = reloj
        self.mediciones: list[Medicion] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        interno = self._fabrica()
        inicio = self._reloj()
        try:
            respuesta = interno.handle_request(request)
            respuesta.read()
        finally:
            interno.close()
        segundos = self._reloj() - inicio
        self.mediciones.append(_medir(request, respuesta, segundos))
        return respuesta


def _medir(request: httpx.Request, respuesta: httpx.Response, segundos: float) -> Medicion:
    try:
        sql = str(json.loads(request.content).get("sql") or "")
    except (ValueError, AttributeError):
        sql = ""
    try:
        cuerpo = respuesta.json()
    except ValueError:
        cuerpo = None
    filas = truncated = None
    if isinstance(cuerpo, dict) and "rows" in cuerpo:
        filas = len(cuerpo.get("rows") or [])
        truncated = bool(cuerpo.get("truncated"))
    return Medicion(filas=filas, truncated=truncated, bytes=len(respuesta.content),
                    segundos=segundos, sql=sql)


@dataclass
class Entorno:
    cliente: SigridApiContratoClient
    transporte: TransporteQueMide
    umbral: float
    secretos: tuple[str | None, ...]

    def llamar(self, funcion: Callable[[], Any]) -> tuple[Any, BaseException | None, list[Medicion]]:
        """Ejecuta ``funcion`` y devuelve su resultado (o la excepción) con
        las peticiones que hizo."""
        desde = len(self.transporte.mediciones)
        try:
            resultado, error = funcion(), None
        except Exception as exc:  # noqa: BLE001 - se informa, nunca se oculta
            resultado, error = None, exc
        return resultado, error, self.transporte.mediciones[desde:]

    def error(self, exc: BaseException) -> str:
        return redactar(f"{type(exc).__name__}: {exc}", self.secretos)

    def leer(self, sql: str, parametros: list[Any], etiqueta: str) -> list[dict[str, Any]]:
        """Lectura «sin tope» (``max_rows`` = el tope de sigrid-api) y sin
        tolerar truncado (``NO_TOLERA``)."""
        columnas, filas = self.cliente._post_sql_read(
            sql=sql, parameters=parametros, database=self.cliente._database,
            label=etiqueta, politica=PoliticaTruncado.NO_TOLERA, max_rows=MAX_FILAS_POR_PETICION,
        )
        return [dict(zip(columnas, fila)) for fila in filas]


def construir_cliente(fabrica_settings: Callable[[], Any] | None = None) -> Entorno:
    """El cliente de sv3 como en ``composition.py``, desde su ``.env``."""
    if fabrica_settings is None:
        from config.settings import Settings as fabrica_settings
    try:
        settings = fabrica_settings()
    except ValidationError as exc:
        campos = sorted({".".join(str(p) for p in e.get("loc", ())) for e in exc.errors()})
        raise SystemExit(
            "No se pudo leer la configuración de sv3 (.env). Revisa: "
            + ", ".join(campos) + " (no se muestran los valores)."
        ) from None
    if not settings.sigrid_credentials_present:
        raise SystemExit(
            "Faltan SIGRID_API_BASE_URL, SIGRID_API_FUNCTION_KEY o "
            "SIGRID_API_DATABASE en el .env de sv3."
        )
    transporte = TransporteQueMide()
    cliente = SigridApiContratoClient(
        base_url=settings.sigrid_api_base_url,
        function_key=settings.sigrid_api_function_key,
        database=settings.sigrid_api_database,
        timeout_s=settings.sigrid_api_timeout_s,
        transport=transporte,
    )
    return Entorno(
        cliente=cliente,
        transporte=transporte,
        umbral=float(settings.header_resolver_min_score),
        secretos=(settings.sigrid_api_function_key, settings.sigrid_api_base_url),
    )


def configurar_logs() -> None:
    """Salida limpia: el cliente de sv3 registra URL y peticiones en INFO;
    el script ya informa de cada petición y de cada error."""
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger(modulo_cliente.logger.name).setLevel(logging.CRITICAL)


# ------------------------------------------------------------------ #
# Formato
# ------------------------------------------------------------------ #
def redactar(texto: str, secretos: Iterable[str | None]) -> str:
    for secreto in secretos:
        if secreto:
            texto = texto.replace(secreto, "***")
    return texto


def miles(n: int | None) -> str:
    return "?" if n is None else f"{n:,}".replace(",", ".")


def decimal(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def bandera(valor: bool | None) -> str:
    return "?" if valor is None else ("true" if valor else "false")


def _describir(m: Medicion) -> str:
    return (f"filas={miles(m.filas)}  truncated={bandera(m.truncated)}  "
            f"bytes={miles(m.bytes)}  segundos={decimal(m.segundos)}")


def texto_por_lineas(columnas: list[str], filas: list[list[Any]]) -> dict[str, str]:
    """El texto de familia de ANTES de F-052: por línea, nombre de contrato,
    descripción y código de producto no vacíos, en orden de llegada."""
    partes: dict[str, list[str]] = {}
    for fila in filas:
        registro = dict(zip(columnas, fila))
        cif = str(registro.get("cif") or "").strip()
        if not cif:
            continue
        destino = partes.setdefault(cif, [])
        for campo in _CAMPOS_TEXTO:
            valor = str(registro.get(campo) or "").strip()
            if valor:
                destino.append(valor)
    return {cif: " ".join(valores) for cif, valores in partes.items()}


def _familias(texto: str | None) -> list[str]:
    # Igual que el resolver: familias_de_texto((r.texto or "").lower())
    return sorted(familias_de_texto((texto or "").lower()))


# ------------------------------------------------------------------ #
# R29 · agregada de una obra, score del nombre y fetch_contratos
# ------------------------------------------------------------------ #
def verificar_obra(
    entorno: Entorno, *, obra: str, cif: str | None, nombre: str | None,
    repeticiones: int, salida: Callable[[str], None],
) -> bool:
    fallos: list[str] = []
    salida(f"Obra {obra} · CIF {cif or '-'} · nombre {nombre!r} · {repeticiones} repetición(es)")
    salida("Consulta agregada de la obra (fetch_contratos_resumen_por_obra):")
    completas = cif_dentro = 0
    tiempos: list[float] = []
    resumenes: list[Any] | None = None
    for n in range(1, repeticiones + 1):
        resultado, error, mediciones = entorno.llamar(
            lambda: entorno.cliente.fetch_contratos_resumen_por_obra(codigo_obra=obra)
        )
        tiempos.extend(m.segundos for m in mediciones)
        medicion = mediciones[-1] if mediciones else None
        partes = [f"  #{n}"]
        if medicion is not None and medicion.filas is not None:
            partes.append(_describir(medicion))
        if error is not None:
            partes.append(f"ERROR: {entorno.error(error)}")
        else:
            completas += 1
            resumenes = list(resultado)
            partes.append(f"proveedores={len(resumenes)}")
            if cif:
                dentro = any(r.cif == cif for r in resumenes)
                cif_dentro += dentro
                partes.append(f"CIF {cif}: {'dentro' if dentro else 'FUERA'}")
        salida("  ".join(partes))
    maximo = max(tiempos, default=0.0)
    resumen = f"Consulta agregada: {completas}/{repeticiones} completas (truncated=false)"
    if cif:
        resumen += f", CIF dentro en {cif_dentro}/{completas}"
    salida(f"{resumen}, tiempo máximo {decimal(maximo)} s (límite {LIMITE_SEGUNDOS:.0f} s)")
    if completas < repeticiones:
        fallos.append(f"{repeticiones - completas} de {repeticiones} llamadas a la consulta "
                      "agregada fallaron o llegaron truncadas")
    if cif and cif_dentro < completas:
        fallos.append(f"el CIF {cif} no está en {completas - cif_dentro} de {completas} respuestas")
    if maximo >= LIMITE_SEGUNDOS:
        fallos.append(f"la consulta agregada tardó {decimal(maximo)} s (límite {LIMITE_SEGUNDOS:.0f} s)")
    if nombre:
        fallos.extend(_verificar_nombre(entorno, resumenes, obra=obra, cif=cif, nombre=nombre, salida=salida))
    if cif:
        fallos.extend(_verificar_fetch_contratos(entorno, obra=obra, cif=cif, salida=salida))
    return _veredicto("R29", fallos, salida)


def _verificar_nombre(
    entorno: Entorno, resumenes: list[Any] | None, *, obra: str, cif: str | None,
    nombre: str, salida: Callable[[str], None],
) -> list[str]:
    if resumenes is None:
        salida(f"Nombre {nombre!r}: sin candidatos: la consulta agregada no respondió")
        return []
    salida(f"Nombre {nombre!r} frente a los {len(resumenes)} proveedores de la obra {obra} "
           f"(red por nombre; umbral {decimal(entorno.umbral)}):")
    puntuados = [(_score_razon_social(nombre, r.nombre), r) for r in resumenes]
    for score, r in sorted(puntuados, key=lambda p: -p[0])[:5]:
        salida(f"  {decimal(score)}  {r.cif}  {r.nombre}")
    # Mismo criterio que HeaderResolverService._mejor_candidato_por_nombre.
    mejor, mejor_score = None, 0.0
    for score, r in puntuados:
        if score > mejor_score:
            mejor, mejor_score = r, score
    propuesta = mejor is not None and mejor_score >= entorno.umbral
    salida(f"Mejor candidato: {mejor.cif if mejor else 'ninguno'} (score {decimal(mejor_score)}) "
           f"-> {'propuesta' if propuesta else 'nadie casa'}")
    fallos = []
    if not propuesta:
        fallos.append(f"ningún proveedor llega al umbral {decimal(entorno.umbral)} con el nombre {nombre!r}")
    if cif:
        del_cif = [s for s, r in puntuados if r.cif == cif]
        salida(f"Score del CIF {cif}: "
               + (decimal(max(del_cif)) if del_cif else "no está entre los candidatos"))
        if mejor is None or mejor.cif != cif:
            fallos.append(f"el mejor candidato por nombre no es {cif}")
    return fallos


def _verificar_fetch_contratos(
    entorno: Entorno, *, obra: str, cif: str, salida: Callable[[str], None],
) -> list[str]:
    contratos, error, mediciones = entorno.llamar(
        lambda: entorno.cliente.fetch_contratos(cif_proveedor=cif, codigo_obra_normalizado=obra)
    )
    if error is not None:
        salida(f"fetch_contratos: ERROR: {entorno.error(error)}")
        return ["fetch_contratos falló"]
    salida(f"fetch_contratos({cif}, {obra}): {len(contratos)} contrato(s)")
    for c in contratos:
        salida(f"  {c.codigo_contrato}  {len(c.lines)} línea(s)  {c.nombre_contrato or ''}")
    lineas = [m for m in mediciones if "AS contrato_ide" in m.sql]
    salida(f"  header_and_lines: {len(lineas)} petición(es), "
           f"filas={miles(sum(m.filas or 0 for m in lineas))}, "
           f"truncated={bandera(any(m.truncated for m in lineas))}")
    return [] if contratos else ["fetch_contratos no devolvió ningún contrato"]


# ------------------------------------------------------------------ #
# R30 · familias agregada frente a por líneas, CIF frente a DISTINCT
# ------------------------------------------------------------------ #
def comparar_familias(entorno: Entorno, *, obras: list[str], salida: Callable[[str], None]) -> bool:
    con_error = diferencias = cif_distintos = 0
    for obra in obras:
        salida(f"Obra {obra}")
        agregada, error, med_agregada = entorno.llamar(
            lambda o=obra: entorno.cliente.fetch_contratos_resumen_por_obra(codigo_obra=o)
        )
        if error is None:
            lineas, error, med_lineas = entorno.llamar(
                lambda o=obra: entorno.leer(_SQL_LINEAS_OBRA, [o], f"lineas_obra_{o}")
            )
        if error is None:
            distinct, error, _ = entorno.llamar(
                lambda o=obra: entorno.cliente.fetch_proveedores_por_obra(codigo_obra=o)
            )
        if error is not None:
            salida(f"  ERROR: {entorno.error(error)}")
            con_error += 1
            continue
        for etiqueta, mediciones in (("agregada", med_agregada), ("por líneas", med_lineas)):
            m = mediciones[-1]
            salida(f"  {etiqueta}: {miles(m.filas)} filas, truncated={bandera(m.truncated)}, "
                   f"{decimal(m.segundos)} s, {miles(m.bytes)} bytes")
        salida(f"  DISTINCT (fetch_proveedores_por_obra): {len(distinct)} CIF")

        textos_agregada = {r.cif: r.texto for r in agregada}
        columnas = list(lineas[0]) if lineas else []
        textos_lineas = texto_por_lineas(columnas, [list(f.values()) for f in lineas])
        cif_distinct = {c for c, _ in distinct if c}
        de_mas = sorted(set(textos_agregada) - cif_distinct)
        de_menos = sorted(cif_distinct - set(textos_agregada))
        salida(f"  CIF: agregada {len(textos_agregada)} · por líneas {len(textos_lineas)} · "
               f"DISTINCT {len(cif_distinct)} · de más {len(de_mas)} · de menos {len(de_menos)}")
        if de_mas:
            salida(f"    de más: {', '.join(de_mas)}")
        if de_menos:
            salida(f"    de menos: {', '.join(de_menos)}")
        distintas = []
        for c in sorted(set(textos_agregada) | set(textos_lineas)):
            por_lineas, agregadas = _familias(textos_lineas.get(c)), _familias(textos_agregada.get(c))
            if por_lineas != agregadas:
                distintas.append(f"    {c}: por líneas {por_lineas} · agregada {agregadas}")
        salida(f"  Diferencias de familias: {len(distintas)}")
        for linea in distintas:
            salida(linea)
        diferencias += len(distintas)
        cif_distintos += len(de_mas) + len(de_menos)
    detalle = (f"{len(obras)} obra(s), {diferencias} diferencias de familias, "
               f"{cif_distintos} CIF distintos")
    if con_error:
        detalle = f"{con_error} obra(s) con error, " + detalle
    ok = not (con_error or diferencias or cif_distintos)
    salida(f"RESULTADO R30: {'OK' if ok else 'FALLA'} ({detalle})")
    return ok


# ------------------------------------------------------------------ #
# design §8 · obras de más de 1.000 líneas
# ------------------------------------------------------------------ #
def listar_obras_grandes(entorno: Entorno, *, salida: Callable[[str], None]) -> bool:
    filas, error, _ = entorno.llamar(lambda: entorno.leer(_SQL_OBRAS_GRANDES, [], "obras_grandes"))
    if error is not None:
        salida(f"ERROR: {entorno.error(error)}")
        return False
    salida(f"Obras con más de 1.000 líneas de contrato: {len(filas)}")
    salida("  obra      líneas  proveedores")
    for f in filas:
        salida(f"  {f['obra']!s:<6}{miles(f['lineas']):>8}{miles(f['proveedores']):>13}")
    lista = ", ".join(f"'{f['obra']}'" for f in filas)
    salida(f"Lista para el SELECT de sospechosos (T23): {lista}")
    return True


def _veredicto(etiqueta: str, fallos: list[str], salida: Callable[[str], None]) -> bool:
    if not fallos:
        salida(f"RESULTADO {etiqueta}: OK")
        return True
    salida(f"RESULTADO {etiqueta}: FALLA")
    for fallo in fallos:
        salida(f"  - {fallo}")
    return False


# ------------------------------------------------------------------ #
# Entrada
# ------------------------------------------------------------------ #
def _analizar(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="verificar_f052_proveedores_obra.py",
        description="F-052: verificación de solo lectura contra sigrid-api (R29, R30, design §8).",
    )
    parser.add_argument("--obra", action="append", default=[], help="código de obra (repetible en --comparar-familias)")
    parser.add_argument("--cif", help="CIF esperado entre los proveedores de la obra (R29)")
    parser.add_argument("--nombre", help="nombre de proveedor leído, para el score (R29)")
    parser.add_argument("--repeticiones", type=int, default=1, help="llamadas seguidas a la agregada (R29)")
    parser.add_argument("--comparar-familias", action="store_true", help="R30: agregada frente a por líneas")
    parser.add_argument("--listar-obras-grandes", action="store_true", help="design §8: obras de más de 1.000 líneas")
    args = parser.parse_args(argv)
    if args.listar_obras_grandes and (args.obra or args.comparar_familias):
        parser.error("--listar-obras-grandes no admite --obra ni --comparar-familias")
    if not args.listar_obras_grandes and not args.obra:
        parser.error("falta --obra (o --listar-obras-grandes)")
    if not (args.listar_obras_grandes or args.comparar_familias) and len(args.obra) != 1:
        parser.error("la verificación R29 es de UNA obra; para varias, --comparar-familias")
    if args.repeticiones < 1:
        parser.error("--repeticiones debe ser 1 o más")
    return args


def main(
    argv: list[str] | None = None,
    *,
    construir: Callable[[], Entorno] = construir_cliente,
    salida: Callable[[str], None] = print,
) -> int:
    args = _analizar(argv)
    obras = []
    for valor in args.obra:
        obra = normalizar_codigo_obra(valor)
        if obra is None:
            salida(f"{valor!r} no es un código de obra válido (4 dígitos empezando por 0, o 3 dígitos).")
            return 2
        obras.append(obra)
    entorno = construir()
    salida("F-052 · verificación de SOLO LECTURA contra sigrid-api")
    if args.listar_obras_grandes:
        ok = listar_obras_grandes(entorno, salida=salida)
    elif args.comparar_familias:
        ok = comparar_familias(entorno, obras=obras, salida=salida)
    else:
        cif = (args.cif or "").strip().upper().replace(" ", "") or None
        ok = verificar_obra(entorno, obra=obras[0], cif=cif, nombre=args.nombre,
                            repeticiones=args.repeticiones, salida=salida)
    return 0 if ok else 1


if __name__ == "__main__":
    configurar_logs()
    raise SystemExit(main())
