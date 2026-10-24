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
- :func:`leer_partidas_obra`: UNA consulta, ``NO_TOLERA`` y
  :data:`~ruesma_comun.sigrid.lectura.MAX_FILAS_POR_PETICION`; la obra se
  canoniza con ``canonizar_codigo_obra`` (F-070); vacía ⇒ no consulta.
- :func:`normalizar_partida`, :func:`partes_de_partida`,
  :func:`casar_partida` y sus motivos.
- (F-076) :func:`resolver_partida_obra`: qué partida debe usar quien valora
  (el código de la lista o la lectura intacta) con la guarda de no hoja.
- (F-076) :class:`CachePartidasObra`: la lista por obra en memoria del
  proceso (TTL, LRU, fallo recordado); nunca lanza.
- (F-098) Cada hoja lleva su ``ide``, su **capítulo** (la raíz de su cadena)
  y su **código completo** (:func:`codigo_completo`: ``CD.99.01.64`` para el
  cod ``99.01.64`` de CD), y la lista sus capítulos
  (:attr:`ListaPartidasObra.capitulos`). Lo que se guarda y se manda sigue
  siendo el cod; el completo es lo que ve el humano y una forma más de casar
  una lectura con su hoja (motivo ``completa``): :func:`misma_partida`,
  :func:`mostrar_partida` y :meth:`CachePartidasObra.consultar`.
"""
from __future__ import annotations

import logging
import re
import threading
import time
import unicodedata
from collections import OrderedDict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from ruesma_comun.obras import canonizar_codigo_obra
from ruesma_comun.sigrid.lectura import MAX_FILAS_POR_PETICION, PoliticaTruncado

logger = logging.getLogger(__name__)

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
#: (F-098 R6) La lectura casa con UNA hoja solo por su código completo
#: (``CD.99.01.64`` ⇒ la hoja ``99.01.64`` de CD).
MOTIVO_COMPLETA = "completa"

MOTIVOS_PARTIDA = frozenset(
    {
        MOTIVO_EXACTA,
        MOTIVO_NORMALIZADA,
        MOTIVO_COMPLETA,
        MOTIVO_COMPUESTA,
        MOTIVO_ALM,
        MOTIVO_SIN_PARTIDA,
        MOTIVO_FUERA_DE_LISTA,
        MOTIVO_AMBIGUA,
    }
)
#: Motivos en que la lectura casa con la lista (``validada = true``).
MOTIVOS_CASADOS = frozenset({MOTIVO_EXACTA, MOTIVO_NORMALIZADA, MOTIVO_COMPLETA, MOTIVO_COMPUESTA})
#: Motivos en que la lectura NO casa (``validada = false``: a revisión).
MOTIVOS_NO_CASADOS = frozenset({MOTIVO_FUERA_DE_LISTA, MOTIVO_AMBIGUA})

# Separa todo lo que no es letra ni dígito (Unicode). El «_» es carácter de
# palabra para ``\w``, así que se añade a mano. La «/» se trata antes.
_RE_SEPARADOR = re.compile(r"[\W_]+")


@dataclass(frozen=True)
class PartidaObra:
    """Partida HOJA de una obra. Mismos campos que ``PartidaOption`` de sv4.

    (F-098 R1) Además: ``ide`` (``obrparpar.ide``), ``capitulo`` (el cod de la
    raíz de su cadena, o ``None``), ``capitulo_descripcion`` y
    ``codigo_completo`` (:func:`codigo_completo`; si no se da, el cod). Van al
    final y con defecto, así que quien la construye con los tres campos de
    siempre no se rompe, y NO entran en la igualdad ni en el hash: dos hojas
    siguen siendo iguales si lo son su cod y sus descripciones, como en F-076
    (R5).
    """

    codigo: str
    descripcion: str | None
    descripcion_agregada: str | None
    ide: Any = field(default=None, compare=False)
    capitulo: str | None = field(default=None, compare=False)
    capitulo_descripcion: str | None = field(default=None, compare=False)
    codigo_completo: str | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        if self.codigo_completo is None:
            object.__setattr__(self, "codigo_completo", self.codigo)


@dataclass(frozen=True)
class CapituloObra:
    """(F-098 R4) Un capítulo con hojas: su cod (``None`` = «Sin capítulo»), su
    descripción y cuántas hojas cuelgan de él."""

    codigo: str | None
    descripcion: str | None
    n_hojas: int


@dataclass(frozen=True)
class ListaPartidasObra:
    """Partidas de una obra: las hojas y los códigos que NO son hoja.

    (F-098) ``no_hojas_completos``: el código completo de cada no hoja que lo
    tiene distinto de su cod (``CD.99.01`` del subcapítulo ``99.01`` de CD),
    para la guarda de no hoja de :func:`resolver_partida_obra` (R8).
    """

    obra: str
    hojas: tuple[PartidaObra, ...]
    no_hojas: tuple[str, ...]
    no_hojas_completos: tuple[str, ...] = ()

    @property
    def codigos(self) -> tuple[str, ...]:
        """Códigos de las hojas, en el orden de la lista."""
        return tuple(h.codigo for h in self.hojas)

    @property
    def capitulos(self) -> tuple[CapituloObra, ...]:
        """(F-098 R4) Capítulos con al menos una hoja, por código; ``None`` al final."""
        cuenta: dict[str | None, int] = {}
        descripcion: dict[str | None, str | None] = {}
        for h in self.hojas:
            cuenta[h.capitulo] = cuenta.get(h.capitulo, 0) + 1
            descripcion.setdefault(h.capitulo, h.capitulo_descripcion)
        orden = sorted(cuenta, key=lambda c: (c is None, c or ""))
        return tuple(CapituloObra(c, descripcion[c], cuenta[c]) for c in orden)

    def cod_repetido(self, cod: str) -> bool:
        """(F-098 R12) ``True`` si dos o más hojas tienen ese cod (tal cual)."""
        return sum(1 for h in self.hojas if h.codigo == cod) >= 2

    @classmethod
    def desde_filas(
        cls, obra: str, columnas: Sequence[str], filas: Sequence[Sequence[Any]]
    ) -> ListaPartidasObra:
        """Construye la lista desde la respuesta de :data:`SQL_PARTIDAS_POR_OBRA`."""
        by_ide, parent_ides = _indexar(columnas, filas)
        no_hojas = sorted(
            {nodo["cod"] for ide, nodo in by_ide.items() if ide in parent_ides and nodo["cod"]}
        )
        completos: set[str] = set()
        for ide, nodo in by_ide.items():
            if ide in parent_ides and nodo["cod"]:
                completo = codigo_completo(by_ide[_capitulo_de(by_ide, ide)]["cod"], nodo["cod"])
                if completo != nodo["cod"]:
                    completos.add(completo)
        return cls(
            obra=obra,
            hojas=tuple(_hojas(by_ide, parent_ides)),
            no_hojas=tuple(no_hojas),
            no_hojas_completos=tuple(sorted(completos)),
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


# ------------------------------------------------------------------ #
# F-098 · capítulo y código completo
# ------------------------------------------------------------------ #
def _comparable(texto: str) -> str:
    """Forma de COMPARAR de R3: NFKC, mayúsculas y sin espacios exteriores."""
    return unicodedata.normalize("NFKC", texto).upper().strip()


def _hay_limite(antes: str, despues: str | None) -> bool:
    """(R3 b) ¿Hay límite entre el último carácter del capítulo (``antes``) y el
    siguiente del cod (``despues``; ``None`` o vacío = fin del cod)?

    Lo hay en el fin del cod, si uno de los dos no es alfanumérico o si uno es
    letra y el otro dígito (``CD`` | ``2.01``).
    """
    if not despues:
        return True
    if not antes.isalnum() or not despues.isalnum():
        return True
    return antes.isalpha() != despues.isalpha()


def _raiz_alfabetica(capitulo: str) -> str:
    """(R3 c, P9) Las letras iniciales del capítulo, tras comparar: ``CI.F2`` ⇒
    ``CI``, ``CD1`` ⇒ ``CD``, ``ANT.`` ⇒ ``ANT``, ``98`` ⇒ vacía."""
    texto = _comparable(capitulo)
    fin = 0
    while fin < len(texto) and texto[fin].isalpha():
        fin += 1
    return texto[:fin]


def codigo_completo(capitulo: str | None, cod: str) -> str:
    """(F-098 R3) El código de una hoja tal como lo ve el humano.

    Comparando con NFKC, mayúsculas y sin espacios exteriores, en este orden:

    a. Sin capítulo (``None`` o vacío) ⇒ el cod.
    b. El cod ya empieza por el capítulo seguido de límite (:func:`_hay_limite`)
       ⇒ el cod tal cual (``CI.4.18`` en CI, ``CD2.01`` en CD).
    c. (P9) El cod empieza por la raíz alfabética no vacía del capítulo seguida
       de fin o de algo que no es letra ⇒ el cod tal cual (``CI.01.01`` en
       ``CI.F2``, ``CD2`` en ``CD1``).
    d. Si no, capítulo + cod, con un ``.`` en medio salvo que el capítulo ya
       termine en un carácter no alfanumérico (``CD.99.01.64``, ``ANT.98.01``).

    Se compone con el cod tal cual: lo que se enseña no se normaliza.
    """
    cap = "" if capitulo is None else _comparable(capitulo)
    if not cap:
        return cod
    codigo = _comparable(cod)
    if codigo.startswith(cap) and _hay_limite(cap[-1], codigo[len(cap):len(cap) + 1]):
        return cod
    raiz = _raiz_alfabetica(cap)
    if raiz and codigo.startswith(raiz) and not codigo[len(raiz):len(raiz) + 1].isalpha():
        return cod
    separador = "." if cap[-1].isalnum() else ""
    return f"{capitulo}{separador}{cod}"


def _capitulo_de(by_ide: dict[Any, dict[str, Any]], ide: Any) -> Any:
    """(F-098 R2) ``ide`` de la raíz de la cadena de ``ide``.

    Sube por ``padide`` hasta un nodo sin padre (0 o nulo, ya ``None`` en
    :func:`_indexar`) o cuyo padre no está entre las filas; una raíz es su
    propio capítulo. Si la subida repite un nodo (ciclo), para en el último no
    repetido. Sin bajar de nivel aunque la obra tenga una sola raíz (P6).
    """
    visto = {ide}
    actual = ide
    while True:
        padre = by_ide[actual]["padide"]
        if padre not in by_ide or padre in visto:
            return actual
        visto.add(padre)
        actual = padre


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
        raiz = by_ide[_capitulo_de(by_ide, ide)]
        capitulo = raiz["cod"]
        out.append(
            PartidaObra(
                codigo=cod,
                descripcion=node.get("res"),
                descripcion_agregada=_ruta(node) or node.get("res"),
                ide=ide,
                capitulo=capitulo,
                capitulo_descripcion=raiz["res"] if capitulo else None,
                codigo_completo=codigo_completo(capitulo, cod),
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


def leer_partidas_obra(leer: LectorSql, obra: Any) -> ListaPartidasObra | None:
    """Lista de partidas de ``obra``: UNA consulta a sigrid-api (F-076 R3).

    La obra se lleva al código de la consulta con ``canonizar_codigo_obra``
    (F-070: ``686`` ⇒ ``0686``, ``var`` ⇒ ``VAR``; lo que no encaja, recortado
    tal cual, como las demás consultas por obra de sv4). Si queda vacía, NO se
    consulta y se devuelve ``None`` (no hay lista). La lectura va con
    ``NO_TOLERA`` y ``max_rows`` = :data:`MAX_FILAS_POR_PETICION`: una lista
    truncada calcularía mal las hojas sin error, así que ``truncated=true``
    acaba en :class:`~ruesma_comun.sigrid.lectura.SigridRespuestaTruncada` (la
    lanza el lector) y nunca en una lista parcial. Cualquier error del lector
    se propaga: degradar es cosa de quien llama.

    (F-049 canonizaba con su ``obra_a_consultar`` y un índice de obras, que no
    están en ``dev``; al retomarla, se queda su versión.)
    """
    canonica = canonizar_codigo_obra(None if obra is None else str(obra))
    if canonica is None:
        return None
    columnas, filas = leer(
        SQL_PARTIDAS_POR_OBRA,
        [canonica],
        f"partidas_obra_{canonica}",
        PoliticaTruncado.NO_TOLERA,
        MAX_FILAS_POR_PETICION,
    )
    return ListaPartidasObra.desde_filas(canonica, columnas, filas)


# ------------------------------------------------------------------ #
# Casar una lectura con la lista (H1: verifica, nunca elige)
# ------------------------------------------------------------------ #
#: Por dónde casa una entrada del índice: el cod de la hoja o su código completo.
_POR_COD = "cod"
_POR_COMPLETO = "completo"


def _indice_normalizado(lista: ListaPartidasObra) -> dict[str, set[tuple[str, str]]]:
    """Forma normalizada → ``(cod, por)`` de las hojas que la tienen.

    (F-098 R6) Cada hoja entra por la clave de su cod (``por = "cod"``) y, si su
    código completo es otro, también por la clave del completo (``"completo"``),
    en TODA la lista: sin restringir a ningún capítulo (P6).
    """
    indice: dict[str, set[tuple[str, str]]] = {}
    for hoja in lista.hojas:
        formas = [(hoja.codigo, _POR_COD)]
        if hoja.codigo_completo != hoja.codigo:
            formas.append((hoja.codigo_completo, _POR_COMPLETO))
        for forma, por in formas:
            clave = normalizar_partida(forma)
            if clave is not None:
                indice.setdefault(clave, set()).add((hoja.codigo, por))
    return indice


def _casar_simple(
    lectura: str, exactos: set[str], indice: dict[str, set[tuple[str, str]]]
) -> tuple[str, str | None]:
    """Casa UNA partida (sin ``/``): (motivo, código de la lista o None).

    La exacta literal primero (R7). Luego las candidatas de su clave: con UN
    cod distinto, ``normalizada`` si casa por su cod y ``completa`` si solo por
    su código completo; con dos o más, ``ambigua`` (R6).
    """
    if lectura in exactos:
        return MOTIVO_EXACTA, lectura
    entradas = indice.get(normalizar_partida(lectura) or "", set())
    candidatos = {cod for cod, _ in entradas}
    if not candidatos:
        return MOTIVO_FUERA_DE_LISTA, None
    if len(candidatos) > 1:
        return MOTIVO_AMBIGUA, None
    (codigo,) = candidatos
    if (codigo, _POR_COD) in entradas:
        return MOTIVO_NORMALIZADA, codigo
    return MOTIVO_COMPLETA, codigo


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
       ``normalizada`` (por su cod) o ``completa`` (F-098: solo por su código
       completo, ``CD.99.01.64`` ⇒ ``99.01.64``); con dos o más hojas
       distintas ⇒ ``ambigua``. Se busca en toda la lista.
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


# ------------------------------------------------------------------ #
# F-076 · resolver la partida de una línea contra su obra
# ------------------------------------------------------------------ #
#: Motivos de :class:`ResolucionPartida` (F-076 R5).
RESOLUCION_EXACTA = "exacta"
RESOLUCION_NORMALIZADA = "normalizada"
RESOLUCION_FUERA_DE_LISTA = "fuera_de_lista"
RESOLUCION_AMBIGUA = "ambigua"
RESOLUCION_NO_APLICA = "no_aplica"

MotivoResolucion = Literal["exacta", "normalizada", "fuera_de_lista", "ambigua", "no_aplica"]


@dataclass(frozen=True)
class ResolucionPartida:
    """Qué partida usar para una lectura (F-076 R5).

    ``codigo`` es el código TAL COMO FIGURA EN LA LISTA con ``exacta`` y
    ``normalizada``; en cualquier otro motivo, la lectura sin cambios.
    ``leida`` es la lectura tal cual llegó.
    """

    codigo: str | None
    motivo: MotivoResolucion
    leida: str | None

    @property
    def cambia(self) -> bool:
        """``True`` si quien valora debe usar otro texto que el leído."""
        return self.codigo != self.leida


def _choca_con_no_hoja(lista: ListaPartidasObra, lectura: Any) -> bool:
    """La clave de la lectura es la de algún código NO hoja de la obra: su cod
    o (F-098 R8) su código completo (``CD.99.01`` del subcapítulo ``99.01``)."""
    clave = normalizar_partida(lectura)
    return clave is not None and any(
        normalizar_partida(c) == clave for c in (*lista.no_hojas, *lista.no_hojas_completos)
    )


def resolver_partida_obra(lista: ListaPartidasObra, lectura: Any, alm: str | None) -> ResolucionPartida:
    """La partida que debe usar quien valora una línea (F-076 R5).

    :func:`casar_partida` y, encima:

    - ``alm`` / ``sin_partida`` ⇒ ``no_aplica`` (almacén o nada que verificar).
    - Lectura no exacta cuya clave es la de un código NO hoja de la obra (su
      cod o, F-098 R8, su código completo) ⇒ ``fuera_de_lista``: nunca se
      normaliza hacia otra fila del árbol (``03.02`` capítulo ≠ ``3.02`` hoja).
    - (F-098 R8) ``completa`` ⇒ ``normalizada`` con el cod de la lista: lo que
      se guarda es el cod, nunca la lectura con un prefijo recortado.
    - ``compuesta`` ⇒ ``fuera_de_lista``: Sigrid admite una partida por línea
      y el reparto es de F-049.
    - ``fuera_de_lista`` / ``ambigua`` ⇒ la lectura sin cambios.
    """
    leida = None if lectura is None else str(lectura)
    caso = casar_partida(lista, lectura, alm)
    if caso.motivo in (MOTIVO_ALM, MOTIVO_SIN_PARTIDA):
        return ResolucionPartida(leida, RESOLUCION_NO_APLICA, leida)
    if caso.motivo == MOTIVO_EXACTA:
        return ResolucionPartida(caso.codigos_lista[0], RESOLUCION_EXACTA, leida)
    if _choca_con_no_hoja(lista, lectura):
        return ResolucionPartida(leida, RESOLUCION_FUERA_DE_LISTA, leida)
    if caso.motivo in (MOTIVO_NORMALIZADA, MOTIVO_COMPLETA):
        return ResolucionPartida(caso.codigos_lista[0], RESOLUCION_NORMALIZADA, leida)
    if caso.motivo == MOTIVO_AMBIGUA:
        return ResolucionPartida(leida, RESOLUCION_AMBIGUA, leida)
    return ResolucionPartida(leida, RESOLUCION_FUERA_DE_LISTA, leida)


@dataclass
class _Entrada:
    lista: ListaPartidasObra | None  # la última buena (puede estar caducada)
    leida_en: float | None  # cuándo se leyó la buena
    fallo_hasta: float | None  # hasta cuándo no se reconsulta tras un fallo


class CachePartidasObra:
    """Lista de partidas por obra en memoria del proceso (F-076 R6).

    - Clave: la obra canonizada (``canonizar_codigo_obra``); vacía ⇒ ``None``
      sin consultar.
    - N peticiones de la misma obra dentro de ``ttl_s`` ⇒ UNA consulta.
    - Más de ``max_obras`` ⇒ sale la menos usada (LRU).
    - Si la consulta falla o trunca: la lista caducada si la hay o, si no,
      ``None``; el fallo se recuerda ``ttl_fallo_s`` sin reconsultar (para no
      martillear sigrid-api) y se registra un WARNING con la obra y la causa.
    - Una lista con 0 hojas cuenta como «sin lista» (``None``), pero se
      cachea como cualquier otra.
    - Nunca lanza: degradar es la norma (quien llama valora como siempre).

    Implementa ``PartidasObraPort`` de sv6. Segura entre hilos: el estado va
    bajo un candado; la consulta, fuera de él.
    """

    def __init__(
        self,
        lector: LectorSql,
        *,
        ttl_s: float,
        max_obras: int,
        ttl_fallo_s: float,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        if ttl_s < 0 or ttl_fallo_s < 0:
            raise ValueError("CachePartidasObra: ttl_s y ttl_fallo_s no pueden ser negativos")
        if max_obras < 1:
            raise ValueError("CachePartidasObra: max_obras debe ser >= 1")
        self._lector = lector
        self._ttl_s = ttl_s
        self._max_obras = max_obras
        self._ttl_fallo_s = ttl_fallo_s
        self._reloj = reloj
        self._entradas: OrderedDict[str, _Entrada] = OrderedDict()
        self._candado = threading.Lock()

    def lista(self, obra: str | None) -> ListaPartidasObra | None:
        """Lista de ``obra`` (hojas > 0) o ``None`` si no hay; nunca lanza."""
        try:
            return self._lista(obra)
        except Exception as exc:  # noqa: BLE001 - R6: nunca lanza
            logger.warning("[partidas-obra] obra=%s fallo inesperado: %r", obra, exc)
            return None

    def _lista(self, obra: str | None) -> ListaPartidasObra | None:
        clave = canonizar_codigo_obra(obra)
        if clave is None:
            return None
        ahora = self._reloj()
        with self._candado:
            entrada = self._entradas.get(clave)
            if entrada is not None:
                self._entradas.move_to_end(clave)
                vigente = entrada.leida_en is not None and ahora - entrada.leida_en < self._ttl_s
                en_fallo = entrada.fallo_hasta is not None and ahora < entrada.fallo_hasta
                if vigente or en_fallo:
                    return _con_hojas(entrada.lista)
        try:
            # ``clave`` ya es canónica y no vacía: la lectura nunca da ``None``.
            lista = leer_partidas_obra(self._lector, clave) or ListaPartidasObra(clave, (), ())
        except Exception as exc:  # noqa: BLE001 - fallo o truncado: se degrada
            with self._candado:
                previa = self._entradas.get(clave)
                vieja = previa.lista if previa is not None else None
                leida_en = previa.leida_en if previa is not None else None
                self._guardar(clave, _Entrada(vieja, leida_en, ahora + self._ttl_fallo_s))
            logger.warning(
                "[partidas-obra] obra=%s sin lista de sigrid-api (%s); se usa %s y no se reconsulta en %ss",
                clave,
                exc,
                "la lista caducada" if vieja is not None else "ninguna",
                self._ttl_fallo_s,
            )
            return _con_hojas(vieja)
        with self._candado:
            self._guardar(clave, _Entrada(lista, ahora, None))
        logger.info(
            "[partidas-obra] obra=%s hojas=%s segundos=%.2f",
            clave,
            len(lista.hojas),
            self._reloj() - ahora,
        )
        return _con_hojas(lista)

    def _guardar(self, clave: str, entrada: _Entrada) -> None:
        self._entradas[clave] = entrada
        self._entradas.move_to_end(clave)
        while len(self._entradas) > self._max_obras:
            self._entradas.popitem(last=False)


def _con_hojas(lista: ListaPartidasObra | None) -> ListaPartidasObra | None:
    """0 hojas cuenta como «sin lista» (F-076 R6, como el remate de F-049)."""
    if lista is None or not lista.hojas:
        return None
    return lista
