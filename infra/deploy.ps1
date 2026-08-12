# deploy.ps1
# Redespliegue COMPLETO (o parcial) del pipeline de albaranes.
#
#   . .\00_vars.ps1
#   .\deploy.ps1                              # build de los 6 + update, tag por fecha
#   .\deploy.ps1 -Only sv4,sv6                # solo esos dos
#   .\deploy.ps1 -Tag r20260724-1433 -SkipBuild   # apps -> imagen YA construida
#
# Por que existe (24-jul-2026): el despliegue "a mano" fallaba de tres
# formas distintas y las tres costaron una manana:
#   1. Nombres de app inventados (ca-sv2 en vez de ca-sv2-extraccion) ->
#      "does not exist". Ahora salen del mapa $APPS de 00_vars.ps1.
#   2. Bucles foreach que morian en la primera iteracion: la extension
#      containerapp escribe avisos en stderr y con
#      $ErrorActionPreference=Stop heredado abortaban en silencio (solo se
#      actualizaba el primer servicio). Aqui se fija Continue y se
#      comprueba $LASTEXITCODE servicio a servicio.
#   3. Tags reescritos (v2, v3...): la revision viva conserva el DIGEST con
#      el que nacio, asi que Azure seguia ejecutando la imagen vieja aunque
#      el ACR tuviera codigo nuevo. Ahora el tag es por fecha y ademas se
#      fuerza revision nueva con --revision-suffix.
#
# Deja las apps en modo de revision SINGLE: una sola revision activa. Con
# 'multiple' dos revisiones compiten por la misma cola y el trafico se
# reparte entre imagen nueva y vieja.

param(
    [string]   $Tag       = "",
    [string[]] $Only      = @(),
    [switch]   $SkipBuild,
    [string]   $Suffix    = ""
)

# NO Stop: az containerapp escupe avisos por stderr y abortaria el script.
$ErrorActionPreference = "Continue"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

# --------------------------------------------------------------------- #
# FIX de scope de Windows PowerShell 5.1 (24-jul-2026) — el MISMO bug que
# ya documenta build_images.ps1: dentro de un script hijo, indexar un mapa
# GLOBAL con la variable de un foreach devuelve $null ("No se puede
# indizar en una matriz nula"). Solucion: recargar 00_vars.ps1 si falta
# algo y COPIAR los mapas a hashtables LOCALES con claves/valores forzados
# a [string]. Robusto en 5.1 y 7.x.
# --------------------------------------------------------------------- #
if (-not $Global:REPO -or -not $Global:APPS -or -not $Global:IMG) {
    Write-Host "[infra] mapas ausentes en la sesion; recargando 00_vars.ps1" -ForegroundColor Yellow
    . (Join-Path $PSScriptRoot "00_vars.ps1")
}
if (-not $Global:APPS) { throw "Falta `$APPS. Haz:  . .\00_vars.ps1" }

$RepoMap = @{}
foreach ($k in $Global:REPO.Keys) { $RepoMap[[string]$k] = [string]$Global:REPO[$k] }
$AppMap = @{}
foreach ($k in $Global:APPS.Keys) { $AppMap[[string]$k] = [string]$Global:APPS[$k] }
$Orden = @($Global:APPS.Keys | ForEach-Object { [string]$_ })

if (-not $Global:RG) { throw "Falta `$RG. Haz primero:  . .\00_vars.ps1" }
$RG = [string]$Global:RG
$ACR = [string]$Global:ACR
$AcrLogin = if ($Global:ACR_LOGIN) { [string]$Global:ACR_LOGIN } else { "$ACR.azurecr.io" }

# --- Tag del despliegue -----------------------------------------------------
if (-not $Tag) { $Tag = "r" + (Get-Date -Format "yyyyMMdd-HHmm") }
Set-DeployTag $Tag | Out-Null
# $IMG lo acaba de reescribir Set-DeployTag: se copia DESPUES.
$ImgMap = @{}
foreach ($k in $Global:IMG.Keys) { $ImgMap[[string]$k] = [string]$Global:IMG[$k] }
if (-not $Suffix) { $Suffix = $Tag.ToLower() }

# --- Servicios a desplegar --------------------------------------------------
$svcs = if ($Only.Count) { @($Only | ForEach-Object { [string]$_ }) } else { $Orden }
foreach ($s in $svcs) {
    if (-not $AppMap.ContainsKey($s)) {
        throw "Servicio '$s' desconocido. Validos: $($Orden -join ', ')"
    }
}

Write-Host "`n=========================================================" -ForegroundColor Cyan
Write-Host " DESPLIEGUE  tag=$Tag  RG=$RG" -ForegroundColor Cyan
Write-Host " servicios: $($svcs -join ', ')" -ForegroundColor Cyan
Write-Host "=========================================================" -ForegroundColor Cyan

# --- 1) Build en ACR --------------------------------------------------------
if ($SkipBuild) {
    Write-Host "`n[1/3] BUILD omitido (-SkipBuild)." -ForegroundColor DarkGray
} else {
    Write-Host "`n[1/3] Construyendo imagenes (inyecta 'comun' fresco en cada una)..." -ForegroundColor Yellow
    & (Join-Path $PSScriptRoot "build_images.ps1")
    if ($LASTEXITCODE -ne 0) { throw "build_images.ps1 fallo (exit $LASTEXITCODE). Nada desplegado." }
}

# --- 2) Verificar que el tag existe en ACR ----------------------------------
Write-Host "`n[2/3] Verificando tags en ACR..." -ForegroundColor Yellow
$faltan = @()
foreach ($s in $svcs) {
    $repo = $RepoMap[$s]
    if (-not $repo) { throw "Sin repositorio para '$s' en `$REPO (00_vars.ps1)." }
    $tags = az acr repository show-tags -n $ACR --repository $repo -o tsv 2>$null
    if ($tags -notcontains $Tag) { $faltan += "${repo}:${Tag}" }
}
if ($faltan.Count) {
    throw "No estan en ACR: $($faltan -join ', '). Revisa el log del build."
}
Write-Host "      OK: $Tag presente en los $($svcs.Count) repositorios." -ForegroundColor Green

# --- 3) Update de las Container Apps ---------------------------------------
Write-Host "`n[3/3] Actualizando Container Apps..." -ForegroundColor Yellow
$fallos = @()
foreach ($s in $svcs) {
    $app = $AppMap[$s]
    $img = "$AcrLogin/$($ImgMap[$s])"
    Write-Host "`n  -> $app  <-  $img" -ForegroundColor Cyan

    az containerapp revision set-mode -n $app -g $RG --mode single | Out-Null
    az containerapp update -n $app -g $RG --image $img --revision-suffix $Suffix | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "     FALLO (exit $LASTEXITCODE)" -ForegroundColor Red
        $fallos += $app
    } else {
        Write-Host "     OK  revision $app--$Suffix" -ForegroundColor Green
    }
}

# --- Verificacion final -----------------------------------------------------
Write-Host "`nEstado final:" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "check_deploy.ps1") -Expected $Tag

if ($fallos.Count) {
    Write-Host "`nFALLARON: $($fallos -join ', ')" -ForegroundColor Red
    Write-Host "Log de un servicio:  az containerapp logs show -n <app> -g $RG --tail 60 --follow" -ForegroundColor Yellow
    exit 1
}
Write-Host "`nDespliegue OK con tag $Tag." -ForegroundColor Green
Write-Host "Recuerda: Ctrl+F5 en el portal (sv4 sirve CSS/JS con cache-buster por reinicio)." -ForegroundColor DarkGray
