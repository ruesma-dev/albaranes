# create_capps.ps1
# Fase 2 (parte 2): crea los Container Apps del núcleo del pipeline
# (sv5 interno HTTP, sv6/sv2/sv3 workers con KEDA). sv4 y sv1 van aparte.
#
# Requisitos previos:
#   - Imágenes en ACR (build_images.ps1 hecho).
#   - Secretos en Key Vault (add_secrets.ps1) + PG-PASSWORD.
#   - Bloque $SP de SharePoint relleno en 00_capps_vars.ps1.
#
# Uso:
#     . .\00_vars.ps1
#     . .\00_capps_vars.ps1
#     .\create_capps.ps1

$ErrorActionPreference = "Stop"
if (-not $MI_ID)  { throw "Falta `$MI_ID. Haz:  . .\00_capps_vars.ps1" }
if (-not $IMG)    { throw "Falta `$IMG (mapa de imágenes). Haz:  . .\00_vars.ps1" }
if ($SP["SHAREPOINT_DRIVE_ID"] -eq "RELLENA") { throw "Rellena el bloque `$SP (SharePoint) en 00_capps_vars.ps1" }
az account set --subscription $SUBSCRIPTION

# --- Helpers de secretos / env ---------------------------------------------
# Secreto de container app -> referencia a Key Vault con la managed identity.
function KvRef($kvSecretName) { "keyvaultref:$KV_URI/secrets/$kvSecretName,identityref:$MI_ID" }
# Convierte el hashtable $SP en pares "CLAVE=valor" para --env-vars.
function SpEnv() { $SP.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" } }

# Bloques de PG reutilizables (la contraseña va por secretref).
$pgEnv = @(
    "PG_HOST=$PG_HOST", "PG_PORT=5432", "PG_DB=$PG_DB",
    "PG_USER=$PG_ADMIN", "PG_PASSWORD=secretref:pg-password"
)

# --- Modelos LLM por defecto -----------------------------------------------
# El .env local NO viaja a Azure (se excluye del build), así que el modelo se
# fija aquí. sv2 usa los tres proveedores; sv5 solo Claude. Cambia el modelo en
# ESTE sitio y vuelve a crear, o en caliente con .\set_models.ps1 (que hace
# el --set-env-vars sobre las apps ya desplegadas).
# OJO 1: el adaptador de Claude (comun/llm/claude_messages_client.py) NO
# envia temperature/top_p/top_k, imprescindible desde Opus 4.7 (esos
# parametros devuelven 400). Si algun dia se anaden, fallaria.
# OJO 2 (24-jul-2026): los modelos nuevos a veces ENVUELVEN el JSON de
# respuesta ({"lineas": {"lineas": [...]}} con opus-4-7; string-JSON con
# sonnet-5). Lo absorbe comun/llm/json_coercion.py -> si cambias de modelo
# y sv5 empieza a devolver 400 "Input should be a valid list", el fix va
# ahi, no en el prompt.
$ANTHROPIC_MODEL = "claude-opus-4-8"   # 16-ago-2026 (decision del humano)
$OPENAI_MODEL    = "gpt-5.4"
$GEMINI_MODEL    = "gemini-3.7-flash"  # 16-ago-2026 (IA1; antes gemini-3.1-pro-preview)

function Run-Az($argList) {
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az falló (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

# ============================================================ sv5 (interno) ==
Write-Host "`n=== sv5 (valuation, interno HTTP :8002) ===" -ForegroundColor Green
$sv5Secrets = @("pg-password=$(KvRef 'PG-PASSWORD')",
                "graph-key=$(KvRef 'GRAPH-KEY')",
                "anthropic-key=$(KvRef 'ANTHROPIC-API-KEY')")
$sv5Env = @() + $pgEnv + @(
    "GRAPH_KEY=secretref:graph-key",
    "ANTHROPIC_API_KEY=secretref:anthropic-key",
    "ANTHROPIC_MODEL=$ANTHROPIC_MODEL",
    "API_HOST=0.0.0.0", "API_PORT=8002", "LOG_DIR=/tmp/logs"
) + (SpEnv)
$a = @("containerapp","create","-n","ca-sv5-valuation","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv5'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,
       "--ingress","internal","--target-port","8002",
       "--min-replicas","1","--max-replicas","3",
       "--secrets") + $sv5Secrets + @("--env-vars") + $sv5Env + @("--tags") + $TAGS
Run-Az $a
$SV5_FQDN = az containerapp show -n ca-sv5-valuation -g $RG --query "properties.configuration.ingress.fqdn" -o tsv
if (-not $SV5_FQDN) { throw "No obtuve el FQDN interno de sv5." }
Write-Host "  sv5 interno: https://$SV5_FQDN" -ForegroundColor Cyan

# =========================================================== sv6 (worker) ===
Write-Host "`n=== sv6 (valorador, worker q-valoracion) ===" -ForegroundColor Green
$sv6Secrets = @("pg-password=$(KvRef 'PG-PASSWORD')")
$sv6Env = @("AZURE_CLIENT_ID=$MI_CLIENTID", "COLAS_ACCOUNT_URL=$QUEUE_URL",
            "VALUATION_API_BASE_URL=https://$SV5_FQDN", "LOG_DIR=/tmp/logs") + $pgEnv
$a = @("containerapp","create","-n","ca-sv6-valorador","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv6'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,"--min-replicas","0","--max-replicas",$WORKER_MAX_REPLICAS,
       "--command","python","--args","main_worker.py",
       "--scale-rule-name","q-valoracion-scaler","--scale-rule-type","azure-queue",
       "--scale-rule-metadata","accountName=$STORAGE","queueName=q-valoracion","queueLength=$KEDA_QUEUE_LENGTH",
       "--scale-rule-identity",$MI_ID,
       "--secrets") + $sv6Secrets + @("--env-vars") + $sv6Env + @("--tags") + $TAGS
Run-Az $a

# =========================================================== sv2 (worker) ===
Write-Host "`n=== sv2 (extracción, worker q-extraccion) ===" -ForegroundColor Green
$sv2Secrets = @("anthropic-key=$(KvRef 'ANTHROPIC-API-KEY')",
                "openai-key=$(KvRef 'OPENAI-API-KEY')",
                "gemini-key=$(KvRef 'GEMINI-API-KEY')")
$sv2Env = @("AZURE_CLIENT_ID=$MI_CLIENTID", "COLAS_ACCOUNT_URL=$QUEUE_URL",
            "BLOBS_ACCOUNT_URL=$BLOB_URL", "LOG_DIR=/tmp/logs",
            "WORKER_CON_FASE2=false", "IA_PRIMERA_FASE=gemini",
            "ANTHROPIC_API_KEY=secretref:anthropic-key",
            "OPENAI_API_KEY=secretref:openai-key",
            "GEMINI_API_KEY=secretref:gemini-key",
            "ANTHROPIC_MODEL=$ANTHROPIC_MODEL",
            "OPENAI_MODEL=$OPENAI_MODEL",
            "GEMINI_MODEL=$GEMINI_MODEL")
$a = @("containerapp","create","-n","ca-sv2-extraccion","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv2'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,"--min-replicas","0","--max-replicas",$WORKER_MAX_REPLICAS,
       "--command","python","--args","main_worker.py",
       "--scale-rule-name","q-extraccion-scaler","--scale-rule-type","azure-queue",
       "--scale-rule-metadata","accountName=$STORAGE","queueName=q-extraccion","queueLength=$KEDA_QUEUE_LENGTH",
       "--scale-rule-identity",$MI_ID,
       "--secrets") + $sv2Secrets + @("--env-vars") + $sv2Env + @("--tags") + $TAGS
Run-Az $a

# =========================================================== sv3 (worker) ===
Write-Host "`n=== sv3 (persistencia, worker q-persistencia) ===" -ForegroundColor Green
$sv3Secrets = @("pg-password=$(KvRef 'PG-PASSWORD')",
                "graph-key=$(KvRef 'GRAPH-KEY')",
                "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')")
$sv3Env = @("AZURE_CLIENT_ID=$MI_CLIENTID", "COLAS_ACCOUNT_URL=$QUEUE_URL",
            "BLOBS_ACCOUNT_URL=$BLOB_URL", "LOG_DIR=/tmp/logs",
            "GRAPH_KEY=secretref:graph-key",
            "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
            "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
            "SIGRID_API_DATABASE=$SIGRID_DB",
            "VALUATION_TRIGGER_ENABLED=false",
            "PG_ADMIN_DB=postgres", "PG_ADMIN_USER=$PG_ADMIN",
            "PG_ADMIN_PASSWORD=secretref:pg-password") + $pgEnv + (SpEnv)
$a = @("containerapp","create","-n","ca-sv3-persistencia","-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv3'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,"--min-replicas","0","--max-replicas",$WORKER_MAX_REPLICAS,
       "--command","python","--args","main_worker.py",
       "--scale-rule-name","q-persistencia-scaler","--scale-rule-type","azure-queue",
       "--scale-rule-metadata","accountName=$STORAGE","queueName=q-persistencia","queueLength=$KEDA_QUEUE_LENGTH",
       "--scale-rule-identity",$MI_ID,
       "--secrets") + $sv3Secrets + @("--env-vars") + $sv3Env + @("--tags") + $TAGS
Run-Az $a

Write-Host "`n=== Container Apps creados ===" -ForegroundColor Green
az containerapp list -g $RG --query "[].name" -o tsv
Write-Host "`nSV5 interno: https://$SV5_FQDN" -ForegroundColor Yellow
Write-Host "Workers a min-replicas=0: escalan con KEDA al haber mensajes en cola." -ForegroundColor Yellow
