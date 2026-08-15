# application/services/valuation_builder.py
from __future__ import annotations

import logging
import re
from typing import Dict

from application.services.importe_calculator import ImporteCalculator
import dataclasses

from application.services.residuos_container_calc import (
    calcular_contenedores_residuos,
)
from application.services.partida_matcher import (
    PartidaMatcher,
    PartidaMatchResult,
)
from application.services.price_reconciler import PriceReconciler
from application.services.unit_category_guard import UnitCategoryGuard
from application.services.unit_converter import UnitConverter
from domain.models.valuation_envelope import (
    AlbaranLineContextDto,
    ContratoLineContextDto,
    LineValuationDto,
    ValuationEnvelope,
)
from domain.models.valuation_records import (
    DerivedContratoLineRecord,
    LineValuationRecord,
    MatchMethod,
    ValuationHeaderRecord,
)

from application.services.designacion_hormigon import (
    CONSISTENCIAS_CON_INCREMENTO,
    NOMBRE_CONSISTENCIA,
    cemento_es_sr,
    normalizar_texto,
    parsear_designacion_hormigon,
)

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------- #
# (jul 2026) Red determinista M1 — INCREMENTOS POR AÑO en hormigón.
# Caso real (HORMICEM 37816/37819): contrato CTSU24 + albarán 2025 →
# el prompt de IA3 marca como OBLIGATORIO emitir "INCREMENTO POR AÑO
# 2025", pero la IA no lo emitió en ninguna de las dos páginas (el
# propio prompt avisa: "es el que más veces se escapa"). Además, el
# campo context.meta.fecha_albaran que el prompt referencia NUNCA se
# enviaba (fix en sv5 de la misma tanda). Los incrementos por año son
# 100%% computables sin IA: año del contrato = prefijo CTSU{AA};
# año del albarán = fecha. El builder genera las M1 que falten
# (con dedupe si IA3 sí las trajo), buscando tarifa en las líneas de
# contrato; sin tarifa → precio null y revisión (forma C del prompt).
# ------------------------------------------------------------------- #
_RE_ANIO_CODIGO_CONTRATO = re.compile(r"^[A-Z]{2,6}(\d{2})[/\-]")
_RE_ANIO_4 = re.compile(r"\b(20\d{2})\b")


def _anio_de_codigo_contrato(codigo: str | None) -> int | None:
    """CTSU24/0452 → 2024. Solo confía en ventanas razonables (2020-49)."""
    m = _RE_ANIO_CODIGO_CONTRATO.match((codigo or "").strip().upper())
    if not m:
        return None
    anio = 2000 + int(m.group(1))
    return anio if 2020 <= anio <= 2049 else None


def _anio_de_fecha(fecha: str | None) -> int | None:
    """'2025-09-29' → 2025."""
    s = (fecha or "").strip()
    if len(s) >= 4 and s[:4].isdigit():
        anio = int(s[:4])
        return anio if 2020 <= anio <= 2049 else None
    return None


def _anio_de_texto(texto: str | None) -> str | None:
    """Primer año 20XX que aparezca en el texto, como string, o None."""
    m = _RE_ANIO_4.search(texto or "")
    return m.group(1) if m else None


def _sanear_matches_incremento_year(*, sinteticas, contrato_by_id) -> int:
    """Guard determinista de AÑO (jul 2026, caso real Horpresol).

    IA4 (conciliación) casó "INCREMENTO POR AÑO 2025" con la tarifa
    "INCREMENTO PRECIO ... HA-25/B/20/XC2" del año 2024 (el contrato
    no tarifa 2025): 38,50 € indebidos y dos filas idénticas en sv4.
    Regla: una sintética de incremento POR AÑO solo puede quedarse
    casada con una línea de contrato que contenga ESE MISMO año. Si
    la línea casada contiene años y ninguno coincide, se anula el
    match (no_match, precio null → revisión, Forma C). Una tarifa
    sin año explícito (genérica) se respeta. Corre DESPUÉS de IA3 e
    IA4 (ambas mutan el envelope antes del build), así que cubre a
    las dos. Devuelve cuántos matches anuló.
    """
    anulados = 0
    for _, dto in sinteticas:
        if (dto.rol_linea or "").strip().lower() != "incremento_year":
            continue
        if dto.matched_contrato_line_id is None:
            continue
        anio = _anio_de_texto(
            f"{dto.descripcion_linea or ''} {dto.modifier_reason or ''}"
        )
        if anio is None:
            continue
        cl = contrato_by_id.get(dto.matched_contrato_line_id)
        anios_cl = _RE_ANIO_4.findall(
            (cl.descripcion or "") if cl is not None else ""
        )
        if not anios_cl or anio in anios_cl:
            continue
        logger.warning(
            "[builder][guard-año] sintética %r (año %s) venía casada "
            "con contrato_line_id=%s (%r, años %s): match ANULADO "
            "(tarifa de otro año). Queda a revisión (Forma C).",
            dto.descripcion_linea, anio,
            dto.matched_contrato_line_id,
            cl.descripcion if cl is not None else None, anios_cl,
        )
        dto.matched_contrato_line_id = None
        dto.precio_unitario_contrato_db = None
        dto.match_method = "no_match"
        dto.razon_corta = (
            (dto.razon_corta or "")
            + f" | guard determinista: tarifa de año distinto "
            f"({'/'.join(sorted(set(anios_cl)))}) anulada para el "
            f"año {anio}"
        )[:500]
        anulados += 1

    # ------------------------------------------------------------- #
    # Capa (b) — la tarifa Sigrid NO lleva el año en el texto (caso
    # real Horpresol: "INCREMENTO PRECIO HORMIGÓN HA-25/B/20/XC2";
    # el "año 2024" solo está en la sub-descripción del anexo, que
    # no viaja). Regla: DOS años distintos no pueden compartir la
    # MISMA tarifa (misma descripción normalizada, cualquier
    # partida): la tarifa cubre UN ejercicio. Se conserva el año más
    # antiguo (el primero que esa tarifa tarificó) y el resto se
    # anula a revisión. Conservador: una tarifa genuinamente
    # "anual genérica" quedaría a revisión, que es preferible a
    # cobrar dos ejercicios con el precio de uno.
    # ------------------------------------------------------------- #
    por_tarifa: dict = {}
    for _, dto in sinteticas:
        if (dto.rol_linea or "").strip().lower() != "incremento_year":
            continue
        if dto.matched_contrato_line_id is None:
            continue
        anio = _anio_de_texto(
            f"{dto.descripcion_linea or ''} {dto.modifier_reason or ''}"
        )
        if anio is None:
            continue
        cl = contrato_by_id.get(dto.matched_contrato_line_id)
        desc_norm = normalizar_texto(
            cl.descripcion if cl is not None else ""
        )
        clave = (dto.parent_merge_line_id, desc_norm)
        por_tarifa.setdefault(clave, []).append((int(anio), dto))
    for (parent, desc_norm), grupo in por_tarifa.items():
        anios_grupo = {a for a, _ in grupo}
        if len(anios_grupo) <= 1:
            continue
        conservado = min(anios_grupo)
        for anio, dto in grupo:
            if anio == conservado:
                continue
            logger.warning(
                "[builder][guard-año] la tarifa %r (sin año en el "
                "texto) ya cubre el año %s: match del año %s ANULADO "
                "(base merge=%s). Queda a revisión.",
                desc_norm, conservado, anio, parent,
            )
            dto.matched_contrato_line_id = None
            dto.precio_unitario_contrato_db = None
            dto.match_method = "no_match"
            dto.razon_corta = (
                (dto.razon_corta or "")
                + f" | guard determinista: la misma tarifa ya cubre "
                f"el año {conservado}; no puede cobrar también el "
                f"{anio}"
            )[:500]
            anulados += 1
    return anulados


def _anios_m1_ya_emitidos(sinteticas, parent_merge_line_id: int) -> set[int]:
    """Años de incremento que IA3 YA emitió para esa base (dedupe)."""
    anios: set[int] = set()
    for _, dto in sinteticas:
        if dto.parent_merge_line_id != parent_merge_line_id:
            continue
        es_year = (
            (dto.rol_linea or "") == "incremento_year"
            or (dto.modifier_source or "") in ("year_contract", "year_albaran")
            or "AÑO" in (dto.descripcion_linea or "").upper()
        )
        if not es_year:
            continue
        for texto in (dto.descripcion_linea, dto.modifier_reason):
            for m in _RE_ANIO_4.finditer(texto or ""):
                anios.add(int(m.group(1)))
    return anios


def _tarifa_incremento_anio(contrato_lines, anio: int):
    """Línea de contrato que tarifa el incremento de ese año, o None."""
    patron = re.compile(
        rf"(INCREMENT|REVISI|ACTUALIZ)\w*[^0-9]{{0,60}}{anio}"
        rf"|PRECIO\s*{anio}",
        re.IGNORECASE,
    )
    for cl in contrato_lines:
        if patron.search(cl.descripcion or ""):
            return cl
    return None


# ------------------------------------------------------------------- #
# (jul 2026) Red determinista de CÓDIGO — feedback JO (albarán
# Horpresol HA-25/B/12/XC2/F/P): los incrementos que se leen del
# propio CÓDIGO del hormigón (consistencia F/L/S, FRATASADO /F/,
# FIBRAS /P/) y del cemento (/SR) son 100%% computables sin IA. El
# builder genera las sintéticas que IA3 no emitió, con dedupe y
# búsqueda de tarifa por grafías; sin tarifa → precio null +
# revisión (Forma C), mismo patrón que la red M1 de años.
# ------------------------------------------------------------------- #
def _mod_ya_emitido(
    sinteticas,
    parent_merge_line_id: int,
    *,
    roles: tuple[str, ...] = (),
    claves: tuple[str, ...] = (),
) -> bool:
    """True si IA3 YA emitió una sintética equivalente para esa base.

    Equivalente = mismo parent y (rol_linea en ``roles`` O alguna de
    las ``claves`` aparece en descripción/motivo normalizados).
    """
    for _, dto in sinteticas:
        if dto.parent_merge_line_id != parent_merge_line_id:
            continue
        if roles and (dto.rol_linea or "") in roles:
            return True
        texto = normalizar_texto(
            f"{dto.descripcion_linea or ''} {dto.modifier_reason or ''}"
        )
        if claves and any(clave in texto for clave in claves):
            return True
    return False


def _tarifa_por_claves(contrato_lines, *, todas: tuple[str, ...]):
    """Primera línea de contrato cuya descripción normalizada contiene
    TODAS las claves, o None."""
    for cl in contrato_lines:
        desc = normalizar_texto(cl.descripcion)
        if desc and all(clave in desc for clave in todas):
            return cl
    return None


def _tarifa_cemento_sr(contrato_lines):
    """Línea de contrato que tarifa el cemento SR, o None. Exige
    CEMENTO + (SULFORRES* o la palabra completa SR) para no casar
    siglas incrustadas."""
    for cl in contrato_lines:
        desc = normalizar_texto(cl.descripcion)
        if "CEMENTO" not in desc:
            continue
        if "SULFORRES" in desc or re.search(r"\bSR\b", desc):
            return cl
    return None


_RE_MOVIMIENTO_RESIDUOS = re.compile(
    r"\b(porte|transporte|movimiento|desplazamiento|retirada|entrega|"
    r"cambio|colocacion|colocación|recogida)",
    re.IGNORECASE,
)


def _es_movimiento_residuos(*, ctx, albaran_line, contrato_line) -> bool:
    """(jul 2026) True si la línea es un MOVIMIENTO de residuos
    (porte / retirada / entrega / cambio de contenedor...).

    Señales, cualquiera vale (la línea ya debe ser tipo_familia
    'residuos'): rol_linea transporte/desplazamiento del contexto, o
    palabra de movimiento en la descripción del albarán o de la línea
    de contrato casada.
    """
    if ctx is None or getattr(ctx, "tipo_familia", None) != "residuos":
        return False
    if getattr(ctx, "rol_linea", None) in ("transporte", "desplazamiento"):
        return True
    textos = " ".join(
        t for t in (
            getattr(albaran_line, "descripcion", None) if albaran_line else None,
            getattr(contrato_line, "descripcion", None) if contrato_line else None,
        ) if t
    )
    return bool(_RE_MOVIMIENTO_RESIDUOS.search(textos))


class ValuationBuilder:
    """Transforma el envelope del servicio 5 en los records a persistir.

    Se procesa en TRES pasadas (sub-tanda 2D):

      Pasada 1: líneas base.
        - line_kind='from_albaran', rol_linea in (None, 'base').
        - Matching normal (partida_matcher.match).

      Pasada 2: líneas complementarias declaradas.
        - line_kind='from_albaran', rol_linea != 'base' (la línea está
          declarada en el albarán, no la ha generado el valorador).
        - Heredan partida de su base vía ref_linea_base_merge_id
          (sub-tanda 2C, resolve_partida_for_complementaria).

      Pasada 3: líneas sintéticas (sub-tanda 2D).
        - line_kind='synthetic_modifier'.
        - Heredan partida de su base vía parent_merge_line_id
          (resolve_partida_for_synthetic).

    Este orden garantiza que cuando una línea complementaria o sintética
    consulta la partida (o el descuento) de su base, la base ya está
    resuelta.

    -------------------------------------------------------------------
    Tanda descuento — abr 2026
    -------------------------------------------------------------------
    El builder ahora propaga ``descuento_albaran`` al ImporteCalculator
    para que la fórmula del importe valorado sea:

        importe = cantidad × precio_contrato × (1 - descuento/100)

    Reglas de propagación:
      - Líneas 'from_albaran' (base o complementaria): el descuento
        viene del propio AlbaranLineContextDto.descuento_albaran.
      - Líneas 'synthetic_modifier' (M1-M7): heredan el descuento del
        record YA RESUELTO de la línea base padre (parent_record).
        Decisión de negocio Construcciones Ruesma: las sintéticas
        heredan el descuento del padre.

    El descuento aplicado se persiste en
    ``LineValuationRecord.descuento_albaran_aplicado`` para auditoría.
    -------------------------------------------------------------------

    -------------------------------------------------------------------
    Tanda precedencia albarán — jul 2026
    -------------------------------------------------------------------
    Los valores LEÍDOS del albarán (importe / unitario / descuento)
    MANDAN sobre el precio del contrato: el casado aporta partida,
    código y concepto, pero no pisa valores. Ver PriceReconciler e
    ImporteCalculator. Las sintéticas M1–M7 siguen valorándose a
    contrato (no existen en el albarán).
    -------------------------------------------------------------------
    """

    def __init__(
        self,
        *,
        unit_category_guard: UnitCategoryGuard,
        price_reconciler: PriceReconciler,
        partida_matcher: PartidaMatcher,
        unit_converter: UnitConverter,
        importe_calculator: ImporteCalculator,
        # (F-003) Interruptores de las redes nuevas. A False, el
        # comportamiento es el previo a la feature.
        guard_aritmetico_enabled: bool = True,
        red_atributo_sustantivo_enabled: bool = True,
        # Tolerancia del guard aritmético. Es la MISMA que usa el
        # ImporteCalculator (IMPORTE_TOLERANCE_PCT): no se inventa un
        # umbral nuevo para comparar los mismos importes.
        importe_tolerance_pct: float = 5.0,
    ) -> None:
        self._guard = unit_category_guard
        self._reconciler = price_reconciler
        self._partida_matcher = partida_matcher
        self._converter = unit_converter
        self._importe_calc = importe_calculator
        self._guard_aritmetico_enabled = bool(guard_aritmetico_enabled)
        self._red_atributo_sustantivo_enabled = bool(
            red_atributo_sustantivo_enabled
        )
        self._importe_tolerance_pct = float(importe_tolerance_pct)

    def build(
        self,
        *,
        envelope: ValuationEnvelope,
        existing_document_already_valued: bool,
    ) -> tuple[ValuationHeaderRecord, list[LineValuationRecord]]:
        # Codigo de contrato de esta valoracion (para la "linea nueva" de
        # fallback cuando la IA no casa nada con el contrato).
        self._codigo_contrato_actual = envelope.meta.codigo_contrato
        albaran_by_id: Dict[int, AlbaranLineContextDto] = {
            line.merge_line_id: line for line in envelope.context.lineas_albaran
        }
        contrato_by_id: Dict[int, ContratoLineContextDto] = {
            line.contrato_line_id: line
            for line in envelope.context.lineas_contrato
        }
        contrato_lines = envelope.context.lineas_contrato

        merge_id_by_line_index: Dict[int, int] = {
            line.line_index: line.merge_line_id
            for line in envelope.context.lineas_albaran
        }

        # Clasificación en TRES grupos.
        base_lines: list[tuple[int, LineValuationDto]] = []
        complementarias: list[tuple[int, LineValuationDto]] = []
        sinteticas: list[tuple[int, LineValuationDto]] = []

        for idx, line in enumerate(envelope.data.lineas):
            if line.line_kind == "synthetic_modifier":
                sinteticas.append((idx, line))
                continue
            ctx = self._get_albaran_ctx(line, albaran_by_id)
            if ctx is None or ctx.rol_linea in (None, "base"):
                base_lines.append((idx, line))
            else:
                complementarias.append((idx, line))

        # (jul 2026) Red determinista M1: inyecta los incrementos por
        # año que IA3 debía emitir y no emitió, como si vinieran en el
        # sobre (reutilizan TODA la maquinaria de sintéticas: herencia
        # de partida/cantidad/descuento, reconcile, importe).
        inyectadas = self._sinteticas_m1_faltantes(
            envelope=envelope,
            base_lines=base_lines,
            sinteticas=sinteticas,
        )
        # (jul 2026) Red determinista de CÓDIGO: consistencia F/L/S,
        # fratasado /F/, fibras /P/ y cemento /SR leídos del propio
        # código del hormigón. Mismo mecanismo que la M1.
        inyectadas += self._sinteticas_codigo_faltantes(
            envelope=envelope,
            base_lines=base_lines,
            sinteticas=sinteticas,
        )
        # (jul 2026) Guard determinista de AÑO: anula matches de
        # incrementos por año casados (por IA3 o IA4) con tarifas de
        # OTRO año. Ver _sanear_matches_incremento_year.
        _sanear_matches_incremento_year(
            sinteticas=sinteticas,
            contrato_by_id=contrato_by_id,
        )
        next_idx = len(envelope.data.lineas)
        for dto in inyectadas:
            sinteticas.append((next_idx, dto))
            next_idx += 1

        # Records indexados por la posición ORIGINAL en envelope.data.lineas
        # para poder recomponer al final en el orden recibido.
        records_by_index: Dict[int, LineValuationRecord] = {}
        # Records base (from_albaran) indexados por merge_line_id para que
        # complementarias y sintéticas puedan heredar su partida.
        records_by_merge_id: Dict[int, LineValuationRecord] = {}

        # -----------------------------------------------------------------
        # Pasada 1: líneas base.
        # -----------------------------------------------------------------
        for idx, line in base_lines:
            record = self._build_line(
                line=line,
                albaran_by_id=albaran_by_id,
                contrato_by_id=contrato_by_id,
                contrato_lines=contrato_lines,
                line_already_valued=existing_document_already_valued,
                partida_override=None,
                ref_linea_base_merge_id=None,
            )
            records_by_index[idx] = record
            if record.merge_line_id is not None:
                records_by_merge_id[record.merge_line_id] = record

        # -----------------------------------------------------------------
        # Pasada 2: líneas complementarias declaradas (sub-tanda 2C).
        # -----------------------------------------------------------------
        for idx, line in complementarias:
            ctx = self._get_albaran_ctx(line, albaran_by_id)
            ref_base_merge_id: int | None = None
            partida_base: str | None = None

            if ctx is not None and ctx.ref_linea_base is not None:
                ref_base_merge_id = merge_id_by_line_index.get(ctx.ref_linea_base)
                if ref_base_merge_id is not None:
                    base_record = records_by_merge_id.get(ref_base_merge_id)
                    if base_record is not None:
                        partida_base = base_record.codigo_partida_final
                    else:
                        logger.warning(
                            "[builder] complementaria merge_id=%s apunta a "
                            "ref_linea_base=%s (merge_id=%s) no resuelta; "
                            "partida null.",
                            line.merge_line_id, ctx.ref_linea_base,
                            ref_base_merge_id,
                        )
                else:
                    logger.warning(
                        "[builder] complementaria merge_id=%s con "
                        "ref_linea_base=%s no encontrada en lineas_albaran.",
                        line.merge_line_id, ctx.ref_linea_base,
                    )

            record = self._build_line(
                line=line,
                albaran_by_id=albaran_by_id,
                contrato_by_id=contrato_by_id,
                contrato_lines=contrato_lines,
                line_already_valued=existing_document_already_valued,
                partida_override=partida_base,
                ref_linea_base_merge_id=ref_base_merge_id,
            )
            records_by_index[idx] = record
            if record.merge_line_id is not None:
                records_by_merge_id[record.merge_line_id] = record

        # -----------------------------------------------------------------
        # Pasada 3: líneas sintéticas (sub-tanda 2D).
        # -----------------------------------------------------------------
        for idx, line in sinteticas:
            parent_id = line.parent_merge_line_id
            partida_heredada: str | None = None
            parent_record: LineValuationRecord | None = None
            if parent_id is None:
                logger.warning(
                    "[builder] sintética sin parent_merge_line_id; "
                    "descripcion=%r.",
                    line.descripcion_linea,
                )
            else:
                parent_record = records_by_merge_id.get(parent_id)
                if parent_record is None:
                    logger.warning(
                        "[builder] sintética parent_merge_line_id=%s "
                        "no resuelta.",
                        parent_id,
                    )
                else:
                    partida_heredada = parent_record.codigo_partida_final

            record = self._build_synthetic_line(
                line=line,
                parent_merge_line_id=parent_id,
                partida_heredada=partida_heredada,
                parent_record=parent_record,
                albaran_by_id=albaran_by_id,
                contrato_by_id=contrato_by_id,
            )
            records_by_index[idx] = record

        # Recomponemos en el orden original (las M1 inyectadas por la
        # red determinista llevan índices altos: quedan al final).
        records = [
            records_by_index[i] for i in sorted(records_by_index)
        ]

        header = self._build_header(
            envelope=envelope,
            records=records,
        )
        return header, records

    # ------------------------------------------------------------------ #
    # Auxiliares
    # ------------------------------------------------------------------ #

    def _sinteticas_m1_faltantes(
        self,
        *,
        envelope,
        base_lines,
        sinteticas,
    ) -> list[LineValuationDto]:
        """Genera los incrementos por año (M1) que IA3 no emitió.

        Determinista puro: año contrato del prefijo del código
        (CTSU{AA}), año albarán de meta.fecha_albaran (viaja desde sv5
        en esta misma tanda). Una línea por año en
        (año_contrato+1 .. año_albarán], por cada base de hormigón,
        con dedupe si IA3 ya la trajo. Tarifa: primera línea de
        contrato tipo "INCREMENTO/REVISIÓN/PRECIO {año}"; sin tarifa →
        precio null + revisión (forma C del prompt de IA3).
        """
        anio_contrato = _anio_de_codigo_contrato(
            envelope.meta.codigo_contrato
        )
        anio_albaran = _anio_de_fecha(
            getattr(envelope.meta, "fecha_albaran", None)
        )
        if anio_contrato is None or anio_albaran is None:
            return []
        if anio_albaran <= anio_contrato:
            return []

        albaran_by_id = {
            l.merge_line_id: l for l in envelope.context.lineas_albaran
        }
        contrato_lines = envelope.context.lineas_contrato
        nuevas: list[LineValuationDto] = []

        for _, base in base_lines:
            if base.merge_line_id is None:
                continue
            alb = albaran_by_id.get(base.merge_line_id)
            ctx = alb.contexto_linea if alb is not None else None
            if ctx is None or getattr(ctx, "tipo_familia", None) != "hormigon":
                continue
            ya = _anios_m1_ya_emitidos(sinteticas, base.merge_line_id)
            for anio in range(anio_contrato + 1, anio_albaran + 1):
                if anio in ya:
                    continue
                tarifa = _tarifa_incremento_anio(contrato_lines, anio)
                fuente = (
                    "year_albaran" if anio == anio_albaran
                    else "year_contract"
                )
                logger.info(
                    "[builder][m1-determinista] base merge=%s año=%s "
                    "tarifa=%s (IA3 no lo emitió).",
                    base.merge_line_id, anio,
                    "sí" if tarifa is not None else "no",
                )
                nuevas.append(LineValuationDto(
                    merge_line_id=None,
                    line_kind="synthetic_modifier",
                    parent_merge_line_id=base.merge_line_id,
                    modifier_source=fuente,
                    modifier_reason=(
                        f"Red determinista M1: incremento año {anio} "
                        f"(contrato {anio_contrato}, albarán "
                        f"{anio_albaran}); IA3 no lo emitió."
                    ),
                    descripcion_linea=(
                        f"INCREMENTO POR AÑO {anio} EN HORMIGÓN"
                    ),
                    rol_linea="incremento_year",
                    match_method=(
                        "semantic" if tarifa is not None else "no_match"
                    ),
                    matched_contrato_line_id=(
                        tarifa.contrato_line_id if tarifa is not None
                        else None
                    ),
                    match_confidence_pct=(
                        90.0 if tarifa is not None else 0.0
                    ),
                    precio_unitario_contrato_db=(
                        tarifa.precio_unitario if tarifa is not None
                        else None
                    ),
                    razon_corta=(
                        f"Incremento por año {anio} generado por red "
                        "determinista"
                        + (
                            "" if tarifa is not None
                            else f"; el contrato no tarifa el año {anio}"
                        )
                    ),
                ))
        return nuevas

    def _sinteticas_codigo_faltantes(
        self,
        *,
        envelope,
        base_lines,
        sinteticas,
    ) -> list[LineValuationDto]:
        """Red determinista de CÓDIGO (jul 2026, feedback JO).

        Por cada base de hormigón parsea la designación posicional
        (designacion_hormigon) desde descripcion_extendida +
        descripción del albarán y genera las sintéticas que IA3 no
        emitió: consistencia especial (F/L/S), FRATASADO (extra /F/
        tras la exposición), FIBRAS DE POLIPROPILENO (extra /P/) y
        CEMENTO SULFORRESISTENTE (/SR en el cemento). Dedupe contra
        las de IA3; tarifa por grafías; sin tarifa → Forma C.
        """
        albaran_by_id = {
            l.merge_line_id: l for l in envelope.context.lineas_albaran
        }
        contrato_lines = envelope.context.lineas_contrato
        nuevas: list[LineValuationDto] = []

        for _, base in base_lines:
            if base.merge_line_id is None:
                continue
            alb = albaran_by_id.get(base.merge_line_id)
            ctx = alb.contexto_linea if alb is not None else None
            if ctx is None or getattr(ctx, "tipo_familia", None) != "hormigon":
                continue
            texto = " ".join(
                parte for parte in (
                    getattr(ctx, "descripcion_extendida", None) or "",
                    (alb.descripcion or "") if alb is not None else "",
                ) if parte
            ).strip()
            if not texto:
                continue
            desig = parsear_designacion_hormigon(texto)

            # a) Consistencia especial (2ª posición ∈ {F, L, S}).
            if (
                desig is not None
                and desig.consistencia in CONSISTENCIAS_CON_INCREMENTO
                and not _mod_ya_emitido(
                    sinteticas, base.merge_line_id,
                    roles=("incremento_consistencia",),
                    claves=("CONSISTENCIA",),
                )
            ):
                nombre = NOMBRE_CONSISTENCIA[desig.consistencia]
                tarifa = (
                    _tarifa_por_claves(
                        contrato_lines, todas=("CONSISTENCIA", nombre),
                    )
                    or _tarifa_por_claves(contrato_lines, todas=(nombre,))
                )
                nuevas.append(self._dto_red_codigo(
                    base=base,
                    rol="incremento_consistencia",
                    descripcion=f"INCREMENTO POR CONSISTENCIA {nombre}",
                    motivo=(
                        f"consistencia {desig.consistencia} "
                        f"({nombre.lower()}) en {desig.texto}"
                    ),
                    etiqueta=f"consistencia {nombre.lower()}",
                    tarifa=tarifa,
                ))

            # b) FRATASADO (extra /F/ tras la exposición).
            if (
                desig is not None
                and desig.fratasado
                and not _mod_ya_emitido(
                    sinteticas, base.merge_line_id,
                    roles=("incremento_fratasado",),
                    claves=("FRATASAD",),
                )
            ):
                tarifa = _tarifa_por_claves(
                    contrato_lines, todas=("FRATASAD",),
                )
                nuevas.append(self._dto_red_codigo(
                    base=base,
                    rol="incremento_fratasado",
                    descripcion="INCREMENTO POR HORMIGÓN FRATASADO",
                    motivo=(
                        f"extra /F/ (fratasado) tras la exposición "
                        f"en {desig.texto}"
                    ),
                    etiqueta="fratasado",
                    tarifa=tarifa,
                ))

            # c) FIBRAS DE POLIPROPILENO (extra /P/). Dedupe SOLO por
            #    clave FIBRA: el rol incremento_aditivo también lo usan
            #    las sintéticas 'SIN ADITIVO' y no deben bloquear.
            if (
                desig is not None
                and desig.fibras_polipropileno
                and not _mod_ya_emitido(
                    sinteticas, base.merge_line_id,
                    claves=("FIBRA",),
                )
            ):
                tarifa = _tarifa_por_claves(
                    contrato_lines, todas=("FIBRA",),
                )
                nuevas.append(self._dto_red_codigo(
                    base=base,
                    rol="incremento_aditivo",
                    descripcion="INCREMENTO POR FIBRA DE POLIPROPILENO",
                    motivo=(
                        f"extra /P/ (fibras polipropileno) "
                        f"en {desig.texto}"
                    ),
                    etiqueta="fibras polipropileno",
                    tarifa=tarifa,
                ))

            # d) CEMENTO SULFORRESISTENTE (/SR real en el albarán).
            if cemento_es_sr(texto) and not _mod_ya_emitido(
                sinteticas, base.merge_line_id,
                roles=("incremento_cemento",),
                claves=("SULFORRES", "CEMENTO"),
            ):
                tarifa = _tarifa_cemento_sr(contrato_lines)
                nuevas.append(self._dto_red_codigo(
                    base=base,
                    rol="incremento_cemento",
                    descripcion=(
                        "INCREMENTO POR CEMENTO SULFORRESISTENTE (SR)"
                    ),
                    motivo="cemento /SR declarado en el albarán",
                    etiqueta="cemento SR",
                    tarifa=tarifa,
                ))
        return nuevas

    @staticmethod
    def _dto_red_codigo(
        *,
        base,
        rol: str,
        descripcion: str,
        motivo: str,
        etiqueta: str,
        tarifa,
    ) -> LineValuationDto:
        """DTO sintético de la red de código (espejo del de la M1)."""
        logger.info(
            "[builder][red-codigo] base merge=%s %s tarifa=%s "
            "(IA3 no lo emitió).",
            base.merge_line_id, etiqueta,
            "sí" if tarifa is not None else "no",
        )
        return LineValuationDto(
            merge_line_id=None,
            line_kind="synthetic_modifier",
            parent_merge_line_id=base.merge_line_id,
            modifier_source="codigo_producto",
            modifier_reason=(
                f"Red determinista de código: {motivo}; "
                "IA3 no lo emitió."
            ),
            descripcion_linea=descripcion,
            rol_linea=rol,
            match_method=(
                "semantic" if tarifa is not None else "no_match"
            ),
            matched_contrato_line_id=(
                tarifa.contrato_line_id if tarifa is not None else None
            ),
            match_confidence_pct=(
                90.0 if tarifa is not None else 0.0
            ),
            precio_unitario_contrato_db=(
                tarifa.precio_unitario if tarifa is not None else None
            ),
            razon_corta=(
                f"Incremento por {etiqueta} generado por red "
                "determinista de código"
                + (
                    "" if tarifa is not None
                    else "; el contrato no lo tarifa"
                )
            ),
        )

    @staticmethod
    def _get_albaran_ctx(
        line: LineValuationDto,
        albaran_by_id: Dict[int, AlbaranLineContextDto],
    ):
        """Devuelve el ContextoLinea de la línea, o None.

        Solo tiene sentido para líneas from_albaran (con merge_line_id).
        Las sintéticas no tienen contexto propio — heredan el de la base.
        """
        if line.merge_line_id is None:
            return None
        albaran_line = albaran_by_id.get(line.merge_line_id)
        if albaran_line is None:
            return None
        return albaran_line.contexto_linea

    def _build_line(
        self,
        *,
        line: LineValuationDto,
        albaran_by_id: Dict[int, AlbaranLineContextDto],
        contrato_by_id: Dict[int, ContratoLineContextDto],
        contrato_lines: list[ContratoLineContextDto],
        line_already_valued: bool,
        partida_override: str | None,
        ref_linea_base_merge_id: int | None,
    ) -> LineValuationRecord:
        """Construye el record de una línea from_albaran (base o complementaria)."""
        albaran_line = albaran_by_id.get(line.merge_line_id)  # type: ignore[arg-type]
        contrato_line = (
            contrato_by_id.get(line.matched_contrato_line_id)
            if line.matched_contrato_line_id is not None
            else None
        )

        unidad_albaran = albaran_line.unidad_medida if albaran_line else None
        unidad_contrato = (
            contrato_line.unidad_medida if contrato_line is not None else None
        )

        ctx = albaran_line.contexto_linea if albaran_line is not None else None
        rol_linea = ctx.rol_linea if ctx is not None else None

        # ------------------------------------------------------------ #
        # Tanda descuento — abr 2026
        # Descuento de la línea del albarán (None si no hay).
        # ------------------------------------------------------------ #
        descuento_linea: float | None = (
            albaran_line.descuento_albaran
            if albaran_line is not None
            else None
        )

        # 1. Unit guard
        categoria, category_match, guard_reasons = self._guard.resolve(
            line=line,
            unidad_albaran=unidad_albaran,
            unidad_contrato=unidad_contrato,
        )

        # 2. Price reconciliation
        # (jul 2026) Regla de precedencia: los valores LEÍDOS del
        # albarán mandan; el contrato solo aporta partida/código y su
        # precio queda como fallback si el albarán no trae valores.
        # Se pasa el descuento para derivar el unitario BRUTO desde el
        # importe leído (importe / (cantidad × (1 − dto/100))).
        reconciliation = self._reconciler.reconcile(
            precio_1a=line.precio_unitario_contrato_db,
            precio_1b=line.precio_unitario_pdf_inferido,
            precio_albaran_declarado=(
                albaran_line.precio_unitario_albaran if albaran_line else None
            ),
            cantidad_albaran=(
                albaran_line.cantidad if albaran_line else None
            ),
            importe_albaran=(
                albaran_line.importe_albaran if albaran_line else None
            ),
            line_already_valued=line_already_valued,
            descuento_pct=descuento_linea,
        )

        # 2.bis (F-003, R5) ¿Se aplica el descuento del albarán al
        # importe? SOLO si el precio unitario final SALE del albarán. Si
        # el precio viene del CONTRATO (o del PDF de contrato), aplicarle
        # además el descuento del albarán cuenta dos veces la misma
        # rebaja: el precio pactado ya es el que es. Queda motivo de
        # auditoría para que el revisor sepa que el descuento se leyó y
        # se ignoró a propósito.
        #
        # OJO: el descuento SÍ sigue viajando al reconciler (arriba) —
        # ahí se usa para derivar el unitario BRUTO desde el importe
        # leído, que es otra cosa.
        precio_sale_del_albaran = reconciliation.source in (
            "albaran_declared",
            "albaran_calculated",
        )
        descuento_para_importe = (
            descuento_linea if precio_sale_del_albaran else None
        )
        descuento_no_aplicado_a_contrato = (
            not precio_sale_del_albaran
            and descuento_linea is not None
            and float(descuento_linea) != 0.0
        )

        # 3. Partida matching
        if partida_override is not None or ref_linea_base_merge_id is not None:
            partida_result: PartidaMatchResult = (
                self._partida_matcher.resolve_partida_for_complementaria(
                    codigo_partida_base=partida_override,
                )
            )
        else:
            partida_result = self._partida_matcher.match(
                line=line,
                codigo_partida_albaran=(
                    albaran_line.codigo_partida_albaran if albaran_line else None
                ),
                precio_unitario_final=reconciliation.final_price,
                unidad_albaran=unidad_albaran,
                contrato_lines=contrato_lines,
                albaran_descripcion=(
                    albaran_line.descripcion if albaran_line else None
                ),
                albaran_codigo_producto=(
                    albaran_line.codigo if albaran_line else None
                ),
            )

        effective_matched_id = partida_result.matched_contrato_line_id
        if effective_matched_id is None and partida_result.derived_line is None:
            effective_matched_id = line.matched_contrato_line_id

        # Fallback "LINEA NUEVA": si la IA no caso NADA (ni linea de
        # contrato ni derivada), generamos una linea DERIVADA a partir del
        # propio albaran (concepto/cantidad/precio/partida declarados) para
        # que NINGUNA linea quede sin salmon. origen='nueva_no_match' -> en
        # sv4 sale como "Nueva" (no Sigrid), igual que el modo "nueva" del
        # boton +. Cuenta en el total (importe = cantidad x final_price).
        nueva_derived = None
        if effective_matched_id is None and partida_result.derived_line is None:
            _cl_ia = (
                contrato_by_id.get(line.matched_contrato_line_id)
                if line.matched_contrato_line_id is not None
                else None
            )
            if _cl_ia is not None:
                # (a) La IA SI caso una linea de contrato (mismo concepto)
                #     pero el partida_matcher la descarto por cruce de
                #     partida -> derivada MODIFICADA: respeta descripcion +
                #     unitario del CONTRATO, imputa a la partida del ALBARAN.
                nueva_derived = DerivedContratoLineRecord(
                    codigo_contrato=(self._codigo_contrato_actual or ""),
                    codigo_producto=_cl_ia.codigo_producto,
                    descripcion_linea=_cl_ia.descripcion,
                    unidad_medida=_cl_ia.unidad_medida,
                    precio_unitario=_cl_ia.precio_unitario,
                    codigo_partida=(
                        albaran_line.codigo_partida_albaran
                        if albaran_line else None
                    ),
                    origen="nueva_no_match",
                )
            else:
                # (b) La IA no caso nada -> NUEVA generica desde el albaran.
                nueva_derived = DerivedContratoLineRecord(
                    codigo_contrato=(self._codigo_contrato_actual or ""),
                    codigo_producto=(
                        albaran_line.codigo if albaran_line else None
                    ),
                    descripcion_linea=(
                        (albaran_line.descripcion if albaran_line else None)
                        or line.descripcion_linea
                    ),
                    unidad_medida=unidad_albaran,
                    precio_unitario=reconciliation.final_price,
                    codigo_partida=(
                        albaran_line.codigo_partida_albaran
                        if albaran_line else None
                    ),
                    origen="nueva_no_match",
                )

        # 4. Unit conversion
        if category_match and partida_result.derived_line is not None:
            unidad_contrato_para_conversion = unidad_albaran
        else:
            unidad_contrato_para_conversion = unidad_contrato

        if category_match:
            converted = self._converter.convert(
                cantidad=albaran_line.cantidad if albaran_line else None,
                unidad_albaran=unidad_albaran,
                unidad_contrato=unidad_contrato_para_conversion,
            )
        else:
            converted = self._converter.convert(
                cantidad=None,
                unidad_albaran=unidad_albaran,
                unidad_contrato=unidad_contrato_para_conversion,
            )

        # 4.bis Residuos: la cantidad VALORADA es el nº de contenedores
        # (contrato: X m3/contenedor), no los m3 del albaran. m3 y Tn se
        # conservan como metadato (contexto_linea) para trabajos posteriores.
        # Determinista y AISLADO: solo afecta a lineas tipo_familia='residuos';
        # si no se puede calcular, cae a la cantidad normal y marca revision.
        residuos_calc = None
        if ctx is not None and getattr(ctx, "tipo_familia", None) == "residuos":
            residuos_calc = calcular_contenedores_residuos(
                contexto_linea=ctx,
                contrato_line=contrato_by_id.get(effective_matched_id),
                contrato_lines=contrato_lines,
                contenedor_m3_ia=getattr(line, "contenedor_m3", None),
            )
        if residuos_calc is not None and residuos_calc.num_contenedores is not None:
            _cant_conv_final = float(residuos_calc.num_contenedores)
            _cant_alb_final = float(residuos_calc.num_contenedores)
        else:
            _cant_conv_final = converted.cantidad_convertida
            _cant_alb_final = albaran_line.cantidad if albaran_line else None

        # (jul 2026) Regla de negocio residuos: una línea de MOVIMIENTO
        # (porte / retirada / entrega / cambio de contenedor) que llega
        # SIN cantidad vale 1 — el albarán documenta UN movimiento.
        # Sin esto, la línea quedaba con cantidad/importe vacíos.
        _movimiento_asumido_1 = False
        if (
            (_cant_conv_final is None or _cant_conv_final == 0)
            and (_cant_alb_final is None or _cant_alb_final == 0)
            and _es_movimiento_residuos(
                ctx=ctx,
                albaran_line=albaran_line,
                contrato_line=contrato_by_id.get(effective_matched_id),
            )
        ):
            _cant_conv_final = 1.0
            _cant_alb_final = 1.0
            _movimiento_asumido_1 = True

        # 5. Importe (con descuento aplicado)
        importe_result = self._importe_calc.compute(
            cantidad_convertida=_cant_conv_final,
            cantidad_albaran=_cant_alb_final,
            precio_unitario_final=reconciliation.final_price,
            importe_albaran_declarado=(
                albaran_line.importe_albaran if albaran_line else None
            ),
            descuento_pct=descuento_para_importe,
        )

        reasons: list[str] = []
        if descuento_no_aplicado_a_contrato:
            reasons.append("descuento_albaran_no_aplicado_a_precio_contrato")
        reasons.extend(guard_reasons)
        reasons.extend(reconciliation.reasons)
        reasons.extend(partida_result.reasons)
        reasons.extend(converted.reasons)
        if _movimiento_asumido_1:
            reasons.append("movimiento_residuos_sin_cantidad_asumido_1")

        # (jul 2026) Hormigón: si IA2 dejó constancia de que faltan las
        # horas de descarga (fin/límite en blanco), el exceso de tiempo
        # no es computable — se avisa para que el revisor lo mire.
        if (
            ctx is not None
            and getattr(ctx, "tipo_familia", None) == "hormigon"
            and rol_linea in (None, "base")
            and getattr(ctx, "notas_tiempo", None)
        ):
            _nt = str(ctx.notas_tiempo).lower()
            if re.search(r"fin de descarga|hora fin", _nt) and re.search(
                r"\bno\b|\bsin\b|ilegibl|vac[ií]|falta|en blanco", _nt
            ):
                reasons.append("horas_descarga_incompletas")
        reasons.extend(importe_result.reasons)
        if residuos_calc is not None:
            reasons.extend(residuos_calc.reasons)
        if line.match_method == "no_match":
            reasons.append("ia_no_match")

        if ctx is None:
            tarifa_pdf_encontrada: bool | None = None
        else:
            tarifa_pdf_encontrada = line.precio_unitario_pdf_inferido is not None
            if not tarifa_pdf_encontrada:
                if reconciliation.source not in (
                    "contract_line_match", "both_agreed",
                ):
                    reasons.append("modifier_not_in_contract")

        review_required = (
            not category_match
            or reconciliation.agreement == "mismatch"
            or reconciliation.source == "none"
            or converted.ambiguous
            or importe_result.importe_source == "none"
            or line.match_method == "no_match"
            or line.match_confidence_pct < 60.0
            or (ctx is not None and tarifa_pdf_encontrada is False
                and reconciliation.source not in (
                    "contract_line_match", "both_agreed",
                ))
        )
        # Residuos sin nº de contenedores calculable → revisión manual.
        if residuos_calc is not None and residuos_calc.num_contenedores is None:
            review_required = True
        # (jul 2026) Volumen implausible (posibles Tn coladas en el
        # campo de volumen): el número se calcula igual, pero la
        # línea SIEMPRE va a revisión con la sospecha en reasons.
        if residuos_calc is not None and any(
            r.startswith("residuos_volumen_implausible")
            for r in residuos_calc.reasons
        ):
            review_required = True

        return LineValuationRecord(
            merge_line_id=line.merge_line_id,
            matched_contrato_line_id=effective_matched_id,
            derived_contrato_line_record=(
                partida_result.derived_line
                if partida_result.derived_line is not None
                else nueva_derived
            ),
            precio_unitario_contrato_db=line.precio_unitario_contrato_db,
            precio_unitario_pdf_inferido=line.precio_unitario_pdf_inferido,
            precio_unitario_final=reconciliation.final_price,
            precio_unitario_source=reconciliation.source,
            precio_unitario_agreement=reconciliation.agreement,
            unidad_albaran=unidad_albaran,
            unidad_contrato=unidad_contrato,
            unidad_categoria=categoria,
            unidad_category_match=category_match,
            cantidad_albaran=(
                albaran_line.cantidad if albaran_line else None
            ),
            # Residuos: la cantidad valorada es el nº de contenedores
            # (_cant_conv_final). Para el resto == converted.cantidad_
            # convertida (el else de arriba lo iguala), así que no cambia.
            cantidad_convertida=_cant_conv_final,
            factor_conversion=converted.factor,
            importe_calculado=importe_result.importe_calculado,
            importe_albaran_declarado=(
                albaran_line.importe_albaran if albaran_line else None
            ),
            importe_source=importe_result.importe_source,
            codigo_partida_albaran=(
                albaran_line.codigo_partida_albaran if albaran_line else None
            ),
            codigo_partida_final=partida_result.codigo_partida_final,
            partida_action=partida_result.partida_action,
            match_confidence_pct=float(line.match_confidence_pct),
            match_method=line.match_method,  # type: ignore[arg-type]
            review_required=review_required,
            review_reasons=reasons,
            ia_reasoning=line.razon_corta,
            # Sub-tanda 2C
            rol_linea=rol_linea,
            ref_linea_base_merge_id=ref_linea_base_merge_id,
            tarifa_pdf_encontrada=tarifa_pdf_encontrada,
            modifiers_applied=None,
            # Sub-tanda 2D
            line_kind="from_albaran",
            parent_merge_line_id=None,
            modifier_source=None,
            modifier_reason=None,
            descripcion_linea=None,
            # Tanda descuento — abr 2026
            descuento_albaran_aplicado=importe_result.descuento_aplicado,
        )

    def _build_synthetic_line(
        self,
        *,
        line: LineValuationDto,
        parent_merge_line_id: int | None,
        partida_heredada: str | None,
        parent_record: LineValuationRecord | None,
        albaran_by_id: Dict[int, AlbaranLineContextDto],
        contrato_by_id: Dict[int, ContratoLineContextDto],
    ) -> LineValuationRecord:
        """Construye el record de una línea sintética (sub-tanda 2D).

        Reglas:
          - No tiene línea del albarán propia. Hereda cantidad y unidad
            del parent. La herencia preferida es desde el RECORD YA
            RESUELTO del parent (``parent_record``), no del albarán
            directamente — los albaranes de hormigón suelen no traer
            unidad como columna textual (el OCR no la captura) y por
            tanto ``parent_albaran.unidad_medida`` puede ser None. En
            ese caso la unidad real vive en ``parent_record.unidad_contrato``
            (que viene del matching con la línea del contrato) o
            ``parent_record.unidad_albaran``.
          - Hereda partida de la base (resolve_partida_for_synthetic).
          - No se crea línea derivada en contrato.
          - precio_unitario_final = precio_unitario_pdf_inferido del LLM.
          - Si precio null → review_required con motivo
            'modifier_identified_no_tariff' (el revisor decide si factura).
          - importe = cantidad * precio cuando ambos disponibles.

        Tanda descuento — abr 2026:
          - Hereda ``descuento_albaran_aplicado`` del parent_record.
          - Si parent_record es None (no resuelto), no aplica descuento.
          - El descuento se aplica al importe sintético igual que en
            las líneas from_albaran (regla de negocio: las sintéticas
            heredan el descuento del padre).
        """
        parent_albaran = (
            albaran_by_id.get(parent_merge_line_id)
            if parent_merge_line_id is not None
            else None
        )

        # ------------------------------------------------------------ #
        # Tanda descuento — abr 2026
        # Herencia del descuento del padre.
        # ------------------------------------------------------------ #
        descuento_heredado: float | None = (
            parent_record.descuento_albaran_aplicado
            if parent_record is not None
            else None
        )

        # Detección de línea de tiempo (M6 del prompt): tiene semántica
        # distinta del resto — cantidad y unidad no heredan del parent,
        # vienen del LLM (cantidad = minutos de exceso, unidad = "min").
        is_time_line = (line.modifier_source == "tiempo_exceso")

        # Detección de línea de carga incompleta (M7 del prompt):
        # similar a tiempo en que la cantidad la calcula el LLM
        # (m³ que faltan hasta el mínimo del contrato), PERO la unidad
        # y la categoría se heredan del parent (es m³, no "min").
        is_carga_incompleta_line = (
            line.modifier_source == "carga_incompleta"
        )

        if is_time_line:
            # cantidad_override es el CAMPO CLAVE para líneas de tiempo:
            # el LLM calcula los minutos de exceso a partir de
            # notas_tiempo y los manda aquí. Puede ser 0 (descarga
            # dentro del tiempo). Si el LLM no lo envía (no debería
            # pasar si emite una M6, pero por seguridad), fallback a
            # 0.0 — así al menos la línea se persiste aunque sin
            # información real de minutos.
            cantidad = (
                float(line.cantidad_override)
                if line.cantidad_override is not None
                else 0.0
            )
            unidad = "min"
            unidad_cat = "time"
        elif is_carga_incompleta_line:
            # cantidad_override = m³ de diferencia hasta el mínimo
            # facturable del contrato (típicamente max(0, 6 - vertido)).
            # Calculada por el LLM en M7.3. Si no viene, fallback a 0.0
            # (el revisor verá la línea con importe 0 y sabrá que algo
            # falló en el cálculo).
            cantidad = (
                float(line.cantidad_override)
                if line.cantidad_override is not None
                else 0.0
            )
            # Unidad y categoría: igual que el resto de sintéticas
            # (heredan del parent, típicamente m³).
            unidad: str | None = None
            if parent_record is not None:
                unidad = parent_record.unidad_contrato or parent_record.unidad_albaran
            if not unidad and parent_albaran is not None:
                unidad = parent_albaran.unidad_medida

            if parent_record is not None and parent_record.unidad_categoria:
                unidad_cat = parent_record.unidad_categoria
            elif parent_albaran is not None and parent_albaran.unidad_categoria:
                unidad_cat = parent_albaran.unidad_categoria
            else:
                unidad_cat = "unknown"
        else:
            # Cantidad: del parent_record si existe (ya resuelto con factor
            # de conversión), si no del albarán directamente como fallback.
            if parent_record is not None and parent_record.cantidad_albaran is not None:
                cantidad = parent_record.cantidad_albaran
            elif parent_albaran is not None:
                cantidad = parent_albaran.cantidad
            else:
                cantidad = None

            # Unidad: prioridad al record ya resuelto del parent
            # (unidad_contrato → unidad_albaran), con fallback al albarán.
            unidad: str | None = None
            if parent_record is not None:
                unidad = parent_record.unidad_contrato or parent_record.unidad_albaran
            if not unidad and parent_albaran is not None:
                unidad = parent_albaran.unidad_medida

            # Categoría de unidad: se hereda igual.
            if parent_record is not None and parent_record.unidad_categoria:
                unidad_cat = parent_record.unidad_categoria
            elif parent_albaran is not None and parent_albaran.unidad_categoria:
                unidad_cat = parent_albaran.unidad_categoria
            else:
                unidad_cat = "unknown"

        # Reconciliación de precio IDÉNTICA a la base (no es un caso por
        # modificador): si la IA macheó esta sintética a una línea del
        # contrato (Paso 7 — macheo semántico), su precio llega en
        # precio_unitario_contrato_db (Fase 1A) y se reconcilia contra el
        # del PDF (Fase 1B). Si la IA no macheó (el contrato no tarifa ese
        # modificador), precio_unitario_contrato_db es null y queda el del
        # PDF (only_1b) o nada (neither). Una sintética no tiene precio
        # declarado de albarán, así que esos campos van a None.
        reconciliation = self._reconciler.reconcile(
            precio_1a=line.precio_unitario_contrato_db,
            precio_1b=line.precio_unitario_pdf_inferido,
            precio_albaran_declarado=None,
            cantidad_albaran=None,
            importe_albaran=None,
            line_already_valued=False,
        )
        precio_final = reconciliation.final_price
        precio_source = reconciliation.source
        precio_agreement = reconciliation.agreement

        # ------------------------------------------------------------ #
        # Cálculo de importe (con descuento heredado del padre).
        #
        # Regla normal: cantidad × precio × (1 - descuento/100).
        # Casos especiales:
        #   - cantidad = 0 (típicamente línea de tiempo sin exceso):
        #     importe = 0 siempre.
        #   - cantidad > 0 y precio null: importe null (Forma C).
        #   - cantidad null: importe null.
        # ------------------------------------------------------------ #
        importe_calc: float | None = None
        importe_source = "none"
        descuento_aplicado: float | None = None

        if cantidad is not None:
            if float(cantidad) == 0.0:
                importe_calc = 0.0
                importe_source = "calculated"
            elif precio_final is not None:
                # Aplicación del descuento heredado al importe sintético.
                bruto = float(cantidad) * float(precio_final)
                if descuento_heredado is not None and descuento_heredado > 0.0:
                    importe_calc = round(
                        bruto * (1.0 - descuento_heredado / 100.0),
                        2,
                    )
                    descuento_aplicado = descuento_heredado
                else:
                    importe_calc = round(bruto, 2)
                importe_source = "calculated"

        partida_result = self._partida_matcher.resolve_partida_for_synthetic(
            codigo_partida_base=partida_heredada,
        )

        reasons: list[str] = list(partida_result.reasons)

        # --------------------------------------------------------------- #
        # "Nueva" automatica por partida (jun 2026):
        # La IA machea cada modificador SEMANTICAMENTE contra la tabla del
        # contrato (Paso 7), pero la PARTIDA no la decide la IA: es
        # deterministica. Si la linea de contrato macheada vive en OTRA
        # partida que la del albaran (heredada del parent), NO la
        # referenciamos directamente: derivamos una linea NUEVA en la
        # partida del albaran, con el concepto/precio de la macheada
        # (mismo criterio que la base). Si esta en la MISMA partida (o no
        # hay match, o no hay partida heredada), se mantiene el match.
        # --------------------------------------------------------------- #
        partida_heredada_norm = (
            partida_result.codigo_partida_final or ""
        ).strip()
        matched_line = (
            contrato_by_id.get(line.matched_contrato_line_id)
            if line.matched_contrato_line_id is not None
            else None
        )
        effective_matched_id: int | None = line.matched_contrato_line_id
        derived_record: DerivedContratoLineRecord | None = None
        partida_action = partida_result.partida_action

        if (
            matched_line is not None
            and partida_heredada_norm
            and (matched_line.codigo_partida or "").strip()
            != partida_heredada_norm
        ):
            # (jul 2026) UX del revisor — feedback pgris: si la
            # sintética es un incremento POR AÑO y la tarifa del
            # contrato no lleva el año en su texto (Sigrid solo
            # trae "INCREMENTO PRECIO HORMIGÓN HA-25/B/20/XC2";
            # el año vive en la sub-descripción del anexo, que no
            # viaja), el concepto derivado añade " — AÑO XXXX":
            # así dos ejercicios nunca se ven idénticos en sv4.
            descripcion_derivada = (
                matched_line.descripcion or line.descripcion_linea
            )
            if (line.rol_linea or "").strip().lower() == "incremento_year":
                anio_syn = _anio_de_texto(
                    f"{line.descripcion_linea or ''} "
                    f"{line.modifier_reason or ''}"
                )
                if anio_syn and anio_syn not in (descripcion_derivada or ""):
                    descripcion_derivada = (
                        f"{descripcion_derivada} — AÑO {anio_syn}"
                    )
            derived_record = DerivedContratoLineRecord(
                codigo_contrato=matched_line.codigo_contrato,
                codigo_producto=None,
                descripcion_linea=descripcion_derivada,
                unidad_medida=matched_line.unidad_medida or unidad,
                precio_unitario=precio_final,
                codigo_partida=partida_result.codigo_partida_final,
                origen="missing_partida",
            )
            effective_matched_id = None
            partida_action = "new_line_created"
            reasons.append("modifier_derived_partida_distinta")

        # 'modifier_identified_no_tariff' solo si el modificador tiene
        # cantidad > 0 (hay algo que cobrar) y no encontramos tarifa.
        # Si cantidad es 0 (caso típico de tiempo sin exceso), no hay
        # nada que revisar.
        has_quantity = cantidad is not None and float(cantidad) > 0.0
        if precio_final is None and has_quantity:
            reasons.append("modifier_identified_no_tariff")
        if parent_merge_line_id is None:
            reasons.append("synthetic_without_parent")
        elif parent_albaran is None:
            reasons.append("synthetic_parent_not_in_context")
        if descuento_aplicado is not None and descuento_aplicado > 0.0:
            reasons.append(
                f"descuento_heredado_aplicado:{descuento_aplicado}%"
            )

        review_required = (
            (precio_final is None and has_quantity)
            or precio_agreement == "mismatch"
            or parent_merge_line_id is None
            or parent_albaran is None
            or line.match_confidence_pct < 60.0
        )

        tarifa_pdf_encontrada: bool | None = (
            line.precio_unitario_pdf_inferido is not None
        )

        # Fallback "LINEA NUEVA" para sinteticas SIN match de contrato:
        # si la IA no caso el modificador (ni hay derivada por partida
        # distinta), derivamos una linea NUEVA a partir del propio
        # modificador para que NINGUNA linea quede sin salmon (mismo
        # criterio que en _build_line). origen='nueva_no_match' -> en sv4
        # sale como "Nueva". Cuenta en el total (importe = cant x precio).
        if effective_matched_id is None and derived_record is None:
            derived_record = DerivedContratoLineRecord(
                codigo_contrato=(
                    getattr(self, "_codigo_contrato_actual", None) or ""
                ),
                codigo_producto=None,
                descripcion_linea=line.descripcion_linea,
                unidad_medida=unidad,
                precio_unitario=precio_final,
                codigo_partida=partida_result.codigo_partida_final,
                origen="nueva_no_match",
            )
            partida_action = partida_action or "new_line_created"

        return LineValuationRecord(
            merge_line_id=None,
            matched_contrato_line_id=effective_matched_id,
            derived_contrato_line_record=derived_record,
            precio_unitario_contrato_db=line.precio_unitario_contrato_db,
            precio_unitario_pdf_inferido=line.precio_unitario_pdf_inferido,
            precio_unitario_final=precio_final,
            precio_unitario_source=precio_source,  # type: ignore[arg-type]
            precio_unitario_agreement=precio_agreement,  # type: ignore[arg-type]
            unidad_albaran=unidad,
            unidad_contrato=unidad,
            unidad_categoria=unidad_cat,
            unidad_category_match=True,
            cantidad_albaran=cantidad,
            cantidad_convertida=cantidad,
            factor_conversion=1.0 if cantidad is not None else None,
            importe_calculado=importe_calc,
            importe_albaran_declarado=None,
            importe_source=importe_source,  # type: ignore[arg-type]
            codigo_partida_albaran=None,
            codigo_partida_final=partida_result.codigo_partida_final,
            partida_action=partida_action,
            match_confidence_pct=float(line.match_confidence_pct),
            match_method=line.match_method,  # type: ignore[arg-type]
            review_required=review_required,
            review_reasons=reasons,
            ia_reasoning=line.razon_corta,
            # Sub-tanda 2C
            rol_linea=line.rol_linea,
            ref_linea_base_merge_id=None,
            tarifa_pdf_encontrada=tarifa_pdf_encontrada,
            modifiers_applied=None,
            # Sub-tanda 2D — identificación de la sintética
            line_kind="synthetic_modifier",
            parent_merge_line_id=parent_merge_line_id,
            modifier_source=line.modifier_source,
            modifier_reason=line.modifier_reason,
            descripcion_linea=line.descripcion_linea,
            # Tanda descuento — abr 2026 (heredado del padre)
            descuento_albaran_aplicado=descuento_aplicado,
        )

    @staticmethod
    def _build_header(
        *,
        envelope: ValuationEnvelope,
        records: list[LineValuationRecord],
    ) -> ValuationHeaderRecord:
        total_valorado = sum(
            float(r.importe_calculado or 0.0) for r in records
        )
        match_counts = {
            "exact_concept": 0,
            "semantic": 0,
            "price_only": 0,
            "no_match": 0,
        }
        for r in records:
            mm: MatchMethod = r.match_method
            if mm in match_counts:
                match_counts[mm] += 1

        header_review_required = any(r.review_required for r in records)
        header_reasons: list[str] = []
        if header_review_required:
            header_reasons.append("at_least_one_line_requires_review")
        if match_counts["no_match"] > 0:
            header_reasons.append(
                f"lines_without_match:{match_counts['no_match']}"
            )

        return ValuationHeaderRecord(
            document_id=envelope.meta.document_id,
            contrato_codigo=envelope.meta.codigo_contrato,
            status="ok",
            provider_ia=envelope.meta.primary_provider,
            model_name=envelope.meta.model,
            prompt_key=envelope.meta.prompt_key,
            total_valorado=round(total_valorado, 2),
            total_lines=len(records),
            lines_matched_exact=match_counts["exact_concept"],
            lines_matched_semantic=match_counts["semantic"],
            lines_matched_price_only=match_counts["price_only"],
            lines_unmatched=match_counts["no_match"],
            review_required=header_review_required,
            review_reasons=header_reasons,
            raw_ia_envelope_json=None,
        )
