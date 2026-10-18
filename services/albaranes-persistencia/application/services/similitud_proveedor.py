# application/services/similitud_proveedor.py
"""Criterio ÚNICO de nombre de proveedor (F-073 · R1–R9).

Lo usan los cuatro sitios de sv3 que comparan el nombre LEÍDO con una razón
social: el atajo por nombre del paso 1 y el fallback global del paso 2 del
resolver de cabecera, la propuesta de la red por CIF (F-052) y el candidato
claro (F-062). La obra (``_resolve_obra``) NO lo usa: sigue con
``_match_score`` (R16).

Origen: incidencia 0694 (2026-10-15). «FEYMACO, S.A.» y «TEYMACO, S.A.»
sacaban 0,50 frente a HIERROS RODRIGO, S.A. y frente a FEYMACO (solo casaba
«s.a.») y en el empate ganaba el primero. Aquí la puntuación separa
palabras, las formas jurídicas y las palabras vacías no cuentan, una letra
mal leída en una palabra de 5+ caracteres casa, y elegir por nombre exige
llegar al umbral Y sacar un margen al segundo CIF.

Puro: sin E/S ni dependencias nuevas.
"""
from __future__ import annotations

import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from ruesma_comun.proveedores import normalizar_cif

#: R2 · formas jurídicas (lista cerrada): no identifican a nadie.
FORMAS_JURIDICAS: frozenset[str] = frozenset(
    "sa sl slu sau sll slne slp scoop coop sc scp scl sccl cb srl sad aie "
    "ute sociedad anonima limitada unipersonal laboral cooperativa".split()
)
#: R2 · palabras vacías.
PALABRAS_VACIAS: frozenset[str] = frozenset(
    "de del la las el los y e en para por con a al".split()
)
#: R9 · margen por defecto sobre el segundo CIF (inclusivo).
MARGEN_NOMBRE_POR_DEFECTO: float = 0.25

#: R2 · signos que separan palabras.
_SEPARADORES = str.maketrans({c: " " for c in ",.;:()[]{}-/\\\"'&+*_"})
#: R5 · longitudes de palabra.
_MINIMO_SUBCADENA = 3
_MINIMO_APROXIMADA = 5
_LONGITUD_EXACTA = 2
#: R9 · tolerancia de coma flotante en el margen: las similitudes son
#: fracciones de palabras y 2/3 - 5/12 da 0,2499… en vez de 0,25.
_TOLERANCIA = 1e-9


def palabras_razon_social(texto: str | None) -> tuple[str, ...]:
    """Palabras significativas de un nombre (R2), en su orden.

    Minúsculas y sin acentos; la puntuación de ``_SEPARADORES`` separa; fuera
    las palabras de un carácter, las formas jurídicas y las palabras vacías.
    """
    minusculas = (texto or "").lower().translate(_SEPARADORES)
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFD", minusculas)
        if not unicodedata.combining(c)
    )
    return tuple(
        p for p in sin_acentos.split()
        if len(p) > 1 and p not in FORMAS_JURIDICAS and p not in PALABRAS_VACIAS
    )


def distancia_edicion(a: str, b: str) -> int:
    """Distancia de Levenshtein (inserciones, borrados y sustituciones).

    La única de sv3 (R8): desempata por CIF en el candidato claro (F-062 ·
    R4) y aproxima palabras en ``similitud_razon_social`` (R5).
    """
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        actual = [i]
        for j, cb in enumerate(b, start=1):
            actual.append(min(
                anterior[j] + 1,
                actual[j - 1] + 1,
                anterior[j - 1] + (ca != cb),
            ))
        anterior = actual
    return anterior[-1]


def _casa(palabra: str, texto_otro: str, palabras_otro: tuple[str, ...]) -> bool:
    """R5 · ¿la palabra casa en el otro nombre?"""
    if len(palabra) >= _MINIMO_SUBCADENA and palabra in texto_otro:
        return True
    if len(palabra) >= _MINIMO_APROXIMADA:
        return any(
            len(otra) >= _MINIMO_APROXIMADA
            and abs(len(otra) - len(palabra)) <= 1  # condición necesaria
            and distancia_edicion(palabra, otra) <= 1
            for otra in palabras_otro
        )
    return len(palabra) == _LONGITUD_EXACTA and palabra in palabras_otro


def _direccion(de: tuple[str, ...], a: tuple[str, ...], texto_a: str) -> float:
    """R5 · fracción de palabras de ``de`` que casan en ``a``."""
    return sum(1 for p in de if _casa(p, texto_a, a)) / len(de)


def similitud_razon_social(leido: str | None, candidato: str | None) -> float:
    """Similitud del nombre leído con una razón social, en [0, 1] (R3–R7).

    Sin palabras en alguno ⇒ 0 (R3: «S.A.» sola no casa). Texto de palabras
    de uno contenido en el del otro ⇒ 1 (R4). Si no, el máximo de las dos
    direcciones (R5): simétrica (R7).
    """
    a = palabras_razon_social(leido)
    b = palabras_razon_social(candidato)
    if not a or not b:
        return 0.0
    texto_a, texto_b = " ".join(a), " ".join(b)
    if texto_a in texto_b or texto_b in texto_a:
        return 1.0
    return max(_direccion(a, b, texto_b), _direccion(b, a, texto_a))


# ------------------------------------------------------------------ #
# Elegir por nombre (R9–R12)
# ------------------------------------------------------------------ #
@dataclass(frozen=True)
class CandidatoNombre:
    """Un CIF con su mejor similitud frente al nombre leído."""

    cif: str
    nombre: str | None
    similitud: float


@dataclass(frozen=True)
class EleccionPorNombre:
    """Decisión de ``elegir_por_nombre``.

    ``elegido``: el CIF elegido (R9) o ``None``. ``empatados``: solo cuando
    el mejor llega al umbral y no saca el margen, los que quedan a MENOS del
    margen del mejor, en orden (-similitud, cif) (R11). ``segunda``: la
    similitud del segundo CIF, 0 sin segundo (R13). ``mejor``: el primero en
    ese orden, elegido o no, para el log (R13).
    """

    elegido: CandidatoNombre | None
    empatados: tuple[CandidatoNombre, ...]
    segunda: float
    mejor: CandidatoNombre | None


def _orden(candidato: CandidatoNombre) -> tuple[float, str, str]:
    return (-candidato.similitud, candidato.cif, candidato.nombre or "")


def _decidir(
    por_cif: Iterable[CandidatoNombre], *, umbral: float, margen: float,
) -> EleccionPorNombre:
    """R9 y R10 sobre candidatos ya agrupados (un CIF, una entrada)."""
    ordenados = sorted(por_cif, key=_orden)
    if not ordenados:
        return EleccionPorNombre(elegido=None, empatados=(), segunda=0.0, mejor=None)
    mejor = ordenados[0]
    segunda = ordenados[1].similitud if len(ordenados) > 1 else 0.0
    if mejor.similitud < umbral:
        return EleccionPorNombre(elegido=None, empatados=(), segunda=segunda, mejor=mejor)
    if mejor.similitud - segunda >= margen - _TOLERANCIA:
        return EleccionPorNombre(elegido=mejor, empatados=(), segunda=segunda, mejor=mejor)
    empatados = tuple(
        c for c in ordenados if mejor.similitud - c.similitud < margen - _TOLERANCIA
    )
    return EleccionPorNombre(elegido=None, empatados=empatados, segunda=segunda, mejor=mejor)


def elegir_por_nombre(
    leido: str | None,
    candidatos: Iterable[tuple[str | None, str | None]],
    *,
    umbral: float,
    margen: float,
) -> EleccionPorNombre:
    """Elige un CIF solo por la similitud del nombre, nunca en un empate.

    ``candidatos``: pares ``(cif, razón social)``. Se agrupan por
    ``normalizar_cif(cif)`` o, si no normaliza, por el CIF recortado; un CIF
    vacío se ignora. Cada CIF cuenta con su mejor similitud, y el CIF que se
    devuelve es el de esa fila, recortado (el que se escribe en el merge).
    Elige el mejor si llega a ``umbral`` y supera al segundo CIF en
    ``margen`` o más (los dos inclusivos; sin segundo, cuenta 0). La
    decisión no depende del orden de llegada (R12).
    """
    por_clave: dict[str, CandidatoNombre] = {}
    for cif, nombre in candidatos:
        recortado = (cif or "").strip()
        clave = normalizar_cif(recortado) or recortado
        if not clave:
            continue
        candidato = CandidatoNombre(
            cif=recortado, nombre=nombre,
            similitud=similitud_razon_social(leido, nombre),
        )
        actual = por_clave.get(clave)
        if actual is None or _orden(candidato) < _orden(actual):
            por_clave[clave] = candidato
    return _decidir(por_clave.values(), umbral=umbral, margen=margen)
