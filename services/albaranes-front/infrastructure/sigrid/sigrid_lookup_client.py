# infrastructure/sigrid/sigrid_lookup_client.py
from __future__ import annotations

import json
import logging
from typing import Any

import httpx
from ruesma_comun.obras import canonizar_codigo_obra
from ruesma_comun.proveedores import cifs_propios, es_cif_propio, normalizar_cif
from ruesma_comun.sigrid import (
    SQL_PARTIDAS_POR_OBRA,
    ListaPartidasObra,
    PoliticaTruncado,
    comprobar_truncado,
    leer_partidas_obra,
)

from domain.models.review_models import (
    BusquedaProveedores,
    ContratoOption,
    ObraOption,
    PartidaOption,
    ProveedorOption,
)

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[sigrid-lookup]"


# Proveedores con contrato de compra para una obra. Mismo patron de
# joins que el contrato-client del sv3 (ctr + con + con_obr), pero SIN el
# filtro de cif: queremos TODOS los proveedores de la obra. emp=1 (empresa
# Construcciones Ruesma), igual que el contrato-client.
_SQL_PROVEEDORES_POR_OBRA = """\
SELECT DISTINCT
    prv.cif AS cif,
    prv.raz AS nombre
FROM ctr
JOIN con AS con_ctr ON ctr.ide    = con_ctr.ide
JOIN con AS con_obr ON ctr.obride = con_obr.ide
JOIN prv            ON ctr.entide = prv.ide
WHERE con_obr.cod = ?
  AND con_ctr.emp = 1
ORDER BY prv.raz
"""

# (F-114) Búsqueda global de proveedores VIVOS por nombre o CIF. «Vivo» =
# ficha de ``prv`` cuyo ``con`` tiene ``tip = 5``, ``emp = 1`` y
# ``fecbaj = 0``: la misma definición con la que sigrid-api resuelve la
# identidad de un alta sin contrato (``L17_PROVEEDOR_POR_CIF``). TODO va por
# parámetro (R15). Un proveedor por CIF, con la razón social menor y las
# fichas vivas con ese CIF (R17). ``prv.raz`` es texto de 128, no ``text``:
# admite ``MIN`` y ``ORDER BY``. ``ESCAPE '!'``: la barra invertida da error
# 506 a través de sigrid-api (T0, 2026-10-30).
#
# (T8, 2026-10-31, D2) El texto SOLO elige qué CIF salen (subconsulta ``m``:
# alguna ficha viva suya casa por nombre o por CIF); el nombre y las fichas
# se calculan sobre TODAS las fichas vivas de ese CIF (``v``). Antes el
# filtro iba antes del GROUP BY y un CIF con dos fichas de razón social
# distinta salía con ``fichas = 1`` buscando por el nombre de una de ellas.
_SQL_PROVEEDORES_TODOS = """\
SELECT TOP (?)
    v.cif      AS cif,
    MIN(v.raz) AS nombre,
    COUNT(*)   AS fichas
FROM prv AS v
JOIN con AS c ON c.ide = v.ide
WHERE c.tip = ? AND c.emp = ? AND c.fecbaj = ?
  AND v.cif IN (
      SELECT m.cif
      FROM prv AS m
      JOIN con AS mc ON mc.ide = m.ide
      WHERE mc.tip = ? AND mc.emp = ? AND mc.fecbaj = ?
        AND m.cif IS NOT NULL AND LTRIM(RTRIM(m.cif)) <> ''
        AND (m.raz COLLATE Latin1_General_CI_AI LIKE ? ESCAPE '!'
             OR REPLACE(REPLACE(UPPER(m.cif), ' ', ''), '-', '') LIKE ? ESCAPE '!')
  )
GROUP BY v.cif
ORDER BY MIN(v.raz), v.cif
"""

#: (F-114 D1) Caracteres útiles mínimos del texto y proveedores por respuesta.
MINIMO_BUSQUEDA_PROVEEDOR = 3
LIMITE_BUSQUEDA_PROVEEDOR = 50
#: ``con.tip`` de un proveedor y empresa Construcciones Ruesma (D7).
TIP_PROVEEDOR = 5
EMPRESA_RUESMA = 1

#: (F-114 R19, F-063) Los CIF propios nunca se ofrecen como proveedor.
_CIFS_PROPIOS = cifs_propios(None)

#: Carácter de escape del ``LIKE`` y lo que hay que escapar con él (R16).
_ESCAPE_LIKE = "!"
_COMODINES_LIKE = ("!", "%", "_", "[")


def _patron_like(texto: str) -> str:
    """``%texto%`` con ``!``, ``%``, ``_`` y ``[`` como literales (R16)."""
    escapado = "".join(
        _ESCAPE_LIKE + c if c in _COMODINES_LIKE else c for c in texto
    )
    return f"%{escapado}%"


# Lista de obras (codigo + nombre). Mismo join que el obra-client del sv3
# (obr + con). Sin filtro emp para no excluir obras.
#
# IMPORTANTE: NO usar SELECT DISTINCT aqui. ``obr.res`` es de tipo
# text/ntext en Sigrid y SQL Server lanza error 42000 ("el tipo de datos
# text/ntext no se puede seleccionar como DISTINCT porque no es
# comparable"). Por eso traemos todas las filas (una por obra; pueden
# repetirse con.cod si la obra se recreo) y DEDUPLICAMOS POR CODIGO en
# Python. ``ORDER BY con.cod`` si es valido porque ``cod`` es comparable.
_SQL_OBRAS = """\
SELECT
    con.cod AS codigo,
    obr.res AS nombre
FROM obr
JOIN con ON obr.ide = con.ide
WHERE con.cod IS NOT NULL
ORDER BY con.cod
"""

# Contratos de una obra (codigo + nombre del contrato + proveedor). Mismo
# join que proveedores (ctr + con_ctr + con_obr), filtrando por obra. emp=1
# (Construcciones Ruesma). NO usamos SELECT DISTINCT porque ``con_ctr.res``
# (nombre del contrato) es text/ntext en Sigrid y SQL Server no permite
# DISTINCT sobre ese tipo (error 42000); deduplicamos POR CODIGO en Python,
# igual que el desplegable de obras. El filtro por CIF se aplica en Python
# (laxo, normalizando) para tolerar diferencias de formato del CIF.
_SQL_CONTRATOS_POR_OBRA = """\
SELECT
    con_ctr.cod AS codigo,
    con_ctr.res AS nombre,
    ctr.entcif  AS cif,
    prv.raz     AS nombre_proveedor
FROM ctr
JOIN con AS con_ctr ON ctr.ide    = con_ctr.ide
JOIN con AS con_obr ON ctr.obride = con_obr.ide
JOIN prv            ON ctr.entide = prv.ide
WHERE con_obr.cod = ?
  AND con_ctr.emp = 1
ORDER BY con_ctr.cod
"""

# (F-076 R15) La consulta de partidas y el cálculo de hojas viven en
# ``ruesma_comun.sigrid.partidas`` (la misma lista que normaliza sv6). Este
# nombre se conserva SOLO como referencia a la de comun (no es una copia):
# los tests de F-052 y F-070 reconocen la consulta por él.
_SQL_PARTIDAS_POR_OBRA = SQL_PARTIDAS_POR_OBRA


class SigridLookupClient:
    """Cliente HTTP de SOLO LECTURA contra la Function App ``sigrid-api``.

    Sirve los desplegables de cabecera del portal (elegir proveedor con
    contrato en la obra / elegir obra). No persiste nada ni toca el camino
    de escritura de contratos (eso es del sv3). Realiza POST a
    ``/api/sql/read`` con cabecera ``x-functions-key``.
    """

    def __init__(
        self,
        *,
        base_url: str,
        function_key: str,
        database: str,
        timeout_s: float = 30.0,
        max_rows: int = 5000,
    ) -> None:
        if not base_url:
            raise ValueError("SigridLookupClient requiere base_url no vacio")
        if not function_key:
            raise ValueError("SigridLookupClient requiere function_key no vacio")
        if not database:
            raise ValueError("SigridLookupClient requiere database no vacio")
        self._base_url = base_url.rstrip("/")
        self._function_key = function_key
        self._database = database
        self._timeout_s = float(timeout_s)
        self._max_rows = int(max_rows)
        logger.info(
            "%s Instanciado. base_url=%s database=%s timeout_s=%s max_rows=%s key_len=%s",
            _LOG_PREFIX,
            self._base_url,
            self._database,
            self._timeout_s,
            self._max_rows,
            len(function_key),
        )

    # ----------------------------------------------------------------- #
    # API publica
    # ----------------------------------------------------------------- #
    def fetch_proveedores_por_obra(
        self,
        *,
        codigo_obra: str,
    ) -> list[ProveedorOption]:
        # F-070 · R10/R11: obra canónica (``686`` ⇒ ``0686``, ``var`` ⇒
        # ``VAR``); lo que no encaja, recortado como hoy.
        codigo = canonizar_codigo_obra(codigo_obra)
        if not codigo:
            return []
        columns, rows = self._post_sql_read(
            sql=_SQL_PROVEEDORES_POR_OBRA,
            parameters=[codigo],
            label=f"proveedores_obra_{codigo}",
            # F-052 R28: una lista de proveedores a la que le falta el
            # bueno es peor que el aviso «Sigrid no disponible» (el front
            # mantiene la entrada manual).
            politica=PoliticaTruncado.NO_TOLERA,
        )
        seen: set[str] = set()
        out: list[ProveedorOption] = []
        for row in rows:
            row_map = dict(zip(columns, row))
            cif = _opt_str(row_map.get("cif"))
            if not cif or cif in seen:
                continue
            seen.add(cif)
            out.append(
                ProveedorOption(cif=cif, nombre=_opt_str(row_map.get("nombre")))
            )
        logger.info(
            "%s proveedores_por_obra obra=%s -> %s proveedores",
            _LOG_PREFIX,
            codigo,
            len(out),
        )
        return out

    def buscar_proveedores(self, *, texto: str) -> BusquedaProveedores:
        """(F-114) Proveedores vivos de Sigrid cuyo nombre o CIF contienen
        ``texto``: uno por CIF, ordenados por nombre, como mucho
        ``LIMITE_BUSQUEDA_PROVEEDOR`` y ``mas`` si había más (R17, R18).

        Nombre sin mayúsculas ni acentos (``COLLATE``) y CIF sin espacios,
        guiones ni mayúsculas; ``%``, ``_``, ``[`` y ``!`` literales (R16).
        Fuera los CIF propios y las filas sin CIF (R19). Truncado ⇒
        ``SigridRespuestaTruncada`` (``NO_TOLERA``, R20). Bajo el mínimo,
        vacío sin llamar (el endpoint ya corta, R13).
        """
        t = (texto or "").strip()
        if len(t) < MINIMO_BUSQUEDA_PROVEEDOR:
            return BusquedaProveedores(items=[], mas=False)
        patron_nombre = _patron_like(t)
        patron_cif = _patron_like(t.upper().replace(" ", "").replace("-", ""))
        columns, rows = self._post_sql_read(
            sql=_SQL_PROVEEDORES_TODOS,
            # Vivo dos veces: en las fichas que se cuentan (``v``) y en las
            # que casan con el texto (``m``, T8 D2).
            parameters=[
                LIMITE_BUSQUEDA_PROVEEDOR + 1,
                TIP_PROVEEDOR,
                EMPRESA_RUESMA,
                0,
                TIP_PROVEEDOR,
                EMPRESA_RUESMA,
                0,
                patron_nombre,
                patron_cif,
            ],
            label="proveedores_todos",
            # Como la lista de la obra (F-052 R28): una búsqueda a la que le
            # falta el bueno es peor que el aviso de error.
            politica=PoliticaTruncado.NO_TOLERA,
        )
        # Dedupe por CIF normalizado: dos grafías del mismo CIF llegan en
        # grupos distintos del GROUP BY; se suman sus fichas y se conserva
        # el primero (ya ordenado por nombre).
        por_cif: dict[str, ProveedorOption] = {}
        for row in rows:
            row_map = dict(zip(columns, row))
            cif = _opt_str(row_map.get("cif"))
            clave = normalizar_cif(cif)
            if not clave or es_cif_propio(cif, _CIFS_PROPIOS):
                continue
            fichas = int(row_map.get("fichas") or 1)
            previo = por_cif.get(clave)
            if previo is None:
                por_cif[clave] = ProveedorOption(
                    cif=cif, nombre=_opt_str(row_map.get("nombre")), fichas=fichas,
                )
            else:
                previo.fichas = (previo.fichas or 0) + fichas
        mas = len(rows) > LIMITE_BUSQUEDA_PROVEEDOR
        items = list(por_cif.values())[:LIMITE_BUSQUEDA_PROVEEDOR]
        logger.info(
            "%s proveedores_todos texto=%r -> %s proveedores mas=%s",
            _LOG_PREFIX,
            t,
            len(items),
            mas,
        )
        return BusquedaProveedores(items=items, mas=mas)

    def fetch_obras(self) -> list[ObraOption]:
        columns, rows = self._post_sql_read(
            sql=_SQL_OBRAS,
            parameters=[],
            label="obras",
            politica=PoliticaTruncado.TOLERA,
        )
        seen: set[str] = set()
        out: list[ObraOption] = []
        for row in rows:
            row_map = dict(zip(columns, row))
            cod = _opt_str(row_map.get("codigo"))
            if not cod or cod in seen:
                continue
            seen.add(cod)
            out.append(
                ObraOption(codigo=cod, nombre=_opt_str(row_map.get("nombre")))
            )
        logger.info("%s obras -> %s obras", _LOG_PREFIX, len(out))
        return out

    def fetch_partidas_por_obra(
        self,
        *,
        codigo_obra: str,
    ) -> list[PartidaOption]:
        """Partidas HOJA del presupuesto de la obra en Sigrid (F-076 R15).

        Delega en ``ruesma_comun.sigrid.leer_partidas_obra``: la misma SQL
        (con ``con_obr.emp = 1``) y la misma definición de hoja que usa sv6 al
        normalizar (nunca capítulos ni subcapítulos; ``descripcion_agregada`` =
        ruta de capítulos). La obra se canoniza con ``canonizar_codigo_obra``
        (F-070); vacía ⇒ ``[]`` sin consultar. Lista truncada ⇒
        ``SigridRespuestaTruncada`` (``NO_TOLERA``, 500.000 filas), que el
        endpoint convierte en ``ok=false`` (P7).

        (F-098) El endpoint lee por la caché de sv4 (``lector_partidas``); esto
        queda para quien quiera la lista sin caché, con los mismos campos.
        """
        lista = leer_partidas_obra(self.lector_partidas, codigo_obra)
        if lista is None:
            return []
        out = opciones_partida(lista)
        logger.info(
            "%s partidas_por_obra obra=%s -> %s partidas hoja (%s no hoja)",
            _LOG_PREFIX,
            lista.obra,
            len(out),
            len(lista.no_hojas),
        )
        return out

    def lector_partidas(
        self,
        sql: str,
        parametros: list[Any],
        etiqueta: str,
        politica: PoliticaTruncado,
        max_rows: int,
    ) -> tuple[list[str], list[list[Any]]]:
        """``LectorSql`` de comun sobre el HTTP de este cliente.

        Aplica la política y el ``max_rows`` que pide comun (``NO_TOLERA`` y
        500.000 filas): una lista de partidas truncada calcularía mal las
        hojas sin error. (F-098 R27) Público: sobre él se monta la
        ``CachePartidasObra`` de sv4 (``app.py``).
        """
        return self._post_sql_read(
            sql=sql,
            parameters=parametros,
            label=etiqueta,
            politica=politica,
            max_rows=max_rows,
        )

    def fetch_contratos(
        self,
        *,
        codigo_obra: str,
        cif: str | None = None,
    ) -> list[ContratoOption]:
        """Contratos de una obra en Sigrid (codigo + nombre + proveedor).

        Si se pasa ``cif``, filtra (laxo, normalizado) a los contratos de
        ese proveedor; si no, devuelve todos los de la obra. Deduplica por
        codigo de contrato.
        """
        # F-070 · R10/R11: obra canónica (``686`` ⇒ ``0686``, ``var`` ⇒
        # ``VAR``); lo que no encaja, recortado como hoy.
        codigo = canonizar_codigo_obra(codigo_obra)
        if not codigo:
            return []
        columns, rows = self._post_sql_read(
            sql=_SQL_CONTRATOS_POR_OBRA,
            parameters=[codigo],
            label=f"contratos_obra_{codigo}",
            politica=PoliticaTruncado.TOLERA,
        )

        def _norm_cif(value: str | None) -> str:
            return (value or "").strip().upper().replace(" ", "").replace("-", "")

        cif_filtro = _norm_cif(cif) if cif else None
        seen: set[str] = set()
        out: list[ContratoOption] = []
        for row in rows:
            row_map = dict(zip(columns, row))
            cod = _opt_str(row_map.get("codigo"))
            if not cod or cod in seen:
                continue
            row_cif = _opt_str(row_map.get("cif"))
            if cif_filtro and _norm_cif(row_cif) != cif_filtro:
                continue
            seen.add(cod)
            out.append(
                ContratoOption(
                    codigo=cod,
                    nombre=_opt_str(row_map.get("nombre")),
                    cif=row_cif,
                    nombre_proveedor=_opt_str(row_map.get("nombre_proveedor")),
                )
            )
        logger.info(
            "%s contratos_obra obra=%s cif=%s -> %s contratos",
            _LOG_PREFIX, codigo, cif_filtro or "(todos)", len(out),
        )
        return out

    # ----------------------------------------------------------------- #
    # HTTP primitive
    # ----------------------------------------------------------------- #
    def _post_sql_read(
        self,
        *,
        sql: str,
        parameters: list[Any],
        label: str,
        politica: PoliticaTruncado,
        max_rows: int | None = None,
    ) -> tuple[list[str], list[list[Any]]]:
        """POST a ``/api/sql/read``.

        ``politica`` es obligatoria (F-052 R28): ``truncated=true`` nunca
        pasa en silencio. ``NO_TOLERA`` lanza ``SigridRespuestaTruncada``;
        ``TOLERA`` devuelve las filas y deja un WARNING con la etiqueta.
        ``max_rows``: ``None`` = el del cliente (F-076: las partidas piden el
        suyo).
        """
        url = f"{self._base_url}/api/sql/read"
        payload = {
            "database": self._database,
            "sql": sql,
            "parameters": parameters,
            "timeout_seconds": int(self._timeout_s),
            "max_rows": self._max_rows if max_rows is None else int(max_rows),
        }
        headers = {
            "x-functions-key": self._function_key,
            "Content-Type": "application/json",
        }

        logger.info(
            "%s REQUEST [%s] -> POST %s db=%s params=%s",
            _LOG_PREFIX,
            label,
            url,
            self._database,
            parameters,
        )

        transport = httpx.HTTPTransport(retries=1)
        try:
            with httpx.Client(timeout=self._timeout_s, transport=transport) as client:
                response = client.post(url, json=payload, headers=headers)
        except Exception as exc:
            logger.exception(
                "%s FALLO de transporte [%s]. exc=%r", _LOG_PREFIX, label, exc
            )
            raise

        status = response.status_code
        body_text = response.text or ""
        if status >= 400:
            logger.warning(
                "%s RESPONSE [%s] status=%s preview=%s",
                _LOG_PREFIX,
                label,
                status,
                body_text[:300],
            )
            raise RuntimeError(f"sigrid-api respondio {status}: {body_text[:300]}")

        try:
            body: dict[str, Any] = response.json()
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"sigrid-api respuesta no JSON: {body_text[:300]}"
            ) from exc

        if not body.get("ok", False):
            raise RuntimeError(f"sigrid-api devolvio ok=false: {body!r}")

        comprobar_truncado(body, politica=politica, etiqueta=label, logger=logger)

        columns: list[str] = list(body.get("columns") or [])
        rows: list[list[Any]] = list(body.get("rows") or [])
        return columns, rows


def opciones_partida(lista: ListaPartidasObra) -> list[PartidaOption]:
    """(F-098 R14) Las hojas de la lista de comun como opciones del selector:
    el cod, lo que se enseña (``codigo_completo``), su capítulo, su ``ide`` y
    si el cod se repite en la obra; en el orden de la lista."""
    return [
        PartidaOption(
            codigo=hoja.codigo,
            descripcion=hoja.descripcion,
            descripcion_agregada=hoja.descripcion_agregada,
            ide=hoja.ide,
            codigo_completo=hoja.codigo_completo,
            capitulo=hoja.capitulo,
            cod_repetido=lista.cod_repetido(hoja.codigo),
        )
        for hoja in lista.hojas
    ]


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)
