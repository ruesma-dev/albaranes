<!-- specs/F-002-obra-proveedor/design.md -->
# F-002 · Tanda 1 — Identificación de obra y proveedor (G1+G2) · Diseño

Toca DOS servicios: **sv2** (`services/albaranes-api`, prompt de IA1) y
**sv3** (`services/albaranes-persistencia`, redes deterministas). No toca
schema de BBDD: todas las columnas necesarias existen ya
(`review_required`, `review_reasons_json`, `review_notes`,
`obra_codigo_origen`, `email_received_datetime`).

## Contexto del código real (leído, no supuesto)

- sv2 carga los prompts con `YamlPromptRepository`
  (`infrastructure/prompts/yaml_prompt_repository.py`) desde
  `config/prompts.yaml` (`PROMPTS_YAML_PATH`). La fase 1
  (`AlbaranExtractionService.extract_phase_1`) NO renderiza placeholders
  hoy; la fase 2 sí (patrón `str.replace`, con append de compatibilidad si
  el placeholder no está en el YAML desplegado). Se replica ese patrón.
- El worker de sv2 (`interface_adapters/worker/extraction_worker.py`)
  ejecuta fase 1 + fase 2 y tiene un puerto `GroundingCabecera` cableado a
  `GroundingNulo()` (la fase 2 corre HOY sin grounding en modo colas). Esta
  feature NO reactiva ese grounding: actúa en fase 1 (lista de obras, que no
  depende del JSON extraído) y en las redes de sv3.
- sv3: el `PersistAlbaranPipeline` ejecuta, best-effort y en orden:
  `HeaderResolverService` (deduce obra/CIF si faltan) →
  `ObraEnrichmentService` (valida `obra_codigo` contra Sigrid y sobrescribe
  nombre/dirección) → `ContratoEnrichmentService` → trigger de valoración.
  Los lookups Sigrid necesarios YA existen en
  `infrastructure/sigrid/sigrid_api_obra_client.py` (`fetch_obra_by_codigo`,
  `search_obras`) y `sigrid_api_contrato_client.py`
  (`fetch_proveedor_by_cif`, `fetch_contratos_resumen_por_obra`,
  `search_proveedores`).
- **Gap detectado**: en modo colas el mensaje de `q-persistencia` solo trae
  `document_id` + `correlation_key`; el handler
  (`interface_adapters/worker/persistence_worker.py`) construye
  `context={"correlation_key": ...}` sin bloque `email`, así que
  `email_received_datetime` queda NULL en el merge. El dato SÍ existe: sv1 lo
  guarda en `workflow_runs.payload_json` (`email_received_at_utc`,
  `from_address`, `subject`, `email_message_id`, `attachment_*`,
  `page_number`, `total_pages`), accesible con
  `ruesma_comun.workflows.RepositorioWorkflows.obtener_por_correlation_key`.
  El guard de año exige recuperar ese contexto (R12).

## sv2 — lista de obras activas en el prompt de IA1

### Ficheros a crear

- `services/albaranes-api/domain/ports/obras_activas_provider.py` — capa
  domain. `@dataclass(frozen=True) ObraActiva(codigo: str, nombre: str | None)`
  y `class ObrasActivasProvider(Protocol)` con
  `obtener(self) -> list[ObraActiva] | None` (None = no disponible).
- `services/albaranes-api/infrastructure/sigrid/__init__.py` — vacío (con
  comentario de ruta).
- `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py`
  — capa infrastructure. `class SigridApiObrasClient` con
  `__init__(*, base_url, function_key, database, timeout_s=30.0,
  max_rows=10000, cod_min=450)` y `obtener() -> list[ObraActiva] | None`.
  POST a `/api/sql/read` con la MISMA query de obras que usa sv3
  (`SELECT con.cod, obr.res ... FROM obr JOIN con ...`), cabecera
  `x-functions-key`, httpx con `HTTPTransport(retries=1)`. `max_rows=10000`
  (configuración actual de sigrid-api por petición, dato corregido por el
  humano el 2026-08-13); si llegan `max_rows` filas exactas se loguea aviso
  de posible truncado. **Filtro provisional de «obra activa» (R1-bis)**:
  tras el fetch se descartan los códigos que no sean 4 dígitos numéricos o
  cuyo valor numérico sea `<= cod_min` (`OBRAS_ACTIVAS_COD_MIN`, default
  450; con 0 el corte queda desactivado). El filtro se aplica en Python (no
  en SQL) para que retirar el corte sea un cambio de configuración, no de
  query. Ante error: loguea y devuelve `None` (nunca propaga).
- `services/albaranes-api/infrastructure/sigrid/obras_activas_cache.py` —
  capa infrastructure. `class ObrasActivasCacheTTL(ObrasActivasProvider)`
  con `__init__(provider, *, ttl_s: float, clock=time.monotonic)`. Dentro
  del TTL devuelve la copia cacheada sin llamar al provider (R3); si al
  expirar el provider devuelve `None`, sirve el valor viejo (stale) si lo
  hay. Caché en memoria por réplica (las réplicas KEDA arrancan frías: 1
  llamada por arranque + 1 por expiración; la query es barata).
- `services/albaranes-api/tests/` — `conftest.py` (vacío, ancla el
  rootdir para que `application/`, `domain/`, `infrastructure/` importen),
  `test_f002_prompt_obras.py`, `test_f002_obras_cache.py`.

### Ficheros a modificar

- `services/albaranes-api/config/settings.py` — bloque nuevo:
  `SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY`, `SIGRID_API_DATABASE`
  (opcionales, mismo esquema que sv3), `SIGRID_API_TIMEOUT_S` (30.0),
  `OBRAS_ACTIVAS_ENABLED` (true), `OBRAS_ACTIVAS_TTL_S` (21600 = 6 h),
  `OBRAS_ACTIVAS_MAX` (300, mismo tope que el grounding; SOLO controla el
  tamaño del prompt) y `OBRAS_ACTIVAS_COD_MIN` (450, corte provisional de
  «obra activa»; 0 = sin corte). Property
  `sigrid_credentials_present` como en sv3. Si `OBRAS_ACTIVAS_ENABLED=true`
  pero faltan credenciales: WARN en wiring y funcionalidad desactivada (no
  se rompe el arranque — best-effort, igual que sv3).
- `services/albaranes-api/config/prompts.yaml` — en `albaran_factura_es`:
  1. Nueva subsección en `task`, dentro de «Reglas para la cabecera», con el
     placeholder `{obras_activas}` y la regla: `obra_codigo` se elige SOLO
     de la lista; si el documento no permite identificar la obra con
     seguridad, `null`; PROHIBIDO devolver un código que no esté en la
     lista (R1).
  2. Reescritura de la regla `proveedor_nombre` (R4): razón social del
     bloque fiscal que acompaña al CIF; la marca comercial del logotipo NO
     es el proveedor (eliminar el actual «Puede venir en el logo»).
- `services/albaranes-api/application/services/albaran_extraction_service.py`
  — `__init__` acepta `obras_activas_provider: ObrasActivasProvider | None = None`.
  `extract_phase_1` renderiza el placeholder:
  `_render_obras_activas(obras) -> str` produce el bloque determinista
  (una línea `codigo — nombre` por obra, **orden ascendente por código**,
  cap `OBRAS_ACTIVAS_MAX` aplicado en wiring o en el render) o la nota
  `(Lista de obras no disponible en esta ejecución: extrae obra_codigo del
  documento como siempre.)`. Sustitución con `str.replace`; si el YAML
  desplegado no tiene `{obras_activas}` y hay lista, el bloque se APPENDEA
  al final del task (mismo patrón de compatibilidad que `{sigrid_context}`
  en fase 2). La llamada a `provider.obtener()` va en try/except → None
  (R2, R16).
- `services/albaranes-api/interface_adapters/composition.py` y
  `interface_adapters/api/app.py` — wiring: si settings lo permiten,
  `ObrasActivasCacheTTL(SigridApiObrasClient(...), ttl_s=...)` inyectado en
  `AlbaranExtractionService`. (main_worker.py no cambia: usa
  `build_pipeline`.)

### Por qué sv2 llama a sigrid-api directamente (decisión D1)

Alternativas evaluadas:

1. **HTTP a sv3** (reutilizar su `/v1/sigrid/header-grounding` o un endpoint
   nuevo): descartada — en Azure `ca-sv3-persistencia` es un worker KEDA
   **sin ingress**; sv2 no puede llamarle.
2. **Caché en Blob mantenida por sv3**: descartada — sv3 corre DESPUÉS de
   sv2 en la cadena (arranque frío sin lista), no hay timer que la refresque
   y añade un artefacto compartido más.
3. **Cliente sigrid-api propio en sv2 + caché TTL en memoria** (elegida):
   respeta «Sigrid SOLO lectura vía sigrid-api», una llamada por
   réplica/TTL, degradación limpia a None.

Consecuencias de D1 (las ejecuta el implementer, las aplica el humano en
Azure): `ca-sv2-extraccion` necesita `SIGRID_API_BASE_URL`,
`SIGRID_API_DATABASE` y el secret `SIGRID_API_FUNCTION_KEY` (referencia Key
Vault, ya existe para sv3); y el documento `azure-apps/albaranes.md` debe
actualizarse en el mismo trabajo (sv2 pasa a consumir sigrid-api).

## sv3 — redes deterministas

### Ficheros a crear

- `services/albaranes-persistencia/application/services/fecha_guard_service.py`
  — capa application. `class FechaGuardService` con
  `__init__(*, repository, enabled: bool = True, max_dias: int = 365)` y
  `check_merge_document(*, merge_document_id: str) -> None`. Lee
  `(fecha, email_received_datetime)` del merge; parsea `fecha` con
  `date.fromisoformat` (no parseable/nula → no-op, R15); referencia =
  `email_received_datetime` parseado o `now(UTC)` si falta (R14); si
  `abs(delta) > max_dias` → `repository.marcar_revision_cabecera(...)` con
  motivo `fecha_albaran_fuera_de_rango:<fecha>` y nota `[AVISO] Fecha ...`
  (R13). Best-effort completo.
- `services/albaranes-persistencia/interface_adapters/worker/workflow_context_adapter.py`
  — `class FuenteContextoEmailWorkflows` que implementa el puerto nuevo
  `FuenteContextoEmail` usando
  `ruesma_comun.workflows.RepositorioWorkflows.obtener_por_correlation_key`:
  parsea `payload_json` y devuelve el dict de contexto con las claves que ya
  espera el repositorio de sv3 (`_build_document`):
  `{"email": {"id", "subject", "sender", "receivedDateTime"},
    "document": {"source_attachment_filename", "source_attachment_mime_type",
    "source_attachment_sha256", "page_number", "page_count"}}`
  mapeando `email_message_id→id`, `from_address→sender`,
  `email_received_at_utc→receivedDateTime`, `subject→subject`,
  `attachment_content_type→source_attachment_mime_type`,
  `total_pages→page_count`. Fila ausente o payload roto → `{}` (R12 solo
  aplica si hay fila). **`ruesma_comun` NO se toca** (tocarlo obliga a
  reconstruir 4 imágenes): se usa su API pública tal cual.
- `services/albaranes-persistencia/tests/` — `conftest.py`,
  `test_f002_red_obra.py`, `test_f002_red_proveedor.py`,
  `test_f002_fecha_guard.py`, `test_f002_contexto_email_worker.py`.

### Ficheros a modificar

- `services/albaranes-persistencia/domain/ports/obra_merge_repository_port.py`
  — añadir al Protocol:
  `descartar_obra_no_valida(*, document_id, codigo_leido, motivo) -> None` y
  `retirar_revision_obra(*, document_id) -> None`.
- `services/albaranes-persistencia/domain/ports/header_resolver_ports.py` —
  `ProveedorReverseLookupClient` += `fetch_proveedor_by_cif(*, cif) ->
  tuple[str, str | None] | None` (el adaptador real ya lo tiene);
  `HeaderMergeRepository` +=
  `set_merge_proveedor_nombre_canonico(*, document_id, nombre) -> None` y
  `marcar_revision_cabecera(*, document_id, motivo, nota, nota_prefijo) -> None`.
- `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py`
  — implementar los métodos nuevos:
  - `marcar_revision_cabecera`: `review_required=true` + append idempotente
    del motivo a `review_reasons_json` (lista JSON; no duplicar el mismo
    motivo) + `append_review_note` con dedupe por prefijo (reutiliza
    `remove_review_note_prefix` + `append_review_note` existentes).
  - `descartar_obra_no_valida`: en una transacción, `obra_codigo=NULL`,
    `obra_codigo_origen=NULL` y marca de revisión (motivo + nota
    `[AVISO] Obra`). NO borra `obra_nombre`/`obra_direccion` leídos (ayudan
    al revisor).
  - `retirar_revision_obra`: quita nota `[AVISO] Obra` y motivos `obra_*` de
    `review_reasons_json` (R7). `review_required` NO se recalcula a false
    (puede haber otros motivos; lo cierra el revisor al aprobar — decisión D7).
  - `get_merge_fechas_para_guard(*, document_id) -> tuple[str | None, str | None]`
    (fecha, email_received_datetime).
- `services/albaranes-persistencia/application/services/obra_enrichment_service.py`
  — red de obra (R5–R7): donde hoy el `not found` solo loguea
  (`Sigrid devolvió 0 filas útiles`), llamar a
  `repository.descartar_obra_no_valida(...)` con motivo
  `obra_inexistente:<codigo>`; donde la normalización falla con código NO
  nulo, ídem con `obra_codigo_invalido:<valor>`; cuando la obra valida,
  llamar a `retirar_revision_obra` (además del update de nombre/dirección
  actual). Flag `enabled_red` (settings `RED_OBRA_ENABLED`) para poder
  volver al comportamiento previo (R17).
- `services/albaranes-persistencia/application/services/header_resolver_service.py`
  — red de proveedor (R8–R11) en `_resolve_proveedor`, rama
  `if (proveedor_cif or "").strip():` (hoy hace return inmediato):
  1. `fetch_proveedor_by_cif(cif_limpio)`; encontrado → `repository.
     set_merge_proveedor_nombre_canonico(...)` con `prv.raz` (R8), retirar
     aviso previo, return.
  2. No encontrado → candidatos `fetch_contratos_resumen_por_obra(obra
     efectiva)`; si el mejor `_match_score` de nombre >= `min_score` →
     `marcar_revision_cabecera` con motivo `proveedor_cif_no_casa:<cif>` y
     nota-propuesta `[AVISO] Proveedor` con CIF + razón social del candidato
     (R9). Si no hay candidato que case (o no hay obra efectiva) → misma
     marca sin propuesta (R10). En ningún caso se sobrescriben
     `proveedor_cif`/`proveedor_nombre` leídos (decisión D3).
  3. Sin CIF → flujo actual intacto (R11). Flag `RED_PROVEEDOR_CIF_ENABLED`.
- `services/albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py`
  — nuevo colaborador opcional `fecha_guard_service` y paso best-effort
  `_check_fecha_guard_safely(...)` tras `_enrich_obra_safely` en las tres
  rutas (run normal, duplicado, `reenrich_by_merge_id`).
- `services/albaranes-persistencia/interface_adapters/worker/ports.py` —
  puerto `FuenteContextoEmail` (`obtener(correlation_key) -> dict`).
- `services/albaranes-persistencia/interface_adapters/worker/persistence_worker.py`
  — `construir_handler_persistencia` acepta
  `fuente_contexto: FuenteContextoEmail | None`; el handler fusiona el dict
  devuelto con `{"correlation_key": ...}` (R12). Best-effort.
- `services/albaranes-persistencia/main_worker.py` — construir
  `FuenteContextoEmailWorkflows` con un `SessionFactory` propio (misma
  `settings.database_url`; segundo engine asumido, patrón ya usado por sv1)
  y pasarla al handler.
- `services/albaranes-persistencia/interface_adapters/composition.py` —
  wiring de `FechaGuardService` y de los flags nuevos.
- `services/albaranes-persistencia/config/settings.py` — `RED_OBRA_ENABLED`
  (true), `RED_PROVEEDOR_CIF_ENABLED` (true), `FECHA_GUARD_ENABLED` (true),
  `FECHA_GUARD_MAX_DIAS` (365).

## Ficheros que NO se tocan (colindantes que tentarían)

- `services/albaranes-comun/**` (`ruesma_comun`): se usa su API tal cual.
  Tocarlo = reconstruir sv2, sv3, sv5 y sv6.
- `application/services/albaran_confidence_service.py` (sv3): el scoring del
  merge no cambia; las redes actúan DESPUÉS del merge.
- `application/services/header_grounding_service.py` y el endpoint
  `POST /v1/sigrid/header-grounding` (sv3): camino HTTP del difunto sv7; ni
  se reactiva ni se borra en esta feature.
- Prompts de fase 2 (`albaran_revision_fase2_*`) y
  `config/revision_rules.yaml` de sv2.
- sv4, sv5, sv6, sv1: cero cambios.
- Schema de BBDD: sin DDL nuevo (columnas existentes bastan).

## SQL

No hay ficheros `.sql` (convención del repo: DDL inline idempotente). Esta
feature NO añade columnas ni tablas. Escrituras nuevas sobre
`albaran_documents_merge` (dueño: sv3, servicio correcto): `obra_codigo`,
`obra_codigo_origen`, `proveedor_nombre`, `review_required`,
`review_reasons_json`, `review_notes`. Lectores acoplados avisados: sv5 lee
el merge con SQL crudo pero NO lee ninguna de estas columnas de revisión
(sin riesgo de rename: no se renombra nada); sv4 ya muestra
`review_notes`/`review_required`.

## Riesgos y decisiones

- **D1** (sv2 → sigrid-api directo): ver sección sv2. **ACEPTADA por el
  humano (2026-08-13).** Requiere secret nuevo en `ca-sv2-extraccion` y
  actualización de `azure-apps/albaranes.md` (tareas T9/T10).
- **D2 — criterio de «obra activa» PROVISIONAL (2026-08-13)**: el criterio
  de negocio queda PENDIENTE de definir. Regla provisional confirmada por el
  humano para arrancar: solo obras con código de 4 dígitos numéricos y
  mayor que 0450, implementada como filtro configurable
  (`OBRAS_ACTIVAS_COD_MIN`, R1-bis). El corte `>0450` se retirará (poniendo
  el valor a 0 o sustituyéndolo por el filtro real) cuando negocio defina
  «obra activa». `OBRAS_ACTIVAS_MAX` es independiente: solo controla el
  tamaño del prompt.
- **D3** — la red de proveedor con CIF que no casa PROPONE y marca revisión;
  no sobrescribe (lo decide el humano en sv4). Coherente con §10.1.
- **D4** — la canonicalización por CIF (R8) SÍ sobrescribe
  `proveedor_nombre` (dato determinista del maestro, no una conjetura). El
  literal leído queda en las tablas raw.
- **D5** — guard de año sin fecha de email: referencia = now(UTC) (R14).
- **D6** — límite de filas de sigrid-api: dato CORREGIDO por el humano
  (2026-08-13): la configuración actual de sigrid-api es de **10.000 filas
  por petición** (no 1.000 como decía `docs/ARCHITECTURE.md`). La lista de
  obras se pide en UNA petición con `max_rows=10000`; si llegan `max_rows`
  filas exactas se avisa de posible truncado. `OBRAS_ACTIVAS_MAX` se
  mantiene únicamente como control del tamaño del prompt.
- **D7** — `retirar_revision_obra` limpia nota+motivos pero no baja
  `review_required`: puede haber otros motivos vivos y el cierre es del
  revisor.
- **Riesgo** — crear `tests/` en sv2 y sv3 activa la sección 7 bis de
  `harness/init.sh` para esos servicios: sus venvs deben tener `pytest`
  (comprobarlo en la primera tarea de tests; si falta, instalarlo en el venv
  del servicio, no en requirements de producción).
- **Riesgo** — tamaño del prompt IA1: ~300 líneas cortas de obras ≈ pocos
  miles de tokens; asumible. `OBRAS_ACTIVAS_MAX` permite recortar sin
  redeploy de código.
- **Riesgo** — los métodos nuevos de repositorio no se pueden probar sin
  BBDD: se validan por revisión de código + verificación MANUAL del humano
  contra el entorno local (ver tasks). Los servicios se testean con fakes.
- **Compatibilidad F-011**: el bloque de obras es determinista (orden y
  formato fijos) y la regla de salida de IA1 no cambia de schema
  (`documento_albaran`): las evals de ground truth podrán fijar la lista de
  obras como fixture.

## Límite de microservicio

Dentro del límite: sv2 solo toca SU prompt y una consulta de solo lectura;
sv3 solo toca la identificación del documento que ya le pertenece (dueño del
merge). Nada de esto pertenece a otro servicio ni merece servicio propio.

## Decisiones tomadas (2026-08-13, respondidas por el humano)

Ninguna pregunta queda abierta.

- **P1 → resuelta (provisional).** El criterio de negocio de «obra activa»
  queda pendiente de definir por negocio; mientras tanto rige la regla
  provisional confirmada: **solo obras con código de 4 dígitos numéricos y
  mayor que 0450**, implementada como filtro configurable
  (`OBRAS_ACTIVAS_COD_MIN`, default 450; 0 = sin corte). Ver R1-bis y D2.
  El corte se retirará cuando negocio defina el criterio real.
- **P2 → resuelta (corrección de dato).** sigrid-api está configurado a
  **10.000 filas por petición**, no 1.000. Actualizado D6 y el cliente
  (`max_rows=10000`). `OBRAS_ACTIVAS_MAX` se mantiene solo como control del
  tamaño del prompt. (T12 sigue anotando el nº real de obras devueltas,
  como dato operativo, no como decisión pendiente.)
- **P3 → resuelta.** Aceptado reutilizar `HEADER_RESOLVER_MIN_SCORE` (0.5)
  como umbral de la propuesta de proveedor (R9); retocable por
  configuración si los datos reales lo piden.
- **D1 → aceptada.** sv2 llama a sigrid-api directamente. La actualización
  de `azure-apps/albaranes.md` y el secret nuevo de `ca-sv2-extraccion`
  forman parte de la feature (T9/T10).
