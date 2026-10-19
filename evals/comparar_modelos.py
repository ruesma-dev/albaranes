# evals/comparar_modelos.py
"""Compara modelos de IA en UNA fase, con acierto y coste por albarán (F-083).

    python -m evals.comparar_modelos --fase IA1|IA2|IA3|IA4 --modelos a,b[,...]
        [--casos GEN-001,HOR-001] [--repeticiones N] [--tope-usd 25]
        [--tope-total-usd 200] [--estimar] [--resumen <md>] [--salida <dir>]

Cada modelo se mide en la fase pedida con el resto del ciclo fijo: la
referencia de producción prepara la entrada (IA1 para IA2, IA3 para IA4) y,
en IA3, la conciliación sale del libro IA4. La referencia de la fase se añade
siempre (R12) y va la primera en cada repetición. Los tokens de cada llamada
los mide el `MedidorDeUso` que entra como `call_logger` de los clientes de
comun, y el coste sale de la tabla versionada `evals/precios_modelos.json`.

CUESTA DINERO y solo lo lanza el humano. Antes de llamar a nada imprime la
estimación y para (código 2) si: un modelo no está en la tabla o está
excluido, la tabla está caducada, falta una clave, la estimación supera
`--tope-usd` o, sumada al gasto acumulado de la feature, `--tope-total-usd`.
`--estimar` imprime la estimación y sale con 0 sin pedir claves.

Códigos: 0 hecho, 1 ningún candidato dio resultado, 2 parada antes de gastar,
3 cortado por el tope de gasto a mitad de la corrida.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, Decimal, InvalidOperation
from pathlib import Path

from evals.conversor import RUTA_FIXTURES
from evals.costes import (
    FASES,
    Estimacion,
    Partida,
    Tabla,
    TablaCaducada,
    TablaInvalida,
    cargar_tabla,
    estimar,
    precio_vigente,
)
from evals.informe_modelos import gasto_acumulado, tokens_medidos
from evals.procesos import sv6_build
from evals.procesos.medidor import lanzar
from evals.procesos.sv2_extraccion import RUTA_ALBARANES, ruta_de_albaran
from evals.procesos.sv5_valoracion import ClavesAusentes, comprobar_claves
from evals.runner import cargar_fixtures

RAIZ_REPO = Path(__file__).resolve().parent.parent

#: El resumen SIN valores que se versiona, acumulativo (R29).
RUTA_RESUMEN = RAIZ_REPO / "progress" / "comparar_modelos_F-083.md"

#: El detalle CON valores, una carpeta por invocación. `evals/salidas/` lo ignora git.
RUTA_SALIDAS = RAIZ_REPO / "evals" / "salidas" / "comparar_modelos"

#: Topes por defecto (P3 de la PARADA 1).
TOPE_USD = Decimal("25")
TOPE_TOTAL_USD = Decimal("200")

#: Qué fase prepara la entrada de la fase medida, y con qué etiqueta de trabajo.
PREPARACION = {"IA2": ("IA1", "prep_IA1"), "IA4": ("IA3", "prep_IA3")}

#: Libro del que salen los casos de cada fase.
LIBRO_DE_FASE = {"IA1": "IA1", "IA2": "IA2", "IA3": "inputs", "IA4": "IA4"}


class Parada(RuntimeError):
    """La corrida no puede empezar. Se lanza siempre ANTES de llamar al LLM."""


def _lanzar_sv2(trabajo: dict) -> dict:  # pragma: no cover - subproceso con LLM
    return lanzar("evals.procesos.sv2_modelos", trabajo, "sv2")


def _lanzar_sv5(trabajo: dict) -> dict:  # pragma: no cover - subproceso con LLM
    return lanzar("evals.procesos.sv5_modelos", trabajo, "sv5")


def _build_sv6(trabajo: dict) -> dict:  # pragma: no cover - subproceso
    return sv6_build.ejecutar_en_subproceso(trabajo)


def _ahora() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


@dataclass
class Dependencias:
    """Lo que toca el mundo exterior; los tests pasan dobles."""

    ejecutar_sv2: Callable[[dict], dict] = _lanzar_sv2
    ejecutar_sv5: Callable[[dict], dict] = _lanzar_sv5
    build_sv6: Callable[[dict], dict] = _build_sv6
    tabla: Tabla | None = None
    fixtures: Path = RUTA_FIXTURES
    albaranes: Path = RUTA_ALBARANES
    ahora: Callable[[], dt.datetime] = _ahora


@dataclass
class Plan:
    """Qué se mide: modelos (la referencia primero), casos, repeticiones y preparación."""

    fase: str
    modelos: list[str]
    referencia: str
    referencia_anadida: bool
    preparacion: str | None
    casos: list[str]
    omitidos: dict[str, str] = field(default_factory=dict)
    repeticiones: int = 1
    proveedores: list[str] = field(default_factory=list)

    def bloques(self) -> list[tuple[int, str]]:
        """(repetición, modelo), con los modelos intercalados en cada repetición (R25)."""
        return [
            (repeticion, modelo)
            for repeticion in range(1, self.repeticiones + 1)
            for modelo in self.modelos
        ]

    def partidas(self) -> list[Partida]:
        """Las llamadas previstas: una por caso y bloque, y la preparación una vez."""
        partidas = [
            Partida(modelo, "candidato", self.fase, len(self.casos) * self.repeticiones)
            for modelo in self.modelos
        ]
        if self.preparacion is not None:
            fase_previa = PREPARACION[self.fase][0]
            partidas.append(Partida(self.preparacion, "preparación", fase_previa, len(self.casos)))
        return partidas


# --- Plan (R11–R13) --------------------------------------------------------------


def casos_de_fase(
    fase: str, fixtures: Path, albaranes: Path, pedidos: list[str] | None
) -> tuple[list[str], dict[str, str]]:
    """Los casos que se miden en la fase y los que se quedan fuera, con su motivo.

    IA1 e IA2: los de su libro con albarán. IA3: todos los de INPUTS (R22).
    IA4: los del libro IA4 que tienen INPUTS (R23).
    """
    libro = cargar_fixtures(fixtures, LIBRO_DE_FASE[fase])
    inputs = cargar_fixtures(fixtures, "inputs") if fase == "IA4" else {}
    omitidos: dict[str, str] = {}
    candidatos = sorted(libro)
    if pedidos:
        omitidos.update(
            {caso: "no está en el libro de la fase" for caso in pedidos if caso not in libro}
        )
        candidatos = [caso for caso in candidatos if caso in pedidos]
    casos = []
    for caso in candidatos:
        if fase in ("IA1", "IA2") and ruta_de_albaran(caso, albaranes) is None:
            omitidos[caso] = "no existe el fichero del albarán"
        elif fase == "IA4" and caso not in inputs:
            omitidos[caso] = "sin caso en INPUTS"
        else:
            casos.append(caso)
    return casos, omitidos


def planificar(opciones, tabla: Tabla, fixtures: Path, albaranes: Path) -> Plan:
    """El plan de la invocación; `Parada` si un modelo no vale o no hay casos."""
    fase = opciones.fase
    pedidos = list(dict.fromkeys(opciones.lista_modelos))
    malos = []
    for modelo in pedidos:
        if modelo not in tabla.modelos:
            malos.append(f"{modelo} (no está en la tabla)")
        elif tabla.modelo(modelo).papel == "excluido":
            malos.append(f"{modelo} (excluido: {tabla.modelo(modelo).motivo})")
    if malos:
        raise Parada(
            "modelos no válidos: " + "; ".join(malos)
            + ". Válidos: " + ", ".join(tabla.validos())
            + ". No se ha llamado a ningún LLM."
        )
    referencia = tabla.referencia(fase)
    modelos = [referencia, *(m for m in pedidos if m != referencia)]
    preparacion = tabla.referencia(PREPARACION[fase][0]) if fase in PREPARACION else None
    casos, omitidos = casos_de_fase(fase, fixtures, albaranes, opciones.lista_casos)
    if not casos:
        raise Parada(
            f"ningún caso que medir en {fase} (omitidos: {len(omitidos)}). "
            f"No se ha llamado a ningún LLM."
        )
    proveedores = sorted(
        {tabla.modelo(m).proveedor for m in [*modelos, *filter(None, [preparacion])]}
    )
    return Plan(
        fase=fase,
        modelos=modelos,
        referencia=referencia,
        referencia_anadida=referencia not in pedidos,
        preparacion=preparacion,
        casos=casos,
        omitidos=omitidos,
        repeticiones=opciones.repeticiones,
        proveedores=proveedores,
    )


# --- Estimación y paradas antes de gastar (R4, R14–R18) ---------------------------


def usd(valor: Decimal) -> str:
    """USD con 4 decimales, redondeado hacia arriba: una estimación no se queda corta."""
    return str(valor.quantize(Decimal("0.0001"), rounding=ROUND_CEILING))


def imprimir_estimacion(plan: Plan, estimacion: Estimacion) -> None:
    print(
        f"Estimación · {plan.fase} · {len(plan.casos)} casos · "
        f"{plan.repeticiones} repetición(es) · antes de llamar a nada"
    )
    if plan.referencia_anadida:
        print(
            f"AVISO: se añade la referencia de {plan.fase} ({plan.referencia}), que no se "
            f"había pedido: sin ella no hay con qué comparar (R12)."
        )
    if plan.omitidos:
        detalle = ", ".join(f"{caso}: {motivo}" for caso, motivo in sorted(plan.omitidos.items()))
        print(f"Omitidos: {len(plan.omitidos)} ({detalle})")
    for linea in estimacion.lineas:
        print(
            f"- {linea.modelo} · {linea.etiqueta} · {linea.llamadas} llamadas · "
            f"{linea.entrada} / {linea.salida} tokens ({linea.origen}) · ≈ {usd(linea.usd)} USD"
        )
    print(f"Total estimado: {usd(estimacion.total)} USD")


def _leer(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8") if ruta.is_file() else ""


def ejecutar(opciones, entorno: dict, dependencias: Dependencias) -> int:
    """Planifica, estima, para si algo falta y, si no, corre. Devuelve el código."""
    tabla = dependencias.tabla or cargar_tabla()
    plan = planificar(opciones, tabla, Path(dependencias.fixtures), Path(dependencias.albaranes))
    ahora = dependencias.ahora()
    for modelo in [*plan.modelos, *filter(None, [plan.preparacion])]:
        precio_vigente(tabla.modelo(modelo), ahora.date())  # R4: TablaCaducada
    resumen = _leer(Path(opciones.resumen))
    estimacion = estimar(plan.partidas(), tabla, tokens_medidos(resumen), ahora.date())
    imprimir_estimacion(plan, estimacion)
    if opciones.estimar:
        return 0
    comprobar_claves(plan.proveedores, entorno)
    if estimacion.total > opciones.tope_usd:
        raise Parada(
            f"la estimación ({usd(estimacion.total)} USD) supera --tope-usd "
            f"{opciones.tope_usd}. No se ha llamado a ningún LLM."
        )
    acumulado = gasto_acumulado(resumen)
    if acumulado + estimacion.total > opciones.tope_total_usd:
        raise Parada(
            f"el gasto acumulado de F-083 es {acumulado} USD y esta invocación se estima en "
            f"{usd(estimacion.total)} USD: juntos superan --tope-total-usd "
            f"{opciones.tope_total_usd}. No se ha llamado a ningún LLM."
        )
    return ejecutar_plan(plan, opciones, tabla, dependencias, ahora)


def ejecutar_plan(plan, opciones, tabla, dependencias, ahora) -> int:
    """La corrida por bloques: llega en T8."""
    raise NotImplementedError("la ejecución por bloques llega en T8")


# --- CLI --------------------------------------------------------------------------


def _decimal(texto: str) -> Decimal:
    try:
        valor = Decimal(texto)
    except InvalidOperation as error:
        raise argparse.ArgumentTypeError(f"{texto!r} no es un importe en USD") from error
    if valor < 0:
        raise argparse.ArgumentTypeError("un tope no puede ser negativo")
    return valor


def _lista(texto: str) -> list[str]:
    return list(dict.fromkeys(parte.strip() for parte in texto.split(",") if parte.strip()))


def analizar(argv: list[str] | None) -> argparse.Namespace:
    analizador = argparse.ArgumentParser(
        prog="python -m evals.comparar_modelos",
        description=(
            "Compara modelos de IA en una fase con acierto y coste por albarán. "
            "Llama a LLM reales: cuesta dinero."
        ),
    )
    analizador.add_argument("--fase", required=True, choices=FASES)
    analizador.add_argument("--modelos", required=True, help="ids de la tabla, separados por coma")
    analizador.add_argument("--casos", default="", help="caso_id separados por coma")
    analizador.add_argument("--repeticiones", type=int, default=1, help="por defecto 1")
    analizador.add_argument("--tope-usd", type=_decimal, default=TOPE_USD,
                            help="gasto máximo de esta invocación (por defecto 25)")
    analizador.add_argument("--tope-total-usd", type=_decimal, default=TOPE_TOTAL_USD,
                            help="gasto máximo de la feature, sumando las líneas GASTO (200)")
    analizador.add_argument("--estimar", action="store_true",
                            help="solo imprime la estimación: ni claves ni llamadas")
    analizador.add_argument("--resumen", default=str(RUTA_RESUMEN),
                            help="resumen SIN valores, acumulativo (versionable)")
    analizador.add_argument("--salida", default="",
                            help="detalle CON valores (por defecto evals/salidas/comparar_modelos/"
                            "<fecha-hora>/, ignorado por git)")
    opciones = analizador.parse_args(argv)
    opciones.lista_modelos = _lista(opciones.modelos)
    opciones.lista_casos = _lista(opciones.casos) or None
    if not opciones.lista_modelos:
        analizador.error("--modelos no puede estar vacío")
    if opciones.repeticiones < 1:
        analizador.error("--repeticiones tiene que ser 1 o más")
    return opciones


def main(
    argv: list[str] | None = None,
    *,
    entorno: dict | None = None,
    dependencias: Dependencias | None = None,
) -> int:
    """CLI. Códigos: 0 hecho, 1 sin resultados, 2 parada antes de gastar, 3 cortado por tope."""
    opciones = analizar(argv)
    try:
        return ejecutar(
            opciones,
            entorno if entorno is not None else dict(os.environ),
            dependencias or Dependencias(),
        )
    except (Parada, ClavesAusentes, TablaCaducada, TablaInvalida) as error:
        print(f"comparar_modelos: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
