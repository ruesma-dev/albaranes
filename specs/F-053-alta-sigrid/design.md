<!-- specs/F-053-alta-sigrid/design.md -->
# F-053 · Alta en Sigrid de los albaranes aprobados · Diseño

Requisitos: `requirements.md`. Preguntas abiertas: `progress/spec_F-053.md`.

## 1. Encaje, límite de servicio y precondiciones

Responsabilidad **nueva** (escribir en el ERP): **servicio nuevo sv9**
(`services/albaranes-alta-sigrid`, `ca-sv9-alta-sigrid`), solo worker, hexagonal
como sv6 (pregunta 1). `sv7` = orquestador retirado, `sv8` = aprendizaje
(docstring de `MensajeFeedback`). Flujo: sv4 aprueba → `q-feedback` (reservada
para esto en `docs/ARCHITECTURE.md`) → sv9 → sigrid-api → `albaran_altas_sigrid`
← sv4 la lee (pregunta 2).

**Precondiciones (humano, 2026-10-01)** para `in_progress`: (1) la **medición**
(`services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py`, solo
lectura, la ejecuta el humano; comando en `progress/spec_F-053.md`); (2) **PRE-1**
desplegada en sigrid-api (§2). Producto: «de momento siempre va a ser suministro
de materiales» ⇒ sin vincular, `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` = `MA9999`;
elegir entre MA9999/SM9999/SB9999/QA9999 por familia es mejora futura.

## 2. sigrid-api: lo que hay hoy y lo que hace falta (PRE-1)

Leído en `sigrid-api` (git, `dev` 2a5ac24; `sigrid-api-v2` es una copia de julio
sin git): `domain/models/albaran_*models.py`, `application/use_cases/create_*albaran*`.

- `sigrid/albaran`: `{database, cod_contrato, cod_obra, cif_proveedor,
  su_referencia (→ dca.entref, 128), fecha_albaran, lineas_recibidas:
  [{ctrpro_ide, cantidad ≥ 0}], empide?, commit}`. Precio, partida (`paride`),
  almacén y cuenta salen del `ctrpro`: sin override, y solo líneas de contrato.
- `sigrid/albaran-directo`: exige `proide` de Sigrid por línea (el pipeline no
  lo tiene), no vincula con contrato, y con `paride` nulo **hereda** el de la
  última `dcapro` del producto (convertiría almacén en partida ajena).
- Ninguno es idempotente (`dca.synckey` sin usar); 400 con texto libre, 500 lo
  inesperado. `concepto-grafico`: idempotente por `sha256`, `usu` en `dbo.usu`.

**El criterio del humano no se puede expresar hoy** (vinculadas y sin vincular
en un albarán, partida por línea, almacén explícito, negativas). F-053 depende
de **PRE-1**, feature del repositorio sigrid-api (allí el siguiente id libre es
F-009). Lo que necesita (ampliación compatible de `sigrid/albaran` o ruta nueva):
- `cod_contrato` opcional (obligatorio si hay `lineas_recibidas`).
- `referencia_externa` (≤128) → `dca.synckey`, con idempotencia como
  `partes-reclamacion`: misma `emp` y referencia ⇒ `idempotente` con su `ide`/`cod`,
  comprobado también dentro de la transacción, bajo applock.
- En cada línea: `referencia_linea` (se devuelve) y `partida` (código, resuelto
  contra las partidas de la obra) **o** `almacen: true` (`paride` 0), nunca heredado.
- `lineas_recibidas[]` (vinculadas: producto, precio y cuenta del `ctrpro`, y
  **consumen medición**: `canser`, `ctrprodes`, `estser`) más lo anterior; varias
  pueden ir al mismo `ctrpro`. `lineas_sin_contrato[]`: `{producto (CÓDIGO de
  Sigrid, p. ej. MA9999, resuelto a su `proide`), descripcion, unidad, cantidad,
  precio}` → `dcapro` sin `docori*` ni `canser`. Cuenta/IVA/naturaleza del
  producto genérico: de su maestro o de su última `dcapro` (roadmap 2 de sigrid-api).
- **Cantidades negativas** (devoluciones, humano 2026-10-01) en los dos tipos.
  PRE-1 debe **medir y replicar** al escritorio de Sigrid (`dcapro` reales con
  `can < 0` y sus `mov`): el stock baja; el PMP hoy se recalcula con `canent·pre`
  y con `canent < 0` se movería (¿lo recalcula Sigrid o sale al PMP vigente?);
  en vinculadas `canser += can` (baja) y se recalculan `estser/estfac`.
- Respuesta por línea con `referencia_linea`, partida aplicada, `precio` y `total`;
  errores con código (`partida_no_encontrada`, `producto_no_encontrado`,
  `colision_de_clave`…). Dry-run por defecto.

## 3. Ficheros a crear

sv9, `services/albaranes-alta-sigrid/` (estructura de sv6; primera línea de
cada fichero, su ruta):
- `main_worker.py` (`ejecutar_worker` sobre `COLA_FEEDBACK`; log del modo),
  `Dockerfile`, `requirements.txt`, `sv9.md`, `.env.example` sin valores,
  `config/settings.py` (§7) y `config/logging_config.py` (patrón sv6).
- `domain/models/alta_models.py` — `EstadoAlta` (StrEnum de los 9 estados),
  `CabeceraAlta`, `LineaAlta`, `DatosAlta` (lo leído de BBDD), `PeticionAlbaran`,
  `LineaRecibida`, `Motivo(codigo, detalle)`, `ResultadoAlta`.
- `domain/ports/alta_repository.py` — `AltaRepository` (ABC): `reclamar(document_id,
  ahora, desde, espera) -> Reclamacion`, `leer_datos(document_id) -> DatosAlta`,
  `guardar(document_id, resultado)`, `leer_alta(document_id)`.
- `domain/ports/sigrid_alta_port.py` — `SigridAltaPort` (ABC): `buscar_albaranes
  (cif, referencia) -> list[AlbaranSigrid]`, `existe_concepto(ide) -> bool`,
  `alta_albaran(peticion, commit) -> RespuestaSigrid` (PRE-1), `adjuntar_pdf(...)`.
  Solo esas cuatro operaciones (R33).
- `domain/ports/pdf_port.py` — `PdfAlbaranPort.descargar(datos) -> bytes`.
- `domain/services/validador_alta.py` — puro: `validar_y_construir(datos, empide,
  producto) -> PeticionAlbaran | list[Motivo]` (R10–R13).
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
  traduce `AlbaranBloqueadoError` (R25) y rechaza aprobar sin valoración `ok`
  (`AlbaranSinValorarError`, R37) en `approve_document` y `save_document`.
- `.../albaranes-front/infrastructure/database/review_repository.py` —
  `leer_alta_sigrid(document_id)`, `es_aprobado`, `estado_valoracion` y
  `_exigir_desbloqueado(session, document_id)`: `SELECT ... FROM
  albaran_documents_merge m LEFT JOIN albaran_altas_sigrid a ... FOR UPDATE OF m`;
  la llaman al empezar, en su sesión, `update_document`, `set_approved(False)`,
  `soft_delete_document`, purga, restaurar del deshacer y los métodos de
  conciliación y alta de líneas (R26). Si la tabla no existe, no hay alta.
- `.../albaranes-front/interface_adapters/web/app.py` — 409 (API) o redirección
  con mensaje (formularios) para R25; saltos de R27; rutas nuevas `POST
  /documents/{id}/alta-sigrid/solicitar` y `/alta-sigrid/verificar-anulacion`;
  revalorar y re-buscar contratos consultan el alta antes de publicar.
- `.../templates/document_detail.html` (panel; «Guardar y aprobar» deshabilitado
  sin valoración `ok`), `documents_list.html` (estado del alta y «Aprobar»
  deshabilitado sin valoración, R31, R37).
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
4. `buscar_albaranes(cif, referencia)` → `registrado` si su `synckey` es la
   nuestra, si no `ya_en_sigrid` (R14); `incierto` reenvía igual (R15).
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
(escribir). sv5 no la lee. Lecturas de sv9: merge (cabecera), `albaran_valuations`
(`status`, `contrato_codigo`), `albaran_line_valuations` (cantidades, unidad,
`precio_unitario_final`, `importe_calculado`, `matched_/derived_contrato_line_id`,
`codigo_partida_final`, `partida_action`, `descripcion_linea`), la descripción de
`albaran_lines_merge` y `albaran_contrato_lines_merge` (`sigrid_ide`, contrato).

Consulta de duplicados (R14), vía `sql/read`, parametrizada:
`SELECT c.ide, c.cod, c.fec, d.synckey FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide
WHERE c.tip = 14 AND d.entcif = ? AND d.entref = ?`. `existe_concepto`:
`SELECT ide FROM dbo.con WHERE ide = ? AND tip = 14`.

## 7. Configuración

sv9: `ALTA_SIGRID_DESDE_UTC` (vacía = no hace nada), `ALTA_SIGRID_COMMIT`
(defecto `false`; solo lo cambia el humano), `ALTA_SIGRID_ESPERA_INCIERTO_MIN`
(15), `ALTA_SIGRID_TOLERANCIA_EUR` (0,05), `ALTA_SIGRID_AVISOS_BLOQUEANTES`
(lista; defecto «plantilla de cabecera no es del mismo proveedor» y «sin
historico de dcapro»), `ALTA_SIGRID_USUARIO`, `ALTA_SIGRID_EMPIDE` (fijo; vacía
= defecto de sigrid-api), `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (`MA9999`), `SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY` (secreto), `SIGRID_API_DATABASE`
(`ruesma`), `PG_*`, Graph/SharePoint y colas, con los nombres de sv3/sv6.
sv4: `ALTA_SIGRID_DESDE_UTC` y `ALTA_SIGRID_ESPERA_INCIERTO_MIN`, **con el mismo
valor que sv9** (lo fija el script de despliegue desde una sola variable).
En local, `ALTA_SIGRID_COMMIT` no se pone nunca (regla de solo lectura).

## 8. Orden y dependencias

**Medición y PRE-1 → F-052 → F-051 → F-053.** F-052 da el CIF correcto; F-051
fija el almacén (partida vacía + marca en `partida_action`) y su ruta de sv4
(`asignar_almacen`) entra en R25 al fusionar. F-053 se implementa a la vez y se
fusiona después; el modo `real`, con las tres en producción. «Solo líneas con
importe» ya deja fuera el «solo llevar» de F-006; F-015 (tachadas), pregunta 12.
Despliegue: sv3 (tabla) → sv9 (con DESDE vacía) → sv4 → DESDE en ambos
(simulación) → días de simulación → `ALTA_SIGRID_COMMIT=true` (humano).

## 9. Reglas del repo y documentación (propuesta; NO se aplica aquí)

`CLAUDE.md`, redacción propuesta: «Sigrid solo vía sigrid-api, nunca SQL
directo. Leer: cualquier servicio. Escribir: **solo sv9**, con el alta de
albarán y `concepto-grafico`, nunca `sql/write`, y solo con
`ALTA_SIGRID_COMMIT=true`, que activa el humano. Desde local, nunca.» Igual en
`docs/ARCHITECTURE.md` y `docs/referencia/dominio_negocio_albaranes.md` §5.2.
`azure-apps/albaranes.md`: sv9, la tabla y el consumo de sigrid-api. La fila de
`azure-apps/sigrid_api.md` §10 es de sigrid-api: se propone (pregunta 15).

## 10. Ficheros que NO se tocan

- `sigrid-api` ni su configuración en Azure: PRE-1 es ficha de ese repositorio.
- sv1, sv2, sv5; sv6 (su valoración se lee, no se cambia).
- `albaran_documents_merge` y tablas de sv6: ninguna columna nueva.
- `ruesma_comun.importes`, `familias`, `origen_datos`.
- `infra/*.local.ps1`, `.env`: nada de IDs, claves ni URLs reales.

## 11. Riesgos y decisiones

- **Doble alta**: la cierra la idempotencia de PRE-1 (`synckey`). Además:
  `FOR UPDATE` y estados, una réplica, grabación sin reintento, `incierto` no se
  retoma antes de la Espera (la Function sigue viva tras el corte de 230 s) y
  búsqueda por CIF + referencia (altas a mano; un número repetido da
  `ya_en_sigrid`, preferible a duplicar).
- **Nunca se graba aproximado**: lo que la previa no devuelve tal cual se pidió
  (importe, partida, líneas) va a `revisar`.
- **Clave de sigrid-api** (decidido 2026-10-01: la de siempre). Riesgo
  aceptado: con la escritura abierta, quien tenga la clave por defecto (sv2, sv3,
  sv4 y otros proyectos) puede grabar en Sigrid; el control es de código y revisión.
- **Carrera sv4 ↔ sv9**: ambos bloquean la fila del merge; las operaciones que
  solo publican (revalorar, re-buscar) comprueban sin cerrojo: la instantánea
  que se envía es la de `peticion_json`, y la revisión posterior la detecta.
- **Sin valorar no se aprueba** (R37): como sv6 solo valora contra un contrato,
  un albarán sin contrato tampoco se podrá aprobar (pregunta 21).
- Descartado: `albaran-directo` (hereda partida, exige `proide`); partir un
  albarán en dos altas; exigir casar con el contrato; elegir producto por
  familia (futuro); estado en el merge (deshacer); `sql/write`.
- Verificación con BBDD real, Azurite y sigrid-api: manual del humano (tasks).
