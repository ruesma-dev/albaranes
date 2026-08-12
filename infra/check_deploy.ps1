# check_deploy.ps1
# Radiografia del despliegue: que imagen corre CADA app, desde cuando, con
# cuantas replicas y con que modelos LLM. Uso:
#
#   . .\00_vars.ps1
#   .\check_deploy.ps1                            # estado actual
#   .\check_deploy.ps1 -Expected r20260724-1433   # marca desviaciones
#   .\check_deploy.ps1 -ConModelos                # + modelos LLM
#
# Lee la REVISION ACTIVA, no la plantilla de la app: es la unica forma de
# saber que se esta ejecutando de verdad (una revision conserva el digest
# con el que nacio aunque el tag del ACR se haya reescrito despues).

param(
    [string] $Expected = "",
    [switch] $ConModelos
)

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

$filas = @()
foreach ($s in $Orden) {
    $app = $AppMap[$s]
    $revs = az containerapp revision list -n $app -g $RG `
        --query "[?properties.active].{rev:name, creada:properties.createdTime, image:properties.template.containers[0].image, replicas:properties.replicas}" `
        -o json 2>$null | ConvertFrom-Json

    if (-not $revs) {
        $filas += [pscustomobject]@{
            svc = $s; app = $app; imagen = "-"; rev = "(ninguna)"
            creada = "-"; replicas = "-"; estado = "SIN REVISION ACTIVA"
        }
        continue
    }
    $revs = @($revs)
    foreach ($r in $revs) {
        $tagRev = ($r.image -split ":")[-1]
        $estado = "ok"
        if ($revs.Count -gt 1) { $estado = "MULTIPLES ACTIVAS" }
        elseif ($Expected -and $tagRev -ne $Expected) { $estado = "TAG VIEJO ($tagRev)" }
        $filas += [pscustomobject]@{
            svc      = $s
            app      = $app
            imagen   = ($r.image -split "/")[-1]
            rev      = $r.rev
            creada   = ([datetime]$r.creada).ToLocalTime().ToString("dd/MM HH:mm")
            replicas = $r.replicas
            estado   = $estado
        }
    }
}

$filas | Format-Table svc, app, imagen, rev, creada, replicas, estado -AutoSize

$malos = @($filas | Where-Object { $_.estado -ne "ok" })
if ($malos.Count) {
    Write-Host "AVISOS:" -ForegroundColor Yellow
    foreach ($m in $malos) { Write-Host "  $($m.app): $($m.estado)" -ForegroundColor Yellow }
    Write-Host "  - MULTIPLES ACTIVAS -> .\fix_revisiones.ps1" -ForegroundColor DarkGray
    Write-Host "  - TAG VIEJO         -> .\deploy.ps1 -Only <svc>" -ForegroundColor DarkGray
} else {
    Write-Host "Todo en orden." -ForegroundColor Green
}
Write-Host "Nota: replicas=0 es NORMAL en workers (sv3/sv6 escalan a cero y despiertan con la cola)." -ForegroundColor DarkGray

if ($ConModelos) {
    Write-Host "`nModelos LLM por app:" -ForegroundColor Cyan
    foreach ($s in $Orden) {
        $app = $AppMap[$s]
        $envs = az containerapp show -n $app -g $RG `
            --query "properties.template.containers[0].env[?name=='ANTHROPIC_MODEL' || name=='OPENAI_MODEL' || name=='GEMINI_MODEL'].{n:name,v:value}" `
            -o json 2>$null | ConvertFrom-Json
        if ($envs) {
            $txt = (@($envs) | ForEach-Object { "$($_.n)=$($_.v)" }) -join "  "
            "{0,-22} {1}" -f $app, $txt
        }
    }
}
