# fase1_infra.ps1
# Provisión de la infraestructura de albaranes (Fase 1) con az CLI.
# Crea TODO menos los Container Apps (eso es Fase 2, tras empujar imágenes).
#
# Requisitos: Azure CLI logado (az login), permisos para crear recursos y
# asignar roles de datos (User Access Administrator o equivalente) en el RG.
#
# Uso:
#     . .\00_vars.ps1
#     .\fase1_infra.ps1
#
# Se te pedirá la contraseña del admin de PostgreSQL de forma segura (o ponla
# antes en $env:PG_ADMIN_PASSWORD).

$ErrorActionPreference = "Stop"

function Section($t) { Write-Host "`n=== $t ===" -ForegroundColor Green }
function Require($val, $msg) {
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Host "`nABORTADO: $msg" -ForegroundColor Red
        exit 1
    }
}

# --- 0) Precondiciones ------------------------------------------------------
Section "0) Suscripción, proveedores y extensión containerapp"
az account set --subscription $SUBSCRIPTION
foreach ($p in @(
    "Microsoft.App","Microsoft.OperationalInsights","Microsoft.Storage",
    "Microsoft.DBforPostgreSQL","Microsoft.KeyVault",
    "Microsoft.ContainerRegistry","Microsoft.ManagedIdentity")) {
    az provider register --namespace $p --only-show-errors | Out-Null
}
az extension add --name containerapp --upgrade --only-show-errors | Out-Null

# Contraseña del admin de PostgreSQL (segura; nunca se imprime).
if ($env:PG_ADMIN_PASSWORD) {
    $PGPASS = $env:PG_ADMIN_PASSWORD
} else {
    $sec = Read-Host "Contraseña para el admin de PostgreSQL ($PG_ADMIN)" -AsSecureString
    $PGPASS = [System.Net.NetworkCredential]::new("", $sec).Password
}

# objectId del que ejecuta (para darle permiso de escribir secretos en KV).
# Si te logaste con service principal, signed-in-user no existe: lo toleramos.
$ME = az ad signed-in-user show --query "id" -o tsv 2>$null
if ([string]::IsNullOrWhiteSpace($ME)) {
    Write-Host "  (aviso) no pude resolver tu objectId; me salto el rol 'Key Vault Secrets Officer' para ti." -ForegroundColor Yellow
}

# --- 1) Resource group ------------------------------------------------------
Section "1) Resource group $RG"
az group create -n $RG -l $LOCATION --tags $TAGS | Out-Null

# --- 2) Managed identity (compartida por todos los Container Apps) -----------
Section "2) Managed identity $MI"
az identity create -n $MI -g $RG -l $LOCATION --tags $TAGS | Out-Null
$MI_PRINCIPAL = az identity show -n $MI -g $RG --query "principalId" -o tsv
$MI_CLIENT    = az identity show -n $MI -g $RG --query "clientId"    -o tsv
$MI_ID        = az identity show -n $MI -g $RG --query "id"          -o tsv
Write-Host "  principalId=$MI_PRINCIPAL"

function Assign-Role($role, $scope) {
    # Idempotente: si ya está asignado, az avisa pero no rompemos.
    az role assignment create --assignee-object-id $MI_PRINCIPAL `
        --assignee-principal-type ServicePrincipal `
        --role $role --scope $scope --only-show-errors 2>$null | Out-Null
}

# --- 3) Azure Container Registry --------------------------------------------
Section "3) ACR $ACR"
az acr create -n $ACR -g $RG -l $LOCATION --sku Basic --tags $TAGS | Out-Null
$ACR_ID = az acr show -n $ACR -g $RG --query "id" -o tsv
Assign-Role "AcrPull" $ACR_ID

# --- 4) Log Analytics workspace ---------------------------------------------
Section "4) Log Analytics $LAW"
az monitor log-analytics workspace create -g $RG -n $LAW -l $LOCATION --tags $TAGS | Out-Null
$LAW_CUSTOMERID = az monitor log-analytics workspace show -g $RG -n $LAW --query "customerId" -o tsv
$LAW_KEY = az monitor log-analytics workspace get-shared-keys -g $RG -n $LAW --query "primarySharedKey" -o tsv
Require $LAW_CUSTOMERID "No pude obtener el customerId de Log Analytics '$LAW'."

# --- 5) Storage account + colas + contenedores ------------------------------
Section "5) Storage $STORAGE (5 colas + 2 contenedores)"
az storage account create -n $STORAGE -g $RG -l $LOCATION `
    --sku Standard_LRS --kind StorageV2 `
    --allow-blob-public-access false --min-tls-version TLS1_2 --tags $TAGS | Out-Null
$STKEY = az storage account keys list -n $STORAGE -g $RG --query "[0].value" -o tsv
$STID  = az storage account show -n $STORAGE -g $RG --query "id" -o tsv
Require $STID "El storage '$STORAGE' no se creó (nombre global pillado u otro error). Cambia `$SUFFIX en 00_vars.ps1 y re-ejecuta."
Require $STKEY "No pude leer la clave del storage '$STORAGE'."

# Roles de DATOS para la managed identity (runtime usa MI, no la clave).
Assign-Role "Storage Queue Data Contributor" $STID
Assign-Role "Storage Blob Data Contributor"  $STID

# Colas del sistema + sus poison.
foreach ($q in @("q-emails","q-extraccion","q-persistencia","q-valoracion","q-feedback")) {
    az storage queue create --name $q             --account-name $STORAGE --account-key $STKEY --only-show-errors | Out-Null
    az storage queue create --name "$q-poison"    --account-name $STORAGE --account-key $STKEY --only-show-errors | Out-Null
}
# Contenedores efímeros del hand-off entre workers (privados).
foreach ($c in @("input","envelopes")) {
    az storage container create --name $c --account-name $STORAGE --account-key $STKEY `
        --public-access off --only-show-errors | Out-Null
}

# --- 6) Key Vault (RBAC) + permisos -----------------------------------------
Section "6) Key Vault $KV (RBAC)"
az keyvault create -n $KV -g $RG -l $LOCATION `
    --enable-rbac-authorization true --tags $TAGS | Out-Null
$KV_ID = az keyvault show -n $KV -g $RG --query "id" -o tsv
Require $KV_ID "El Key Vault '$KV' no se creó (nombre global pillado u otro error). Cambia `$SUFFIX en 00_vars.ps1 y re-ejecuta."
# La MI puede LEER secretos en runtime.
Assign-Role "Key Vault Secrets User" $KV_ID
# Tú (el que despliega) puedes ESCRIBIR secretos (para add_secrets.ps1).
if (-not [string]::IsNullOrWhiteSpace($ME)) {
    az role assignment create --assignee-object-id $ME --assignee-principal-type User `
        --role "Key Vault Secrets Officer" --scope $KV_ID --only-show-errors 2>$null | Out-Null
}

# --- 7) Container Apps Environment (Consumo, público) -----------------------
Section "7) Container Apps Environment $CAE"
az containerapp env create -n $CAE -g $RG -l $LOCATION `
    --logs-destination log-analytics `
    --logs-workspace-id $LAW_CUSTOMERID --logs-workspace-key $LAW_KEY `
    --tags $TAGS | Out-Null

# --- 8) PostgreSQL Flexible Server + pgvector + firewall --------------------
Section "8) PostgreSQL $PG (tarda varios minutos)"
if ($MY_IP -eq "AUTO") {
    try {
        $MY_IP_RES = (Invoke-RestMethod -Uri "https://api.ipify.org").Trim()
        Write-Host "  IP pública detectada: $MY_IP_RES"
    } catch {
        $MY_IP_RES = Read-Host "  No pude autodetectar tu IP pública. Introdúcela"
    }
} else { $MY_IP_RES = $MY_IP }

az postgres flexible-server create -n $PG -g $RG -l $LOCATION `
    --tier $PG_TIER --sku-name $PG_SKU --version $PG_VER `
    --storage-size $PG_STORAGE_GB `
    --admin-user $PG_ADMIN --admin-password $PGPASS `
    --public-access $MY_IP_RES `
    --tags $TAGS --yes | Out-Null

# Crear la base de datos en paso aparte: las CLI nuevas NO admiten
# --database-name dentro de 'create' (lo reservan a clusters elásticos).
az postgres flexible-server db create -g $RG -s $PG -d $PG_DB --only-show-errors | Out-Null

# Permitir servicios de Azure (los Container Apps de Consumo tienen IP saliente
# dinámica) -> regla 0.0.0.0-0.0.0.0 (especial = "Allow Azure services").
az postgres flexible-server firewall-rule create -g $RG -n $PG `
    --rule-name AllowAzureServices `
    --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 --only-show-errors | Out-Null

# Habilitar la extensión pgvector (allowlist; el CREATE EXTENSION se hace luego).
az postgres flexible-server parameter set -g $RG -s $PG `
    --name azure.extensions --value vector --only-show-errors | Out-Null

$PG_FQDN = az postgres flexible-server show -n $PG -g $RG --query "fullyQualifiedDomainName" -o tsv
Require $PG_FQDN "El PostgreSQL '$PG' no se creó (nombre global pillado u otro error). Cambia `$SUFFIX en 00_vars.ps1 y re-ejecuta."

# Guardar la contraseña de PG en Key Vault (RBAC ya propagó tras crear PG).
az keyvault secret set --vault-name $KV --name "PG-PASSWORD" --value $PGPASS --only-show-errors | Out-Null

# --- 9) Resumen -------------------------------------------------------------
Section "9) RESUMEN"
Write-Host "RG               : $RG"
Write-Host "Managed identity : $MI  (clientId=$MI_CLIENT)"
Write-Host "ACR              : $ACR.azurecr.io"
Write-Host "Log Analytics    : $LAW"
Write-Host "Storage          : $STORAGE  (colas + contenedores input/envelopes)"
Write-Host "Key Vault        : $KV  (PG-PASSWORD ya guardada)"
Write-Host "CA Environment   : $CAE  (Consumo, público)"
Write-Host "PostgreSQL       : $PG_FQDN  db=$PG_DB user=$PG_ADMIN"
Write-Host "`nSIGUIENTE:" -ForegroundColor Yellow
Write-Host "  1) En la BBDD '$PG_DB' ejecuta una vez:  CREATE EXTENSION IF NOT EXISTS vector;"
Write-Host "  2) Rellena y corre .\add_secrets.ps1 con tus claves ROTADAS."
Write-Host "  3) Fase 2: az acr build de las 6 imágenes y creación de los Container Apps."

# Exporta a la sesión para Fase 2.
$Global:MI_ID = $MI_ID; $Global:MI_CLIENT = $MI_CLIENT
$Global:ACR_LOGIN = "$ACR.azurecr.io"; $Global:PG_FQDN = $PG_FQDN
