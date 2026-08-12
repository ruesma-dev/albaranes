# create_sv1.ps1
# Crea el Container App de sv1 (intake de correo → blob input/ + q-extraccion).
# Daemon: min/max 1 réplica, SIN ingress, SIN KEDA (sondea el buzón en bucle).
#
# Uso:
#     . .\00_vars.ps1
#     . .\00_capps_vars.ps1
#     .\create_sv1.ps1
#
# Prerequisitos: imagen sv1 en ACR (build_images.ps1) y secretos en Key Vault.

$ErrorActionPreference = "Stop"
if (-not $MI_ID) { throw "Falta `$MI_ID. Haz:  . .\00_capps_vars.ps1" }
if (-not $IMG)   { throw "Falta `$IMG (mapa de imágenes). Haz:  . .\00_vars.ps1" }
az account set --subscription $SUBSCRIPTION

# Buzón a vigilar (confírmalo; el del piloto era dev@ruesma.es).
$MAILBOX = "albaranes@ruesma.es"

function KvRef($n) { "keyvaultref:$KV_URI/secrets/$n,identityref:$MI_ID" }

$secrets = @("pg-password=$(KvRef 'PG-PASSWORD')",
             "graph-key=$(KvRef 'GRAPH-KEY')")

$envv = @(
    "AZURE_CLIENT_ID=$MI_CLIENTID",
    "COLAS_ACCOUNT_URL=$QUEUE_URL",
    "BLOBS_ACCOUNT_URL=$BLOB_URL",
    "PG_HOST=$PG_HOST", "PG_PORT=5432", "PG_DB=$PG_DB",
    "PG_USER=$PG_ADMIN", "PG_PASSWORD=secretref:pg-password",
    "GRAPH_KEY=secretref:graph-key",
    "MAILBOX_ADDRESS=$MAILBOX",
    "SOURCE_FOLDER=inbox", "FOLDER_PROCESADOS=Procesados", "FOLDER_ERRORES=Errores",
    "POLL_INTERVAL_S=60", "MAX_EMAILS=10", "MAX_ATTACHMENT_MB=25", "GRAPH_TIMEOUT_S=60",
    "LOG_DIR=/tmp/logs"
)

Write-Host "=== sv1 (intake correo, daemon) ===" -ForegroundColor Green
$a = @("containerapp","create","-n","ca-sv1-intake","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv1'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,
       "--min-replicas","1","--max-replicas","1",
       "--secrets") + $secrets + @("--env-vars") + $envv + @("--tags") + $TAGS
az @a | Out-Null
if ($LASTEXITCODE -ne 0) { throw "az falló creando ca-sv1-intake (exit $LASTEXITCODE)" }

Write-Host "OK ca-sv1-intake creado (min/max 1, sin ingress)." -ForegroundColor Green
Write-Host "Sondea '$MAILBOX' cada 60s. Logs:" -ForegroundColor Yellow
Write-Host "  az containerapp logs show -n ca-sv1-intake -g $RG --tail 60 --follow" -ForegroundColor Yellow
