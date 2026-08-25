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

# ------------------------------------------------------------------- #
# (F-036 R14) El catálogo LER y su validador se MOVIERON a
# ``ruesma_comun.ler``: sv5 también los necesita (regla dura de
# tipología de valoración) y no puede importar el dominio de sv2. Aquí
# queda SOLO la reexportación, para no romper a quien ya importaba
# desde este módulo (``tipologia_resolver``, entre otros). Cero lógica
# duplicada: si algo del catálogo hay que tocar, se toca en comun.
# ------------------------------------------------------------------- #
from ruesma_comun.ler import (
    es_ler_valido,
    normalizar_ler,
    texto_contiene_ler,
)

__all__ = [
    "Tipologia",
    "es_ler_valido",
    "normalizar_ler",
    "texto_contiene_hormigon",
    "texto_contiene_ler",
    "texto_contiene_mortero",
]


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
