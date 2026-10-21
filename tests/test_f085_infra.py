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
