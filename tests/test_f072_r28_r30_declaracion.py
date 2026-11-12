# tests/test_f072_r28_r30_declaracion.py
"""F-072 · R28–R30: la declaración de albaranes y su documentación.

Los siete servicios que importan `ruesma_comun` lo declaran (dependencia de la
carpeta de la comun y módulo vigilado), para que un commit en la comun invalide
su caché y un worktree que importa la comun de otro árbol lo diga. La comun e
`infra` no declaran nada. El ejemplo documenta los tres campos nuevos.

R30 (que `harness/ARNES_VERSION.md` anotase la caché de la 1.7.16 sobre un
arnés sellado en la 1.7.2) se retiró al actualizar el arnés a la 1.10.0: el
repositorio ya no lleva piezas sueltas y esa nota dejó de existir.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness.servicios import cargar_servicios

RAIZ = Path(__file__).resolve().parents[1]
COMUN = "services/albaranes-comun"
CON_COMUN = ("sv1-email", "sv2-api", "sv3-persistencia", "sv4-front",
             "sv5-valoracion-api", "sv6-valoracion-persist", "sv9-alta-sigrid")


def _declarados() -> dict:
    return {s.nombre: s for s in cargar_servicios(raiz=str(RAIZ))}


@pytest.mark.parametrize("nombre", CON_COMUN)
def test_f072_r28_los_siete_servicios_declaran_la_comun(nombre: str) -> None:
    servicio = _declarados()[nombre]

    assert servicio.depende_de == (COMUN,)
    assert servicio.importa == ("ruesma_comun",)
    assert servicio.entradas_no_versionadas == ()


@pytest.mark.parametrize("nombre", ["comun", "infra"])
def test_f072_r28_comun_e_infra_no_declaran_nada(nombre: str) -> None:
    servicio = _declarados()[nombre]

    assert (servicio.depende_de, servicio.importa, servicio.entradas_no_versionadas) == (
        (), (), ())


def test_f072_r28_ningun_otro_servicio_python_importa_la_comun_sin_declararla() -> None:
    """Si mañana otro servicio importa la comun, este test lo pide en la declaración."""
    sin_declarar = []
    for servicio in _declarados().values():
        if servicio.lenguaje != "python" or servicio.nombre == "comun":
            continue
        carpeta = RAIZ / servicio.ruta
        usa = any(
            "ruesma_comun" in fichero.read_text(encoding="utf-8", errors="replace")
            for fichero in carpeta.rglob("*.py")
            if ".venv" not in fichero.parts and "__pycache__" not in fichero.parts
        )
        if usa and "ruesma_comun" not in servicio.importa:
            sin_declarar.append(servicio.nombre)

    assert sin_declarar == []


def test_f072_r29_el_ejemplo_documenta_y_usa_los_tres_campos() -> None:
    ejemplo = json.loads((RAIZ / "harness" / "servicios.ejemplo.json").read_text(
        encoding="utf-8"))
    campos = ("depende_de", "importa", "entradas_no_versionadas")

    for campo in campos:
        assert campo in ejemplo["$doc"]
    assert any(all(campo in servicio for campo in campos)
               for servicio in ejemplo["servicios"])
    assert "find_spec" in ejemplo["$doc"] or "conftest" in ejemplo["$doc"]

