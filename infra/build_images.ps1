# build_images.ps1
# Fase 2 (parte 1): construye y empuja las imágenes a ACR con az acr build.
#
# Construye desde un CONTEXTO TEMPORAL: copia el código del servicio (sin
# .venv/.git/.idea) a una carpeta temporal, le inyecta el paquete 'comun' y el
# Dockerfile/requirements/.dockerignore CORRECTOS de .\manifests\<svc>\, y
# construye desde ahí. Así NO toca el árbol de trabajo ni depende de
# Dockerfiles viejos que haya dentro.
#
# DE DÓNDE SALE EL CÓDIGO (14-sep-2026, el fallo que costó dos meses):
# hasta hoy $ProjectsRoot valía "C:\Users\pgris\PycharmProjects" y cada
# servicio se buscaba en una carpeta HERMANA (albaranes-email, albaranes-api,
# ...). Esas carpetas son los repositorios PREVIOS a la migración; cuatro
# tienen como último commit literalmente "ARCHIVADO: migrado al monorepo
# albaranes; no trabajar aqui". Resultado: el build empaquetaba código de
# julio y NADA de lo desarrollado desde entonces llegó a producción, sin un
# solo aviso. Ahora la raíz se DERIVA de la ubicación de este script
# (infra\ vive dentro del monorepo => <repo>\services) y la guarda
# Assert-FuenteDelMonorepo hace fallar el build en seco si alguna carpeta
# fuente cae fuera de ese services\.
#
# Uso:
#     . .\00_vars.ps1
#     .\build_images.ps1                  # los 6 servicios
#     .\build_images.ps1 -Only sv3        # solo sv3
#     .\build_images.ps1 -Only sv2,sv6    # solo esos dos
#
# Estructura esperada junto a este script:  .\manifests\sv1 ... \sv6
# Requisito: az login con AcrPush en el registro.

param(
    # Vacío = <repo>\services, derivado de la ubicación de este script. Se
    # admite explícito para no cerrar la puerta a otro uso, pero sigue sujeto
    # a la guarda de fuente (ver -PermitirFuenteExterna).
    [string]   $ProjectsRoot  = "",
    [string]   $ComunPath     = "",      # vacío = <ProjectsRoot>\albaranes-comun
    [string]   $ManifestsRoot = "",      # vacío = .\manifests
    [string[]] $Only          = @(),     # sv1..sv6; vacío = todos
    [switch]   $PermitirFuenteExterna,   # desactiva la guarda de fuente (excepcional)
    [string]   $Tag           = "latest" # OBSOLETO: el repo:tag real viene de $IMG (00_vars.ps1)
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
# --- Raíz del código fuente -------------------------------------------------
# Este script vive en <repo>\infra, así que el código de los servicios está en
# <repo>\services. Derivarlo del propio script (y no de una ruta absoluta
# escrita a mano) es lo que garantiza que se construye SIEMPRE desde este
# monorepo y no desde las carpetas archivadas de al lado.
$RepoRoot     = Split-Path -Parent $PSScriptRoot
$ServicesRoot = Join-Path $RepoRoot "services"
if (-not (Test-Path $ServicesRoot)) {
    throw "No encuentro '$ServicesRoot'. Este script debe vivir en <repo>\infra de un monorepo con carpeta 'services'."
}
if (-not $ProjectsRoot)  { $ProjectsRoot  = $ServicesRoot }
if (-not $ComunPath)     { $ComunPath     = Join-Path $ProjectsRoot "albaranes-comun" }
if (-not $ManifestsRoot) { $ManifestsRoot = Join-Path $PSScriptRoot "manifests" }

# --- GUARDA DE FUENTE (14-sep-2026) -----------------------------------------
# Criterio objetivo y barato: ninguna carpeta fuente puede caer fuera del
# services\ DEL REPOSITORIO DONDE VIVE ESTE SCRIPT. Es exactamente lo que nos
# habría avisado el día que el build empaquetó en silencio los repositorios
# archivados en vez del monorepo.
function Get-RutaCompleta {
    param([string] $Ruta)
    if (Test-Path -LiteralPath $Ruta) { return (Resolve-Path -LiteralPath $Ruta).ProviderPath }
    return [System.IO.Path]::GetFullPath($Ruta)
}
function Test-RutaBajoRaiz {
    param([string] $Ruta, [string] $Raiz)
    $sep = [string][System.IO.Path]::DirectorySeparatorChar
    $r = (Get-RutaCompleta $Ruta).TrimEnd('\', '/')
    $b = (Get-RutaCompleta $Raiz).TrimEnd('\', '/')
    if ($r -eq $b) { return $true }
    return $r.StartsWith(($b + $sep), [System.StringComparison]::OrdinalIgnoreCase)
}
function Assert-FuenteDelMonorepo {
    param([string] $Que, [string] $Ruta)
    if (Test-RutaBajoRaiz -Ruta $Ruta -Raiz $ServicesRoot) { return }
    if ($PermitirFuenteExterna) {
        Write-Warning "[build] fuente EXTERNA para ${Que}: $Ruta (fuera de $ServicesRoot). Sigo por -PermitirFuenteExterna."
        return
    }
    Write-Host ""
    Write-Host "FUENTE EQUIVOCADA para $Que" -ForegroundColor Red
    Write-Host "  ruta            : $Ruta"          -ForegroundColor Red
    Write-Host "  debe estar bajo : $ServicesRoot"  -ForegroundColor Red
    Write-Host "El codigo bueno vive en ESTE monorepo. Las carpetas hermanas bajo"        -ForegroundColor Yellow
    Write-Host "PycharmProjects\ son repositorios ARCHIVADOS: construir desde ahi sube"   -ForegroundColor Yellow
    Write-Host "imagenes con codigo anterior a la migracion (paso el 14-sep-2026 y no"    -ForegroundColor Yellow
    Write-Host "aviso nadie). Si de verdad quieres construir desde fuera, repite con"     -ForegroundColor Yellow
    Write-Host "-PermitirFuenteExterna." -ForegroundColor Yellow
    throw "Fuente fuera del monorepo para ${Que}: $Ruta"
}

if (-not (Test-Path $ComunPath))     { throw "No encuentro 'comun' en $ComunPath (usa -ComunPath)" }
if (-not (Test-Path $ManifestsRoot)) { throw "No encuentro 'manifests' en $ManifestsRoot" }
Assert-FuenteDelMonorepo -Que "comun" -Ruta $ComunPath

# --- Suscripción ------------------------------------------------------------
# 00_vars.ps1 trae el valor REDACTADO y carga encima 00_vars.local.ps1 (no
# versionado) con el real. Si aun así sigue redactado, se para aquí: antes
# 'az account set' fallaba con un "The subscription of 'redactado-ver-copia-
# local' doesn't exist in cloud 'AzureCloud'" y el build continuaba contra la
# suscripción activa POR CASUALIDAD.
if (-not $SUBSCRIPTION -or $SUBSCRIPTION -like "REDACTADO*") {
    throw "La suscripcion no esta resuelta (vale '$SUBSCRIPTION'). Falta infra\00_vars.local.ps1 con el valor real; sin el no se sabe contra que suscripcion se construye."
}
az account set --subscription $SUBSCRIPTION

# imagen -> carpeta del servicio DENTRO de <repo>\services. El mapa de nombres
# es el de siempre; lo que cambió el 14-sep-2026 es la RAÍZ, no los nombres.
$services = [ordered]@{
    "sv1" = "albaranes-email"
    "sv2" = "albaranes-api"
    "sv3" = "albaranes-persistencia"
    "sv4" = "albaranes-front"
    "sv5" = "albaran-valoracion-api"
    "sv6" = "albaran-valoracion-persist"
}

# --- Filtro -Only -----------------------------------------------------------
# Mismo formato que deploy.ps1 (lista de sv1..sv6). Antes no existía: deploy
# pasaba su -Only y aquí se construían los seis igualmente.
$todos = @($services.Keys | ForEach-Object { [string]$_ })
if ($Only.Count) {
    $pedidos = @($Only | ForEach-Object { [string]$_ })
    foreach ($s in $pedidos) {
        if ($todos -notcontains $s) { throw "Servicio '$s' desconocido. Validos: $($todos -join ', ')" }
    }
    # Se respeta el orden del mapa, no el que llegue en -Only.
    $aConstruir = @($todos | Where-Object { $pedidos -contains $_ })
} else {
    $aConstruir = $todos
}

Write-Host "[build] raiz del codigo   : $ProjectsRoot" -ForegroundColor Cyan
Write-Host "[build] paquete comun     : $ComunPath"    -ForegroundColor Cyan
Write-Host "[build] servicios a construir: $($aConstruir -join ', ')" -ForegroundColor Cyan
$omitidos = @($todos | Where-Object { $aConstruir -notcontains $_ })
if ($omitidos.Count) {
    Write-Host "[build] omitidos por -Only  : $($omitidos -join ', ')" -ForegroundColor DarkGray
}

foreach ($img in $aConstruir) {
    $mf = Join-Path $ManifestsRoot $img
    if (-not (Test-Path $mf)) { throw "No hay manifests\$img : no se puede construir $img." }
    $svcDir = Join-Path $ProjectsRoot $services[$img]
    if (-not (Test-Path $svcDir)) { throw "No existe la carpeta fuente de $img : $svcDir" }
    Assert-FuenteDelMonorepo -Que $img -Ruta $svcDir

    Write-Host "`n=== $img  ($svcDir) ===" -ForegroundColor Cyan
    # (15-sep-2026) Contexto con nombre UNICO por ejecucion. Antes era fijo
    # ("acrbuild_$img") y bastaba con que Windows tuviera la carpeta abierta
    # -antivirus, Explorador, un indexador- para que el borrado fallara y,
    # con $ErrorActionPreference='Stop', tumbara el despliegue ENTERO.
    $ctx = Join-Path $env:TEMP ("acrbuild_{0}_{1}" -f $img, (Get-Date -Format "yyyyMMddHHmmss"))
    # Limpieza de contextos viejos: best-effort, nunca fatal.
    Get-ChildItem -Path $env:TEMP -Directory -Filter "acrbuild_$img*" -ErrorAction SilentlyContinue |
        ForEach-Object {
            try { Remove-Item -Recurse -Force $_.FullName -ErrorAction Stop }
            catch { Write-Warning "[build] no se pudo borrar el contexto viejo $($_.TargetObject): se deja y se sigue." }
        }
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
        # La imagen YA esta construida y subida: no poder borrar un temporal
        # es un aviso, no un fallo del despliegue.
        try {
            if (Test-Path $ctx) { Remove-Item -Recurse -Force $ctx -ErrorAction Stop }
        }
        catch {
            Write-Warning "[build] no se pudo borrar el contexto temporal $ctx : $($_.Exception.Message)"
            Write-Warning "[build] la imagen de $img ya esta en el ACR; se continua."
        }
    }
}

Write-Host "`nImágenes en ACR:" -ForegroundColor Yellow
az acr repository list --name $ACR -o tsv
