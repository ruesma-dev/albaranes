# tests/test_f069_infra.py
"""F-069 · T13 · la Lista en ``infra/`` y la retirada de ``ALTA_SIGRID_EMPIDE`` (R28).

Tests de texto sobre los ``.ps1`` (como los de F-053): nadie los ejecuta aquí.

- ``00_capps_vars.ps1`` versiona la Lista (vacía de inicio; Logins e ``ide``,
  nunca correos completos, nombres ni DNI) y una ``EscaparJsonNativo`` que
  comparten el mapeo de productos y la Lista; ya no ``ALTA_SIGRID_EMPIDE``.
- ``create_capps_sv9.ps1`` y ``set_alta_sigrid.ps1`` pasan la Lista SOLO a sv9,
  escapada, y la releen; ya no pasan ``ALTA_SIGRID_EMPIDE``; ninguno pone
  ``ALTA_SIGRID_COMMIT`` (``create`` lo deja en ``false``, como F-053).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

INFRA = Path(__file__).resolve().parents[3] / "infra"
VARIABLE = "ALTA_SIGRID_EQUIVALENCIAS_USUARIO"


def _ps1(nombre: str) -> str:
    return (INFRA / nombre).read_text(encoding="utf-8-sig")


def _sin_comentarios(texto: str) -> str:
    return "\n".join(linea.split("#")[0] for linea in texto.splitlines())


def test_f069_r28_vars_versiona_la_lista_vacia():
    texto = _ps1("00_capps_vars.ps1")
    (valor,) = re.findall(rf"^\$Global:{VARIABLE}\s*=\s*(.*?)\s*(?:#.*)?$", texto, re.MULTILINE)
    assert valor in ('""', "''")
    assert "@" not in valor
    # El comentario dice qué va y qué no.
    bloque = texto[texto.index(VARIABLE) - 900: texto.index(VARIABLE)]
    assert "Login" in bloque and "correos" in bloque and "DNI" in bloque


def test_f069_r28_vars_sin_empide():
    assert "ALTA_SIGRID_EMPIDE" not in _ps1("00_capps_vars.ps1")


def test_f069_r28_vars_escapar_json_compartida_con_el_mapeo():
    texto = _ps1("00_capps_vars.ps1")
    assert re.search(r"^function Global:EscaparJsonNativo\(", texto, re.MULTILINE)
    funcion = texto[texto.index("function Global:EscaparJsonNativo("):]
    funcion = funcion[:funcion.index("\n}") + 2]
    # La lógica de hoy del mapeo, sin cambiar su resultado.
    assert "$PSVersionTable.PSVersion.Major -lt 7" in funcion
    assert '$PSNativeCommandArgumentPassing -eq "Legacy"' in funcion
    assert "-replace '\"', '\\\"'" in funcion
    comun = texto[texto.index("function Global:AltaSigridEnvComun("):]
    comun = comun[:comun.index("\n}") + 2]
    assert "EscaparJsonNativo" in comun
    assert "-replace" not in comun


@pytest.mark.parametrize("script", ["create_capps_sv9.ps1", "set_alta_sigrid.ps1"])
def test_f069_r28_scripts_pasan_la_lista_escapada_a_sv9(script):
    codigo = _sin_comentarios(_ps1(script))
    par = f'"{VARIABLE}=$(EscaparJsonNativo $Global:{VARIABLE})"'
    assert par in codigo
    assert "ALTA_SIGRID_EMPIDE" not in _ps1(script)


def test_f069_r28_set_alta_sigrid_la_lista_solo_en_sv9_y_la_relee():
    codigo = _sin_comentarios(_ps1("set_alta_sigrid.ps1"))
    solo_sv9 = codigo[codigo.index("$soloSv9 = @("):]
    solo_sv9 = solo_sv9[:solo_sv9.index(")\n") + 1]
    assert VARIABLE in solo_sv9
    comun = _ps1("00_capps_vars.ps1")
    comun = comun[comun.index("function Global:AltaSigridEnvComun("):]
    assert VARIABLE not in comun[:comun.index("\n}")]
    assert re.search(rf'Leer \$Sv9 "{VARIABLE}"', codigo)
    assert re.search(rf"\$fallos \+= \"{VARIABLE}", codigo)


def test_f069_r28_create_sv9_relee_la_lista():
    codigo = _sin_comentarios(_ps1("create_capps_sv9.ps1"))
    assert re.search(rf"env\[\?name=='{VARIABLE}'\]", codigo)
    assert "throw" in codigo[codigo.index(f"env[?name=='{VARIABLE}']"):]


def test_f069_r28_la_lista_no_va_a_sv4():
    assert VARIABLE not in _ps1("create_capps_sv4.ps1")
    assert VARIABLE not in _ps1("create_capps.ps1")


@pytest.mark.parametrize("script", ["00_capps_vars.ps1", "create_capps_sv9.ps1",
                                    "set_alta_sigrid.ps1"])
def test_f069_r28_ninguno_pone_commit_a_true(script):
    codigo = _sin_comentarios(_ps1(script))
    assert not re.search(r"ALTA_SIGRID_COMMIT=true", codigo, re.IGNORECASE)


def test_f069_r28_create_sv9_sigue_en_simulacion():
    codigo = _sin_comentarios(_ps1("create_capps_sv9.ps1"))
    assert '"ALTA_SIGRID_COMMIT=false"' in codigo


@pytest.mark.parametrize("script, bom", [
    ("00_capps_vars.ps1", False),   # ya era así (sin BOM): no se cambia
    ("create_capps_sv9.ps1", True), ("set_alta_sigrid.ps1", True),
])
def test_f069_r28_ps1_conservan_su_codificacion(script, bom):
    bruto = (INFRA / script).read_bytes()
    assert bruto.startswith(b"\xef\xbb\xbf") is bom
    bruto.decode("utf-8-sig")
