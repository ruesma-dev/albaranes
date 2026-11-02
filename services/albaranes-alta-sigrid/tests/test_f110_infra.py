# tests/test_f110_infra.py
"""F-110 · T4 · la guarda ``ALTA_SIGRID_ENVIAR_DTO`` en ``infra/`` (R20).

Tests de texto sobre los ``.ps1`` (como los de F-053 y F-069): nadie los
ejecuta aquí.

- ``00_capps_vars.ps1`` versiona ``ALTA_SIGRID_ENVIAR_DTO = "false"`` y la pasa
  dentro de ``AltaSigridEnvComun`` (sv4 y sv9 con el mismo valor).
- ``set_alta_sigrid.ps1`` la relee en las dos apps y avisa si difieren.
- Ningún ``.ps1`` la pone a ``true``; los ``create_capps`` no la nombran (crean
  sin ella ⇒ apagada).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

INFRA = Path(__file__).resolve().parents[3] / "infra"
VARIABLE = "ALTA_SIGRID_ENVIAR_DTO"


def _ps1(nombre: str) -> str:
    return (INFRA / nombre).read_text(encoding="utf-8-sig")


def _sin_comentarios(texto: str) -> str:
    return "\n".join(linea.split("#")[0] for linea in texto.splitlines())


def _funcion_comun() -> str:
    texto = _ps1("00_capps_vars.ps1")
    comun = texto[texto.index("function Global:AltaSigridEnvComun("):]
    return comun[:comun.index("\n}") + 2]


def test_f110_r20_vars_versiona_la_guarda_apagada():
    texto = _ps1("00_capps_vars.ps1")
    valores = re.findall(rf"^\$Global:{VARIABLE}\s*=\s*(\S+)", texto, re.MULTILINE)
    assert valores == ['"false"']
    # El comentario dice quién la enciende y cuándo.
    bloque = texto[texto.index(f"$Global:{VARIABLE}") - 700: texto.index(f"$Global:{VARIABLE}")]
    assert "humano" in bloque and "F-018" in bloque


def test_f110_r20_va_en_los_pares_comunes():
    comun = _sin_comentarios(_funcion_comun())
    assert f'"{VARIABLE}=$($Global:{VARIABLE})"' in comun


def test_f110_r20_set_alta_sigrid_la_relee_en_las_dos():
    codigo = _sin_comentarios(_ps1("set_alta_sigrid.ps1"))
    (lista,) = re.findall(r"foreach \(\$nombre in @\(([^)]*)\)\)", codigo)
    assert f'"{VARIABLE}"' in lista
    # La relectura compara sv9 con sv4 y lo apunta en los fallos.
    assert '$v9 = Leer $Sv9 $nombre; $v4 = Leer $Sv4 $nombre' in codigo
    assert '$fallos += "$nombre distinto"' in codigo


def test_f110_r20_set_alta_sigrid_la_pasa_a_las_dos_apps():
    codigo = _sin_comentarios(_ps1("set_alta_sigrid.ps1"))
    assert "$comun = @(AltaSigridEnvComun)" in codigo
    assert "@(@($Sv9, ($comun + $soloSv9)), @($Sv4, $comun))" in codigo
    solo_sv9 = codigo[codigo.index("$soloSv9 = @("):]
    solo_sv9 = solo_sv9[:solo_sv9.index(")\n") + 1]
    assert VARIABLE not in solo_sv9


@pytest.mark.parametrize("script", sorted(p.name for p in INFRA.glob("*.ps1")))
def test_f110_r20_ningun_script_la_pone_a_true(script):
    codigo = _sin_comentarios(_ps1(script))
    assert not re.search(rf"{VARIABLE}\s*=\s*[\"']?true", codigo, re.IGNORECASE)
    assert not re.search(rf"\$Global:{VARIABLE}\s*=\s*[\"']?true", codigo, re.IGNORECASE)


@pytest.mark.parametrize("script", ["create_capps_sv9.ps1", "create_capps_sv4.ps1"])
def test_f110_r20_create_capps_no_la_nombran(script):
    if not (INFRA / script).exists():
        pytest.skip(f"{script} no existe")
    assert VARIABLE not in _sin_comentarios(_ps1(script)).replace("AltaSigridEnvComun", "")
