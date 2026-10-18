# tests/test_f064_empresas_cliente.py
"""F-064 · R1–R4: la lista de empresas del cliente que leen IA1 e IA2.

El CLIENTE de todos los albaranes es la constructora (hoy, una sola empresa:
la de ``CIFS_PROPIOS_POR_DEFECTO`` de ``ruesma_comun``). Su CIF va impreso en
los albaranes y la IA lo leyó como CIF del proveedor (FEYMACO, 2026-10-08).
F-064 le dice a la IA cuáles son, con un bloque que sale de la MISMA fuente
que el descarte de F-063 en sv3: ``ruesma_comun.proveedores``.

- R1: una sola fuente (``CIFS_PROPIOS_POR_DEFECTO`` + ``cifs_propios``),
  ampliada con ``CIFS_PROPIOS``; sv2 no mantiene lista propia.
- R2: sv2 lee ``CIFS_PROPIOS`` y se la pasa al servicio (worker y API).
- R3: bloque determinista, ``CIF — razón social``, CIF normalizado.
- R4: una empresa nueva llega al prompt de IA1 y al de IA2 sin tocar YAML.

Sin red ni LLM. CIF inventados (``B99999999``, ``Q0000000J``).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest
from application.services.empresas_cliente import (
    MARCADOR_EMPRESAS_CLIENTE,
    EmpresaCliente,
    empresas_cliente,
    render_empresas_cliente,
)
from ruesma_comun import proveedores
from ruesma_comun.proveedores import CIFS_PROPIOS_POR_DEFECTO

RAIZ = Path(__file__).resolve().parents[1]
CABECERA = "EMPRESAS DEL CLIENTE (CIF — razón social):"
SIN_RAZON = "empresa del grupo, sin razón social configurada"

#: Las de serie, tal como las da ``ruesma_comun`` (hoy, una).
DE_SERIE = tuple(
    EmpresaCliente(cif=cif, razon_social=razon)
    for cif, razon in CIFS_PROPIOS_POR_DEFECTO.items()
)


# ------------------------------------------------------------------ #
# R1 · una sola fuente: ruesma_comun.proveedores
# ------------------------------------------------------------------ #
def test_f064_r1_sin_extra_son_las_de_serie_con_su_razon_social() -> None:
    assert empresas_cliente(None) == DE_SERIE
    assert empresas_cliente("") == DE_SERIE
    assert empresas_cliente() == DE_SERIE


def test_f064_r1_hoy_la_de_serie_es_la_constructora() -> None:
    """Ancla del caso real: A81873903 con la razón social de serie."""
    assert empresas_cliente(None) == (
        EmpresaCliente(cif="A81873903", razon_social="Construcciones Ruesma"),
    )


def test_f064_r1_cifs_propios_solo_amplia_tras_las_de_serie() -> None:
    lista = empresas_cliente("B99999999")

    assert lista[: len(DE_SERIE)] == DE_SERIE
    assert lista[len(DE_SERIE):] == (
        EmpresaCliente(cif="B99999999", razon_social=None),
    )


def test_f064_r1_repetir_una_de_serie_en_cifs_propios_no_la_duplica() -> None:
    """Ni la duplica ni le quita la razón social: solo amplía."""
    assert empresas_cliente("a-81873903, A81873903") == DE_SERIE


def test_f064_r1_usa_cifs_propios_de_comun(monkeypatch) -> None:
    """La ampliación pasa por ``cifs_propios`` de comun (misma regla que sv3):
    si comun cambia sus separadores o su normalización, sv2 lo hereda."""
    llamadas: list[str | None] = []
    original = proveedores.cifs_propios

    def espia(extra):
        llamadas.append(extra)
        return original(extra)

    monkeypatch.setattr(
        "application.services.empresas_cliente.cifs_propios", espia,
    )

    empresas_cliente("B99999999")

    assert llamadas == ["B99999999"]


def test_f064_r1_ningun_codigo_de_sv2_escribe_el_cif_a_mano() -> None:
    """sv2 no mantiene lista propia: el CIF de serie no aparece en su código
    Python (fuera de los tests). Los YAML los fija R5."""
    cif = "A81873903"
    encontrados = [
        ruta.relative_to(RAIZ).as_posix()
        for ruta in RAIZ.rglob("*")
        if ruta.suffix == ".py"
        and "tests" not in ruta.relative_to(RAIZ).parts
        and ".venv" not in ruta.parts
        and cif in ruta.read_text(encoding="utf-8", errors="replace")
    ]
    assert encontrados == []


# ------------------------------------------------------------------ #
# R3 · bloque determinista
# ------------------------------------------------------------------ #
def test_f064_r3_bloque_con_cabecera_y_una_linea_por_empresa() -> None:
    bloque = render_empresas_cliente(empresas_cliente(None))

    assert bloque == f"{CABECERA}\n  - A81873903 — Construcciones Ruesma"


def test_f064_r3_anadidas_ordenadas_normalizadas_y_con_texto_fijo() -> None:
    bloque = render_empresas_cliente(empresas_cliente("q-0000000-j; b-99.999.999"))

    assert bloque.splitlines() == [
        CABECERA,
        "  - A81873903 — Construcciones Ruesma",
        f"  - B99999999 — {SIN_RAZON}",
        f"  - Q0000000J — {SIN_RAZON}",
    ]


def test_f064_r3_mismo_dato_mismo_bloque() -> None:
    """Determinista: el orden de la variable no cambia el prompt."""
    assert render_empresas_cliente(
        empresas_cliente("Q0000000J,B99999999"),
    ) == render_empresas_cliente(empresas_cliente("B99999999 Q0000000J"))


def test_f064_r3_las_de_serie_conservan_el_orden_del_diccionario(monkeypatch) -> None:
    monkeypatch.setitem(CIFS_PROPIOS_POR_DEFECTO, "B99999999", "Zeta Demo")
    monkeypatch.setitem(CIFS_PROPIOS_POR_DEFECTO, "B11111111", "Alfa Demo")

    cifs = [empresa.cif for empresa in empresas_cliente(None)]

    assert cifs == ["A81873903", "B99999999", "B11111111"]


def test_f064_r3_una_de_serie_sin_razon_social_lleva_el_texto_fijo(monkeypatch) -> None:
    monkeypatch.setitem(CIFS_PROPIOS_POR_DEFECTO, "B99999999", "")

    bloque = render_empresas_cliente(empresas_cliente(None))

    assert bloque.splitlines()[-1] == f"  - B99999999 — {SIN_RAZON}"


def test_f064_r3_el_cif_de_serie_tambien_va_normalizado(monkeypatch) -> None:
    monkeypatch.setitem(CIFS_PROPIOS_POR_DEFECTO, "b-99.999.999", "Demo")

    assert empresas_cliente(None)[-1] == EmpresaCliente(
        cif="B99999999", razon_social="Demo",
    )


def test_f064_r3_sin_empresas_el_bloque_lo_dice() -> None:
    assert render_empresas_cliente(()) == f"{CABECERA}\n  - (ninguna)"


def test_f064_r3_el_marcador_es_el_de_la_spec() -> None:
    assert MARCADOR_EMPRESAS_CLIENTE == "{empresas_cliente}"


# ------------------------------------------------------------------ #
# R4 · una empresa nueva de serie entra sin tocar YAML (lista)
# ------------------------------------------------------------------ #
def test_f064_r4_lee_el_diccionario_en_cada_llamada(monkeypatch) -> None:
    antes = empresas_cliente(None)
    monkeypatch.setitem(CIFS_PROPIOS_POR_DEFECTO, "B99999999", "Grupo Demo")

    despues = empresas_cliente(None)

    assert despues == antes + (EmpresaCliente("B99999999", "Grupo Demo"),)


# ------------------------------------------------------------------ #
# Capa: application pura, solo importa ruesma_comun.proveedores
# ------------------------------------------------------------------ #
def test_f064_modulo_puro_solo_importa_comun_proveedores() -> None:
    ruta = RAIZ / "application" / "services" / "empresas_cliente.py"
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    modulos = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom):
            modulos.add(nodo.module)
        elif isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)

    assert modulos <= {"__future__", "dataclasses", "ruesma_comun.proveedores"}


@pytest.mark.parametrize("empresa", DE_SERIE)
def test_f064_r3_empresa_es_inmutable(empresa) -> None:
    with pytest.raises(AttributeError):
        empresa.cif = "B99999999"  # type: ignore[misc]


# ------------------------------------------------------------------ #
# R2 · sv2 lee CIFS_PROPIOS y se la pasa al servicio
# ------------------------------------------------------------------ #
_COMPOSICIONES = (
    RAIZ / "interface_adapters" / "composition.py",
    RAIZ / "interface_adapters" / "api" / "app.py",
)


def _settings(**entorno):
    from config.settings import Settings

    return Settings(
        _env_file=None,
        ENABLE_OPENAI=False,
        ENABLE_CLAUDE=False,
        GEMINI_API_KEY="x",
        IA_SEGUNDA_FASE="gemini",
        **entorno,
    )


def test_f064_r2_cifs_propios_es_opcional_y_vacio_por_defecto() -> None:
    assert _settings().cifs_propios == ""


def test_f064_r2_cifs_propios_se_lee_del_entorno(monkeypatch) -> None:
    monkeypatch.setenv("CIFS_PROPIOS", "B99999999")

    assert _settings().cifs_propios == "B99999999"


def _argumento_empresas(ruta: Path) -> list[str]:
    """Lo que pasa cada ``AlbaranExtractionService(...)`` de ``ruta`` como
    ``empresas_cliente`` (``ast.unparse``), o ``"FALTA"``."""
    valores = []
    for nodo in ast.walk(ast.parse(ruta.read_text(encoding="utf-8"))):
        if not (isinstance(nodo, ast.Call) and getattr(nodo.func, "id", None) == "AlbaranExtractionService"):
            continue
        argumento = next((k for k in nodo.keywords if k.arg == "empresas_cliente"), None)
        valores.append(ast.unparse(argumento.value) if argumento else "FALTA")
    return valores


def test_f064_r2_worker_y_api_pasan_la_lista_de_cifs_propios() -> None:
    for ruta in _COMPOSICIONES:
        assert _argumento_empresas(ruta) == ["empresas_cliente(settings.cifs_propios)"], ruta.name


def test_f064_r2_sin_argumento_el_servicio_usa_la_lista_de_serie() -> None:
    from test_f064_prompt_ia1_proveedor import _instructions_fase_1

    assert render_empresas_cliente(empresas_cliente(None)) in _instructions_fase_1()


def test_f064_r2_con_cifs_propios_la_anadida_llega_al_prompt() -> None:
    from test_f064_prompt_ia1_proveedor import _instructions_fase_1

    instructions = _instructions_fase_1(empresas_cliente=empresas_cliente("B99999999"))

    assert f"  - B99999999 — {SIN_RAZON}" in instructions


# ------------------------------------------------------------------ #
# R4 · una empresa nueva de serie llega a IA1 y a IA2 sin tocar YAML
# ------------------------------------------------------------------ #
def test_f064_r4_una_de_serie_nueva_llega_a_ia1_y_a_ia2(monkeypatch) -> None:
    from test_f064_prompt_ia1_proveedor import _instructions_fase_1
    from test_f064_prompt_ia2_proveedor import CLAVES_FASE_2, _instructions_fase_2

    monkeypatch.setitem(CIFS_PROPIOS_POR_DEFECTO, "B99999999", "Grupo Demo")
    linea = "  - B99999999 — Grupo Demo"

    assert linea in _instructions_fase_1()
    for clave in CLAVES_FASE_2:
        assert linea in _instructions_fase_2(clave), clave


def test_f064_r3_dos_de_serie_que_normalizan_igual_salen_una_vez(monkeypatch) -> None:
    """La primera manda (con su razón social); la repetida no duplica el CIF."""
    monkeypatch.setitem(CIFS_PROPIOS_POR_DEFECTO, "a-81873903", "Otra razón")

    assert empresas_cliente(None) == DE_SERIE[:1]
