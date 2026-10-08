# tests/doble_sigrid_api.py
"""Doble de sigrid-api para los tests de F-052 (design §7). Sin red.

``httpx.MockTransport`` que atiende ``POST /api/sql/read`` como el real
(``azure-apps/sigrid_api.md`` §6): reconoce cada consulta del cliente de
contratos de sv3 por un fragmento distintivo de su SQL y la sirve desde
UN ÚNICO fixture por líneas de contrato, así que todas las consultas ven
los mismos datos:

- la consulta de resumen ANTIGUA (una fila por línea, sin ``ORDER BY``:
  el orden de llegada es el del fixture);
- la AGREGADA (``WITH`` + ``FOR XML PATH``), calculada en Python con su
  semántica: por proveedor, valores recortados (solo espacios, como
  ``LTRIM(RTRIM())``), distintos y no vacíos de nombre de contrato,
  descripción de línea y código de producto, unidos por espacio y en
  orden; códigos de contrato distintos y ordenados, unidos por ``|``;
- ``header_and_lines`` y ``search_proveedores``, con ``OFFSET/FETCH``;
- ``fetch_proveedor_by_cif``, ``proveedores_por_obra`` y los documentos
  del contrato (``rcg``/``gra``);
- las obras de más de 1.000 líneas del script de verificación (T14).

Como el real: ``max_rows`` por defecto 200, se devuelven como mucho
``max_rows`` filas y ``truncated=true`` si se alcanzó (``>=``);
``OFFSET`` sin ``ORDER BY`` es un error de SQL Server (400, ``ok=false``).
Modos: ``error_xml`` (la agregada falla con «FOR XML could not
serialize»), ``forzar_truncado`` (toda respuesta dice ``truncated=true``)
y ``barajar`` (semilla: baraja las respuestas sin orden fijado por
``OFFSET``, como haría el servidor con otro plan de ejecución).

Fixture «0691»: 2.083 filas, 81 proveedores, semilla fija y B82899550
(SALMEDINA, contrato CTSU24/0402 con 5 líneas) a partir de la fila 1.000
de la consulta antigua. Trae descripciones repetidas, espacios sobrantes,
vacíos y ``NULL`` (R4) y un proveedor con un contrato sin líneas.
Obra «0668»: un proveedor con 1.200 líneas (R11). Lista global de
proveedores: 3.543 (R12).

Fixture «F-062» (``fixture_f062``, aparte): obras 0720 y 0678 de los tres
albaranes medidos el 2026-10-07 (HORMIGONES MAT y ARIDOS ANFERSA, con una
hormigonera que empata por nombre).

Fixture «F-063» (``fixture_f063``, aparte): obra 0694 de la incidencia de
FEYMACO del 2026-10-08, con Construcciones Ruesma (el cliente) en ``prv``.
"""
from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import httpx

CIF_SALMEDINA = "B82899550"
RAZ_SALMEDINA = "SALMEDINA, S.L."
CONTRATO_SALMEDINA = "CTSU24/0402"
CIF_GRANDE_0668 = "B00001200"
LINEAS_GRANDE_0668 = 1200
TOTAL_PROVEEDORES_GLOBAL = 3543

_BASE_URL = "https://sigrid-api.doble"

_VOCABULARIO: dict[str, tuple[str, ...]] = {
    "hormigon": ("HORMIGON HA-25/B/20/IIa", "HORMIGÓN HM-20/P/20/I", "BOMBEO DE HORMIGON"),
    "mortero": ("MORTERO M-7,5 SECO", "MORTERO COLA GRIS"),
    "residuos": ("CONTENEDOR 6 M3 RCD", "CANON VERTIDO ESCOMBRO LIMPIO"),
    "acero": ("ACERO CORRUGADO B500S", "MALLAZO ME 15X15 D6", "FERRALLA ELABORADA"),
    "combustible": ("GASOLEO A GRANEL", "ADBLUE GRANEL"),
    "maquinaria": ("ALQUILER RETROEXCAVADORA MIXTA", "GRUA AUTOPROPULSADA 50T"),
    "neutro": ("PARTIDA ALZADA", "TRANSPORTE", "MANO DE OBRA OFICIAL 1ª", "PORTES", "SUMINISTRO VARIOS"),
}
_PERFILES = [k for k in _VOCABULARIO if k != "neutro"]

_ERROR_XML = (
    "FOR XML could not serialize the data for node 'NoName' because it "
    "contains a character (0x0001) which is not allowed in XML."
)

_COLUMNAS_HEADER = [
    "contrato_ide", "codigo_contrato", "nombre_contrato", "fecha_alta_contrato",
    "fecha_contrato", "vigencia_desde", "vigencia_hasta", "importe_total",
    "cif_proveedor", "nombre_proveedor", "codigo_obra", "nombre_obra",
    "line_ide", "linea", "numero_linea", "codigo_producto", "codigo_alternativo",
    "unidad_medida", "descripcion_linea", "uds", "cantidad_servida",
    "cantidad_facturada", "pendiente_servir", "precio_unitario", "precio_bruto",
    "descuentos", "importe_linea", "cuota_iva", "doc_origen", "codigo_partida",
    "descripcion_partida",
]


@dataclass(frozen=True)
class Linea:
    """Una fila de ``ctr ⋈ ctrpro``: una línea de contrato (o el contrato
    sin líneas, con los campos de línea a ``None``)."""

    obra: str
    cif: str
    raz: str
    contrato_ide: int
    cod_ctr: str
    res_ctr: str | None
    line_ide: int | None
    pos: int | None
    res_lin: str | None
    cod_pro: str | None


@dataclass(frozen=True)
class Fixture:
    lineas: tuple[Linea, ...]
    proveedores_global: tuple[tuple[str, str], ...]

    def de_obra(self, obra: str) -> list[Linea]:
        return [ln for ln in self.lineas if ln.obra == obra]


# ------------------------------------------------------------------ #
# Fixture
# ------------------------------------------------------------------ #
def _variante(rng: random.Random, valor: str) -> str | None:
    """Mismo valor con ruido: espacios sobrantes, vacío o NULL."""
    r = rng.random()
    if r < 0.06:
        return None
    if r < 0.10:
        return ""
    if r < 0.13:
        return "   "
    if r < 0.30:
        return f"  {valor}   "
    return valor


def _lineas_de_contrato(
    rng: random.Random, *, obra, cif, raz, contrato_ide, cod_ctr, res_ctr,
    n_lineas, perfil, siguiente_linea,
) -> list[Linea]:
    if n_lineas == 0:
        return [Linea(obra, cif, raz, contrato_ide, cod_ctr, res_ctr, None, None, None, None)]
    out = []
    for pos in range(1, n_lineas + 1):
        pool = _VOCABULARIO[perfil] if rng.random() < 0.6 else _VOCABULARIO["neutro"]
        res_lin = _variante(rng, rng.choice(pool))
        cod_pro = _variante(rng, f"P{rng.randint(1, 40):05d}") if rng.random() < 0.7 else None
        out.append(Linea(
            obra, cif, raz, contrato_ide, cod_ctr, res_ctr,
            siguiente_linea(), pos, res_lin, cod_pro,
        ))
    return out


@lru_cache(maxsize=1)
def fixture_por_defecto() -> Fixture:
    rng = random.Random(20260930)
    contador = {"linea": 900000, "contrato": 2400000}

    def siguiente_linea() -> int:
        contador["linea"] += 1
        return contador["linea"]

    def siguiente_contrato() -> int:
        contador["contrato"] += 1
        return contador["contrato"]

    # --- Obra 0691: 81 proveedores, 84 contratos, 2.083 filas --------
    proveedores = [
        (f"B{10000000 + 7919 * i:08d}", f"PROVEEDOR OBRA {i:02d}, S.L.", rng.choice(_PERFILES))
        for i in range(80)
    ]
    contratos: list[dict[str, Any]] = []
    for i, (cif, raz, perfil) in enumerate(proveedores):
        for k in range(2 if i < 3 else 1):
            nombre = rng.choice((
                f"SUMINISTRO {perfil.upper()} OBRA 0691", "CONTRATO MARCO", None, "", "  PEDIDO ABIERTO  ",
            ))
            contratos.append({
                "cif": cif, "raz": raz, "perfil": perfil, "res_ctr": nombre,
                "cod": f"CT{i:02d}{k}/{rng.randint(100, 999)}", "n": 1,
            })
    contratos[-1]["n"] = 0  # contrato sin líneas: su proveedor sigue siendo candidato
    restantes = 2083 - 5 - sum(max(1, c["n"]) for c in contratos)
    con_lineas = [c for c in contratos if c["n"] > 0]
    for _ in range(restantes):
        rng.choice(con_lineas)["n"] += 1
    filas: list[Linea] = []
    for c in contratos:
        filas.extend(_lineas_de_contrato(
            rng, obra="0691", cif=c["cif"], raz=c["raz"], contrato_ide=siguiente_contrato(),
            cod_ctr=c["cod"], res_ctr=c["res_ctr"], n_lineas=c["n"], perfil=c["perfil"],
            siguiente_linea=siguiente_linea,
        ))
    salmedina = [
        Linea("0691", CIF_SALMEDINA, RAZ_SALMEDINA, 2405748, CONTRATO_SALMEDINA,
              "GESTION DE RESIDUOS OBRA 0691", siguiente_linea(), pos, desc, None)
        for pos, desc in enumerate(
            ("CONTENEDOR 6 M3 RCD", "  CONTENEDOR 6 M3 RCD ", "CANON VERTIDO ESCOMBRO LIMPIO",
             "TRANSPORTE", ""), start=1)
    ]
    filas[1500:1500] = salmedina  # más allá de la fila 1.000 de la consulta antigua

    # --- Obra 0668: un proveedor con 1.200 líneas en dos contratos ---
    grande = []
    for cod, n in (("CTGR25/0002", 700), ("CTGR25/0001", 500)):
        grande.extend(_lineas_de_contrato(
            rng, obra="0668", cif=CIF_GRANDE_0668, raz="GRAN SUMINISTRADOR, S.A.",
            contrato_ide=siguiente_contrato(), cod_ctr=cod, res_ctr="SUMINISTRO HORMIGON",
            n_lineas=n, perfil="hormigon", siguiente_linea=siguiente_linea,
        ))
    rng.shuffle(grande)  # la consulta sin ORDER BY no garantiza orden
    otros_0668 = [
        Linea("0668", f"B{20000000 + j:08d}", f"OTRO 0668 {j}", siguiente_contrato(),
              f"CTOT25/{j:04d}", None, siguiente_linea(), 1, "PORTES", None)
        for j in range(2)
    ]

    lineas = tuple(filas + grande + otros_0668)
    en_obras = sorted({(ln.cif, ln.raz) for ln in lineas})
    globales = [
        (f"A{30000000 + n:08d}", f"PROVEEDOR GLOBAL {n:04d}")
        for n in range(TOTAL_PROVEEDORES_GLOBAL - len(en_obras))
    ]
    todos = en_obras + globales
    rng.shuffle(todos)
    return Fixture(lineas=lineas, proveedores_global=tuple(todos))


# ------------------------------------------------------------------ #
# Fixture de F-062 (design §8): los tres albaranes medidos por el humano
# el 2026-10-07. Aparte del de F-052, que no se toca.
# ------------------------------------------------------------------ #
#: Proveedor real de 19407 y 19394 (obra 0720). CIF con control válido.
CIF_HORMIGONES_MAT = "B66056201"
RAZ_HORMIGONES_MAT = "HORMIGONES MAT, S.L.U."
CONTRATO_HORMIGONES_MAT = "CTSU26/0208"
#: Otra hormigonera de la 0720 cuyo nombre EMPATA a 1,0 con «Hormigones
#: Mat SL» («mat» casa con «materiales»), con CIF válido y lejano de los
#: dos leídos: solo la distancia de CIF la separa del bueno.
CIF_HORMIGONERA_EMPATE = "A28123453"
RAZ_HORMIGONERA_EMPATE = "HORMIGONES Y MATERIALES DEL NORTE, S.A."
#: Proveedor real de 1790636816 (obra 0678).
CIF_ARIDOS_ANFERSA = "B18487421"
RAZ_ARIDOS_ANFERSA = "ARIDOS ANFERSA, S.L."
CONTRATO_ARIDOS_ANFERSA = "CTSU24/0176"
#: Otro proveedor de la 0678 que se parece a medias (0,5): no es elegible.
CIF_ARIDOS_SUR = "B11111119"
RAZ_ARIDOS_SUR = "ARIDOS DEL SUR, S.L."

#: Los tres CIF mal leídos por la IA (control inválido; no existen en prv).
CIF_LEIDO_19407 = "B86056201"
CIF_LEIDO_19394 = "B86056095"
CIF_LEIDO_1790636816 = "B18437421"


@lru_cache(maxsize=1)
def fixture_f062() -> Fixture:
    contador = {"linea": 700000}

    def contrato(obra, cif, raz, ide, cod, res, descripciones) -> list[Linea]:
        out = []
        for pos, desc in enumerate(descripciones, start=1):
            contador["linea"] += 1
            out.append(Linea(obra, cif, raz, ide, cod, res, contador["linea"], pos, desc, None))
        return out

    lineas = tuple(
        contrato("0720", CIF_HORMIGONES_MAT, RAZ_HORMIGONES_MAT, 2600208, CONTRATO_HORMIGONES_MAT,
                 "SUMINISTRO HORMIGON OBRA 0720",
                 ("HORMIGON HA-25/B/20/IIa", "BOMBEO DE HORMIGON"))
        + contrato("0720", CIF_HORMIGONERA_EMPATE, RAZ_HORMIGONERA_EMPATE, 2600301, "CTSU26/0301",
                   "SUMINISTRO HORMIGON", ("HORMIGON HM-20/P/20/I",))
        + contrato("0678", CIF_ARIDOS_ANFERSA, RAZ_ARIDOS_ANFERSA, 2400176, CONTRATO_ARIDOS_ANFERSA,
                   "SUMINISTRO ARIDOS OBRA 0678", ("ZAHORRA ARTIFICIAL", "GRAVA 20/40"))
        + contrato("0678", CIF_ARIDOS_SUR, RAZ_ARIDOS_SUR, 2400177, "CTSU24/0177",
                   "ARIDOS", ("ARENA LAVADA",))
    )
    globales = tuple(sorted({(ln.cif, ln.raz) for ln in lineas} | {
        ("A30000001", "PROVEEDOR GLOBAL 0001"),
    }))
    return Fixture(lineas=lineas, proveedores_global=globales)


# ------------------------------------------------------------------ #
# Fixture de F-063 (design §4): la incidencia de FEYMACO del 2026-10-08.
# Aparte de los de F-052 y F-062, que no se tocan.
# ------------------------------------------------------------------ #
#: Construcciones Ruesma: el CLIENTE. Está en ``prv`` (por eso sv3 lo daba
#: por bueno) pero no tiene contrato como proveedor en la obra.
CIF_RUESMA = "A81873903"
RAZ_RUESMA = "CONSTRUCCIONES RUESMA, S.A."
#: FEYMACO, proveedor real del albarán (obra 0694). Su razón social en
#: Sigrid no se conoce: el log de producción prueba que casa por nombre con
#: lo leído, y esta lo cumple.
CIF_FEYMACO = "A28733558"
RAZ_FEYMACO = "FERRETERIA Y MAQUINARIA PARA LA CONSTRUCCION, S.A."
CONTRATO_FEYMACO = "CTSU26/0694"
#: Otro proveedor de la 0694 que no casa por nombre.
CIF_OTRO_0694 = "B44444444"
RAZ_OTRO_0694 = "TRANSPORTES DEL CENTRO, S.L."
#: Lo que leyó la IA (nombre bien; CIF, el del cliente).
NOMBRE_LEIDO_FEYMACO = "FERRETERÍA Y MAQUINARIA PARA LA CONSTRUCCIÓN, S. A."


@lru_cache(maxsize=1)
def fixture_f063() -> Fixture:
    contador = {"linea": 800000}

    def contrato(cif, raz, ide, cod, res, descripciones) -> list[Linea]:
        out = []
        for pos, desc in enumerate(descripciones, start=1):
            contador["linea"] += 1
            out.append(Linea("0694", cif, raz, ide, cod, res, contador["linea"], pos, desc, None))
        return out

    lineas = tuple(
        contrato(CIF_FEYMACO, RAZ_FEYMACO, 2600694, CONTRATO_FEYMACO,
                 "SUMINISTRO FERRETERIA OBRA 0694", ("DISCO CORTE 230 MM", "GUANTES NITRILO"))
        + contrato(CIF_OTRO_0694, RAZ_OTRO_0694, 2600695, "CTSU26/0695", "PORTES", ("PORTES",))
    )
    globales = tuple(sorted({(ln.cif, ln.raz) for ln in lineas} | {
        (CIF_RUESMA, RAZ_RUESMA),
        ("A30000001", "PROVEEDOR GLOBAL 0001"),
    }))
    return Fixture(lineas=lineas, proveedores_global=globales)


# ------------------------------------------------------------------ #
# Semántica de la consulta agregada (design §4), en Python
# ------------------------------------------------------------------ #
def _recorta(valor: str | None) -> str | None:
    if valor is None:
        return None
    v = valor.strip(" ")  # LTRIM/RTRIM de SQL Server: solo espacios
    return v or None


def filas_agregadas(lineas: list[Linea]) -> list[list[Any]]:
    """``[cif, nombre, codigos_contratos, texto]`` por ``(cif, raz)``,
    ordenadas por ``cif, raz`` como la SQL."""
    textos: dict[str, set[str]] = {}
    codigos: dict[str, set[str]] = {}
    for ln in lineas:
        textos.setdefault(ln.cif, set())
        codigos.setdefault(ln.cif, set()).add(ln.cod_ctr)
        for v in (ln.res_ctr, ln.res_lin, ln.cod_pro):
            r = _recorta(v)
            if r:
                textos[ln.cif].add(r)
    out = []
    for cif, raz in sorted({(ln.cif, ln.raz) for ln in lineas}):
        texto = " ".join(sorted(textos[cif])) or None
        out.append([cif, raz, "|".join(sorted(codigos[cif])), texto])
    return out


# ------------------------------------------------------------------ #
# El doble
# ------------------------------------------------------------------ #
_RE_OFFSET = re.compile(r"OFFSET\s+\?\s+ROWS\s+FETCH\s+NEXT\s+\?\s+ROWS\s+ONLY", re.IGNORECASE)
_RE_ORDER_BY = re.compile(r"\bORDER\s+BY\b", re.IGNORECASE)


class ErrorSql(Exception):
    pass


class DobleSigridApi:
    """sigrid-api en memoria. ``peticiones`` guarda cada payload recibido
    y ``respuestas`` cada cuerpo devuelto, en orden."""

    def __init__(
        self,
        fixture: Fixture | None = None,
        *,
        error_xml: bool = False,
        forzar_truncado: bool = False,
        barajar: int | None = None,
    ) -> None:
        self.fixture = fixture or fixture_por_defecto()
        self.error_xml = error_xml
        self.forzar_truncado = forzar_truncado
        self._rng = random.Random(barajar) if barajar is not None else None
        self.peticiones: list[dict[str, Any]] = []
        self.respuestas: list[dict[str, Any]] = []
        self.transport = httpx.MockTransport(self._atender)

    def cliente(self, **kwargs):
        """``SigridApiContratoClient`` de sv3 conectado a este doble."""
        from infrastructure.sigrid.sigrid_api_contrato_client import (
            SigridApiContratoClient,
        )

        return SigridApiContratoClient(
            base_url=_BASE_URL, function_key="clave-de-test", database="ruesma",
            transport=self.transport, **kwargs,
        )

    def peticiones_con(self, fragmento: str) -> list[dict[str, Any]]:
        return [p for p in self.peticiones if fragmento in p["sql"]]

    # --- HTTP ------------------------------------------------------ #
    def _atender(self, request: httpx.Request) -> httpx.Response:
        if request.url.path != "/api/sql/read":
            return httpx.Response(404, json={"ok": False, "error": "ruta desconocida"})
        payload = json.loads(request.content)
        self.peticiones.append(payload)
        try:
            columnas, filas, ordenado = self._consulta(payload["sql"], list(payload.get("parameters") or []))
        except ErrorSql as exc:
            body = {"ok": False, "error": str(exc), "details": {"type": "sql"}}
            self.respuestas.append(body)
            return httpx.Response(400, json=body)
        if self._rng is not None and not ordenado:
            filas = list(filas)
            self._rng.shuffle(filas)
        max_rows = int(payload.get("max_rows") or 200)
        truncated = len(filas) >= max_rows or self.forzar_truncado
        filas = filas[:max_rows]
        body = {
            "ok": True, "database": payload.get("database"), "columns": columnas,
            "rows": filas, "row_count": len(filas), "truncated": truncated,
        }
        self.respuestas.append(body)
        return httpx.Response(200, json=body)

    # --- SQL ------------------------------------------------------- #
    def _consulta(self, sql: str, params: list[Any]) -> tuple[list[str], list[list[Any]], bool]:
        paginada = bool(_RE_OFFSET.search(sql))
        if paginada and not _RE_ORDER_BY.search(_RE_OFFSET.sub("", sql)):
            raise ErrorSql("Invalid usage of the option NEXT in the FETCH statement.")
        offset = fetch = None
        if paginada:
            params, (offset, fetch) = params[:-2], params[-2:]

        columnas, filas, ordenado = self._despachar(sql, params)
        if paginada:
            filas = filas[int(offset):int(offset) + int(fetch)]
        return columnas, filas, ordenado or paginada

    def _despachar(self, sql: str, params: list[Any]) -> tuple[list[str], list[list[Any]], bool]:
        fx = self.fixture
        if "HAVING COUNT(*) > 1000" in sql:
            # Script de T14 (--listar-obras-grandes): filas de la consulta
            # por líneas y proveedores distintos, por obra.
            por_obra: dict[str, list[Linea]] = {}
            for ln in fx.lineas:
                por_obra.setdefault(ln.obra, []).append(ln)
            filas = [
                [obra, len(lns), len({ln.cif for ln in lns})]
                for obra, lns in por_obra.items() if len(lns) > 1000
            ]
            filas.sort(key=lambda f: (-f[1], f[0]))
            return ["obra", "lineas", "proveedores"], filas, True
        if "SELECT TOP 1 prv.cif" in sql:
            buscado = str(params[0])
            nombres = {c: n for c, n in fx.proveedores_global}
            fila = [[buscado, nombres[buscado]]] if buscado in nombres else []
            return ["cif", "nombre"], fila, True
        if "AS contrato_ide" in sql:
            cif, obra = params
            lineas = [ln for ln in fx.de_obra(obra) if ln.cif == cif]
            lineas.sort(key=lambda ln: (
                ln.cod_ctr, ln.contrato_ide,
                -1 if ln.pos is None else ln.pos,
                -1 if ln.line_ide is None else ln.line_ide,
            ))
            return _COLUMNAS_HEADER, [_fila_header(ln) for ln in lineas], True
        if "FOR XML PATH" in sql:
            if self.error_xml:
                raise ErrorSql(_ERROR_XML)
            return (
                ["cif", "nombre", "codigos_contratos", "texto"],
                filas_agregadas(fx.de_obra(params[0])),
                False,
            )
        if "prv.cif IS NOT NULL AND con.emp = 1" in sql:
            filas = [list(p) for p in fx.proveedores_global]
            if _RE_ORDER_BY.search(sql):
                filas.sort(key=lambda f: (f[0], f[1]))
            return ["cif", "nombre"], filas, bool(_RE_ORDER_BY.search(sql))
        if "SELECT DISTINCT prv.cif AS cif, prv.raz AS nombre" in sql and "con_obr.cod = ?" in sql:
            filas = [list(p) for p in sorted({(ln.cif, ln.raz) for ln in fx.de_obra(params[0])})]
            return ["cif", "nombre"], filas, False
        if "AS descripcion_linea" in sql and "con_obr.cod = ?" in sql:
            filas = [
                [ln.cif, ln.raz, ln.cod_ctr, ln.res_ctr, ln.res_lin, ln.cod_pro]
                for ln in fx.de_obra(params[0])
            ]
            columnas = ["cif", "nombre", "codigo_contrato", "nombre_contrato",
                        "descripcion_linea", "codigo_producto"]
            return columnas, filas, False
        if "FROM rcg" in sql:
            ide = int(params[0])
            return (
                ["rcg_pos", "gra_cod", "gra_nom", "gra_nomori", "gra_fec"],
                [[1, f"G{ide}", "contrato.pdf", "contrato.pdf", 20240802]],
                True,
            )
        if "FROM gra" in sql and "WHERE cod = ?" in sql:
            cod = str(params[0])
            return ["gra_rep_ide", "gra_nom", "gra_nomori"], [[int(cod[1:]) + 1, "contrato.pdf", "contrato.pdf"]], True
        raise ErrorSql(f"doble: SQL no reconocida: {sql[:120]!r}")


def _fila_header(ln: Linea) -> list[Any]:
    valores = {
        "contrato_ide": ln.contrato_ide, "codigo_contrato": ln.cod_ctr,
        "nombre_contrato": ln.res_ctr, "fecha_alta_contrato": 20240801,
        "fecha_contrato": 20240802, "vigencia_desde": 0, "vigencia_hasta": 0,
        "importe_total": 1000.0, "cif_proveedor": ln.cif, "nombre_proveedor": ln.raz,
        "codigo_obra": ln.obra, "nombre_obra": f"OBRA {ln.obra}",
        "line_ide": ln.line_ide, "linea": ln.pos, "numero_linea": ln.pos,
        "codigo_producto": ln.cod_pro, "descripcion_linea": ln.res_lin,
        "uds": None if ln.pos is None else 1.0,
    }
    return [valores.get(c) for c in _COLUMNAS_HEADER]
