# evals/runner.py
"""Runner de los evals: las dos corridas y su informe.

    python -m evals.runner --con-llm [--feature F-XXX]   # pasada completa
    python -m evals.runner [--feature F-XXX]             # modo determinista

La **pasada completa** ejecuta las cuatro fases MÁS el extremo-a-extremo, sin
trocear (decisión D2): la contención del coste está en CUÁNDO se lanza —la
puerta del arnés o una petición del humano—, no en cuánto ejecuta. El **modo
determinista** no hace ni una llamada de red: estimula las redes de sv6 desde
el propio ground truth.

Pedir IA1/IA2 sin `--con-llm` es un error explícito: el gasto en LLM nunca
ocurre por defecto. Y este runner NO lo invoca nunca `harness/init.sh`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from evals.comparador import comparar_tablas
from evals.conversor import RUTA_FIXTURES
from evals.criticidad import cargar_criticidad
from evals.informe import MODO_COMPLETA, MODO_DETERMINISTA, render
from evals.modelos import (
    ResultadoCaso,
    ResultadoFase,
    ResultadoPasada,
)
from evals.procesos import sv2_extraccion, sv5_valoracion, sv6_build

#: Directorio de informes del arnés.
RUTA_PROGRESS = Path(__file__).resolve().parent.parent / "progress"

#: Fases de cada corrida. La completa no se trocea (D2).
FASES_COMPLETA: tuple[str, ...] = ("IA1", "IA2", "IA3", "IA4", "E2E")
FASES_DETERMINISTA: tuple[str, ...] = ("IA3", "IA4", "E2E")

#: Fases que no existen sin llamadas LLM: no hay modo determinista de leer un
#: albarán en PDF.
FASES_SOLO_CON_LLM: frozenset[str] = frozenset({"IA1", "IA2"})


class UsoIncorrecto(RuntimeError):
    """Lo que se ha pedido no se puede ejecutar tal como se ha pedido."""


# --- Carga de fixtures ------------------------------------------------------


def cargar_fixtures(directorio: Path, fase: str) -> dict[str, dict]:
    """Todos los casos de una fase, indexados por `caso_id`."""
    carpeta = Path(directorio) / fase
    if not carpeta.is_dir():
        return {}
    casos = {}
    for ruta in sorted(carpeta.glob("*.json")):
        if ruta.name.startswith("_"):
            continue
        casos[ruta.stem] = json.loads(ruta.read_text(encoding="utf-8"))
    return casos


def _filtrar(casos: dict[str, dict], pedidos: list[str] | None) -> dict[str, dict]:
    if not pedidos:
        return casos
    return {caso: datos for caso, datos in casos.items() if caso in set(pedidos)}


# --- Modo determinista ------------------------------------------------------


def corrida_determinista(
    fixtures: Path, casos_pedidos: list[str] | None = None
) -> tuple[list[ResultadoFase], list[str]]:
    """IA3, IA4 y extremo-a-extremo contra las redes de sv6, sin ninguna red."""
    criticidad = cargar_criticidad()
    inputs = _filtrar(cargar_fixtures(fixtures, "inputs"), casos_pedidos)
    ia3 = cargar_fixtures(fixtures, "IA3")
    ia4 = cargar_fixtures(fixtures, "IA4")
    final = cargar_fixtures(fixtures, "final")

    fase_ia3 = ResultadoFase(nombre="IA3")
    fase_ia4 = ResultadoFase(nombre="IA4")
    fase_e2e = ResultadoFase(nombre="E2E")
    no_observables: list[str] = []

    if not inputs:
        motivo = "no hay ningún caso en evals/fixtures/inputs/"
        for fase in (fase_ia3, fase_ia4, fase_e2e):
            fase.motivo = motivo
        return [fase_ia3, fase_ia4, fase_e2e], no_observables

    envelopes: dict[str, dict] = {}
    for caso_id, datos in inputs.items():
        envelope = sv6_build.construir_envelope_estimulado(
            datos, ia3.get(caso_id, {"tablas": {}})
        )
        if caso_id in ia4:
            sv5_valoracion.aplicar_conciliacion(
                envelope,
                sv5_valoracion.conciliaciones_desde_ground_truth(
                    ia4[caso_id], envelope
                ),
            )
        envelopes[caso_id] = envelope

    salida = sv6_build.ejecutar_en_subproceso(
        {
            "casos": [
                {"caso_id": caso_id, "envelope": envelope}
                for caso_id, envelope in envelopes.items()
            ]
        }
    )
    resultados = {r["caso_id"]: r for r in salida["resultados"]}

    for caso_id, envelope in envelopes.items():
        resultado = resultados.get(caso_id)
        if resultado is None:
            fase_e2e.casos.append(
                ResultadoCaso.omitido(caso_id, "E2E", "sv6 no devolvió resultado")
            )
            continue

        if caso_id in ia3:
            evaluacion = sv6_build.evaluar_caso_determinista(
                caso_id=caso_id,
                envelope=envelope,
                resultado=resultado,
                ia3=ia3[caso_id],
                final=None,
                criticidad=criticidad,
            )
            fase_ia3.casos.append(
                ResultadoCaso.desde_discrepancias(caso_id, "IA3", evaluacion.discrepancias)
            )
            no_observables.extend(evaluacion.no_observables)
        else:
            fase_ia3.casos.append(
                ResultadoCaso.omitido(caso_id, "IA3", "sin caso en el libro IA3")
            )

        if caso_id in ia4:
            fase_ia4.casos.append(
                ResultadoCaso.desde_discrepancias(
                    caso_id,
                    "IA4",
                    _evaluar_ia4(ia4[caso_id], envelope, criticidad),
                )
            )
        else:
            fase_ia4.casos.append(
                ResultadoCaso.omitido(caso_id, "IA4", "sin caso en el libro IA4")
            )

        if caso_id in final:
            evaluacion = sv6_build.evaluar_caso_determinista(
                caso_id=caso_id,
                envelope=envelope,
                resultado=resultado,
                ia3=None,
                final=final[caso_id],
                criticidad=criticidad,
            )
            fase_e2e.casos.append(
                ResultadoCaso.desde_discrepancias(caso_id, "E2E", evaluacion.discrepancias)
            )
            no_observables.extend(evaluacion.no_observables)
        else:
            fase_e2e.casos.append(
                ResultadoCaso.omitido(
                    caso_id, "E2E", "sin caso en el libro RESULTADO_FINAL"
                )
            )

    return [fase_ia3, fase_ia4, fase_e2e], sorted(set(no_observables))


def _evaluar_ia4(ia4: dict, envelope: dict, criticidad) -> list:
    """Compara el efecto de la conciliación sobre el envelope con lo esperado."""
    conciliaciones = sv5_valoracion.conciliaciones_desde_ground_truth(ia4, envelope)
    obtenidas = sv5_valoracion.proyectar_ia4(conciliaciones, envelope)
    esperadas = ia4.get("tablas", {}).get("conciliacion", [])
    return comparar_tablas(
        esperadas,
        obtenidas,
        criticidad,
        claves=("num_linea",),
        prefijo="IA4.conciliacion",
        observables=(
            "num_linea",
            "concilia",
            "linea_contrato_esperada",
            "precio_unitario_esperado",
        ),
        severidad_sobrantes="aviso",
    )


# --- Pasada completa --------------------------------------------------------


def corrida_completa(
    fixtures: Path,
    casos_pedidos: list[str] | None = None,
    proveedores: list[str] | None = None,
    directorio_albaranes: Path | None = None,
) -> tuple[list[ResultadoFase], list[str]]:
    """Las cuatro fases con LLM reales más el extremo-a-extremo (R9, R14)."""
    criticidad = cargar_criticidad()
    inputs = _filtrar(cargar_fixtures(fixtures, "inputs"), casos_pedidos)
    ia1 = _filtrar(cargar_fixtures(fixtures, "IA1"), casos_pedidos)
    ia2 = _filtrar(cargar_fixtures(fixtures, "IA2"), casos_pedidos)
    ia3 = cargar_fixtures(fixtures, "IA3")
    ia4 = cargar_fixtures(fixtures, "IA4")
    final = cargar_fixtures(fixtures, "final")

    invocados_ia1 = sv2_extraccion.proveedores_a_invocar("IA1", proveedores)
    invocados_ia2 = sv2_extraccion.proveedores_a_invocar("IA2", proveedores)
    sv5_valoracion.comprobar_claves(sorted(set(invocados_ia1 + invocados_ia2)))

    fase_ia1 = ResultadoFase(nombre="IA1", proveedores=invocados_ia1)
    fase_ia2 = ResultadoFase(nombre="IA2", proveedores=invocados_ia2)
    no_observables: list[str] = []

    trabajo_sv2 = []
    for caso_id, datos in sorted({**ia1, **ia2}.items()):
        ruta = sv2_extraccion.ruta_de_albaran(
            caso_id, directorio_albaranes or sv2_extraccion.RUTA_ALBARANES
        )
        if ruta is None:
            motivo = f"no existe el fichero del albarán de {caso_id}"
            fase_ia1.casos.append(ResultadoCaso.omitido(caso_id, "IA1", motivo))
            fase_ia2.casos.append(ResultadoCaso.omitido(caso_id, "IA2", motivo))
            continue
        trabajo_sv2.append(
            {
                "caso_id": caso_id,
                "fichero": str(ruta),
                "tipologia": datos.get("tipologia", ""),
            }
        )

    if trabajo_sv2:
        salida = sv2_extraccion.ejecutar_en_subproceso(
            {
                "casos": trabajo_sv2,
                "proveedores": sorted(set(invocados_ia1 + invocados_ia2)),
            }
        )
        for resultado in salida["resultados"]:
            caso_id = resultado["caso_id"]
            for proveedor, documentos in resultado["proveedores"].items():
                if caso_id in ia1 and proveedor in invocados_ia1:
                    fase_ia1.casos.append(
                        ResultadoCaso.desde_discrepancias(
                            f"{caso_id}/{proveedor}",
                            "IA1",
                            _comparar_tablas_de(
                                ia1[caso_id],
                                sv2_extraccion.proyectar_ia1(documentos["ia1"], caso_id),
                                criticidad,
                                (("cabeceras", ()), ("lineas", ("num_linea",))),
                                "IA1",
                            ),
                        )
                    )
                if caso_id in ia2 and proveedor in invocados_ia2:
                    fase_ia2.casos.append(
                        ResultadoCaso.desde_discrepancias(
                            f"{caso_id}/{proveedor}",
                            "IA2",
                            _comparar_tablas_de(
                                ia2[caso_id],
                                sv2_extraccion.proyectar_ia2(documentos["ia2"], caso_id),
                                criticidad,
                                (("contexto", ("num_linea", "campo_contexto")),),
                                "IA2",
                            ),
                        )
                    )

    fases_valoracion, no_observables_valoracion = _corrida_valoracion_real(
        inputs, ia3, ia4, final, criticidad, proveedores
    )
    no_observables.extend(no_observables_valoracion)
    return [fase_ia1, fase_ia2, *fases_valoracion], sorted(set(no_observables))


def _comparar_tablas_de(fixture, proyeccion, criticidad, tablas, prefijo) -> list:
    discrepancias = []
    for nombre, claves in tablas:
        discrepancias.extend(
            comparar_tablas(
                fixture.get("tablas", {}).get(nombre, []),
                proyeccion.get(nombre, []),
                criticidad,
                claves=claves,
                prefijo=f"{prefijo}.{nombre}",
                observables=None,
                severidad_sobrantes="aviso",
            )
        )
    return discrepancias


def _corrida_valoracion_real(
    inputs, ia3, ia4, final, criticidad, proveedores
) -> tuple[list[ResultadoFase], list[str]]:
    """IA3 e IA4 reales de sv5 y el build de sv6 con el envelope resultante."""
    proveedor = (proveedores or ["gemini"])[0]
    fase_ia3 = ResultadoFase(nombre="IA3", proveedores=[proveedor])
    fase_ia4 = ResultadoFase(nombre="IA4", proveedores=[proveedor])
    fase_e2e = ResultadoFase(nombre="E2E", proveedores=[proveedor])
    no_observables: list[str] = []

    if not inputs:
        motivo = "no hay ningún caso en evals/fixtures/inputs/"
        for fase in (fase_ia3, fase_ia4, fase_e2e):
            fase.motivo = motivo
        return [fase_ia3, fase_ia4, fase_e2e], no_observables

    salida_sv5 = sv5_valoracion.ejecutar_en_subproceso(
        {
            "proveedor": proveedor,
            "casos": [
                {
                    "caso_id": caso_id,
                    "contexto": sv5_valoracion.construir_contexto(datos),
                }
                for caso_id, datos in sorted(inputs.items())
            ],
        }
    )
    envelopes = {r["caso_id"]: r["envelope"] for r in salida_sv5["resultados"]}
    conciliaciones = {
        r["caso_id"]: r.get("conciliaciones", []) for r in salida_sv5["resultados"]
    }

    salida_sv6 = sv6_build.ejecutar_en_subproceso(
        {
            "casos": [
                {"caso_id": caso_id, "envelope": envelope}
                for caso_id, envelope in envelopes.items()
            ]
        }
    )
    resultados = {r["caso_id"]: r for r in salida_sv6["resultados"]}

    for caso_id, envelope in envelopes.items():
        resultado = resultados.get(caso_id)
        if resultado is None:
            fase_e2e.casos.append(
                ResultadoCaso.omitido(caso_id, "E2E", "sv6 no devolvió resultado")
            )
            continue
        for fase, nombre, fixture in (
            (fase_ia3, "IA3", ia3.get(caso_id)),
            (fase_e2e, "E2E", final.get(caso_id)),
        ):
            if fixture is None:
                fase.casos.append(
                    ResultadoCaso.omitido(caso_id, nombre, f"sin caso en el libro {nombre}")
                )
                continue
            evaluacion = sv6_build.evaluar_caso_determinista(
                caso_id=caso_id,
                envelope=envelope,
                resultado=resultado,
                ia3=fixture if nombre == "IA3" else None,
                final=fixture if nombre == "E2E" else None,
                criticidad=criticidad,
            )
            fase.casos.append(
                ResultadoCaso.desde_discrepancias(caso_id, nombre, evaluacion.discrepancias)
            )
            no_observables.extend(evaluacion.no_observables)

        if caso_id in ia4:
            fase_ia4.casos.append(
                ResultadoCaso.desde_discrepancias(
                    caso_id,
                    "IA4",
                    comparar_tablas(
                        ia4[caso_id].get("tablas", {}).get("conciliacion", []),
                        sv5_valoracion.proyectar_ia4(
                            conciliaciones.get(caso_id, []), envelope
                        ),
                        criticidad,
                        claves=("num_linea",),
                        prefijo="IA4.conciliacion",
                        observables=(
                            "num_linea",
                            "concilia",
                            "linea_contrato_esperada",
                            "precio_unitario_esperado",
                        ),
                    ),
                )
            )
        else:
            fase_ia4.casos.append(
                ResultadoCaso.omitido(caso_id, "IA4", "sin caso en el libro IA4")
            )

    return [fase_ia3, fase_ia4, fase_e2e], no_observables


# --- Orquestación y CLI -----------------------------------------------------


def _commit_actual(raiz: Path) -> str:
    proceso = subprocess.run(
        ["git", "-C", str(raiz), "rev-parse", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proceso.stdout.strip() if proceso.returncode == 0 else ""


def comprobar_peticion(con_llm: bool, fases: list[str]) -> None:
    """El gasto en LLM siempre es explícito (R10)."""
    if con_llm:
        return
    pedidas = FASES_SOLO_CON_LLM & set(fases)
    if pedidas:
        raise UsoIncorrecto(
            f"{', '.join(sorted(pedidas))} solo se pueden evaluar llamando a los "
            f"proveedores LLM reales. Añade --con-llm si quieres pagar esa "
            f"corrida, o quítalas de --fases."
        )


def ejecutar(opciones: argparse.Namespace) -> tuple[ResultadoPasada, list[str]]:
    """Ejecuta la corrida pedida y devuelve su resultado sin escribir nada."""
    fases = (
        [f.strip().upper() for f in opciones.fases.split(",") if f.strip()]
        if opciones.fases
        else list(FASES_COMPLETA if opciones.con_llm else FASES_DETERMINISTA)
    )
    comprobar_peticion(opciones.con_llm, fases)

    fixtures = Path(opciones.fixtures)
    casos = opciones.casos.split(",") if opciones.casos else None
    proveedores = opciones.proveedores.split(",") if opciones.proveedores else None

    if opciones.con_llm:
        resultados, no_observables = corrida_completa(fixtures, casos, proveedores)
    else:
        resultados, no_observables = corrida_determinista(fixtures, casos)

    pasada = ResultadoPasada(
        modo=MODO_COMPLETA if opciones.con_llm else MODO_DETERMINISTA,
        fases=[fase for fase in resultados if fase.nombre in fases],
        feature=opciones.feature or "",
        commit=_commit_actual(Path(opciones.fixtures).resolve().parent.parent),
        fecha=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    return pasada, no_observables


def ruta_de_informe(feature: str, directorio: Path | str = RUTA_PROGRESS) -> Path:
    """`progress/evals_F-XXX.md`, o `progress/evals_manual.md` sin feature."""
    nombre = f"evals_{feature}.md" if feature else "evals_manual.md"
    return Path(directorio) / nombre


def main(argv: list[str] | None = None) -> int:
    """CLI del runner. Códigos de salida: 0 VERDE, 1 ROJO, 2 NO_EVALUABLE (R16)."""
    analizador = argparse.ArgumentParser(
        prog="python -m evals.runner",
        description="Ejecuta los evals de IA contra el ground truth.",
    )
    analizador.add_argument(
        "--con-llm",
        action="store_true",
        help="pasada completa con llamadas LLM reales (cuesta dinero)",
    )
    analizador.add_argument("--feature", default="")
    analizador.add_argument("--casos", default="", help="lista de caso_id separados por coma")
    analizador.add_argument("--proveedores", default="", help="amplía los proveedores de IA1/IA2")
    analizador.add_argument("--fases", default="", help=f"por defecto {','.join(FASES_DETERMINISTA)}")
    analizador.add_argument("--fixtures", default=str(RUTA_FIXTURES))
    analizador.add_argument("--informes", default=str(RUTA_PROGRESS))
    opciones = analizador.parse_args(argv)

    try:
        pasada, no_observables = ejecutar(opciones)
    except (UsoIncorrecto, sv5_valoracion.ClavesAusentes) as error:
        print(str(error), file=sys.stderr)
        return 2

    destino = ruta_de_informe(opciones.feature, opciones.informes)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(render(pasada, no_observables), encoding="utf-8")

    print(f"{pasada.veredicto()} · informe en {destino}")
    return pasada.codigo_salida()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
