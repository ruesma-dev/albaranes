# 00_capps_vars.ps1
# Variables para crear los Container Apps. Dot-source DESPUÉS de 00_vars.ps1:
#     . .\00_vars.ps1
#     . .\00_capps_vars.ps1
#
# Calcula valores derivados de Fase 1 y deja un bloque SharePoint/Sigrid que
# TÚ rellenas copiando de tus .env de sv3 y sv5 que ya funcionan.

$ErrorActionPreference = "Stop"
if (-not $RG) { throw "Falta `$RG. Haz primero:  . .\00_vars.ps1" }

# --- Derivados de Fase 1 (se consultan a Azure) -----------------------------
$Global:MI_ID       = az identity show -n $MI -g $RG --query "id" -o tsv
$Global:MI_CLIENTID = az identity show -n $MI -g $RG --query "clientId" -o tsv
$Global:ACR_LOGIN   = "$ACR.azurecr.io"
$Global:KV_URI      = "https://$KV.vault.azure.net"
$Global:PG_HOST     = "$PG.postgres.database.azure.com"
$Global:QUEUE_URL   = "https://$STORAGE.queue.core.windows.net"
$Global:BLOB_URL    = "https://$STORAGE.blob.core.windows.net"

# --- SharePoint: PEGA aquí los valores de tu sv3/.env que funciona ----------
# (Son los SHAREPOINT_* NO secretos. El secreto GRAPH_KEY va por Key Vault.)
# Borra los que no uses; añade los que te falten. El modo del piloto era
# drive_id, así que como mínimo necesitas SHAREPOINT_MODE y SHAREPOINT_DRIVE_ID.
$Global:SP = [ordered]@{
  "SHAREPOINT_MODE"        = "drive_id"      # o lo que tengas
  "SHAREPOINT_DRIVE_ID"    = "b!1MGRgCm-hU2ZQzBy5nJKU0IHpwhGorZHmWz-yozHEtpEwh0tlcBwQqMKgTOZjcR_"       # <-- de tu .env
  "SHAREPOINT_FOLDER_ROOT" = "albaranes"       # <-- de tu .env (carpeta raíz)
  "SHAREPOINT_LINK_TYPE"   = "view"
  "SHAREPOINT_LINK_SCOPE"  = "organization"
  # Si usas hostname/site_path en vez de drive_id, añade:
  # "SHAREPOINT_HOSTNAME"  = "..."; "SHAREPOINT_SITE_PATH" = "..."; "SHAREPOINT_DRIVE_NAME" = "..."
}

# --- Sigrid (no secreto) ----------------------------------------------------
$Global:SIGRID_DB = "ruesma"   # SIGRID_API_DATABASE del piloto

# --- Escalado KEDA ----------------------------------------------------------
$Global:KEDA_QUEUE_LENGTH = 5   # mensajes objetivo por réplica
$Global:WORKER_MAX_REPLICAS = 5

Write-Host "[capps-vars] MI_CLIENTID=$MI_CLIENTID  PG_HOST=$PG_HOST" -ForegroundColor Cyan
Write-Host "[capps-vars] QUEUE_URL=$QUEUE_URL" -ForegroundColor Cyan
if ($SP["SHAREPOINT_DRIVE_ID"] -eq "RELLENA") {
    Write-Host "[capps-vars] AVISO: rellena el bloque SharePoint (\$SP) antes de crear sv3/sv5." -ForegroundColor Yellow
}
