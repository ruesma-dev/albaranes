# tests/test_f070_codigo_obra.py
"""F-070 · La obra siempre con el 0 inicial, salvo VAR y POSTV2 (R1–R5).

Regla del humano (literal): «es crucial que añada el 0 inicial si no es VAR
ni POSTV2». VAR y POSTV2 son códigos de obra válidos en Sigrid y se dejan tal
cual, en mayúsculas. Un único punto en comun (``ruesma_comun.obras``): sv3,
sv4 y sv9 lo importan, nadie repite los literales (R5).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from ruesma_comun.obras import (
    CODIGOS_OBRA_SIN_CERO,
    canonizar_codigo_obra,
    normalizar_codigo_obra,
)


# ---------------------------------------------------------------- #
# R1 — 3 dígitos ⇒ 0 delante; 4 dígitos con 0 ⇒ el mismo (sin cambios).
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("686", "0686"),
        (" 686 ", "0686"),
        ("0686", "0686"),
        (" 0686\t", "0686"),
        ("900", "0900"),  # P1 de la PARADA 1: regla tal cual, sin excepción
        ("000", "0000"),
    ],
)
def test_f070_r1_tres_digitos_llevan_cero(valor, esperado):
    assert normalizar_codigo_obra(valor) == esperado


def test_f070_r1_entero_de_tres_cifras():
    assert normalizar_codigo_obra(686) == "0686"  # type: ignore[arg-type]


# ---------------------------------------------------------------- #
# R2 — VAR y POSTV2 en cualquier combinación de mayúsculas ⇒ en mayúsculas.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("VAR", "VAR"),
        ("var", "VAR"),
        (" Var ", "VAR"),
        ("POSTV2", "POSTV2"),
        ("postv2", "POSTV2"),
        (" Postv2 ", "POSTV2"),
        ("\tpOsTv2\n", "POSTV2"),
    ],
)
def test_f070_r2_var_y_postv2_son_canonicos(valor, esperado):
    assert normalizar_codigo_obra(valor) == esperado


def test_f070_r2_lista_de_codigos_sin_cero_es_exactamente_var_y_postv2():
    """P2 de la PARADA 1: solo VAR y POSTV2; nada más se cuela."""
    assert CODIGOS_OBRA_SIN_CERO == frozenset({"VAR", "POSTV2"})
    assert isinstance(CODIGOS_OBRA_SIN_CERO, frozenset)


# ---------------------------------------------------------------- #
# R3 — cualquier otra cosa ⇒ None, como hoy.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    "valor",
    [
        None, "", "   ", "7", "12", "1234", "1001", "12345", "123456",
        "GG", "CM", "POSTV", "POSTV3", "VARIOS", "VA R", "0578-B", "0676B",
        "06a1", "686.", "V AR", "XVAR", "VARX", "0VAR",
    ],
)
def test_f070_r3_otros_valores_no_son_canonicos(valor):
    assert normalizar_codigo_obra(valor) is None


# ---------------------------------------------------------------- #
# R4 — canonizar: el canónico si lo hay; si no, el valor recortado.
# ---------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("686", "0686"),
        (" 686 ", "0686"),
        ("0686", "0686"),
        (" var ", "VAR"),
        ("Postv2", "POSTV2"),
        (" GG ", "GG"),
        ("gg", "gg"),          # lo que no encaja va tal cual (solo recortado)
        ("1234", "1234"),
        (" 0578-B ", "0578-B"),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_f070_r4_canonizar(valor, esperado):
    assert canonizar_codigo_obra(valor) == esperado


def test_f070_r4_canonizar_entero():
    assert canonizar_codigo_obra(686) == "0686"  # type: ignore[arg-type]
    assert canonizar_codigo_obra(1234) == "1234"  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "valor",
    ["686", " var ", "POSTV2", " GG ", "1234", "", None, "0686", "x y"],
)
def test_f070_r4_canonizar_es_idempotente(valor):
    una = canonizar_codigo_obra(valor)
    assert canonizar_codigo_obra(una) == una


# ---------------------------------------------------------------- #
# R5 — VAR y POSTV2 definidos UNA sola vez, en ruesma_comun.obras.
# ---------------------------------------------------------------- #
_RAIZ_SERVICIOS = Path(__file__).resolve().parents[2]
_UNICO_SITIO = (
    _RAIZ_SERVICIOS / "albaranes-comun" / "ruesma_comun" / "obras" / "codigo.py"
)
_EXCLUIDOS = {"tests", ".venv", "venv", "__pycache__", "node_modules"}


def _ficheros_de_produccion() -> list[Path]:
    ficheros = []
    for ruta in _RAIZ_SERVICIOS.rglob("*.py"):
        relativa = ruta.relative_to(_RAIZ_SERVICIOS)
        if any(parte in _EXCLUIDOS for parte in relativa.parts):
            continue
        ficheros.append(ruta)
    return ficheros


def _literales_prohibidos(ruta: Path) -> list[int]:
    arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"), filename=str(ruta))
    return [
        nodo.lineno
        for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Constant)
        and isinstance(nodo.value, str)
        and nodo.value.strip().upper() in {"VAR", "POSTV2"}
    ]


def test_f070_r5_recorre_los_servicios():
    """Guarda del propio test: si el recorrido no viera nada, pasaría en falso."""
    ficheros = _ficheros_de_produccion()
    assert _UNICO_SITIO in ficheros
    servicios = {f.relative_to(_RAIZ_SERVICIOS).parts[0] for f in ficheros}
    assert {
        "albaranes-persistencia", "albaranes-front", "albaranes-alta-sigrid",
    } <= servicios
    assert _literales_prohibidos(_UNICO_SITIO), "la constante debe vivir aquí"


def test_f070_r5_var_y_postv2_solo_en_ruesma_comun_obras():
    repetidos = {
        str(ruta.relative_to(_RAIZ_SERVICIOS)): lineas
        for ruta in _ficheros_de_produccion()
        if ruta != _UNICO_SITIO and (lineas := _literales_prohibidos(ruta))
    }
    assert repetidos == {}, (
        "VAR/POSTV2 repetidos fuera de ruesma_comun/obras/codigo.py: "
        f"{repetidos}. Usa CODIGOS_OBRA_SIN_CERO."
    )
