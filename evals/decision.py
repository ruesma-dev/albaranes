# evals/decision.py
"""Métricas por modelo y criterio de recomendación del comparador (F-083).

Puro. El criterio (design §6) es «acierto primero, coste después», y nada se
decide contra una referencia que no se ha medido en la misma invocación:

1. **Elegible** (R30): 0 `ERROR`, 0 `NO_EJECUTADO` y fallos críticos ≤ los de
   la referencia. Sin referencia completa, la fase queda «sin datos».
2. **Banda de empate** (R31): fallos ≤ mejor + máx(2, 5 % del mejor). El banco
   varía unos 10 fallos entre corridas con el mismo código.
3. **Recomendado** (R32): el más barato por albarán de la banda; si otro cuesta
   menos de un 5 % más, el más rápido de los dos.
4. **Cambiar** (R33) solo si compensa un cambio de producción: mejora clara
   (≤ 0,9 × fallos con coste ≤ 1,5×) o ahorro claro (coste ≤ 0,7×).
5. **Latencia** (R34): aviso si tarda más del doble que la referencia.
6. **Provisional** (R35) con menos de 3 repeticiones.

Los umbrales son los de P6 y se cambian aquí, cada uno con su test.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal

from evals.modelos import ERROR, ROJO, VERDE, ResultadoCaso

#: Estado de un caso que no se llegó a llamar porque se alcanzó el tope (R19).
NO_EJECUTADO = "NO_EJECUTADO"

BANDA_MINIMA = 2
BANDA_RELATIVA = Decimal("0.05")
EMPATE_COSTE = Decimal("0.05")
MEJORA_FALLOS = Decimal("0.9")
MEJORA_COSTE = Decimal("1.5")
AHORRO_COSTE = Decimal("0.7")
LATENCIA = 2
REPETICIONES_FIRMES = 3


@dataclass
class Metricas:
    """Lo que el informe da de un modelo en una fase (R27)."""

    modelo: str
    fase: str
    repeticiones: int = 1
    casos: int = 0
    errores: int = 0
    no_ejecutados: int = 0
    verdes: int = 0
    fallos: Decimal = Decimal(0)
    fallos_min: int = 0
    fallos_max: int = 0
    avisos: int = 0
    tiempo_medio_s: Decimal = Decimal(0)
    tiempo_max_s: Decimal = Decimal(0)
    llamadas: int = 0
    tokens_entrada_medios: Decimal = Decimal(0)
    tokens_salida_medios: Decimal = Decimal(0)
    coste_total: Decimal = Decimal(0)
    coste_por_albaran: Decimal = Decimal(0)
    uso_incompleto: int = 0
    fallos_medidor: int = 0
    modelos_servidos: list[str] = field(default_factory=list)
    motivos_parada: dict[str, int] = field(default_factory=dict)


def _media(total, cuantos: int) -> Decimal:
    return Decimal(total) / cuantos if cuantos else Decimal(0)


def medir(
    modelo: str,
    fase: str,
    casos_por_repeticion: list[list[ResultadoCaso]],
    registros: list[dict],
    etiqueta: str = "candidato",
) -> Metricas:
    """Agrega los casos de cada repetición y los registros del medidor del modelo.

    `registros` son los del modelo en esta fase con su `repeticion`; solo
    cuentan los de `etiqueta`: los de preparación se miden aparte (R27).
    """
    fallos_por_rep = []
    metricas = Metricas(modelo=modelo, fase=fase, repeticiones=len(casos_por_repeticion))
    for casos in casos_por_repeticion:
        evaluados = [c for c in casos if c.estado in (VERDE, ROJO)]
        metricas.casos += len(evaluados)
        metricas.errores += sum(1 for c in casos if c.estado == ERROR)
        metricas.no_ejecutados += sum(1 for c in casos if c.estado == NO_EJECUTADO)
        metricas.verdes += sum(1 for c in evaluados if c.estado == VERDE)
        metricas.avisos += sum(len(c.avisos) for c in evaluados)
        fallos_por_rep.append(sum(len(c.fallos) for c in evaluados))
    metricas.fallos = _media(sum(fallos_por_rep), len(fallos_por_rep))
    metricas.fallos_min = min(fallos_por_rep, default=0)
    metricas.fallos_max = max(fallos_por_rep, default=0)

    propios = [r for r in registros if r.get("etiqueta") == etiqueta]
    duraciones: dict[tuple, int] = {}
    con_respuesta = set()
    servidos, motivos = set(), Counter()
    entrada = salida = respondidas = 0
    for registro in propios:
        albaran = (registro.get("repeticion"), registro.get("caso_id"))
        metricas.coste_total += Decimal(registro["coste_usd"])
        metricas.fallos_medidor += bool(registro.get("fallo_medidor"))
        metricas.uso_incompleto += bool(registro.get("uso_incompleto"))
        if isinstance(registro.get("duracion_ms"), int):
            duraciones[albaran] = duraciones.get(albaran, 0) + registro["duracion_ms"]
        if registro.get("con_respuesta"):
            # Los tokens medios, solo de las llamadas con respuesta: una sin
            # respuesta no mide nada y bajaría la estimación siguiente (R15).
            respondidas += 1
            entrada += (
                registro["entrada"] + registro["lectura_cache"] + registro["escritura_cache"]
            )
            salida += registro["salida"]
            con_respuesta.add(albaran)
            if registro.get("modelo_servido"):
                servidos.add(registro["modelo_servido"])
            if registro.get("motivo_parada"):
                motivos[registro["motivo_parada"]] += 1
    metricas.llamadas = len(propios)
    metricas.tokens_entrada_medios = _media(entrada, respondidas)
    metricas.tokens_salida_medios = _media(salida, respondidas)
    metricas.tiempo_medio_s = _media(sum(duraciones.values()), len(duraciones)) / 1000
    metricas.tiempo_max_s = Decimal(max(duraciones.values(), default=0)) / 1000
    metricas.coste_por_albaran = _media(metricas.coste_total, len(con_respuesta))
    metricas.modelos_servidos = sorted(servidos)
    metricas.motivos_parada = dict(motivos)
    return metricas


@dataclass
class Recomendacion:
    elegibles: list[str]
    banda: list[str]
    recomendado: str | None
    veredicto: str
    avisos: list[str]
    provisional: bool
    etiqueta_provisional: str


def _etiqueta(repeticiones: int) -> str:
    if repeticiones >= REPETICIONES_FIRMES:
        return ""
    return f"provisional ({repeticiones} repetici{'ón' if repeticiones == 1 else 'ones'})"


def recomendar(metricas: dict[str, Metricas], referencia: str, repeticiones: int) -> Recomendacion:
    """Elegibles, banda, recomendado y veredicto de una fase (R30–R35)."""
    etiqueta = _etiqueta(repeticiones)
    provisional = bool(etiqueta)
    ref = metricas.get(referencia)
    if ref is None or ref.errores or ref.no_ejecutados or not ref.casos:
        return Recomendacion([], [], None, "sin datos", [], provisional, etiqueta)

    elegibles = [
        m for m in metricas.values()
        if not m.errores and not m.no_ejecutados and m.fallos <= ref.fallos
    ]
    mejor = min(m.fallos for m in elegibles)
    holgura = max(Decimal(BANDA_MINIMA), BANDA_RELATIVA * mejor)
    banda = [m for m in elegibles if m.fallos <= mejor + holgura]

    barato = min(banda, key=lambda m: (m.coste_por_albaran, m.tiempo_medio_s, m.modelo))
    empatados = [
        m for m in banda
        if m is barato
        or m.coste_por_albaran - barato.coste_por_albaran < EMPATE_COSTE * barato.coste_por_albaran
    ]
    elegido = min(empatados, key=lambda m: (m.tiempo_medio_s, m.coste_por_albaran, m.modelo))

    veredicto = "mantener"
    if elegido.modelo != referencia:
        mejora = (
            elegido.fallos <= MEJORA_FALLOS * ref.fallos
            and elegido.coste_por_albaran <= MEJORA_COSTE * ref.coste_por_albaran
        )
        ahorro = elegido.coste_por_albaran <= AHORRO_COSTE * ref.coste_por_albaran
        if mejora or ahorro:
            veredicto = "cambiar"

    avisos = []
    if elegido.tiempo_medio_s > LATENCIA * ref.tiempo_medio_s:
        avisos.append(
            f"{elegido.modelo} tarda de media {elegido.tiempo_medio_s:.1f} s por albarán, más "
            f"del doble que la referencia ({ref.tiempo_medio_s:.1f} s): el cliente de Claude "
            f"corta a 120 s"
        )
    return Recomendacion(
        elegibles=[m.modelo for m in elegibles],
        banda=[m.modelo for m in banda],
        recomendado=elegido.modelo,
        veredicto=veredicto,
        avisos=avisos,
        provisional=provisional,
        etiqueta_provisional=etiqueta,
    )
