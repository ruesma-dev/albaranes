<!-- specs/F-053-alta-sigrid/design.md -->
# F-053 · Alta en Sigrid de los albaranes aprobados · Diseño (v8)

Requisitos: `requirements.md`. Decisiones (P1–P7 del 2026-10-06; U1–U7 de la v8, 2026-10-13): `progress/spec_F-053.md`.
«Contrato» = `sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md` (**v8**, `8a6ecab`; dueño sigrid-api;
aquí se enlaza, no se copia; si discrepa de la spec de F-009, manda esa spec).

## 1. Encaje, límite de servicio y precondiciones

Responsabilidad **nueva** (escribir en el ERP): **servicio nuevo sv9** (`services/albaranes-alta-sigrid`,
`ca-sv9-alta-sigrid`), solo worker, hexagonal como sv6 (decidido). `sv7` = orquestador retirado, `sv8` =
aprendizaje (docstring de `MensajeFeedback`). Flujo: sv4 aprueba → `q-feedback` (reservada para esto en
`docs/ARCHITECTURE.md`) → sv9 → sigrid-api → `albaran_altas_sigrid` ← sv4 la lee. Precondiciones: §8.

**Producto de las sin vincular (humano, 2026-10-05).** La analítica de una sin vincular sale de la obra y de la
naturaleza que sigrid-api asigna al producto por configuración (`MA99`, `QA99`, `XA99`; contrato H10 y H34), no
de la partida ni del almacén: el producto importa. Regla: familia `alquiler_maquinaria` → `QA9999`,
`medios_auxiliares` → `XA9999` (andamios, puntales…), resto → `MA9999`, **por línea** (`familia_efectiva`: en un
mixto manda la de la línea), y el administrativo lo cambia en sv4 antes de aprobar. Vinculadas: las del contrato.
**Familia `medios_auxiliares`**: aún no existe en `ruesma_comun.contratos.familias`; la da de alta **F-061** (ruta
sensible: prompt de IA1, `TipoFamilia` copiado, evals). Mientras, `MA9999` y el administrativo elige `XA9999` (R40–R41).

**Usuario de Sigrid (humano, 2026-10-13; v8).** «Con el usuario del correo de Ruesma que esté usando la app; si no
coinciden, el mío (pgris) de momento». sv4 sabe quién es por **Easy Auth** (Entra ID, `infra/create_capps_sv4.ps1`):
la plataforma inyecta `X-MS-CLIENT-PRINCIPAL-NAME` (UPN) y no deja que el cliente la fije. Hoy solo la usa el
**listado**; la **ficha** (PUT) no la lee y guarda `DEFAULT_REVIEWER` (o nada): R49 lo corrige. El `approved_by` del
merge llega a sv9 en R5 (bajo el cerrojo) y es la única fuente: el del mensaje no se usa. `dbo.usu` no tiene correo
(`ele` vacío en los 233 usuarios, T0c): se casa la parte antes de la @ con `dbo.usu.cod`, como valida sigrid-api.

## 2. sigrid-api: F-009, modo extendido de `sigrid/albaran`

Forma completa (campos, casos de línea, respuesta, errores, ejemplos): contrato §2, §3 y §6. Lo que sv9 manda,
R12 (misma ruta `POST /api/sigrid/albaran`, modo por las claves `lineas`/`referencia_externa`, `extra="forbid"`).
Lo que lee: `estado` (`previsto`|`creado`|`idempotente`), `con_ide`, `cod`, `avisos[{codigo, mensaje}]`, `totales`
y `lineas[]` casadas por `referencia_linea` (también en `idempotente`); en 400, `details.codigo` y `details.lineas`.

**Configuración que pone sigrid-api** (no F-053; T0c conforme, 2026-10-13): `SIGRID_ALBARAN_WRITE_ENABLED`,
`SIGRID_ALBARAN_PREFIJOS_REFERENCIA=["ALB-"]`, `SIGRID_ALBARAN_EMPRESAS_OBRA=[1]`, `SIGRID_ALBARAN_PRODUCTOS_SIN_CONTRATO`
(los valores del mapeo de §7) y `SIGRID_ALBARAN_NATURALEZA_POR_PRODUCTO` (`MA99`, `QA99`, `XA99`; H34).

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
`<obra>.<sufijo>` (H10): alta a mano o crearla. `naturaleza` no existe en F-009 v8 (mandarla da 400 sin código;
`naturaleza_no_valida` es configuración, H34). `fecha_no_valida` ya no existe (v5.1): la controla sv9 (R10, R39).

Avisos **bloqueantes** por `codigo` (R17; `ALTA_SIGRID_AVISOS_BLOQUEANTES`, defecto `producto_sin_historico`;
`plantilla_de_otro_proveedor` ya no existe, H25) → `revisar`. Informativos, se enseñan en el panel:
`partida_distinta_del_contrato`, `sin_partida_en_linea_con_partida` (H12), `precio_distinto_del_contrato`,
`supera_pendiente`, `servido_negativo`, `stock_negativo`, `iva_de_otro_proveedor`, `cod_provisional`.

## 3. Ficheros a crear

sv9, `services/albaranes-alta-sigrid/` (estructura de sv6; primera línea de cada fichero, su ruta):
- `main_worker.py` (`ejecutar_worker` sobre `COLA_FEEDBACK`; log del modo), `Dockerfile`, `requirements.txt`,
  `sv9.md`, `.env.example` sin valores, `config/settings.py` (§7) y `config/logging_config.py` (patrón sv6).
- `domain/models/alta_models.py` — `EstadoAlta` (9 estados), `CabeceraAlta`, `LineaAlta` (con `line_index`,
  `tipo_familia`, `producto_sigrid`), `DatosAlta`, `PeticionAlbaran`, `LineaPeticion`, `Motivo`, `ResultadoAlta`.
- `domain/ports/alta_repository.py` — `AltaRepository` (ABC): `reclamar(document_id, ahora, desde, espera) ->
  Reclamacion`, `leer_datos(document_id) -> DatosAlta`, `guardar(document_id, resultado)`, `leer_alta(document_id)`.
- `domain/ports/sigrid_alta_port.py` — `SigridAltaPort` (ABC): `buscar_albaranes(cif, referencia) ->
  list[AlbaranSigrid]`, `existe_concepto(ide) -> bool`, **`buscar_usuario(cod) -> str | None`** (v8, R47),
  `alta_albaran(peticion, commit) -> RespuestaAlta | ErrorAlta` (§2), `adjuntar_pdf(..., usu)` (v8: `usu` por
  llamada, R22). Solo las tres rutas de R33.
- `domain/ports/pdf_port.py` — `PdfAlbaranPort.descargar(datos) -> bytes`.
- `domain/services/validador_alta.py` — puro: `normalizar_cif(cif) -> str` y `validar_y_construir(datos,
  config, hoy, usu) -> PeticionAlbaran | list[Motivo]` (R10–R13, R39, R43, R46); `config` = `empide` y mapeo (v8:
  `usu` sale de `config` y llega por documento).
- **`domain/services/usuario_sigrid.py`** (v8) — puro: `candidato_usuario(approved_by) -> str | None`: la parte antes
  de la @ si el texto, sin espacios, acaba en `@ruesma.es` sin distinguir mayúsculas y esa parte no está vacía ni
  pasa de 24; si no, `None` (texto libre, `DEFAULT_REVIEWER`, invitado `#EXT#`, otro dominio, `None`) (R47).
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

`ruesma_comun` (puros, sin E/S; los usan sv4 y sv9, R38; hechos en T1, detalle en sus docstrings):
`valoracion.esta_valorado(status, importes)` y `alta_sigrid` (`leer_mapeo` con `ValueError` de R44,
`productos_admitidos`, `producto_efectivo(elegido, tipo_familia_linea, clasificacion, mapeo)`: el elegido o
`mapeo.get(familia_efectiva(...), mapeo["*"])`, y `NOMBRES_PRODUCTO`).

sv4: `templates/_alta_sigrid.html` (panel de la ficha, R29–R30).

## 4. Ficheros a modificar

- `services/albaranes-comun/ruesma_comun/colas/mensajes.py` — `MensajeFeedback.accion: Literal["alta",
  "verificar_anulacion"] = "alta"`; docstring: consumidor sv9. Tocar comun obliga a reconstruir todas las imágenes.
- sv3 — `albaran_altas_sigrid` (§6) en `phase2_ddl`. R45: `run` mira el alta (`buscar_conservado_por_alta`, con los
  `ESTADOS_ALTA_BLOQUEANTES`) antes de SharePoint y de las dos ramas, y `save` repite: `FOR UPDATE` de los merges y
  luego, en otra sentencia, el alta (una sola, en READ COMMITTED, no ve lo que sv9 confirma mientras espera; H4).
- sv6 `infrastructure/database/schema_contribution.py` y `orm_valuation_models.py` — columna `producto_sigrid` (§6),
  nula y sin defecto (el replace la deja `NULL`, R42); ninguna lógica de sv6 cambia (dueño de las tablas de valoración).
- sv3 `scripts/medir_admisibilidad_f053.py` y su test — fuera `MARCAS_ALMACEN` (F-051 v4: `sin_partida_sin_casar`,
  registrable) y recuento `lineas_de_otro_contrato` con sus `document_id` (R46, D2).
- sv4 `config/settings.py` (DESDE, Espera y mapeo con `leer_mapeo`, R44); `domain/ports/orchestrator_port.py` y
  `infrastructure/colas/colas_orchestrator_client.py` (`notify_document_approved` dice si publicó; `solicitar_alta_sigrid`).
- `.../albaranes-front/application/services/review_service.py` — cliente de colas y configuración; publica en el
  paso a aprobado (R1–R4); traduce `AlbaranBloqueadoError` (R25); rechaza aprobar lo no valorado
  (`AlbaranSinValorarError`, R37); `elegir_producto_sigrid` con deshacer y `productos_admitidos` (R41). **v8**:
  `puede_reintentar_adjunto` y `reintentar_adjunto_sigrid` (`registrado`, `real`, adjunto no colgado ⇒ `accion="alta"`).
- `.../albaranes-front/infrastructure/database/review_repository.py` — `leer_alta_sigrid`, `estado_aprobacion`,
  «valorado» en la transacción (R37), `_exigir_desbloqueado` en DOS sentencias (cerrojo del merge y después el alta,
  como H4) al empezar cada método de R26 (sin tabla = sin alta; lista en T19), `guardar_producto_sigrid` (R41) y
  la lectura de líneas valoradas con `producto_sigrid`, `tipologia`/`tipologia_mixta` y `contexto_linea_json`.
- `.../albaranes-front/interface_adapters/web/app.py` — 409 (API) o redirección con mensaje (formularios) para
  R25; saltos de R27; rutas nuevas `POST /documents/{id}/alta-sigrid/solicitar`, `/alta-sigrid/verificar-anulacion`
  y `POST /api/documents/{id}/lineas-valoradas/{lv_id}/producto-sigrid` (`{"producto": str | null}`; 400 de R41);
  revalorar y re-buscar contratos consultan el alta antes de publicar. **v8**: `/alta-sigrid/reintentar-adjunto`
  (R30); `_reviewer_from_request` pasa a cabecera > formulario > `DEFAULT_REVIEWER` y el PUT `/api/documents/{id}`
  recibe `Request` y pone en `payload.approved_by` la cabecera si llega (el cuerpo solo cuenta sin ella; R49).
- `.../templates/document_detail.html` (panel; columna «Producto Sigrid» de R40 en la tabla de líneas valoradas,
  solo con DESDE; «Guardar y aprobar» deshabilitado sin valoración), `documents_list.html` (estado del alta y
  «Aprobar» deshabilitado sin valoración, R31, R37); **v8**: `_alta_sigrid.html` con `usu` («respaldo») y el botón.
- sv9 (**v8**): `config/settings.py` — `ALTA_SIGRID_USUARIO` pasa a `ALTA_SIGRID_USUARIO_RESPALDO` (U4; sin defecto en
  código), `main_worker.py` (aviso si DESDE está puesta y el respaldo vacío), `.env.example`, `sv9.md`; servicio,
  cliente y fakes según §3 y §5.
- `harness/servicios.json` — `sv9-alta-sigrid`. `infra/` — sv9 en `$APPS` de `deploy.ps1`/`build_images.ps1` y su
  `create_capps*.ps1` (KEDA sobre `q-feedback`, **máximo 1 réplica**, secreto `SIGRID_API_FUNCTION_KEY` de Key Vault;
  DESDE, Espera y mapeo a sv4 y sv9 desde una variable; redactado). **v8**: el respaldo en `00_capps_vars.ps1`,
  `create_capps_sv9.ps1`, `set_alta_sigrid.ps1` y `README_capps.md` (U5: valor `pgris`, no es secreto).
- `docs/ARCHITECTURE.md` — fila sv9, `q-feedback` con consumidor, tabla y columna nuevas, y la regla de acceso a
  Sigrid (§9). `azure-apps/albaranes.md` en el mismo trabajo (v8: la variable renombrada y el origen de `usu`).

## 5. Flujo de sv9 (`AltaSigridService.procesar`)

1. `reclamar` (R5–R8), en una transacción con el merge `FOR UPDATE`: decide `ignorar` / `solo_adjunto` /
   `a_incierto` / `procesar` / `verificar_anulacion`; si procesa, UPSERT a `en_curso` con `ultimo_intento_at_utc`.
2. `verificar_anulacion` (R28): `existe_concepto(sigrid_con_ide)` → `anulado` o aviso.
3. `leer_datos`; **v8**: si no se retoma un `incierto`, `usu` = `buscar_usuario(candidato_usuario(approved_by))` o el
   respaldo; lectura caída o respaldo vacío → `error` `usuario_no_resuelto` (R47–R48). `validar_y_construir` →
   `no_admitido` si hay motivos (R10–R13); `revisar` si la fecha no es plausible, hay signos opuestos (R39) o una
   línea casa con otro contrato (R46, con WARNING). Sin llamar a sigrid-api salvo `dbo.usu`.
4. `buscar_albaranes` (CIF normalizado, referencia normalizada) → `ya_en_sigrid` si hay alta a mano (R14).
5. Previa: 400/5xx → `clasificar` (§2); `idempotente` → `registrado` (+ `registrado_distinto`, R15); `comparar`
   → `revisar` (R16–R18). 6. Simulación → `simulado` (R19); real → grabación única (R20–R21). 7. Adjunto
   (R22–R23), con el `usu` de `peticion_json` (también en `solo_adjunto`). Todo en `try/finally` (R9).

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

Tabla aparte para el alta, no columnas del merge (el deshacer de sv4 restaura la fila del merge). El producto va en
la línea valorada: el deshacer ya fotografía la fila y el replace de sv6 la descarta como el almacén (R42). Fechas
`VARCHAR(64)` ISO. Lo que lee sv9: `SQL_CABECERA` y `SQL_LINEAS` de `sql_alta_repository.py`. v8 sin DDL nuevo: el
`usu` usado queda en `peticion_json` y el panel lo compara con `approved_by` (R29).

`sql/read` (R14; **v8**, U6: referencia normalizada con `N(x)` = `UPPER` sin espacios, `.`, `-` ni `/`): `SELECT c.ide,
c.cod, c.fec FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = 14 AND d.entcif = ? AND N(d.entref) = ? AND
ISNULL(d.synckey, '') <> ?` (`N` en T-SQL con `REPLACE` anidados; sv9 pasa el número ya normalizado); `existe_concepto`:
`SELECT ide FROM dbo.con WHERE ide = ? AND tip = 14`; **`buscar_usuario`** (v8): `SELECT TOP (1) cod FROM dbo.usu
WHERE cod = ?` (la misma de sigrid-api; se manda el `cod` devuelto). Comprobar `truncated` (`comprobar_truncado`).

## 7. Configuración

sv9: `ALTA_SIGRID_DESDE_UTC` (vacía = no hace nada), `ALTA_SIGRID_COMMIT` (defecto `false`; solo lo cambia el
humano), `ALTA_SIGRID_ESPERA_INCIERTO_MIN` (15), `ALTA_SIGRID_TOLERANCIA_EUR` (0,05),
`ALTA_SIGRID_AVISOS_BLOQUEANTES` (§2), **`ALTA_SIGRID_USUARIO_RESPALDO`** (v8; login de `dbo.usu` para R47, hoy
`pgris`, T0c), `ALTA_SIGRID_EMPIDE` (vacía = defecto de sigrid-api), `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (JSON;
defecto `{"alquiler_maquinaria": "QA9999", "medios_auxiliares": "XA9999", "*": "MA9999"}`),
`SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY` (secreto), `SIGRID_API_DATABASE` (`ruesma`), `PG_*`, Graph/SharePoint
y colas, con los nombres de sv3/sv6. sv4: DESDE, Espera y mapeo, **con el mismo valor que sv9** (una sola variable
del despliegue); `DEFAULT_REVIEWER` solo en local (R49). Mapeo fuera de la lista blanca de sigrid-api (§2) ⇒
`producto_no_permitido` → `error`. En local, `ALTA_SIGRID_COMMIT` no se pone nunca.

## 8. Orden y dependencias

F-051 está en `dev` (T0d) y F-009 desplegada con la escritura abierta desde el 2026-10-07: la única llave de
albaranes es `ALTA_SIGRID_COMMIT`. La v8 (T41–T50) va antes del despliegue en simulación. **Evolución, no bloqueo**:
F-049 (`paride`, H17; mientras, `partida_ambigua` → `no_admitido`), F-061 (`medios_auxiliares`), F-058 (conservar el
producto al revalorar), F-015 (tachadas); ALM impreso sin vincular (H30): F-060/F-007. Despliegue (comun reconstruye
todas las imágenes): sv6 y sv3 → sv9 (DESDE vacía) → sv4 → DESDE en ambos (simulación) → días de simulación →
`ALTA_SIGRID_COMMIT=true` (humano). Antes de real, F-065 fase 1 desplegada (ya lo está, 2026-10-11).

## 9. Reglas del repo y documentación (propuesta; NO se aplica aquí)

`CLAUDE.md`, propuesta: «Sigrid solo vía sigrid-api, nunca SQL directo. Leer: cualquier servicio. Escribir: **solo
sv9**, con el alta de albarán y `concepto-grafico`, nunca `sql/write`, y solo con `ALTA_SIGRID_COMMIT=true`, que
activa el humano. Desde local, nunca.» Igual en `docs/ARCHITECTURE.md` y `docs/referencia/dominio_negocio_albaranes.md`
§5.2. `azure-apps/albaranes.md`: sv9, tabla y consumo de sigrid-api. Contrato (v8): las filas de consumo que citan
`ALTA_SIGRID_USUARIO` (§2 `usu`, cabecera, `concepto-grafico`) se actualizan como consumo, avisando a la sesión sigrid-api.

## 10. Ficheros que NO se tocan

- `sigrid-api` ni su configuración: F-009 y el contrato son de ese repositorio (salvo las filas de consumo, §9).
- sv1, sv2, sv5; la lógica de sv6 (solo su DDL y ORM, §4). `albaran_documents_merge` y `albaran_lines_merge`.
- `ruesma_comun.contratos.familias`, `contexto_linea`, los prompts de IA1 y los evals (F-061); `importes`, `origen_datos`.
- `infra/*.local.ps1`, `.env`: nada de IDs, claves ni URLs reales. `infra/create_capps_sv4.ps1` (Easy Auth ya está).

## 11. Riesgos y decisiones

- **Doble alta**: la cierra la idempotencia de F-009 (`synckey` bajo applock). Además: `FOR UPDATE` y estados,
  una réplica, grabación sin reintento automático, `incierto` no se retoma antes de la Espera y búsqueda por CIF +
  referencia (altas a mano; un número repetido da `ya_en_sigrid`, preferible a duplicar). T0b: `entref` lleva el
  número del proveedor en el 67 % de 2026 (el resto, referencias internas `PROF…`/`PREV…`/`IMPUT…`) y casi nunca se
  repite (2 pares), pero con formato libre (puntos, espacios, barras): sin normalizar, un duplicado se escaparía (U6).
- **Precio neto**: F-009 calcula `tot = cantidad·precio` sin descuento: se manda el unitario **neto** (importe /
  cantidad) a 6 decimales (H14), no el bruto. Signos opuestos (descuento) ⇒ `revisar`; a mano en Sigrid (R39, H8).
- **Nunca se graba aproximado**: lo que la previa no devuelve tal cual se pidió (importe, partida, líneas) va a
  `revisar`; una cuenta analítica que la obra no tiene no se inventa (contrato H10).
- **Producto calculado al leer**, no guardado: sv4 al pintar y sv9 al construir, con la misma función y mapeo; lo
  mandado queda en `peticion_json`. Guardarlo obligaría a sv6 a calcularlo o a reescribirlo si la IA reclasifica.
- **`idempotente` distinto** (H18): queda `registrado` (bloqueado, se corrige anulando, R28) con el motivo
  `registrado_distinto`, no `revisar`: `revisar` desbloquearía un albarán que ya está en Sigrid.
- **Clave de sigrid-api** (decidido 2026-10-01: la de siempre). Riesgo aceptado: quien tenga la clave por defecto
  puede grabar con la escritura abierta; el control es de código y revisión. **Carrera sv4 ↔ sv9**: ambos bloquean
  la fila del merge; revalorar y re-buscar solo publican y comprueban sin cerrojo.
- **Sin valorar no se aprueba** (R37); sin contrato valora a mano el administrativo (sv4 ya lo permite).
- **Usuario (v8)**: la cabecera de Easy Auth no la puede poner el navegador, pero el formulario y el cuerpo sí: por
  eso manda la cabecera (R49). Un UPN que no es `cod` (p. ej. `nombre.apellido@`) o un aprobado anterior a R49
  (`DEFAULT_REVIEWER`) cae al respaldo: el albarán sale en Sigrid a nombre de `pgris`, visible en el panel. No se
  usa el correo de quien pulsa «Solicitar alta» (U2). El respaldo no se valida al arrancar: si no existe,
  `usuario_no_valido` → `error`.
- Descartado: `albaran-directo` (hereda partida, exige `proide`); partir un albarán en dos altas; exigir casar con
  el contrato; campo `almacen` (no existe en F-009 v5.1); producto en una tabla aparte (huérfana al revalorar); DDL
  de la columna en sv3; estado en el merge (deshacer); `sql/write`; casar por `dbo.usu.ele` (vacío; v8).
