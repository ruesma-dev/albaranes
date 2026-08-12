# fix_revisiones.ps1
# Deja UNA sola revision activa por app: pone modo single y desactiva las
# revisiones activas que no sean la ultima. Uso:
#
#   . .\00_vars.ps1
#   .\fix_revisiones.ps1              # todas las apps
#   .\fix_revisiones.ps1 -Only sv5,sv6
#
# Por que (24-jul-2026): sv5 y sv6 acabaron con DOS revisiones activas y en
# un worker eso significa dos consumidores de la misma cola, con imagenes
# potencialmente distintas.

param([string[]] $Only = @())

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

$svcs = if ($Only.Count) { @($Only | ForEach-Object { [string]$_ }) } else { $Orden }

foreach ($s in $svcs) {
    $app = $AppMap[$s]
    if (-not $app) { continue }
    $revs = az containerapp revision list -n $app -g $RG `
        --query "[?properties.active].{rev:name, creada:properties.createdTime}" `
        -o json 2>$null | ConvertFrom-Json
    $revs = @($revs)
    if ($revs.Count -le 1) {
        Write-Host "$app : 1 revision activa, nada que hacer." -ForegroundColor DarkGray
        continue
    }
    az containerapp revision set-mode -n $app -g $RG --mode single | Out-Null
    $ordenadas = $revs | Sort-Object { [datetime]$_.creada } -Descending
    $ultima = $ordenadas[0].rev
    Write-Host "$app : $($revs.Count) activas; conservo $ultima" -ForegroundColor Cyan
    foreach ($r in $ordenadas[1..($ordenadas.Count - 1)]) {
        az containerapp revision deactivate -n $app -g $RG --revision $r.rev | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   desactivada $($r.rev)" -ForegroundColor Green
        } else {
            Write-Host "   FALLO desactivando $($r.rev)" -ForegroundColor Red
        }
    }
}

Write-Host "`nEstado:" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "check_deploy.ps1")
