# Medición de F-111 (SOLO LECTURA: BBDD albaranes de Azure y Sigrid vía sigrid-api).
# Las claves salen de Key Vault a variables del proceso y se borran en finally;
# nunca a fichero. Uso, desde la raíz del repo:
#   .\scripts\medicion_F-111\run.ps1 m1_residuos.py   # A y B: contenedores y residuos sin partida
#   .\scripts\medicion_F-111\run.ps1 m2_capitulos.py  # C: capítulo de residuos de cada obra
# Tras desplegar F-111 y revalorar (T13) se espera: defecto6 = 0, «cambian de
# número» = 0 y ninguna línea de residuos con 8 m³ en contenedor=6.
param([Parameter(Mandatory)][string]$Script)
$ErrorActionPreference = 'Stop'
$raiz = Resolve-Path "$PSScriptRoot\..\.."
Push-Location "$raiz\infra"
. .\00_vars.ps1 | Out-Null
Pop-Location
try {
    $env:F111_PG_HOST = "$PG.postgres.database.azure.com"
    $env:F111_PG_USER = $PG_ADMIN
    $env:F111_PG_DB = $PG_DB
    $env:F111_PG_PASS = az keyvault secret show --vault-name $KV -n PG-PASSWORD --query value -o tsv
    $env:F111_SIGRID_URL = $SIGRID_BASE_URL
    $env:F111_SIGRID_KEY = az keyvault secret show --vault-name $KV -n SIGRID-API-FUNCTION-KEY --query value -o tsv
    & "$raiz\.venv\Scripts\python.exe" -I "$PSScriptRoot\$Script"
} finally {
    Remove-Item Env:F111_PG_PASS, Env:F111_SIGRID_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:F111_PG_HOST, Env:F111_PG_USER, Env:F111_PG_DB, Env:F111_SIGRID_URL -ErrorAction SilentlyContinue
}
