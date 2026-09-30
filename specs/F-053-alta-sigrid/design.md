<!-- specs/F-053-alta-sigrid/design.md -->
# F-053 · Alta en Sigrid de los albaranes aprobados · Diseño

Requisitos: `requirements.md`. Preguntas abiertas: `progress/spec_F-053.md`.

## 1. Encaje y límite de servicio

Responsabilidad **nueva** (escribir en el ERP): no cabe en ningún servicio
actual. Se propone un **servicio nuevo del monorepo, sv9**
(`services/albaranes-alta-sigrid`, Container App `ca-sv9-alta-sigrid`), solo
worker, hexagonal como sv6. **Lo confirma el humano en la PARADA 1**
(alternativa: proyecto aparte; pregunta 1). Nombre: `sv7` era el orquestador
retirado (comentarios de sv4 y `ruesma_comun.workflows`) y `sv8` está
reservado al aprendizaje (`ca-sv8-aprendizaje` en el docstring de
`MensajeFeedback`); `sv9` no aparece en el repositorio.

Flujo: sv4 aprueba → `q-feedback` (`MensajeFeedback`, ya existe) → sv9 →
sigrid-api (`sql/read`, `sigrid/albaran`, `sigrid/concepto-grafico`) →
`albaran_altas_sigrid` ← sv4 la lee. Se consume `q-feedback` porque
`docs/ARCHITECTURE.md` (normativo) la reserva para esto; si algún día hay
servicio de aprendizaje, necesitará su propia cola (pregunta 2).

## 2. Lo que sigrid-api permite hoy (leído en su código, `dev` 2a5ac24)

`sigrid-api` (git, sep 2026) es el vigente; `sigrid-api-v2` es una copia de
julio sin git. Modelos: `domain/models/albaran_domain_models.py` y
`albaran_directo_models.py`; lógica: `application/use_cases/create_*albaran*`.

- `sigrid/albaran`: `{database, cod_contrato, cod_obra, cif_proveedor,
  su_referencia (→ dca.entref, 128 en Sigrid), fecha_albaran (AAAAMMDD),
  lineas_recibidas: [{ctrpro_ide, cantidad ≥ 0}], empide?, commit}`. Precio,
  partida (`paride`), almacén y cuenta salen de la **línea de contrato**: no hay
  override de precio ni de partida. Solo incluye las líneas pedidas (el
  docstring de la ruta dice «todas»: manda el código, y R17 lo vigila).
- Errores: `ValueError` → 400 con texto libre (sin códigos); lo inesperado → 500.
  La grabación va en una transacción; los 400 de datos salen antes de escribir.
- **Sin idempotencia** (roadmap 1 de `sigrid_api.md` §13): nada impide dar dos
  veces el mismo albarán. `dca.synckey` existe pero el endpoint no lo usa.
  Por eso R14/R15 buscan por `entcif` + `entref` (índice `entref` en `dca`).
- `sigrid/albaran-directo` exige `proide` (producto de Sigrid) por línea: el
  pipeline no lo tiene. **Fuera de v1** (pregunta 4).
- `sigrid/concepto-grafico`: idempotente por `sha256`; éxito = `ok &&
  (committed || idempotente)`; `usu` debe existir en `dbo.usu`.

Consecuencia: v1 registra solo albaranes **íntegramente dentro de un contrato**
(cada línea con cantidad casa con un `ctrpro` del contrato de la valoración, con
su misma partida). El resto queda `no_admitido` con motivo y se da de alta a
mano. Ampliarlo exige cambios en sigrid-api (otro repositorio): pregunta 4.

## 3. Ficheros a crear

sv9, `services/albaranes-alta-sigrid/` (estructura de sv6; primera línea de
cada fichero, su ruta):
- `main_worker.py` — `ejecutar_worker` de `ruesma_comun.colas.arranque` sobre
  `COLA_FEEDBACK`; log de arranque con el modo en claro.
- `Dockerfile`, `requirements.txt`, `sv9.md`, `.env.example` (sin valores).
- `config/settings.py` (§7), `config/logging_config.py` (copia del patrón sv6).
- `domain/models/alta_models.py` — `EstadoAlta` (StrEnum de los 9 estados),
  `CabeceraAlta`, `LineaAlta`, `DatosAlta` (lo leído de BBDD), `PeticionAlbaran`,
  `LineaRecibida`, `Motivo(codigo, detalle)`, `ResultadoAlta`.
- `domain/ports/alta_repository.py` — `AltaRepository` (ABC): `reclamar(document_id,
  ahora, desde, espera) -> Reclamacion`, `leer_datos(document_id) -> DatosAlta`,
  `guardar(document_id, resultado)`, `leer_alta(document_id)`.
- `domain/ports/sigrid_alta_port.py` — `SigridAltaPort` (ABC): `buscar_albaranes
  (cif, referencia) -> list[AlbaranSigrid]`, `existe_concepto(ide) -> bool`,
  `alta_albaran(peticion, commit) -> RespuestaSigrid`, `adjuntar_pdf(...)`.
  Solo esas cuatro operaciones (R33).
- `domain/ports/pdf_port.py` — `PdfAlbaranPort.descargar(datos) -> bytes`.
- `domain/services/validador_alta.py` — puro: `validar_y_construir(datos, empide)
  -> PeticionAlbaran | list[Motivo]` (R10–R13).
- `domain/services/comparador_previa.py` — puro: `comparar(peticion, datos,
  respuesta, tolerancia_eur, avisos_bloqueantes) -> list[Motivo]` (R17).
- `domain/services/clasificador.py` — puro: resultado HTTP de la grabación →
  estado (R18, R20, R21); tiempo agotado y 5xx → `incierto`.
- `application/alta_sigrid_service.py` — `AltaSigridService.procesar(mensaje)`:
  orquesta §5; única clase que conoce el modo.
- `infrastructure/database/sql_alta_repository.py` — SQL con `text()` de
  SQLAlchemy y `ruesma_comun.db`.
- `infrastructure/sigrid/sigrid_api_alta_client.py` — httpx + tenacity (R24);
  la grabación usa un cliente sin reintentos y `timeout` 240 s (> 230 s del balanceador).
- `infrastructure/sharepoint/pdf_sharepoint.py` — baja el PDF con
  `ruesma_comun.sharepoint.GraphSharePointClient` por `sharepoint_relative_path`.
- `interface_adapters/composition.py`, `interface_adapters/worker/alta_worker.py`
  — traduce el mensaje y llama al servicio; los resultados de negocio confirman
  el mensaje; solo una excepción de infraestructura antes de R5 lo reencola.
- `tests/` — fakes de los tres puertos; nada de red ni BBDD.

sv4: `templates/_alta_sigrid.html` (panel de la ficha, R29–R30).

## 4. Ficheros a modificar

- `services/albaranes-comun/ruesma_comun/colas/mensajes.py` — `MensajeFeedback.
  accion: Literal["alta","verificar_anulacion"] = "alta"`; docstring: consumidor
  sv9. Cambiar comun obliga a reconstruir todas las imágenes (ARCHITECTURE).
- `services/albaranes-persistencia/infrastructure/database/schema_contribution.py`
  — `CREATE TABLE IF NOT EXISTS albaran_altas_sigrid` (§6).
- `services/albaranes-front/config/settings.py` — `ALTA_SIGRID_DESDE_UTC`,
  `ALTA_SIGRID_ESPERA_INCIERTO_MIN`.
- `.../albaranes-front/domain/ports/orchestrator_port.py` y
  `infrastructure/colas/colas_orchestrator_client.py` — `notify_document_approved`
  pasa a devolver si publicó; nuevo `solicitar_alta_sigrid(document_id, accion)`.
- `.../albaranes-front/application/services/review_service.py` — recibe el
  cliente de colas y la configuración; publica en el paso a aprobado (R1–R4);
  traduce `AlbaranBloqueadoError` en las operaciones de R25.
- `.../albaranes-front/infrastructure/database/review_repository.py` —
  `leer_alta_sigrid(document_id)`, `es_aprobado(document_id)` y
  `_exigir_desbloqueado(session, document_id)`: `SELECT ... FROM
  albaran_documents_merge m LEFT JOIN albaran_altas_sigrid a ... FOR UPDATE OF m`;
  la llaman al empezar, en su sesión, `update_document`, `set_approved(False)`,
  `soft_delete_document`, purga, restaurar del deshacer y los métodos de
  conciliación y alta de líneas (R26). Si la tabla no existe, no hay alta.
- `.../albaranes-front/interface_adapters/web/app.py` — 409 (API) o redirección
  con mensaje (formularios) para R25; saltos de R27; rutas nuevas `POST
  /documents/{id}/alta-sigrid/solicitar` y `/alta-sigrid/verificar-anulacion`;
  revalorar y re-buscar contratos consultan el alta antes de publicar.
- `.../templates/document_detail.html` (incluye el panel),
  `documents_list.html` (estado en la columna Aprobado, R31).
- `harness/servicios.json` — `sv9-alta-sigrid`.
- `infra/` — sv9 en `$APPS` de `deploy.ps1`/`build_images.ps1` y su
  `create_capps*.ps1`: escalado KEDA sobre `q-feedback` con **máximo 1 réplica**,
  secreto `SIGRID_API_FUNCTION_KEY` desde Key Vault. Redactado como los demás.
- `docs/ARCHITECTURE.md` — fila sv9, `q-feedback` con consumidor, tabla nueva,
  y la regla de acceso a Sigrid (§9). `azure-apps/albaranes.md` en el mismo trabajo.

## 5. Flujo de sv9 (`AltaSigridService.procesar`)

1. `reclamar` (R5–R8), una transacción: `SELECT ... FROM albaran_documents_merge
   WHERE id = :id FOR UPDATE`; lee el alta; decide `ignorar` / `solo_adjunto` /
   `a_incierto` / `procesar` / `verificar_anulacion`; si procesa, UPSERT del alta a
   `en_curso` con `ultimo_intento_at_utc = ahora`.
2. `verificar_anulacion` (R28): `existe_concepto(sigrid_con_ide)` → `anulado` o aviso.
3. `leer_datos` y `validar_y_construir` → `no_admitido` si hay motivos (R10–R13).
4. `buscar_albaranes(cif, referencia)` → `ya_en_sigrid`, o `registrado` si
   venía de `incierto` con un único resultado (R14–R15).
5. Previa (`commit=false`) → 400 = `error`; `comparar` → `revisar` (R16–R18).
6. Simulación → `simulado` (R19). Real → grabación única (R20–R21).
7. Adjunto (R22–R23). Todo el cuerpo va en `try/finally` para R9.

Cada paso guarda `peticion_json`, `respuesta_json`, `motivos_json` y añade una
entrada `{ts, estado, cod, motivos}` a `historial_json`.

## 6. SQL (DDL en sv3, dueño del schema; sin ficheros `.sql`: DDL inline)

```sql
CREATE TABLE IF NOT EXISTS albaran_altas_sigrid (
  document_id VARCHAR(36) PRIMARY KEY
    REFERENCES albaran_documents_merge(id) ON DELETE CASCADE,
  estado VARCHAR(24) NOT NULL, modo VARCHAR(12),
  sigrid_con_ide INTEGER, sigrid_cod VARCHAR(24),
  adjunto_estado VARCHAR(16), sigrid_gra_ide INTEGER,
  motivos_json TEXT, avisos_json TEXT, peticion_json TEXT, respuesta_json TEXT,
  historial_json TEXT, intentos INTEGER NOT NULL DEFAULT 0,
  approved_at_utc VARCHAR(64), approved_by VARCHAR(255),
  ultimo_intento_at_utc VARCHAR(64), creado_at_utc VARCHAR(64) NOT NULL,
  actualizado_at_utc VARCHAR(64));
CREATE INDEX IF NOT EXISTS ix_albaran_altas_sigrid_estado ON albaran_altas_sigrid (estado);
```

Tabla aparte y no columnas del merge: el deshacer de sv4 restaura instantáneas
de la fila del merge y devolvería un alta a un estado viejo. Fechas como
`VARCHAR(64)` ISO, igual que el resto del esquema. Lectores: sv4 (leer) y sv9
(escribir). sv5 no la lee. Lecturas de sv9: merge, `albaran_valuations`
(`status`, `contrato_codigo`), `albaran_line_valuations` (`cantidad_albaran`,
`cantidad_convertida`, `importe_calculado`, `matched_contrato_line_id`,
`derived_contrato_line_id`, `codigo_partida_final`, `partida_action`) y
`albaran_contrato_lines_merge` (`sigrid_ide`, `codigo_partida`, contrato).

Consulta de duplicados (R14), vía `sql/read`, parametrizada:
`SELECT c.ide, c.cod, c.fec FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide
WHERE c.tip = 14 AND d.entcif = ? AND d.entref = ?`. `existe_concepto`:
`SELECT ide FROM dbo.con WHERE ide = ? AND tip = 14`.

## 7. Configuración

sv9: `ALTA_SIGRID_DESDE_UTC` (vacía = no hace nada), `ALTA_SIGRID_COMMIT`
(defecto `false`; solo lo cambia el humano), `ALTA_SIGRID_ESPERA_INCIERTO_MIN`
(15), `ALTA_SIGRID_TOLERANCIA_EUR` (0,05), `ALTA_SIGRID_AVISOS_BLOQUEANTES`
(lista; defecto «plantilla de cabecera no es del mismo proveedor» y «sin
historico de dcapro»), `ALTA_SIGRID_USUARIO`, `ALTA_SIGRID_EMPIDE` (opcional),
`SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY` (secreto), `SIGRID_API_DATABASE`
(`ruesma`), `PG_*`, Graph/SharePoint y colas, con los nombres de sv3/sv6.
sv4: `ALTA_SIGRID_DESDE_UTC` y `ALTA_SIGRID_ESPERA_INCIERTO_MIN`, **con el mismo
valor que sv9** (lo fija el script de despliegue desde una sola variable).
En local, `ALTA_SIGRID_COMMIT` no se pone nunca (regla de solo lectura).

## 8. Orden y dependencias

**F-052 → F-051 → F-053.** F-052 garantiza el CIF correcto (sin él, la
petición localiza mal el contrato o `ya_en_sigrid` busca con otro CIF). F-051
fija la semántica de almacén que usa R11 (partida vacía + marca en
`partida_action`); su ruta nueva de sv4 (`asignar_almacen`) entra en R25 al
fusionar. F-053 se puede implementar en su rama a la vez, pero se fusiona
después de las dos, y el modo `real` no se enciende hasta que las tres estén en
producción. F-006 (`no_registrar_sigrid`) y F-015 (tachadas) no están hechas:
cuando lleguen, sus líneas se excluyen en R13 (pregunta 12).
Despliegue: sv3 (tabla) → sv9 (con DESDE vacía) → sv4 → DESDE en ambos
(simulación) → días de simulación → `ALTA_SIGRID_COMMIT=true` (humano).

## 9. Reglas del repo y documentación (propuesta; NO se aplica aquí)

`CLAUDE.md`, regla dura de Sigrid, redacción propuesta: «Sigrid (ERP) solo se
consulta vía sigrid-api, nunca por SQL directo. Leer: cualquier servicio.
Escribir: **solo sv9**, solo con `sigrid/albaran` y `sigrid/concepto-grafico`,
nunca `sql/write`, y solo con `ALTA_SIGRID_COMMIT=true`, que activa el humano.
Desde local, nunca se escribe.» Mismo cambio en `docs/ARCHITECTURE.md`
(«Acceso a datos»), en la línea de `q-feedback` y en
`docs/referencia/dominio_negocio_albaranes.md` §5.2 (hablaba de `sql/write`).
`azure-apps/albaranes.md`: sv9, la tabla y el consumo de sigrid-api. La fila de
consumidores de `azure-apps/sigrid_api.md` §10 es del proyecto sigrid-api: se
propone, no se edita (pregunta 15). Si el cambio de regla vale para otros
proyectos, se porta a `arnes-base` en el mismo trabajo.

## 10. Ficheros que NO se tocan

- `sigrid-api` (decisión del humano) ni su configuración en Azure.
- sv1, sv2, sv5; sv6 (su valoración se lee, no se cambia).
- `albaran_documents_merge` y tablas de sv6: ninguna columna nueva.
- `ruesma_comun.importes`, `familias`, `origen_datos`.
- `infra/*.local.ps1`, `.env`: nada de IDs, claves ni URLs reales.

## 11. Riesgos y decisiones

- **Doble alta**: sin idempotencia en sigrid-api. Defensas: reclamación con
  `FOR UPDATE` y estados; una sola réplica; grabación sin reintento; `incierto`
  no se retoma antes de la Espera (la Function sigue viva tras el corte de
  230 s); búsqueda por CIF + referencia antes de la previa y al retomar. Queda
  un hueco si Sigrid tarda más que la Espera en terminar: la pregunta 4 propone
  `referencia_externa` → `dca.synckey` con idempotencia en sigrid-api.
- **Falsos duplicados**: un proveedor que repite número bloquea el alta
  (`ya_en_sigrid`, visible). Preferible a duplicar en el ERP.
- **Lo que no se puede expresar hoy** (precio, partida, líneas sin contrato,
  devoluciones) va a `no_admitido`/`revisar`; nunca se graba aproximado.
- **Clave de sigrid-api**: con la escritura abierta, cualquiera que tenga la
  clave por defecto puede escribir (sv2, sv3 y sv4 ya la tienen). Pregunta 16.
- **Carrera sv4 ↔ sv9**: ambos bloquean la fila del merge; las operaciones que
  solo publican (revalorar, re-buscar) comprueban sin cerrojo: la instantánea
  que se envía es la de `peticion_json`, y la revisión posterior la detecta.
- Descartado: validar al aprobar y bloquear la aprobación (pregunta 5);
  guardar el estado en el merge (deshacer); `sql/write` (decisión del humano).
- Verificación con BBDD real, Azurite y sigrid-api: manual del humano (tasks).
