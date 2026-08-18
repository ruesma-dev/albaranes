<!-- docs/ARCHITECTURE.md -->
# Arquitectura · albaranes (monorepo)

> Este documento es NORMATIVO: el spec-author diseña contra él y el
> reviewer rechaza lo que lo incumpla. Si no está aquí, no es un requisito.
> Redactado el 2026-08-12 leyendo el código real y `azure-apps/albaranes.md`.
> La sección «Semántica de dominio» está **pendiente de validación por el
> humano** (ver nota en esa sección).

## Qué hace este proyecto

Pipeline que automatiza el ciclo de vida de los **albaranes de proveedor**
de Construcciones Ruesma: llegan por email, se extraen, se persisten y
enriquecen con los contratos del ERP (Sigrid), se **valoran** contra esos
contratos (matching de líneas y precios) y un humano los revisa y aprueba en
un front web. La IA trabaja en **cuatro fases secuenciales** (una detrás de
otra, no en paralelo): **IA1** extracción genérica (3 proveedores LLM sobre
material idéntico) → **IA2** refinado por tipología (`contexto_linea`), ambas
en sv2 → **IA3** valoración contra contrato + sintéticas M1–M7 (sv5) →
**IA4** conciliación de líneas sin match (sv5, orquestada por sv6, que muta
el envelope antes del build). Incluso los 3 proveedores de IA1 se llaman uno
detrás de otro. El pipeline es **estrictamente secuencial por documento**; el
paralelismo real del sistema está a nivel de documentos: réplicas KEDA
compitiendo por la cola.

Hay **dos despliegues**: el de **Azure es el real** (6 Container Apps en
Spain Central, colas de Azure Storage, workers KEDA; se gestiona con
`infra/`) y el **local es solo para pruebas** (usa Azurite;
`infra/docs/levantar-pipeline-local.md`).

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
cada servicio instala como paquete. Dos colas especiales: **`q-feedback`**
está reservada para el futuro servicio de entrada al ERP (aprobado → alta en
Sigrid vía sigrid-api `sql/write`; el consumidor NO está construido) y
**`q-emails`** es una huérfana del diseño original, pendiente de limpieza
(F-009). El encadenado HTTP directo sv1→sv2→sv3 está **muerto**: en local
también se trabaja con colas (Azurite).

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

> Este es el RESUMEN operativo. El detalle normativo completo —tipologías de
> albarán y reglas de negocio con su estado ✅ implementada / 🔶 decidida
> pendiente— vive en `docs/referencia/dominio_negocio_albaranes.md` (§9–§10)
> y **prevalece sobre este resumen** en caso de conflicto.

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
   1 página = 1 albarán (sv1 trocea los PDF multipágina).
10. **Añadir un `modifier_source` nuevo (sintéticas) toca 5 sitios**: prompt
    YAML de sv5, schema Pydantic de sv5, DTO del envelope de sv6, record de
    sv6 y builder de sv6. Hacerlo a medias rompe la valoración.
11. **Aditivos de hormigón: jamás** (Ruesma no los usa; ninguna sintética de
    aditivo). Y en albaranes que ya vienen valorados: **transcribir, no
    recomponer** (precios, descuentos e importes se copian tal cual; nunca
    derivar unos de otros).
12. **Matching estricto**: un atributo sustantivo distinto (tamaño, modelo,
    tipo) ⇒ NO casar; mejor línea nueva sin precio a revisión que un precio
    equivocado con apariencia de bueno.
13. **Precio, descuento e importe de una línea de albarán** (F-019, ago 2026).
    `precio` es el unitario **bruto** (antes de descuento) y **`precio_neto`
    de una línea de albarán es el IMPORTE de la línea tras descuento**, NO un
    precio unitario — nombre histórico y engañoso, pero es la semántica que
    aplican el prompt de IA1, el guard de consistencia de sv3, el front sv4 y
    los clientes de Document AI / Document Intelligence. Fórmula canónica,
    única y sin excepciones:
    **`importe = cantidad × precio × (1 − descuento/100)`**.
    Y **el unitario leído manda**: el importe solo se despeja
    (`importe / (cantidad × (1 − dto/100))`) cuando el albarán no trae
    unitario. Si ambos existen y discrepan, gana el declarado y la línea va a
    revisión — nunca se inventa un unitario en silencio. Leer un `precio_neto`
    como si fuera unitario multiplica el importe por la cantidad: es lo que
    valoró en 6.238,14 € un albarán de 139,66 € (`progress/
    prueba_local_feymaco_20260818.md`). El contrato del ERP nunca pisa un
    valor leído del albarán: es fallback solo cuando no hay ninguno.
    La fórmula obliga a **todo el que escriba un importe**, no solo al
    valorador: sv6 la aplica en `ImporteCalculator` y sv4 en
    `review_repository._importe_de_linea` cuando el revisor guarda. Quien
    recalcule un importe sin el factor del descuento deshace el trabajo del
    otro: el 2026-08-18 sv6 valoró el albarán 2.137.569 en sus 139,66 €
    correctos y el primer guardado desde el front lo dejó en 232,76 €. Un
    servicio **no reetiqueta** como `calculated` un importe que el albarán
    declara si nadie ha tocado la línea.

## Acceso a datos y sistemas externos

- **PostgreSQL `albaranes`** (Azure Flexible Server compartido
  `psql-albaranes-rs9k2`): sv3 dueño del schema; sv4 lectura+escritura de
  revisión; sv5 SOLO lectura; sv6 dueño de las 3 tablas de valoración; sv1
  solo `workflow_runs`. Cambios a nivel de servidor afectan a otros
  proyectos: prohibidos desde aquí.
- **Sigrid (ERP)**: SOLO vía `sigrid-api` (function key), SOLO lectura.
  Configurado a 10.000 filas por petición (2026-08-13; el dato de 1.000 de
  `azure-apps` está desactualizado); el balanceador corta a los 230 s.
- **Microsoft Graph**: buzón M365 (sv1) y SharePoint (sv3/sv4/sv5) con
  `GRAPH_KEY`. SharePoint es el almacén durable de documentos.
- **APIs LLM**: Anthropic/OpenAI/Gemini (sv2 y sv5, flags `ENABLE_*`).
  Las claves llegan por entorno/Key Vault, jamás en código ni en specs.
- **Colas y blobs**: Azure Storage en la nube; **Azurite en local**
  (`COLAS_CONNECTION_STRING`) — desde local nunca contra las colas reales.
- Los unit tests no tocan NINGUNO de estos sistemas: mocks y fixtures.

## Infra y despliegue

`infra/` gestiona SOLO el despliegue de Azure (el real); el local de pruebas
no usa estos scripts. Detalle completo del despliegue, troubleshooting y
rollback: `docs/referencia/dominio_negocio_albaranes.md` §6–§7.

- Azure Container Apps (Spain Central), registro `acralbaranesdev` (admin
  deshabilitado: acceso por managed identity), secretos en Key Vault
  referenciados desde cada Container App.
- **Modo single de revisiones** (dos revisiones activas = dos consumidores
  de la misma cola con imágenes distintas) y **`comun` horneado en cada
  imagen**: tocar `ruesma_comun` obliga a reconstruir sv2, sv3, sv5 y sv6
  — un fix en comun sin rebuild no existe en Azure.
- Scripts en `infra/`: `fase1_infra.ps1` (provisión), `add_secrets.ps1`,
  `create_capps*.ps1`, `build_images.ps1` + `deploy.ps1` (redespliegue).
  `build_images.ps1` espera los repos como hermanos: desde el monorepo,
  pasarle `-ProjectsRoot <monorepo>\services`.
- Imágenes con **tags fechados** (`rYYYYMMDD-HHmm`), nunca reescribir tags.
- Los IDs de suscripción/tenant/MI están **redactados** en los scripts
  versionados; los valores reales viven en `infra/*.local.ps1` (gitignored).
- `.env` nunca viaja: ni a git ni a una imagen.
