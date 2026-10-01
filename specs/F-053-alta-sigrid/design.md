<!-- specs/F-053-alta-sigrid/design.md -->
# F-053 · Alta en Sigrid de los albaranes aprobados · Diseño

Requisitos: `requirements.md`. Decisiones (todas cerradas, 2026-10-01): `progress/spec_F-053.md`.

## 1. Encaje, límite de servicio y precondiciones

Responsabilidad **nueva** (escribir en el ERP): **servicio nuevo sv9**
(`services/albaranes-alta-sigrid`, `ca-sv9-alta-sigrid`), solo worker, hexagonal
como sv6 (decidido). `sv7` = orquestador retirado, `sv8` = aprendizaje
(docstring de `MensajeFeedback`). Flujo: sv4 aprueba → `q-feedback` (reservada
para esto en `docs/ARCHITECTURE.md`) → sv9 → sigrid-api → `albaran_altas_sigrid`
← sv4 la lee (decidido).

**Precondiciones (humano, 2026-10-01)** para `in_progress`: (1) la **medición**
(`services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py`, solo
lectura, la ejecuta el humano; comando en `progress/spec_F-053.md`); (2) **F-009
de sigrid-api** desplegada y con su llave de escritura (§2). Producto: «de momento siempre va a ser suministro
de materiales» ⇒ sin vincular, `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` = `MA9999`;
elegir entre MA9999/SM9999/SB9999/QA9999 por familia es mejora futura.

## 2. sigrid-api: F-009, modo extendido de `sigrid/albaran`

Hoy no basta (solo líneas de contrato, sin partida propia, sin idempotencia).
**F-009 de sigrid-api** (spec v2 `1bbcfc1`; si cambia, manda la suya) añade a la
**misma ruta** un modo extendido, elegido por las claves `lineas`/`referencia_externa`.

- **Petición** (`extra="forbid"`): `{database, cod_obra (≤24), cif_proveedor
  (≤24), cod_contrato (≤24 | null), referencia_externa ("ALB-…", ≤128),
  su_referencia (≤128), fecha_albaran, empide | null, commit, lineas:
  [{referencia_linea (≤64), ctrpro_ide | producto (código, ≤24), descripcion
  (≤128, obligatoria sin vincular), unidad (≤8), cantidad (≠ 0; < 0 devolución),
  precio (≥ 0), partida (código, ≤24) | almacen: true}]}`. Nunca `lineas_recibidas`
  (`peticion_mixta`); una vinculada exige `cod_contrato`.
- **Qué hace**: partida resuelta en la obra, nunca heredada; `pre` = `precio` y
  `tot` = `round(cantidad·precio, 2)` (distinto del contrato → aviso); cada línea
  su `dcapro` aunque repitan `ctrpro`; devoluciones con `canser += cantidad`
  aunque quede < 0; idempotencia por `dca.synckey` dentro de la transacción;
  tope `SIGRID_ALBARAN_MAX_LINEAS` (100).
- **Respuesta 200** (previa, grabación o idempotente): la clásica (`con_ide`,
  `cod`, `cabecera`, `lineas`, `totales`…) más `estado` (`previsto` | `creado` |
  `idempotente`), `referencia_externa`, `avisos[{codigo, mensaje}]` y `filas`; cada
  línea añade `referencia_linea`, `tipo`, `producto`, `paride`, `partida`, `almacen`
  y `avisos`. **Error 400**: `{ok:false, error, details:{type, codigo,
  lineas?:[{indice, referencia_linea, codigo, mensaje}]}}`; sin `codigo` =
  validación Pydantic; 500 = inesperado.
- **Configuración que pone sigrid-api** (no F-053): `SIGRID_ALBARAN_WRITE_ENABLED`
  (segunda llave del `commit`), `SIGRID_ALBARAN_PREFIJOS_REFERENCIA=["ALB-"]`,
  `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO=["MA9999"]`.

**Códigos → estado del alta (R18) y lo que ve el revisor en sv4:**

| `details.codigo` | Estado | Panel de sv4 |
|---|---|---|
| `lineas_no_validas` (`linea_no_es_del_contrato`, `partida_no_encontrada`, `partida_ambigua`, `partida_no_imputable`, `producto_no_encontrado`) | `no_admitido` | cada línea con su código y mensaje; se corrige y «Solicitar alta» |
| `obra_no_encontrada`, `obra_ambigua`, `contrato_no_encontrado`, `contrato_ambiguo`, `proveedor_sin_albaran_previo` | `no_admitido` | corregir obra o contrato; el proveedor sin albarán previo se da de alta a mano |
| `referencia_en_conflicto` | `revisar` | otro albarán de Sigrid lleva nuestra referencia: mirarlo |
| `escritura_albaranes_deshabilitada`, `base_de_datos_no_permitida`, `referencia_no_permitida`, `demasiadas_lineas`, `estado_inicial_no_encontrado`, `almacen_de_obra_no_resuelto`, `peticion_mixta`, `producto_no_permitido` en una línea, 400 sin código | `error` | «fallo de configuración o del servicio» con el código; no es del revisor |
| `colision_de_clave`, `filas_afectadas_inesperadas` | `error` | ERP intacto; «Solicitar alta» reintenta con la misma referencia |
| 5xx, tiempo agotado, conexión | `incierto` (grabación) / `error` (previa) | tras la Espera, reintento seguro por idempotencia |

Avisos **bloqueantes** por `codigo` (R17; `ALTA_SIGRID_AVISOS_BLOQUEANTES`, defecto
`plantilla_de_otro_proveedor`, `producto_sin_historico`) → `revisar`. Informativos,
se enseñan en el panel: `partida_distinta_del_contrato`,
`precio_distinto_del_contrato`, `supera_pendiente`, `servido_negativo`,
`stock_negativo`, `cod_provisional`.

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
  `alta_albaran(peticion, commit) -> RespuestaAlta | ErrorAlta` (§2), `adjuntar_pdf`.
  Solo esas cuatro operaciones (R33).
- `domain/ports/pdf_port.py` — `PdfAlbaranPort.descargar(datos) -> bytes`.
- `domain/services/validador_alta.py` — puro: `validar_y_construir(datos, empide,
  producto) -> PeticionAlbaran | list[Motivo]` (R10–R13).
- `domain/services/comparador_previa.py` — puro: `comparar(peticion, datos,
  respuesta, tolerancia_eur, avisos_bloqueantes) -> list[Motivo]` (R17).
- `domain/services/clasificador.py` — puro: respuesta de sigrid-api → estado,
  con la tabla de §2 como dato (R15, R18, R20, R21).
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
- `ruesma_comun/valoracion.py` (nuevo, puro) — `esta_valorado(status, importes)
  -> bool` del glosario (R38): lo usan sv4 (R37) y sv9 (R10).
- `services/albaranes-persistencia/infrastructure/database/schema_contribution.py`
  — `CREATE TABLE IF NOT EXISTS albaran_altas_sigrid` (§6).
- `services/albaranes-front/config/settings.py` — `ALTA_SIGRID_DESDE_UTC`,
  `ALTA_SIGRID_ESPERA_INCIERTO_MIN`.
- `.../albaranes-front/domain/ports/orchestrator_port.py` y
  `infrastructure/colas/colas_orchestrator_client.py` — `notify_document_approved`
  pasa a devolver si publicó; nuevo `solicitar_alta_sigrid(document_id, accion)`.
- `.../albaranes-front/application/services/review_service.py` — recibe el
  cliente de colas y la configuración; publica en el paso a aprobado (R1–R4);
  traduce `AlbaranBloqueadoError` (R25) y rechaza aprobar lo no valorado
  (`AlbaranSinValorarError`, R37) en `approve_document` y `save_document`.
- `.../albaranes-front/infrastructure/database/review_repository.py` —
  `leer_alta_sigrid(document_id)`, `es_aprobado`, `datos_valoracion` (status e importes) y
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

1. `reclamar` (R5–R8), en una transacción con el merge `FOR UPDATE`: decide
   `ignorar` / `solo_adjunto` / `a_incierto` / `procesar` / `verificar_anulacion`;
   si procesa, UPSERT a `en_curso` con `ultimo_intento_at_utc = ahora`.
2. `verificar_anulacion` (R28): `existe_concepto(sigrid_con_ide)` → `anulado` o aviso.
3. `leer_datos` y `validar_y_construir` → `no_admitido` si hay motivos (R10–R13).
4. `buscar_albaranes` → `ya_en_sigrid` si hay alta a mano (R14).
5. Previa: 400/5xx → `clasificar` (§2); `idempotente` → `registrado` (R15);
   `comparar` → `revisar` (R16–R18). 6. Simulación → `simulado` (R19); real →
   grabación única (R20–R21). 7. Adjunto (R22–R23). Todo en `try/finally` (R9).

Cada paso guarda petición, respuesta y motivos, y apunta `{ts, estado, cod, motivos}` en `historial_json`.

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

Tabla aparte, no columnas del merge (el deshacer de sv4 restaura la fila del
merge). Fechas `VARCHAR(64)` ISO como el resto. sv4 la lee, sv9 la escribe, sv5
no la lee. Lecturas de sv9: merge (cabecera), `albaran_valuations`
(`status`, `contrato_codigo`), `albaran_line_valuations` (cantidades, unidad,
`precio_unitario_final`, `importe_calculado`, `matched_/derived_contrato_line_id`,
`codigo_partida_final`, `partida_action`, `descripcion_linea`), la descripción de
`albaran_lines_merge` y `albaran_contrato_lines_merge` (`sigrid_ide`, contrato).

`sql/read` (R14): `SELECT c.ide, c.cod, c.fec FROM dbo.con c JOIN dbo.dca d ON
d.ide = c.ide WHERE c.tip = 14 AND d.entcif = ? AND d.entref = ? AND
ISNULL(d.synckey, '') <> ?`; `existe_concepto`: `SELECT ide FROM dbo.con WHERE ide = ? AND tip = 14`.

## 7. Configuración

sv9: `ALTA_SIGRID_DESDE_UTC` (vacía = no hace nada), `ALTA_SIGRID_COMMIT`
(defecto `false`; solo lo cambia el humano), `ALTA_SIGRID_ESPERA_INCIERTO_MIN`
(15), `ALTA_SIGRID_TOLERANCIA_EUR` (0,05), `ALTA_SIGRID_AVISOS_BLOQUEANTES` (códigos,
§2), `ALTA_SIGRID_USUARIO`, `ALTA_SIGRID_EMPIDE` (vacía = defecto de sigrid-api),
`ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (`MA9999`), `SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY` (secreto), `SIGRID_API_DATABASE`
(`ruesma`), `PG_*`, Graph/SharePoint y colas, con los nombres de sv3/sv6.
sv4: `ALTA_SIGRID_DESDE_UTC` y `ALTA_SIGRID_ESPERA_INCIERTO_MIN`, **con el mismo
valor que sv9** (lo fija el script de despliegue desde una sola variable).
En local, `ALTA_SIGRID_COMMIT` no se pone nunca (regla de solo lectura).

## 8. Orden y dependencias

**Medición y F-009 de sigrid-api → F-052 → F-051 → F-053.** F-052 da el CIF correcto; F-051
fija el almacén (partida vacía + marca en `partida_action`) y su ruta de sv4
(`asignar_almacen`) entra en R25 al fusionar. F-053 se implementa a la vez y se
fusiona después; el modo `real`, con las tres en producción. «Solo líneas con
importe» ya deja fuera el «solo llevar» de F-006; F-015 (tachadas), cuando llegue.
Despliegue: sv3 (tabla) → sv9 (con DESDE vacía) → sv4 → DESDE en ambos
(simulación) → días de simulación → llave de F-009 abierta y `ALTA_SIGRID_COMMIT=true` (humano).

## 9. Reglas del repo y documentación (propuesta; NO se aplica aquí)

`CLAUDE.md`, redacción propuesta: «Sigrid solo vía sigrid-api, nunca SQL
directo. Leer: cualquier servicio. Escribir: **solo sv9**, con el alta de
albarán y `concepto-grafico`, nunca `sql/write`, y solo con
`ALTA_SIGRID_COMMIT=true`, que activa el humano. Desde local, nunca.» Igual en
`docs/ARCHITECTURE.md` y `docs/referencia/dominio_negocio_albaranes.md` §5.2.
`azure-apps/albaranes.md`: sv9, la tabla y el consumo de sigrid-api (la fila de
`sigrid_api.md` §10 la actualiza F-009, su R36).

## 10. Ficheros que NO se tocan

- `sigrid-api` ni su configuración: F-009 es ficha de ese repositorio.
- sv1, sv2, sv5; sv6 (su valoración se lee, no se cambia).
- `albaran_documents_merge` y tablas de sv6: ninguna columna nueva.
- `ruesma_comun.importes`, `familias`, `origen_datos`.
- `infra/*.local.ps1`, `.env`: nada de IDs, claves ni URLs reales.

## 11. Riesgos y decisiones

- **Doble alta**: la cierra la idempotencia de F-009 (`synckey` bajo applock).
  Además: `FOR UPDATE` y estados, una réplica, grabación sin reintento automático,
  `incierto` no se retoma antes de la Espera y búsqueda por CIF + referencia (altas
  a mano; un número repetido da `ya_en_sigrid`, preferible a duplicar).
- **Precio neto**: F-009 calcula `tot = cantidad·precio` sin descuento, así que se
  manda el unitario **neto** (importe / cantidad), no el bruto de la valoración.
- **Nunca se graba aproximado**: lo que la previa no devuelve tal cual se pidió
  (importe, partida, líneas) va a `revisar`.
- **Clave de sigrid-api** (decidido 2026-10-01: la de siempre). Riesgo
  aceptado: con la escritura abierta, quien tenga la clave por defecto (sv2, sv3,
  sv4 y otros proyectos) puede grabar en Sigrid; el control es de código y revisión.
- **Carrera sv4 ↔ sv9**: ambos bloquean la fila del merge; revalorar y re-buscar
  solo publican y comprueban sin cerrojo (lo enviado queda en `peticion_json`).
- **Sin valorar no se aprueba** (R37). Sin contrato valora a mano el
  administrativo y **sv4 ya lo permite** (`add_standalone_valuation_line`,
  `add_conciliacion_for_merge_line`; cabecera `manual`). «Valorar ahora» borra lo manual.
- Descartado: `albaran-directo` (hereda partida, exige `proide`); partir un
  albarán en dos altas; exigir casar con el contrato; elegir producto por
  familia (futuro); estado en el merge (deshacer); `sql/write`.
