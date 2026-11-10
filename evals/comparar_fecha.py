# evals/comparar_fecha.py
"""Compara la FECHA que leen IA1 e IA2 con la referencia de recepción, base frente a rama (F-112).

    python -m evals.comparar_fecha [--juegos A,B,C,D] [--repeticiones 2]
        [--variante base|rama|ambas] [--base <ref>] [--albaranes <dir>]
        [--casos-fecha <json>] [--sinteticos <json>] [--salida <dir>]
        [--resumen <fichero>] [--solo-validar]

Por qué existe: en producción el 12 % de los albaranes tenía la fecha a más de
un año de su correo (el año mal leído). F-112 le da a IA1 e IA2 el día de
recepción como referencia del AÑO; aquí se mide si arregla el fallo sin
romper lo que funciona ni pisar un año antiguo impreso de verdad.

Juegos (specs/F-112-anio-fecha-albaran/design.md §7, R19):
- **A**: los documentos de producción de `evals/casos_fecha.json`, con su
  recepción real (clases `anio`, `dudoso` y `antigua`).
- **B**: 20 casos del banco (`evals/fixtures/IA1/`) con fecha esperada,
  muestreados con semilla fija; referencia = esperada + 7 días.
- **C**: los del banco con fecha esperada anterior a 2025-01-01; referencia =
  esperada + 730 días.
- **D**: los sintéticos de cambio de año (`evals/casos_fecha_sinteticos.json`,
  R27); referencia con `fecha_recepcion_de` sobre su `recibido_utc`.

Por caso, variante y repetición: IA1 y luego IA2 con la referencia del juego,
sin correo, sin lista de obras y sin Sigrid. Cada fecha se clasifica en
`exacta`, `referencia`, `solo_anio`, `otra`, `nula` o `error`; la mayoría de
las repeticiones da la del caso (empate ⇒ `inestable`). Aparte, por
ejecución, el efecto de IA2: `corrige`, `estropea`, `cambia` o `igual`.

Veredicto VERDE solo con C1–C7 (R22) y con las dos variantes y los cuatro
juegos; si no, NO APLICA.

Cuesta dinero: 2 llamadas por caso, variante y repetición. Antes de gastar
nada se para (código 2) si falta la clave de un proveedor, si ningún caso
tiene albarán, si un JSON de casos no valida o si falla el `git show` de la
base. `--solo-validar` hace solo esas comprobaciones (código 0 si todo valida).

Salidas:
- en `--salida` (por defecto `evals/salidas/comparar_fecha/<fecha-hora>/`,
  ignorado por git): un JSON por variante y repetición y `resumen.md`, CON
  las fechas leídas;
- en `--resumen` (por defecto `progress/comparar_fecha_F-112.md`): recuentos,
  caso_id por categoría, efecto de IA2 y veredicto, SIN proveedor del
  albarán, CIF, número ni fechas.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import math
import os
import random
import re
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from evals.procesos import sv2_extraccion, sv2_fecha
from evals.procesos.errores import avisar, describir_error
from evals.procesos.sv5_valoracion import (
    MODELOS_POR_PROVEEDOR,
    ClavesAusentes,
    comprobar_claves,
)

RAIZ_REPO = sv2_extraccion.RAIZ_REPO

#: Dónde van las corridas (con valores). `evals/salidas/` lo ignora git.
RUTA_SALIDAS = RAIZ_REPO / "evals" / "salidas" / "comparar_fecha"

#: El resumen SIN valores que se versiona.
RUTA_RESUMEN_VERSIONABLE = RAIZ_REPO / "progress" / "comparar_fecha_F-112.md"

#: Fixtures del banco (fecha esperada y tipología en `IA1/`).
RUTA_FIXTURES = RAIZ_REPO / "evals" / "fixtures"

#: Juego A (versionado; lo rellena M1) y juego D (lo genera `evals.sinteticos_fecha`).
RUTA_CASOS_FECHA = RAIZ_REPO / "evals" / "casos_fecha.json"
RUTA_SINTETICOS = RAIZ_REPO / "evals" / "casos_fecha_sinteticos.json"

#: El bloque de sv2 que da la referencia de los juegos A y D (R1, R27).
RUTA_FECHA_RECEPCION = sv2_extraccion.RAIZ_SV2 / "application" / "services" / "fecha_recepcion.py"

JUEGOS = ("A", "B", "C", "D")
VARIANTES = sv2_fecha.VARIANTES
FASES = ("ia1", "ia2")

#: Juego B: tamaño de la muestra y semilla fija (D7: 416 llamadas con A, B y C).
MUESTRA_B = 20
SEMILLA_B = 20261030
#: Referencias de B y C respecto a la esperada.
DESFASE_B = timedelta(days=7)
DESFASE_C = timedelta(days=730)
#: Juego C: los del banco anteriores a esta fecha.
CORTE_C = date(2025, 1, 1)
#: C1 (D6): fracción de los `anio` del juego A con mayoría exacta tras IA2 en rama.
UMBRAL_C1 = 0.8

#: Clases del juego A (design §7.1).
CLASES_A = ("anio", "dudoso", "antigua")

#: Categorías de una fecha y de la mayoría de un caso, en el orden del informe.
CATEGORIAS = {
    "exacta": "la fecha esperada (día, mes y año)",
    "referencia": "la referencia de recepción copiada como fecha (y no es la esperada)",
    "solo_anio": "día y mes de la esperada con otro año: el fallo que corrige F-112",
    "otra": "otra fecha (o un texto que no es fecha)",
    "nula": "sin fecha",
    "error": "la ejecución falló o no hay albarán",
    "inestable": "(solo mayoría) empate entre categorías en las repeticiones",
}

#: Efecto de IA2 por ejecución (fecha tras IA1 frente a la final).
EFECTOS = {
    "corrige": "IA1 no exacta, final exacta",
    "estropea": "IA1 exacta, final no",
    "cambia": "las dos no exactas y distintas",
    "igual": "el resto (misma fecha, o las dos exactas)",
}

_FORMATO_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class Parada(RuntimeError):
    """La corrida no puede empezar. Se lanza siempre ANTES de llamar al LLM."""


@dataclass(frozen=True)
class Caso:
    """Un caso de un juego: lo que se espera y la referencia que recibe la IA."""

    juego: str
    caso_id: str
    tipologia: str
    esperada: date
    referencia: date
    clase: str = ""

    @property
    def clave(self) -> str:
        return f"{self.juego}/{self.caso_id}"


@dataclass
class Dependencias:
    """Lo que toca el mundo exterior; los tests pasan dobles."""

    ficheros_de_base: Callable[..., dict] = sv2_fecha.ficheros_de_base
    ficheros_de_rama: Callable[[], dict] = sv2_fecha.ficheros_de_rama
    montar_extractor: Callable[..., Callable[[str, str, Path, str, date], dict]] = sv2_fecha.montar_extractor
    fixtures: Path = RUTA_FIXTURES


@dataclass
class Corrida:
    """Lo que devolvieron IA1 e IA2: `resultados[variante][repeticion - 1][clave]`."""

    casos: list[Caso]
    juegos: list[str]
    variantes: list[str]
    repeticiones: int
    proveedores: dict[str, str]
    modelos: dict[str, str]
    resultados: dict[str, list[dict[str, dict]]] = field(default_factory=dict)


# --- La referencia de sv2 (R1) -----------------------------------------------------

_MODULO_FECHA = None


def fecha_recepcion_de(recibido: str | None) -> date | None:
    """`fecha_recepcion_de` de sv2 sobre un `recibido_utc` (día en Europe/Madrid).

    Se carga el fichero de sv2 por su ruta (es puro): meter sv2 en `sys.path`
    chocaría con los paquetes `application` de otros servicios.
    """
    global _MODULO_FECHA
    if _MODULO_FECHA is None:
        especificacion = importlib.util.spec_from_file_location("sv2_fecha_recepcion", RUTA_FECHA_RECEPCION)
        modulo = importlib.util.module_from_spec(especificacion)
        especificacion.loader.exec_module(modulo)
        _MODULO_FECHA = modulo
    from ruesma_comun.correo import construir_contexto_correo

    return _MODULO_FECHA.fecha_recepcion_de(construir_contexto_correo("", "", recibido_utc=recibido))


# --- Juegos (R19) ------------------------------------------------------------------


def _fecha_valida(valor) -> date | None:
    if not isinstance(valor, str) or not _FORMATO_FECHA.match(valor):
        return None
    try:
        return date.fromisoformat(valor)
    except ValueError:
        return None


def _leer_json(ruta: Path, nombre: str) -> dict:
    if not Path(ruta).is_file():
        raise Parada(f"{nombre}: no existe el fichero. No se ha llamado a ningún LLM.")
    try:
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise Parada(f"{nombre}: no es un JSON válido. No se ha llamado a ningún LLM.") from None
    if not isinstance(datos, dict) or not isinstance(datos.get("casos"), list):
        raise Parada(f"{nombre}: falta la lista `casos`. No se ha llamado a ningún LLM.")
    return datos


def _validar(datos: dict, nombre: str, campo_recibido: str, juego: str) -> list[Caso]:
    """Comprueba cada caso; los mensajes citan posición y campo, nunca valores (R23)."""
    casos: list[Caso] = []
    vistos: dict[str, int] = {}
    for posicion, fila in enumerate(datos["casos"], start=1):
        def parar(motivo: str, posicion=posicion) -> None:
            raise Parada(f"{nombre}: el caso nº {posicion} {motivo}. No se ha llamado a ningún LLM.")

        if not isinstance(fila, dict):
            parar("no es un objeto")
        caso_id = fila.get("caso_id")
        if not isinstance(caso_id, str) or not caso_id.strip():
            parar("no tiene `caso_id`")
        if caso_id in vistos:
            parar(f"repite el `caso_id` del caso nº {vistos[caso_id]}")
        vistos[caso_id] = posicion
        tipologia = fila.get("tipologia")
        if not isinstance(tipologia, str):
            parar("no tiene `tipologia`")
        esperada = _fecha_valida(fila.get("fecha_esperada"))
        if esperada is None:
            parar("no tiene `fecha_esperada` con formato AAAA-MM-DD")
        referencia = fecha_recepcion_de(fila.get(campo_recibido)) if isinstance(
            fila.get(campo_recibido), str
        ) else None
        if referencia is None:
            parar(f"no tiene `{campo_recibido}` con una fecha o fecha-hora ISO válida")
        clase = ""
        if juego == "A":
            clase = fila.get("clase")
            if clase not in CLASES_A:
                parar("no tiene `clase` `anio`, `dudoso` o `antigua`")
        casos.append(Caso(juego, caso_id, tipologia, esperada, referencia, clase))
    return casos


def juego_a(ruta: Path) -> list[Caso]:
    """Los documentos de producción, con su recepción real (`recibido`)."""
    return _validar(_leer_json(ruta, "casos_fecha.json"), "casos_fecha.json", "recibido", "A")


def juego_d(ruta: Path) -> list[Caso]:
    """Los sintéticos de cambio de año, con su `recibido_utc` (R27)."""
    return _validar(
        _leer_json(ruta, "casos_fecha_sinteticos.json"), "casos_fecha_sinteticos.json", "recibido_utc", "D"
    )


def banco(fixtures: Path) -> dict[str, tuple[date, str]]:
    """`caso_id → (fecha esperada, tipología)` de los casos de IA1 con fecha esperada."""
    casos: dict[str, tuple[date, str]] = {}
    for ruta in sorted((Path(fixtures) / "IA1").glob("*.json")):
        if ruta.name.startswith("_"):
            continue
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        cabeceras = (datos.get("tablas") or {}).get("cabeceras") or [{}]
        esperada = _fecha_valida((cabeceras[0] or {}).get("fecha"))
        if esperada is None:
            continue
        casos[str(datos.get("caso_id") or ruta.stem)] = (esperada, str(datos.get("tipologia") or ""))
    return casos


def juego_b(fixtures: Path, muestra: int = MUESTRA_B, semilla: int = SEMILLA_B) -> list[Caso]:
    """`muestra` casos del banco, elegidos con semilla fija; referencia = esperada + 7 días."""
    todos = banco(fixtures)
    elegidos = sorted(random.Random(semilla).sample(sorted(todos), min(muestra, len(todos))))
    return [Caso("B", c, todos[c][1], todos[c][0], todos[c][0] + DESFASE_B) for c in elegidos]


def juego_c(fixtures: Path) -> list[Caso]:
    """Los del banco anteriores a 2025-01-01; referencia = esperada + 730 días."""
    todos = banco(fixtures)
    return [
        Caso("C", c, tipologia, esperada, esperada + DESFASE_C)
        for c, (esperada, tipologia) in sorted(todos.items())
        if esperada < CORTE_C
    ]


def construir_juegos(
    juegos: list[str], fixtures: Path, ruta_a: Path, ruta_d: Path
) -> list[Caso]:
    """Los casos de los juegos pedidos, en el orden A, B, C, D."""
    casos: list[Caso] = []
    for juego in JUEGOS:
        if juego not in juegos:
            continue
        if juego == "A":
            casos += juego_a(ruta_a)
        elif juego == "B":
            casos += juego_b(fixtures)
        elif juego == "C":
            casos += juego_c(fixtures)
        else:
            casos += juego_d(ruta_d)
    return casos


# --- Clasificación (R21) -----------------------------------------------------------


def clasificar_fecha(valor, esperada: date, referencia: date) -> str:
    """`exacta`, `referencia`, `solo_anio`, `otra` o `nula`."""
    if valor is None or not str(valor).strip():
        return "nula"
    try:
        leida = date.fromisoformat(str(valor).strip()[:10])
    except ValueError:
        return "otra"
    if leida == esperada:
        return "exacta"
    if leida == referencia:
        return "referencia"
    if (leida.month, leida.day) == (esperada.month, esperada.day):
        return "solo_anio"
    return "otra"


def _categoria(resultado: dict | None, caso: Caso) -> str:
    if not resultado or "error" in resultado:
        return "error"
    return clasificar_fecha(resultado.get("fecha"), caso.esperada, caso.referencia)


def efecto_ia2(ejecucion: dict, caso: Caso) -> str | None:
    """`corrige`, `estropea`, `cambia` o `igual`; `None` si alguna fase falló."""
    ia1, ia2 = ejecucion.get("ia1"), ejecucion.get("ia2")
    if not ia1 or not ia2 or "error" in ia1 or "error" in ia2:
        return None
    exacta_1 = _categoria(ia1, caso) == "exacta"
    exacta_2 = _categoria(ia2, caso) == "exacta"
    if exacta_2 and not exacta_1:
        return "corrige"
    if exacta_1 and not exacta_2:
        return "estropea"
    if not exacta_1 and (ia1.get("fecha") or None) != (ia2.get("fecha") or None):
        return "cambia"
    return "igual"


def mayoritaria(categorias: list[str]) -> str:
    """La categoría que más se repite; empate ⇒ `inestable`; sin ejecuciones ⇒ `error`."""
    if not categorias:
        return "error"
    cuenta = Counter(categorias).most_common()
    if len(cuenta) > 1 and cuenta[0][1] == cuenta[1][1]:
        return "inestable"
    return cuenta[0][0]


def clasificar(corrida: Corrida) -> dict:
    """`[clave][variante] = {ia1: [cats], ia2: [cats], mayoria: {ia1, ia2}, efectos: [...]}`."""
    clasificacion: dict[str, dict] = {}
    for caso in corrida.casos:
        clasificacion[caso.clave] = {}
        for variante in corrida.variantes:
            vueltas = [vuelta[caso.clave] for vuelta in corrida.resultados[variante]]
            por_fase = {fase: [_categoria(v.get(fase), caso) for v in vueltas] for fase in FASES}
            clasificacion[caso.clave][variante] = {
                **por_fase,
                "mayoria": {fase: mayoritaria(por_fase[fase]) for fase in FASES},
                "efectos": [efecto_ia2(v, caso) for v in vueltas],
            }
    return clasificacion


def _del_juego(corrida: Corrida, juego: str, clase: str | None = None) -> list[Caso]:
    return [c for c in corrida.casos if c.juego == juego and (clase is None or c.clase == clase)]


def _con_mayoria(clasificacion: dict, casos: list[Caso], variante: str, fase: str, categoria: str) -> list[str]:
    return [c.caso_id for c in casos if clasificacion[c.clave][variante]["mayoria"][fase] == categoria]


def _ejecuciones(clasificacion: dict, casos: list[Caso], variante: str, fase: str, categoria: str) -> int:
    return sum(clasificacion[c.clave][variante][fase].count(categoria) for c in casos)


def _efectos(clasificacion: dict, casos: list[Caso], variante: str, efecto: str) -> list[str]:
    """`caso_id` (con repetición) de las ejecuciones con ese efecto."""
    return [
        c.caso_id
        for c in casos
        for e in clasificacion[c.clave][variante]["efectos"]
        if e == efecto
    ]


# --- Veredicto (R22) ---------------------------------------------------------------


def veredicto(corrida: Corrida, clasificacion: dict) -> dict:
    """C1–C7 de R22 y el global. Sin las dos variantes o sin los cuatro juegos, NO APLICA."""
    if set(corrida.variantes) != set(VARIANTES):
        return {"global": "NO APLICA", "motivo": "hace falta medir las dos variantes (base y rama)"}
    if set(corrida.juegos) != set(JUEGOS):
        return {"global": "NO APLICA", "motivo": "hace falta medir los cuatro juegos (A, B, C y D)"}

    anio = _del_juego(corrida, "A", "anio")
    rama_c1 = _con_mayoria(clasificacion, anio, "rama", "ia2", "exacta")
    base_c1 = _con_mayoria(clasificacion, anio, "base", "ia2", "exacta")
    umbral = math.ceil(UMBRAL_C1 * len(anio))
    c1 = bool(anio) and len(rama_c1) >= umbral and len(rama_c1) >= len(base_c1)

    b = _del_juego(corrida, "B")
    perdidos_b = sorted(
        set(_con_mayoria(clasificacion, b, "base", "ia2", "exacta"))
        - set(_con_mayoria(clasificacion, b, "rama", "ia2", "exacta"))
    )

    c = _del_juego(corrida, "C")
    exactos_base_c = set(_con_mayoria(clasificacion, c, "base", "ia2", "exacta"))
    pisados_c = sorted(
        caso.caso_id
        for caso in c
        if caso.caso_id in exactos_base_c
        and clasificacion[caso.clave]["rama"]["mayoria"]["ia2"] in ("solo_anio", "referencia")
    )

    referencias = sum(
        _ejecuciones(clasificacion, corrida.casos, "rama", fase, "referencia") for fase in FASES
    )
    estropea = sorted(set(_efectos(clasificacion, corrida.casos, "rama", "estropea")))

    d = _del_juego(corrida, "D")
    fallan_d = sorted({x.caso_id for x in d} - set(_con_mayoria(clasificacion, d, "rama", "ia2", "exacta")))

    antigua = _del_juego(corrida, "A", "antigua")
    fallan_c7 = sorted(
        {x.caso_id for x in antigua} - set(_con_mayoria(clasificacion, antigua, "rama", "ia2", "exacta"))
    )

    def lista(casos: list[str]) -> str:
        return ", ".join(casos) if casos else "(ninguno)"

    resultado = {
        "C1": {
            "ok": c1,
            "detalle": (
                f"juego A, casos `anio` con mayoría exacta tras IA2: rama = {len(rama_c1)} de {len(anio)} "
                f"(umbral {umbral}), base = {len(base_c1)} (rama ≥ umbral y ≥ base)"
                + ("" if anio else "; sin casos `anio` no se puede juzgar")
            ),
        },
        "C2": {"ok": not perdidos_b, "detalle": f"juego B, casos que pierden la exacta en rama: {lista(perdidos_b)}"},
        "C3": {
            "ok": not pisados_c,
            "detalle": f"juego C, exactos en base que pasan a solo_anio o referencia en rama: {lista(pisados_c)}",
        },
        "C4": {"ok": referencias == 0, "detalle": f"ejecuciones `referencia` en rama: {referencias} (debe ser 0)"},
        "C5": {"ok": not estropea, "detalle": f"casos con IA2 `estropea` en rama: {lista(estropea)}"},
        "C6": {"ok": bool(d) and not fallan_d, "detalle": f"juego D, sin mayoría exacta en rama: {lista(fallan_d)}"
               + ("" if d else "; sin casos D no se puede juzgar")},
        "C7": {"ok": not fallan_c7, "detalle": f"juego A, `antigua` sin mayoría exacta en rama: {lista(fallan_c7)}"},
    }
    resultado["global"] = "VERDE" if all(resultado[f"C{i}"]["ok"] for i in range(1, 8)) else "ROJO"
    return resultado


# --- Corrida -----------------------------------------------------------------------


def correr(
    casos: list[Caso],
    rutas: dict[str, Path | None],
    variantes: list[str],
    repeticiones: int,
    extraer: Callable[[str, str, Path, str, date], dict],
) -> dict[str, list[dict[str, dict]]]:
    """Repetición a repetición, variante a variante y caso a caso, cada uno AISLADO.

    Las variantes se intercalan dentro de cada repetición para que un cambio
    del proveedor a mitad de corrida afecte a las dos por igual.
    """
    resultados: dict[str, list[dict[str, dict]]] = {v: [] for v in variantes}
    for repeticion in range(1, repeticiones + 1):
        for variante in variantes:
            resultados[variante].append(
                {caso.clave: _un_caso(variante, repeticion, caso, rutas.get(caso.caso_id), extraer) for caso in casos}
            )
    return resultados


def _un_caso(variante: str, repeticion: int, caso: Caso, ruta: Path | None, extraer) -> dict:
    etiqueta = f"r{repeticion} · {variante} · {caso.clave}"
    if ruta is None:
        fallo = {"fase": "preproceso", "tipo": "SinAlbaran", "motivo": f"no existe el albarán de {caso.caso_id}"}
        return {"ia1": {"error": fallo}, "ia2": {"error": fallo}}
    try:
        salida = extraer(variante, caso.caso_id, ruta, caso.tipologia, caso.referencia)
    except Exception as error:  # noqa: BLE001 - se aísla el caso, no se oculta
        fallo = describir_error(error, "IA1")
        avisar("comparar_fecha", f"{etiqueta}: error · {fallo['motivo']}")
        return {"ia1": {"error": fallo}, "ia2": {"error": {**fallo, "fase": "IA2"}}}
    avisar("comparar_fecha", f"{etiqueta}: ok")
    return {fase: salida.get(fase) for fase in FASES}


# --- Informes (R24, R29) -----------------------------------------------------------


def _cabecera(corrida: Corrida, commits: dict[str, str], base: str, fecha: str) -> list[str]:
    return [
        (
            f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · base `{base}` "
            f"(`{commits.get('base') or '?'}`)"
        ),
        (
            f"- IA1: `{corrida.proveedores['IA1']}`, modelo `{corrida.modelos['IA1']}` · "
            f"IA2: `{corrida.proveedores['IA2']}`, modelo `{corrida.modelos['IA2']}`"
        ),
        (
            f"- Juegos: {', '.join(corrida.juegos)} · variantes: {', '.join(corrida.variantes)} · "
            f"repeticiones: {corrida.repeticiones} · casos: {len(corrida.casos)} "
            "(sin correo, sin lista de obras, sin Sigrid)"
        ),
    ]


def _tabla_juego(corrida: Corrida, clasificacion: dict, juego: str) -> list[str]:
    casos = _del_juego(corrida, juego)
    columnas = [f"{v} {f.upper()}" for v in corrida.variantes for f in FASES]
    lineas = [
        f"### Juego {juego} ({len(casos)} casos)",
        "",
        "| Mayoría del caso | " + " | ".join(columnas) + " | Qué significa |",
        "|---|" + "---|" * len(columnas) + "---|",
    ]
    for categoria, texto in CATEGORIAS.items():
        celdas = [
            str(len(_con_mayoria(clasificacion, casos, v, f, categoria))) for v in corrida.variantes for f in FASES
        ]
        lineas.append(f"| {categoria} | " + " | ".join(celdas) + f" | {texto} |")
    ejecuciones = [
        str(_ejecuciones(clasificacion, casos, v, f, "referencia")) for v in corrida.variantes for f in FASES
    ]
    lineas.append("| *ejecuciones `referencia`* | " + " | ".join(ejecuciones) + " | para C4 |")
    return lineas


def _tabla_efectos(corrida: Corrida, clasificacion: dict) -> list[str]:
    lineas = [
        "| Juego | Variante | " + " | ".join(EFECTOS) + " |",
        "|---|---|" + "---|" * len(EFECTOS),
    ]
    for juego in corrida.juegos:
        casos = _del_juego(corrida, juego)
        for variante in corrida.variantes:
            celdas = [str(len(_efectos(clasificacion, casos, variante, e))) for e in EFECTOS]
            lineas.append(f"| {juego} | {variante} | " + " | ".join(celdas) + " |")
    return lineas


def _errores_sin_valores(corrida: Corrida) -> list[str]:
    lineas = []
    for caso in corrida.casos:
        fallos = []
        for variante in corrida.variantes:
            for indice, vuelta in enumerate(corrida.resultados[variante], start=1):
                for fase in FASES:
                    error = (vuelta[caso.clave].get(fase) or {}).get("error")
                    if error:
                        fallos.append(f"{variante} r{indice}: {error['fase']} · {error['tipo']}")
                        break
        if fallos:
            lineas.append(f"- {caso.clave} ({'; '.join(fallos)})")
    return lineas or ["(ninguno)"]


def _juicio(juicio: dict) -> list[str]:
    if juicio["global"] == "NO APLICA":
        return [f"- C1–C7 no se juzgan: {juicio['motivo']}."]
    return [
        f"- C{i} · {'OK' if juicio[f'C{i}']['ok'] else 'KO'} · {juicio[f'C{i}']['detalle']}" for i in range(1, 8)
    ]


def render_versionable(
    corrida: Corrida, clasificacion: dict, juicio: dict, commits: dict[str, str], base: str,
    fecha: str, salida: str,
) -> str:
    """Recuentos, caso_id por categoría, efecto de IA2 y veredicto. NINGUNA fecha ni dato del albarán."""
    lineas = [
        "<!-- progress/comparar_fecha_F-112.md -->",
        "# F-112 · Comparador de la fecha base/rama",
        "",
        "Generado por `python -m evals.comparar_fecha`. **Sin valores**: solo recuentos, caso_id y veredicto.",
        f"Las fechas leídas están en `{salida}`, que git ignora.",
        "",
        *_cabecera(corrida, commits, base, fecha),
        "",
        "## Recuentos (casos por categoría mayoritaria)",
        "",
    ]
    for juego in corrida.juegos:
        lineas += [*_tabla_juego(corrida, clasificacion, juego), ""]
    lineas += ["## Casos por categoría mayoritaria", ""]
    for juego in corrida.juegos:
        casos = _del_juego(corrida, juego)
        for variante in corrida.variantes:
            for fase in FASES:
                partes = [
                    f"{categoria}: {', '.join(ids)}"
                    for categoria in CATEGORIAS
                    if (ids := _con_mayoria(clasificacion, casos, variante, fase, categoria))
                ]
                lineas.append(f"- **{juego} · {variante} tras {fase.upper()}** · " + (" · ".join(partes) or "(vacío)"))
    lineas += ["", "## Efecto de IA2 (ejecuciones, fecha de IA1 frente a la final)", "",
               *_tabla_efectos(corrida, clasificacion), ""]
    for variante in corrida.variantes:
        estropea = sorted(set(_efectos(clasificacion, corrida.casos, variante, "estropea")))
        lineas.append(f"- `estropea` en {variante}: {', '.join(estropea) if estropea else '(ninguno)'}")
    lineas += ["", "## Ejecuciones con error", "", *_errores_sin_valores(corrida), "", "## Veredicto", ""]
    lineas += [*_juicio(juicio), "", f"VEREDICTO: {juicio['global']}"]
    return "\n".join(lineas) + "\n"


def _valor(resultado: dict | None) -> str:
    if not resultado:
        return "—"
    if "error" in resultado:
        return f"ERROR ({resultado['error']['tipo']})"
    return "null" if resultado.get("fecha") is None else f"`{resultado['fecha']}`"


def render_detalle(
    corrida: Corrida, clasificacion: dict, juicio: dict, commits: dict[str, str], base: str, fecha: str,
) -> str:
    """El resumen CON fechas, para el directorio ignorado."""
    columnas = [
        f"{v} r{i} {f.upper()}" for v in corrida.variantes for i in range(1, corrida.repeticiones + 1) for f in FASES
    ]
    mayorias = [f"{v} {f.upper()}" for v in corrida.variantes for f in FASES]
    encabezado = ["caso", "clase", "esperada", "referencia", *columnas, *mayorias]
    lineas = [
        "# Comparador de la fecha base/rama · detalle CON valores (no versionar)",
        "",
        *_cabecera(corrida, commits, base, fecha),
        "",
        f"VEREDICTO: {juicio['global']}",
        "",
        "| " + " | ".join(encabezado) + " |",
        "|" + "---|" * len(encabezado),
    ]
    for caso in corrida.casos:
        celdas = [caso.clave, caso.clase or "—", caso.esperada.isoformat(), caso.referencia.isoformat()]
        celdas += [
            _valor(vuelta[caso.clave].get(f)) for v in corrida.variantes for vuelta in corrida.resultados[v] for f in FASES
        ]
        celdas += [clasificacion[caso.clave][v]["mayoria"][f] for v in corrida.variantes for f in FASES]
        lineas.append("| " + " | ".join(celdas) + " |")
    lineas += ["", "## Veredicto", "", *_juicio(juicio)]
    return "\n".join(lineas) + "\n"


def escribir(corrida: Corrida, salida: Path, resumen: Path, commits: dict[str, str], base: str, fecha: str) -> dict:
    """Los JSON y el detalle en `salida`; el resumen sin valores en `resumen`."""
    clasificacion = clasificar(corrida)
    juicio = veredicto(corrida, clasificacion)
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
        render_detalle(corrida, clasificacion, juicio, commits, base, fecha), encoding="utf-8"
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


# --- Preparación: todo lo que puede parar la corrida, antes de gastar (R23) ---------


def localizar_albaranes(casos: list[Caso], directorio: Path) -> dict[str, Path | None]:
    rutas = {caso.caso_id: sv2_extraccion.ruta_de_albaran(caso.caso_id, directorio) for caso in casos}
    if not any(rutas.values()):
        raise Parada(f"ningún caso tiene albarán en {directorio}. No se ha llamado a ningún LLM.")
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
    juegos = opciones.lista_juegos
    variantes = list(VARIANTES) if opciones.variante == "ambas" else [opciones.variante]
    proveedores = {
        fase: sv2_extraccion.proveedores_a_invocar(fase, None, entorno)[0] for fase in ("IA1", "IA2")
    }
    comprobar_claves(list(dict.fromkeys(proveedores.values())), entorno)
    casos = construir_juegos(juegos, dependencias.fixtures, Path(opciones.casos_fecha), Path(opciones.sinteticos))
    rutas = localizar_albaranes(casos, Path(opciones.albaranes))

    with tempfile.TemporaryDirectory(prefix="comparar_fecha_") as temporal:
        ficheros: dict[str, dict] = {}
        if "base" in variantes:
            ficheros["base"] = dependencias.ficheros_de_base(Path(temporal), base=opciones.base)
        if "rama" in variantes:
            ficheros["rama"] = dependencias.ficheros_de_rama()

        con_albaran = sum(1 for caso in casos if rutas.get(caso.caso_id))
        llamadas = 2 * con_albaran * len(variantes) * opciones.repeticiones
        if opciones.solo_validar:
            print(
                f"comparar_fecha: todo valida · {len(casos)} casos ({con_albaran} con albarán) · "
                f"juegos {', '.join(juegos)} · {llamadas} llamadas si se lanza. No se ha llamado a ningún LLM."
            )
            return 0

        modelos = {}
        for fase, proveedor in proveedores.items():
            variable, por_defecto = MODELOS_POR_PROVEEDOR.get(proveedor, ("", ""))
            modelos[fase] = entorno.get(variable) or por_defecto
        avisar(
            "comparar_fecha",
            f"{llamadas} llamadas (IA1 {proveedores['IA1']} · IA2 {proveedores['IA2']}) · "
            f"juegos {', '.join(juegos)} · variantes {', '.join(variantes)}",
        )
        extraer = dependencias.montar_extractor(ficheros, proveedores, entorno)
        corrida = Corrida(
            casos=casos,
            juegos=juegos,
            variantes=variantes,
            repeticiones=opciones.repeticiones,
            proveedores=proveedores,
            modelos=modelos,
            resultados=correr(casos, rutas, variantes, opciones.repeticiones, extraer),
        )

    salida = Path(opciones.salida) if opciones.salida else directorio_por_defecto()
    resumen = Path(opciones.resumen)
    fecha = dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    commits = {"rama": _commit("HEAD"), "base": _commit(opciones.base)}
    juicio = escribir(corrida, salida, resumen, commits, opciones.base, fecha)

    print(f"comparar_fecha: detalle con valores en {salida}")
    print(f"comparar_fecha: resumen sin valores en {resumen} · VEREDICTO: {juicio['global']}")
    alguna = any(
        "error" not in (resultado.get("ia1") or {"error": True})
        for vueltas in corrida.resultados.values()
        for vuelta in vueltas
        for resultado in vuelta.values()
    )
    return 0 if alguna else 1


def _analizador() -> argparse.ArgumentParser:
    analizador = argparse.ArgumentParser(
        prog="python -m evals.comparar_fecha",
        description=(
            "Compara la fecha que leen IA1 e IA2 con la referencia de recepción, con los YAML de la "
            "base y con los de esta rama. Llama a un LLM real: cuesta dinero."
        ),
    )
    analizador.add_argument("--juegos", default=",".join(JUEGOS), help="A, B, C y/o D separados por coma")
    analizador.add_argument("--repeticiones", type=int, default=2, help="por defecto 2")
    analizador.add_argument(
        "--variante", choices=("base", "rama", "ambas"), default="ambas", help="por defecto ambas"
    )
    analizador.add_argument(
        "--base", default=sv2_fecha.BASE_POR_DEFECTO,
        help="referencia de git de la que salen los YAML de la variante base (por defecto dev)",
    )
    analizador.add_argument("--casos-fecha", default=str(RUTA_CASOS_FECHA), help="juego A")
    analizador.add_argument("--sinteticos", default=str(RUTA_SINTETICOS), help="juego D")
    analizador.add_argument(
        "--salida", default="",
        help="directorio de la corrida, CON valores (por defecto evals/salidas/comparar_fecha/<fecha-hora>/)",
    )
    analizador.add_argument(
        "--resumen", default=str(RUTA_RESUMEN_VERSIONABLE),
        help="resumen SIN valores para versionar (por defecto progress/comparar_fecha_F-112.md)",
    )
    analizador.add_argument(
        "--albaranes", default=str(sv2_extraccion.RUTA_ALBARANES),
        help="directorio de los albaranes (por defecto evals/inputs/albaranes)",
    )
    analizador.add_argument(
        "--solo-validar", action="store_true",
        help="solo las comprobaciones previas; no llama a ninguna IA",
    )
    return analizador


def main(
    argv: list[str] | None = None,
    *,
    entorno: dict | None = None,
    dependencias: Dependencias | None = None,
) -> int:
    """CLI. Códigos: 0 hecho (o todo valida), 1 ninguna extracción salió, 2 parada antes de gastar."""
    analizador = _analizador()
    opciones = analizador.parse_args(argv)
    juegos = list(dict.fromkeys(j.strip().upper() for j in opciones.juegos.split(",") if j.strip()))
    if not juegos or not set(juegos) <= set(JUEGOS):
        analizador.error("--juegos admite A, B, C y D")
    if opciones.repeticiones < 1:
        analizador.error("--repeticiones tiene que ser 1 o más")
    opciones.lista_juegos = [j for j in JUEGOS if j in juegos]

    try:
        return ejecutar(
            opciones,
            entorno if entorno is not None else dict(os.environ),
            dependencias or Dependencias(),
        )
    except (Parada, ClavesAusentes, sv2_fecha.BaseNoDisponible) as error:
        print(f"comparar_fecha: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
