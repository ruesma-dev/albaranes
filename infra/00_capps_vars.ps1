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

# --- F-053 · Alta en Sigrid (sv9 y sv4) -------------------------------------
# UNA sola fuente para sv4 y sv9: create_capps_sv9.ps1 y set_alta_sigrid.ps1
# leen de aqui, y set_alta_sigrid.ps1 pone LOS MISMOS valores en las dos apps
# (design §7: DESDE, Espera y mapeo deben coincidir).
#   - ALTA_SIGRID_DESDE_UTC vacia = feature APAGADA (sv9 confirma sin hacer
#     nada y sv4 no publica ni pinta nada). La pone el humano.
#   - ALTA_SIGRID_USUARIO_RESPALDO (F-053 v8, U1/U5): login de dbo.usu con el
#     que se da de alta cuando quien aprobo no casa con un login de Sigrid
#     (R47). Es pgris (existe en dbo.usu, T0c); no es secreto. Vacio = esas
#     altas van a error (usuario_no_resuelto, R48).
# ALTA_SIGRID_COMMIT NO esta aqui a proposito: create_capps_sv9.ps1 crea sv9
# con ALTA_SIGRID_COMMIT=false (simulacion) y SOLO el humano lo cambia, a
# mano y con autorizacion (MANUAL T29). Ningun script lo pone a true.
$Global:ALTA_SIGRID_DESDE_UTC            = ""
$Global:ALTA_SIGRID_ESPERA_INCIERTO_MIN  = "15"
# Mapeo familia -> producto (JSON con clave "*"). VACIO = el defecto del codigo,
# igual en sv4 y sv9: {"alquiler_maquinaria": "QA9999", "medios_auxiliares":
# "XA9999", "*": "MA9999"}. Si lo cambias, set_alta_sigrid.ps1 lo pasa con las
# comillas escapadas y lo RELEE de las dos apps: un JSON roto no arranca (R44).
$Global:ALTA_SIGRID_PRODUCTO_POR_DEFECTO = ""
$Global:ALTA_SIGRID_USUARIO_RESPALDO     = "pgris"   # U5: versionado, no es secreto
$Global:ALTA_SIGRID_EMPIDE               = ""   # vacia = defecto de sigrid-api

# Pares CLAVE=valor comunes a sv4 y sv9 (los tres que deben coincidir).
# Windows PowerShell 5.1 (y 7.x en modo Legacy) se come las comillas dobles de
# los argumentos a programas nativos: el JSON del mapeo se escapa a mano.
function Global:AltaSigridEnvComun() {
    $pares = @(
        "ALTA_SIGRID_DESDE_UTC=$($Global:ALTA_SIGRID_DESDE_UTC)",
        "ALTA_SIGRID_ESPERA_INCIERTO_MIN=$($Global:ALTA_SIGRID_ESPERA_INCIERTO_MIN)"
    )
    $mapeo = [string]$Global:ALTA_SIGRID_PRODUCTO_POR_DEFECTO
    if ($mapeo) {
        $legacy = ($PSVersionTable.PSVersion.Major -lt 7) -or ($PSNativeCommandArgumentPassing -eq "Legacy")
        if ($legacy) { $mapeo = $mapeo -replace '"', '\"' }
        $pares += "ALTA_SIGRID_PRODUCTO_POR_DEFECTO=$mapeo"
    }
    $pares
}

# --- Escalado KEDA ----------------------------------------------------------
$Global:KEDA_QUEUE_LENGTH = 5   # mensajes objetivo por réplica
$Global:WORKER_MAX_REPLICAS = 5

Write-Host "[capps-vars] MI_CLIENTID=$MI_CLIENTID  PG_HOST=$PG_HOST" -ForegroundColor Cyan
Write-Host "[capps-vars] QUEUE_URL=$QUEUE_URL" -ForegroundColor Cyan
if ($SP["SHAREPOINT_DRIVE_ID"] -eq "RELLENA") {
    Write-Host "[capps-vars] AVISO: rellena el bloque SharePoint (\$SP) antes de crear sv3/sv5." -ForegroundColor Yellow
}
