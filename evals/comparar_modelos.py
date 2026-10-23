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
import copy
import datetime as dt
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import ROUND_CEILING, Decimal, InvalidOperation
from pathlib import Path

from evals import runner
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
from evals.criticidad import cargar_criticidad
from evals.decision import NO_EJECUTADO, medir, recomendar
from evals.informe_modelos import (
    Seccion,
    anadir_seccion,
    gasto_acumulado,
    render_detalle,
    render_versionable,
    tokens_medidos,
)
from evals.modelos import ERROR, ROJO, VERDE, ResultadoCaso
from evals.procesos import sv5_valoracion, sv6_build
from evals.procesos.medidor import lanzar, registros_de_fichero
from evals.procesos.sv2_extraccion import RUTA_ALBARANES, ruta_de_albaran
from evals.procesos.sv5_valoracion import ClavesAusentes, comprobar_claves
from evals.runner import cargar_fixtures

RAIZ_REPO = Path(__file__).resolve().parent.parent

#: El resumen SIN valores que se versiona, acumulativo (R29).
RUTA_RESUMEN = RAIZ_REPO / "progress" / "comparar_modelos_F-083.md"

#: El detalle CON valores, una carpeta por invocación. `evals/salidas/` lo ignora git.
RUTA_SALIDAS = RAIZ_REPO / "evals" / "salidas" / "comparar_modelos"

#: Topes por defecto (P3 de la PARADA 1).
TOPE_USD = Decimal(25)
TOPE_TOTAL_USD = Decimal(200)

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
    repeticiones: int
    omitidos: dict[str, str] = field(default_factory=dict)
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
    IA4: los del libro IA4 que tienen INPUTS (R23). En IA3 e IA4 se quedan
    fuera los que tienen el documento del contrato en el índice y no en local
    (F-084 R33): se mediría otra cosa.
    """
    libro = cargar_fixtures(fixtures, LIBRO_DE_FASE[fase])
    inputs = cargar_fixtures(fixtures, "inputs") if fase in ("IA3", "IA4") else {}
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
        elif inputs and (motivo := sv5_valoracion.falta_documento(inputs[caso])):
            omitidos[caso] = motivo
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


# --- Ejecución por bloques (R19, R21, R23–R26) -------------------------------------

#: Por qué un caso no tiene resultado del bloque.
MOTIVO_NO_DEVUELTO = "el bloque no devolvió el caso"
MOTIVO_NO_EJECUTADO = "no ejecutado: se alcanzó --tope-usd"


@dataclass
class Bloque:
    """Lo que devolvió un bloque: resultado por caso y los registros del medidor."""

    resultados: dict[str, dict]
    registros: list[dict]


def _trabajos_de_casos(plan: Plan, fixtures: Path, albaranes: Path) -> dict[str, dict]:
    """La entrada de cada caso para el subproceso, sin los valores del candidato."""
    if plan.fase in ("IA1", "IA2"):
        libro = cargar_fixtures(fixtures, plan.fase)
        return {
            caso: {
                "caso_id": caso,
                "fichero": str(ruta_de_albaran(caso, albaranes)),
                "tipologia": libro[caso].get("tipologia", ""),
            }
            for caso in plan.casos
        }
    inputs = cargar_fixtures(fixtures, "inputs")
    return {
        caso: {"caso_id": caso, "contexto": sv5_valoracion.construir_contexto(inputs[caso])}
        for caso in plan.casos
    }


def _ejecutar_bloque(
    trabajo_fase: str,
    modelo_id: str,
    casos: list[dict],
    presupuesto: Decimal,
    registros: Path,
    tabla: Tabla,
    dependencias: Dependencias,
    fecha: dt.date,
) -> Bloque:
    """Un bloque en su subproceso; si muere, sus casos quedan con error y lo
    ya pagado se recupera del fichero de registros del medidor (R26)."""
    modelo = tabla.modelo(modelo_id)
    trabajo = {
        "fase": trabajo_fase,
        "modelo": {
            "id": modelo.id,
            "proveedor": modelo.proveedor,
            "herramienta_forzada": modelo.herramienta_forzada,
        },
        "casos": casos,
        "presupuesto_usd": str(presupuesto),
        "fecha": fecha.isoformat(),
        "registros": str(registros),
    }
    ejecutar = dependencias.ejecutar_sv2 if "IA1" in trabajo_fase or trabajo_fase == "IA2" else (
        dependencias.ejecutar_sv5
    )
    try:
        salida = ejecutar(trabajo)
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"comparar_modelos: el bloque {trabajo_fase} de {modelo_id} murió: {error}",
              file=sys.stderr)
        motivo = {"fase": trabajo_fase, "tipo": type(error).__name__,
                  "motivo": "el subproceso del bloque murió (detalle en la consola)"}
        return Bloque(
            {caso["caso_id"]: {"caso_id": caso["caso_id"], "error": motivo} for caso in casos},
            registros_de_fichero(registros),
        )
    return Bloque({r.get("caso_id"): r for r in salida.get("resultados", [])},
                  list(salida.get("registros", [])))


def _gasto(registros: list[dict]) -> Decimal:
    return sum((Decimal(r.get("coste_usd", "0")) for r in registros), Decimal(0))


def _motivo_error(resultado: dict) -> str:
    error = resultado.get("error") or {}
    return f"ERROR en {error.get('fase') or '?'} · {error.get('motivo', '')}"


def _caso_sin_evaluar(
    caso: str, fase: str, resultado: dict | None, preparacion: dict | None, hay_preparacion: bool
) -> ResultadoCaso | None:
    """El caso como ERROR o NO_EJECUTADO, o `None` si hay con qué evaluarlo.

    Con preparación, manda la del caso: si falló, el candidato ni lo recibió.
    """
    if hay_preparacion:
        if preparacion is None:
            return ResultadoCaso.con_error(caso, fase, f"falló la preparación · {MOTIVO_NO_DEVUELTO}")
        if preparacion.get("error"):
            return ResultadoCaso.con_error(
                caso, fase, f"falló la preparación · {_motivo_error(preparacion)}"
            )
        if preparacion.get("no_ejecutado"):
            return ResultadoCaso(caso_id=caso, fase=fase, estado=NO_EJECUTADO,
                                 motivo=f"preparación {MOTIVO_NO_EJECUTADO}")
    if resultado is None:
        return ResultadoCaso.con_error(caso, fase, MOTIVO_NO_DEVUELTO)
    if resultado.get("no_ejecutado"):
        return ResultadoCaso(caso_id=caso, fase=fase, estado=NO_EJECUTADO, motivo=MOTIVO_NO_EJECUTADO)
    if resultado.get("error"):
        return ResultadoCaso.con_error(caso, fase, _motivo_error(resultado))
    return None


def _evaluar_bloque(
    plan: Plan,
    bloque: Bloque,
    prep: dict[str, dict],
    libros: dict[str, dict],
    criticidad,
    dependencias: Dependencias,
) -> dict[str, list[ResultadoCaso]]:
    """Los casos del bloque evaluados en la fase (y en E2E si es IA3 o IA4)."""
    fases = [plan.fase] if plan.fase in ("IA1", "IA2") else [plan.fase, "E2E"]
    por_fase: dict[str, dict[str, ResultadoCaso]] = {fase: {} for fase in fases}
    evaluables: dict[str, dict] = {}
    for caso in plan.casos:
        resultado = bloque.resultados.get(caso)
        for fase in fases:
            sin_evaluar = _caso_sin_evaluar(
                caso, fase, resultado, prep.get(caso), plan.preparacion is not None
            )
            if sin_evaluar is not None:
                por_fase[fase][caso] = sin_evaluar
        if all(caso not in por_fase[fase] for fase in fases):
            evaluables[caso] = resultado

    if plan.fase in ("IA1", "IA2"):
        for caso, resultado in evaluables.items():
            por_fase[plan.fase][caso] = ResultadoCaso.desde_discrepancias(
                caso, plan.fase,
                runner.comparar_sv2(plan.fase, libros[plan.fase][caso], resultado["documento"],
                                    caso, criticidad),
            )
    else:
        envelopes, conciliaciones = {}, {}
        for caso, resultado in evaluables.items():
            if plan.fase == "IA3":
                envelope = copy.deepcopy(resultado["envelope"])
                if caso in libros["IA4"]:  # D3: la IA4 del libro, sin LLM
                    sv5_valoracion.aplicar_conciliacion(
                        envelope,
                        sv5_valoracion.conciliaciones_desde_ground_truth(libros["IA4"][caso], envelope),
                    )
            else:
                envelope = copy.deepcopy(prep[caso]["envelope"])
                conciliaciones[caso] = resultado.get("conciliaciones", [])
                sv5_valoracion.aplicar_conciliacion(envelope, conciliaciones[caso])
            envelopes[caso] = envelope
        if envelopes:
            evaluadas, _ = runner.evaluar_valoracion(
                envelopes,
                conciliaciones,
                libros["IA3"] if plan.fase == "IA3" else {},
                libros["IA4"] if plan.fase == "IA4" else {},
                libros["final"],
                criticidad,
                build=dependencias.build_sv6,
            )
            for fase_evaluada in evaluadas:
                if fase_evaluada.nombre in por_fase:
                    for resultado_caso in fase_evaluada.casos:
                        por_fase[fase_evaluada.nombre][resultado_caso.caso_id] = resultado_caso
    return {
        fase: [casos[c] for c in plan.casos if c in casos] for fase, casos in por_fase.items()
    }


def _directorio_salida(opciones, ahora: dt.datetime) -> Path:
    if opciones.salida:
        return Path(opciones.salida)
    return RUTA_SALIDAS / ahora.astimezone().strftime("%Y-%m-%d-%H%M%S")


def _relativa(ruta: Path) -> str:
    try:
        return Path(ruta).resolve().relative_to(RAIZ_REPO).as_posix()
    except ValueError:
        return Path(ruta).as_posix()


def ejecutar_plan(plan: Plan, opciones, tabla: Tabla, dependencias: Dependencias, ahora) -> int:
    """Preparación, bloques intercalados, evaluación, métricas e informes."""
    fecha = ahora.date()
    salida = _directorio_salida(opciones, ahora)
    salida.mkdir(parents=True, exist_ok=True)
    fixtures = Path(dependencias.fixtures)
    trabajos = _trabajos_de_casos(plan, fixtures, Path(dependencias.albaranes))
    libros = {nombre: cargar_fixtures(fixtures, nombre) for nombre in ("IA1", "IA2", "IA3", "IA4", "final")}
    tope = opciones.tope_usd
    gastado = Decimal(0)

    prep: dict[str, dict] = {}
    registros_prep: list[dict] = []
    if plan.preparacion is not None:
        bloque = _ejecutar_bloque(
            PREPARACION[plan.fase][1], plan.preparacion, list(trabajos.values()), tope,
            salida / "registros_preparacion.jsonl", tabla, dependencias, fecha,
        )
        prep = bloque.resultados
        registros_prep = list(bloque.registros)
        gastado += _gasto(bloque.registros)

    # Lo que la preparación devuelve y el campo con que entra en cada caso del candidato.
    salida_prep, campo_prep = ("documento", "ia1") if plan.fase == "IA2" else ("envelope", "envelope")
    casos_por_modelo: dict[str, dict[str, list[list[ResultadoCaso]]]] = {}
    registros: dict[str, list[dict]] = {modelo: [] for modelo in plan.modelos}
    brutos = []
    for repeticion, modelo in plan.bloques():
        casos = []
        for caso, trabajo in trabajos.items():
            if plan.preparacion is None:
                casos.append(trabajo)
            elif salida_prep in prep.get(caso, {}):
                casos.append({**trabajo, campo_prep: prep[caso][salida_prep]})
        restante = tope - gastado
        if restante <= 0:
            bloque = Bloque({c["caso_id"]: {"caso_id": c["caso_id"], "no_ejecutado": True}
                             for c in casos}, [])
        else:
            bloque = _ejecutar_bloque(
                plan.fase, modelo, casos, restante,
                salida / f"registros_{modelo}_r{repeticion}.jsonl", tabla, dependencias, fecha,
            )
        gastado += _gasto(bloque.registros)
        registros[modelo] += [{**r, "repeticion": repeticion} for r in bloque.registros]
        brutos.append({"modelo": modelo, "repeticion": repeticion, "resultados": bloque.resultados})
        evaluado = _evaluar_bloque(plan, bloque, prep, libros, cargar_criticidad(), dependencias)
        for fase, lista in evaluado.items():
            casos_por_modelo.setdefault(fase, {}).setdefault(modelo, []).append(lista)

    return _cerrar(plan, opciones, ahora, salida, casos_por_modelo, registros, registros_prep,
                   prep, brutos, gastado)


def _cerrar(plan, opciones, ahora, salida, casos_por_modelo, registros, registros_prep, prep,
            brutos, gastado) -> int:
    """Métricas, recomendación, los dos informes y el código de salida."""
    principal = casos_por_modelo[plan.fase]
    metricas = {m: medir(m, plan.fase, principal[m], registros[m]) for m in plan.modelos}
    e2e = {
        m: medir(m, "E2E", casos_por_modelo["E2E"][m], registros[m])
        for m in plan.modelos
    } if "E2E" in casos_por_modelo else {}
    metricas_prep = None
    if plan.preparacion is not None:
        metricas_prep = medir(plan.preparacion, PREPARACION[plan.fase][0], [],
                              registros_prep, etiqueta="preparación")
    errores = [
        (modelo, repeticion, caso.caso_id, caso.motivo)
        for modelo in plan.modelos
        for repeticion, lista in enumerate(principal[modelo], start=1)
        for caso in lista
        if caso.estado == ERROR
    ]
    cortado = any(
        caso.estado == NO_EJECUTADO for listas in principal.values() for lista in listas for caso in lista
    )
    seccion = Seccion(
        fecha=ahora.strftime("%Y-%m-%dT%H:%M:%SZ"),
        fase=plan.fase,
        commit=runner._commit_actual(RAIZ_REPO),
        casos=plan.casos,
        omitidos=plan.omitidos,
        repeticiones=plan.repeticiones,
        referencia=plan.referencia,
        referencia_anadida=plan.referencia_anadida,
        preparacion=plan.preparacion,
        metricas=metricas,
        recomendacion=recomendar(metricas, plan.referencia, plan.repeticiones),
        gasto_real=gastado,
        salida=_relativa(salida),
        metricas_e2e=e2e,
        metricas_preparacion=metricas_prep,
        errores=errores,
        cortado=cortado,
    )
    resumen = Path(opciones.resumen)
    resumen.parent.mkdir(parents=True, exist_ok=True)
    resumen.write_text(anadir_seccion(_leer(resumen), render_versionable(seccion)), encoding="utf-8")
    (salida / "detalle.md").write_text(render_detalle(seccion, principal), encoding="utf-8")
    (salida / "resultados.json").write_text(
        json.dumps(
            {"fase": plan.fase, "preparacion": prep, "bloques": brutos,
             "registros": {**registros, "preparación": registros_prep}},
            ensure_ascii=False, indent=2, default=str,
        ),
        encoding="utf-8",
    )
    print(f"comparar_modelos: gasto real {gastado} USD · detalle con valores en {salida}")
    print(f"comparar_modelos: resumen sin valores en {resumen} · "
          f"{seccion.recomendacion.veredicto}")
    if cortado:
        return 3
    alguno = any(caso.estado in (VERDE, ROJO) for listas in principal.values()
                 for lista in listas for caso in lista)
    return 0 if alguno else 1


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
