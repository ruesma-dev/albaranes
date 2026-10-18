# set_partidas_sv6.ps1
# F-076: da a sv6 (ca-sv6-valorador) lo que necesita para normalizar la
# partida contra las de la obra: el secreto sigrid-key (referencia a Key
# Vault SIGRID-API-FUNCTION-KEY, el mismo que ya usan sv3, sv4 y sv9) y las
# variables de R17. Idempotente: relanzarlo deja lo mismo. NO lo ejecuta
# ningun agente; lo lanza el humano ANTES de desplegar sv6 (design §9: sin
# las variables, sv6 valora como siempre y nada cambia).
#
#   . .\00_vars.ps1
#   . .\00_capps_vars.ps1
#   .\set_partidas_sv6.ps1
#
# Vuelta atras sin redesplegar:
#   az containerapp update -n ca-sv6-valorador -g $RG --set-env-vars PARTIDAS_OBRA_NORMALIZAR_ENABLED=false
#
# Al final RELEE la app y dice OK/KO por variable (8) y por el secreto.

$ErrorActionPreference = "Continue"
$env:AZURE_CORE_ONLY_SHOW_ERRORS = "true"

if (-not $Global:APPS) { . (Join-Path $PSScriptRoot "00_vars.ps1") }
if (-not $Global:MI_ID -or -not $Global:KV_URI) {
    throw "Faltan MI_ID / KV_URI. Haz:  . .\00_capps_vars.ps1"
}
if (-not $Global:SIGRID_BASE_URL -or -not $Global:SIGRID_DB) {
    throw "Faltan SIGRID_BASE_URL / SIGRID_DB (00_vars.ps1 y 00_capps_vars.ps1)."
}
$RG = [string]$Global:RG
$Sv6 = [string]$Global:APPS["sv6"]

# Valores por defecto de F-076 (R17); cambialos aqui si hace falta.
$Esperadas = [ordered]@{
    "SIGRID_API_BASE_URL"              = [string]$Global:SIGRID_BASE_URL
    "SIGRID_API_DATABASE"              = [string]$Global:SIGRID_DB
    "SIGRID_API_TIMEOUT_S"             = "30"
    "PARTIDAS_OBRA_NORMALIZAR_ENABLED" = "true"
    "PARTIDAS_OBRA_TTL_S"              = "21600"
    "PARTIDAS_OBRA_MAX_OBRAS"          = "64"
    "PARTIDAS_OBRA_FALLO_TTL_S"        = "300"
}
$Secreto = "sigrid-key"
$RefKv = "keyvaultref:$($Global:KV_URI)/secrets/SIGRID-API-FUNCTION-KEY,identityref:$($Global:MI_ID)"

$fallos = @()
Write-Host "`n-> $Sv6 : secreto $Secreto (Key Vault SIGRID-API-FUNCTION-KEY)" -ForegroundColor Cyan
az containerapp secret set -n $Sv6 -g $RG --secrets "$Secreto=$RefKv" | Out-Null
if ($LASTEXITCODE -ne 0) { $fallos += "secreto $Secreto"; Write-Host "   FALLO (exit $LASTEXITCODE)" -ForegroundColor Red }

$vars = @($Esperadas.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" })
$vars += "SIGRID_API_FUNCTION_KEY=secretref:$Secreto"
Write-Host "-> $Sv6 : $($vars -join '  ')" -ForegroundColor Cyan
az containerapp revision set-mode -n $Sv6 -g $RG --mode single | Out-Null
az containerapp update -n $Sv6 -g $RG --set-env-vars @vars | Out-Null
if ($LASTEXITCODE -ne 0) { $fallos += "update $Sv6"; Write-Host "   FALLO (exit $LASTEXITCODE)" -ForegroundColor Red }

function Leer($campo, $nombre) {
    az containerapp show -n $Sv6 -g $RG `
        --query "properties.template.containers[0].env[?name=='$nombre'].$campo | [0]" -o tsv 2>$null
}
Write-Host "`nComprobacion (lo que quedo en $Sv6):" -ForegroundColor Yellow
foreach ($par in $Esperadas.GetEnumerator()) {
    $valor = Leer "value" $par.Key
    $marca = if ($valor -eq $par.Value) { "OK" } else { "KO" }
    Write-Host ("  {0,-34} '{1}'  {2}" -f $par.Key, $valor, $marca)
    if ($marca -eq "KO") { $fallos += $par.Key }
}
$ref = Leer "secretRef" "SIGRID_API_FUNCTION_KEY"
$marca = if ($ref -eq $Secreto) { "OK" } else { "KO" }
Write-Host ("  {0,-34} secretref:'{1}'  {2}" -f "SIGRID_API_FUNCTION_KEY", $ref, $marca)
if ($marca -eq "KO") { $fallos += "SIGRID_API_FUNCTION_KEY" }
$hay = az containerapp secret list -n $Sv6 -g $RG --query "[?name=='$Secreto'] | length(@)" -o tsv 2>$null
$marca = if ($hay -eq "1") { "OK" } else { "KO" }
Write-Host ("  {0,-34} {1}" -f "secreto $Secreto", $marca)
if ($marca -eq "KO") { $fallos += "secreto $Secreto" }

if ($fallos.Count) { Write-Host "`nREVISAR: $($fallos -join ', ')" -ForegroundColor Red; exit 1 }
Write-Host "`nAjustes de F-076 aplicados a $Sv6. Ya se puede desplegar sv6." -ForegroundColor Green
