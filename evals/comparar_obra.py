# evals/comparar_obra.py
"""Compara la OBRA que lee IA1 con el prompt de `dev` y con el de esta rama.

    python -m evals.comparar_obra --casos GEN-001,HOR-003 [--repeticiones 3]
        [--variante dev|rama|ambas] [--base <ref>] [--salida <dir>]

La variante `dev` usa el `prompts.yaml` de la referencia `--base` (por
defecto la rama `dev`). Desde que F-048 está en `dev`, medir el prompt de
antes contra el nuevo pide `--base 1807e83`, el `dev` de antes de F-048: con
la base por defecto las dos variantes llevarían el prompt nuevo.

Por qué existe: la pasada con LLM de F-048 no pudo decir si el prompt nuevo
empeora `obra_codigo`. El banco no la compara (está a NO_COMPARAR en los 59
casos) y el modo `completa` corre IA1 sin la lista de obras activas
(`progress/analisis_evals_F-048.md`). Aquí se mide directamente: SOLO la
fase 1, sin correo, con el proveedor de fase 1 de producción
(`IA_PRIMERA_FASE`, gemini por defecto) y CON la lista de obras activas
consultada a sigrid-api (solo lectura, una vez por corrida). Cada variante se
repite N veces para separar la señal del prompt del ruido del propio LLM.

Cuesta dinero: 1 llamada al LLM por caso, variante y repetición. Antes de
gastar nada se para si falta la clave del proveedor, si sigrid-api no está
configurado o no responde, o si ningún caso tiene albarán.

Salidas:
- en `--salida` (por defecto `evals/salidas/comparar_obra/<fecha-hora>/`,
  ignorado por git): un JSON por variante y repetición (`caso_id → obra`) y
  `resumen.md`, CON los valores;
- en `--resumen` (por defecto `progress/comparar_obra_F-048.md`): recuentos y
  caso_id por categoría, SIN ningún código ni nombre de obra. Es el único que
  se versiona.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from evals.procesos import sv2_extraccion, sv2_obra
from evals.procesos.errores import avisar, describir_error
from evals.procesos.sv5_valoracion import (
    MODELOS_POR_PROVEEDOR,
    ClavesAusentes,
    comprobar_claves,
)

RAIZ_REPO = sv2_extraccion.RAIZ_REPO

#: Dónde van las corridas (con valores). `evals/salidas/` lo ignora git.
RUTA_SALIDAS = RAIZ_REPO / "evals" / "salidas" / "comparar_obra"

#: El resumen SIN valores que se versiona.
RUTA_RESUMEN_VERSIONABLE = RAIZ_REPO / "progress" / "comparar_obra_F-048.md"

VARIANTES = sv2_obra.VARIANTES

#: Qué significa cada categoría, en el orden en que se informan.
CATEGORIAS_DOS_VARIANTES = {
    "difiere": "dev y rama estables consigo mismas y DISTINTAS entre sí: señal del prompt",
    "inestable": "alguna variante cambia de obra entre repeticiones: ruido del LLM",
    "identico": "dev y rama estables y con la misma obra",
    "con_errores": "alguna repetición falló o no hay albarán: no se puede juzgar",
}
CATEGORIAS_UNA_VARIANTE = {
    "estable": "la misma obra en todas las repeticiones",
    "inestable": "cambia de obra entre repeticiones: ruido del LLM",
    "con_errores": "alguna repetición falló o no hay albarán: no se puede juzgar",
}


class Parada(RuntimeError):
    """La corrida no puede empezar. Se lanza siempre ANTES de llamar al LLM."""


@dataclass
class Dependencias:
    """Lo que toca el mundo exterior; los tests pasan dobles."""

    prompt_de_dev: Callable[..., Path] = sv2_obra.prompt_de_dev
    prompt_de_rama: Callable[[], Path] = sv2_obra.prompt_de_rama
    consultar_obras: Callable[[dict], list | None] = sv2_obra.consultar_obras
    montar_extractor: Callable[..., Callable[[str, str, Path], dict]] = sv2_obra.montar_extractor


@dataclass
class Corrida:
    """Lo que devolvió IA1: `resultados[variante][repeticion - 1][caso_id]`."""

    casos: list[str]
    variantes: list[str]
    repeticiones: int
    proveedor: str
    modelo: str
    obras: int
    resultados: dict[str, list[dict[str, dict]]] = field(default_factory=dict)


# --- Corrida -------------------------------------------------------------------


def correr(
    casos: dict[str, Path | None],
    variantes: list[str],
    repeticiones: int,
    extraer: Callable[[str, str, Path], dict],
) -> dict[str, list[dict[str, dict]]]:
    """Repetición a repetición, variante a variante y caso a caso, cada uno AISLADO.

    Las variantes se intercalan dentro de cada repetición para que un cambio
    del proveedor a mitad de corrida afecte a las dos por igual. Un fallo se
    anota con su forma (`describir_error`, sin el texto de la excepción) y se
    sigue: una corrida facturada no se pierde por un caso.
    """
    resultados: dict[str, list[dict[str, dict]]] = {v: [] for v in variantes}
    for repeticion in range(1, repeticiones + 1):
        for variante in variantes:
            vuelta: dict[str, dict] = {}
            for caso_id, ruta in casos.items():
                vuelta[caso_id] = _un_caso(variante, repeticion, caso_id, ruta, extraer)
            resultados[variante].append(vuelta)
    return resultados


def _un_caso(variante, repeticion, caso_id, ruta, extraer) -> dict:
    etiqueta = f"r{repeticion} · {variante} · caso {caso_id}"
    if ruta is None:
        return {
            "error": {
                "fase": "preproceso",
                "tipo": "SinAlbaran",
                "motivo": f"no existe el fichero del albarán de {caso_id}",
            }
        }
    try:
        obra = extraer(variante, caso_id, ruta)
    except Exception as error:  # noqa: BLE001 - se aísla el caso, no se oculta
        fallo = describir_error(error, "IA1")
        avisar("comparar_obra", f"{etiqueta}: error en IA1 · {fallo['motivo']}")
        return {"error": fallo}
    avisar("comparar_obra", f"{etiqueta}: ok")
    return {"obra_codigo": obra.get("obra_codigo"), "obra_nombre": obra.get("obra_nombre")}


# --- Clasificación ---------------------------------------------------------------


def _codigo(resultado: dict) -> str | None:
    """El código comparable: sin espacios alrededor; `None` (y vacío) es «sin obra»."""
    valor = resultado.get("obra_codigo")
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def clasificar_caso(por_variante: dict[str, list[dict]]) -> dict:
    """Estabilidad de cada variante, si coinciden y la categoría del caso.

    Se compara SOLO `obra_codigo`: el nombre acompaña en el detalle, pero una
    obra escrita de otra manera es la misma obra. Con una repetición que
    falló, la estabilidad de esa variante es `None` y el caso va a
    `con_errores`.
    """
    estable: dict[str, bool | None] = {}
    valor: dict[str, str | None] = {}
    con_errores = False
    for variante, resultados in por_variante.items():
        if not resultados or any("error" in r for r in resultados):
            estable[variante] = None
            con_errores = True
            continue
        codigos = {_codigo(r) for r in resultados}
        estable[variante] = len(codigos) == 1
        valor[variante] = next(iter(codigos)) if len(codigos) == 1 else None

    coinciden: bool | None = None
    if con_errores:
        categoria = "con_errores"
    elif not all(estable.values()):
        categoria = "inestable"
    elif len(por_variante) == 1:
        categoria = "estable"
    else:
        coinciden = len(set(valor.values())) == 1
        categoria = "identico" if coinciden else "difiere"
    return {"estable": estable, "coinciden": coinciden, "categoria": categoria}


def clasificar(corrida: Corrida) -> dict[str, dict]:
    """La clasificación de cada caso de la corrida."""
    return {
        caso_id: clasificar_caso(
            {
                variante: [vuelta[caso_id] for vuelta in corrida.resultados[variante]]
                for variante in corrida.variantes
            }
        )
        for caso_id in corrida.casos
    }


def _categorias(corrida: Corrida) -> dict[str, str]:
    return CATEGORIAS_DOS_VARIANTES if len(corrida.variantes) > 1 else CATEGORIAS_UNA_VARIANTE


def _etiqueta_sin_valores(caso_id: str, clasificacion: dict, corrida: Corrida) -> str:
    """El caso con lo que explica su categoría, sin ningún valor de obra."""
    if clasificacion["categoria"] == "inestable" and len(corrida.variantes) > 1:
        inestables = [v for v, e in clasificacion["estable"].items() if e is False]
        return f"{caso_id} ({' y '.join(inestables)})"
    if clasificacion["categoria"] == "con_errores":
        fallos = []
        for variante in corrida.variantes:
            for indice, vuelta in enumerate(corrida.resultados[variante], start=1):
                error = vuelta[caso_id].get("error")
                if error:
                    fallos.append(f"{variante} r{indice}: {error['fase']} · {error['tipo']}")
        return f"{caso_id} ({'; '.join(fallos)})"
    return caso_id


# --- Informes --------------------------------------------------------------------


def _cabecera(corrida: Corrida, commits: dict[str, str], fecha: str) -> list[str]:
    return [
        f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · dev `{commits.get('dev') or '?'}`",
        f"- IA1 (solo fase 1, sin correo): proveedor `{corrida.proveedor}`, modelo `{corrida.modelo}`",
        (
            f"- Variantes: {', '.join(corrida.variantes)} · repeticiones: {corrida.repeticiones} · "
            f"casos: {len(corrida.casos)}"
        ),
        f"- Lista de obras activas: {corrida.obras} obras, una sola consulta a sigrid-api",
        (
            "- Estable = el mismo `obra_codigo` en todas las repeticiones (el nombre no cuenta)."
            + (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones == 1 else "")
        ),
    ]


def _tabla_recuentos(corrida: Corrida, clasificacion: dict[str, dict]) -> list[str]:
    lineas = ["| Categoría | Nº | Qué significa |", "|---|---|---|"]
    for categoria, texto in _categorias(corrida).items():
        numero = sum(1 for c in clasificacion.values() if c["categoria"] == categoria)
        lineas.append(f"| {categoria} | {numero} | {texto} |")
    return lineas


def render_versionable(
    corrida: Corrida, clasificacion: dict[str, dict], commits: dict[str, str], fecha: str, salida: str
) -> str:
    """Recuentos y caso_id por categoría. NINGÚN código ni nombre de obra."""
    lineas = [
        "<!-- progress/comparar_obra_F-048.md -->",
        "# F-048 · Comparador de obra dev/rama",
        "",
        "Generado por `python -m evals.comparar_obra`. **Sin valores**: solo recuentos y caso_id.",
        f"Los códigos de obra están en `{salida}`, que git ignora.",
        "",
        *_cabecera(corrida, commits, fecha),
        "",
        "## Recuentos",
        "",
        *_tabla_recuentos(corrida, clasificacion),
        "",
        "## Casos por categoría",
        "",
    ]
    for categoria in _categorias(corrida):
        casos = [
            _etiqueta_sin_valores(caso_id, c, corrida)
            for caso_id, c in clasificacion.items()
            if c["categoria"] == categoria
        ]
        lineas.append(f"- **{categoria}**: {', '.join(casos) if casos else '(ninguno)'}")
    return "\n".join(lineas) + "\n"


def _valor(resultado: dict) -> str:
    if "error" in resultado:
        return f"ERROR ({resultado['error']['tipo']})"
    codigo = resultado.get("obra_codigo")
    return "null" if codigo is None else f"`{codigo}`"


def _si_no(valor: bool | None) -> str:
    return "—" if valor is None else ("sí" if valor else "no")


def render_detalle(
    corrida: Corrida, clasificacion: dict[str, dict], commits: dict[str, str], fecha: str
) -> str:
    """El resumen CON valores, para el directorio ignorado."""
    columnas = [
        f"{variante} r{indice}"
        for variante in corrida.variantes
        for indice in range(1, corrida.repeticiones + 1)
    ]
    estables = [f"{variante} estable" for variante in corrida.variantes]
    coinciden = ["coinciden"] if len(corrida.variantes) > 1 else []
    encabezado = ["caso", *columnas, *estables, *coinciden, "categoría"]
    lineas = [
        "# Comparador de obra dev/rama · detalle CON valores (no versionar)",
        "",
        *_cabecera(corrida, commits, fecha),
        "",
        *_tabla_recuentos(corrida, clasificacion),
        "",
        "## Por caso",
        "",
        "| " + " | ".join(encabezado) + " |",
        "|" + "---|" * len(encabezado),
    ]
    for caso_id in corrida.casos:
        c = clasificacion[caso_id]
        celdas = [caso_id]
        celdas += [
            _valor(vuelta[caso_id])
            for variante in corrida.variantes
            for vuelta in corrida.resultados[variante]
        ]
        celdas += [_si_no(c["estable"][v]) for v in corrida.variantes]
        if coinciden:
            celdas.append(_si_no(c["coinciden"]))
        celdas.append(c["categoria"])
        lineas.append("| " + " | ".join(celdas) + " |")

    nombres = [
        f"- {caso_id} · {variante} r{indice}: {vuelta[caso_id].get('obra_nombre')!r}"
        for caso_id in corrida.casos
        for variante in corrida.variantes
        for indice, vuelta in enumerate(corrida.resultados[variante], start=1)
        if "error" not in vuelta[caso_id]
    ]
    errores = [
        f"- {caso_id} · {variante} r{indice}: {vuelta[caso_id]['error']['motivo']}"
        for caso_id in corrida.casos
        for variante in corrida.variantes
        for indice, vuelta in enumerate(corrida.resultados[variante], start=1)
        if "error" in vuelta[caso_id]
    ]
    lineas += ["", "## obra_nombre leído", "", *(nombres or ["(ninguno)"])]
    lineas += ["", "## Errores", "", *(errores or ["(ninguno)"])]
    return "\n".join(lineas) + "\n"


def escribir(
    corrida: Corrida, salida: Path, resumen: Path, commits: dict[str, str], fecha: str
) -> dict[str, dict]:
    """Los JSON y el detalle en `salida`; el resumen sin valores en `resumen`."""
    clasificacion = clasificar(corrida)
    salida.mkdir(parents=True, exist_ok=True)
    for variante in corrida.variantes:
        for indice, vuelta in enumerate(corrida.resultados[variante], start=1):
            carga = {
                "variante": variante,
                "repeticion": indice,
                "proveedor": corrida.proveedor,
                "modelo": corrida.modelo,
                "casos": vuelta,
            }
            (salida / f"{variante}_r{indice}.json").write_text(
                json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    (salida / "resumen.md").write_text(
        render_detalle(corrida, clasificacion, commits, fecha), encoding="utf-8"
    )
    resumen.parent.mkdir(parents=True, exist_ok=True)
    resumen.write_text(
        render_versionable(corrida, clasificacion, commits, fecha, _relativa(salida)),
        encoding="utf-8",
    )
    return clasificacion


def _relativa(ruta: Path) -> str:
    try:
        return Path(ruta).resolve().relative_to(RAIZ_REPO).as_posix()
    except ValueError:
        return Path(ruta).as_posix()


# --- Preparación: todo lo que puede parar la corrida, antes de gastar -------------


def _variantes(pedida: str) -> list[str]:
    return list(VARIANTES) if pedida == "ambas" else [pedida]


def comprobar_sigrid(entorno: dict) -> None:
    faltan = sv2_obra.faltan_variables_sigrid(entorno)
    if faltan:
        raise Parada(
            "sigrid-api no está configurado: faltan en el entorno "
            + ", ".join(faltan)
            + ". Sin la lista de obras activas la comparación no se parece a producción. "
            "No se ha llamado a ningún LLM."
        )


def localizar_albaranes(casos: list[str], directorio: Path) -> dict[str, Path | None]:
    rutas = {caso: sv2_extraccion.ruta_de_albaran(caso, directorio) for caso in casos}
    if not any(rutas.values()):
        raise Parada(
            f"ningún caso tiene albarán en {directorio}. No se ha llamado a ningún LLM."
        )
    return rutas


def directorio_por_defecto() -> Path:
    return RUTA_SALIDAS / dt.datetime.now().astimezone().strftime("%Y-%m-%d-%H%M%S")


def _commit(referencia: str) -> str:
    proceso = subprocess.run(
        ["git", "-C", str(RAIZ_REPO), "rev-parse", "--short", referencia],
        capture_output=True,
        text=True,
        check=False,
    )
    return proceso.stdout.strip() if proceso.returncode == 0 else ""


def ejecutar(opciones: argparse.Namespace, entorno: dict, dependencias: Dependencias) -> int:
    """Prepara (y para si algo falta), corre y escribe. Devuelve el código de salida."""
    casos = opciones.lista_casos
    variantes = _variantes(opciones.variante)
    proveedor = sv2_extraccion.proveedores_a_invocar("IA1", None, entorno)[0]
    comprobar_claves([proveedor], entorno)
    rutas = localizar_albaranes(casos, Path(opciones.albaranes))
    comprobar_sigrid(entorno)

    with tempfile.TemporaryDirectory(prefix="comparar_obra_") as temporal:
        prompts: dict[str, Path] = {}
        if "dev" in variantes:
            prompts["dev"] = dependencias.prompt_de_dev(Path(temporal), base=opciones.base)
        if "rama" in variantes:
            prompts["rama"] = dependencias.prompt_de_rama()

        obras = dependencias.consultar_obras(entorno)
        if not obras:
            raise Parada(
                "sigrid-api no está disponible: no ha devuelto la lista de obras activas "
                "(el detalle, si lo hay, está en el log de arriba). Sin ella la comparación "
                "no se parece a producción. No se ha llamado a ningún LLM."
            )

        variable_modelo, modelo_por_defecto = MODELOS_POR_PROVEEDOR.get(proveedor, ("", ""))
        modelo = entorno.get(variable_modelo) or modelo_por_defecto
        llamadas = sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones
        avisar(
            "comparar_obra",
            f"{llamadas} llamadas a {proveedor} ({modelo}) · {len(obras)} obras activas · "
            f"variantes {', '.join(variantes)}",
        )
        extraer = dependencias.montar_extractor(prompts, obras, proveedor, entorno)
        corrida = Corrida(
            casos=casos,
            variantes=variantes,
            repeticiones=opciones.repeticiones,
            proveedor=proveedor,
            modelo=modelo,
            obras=len(obras),
            resultados=correr(rutas, variantes, opciones.repeticiones, extraer),
        )

    salida = Path(opciones.salida) if opciones.salida else directorio_por_defecto()
    resumen = Path(opciones.resumen)
    fecha = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    commits = {"rama": _commit("HEAD"), "dev": _commit(opciones.base)}
    escribir(corrida, salida, resumen, commits, fecha)

    print(f"comparar_obra: detalle con valores en {salida}")
    print(f"comparar_obra: resumen sin valores en {resumen}")
    alguna_extraccion = any(
        "error" not in resultado
        for vueltas in corrida.resultados.values()
        for vuelta in vueltas
        for resultado in vuelta.values()
    )
    return 0 if alguna_extraccion else 1


def _analizador() -> argparse.ArgumentParser:
    analizador = argparse.ArgumentParser(
        prog="python -m evals.comparar_obra",
        description=(
            "Compara la obra que lee IA1 (fase 1, sin correo, con la lista de obras de "
            "sigrid-api) con el prompt de dev y con el de esta rama. Llama a un LLM real: "
            "cuesta dinero."
        ),
    )
    analizador.add_argument("--casos", required=True, help="caso_id separados por coma")
    analizador.add_argument("--repeticiones", type=int, default=3, help="por defecto 3")
    analizador.add_argument(
        "--variante", choices=("dev", "rama", "ambas"), default="ambas", help="por defecto ambas"
    )
    analizador.add_argument(
        "--base",
        default=sv2_obra.BASE_POR_DEFECTO,
        help="referencia de git de la que sale el prompt de la variante dev (por defecto "
        "dev; 1807e83 es el dev de antes de F-048)",
    )
    analizador.add_argument(
        "--salida",
        default="",
        help="directorio de la corrida, CON valores (por defecto "
        "evals/salidas/comparar_obra/<fecha-hora>/, ignorado por git)",
    )
    analizador.add_argument(
        "--resumen",
        default=str(RUTA_RESUMEN_VERSIONABLE),
        help="resumen SIN valores para versionar (por defecto progress/comparar_obra_F-048.md)",
    )
    analizador.add_argument(
        "--albaranes",
        default=str(sv2_extraccion.RUTA_ALBARANES),
        help="directorio de los albaranes (por defecto el del banco, evals/inputs/albaranes)",
    )
    return analizador


def main(
    argv: list[str] | None = None,
    *,
    entorno: dict | None = None,
    dependencias: Dependencias | None = None,
) -> int:
    """CLI. Códigos: 0 hecho, 1 ninguna extracción salió, 2 parada antes de gastar."""
    analizador = _analizador()
    opciones = analizador.parse_args(argv)
    casos = list(dict.fromkeys(c.strip() for c in opciones.casos.split(",") if c.strip()))
    if not casos:
        analizador.error("--casos no puede estar vacío")
    if opciones.repeticiones < 1:
        analizador.error("--repeticiones tiene que ser 1 o más")
    opciones.lista_casos = casos

    try:
        return ejecutar(
            opciones,
            entorno if entorno is not None else dict(os.environ),
            dependencias or Dependencias(),
        )
    except (Parada, ClavesAusentes, sv2_obra.PromptDevNoDisponible) as error:
        print(f"comparar_obra: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
