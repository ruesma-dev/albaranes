# ruesma_comun/ler.py
"""Catálogo LER (Decisión 2014/955/UE) y su validador, compartidos.

Un código LER identifica un residuo y es la señal DURA de que un albarán
es de gestión de residuos. La regla vive en más de un servicio:

  - sv2 la usa en ``tipologia_resolver`` para enrutar la fase 2.
  - sv5 la usa en ``_derivar_tipologia_valoracion`` como defensa en
    profundidad, por si el contexto llega sin ``tipo_familia`` (F-036 R13).

Hasta F-036 esto vivía solo en el dominio de sv2
(``services/albaranes-api/domain/models/tipologia.py``). sv5 no puede
importar el dominio de otro servicio, así que la alternativa era copiar
el catálogo: dos tablas de 20 capítulos que divergen a la primera
corrección. Por eso se movió aquí, y en sv2 queda solo la reexportación
(**R14**). El coste aceptado por el humano: reconstruir las imágenes de
sv2, sv3, sv5 y sv6, porque ``ruesma_comun`` va horneado en cada una.

AQUÍ NO HAY LÓGICA DE DOMINIO de ningún servicio: el catálogo LER es una
norma europea, no una decisión de este sistema. Módulo puro: sin red,
sin BBDD, sin configuración.
"""
from __future__ import annotations

import re

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
