# ruesma_comun/sigrid/partidas.py
"""Partidas HOJA de una obra en Sigrid y cómo casar con ellas una lectura.

Subconjunto APROBADO de F-049 (bloques A y A2, ``224f64e``) portado a ``dev``
por F-076 sin cambios de semántica, más lo que F-076 añade
(:func:`resolver_partida_obra`, :class:`CachePartidasObra`). Cuando F-049 se
retome, su ``partidas.py`` es superconjunto de este: se queda el suyo
conservando lo de F-076 (design §8 de F-076).

EXCEPCIÓN CONSCIENTE A D2 DE F-052 («la SQL de cada servicio no se
comparte»): la lista de partidas de una obra la necesitan varios servicios con
la MISMA consulta y la MISMA definición de hoja —sv4 para su selector y sv6
para normalizar la partida al valorar (F-076)—. Dos copias divergirían (ya
pasó con la normalización del código de obra, F-052 CR-C1), así que la SQL y
el cálculo viven aquí. El HTTP sigue en cada servicio: este módulo recibe la
primitiva de lectura como función (:class:`LectorSql`) y no abre red ni BBDD.

REGLA DE FONDO (H1 del humano, F-049, 2026-10-02): aquí se VERIFICA y se
NORMALIZA, nunca se ELIGE. :func:`casar_partida` solo da por buena una
lectura que coincide con una hoja tal cual o tras :func:`normalizar_partida`;
jamás busca «la más parecida» (ni sufijo, ni prefijo, ni distancia, ni
expansión de abreviaturas). Si no casa, lo dice y la lectura se queda.

- :data:`SQL_PARTIDAS_POR_OBRA`: la de sv4 más el filtro de empresa
  (``con_obr.emp = 1``).
- :func:`hojas_de_filas` y :meth:`ListaPartidasObra.desde_filas`: hojas con
  la semántica de sv4 (padre 0/nulo = sin padre; sin ``cod`` fuera; ruta de
  capítulos; orden por código) y, aparte, los códigos no hoja.
- :func:`normalizar_partida`, :func:`partes_de_partida`,
  :func:`casar_partida` y sus motivos.
"""
from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from ruesma_comun.sigrid.lectura import PoliticaTruncado

# Partidas del presupuesto de una obra (obrparpar). Es la
# ``_SQL_PARTIDAS_POR_OBRA`` de sv4 (``sigrid_lookup_client.py``) del
# 2026-10-02 MÁS el filtro de empresa (design §2 y §4 de F-049): los códigos
# de obra NO son únicos entre empresas (0517 y 0581 existen en la 1 y en
# otra), y sin ``con_obr.emp = 1`` (Construcciones Ruesma, como en las
# consultas de contratos y proveedores de sv3 y sv4) se mezclan las partidas
# de dos obras. Trae TODAS las filas de la obra (ide, padide, cod, res); las
# hojas y la ruta de capítulos se calculan en Python (:func:`hojas_de_filas`).
# ``obride`` apunta a ``obr.ide`` = ``con.ide``; se filtra por código de obra
# y empresa vía ``con``.
SQL_PARTIDAS_POR_OBRA = """\
SELECT
    p.ide    AS ide,
    p.padide AS padide,
    p.cod    AS cod,
    p.res    AS res
FROM obrparpar AS p
JOIN con AS con_obr ON p.obride = con_obr.ide
WHERE con_obr.cod = ?
  AND con_obr.emp = 1
ORDER BY p.cod
"""

# Motivos de :func:`casar_partida`.
MOTIVO_EXACTA = "exacta"
MOTIVO_NORMALIZADA = "normalizada"
MOTIVO_COMPUESTA = "compuesta"
MOTIVO_ALM = "alm"
MOTIVO_SIN_PARTIDA = "sin_partida"
MOTIVO_FUERA_DE_LISTA = "fuera_de_lista"
MOTIVO_AMBIGUA = "ambigua"

MOTIVOS_PARTIDA = frozenset(
    {
        MOTIVO_EXACTA,
        MOTIVO_NORMALIZADA,
        MOTIVO_COMPUESTA,
        MOTIVO_ALM,
        MOTIVO_SIN_PARTIDA,
        MOTIVO_FUERA_DE_LISTA,
        MOTIVO_AMBIGUA,
    }
)
#: Motivos en que la lectura casa con la lista (``validada = true``).
MOTIVOS_CASADOS = frozenset({MOTIVO_EXACTA, MOTIVO_NORMALIZADA, MOTIVO_COMPUESTA})
#: Motivos en que la lectura NO casa (``validada = false``: a revisión).
MOTIVOS_NO_CASADOS = frozenset({MOTIVO_FUERA_DE_LISTA, MOTIVO_AMBIGUA})

# Separa todo lo que no es letra ni dígito (Unicode). El «_» es carácter de
# palabra para ``\w``, así que se añade a mano. La «/» se trata antes.
_RE_SEPARADOR = re.compile(r"[\W_]+")


@dataclass(frozen=True)
class PartidaObra:
    """Partida HOJA de una obra. Mismos campos que ``PartidaOption`` de sv4."""

    codigo: str
    descripcion: str | None
    descripcion_agregada: str | None


@dataclass(frozen=True)
class ListaPartidasObra:
    """Partidas de una obra: las hojas y los códigos que NO son hoja."""

    obra: str
    hojas: tuple[PartidaObra, ...]
    no_hojas: tuple[str, ...]

    @property
    def codigos(self) -> tuple[str, ...]:
        """Códigos de las hojas, en el orden de la lista."""
        return tuple(h.codigo for h in self.hojas)

    @classmethod
    def desde_filas(
        cls, obra: str, columnas: Sequence[str], filas: Sequence[Sequence[Any]]
    ) -> ListaPartidasObra:
        """Construye la lista desde la respuesta de :data:`SQL_PARTIDAS_POR_OBRA`."""
        by_ide, parent_ides = _indexar(columnas, filas)
        no_hojas = sorted(
            {nodo["cod"] for ide, nodo in by_ide.items() if ide in parent_ides and nodo["cod"]}
        )
        return cls(
            obra=obra,
            hojas=tuple(_hojas(by_ide, parent_ides)),
            no_hojas=tuple(no_hojas),
        )


@dataclass(frozen=True)
class CasePartida:
    """Resultado de :func:`casar_partida`.

    ``codigos_lista`` lleva los códigos TAL COMO FIGURAN EN LA LISTA solo
    cuando la lectura casa (``exacta``, ``normalizada``: uno; ``compuesta``:
    uno por parte). En cualquier otro motivo va vacío: no se ofrece ningún
    candidato, para que nadie pueda «elegir» con él (H1).
    """

    motivo: str
    codigos_lista: tuple[str, ...] = ()

    @property
    def validada(self) -> bool | None:
        """``True`` si casa, ``False`` si no casa, ``None`` si no aplica.

        ``None`` para ``alm`` y ``sin_partida``: no hay nada que verificar
        contra la lista (R21).
        """
        if self.motivo in MOTIVOS_CASADOS:
            return True
        if self.motivo in MOTIVOS_NO_CASADOS:
            return False
        return None


class LectorSql(Protocol):
    """Primitiva de lectura de sigrid-api que pone cada servicio.

    Recibe la SQL, sus parámetros, una etiqueta para el log, la política
    de truncado y el ``max_rows``; devuelve ``(columnas, filas)``. Debe
    aplicar ``politica`` con
    :func:`~ruesma_comun.sigrid.lectura.comprobar_truncado`: con
    ``NO_TOLERA``, un ``truncated=true`` lanza
    :class:`~ruesma_comun.sigrid.lectura.SigridRespuestaTruncada`.
    """

    def __call__(
        self,
        sql: str,
        parametros: list[Any],
        etiqueta: str,
        politica: PoliticaTruncado,
        max_rows: int,
    ) -> tuple[list[str], list[list[Any]]]: ...


# ------------------------------------------------------------------ #
# Normalización y partes
# ------------------------------------------------------------------ #
def _segmento(segmento: str) -> str:
    """Quita los ceros a la izquierda a un segmento SOLO numérico."""
    if segmento.isdigit():
        return segmento.lstrip("0") or "0"
    return segmento


def normalizar_partida(codigo: Any) -> str | None:
    """Forma de COMPARACIÓN de un código de partida; ``None`` si no hay.

    NFKC y mayúsculas; todo lo que no es letra ni dígito (salvo ``/``)
    separa segmentos; sin segmentos vacíos; los segmentos solo numéricos
    pierden los ceros a la izquierda; se unen con ``.``. Cada parte de una
    compuesta (``/``) se normaliza por separado y se vuelven a unir con
    ``/``, sin partes vacías. ``CI.04.18`` ≡ ``CI.4.18``.

    Es solo para comparar: nunca se escribe en el albarán (lo que se
    escribe es el código tal como figura en la lista).
    """
    if codigo is None:
        return None
    texto = unicodedata.normalize("NFKC", str(codigo)).upper()
    partes: list[str] = []
    for trozo in texto.split("/"):
        segmentos = [_segmento(s) for s in _RE_SEPARADOR.split(trozo) if s]
        if segmentos:
            partes.append(".".join(segmentos))
    return "/".join(partes) or None


def partes_de_partida(codigo: Any) -> list[str]:
    """Partes de una partida compuesta, cortando por ``/``.

    No completa abreviaturas: ``P4/P5.01.09`` da ``["P4", "P5.01.09"]``,
    nunca ``P4.01.09``. Cada parte va sin espacios exteriores (y en NFKC,
    para cortar también por una barra de ancho completo); las vacías se
    descartan. ``None`` o vacío ⇒ ``[]``.
    """
    if codigo is None:
        return []
    texto = unicodedata.normalize("NFKC", str(codigo))
    return [p.strip() for p in texto.split("/") if p.strip()]


# ------------------------------------------------------------------ #
# Hojas (semántica de sv4, ``fetch_partidas_por_obra``)
# ------------------------------------------------------------------ #
def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


def _indexar(
    columnas: Sequence[str], filas: Sequence[Sequence[Any]]
) -> tuple[dict[Any, dict[str, Any]], set[Any]]:
    """Indexa las filas por ``ide`` y registra qué ``ide`` son padre."""
    columnas = list(columnas)
    by_ide: dict[Any, dict[str, Any]] = {}
    parent_ides: set[Any] = set()
    for row in filas:
        rm = dict(zip(columnas, row))
        ide = rm.get("ide")
        if ide is None:
            continue
        padide = rm.get("padide")
        # En Sigrid el 0 en un índice equivale a "sin padre".
        if padide in (0, "0"):
            padide = None
        by_ide[ide] = {
            "ide": ide,
            "padide": padide,
            "cod": _opt_str(rm.get("cod")),
            "res": _opt_str(rm.get("res")),
        }
        if padide is not None:
            parent_ides.add(padide)
    return by_ide, parent_ides


def _hojas(by_ide: dict[Any, dict[str, Any]], parent_ides: set[Any]) -> list[PartidaObra]:
    def _ruta(node: dict[str, Any]) -> str:
        # Camino raíz→hoja de descripciones (res), evitando ciclos.
        partes: list[str] = []
        visto: set[Any] = set()
        cur: dict[str, Any] | None = node
        while cur is not None and cur["ide"] not in visto:
            visto.add(cur["ide"])
            if cur.get("res"):
                partes.append(cur["res"])
            pad = cur.get("padide")
            cur = by_ide.get(pad) if pad is not None else None
        partes.reverse()
        return " › ".join(partes)

    out: list[PartidaObra] = []
    for ide, node in by_ide.items():
        # HOJA = no es padre de ninguna otra fila.
        if ide in parent_ides:
            continue
        cod = node.get("cod")
        if not cod:
            continue
        out.append(
            PartidaObra(
                codigo=cod,
                descripcion=node.get("res"),
                descripcion_agregada=_ruta(node) or node.get("res"),
            )
        )
    out.sort(key=lambda p: p.codigo)
    return out


def hojas_de_filas(columnas: Sequence[str], filas: Sequence[Sequence[Any]]) -> list[PartidaObra]:
    """Partidas HOJA a partir de las filas de :data:`SQL_PARTIDAS_POR_OBRA`.

    Semántica de sv4 (``fetch_partidas_por_obra``), sin cambios: hoja = no
    es ``padide`` de ninguna otra fila; ``padide`` 0 o nulo = sin padre;
    filas sin ``ide`` o hojas sin ``cod`` fuera; ``descripcion_agregada``
    = ruta de capítulos (``res`` unidos por `` › ``, sin ciclos); orden por
    código.
    """
    by_ide, parent_ides = _indexar(columnas, filas)
    return _hojas(by_ide, parent_ides)


# ------------------------------------------------------------------ #
# Casar una lectura con la lista (H1: verifica, nunca elige)
# ------------------------------------------------------------------ #
def _indice_normalizado(lista: ListaPartidasObra) -> dict[str, set[str]]:
    """Forma normalizada → códigos DISTINTOS de la lista que la tienen."""
    indice: dict[str, set[str]] = {}
    for codigo in lista.codigos:
        clave = normalizar_partida(codigo)
        if clave is not None:
            indice.setdefault(clave, set()).add(codigo)
    return indice


def _casar_simple(
    lectura: str, exactos: set[str], indice: dict[str, set[str]]
) -> tuple[str, str | None]:
    """Casa UNA partida (sin ``/``): (motivo, código de la lista o None)."""
    if lectura in exactos:
        return MOTIVO_EXACTA, lectura
    candidatos = indice.get(normalizar_partida(lectura) or "")
    if not candidatos:
        return MOTIVO_FUERA_DE_LISTA, None
    if len(candidatos) > 1:
        return MOTIVO_AMBIGUA, None
    return MOTIVO_NORMALIZADA, next(iter(candidatos))


def casar_partida(lista: ListaPartidasObra, lectura: Any, alm: str | None) -> CasePartida:
    """Comprueba una lectura de partida contra la lista de su obra.

    Orden:

    1. Sin nada legible (``normalizar_partida`` da ``None``) ⇒ ``sin_partida``.
    2. Igual al literal ``alm`` (sin espacios exteriores, sin distinguir
       mayúsculas, como sv6) ⇒ ``alm``. ``alm`` vacío o ``None`` desactiva
       este paso.
    3. La lectura entera (sin espacios exteriores) es un código de la lista
       ⇒ ``exacta``.
    4. La lectura entera, normalizada, coincide con UNA hoja ⇒
       ``normalizada``; con dos o más hojas distintas ⇒ ``ambigua``.
    5. Con dos o más partes (``/``): cada parte se casa por separado (tal
       cual y, si no, normalizada). Si alguna no casa ⇒ ``fuera_de_lista``;
       si no, si alguna es ambigua ⇒ ``ambigua``; si todas casan ⇒
       ``compuesta``, con un código de la lista por parte.
    6. Cualquier otra cosa ⇒ ``fuera_de_lista``.

    Nunca por parecido, sufijo, prefijo ni distancia; una abreviatura
    (``P4/P5.01.09``) no se completa: ``P4`` no es hoja ⇒ ``fuera_de_lista``.
    """
    if lectura is None or normalizar_partida(lectura) is None:
        return CasePartida(MOTIVO_SIN_PARTIDA)
    cruda = str(lectura).strip()
    if alm and cruda.upper() == alm.strip().upper():
        return CasePartida(MOTIVO_ALM)

    exactos = set(lista.codigos)
    indice = _indice_normalizado(lista)

    motivo, codigo = _casar_simple(cruda, exactos, indice)
    if codigo is not None:
        return CasePartida(motivo, (codigo,))
    if motivo == MOTIVO_AMBIGUA:
        return CasePartida(MOTIVO_AMBIGUA)

    partes = partes_de_partida(cruda)
    if len(partes) < 2:
        return CasePartida(MOTIVO_FUERA_DE_LISTA)
    resultados = [_casar_simple(parte, exactos, indice) for parte in partes]
    motivos = {m for m, _ in resultados}
    if MOTIVO_FUERA_DE_LISTA in motivos:
        return CasePartida(MOTIVO_FUERA_DE_LISTA)
    if MOTIVO_AMBIGUA in motivos:
        return CasePartida(MOTIVO_AMBIGUA)
    return CasePartida(MOTIVO_COMPUESTA, tuple(c for _, c in resultados if c is not None))
