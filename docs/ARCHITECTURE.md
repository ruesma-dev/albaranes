<!-- docs/ARCHITECTURE.md -->
# Arquitectura · albaranes (monorepo)

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
> Redactado el 2026-08-12 leyendo el código real y `azure-apps/albaranes.md`.
> La sección «Semántica de dominio» está **pendiente de validación por el
> humano** (ver nota en esa sección).

## Qué hace este proyecto

Pipeline que automatiza el ciclo de vida de los **albaranes de proveedor**
de Construcciones Ruesma: llegan por email, se extraen con varias IAs en
paralelo, se persisten y enriquecen con los contratos del ERP (Sigrid), se
**valoran** contra esos contratos (matching de líneas y precios) y un humano
los revisa y aprueba en un front web. Corre como 6 Azure Container Apps en
Spain Central; la comunicación entre etapas es por **colas de Azure Storage**
(Azurite en local).

## Capas y estructura

**Nivel monorepo** — un servicio por etapa, hand-off por colas:

| Servicio | Carpeta | Rol | Consume | Publica | HTTP |
|---|---|---|---|---|---|
| sv1 | `services/albaranes-email` | Ingesta buzón M365, PDF a Blob `input/` | — (daemon polling) | `q-extraccion` | — |
| sv2 | `services/albaranes-api` | Extracción multi-IA (envelope, sin merge) | `q-extraccion` | `q-persistencia` | :8000 |
| sv3 | `services/albaranes-persistencia` | Dueño del schema PG; raw+merge, SharePoint, contratos Sigrid | `q-persistencia` | `q-valoracion` | :8001 |
| sv4 | `services/albaranes-front` | Front humano de revisión/aprobación | — | `q-persistencia`, `q-valoracion`, `q-feedback` | :8004 |
| sv5 | `services/albaran-valoracion-api` | Motor IA de valoración (stateless, no persiste) | — | — | :8002 |
| sv6 | `services/albaran-valoracion-persist` | Valorador: llama a sv5, reglas deterministas, persiste | `q-valoracion` | — (fin de cadena) | :8003 |

Los nombres canónicos de colas (`q-emails`, `q-extraccion`, `q-persistencia`,
`q-valoracion`, `q-feedback`), los contratos Pydantic de mensajes y el runtime
de colas/blobs viven en **`services/albaranes-comun`** (`ruesma_comun`), que
cada servicio instala como paquete. sv7 (orquestador antiguo) está disuelto.

**Nivel servicio** — hexagonal: `domain/` (modelos y puertos, sin
dependencias externas), `application/` (pipelines y servicios),
`infrastructure/` (adaptadores: BBDD, colas, Graph, Sigrid, LLM),
`interface_adapters/` (`api`/`web`/`worker`) y `composition.py` como raíz de
composición. sv2, sv3 y sv6 tienen doble entrada: `main.py` (HTTP) y
`main_worker.py` (consumidor de cola).

**Blobs**: `input/{document_id}.pdf` (lo deja sv1) y
`envelopes/{document_id}_{fase}.json` (lo deja sv2). Son efímeros; lo durable
va a SharePoint (PDF del albarán, JSONs de IA, PDF del contrato).

## Semántica de dominio imprescindible

> **BORRADOR deducido del código y de `azure-apps/albaranes.md`; el humano
> debe validarlo antes del primer uso real.** Lo que esté mal aquí producirá
> bugs con confianza de reviewer.

1. **El merge es la fuente de verdad.** `albaran_documents_merge` (UQ por
   `source_sha256`) y sus líneas. Las tablas raw (`albaran_documents`,
   `albaran_lines`, una fila por proveedor IA) son auditoría forense: ninguna
   feature construye lógica sobre ellas.
2. **La valoración es un replace transaccional**: DELETE por `document_id`
   (CASCADE) + INSERT completo. Nunca update incremental de una valoración.
3. **sv5 lee con SQL crudo, sin ORM**: su contrato con el schema es implícito
   por nombre de columna. Renombrar una columna del merge compila en sv3 y
   revienta sv5 en runtime. Todo cambio de schema lista sus lectores.
4. **`albaran_contrato_lines_merge` la crean sv3 Y sv4** (`IF NOT EXISTS`
   ambos; gana el que arranca primero). Acoplamiento conocido y documentado:
   si se toca ese DDL, se toca en los dos sitios.
5. **sv4 edita el merge in-place, sin control optimista**: dos revisores
   simultáneos se pisan (limitación conocida, no un bug a "arreglar" de
   pasada sin feature propia).
6. **`codigo_imputacion`** en una línea de albarán = la partida impresa en el
   papel (si la hay); **`codigo_partida_final`** en la valoración es la
   decisión tras el matching. No son intercambiables.
7. **Líneas sintéticas**: la valoración puede crear líneas que no existen en
   el albarán (`line_kind=synthetic_modifier`, portes/recargos) y líneas de
   contrato derivadas (`contrato_lines_derived`, `origen ∈ {missing_partida,
   alm_acopio}`). Al agregar importes hay que decidir explícitamente si
   entran o no.
8. **Unidades y tolerancias en sv6**: conversión por
   `UNIT_REGISTRY_YAML_PATH`, tolerancias `PRICE_TOLERANCE_PCT` e
   `IMPORTE_TOLERANCE_PCT`. No comparar cantidades ni precios de unidades
   distintas sin pasar por el conversor.
9. **Dedup de ingesta**: sv1 deduplica por `correlation_key` contra
   `workflow_runs` (PG). Reprocesar un email no debe crear un documento
   nuevo; el sha256 del PDF es la identidad del documento aguas abajo.

## Acceso a datos y sistemas externos

- **PostgreSQL `albaranes`** (Azure Flexible Server compartido
  `psql-albaranes-rs9k2`): sv3 dueño del schema; sv4 lectura+escritura de
  revisión; sv5 SOLO lectura; sv6 dueño de las 3 tablas de valoración; sv1
  solo `workflow_runs`. Cambios a nivel de servidor afectan a otros
  proyectos: prohibidos desde aquí.
- **Sigrid (ERP)**: SOLO vía `sigrid-api` (function key), SOLO lectura.
  Máximo 1.000 filas por petición; el balanceador corta a los 230 s.
- **Microsoft Graph**: buzón M365 (sv1) y SharePoint (sv3/sv4/sv5) con
  `GRAPH_KEY`. SharePoint es el almacén durable de documentos.
- **APIs LLM**: Anthropic/OpenAI/Gemini (sv2 y sv5, flags `ENABLE_*`).
  Las claves llegan por entorno/Key Vault, jamás en código ni en specs.
- **Colas y blobs**: Azure Storage en la nube; **Azurite en local**
  (`COLAS_CONNECTION_STRING`) — desde local nunca contra las colas reales.
- Los unit tests no tocan NINGUNO de estos sistemas: mocks y fixtures.

## Infra y despliegue

- Azure Container Apps (Spain Central), registro `acralbaranesdev` (admin
  deshabilitado: acceso por managed identity), secretos en Key Vault
  referenciados desde cada Container App.
- Scripts en `infra/`: `fase1_infra.ps1` (provisión), `add_secrets.ps1`,
  `create_capps*.ps1`, `build_images.ps1` + `deploy.ps1` (redespliegue).
  `build_images.ps1` espera los repos como hermanos: desde el monorepo,
  pasarle `-ProjectsRoot <monorepo>\services`.
- Imágenes con **tags fechados** (`rYYYYMMDD-HHmm`), nunca reescribir tags.
- Los IDs de suscripción/tenant/MI están **redactados** en los scripts
  versionados; los valores reales viven en `infra/*.local.ps1` (gitignored).
- `.env` nunca viaja: ni a git ni a una imagen.
