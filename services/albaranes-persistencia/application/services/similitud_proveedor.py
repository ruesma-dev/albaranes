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

#: R2 · formas jurídicas (lista cerrada): no identifican a nadie.
FORMAS_JURIDICAS: frozenset[str] = frozenset(
    "sa sl slu sau sll slne slp scoop coop sc scp scl sccl cb srl sad aie "
    "ute sociedad anonima limitada unipersonal laboral cooperativa".split()
)
#: R2 · palabras vacías.
PALABRAS_VACIAS: frozenset[str] = frozenset(
    "de del la las el los y e en para por con a al".split()
)
#: R2 · signos que separan palabras.
_SEPARADORES = str.maketrans({c: " " for c in ",.;:()[]{}-/\\\"'&+*_"})
#: R5 · longitudes de palabra.
_MINIMO_SUBCADENA = 3
_MINIMO_APROXIMADA = 5
_LONGITUD_EXACTA = 2


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
