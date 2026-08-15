# application/services/atributo_sustantivo_guard.py
"""Red determinista de ATRIBUTO SUSTANTIVO (F-003, R11–R12).

Un «ELEMENTO BASE 0,5 mm» no es un «ELEMENTO BASE 0,6 mm»: las
descripciones se parecen al 95 % y el producto es otro. El prompt de
IA3/IA4 lo prohíbe (R9/R10), pero un prompt no es una garantía. Esta red
corre DESPUÉS de IA4 y ANTES de las pasadas del builder y anula el match
cuando albarán y contrato traen magnitudes del MISMO tipo con valores
distintos.

Regla de negocio (§10.5): mejor una línea nueva SIN precio a revisión
que un precio equivocado con apariencia de bueno.

Límites conscientes (D5):

  - Solo detecta atributos NUMÉRICOS con unidad (0,5 mm, ø300, 6 m3).
    Los modelos y nombres no numéricos (ladrillos CETOSA, «BOLSA DE
    CUÑAS») los cubren los prompts: una red de similitud textual daría
    falsos positivos.
  - Anula SOLO si ambos textos hablan de la misma magnitud y se
    contradicen. Si el contrato detalla más que el albarán, el match
    aguanta.
  - No toca hormigón ni mortero (tienen su propia maquinaria posicional
    sobre la designación HA-25/B/20/XC2) ni las líneas sintéticas.
  - El mismo número escrito de otra forma NO dispara nada:
    0,5 = 0.5 = 0,50 y D-300 = D300 = DN300 = ø300.

Módulo puro salvo por la mutación explícita de los DTOs, mismo contrato
de uso que ``_sanear_matches_incremento_year``.
"""
from __future__ import annotations

import logging
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, Optional, Tuple

logger = logging.getLogger(__name__)

# Categoría física de cada unidad reconocida. Solo se comparan valores
# de la MISMA categoría: 6 m3 y 6 kg no se contradicen, hablan de cosas
# distintas.
_UNIDADES: dict[str, tuple[str, Decimal]] = {
    # longitud → todo a milímetros
    "mm": ("longitud", Decimal("1")),
    "cm": ("longitud", Decimal("10")),
    "m": ("longitud", Decimal("1000")),
    # superficie → m2
    "m2": ("superficie", Decimal("1")),
    # volumen → m3
    "m3": ("volumen", Decimal("1")),
    "l": ("volumen", Decimal("0.001")),
    # masa → kilogramos
    "kg": ("masa", Decimal("1")),
    "t": ("masa", Decimal("1000")),
    "tn": ("masa", Decimal("1000")),
}

# Número con coma o punto decimal seguido de una unidad conocida
# (pegada o separada). Ej.: "0,5 mm", "12mm", "6 m3".
_RE_NUMERO_UNIDAD = re.compile(
    r"(?<![\w.,])(\d+(?:[.,]\d+)?)\s*"
    r"(mm|cm|m2|m3|m|kg|tn|t|l)(?![\w])",
    re.IGNORECASE,
)

# Diámetros: ø12, D-300, D300, DN300. La unidad es implícita (mm) y lo
# que importa es que el NÚMERO coincida.
_RE_DIAMETRO = re.compile(
    r"(?:ø|\bdn|\bd)\s*[-_/]?\s*(\d+(?:[.,]\d+)?)\b",
    re.IGNORECASE,
)

_FAMILIAS_EXCLUIDAS = {"hormigon", "mortero"}

Token = Tuple[str, Decimal, str]


def _sin_acentos(texto: str) -> str:
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in descompuesto if unicodedata.category(c) != "Mn")


def _a_decimal(bruto: str) -> Optional[Decimal]:
    try:
        return Decimal(bruto.replace(",", ".")).normalize()
    except (InvalidOperation, ValueError):
        return None


def extraer_tokens_dimension(texto: Optional[str]) -> set[Token]:
    """Magnitudes de un texto, como ``(categoria, valor, unidad_base)``.

    El valor va NORMALIZADO a la unidad base de su categoría, así que
    «0,50 m» y «500 mm» producen el mismo token: la red no salta por
    cómo esté escrito el número, solo por cuánto vale.
    """
    if not texto:
        return set()

    plano = _sin_acentos(str(texto))
    tokens: set[Token] = set()

    for numero, unidad in _RE_NUMERO_UNIDAD.findall(plano):
        valor = _a_decimal(numero)
        if valor is None:
            continue
        categoria, factor = _UNIDADES[unidad.lower()]
        tokens.add((categoria, (valor * factor).normalize(), categoria))

    for numero in _RE_DIAMETRO.findall(plano):
        valor = _a_decimal(numero)
        if valor is None:
            continue
        tokens.add(("diametro", valor.normalize(), "diametro"))

    return tokens


def _categorias_en_conflicto(
    tokens_albaran: set[Token],
    tokens_contrato: set[Token],
) -> list[tuple[str, set[Decimal], set[Decimal]]]:
    """Categorías presentes en AMBOS textos con valores que no coinciden.

    Coinciden si comparten al menos un valor: «TUBO 300 mm» contra
    «TUBO 300 mm 6 kg» no es una contradicción, es un contrato que
    detalla más.
    """
    conflictos: list[tuple[str, set[Decimal], set[Decimal]]] = []
    por_categoria_a: Dict[str, set[Decimal]] = {}
    por_categoria_c: Dict[str, set[Decimal]] = {}
    for categoria, valor, _ in tokens_albaran:
        por_categoria_a.setdefault(categoria, set()).add(valor)
    for categoria, valor, _ in tokens_contrato:
        por_categoria_c.setdefault(categoria, set()).add(valor)

    for categoria, valores_a in por_categoria_a.items():
        valores_c = por_categoria_c.get(categoria)
        if not valores_c:
            continue
        if valores_a & valores_c:
            continue
        conflictos.append((categoria, valores_a, valores_c))
    return conflictos


def _fmt(valores: Iterable[Decimal]) -> str:
    return "/".join(str(v) for v in sorted(valores))


def sanear_matches_atributo_sustantivo(
    *,
    lineas: Iterable[tuple[int, Any]],
    albaran_by_id: Dict[int, Any],
    contrato_by_id: Dict[int, Any],
) -> Dict[int, list[str]]:
    """Anula los matches con atributo sustantivo distinto.

    ``lineas`` son pares ``(idx, dto)`` de líneas ``from_albaran`` (el
    mismo formato que usan las pasadas del builder). Muta los DTOs y
    devuelve los motivos por ``merge_line_id``, para que el builder los
    cuelgue del record — la línea acaba en «nueva sin precio a
    revisión» por el camino que ya existe (``match_method='no_match'``).
    """
    motivos: Dict[int, list[str]] = {}

    for _, dto in lineas:
        if getattr(dto, "line_kind", "from_albaran") != "from_albaran":
            continue
        merge_line_id = getattr(dto, "merge_line_id", None)
        if merge_line_id is None:
            continue
        if getattr(dto, "matched_contrato_line_id", None) is None:
            continue

        albaran_line = albaran_by_id.get(merge_line_id)
        contrato_line = contrato_by_id.get(dto.matched_contrato_line_id)
        if albaran_line is None or contrato_line is None:
            continue

        contexto = getattr(albaran_line, "contexto_linea", None)
        familia = getattr(contexto, "tipo_familia", None) if contexto else None
        if familia in _FAMILIAS_EXCLUIDAS:
            continue

        conflictos = _categorias_en_conflicto(
            extraer_tokens_dimension(getattr(albaran_line, "descripcion", None)),
            extraer_tokens_dimension(
                getattr(contrato_line, "descripcion", None)
            ),
        )
        if not conflictos:
            continue

        categoria, valores_a, valores_c = conflictos[0]
        motivo = (
            f"atributo_sustantivo_mismatch:"
            f"{_fmt(valores_a)}!={_fmt(valores_c)}"
        )
        logger.warning(
            "[builder][red-atributo] línea merge_id=%s (%r) venía casada "
            "con contrato_line_id=%s (%r): match ANULADO por %s distinta "
            "(%s vs %s). Queda como línea nueva sin precio, a revisión.",
            merge_line_id,
            getattr(albaran_line, "descripcion", None),
            dto.matched_contrato_line_id,
            getattr(contrato_line, "descripcion", None),
            categoria,
            _fmt(valores_a),
            _fmt(valores_c),
        )

        dto.matched_contrato_line_id = None
        # (D6) Se anulan los DOS precios: dejar vivo el inferido del PDF
        # reintroduciría el precio equivocado por la puerta de atrás.
        dto.precio_unitario_contrato_db = None
        dto.precio_unitario_pdf_inferido = None
        dto.match_method = "no_match"
        dto.razon_corta = (
            (getattr(dto, "razon_corta", "") or "")
            + f" | red determinista: {categoria} distinta "
            f"({_fmt(valores_a)} vs {_fmt(valores_c)}); no se casa"
        )[:500]

        motivos.setdefault(merge_line_id, []).append(motivo)

    return motivos
