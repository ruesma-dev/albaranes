# tests/test_estructura_monorepo.py
"""Coherencia entre `harness/servicios.json` y el árbol real del monorepo.

F-001. El arnés declara los servicios en `harness/servicios.json` y a partir de
esa declaración decide qué comprueba y qué no (ver sección 7 bis de
`harness/init.sh`). Si la declaración se desalinea del árbol —una ruta que se
renombra, un servicio que se mueve— el portero deja de mirar donde debe y lo
hace en silencio. Estos tests convierten esa desalineación en un fallo ruidoso.

Solo biblioteca estándar (`ast`, `json`, `pathlib`): sin red, sin base de datos
y sin importar código de ningún servicio, de modo que la suite de la raíz corre
con el intérprete de la raíz y no necesita los entornos de los servicios.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

#: Raíz del repositorio: este fichero vive en `<raíz>/tests/`.
RAIZ_REPO = Path(__file__).resolve().parents[1]

#: Declaración de servicios que consume el arnés.
RUTA_SERVICIOS = RAIZ_REPO / "harness" / "servicios.json"

#: Primera línea obligatoria de todo fichero de código (docs/CONVENTIONS.md).
CABECERA_ESPERADA = "# tests/test_estructura_monorepo.py"

#: Un servicio Python es ejecutable o instalable: trae uno de estos dos.
MANIFIESTOS_PYTHON = ("pyproject.toml", "main.py")

#: Módulos que este fichero puede importar. Todos de la biblioteca estándar:
#: la lista es la que hace verificable el criterio «sin red ni BBDD».
MODULOS_PERMITIDOS = frozenset({"__future__", "ast", "json", "pathlib"})


def cargar_servicios(ruta: Path = RUTA_SERVICIOS) -> list[dict]:
    """Devuelve los servicios declarados en `ruta`.

    Falla explícitamente si el fichero no existe o no declara ninguno: una
    declaración vacía haría pasar en vacío todos los tests de este módulo.
    """
    assert ruta.is_file(), f"No existe la declaración de servicios: {ruta}"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    servicios = datos.get("servicios", [])
    assert servicios, f"{ruta} no declara ningún servicio"
    return servicios


def es_python(servicio: dict) -> bool:
    """¿El servicio está declarado como Python?"""
    return str(servicio.get("lenguaje", "")).strip().lower() == "python"


def modulos_importados(ruta: Path) -> set[str]:
    """Módulos raíz que importa `ruta`, leídos de su árbol sintáctico."""
    arbol = ast.parse(ruta.read_text(encoding="utf-8"))
    modulos: set[str] = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name.split(".")[0] for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level:  # import relativo: no es un módulo externo
                continue
            modulos.add((nodo.module or "").split(".")[0])
    return modulos


def test_f001_r1_el_fichero_declara_su_ruta_en_la_primera_linea() -> None:
    """R1: primera línea = comentario con la ruta relativa del fichero."""
    fichero = Path(__file__).resolve()
    primera_linea = fichero.read_text(encoding="utf-8").splitlines()[0]
    assert primera_linea == CABECERA_ESPERADA, (
        f"La primera línea debe ser {CABECERA_ESPERADA!r} "
        f"(docs/CONVENTIONS.md), y es {primera_linea!r}"
    )


def test_f001_r2_cada_ruta_declarada_existe_como_directorio() -> None:
    """R2: toda `ruta` de servicios.json existe como directorio del repo."""
    inexistentes = [
        f"{servicio.get('nombre', '(sin nombre)')} -> {servicio['ruta']}"
        for servicio in cargar_servicios()
        if not (RAIZ_REPO / servicio["ruta"]).is_dir()
    ]
    assert not inexistentes, (
        "harness/servicios.json declara rutas que no existen como directorio "
        f"del repositorio: {inexistentes}"
    )


def test_f001_r3_cada_servicio_python_trae_pyproject_o_main() -> None:
    """R3: todo servicio Python declarado trae `pyproject.toml` o `main.py`."""
    sin_manifiesto = [
        f"{servicio.get('nombre', '(sin nombre)')} -> {servicio['ruta']}"
        for servicio in cargar_servicios()
        if es_python(servicio)
        and not any(
            (RAIZ_REPO / servicio["ruta"] / nombre).is_file()
            for nombre in MANIFIESTOS_PYTHON
        )
    ]
    assert not sin_manifiesto, (
        "Servicios declarados como python sin ninguno de "
        f"{list(MANIFIESTOS_PYTHON)}: {sin_manifiesto}"
    )


def test_f001_r4_el_test_solo_importa_biblioteca_estandar() -> None:
    """R4: este módulo no puede tocar red ni BBDD; solo importa stdlib."""
    prohibidos = sorted(modulos_importados(Path(__file__).resolve()) - MODULOS_PERMITIDOS)
    assert not prohibidos, (
        "Este test debe funcionar solo con filesystem y json de la biblioteca "
        f"estándar; importa además: {prohibidos}"
    )
