# build_images.ps1
# Fase 2 (parte 1): construye y empuja las imágenes a ACR con az acr build.
#
# Construye desde un CONTEXTO TEMPORAL: copia el código del proyecto (sin
# .venv/.git/.idea) a una carpeta temporal, le inyecta el paquete 'comun' y el
# Dockerfile/requirements/.dockerignore CORRECTOS de .\manifests\<svc>\, y
# construye desde ahí. Así NO toca tus proyectos ni depende de Dockerfiles
# viejos que tengas dentro.
#
# Uso:
#     . .\00_vars.ps1
#     .\build_images.ps1
#
# Estructura esperada junto a este script:  .\manifests\sv2 ... \sv6
# Requisito: az login con AcrPush en el registro.

param(
    [string] $ProjectsRoot  = "C:\Users\pgris\PycharmProjects",
    [string] $ComunPath     = "",
    [string] $ManifestsRoot = "",
    [string] $Tag           = "latest"   # OBSOLETO: el repo:tag real viene de $IMG (00_vars.ps1)
)
$ErrorActionPreference = "Stop"

if (-not $ACR) { throw "Falta `$ACR. Haz primero:  . .\00_vars.ps1" }
# (jul 2026) Autocuración: si $IMG falta o está incompleto en la sesión
# (visto en Windows PowerShell 5.1), recarga 00_vars.ps1 desde la carpeta
# del propio script. Así el build nunca depende del estado de la consola.
if (-not $IMG -or -not $IMG["sv1"]) {
    Write-Host "[build] `$IMG ausente o incompleto en la sesión; recargando 00_vars.ps1" -ForegroundColor Yellow
    . (Join-Path $PSScriptRoot "00_vars.ps1")
}
if (-not $IMG) { throw "Falta `$IMG (mapa de imágenes). Haz primero:  . .\00_vars.ps1" }

# (jul 2026) FIX de scope de Windows PowerShell 5.1: indexar $IMG[$img]
# con la variable del foreach devolvía vacío aunque $IMG tuviera las 6
# claves (el $IMG global heredado no resolvía la indexación por variable
# dentro del script hijo; sí lo hacía $Global:IMG). Copiamos el mapa a un
# hashtable LOCAL del script, con claves/valores forzados a [string], y
# usamos ESE en el bucle. Robusto en 5.1 y 7.x.
$ImgMap = @{}
foreach ($k in $Global:IMG.Keys) { $ImgMap[[string]$k] = [string]$Global:IMG[$k] }
if ($ImgMap.Count -eq 0) { throw "El mapa `$IMG está vacío tras copiarlo. Recarga:  . .\00_vars.ps1" }
Write-Host "[build] mapa de imágenes: $($ImgMap.Count) servicios ($((($ImgMap.Keys | Sort-Object) -join ', ')))" -ForegroundColor DarkGray
if (-not $ComunPath)     { $ComunPath     = Join-Path $ProjectsRoot "albaranes-comun" }
if (-not $ManifestsRoot) { $ManifestsRoot = Join-Path $PSScriptRoot "manifests" }
if (-not (Test-Path $ComunPath))     { throw "No encuentro 'comun' en $ComunPath (usa -ComunPath)" }
if (-not (Test-Path $ManifestsRoot)) { throw "No encuentro 'manifests' en $ManifestsRoot" }

az account set --subscription $SUBSCRIPTION

# imagen -> carpeta del proyecto
$services = [ordered]@{
    "sv1" = "albaranes-email"
    "sv2" = "albaranes-api"
    "sv3" = "albaranes-persistencia"
    "sv4" = "albaranes-front"
    "sv5" = "albaran-valoracion-api"
    "sv6" = "albaran-valoracion-persist"
}

foreach ($img in $services.Keys) {
    $mf = Join-Path $ManifestsRoot $img
    if (-not (Test-Path $mf)) { Write-Warning "Salto $img : no hay manifests\$img (aún)"; continue }
    $svcDir = Join-Path $ProjectsRoot $services[$img]
    if (-not (Test-Path $svcDir)) { Write-Warning "Salto $img : no existe $svcDir"; continue }

    Write-Host "`n=== $img  ($svcDir) ===" -ForegroundColor Cyan
    $ctx = Join-Path $env:TEMP "acrbuild_$img"
    if (Test-Path $ctx) { Remove-Item -Recurse -Force $ctx }
    New-Item -ItemType Directory -Path $ctx | Out-Null
    try {
        # 1) código del proyecto -> contexto temporal (sin pesados ni comun viejo)
        robocopy $svcDir $ctx /E `
            /XD .venv .git .idea __pycache__ .pytest_cache comun logs `
            /XF *.log *.pyc /NFL /NDL /NJH /NJS /NP | Out-Null
        if ($LASTEXITCODE -ge 8) { throw "robocopy falló copiando $svcDir (code $LASTEXITCODE)" }

        # 2) comun + manifests CORRECTOS (sobrescriben lo que hubiera)
        Copy-Item -Recurse $ComunPath (Join-Path $ctx "comun")
        Copy-Item (Join-Path $mf "Dockerfile")      (Join-Path $ctx "Dockerfile")      -Force
        Copy-Item (Join-Path $mf "requirements.txt") (Join-Path $ctx "requirements.txt") -Force
        Copy-Item (Join-Path $mf ".dockerignore")   (Join-Path $ctx ".dockerignore")   -Force

        # 3) build en ACR con el repo:tag REAL del servicio (mapa $IMG)
        $imgRef = $ImgMap[[string]$img]
        if (-not $imgRef) {
            $claves = (($ImgMap.Keys | Sort-Object) -join ", ")
            throw "No hay entrada para '$img' en el mapa de imágenes. Claves presentes: [$claves]."
        }
        Push-Location $ctx
        az acr build --registry $ACR --image $imgRef .
        $code = $LASTEXITCODE
        Pop-Location
        if ($code -ne 0) { throw "Build de $img FALLO (exit $code). Revisa el log de arriba." }
        Write-Host "OK $img -> $ACR.azurecr.io/$imgRef" -ForegroundColor Green
    }
    finally {
        if (Test-Path $ctx) { Remove-Item -Recurse -Force $ctx }
    }
}

Write-Host "`nImágenes en ACR:" -ForegroundColor Yellow
az acr repository list --name $ACR -o tsv
