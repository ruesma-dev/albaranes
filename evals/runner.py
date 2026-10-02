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

from evals.comparador import campos_no_observables, comparar_tablas
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

    resultados, motivo_muerte = _build_sv6(envelopes, (fase_ia3, fase_e2e))

    for caso_id, envelope in envelopes.items():
        resultado = resultados.get(caso_id)
        motivo_sv6 = _motivo_sv6(resultado, motivo_muerte)
        if motivo_sv6:
            # Sin build no hay IA3 ni E2E; IA4 no depende de sv6 y se evalúa.
            fase_ia3.casos.append(ResultadoCaso.con_error(caso_id, "IA3", motivo_sv6))
        elif caso_id in ia3:
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

        if motivo_sv6:
            fase_e2e.casos.append(ResultadoCaso.con_error(caso_id, "E2E", motivo_sv6))
        elif caso_id in final:
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


def _build_sv6(envelopes: dict[str, dict], fases) -> tuple[dict[str, dict], str]:
    """El build de sv6 de todos los envelopes; si el subproceso muere, las fases
    que dependen de él (`fases`) se quedan con el motivo y sin resultados."""
    salida, motivo_muerte = _ejecutar_aislado(
        "sv6",
        sv6_build.ejecutar_en_subproceso,
        {
            "casos": [
                {"caso_id": caso_id, "envelope": envelope}
                for caso_id, envelope in envelopes.items()
            ]
        },
    )
    if salida is None:
        for fase in fases:
            fase.motivo = motivo_muerte
    resultados = {r.get("caso_id"): r for r in (salida or {}).get("resultados", [])}
    return resultados, motivo_muerte


def _motivo_sv5(resultado: dict | None) -> str:
    """Por qué no hay valoración de sv5 para un caso; vacío si la hay."""
    if resultado is None:
        return "sv5 no devolvió resultado"
    error = resultado.get("error")
    if error:
        return f"ERROR en {error.get('fase') or 'sv5'} (sv5) · {error.get('motivo', '')}"
    return ""


def _motivo_sv6(resultado: dict | None, motivo_muerte: str) -> str:
    """Por qué no hay build de sv6 para un caso; vacío si lo hay."""
    if resultado is None:
        return motivo_muerte or "sv6 no devolvió resultado"
    error = resultado.get("error")
    if error:
        return f"ERROR en el build de sv6 · {error.get('motivo', '')}"
    return ""


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
        _evaluar_sv2(
            trabajo_sv2,
            sorted(set(invocados_ia1 + invocados_ia2)),
            {"IA1": (fase_ia1, ia1, invocados_ia1), "IA2": (fase_ia2, ia2, invocados_ia2)},
            criticidad,
            no_observables,
        )

    fases_valoracion, no_observables_valoracion = _corrida_valoracion_real(
        inputs, ia3, ia4, final, criticidad, proveedores
    )
    no_observables.extend(no_observables_valoracion)
    return [fase_ia1, fase_ia2, *fases_valoracion], sorted(set(no_observables))


#: Cómo se compara cada fase de sv2: la proyección y las tablas con sus claves.
_COMPARACION_SV2 = {
    "IA1": (sv2_extraccion.proyectar_ia1, (("cabeceras", ()), ("lineas", ("num_linea",)))),
    "IA2": (sv2_extraccion.proyectar_ia2, (("contexto", ("num_linea", "campo_contexto")),)),
}


def _ejecutar_aislado(servicio: str, ejecutar, trabajo: dict) -> tuple[dict | None, str]:
    """Lanza un subproceso de evals; si muere, devuelve el motivo en vez de reventar.

    Hasta el 2026-09-24 el `RuntimeError` subía hasta el CLI y la pasada moría
    sin informe. El detalle del fallo (el stderr del hijo) va a la consola y
    NO al motivo: el motivo acaba en el informe, que se versiona sin valores
    (R31 de F-047), y ese stderr puede traerlos.
    """
    try:
        return ejecutar(trabajo), ""
    except (RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"runner: el subproceso de {servicio} murió:\n{error}", file=sys.stderr)
        return None, (
            f"el subproceso de {servicio} murió sin devolver resultados "
            f"({type(error).__name__}); el detalle está en la salida de error de "
            f"la pasada, no aquí, porque puede llevar valores del albarán"
        )


def _evaluar_sv2(trabajo, proveedores, fases, criticidad, no_observables) -> None:
    """IA1 e IA2 de todos los casos; un caso roto sale ERROR con su motivo.

    Todos los motivos de aquí nacen de un fallo —el subproceso murió, no
    devolvió el caso o el caso reventó—, así que ninguno es un OMITIDO (CR-E2).
    """
    salida, motivo_muerte = _ejecutar_aislado(
        "sv2",
        sv2_extraccion.ejecutar_en_subproceso,
        {"casos": trabajo, "proveedores": proveedores},
    )
    if salida is None:
        for fase, _, _ in fases.values():
            fase.motivo = motivo_muerte
    resultados = {r.get("caso_id"): r for r in (salida or {}).get("resultados", [])}

    for pedido in trabajo:
        caso_id = pedido["caso_id"]
        resultado = resultados.get(caso_id)
        for proveedor in proveedores:
            if resultado is None:
                motivos = dict.fromkeys(fases, motivo_muerte or "sv2 no devolvió resultado")
            elif resultado.get("error"):
                motivos = _motivos_de_error(resultado["error"])
            else:
                documentos = resultado.get("proveedores", {}).get(proveedor)
                if documentos is None:
                    motivos = dict.fromkeys(fases, "sv2 no devolvió resultado")
                else:
                    motivos = _motivos_de_error(documentos.get("error"))
            for nombre, (fase, fixtures, invocados) in fases.items():
                if caso_id not in fixtures or proveedor not in invocados:
                    continue
                etiqueta = f"{caso_id}/{proveedor}"
                if motivos.get(nombre):
                    fase.casos.append(ResultadoCaso.con_error(etiqueta, nombre, motivos[nombre]))
                    continue
                proyectar, tablas = _COMPARACION_SV2[nombre]
                fase.casos.append(
                    ResultadoCaso.desde_discrepancias(
                        etiqueta,
                        nombre,
                        _comparar_tablas_de(
                            fixtures[caso_id],
                            proyectar(documentos[nombre.lower()], caso_id),
                            criticidad,
                            tablas,
                            nombre,
                            no_observables,
                        ),
                    )
                )


def _motivos_de_error(error: dict | None) -> dict[str, str]:
    """Qué fases no se pueden evaluar por el error de sv2, y por qué.

    Si falla IA1, IA2 ni se llamó; si falla IA2, lo de IA1 vale y se evalúa.
    Un fallo antes de IA1 (el preproceso del albarán) deja fuera las dos.
    """
    if not error:
        return {}
    fase, motivo = error.get("fase", ""), error.get("motivo", "")
    if fase == "IA2":
        return {"IA2": f"ERROR en IA2 · {motivo}"}
    if fase == "IA1":
        return {"IA1": f"ERROR en IA1 · {motivo}", "IA2": f"no se evaluó: falló IA1 · {motivo}"}
    return dict.fromkeys(("IA1", "IA2"), f"ERROR en {fase or 'sv2'} · {motivo}")


def _comparar_tablas_de(
    fixture, proyeccion, criticidad, tablas, prefijo, no_observables=None
) -> list:
    """Compara IA1/IA2 SOLO por lo que la corrida ve, como ya hacen IA3 e IA4.

    Sin esta poda, el ground truth le exigía a la extracción las columnas de
    control del banco —`caso_id`, `fichero_albaran`, `comentario`— y los campos
    que sv2 no extrae (`unidad`, `descuentos`, F-024). En la pasada del
    2026-09-16 eso fueron 258 fallos de ruido que tapaban los 94 defectos de
    verdad (R25). Lo podado se declara en el informe, no desaparece (R26).
    """
    discrepancias = []
    for nombre, claves in tablas:
        esperadas = fixture.get("tablas", {}).get(nombre, [])
        observables = sv2_extraccion.OBSERVABLES.get(nombre)
        discrepancias.extend(
            comparar_tablas(
                esperadas,
                proyeccion.get(nombre, []),
                criticidad,
                claves=claves,
                prefijo=f"{prefijo}.{nombre}",
                observables=observables,
                severidad_sobrantes="aviso",
            )
        )
        if observables is not None and no_observables is not None:
            no_observables.extend(campos_no_observables(esperadas, observables))
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

    fases = (fase_ia3, fase_ia4, fase_e2e)
    salida_sv5, motivo_muerte_sv5 = _ejecutar_aislado(
        "sv5",
        sv5_valoracion.ejecutar_en_subproceso,
        {
            "proveedor": proveedor,
            "casos": [
                {
                    "caso_id": caso_id,
                    "contexto": sv5_valoracion.construir_contexto(datos),
                }
                for caso_id, datos in sorted(inputs.items())
            ],
        },
    )
    if salida_sv5 is None:
        for fase in fases:
            fase.motivo = motivo_muerte_sv5
            fase.casos.extend(
                ResultadoCaso.con_error(caso_id, fase.nombre, motivo_muerte_sv5)
                for caso_id in sorted(inputs)
            )
        return list(fases), no_observables

    por_caso = {r.get("caso_id"): r for r in salida_sv5.get("resultados", [])}
    envelopes: dict[str, dict] = {}
    conciliaciones: dict[str, list] = {}
    for caso_id in sorted(inputs):
        resultado_sv5 = por_caso.get(caso_id)
        motivo = _motivo_sv5(resultado_sv5)
        if motivo:
            # Sin la valoración de sv5 no hay envelope: ni IA3, ni IA4, ni build.
            for fase in fases:
                fase.casos.append(ResultadoCaso.con_error(caso_id, fase.nombre, motivo))
            continue
        envelopes[caso_id] = resultado_sv5["envelope"]
        conciliaciones[caso_id] = resultado_sv5.get("conciliaciones", [])

    resultados, motivo_muerte = (
        _build_sv6(envelopes, (fase_ia3, fase_e2e)) if envelopes else ({}, "")
    )

    for caso_id, envelope in envelopes.items():
        resultado = resultados.get(caso_id)
        motivo_sv6 = _motivo_sv6(resultado, motivo_muerte)
        for fase, nombre, fixture in (
            (fase_ia3, "IA3", ia3.get(caso_id)),
            (fase_e2e, "E2E", final.get(caso_id)),
        ):
            if motivo_sv6:
                fase.casos.append(ResultadoCaso.con_error(caso_id, nombre, motivo_sv6))
                continue
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
    destino.write_text(render(pasada, no_observables=no_observables), encoding="utf-8")

    print(f"{pasada.veredicto()} · informe en {destino}")
    return pasada.codigo_salida()


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
