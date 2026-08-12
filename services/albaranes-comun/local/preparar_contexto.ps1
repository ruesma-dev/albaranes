# local/preparar_contexto.ps1
<#
Prepara el CONTEXTO DE BUILD de un servicio y (opcionalmente) lanza el
build en Azure Container Registry — sin Docker Desktop en Windows.

Convención de carpetas (la actual de PyCharm):
    C:\Users\pgris\PycharmProjects\
        comun\      ← este paquete (ruesma-albaranes-comun)
        sv1\ sv2\ sv3\ sv4\ sv5\ sv6\

El contexto resultante en %TEMP% contiene:
    comun\      → copia del paquete común
    servicio\   → copia del servicio SIN: .env, .venv, __pycache__,
                  logs, .git, .idea, scripts (diagnóstico), tests
    Dockerfile  → el del servicio

Uso:
    # Solo preparar el contexto (inspección manual):
    .\preparar_contexto.ps1 -Servicio sv2

    # Preparar y construir en ACR (build remoto, ~2-4 min):
    .\preparar_contexto.ps1 -Servicio sv2 -Registro acralbaranesruesma -Tag v1

NOTA .env: queda EXCLUIDO de la imagen a propósito. En la nube la
configuración llega por variables/secretos de Container Apps;
pydantic-settings ignora el env_file si el fichero no existe.
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("sv1", "sv2", "sv3", "sv4", "sv5", "sv6")]
    [string]$Servicio,

    [string]$Registro = "",
    [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

# Raíz = carpeta que contiene comun\ y los svN\ (dos niveles por encima
# de este script: comun\local\preparar_contexto.ps1).
$raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$origenComun = Join-Path $raiz "comun"
$origenServicio = Join-Path $raiz $Servicio

if (-not (Test-Path (Join-Path $origenServicio "Dockerfile"))) {
    throw "No existe $origenServicio\Dockerfile — ¿servicio correcto?"
}

$contexto = Join-Path $env:TEMP "albaranes-build-$Servicio"
if (Test-Path $contexto) { Remove-Item $contexto -Recurse -Force }
New-Item -ItemType Directory -Path $contexto | Out-Null

$excluirDirs = @(".venv", "venv", "__pycache__", ".git", ".idea",
                 "logs", "node_modules", "tests", "scripts", ".pytest_cache")
$excluirFich = @(".env", "*.log", "nohup.out")

# /MIR no: copiamos limpio con /E. robocopy devuelve códigos <8 como éxito.
robocopy $origenComun (Join-Path $contexto "comun") /E /NFL /NDL /NJH /NJS `
    /XD $excluirDirs /XF $excluirFich | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy comun falló ($LASTEXITCODE)" }

robocopy $origenServicio (Join-Path $contexto "servicio") /E /NFL /NDL /NJH /NJS `
    /XD $excluirDirs /XF $excluirFich | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy servicio falló ($LASTEXITCODE)" }

Copy-Item (Join-Path $origenServicio "Dockerfile") (Join-Path $contexto "Dockerfile")

Write-Host "Contexto preparado en: $contexto"

if ($Registro) {
    $imagen = "albaranes/${Servicio}:${Tag}"
    Write-Host "Lanzando build remoto en ACR '$Registro' → $imagen ..."
    az acr build --registry $Registro --image $imagen --file (Join-Path $contexto "Dockerfile") $contexto
    if ($LASTEXITCODE -ne 0) { throw "az acr build falló" }
    Write-Host "Imagen publicada: $Registro.azurecr.io/$imagen"
} else {
    Write-Host "Sin -Registro: solo se ha preparado el contexto (no se construye)."
}
