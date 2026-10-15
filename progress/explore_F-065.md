# Diagnóstico «correo Milagros» (METALFIRE, CTSU25/0359) — rama `dev` (b380b43)

Rutas relativas a `services/albaranes-front/` (sv4) salvo indicación.

Correo (2026-10-09, administración de obra): (1) tiene que repartir las unidades del albarán en 3 partidas; (2) «si le
cambio las partidas me arrastra del contrato; si le doy que no me la cambie me la pone como nueva»; (3) puso 6/7 en las
dos líneas de puerta y añadió con «Traer líneas contrato» una tercera con 5; «Guardar todas» lo dejaba bien, pero
«Guardar y aprobar» devolvió las dos primeras a 8 y 10 (lo leído) y respetó el 5 ⇒ 23 unidades en vez de 18.

## 1. Causa del fallo de «Guardar y aprobar» — confirmada la hipótesis (a)

### «Guardar todas» (`templates/document_detail.html:585`, JS `static/app.js:1251-1305`)
- PATCH por fila a `/api/documents/{id}/lines/{vid}/conciliacion/campos` con `_conciliaBody(tr)` (`app.js:1100-1114`).
- `interface_adapters/web/app.py:1481-1509` → `ReviewService.update_line_conciliacion` (`application/services/review_service.py:415-454`) → `ReviewRepository.update_line_conciliacion` (`infrastructure/database/review_repository.py:1815-2114`).
- Solo escribe `albaran_line_valuations` (`review_repository.py:2083-2100`): `cantidad_albaran = 6/7`, **`cantidad_convertida = NULL`**, importe 690/805, `importe_source='calculated'`. **No toca `albaran_lines_merge`** (sigue 8/10).
- La línea de «Traer líneas contrato» (`app.py:1687-1726`, `review_repository.py:2589-2721`) nace `merge_line_id = NULL`, `line_kind='manual'`, cantidad vacía, `matched_contrato_line_id` puesto (`2692-2697`).

### «Guardar y aprobar» (`document_detail.html:246`; `app.js:1970` → `sendSave(true)` `app.js:1944-1967`)
- PUT `/api/documents/{id}` con `collectPayload(true)` (`app.js:1916-1942`); `payload.lines` = `collectLinesAndValuationUpdates()` (`app.js:1862-1900`), que reenvía **tal cual** `window.__documentData.lines` (las líneas blancas del merge, 8 y 10; comentario `app.js:1863-1869`). `valuation_line_updates` vacío.
- `app.py:1204-1243` → `ReviewService.guardar` (`review_service.py:220-238`) → `_guardar_y_aprobar` (`176-218`) → `ReviewRepository.update_document_y_transicion` (`review_repository.py:3411-3623`).

### Dónde se pisa
1. `review_repository.py:3516-3535` reescribe las líneas del merge con lo mismo (inocuo).
2. `3596-3601`: `_recalc_valuation_importes(new_line_quantities=self._cantidades_del_payload(payload), new_line_discounts=self._descuentos_del_payload(payload))`.
3. `_cantidades_del_payload` (`3631-3642`) ⇒ `{merge_line_id: cantidad}` de TODAS las blancas: `{id1: 8, id2: 10, idPORTES: 1}`.
4. `_recalc_valuation_importes` (`3836-4081`): las valoradas sin `merge_line_id` se saltan (`3891-3893`) ⇒ la tercera conserva el 5; las otras: `nueva_cant_albaran = 8 / 10` (`3898-3901`); el guardián F-019 R24 (`3994-4002`) ve cambio (6≠8) y no protege; `UPDATE albaran_line_valuations SET cantidad_albaran = 8/10, cantidad_convertida = NULL, importe_calculado = 920/1150` (`4009-4027`); se añade `front_sin_cantidad_convertida` (`4037-4044`).
5. Total: 920 + 1150 + 575 + portes = 23 puertas.

Causa de fondo: desde la «TANDA 2A» las blancas son de solo lectura y el PUT las reenvía solo para no borrarlas, pero el
repositorio sigue tratando `payload.lines[].cantidad` como «lo que acaba de editar el revisor» (comentarios
`3587-3594`, `3896-3897`). Cualquier PUT resincroniza las salmón ligadas por `merge_line_id` con la lectura de la IA.
- El **descuento** cae por la misma vía (`_descuentos_del_payload`, `3644-3666`).
- **«Deshacer» no lo arregla**: el snapshot de ese guardado solo guarda cabeceras (`review_service.py:186-193`).

### ¿Afecta al «Guardar» simple? Sí, igual
`saveBtn` → `sendSave(false)` (`app.js:1969`), y todos los PUT con `collectPayload`: autoguardado al elegir obra o
proveedor (`app.js:1696`), paso 1 de «Valorar ahora» (`2062-2066`; ahí da igual), `persistSelection` al elegir contrato
(`2360-2365`), «Guardar y volver a buscar» (`2523-2528`). **No pisa** el «Aprobar» del listado
(`POST /documents/{id}/approve`, `app.py:766` → `set_approved`, `review_repository.py:4395-4435`).

### Hipótesis (b) descartada
Aprobar no publica `q-valoracion`: `_pedir_alta_si_toca` (`review_service.py:325-358`) → `notify_document_approved`
(`infrastructure/colas/colas_orchestrator_client.py:105-136`) publica `MensajeFeedback(accion="alta")` en `q-feedback`.

## 2. Qué da de alta sv9 (F-053)

sv9 lee **`albaran_line_valuations`** (`services/albaranes-alta-sigrid/infrastructure/database/sql_alta_repository.py:93-106`,
`SQL_LINEAS`): `cantidad_albaran`, `cantidad_convertida`, `importe_calculado`, matched/derived, `codigo_partida_final`,
`producto_sigrid`; del merge solo `line_index`, `concepto`, `contexto_linea_json` (LEFT JOIN). Las manuales entran al
final (`validador_alta.py:134-142`). ⇒ el 8/10/5 sería lo que vería sv9.

**Segundo defecto:** una línea vinculada usa la **cantidad convertida** (`validador_alta.py:116-117`; spec
`requirements.md:17`, R10 `:53`); si es NULL ⇒ `cantidad_sin_convertir` ⇒ `no_admitido` (`validador_alta.py:219-220`).
sv4 deja `cantidad_convertida = NULL` en el PATCH (`review_repository.py:2087`), en «Traer líneas contrato»
(`2692-2695`) y en el recálculo del PUT (`3920-3943`, `4021`). ⇒ **cualquier línea vinculada editada a mano en sv4
no se puede dar de alta**; y si se arregla eso sin arreglar el punto 1, las 23 puertas llegarían a Sigrid.

## 3. Cambiar la partida de una línea SIGRID

- **(i) Combo de partida** (lista líneas de contrato, «Almacén (sin partida)» primera; `app.js:884-897, 949-1076`):
  `pick()` (`984-1005`) → PATCH `.../conciliacion` `mode=contract_line` (`app.js:173-209` → `app.py:1445-1474` →
  `review_repository.py:1693-1729`): reapunta `matched_contrato_line_id` y trae precio/importe, **no toca
  `codigo_partida_final`, `unidad_contrato` ni `descripcion_linea`** (O1 de F-051). El comentario `app.js:992-996`
  no se corresponde con el backend. ⇒ «me arrastra del contrato».
- **(ii) Teclear otra partida y guardar** (`review_repository.py:1957-1977, 2004-2037`): si hay casada y la partida
  nueva ≠ actual y ≠ de la casada ⇒ `contrato_lines_derived` `manual_override`, `matched = NULL` ⇒ **NUEVA** (igual al
  cambiar unidad o precio). Regla de junio 2026 (docstring `1831-1842`). Excepciones F-051: vaciar = almacén (R12,
  `1959-1962`); la partida de la casada sigue Sigrid (R20, `1965-1972`).
- El `confirm()` «pasará a NUEVA» solo lo lanza el «Guardar» de fila (`app.js:1188-1201`, `cambiaIdentidad`
  `1118-1131`). **«Guardar todas» no pide confirmación** (`1253-1304`): si cancela el confirm, el valor queda en el
  input y «Guardar todas» lo manda ⇒ NUEVA sin avisar. ⇒ «si le doy que no me la cambie me la pone como nueva».
- F-053: `es_linea_vinculada` (`services/albaranes-comun/ruesma_comun/alta_sigrid.py:119-140`) exige matched, sin
  derived, con `sigrid_ide`, del contrato de la valoración. Una NUEVA va sin vincular (producto genérico MA9999,
  `alta_sigrid.py:44-48,167-186`). F-053 **sí admite** vinculada con partida propia (`ctrpro_ide` + `partida =
  codigo_partida_final`, `validador_alta.py:262-277`; `requirements.md:62-65`): lo impide la regla SIGRID→NUEVA de
  sv4. Si Sigrid acepta «ctrpro de una partida imputado a otra» lo decide el humano (F-009 v8 «partida por línea»).

## 4. Repartir una línea en varias partidas

Hoy: «Añadir línea» (`app.js:1307-1336` → `app.py:1614-1632` → `review_repository.py:2470-2584`, NUEVA suelta);
«Traer líneas contrato» (`review_repository.py:2589-2721`, vinculada con la partida del contrato y cantidad vacía:
misma partida en las tres; cambiarla ⇒ NUEVA; `cantidad_convertida` NULL); F7 «duplicar» (`app.js:3035-3119`, copia
NUEVA); rebajar la original ⇒ el siguiente PUT lo deshace. Las manuales se pierden con «Valorar ahora»
(`review_repository.py:2484-2485`; F-058).

Faltaría para un «dividir línea» (p. ej. `POST /lines/{vid}/dividir {partes:[{cantidad, partida}]}`):
1. Arreglar antes el punto 1.
2. Hijas con `matched_contrato_line_id`, `precio_unitario_final`, `factor_conversion`, `unidad_contrato` y
   `cantidad_convertida = factor × cantidad` (vinculadas para sv9).
3. Dos valoraciones con el mismo `merge_line_id` no caben en la ficha (`lines_by_merge_line_id`,
   `review_repository.py:1218, 1319-1322`; `add_conciliacion_for_merge_line` `2384`): hijas con `merge_line_id`
   NULL + `parent`/`split_of` (DDL en sv6, dueño del esquema) o cambiar la clave del pintado.
4. Cambiar la partida de una hija sin volverla NUEVA (relajar `1965-1977`), previa confirmación de que Sigrid lo admite.
5. Invariante: suma de hijas = cantidad original (aviso o bloqueo).
6. Sobrevivir a revalorar (F-058).

Backlog: **F-016** «Reparto de una línea del albarán entre varias partidas» (`pending`, rama
`feature/F-016-linea-multipartida`; caso Feymaco 108 = 54 + 54; cita F-013, hoy sustituida por F-053) es este caso.
F-058 (revalorar no pierde lo manual) es necesaria. F-049, F-060, F-007 no cubren el reparto. **Ninguna ficha recoge
el punto 1 ni el `cantidad_convertida` NULL del punto 2.**

## 5. Tests

No hay test de «PATCH de línea valorada y luego PUT/aprobar». Fijan el comportamiento actual (la cantidad del payload
del merge manda en el recálculo), escritos cuando la blanca era editable:
`tests/test_f019_r23_cableado_payload.py:89`, `tests/test_f019_r23_r26_recalculo_importe.py:299`,
`tests/test_f036_r1_r8_conversion_no_reproducible.py:456`. `tests/test_f051_almacen_front.py:1341` solo comprueba
`_conciliaBody`; `tests/test_f053_t19_cerrojo.py:292` la transición; sv9 `tests/test_f053_validador.py:145`
`cantidad_sin_convertir` aislado.
