# infra/bootstrap_db.ps1
# Bootstrap idempotente de PostgreSQL para el sistema de albaranes.
# Ejecutar DESPUES de crear el servidor PG flexible y ANTES de crear los Container Apps.
# Requisitos: az CLI logueado + python con "psycopg[binary]" instalable (pip install "psycopg[binary]").
#
# Cubre los huecos detectados en la validacion e2e:
#   1. Crear la BBDD (el flag NO va en 'server create', va en 'db create').
#   2. pgvector en DOS pasos: allowlist azure.extensions=VECTOR + CREATE EXTENSION.
#   3. (opcional, comentado) re-subida de secretos KV via --file para evitar mangling.
#
# Los indices unicos parciales de contratos NO se crean aqui: los crea el DDL de
# arranque de sv3 (necesitan que las tablas existan, cosa que hace la app al bootear).

$ErrorActionPreference = "Stop"

# --- Parametros (ajusta si cambian los nombres) ---
$RG      = "rg-albaranes-dev"
$PG      = "psql-albaranes-rs9k2"
$DB      = "albaranes"
$KV      = "kv-albaranes-rs9k2"
$PG_HOST = "psql-albaranes-rs9k2.postgres.database.azure.com"
$PG_USER = "ruesmaadmin"

Write-Host "=== Bootstrap BBDD albaranes ==="

# --- 1. Firewall: permitir servicios de Azure (Container Apps llegan a PG) ---
#     create actua como upsert; idempotente.
az postgres flexible-server firewall-rule create -g $RG -s $PG -n AllowAllAzure `
    --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 | Out-Null
Write-Host "[1/5] Firewall AllowAllAzure OK"

# --- 2. Crear la BBDD (idempotente: comprobamos antes) ---
$dbExists = az postgres flexible-server db show -g $RG -s $PG -d $DB --query name -o tsv 2>$null
if ([string]::IsNullOrWhiteSpace($dbExists)) {
    az postgres flexible-server db create -g $RG -s $PG -n $DB | Out-Null
    Write-Host "[2/5] BBDD '$DB' creada"
} else {
    Write-Host "[2/5] BBDD '$DB' ya existe"
}

# --- 3. Allowlist de extensiones a nivel servidor (incluir VECTOR). Parametro dinamico. ---
$ext = az postgres flexible-server parameter show -g $RG -s $PG --name azure.extensions --query value -o tsv
if ($ext -notmatch "VECTOR") {
    if ([string]::IsNullOrWhiteSpace($ext)) { $newext = "VECTOR" } else { $newext = "$ext,VECTOR" }
    az postgres flexible-server parameter set -g $RG -s $PG --name azure.extensions --value $newext | Out-Null
    Write-Host "[3/5] azure.extensions -> $newext"
} else {
    Write-Host "[3/5] azure.extensions ya incluye VECTOR"
}

# --- 4. Firewall temporal a la IP actual para poder ejecutar el DDL de bootstrap ---
$myip = (Invoke-RestMethod https://api.ipify.org).Trim()
az postgres flexible-server firewall-rule create -g $RG -s $PG -n BootstrapClient `
    --start-ip-address $myip --end-ip-address $myip | Out-Null
Write-Host "[4/5] Firewall BootstrapClient -> $myip (espero 45s a propagar)"
Start-Sleep -Seconds 45

# --- 5. CREATE EXTENSION vector en la BBDD (no se puede via az; via psycopg) ---
$env:PGPASS_TMP = az keyvault secret show --vault-name $KV -n PG-PASSWORD --query value -o tsv

@"
import os, psycopg
conn = psycopg.connect(
    host='$PG_HOST', port=5432, dbname='$DB', user='$PG_USER',
    password=os.environ['PGPASS_TMP'], sslmode='require', autocommit=True,
)
conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
row = conn.execute("SELECT extversion FROM pg_extension WHERE extname='vector'").fetchone()
print('vector:', row[0] if row else 'NO INSTALADA')
conn.close()
"@ | Set-Content -Encoding UTF8 "$env:TEMP\bootstrap_ext.py"

python "$env:TEMP\bootstrap_ext.py"

Remove-Item Env:\PGPASS_TMP
Remove-Item "$env:TEMP\bootstrap_ext.py"
Write-Host "[5/5] Extension vector OK"

# (Opcional) eliminar la regla temporal de tu IP cuando termines de operar:
# az postgres flexible-server firewall-rule delete -g $RG -s $PG -n BootstrapClient --yes | Out-Null

Write-Host ""
Write-Host "Bootstrap completado."
Write-Host "Las tablas y los indices unicos parciales los crea sv3 al arrancar (imagen con el fix de DDL)."

# ---------------------------------------------------------------------------
# PATRON SECRETOS KV via --file (evita el mangling de JSON inline tipo GRAPH-KEY).
# Descomenta y ajusta la ruta del .env / valores. Escribir SIEMPRE a fichero
# ASCII sin BOM y referenciar con @ruta.
# ---------------------------------------------------------------------------
# $tmp = "$env:TEMP\graphkey.json"
# Get-Content ".\.env" | Select-String '^GRAPH_KEY=' | ForEach-Object {
#     ($_ -replace '^GRAPH_KEY=', '')
# } | Set-Content -Encoding Ascii $tmp
# az keyvault secret set --vault-name $KV -n GRAPH-KEY --file $tmp | Out-Null
# Remove-Item $tmp
