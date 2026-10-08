# evals/comparar_proveedor.py
"""Compara el PROVEEDOR que leen IA1 e IA2 con los YAML de la base y con los de esta rama (F-064).

    python -m evals.comparar_proveedor [--casos FER-001,HOR-005] [--repeticiones 3]
        [--variante base|rama|ambas] [--base <ref>] [--albaranes <dir>]
        [--salida <dir>] [--resumen <fichero>]

Por qué existe: el banco no mide el CIF del proveedor (`proveedor_cif` está a
NO_COMPARAR en los casos de IA1, IA2 solo compara `contexto_linea` y el E2E no
lo observa). F-064 cambia el prompt de IA1 y la checklist de IA2 para que el
CIF del CLIENTE (la constructora) nunca salga como proveedor; aquí se mide.

Por caso, variante y repetición: fase 1 con el proveedor de `IA_PRIMERA_FASE`
y fase 2 con el de `IA_SEGUNDA_FASE` (prompt según la tipología del caso,
como el runner), sin correo, sin lista de obras y sin contexto de Sigrid. El
CIF tras IA1 y tras IA2 se clasifica en `emisor` (el de
`evals/fixtures/final/<caso>.json`), `cliente` (una empresa del cliente),
`nulo` u `otro`; un fallo cuenta como `error`. Con varias repeticiones, la
categoría de cada caso es la mayoritaria (empate ⇒ `inestable`).

Criterios (specs/F-064-proveedor-en-prompts/design.md §7):
- C1 · en la rama, 0 ejecuciones con CIF `cliente` tras IA2; tras IA1, ≤ base.
- C2 · casos con mayoría `emisor`: rama ≥ base, tras IA1 y tras IA2.
- C3 · ningún caso con mayoría `emisor` en base la pierde en la rama.

Cuesta dinero: 2 llamadas (IA1 e IA2) por caso, variante y repetición. Antes
de gastar nada se para (código 2) si falta la clave de algún proveedor, si
ningún caso tiene albarán, si a un caso le falta el CIF esperado o si el
`git show` de la base falla.

Salidas:
- en `--salida` (por defecto `evals/salidas/comparar_proveedor/<fecha-hora>/`,
  ignorado por git): un JSON por variante y repetición y `resumen.md`, CON
  los CIF y los nombres;
- en `--resumen` (por defecto `progress/comparar_proveedor_F-064.md`):
  recuentos, caso_id por categoría y veredicto, SIN ningún CIF ni nombre.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from ruesma_comun.proveedores import cifs_propios, es_cif_propio, normalizar_cif

from evals.procesos import sv2_extraccion, sv2_proveedor
from evals.procesos.errores import avisar, describir_error
from evals.procesos.sv5_valoracion import (
    MODELOS_POR_PROVEEDOR,
    ClavesAusentes,
    comprobar_claves,
)

RAIZ_REPO = sv2_extraccion.RAIZ_REPO

#: Dónde van las corridas (con valores). `evals/salidas/` lo ignora git.
RUTA_SALIDAS = RAIZ_REPO / "evals" / "salidas" / "comparar_proveedor"

#: El resumen SIN valores que se versiona.
RUTA_RESUMEN_VERSIONABLE = RAIZ_REPO / "progress" / "comparar_proveedor_F-064.md"

#: Fixtures del banco: el CIF esperado (final) y la tipología (IA1).
RUTA_FIXTURES = RAIZ_REPO / "evals" / "fixtures"

#: Los 11 casos con el cliente impreso y los 8 controles (design.md §7).
CASOS_CON_CLIENTE = (
    "FER-001", "FER-002", "FER-003",
    "HOR-005", "HOR-006", "HOR-007", "HOR-008", "HOR-009", "HOR-010", "HOR-011",
    "MOR-003",
)
CASOS_CONTROL = ("ALQ-001", "COM-001", "GEN-002", "GEN-004", "GEN-010", "HOR-012", "RES-001", "RES-010")
CASOS_POR_DEFECTO = CASOS_CON_CLIENTE + CASOS_CONTROL

VARIANTES = sv2_proveedor.VARIANTES
FASES = ("ia1", "ia2")

#: Categorías de una ejecución y de la mayoría de un caso, en el orden del informe.
CATEGORIAS = {
    "emisor": "el CIF esperado del emisor (normalizado)",
    "cliente": "el CIF de una empresa del cliente: el fallo que corrige F-064",
    "nulo": "sin CIF",
    "otro": "un CIF que no es ni el del emisor ni el del cliente",
    "error": "la ejecución falló o no hay albarán",
    "inestable": "(solo mayoría) empate entre categorías en las repeticiones",
}

#: Valor del banco que significa «no comparar».
_NO_COMPARAR = "@@NO_COMPARAR@@"


class Parada(RuntimeError):
    """La corrida no puede empezar. Se lanza siempre ANTES de llamar al LLM."""


@dataclass
class Dependencias:
    """Lo que toca el mundo exterior; los tests pasan dobles."""

    ficheros_de_base: Callable[..., dict] = sv2_proveedor.ficheros_de_base
    ficheros_de_rama: Callable[[], dict] = sv2_proveedor.ficheros_de_rama
    montar_extractor: Callable[..., Callable[[str, str, Path, str], dict]] = sv2_proveedor.montar_extractor
    fixtures: Path = RUTA_FIXTURES


@dataclass
class Corrida:
    """Lo que devolvieron IA1 e IA2: `resultados[variante][repeticion - 1][caso_id]`."""

    casos: list[str]
    variantes: list[str]
    repeticiones: int
    proveedores: dict[str, str]
    modelos: dict[str, str]
    resultados: dict[str, list[dict[str, dict]]] = field(default_factory=dict)


# --- Fixtures -------------------------------------------------------------------


def _fixture(caso_id: str, fase: str, fixtures: Path) -> dict | None:
    ruta = Path(fixtures) / fase / f"{caso_id}.json"
    if not ruta.is_file():
        return None
    return json.loads(ruta.read_text(encoding="utf-8"))


def esperado_de(caso_id: str, fixtures: Path) -> str | None:
    """El CIF del emisor según `fixtures/final/<caso>.json` (`datos_generales[0].cif`)."""
    datos = _fixture(caso_id, "final", fixtures) or {}
    filas = (datos.get("tablas") or {}).get("datos_generales") or [{}]
    cif = filas[0].get("cif")
    if cif is None or cif == _NO_COMPARAR:
        return None
    return normalizar_cif(str(cif))


def tipologia_de(caso_id: str, fixtures: Path) -> str:
    """La tipología del caso según `fixtures/IA1/<caso>.json` (vacía si no la hay)."""
    datos = _fixture(caso_id, "IA1", fixtures) or {}
    return str(datos.get("tipologia") or "")


# --- Clasificación ---------------------------------------------------------------


def clasificar_cif(cif: str | None, esperado: str | None, propios: frozenset[str]) -> str:
    """`cliente`, `emisor`, `nulo` u `otro`, comparando normalizado."""
    normalizado = normalizar_cif(cif)
    if normalizado is None:
        return "nulo"
    if es_cif_propio(normalizado, propios):
        return "cliente"
    if esperado is not None and normalizado == normalizar_cif(esperado):
        return "emisor"
    return "otro"


def _categoria(resultado: dict | None, esperado: str | None, propios: frozenset[str]) -> str:
    if not resultado or "error" in resultado:
        return "error"
    return clasificar_cif(resultado.get("cif"), esperado, propios)


def mayoritaria(categorias: list[str]) -> str:
    """La categoría que más se repite; empate ⇒ `inestable`; sin ejecuciones ⇒ `error`."""
    if not categorias:
        return "error"
    cuenta = Counter(categorias).most_common()
    if len(cuenta) > 1 and cuenta[0][1] == cuenta[1][1]:
        return "inestable"
    return cuenta[0][0]


def clasificar(corrida: Corrida, esperados: dict[str, str | None], propios: frozenset[str]) -> dict:
    """`[caso][variante] = {ia1: [cats], ia2: [cats], mayoria: {ia1, ia2}}`."""
    clasificacion: dict[str, dict] = {}
    for caso in corrida.casos:
        clasificacion[caso] = {}
        for variante in corrida.variantes:
            por_fase = {
                fase: [
                    _categoria(vuelta[caso].get(fase), esperados.get(caso), propios)
                    for vuelta in corrida.resultados[variante]
                ]
                for fase in FASES
            }
            clasificacion[caso][variante] = {
                **por_fase,
                "mayoria": {fase: mayoritaria(por_fase[fase]) for fase in FASES},
            }
    return clasificacion


def _ejecuciones(clasificacion: dict, variante: str, fase: str, categoria: str) -> int:
    return sum(c[variante][fase].count(categoria) for c in clasificacion.values())


def _con_mayoria(clasificacion: dict, variante: str, fase: str, categoria: str) -> list[str]:
    return [caso for caso, c in clasificacion.items() if c[variante]["mayoria"][fase] == categoria]


def veredicto(clasificacion: dict, variantes: list[str]) -> dict:
    """C1, C2 y C3 de design.md §7 y el veredicto global. Sin las dos variantes, NO APLICA."""
    if set(variantes) != set(VARIANTES):
        return {"global": "NO APLICA", "reproduce_incidente": None}

    cliente = {
        (v, f): _ejecuciones(clasificacion, v, f, "cliente") for v in VARIANTES for f in FASES
    }
    c1 = cliente[("rama", "ia2")] == 0 and cliente[("rama", "ia1")] <= cliente[("base", "ia1")]
    emisor = {(v, f): _con_mayoria(clasificacion, v, f, "emisor") for v in VARIANTES for f in FASES}
    c2 = all(len(emisor[("rama", f)]) >= len(emisor[("base", f)]) for f in FASES)
    perdidos = sorted(
        {caso for f in FASES for caso in emisor[("base", f)] if caso not in emisor[("rama", f)]}
    )
    resultado = {
        "C1": {
            "ok": c1,
            "detalle": (
                f"ejecuciones con CIF cliente: rama tras IA2 = {cliente[('rama', 'ia2')]} (debe ser 0); "
                f"tras IA1 rama = {cliente[('rama', 'ia1')]}, base = {cliente[('base', 'ia1')]} (rama ≤ base)"
            ),
        },
        "C2": {
            "ok": c2,
            "detalle": "; ".join(
                f"tras {f.upper()} rama = {len(emisor[('rama', f)])}, base = {len(emisor[('base', f)])}"
                for f in FASES
            ) + " (casos con mayoría emisor, rama ≥ base)",
        },
        "C3": {
            "ok": not perdidos,
            "detalle": "casos que pierden la mayoría emisor en la rama: "
            + (", ".join(perdidos) if perdidos else "(ninguno)"),
        },
        "reproduce_incidente": cliente[("base", "ia1")] + cliente[("base", "ia2")] > 0,
    }
    resultado["global"] = "VERDE" if c1 and c2 and not perdidos else "ROJO"
    return resultado


# --- Corrida ---------------------------------------------------------------------


def correr(
    casos: dict[str, Path | None],
    tipologias: dict[str, str],
    variantes: list[str],
    repeticiones: int,
    extraer: Callable[[str, str, Path, str], dict],
) -> dict[str, list[dict[str, dict]]]:
    """Repetición a repetición, variante a variante y caso a caso, cada uno AISLADO.

    Las variantes se intercalan dentro de cada repetición para que un cambio
    del proveedor a mitad de corrida afecte a las dos por igual.
    """
    resultados: dict[str, list[dict[str, dict]]] = {v: [] for v in variantes}
    for repeticion in range(1, repeticiones + 1):
        for variante in variantes:
            resultados[variante].append(
                {
                    caso: _un_caso(variante, repeticion, caso, ruta, tipologias.get(caso, ""), extraer)
                    for caso, ruta in casos.items()
                }
            )
    return resultados


def _un_caso(variante, repeticion, caso_id, ruta, tipologia, extraer) -> dict:
    etiqueta = f"r{repeticion} · {variante} · caso {caso_id}"
    if ruta is None:
        fallo = {"fase": "preproceso", "tipo": "SinAlbaran", "motivo": f"no existe el albarán de {caso_id}"}
        return {"ia1": {"error": fallo}, "ia2": {"error": fallo}}
    try:
        salida = extraer(variante, caso_id, ruta, tipologia)
    except Exception as error:  # noqa: BLE001 - se aísla el caso, no se oculta
        fallo = describir_error(error, "IA1")
        avisar("comparar_proveedor", f"{etiqueta}: error · {fallo['motivo']}")
        return {"ia1": {"error": fallo}, "ia2": {"error": {**fallo, "fase": "IA2"}}}
    avisar("comparar_proveedor", f"{etiqueta}: ok")
    return {fase: salida.get(fase) for fase in FASES}


# --- Informes --------------------------------------------------------------------


def _cabecera(corrida: Corrida, commits: dict[str, str], base: str, fecha: str) -> list[str]:
    return [
        f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · base `{base}` "
        f"(`{commits.get('base') or '?'}`)",
        f"- IA1: proveedor `{corrida.proveedores['IA1']}`, modelo `{corrida.modelos['IA1']}` · "
        f"IA2: proveedor `{corrida.proveedores['IA2']}`, modelo `{corrida.modelos['IA2']}`",
        f"- Variantes: {', '.join(corrida.variantes)} · repeticiones: {corrida.repeticiones} · "
        f"casos: {len(corrida.casos)} (sin correo, sin lista de obras, sin contexto de Sigrid)",
    ]


def _tabla_recuentos(corrida: Corrida, clasificacion: dict) -> list[str]:
    columnas = [f"{v} {f.upper()}" for v in corrida.variantes for f in FASES]
    lineas = [
        "| Mayoría del caso | " + " | ".join(columnas) + " | Qué significa |",
        "|---|" + "---|" * len(columnas) + "---|",
    ]
    for categoria, texto in CATEGORIAS.items():
        celdas = [
            str(len(_con_mayoria(clasificacion, v, f, categoria)))
            for v in corrida.variantes
            for f in FASES
        ]
        lineas.append(f"| {categoria} | " + " | ".join(celdas) + f" | {texto} |")
    ejecuciones = [
        str(_ejecuciones(clasificacion, v, f, "cliente")) for v in corrida.variantes for f in FASES
    ]
    lineas.append("| *ejecuciones con CIF cliente* | " + " | ".join(ejecuciones) + " | para C1 |")
    return lineas


def _errores_sin_valores(corrida: Corrida) -> list[str]:
    lineas = []
    for caso in corrida.casos:
        fallos = []
        for variante in corrida.variantes:
            for indice, vuelta in enumerate(corrida.resultados[variante], start=1):
                for fase in FASES:
                    error = (vuelta[caso].get(fase) or {}).get("error")
                    if error:
                        fallos.append(f"{variante} r{indice}: {error['fase']} · {error['tipo']}")
                        break
        if fallos:
            lineas.append(f"- {caso} ({'; '.join(fallos)})")
    return lineas or ["(ninguno)"]


def render_versionable(
    corrida: Corrida, clasificacion: dict, juicio: dict, commits: dict[str, str], base: str,
    fecha: str, salida: str,
) -> str:
    """Recuentos, caso_id por categoría y veredicto. NINGÚN CIF ni nombre."""
    lineas = [
        "<!-- progress/comparar_proveedor_F-064.md -->",
        "# F-064 · Comparador del proveedor base/rama",
        "",
        "Generado por `python -m evals.comparar_proveedor`. **Sin valores**: solo recuentos, "
        "caso_id y veredicto.",
        f"Los CIF y los nombres están en `{salida}`, que git ignora.",
        "",
        *_cabecera(corrida, commits, base, fecha),
        "",
        "## Recuentos (casos por categoría mayoritaria)",
        "",
        *_tabla_recuentos(corrida, clasificacion),
        "",
        "## Casos por categoría mayoritaria",
        "",
    ]
    for variante in corrida.variantes:
        for fase in FASES:
            partes = [
                f"{categoria}: {', '.join(casos)}"
                for categoria in CATEGORIAS
                if (casos := _con_mayoria(clasificacion, variante, fase, categoria))
            ]
            lineas.append(f"- **{variante} tras {fase.upper()}** · " + " · ".join(partes))
    lineas += ["", "## Ejecuciones con error", "", *_errores_sin_valores(corrida), "", "## Veredicto", ""]
    if juicio["global"] == "NO APLICA":
        lineas.append("- Con una sola variante no hay comparación: C1–C3 no se juzgan.")
    else:
        for criterio in ("C1", "C2", "C3"):
            estado = "OK" if juicio[criterio]["ok"] else "KO"
            lineas.append(f"- {criterio} · {estado} · {juicio[criterio]['detalle']}")
        if not juicio["reproduce_incidente"]:
            lineas.append(
                "- AVISO: la base no dio ningún CIF cliente: el banco no reproduce el incidente "
                "y C1 no prueba nada (design.md §7: añadir el albarán real)."
            )
    lineas += ["", f"VEREDICTO: {juicio['global']}"]
    return "\n".join(lineas) + "\n"


def _valor(resultado: dict | None) -> str:
    if not resultado:
        return "—"
    if "error" in resultado:
        return f"ERROR ({resultado['error']['tipo']})"
    return "null" if resultado.get("cif") is None else f"`{resultado['cif']}`"


def render_detalle(
    corrida: Corrida, clasificacion: dict, juicio: dict, esperados: dict, commits: dict[str, str],
    base: str, fecha: str,
) -> str:
    """El resumen CON valores, para el directorio ignorado."""
    columnas = [
        f"{v} r{i} {f.upper()}"
        for v in corrida.variantes
        for i in range(1, corrida.repeticiones + 1)
        for f in FASES
    ]
    mayorias = [f"{v} {f.upper()}" for v in corrida.variantes for f in FASES]
    encabezado = ["caso", "esperado", *columnas, *mayorias]
    lineas = [
        "# Comparador del proveedor base/rama · detalle CON valores (no versionar)",
        "",
        *_cabecera(corrida, commits, base, fecha),
        "",
        *_tabla_recuentos(corrida, clasificacion),
        "",
        f"VEREDICTO: {juicio['global']}",
        "",
        "## Por caso (CIF; la última columna, la categoría mayoritaria)",
        "",
        "| " + " | ".join(encabezado) + " |",
        "|" + "---|" * len(encabezado),
    ]
    for caso in corrida.casos:
        celdas = [caso, f"`{esperados.get(caso)}`"]
        celdas += [
            _valor(vuelta[caso].get(f))
            for v in corrida.variantes
            for vuelta in corrida.resultados[v]
            for f in FASES
        ]
        celdas += [clasificacion[caso][v]["mayoria"][f] for v in corrida.variantes for f in FASES]
        lineas.append("| " + " | ".join(celdas) + " |")
    nombres = [
        f"- {caso} · {v} r{i} {f.upper()}: {vuelta[caso][f].get('nombre')!r}"
        for caso in corrida.casos
        for v in corrida.variantes
        for i, vuelta in enumerate(corrida.resultados[v], start=1)
        for f in FASES
        if vuelta[caso].get(f) and "error" not in vuelta[caso][f]
    ]
    errores = [
        f"- {caso} · {v} r{i} {f.upper()}: {vuelta[caso][f]['error']['motivo']}"
        for caso in corrida.casos
        for v in corrida.variantes
        for i, vuelta in enumerate(corrida.resultados[v], start=1)
        for f in FASES
        if vuelta[caso].get(f) and "error" in vuelta[caso][f]
    ]
    lineas += ["", "## proveedor_nombre leído", "", *(nombres or ["(ninguno)"])]
    lineas += ["", "## Errores", "", *(errores or ["(ninguno)"])]
    return "\n".join(lineas) + "\n"


def escribir(
    corrida: Corrida, esperados: dict, salida: Path, resumen: Path, commits: dict[str, str],
    base: str, fecha: str,
) -> dict:
    """Los JSON y el detalle en `salida`; el resumen sin valores en `resumen`."""
    clasificacion = clasificar(corrida, esperados, cifs_propios(None))
    juicio = veredicto(clasificacion, corrida.variantes)
    salida.mkdir(parents=True, exist_ok=True)
    for variante in corrida.variantes:
        for indice, vuelta in enumerate(corrida.resultados[variante], start=1):
            carga = {
                "variante": variante,
                "repeticion": indice,
                "proveedores": corrida.proveedores,
                "modelos": corrida.modelos,
                "casos": vuelta,
            }
            (salida / f"{variante}_r{indice}.json").write_text(
                json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    (salida / "resumen.md").write_text(
        render_detalle(corrida, clasificacion, juicio, esperados, commits, base, fecha), encoding="utf-8"
    )
    resumen.parent.mkdir(parents=True, exist_ok=True)
    resumen.write_text(
        render_versionable(corrida, clasificacion, juicio, commits, base, fecha, _relativa(salida)),
        encoding="utf-8",
    )
    return juicio


def _relativa(ruta: Path) -> str:
    try:
        return Path(ruta).resolve().relative_to(RAIZ_REPO).as_posix()
    except ValueError:
        return Path(ruta).as_posix()


# --- Preparación: todo lo que puede parar la corrida, antes de gastar -------------


def localizar_albaranes(casos: list[str], directorio: Path) -> dict[str, Path | None]:
    rutas = {caso: sv2_extraccion.ruta_de_albaran(caso, directorio) for caso in casos}
    if not any(rutas.values()):
        raise Parada(f"ningún caso tiene albarán en {directorio}. No se ha llamado a ningún LLM.")
    return rutas


def esperados_de(casos: list[str], fixtures: Path) -> dict[str, str]:
    esperados = {caso: esperado_de(caso, fixtures) for caso in casos}
    sin_cif = [caso for caso, cif in esperados.items() if cif is None]
    if sin_cif:
        raise Parada(
            "estos casos no tienen CIF esperado en evals/fixtures/final: "
            + ", ".join(sin_cif)
            + ". Sin él no se puede decir si el CIF es el del emisor. No se ha llamado a ningún LLM."
        )
    return esperados


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
    variantes = list(VARIANTES) if opciones.variante == "ambas" else [opciones.variante]
    proveedores = {
        fase: sv2_extraccion.proveedores_a_invocar(fase, None, entorno)[0] for fase in ("IA1", "IA2")
    }
    comprobar_claves(list(dict.fromkeys(proveedores.values())), entorno)
    rutas = localizar_albaranes(casos, Path(opciones.albaranes))
    esperados = esperados_de(casos, dependencias.fixtures)
    tipologias = {caso: tipologia_de(caso, dependencias.fixtures) for caso in casos}

    with tempfile.TemporaryDirectory(prefix="comparar_proveedor_") as temporal:
        ficheros: dict[str, dict] = {}
        if "base" in variantes:
            ficheros["base"] = dependencias.ficheros_de_base(Path(temporal), base=opciones.base)
        if "rama" in variantes:
            ficheros["rama"] = dependencias.ficheros_de_rama()

        modelos = {}
        for fase, proveedor in proveedores.items():
            variable, por_defecto = MODELOS_POR_PROVEEDOR.get(proveedor, ("", ""))
            modelos[fase] = entorno.get(variable) or por_defecto
        llamadas = 2 * sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones
        avisar(
            "comparar_proveedor",
            f"{llamadas} llamadas (IA1 {proveedores['IA1']} · IA2 {proveedores['IA2']}) · "
            f"variantes {', '.join(variantes)}",
        )
        extraer = dependencias.montar_extractor(ficheros, proveedores, entorno)
        corrida = Corrida(
            casos=casos,
            variantes=variantes,
            repeticiones=opciones.repeticiones,
            proveedores=proveedores,
            modelos=modelos,
            resultados=correr(rutas, tipologias, variantes, opciones.repeticiones, extraer),
        )

    salida = Path(opciones.salida) if opciones.salida else directorio_por_defecto()
    resumen = Path(opciones.resumen)
    fecha = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    commits = {"rama": _commit("HEAD"), "base": _commit(opciones.base)}
    juicio = escribir(corrida, esperados, salida, resumen, commits, opciones.base, fecha)

    print(f"comparar_proveedor: detalle con valores en {salida}")
    print(f"comparar_proveedor: resumen sin valores en {resumen} · VEREDICTO: {juicio['global']}")
    alguna = any(
        "error" not in (resultado.get("ia1") or {"error": True})
        for vueltas in corrida.resultados.values()
        for vuelta in vueltas
        for resultado in vuelta.values()
    )
    return 0 if alguna else 1


def _analizador() -> argparse.ArgumentParser:
    analizador = argparse.ArgumentParser(
        prog="python -m evals.comparar_proveedor",
        description=(
            "Compara el proveedor (CIF) que leen IA1 e IA2 con los YAML de la base y con los de "
            "esta rama. Llama a un LLM real: cuesta dinero."
        ),
    )
    analizador.add_argument(
        "--casos", default=",".join(CASOS_POR_DEFECTO),
        help="caso_id separados por coma (por defecto los 19 de design.md §7)",
    )
    analizador.add_argument("--repeticiones", type=int, default=3, help="por defecto 3")
    analizador.add_argument(
        "--variante", choices=("base", "rama", "ambas"), default="ambas", help="por defecto ambas"
    )
    analizador.add_argument(
        "--base", default=sv2_proveedor.BASE_POR_DEFECTO,
        help="referencia de git de la que salen los YAML de la variante base (por defecto dev)",
    )
    analizador.add_argument(
        "--salida", default="",
        help="directorio de la corrida, CON valores (por defecto "
        "evals/salidas/comparar_proveedor/<fecha-hora>/, ignorado por git)",
    )
    analizador.add_argument(
        "--resumen", default=str(RUTA_RESUMEN_VERSIONABLE),
        help="resumen SIN valores para versionar (por defecto progress/comparar_proveedor_F-064.md)",
    )
    analizador.add_argument(
        "--albaranes", default=str(sv2_extraccion.RUTA_ALBARANES),
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
    except (Parada, ClavesAusentes, sv2_proveedor.BaseNoDisponible) as error:
        print(f"comparar_proveedor: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
