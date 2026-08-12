# set_models.ps1
# Cambia EN CALIENTE los modelos LLM de las apps que los usan (sv2 los tres
# proveedores, sv5 solo Claude) sin reconstruir imagenes. Uso:
#
#   . .\00_vars.ps1
#   .\set_models.ps1 -Anthropic claude-sonnet-5
#   .\set_models.ps1 -Anthropic claude-opus-4-7 -Openai gpt-5.4
#
# --set-env-vars solo toca las variables nombradas: el resto del entorno y
# los secretref (API keys via Key Vault) quedan intactos. Cada cambio crea
# una revision nueva; se fuerza modo SINGLE para no dejar dos revisiones
# activas compitiendo (paso el 24-jul-2026 con sv2).
#
# NO persiste si recreas las apps desde cero: cambia tambien
# $ANTHROPIC_MODEL / $OPENAI_MODEL / $GEMINI_MODEL en create_capps.ps1.
#
# Al cambiar de modelo, VALORA un albaran y mira el log de sv5: los modelos
# nuevos deforman el JSON de respuesta de formas distintas (opus-4-7 anida
# el documento bajo su propia clave; sonnet-5 lo devuelve como string).
# comun/llm/json_coercion.py lo absorbe y avisa con "[json-coercion] ...".
# Un 400 "Input should be a valid list" = forma nueva sin cubrir.

param(
    [string] $Anthropic = "",
    [string] $Openai    = "",
    [string] $Gemini    = ""
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

if (-not ($Anthropic -or $Openai -or $Gemini)) {
    throw "Indica al menos un modelo: -Anthropic / -Openai / -Gemini"
}

# Que variable vive en que app (sv2: los tres; sv5: solo Anthropic).
$destino = [ordered]@{
    "sv2" = @("ANTHROPIC_MODEL", "OPENAI_MODEL", "GEMINI_MODEL")
    "sv5" = @("ANTHROPIC_MODEL")
}
$valor = @{
    "ANTHROPIC_MODEL" = $Anthropic
    "OPENAI_MODEL"    = $Openai
    "GEMINI_MODEL"    = $Gemini
}

$sfx = "m" + (Get-Date -Format "MMddHHmm")
$i = 0
foreach ($s in @($destino.Keys)) {
    $app = $AppMap[[string]$s]
    if (-not $app) { Write-Host "  (sin app para '$s')" -ForegroundColor DarkGray; continue }
    $sets = @()
    foreach ($v in $destino[$s]) { if ($valor[$v]) { $sets += "$v=$($valor[$v])" } }
    if (-not $sets.Count) { continue }
    $i++
    Write-Host "`n-> $app : $($sets -join '  ')" -ForegroundColor Cyan
    az containerapp revision set-mode -n $app -g $RG --mode single | Out-Null
    az containerapp update -n $app -g $RG --set-env-vars @sets --revision-suffix "$sfx$i" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   FALLO (exit $LASTEXITCODE)" -ForegroundColor Red
    } else {
        Write-Host "   OK" -ForegroundColor Green
    }
}

Write-Host "`nEstado:" -ForegroundColor Yellow
& (Join-Path $PSScriptRoot "check_deploy.ps1") -ConModelos
