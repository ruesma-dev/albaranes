# domain/models/tipologia.py
"""Tipología del albarán (nivel documento).

Un albarán es de UNA sola tipología (no mezcla actividades). La tipología
enruta la extracción particular (fase 2) y la valoración (sv5):

  - ``generico``  : caso por defecto (línea-a-contrato).
  - ``hormigon``  : hormigón preparado; genera líneas sintéticas M1–M7.
  - ``residuos``  : gestión de residuos (RCD); trae LER + m³ + Tn por línea
                    y se valora por CONTENEDOR según contrato.

La tipología la propone la IA de fase 1, pero se CONSOLIDA de forma
determinista en ``tipologia_resolver`` (regla dura: si hay un código LER
en el documento → residuos). El enum es cerrado a propósito: la IA no
puede inventar tipos y, ante la duda, cae en ``generico``.
"""
from __future__ import annotations

import re
from enum import Enum


class Tipologia(str, Enum):
    GENERICO = "generico"
    HORMIGON = "hormigon"
    MORTERO = "mortero"
    RESIDUOS = "residuos"

    @classmethod
    def from_str(cls, value: str | None) -> "Tipologia":
        """Normaliza un string a Tipologia; desconocido/None → GENERICO."""
        if not value:
            return cls.GENERICO
        try:
            return cls(str(value).strip().lower())
        except ValueError:
            return cls.GENERICO


# Un código LER es de 6 dígitos, habitualmente escrito en pares
# ("17 05 04", "170504", "17.05.04", "17-05-04"). Este patrón captura las
# variantes con separadores opcionales de espacio/punto/guion entre pares.
_LER_REGEX = re.compile(r"\b(\d{2})([ .\-]?)(\d{2})[ .\-]?(\d{2})\b")

# ------------------------------------------------------------------- #
# (jul 2026) Validación contra el catálogo LER real (Decisión
# 2014/955/UE): capítulo → subcapítulos válidos. Un número de 6 dígitos
# NO es un LER si su par capítulo/subcapítulo no existe en el catálogo.
#
# Motivo (bug real): la regex sola casaba CUALQUIER número de 6 dígitos
# — el código de producto "192137" de un albarán de MORTERO de Prebetong
# disparó la regla dura "LER → residuos" y la fase 2 corrió con el
# prompt de residuos. 19 21 no existe (el capítulo 19 llega al
# subcapítulo 13), así que la validación lo descarta.
# ------------------------------------------------------------------- #
_CAPITULOS_LER: dict[int, frozenset[int]] = {
    1: frozenset({1, 3, 4, 5}),
    2: frozenset(range(1, 8)),
    3: frozenset({1, 2, 3}),
    4: frozenset({1, 2}),
    5: frozenset({1, 6, 7}),
    6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),
    7: frozenset(range(1, 8)),
    8: frozenset({1, 2, 3, 4, 5}),
    9: frozenset({1}),
    10: frozenset(range(1, 15)),
    11: frozenset({1, 2, 3, 5}),
    12: frozenset({1, 3}),
    13: frozenset({1, 2, 3, 4, 5, 7, 8}),
    14: frozenset({6}),
    15: frozenset({1, 2}),
    16: frozenset(range(1, 12)),
    17: frozenset({1, 2, 3, 4, 5, 6, 8, 9}),
    18: frozenset({1, 2}),
    19: frozenset(range(1, 14)),
    20: frozenset({1, 2, 3}),
}

# Palabras que dan contexto de residuos a un número LER (p.ej.
# "LER 170504", "residuo 170904", "cambio de contenedor 17 09 04").
_PALABRAS_CONTEXTO_LER = (
    "ler", "residu", "rcd", "escombr", "vertedero", "vertido",
    "gestor", "traslado", "contenedor",
)


def es_ler_valido(seis_digitos: str | None) -> bool:
    """True si los 6 dígitos existen como capítulo/subcapítulo LER."""
    s = re.sub(r"\D", "", str(seis_digitos or ""))
    if len(s) != 6:
        return False
    capitulo, subcapitulo = int(s[0:2]), int(s[2:4])
    return subcapitulo in _CAPITULOS_LER.get(capitulo, frozenset())


def normalizar_ler(texto: str | None) -> str | None:
    """Devuelve el LER en formato canónico de 6 dígitos, o None.

    (jul 2026) Solo devuelve candidatos VÁLIDOS según el catálogo; un
    número de 6 dígitos con capítulo/subcapítulo inexistente (código de
    producto, referencia...) devuelve None.
    """
    if not texto:
        return None
    for m in _LER_REGEX.finditer(str(texto)):
        solo_digitos = re.sub(r"\D", "", m.group(0))
        if len(solo_digitos) == 6 and es_ler_valido(solo_digitos):
            return solo_digitos
    return None


# Designaciones de hormigón estructural/no estructural según EHE:
# HA (armado), HM (masa), HL (limpieza), HNE (no estructural), seguidas
# de la resistencia (HA-25, HM20, HL-150, HNE-15...). Sirve para detectar
# la tipología 'hormigon' desde el código/concepto de la línea sin
# depender de que la IA rellene contexto_linea.
_HORMIGON_REGEX = re.compile(r"\bH[ALMN]E?\s?-?\s?\d{2,3}\b", re.IGNORECASE)


# Designaciones de MORTERO segun resistencia (M-5, M-7,5, M-10, M-12,5,
# M-15, M-20...). El prefijo es 'M-' + resistencia; se distingue del
# hormigon (H*) por la letra. Tambien vale la palabra "mortero".
#
# (jul 2026, blindado) Una designacion ENTERA (M-8, M-10, M-12...)
# coincide con las METRICAS de tornilleria ("TORNILLO M-10", "TUERCA
# M-8"): por si sola ya NO basta; exige ademas palabra de contexto de
# mortero en el texto. La designacion con DECIMAL (M-7,5 / M-12,5) es
# inequivocamente mortero y sigue bastando sola.
_MORTERO_REGEX_DECIMAL = re.compile(
    r"\bM-\s?\d{1,2}[.,]\d\b", re.IGNORECASE
)
_MORTERO_REGEX_ENTERO = re.compile(r"\bM-\s?\d{1,2}\b", re.IGNORECASE)
_PALABRAS_CONTEXTO_MORTERO = (
    "mortero", "seco", "estabilizad", "central", "cemento", "amasad",
)


def texto_contiene_mortero(texto: str | None) -> bool:
    """True si el texto contiene una designacion de mortero o la
    palabra 'mortero'. Ver nota de blindaje sobre metricas M-x."""
    if not texto:
        return False
    t = str(texto)
    t_lower = t.lower()
    if "mortero" in t_lower:
        return True
    if _MORTERO_REGEX_DECIMAL.search(t):
        return True
    if _MORTERO_REGEX_ENTERO.search(t):
        return any(p in t_lower for p in _PALABRAS_CONTEXTO_MORTERO)
    return False


def texto_contiene_hormigon(texto: str | None) -> bool:
    """True si el texto contiene una designación de hormigón (HA-25,
    HM20...) o la propia palabra ("HORMIGON BOMBEADO" sin designación
    también debe enrutar a la tipología hormigón — blindaje jul 2026)."""
    if not texto:
        return False
    t = str(texto)
    return bool(_HORMIGON_REGEX.search(t)) or "hormig" in t.lower()


def texto_contiene_ler(texto: str | None) -> bool:
    """True si el texto contiene un código LER CREÍBLE.

    (jul 2026, blindado) Tres niveles según la grafía, siempre
    validando capítulo/subcapítulo contra el catálogo:
      * "17 05 04" con ESPACIOS → basta por sí solo: es la grafía
        canónica LER y las fechas no se escriben con espacios.
      * "17.05.04" / "17-05-04" con punto/guion → FORMA DE FECHA
        (dd-mm-aa): solo cuenta si el texto trae además contexto de
        residuos ("LER", "residuo", "contenedor"...).
      * "170504" pegado → igual: solo con contexto; un 6-dígitos
        suelto en un campo de código suele ser referencia de producto
        (bug real: "192137" de Prebetong disparaba residuos).
    """
    if not texto:
        return False
    t = str(texto)
    t_lower = t.lower()
    hay_contexto = any(p in t_lower for p in _PALABRAS_CONTEXTO_LER)
    for m in _LER_REGEX.finditer(t):
        solo_digitos = re.sub(r"\D", "", m.group(0))
        if len(solo_digitos) != 6 or not es_ler_valido(solo_digitos):
            continue
        separador = m.group(2)
        con_espacios = separador == " "
        if con_espacios or hay_contexto:
            return True
    return False
