# F-065 · diseño (v5: §5.5, fase 3 bis y sus pasadas 3 y 4)

Rutas relativas a `services/albaranes-front/` (sv4) salvo indicación. Diagnóstico con fichero:línea en
`progress/explore_F-065.md` y `progress/explore_front_detalle.md` (F1–F25). Decisiones: §7.

## 1. Encaje y límite de servicio

- Todo es **revisión humana de la valoración**: sv4 ya escribe `albaran_line_valuations` y
  `contrato_lines_derived` en cada edición. Sin servicio nuevo y sin cambio de contrato con sigrid-api: una Nueva
  va sin vincular con producto genérico (F-053), una Contrato vinculada por `ctrpro_ide`, y N filas al mismo
  `ctrpro` son N líneas (F-009 v8, `contrato_albaranes.md` §2.2).
- **sv6** solo pone la columna `bloqueada` (dueño del esquema de valoración, como `producto_sigrid` en F-053). El
  replace de sv6 no la escribe: vale `false` tras revalorar (F-058).
- **sv9 no cambia**: `SQL_LINEAS` lee todas las filas, también las de `merge_line_id` nulo; no lee `bloqueada`
  (R16). Solo tests de contrato (R10, R36). **comun no cambia** (importes, `es_linea_vinculada`, `esta_valorado`).
- **Partidas de la obra (R27)**: se reutiliza lo que sv4 ya tiene, `SigridLookupClient.fetch_partidas_por_obra` y
  `GET /api/sigrid/partidas` (hojas de `obrparpar`, hoy sin uso: F19). **No se mueve nada a comun**: lo hace F-049
  (rama sin fusionar: T1 lleva la consulta a `ruesma_comun.sigrid.partidas` con `con_obr.emp = 1`, T16–T17 hacen
  que sv4 delegue y lea `NO_TOLERA`). F-065 solo consume el endpoint y trata `ok = false` como «Sigrid no
  responde»; al fusionar F-049 el endpoint conserva su forma (`items[]` con `codigo`, `descripcion`,
  `descripcion_agregada`), así que no hay conflicto de lógica, solo de fichero en `sigrid_lookup_client.py` si
  alguna de las dos lo tocara (F-065 no lo toca).
- sv5 no lee `albaran_line_valuations` de BBDD: nada que listar. Lectores de `bloqueada`: solo sv4.

## 2. Fases y despliegue

1. **Fase 1** (R1–R23): sv6 (DDL) → sv4. Se despliega sola y antes de pasar F-053 a real (`ALTA_SIGRID_COMMIT`)
   y de poner `ALTA_SIGRID_DESDE`. Sin ella, lo que se aprueba no es lo que el administrativo dejó.
2. **Fase 2** (R24–R28): solo sv4. 3. **Fase 3** (R29–R36): solo sv4 + test de sv9. R37 en cada fase.
Una revisión del reviewer por fase, como F-053.

## 3. Ficheros a modificar

| Fichero | Qué cambia | R |
|---|---|---|
| `domain/models/review_models.py` | `MergeDocumentUpdatePayload`: `lines` y `valuation_line_updates` se aceptan y se ignoran (compatibilidad con un `app.js` en caché); `ConciliacionEditBody` → modelo de dominio con `model_fields_set`; función pura `cantidades_tras_editar` (§5.1); `es_fila_manual` (definición de requirements); `DisplayLine.bloqueada`; fase 3: `ParteDivision`, `DivisionBody`, `repartir` | R1, R6–R8, R13, R22, R29–R33 |
| `infrastructure/database/review_repository.py` | `update_document_y_transicion`: sin bloque de líneas, sin `_apply_valuation_line_updates_in_session`, sin recálculo; nunca `approved = False`; R20 antes de aprobar. Retira `_recalc_valuation_importes`, `_cantidades_del_payload`, `_descuentos_del_payload` (y lo que solo usan ellos) | R1–R3, R11, R20 |
| ídem | `_exigir_editable(session, document_id, valuation_line_id=None)`: `_exigir_desbloqueado` (F-053) + aprobado (R4, `AlbaranAprobadoError`) + fila bloqueada (R14, `LineaBloqueadaError`). Sustituye a `_exigir_desbloqueado` en todos los métodos de escritura salvo `set_approved(False)` (desaprobar) | R4, R14 |
| ídem | `update_line_conciliacion(..., campos: dict, bloquear: bool)`: solo los campos presentes; cantidades por §5.1; no-op; `bloqueada = TRUE` si `bloquear`. `bloquear_linea`/`desbloquear_linea` | R6–R10, R13, R15 |
| ídem | `asignar_almacen` (todas) y el borrado masivo: excluyen `bloqueada` y devuelven cuántas saltaron; `set_approved(True)` con R20; `contar_filas_manuales`; `lineas_sin_cantidad_o_importe`; suma leída de las blancas (`precio_neto`) en el detalle | R14, R20–R22 |
| ídem | `add_valuation_lines_from_contrato(..., lineas: list[(contrato_line_id, cantidad)])`: cc = ca = Q, factor 1, importe con `_importe_de_linea` | R23 |
| ídem | `_load_conciliation_map_in_session`: `unitario` de una fila Contrato = `precio_unitario_final`; el del contrato, aparte (`unitario_contrato`) para el `title` | R9 |
| `application/services/review_service.py` | entradas de deshacer de bloquear/desbloquear; `_guardar_y_aprobar` sin snapshots de líneas; errores nuevos | R13, R15 |
| `interface_adapters/web/app.py` | 409 para `AlbaranAprobadoError` y `LineaBloqueadaError` en todas las rutas de escritura (incluidas `valuate`, `re-fetch-contratos`, `/api/undo`, producto); `POST .../lines/{vid}/bloquear` y `.../desbloquear`; `from-contrato` con cantidades (422 si falta); el PATCH de campos con `?bloquear=1`; el aprobar del listado devuelve el aviso de R20; «Desaprobar» desde la ficha vuelve a la ficha (`?volver=ficha`) | R4, R5, R13–R15, R20, R23 |
| `static/app.js` | §5.2 | R1, R8, R9, R12, R13, R18, R19, R21–R23 |
| `templates/document_detail.html` | ficha aprobada en solo lectura + «Desaprobar para editar»; fila bloqueada en solo lectura + «Desbloquear»; precio aplicado; cantidades en el panel «Traer»; datos para R21–R22 | R5, R9, R13, R21–R23 |
| `services/albaran-valoracion-persist/infrastructure/database/schema_contribution.py` (+ ORM si lo declara) | `ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS bloqueada BOOLEAN NOT NULL DEFAULT FALSE` | R17 |
| `docs/ARCHITECTURE.md`, `../azure-apps/albaranes.md` | regla 20; columna `bloqueada`, `line_kind` `manual`/`reparto` | R37 |

Fase 2 toca `app.js` (combo de partidas, origen, sin `confirm` de NUEVA), la plantilla («Contrato») y en el
repositorio `update_line_conciliacion` (regla de origen, §5.3) y `set_line_conciliacion` (`contract_line` copia
partida y precio, R28). Fase 3: `dividir_linea` en el repositorio, ruta y servicio, diálogo F6 (§5.4).

Tests nuevos (`services/albaranes-front/tests/`, SQLite en memoria de `conftest.py`; JS real con node, patrón
`_ejecutar_js` de `test_f051_almacen_front.py`): `test_f065_f1_cabecera.py` (R1–R5), `test_f065_f1_fila.py`
(R6–R12), `test_f065_f1_bloqueo.py` (R13–R17), `test_f065_f1_aprobar.py` (R18–R23), `test_f065_f1_js.py`,
`test_f065_f2_origen.py`, `test_f065_f3_dividir.py`; sv6 `tests/test_f065_bloqueada_ddl.py`; sv9
`tests/test_f065_partes.py`.

## 4. Ficheros que NO se tocan

- sv9 (salvo test), comun, sv5, sv3, sv2; en sv6, solo `schema_contribution.py` (y su ORM).
- `sigrid_lookup_client.py` y la ruta `/api/sigrid/partidas` (F-049 los cambia; F-065 solo los usa).
- La propuesta automática de obra y proveedor (X4, fuera de alcance): en un aprobado ya no guarda por R4, y el
  front no la lanza en la ficha de solo lectura.
- El merge (`albaran_lines_merge`): ninguna ruta de F-065 lo escribe.
- La bandeja salvo el aviso de R20 en «Aprobar» (el flujo de bandeja es F-066).

## 5. Funciones

### 5.1 `cantidades_tras_editar(*, q_nueva, cantidad_albaran, cantidad_convertida, factor) -> (ca, cc)` (pura)

`q_nueva is None` ⇒ sin tocar (R7). Reproducible y `factor ≠ 0` ⇒ `(q/factor, q)`; `cantidad_convertida is None`
y `factor in (None, 1)` ⇒ `(q, q)`; si no ⇒ `(cantidad_albaran, q)` (R6). `update_line_conciliacion` compara
cada campo presente con el actual (`numeros_iguales`, `strip`, `_sanear_descuento`): lo igual se descarta; si no
queda nada, solo completa `cantidad_convertida` nula y, con `bloquear`, marca `bloqueada` (R8, R13). El importe,
cuando algo cambia, sale de `_importe_de_linea(precio, Q, dto)`. Filas legadas (el PATCH viejo dejó `ca = Q` y
`cc` nula): el caso (c) fija `cc = Q`, correcto; la `ca` vieja no se repara (§8).

### 5.2 Front de la fase 1

- `collectPayload` sin `lines` ni `valuation_line_updates` (R1).
- `_camposCambiados(tr)` sustituye a `_conciliaBody`: solo inputs con valor distinto del inicial, números con
  `parseNumEs` y comparados con tolerancia (F16), partida `""` = almacén. El `data-default` del precio es el
  aplicado (R9). Lo usan «Guardar» de fila (`?bloquear=1`) y «Guardar todas» (solo filas sucias, también
  `?bloquear=1`) (R8, R13, R18).
- La celda de importe enseña siempre el `importe_calculado` guardado; al teclear, `syncImporteUnitario` lo
  repinta con `Q × pu × (1 − dto)`, que es lo que guardará el backend (R12), también en las no reproducibles.
- Filas bloqueadas: inputs `readonly`, sin combos, botón «Desbloquear» (POST y `reload`).
- R19: `sendSave` cuenta filas sucias antes del PUT. R21: con `suma_valorada` y `suma_leida` del detalle,
  `confirm` antes de aprobar. R22: `n_filas_manuales` del detalle, `confirm` en «Valorar ahora», «Guardar y volver
  a buscar» y el `change` del combo de contrato (antes del PUT).
- «Traer líneas contrato»: un input de cantidad por casilla marcada; «Incorporar» deshabilitado si falta (R23).

### 5.3 Fase 2: regla de origen al editar (R24–R28)

- `cambia_origen(fila, cambios) -> bool` (pura): Contrato y (partida no vacía ≠ `partida_casada` y ≠ la actual, o
  precio ≠ el actual, o unidad ≠ la actual) ⇒ Nueva. Vaciar = almacén (F-051 R12, sigue Contrato); poner la de la
  casada = sigue Contrato (F-051 R20). Descripción, cantidad, descuento y código externo nunca cambian el origen.
  `update_line_conciliacion` ya convierte en Nueva con `manual_override`; lo que cambia es el `confirm` (fuera) y
  que la decisión use solo los campos presentes (R8) con el precio aplicado (R9).
- Combo de partida: `fetch('/api/sigrid/partidas?obra=…')` una vez; `items` + «Almacén» primero; filtro por
  código y `descripcion_agregada`; teclado con el patrón de `makeLineCombo` (flechas, Enter, Esc); un texto que no
  es de la lista no se guarda. `ok = false` o lista vacía ⇒ solo «Almacén» (+ aviso si `ok = false`).
- «Origen ✎»: `mode=contract_line` copia ahora también `codigo_partida_final` y `precio_unitario_final` de la
  línea elegida (Contrato «cuadra»). El combo de concepto queda como input de texto.

### 5.4 Fase 3: dividir (R29–R36), modelo M1 sin DDL

- `repartir(*, q, ca0, importe0, precio, descuento, partes) -> list[ParteCalculada]` (pura; `RepartoInvalido`
  para R30). `dividir_linea(document_id, valuation_line_id, partes) -> list[int]`: `_exigir_editable` (alta,
  aprobado, bloqueada) → original = parte 1 → por parte k ≥ 2, `INSERT` copiando de la original precio y su
  origen y acuerdo, unidades y su categoría, `factor_conversion`, descuento, `producto_sigrid`, `codigo_externo`,
  `match_method`, `match_confidence_pct`, la descripción (`descripcion_linea` o el concepto de su blanca), con
  `line_kind = 'reparto'`, `merge_line_id` nulo, `parent_merge_line_id`, `importe_source = 'calculated'`; si la
  parte cambia de partida (R32), su propia derivada `manual_override` y `matched` nulo; vacía ⇒
  `almacen_elegido` → `total_valorado` con `ROUND` → commit. Deshacer: `restore` original + cabecera,
  `delete_created` partes y derivadas.
- Display: las `reparto` se agrupan por `parent_merge_line_id` como las sintéticas, pero `_synthetic_to_display`
  conserva `line_kind = 'reparto'` (hoy todo lo no `manual` sale como sintética); «Parte k de N» por `id`.
- F6: `<dialog>` con N (2–20), cantidad y partida (combo de §5.3) por parte, «Falta: X»; F7 y su código se quitan.

### 5.5 Fase 3 bis: ajustes de las MANUAL T19/T27 (v3, 2026-10-12; solo `app.js`, plantilla y CSS de sv4)

- **F7 divide** (antes F6); F6 no hace nada en la ficha (vuelve a ser del navegador). Títulos «(F7)».
- **Última parte automática**: `faltaPorRepartir(q, demás)` (redondeo a 1e-6, no a 1e-3: es la cantidad que se manda)
  la rellena en vivo; input `readonly`, sin tabulación y con otro fondo; `estadoReparto` da el mensaje («Reparto
  completo.», «Sobra: X», «La última parte quedaría a 0.», «Falta la cantidad de la parte k.», «La parte k no puede ser 0
  ni de otro signo.») y si la última va en rojo (0 o de otro signo que Q). «Aceptar» sigue con `repartoValido` sobre
  todas. Al cambiar N se conservan las editables (no el resto viejo). El servidor no cambia.
- **Combo de partida** (`attachPartidaCombo`): `pick` avisa con el `input` de siempre (wireConciliaEdit) sin reabrir
  (el `input` del propio combo lo ignora mientras elige). Con texto nuevo: `scrollTop = 0` y la marcada la da
  `marcadaAlTeclear`: «Almacén» si `esAlmacenTecleado` (prefijo de «almacen» sin acentos, o lo trae entero); si no, la
  primera partida que coincide; si ninguna, ninguna. **v4 (H1, humano 2026-10-13)**: Enter elige la marcada y, sin
  marcada (abrir por foco o clic, o un texto sin coincidencias), NO elige nada: ni POST a `/almacen` ni cambio de
  valor; la lista sigue abierta (así un segundo Enter tampoco guarda la fila ni acepta «Dividir» con un texto que no es
  de la lista); Esc o salir devuelven el valor de antes. Las flechas mandan sobre la marcada.
- **v5 (pasada 4, humano 2026-10-13; fallo de la MANUAL: con las partidas aún llegando de Sigrid la lista seguía
  cerrada, el combo soltaba el Enter y el «Guardar» de la fila guardaba lo tecleado)**: en la partida, Enter SIEMPRE es
  del combo (`preventDefault` + `stopImmediatePropagation`, lista abierta, cerrada o cargando): elige la marcada o nada;
  nunca guarda la fila ni acepta «Dividir» (para eso, «Guardar» o Enter en otra celda). La lista se abre al momento con
  «Cargando partidas…» (sin opciones: Enter no elige) y, al llegar, se pinta con la marcada de lo tecleado; si se cerró
  mientras (Esc, salir), no se reabre. `partidasInvalidas(filas)`: antes de «Guardar» de la fila (botón o Enter en otra
  celda), de «Guardar todas» (no envía NADA si alguna falla) y del aviso de «Guardar»/«Guardar y aprobar» con filas
  sin guardar, una partida CAMBIADA que no es de la lista (vacía = almacén vale; Sigrid caído ⇒ solo almacén; la que la
  fila ya tenía no viaja y no se mira) se marca en rojo (`partida-invalida`, `aria-invalid`, `title` «Partida no
  válida…») y no se envía; al cambiarla, el rojo se quita. En «Aceptar» de «Dividir», lo mismo con la de la propia fila
  también válida. El servidor no cambia (P11).
- **Pasada 5 (CR4 de la review)**: «Guardar» y «Guardar todas» desactivan el botón YA, esperan la lista y, en el mismo
  tick, validan (`partidasMalas(filas, items)`, síncrona) y arman el cuerpo: lo validado es lo enviado aunque la
  casilla cambie durante la espera, y un segundo clic no manda otro PATCH. Salir de la partida antes de que llegue la
  lista no deshace a ciegas: se decide al llegar (O6). «Dividir»: «Aceptar» desactivado = reparto que no vale o envío
  en curso; dos Enter seguidos, un POST (O7).
- **Acciones** (dato del humano: con una fila «Desbloquear» la tabla se ensanchaba y «Guardar»/«Dividir» salían de la
  vista): columna `sticky` a la derecha, opaca, fija (`data-col-fixed`, no se arrastra) y de 200 px; «Borrar» compacto
  («✕» con `title`); sin `nowrap` ni `overflow: hidden` (si se estrecha, los botones bajan de línea). Causa hallada: T24 borró por error el bloque «Columnas de tabla GENÉRICAS» de `app.js`
  (anchos, orden, reordenar, «↺ Columnas»; también la tabla de la bandeja); se restaura tal cual era antes de T24.

## 6. SQL

- **DDL** (sv6, dueño): `ALTER TABLE albaran_line_valuations ADD COLUMN IF NOT EXISTS bloqueada BOOLEAN NOT NULL
  DEFAULT FALSE`; sv4 la misma sentencia en su lista defensiva (`_review_schema_statements`, como
  `codigo_externo`). Lector acoplado: solo sv4. Sin backfill (todas nacen desbloqueadas).
- **DML** de sv4 sobre lo que ya escribe. Valores nuevos sin CHECK: `line_kind = 'reparto'`.

## 7. Decisiones (PARADA 1 del 2026-10-09 y recomendaciones aceptadas)

- **Resueltas por el humano**: cambiar la partida ⇒ Nueva (resp. 1; deja de valer P1 de la v1); al editar no se
  llama a la IA (resp. 2); aprobar no exige filas bloqueadas (resp. 3); combo con todas las partidas de la obra y,
  sin partidas, solo «Almacén» (resp. 4); P2 = separar guardados (R1).
- **Recomendación aceptada**: P3 regla de cantidades (R6); P4 M1 sin DDL para las partes; P5 422 al dividir y
  aviso después (R30, R35); P6 importe prorrateado (R33); P7 confirmación y F-058 amplía (R22); P8 F-016
  absorbida; P9 tres fases.
- **Nuevas, decididas por defecto (a confirmar en la revisión del humano)**: **P10** vaciar la partida (almacén) o
  volver a la de la casada no cambia el origen (F-051 D4/R20, decisiones del humano del 2026-10-05; si ahora
  debiera ser Nueva, se cambia `cambia_origen`); **P11** el combo solo admite partidas de la lista (sigrid-api
  rechazaría otra con `partida_no_encontrada`); con Sigrid caído, solo «Almacén»; **P12** R20 bloquea la
  aprobación con filas sin cantidad o importe (sv9 no las mandaría: hoy se pierden en silencio); **P13** desbloquear
  una fila no exige permiso especial (cualquiera que edite).

## 8. Riesgos y alternativas descartadas

- **Retirar el recálculo del PUT** borra código con tests (F-019, F-036). Las garantías no se pierden: pasan a
  la fila (R6–R8, R11) y T6 las reescribe caso por caso. Descartado mantenerlo «solo si la blanca cambió» (v1):
  ninguna pantalla edita ya las blancas y el humano eligió separar guardados.
- **Hallazgo de la v1, ahora cerrado por R1, R6–R8 y R18**: «Guardar todas» + PUT multiplicaba el importe en
  filas con conversión (×1000 kg→t, ×6 contenedores) y reetiquetaba importes declarados.
- **Datos ya dañados** (O2 de la tabla): filas con `cantidad_convertida` nula ⇒ sv9 `no_admitido`, fallo seguro;
  filas pasadas a Nueva por F3 no se detectan solas. Consulta de solo lectura en producción y decisión del humano:
  fuera de la spec (anotada en F-067).
- **Aprobado = solo lectura**: un administrativo que hoy corrige sobre aprobados tendrá que desaprobar (F-053 R25
  lo impide con alta bloqueante: entonces se corrige en Sigrid). Es lo que pide X3.
- **Partes al final en Sigrid**: sv9 ordena las de `merge_line_id` nulo detrás; sin efecto contable.
- **Conflictos de fusión** previsibles: `features.json`/`BACKLOG.md` con F-064; `review_models.py`, `app.py` y la
  plantilla con F-049 (bloque C toca sv4) — resolver al fusionar, sin solaparse en lógica.
