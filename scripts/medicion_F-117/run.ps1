# Medición de F-117 (SOLO LECTURA: BBDD albaranes de Azure y Sigrid vía sigrid-api).
# Las claves salen de Key Vault a variables del proceso y se borran en finally;
# nunca a fichero. Uso, desde la raíz del repo (o con -Repo apuntando al
# checkout que tiene infra\00_vars.local.ps1 y .venv, p. ej. desde un worktree):
#   .\scripts\medicion_F-117\run.ps1 m1_fuera_de_lista.py
#   .\scripts\medicion_F-117\run.ps1 m1_fuera_de_lista.py -Repo C:\Users\pgris\PycharmProjects\albaranes
# Tras desplegar F-117 y revalorar se espera: las lecturas con E1=1 ya no salen
# con partida_fuera_de_lista sino con partida_equivalente.
param([Parameter(Mandatory)][string]$Script, [string]$Repo = "$PSScriptRoot\..\..")
$ErrorActionPreference = 'Stop'
$raiz = Resolve-Path $Repo
Push-Location "$raiz\infra"
. .\00_vars.ps1 | Out-Null
Pop-Location
try {
    $env:F117_PG_HOST = "$PG.postgres.database.azure.com"
    $env:F117_PG_USER = $PG_ADMIN
    $env:F117_PG_DB = $PG_DB
    $env:F117_PG_PASS = az keyvault secret show --vault-name $KV -n PG-PASSWORD --query value -o tsv
    $env:F117_SIGRID_URL = $SIGRID_BASE_URL
    $env:F117_SIGRID_KEY = az keyvault secret show --vault-name $KV -n SIGRID-API-FUNCTION-KEY --query value -o tsv
    & "$raiz\.venv\Scripts\python.exe" -I "$PSScriptRoot\$Script"
} finally {
    Remove-Item Env:F117_PG_PASS, Env:F117_SIGRID_KEY -ErrorAction SilentlyContinue
    Remove-Item Env:F117_PG_HOST, Env:F117_PG_USER, Env:F117_PG_DB, Env:F117_SIGRID_URL -ErrorAction SilentlyContinue
}
