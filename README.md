# albaranes — monorepo del pipeline de albaranes

Monorepo montado el 2026-08-12 por volcado limpio de los repositorios de
origen, que quedan archivados en solo lectura como referencia (cada uno
tiene un `ARCHIVADO.md` que apunta aquí). El repo de origen, su rama y el
hash HEAD en el momento de la importación están anotados en el mensaje
del commit de importación de cada carpeta.

## Estructura

| Carpeta | Origen |
|---|---|
| `services/albaranes-email` (sv1) | repo `albaranes-email` |
| `services/albaranes-api` (sv2) | repo `albaranes-api` |
| `services/albaranes-persistencia` (sv3) | repo `albaranes-persistencia` |
| `services/albaranes-front` (sv4) | repo `albaranes-front` |
| `services/albaran-valoracion-api` (sv5) | repo `albaran-valoracion-api` |
| `services/albaran-valoracion-persist` (sv6) | repo `albaran-valoracion-persist` |
| `services/albaranes-comun` | repo `albaranes-comun` (no estaba en git) |
| `infra/` | repo `albaranes-infra` (no estaba en git) |

## Infra: valores locales

Los IDs de suscripción, tenant y managed identity están **redactados** en
los scripts versionados (regla: nunca IDs en el repositorio). Los valores
reales viven en `infra/*.local.ps1`, que no se versiona.

La BBDD, colas y contratos entre servicios están documentados en
`azure-apps/albaranes.md`.
