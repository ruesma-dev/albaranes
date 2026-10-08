<!-- specs/F-053-alta-sigrid/design.md -->
# F-053 · Alta en Sigrid de los albaranes aprobados · Diseño (v7)

Requisitos: `requirements.md`. Decisiones (P1–P7 cerradas el 2026-10-06): `progress/spec_F-053.md`. «Contrato» =
`sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md` (**v8**, `8a6ecab`; dueño sigrid-api; aquí se
enlaza, no se copia; si discrepa de la spec de F-009, manda esa spec).

## 1. Encaje, límite de servicio y precondiciones

Responsabilidad **nueva** (escribir en el ERP): **servicio nuevo sv9** (`services/albaranes-alta-sigrid`,
`ca-sv9-alta-sigrid`), solo worker, hexagonal como sv6 (decidido). `sv7` = orquestador retirado, `sv8` =
aprendizaje (docstring de `MensajeFeedback`). Flujo: sv4 aprueba → `q-feedback` (reservada para esto en
`docs/ARCHITECTURE.md`) → sv9 → sigrid-api → `albaran_altas_sigrid` ← sv4 la lee.

**Precondiciones**: §8 (**F-051 en `dev`** para implementar; **F-009 desplegada** para la previa y el modo real).

**Producto de las sin vincular (humano, 2026-10-05).** La analítica de una sin vincular sale de la obra y de la
naturaleza que sigrid-api asigna al producto por configuración (`MA99`, `QA99`, `XA99`; contrato H10 y H34), no
de la partida ni del almacén: el producto importa. Regla: familia `alquiler_maquinaria` → `QA9999`,
`medios_auxiliares` → `XA9999` (andamios, puntales…), resto → `MA9999`, **por línea** (`familia_efectiva`: en un
mixto manda la de la línea), y el administrativo lo cambia en sv4 antes de aprobar. Vinculadas: las del contrato.

**Familia `medios_auxiliares`**: no existe hoy en `ruesma_comun.contratos.familias`. Darla de alta es ruta sensible
(prompt de IA1, `TipoFamilia` copiado en sv2/sv3/sv5, evals) y va en **F-061** (ficha propia, decisión del humano
2026-10-06), ni dentro de F-053 ni antes. Mientras no exista, esa clave del mapeo no casa: los andamios salen
`MA9999` por defecto y el administrativo elige `XA9999` a mano en sv4 (R40–R41).

## 2. sigrid-api: F-009, modo extendido de `sigrid/albaran`

Forma completa (campos, casos de línea, respuesta, errores, ejemplos): contrato §2, §3 y §6. Lo que sv9 manda,
R12 (misma ruta `POST /api/sigrid/albaran`, modo por las claves `lineas`/`referencia_externa`, `extra="forbid"`).
Lo que lee: `estado` (`previsto`|`creado`|`idempotente`), `con_ide`, `cod`, `avisos[{codigo, mensaje}]`, `totales`
y `lineas[]` casadas por `referencia_linea` (también en `idempotente`); en 400, `details.codigo` y `details.lineas`.

**Configuración que pone sigrid-api** (no F-053): `SIGRID_ALBARAN_WRITE_ENABLED` (segunda llave),
`SIGRID_ALBARAN_PREFIJOS_REFERENCIA=["ALB-"]`, `SIGRID_ALBARAN_EMPRESAS_OBRA=[1]` y
`SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO=["MA9999","QA9999","XA9999"]`, que debe contener los valores del mapeo
de §7, y `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO` (`MA99`, `QA99`, `XA99`; H34, F-009 v8), que debe cubrirlos.

**Códigos → estado del alta (R18; la tabla es un dato de `clasificador.py`) y lo que ve el revisor en sv4:**

| `details.codigo` | Estado | Panel de sv4 |
|---|---|---|
| `lineas_no_validas` con `linea_no_es_del_contrato`, `partida_no_encontrada`, `partida_ambigua`, `partida_no_imputable`, `paride_no_valido`, `analitica_no_resuelta` | `no_admitido` | cada línea con su código y mensaje; se corrige y «Solicitar alta» |
| `obra_no_encontrada`, `obra_ambigua`, `contrato_no_encontrado`, `contrato_ambiguo`, `proveedor_sin_albaran_previo`, `almacen_de_obra_no_resuelto` (H13), `demasiadas_lineas` (H22) | `no_admitido` | corregir obra o contrato; proveedor sin albarán previo, obra con dos almacenes o más de 100 líneas: alta a mano |
| `referencia_en_conflicto` | `revisar` | otro albarán de Sigrid lleva nuestra referencia: mirarlo |
| `escritura_albaranes_deshabilitada`, `base_de_datos_no_permitida`, `referencia_no_permitida`, `obra_de_empresa_no_permitida`, `usuario_no_valido`, `estado_inicial_no_encontrado`, `peticion_mixta`; línea con `producto_no_permitido`, `producto_no_encontrado` (H24), `naturaleza_no_valida` (H34) o `precio_negativo`; 400 sin código; código desconocido (H25) | `error` | «fallo de configuración o del servicio» con el código; no es del revisor |
| `colision_de_clave`, `filas_afectadas_inesperadas` | `error` | ERP intacto; «Solicitar alta» reintenta con la misma referencia |
| 5xx, tiempo agotado, conexión | `incierto` (grabación) / `error` (previa) | tras la Espera, reintento seguro por idempotencia |

En `lineas_no_validas`, si una línea trae un código de la fila `error`, gana `error`. `precio_negativo` no sale de
sv9 (manda |importe| / |cantidad|; signos opuestos, R39). `analitica_no_resuelta`: la obra no tiene la cuenta
`<obra>.<sufijo>` (H10): alta a mano o crearla. `naturaleza` no existe en F-009 v8 (mandarla da 400 sin código):
`naturaleza_no_valida` es configuración de sigrid-api (H34). `fecha_no_valida` ya no existe en sigrid-api (v5.1): la
fecha la controla sv9 (R10, R39). H9 y H20 cerrados (anular borra; `mov` según `pro.tipmov`, sin puerta dura).

Avisos **bloqueantes** por `codigo` (R17; `ALTA_SIGRID_AVISOS_BLOQUEANTES`, defecto `producto_sin_historico`;
`plantilla_de_otro_proveedor` ya no existe, H25) → `revisar`. Informativos, se enseñan en el panel:
`partida_distinta_del_contrato`, `sin_partida_en_linea_con_partida` (H12), `precio_distinto_del_contrato`,
`supera_pendiente`, `servido_negativo`, `stock_negativo`, `iva_de_otro_proveedor`, `cod_provisional`.

## 3. Ficheros a crear

sv9, `services/albaranes-alta-sigrid/` (estructura de sv6; primera línea de cada fichero, su ruta):
- `main_worker.py` (`ejecutar_worker` sobre `COLA_FEEDBACK`; log del modo), `Dockerfile`, `requirements.txt`,
  `sv9.md`, `.env.example` sin valores, `config/settings.py` (§7) y `config/logging_config.py` (patrón sv6).
- `domain/models/alta_models.py` — `EstadoAlta` (StrEnum de los 9 estados), `CabeceraAlta` (con la
  clasificación del documento), `LineaAlta` (con `line_index`, `tipo_familia` y `producto_sigrid`), `DatosAlta`,
  `PeticionAlbaran`, `LineaPeticion`, `Motivo(codigo, detalle)`, `ResultadoAlta`.
- `domain/ports/alta_repository.py` — `AltaRepository` (ABC): `reclamar(document_id, ahora, desde, espera) ->
  Reclamacion`, `leer_datos(document_id) -> DatosAlta`, `guardar(document_id, resultado)`, `leer_alta(document_id)`.
- `domain/ports/sigrid_alta_port.py` — `SigridAltaPort` (ABC): `buscar_albaranes(cif, referencia) ->
  list[AlbaranSigrid]`, `existe_concepto(ide) -> bool`, `alta_albaran(peticion, commit) -> RespuestaAlta |
  ErrorAlta` (§2), `adjuntar_pdf`. Solo esas cuatro operaciones (R33).
- `domain/ports/pdf_port.py` — `PdfAlbaranPort.descargar(datos) -> bytes`.
- `domain/services/validador_alta.py` — puro: `normalizar_cif(cif) -> str` y `validar_y_construir(datos,
  config, hoy) -> PeticionAlbaran | list[Motivo]` (R10–R13, R39, R43, R46); `config` = `usu`, `empide` y mapeo.
- `domain/services/comparador_previa.py` — puro: `comparar(peticion, respuesta, importes, tolerancia_eur,
  avisos_bloqueantes) -> list[Motivo]` (R17; con `idempotente`, solo `registrado_distinto` de R15).
- `domain/services/clasificador.py` — puro: respuesta de sigrid-api → estado, con la tabla de §2 como dato
  (R15, R18, R20, R21).
- `application/alta_sigrid_service.py` — `AltaSigridService.procesar(mensaje)`: orquesta §5; única que conoce el modo.
- `infrastructure/database/sql_alta_repository.py` — SQL con `text()` de SQLAlchemy y `ruesma_comun.db`.
- `infrastructure/sigrid/sigrid_api_alta_client.py` — httpx + tenacity (R24); la grabación usa un cliente sin
  reintentos y `timeout` 240 s (> 230 s del balanceador). Guarda de la respuesta solo lo de R16.
- `infrastructure/sharepoint/pdf_sharepoint.py` — baja el PDF con `ruesma_comun.sharepoint.GraphSharePointClient`
  por `sharepoint_relative_path`.
- `interface_adapters/composition.py`, `interface_adapters/worker/alta_worker.py` — traduce el mensaje y llama
  al servicio; los resultados de negocio confirman el mensaje; solo una excepción de infraestructura antes de R5
  lo reencola.
- `tests/` — fakes de los tres puertos; nada de red ni BBDD.

`ruesma_comun` (puros, sin E/S; los usan sv4 y sv9, R38):
- `ruesma_comun/valoracion.py` — `esta_valorado(status, importes) -> bool` (glosario).
- `ruesma_comun/alta_sigrid.py` — `leer_mapeo(texto) -> dict[str, str]` (`ValueError` si no es objeto JSON de
  textos con `*`, R44), `productos_admitidos(mapeo) -> frozenset[str]`, `producto_efectivo(elegido,
  tipo_familia_linea, clasificacion, mapeo) -> str` (`elegido` si no es nulo; si no, `mapeo.get(familia_efectiva(
  tipo_familia_linea, clasificacion), mapeo["*"])`) y `NOMBRES_PRODUCTO` (`MA9999` «Suministro de materiales»,
  `QA9999` «Alquiler de maquinaria», `XA9999` «Alquiler de medios auxiliares»; sin nombre, el código).

sv4: `templates/_alta_sigrid.html` (panel de la ficha, R29–R30).

## 4. Ficheros a modificar

- `services/albaranes-comun/ruesma_comun/colas/mensajes.py` — `MensajeFeedback.accion: Literal["alta",
  "verificar_anulacion"] = "alta"`; docstring: consumidor sv9. Tocar comun obliga a reconstruir todas las imágenes.
- sv3 — `albaran_altas_sigrid` (§6) en `phase2_ddl`. R45: `run` mira el alta (`buscar_conservado_por_alta`, con los
  `ESTADOS_ALTA_BLOQUEANTES`) antes de SharePoint y de las dos ramas, y `save` repite: `FOR UPDATE` de los merges y
  luego, en otra sentencia, el alta (una sola, en READ COMMITTED, no ve lo que sv9 confirma mientras espera; H4).
- `services/albaran-valoracion-persist/infrastructure/database/schema_contribution.py` y `orm_valuation_models.py`
  — columna `producto_sigrid` (§6) en DDL y ORM (nula, sin defecto: el replace la deja `NULL`, R42). Ninguna
  lógica de sv6 cambia. sv6 es el dueño de las tablas de valoración (`docs/ARCHITECTURE.md`), no sv3.
- sv3 `scripts/medir_admisibilidad_f053.py` y su test — fuera `MARCAS_ALMACEN` (F-051 v4: `sin_partida_sin_casar`,
  registrable) y recuento `lineas_de_otro_contrato` con sus `document_id` (R46, D2).
- `services/albaranes-front/config/settings.py` — `ALTA_SIGRID_DESDE_UTC`, `ALTA_SIGRID_ESPERA_INCIERTO_MIN` y
  `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (con `leer_mapeo`; R44).
- `.../albaranes-front/domain/ports/orchestrator_port.py` y `infrastructure/colas/colas_orchestrator_client.py`
  — `notify_document_approved` pasa a devolver si publicó; nuevo `solicitar_alta_sigrid(document_id, accion)`.
- `.../albaranes-front/application/services/review_service.py` — recibe el cliente de colas y la
  configuración; publica en el paso a aprobado (R1–R4); traduce `AlbaranBloqueadoError` (R25); rechaza aprobar lo
  no valorado (`AlbaranSinValorarError`, R37) en `approve_document` y `save_document`; nuevo
  `elegir_producto_sigrid(document_id, valuation_line_id, producto)` con el patrón de deshacer (foto antes,
  registro después) y validación contra `productos_admitidos` (R41).
- `.../albaranes-front/infrastructure/database/review_repository.py` — `leer_alta_sigrid(document_id)`,
  `estado_aprobacion`, «valorado» en la transacción (R37), `_exigir_desbloqueado(session, document_id)` en DOS
  sentencias (T19, como H4): `SELECT id ... FOR UPDATE` del merge y después el alta; llamada al empezar, en su
  sesión, por `update_document`, `set_approved(False)`, `soft_delete_document`, purga, restaurar del deshacer,
  los métodos de conciliación y alta de líneas y el nuevo `guardar_producto_sigrid` (R26; sin tabla = sin alta);
  `guardar_producto_sigrid` comprueba que la línea es del documento y no vinculada y hace el `UPDATE`; la lectura
  de líneas valoradas añade `producto_sigrid`, `tipologia`/`tipologia_mixta` del merge y `contexto_linea_json`.
- `.../albaranes-front/interface_adapters/web/app.py` — 409 (API) o redirección con mensaje (formularios) para
  R25; saltos de R27; rutas nuevas `POST /documents/{id}/alta-sigrid/solicitar`, `/alta-sigrid/verificar-anulacion`
  y `POST /api/documents/{id}/lineas-valoradas/{lv_id}/producto-sigrid` (`{"producto": str | null}`; 400 de R41);
  revalorar y re-buscar contratos consultan el alta antes de publicar.
- `.../templates/document_detail.html` (panel; columna «Producto Sigrid» de R40 en la tabla de líneas valoradas,
  solo con DESDE; «Guardar y aprobar» deshabilitado sin valoración), `documents_list.html` (estado del alta y
  «Aprobar» deshabilitado sin valoración, R31, R37).
- `harness/servicios.json` — `sv9-alta-sigrid`. `infra/` — sv9 en `$APPS` de `deploy.ps1`/`build_images.ps1` y su `create_capps*.ps1`: escalado KEDA sobre
  `q-feedback` con **máximo 1 réplica**, secreto `SIGRID_API_FUNCTION_KEY` desde Key Vault; DESDE, Espera y mapeo
  a sv4 y sv9 desde una sola variable. Redactado como los demás.
- `docs/ARCHITECTURE.md` — fila sv9, `q-feedback` con consumidor, tabla y columna nuevas, y la regla de acceso a
  Sigrid (§9). `azure-apps/albaranes.md` en el mismo trabajo.

## 5. Flujo de sv9 (`AltaSigridService.procesar`)

1. `reclamar` (R5–R8), en una transacción con el merge `FOR UPDATE`: decide `ignorar` / `solo_adjunto` /
   `a_incierto` / `procesar` / `verificar_anulacion`; si procesa, UPSERT a `en_curso` con `ultimo_intento_at_utc`.
2. `verificar_anulacion` (R28): `existe_concepto(sigrid_con_ide)` → `anulado` o aviso.
3. `leer_datos` y `validar_y_construir` → `no_admitido` si hay motivos (R10–R13); `revisar` si la fecha no es
   plausible, hay signos opuestos (R39) o una línea casa con otro contrato (R46, con WARNING). Sin llamar a sigrid-api.
4. `buscar_albaranes` (CIF normalizado) → `ya_en_sigrid` si hay alta a mano (R14).
5. Previa: 400/5xx → `clasificar` (§2); `idempotente` → `registrado` (+ `registrado_distinto`, R15); `comparar`
   → `revisar` (R16–R18). 6. Simulación → `simulado` (R19); real → grabación única (R20–R21). 7. Adjunto
   (R22–R23). Todo en `try/finally` (R9).

Cada paso guarda petición, respuesta (R16) y motivos, y apunta `{ts, estado, cod, motivos}` en `historial_json`.

## 6. SQL (sin ficheros `.sql`: DDL inline en el `schema_contribution.py` de su dueño)

sv3 (dueño del schema del merge):
```sql
CREATE TABLE IF NOT EXISTS albaran_altas_sigrid (
  document_id VARCHAR(36) PRIMARY KEY REFERENCES albaran_documents_merge(id) ON DELETE CASCADE,
  estado VARCHAR(24) NOT NULL, modo VARCHAR(12), sigrid_con_ide INTEGER, sigrid_cod VARCHAR(24),
  adjunto_estado VARCHAR(16), sigrid_gra_ide INTEGER,
  motivos_json TEXT, avisos_json TEXT, peticion_json TEXT, respuesta_json TEXT,
  historial_json TEXT, intentos INTEGER NOT NULL DEFAULT 0,
  approved_at_utc VARCHAR(64), approved_by VARCHAR(255),
  ultimo_intento_at_utc VARCHAR(64), creado_at_utc VARCHAR(64) NOT NULL, actualizado_at_utc VARCHAR(64));
CREATE INDEX IF NOT EXISTS ix_albaran_altas_sigrid_estado ON albaran_altas_sigrid (estado);
```
sv6 (dueño de las tablas de valoración): `ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS
producto_sigrid VARCHAR(24)` (código elegido en sv4; `NULL` = por defecto). sv5 no la lee; sv6 no la escribe.

Tabla aparte para el alta, no columnas del merge (el deshacer de sv4 restaura la fila del merge). El producto sí
va en la línea valorada: es una decisión sobre esa línea, el deshacer de sv4 ya fotografía la fila entera
(`SELECT *`) y el replace de sv6 la descarta igual que el almacén elegido (R42). Fechas `VARCHAR(64)` ISO. sv4
lee el alta, sv9 la escribe, sv5 no la lee. Lecturas de sv9: merge (cabecera, `tipologia`, `tipologia_mixta`),
`albaran_valuations` (`status`, `contrato_codigo`), `albaran_line_valuations` (cantidades, unidad,
`importe_calculado`, `matched_/derived_contrato_line_id`, `codigo_partida_final`, `descripcion_linea`,
`producto_sigrid`, `merge_line_id`), de `albaran_lines_merge` la descripción, `line_index` y `contexto_linea_json`,
y `albaran_contrato_lines_merge` (`sigrid_ide`).

`sql/read` (R14): `SELECT c.ide, c.cod, c.fec FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = 14 AND
d.entcif = ? AND d.entref = ? AND ISNULL(d.synckey, '') <> ?`; `existe_concepto`: `SELECT ide FROM dbo.con WHERE
ide = ? AND tip = 14`. Comprobar `truncated` (`ruesma_comun.sigrid.comprobar_truncado`, `NO_TOLERA`).

## 7. Configuración

sv9: `ALTA_SIGRID_DESDE_UTC` (vacía = no hace nada), `ALTA_SIGRID_COMMIT` (defecto `false`; solo lo cambia el
humano), `ALTA_SIGRID_ESPERA_INCIERTO_MIN` (15), `ALTA_SIGRID_TOLERANCIA_EUR` (0,05),
`ALTA_SIGRID_AVISOS_BLOQUEANTES` (§2), `ALTA_SIGRID_USUARIO` (login de `dbo.usu`, T0c; va en `usu` y en el
adjunto), `ALTA_SIGRID_EMPIDE` (vacía = defecto de sigrid-api), `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (JSON;
defecto `{"alquiler_maquinaria": "QA9999", "medios_auxiliares": "XA9999", "*": "MA9999"}`),
`SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY` (secreto), `SIGRID_API_DATABASE` (`ruesma`), `PG_*`,
Graph/SharePoint y colas, con los nombres de sv3/sv6. sv4: `ALTA_SIGRID_DESDE_UTC`,
`ALTA_SIGRID_ESPERA_INCIERTO_MIN` y `ALTA_SIGRID_PRODUCTO_POR_DEFECTO`, **con el mismo valor que sv9** (lo
fija el script de despliegue desde una sola variable). Los valores del mapeo deben estar en la lista blanca de
sigrid-api (§2): si no, `producto_no_permitido` → `error`. En local, `ALTA_SIGRID_COMMIT` no se pone nunca.

## 8. Orden y dependencias

**Medición y F-052 hechas → F-051 → F-053.** La implementación empieza con **F-051 en `dev`** (almacén = partida
final vacía; su `asignar_almacen` de sv4 entra en R25): **T0d** fusiona `dev` en la rama. Los tests no usan
sigrid-api; la previa contra sigrid-api (T26, T28) y el modo real (T29) esperan a **F-009 desplegada** (v8; M14e no
cambia el contrato). **Evolución, no bloqueo**: F-049, cuando conserve el `ide` de la partida elegida, deja mandar
`paride` (H17; mientras, `partida_ambigua` → `no_admitido`: otra partida o sin partida); F-061 (`medios_auxiliares`);
F-058 (conservar el producto elegido al revalorar; anotado para el líder); F-015 (tachadas). ALM impreso sin
vincular (H30): vincularlo es de F-060/F-007. «Solo líneas con importe» ya excluye el «solo llevar» de F-006.
Despliegue (comun reconstruye todas las imágenes): sv6 (columna) y sv3 (tabla) → sv9 (DESDE vacía) → sv4 → DESDE
en ambos (simulación) → días de simulación → llave de F-009 abierta y `ALTA_SIGRID_COMMIT=true` (humano).

## 9. Reglas del repo y documentación (propuesta; NO se aplica aquí)

`CLAUDE.md`, propuesta: «Sigrid solo vía sigrid-api, nunca SQL directo. Leer: cualquier servicio. Escribir: **solo
sv9**, con el alta de albarán y `concepto-grafico`, nunca `sql/write`, y solo con `ALTA_SIGRID_COMMIT=true`, que
activa el humano. Desde local, nunca.» Igual en `docs/ARCHITECTURE.md` y `docs/referencia/dominio_negocio_albaranes.md`
§5.2. `azure-apps/albaranes.md`: sv9, tabla y consumo de sigrid-api (`sigrid_api.md` §10 lo actualiza F-009).

## 10. Ficheros que NO se tocan

- `sigrid-api` ni su configuración: F-009 y el contrato son de ese repositorio.
- sv1, sv2, sv5; la lógica de sv6 (solo su DDL y ORM, §4).
- `albaran_documents_merge` y `albaran_lines_merge`: ninguna columna nueva.
- `ruesma_comun.contratos.familias`, `contexto_linea`, los prompts de IA1 y los evals: la familia
  `medios_auxiliares` es de F-061. `ruesma_comun.importes`, `origen_datos`.
- `infra/*.local.ps1`, `.env`: nada de IDs, claves ni URLs reales.

## 11. Riesgos y decisiones

- **Doble alta**: la cierra la idempotencia de F-009 (`synckey` bajo applock). Además: `FOR UPDATE` y estados,
  una réplica, grabación sin reintento automático, `incierto` no se retoma antes de la Espera y búsqueda por CIF +
  referencia (altas a mano; un número repetido da `ya_en_sigrid`, preferible a duplicar).
- **Precio neto**: F-009 calcula `tot = cantidad·precio` sin descuento: se manda el unitario **neto** (importe /
  cantidad) a 6 decimales (H14), no el bruto. Signos opuestos (descuento) ⇒ `revisar`; a mano en Sigrid (R39, H8).
- **Nunca se graba aproximado**: lo que la previa no devuelve tal cual se pidió (importe, partida, líneas) va a
  `revisar`; una cuenta analítica que la obra no tiene no se inventa (contrato H10).
- **Producto calculado al leer**, no guardado: el por defecto sale de la familia en cada lectura (sv4 al pintar,
  sv9 al construir), con la misma función y el mismo mapeo; lo mandado queda en `peticion_json`. Guardar el
  defecto obligaría a sv6 a calcularlo (lógica nueva en sv6) o a reescribirlo cada vez que la IA reclasifica.
- **`idempotente` distinto** (H18): queda `registrado` (bloqueado, se corrige anulando, R28) con el motivo
  `registrado_distinto`, no `revisar` como proponía el contrato: `revisar` desbloquearía un albarán que ya está
  en Sigrid y «Solicitar alta» volvería a dar `idempotente`.
- **Clave de sigrid-api** (decidido 2026-10-01: la de siempre). Riesgo aceptado: quien tenga la clave por defecto
  puede grabar con la escritura abierta; el control es de código y revisión. **Carrera sv4 ↔ sv9**: ambos bloquean
  la fila del merge; revalorar y re-buscar solo publican y comprueban sin cerrojo.
- **Sin valorar no se aprueba** (R37); sin contrato valora a mano el administrativo (sv4 ya lo permite).
- Descartado: `albaran-directo` (hereda partida, exige `proide`); partir un albarán en dos altas; exigir casar con
  el contrato; campo `almacen` (no existe en F-009 v5.1; F-051 v4 lo citaba); producto en una tabla aparte
  (huérfana al revalorar); DDL de la columna en sv3 (la tabla es de sv6); estado en el merge (deshacer); `sql/write`.
