# application/services/header_resolver_service.py
from __future__ import annotations

import logging
import unicodedata

from application.services.familia_detector import (
    familias_de_filas_merge,
    familias_de_texto,
)
from domain.models.header_resolution_models import (
    MOTIVO_PROVEEDOR_CORREGIDO,
    MOTIVO_PROVEEDOR_NO_CASA,
    NOTA_PROVEEDOR_CORREGIDO_PREFIJO,
    ProveedorObraResumen,
)
from domain.models.obra_models import ObraEnrichmentResult
from domain.ports.header_resolver_ports import (
    HeaderMergeRepository,
    ObraReverseLookupClient,
    ProveedorReverseLookupClient,
)
from ruesma_comun.obras import normalizar_codigo_obra
from ruesma_comun.proveedores import (
    identificador_fiscal_valido,
    normalizar_cif,
)
from ruesma_comun.sigrid import SigridRespuestaTruncada

logger = logging.getLogger(__name__)

_LOG_PREFIX = "[header-resolver]"

# Prefijo del aviso de proveedor en review_notes. Se usa tambien para
# RETIRAR el aviso obsoleto (idempotencia en re-enriquecimientos y cuando
# el CIF ya quedo resuelto por el revisor).
_NOTA_PROVEEDOR_PREFIX = "[AVISO] Proveedor"

# ------------------------------------------------------------------ #
# Scoring por obra+familia (jul 2026). Mismo espiritu que el selector
# determinista de contratos: el ganador necesita un minimo de puntos y
# un margen claro sobre el segundo; si no, decide el humano.
# ------------------------------------------------------------------ #
_PUNTOS_MINIMOS = 3
_MARGEN_MINIMO = 2
# El score de nombre (0..1) aporta hasta 4 puntos (nombre exacto = 4).
_PUNTOS_NOMBRE_MAX = 4
# Cada familia comun albaran<->contratos del proveedor aporta 3 puntos.
_PUNTOS_POR_FAMILIA = 3
# Penalizacion si el proveedor tiene familias claras y NINGUNA coincide.
_PENALIZACION_OTRA_FAMILIA = 2

# Origen del CIF cuando la deduccion vino por familia+obra (nombre por
# debajo del umbral). OJO: la columna proveedor_cif_origen es VARCHAR(24);
# el valor debe caber. sv4 lo penaliza en la confianza (factor 0.5).
ORIGEN_DET_FAMILIA_OBRA = "det_familia_obra"


def _norm(value: str | None) -> str:
    """minusculas, sin acentos, espacios colapsados."""
    s = (value or "").lower()
    nfkd = unicodedata.normalize("NFD", s)
    ascii_ = "".join(c for c in nfkd if not unicodedata.combining(c))
    return " ".join(ascii_.split())


def _match_score(q_norm: str, cand_norm: str) -> float:
    """Mismo criterio que el desplegable de sv4:
    1.0 si uno contiene al otro; si no, fraccion de tokens (>=3 letras)
    de la consulta presentes en el candidato.
    """
    if not q_norm or not cand_norm:
        return 0.0
    if cand_norm.find(q_norm) != -1 or q_norm.find(cand_norm) != -1:
        return 1.0
    toks = [t for t in q_norm.split() if len(t) >= 3]
    if not toks:
        return 0.0
    hits = sum(1 for t in toks if t in cand_norm)
    return hits / len(toks)


# ------------------------------------------------------------------ #
# Red de PROVEEDOR por CIF (ago 2026, F-002).
# ------------------------------------------------------------------ #
#: Signos que separan palabras en una razon social pero que _norm no
#: toca ("HORPRESOL, S.L." -> tokens "horpresol," y "s.l."). Sin esto,
#: comparar razones sociales con puntuacion da 0 por un detalle
#: tipografico.
_PUNTUACION_RAZON = str.maketrans({c: " " for c in ",.;:()[]-/\\\"'"})


def _score_razon_social(leido: str | None, candidato: str | None) -> float:
    """Parecido entre el nombre LEIDO y una razon social candidata.

    Dos diferencias con ``_match_score`` a secas, ambas necesarias para
    el caso de referencia de R9 ("GRUPO OTTO HORPRESOL" en el logotipo
    frente a "HORPRESOL, S.L." en el maestro):

      1. Es SIMETRICO. Lo que describe la feature es que el nombre leido
         CONTENGA a un proveedor con contrato, y ese sentido (tokens del
         candidato presentes en lo leido) es el que puntua alto cuando el
         albaran trae la marca comercial del grupo por delante.
      2. Trata la puntuacion como separador, para que "S.L." no arrastre
         el score a cero.

    Se usa SOLO en esta red: los caminos previos del resolver siguen con
    ``_match_score`` tal cual, sin cambio de comportamiento.
    """
    a = _norm((leido or "").translate(_PUNTUACION_RAZON))
    b = _norm((candidato or "").translate(_PUNTUACION_RAZON))
    if not a or not b:
        return 0.0
    return max(_match_score(a, b), _match_score(b, a))


def _distancia_edicion(a: str, b: str) -> int:
    """Distancia de Levenshtein (inserciones, borrados y sustituciones).

    F-062 · R4: desempata entre candidatos claros por cercania al CIF
    leido. Pura y sin dependencias: los CIF tienen 9 caracteres.
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


# ------------------------------------------------------------------ #
# Motivo de la red por nombre (F-052 · design §5 y §6). Sin propuesta,
# la nota de revision dice POR QUE: no es lo mismo que la consulta falle
# que que nadie case.
# ------------------------------------------------------------------ #
MOTIVO_PROPUESTA = "propuesta"
MOTIVO_NADIE_CASA = "nadie_casa"
MOTIVO_SIN_OBRA = "sin_obra"
MOTIVO_SIN_NOMBRE = "sin_nombre"
MOTIVO_CONSULTA_FALLIDA = "consulta_fallida"

# ------------------------------------------------------------------ #
# Candidato claro (F-062 · R4): por que se aplica. Va en la nota.
# ------------------------------------------------------------------ #
VIA_UNICO = "unico"
VIA_CIF_CERCANO = "cif_cercano"


def _motivo_sin_propuesta(
    motivo: str,
    *,
    n_candidatos: int,
    obra: str | None,
    nombre_leido: str | None,
) -> str:
    """Texto que sigue a «el CIF leido X no existe en Sigrid» cuando no
    hay propuesta (R15–R18)."""
    if motivo == MOTIVO_CONSULTA_FALLIDA:
        return (
            "y no se pudo consultar la lista de proveedores de la obra "
            f"{obra} (fallo al consultar Sigrid): no hay propuesta"
        )
    if motivo == MOTIVO_SIN_OBRA:
        return "y no hay obra válida con la que buscar candidatos"
    if motivo == MOTIVO_SIN_NOMBRE:
        return "y no se leyó nombre de proveedor con el que comparar"
    return (
        f"y ninguno de los {n_candidatos} proveedores con contrato en la "
        f"obra {obra} casa con el nombre leído ('{nombre_leido}')"
    )


class _CandidatoObra:
    """Candidato puntuado (proveedor con contrato en la obra)."""

    __slots__ = ("cif", "nombre", "familias", "score_nombre", "puntos")

    def __init__(
        self,
        *,
        cif: str,
        nombre: str | None,
        familias: set[str],
        score_nombre: float,
        puntos: int,
    ) -> None:
        self.cif = cif
        self.nombre = nombre
        self.familias = familias
        self.score_nombre = score_nombre
        self.puntos = puntos

    def etiqueta(self) -> str:
        fams = ",".join(sorted(self.familias)) or "-"
        return f"{self.cif} — {self.nombre or '?'} ({fams})"


class HeaderResolverService:
    """Resolucion DETERMINISTA de cabecera.

    Cuando la 1a fase IA no fijo ``obra_codigo`` y/o ``proveedor_cif``,
    los deduce:

      - OBRA: por NOMBRE + DIRECCION contra Sigrid (igual que siempre).
      - PROVEEDOR, en dos pasos (jul 2026):
          1) Proveedores CON CONTRATO en la obra efectiva (la de la IA o
             la recien deducida): se puntua NOMBRE (hasta 4 puntos) +
             FAMILIA de producto del albaran vs familia de sus contratos
             (+3 por familia comun; -2 si contradice). Con senal fuerte y
             unica se fija el CIF:
               * si el nombre supera el umbral -> origen 'deterministic'
                 (comportamiento clasico, factor 0.6 en confianza sv4);
               * si gana por familia (nombre debil) -> origen
                 'det_familia_obra' + AVISO en review_notes (sv4 lo
                 penaliza con factor 0.5).
             Si hay ambiguedad: NO se fija y se deja un AVISO con los
             candidatos de la obra para que el revisor elija rapido.
          2) Fallback global por nombre contra todos los proveedores con
             contrato (comportamiento previo, umbral ``min_score``).

    Lo resuelto se persiste en el merge marcado con su origen
    (``deterministic`` / ``det_familia_obra`` vs ``ia`` para lo que ya
    trajo la IA), para que la valoracion de confianza sepa de donde
    salio cada dato.

    Best-effort: cualquier fallo se loguea y NO rompe el pipeline.
    """

    def __init__(
        self,
        *,
        obra_client: ObraReverseLookupClient,
        proveedor_client: ProveedorReverseLookupClient,
        repository: HeaderMergeRepository,
        min_score: float = 0.5,
        enabled: bool = True,
        familia_enabled: bool = True,
        nota_max_candidatos: int = 5,
        cif_enabled: bool = True,
        correccion_enabled: bool = True,
        correccion_score_min: float = 1.0,
        correccion_margen_distancia: int = 2,
    ) -> None:
        self._obra_client = obra_client
        self._proveedor_client = proveedor_client
        self._repository = repository
        self._min_score = float(min_score)
        self._enabled = enabled
        self._familia_enabled = bool(familia_enabled)
        self._nota_max_candidatos = max(1, int(nota_max_candidatos))
        self._cif_enabled = bool(cif_enabled)
        # F-062: la red APLICA el candidato claro (interruptor de vuelta
        # atras: con False, D3 de F-002 tal cual).
        self._correccion_enabled = bool(correccion_enabled)
        self._correccion_score_min = float(correccion_score_min)
        self._correccion_margen = int(correccion_margen_distancia)
        logger.info(
            "%s INSTANCIADO (enabled=%s min_score=%s familia=%s cif=%s "
            "correccion=%s score_min=%s margen=%s)",
            _LOG_PREFIX, enabled, self._min_score, self._familia_enabled,
            self._cif_enabled, self._correccion_enabled,
            self._correccion_score_min, self._correccion_margen,
        )

    def resolve_merge_document(self, *, merge_document_id: str) -> None:
        if not self._enabled:
            logger.info("%s DESHABILITADO. document_id=%s",
                        _LOG_PREFIX, merge_document_id)
            return

        hdr = self._repository.get_merge_header_for_resolution(
            document_id=merge_document_id,
        )
        if hdr is None:
            logger.warning("%s sin cabecera. document_id=%s",
                           _LOG_PREFIX, merge_document_id)
            return

        obra_codigo_det = self._resolve_obra(hdr.obra_codigo,
                                             hdr.obra_nombre,
                                             hdr.obra_direccion)
        # Obra EFECTIVA para el paso de proveedor: la recien deducida o
        # la que ya trajo la IA (si normaliza).
        obra_efectiva = (
            obra_codigo_det or normalizar_codigo_obra(hdr.obra_codigo)
        )
        proveedor_cif_det, proveedor_origen = self._resolve_proveedor(
            proveedor_cif=hdr.proveedor_cif,
            proveedor_nombre=hdr.proveedor_nombre,
            obra_codigo_efectiva=obra_efectiva,
            merge_document_id=merge_document_id,
            proveedor_cif_origen=hdr.proveedor_cif_origen,
        )

        # Siempre llamamos al repo: ademas de escribir lo resuelto,
        # marca origen='ia' cuando el dato ya venia de la IA (origen NULL).
        try:
            self._repository.update_merge_resolved_header(
                document_id=merge_document_id,
                obra_codigo_det=obra_codigo_det,
                proveedor_cif_det=proveedor_cif_det,
                proveedor_origen=proveedor_origen,
            )
        except Exception:
            logger.exception(
                "%s error persistiendo resolucion. document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )
            return

        logger.info(
            "%s OK document_id=%s obra_codigo_det=%r proveedor_cif_det=%r "
            "origen=%s",
            _LOG_PREFIX, merge_document_id,
            obra_codigo_det, proveedor_cif_det,
            proveedor_origen if proveedor_cif_det else "-",
        )

    # ----------------------------------------------------------------- #
    # OBRA
    # ----------------------------------------------------------------- #
    def _resolve_obra(
        self,
        obra_codigo: str | None,
        obra_nombre: str | None,
        obra_direccion: str | None,
    ) -> str | None:
        """Devuelve el codigo de obra deducido por texto, o None si ya
        habia codigo valido / no hay texto / no llega al umbral."""
        if obra_codigo and normalizar_codigo_obra(obra_codigo) is not None:
            return None  # la IA ya trajo un codigo valido
        textos = [t for t in (obra_nombre, obra_direccion) if (t or "").strip()]
        if not textos:
            return None
        try:
            candidatos = self._obra_client.search_obras()
        except Exception:
            logger.exception("%s search_obras fallo.", _LOG_PREFIX)
            return None
        if not candidatos:
            return None

        queries = [_norm(t) for t in textos]
        best: ObraEnrichmentResult | None = None
        best_score = 0.0
        for cand in candidatos:
            cand_text = _norm(
                " ".join(
                    p for p in (cand.nombre_obra, cand.direccion_completa) if p
                )
            )
            score = max((_match_score(q, cand_text) for q in queries),
                        default=0.0)
            if score > best_score:
                best_score = score
                best = cand
        if best is not None and best_score >= self._min_score:
            logger.info(
                "%s obra resuelta por texto: codigo=%s score=%.2f",
                _LOG_PREFIX, best.codigo_obra, best_score,
            )
            return (best.codigo_obra or "").strip() or None
        logger.info(
            "%s obra NO resuelta (mejor score=%.2f < %.2f).",
            _LOG_PREFIX, best_score, self._min_score,
        )
        return None

    # ----------------------------------------------------------------- #
    # PROVEEDOR
    # ----------------------------------------------------------------- #
    def _resolve_proveedor(
        self,
        *,
        proveedor_cif: str | None,
        proveedor_nombre: str | None,
        obra_codigo_efectiva: str | None,
        merge_document_id: str,
        proveedor_cif_origen: str | None = None,
    ) -> tuple[str | None, str]:
        """Devuelve ``(cif_deducido | None, origen)``.

        ``origen`` solo es relevante cuando hay CIF deducido:
        'deterministic' (nombre supera umbral) o 'det_familia_obra'
        (decidio la familia con nombre debil).
        """
        cif_leido = (proveedor_cif or "").strip()
        if cif_leido:
            # CIF ya presente (IA o revisor): si quedo un aviso de
            # candidatos de un intento anterior, se retira para no
            # contradecir lo que ve el revisor.
            self._remove_nota_proveedor_safely(merge_document_id)
            # RED DE PROVEEDOR (F-002, R8-R10): el CIF manda, pero hay
            # que comprobarlo contra el maestro prv.
            # (F-062) Con candidato claro, la red APLICA el proveedor en el
            # merge ANTES de que el pipeline busque contratos, que leen el
            # CIF del merge: no hay nada que devolver al llamador.
            self._red_proveedor_por_cif(
                cif_leido=cif_leido,
                proveedor_nombre=proveedor_nombre,
                obra_codigo_efectiva=obra_codigo_efectiva,
                merge_document_id=merge_document_id,
                origen=proveedor_cif_origen,
            )
            return None, "deterministic"

        # Paso 1 (jul 2026) — candidatos con contrato en la obra,
        # puntuados por nombre + familia de producto.
        if self._familia_enabled and obra_codigo_efectiva:
            cif, origen = self._resolver_por_obra_y_familia(
                proveedor_nombre=proveedor_nombre,
                obra_codigo=obra_codigo_efectiva,
                merge_document_id=merge_document_id,
            )
            if cif:
                return cif, origen

        # Paso 2 — fallback global por nombre (comportamiento clasico).
        if not (proveedor_nombre or "").strip():
            return None, "deterministic"
        try:
            proveedores = self._proveedor_client.search_proveedores()
        except Exception:
            logger.exception("%s search_proveedores fallo.", _LOG_PREFIX)
            return None, "deterministic"
        if not proveedores:
            return None, "deterministic"

        q = _norm(proveedor_nombre)
        best_cif: str | None = None
        best_score = 0.0
        for cif, nombre in proveedores:
            score = _match_score(q, _norm(nombre))
            if score > best_score:
                best_score = score
                best_cif = cif
        if best_cif and best_score >= self._min_score:
            logger.info(
                "%s proveedor resuelto por texto (global): cif=%s score=%.2f",
                _LOG_PREFIX, best_cif, best_score,
            )
            self._remove_nota_proveedor_safely(merge_document_id)
            return (best_cif.strip() or None), "deterministic"
        logger.info(
            "%s proveedor NO resuelto (mejor score global=%.2f < %.2f).",
            _LOG_PREFIX, best_score, self._min_score,
        )
        return None, "deterministic"

    # ----------------------------------------------------------------- #
    # RED DE PROVEEDOR POR CIF (F-002 · R8, R9, R10)
    # ----------------------------------------------------------------- #
    def _red_proveedor_por_cif(
        self,
        *,
        cif_leido: str,
        proveedor_nombre: str | None,
        obra_codigo_efectiva: str | None,
        merge_document_id: str,
        origen: str | None = None,
    ) -> None:
        """Contrasta el CIF leido con el maestro ``prv`` de Sigrid.

          - Existe -> ``proveedor_nombre`` pasa a ser la razon social
            canonica (R8 de F-002) y se retiran los motivos de proveedor
            caducados (F-062 · R15, R16). Un CIF que existe nunca se
            sustituye (R13).
          - No existe y hay CANDIDATO CLARO en la obra (F-062 · R3–R5) ->
            se APLICA: CIF y razon social de Sigrid en el merge, a revision
            con motivo ``proveedor_cif_corregido:<leido>><aplicado>`` y nota
            ``[CORREGIDO] Proveedor`` (R6, R7). Salvo origen ``manual``
            (R13) o ``RED_PROVEEDOR_CORRECCION_ENABLED=false`` (R12).
          - No existe y no hay candidato claro -> como antes de F-062: se
            marca revision con motivo ``proveedor_cif_no_casa:<cif>`` y la
            nota PROPONE el mejor por nombre si lo hay (R9/R10 de F-002,
            F-052); si el control del leido no es valido, la nota lo dice
            (F-062 · R11).

        Con la correccion apagada, exactamente D3 de F-002: se propone y no
        se sobrescribe nada. Best-effort completo (R16 de F-002).
        """
        if not self._cif_enabled:
            logger.info(
                "%s RED DE PROVEEDOR desactivada "
                "(RED_PROVEEDOR_CIF_ENABLED=false). document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )
            return

        try:
            encontrado = self._proveedor_client.fetch_proveedor_by_cif(
                cif=cif_leido,
            )
        except Exception:
            # Un fallo de red NO es un CIF inexistente: no se marca nada.
            logger.exception(
                "%s fetch_proveedor_by_cif fallo cif=%s; el documento "
                "queda como estaba.", _LOG_PREFIX, cif_leido,
            )
            return

        if encontrado is not None:
            _, razon_social = encontrado
            self._canonizar_nombre_safely(
                merge_document_id=merge_document_id,
                razon_social=razon_social,
                cif_leido=cif_leido,
            )
            if self._correccion_enabled:
                self._retirar_motivos_safely(
                    merge_document_id=merge_document_id, cif_actual=cif_leido,
                )
            return

        puntuados, motivo = self._candidatos_puntuados(
            proveedor_nombre=proveedor_nombre, obra=obra_codigo_efectiva,
        )
        control_invalido = not identificador_fiscal_valido(cif_leido)
        if self._correccion_enabled:
            if self._aplicar_candidato_claro(
                cif_leido=cif_leido,
                proveedor_nombre=proveedor_nombre,
                obra=obra_codigo_efectiva,
                merge_document_id=merge_document_id,
                origen=origen,
                puntuados=puntuados,
                control_invalido=control_invalido,
            ):
                return
            # R15: una correccion anterior que ya no es el CIF del merge.
            self._retirar_motivos_safely(
                merge_document_id=merge_document_id, cif_actual=cif_leido,
            )

        candidato = self._mejor_de(
            puntuados, motivo=motivo, obra=obra_codigo_efectiva,
        )
        cabeza = (
            f"{_NOTA_PROVEEDOR_PREFIX} el CIF leido {cif_leido} no "
            "existe en Sigrid"
        )
        if candidato is not None:
            nota = (
                f"{cabeza}. PROPUESTA: {candidato.cif} — "
                f"{candidato.nombre or '?'}, con contrato en la obra "
                f"{obra_codigo_efectiva} y nombre parecido al leido "
                f"('{proveedor_nombre or '—'}'). Confirmala o corrigela "
                "en el portal."
            )
        else:
            # F-052 · R15–R18: la nota dice POR QUE no hay propuesta. Una
            # consulta fallida nunca se cuenta como «nadie casa».
            nota = (
                f"{cabeza} "
                + _motivo_sin_propuesta(
                    motivo,
                    n_candidatos=len(puntuados),
                    obra=obra_codigo_efectiva,
                    nombre_leido=proveedor_nombre,
                )
                + ". Revisa el proveedor en el portal."
            )
        if self._correccion_enabled and control_invalido:
            # F-062 · R11. Al FINAL: las consultas de vigilancia del humano
            # buscan «no existe en Sigrid. PROPUESTA:» tal cual.
            nota += (
                f" El carácter de control del CIF leído {cif_leido} no es "
                "válido: es una lectura errónea."
            )
        self._marcar_revision_safely(
            merge_document_id=merge_document_id,
            motivo=f"{MOTIVO_PROVEEDOR_NO_CASA}{cif_leido}",
            nota=nota,
        )

    def _aplicar_candidato_claro(
        self,
        *,
        cif_leido: str,
        proveedor_nombre: str | None,
        obra: str | None,
        merge_document_id: str,
        origen: str | None,
        puntuados: list[tuple[ProveedorObraResumen, float]],
        control_invalido: bool,
    ) -> bool:
        """Aplica el candidato claro si lo hay (F-062 · R6, R7, R13).

        Devuelve ``True`` solo si quedo aplicado; si no hay candidato, el
        revisor fijo el CIF (``manual``) o la escritura falla, ``False`` y
        la red sigue como antes de F-062.
        """
        if (origen or "").strip() == "manual":
            logger.info(
                "%s CIF %s fijado por el revisor (origen manual): no se "
                "corrige. document_id=%s", _LOG_PREFIX, cif_leido,
                merge_document_id,
            )
            return False
        candidato, via = self._candidato_claro(
            cif_leido=cif_leido, puntuados=puntuados,
        )
        if candidato is None:
            return False
        cif = normalizar_cif(candidato.cif)
        nombre = (candidato.nombre or "").strip()
        por_que = (
            "es el único candidato" if via == VIA_UNICO
            else "es el candidato con el CIF más cercano al leído"
        )
        control = (
            " y el carácter de control del CIF leído no es válido "
            "(lectura errónea)" if control_invalido else ""
        )
        nota = (
            f"{NOTA_PROVEEDOR_CORREGIDO_PREFIJO}: leído {cif_leido} → {cif} "
            f"({nombre}). Nombre leído: '{proveedor_nombre or '—'}'. El CIF "
            f"leído no existe en Sigrid{control}; se aplica porque {por_que} "
            f"con contrato en la obra {obra} y nombre completo. Si no es el "
            "proveedor, cámbialo con «Elegir proveedor»."
        )
        try:
            self._repository.aplicar_correccion_proveedor(
                document_id=merge_document_id,
                cif=cif,
                nombre=nombre,
                motivo=f"{MOTIVO_PROVEEDOR_CORREGIDO}{cif_leido}>{cif}",
                nota=nota,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo aplicar el proveedor %s; se marca revision "
                "como antes. document_id=%s", _LOG_PREFIX, cif,
                merge_document_id,
            )
            return False
        logger.warning(
            "%s proveedor CORREGIDO %s -> %s (%s, via=%s, control_leido=%s) "
            "obra=%s document_id=%s", _LOG_PREFIX, cif_leido, cif, nombre,
            via, "invalido" if control_invalido else "valido", obra,
            merge_document_id,
        )
        return True

    def _retirar_motivos_safely(
        self, *, merge_document_id: str, cif_actual: str,
    ) -> None:
        try:
            self._repository.retirar_motivos_proveedor(
                document_id=merge_document_id, cif_actual=cif_actual,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudieron retirar los motivos de proveedor "
                "caducados. document_id=%s", _LOG_PREFIX, merge_document_id,
            )

    def _mejor_candidato_por_nombre(
        self,
        *,
        proveedor_nombre: str | None,
        obra_codigo_efectiva: str | None,
    ) -> tuple[ProveedorObraResumen | None, str, int]:
        """Proveedor con contrato en la obra cuyo nombre casa con el
        leido por encima del umbral, con el motivo y el numero de
        candidatos (F-052 · design §5):

          - ``(candidato, 'propuesta', n)``: alguno llega al umbral.
          - ``(None, 'nadie_casa', n)``: la consulta funciono y ninguno
            de los ``n`` proveedores devueltos llega al umbral.
          - ``(None, 'sin_obra', 0)``: no hay obra efectiva (manda sobre
            la falta de nombre: sin obra no hay lista que comparar).
          - ``(None, 'sin_nombre', 0)``: no se leyo nombre.
          - ``(None, 'consulta_fallida', 0)``: la consulta lanzo (red,
            HTTP, ``ok=false``, truncado, error de ``FOR XML``).
        """
        puntuados, motivo = self._candidatos_puntuados(
            proveedor_nombre=proveedor_nombre, obra=obra_codigo_efectiva,
        )
        return (
            self._mejor_de(puntuados, motivo=motivo, obra=obra_codigo_efectiva),
            motivo,
            len(puntuados),
        )

    def _candidatos_puntuados(
        self,
        *,
        proveedor_nombre: str | None,
        obra: str | None,
    ) -> tuple[list[tuple[ProveedorObraResumen, float]], str]:
        """Proveedores con contrato en la obra, cada uno con su score de
        nombre frente al leido, y el motivo de F-052 (design §5).

        Es la UNICA llamada a ``fetch_contratos_resumen_por_obra`` de la
        pasada de la red (F-062 · design §5.2): de ella salen la propuesta
        de F-052 y el candidato claro de F-062. Sin obra, sin nombre o con
        la consulta fallida (incluido el truncado) la lista va vacia.
        """
        if not obra:
            return [], MOTIVO_SIN_OBRA
        if not (proveedor_nombre or "").strip():
            return [], MOTIVO_SIN_NOMBRE
        try:
            resumenes = list(
                self._proveedor_client.fetch_contratos_resumen_por_obra(
                    codigo_obra=obra,
                ) or []
            )
        except Exception:
            logger.exception(
                "%s fetch_contratos_resumen_por_obra fallo obra=%s; la "
                "propuesta se omite.", _LOG_PREFIX, obra,
            )
            return [], MOTIVO_CONSULTA_FALLIDA
        puntuados = [
            (resumen, _score_razon_social(proveedor_nombre, resumen.nombre))
            for resumen in resumenes
        ]
        mejor_score = max((score for _, score in puntuados), default=0.0)
        if mejor_score > 0.0 and mejor_score >= self._min_score:
            return puntuados, MOTIVO_PROPUESTA
        return puntuados, MOTIVO_NADIE_CASA

    def _mejor_de(
        self,
        puntuados: list[tuple[ProveedorObraResumen, float]],
        *,
        motivo: str,
        obra: str | None,
    ) -> ProveedorObraResumen | None:
        """La propuesta de F-052: el de mayor score; ante un empate, el
        primero (la propuesta tiene que ser estable entre pasadas)."""
        mejor: ProveedorObraResumen | None = None
        mejor_score = 0.0
        for resumen, score in puntuados:
            if score > mejor_score:
                mejor_score = score
                mejor = resumen
        if motivo == MOTIVO_PROPUESTA:
            logger.info(
                "%s candidato de proveedor por nombre: cif=%s score=%.2f "
                "obra=%s", _LOG_PREFIX, mejor.cif, mejor_score, obra,
            )
            return mejor
        if motivo == MOTIVO_NADIE_CASA:
            logger.info(
                "%s ningun candidato de la obra %s casa con el nombre leido "
                "(mejor score=%.2f < %.2f, %d candidatos).",
                _LOG_PREFIX, obra, mejor_score, self._min_score,
                len(puntuados),
            )
        return None

    def _candidato_claro(
        self,
        *,
        cif_leido: str,
        puntuados: list[tuple[ProveedorObraResumen, float]],
    ) -> tuple[ProveedorObraResumen | None, str | None]:
        """Candidato claro de la obra (F-062 · R3, R4, R5) y por que.

        Elegibles: identificador fiscal valido y ``score >=
        correccion_score_min``, agrupados por CIF normalizado (dos filas
        del mismo CIF son un candidato, no un empate). Uno solo ⇒
        ``(el, 'unico')``. Varios ⇒ el de CIF mas cercano al leido, si su
        distancia es al menos ``correccion_margen_distancia`` menor que la
        del siguiente ⇒ ``(el, 'cif_cercano')``. Si no, ``(None, None)``.
        La distancia solo desempata y el control del leido no cuenta (R5).
        """
        elegibles: dict[str, ProveedorObraResumen] = {}
        for resumen, score in puntuados:
            cif = normalizar_cif(resumen.cif)
            if (
                cif is None
                or cif in elegibles
                or score < self._correccion_score_min
                or not identificador_fiscal_valido(cif)
            ):
                continue
            elegibles[cif] = resumen
        if not elegibles:
            return None, None
        if len(elegibles) == 1:
            [unico] = elegibles.values()
            return unico, VIA_UNICO
        leido = normalizar_cif(cif_leido) or ""
        por_distancia = sorted(
            (_distancia_edicion(leido, cif), cif) for cif in elegibles
        )
        (primera, cif_primero), (segunda, _) = por_distancia[0], por_distancia[1]
        if segunda - primera >= self._correccion_margen:
            return elegibles[cif_primero], VIA_CIF_CERCANO
        logger.info(
            "%s %d candidatos elegibles sin margen de CIF (%d frente a %d, "
            "margen %d): no hay candidato claro.", _LOG_PREFIX,
            len(elegibles), primera, segunda, self._correccion_margen,
        )
        return None, None

    def _canonizar_nombre_safely(
        self,
        *,
        merge_document_id: str,
        razon_social: str | None,
        cif_leido: str,
    ) -> None:
        nombre = (razon_social or "").strip()
        if not nombre:
            logger.info(
                "%s CIF %s existe en prv pero sin razon social utilizable; "
                "se conserva el nombre leido.", _LOG_PREFIX, cif_leido,
            )
            return
        try:
            self._repository.set_merge_proveedor_nombre_canonico(
                document_id=merge_document_id,
                nombre=nombre,
            )
            logger.info(
                "%s proveedor canonizado por CIF %s -> %r. document_id=%s",
                _LOG_PREFIX, cif_leido, nombre, merge_document_id,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo canonizar el nombre del proveedor. "
                "document_id=%s", _LOG_PREFIX, merge_document_id,
            )

    def _marcar_revision_safely(
        self, *, merge_document_id: str, motivo: str, nota: str,
    ) -> None:
        try:
            self._repository.marcar_revision_cabecera(
                document_id=merge_document_id,
                motivo=motivo,
                nota=nota,
                nota_prefijo=_NOTA_PROVEEDOR_PREFIX,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo marcar la revision de proveedor. "
                "document_id=%s motivo=%s",
                _LOG_PREFIX, merge_document_id, motivo,
            )

    def _resolver_por_obra_y_familia(
        self,
        *,
        proveedor_nombre: str | None,
        obra_codigo: str,
        merge_document_id: str,
    ) -> tuple[str | None, str]:
        """Puntua los proveedores CON CONTRATO en la obra y decide.

        Devuelve ``(cif, origen)`` si hay ganador claro; ``(None, ...)``
        si no (y en ese caso deja un AVISO con los candidatos si aporta
        informacion util al revisor).
        """
        try:
            resumenes: list[ProveedorObraResumen] = (
                self._proveedor_client.fetch_contratos_resumen_por_obra(
                    codigo_obra=obra_codigo,
                )
            )
        except SigridRespuestaTruncada as exc:
            # F-052 · R6: lista de candidatos INCOMPLETA. No se puntua
            # sobre ella (seria el bug original); se degrada al fallback
            # global por nombre y queda constancia de que obra fue.
            logger.warning(
                "%s fetch_contratos_resumen_por_obra TRUNCADA obra=%s "
                "[%s, %s filas]; se degrada al fallback global por nombre.",
                _LOG_PREFIX, obra_codigo, exc.etiqueta, exc.filas,
            )
            return None, "deterministic"
        except Exception:
            logger.exception(
                "%s fetch_contratos_resumen_por_obra fallo obra=%s; se "
                "degrada al fallback global por nombre.",
                _LOG_PREFIX, obra_codigo,
            )
            return None, "deterministic"
        if not resumenes:
            logger.info(
                "%s obra %s sin proveedores con contrato; paso familia "
                "omitido.", _LOG_PREFIX, obra_codigo,
            )
            return None, "deterministic"

        familias_alb: set[str] = set()
        try:
            filas = self._repository.get_merge_lines_for_scoring(
                document_id=merge_document_id,
            )
            familias_alb = familias_de_filas_merge(filas)
        except Exception:
            logger.exception(
                "%s no se pudieron leer lineas para familia; se sigue "
                "solo con nombre.", _LOG_PREFIX,
            )

        q = _norm(proveedor_nombre)
        candidatos: list[_CandidatoObra] = []
        for r in resumenes:
            fams_prov = familias_de_texto((r.texto or "").lower())
            score_nombre = _match_score(q, _norm(r.nombre)) if q else 0.0
            comunes = familias_alb & fams_prov
            puntos = (
                round(_PUNTOS_NOMBRE_MAX * score_nombre)
                + _PUNTOS_POR_FAMILIA * len(comunes)
            )
            if familias_alb and fams_prov and not comunes:
                puntos -= _PENALIZACION_OTRA_FAMILIA
            candidatos.append(_CandidatoObra(
                cif=r.cif,
                nombre=r.nombre,
                familias=fams_prov,
                score_nombre=score_nombre,
                puntos=puntos,
            ))
            logger.info(
                "%s candidato obra=%s %s -> %s puntos "
                "(nombre=%.2f familias=%s comunes=%s)",
                _LOG_PREFIX, obra_codigo, r.cif, puntos,
                score_nombre, sorted(fams_prov) or "-",
                sorted(comunes) or "-",
            )

        # Atajo por NOMBRE dentro de la obra: si algun candidato supera el
        # umbral clasico, el nombre manda (origen 'deterministic').
        por_nombre = max(candidatos, key=lambda c: c.score_nombre)
        if por_nombre.score_nombre >= self._min_score:
            logger.info(
                "%s proveedor resuelto por NOMBRE dentro de la obra %s: "
                "cif=%s score=%.2f",
                _LOG_PREFIX, obra_codigo, por_nombre.cif,
                por_nombre.score_nombre,
            )
            self._remove_nota_proveedor_safely(merge_document_id)
            return por_nombre.cif, "deterministic"

        # Decision por PUNTOS (nombre debil + familia).
        candidatos.sort(key=lambda c: c.puntos, reverse=True)
        mejor = candidatos[0]
        segundo_puntos = candidatos[1].puntos if len(candidatos) > 1 else -999

        if (
            mejor.puntos >= _PUNTOS_MINIMOS
            and (mejor.puntos - segundo_puntos) >= _MARGEN_MINIMO
        ):
            logger.warning(
                "%s proveedor %s DEDUCIDO por familia+obra (%s puntos, "
                "segundo=%s, nombre=%.2f) obra=%s -> origen=%s",
                _LOG_PREFIX, mejor.cif, mejor.puntos, segundo_puntos,
                mejor.score_nombre, obra_codigo, ORIGEN_DET_FAMILIA_OBRA,
            )
            self._nota_proveedor_safely(
                merge_document_id,
                nota=(
                    f"{_NOTA_PROVEEDOR_PREFIX} {mejor.cif} — "
                    f"{mejor.nombre or '?'} deducido AUTOMATICAMENTE por "
                    "familia de producto "
                    f"({','.join(sorted(mejor.familias & familias_alb)) or '-'}) "
                    f"entre {len(candidatos)} proveedor(es) con contrato "
                    f"en la obra {obra_codigo} "
                    f"(nombre leido: '{proveedor_nombre or '—'}'). "
                    "Verificar que es el correcto."
                ),
            )
            return mejor.cif, ORIGEN_DET_FAMILIA_OBRA

        # Ambiguo o sin senal suficiente: NO se fija, pero si hay algo que
        # contar (candidatos en la obra), se deja el AVISO con el top-N
        # para que el revisor elija rapido en el portal.
        logger.info(
            "%s proveedor NO deducido por familia+obra (mejor=%s puntos, "
            "segundo=%s, minimo=%s, margen=%s).",
            _LOG_PREFIX, mejor.puntos, segundo_puntos,
            _PUNTOS_MINIMOS, _MARGEN_MINIMO,
        )
        top = candidatos[: self._nota_max_candidatos]
        listado = "; ".join(c.etiqueta() for c in top)
        self._nota_proveedor_safely(
            merge_document_id,
            nota=(
                f"{_NOTA_PROVEEDOR_PREFIX} sin CIF: no deducible con "
                f"seguridad. Candidatos con contrato en la obra "
                f"{obra_codigo}: {listado}. Corrige el proveedor arriba "
                "y pulsa \"Guardar y volver a buscar\"."
            ),
        )
        return None, "deterministic"

    # ----------------------------------------------------------------- #
    # Notas de revision (best-effort, con dedupe por prefijo)
    # ----------------------------------------------------------------- #
    def _nota_proveedor_safely(self, merge_document_id: str, *, nota: str) -> None:
        try:
            self._repository.remove_review_note_prefix(
                document_id=merge_document_id,
                prefijo=_NOTA_PROVEEDOR_PREFIX,
            )
            self._repository.append_review_note(
                document_id=merge_document_id,
                nota=nota,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo dejar la nota de proveedor. document_id=%s",
                _LOG_PREFIX, merge_document_id,
            )

    def _remove_nota_proveedor_safely(self, merge_document_id: str) -> None:
        try:
            self._repository.remove_review_note_prefix(
                document_id=merge_document_id,
                prefijo=_NOTA_PROVEEDOR_PREFIX,
            )
        except Exception:  # noqa: BLE001 — best-effort
            logger.exception(
                "%s no se pudo retirar el aviso de proveedor. "
                "document_id=%s", _LOG_PREFIX, merge_document_id,
            )
