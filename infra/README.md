# Fase 1 — Infraestructura albaranes (az CLI directo)

Provisiona en **Spain Central** todo lo necesario **menos los Container Apps**
(eso es Fase 2). Entorno de Container Apps **de Consumo público**, PostgreSQL
Flexible **público + firewall + pgvector**, secretos en **Key Vault (RBAC)** y
una **managed identity** compartida con los roles de datos ya asignados.

## Prerrequisitos
1. **Rotar TODAS las claves** antes de nada (los `.env` se han compartido):
   Graph, function key de sigrid-api, claves de Anthropic/OpenAI/Gemini, y la
   contraseña de PostgreSQL será nueva. **No se despliega con claves viejas.**
2. `az login` y `az account set --subscription <SUB>` (lo hace el script).
3. Permisos para **crear recursos** y **asignar roles de datos** en el RG
   (User Access Administrator o equivalente). La policy `acens-owner-limit`
   impide asignar *Owner*, pero aquí solo asignamos roles de datos concretos.
4. Tener la **extensión `containerapp`** de az (el script la instala).

> **¿Solo quieres redesplegar código?** No necesitas nada de esta Fase 1:
> `. .\00_vars.ps1` y luego `.\deploy.ps1`. Ver `README_capps.md`.

## Orden de ejecución (PowerShell)
```powershell
# 1. Edita 00_vars.ps1: rellena los tags acens-* (costcenter, sla, compliance)
#    y revisa que los nombres globales (ACR/STORAGE/PG/KV) estén libres.
. .\00_vars.ps1

# 2. Provisiona la infraestructura (te pedirá la contraseña de PostgreSQL).
.\fase1_infra.ps1

# 3. En la BBDD 'albaranes', una sola vez (psql / pgAdmin / DBeaver):
#    CREATE EXTENSION IF NOT EXISTS vector;

# 4. Carga los secretos ROTADOS en Key Vault.
.\add_secrets.ps1
```

## Notas / gotchas
- **Nombres únicos globales**: `ACR`, `STORAGE`, `PG`, `KV`. Si alguno está
  pillado, añade sufijo en `00_vars.ps1` (como sigrid-api con `-huyke`).
- **Tags obligatorios**: la policy acens audita/bloquea recursos sin los tags.
  Rellena los `RELLENA` de `00_vars.ps1` antes de correr.
- **Firewall de PostgreSQL**: se abre tu IP (admin) + "Allow Azure services"
  (los Container Apps de Consumo tienen IP saliente dinámica). Es lo pragmático
  para DEV; en endurecimiento posterior se pasa a endpoint privado.
- **Sin tocar la VNet de acens**: el entorno es de Consumo público. Los workers
  no tienen ingress (no son alcanzables desde fuera); solo sv4 expondrá ingress
  con Easy Auth en Fase 2.
- **Diagnóstico**: el entorno manda logs al Log Analytics `log-albaranes-dev`.
  La policy `Deploy-Diag-LogsCat` añadirá además el streaming al workspace
  central de la landing automáticamente.
- **Idempotente**: puedes re-ejecutar `fase1_infra.ps1`; los `create` no
  duplican y las asignaciones de rol repetidas se ignoran.

## Qué viene en Fase 2
- `az acr build` de las 6 imágenes (sv1, sv2, sv3, sv4, sv5, sv6) con los
  Dockerfiles ya preparados.
- Creación de los **Container Apps**: workers (sv2/sv3/sv6) con **escalador
  KEDA por longitud de cola** (auth por managed identity), sv5 interno HTTP,
  sv4 con **ingress externo + Easy Auth**, sv1 daemon `minReplicas=1`.
- Variables de entorno por **Key Vault references** + `COLAS_ACCOUNT_URL` /
  `BLOBS_ACCOUNT_URL` (managed identity, sin secretos de storage).
- **Lifecycle policy** del storage para purgar `input/` y `envelopes/` a los
  7-30 días (el pendiente anotado).
