# create_capps_sv4.ps1 — despliegue de ca-sv4-front (portal de revision)
# Patron de build identico a sv3 (code en raiz + comun/ + comun[azure]).
# Diferencias sv4: ingress EXTERNO :8004, API_HOST=0.0.0.0, publica colas,
# lee Postgres/Graph, y Easy Auth (Entra ID).
#
# Ejecutar por bloques desde PowerShell con az ya logueado (az login).
# Requiere: az 2.85+, el MI id-albaranes-dev con AcrPull en el ACR y
# acceso de lectura de secretos al Key Vault (ya lo tiene sv3).

# =====================================================================
# 0) VARIABLES  — REVISA las dos rutas y SIGRID_API_DATABASE
# =====================================================================
$SUB        = "REDACTADO-VER-COPIA-LOCAL"
$TENANT     = "REDACTADO-VER-COPIA-LOCAL"
$RG         = "rg-albaranes-dev"
$LOC        = "spaincentral"
$APP        = "ca-sv4-front"
$ENVCA      = "cae-albaranes-dev"
$ACR        = "acralbaranesdev"
$ACRLOGIN   = "$ACR.azurecr.io"
$SV4_TAG    = "v2"                        # tag REAL desplegado (subir al reconstruir: colas/EasyAuth/refetch)
$IMAGE      = "$ACRLOGIN/sv4-front:$SV4_TAG"
$MI_NAME    = "id-albaranes-dev"
$KV         = "kv-albaranes-rs9k2"
$KVURI      = "https://$KV.vault.azure.net/secrets"
$STORAGEQ   = "https://stalbaranesrs9k2.queue.core.windows.net"
$MI_CLIENTID= "REDACTADO-VER-COPIA-LOCAL"
$PGHOST     = "psql-albaranes-rs9k2.postgres.database.azure.com"
$SP_DRIVE   = "b!1MGRgCm-hU2ZQzBy5nJKU0IHpwhGorZHmWz-yozHEtpEwh0tlcBwQqMKgTOZjcR_"
$SIGRID_URL = "https://func-sigridapi-dev-huyke.azurewebsites.net"
$SIGRID_DB  = ""   # opcional: BBDD Sigrid (misma que sv3). Vacio = dropdowns OFF, entrada manual

# Rutas locales (PyCharm)
$SV4_DIR    = "C:\Users\pgris\PycharmProjects\albaranes-front"
$COMUN_DIR  = "C:\Users\pgris\PycharmProjects\albaranes-comun"
$MANIFEST   = "$SV4_DIR\manifests\sv4"   # donde dejas Dockerfile/requirements/.dockerignore

az account set --subscription $SUB | Out-Null
$MI_ID = az identity show -g $RG -n $MI_NAME --query id -o tsv
"MI resource id: $MI_ID"

# =====================================================================
# 1) BUILD CONTEXT limpio + ACR build
#    (code de sv4 en raiz + carpeta comun/ con el proyecto albaranes-comun)
# =====================================================================
$CTX = Join-Path $env:TEMP "sv4-build"
if (Test-Path $CTX) { Remove-Item $CTX -Recurse -Force }
New-Item -ItemType Directory -Path $CTX | Out-Null

# 1a) Codigo del servicio en la raiz del contexto (sin basura)
robocopy $SV4_DIR $CTX /E /XD .venv .idea .git __pycache__ logs manifests /XF *.log .env *.zip | Out-Null
# 1b) Proyecto comun -> $CTX\comun  (debe contener pyproject.toml + ruesma_comun/)
robocopy $COMUN_DIR "$CTX\comun" /E /XD .venv .idea .git __pycache__ /XF *.log | Out-Null
$global:LASTEXITCODE = 0   # robocopy usa codigos 0-7 como exito; reset

# 1c) Inyecta Dockerfile/requirements/.dockerignore del manifest
Copy-Item "$MANIFEST\Dockerfile"      "$CTX\Dockerfile"      -Force
Copy-Item "$MANIFEST\requirements.txt" "$CTX\requirements.txt" -Force
Copy-Item "$MANIFEST\.dockerignore"   "$CTX\.dockerignore"   -Force

# 1d) Build en ACR (sin Docker local)
az acr build --registry $ACR --image "sv4-front:$SV4_TAG" $CTX

# =====================================================================
# 2) CONTAINER APP — ingress EXTERNO :8004, MI, secretos KV, env
# =====================================================================
# Secretos desde Key Vault (resueltos por el MI):
$SECRETS = @(
  "pg-password=keyvaultref:$KVURI/PG-PASSWORD,identityref:$MI_ID",
  "graph-key=keyvaultref:$KVURI/GRAPH-KEY,identityref:$MI_ID",
  "sigrid-key=keyvaultref:$KVURI/SIGRID-API-FUNCTION-KEY,identityref:$MI_ID"
)

# Variables de entorno (alias de Settings). API_HOST=0.0.0.0 es OBLIGATORIO
# en contenedor (127.0.0.1 no acepta trafico del ingress).
$ENVVARS = @(
  "API_HOST=0.0.0.0",
  "API_PORT=8004",
  "APP_TITLE=Revision de Albaranes IA",
  "LOG_LEVEL=INFO",
  "AUTO_CREATE_DATABASE=false",
  "PG_HOST=$PGHOST",
  "PG_PORT=5432",
  "PG_DB=albaranes",
  "PG_USER=ruesmaadmin",
  "PG_PASSWORD=secretref:pg-password",
  "PG_ADMIN_DB=postgres",
  "PG_ADMIN_USER=ruesmaadmin",
  "PG_ADMIN_PASSWORD=secretref:pg-password",
  "GRAPH_KEY=secretref:graph-key",
  "SHAREPOINT_DRIVE_ID=$SP_DRIVE",
  "COLAS_ACCOUNT_URL=$STORAGEQ",
  "AZURE_CLIENT_ID=$MI_CLIENTID",
  "SIGRID_API_BASE_URL=$SIGRID_URL",
  "SIGRID_API_FUNCTION_KEY=secretref:sigrid-key",
  "SIGRID_API_DATABASE=$SIGRID_DB"
)

az containerapp create `
  -g $RG -n $APP `
  --environment $ENVCA `
  --image $IMAGE `
  --registry-server $ACRLOGIN --registry-identity $MI_ID `
  --user-assigned $MI_ID `
  --ingress external --target-port 8004 --transport auto `
  --min-replicas 1 --max-replicas 2 `
  --cpu 0.5 --memory 1.0Gi `
  --secrets $SECRETS `
  --env-vars $ENVVARS

$FQDN = az containerapp show -g $RG -n $APP --query properties.configuration.ingress.fqdn -o tsv
"FQDN: https://$FQDN"

# =====================================================================
# 3) EASY AUTH (Entra ID) — App Registration + auth del Container App
#    Tras esto, el portal exige login y sv4 recibe X-MS-CLIENT-PRINCIPAL-NAME.
# =====================================================================
$REDIRECT = "https://$FQDN/.auth/login/aad/callback"
# Reutiliza el App Registration si ya existe (evita duplicados al re-ejecutar).
$APPID = az ad app list --display-name "ohana-albaranes-front" --query "[0].appId" -o tsv
if (-not $APPID) {
  $APPID = az ad app create `
    --display-name "ohana-albaranes-front" `
    --sign-in-audience AzureADMyOrg `
    --web-redirect-uris $REDIRECT `
    --enable-id-token-issuance true `
    --query appId -o tsv
} else {
  # Ya existe: NO sobrescribo sus redirect URIs (podría tener el callback del
  # dominio custom ohana.ruesma.es). Si falta, añádelo a mano en el portal.
  Write-Host "App Registration ya existe (appId=$APPID); dejo intactos sus redirect URIs." -ForegroundColor Yellow
}
"App Registration appId: $APPID"

# Secreto de cliente NUEVO. Sin --append: reemplaza en vez de acumular
# credenciales huérfanas en el App Registration.
$CSECRET = az ad app credential reset --id $APPID --query password -o tsv

# Provider Microsoft + exigir autenticacion
# NOTA: en single-tenant, --tenant-id y --issuer NO pueden ir juntos (Usage
# Error). Usamos SOLO --issuer con el v2.0 endpoint del tenant.
az containerapp auth microsoft update `
  -g $RG -n $APP `
  --client-id $APPID `
  --client-secret $CSECRET `
  --issuer "https://login.microsoftonline.com/$TENANT/v2.0" `
  --yes

az containerapp auth update `
  -g $RG -n $APP `
  --unauthenticated-client-action RedirectToLoginPage `
  --redirect-provider azureactivedirectory

"== LISTO ==  Abre https://$FQDN  (te redirige a login Entra ID)"

