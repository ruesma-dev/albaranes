# set_models.ps1
# Cambia EN CALIENTE los modelos LLM de las apps que los usan sin reconstruir
# imagenes. Que variable vive en que app (F-085):
#   -Gemini    -> GEMINI_MODEL     en sv2           (IA1)
#   -Openai    -> OPENAI_MODEL     en sv2 Y en sv5  (IA2 en sv2; IA3 e IA4 en sv5)
#   -Anthropic -> ANTHROPIC_MODEL  en sv2 y en sv5  (hoy ocioso en los dos)
# -Solo sv2 / -Solo sv5 limita el cambio a esa app (p.e. cambiar IA2 sin
# tocar IA3/IA4). Uso:
#
#   . .\00_vars.ps1
#   .\set_models.ps1 -Openai gpt-6.1-sol
#   .\set_models.ps1 -Openai gpt-5.4 -Solo sv2
#   .\set_models.ps1 -Gemini gemini-4-argon
#
# OJO Claude 5.5 (claude-opus-5-5, claude-sonnet-5-5) y Fable 5.1 en sv5: su
# API rechaza con 400 la herramienta forzada que pide el cliente de comun.
# sv5 lee ANTHROPIC_FORZAR_HERRAMIENTA desde F-086 (defecto true = forzada):
# un Claude 5.5 en sv5 necesita ANTHROPIC_FORZAR_HERRAMIENTA=false, y este
# script no la toca: fijala en ca-sv5-valuation con --set-env-vars antes de
# poner el modelo, y usa -Solo sv5 (sv2 no la lee y sigue forzando).
# Que proveedor usa cada fase de sv5 lo deciden IA3_PROVIDER/IA4_PROVIDER, no
# este script.
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
    [string] $Gemini    = "",
    [ValidateSet("", "sv2", "sv5")]
    [string] $Solo      = ""
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

# Que variable vive en que app (sv2: los tres; sv5: Anthropic y, desde F-085,
# OpenAI, que es el modelo de IA3 e IA4).
$destino = [ordered]@{
    "sv2" = @("ANTHROPIC_MODEL", "OPENAI_MODEL", "GEMINI_MODEL")
    "sv5" = @("ANTHROPIC_MODEL", "OPENAI_MODEL")
}
$valor = @{
    "ANTHROPIC_MODEL" = $Anthropic
    "OPENAI_MODEL"    = $Openai
    "GEMINI_MODEL"    = $Gemini
}

$sfx = "m" + (Get-Date -Format "MMddHHmm")
$i = 0
foreach ($s in @($destino.Keys)) {
    if ($Solo -and $s -ne $Solo) { continue }
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
