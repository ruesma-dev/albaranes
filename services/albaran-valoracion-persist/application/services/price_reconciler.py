# application/services/price_reconciler.py
from __future__ import annotations

import logging
from dataclasses import dataclass

from domain.models.valuation_records import (
    PrecioUnitarioAgreement,
    PrecioUnitarioSource,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PriceReconciliation:
    final_price: float | None
    source: PrecioUnitarioSource
    agreement: PrecioUnitarioAgreement
    reasons: list[str]


class PriceReconciler:
    """Decide el precio unitario final de la línea.

    ------------------------------------------------------------------
    Tanda precedencia albarán — jul 2026
    ------------------------------------------------------------------
    REGLA (Construcciones Ruesma): los valores LEÍDOS del albarán
    MANDAN SIEMPRE que existan. El casado con el contrato aporta
    partida/código/concepto, pero NO pisa importes ni unitarios
    leídos. El precio del contrato queda como FALLBACK únicamente
    cuando el albarán no trae ni importe ni unitario (albaranes sin
    valorar, el caso para el que nació la valoración).

    Motivo: partidas del contrato tipo PA (partida alzada) usadas como
    "precio unitario" generaban importes disparatados (p. ej. una
    cinta de señalización de 18,84 EUR leídos valorada a 960.000 EUR
    por casar con una PA de 8.000 EUR del contrato).

    ------------------------------------------------------------------
    F-019 (ago 2026) — manda el UNITARIO leído
    ------------------------------------------------------------------
    Lo anterior sigue vigente palabra por palabra: el contrato no pisa
    lo leído. Lo que cambia es la precedencia INTERNA entre los dos
    valores del propio albarán. Regla del humano (2026-08-18), en dos
    mitades:

      * si el albarán trae cantidad, precio unitario y descuento, el
        importe es ``cantidad × precio × (1 − dto/100)`` y **el
        unitario leído MANDA**;
      * **solo** si faltan esos campos y sí hay importe final, se
        despeja el unitario de esa misma fórmula.

    Antes ganaba el importe y el unitario declarado solo se respetaba
    si coincidía con el derivado. Con un importe corrompido eso
    fabricaba un unitario inventado en silencio: en la prueba local
    del 2026-08-18 (``progress/prueba_local_feymaco_20260818.md``) la
    línea de papel higiénico del albarán Feymaco 2.137.569 —108 ud a
    0,543 EUR con 40 % de descuento— salió valorada a 58,65 EUR/ud.

    Prioridad:
      1. UNITARIO declarado (≠0) → MANDA, con o sin importe leído.
         source='albaran_declared'. Si además el importe es derivable:
           - coincide dentro de la tolerancia → agreement='neither',
             reason 'albaran_unitario_manda_derivado_coincide';
           - discrepa → agreement='mismatch' y reason
             'unitario_declarado_vs_derivado_mismatch:<decl>!=<deriv>'.
             El precio final es el DECLARADO en ambos casos; el
             mismatch viaja por ``agreement`` porque es lo que
             ``ValuationBuilder._build_line`` ya lleva a
             ``review_required`` (decisión D3 de F-019): así el
             desacuerdo va a revisión en vez de persistirse mudo.
      2. IMPORTE leído (≠0) con cantidad válida y SIN unitario
         declarado → se despeja el DERIVADO BRUTO:
             unitario = importe / (cantidad × (1 − descuento/100))
         (la fórmula canónica del importe es
          cantidad × unitario × (1 − dto/100); derivar sin deshacer el
          descuento daría el unitario NETO y el descuento se aplicaría
          dos veces aguas abajo — bug corregido en jul 2026).
         source='albaran_calculated'.
      3. FALLBACK contrato (albarán sin valores): la cadena clásica —
         1a y 1b coinciden → media; discrepan → 1a; solo 1a → 1a;
         solo 1b → 1b; nada → None.

    Valores 0 leídos se tratan como AUSENTES (una celda vacía no debe
    valorar a 0 EUR); se deja reason de auditoría.

    Las líneas sintéticas (M1–M7) no tienen valores de albarán (el
    builder pasa None explícitos) → caen al fallback contrato, como
    siempre.
    """

    def __init__(self, *, tolerance_pct: float) -> None:
        self._tolerance_pct = float(tolerance_pct)

    def reconcile(
        self,
        *,
        precio_1a: float | None,
        precio_1b: float | None,
        precio_albaran_declarado: float | None,
        cantidad_albaran: float | None,
        importe_albaran: float | None,
        line_already_valued: bool,
        descuento_pct: float | None = None,
    ) -> PriceReconciliation:
        reasons: list[str] = []
        if line_already_valued:
            # Trazabilidad: antes era una rama especial ("el albarán
            # manda"); con la regla jul 2026 ese es el comportamiento
            # general, así que la rama queda subsumida.
            reasons.append("line_already_valued")

        # ---- Saneamiento de los valores leídos (0 → ausente) ------- #
        importe_leido = self._no_cero(
            importe_albaran, "importe_albaran_cero_ignorado", reasons
        )
        declarado = self._no_cero(
            precio_albaran_declarado,
            "precio_declarado_cero_ignorado",
            reasons,
        )

        # ---- Unitario BRUTO derivado del importe leído ------------- #
        derivado_bruto = self._derivar_bruto(
            importe_leido=importe_leido,
            cantidad_albaran=cantidad_albaran,
            descuento_pct=descuento_pct,
            reasons=reasons,
        )

        # ---- 1. El UNITARIO declarado manda (F-019) ---------------- #
        if declarado is not None:
            if derivado_bruto is not None and not self._match(
                declarado, derivado_bruto
            ):
                # El desacuerdo NO cambia el precio (manda el
                # declarado), pero sale por ``agreement`` para que el
                # builder mande la línea a revisión humana.
                reasons.append(
                    f"unitario_declarado_vs_derivado_mismatch:"
                    f"{declarado}!={derivado_bruto}"
                )
                logger.info(
                    "[price-reconciler] unitario declarado %s no cuadra "
                    "con el derivado del importe %s; manda el declarado "
                    "y la línea va a revisión.",
                    declarado, derivado_bruto,
                )
                return PriceReconciliation(
                    final_price=float(declarado),
                    source="albaran_declared",
                    agreement="mismatch",
                    reasons=reasons,
                )
            motivo = (
                "albaran_unitario_manda_derivado_coincide"
                if derivado_bruto is not None
                else "albaran_unitario_declarado_manda"
            )
            return PriceReconciliation(
                final_price=float(declarado),
                source="albaran_declared",
                agreement="neither",
                reasons=reasons + [motivo],
            )

        # ---- 2. Sin unitario declarado: se despeja del importe ----- #
        if derivado_bruto is not None:
            return PriceReconciliation(
                final_price=derivado_bruto,
                source="albaran_calculated",
                agreement="neither",
                reasons=reasons + ["albaran_importe_manda_derivado"],
            )

        # ---- 3. Fallback contrato (cadena clásica 1a/1b) ----------- #
        if precio_1a is not None and precio_1b is not None:
            if self._match(precio_1a, precio_1b):
                # Promediamos para atenuar redondeos.
                avg = (float(precio_1a) + float(precio_1b)) / 2.0
                return PriceReconciliation(
                    final_price=avg,
                    source="both_agreed",
                    agreement="match",
                    reasons=reasons,
                )
            reasons.append(
                f"price_1a_vs_1b_mismatch:{precio_1a}!={precio_1b}"
            )
            logger.info(
                "[price-reconciler] mismatch 1a=%s 1b=%s; prevalece 1a.",
                precio_1a, precio_1b,
            )
            return PriceReconciliation(
                final_price=float(precio_1a),
                source="contract_line_match",
                agreement="mismatch",
                reasons=reasons,
            )

        if precio_1a is not None:
            return PriceReconciliation(
                final_price=float(precio_1a),
                source="contract_line_match",
                agreement="only_1a",
                reasons=reasons + ["only_1a_available"],
            )

        if precio_1b is not None:
            return PriceReconciliation(
                final_price=float(precio_1b),
                source="pdf_inference",
                agreement="only_1b",
                reasons=reasons + ["only_1b_available"],
            )

        return PriceReconciliation(
            final_price=None,
            source="none",
            agreement="neither",
            reasons=reasons + ["no_price_available"],
        )

    # ---------------------------------------------------------------- #
    # Helpers privados
    # ---------------------------------------------------------------- #
    @staticmethod
    def _no_cero(
        valor: float | None,
        reason_si_cero: str,
        reasons: list[str],
    ) -> float | None:
        """0 leído se trata como ausente (celda vacía), con auditoría."""
        if valor is None:
            return None
        if float(valor) == 0.0:
            reasons.append(reason_si_cero)
            return None
        return float(valor)

    @staticmethod
    def _derivar_bruto(
        *,
        importe_leido: float | None,
        cantidad_albaran: float | None,
        descuento_pct: float | None,
        reasons: list[str],
    ) -> float | None:
        """unitario_bruto = importe / (cantidad × (1 − dto/100)).

        Devuelve None si no es derivable (sin importe, sin cantidad
        válida, o descuento 100% que anula el divisor).
        """
        if importe_leido is None:
            return None
        if cantidad_albaran is None or float(cantidad_albaran) == 0.0:
            reasons.append("importe_leido_sin_cantidad_no_derivable")
            return None
        factor = 1.0
        if descuento_pct is not None and 0.0 < float(descuento_pct) <= 100.0:
            if float(descuento_pct) == 100.0:
                reasons.append("descuento_100_no_derivable")
                return None
            factor = 1.0 - float(descuento_pct) / 100.0
        bruto = float(importe_leido) / (float(cantidad_albaran) * factor)
        return round(bruto, 6)

    def _match(self, a: float, b: float) -> bool:
        if a == 0 and b == 0:
            return True
        denom = max(abs(float(a)), abs(float(b)), 1e-9)
        diff_pct = abs(float(a) - float(b)) / denom * 100.0
        return diff_pct <= self._tolerance_pct
