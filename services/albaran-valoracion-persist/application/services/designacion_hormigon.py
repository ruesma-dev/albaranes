# application/services/designacion_hormigon.py
"""Parser DETERMINISTA de la designacion espanola de hormigon.

(jul 2026, feedback JO sobre albaran Horpresol HA-25/B/12/XC2/F/P)

La nomenclatura es POSICIONAL — la MISMA letra cambia de significado
segun donde aparezca:

    TT-RR / C / AA / EXP [/ EXTRA ...]

    - TT-RR: tipo (HM masa / HA armado / HP pretensado) y resistencia
      caracteristica en N/mm2 (HA-25).
    - C (2a posicion): consistencia — S=Seca, P=Plastica, B=Blanda,
      F=Fluida, L=Liquida.
    - AA (3a): tamano maximo de arido en mm (12, 20, 40...).
    - EXP (4a): clase(s) de exposicion — romanas EHE (I, IIa..IIIc,
      IV, Qa-Qc, H, E, F) o europeas (XC1-4, XD, XS, XF, XA),
      combinables con '+'.
    - EXTRAS tras la exposicion: F = hormigon FRATASADO (suelos
      pulidos: garajes, pistas...), P = FIBRAS DE POLIPROPILENO.
      Suelen ir juntos (/F/P). Aqui F NO es fluida y P NO es
      plastica.

Ambiguedad conocida: una 'F' suelta tras el arido SIN otra clase de
exposicion delante puede ser el ambiente F (heladas, EHE clasica). En
ese caso el parser la clasifica como EXPOSICION (conservador: no
inventa un fratasado) y lo anota en ``notas``. La F que va DETRAS de
una exposicion ya reconocida se interpreta como FRATASADO.

Modulo puro (sin I/O) para que la red determinista del builder y los
tests lo usen sin dependencias.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Consistencias validas en 2a posicion y su nombre canonico.
NOMBRE_CONSISTENCIA: dict[str, str] = {
    "S": "SECA",
    "P": "PLASTICA",
    "B": "BLANDA",
    "F": "FLUIDA",
    "L": "LIQUIDA",
}

# Consistencias que generan incremento de precio (feedback jul 2026):
# F (fluida, lleva aditivo), L (liquida) y S (seca). B y P son el
# estandar incluido en el precio base (P cuesta lo mismo que B).
CONSISTENCIAS_CON_INCREMENTO: frozenset[str] = frozenset({"F", "L", "S"})

_RE_DESIGNACION = re.compile(
    r"\b(HM|HA|HP)\s*-?\s*(\d{2,3})((?:\s*/\s*[A-Z0-9+]{1,10}){0,8})",
)
_RE_EXPO_EUROPEA = re.compile(r"^X[A-Z]{1,2}\d?$")
_RE_EXPO_ROMANA = re.compile(r"^(I{1,3}[ABC]?|IV)$")
_RE_EXPO_ESPECIAL = re.compile(r"^(Q[ABC]|E|H)$")
_RE_SULFORRESISTENTE = re.compile(r"SULFO\s*-?\s*RESISTENTE|SULFORRESISTENTE")
_RE_SR_PALABRA = re.compile(r"\bSR\b")


def normalizar_texto(texto: str | None) -> str:
    """Mayusculas, sin acentos (N~ -> N), espacios colapsados."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", texto)
    ascii_ = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_.upper()).strip()


def _es_exposicion(seg: str) -> bool:
    """True si el segmento es una clase de exposicion (o combo '+')."""
    partes = [p for p in seg.split("+") if p]
    if not partes:
        return False
    for parte in partes:
        if (
            _RE_EXPO_EUROPEA.match(parte)
            or _RE_EXPO_ROMANA.match(parte)
            or _RE_EXPO_ESPECIAL.match(parte)
        ):
            continue
        # 'F' (heladas EHE) solo cuenta como exposicion dentro de un
        # combo con '+': "IIA+F". Suelta se decide por posicion fuera.
        if parte == "F" and len(partes) > 1:
            continue
        return False
    return True


@dataclass(frozen=True)
class DesignacionHormigon:
    """Desglose posicional de una designacion de hormigon."""

    texto: str
    tipo: str
    resistencia: int | None = None
    consistencia: str | None = None
    arido_mm: int | None = None
    exposicion: tuple[str, ...] = ()
    fratasado: bool = False
    fibras_polipropileno: bool = False
    extras: tuple[str, ...] = ()
    notas: tuple[str, ...] = ()

    @property
    def consistencia_nombre(self) -> str | None:
        if self.consistencia is None:
            return None
        return NOMBRE_CONSISTENCIA.get(self.consistencia)


def parsear_designacion_hormigon(
    texto: str | None,
) -> DesignacionHormigon | None:
    """Primera designacion encontrada en ``texto``, desglosada.

    Devuelve None si no hay ninguna designacion reconocible.
    """
    norm = normalizar_texto(texto)
    m = _RE_DESIGNACION.search(norm)
    if not m:
        return None

    tipo = m.group(1)
    resistencia = int(m.group(2))
    cola = m.group(3) or ""
    segmentos = [s.strip() for s in cola.split("/") if s.strip()]

    consistencia: str | None = None
    arido: int | None = None
    exposicion: list[str] = []
    fratasado = False
    fibras = False
    extras: list[str] = []
    notas: list[str] = []

    for seg in segmentos:
        # 2a posicion: consistencia (solo antes de arido/exposicion).
        if (
            consistencia is None
            and arido is None
            and not exposicion
            and seg in NOMBRE_CONSISTENCIA
        ):
            consistencia = seg
            continue
        # 3a posicion: arido en mm.
        if arido is None and seg.isdigit():
            valor = int(seg)
            if 4 <= valor <= 99:
                arido = valor
                continue
        # 4a posicion (una o varias): clase(s) de exposicion.
        if _es_exposicion(seg) and not fratasado and not fibras:
            exposicion.append(seg)
            continue
        # 'F' suelta SIN exposicion previa: ambiente F (heladas) EHE.
        # Conservador: no inventamos un fratasado; se anota la duda.
        if seg == "F" and not exposicion:
            exposicion.append("F")
            notas.append(
                "F tras el arido sin otra exposicion: interpretada "
                "como ambiente F (heladas), no como fratasado"
            )
            continue
        # EXTRAS tras la exposicion: F=fratasado, P=fibras.
        if seg == "F":
            fratasado = True
            continue
        if seg == "P":
            fibras = True
            continue
        extras.append(seg)

    return DesignacionHormigon(
        texto=m.group(0).replace(" ", ""),
        tipo=tipo,
        resistencia=resistencia,
        consistencia=consistencia,
        arido_mm=arido,
        exposicion=tuple(exposicion),
        fratasado=fratasado,
        fibras_polipropileno=fibras,
        extras=tuple(extras),
        notas=tuple(notas),
    )


def cemento_es_sr(texto: str | None) -> bool:
    """True si el texto declara cemento sulforresistente (SR).

    Regla (feedback jul 2026): el incremento por cemento especial SOLO
    aplica si el hormigon se fabrica con cemento /SR. "CEM IV/A-(V)
    42.5 R" (sin SR) es cemento normal -> False. Se exige SULFORRES* o
    bien la palabra completa SR junto a un contexto de cemento (CEM)
    para no disparar con siglas incrustadas.

    NEGACIONES (bug real jul 2026): la fase 2 escribe cosas como
    "CEM IV/A-(V) 42.5 R, sin indicacion SR/sulforresistente" — una
    mencion NEGADA no es un cemento SR. Se evalua por frases
    (separadas por . ; :) y una mencion con SIN/NO delante en la
    misma frase se descarta.
    """
    norm = normalizar_texto(texto)
    if not norm:
        return False
    for frase in re.split(r"[.;:]", norm):
        for m in re.finditer(
            r"SULFO\s*-?\s*RESISTENTE|SULFORRESISTENTE|\bSR\b", frase,
        ):
            if m.group(0) == "SR" and "CEM" not in norm:
                continue  # SR suelto sin contexto de cemento
            if re.search(r"\b(SIN|NO)\b", frase[: m.start()]):
                continue  # mencion negada ("sin SR", "no lleva SR")
            return True
    return False
