# 00_vars.ps1
# Variables compartidas de la infraestructura de albaranes (Fase 1).
# Dot-source este fichero en cada consola nueva ANTES de los demás scripts:
#     . .\00_vars.ps1
#
# RELLENA los marcados con  <-- RELLENA  con tus valores reales antes de correr.

# --- Identidad de la suscripción -------------------------------------------
$Global:SUBSCRIPTION = "REDACTADO-VER-COPIA-LOCAL"
$Global:TENANT       = "REDACTADO-VER-COPIA-LOCAL"
$Global:LOCATION     = "spaincentral"

# --- Sufijo único global ----------------------------------------------------
# STORAGE, KV y PG comparten namespace MUNDIAL: deben ser únicos en todo Azure.
# Si la creación falla por "already taken", cambia este sufijo por otro corto
# (minúsculas/dígitos). El ACR ya se creó como 'acralbaranesdev', así que NO
# lleva sufijo (no lo dupliques).
$Global:SUFFIX = "rs9k2"               # <-- cámbialo si algo sigue pillado

# --- Nombres de recursos ----------------------------------------------------
$Global:RG       = "rg-albaranes-dev"
$Global:MI       = "id-albaranes-dev"               # managed identity (ya creada)
$Global:ACR      = "acralbaranesdev"                # YA CREADO -> sin sufijo
$Global:LAW      = "log-albaranes-dev"              # ya creado
$Global:STORAGE  = "stalbaranes$SUFFIX"             # 3-24 minúsc/dígitos, único
$Global:CAE      = "cae-albaranes-dev"
$Global:PG       = "psql-albaranes-$SUFFIX"         # único global
$Global:PG_DB    = "albaranes"
$Global:PG_ADMIN = "ruesmaadmin"
$Global:KV       = "kv-albaranes-$SUFFIX"           # 3-24, único global

# --- Mapa de imagen por servicio (FUENTE ÚNICA: build y create lo comparten)-
# 'repo:tag' REAL que usa cada Container App en ACR. build_images.ps1 construye
# con EXACTAMENTE estos nombres y create_capps.ps1 / create_sv1.ps1 los
# referencian, así nunca pueden discrepar (fue la causa del crash de sv3:
# imagen construida con un nombre y app apuntando a otro).
# Si reconstruyes un servicio con nueva versión, súbele el tag AQUÍ y vuelve a
# correr build+update SOLO de ese servicio.
# REPOSITORIO por servicio (sin tag). Los tags se generan por FECHA en
# cada despliegue (ver Set-DeployTag mas abajo): NUNCA se reescribe un
# tag existente. Motivo (24-jul-2026): reescribir "v2"/"v3" dejaba las
# revisiones de Container Apps clavadas al DIGEST viejo -> Azure seguia
# ejecutando codigo de semanas antes aunque el tag del ACR fuera nuevo.
$Global:REPO = [ordered]@{
  "sv1" = "sv1"
  "sv2" = "sv2"
  "sv3" = "sv3-persistencia"
  "sv4" = "sv4-front"
  "sv5" = "sv5"
  "sv6" = "sv6"
}

# CONTAINER APP por servicio. OJO: rg-partes-dev tiene apps con nombres
# IDENTICOS (ca-sv2-extraccion, ca-sv3-persistencia, ca-sv4-front) para
# el pipeline de PARTES. Todos los scripts pasan -g $RG explicito; no
# lances updates sin resource group o cruzaras las imagenes.
$Global:APPS = [ordered]@{
  "sv1" = "ca-sv1-intake"
  "sv2" = "ca-sv2-extraccion"
  "sv3" = "ca-sv3-persistencia"
  "sv4" = "ca-sv4-front"
  "sv5" = "ca-sv5-valuation"
  "sv6" = "ca-sv6-valorador"
}

# Mapa repo:tag EFECTIVO que consumen build_images.ps1 y create_*.ps1.
# Bitacora de despliegues (el tag vivo lo pone deploy.ps1 al vuelo):
#  r20260724-0942  sv2 hormigon posicional + preproceso por pagina +
#                  residuos; sv3 fix re-valorado force; sv4 fechas +
#                  deshacer por albaran + borrado en bloque; sv5 prompts
#                  hormigon/residuos + regla dura de anios (IA4); sv6
#                  redes deterministas (codigo, guard anio, contenedores)
#  (siguiente)     comun/llm/json_coercion.py: desenvuelve respuestas de
#                  Claude con la clave raiz repetida. SIN esto, con
#                  claude-opus-4-7 sv5 devolvia 400 y sv6 cerraba los
#                  documentos como failed con 0 lineas (en local no se
#                  veia: alli corria sonnet-4-6). Toca comun -> obliga a
#                  reconstruir sv2, sv3, sv5 y sv6.
$Global:IMG = [ordered]@{
  "sv1" = "sv1:r20260724-0942"
  "sv2" = "sv2:r20260724-0942"
  "sv3" = "sv3-persistencia:r20260724-0942"
  "sv4" = "sv4-front:r20260724-0942"
  "sv5" = "sv5:r20260724-0942"
  "sv6" = "sv6:r20260724-0942"
}

# Genera un tag de despliegue por FECHA y reescribe $IMG con el.
# Uso normal: lo llama deploy.ps1 solo. A mano:
#     . .\00_vars.ps1 ; Set-DeployTag            # r20260724-1530
#     . .\00_vars.ps1 ; Set-DeployTag "hotfix-1"
function Global:Set-DeployTag {
    param([string] $Tag = ("r" + (Get-Date -Format "yyyyMMdd-HHmm")))
    foreach ($k in @($Global:REPO.Keys)) {
        $Global:IMG[$k] = "$($Global:REPO[$k]):$Tag"
    }
    $Global:DEPLOY_TAG = $Tag
    Write-Host "[vars] tag de despliegue: $Tag" -ForegroundColor Cyan
    return $Tag
}
# Nota: en ACR quedó un repo 'sv3' huérfano (del nombre corto antiguo). Es
# inofensivo; si quieres limpiarlo:
#   az acr repository delete --name acralbaranesdev --repository sv3 --yes

# --- Tags acens (OBLIGATORIOS por Azure Policy) -----------------------------
$Global:TAGS = @(
  "acens-customer=Construcciones-Ruesma",
  "acens-environment=dev",
  "acens-project=albaranes",
  "acens-responsable-so-app=pgris"
)

# --- PostgreSQL: red e IP de admin -----------------------------------------
$Global:MY_IP = "AUTO"                 # o "88.x.x.x"
$Global:PG_SKU  = "Standard_B1ms"
$Global:PG_TIER = "Burstable"
$Global:PG_VER  = "16"
$Global:PG_STORAGE_GB = 32

# --- sigrid-api (informativo) ----------------------------------------------
$Global:SIGRID_BASE_URL = "https://func-sigridapi-dev-huyke.azurewebsites.net"

Write-Host "[vars] cargadas. RG=$RG  STORAGE=$STORAGE  KV=$KV  PG=$PG" -ForegroundColor Cyan
Write-Host "[vars] servicios: $((($Global:APPS.Keys) -join ', '))  |  despliegue: .\deploy.ps1" -ForegroundColor DarkGray

