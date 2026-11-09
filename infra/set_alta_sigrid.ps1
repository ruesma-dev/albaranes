# set_alta_sigrid.ps1
# F-053: pone EN CALIENTE los ajustes del alta en Sigrid en sv4 Y sv9 con
# LOS MISMOS valores (design §7), leidos de un solo sitio: el bloque F-053 de
# 00_capps_vars.ps1 (ALTA_SIGRID_DESDE_UTC, _ESPERA_INCIERTO_MIN y
# _PRODUCTO_POR_DEFECTO y, desde F-110, _ENVIAR_DTO; en sv9 tambien _USUARIO_RESPALDO y, desde F-069,
# _EQUIVALENCIAS_USUARIO; _EMPIDE ya no se pasa). NO lo ejecuta ningun agente.
#
#   . .\00_vars.ps1
#   . .\00_capps_vars.ps1          # edita antes el bloque F-053
#   .\set_alta_sigrid.ps1
#
# NUNCA toca ALTA_SIGRID_COMMIT (la llave de escritura es solo del humano) y
# al terminar ENSENA su valor en sv9. Orden (design §8): sv9 primero y sv4
# despues, para que nada se publique en q-feedback antes de que sv9 sepa que
# hacer con ello. Cada cambio crea una revision nueva (modo SINGLE).
# Despues RELEE las variables de las dos apps y avisa si no coinciden.

$ErrorActionPreference = "Continue"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

if (-not $Global:APPS) { . (Join-Path $PSScriptRoot "00_vars.ps1") }
if (-not (Get-Command AltaSigridEnvComun -ErrorAction SilentlyContinue)) {
    throw "Falta el bloque F-053 de 00_capps_vars.ps1. Haz:  . .\00_capps_vars.ps1"
}
$RG = [string]$Global:RG
$Sv9 = [string]$Global:APPS["sv9"]
$Sv4 = [string]$Global:APPS["sv4"]

$comun = @(AltaSigridEnvComun)
$soloSv9 = @("ALTA_SIGRID_USUARIO_RESPALDO=$($Global:ALTA_SIGRID_USUARIO_RESPALDO)",
             "ALTA_SIGRID_EQUIVALENCIAS_USUARIO=$(EscaparJsonNativo $Global:ALTA_SIGRID_EQUIVALENCIAS_USUARIO)")
if (($comun + $soloSv9) -match "^ALTA_SIGRID_COMMIT") { throw "set_alta_sigrid.ps1 no toca ALTA_SIGRID_COMMIT." }

$fallos = @()
foreach ($par in @(@($Sv9, ($comun + $soloSv9)), @($Sv4, $comun))) {
    $app = $par[0]; $vars = $par[1]
    Write-Host "`n-> $app : $($vars -join '  ')" -ForegroundColor Cyan
    az containerapp revision set-mode -n $app -g $RG --mode single | Out-Null
    az containerapp update -n $app -g $RG --set-env-vars @vars | Out-Null
    if ($LASTEXITCODE -ne 0) { $fallos += $app; Write-Host "   FALLO (exit $LASTEXITCODE)" -ForegroundColor Red }
}

function Leer($app, $nombre) {
    az containerapp show -n $app -g $RG `
        --query "properties.template.containers[0].env[?name=='$nombre'].value | [0]" -o tsv 2>$null
}
Write-Host "`nComprobacion (lo que quedo en cada app):" -ForegroundColor Yellow
foreach ($nombre in @("ALTA_SIGRID_DESDE_UTC", "ALTA_SIGRID_ESPERA_INCIERTO_MIN", "ALTA_SIGRID_PRODUCTO_POR_DEFECTO", "ALTA_SIGRID_ENVIAR_DTO")) {
    $v9 = Leer $Sv9 $nombre; $v4 = Leer $Sv4 $nombre
    $marca = if ($v9 -eq $v4) { "OK " } else { "DISTINTOS" }
    Write-Host ("  {0,-34} sv9='{1}'  sv4='{2}'  {3}" -f $nombre, $v9, $v4, $marca)
    if ($v9 -ne $v4) { $fallos += "$nombre distinto" }
}
$respaldo = Leer $Sv9 "ALTA_SIGRID_USUARIO_RESPALDO"
Write-Host "  ALTA_SIGRID_USUARIO_RESPALDO (sv9): '$respaldo'"
if (-not $respaldo) { $fallos += "ALTA_SIGRID_USUARIO_RESPALDO vacio en sv9" }
$lista = Leer $Sv9 "ALTA_SIGRID_EQUIVALENCIAS_USUARIO"
$marca = if ([string]$lista -eq [string]$Global:ALTA_SIGRID_EQUIVALENCIAS_USUARIO) { "OK " } else { "DISTINTA" }
Write-Host "  ALTA_SIGRID_EQUIVALENCIAS_USUARIO (sv9): '$lista'  $marca"
if ($marca -ne "OK ") { $fallos += "ALTA_SIGRID_EQUIVALENCIAS_USUARIO en sv9 no es la de 00_capps_vars.ps1" }
$commit = Leer $Sv9 "ALTA_SIGRID_COMMIT"
$color = if ($commit -eq "true") { "Red" } else { "Green" }
Write-Host "  ALTA_SIGRID_COMMIT (sv9, no se toca): '$commit'" -ForegroundColor $color
Write-Host "  Si DESDE no es vacia: sv9 debe decir al arrancar 'modo=simulacion desde=<DESDE>' en su log." -ForegroundColor DarkGray
if ($fallos.Count) { Write-Host "`nREVISAR: $($fallos -join ', ')" -ForegroundColor Red; exit 1 }
Write-Host "`nAjustes del alta aplicados a sv9 y sv4." -ForegroundColor Green
