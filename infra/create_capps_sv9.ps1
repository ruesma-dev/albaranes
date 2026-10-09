# create_capps_sv9.ps1
# F-053: crea ca-sv9-alta-sigrid, el worker que da de alta en Sigrid los
# albaranes aprobados (consume q-feedback). Mismo patron que sv6 en
# create_capps.ps1. NO lo ejecuta ningun agente: lo lanza el humano.
#
# Requisitos previos:
#   - sv6 y sv3 YA desplegados con la version de F-053 (columna
#     producto_sigrid y tabla albaran_altas_sigrid): design §8.
#   - Imagen en ACR: .\build_images.ps1 -Only sv9 (o .\deploy.ps1 -Only sv9
#     una vez creada la app).
#   - Secretos en Key Vault: PG-PASSWORD, GRAPH-KEY, SIGRID-API-FUNCTION-KEY
#     (la clave de siempre de sigrid-api, decision del 2026-10-01).
#   - Bloque F-053 de 00_capps_vars.ps1 revisado (ALTA_SIGRID_USUARIO: T0c).
#
# Uso:
#     . .\00_vars.ps1
#     . .\00_capps_vars.ps1
#     .\create_capps_sv9.ps1
#
# SEGURIDAD (desde el 2026-10-07 sigrid-api ESCRIBE de verdad):
#   - Se crea SIEMPRE con ALTA_SIGRID_COMMIT=false: modo SIMULACION, sv9
#     nunca manda commit=true. Solo el literal 'true' abre (R19); ponerlo es
#     del humano, a mano y con autorizacion (MANUAL T29):
#       az containerapp update -n ca-sv9-alta-sigrid -g $RG --set-env-vars ALTA_SIGRID_COMMIT=true
#   - Se crea con ALTA_SIGRID_DESDE_UTC vacia (lo que haya en 00_capps_vars):
#     vacia = sv9 confirma los mensajes sin hacer nada.
#   - MAXIMO 1 replica: la grabacion no admite dos workers a la vez. No es la
#     unica defensa: reclamar bloquea el merge y lee el alta en dos
#     sentencias (T24b) y sigrid-api es idempotente por referencia/synckey.
#
# Visibilidad de q-feedback: la calcula el propio worker (main_worker.py,
# peor caso de un mensaje + 300 s, 1740 s con los defectos).

$ErrorActionPreference = "Stop"
if (-not $MI_ID)  { throw "Falta `$MI_ID. Haz:  . .\00_capps_vars.ps1" }
if (-not $IMG)    { throw "Falta `$IMG (mapa de imágenes). Haz:  . .\00_vars.ps1" }
if (-not $IMG["sv9"]) { throw "Falta sv9 en `$IMG (00_vars.ps1)." }
if ($SP["SHAREPOINT_DRIVE_ID"] -eq "RELLENA") { throw "Rellena el bloque `$SP (SharePoint) en 00_capps_vars.ps1" }
if (-not (Get-Command AltaSigridEnvComun -ErrorAction SilentlyContinue)) {
    throw "Falta el bloque F-053 de 00_capps_vars.ps1. Haz:  . .\00_capps_vars.ps1"
}
if (-not $Global:ALTA_SIGRID_USUARIO) {
    Write-Warning "ALTA_SIGRID_USUARIO vacio (MANUAL T0c): sigrid-api rechazara las altas cuando DESDE se ponga."
}
az account set --subscription $SUBSCRIPTION

function KvRef($kvSecretName) { "keyvaultref:$KV_URI/secrets/$kvSecretName,identityref:$MI_ID" }
function SpEnv() { $SP.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" } }
function Run-Az($argList) {
    az @argList | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "az falló (exit $LASTEXITCODE) en: $($argList -join ' ')" }
}

$APP_SV9 = [string]$APPS["sv9"]
Write-Host "`n=== sv9 (alta en Sigrid, worker q-feedback, SIMULACION) ===" -ForegroundColor Green
$sv9Secrets = @("pg-password=$(KvRef 'PG-PASSWORD')",
                "graph-key=$(KvRef 'GRAPH-KEY')",
                "sigrid-key=$(KvRef 'SIGRID-API-FUNCTION-KEY')")
$sv9Env = @("AZURE_CLIENT_ID=$MI_CLIENTID", "COLAS_ACCOUNT_URL=$QUEUE_URL",
            "LOG_DIR=/tmp/logs",
            "PG_HOST=$PG_HOST", "PG_PORT=5432", "PG_DB=$PG_DB",
            "PG_USER=$PG_ADMIN", "PG_PASSWORD=secretref:pg-password",
            "GRAPH_KEY=secretref:graph-key",
            "SIGRID_API_BASE_URL=$SIGRID_BASE_URL",
            "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
            "SIGRID_API_DATABASE=$SIGRID_DB",
            "ALTA_SIGRID_COMMIT=false",
            "ALTA_SIGRID_USUARIO=$($Global:ALTA_SIGRID_USUARIO)",
            "ALTA_SIGRID_EMPIDE=$($Global:ALTA_SIGRID_EMPIDE)") + (AltaSigridEnvComun) + (SpEnv)
if (($sv9Env -match "^ALTA_SIGRID_COMMIT=") -ne "ALTA_SIGRID_COMMIT=false") {
    throw "sv9 solo se crea en simulacion (ALTA_SIGRID_COMMIT=false)."
}
$a = @("containerapp","create","-n",$APP_SV9,"-g",$RG,"--environment",$CAE,
       "--image","$ACR_LOGIN/$($IMG['sv9'])",
       "--registry-server",$ACR_LOGIN,"--registry-identity",$MI_ID,
       "--user-assigned",$MI_ID,"--min-replicas","0","--max-replicas","1",
       "--command","python","--args","main_worker.py",
       "--scale-rule-name","q-feedback-scaler","--scale-rule-type","azure-queue",
       "--scale-rule-metadata","accountName=$STORAGE","queueName=q-feedback","queueLength=1",
       "--scale-rule-identity",$MI_ID,
       "--secrets") + $sv9Secrets + @("--env-vars") + $sv9Env + @("--tags") + $TAGS
Run-Az $a
az containerapp revision set-mode -n $APP_SV9 -g $RG --mode single | Out-Null

Write-Host "`nsv9 creado en SIMULACION (ALTA_SIGRID_COMMIT=false), max 1 replica." -ForegroundColor Yellow
Write-Host "Comprobar:  az containerapp logs show -n $APP_SV9 -g $RG --tail 40" -ForegroundColor Yellow
Write-Host "  (al arrancar dice 'modo=simulacion desde=...'; con DESDE vacia, que confirma sin hacer nada)." -ForegroundColor Yellow
