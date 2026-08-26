<!-- docs/referencia/dominio_negocio_albaranes.md -->
# Pipeline de Albaranes — Documento de referencia del proyecto (v2)

> Origen: documentación de proyecto del humano (compendio sv1–sv6 + sigrid_api
> + sesiones de despliegue) · Fecha del documento: 2026-08-05
> Incorporado a `docs/referencia/` el 2026-08-12.
> Llegó ya en Markdown: no requirió conversión con `markitdown`.

> **Redactado.** Se han sustituido por marcadores: el ID de tenant y el de
> suscripción de Azure (§5) y la IP interna del SQL Server de Sigrid (§4).
> El detalle está en el original, fuera del repositorio, y en
> `infra/*.local.ps1` (no versionado).

> **Erratas y vigencia (anotado 2026-08-13, validado con el humano):**
> - **§7 desactualizado**: el modo HTTP directo en local está **muerto**. El
>   local actual usa colas con Azurite (`infra/docs/levantar-pipeline-local.md`).
>   En sv1, `service2_http_client.py`/`service3_http_client.py` son código
>   muerto (nadie los importa) y las `SERVICE*_BASE_URL` de settings son
>   config zombi sin consumidor.
> - **sv1 ya es idempotente**: dedup por BBDD (`workflow_runs` vía
>   `ruesma_comun.workflows`, clave de idempotencia persistida). La
>   limitación #1 del `sv1.md` original está resuelta.
> - El «en paralelo» de los 3 proveedores de IA1 significa «la misma
>   extracción por N proveedores», no concurrencia: las llamadas son
>   **secuenciales** (limitación conocida en `sv2.md`, mejora propuesta
>   ThreadPoolExecutor). Todo el pipeline es secuencial por documento; el
>   paralelismo real son las réplicas KEDA compitiendo por la cola.
> - **§10.7 (bombeo)**: el ejemplo «20 m³/h → 5 h = 210 m³» tiene las horas
>   mal: el caso real son **10,5 h** de bombeo (210/20). La regla es la
>   misma: m³ a facturar = horas × rendimiento mínimo del contrato.
> - **§10.6 (residuos)**: la resta de la prioridad 2 está escrita al revés.
>   La dirección correcta —validada por el humano el 2026-08-13— es
>   **entregados − retirados**, que es lo que el código implementa
>   (`residuos_container_calc.py`); la regla «ambos ⇒ solo cuenta RETIRAR»
>   no deroga esa resta.
> - **§5.4 (modelos)**: la foto del 05/08 decía `claude-sonnet-5` en
>   producción, pero a 2026-08-16 lo desplegado real era `claude-opus-4-7`
>   (sv2 y sv5). Decisión del humano (2026-08-16): modelo objetivo
>   **`claude-opus-4-8`** en sv2 y sv5, y **`gemini-3.7-flash`** en IA1
>   (aplicado con `set_models.ps1` y fijado como default en
>   `create_capps.ps1`).
> - **Reglas nuevas del lote de ground truth alvaro_17082026 (2026-08-17,
>   decididas por el humano):** (1) los prefijos de partida válidos son SOLO
>   **CI, CD y CP** (una lectura «C1» es siempre CI); (2) el orden del
>   administrativo para resolver precio/importe es: líneas iguales ya
>   registradas en líneas de contrato → contrato en papel → como último
>   recurso el **COMPARATIVO asociado al contrato** («OFERTA» en el ground
>   truth = comparativo; es la futura fuente 1c, feature F-017); (3) las
>   **líneas tachadas** del albarán no se registran (F-015); (4) existe el
>   **reparto de una línea impresa entre varias partidas** con cantidades
>   parciales (F-016; caso Feymaco 108 uds = 54+54); (5) el descuento del
>   ground truth va en fracción (0.4 = 40 %).
> - **§5.2**: `q-feedback` está **reservada** para el futuro servicio de
>   entrada al ERP (aprobado en sv4 → alta en Sigrid vía `sql/write`); el
>   consumidor no está construido y nada externo la consume. `q-emails` es
>   una cola huérfana del diseño original (intake partido en receptor+worker,
>   luego colapsado en sv1): candidata a limpieza.

> Construcciones Ruesma S.A. · Ecosistema de microservicios para la digitalización,
> extracción con IA, valoración contra contrato y revisión humana de albaranes de
> proveedor recibidos por email.
> Actualizado: 05/08/2026. Fuentes: documentación sv1–sv6 + sigrid_api del proyecto
> y sesiones de despliegue de la infraestructura vigente.

Índice: §1 Visión · §2 Flujo end-to-end · §3 Modelo de datos · §4 Sigrid ·
§5 Recursos Azure · §6 **Despliegue en Azure (detallado)** · §7 **Ejecución en
local** · §8 Librería común · §9 **Tipologías** · §10 **Reglas de negocio y
decisiones** · §11 Estado actual · §12 Índice documental

---

## 1. Visión general

El sistema convierte un email con albaranes adjuntos (PDF o foto) en **líneas
valoradas contra el contrato del proveedor en Sigrid**, listas para que un
administrativo las revise, corrija y apruebe en un portal web antes de entrar
al ERP. Consta de 6 microservicios (sv1–sv6) + una librería común
(`albaranes-comun`, paquete `ruesma_comun`) + un proyecto de infraestructura
(`albaranes-infra`), todos en Python 3.12 con arquitectura hexagonal
(Ports & Adapters) y patrón pipeline.

```
Email (buzón M365) ──► sv1 intake ──► [q-extraccion] ──► sv2 extracción (3 LLMs)
                                              │ blob input/{id}.pdf
                                              ▼
                       [q-persistencia] ──► sv3 persistencia (merge + Sigrid + SharePoint)
                                              │ blob envelopes/{id}.json
                                              ▼
                       [q-valoracion] ──► sv6 valorador ──HTTP──► sv5 valuation-IA (Claude)
                                              │
                                              ▼
                                    PostgreSQL `albaranes`  ◄──lee/edita── sv4 portal revisión
```

**Cuatro fases de IA**: IA1 extracción genérica (sv2, 3 proveedores) · IA2
refinado por tipología con `contexto_linea` (sv2) · IA3 valoración contra
contrato + sintéticas M1–M7 (sv5) · IA4 conciliación de líneas sin match
(sv5, orquestada por sv6).

**Evolución arquitectónica**: la documentación original (sv1–sv3.md) describe
llamadas HTTP síncronas encadenadas. La arquitectura **vigente en Azure** es
asíncrona por Azure Storage Queues con workers KEDA que escalan 0→N; los
binarios van por Blob efímero y lo durable por SharePoint. El modo HTTP
directo sigue existiendo y es el que se usa **en local** (§7).

---

## 2. Flujo end-to-end detallado

1. **sv1 (intake)** — daemon de polling sobre el buzón vía Microsoft Graph
   (no leídos con adjuntos; filtro `.pdf .jpg .jpeg .png .webp`, ≤25 MB). PDF
   de N páginas → **N documentos lógicos de 1 página** (convención: 1 página =
   1 albarán). Calcula `attachment_sha256` + `document_sha256`, sube binario a
   Blob `input/{document_id}`, publica en `q-extraccion` con contexto de email,
   y mueve el correo a `Procesados`/`Errores` (replay operativo = devolver a
   inbox como no leído).

2. **sv2 (extracción)** — worker de `q-extraccion`. Preprocesado: detección de
   escaneado **por página** (imagen ≥0,70 de cobertura o <150 chars de texto
   real → rasterizar; mixto → todas a imagen); imágenes sueltas con cadena de
   realce (canal rojo → deskew → iluminación → estirado → unsharp → cap
   2400 px). IA1 e IA2 reciben **material idéntico**. Llama a los 3 LLMs con
   el mismo prompt YAML y schema Pydantic estricto (`DocumentoAlbaran`,
   `extra='forbid'`; `contexto_linea` laxo `extra='ignore'`). Publica envelope
   multi-proveedor vía blob `envelopes/{id}.json` + mensaje en
   `q-persistencia`.

3. **sv3 (persistencia)** — worker de `q-persistencia`. **Merge
   multi-proveedor** (`albaran_confidence_service`): normalización (texto,
   CIF, fecha ISO, código imputación, números), score campo a campo con
   ponderación de campos críticos; `contexto_linea` = el bloque completo del
   proveedor **más rico** (no se mezclan campos entre proveedores). Persiste
   raw + merge; sube a SharePoint PDF + 6 JSONs de IA. **Enrichment
   best-effort** vía sigrid-api: obra, contratos del proveedor por CIF con
   líneas (partida, precio) y PDF firmado de cada contrato. 1 contrato →
   auto-selección. Dispara valoración por `q-valoracion`.

4. **sv6 (valorador)** — worker de `q-valoracion`. HTTP interno a sv5
   `/value` (300 s). IA4 `/conciliar` sobre las no casadas (muta el envelope
   antes del build). Build en **3 pasadas** (bases → complementarias →
   sintéticas, cada hija con el record resuelto de su padre) con la maquinaria
   determinista: `PartidaMatcher`, `UnitConverter` + `UnitCategoryGuard`,
   `ImporteCalculator`, `price_reconciler` (1a vs 1b), redes de residuos y
   guards de año. Persistencia = **replace transaccional**.

5. **sv5 (valuation-IA)** — API HTTP interna stateless. Contexto por SQL
   crudo de solo lectura; PDF del contrato desde SharePooint; prefiltrado
   determinista de unidades; llamadas **solo a Claude**. Prompts
   `valuation_es` (V3, ~725 líneas) y `conciliacion_es` (regla dura de años).
   Respuestas saneadas por `json_coercion` antes de validar.

6. **sv4 (portal)** — FastAPI + Jinja2 + JS vanilla. Bandeja + detalle con
   vistas por proveedor, preview PDF vía Graph, edición in-place, selección de
   contrato + re-fetch Sigrid, Valorar (force=True → re-enrich +
   re-valoración), Deshacer, Borrado en bloque, aprobación. Único ingress
   externo (Easy Auth pendiente).

**Sintéticas M1–M7**: M1 año · M2 consistencia · M3 árido · M4 aditivo ·
M5 residuos/gestión · M6 exceso de tiempo · M7 carga incompleta. Con
`modifier_source`, `modifier_reason`, `rol_linea`; heredan partida/unidad de
su base. Al añadir un `modifier_source` nuevo hay que tocar **5 sitios**:
prompt YAML sv5, schema Pydantic sv5, DTO envelope sv6, record sv6, builder sv6.

---

## 3. Modelo de datos (PostgreSQL, BBDD `albaranes`, schema `public`)

Única BBDD compartida en **Azure Database for PostgreSQL Flexible Server**
(spaincentral). Host/credenciales por `PG_*` (password como Key Vault
reference). sv3 la crea si no existe (`AUTO_CREATE_DATABASE=true`).

### 3.1 Diagrama relacional

```
albaran_documents (raw)          albaran_lines (raw)
        │ 1 fila por (sha256, provider) — auditoría por IA

albaran_documents_merge  ◄─── FUENTE DE VERDAD (UQ source_sha256)
   ├─ albaran_lines_merge                (N)
   ├─ albaran_contratos_merge            (N)
   │     └─ albaran_contrato_lines_merge (N, con codigo_partida)
   └─ albaran_valuations (1:1, FK CASCADE)
         ├─ albaran_line_valuations      (N)
         │     ├─ FK merge_line_id            → albaran_lines_merge (NULL en sintéticas)
         │     ├─ FK matched_contrato_line_id → albaran_contrato_lines_merge
         │     └─ FK derived_contrato_line_id → contrato_lines_derived
         └─ contrato_lines_derived      (N)
```

### 3.2 `albaran_documents` / `albaran_lines` (raw, sv3)

Qué dijo cada proveedor antes del merge (mixin de columnas compartido con la
versión merge + discriminador de proveedor). Solo consulta forense.

### 3.3 `albaran_documents_merge` (sv3; columnas de sv4 por ALTER)

| Grupo | Columnas |
|---|---|
| Identificación | `id` UUID v4 PK · `provider_origin` · `source_sha256` (UQ) · `source_filename` · `source_mime_type` |
| Cabecera | `proveedor_nombre` · `proveedor_cif` · `fecha` · `numero_albaran` · `forma_pago` · `obra_codigo` · `obra_nombre` · `obra_direccion` |
| SharePoint | `sharepoint_drive_id` · `sharepoint_item_id` · `sharepoint_relative_path` · `sharepoint_web_url` · `sharepoint_share_url` |
| Artefactos IA | `ia_input_json` / `ia_output_json` inline · `{ia,gem,cla}_{input,output}_{relative_path,web_url}` |
| Contexto email | `email_id` · `email_subject` · `email_sender` · `email_received_datetime` · `raw_context_json` |
| Revisión (sv4) | `approved` bool · `approved_at_utc` · `approved_by` · `reviewed_at_utc` · `last_modified_at_utc` · `review_notes` · `selected_contrato_codigo` |

Índices sv4: `ix_albaran_documents_merge_approved`, `..._conf_calc`.

### 3.4 `albaran_lines_merge` (sv3)

Descripción, cantidad, unidad, precio/dtos/importe leídos, `codigo_imputacion`
(partida impresa en el albarán si la hay), `line_match_score`,
`field_scores_json`, `contexto_linea` (JSON del proveedor más rico),
`raw_extraction_json`.

### 3.5 `albaran_contratos_merge` (sv3 + sv4)

Cabecera de contrato Sigrid (código, descripción…) + sv4: `gra_rep_ide`,
`pdf_sharepoint_relative_path`, `pdf_sharepoint_web_url`.

### 3.6 `albaran_contrato_lines_merge` (sv3 **y** sv4, ambos IF NOT EXISTS)

Recursos del contrato: `codigo_producto`, descripción, unidad,
`precio_unitario`, **`codigo_partida`**. ⚠ DDL duplicado (alarma de diseño
documentada): gana el que arranque primero.

### 3.7 `albaran_valuations` (sv6, 1:1 con documento)

```
id UUID PK · document_id UQ FK CASCADE · contrato_codigo
status ∈ pending|running|ok|failed|no_contract|partial
provider_ia · model_name · prompt_key
total_valorado · total_lines
lines_matched_exact/_semantic/_price_only · lines_unmatched
review_required · review_reasons_json
raw_ia_envelope_json (envelope sv5 completo)
created_at_utc · updated_at_utc
```

### 3.8 `albaran_line_valuations` (sv6)

| Grupo | Columnas / dominios |
|---|---|
| Claves | `id` PK · `valuation_id` FK CASCADE · `merge_line_id` (NULL sintéticas) · `matched_contrato_line_id` · `derived_contrato_line_id` |
| Precios | `precio_unitario_contrato_db` (1a) · `_pdf_inferido` (1b) · `_final` · `precio_source` · `precio_agreement` |
| Unidades | `unidad_albaran` · `unidad_contrato` · `unidad_categoria` · `unidad_category_match` |
| Cantidades | `cantidad_albaran` · `cantidad_convertida` · `cantidad_factor_conversion` |
| Importes | `importe_calculado` · `importe_albaran_declarado` · `importe_source` |
| Partida | `codigo_partida_albaran` · `codigo_partida_final` · `partida_action` ∈ {existing_matched, new_line_created, inherited_from_base_line, alm_acopio, no_action} |
| Matching | `match_method` ∈ {exact_concept, semantic, price_only, no_match} · `match_confidence_pct` · `tarifa_pdf_encontrada` |
| Roles | `rol_linea` (base, incremento_year/consistencia/arido/aditivo/residuos/tiempo/carga_incompleta/otro, extra_tiempo…) · `ref_linea_base_merge_id` |
| Sintéticas | `line_kind` ∈ {from_albaran, synthetic_modifier} · `parent_merge_line_id` · `modifier_source` ∈ {codigo_producto, observaciones, year_contract, year_albaran, tiempo_exceso, gestion_residuos, carga_incompleta, otro} · `modifier_reason` · `descripcion_linea` |
| Auditoría | `review_required` · `review_reasons_json` · `ia_reasoning` · `descuento_albaran_aplicado` |

### 3.9 `contrato_lines_derived` (sv6)

Líneas de contrato creadas por la valoración: `origen` ∈ {missing_partida,
alm_acopio}, `created_by`, `source_doc`, `producto_partida` (indexadas).

### 3.10 Reglas de escritura

1. Valoración = replace transaccional (DELETE por document_id + INSERT).
2. sv4 edita el merge in-place (sin historial ni lock optimista).
3. DDL idempotente en tres servicios (sv3 lo crea todo; sv6 sus 27 sentencias;
   sv4 sus ALTERs con reintento).
4. sv5 lee con SQL crudo → contrato de columnas implícito con sv3.

---

## 4. Integración con Sigrid (ERP)

**sigrid-api** (`func-sigridapi-dev-huyke`, Function App Flex Consumption,
Python 3.12, RG `rg-sigrid-dev-data-api`, spaincentral): passthrough al SQL
Server on-premises (`IP-INTERNA-REDACTADA` vía VPN; túnel local dev
`127.0.0.1:11433`).

- `POST /api/sql/read` · `POST /api/sql/write` · `POST /api/documents/read`
  (binarios, p. ej. PDF de contrato desde `dbo.gra`) + endpoints de dominio.
- Bases: **`ruesma`** (única escribible), `ruesma_rep` (documentaria/replica de
  lectura), `master`. Usuarios `ro_user`/`user_rw`, passwords en
  `kv-sigridapi-dev-huyke`.
- Validación en dos planos (Pydantic + guard semántico); escritura off por defecto.
- Límite duro del balanceador Azure: **230 s** HTTP idle.

---

## 5. Recursos Azure

Tenant `REDACTADO-VER-COPIA-LOCAL` · Suscripción
`REDACTADO-VER-COPIA-LOCAL` (valores reales en `infra/00_vars.local.ps1`,
no versionado) · Región **spaincentral**. Nombres del
RG y recursos de albaranes centralizados en `00_vars.ps1` (`$RG`, `$ACR`,
`$LAW`…).

### 5.1 Container Apps (entorno interno `grayrock-806c3ddd.spaincentral.azurecontainerapps.io`)

| App | Repo ACR | Tipo | Ingress | Réplicas | Notas |
|---|---|---|---|---|---|
| `ca-sv1-intake` | `sv1` | daemon | ninguno | 1 fija | Único contacto con Graph-mail |
| `ca-sv2-extraccion` | `sv2` | worker KEDA | ninguno | 0→N | 3 API keys LLM |
| `ca-sv3-persistencia` | `sv3-persistencia` ⚠ | worker KEDA | ninguno | 0→N | Dueño del schema PG |
| `ca-sv4-front` | `sv4-front` ⚠ | web | **externo** | 1 | Easy Auth pendiente |
| `ca-sv5-valuation` | `sv5` | API HTTP | interno | **min 1** | FQDN interno fijo |
| `ca-sv6-valorador` | `sv6` | worker KEDA | ninguno | 0→N | Scaler `q-valoracion-scaler` (len 5, poll 30 s) |

⚠ repos con nombre ≠ servicio. ⚠ En `rg-partes-dev` existen apps homónimas de
otro proyecto: operar siempre con `-g $RG`.

### 5.2 Datos y mensajería

| Recurso | Nombre | Contenido |
|---|---|---|
| PostgreSQL Flexible Server | (host vía `PG_HOST`) | BBDD `albaranes` (§3) |
| Storage Account | `stalbaranesrs9k2` | Colas + Blob |
| Colas | `q-emails` · `q-extraccion` · `q-feedback` · `q-persistencia` · `q-valoracion` (+ `*-poison`) | visibilidad 600 s, máx. 5 desencolados |
| Blob efímero | `input/{id}` · `envelopes/{id}` | Hand-off binario; los workers NO borran inline. **Pendiente** lifecycle 14 días (`blob_lifecycle.ps1`) |
| ACR | `acralbaranesdev` | Tags de fecha `rYYYYMMDD-HHmm`, inmutables |
| Log Analytics | `log-albaranes-dev` (`$LAW`) | `ContainerAppConsoleLogs_CL` |
| Managed Identity | `id-albaranes-dev` | Colas (KEDA + apps), ACR pull, Key Vault |
| Key Vault | (albaranes) | `PG_PASSWORD`, API keys LLM, `GRAPH_KEY`, `SIGRID_API_FUNCTION_KEY` |

Operativa de colas sin rol de datos: `az storage queue ... --auth-mode key`.

### 5.3 Externos

SharePoint/Graph (carpeta raíz `albaranes`: PDF original + 6 JSONs IA/doc +
PDFs de contratos) · Buzón M365 (`Procesados`/`Errores`) · sigrid-api (§4) ·
APIs SaaS de OpenAI/Google/Anthropic.

### 5.4 Modelos LLM vigentes (05/08/2026)

sv2: `ANTHROPIC_MODEL=claude-sonnet-5`, `OPENAI_MODEL=gpt-5.4`,
`GEMINI_MODEL=gemini-3.1-pro-preview`. sv5: `ANTHROPIC_MODEL=claude-sonnet-5`.
Probados: sonnet-4-6 estable; opus-4-7 funcional tras el fix de
`json_coercion` (deformaba el JSON en ~40% de llamadas). Opus 4.7+ **rechaza**
`temperature/top_p/top_k` (el adaptador común no los envía).

---

## 6. Despliegue en Azure — funcionamiento detallado

### 6.1 Filosofía

Tres principios rigen todo el sistema de despliegue, cada uno nacido de un
incidente real:

1. **Imágenes inmutables con tag de fecha** (`rYYYYMMDD-HHmm`). Nunca se
   reescribe un tag existente. Motivo: una revisión de Container App queda
   anclada al **digest** con el que nació; si reescribes el tag `v2` en ACR,
   Azure sigue ejecutando la imagen vieja aunque el registro tenga código
   nuevo, sin ningún aviso. Costó una mañana entera de "desplegué pero se
   comporta igual".
2. **Una revisión activa por app (modo single)**. Con modo `multiple`, dos
   revisiones compiten: en un worker significa **dos consumidores de la misma
   cola con imágenes potencialmente distintas** (pasó con sv5/sv6: valoraba a
   veces con el código nuevo y a veces con el viejo).
3. **`comun` no tiene imagen propia**: se hornea dentro de cada servicio en el
   build. Consecuencia operativa: **tocar `ruesma_comun` obliga a reconstruir
   sv2, sv3, sv5 y sv6** (todos los que lo empaquetan). Un fix en
   `json_coercion.py` sin rebuild = fix que no existe en Azure.

### 6.2 Anatomía de `deploy.ps1` paso a paso

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-infra
. .\00_vars.ps1          # SIEMPRE primero: carga $RG/$ACR/$LAW, $REPO/$APPS/$IMG
.\deploy.ps1                              # ciclo completo
.\deploy.ps1 -Only sv4,sv6                # subset
.\deploy.ps1 -Tag r20260724-1433 -SkipBuild   # apps → imagen ya construida (rollback/retry)
```

Internamente:

1. **Prólogo anti-scope**. Si faltan los mapas globales, recarga
   `00_vars.ps1`; después **copia `$REPO`/`$APPS`/`$IMG` a hashtables locales
   con claves y valores forzados a `[string]`**. Motivo: bug de Windows
   PowerShell 5.1 — dentro de un script hijo, indexar un mapa global con la
   variable de un `foreach` devuelve `$null` (síntoma: verificación de
   `":r20260724-1433"` con el repo vacío, error `NullArray`).
2. **Tag**: si no se pasa `-Tag`, genera `r + fecha` y llama a `Set-DeployTag`,
   que reescribe `$IMG` (por eso la copia local de `$IMG` se hace DESPUÉS).
   El sufijo de revisión es el tag **en minúsculas** (Azure lo exige).
3. **Build** (salvo `-SkipBuild`): delega en `build_images.ps1`, que lanza
   `az acr build` por repositorio — la construcción ocurre **en la nube de
   ACR**, no hace falta Docker local. Cada Dockerfile copia la carpeta
   `comun` al contexto, así que el build siempre lleva el `ruesma_comun`
   fresco del disco.
4. **Verificación en ACR**: `az acr repository show-tags` por repo; si el tag
   no está en TODOS, **aborta sin tocar ninguna app**. Esto separa "el build
   falló" de "la app no arranca", que se diagnostican distinto.
5. **Update por app**, en el orden de `$APPS`:
   `az containerapp revision set-mode --mode single` +
   `az containerapp update --image $ACR/repo:tag --revision-suffix <tag>`.
   `$ErrorActionPreference=Continue` (¡no Stop!) porque la extensión
   containerapp escribe avisos por stderr y con Stop el `foreach` **muere en
   silencio en la primera iteración** (solo se actualizaba el primer
   servicio). El éxito se comprueba con `$LASTEXITCODE` servicio a servicio y
   los fallos se acumulan sin frenar al resto.
6. **Estado final**: llama a `check_deploy.ps1 -Expected <tag>` y sale con
   código ≠0 si algo falló.

### 6.3 Ciclo de vida de una revisión (qué mirar cuando "no despliega")

Al hacer update nace `ca-<app>--<sufijo>` en estado Provisioning. En modo
single, **Azure solo desactiva la revisión anterior cuando la nueva se declara
Healthy**: ver dos activas durante ~2 minutos es normal. Si persiste, la nueva
**no está arrancando** y la vieja sigue sirviendo como red de seguridad:

```powershell
az containerapp revision list -n <app> -g $RG `
  --query "[].{rev:name, activa:properties.active, provision:properties.provisioningState, salud:properties.healthState, replicas:properties.replicas}" -o table
# provision=Failed / salud=Unhealthy en la nueva → sus logs, apuntando a ESA revisión:
az containerapp logs show -n <app> -g $RG --revision <app>--<sufijo> --tail 100
```

Causas típicas: error de import de Python al arrancar (un pegado a medias en
`comun` tumba sv5 y sv6 a la vez y deja sv1–sv4 sanos), variable de entorno
que falta, o Key Vault reference sin permiso de la identity. Si tras
diagnóstico quedan dos activas: `.\fix_revisiones.ps1 -Only sv5,sv6`
(pone single y desactiva todas menos la más reciente).

### 6.4 Workers KEDA y réplicas

sv2/sv3/sv6 escalan **0→N** con el scaler de cola (ej. `q-valoracion-scaler`:
`queueLength 5`, polling 30 s, auth por `id-albaranes-dev`). Implicaciones:

- `replicas=0` en `check_deploy` es **normal** en reposo.
- Latencia de despertar: hasta ~1 min (poll 30 s + arranque del contenedor).
  Pulsar "Valorar" y no ver nada en 20 s no es un fallo.
- **No hay logs sin réplica**: `az containerapp logs show` da
  `Could not find a replica` con la app a cero. Para depurar:
  `az containerapp update -n <app> -g $RG --min-replicas 1` … y **devolver a 0
  al terminar** (si se olvida, la app consume 24/7).
- Los workers no borran los blobs de hand-off al procesar (semántica
  at-least-once: un mensaje puede reprocesarse y necesita el blob); la
  limpieza es una lifecycle policy del storage (pendiente de aplicar).

### 6.5 Secretos y configuración

- **Secretos** (API keys, PG_PASSWORD, GRAPH_KEY): Key Vault references en la
  Container App, resueltos con la managed identity. Jamás en imagen ni en `.env`.
- **`.env` está excluido del build de las imágenes** deliberadamente. Toda la
  configuración de producción va como env vars de la Container App
  (`create_capps.ps1` al crear; `az containerapp update --set-env-vars` en
  caliente). Un `.env` local con `ANTHROPIC_MODEL=x` NO afecta a Azure.
- **Cambio de modelos en caliente**: `.\set_models.ps1 -Anthropic <m>`
  (sv2: los tres proveedores; sv5: solo Claude). `--set-env-vars` solo toca
  las variables nombradas (secretrefs intactos), crea revisión nueva y fuerza
  modo single. **No persiste** ante una recreación: fijar también
  `$ANTHROPIC_MODEL` en `create_capps.ps1`.
- **Recreación completa**: `create_capps.ps1` (apps + env + scale rules +
  identity + secrets). Tras recrear, redeploy normal.

### 6.6 Verificación post-despliegue (ritual completo)

```powershell
.\check_deploy.ps1 -Expected rYYYYMMDD-HHmm -ConModelos
#  → las 6 con la imagen esperada, 1 revisión activa, modelos correctos

az containerapp update -n ca-sv6-valorador -g $RG --min-replicas 1
az containerapp logs show -n ca-sv6-valorador -g $RG --tail 50 --follow
#  → pulsar "Valorar" en el portal (Ctrl+F5 antes: sv4 cache-busta por reinicio)
#  Señales de éxito:
#    POST .../v1/albaranes/value  "HTTP/1.1 200 OK"      (no 400)
#    [conciliacion] IA4 aplicada: X/Y lineas conciliadas
#    persistida ... lines=N ... total=T
#    status=ok|valued  (no failed lineas=0)
#  En sv5, warnings [json-coercion] = el saneador corrigiendo formato en vuelo (OK)

az containerapp update -n ca-sv6-valorador -g $RG --min-replicas 0   # al acabar
```

### 6.7 Tabla de troubleshooting

| Síntoma | Causa | Acción |
|---|---|---|
| 400 `Input should be a valid list` / `extra_forbidden` en sv5 | El modelo LLM deforma el JSON (cambia con cada modelo) | Fix en `comun/llm/json_coercion.py` + rebuild; NO tocar el prompt |
| `does not exist` al hacer update | Nombre de app inventado (ca-sv2 vs ca-sv2-extraccion) o RG equivocado (homónimos en rg-partes-dev) | Usar `$APPS` y `-g $RG` siempre |
| Solo se actualiza el primer servicio del bucle | stderr de la extensión + `$ErrorActionPreference=Stop` | `Continue` + `$LASTEXITCODE` por servicio (ya en los scripts) |
| `NullArray` / verifica `":tag"` sin repo | Bug scope PS 5.1 con mapas globales en script hijo | Prólogo de copia a hashtables locales (ya en los scripts) |
| Dos revisiones activas persistentes | La nueva no arranca (import error, env, KV) | Logs de esa revisión con `--revision`; luego `fix_revisiones.ps1` |
| "Desplegué y se comporta igual" | Tag reescrito → revisión ancla digest viejo | Nunca reescribir tags; nuevo tag + update |
| `Could not find a replica` en logs | Worker a 0 réplicas | `--min-replicas 1` para depurar |
| Cambié comun y Azure no lo refleja | comun se hornea en el build | `deploy.ps1` (rebuild sv2/sv3/sv5/sv6) |
| Portal con CSS/JS viejos tras deploy | Cache del navegador | Ctrl+F5 (asset_version cambia por reinicio) |
| Modelos "vuelven solos" tras recrear apps | set_models no persiste | Fijar también en `create_capps.ps1` |

### 6.8 Rollback

Las imágenes viejas siguen en ACR con su tag de fecha:

```powershell
.\deploy.ps1 -Tag r20260720-0915 -SkipBuild        # todas
.\deploy.ps1 -Tag r20260720-0915 -SkipBuild -Only sv5,sv6
```

La bitácora de `00_vars.ps1` documenta qué llevaba cada tag.

---

## 7. Ejecución en local para pruebas

### 7.1 Qué cambia respecto a Azure

| Aspecto | Azure | Local |
|---|---|---|
| Encadenado sv1→sv2→sv3 | Colas + blob | **HTTP directo** (`SERVICE2_BASE_URL`/`SERVICE3_BASE_URL` en sv1) |
| Configuración | Env vars de Container App + Key Vault | **`.env` por proyecto** (aquí sí) |
| Modelos LLM | set_models / create_capps | `.env` (¡cuidado con la paridad! el bug de opus solo se vio en Azure porque local corría sonnet-4-6) |
| PostgreSQL | Flexible Server | PostgreSQL 14+ local (sv3 crea la BBDD `albaranes` vía credenciales admin) |
| Sigrid | VPN del spoke | Túnel local `127.0.0.1:11433` (o enrichment off dejando `SIGRID_API_BASE_URL` vacío) |
| SharePoint/Graph | Managed identity + KV | `GRAPH_KEY` en `.env` (JSON o base64-JSON con tenant/client/secret); sin él, sube/preview degradados |
| Logs IA | `/tmp/logs` del contenedor (efímero) | `logs/` del proyecto, persistentes y cómodos |

### 7.2 Prerrequisitos

Python 3.12 · PostgreSQL 14+ · venv por proyecto · (opcional) túnel a Sigrid ·
(opcional) `GRAPH_KEY` de la app Entra con permisos de aplicación
`Mail.ReadWrite` (+`.Shared` si buzón compartido) para sv1 y Files para
SharePoint.

### 7.3 Puertos y orden de arranque

| Orden | Servicio | Puerto | Arranque |
|---|---|---|---|
| 1 | sv2 extractor | **8000** | `python main.py` |
| 2 | sv3 persistencia | **8001** | `python main.py` (crea BBDD + todas las tablas + DDL sv6) |
| 3 | sv5 valuation | **8002** | `python main.py` |
| 4 | sv6 valorador | **8003** | `python main.py` (`VALUATION_API_BASE_URL=http://127.0.0.1:8002`) |
| 5 | sv4 portal | **8004** | `python main.py` → http://127.0.0.1:8004/documents |
| 6 | sv1 intake | — (daemon) | `python main.py` (necesita buzón; para pruebas suele omitirse) |

Por proyecto: `py -3.12 -m venv .venv` · `.\.venv\Scripts\Activate.ps1` ·
`pip install -r requirements.txt` · `copy .env.example .env` y rellenar.

El orden importa poco gracias al DDL idempotente (sv3 primero deja la BBDD
lista; sv4/sv6 reintentan), pero el de la tabla evita ruido de arranque.

### 7.4 Probar sin email: inyección directa

Sin sv1, el pipeline se alimenta a mano:

```bash
# 1) Extracción sola (inspeccionar el envelope de los 3 proveedores):
curl -X POST http://127.0.0.1:8000/v1/albaranes/extract -F "file=@albaran.pdf"

# 2) Ciclo completo hasta valoración: persist con el envelope del paso 1
curl -X POST http://127.0.0.1:8001/v1/albaranes/persist \
  -F "file=@albaran.pdf" \
  -F 'extraction_json=<envelope JSON del paso 1>' \
  -F 'context_json={"email":{...},"attachment":{...},"document":{...}}'
#    → sv3 mergea, enriquece contra Sigrid (si hay túnel) y dispara sv6→sv5

# 3) (re)valorar un documento existente:
curl -X POST http://127.0.0.1:8003/v1/valuation/run \
  -H "Content-Type: application/json" \
  -d '{"document_id":"<uuid>","force":true}'
```

O desde el portal local (8004): bandeja → detalle → "Valorar".

`/health` en cada API para comprobar wiring (sv2 lista los proveedores
habilitados; sv6 expone `schema_ready`).

### 7.5 Avisos de paridad local↔Azure

1. **Mismo modelo LLM que producción** al reproducir bugs: las deformaciones
   de JSON dependen del modelo.
2. Los prompts (`config/prompts.yaml`) se cargan al arranque: cambio de YAML
   ⇒ reiniciar el servicio (en Azure ⇒ rebuild de la imagen, van dentro).
3. Line endings: comun en LF; prompts.yaml y .py de sv6 en CRLF.
4. `ENABLE_OPENAI=true` obligatorio en sv2 (limitación conocida: el envelope
   ancla OpenAI en raíz).
5. Windows + PowerShell 5.1 para los scripts de infra (los bugs de scope no
   aplican a PS 7, pero los scripts están blindados para 5.1).

---

## 8. Librería común (`ruesma_comun`)

- `colas/` — arranque de workers, consumidor (visibilidad 600 s, máx. 5
  desencolados, poison), publicador; auth por managed identity o connection
  string.
- `llm/` — clientes de los 3 proveedores (el de Claude no envía
  temperature/top_p/top_k), `retry_policy` (backoff + jitter),
  **`json_coercion.py`**: saneador pre-validación con 6 deformaciones
  documentadas (doble anidamiento de clave raíz, string-JSON, extras a None,
  extras basura con valor tipo `line_index`, sintéticas sin
  `descripcion_linea` → rellenar con texto del propio modelo o eliminar la
  línea, desanidado de strings hasta 3 niveles). `llm_call_logger`: JSONs de
  debug request/response en `LOG_DIR`.
- `imaging/preprocess.py` — detección de escaneado por página + realce de
  imágenes sueltas; IA1 e IA2 reciben material idéntico.

---

## 9. Tipologías de albarán

> **Anotado el 2026-08-27 (F-043).** Esta sección es la NARRATIVA de negocio
> de cada tipología —qué es, qué se entregó y qué falta—, y sigue valiendo
> como tal. **No es la lista de familias válidas**: esa vive en UN solo
> sitio, el catálogo `ruesma_comun/contratos/familias.py` de
> `services/albaranes-comun`, y es de donde salen las familias que la IA
> puede elegir, sus definiciones, el prompt de fase 2 y el de valoración.
> Mantener aquí una segunda lista es exactamente lo que hizo que sv2, sv5 y
> sv6 acabaran con criterios distintos sobre qué es «residuos» (F-023).
> Si añades o cambias una familia, se hace en el catálogo; esta sección se
> lee para saber **por qué** existe, no para saber **cuáles** hay.
>
> Dos matices que el catálogo sí decide y aquí no se ven:
> - **Familia de DOCUMENTO** (la que clasifica el albarán entero y elige el
>   prompt) hoy son cuatro: `generico`, `hormigon`, `mortero`, `residuos`
>   —las que tienen prompt de fase 2 propio—. `combustible`,
>   `alquiler_maquinaria` y `bombeo` (§9.5–§9.7) son familia de **LÍNEA**:
>   sin prompt al que enrutar, la etiqueta de documento no tendría reglas
>   detrás (decisión del humano, 2026-08-26).
> - **La clasificación la decide IA1 leyendo el papel**, nunca una regla que
>   la deduzca del código LER, del producto, del texto o del CIF. Ver la
>   regla 14 de `docs/ARCHITECTURE.md`.

La tipología determina el prompt de IA2 (bloque `contexto_linea`), las
sintéticas admisibles en IA3 y las redes deterministas de sv6. Estado a
05/08/2026:

### 9.1 Genérico / Suministros — ACTIVA

La base (`albaran_factura_es`): cabecera + líneas con cantidad/unidad/precio/
dtos/importe. Cubre prefabricados, cerámica, ferretería… (LEVEL PREFABRICADOS
salió perfecto: 1.394,40 y 1.494,00 € exactos). Puntos débiles detectados
(feedback 07/2026): transcripción de albaranes ya valorados y match demasiado
laxo (→ reglas en §10.4/§10.5).

### 9.2 Hormigón — ACTIVA (la más elaborada)

Nomenclatura posicional, sintéticas M1–M7, tarifas 1a (BBDD) vs 1b (PDF del
contrato), generador determinista de incremento de año como respaldo.
Pendiente de la tanda 3: re-apuntado de incrementos al recurso del contrato
en la partida de la base, veto de partidas inexistentes y no emitir M6/M7 sin
señal.

### 9.3 Mortero — HOY DENTRO DE HORMIGÓN → SEPARARLA (decidido, pendiente)

Los códigos `D-*` NO siguen la nomenclatura posicional del hormigón y la IA
la aplicaba igualmente (inventó incremento de árido y plastificante en un
mortero). Decisión: familia propia con **veto determinista** (§10.3).

### 9.4 Residuos / Contenedores — ACTIVA (parcial)

Entregado: LER como código de línea (6 dígitos sin espacios), volumen/peso por
etiqueta de casilla (nunca por magnitud), llevadas/retiradas capturadas por
separado, cálculo de contenedores por prioridades con guard de plausibilidad.
Pendiente (tanda 4): la lógica de pago LLEVAR/RETIRAR + línea de canon (§10.6).

### 9.5 Bombeo — NUEVA, PENDIENTE (tanda 4)

Detectada en el feedback (PUMPING TEAM): valoración especial por rendimiento
mínimo contractual (§10.7). Requiere prompt de familia + leer el rendimiento
del contrato.

### 9.6 Combustible / Indirectos — PARCIAL

`contexto_linea` de combustible existe desde sv2. Regla de partida propia
(los indirectos SÍ se destinan) y discrepancia precio contrato vs albarán
pendientes de codificar (ORE OIL).

### 9.7 Alquiler — PARCIAL

`contexto_linea` de alquiler existe desde sv2 (maquinaria, medios auxiliares).
Sin reglas de valoración específicas aún; los fallos de ALQUILERES LUQUE
fueron de transcripción/match, no de la tipología en sí.

---

## 10. Reglas de negocio y decisiones tomadas

Compendio normativo. Cada regla indica dónde se aplica (prompt / red
determinista sv6 / proceso) y su estado: ✅ implementada · 🔶 decidida,
pendiente de implementar.

### 10.1 Identificación del documento

- 🔶 **Obra solo de la lista de obras activas.** IA1 recibirá las obras
  activas de Sigrid inyectadas en el prompt y elegirá SOLO de esa lista; red
  en sv3: obra extraída inexistente → sin obra + revisión. Jamás persistir
  una obra no válida (casos: 0937 inventada; 4 MACOTRAN en 4 obras erróneas).
- 🔶 **Proveedor = razón social del bloque fiscal (con CIF), nunca la marca
  del logotipo.** Red en sv3: resolución por CIF contra Sigrid; si el CIF no
  casa pero el nombre contiene un proveedor con contrato en la obra →
  propuesta a revisión. (Caso "GRUPO OTTO HORPRESOL" vs HORPRESOL, S.L.)
- 🔶 **Guard de año en fechas**: `fecha_albaran` a >1 año de la recepción del
  email → revisión (caso 2023 vs 2026 en foto).
- ✅ 1 página = 1 albarán (split en sv1).
- ✅ Idempotencia por `source_sha256` (UQ en merge).

### 10.2 Hormigón — nomenclatura posicional (lección de negocio completa)

Código `HA-25/B/12/XC2/F/P` → resistencia / consistencia / árido / ambiente /
sufijos:

| Elemento | Valores | Regla de incremento |
|---|---|---|
| Consistencia | **B** blando · **P** plástico | Sin incremento |
| | **F** fluido · **L** líquido · **S** seco | CON incremento (tarifa en contrato) |
| Árido | 12 | Incremento "cambio árido 12-15" |
| | 20 | Sin incremento |
| Ambiente | XC2, Ia, IIa, IIIa… | Posible incremento según contrato |
| Sufijo `/F/` | Fratasado | Incremento (suelos pulidos) |
| Sufijo `/P` | Fibras polipropileno | Incremento (suele ir con fratasado) |
| Cemento `/SR` | Sulforresistente | Solo si aparece en el código |

- ✅ **Aditivos: jamás** (Ruesma no los usa). Ninguna sintética de aditivo.
- ✅ **Incremento por año: UNO solo**, salvo dos años consecutivos declarados.
  El concepto muestra el año ("INCREMENTO AÑO 2025"). IA4 tiene regla dura:
  un incremento de año no casa con la tarifa de otro año.
- ✅ **Exceso de descarga: se lee pero NO se valora** (no va en contrato sino
  en condiciones de oferta; Horpresol no lo factura). Emitir con precio null
  a revisión.
- 🔶 **Incrementos en contrato deben CASAR con su recurso**, y en la
  **partida de la línea base** del hormigón (re-apuntado determinista antes de
  derivar). Solo derivar si de verdad no existe.
- 🔶 **M6/M7 (exceso de tiempo, carga incompleta) solo con señal explícita**
  en el documento; cantidad 0 sin texto → no emitir.
- 🔶 **La partida de un incremento debe existir en el contrato** (o ALM/None);
  jamás un literal nuevo.

### 10.3 Mortero (familia D-*)

- 🔶 **Solo arena**: veto determinista a sintéticas de árido, aditivo,
  plastificante, fibras y fratasado. Admisibles: consistencia con tarifa real
  y cemento especial si aparece.
- 🔶 El tercer campo del código es resistencia, no árido (refuerzo de prompt).
- ✅ Con 2 contratos posibles → sin asignar, elige el humano (comportamiento
  validado por negocio).

### 10.4 Albaranes que VIENEN VALORADOS

- 🔶 **Transcribir, no recomponer**: precio unitario, TODOS los descuentos
  (lista) e importe se copian tal cual están impresos, cada uno por su
  etiqueta de columna. Prohibido derivar precio = importe×algo (caso ×120:
  23.073,60 € por 191,40 €).
- 🔶 **El dto del albarán no se aplica sobre el precio de contrato.**
- 🔶 **Guard aritmético**: `precio × cantidad (− dtos) ≈ importe_linea` leído;
  si no cuadra → revisión, nunca inventar. Y `Σ importes = total albarán`
  (con una línea, idénticos — caso ORE OIL).

### 10.5 Matching albarán ↔ contrato

- 🔶 **Atributo sustantivo distinto ⇒ NO casar.** Si la descripción difiere
  en tamaño, modelo o tipo (ladrillos CETOSA, elemento base 0,5 mm, bolsa de
  cuñas), mejor línea nueva sin precio a revisión que un precio equivocado
  con apariencia de bueno. ("Esto nos dará problemas siempre" — negocio.)
- ✅ Diferencias solo tipográficas/de formato sí casan (mortero D-300).
- ✅ Conciliación IA4 corre ANTES del build y muta el envelope; solo
  interviene en líneas sin match o sin precio.
- ✅ Precio: si 1a (BBDD) y 1b (PDF) discrepan, **prevalece 1a** y se registra
  el desacuerdo (`precio_agreement`).
- ✅ Importe: si el declarado difiere del calculado >5% → se usa el calculado
  con razón `declared_vs_calculated_mismatch`; si no, prevalece el declarado
  (más fiel al documento).
- ✅ Unidades: 7 categorías; conversión solo intra-categoría;
  `UnitCategoryGuard` fuerza revisión en mismatch duro; **`ml` = metro
  lineal** por defecto (convención construcción).
- 🔶 **Líneas manuscritas** (devoluciones, abonos) son legítimas: capturar
  con `origen=manuscrito`; deben entrar en Sigrid (devolución de palets).

### 10.6 Residuos / contenedores

- ✅ LER de 6 dígitos SIN espacios como `codigo` de la línea (fluye a
  CÓD.EXTERNO de Sigrid).
- ✅ Volumen y peso por ETIQUETA de casilla (6 m³ / 29 Tn → volumen=6,
  peso=29, cantidad=6; kg→Tn), nunca por magnitud del número.
- ✅ Llevadas y retiradas se capturan por separado, sin restar en lectura.
- ✅ Contenedores por prioridades: (1) explícitos; (2) retiradas−llevadas si
  ≥1; (3) ceil(volumen/tamaño). Tamaño: exacto del contrato → ese; si no,
  estándar 6 m³; único en contrato → ese. Plausibilidad: volumen >16 m³ →
  `residuos_volumen_implausible` → revisión.
- 🔶 **Solo LLEVAR → no se paga y no entra en Sigrid. RETIRAR → se paga el
  porte + línea de CANON DE VERTEDERO obligatoria. Ambos → solo cuenta
  RETIRAR.**
- 🔶 Partida del recurso del contrato; jamás inventar (16.01 vs 15.01).

### 10.7 Bombeo

- 🔶 **m³ a facturar = horas de bombeo × rendimiento mínimo del contrato**
  (ej. 20 m³/h → 5 h = 210 m³ aunque se bombearan menos). La línea de horas
  NO se factura aparte (embebida en el mínimo). El desplazamiento sí.

### 10.8 Partidas (imputación)

- ✅ Si el albarán trae `codigo_imputacion`, manda (re-apuntado por
  descripción o derivada si la IA casó otra partida).
- ✅ Complementarias y sintéticas heredan la partida de su línea base.
- 🔶 **Suministros NO se destinan**: partida ALM (almacén), imputación
  parcial mensual. **Indirectos SÍ se destinan** a la entrada.
- 🔶 Cuando el mismo recurso existe en varias partidas (contratos de hormigón
  con clones), la elección es **humana**: selector de candidatas en sv4 +
  memoria por obra+producto para prerrellenar. La IA no puede saberlo: la
  información (a qué tajo va el camión) no está en el documento.
- ✅ `codigo_partida_final` auditado con `partida_action`.

### 10.9 Decisiones de arquitectura y operación

- ✅ Colas + workers KEDA en Azure; HTTP directo en local. El buzón M365 como
  "cola visible" para humanos con replay manual.
- ✅ Blob efímero de hand-off sin borrado inline (at-least-once); limpieza por
  lifecycle policy (pendiente).
- ✅ SharePoint = almacenamiento documental durable (PDF + 6 JSONs IA + PDFs
  contrato). PostgreSQL = estado estructurado. Sigrid solo vía sigrid-api.
- ✅ Merge multi-proveedor en sv3 (no hay "proveedor ganador" global);
  `contexto_linea` del proveedor más rico, sin mezclar.
- ✅ Valoración con Claude solo (sv5); extracción con los tres (sv2).
- ✅ Deformaciones de formato de los LLM se absorben en `json_coercion`
  (capa técnica), no en prompts (capa de negocio). Filosofía del saneador:
  extras con valor desconocidos hacen fallar (mejor perder que corromper),
  salvo lista blanca de basura conocida; una sintética irrecuperable se
  elimina antes que tumbar el documento entero.
- ✅ Replace transaccional de valoraciones; edición humana in-place del merge.
- ✅ Imágenes inmutables, modo single, comun horneado (§6.1).
- ✅ Anthropic Tier 2 necesario en producción (Tier 1 de 10k tokens/min se
  queda corto con prompts V3 + PDFs).
- ✅ Evaluación de modelos: banco de ground truth en 6 Excel por categoría
  (pestañas LEEME/ALBARANES/IA1–IA4) rellenados por administrativo; protocolo
  de benchmarking: mismos docs, "Borrar todas → Valorar", 2 pasadas por doc y
  modelo.

---

## 11. Estado actual y trabajo en curso (05/08/2026)

**Desplegado**: tag `r20260724-1433` en las 6 apps (fix json_coercion
completo), Sonnet 5 en producción, benchmarking Sonnet 5 vs Opus 4.7 en
marcha.

**Plan de tandas del feedback de negocio** (JMV, 27–29/07, 16 albaranes):
1. Obra + proveedor (G1+G2) — obras activas a IA1, razón social por CIF,
   redes sv3. 2. Valorados + match estricto + coherencia (G3+G4+G5). 3.
   Hormigón fino (re-apuntado incrementos, veto mortero, M6/M7 con señal,
   partida válida). 4. Bombeo + residuos LLEVAR/RETIRAR/canon. 5. Partida ALM
   por defecto + selector de candidatas en sv4.

**Pendientes de infra**: `blob_lifecycle.ps1` sin ejecutar · devolver
min-replicas 0 a sv3/sv6 tras el benchmarking · Easy Auth en sv4 · aviso
duplicado cosmético en `check_deploy.ps1`.

---

## 12. Índice de documentación fuente

| Documento | Contenido |
|---|---|
| `sv1.md` … `sv6.md` | Análisis exhaustivo por servicio |
| `sigrid_api.md` | Function App passthrough a Sigrid |
| `tablas_sigrid.pdf` | Modelo de datos del ERP |
| `CO388632 … Documento Entregable.pdf` | Diseño de la Landing Zone Azure |
| `BBDD_ALBARANES_AZURE.md` | Monográfico del modelo de datos (05/08/2026) |
