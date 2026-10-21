# tests/test_f085_infra.py
"""F-085 · R1–R6 y R22: la infra versionada fija el paso 1 (modelos por fase).

R1–R4 y R22 leen el texto de los ficheros. R5 y R6 EJECUTAN `set_models.ps1` y
`check_deploy.ps1` con un `az` falso (función de PowerShell y, por si acaso, un
`az.cmd` delante en el PATH y un `AZURE_CONFIG_DIR` vacío): ningún test llama a
Azure. Sin `powershell.exe` (Linux), R5 y R6 se saltan.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
INFRA = RAIZ / "infra"
CREATE_CAPPS = INFRA / "create_capps.ps1"

#: Ficheros del repositorio que toca F-085 (R4: ninguno lleva una clave).
FICHEROS_F085 = (
    "infra/create_capps.ps1",
    "infra/set_models.ps1",
    "infra/check_deploy.ps1",
    "infra/README_capps.md",
    "docs/ARCHITECTURE.md",
    "services/albaranes-api/INSTRUCCIONES_WORKER_sv2.md",
    "services/albaranes-persistencia/INSTRUCCIONES_WORKER_sv3.md",
    "services/albaran-valoracion-api/config/settings.py",
    "services/albaran-valoracion-api/interface_adapters/api/app.py",
    "evals/precios_modelos.json",
    "tests/test_f083_precios.py",
    "tests/test_f085_infra.py",
    "specs/F-085-modelos-produccion/requirements.md",
    "specs/F-085-modelos-produccion/design.md",
    "specs/F-085-modelos-produccion/tasks.md",
)

#: Formas de clave de API (R4). Con longitud mínima, para no confundir
#: «task-», «disk-» o un prefijo citado en un texto con una clave de verdad.
FORMAS_DE_CLAVE = {
    "sk-ant-": re.compile(r"(?<![A-Za-z0-9])sk-ant-[A-Za-z0-9_-]{20,}"),
    "sk-": re.compile(r"(?<![A-Za-z0-9])sk-(?!ant-)[A-Za-z0-9_-]{20,}"),
    "AIza": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
}


def _texto(ruta: Path) -> str:
    return ruta.read_text(encoding="utf-8-sig")


def _asignacion(texto: str, variable: str) -> str:
    """El valor de una asignación `$NOMBRE = "valor"` de una línea (la que lee F-083 R3)."""
    encontrado = re.search(rf'^\${variable}\s*=\s*"([^"]+)"', texto, re.MULTILINE)
    assert encontrado, f"${variable} no es una asignación de una línea en create_capps.ps1"
    return encontrado.group(1)


def _bloque(texto: str, servicio: str) -> str:
    """El trozo de `create_capps.ps1` entre la cabecera `# ===... svN (` y la siguiente."""
    partes = re.split(r"^# =+ .*$", texto, flags=re.MULTILINE)
    cabeceras = re.findall(r"^# =+ (.*)$", texto, flags=re.MULTILINE)
    for cabecera, cuerpo in zip(cabeceras, partes[1:]):
        if cabecera.strip().startswith(f"{servicio} ("):
            return cuerpo
    raise AssertionError(f"no hay bloque de {servicio} en create_capps.ps1")


def _lista(bloque: str, nombre: str) -> list[str]:
    """Las cadenas entre comillas dobles de la asignación `$nombre = ...` del bloque."""
    encontrado = re.search(rf"^\${nombre}\s*=(.*?)^\$", bloque, re.MULTILINE | re.DOTALL)
    assert encontrado, f"${nombre} no está en el bloque"
    return re.findall(r'"([^"]*)"', encontrado.group(1))


def _entorno(servicio: str) -> list[str]:
    return _lista(_bloque(_texto(CREATE_CAPPS), servicio), f"{servicio}Env")


def _secretos(servicio: str) -> list[str]:
    return _lista(_bloque(_texto(CREATE_CAPPS), servicio), f"{servicio}Secrets")


def claves_mal_declaradas(texto: str) -> list[str]:
    """R4: las `*_API_KEY=` que no valen `secretref:<secreto>`."""
    malas = []
    for variable, valor in re.findall(r'"([A-Z0-9_]*_API_KEY)=([^"]*)"', texto):
        if not re.fullmatch(r"secretref:[a-z0-9-]+", valor):
            malas.append(variable)
    return malas


def claves_en(texto: str) -> list[str]:
    """R4: qué formas de clave de API aparecen en un texto."""
    return [forma for forma, patron in FORMAS_DE_CLAVE.items() if patron.search(texto)]


# --- R1 -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("variable", "modelo"),
    [
        ("GEMINI_MODEL", "gemini-4-argon"),
        ("OPENAI_MODEL", "gpt-6.1-sol"),
        ("ANTHROPIC_MODEL", "claude-opus-4-8"),
    ],
)
def test_f085_r1_modelos_del_paso_1(variable, modelo):
    assert _asignacion(_texto(CREATE_CAPPS), variable) == modelo


# --- R2 -----------------------------------------------------------------------


def test_f085_r2_sv5_declara_el_secreto_de_openai():
    assert "openai-key=$(KvRef 'OPENAI-API-KEY')" in _secretos("sv5")


@pytest.mark.parametrize(
    "entrada",
    [
        "ENABLE_OPENAI=true",
        "OPENAI_API_KEY=secretref:openai-key",
        "OPENAI_MODEL=$OPENAI_MODEL",
        "IA3_PROVIDER=openai",
        "IA4_PROVIDER=openai",
        # lo que ya tenía sv5 se queda (Claude instanciado y ocioso)
        "ANTHROPIC_API_KEY=secretref:anthropic-key",
        "ANTHROPIC_MODEL=$ANTHROPIC_MODEL",
        "GRAPH_KEY=secretref:graph-key",
        "API_PORT=8002",
    ],
)
def test_f085_r2_entorno_de_sv5(entrada):
    assert entrada in _entorno("sv5")


@pytest.mark.parametrize("servicio", ["sv5", "sv6", "sv2", "sv3"])
def test_f085_r2_cada_secretref_tiene_su_secreto(servicio):
    declarados = {s.split("=", 1)[0] for s in _secretos(servicio)}
    usados = set(re.findall(r"secretref:([a-z0-9-]+)", " ".join(_entorno(servicio))))
    # el bloque PG compartido ($pgEnv) usa pg-password
    if servicio != "sv2":
        usados.add("pg-password")
    assert usados <= declarados, f"{servicio}: secretref sin secreto {usados - declarados}"


# --- R3 -----------------------------------------------------------------------


def test_f085_r3_sv2_fija_las_dos_fases():
    entorno = _entorno("sv2")
    assert "IA_PRIMERA_FASE=gemini" in entorno
    assert "IA_SEGUNDA_FASE=openai" in entorno


def test_f085_r3_nadie_declara_worker_con_fase2():
    texto = _texto(CREATE_CAPPS)
    entradas = re.findall(r'"([A-Z0-9_]+)=', texto)
    assert "WORKER_CON_FASE2" not in entradas


# --- R4 -----------------------------------------------------------------------


def test_f085_r4_las_api_key_de_create_capps_van_por_secretref():
    texto = _texto(CREATE_CAPPS)
    assert re.findall(r'"([A-Z0-9_]*_API_KEY)=', texto), "no hay ninguna *_API_KEY"
    assert claves_mal_declaradas(texto) == [], "infra/create_capps.ps1"


def test_f085_r4_detecta_una_api_key_en_claro():
    clave = "sk" + "-proj-" + "a" * 24
    texto = f'$e = @("OPENAI_API_KEY={clave}", "GEMINI_API_KEY=secretref:gemini-key", "ANTHROPIC_API_KEY=")'
    assert claves_mal_declaradas(texto) == ["OPENAI_API_KEY", "ANTHROPIC_API_KEY"]


@pytest.mark.parametrize("relativa", FICHEROS_F085)
def test_f085_r4_ningun_fichero_de_f085_lleva_una_clave(relativa):
    ruta = RAIZ / relativa
    assert ruta.exists(), relativa
    encontradas = claves_en(_texto(ruta))
    assert encontradas == [], f"{relativa}: algo con forma de clave {encontradas}"


@pytest.mark.parametrize(
    ("texto", "forma"),
    [
        ("OPENAI_API_KEY=" + "sk" + "-proj-" + "x1" * 12, "sk-"),
        ("ANTHROPIC_API_KEY=" + "sk" + "-ant-" + "api03-" + "y" * 20, "sk-ant-"),
        ("GEMINI_API_KEY=" + "AI" + "za" + "S" * 33, "AIza"),
    ],
)
def test_f085_r4_reconoce_cada_forma_de_clave(texto, forma):
    assert claves_en(texto) == [forma]


@pytest.mark.parametrize("texto", ["la tarea task-1234567890123456789012", "prefijo sk- citado", "AIza"])
def test_f085_r4_no_confunde_texto_normal_con_una_clave(texto):
    assert claves_en(texto) == []


# --- R5, R6: los scripts, ejecutados con un `az` falso ----------------------------

POWERSHELL = shutil.which("powershell.exe") or shutil.which("pwsh")
con_powershell = pytest.mark.skipif(POWERSHELL is None, reason="sin PowerShell")

#: Entorno de prueba: mapas de 00_vars.ps1 mínimos y un `az` que solo apunta.
#: `show` devuelve las variables de fase para que -ConModelos tenga qué pintar.
_PRELUDIO = r"""
$ErrorActionPreference = "Stop"
$Global:APPS = [ordered]@{ "sv2" = "ca-sv2-extraccion"; "sv5" = "ca-sv5-valuation" }
$Global:REPO = @{ "sv2" = "r2"; "sv5" = "r5" }
$Global:IMG  = @{ "sv2" = "i2"; "sv5" = "i5" }
$Global:RG   = "rg-prueba"
$Global:LLAMADAS = New-Object System.Collections.ArrayList
function global:az {
    [void]$Global:LLAMADAS.Add(($args -join " "))
    $global:LASTEXITCODE = 0
    if ($args -contains "show") { '[{"n":"IA3_PROVIDER","v":"openai"},{"n":"OPENAI_MODEL","v":"gpt-6.1-sol"}]' }
}
"""


def _ejecutar(tmp_path: Path, guion: str, *argumentos: str) -> tuple[list[str], str]:
    """Ejecuta un script de infra con el `az` falso; devuelve las llamadas a az y la salida."""
    falso = tmp_path / "bin"
    falso.mkdir(exist_ok=True)
    (falso / "az.cmd").write_text("@echo AZ-CMD-REAL-NO %*\r\n@exit /b 0\r\n", encoding="ascii")
    (tmp_path / "azcfg").mkdir(exist_ok=True)
    envoltorio = tmp_path / "envoltorio.ps1"
    envoltorio.write_text(
        "﻿"
        + _PRELUDIO
        + f"& '{INFRA / guion}' {' '.join(argumentos)}\n"
        + '$Global:LLAMADAS | ForEach-Object { "LLAMADA-AZ: $_" }\n',
        encoding="utf-8",
    )
    entorno = dict(os.environ)
    entorno["PATH"] = f"{falso}{os.pathsep}{entorno.get('PATH', '')}"
    entorno["AZURE_CONFIG_DIR"] = str(tmp_path / "azcfg")
    resultado = subprocess.run(
        [POWERSHELL, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
         "-File", str(envoltorio)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=entorno, timeout=120, check=False,
    )
    salida = resultado.stdout + resultado.stderr
    assert "AZ-CMD-REAL-NO" not in salida, "se llamó a az.exe y no a la función falsa"
    assert resultado.returncode == 0, salida
    llamadas = [l.split("LLAMADA-AZ: ", 1)[1] for l in salida.splitlines() if "LLAMADA-AZ: " in l]
    return llamadas, salida


def _updates(llamadas: list[str]) -> dict[str, str]:
    """`containerapp update` por app: {app: '--set-env-vars ...'}."""
    out = {}
    for llamada in llamadas:
        if llamada.startswith("containerapp update"):
            app = re.search(r"-n (\S+)", llamada).group(1)
            out[app] = llamada
    return out


@con_powershell
def test_f085_r5_openai_cambia_sv2_y_sv5(tmp_path):
    llamadas, _ = _ejecutar(tmp_path, "set_models.ps1", "-Openai", "gpt-prueba")
    updates = _updates(llamadas)
    assert set(updates) == {"ca-sv2-extraccion", "ca-sv5-valuation"}
    for llamada in updates.values():
        assert "--set-env-vars OPENAI_MODEL=gpt-prueba" in llamada
        assert "ANTHROPIC_MODEL" not in llamada and "GEMINI_MODEL" not in llamada


@con_powershell
@pytest.mark.parametrize(
    ("solo", "app"), [("sv2", "ca-sv2-extraccion"), ("sv5", "ca-sv5-valuation")]
)
def test_f085_r5_solo_un_servicio(tmp_path, solo, app):
    llamadas, _ = _ejecutar(tmp_path, "set_models.ps1", "-Openai", "gpt-prueba", "-Solo", solo)
    assert list(_updates(llamadas)) == [app]


@con_powershell
def test_f085_r5_gemini_sigue_siendo_solo_de_sv2(tmp_path):
    llamadas, _ = _ejecutar(tmp_path, "set_models.ps1", "-Gemini", "gemini-prueba")
    updates = _updates(llamadas)
    assert list(updates) == ["ca-sv2-extraccion"]
    assert "GEMINI_MODEL=gemini-prueba" in updates["ca-sv2-extraccion"]


@con_powershell
def test_f085_r5_anthropic_sigue_en_los_dos(tmp_path):
    llamadas, _ = _ejecutar(tmp_path, "set_models.ps1", "-Anthropic", "claude-prueba")
    assert set(_updates(llamadas)) == {"ca-sv2-extraccion", "ca-sv5-valuation"}


@con_powershell
def test_f085_r5_solo_rechaza_un_servicio_que_no_existe(tmp_path):
    with pytest.raises(AssertionError):
        _ejecutar(tmp_path, "set_models.ps1", "-Openai", "gpt-prueba", "-Solo", "sv9")


def test_f085_r5_la_ayuda_avisa_de_claude_5_5_en_sv5():
    ayuda = _texto(INFRA / "set_models.ps1").split("param(")[0]
    assert "ANTHROPIC_FORZAR_HERRAMIENTA" in ayuda
    assert "-Solo" in ayuda


VARIABLES_DE_FASE = (
    "ANTHROPIC_MODEL", "OPENAI_MODEL", "GEMINI_MODEL",
    "IA_PRIMERA_FASE", "IA_SEGUNDA_FASE", "IA3_PROVIDER", "IA4_PROVIDER",
    "ENABLE_OPENAI", "ANTHROPIC_FORZAR_HERRAMIENTA",
)


@con_powershell
def test_f085_r6_con_modelos_pide_y_pinta_las_variables_de_fase(tmp_path):
    llamadas, salida = _ejecutar(tmp_path, "check_deploy.ps1", "-ConModelos")
    consultas = [l for l in llamadas if l.startswith("containerapp show")]
    assert len(consultas) == 2
    for consulta in consultas:
        for variable in VARIABLES_DE_FASE:
            assert f"name=='{variable}'" in consulta, variable
    assert re.search(r"ca-sv5-valuation\s+IA3_PROVIDER=openai\s+OPENAI_MODEL=gpt-6.1-sol", salida)


# --- Ampliación del líder (2026-10-21): sv2 con credenciales de sigrid-api ------
# sv2 arrancaba sin SIGRID_API_* («OBRAS_ACTIVAS_ENABLED=true pero faltan
# credenciales SIGRID_API_*», Log Analytics desde el 07-10) e IA1 recibía
# `obras_activas=NO DISPONIBLE`. Mismo patrón que sv3 y sv9: secreto por Key
# Vault y la URL y la base de 00_vars.ps1 / 00_capps_vars.ps1.

SIGRID_ENTORNO = (
    "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
    "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
    "SIGRID_API_DATABASE=$SIGRID_DB",
)


def test_f085_amp_sv2_declara_el_secreto_de_sigrid_api():
    assert "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')" in _secretos("sv2")


@pytest.mark.parametrize("entrada", SIGRID_ENTORNO)
def test_f085_amp_sv2_lleva_las_credenciales_de_sigrid_api(entrada):
    assert entrada in _entorno("sv2")


def test_f085_amp_sv2_copia_el_patron_de_sv3():
    sv3 = [e for e in _entorno("sv3") if e.startswith("SIGRID_API_")]
    sv2 = [e for e in _entorno("sv2") if e.startswith("SIGRID_API_")]
    assert sv2 == sv3 == list(SIGRID_ENTORNO)
    secreto = [s for s in _secretos("sv3") if s.startswith("sigrid-key=")]
    assert [s for s in _secretos("sv2") if s.startswith("sigrid-key=")] == secreto


def test_f085_amp_sin_url_ni_base_en_claro():
    texto = _texto(CREATE_CAPPS)
    assert "azurewebsites.net" not in texto
    assert not re.search(r'"SIGRID_API_(BASE_URL|DATABASE)=[^$]', texto)


# --- R22 ------------------------------------------------------------------------

DOCUMENTOS_R22 = (
    "infra/README_capps.md",
    "services/albaranes-api/INSTRUCCIONES_WORKER_sv2.md",
    "services/albaranes-persistencia/INSTRUCCIONES_WORKER_sv3.md",
)


@pytest.mark.parametrize("relativa", DOCUMENTOS_R22)
def test_f085_r22_nadie_dice_que_worker_con_fase2_apaga_la_fase_2(relativa):
    for linea in _texto(RAIZ / relativa).splitlines():
        if "WORKER_CON_FASE2" in linea:
            assert "no existe" in linea or "no la lee" in linea, f"{relativa}: {linea.strip()}"


@pytest.mark.parametrize("relativa", DOCUMENTOS_R22)
def test_f085_r22_nadie_dice_que_sv5_solo_usa_claude(relativa):
    texto = _texto(RAIZ / relativa)
    assert not re.search(r"sv5[^.\n]{0,40}\(?solo (usa )?claude", texto, re.IGNORECASE), relativa
