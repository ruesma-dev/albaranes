# tests/test_f051_puntos_de_composicion.py
"""F-051 · review H1 — todo punto que compone el builder de sv6 pasa los ajustes.

Un parámetro de constructor que nace APAGADO (``almacen_sin_partida=False``,
``familias_destinadas=frozenset()``) es un interruptor silencioso: el punto
de composición que no lo pase sigue valorando como antes de la feature y
ningún test de sv6 lo nota. Le pasó a ``evals/procesos/sv6_build.py``: los
evals deterministas (IA3 y E2E) medían la partida sin R1 ni R4.

Este fichero recorre TODOS los puntos de composición (el worker, la API HTTP
y el banco de evals) y falla si:

- aparece un punto nuevo que no está en la lista (hay que mirarlo a mano);
- alguno no pasa un parámetro del constructor (cualquiera, no solo los de
  F-051: así vale para la próxima feature que añada uno);
- alguno pasa un valor distinto del que le toca (``Settings`` en sv6, las
  constantes replicadas en el banco);
- las constantes del banco se separan de los valores por defecto de
  ``Settings`` de sv6;
- el build real del banco (subproceso, sin red ni BBDD ni LLM) no manda a
  almacén una línea sin partida.

Se lee el fuente con ``ast`` porque importar sv6 en este proceso choca con
los paquetes de primer nivel de sv2/sv5 (por eso existe el subproceso).
"""

from __future__ import annotations

import ast
import os
from pathlib import Path

import pytest

import evals.procesos.sv6_build as banco
from evals.procesos.sv6_build import (
    construir_envelope_estimulado,
    ejecutar_en_subproceso,
)

RAIZ = Path(__file__).resolve().parents[1]
SV6 = RAIZ / "services" / "albaran-valoracion-persist"

#: Clases cuyo constructor lleva ajustes de sv6 y dónde se definen.
CLASES_COMPUESTAS = {
    "ValuationBuilder": SV6 / "application" / "services" / "valuation_builder.py",
    "PartidaMatcher": SV6 / "application" / "services" / "partida_matcher.py",
}

_SV6_REL = "services/albaran-valoracion-persist/"
COMPOSICION = _SV6_REL + "interface_adapters/composition.py"
API = _SV6_REL + "interface_adapters/api/app.py"
EVALS = "evals/procesos/sv6_build.py"

#: Puntos de composición conocidos (rutas relativas a la raíz, con «/»).
PUNTOS_CONOCIDOS = frozenset({COMPOSICION, API, EVALS})

#: Valor (``ast.unparse``) que cada punto pasa a cada ajuste de F-051.
_DESDE_SETTINGS = {
    ("PartidaMatcher", "almacen_sin_partida"): "settings.almacen_sin_partida_enabled",
    ("ValuationBuilder", "familias_destinadas"): (
        "familias_destinadas_de_csv(settings.familias_destinadas)"
    ),
}
VALORES_ESPERADOS = {
    COMPOSICION: _DESDE_SETTINGS,
    API: _DESDE_SETTINGS,
    EVALS: {
        ("PartidaMatcher", "almacen_sin_partida"): "ALMACEN_SIN_PARTIDA",
        ("ValuationBuilder", "familias_destinadas"): (
            "familias_destinadas_de_csv(FAMILIAS_DESTINADAS)"
        ),
    },
}

#: Constante del banco ↔ campo de ``Settings`` de sv6 que replica.
CONSTANTES_DEL_BANCO = {
    "TOLERANCIA_PRECIO_PCT": "price_tolerance_pct",
    "TOLERANCIA_IMPORTE_PCT": "importe_tolerance_pct",
    "CODIGO_PARTIDA_ALM": "alm_codigo_partida",
    "ALMACEN_SIN_PARTIDA": "almacen_sin_partida_enabled",
    "FAMILIAS_DESTINADAS": "familias_destinadas",
}

_DIRECTORIOS_FUERA = {
    ".git", ".venv", "venv", "__pycache__", "node_modules", "tests",
    ".pytest_cache", ".mypy_cache", ".ruff_cache",
}


def _arbol(ruta: Path) -> ast.Module:
    return ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))


def _nombre_llamado(nodo: ast.Call) -> str | None:
    if isinstance(nodo.func, ast.Name):
        return nodo.func.id
    if isinstance(nodo.func, ast.Attribute):
        return nodo.func.attr
    return None


def _llamadas(arbol: ast.AST, clase: str) -> list[ast.Call]:
    return [
        nodo
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call) and _nombre_llamado(nodo) == clase
    ]


def _parametros_del_constructor(clase: str) -> set[str]:
    """Nombres de los parámetros de ``__init__`` (sin ``self``)."""
    for nodo in ast.walk(_arbol(CLASES_COMPUESTAS[clase])):
        if isinstance(nodo, ast.ClassDef) and nodo.name == clase:
            for miembro in nodo.body:
                if isinstance(miembro, ast.FunctionDef) and miembro.name == "__init__":
                    argumentos = miembro.args
                    nombres = [a.arg for a in argumentos.args + argumentos.kwonlyargs]
                    return {n for n in nombres if n != "self"}
    raise AssertionError(f"no encuentro {clase}.__init__")


def _puntos_de_composicion() -> set[str]:
    """Ficheros de código (no tests) que construyen alguna clase compuesta."""
    puntos: set[str] = set()
    for carpeta, subcarpetas, ficheros in os.walk(RAIZ):
        subcarpetas[:] = [
            s for s in subcarpetas
            if s not in _DIRECTORIOS_FUERA and not s.startswith(".")
        ]
        for nombre in ficheros:
            if not nombre.endswith(".py") or nombre.startswith("test_"):
                continue
            ruta = Path(carpeta) / nombre
            texto = ruta.read_text(encoding="utf-8", errors="replace")
            if not any(f"{clase}(" in texto for clase in CLASES_COMPUESTAS):
                continue
            try:
                arbol = ast.parse(texto)
            except SyntaxError:
                continue
            if any(_llamadas(arbol, clase) for clase in CLASES_COMPUESTAS):
                puntos.add(ruta.relative_to(RAIZ).as_posix())
    return puntos


def _defaults_de_settings() -> dict[str, object]:
    """Valor por defecto de cada campo de ``Settings`` de sv6 (literal)."""
    defaults: dict[str, object] = {}
    for nodo in ast.walk(_arbol(SV6 / "config" / "settings.py")):
        if isinstance(nodo, ast.ClassDef) and nodo.name == "Settings":
            for miembro in nodo.body:
                if (
                    isinstance(miembro, ast.AnnAssign)
                    and isinstance(miembro.target, ast.Name)
                    and isinstance(miembro.value, ast.Call)
                    and miembro.value.args
                ):
                    try:
                        defaults[miembro.target.id] = ast.literal_eval(
                            miembro.value.args[0]
                        )
                    except ValueError:
                        continue
    return defaults


def test_f051_h1_los_puntos_de_composicion_son_los_conocidos():
    """Un punto nuevo no puede colarse sin que alguien lo revise aquí."""
    assert _puntos_de_composicion() == PUNTOS_CONOCIDOS


@pytest.mark.parametrize("punto", sorted(PUNTOS_CONOCIDOS))
@pytest.mark.parametrize("clase", sorted(CLASES_COMPUESTAS))
def test_f051_h1_cada_punto_pasa_todos_los_parametros_del_constructor(punto, clase):
    """Ningún parámetro se queda en su valor por defecto (apagado) sin decirlo."""
    llamadas = _llamadas(_arbol(RAIZ / punto), clase)
    assert llamadas, f"{punto} no construye {clase}"
    parametros = _parametros_del_constructor(clase)
    for llamada in llamadas:
        pasados = {k.arg for k in llamada.keywords}
        assert parametros <= pasados, (
            f"{punto}: {clase}(...) no pasa {sorted(parametros - pasados)}"
        )


@pytest.mark.parametrize("punto", sorted(PUNTOS_CONOCIDOS))
def test_f051_h1_cada_punto_pasa_el_valor_que_le_toca(punto):
    arbol = _arbol(RAIZ / punto)
    for (clase, parametro), esperado in VALORES_ESPERADOS[punto].items():
        for llamada in _llamadas(arbol, clase):
            valores = {k.arg: ast.unparse(k.value) for k in llamada.keywords}
            assert valores.get(parametro) == esperado, (
                f"{punto}: {clase}({parametro}=...) vale {valores.get(parametro)!r}"
            )


@pytest.mark.parametrize("constante,campo", sorted(CONSTANTES_DEL_BANCO.items()))
def test_f051_h1_el_banco_replica_los_valores_por_defecto_de_settings(
    constante, campo
):
    defaults = _defaults_de_settings()
    assert campo in defaults, f"Settings de sv6 ya no tiene {campo}"
    assert getattr(banco, constante, None) == defaults[campo], (
        f"evals: {constante} se ha separado de Settings.{campo}"
    )


# --- Comportamiento: el build real del banco aplica F-051 --------------------

_CASO = "HOR-951"


def _inputs() -> dict:
    return {
        "caso_id": _CASO,
        "fase": "INPUTS",
        "tipologia": "Hormigon",
        "libro": "INPUTS.xlsx",
        "sha256_libro": "x" * 64,
        "tablas": {
            "caso": [{
                "caso_id": _CASO, "tipologia": "Hormigon", "ia_destino": "ambas",
                "origen": "manual", "contrato_codigo": "CTSU26/0001",
                "descripcion_caso": "línea sin partida en el albarán",
            }],
            "lineas_albaran": [{
                "caso_id": _CASO, "num_linea": 1, "descripcion": "HA-25/B/20/IIa",
                "cantidad": 8, "unidad": "m3", "precio_unitario": 72.5,
                "descuentos": None, "importe": 580.0,
                "codigo_imputacion": None, "observaciones_albaran": None,
            }],
            "contrato_lineas": [{
                "caso_id": _CASO, "codigo_producto": "P-100",
                "descripcion_recurso": "HA-25/B/20/IIa", "unidad": "m3",
                "precio_unitario": 72.5, "codigo_partida": "01.02.03",
                "comentario": None,
            }],
            "condiciones": [{
                "caso_id": _CASO, "campo": "fecha_albaran",
                "valor": "2026-03-04", "comentario": None,
            }],
        },
    }


def _ia3() -> dict:
    return {
        "caso_id": _CASO,
        "fase": "IA3",
        "tipologia": "Hormigon",
        "libro": "IA3_valoracion.xlsx",
        "sha256_libro": "y" * 64,
        "tablas": {
            "lineas_valoradas": [{
                "caso_id": _CASO, "num_linea": 1, "match_method": "exact_concept",
                "codigo_producto_contrato": "P-100",
                "codigo_partida_final": None, "precio_unitario_final": 72.5,
                "precio_source": "contrato_db", "importe_calculado": 580.0,
                "review_required": "?", "comentario": None,
            }],
            "sinteticas_esperadas": [],
            "sinteticas_prohibidas": [],
        },
    }


def test_f051_h1_el_build_del_banco_manda_a_almacen_la_linea_sin_partida():
    """R1 y R4 en el banco: sin partida ⇒ almacén; hormigón ⇒ a revisión."""
    envelope = construir_envelope_estimulado(_inputs(), _ia3())
    salida = ejecutar_en_subproceso(
        {"casos": [{"caso_id": _CASO, "envelope": envelope}]}
    )

    base = next(
        linea
        for linea in salida["resultados"][0]["lineas"]
        if linea["line_kind"] == "from_albaran"
    )
    assert base["partida_action"] == "almacen_sin_partida"
    assert base["codigo_partida_final"] is None
    assert "partida_ausente_familia_destinada" in base["review_reasons"]
