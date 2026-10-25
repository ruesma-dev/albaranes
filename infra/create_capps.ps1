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
# fija aquí. Cambia el modelo en ESTE sitio y vuelve a crear, o en caliente con
# .\set_models.ps1 (que hace el --set-env-vars sobre las apps ya desplegadas).
#
# Quién usa qué (F-085, paso 1 aplicado a mano por el humano el 2026-10-20;
# tabla completa en azure-apps/albaranes.md, «Modelos de IA por fase»):
#   IA1  sv2  IA_PRIMERA_FASE=gemini  -> $GEMINI_MODEL
#   IA2  sv2  IA_SEGUNDA_FASE=openai  -> $OPENAI_MODEL  (corre SIEMPRE: el
#             worker hace fase 1 + fase 2 sin condición; la antigua
#             WORKER_CON_FASE2 no la lee ningún código y ya no se declara)
#   IA3  sv5  IA3_PROVIDER=openai     -> $OPENAI_MODEL
#   IA4  sv5  IA4_PROVIDER=openai     -> $OPENAI_MODEL
# sv5 ya NO es «solo Claude»: habilita OpenAI con la misma clave de Key Vault
# que sv2 (OPENAI-API-KEY), así que la cuota de OpenAI es compartida. Claude
# sigue instanciado y ocioso en sv2 y sv5 ($ANTHROPIC_MODEL): es la vuelta
# atrás de IA3/IA4 (IA3_PROVIDER=claude / IA4_PROVIDER=claude). sv5 no arranca
# si IA3_PROVIDER o IA4_PROVIDER nombran un proveedor apagado (F-085 R9).
# Un Claude 5.5 en sv5 (Opus 5.5 en IA3) necesita ANTHROPIC_FORZAR_HERRAMIENTA=false:
# su API rechaza la herramienta forzada que pide el cliente de comun. sv5 la lee
# desde F-086 con defecto true (la forzada de siempre) y aquí no se fija: el
# cambio de IA3 a Opus 5.5 es la parte C de F-086, solo si su medición pasa.
# OJO 1: el adaptador de Claude (comun/llm/claude_messages_client.py) NO
# envia temperature/top_p/top_k, imprescindible desde Opus 4.7 (esos
# parametros devuelven 400). Si algun dia se anaden, fallaria.
# OJO 2 (24-jul-2026): los modelos nuevos a veces ENVUELVEN el JSON de
# respuesta ({"lineas": {"lineas": [...]}} con opus-4-7; string-JSON con
# sonnet-5). Lo absorbe comun/llm/json_coercion.py -> si cambias de modelo
# y sv5 empieza a devolver 400 "Input should be a valid list", el fix va
# ahi, no en el prompt.
$ANTHROPIC_MODEL = "claude-opus-4-8"   # 16-ago-2026; ocioso desde F-085 (vuelta atrás de IA3/IA4)
$OPENAI_MODEL    = "gpt-6.1-sol"       # 20-oct-2026, F-085: IA2 (sv2), IA3 e IA4 (sv5); antes gpt-5.4
$GEMINI_MODEL    = "gemini-4-argon"    # 20-oct-2026, F-085: IA1; antes gemini-3.7-flash

function Run-Az($argList) {
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az falló (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

# ============================================================ sv5 (interno) ==
Write-Host "`n=== sv5 (valuation, interno HTTP :8002) ===" -ForegroundColor Green
$sv5Secrets = @("pg-password=$(KvRef 'PG-PASSWORD')",
                "graph-key=$(KvRef 'GRAPH-KEY')",
                "anthropic-key=$(KvRef 'ANTHROPIC-API-KEY')",
                "openai-key=$(KvRef 'OPENAI-API-KEY')")
# F-085: IA3 e IA4 con OpenAI. IA3_PROVIDER va con ENABLE_OPENAI en la misma
# creación: con IA3_PROVIDER vacía y dos proveedores, IA3 llamaría a los dos.
$sv5Env = @() + $pgEnv + @(
    "GRAPH_KEY=secretref:graph-key",
    "ANTHROPIC_API_KEY=secretref:anthropic-key",
    "ANTHROPIC_MODEL=$ANTHROPIC_MODEL",
    "ENABLE_OPENAI=true",
    "OPENAI_API_KEY=secretref:openai-key",
    "OPENAI_MODEL=$OPENAI_MODEL",
    "IA3_PROVIDER=openai", "IA4_PROVIDER=openai",
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
# F-076: sv6 lee de sigrid-api (solo sql/read) la lista de partidas de la obra
# para normalizar la partida al valorar. Mismo secreto que sv3/sv4/sv9; sin el,
# sv6 valora como siempre. En una app ya creada: set_partidas_sv6.ps1.
$sv6Secrets = @("pg-password=$(KvRef 'PG-PASSWORD')",
                "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')")
$sv6Env = @("AZURE_CLIENT_ID=$MI_CLIENTID", "COLAS_ACCOUNT_URL=$QUEUE_URL",
            "VALUATION_API_BASE_URL=https://$SV5_FQDN", "LOG_DIR=/tmp/logs",
            "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
            "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
            "SIGRID_API_DATABASE=$SIGRID_DB",
            "SIGRID_API_TIMEOUT_S=30",
            "PARTIDAS_OBRA_NORMALIZAR_ENABLED=true",
            "PARTIDAS_OBRA_TTL_S=21600",
            "PARTIDAS_OBRA_MAX_OBRAS=64",
            "PARTIDAS_OBRA_FALLO_TTL_S=300") + $pgEnv
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
                "gemini-key=$(KvRef 'GEMINI-API-KEY')",
                "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')")
# F-085 (ampliación del líder, 2026-10-21): sv2 lee de sigrid-api (solo
# lectura) la lista de obras activas para el prompt de IA1. Sin SIGRID_API_*
# arrancaba con «OBRAS_ACTIVAS_ENABLED=true pero faltan credenciales» e IA1
# recibía obras_activas=NO DISPONIBLE. Mismo patrón que sv3 y sv9.
$sv2Env = @("AZURE_CLIENT_ID=$MI_CLIENTID", "COLAS_ACCOUNT_URL=$QUEUE_URL",
            "BLOBS_ACCOUNT_URL=$BLOB_URL", "LOG_DIR=/tmp/logs",
            "IA_PRIMERA_FASE=gemini", "IA_SEGUNDA_FASE=openai",
            "ANTHROPIC_API_KEY=secretref:anthropic-key",
            "OPENAI_API_KEY=secretref:openai-key",
            "GEMINI_API_KEY=secretref:gemini-key",
            "ANTHROPIC_MODEL=$ANTHROPIC_MODEL",
            "OPENAI_MODEL=$OPENAI_MODEL",
            "GEMINI_MODEL=$GEMINI_MODEL",
            "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
            "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
            "SIGRID_API_DATABASE=$SIGRID_DB")
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
