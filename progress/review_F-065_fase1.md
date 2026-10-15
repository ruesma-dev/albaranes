<!-- progress/review_F-065_fase1.md -->
Revisión completa (pasada 1) de la fase 1, desde `abec7f8` (spec v2) hasta `02ce1c8` (HEAD)

# F-065 · fase 1 (R1–R23) · review

- **Veredicto: APPROVED**: sin cambios requeridos; 7 observaciones no bloqueantes y decisiones para el humano.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`). Exige fase RED, cobertura ≥ 80 % de lo
  cambiado, campaña de mutación completa con 0 supervivientes sin justificación aceptada y MANUAL con comando exacto.
- Servicios: sv4 (código), sv6 (DDL/ORM de `bloqueada`), sv9 (test); docs y `azure-apps` `3db4274` (contrastados).

## Verificación ejecutada por el reviewer (resultado real)
- `bash harness/init.sh` en el worktree: **exit 0**, `ENTORNO LISTO`; raíz `1083 passed`; `PUERTA COBERTURA: 100.0%
  de 309 líneas cambiadas (309/309, umbral 80%, nivel critico)`; tamaño en topes. Como `init.sh` sirvió sv4/sv6/sv9
  de caché, las relancé sin caché, una a una: **sv4 1015 passed** (78,8 s), **sv6 295 passed**, **sv9 526 passed**.
- **METALFIRE falseado en una COPIA** (scratchpad, `sv4_copia`): reinyecté en el PUT el `_recalc_valuation_importes` y
  los mapas del payload de `abec7f8`, al pie de la letra. `test_f065_f1_cabecera.py` ⇒ **3 failed**:
  `test_f065_r2_metalfire_...` (`assert (8.0, 8.0) == (6.0, 6.0)`), `test_f065_r1_put_con_las_blancas_no_toca_las_filas`
  y el guardián R11. Segunda falsificación (el PATCH vuelve a dejar `cantidad_convertida = NULL`, el defecto que sv9
  rechazaría): **15 failed** entre `test_f065_f1_fila.py`, `..._cabecera.py` y F-036. El árbol real no se tocó.
- **Mutación (recálculo independiente, RM1)**: `alcance_de_feature('F-065')` = rama `a094f44..feature/F-065` (`a094f44`
  = `dev`), **6 ficheros, 925 líneas**; `generar_mutantes` ⇒ **131** (1/0/7/37/76/10 por fichero). Coincide con el
  informe. Desde el SHA medido (`d4fe841`) hasta HEAD solo cambian `progress/`, `tasks.md` y tests: ningún fichero
  del alcance. **Campaña no reejecutada: 1693,2 s según el informe** (> 60 s): vale el recálculo puro + RM1–RM6.
- **RM2**: coste por mutante = 1693,2 × 4 ÷ 131 = **51,7 s** frente a línea base sv4 84,5–89,4 s (0,6×, sin salto de
  orden de magnitud; coherente con `-x` y 131/131 muertos). Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto» = 0.
- **RM3**: ningún mutante declarado equivalente sale muerto (la campaña válida no tiene equivalentes).
- **RM5**: N/A justificado: 0 equivalentes en la campaña válida. Los 5 de la campaña 1 se eliminaron reescribiendo el
  código; comprobé que las reescrituras **no cambian el comportamiento** (punto 9 abajo).
- **RM6**: dos reescrituras quitan una comprobación. (a) Clave de `orden_filas_ficha` sin `merge_line_id`: el
  invariante «una sintética nunca trae `merge_line_id`» lo garantiza QUIEN CONSTRUYE EL DATO, sv6
  (`valuation_builder.py:1786`, `LineValuationRecord(merge_line_id=None, ...)` en `_build_synthetic_line`); y el cargador de
  sv4 (`review_repository.py:1228-1232`) ordena igual dentro de cada grupo. (b) `_mismo_numero` sin la guarda
  `is None`: el `except TypeError` devuelve lo mismo para toda combinación (None/None ⇒ igual; None/número ⇒ distinto;
  ilegible ⇒ distinto). Ninguna defensa se perdió.

## Checkpoints

- **C1** [x] `init.sh` exit 0 · [x] ficheros del arnés presentes.
- **C2** [x] una sola `in_progress` (F-065; F-053 `blocked`) · [x] rama `feature/F-065-lineas-editadas-y-reparto` ·
  [x] `current.md`: el bloque de F-065 está al día (ver O7: un resto antiguo de F-053 que viene de `dev`) ·
  [x] `done` con resumen en `history.md` (sin `done` nuevos).
- **C3** [x] hexagonal: el dominio (`review_models`) solo importa dominio (`domain.services.almacen`); SQL en el
  repositorio; rutas solo traducen errores · [x] primera línea con ruta en todos los ficheros tocados · [x] sin
  `print`/TODO/secretos (los `console.log` están dentro de los harness JS de los tests) ni dependencias nuevas ·
  [x] trampas: (1) solo tablas merge; (2) lectores de `bloqueada`: solo sv4 (sv3, sv5, comun y sv9 no la leen;
  comprobado con grep); (3) cantidades: Q siempre en la unidad del precio, `cantidades_tras_editar` no inventa
  conversiones; las sintéticas entran en `suma_filas` y en R20 si la ficha las pinta (decisión explícita, D5).
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: la puerta dice que no toca rutas sensibles.
- **C4** [x] R1–R23 con test `test_f065_rN_*` (tabla abajo), todos en verde · [x] sin red ni BBDD (SQLite en memoria,
  plantilla y `build_app` reales con servicio falso, JS con node) · [x] MANUAL T13 en `progress/current.md` con el
  comando exacto.
- **C4 bis** [x] rigor `critico` declarado · [x] fase RED con trazas reales (§5: T1 `144 failed, 14 passed`, T2, T6,
  T9 y T10 rompiendo sv9 en una copia) · [x] cobertura `[OK]` 100 % · [x] mutación verificada (arriba) · [x] muertos:
  recálculo puro + RM1–RM6, dicho explícitamente · [x] coste por mutante 51,7 s (> 1 s) · [x] sin cabecera de no
  válida ni «sin veredicto» · [x] RM1 SHA completo `d4fe841c…` y alcance idéntico al de HEAD · [x] RM2 · [x] RM5 N/A
  justificado · [x] RM6 · N/A campaña manual (la automática dio 131 mutantes) · [x] 0 supervivientes · [x]
  «Evidencias» con los cuatro números y 4 workers · [x] ningún N/A sin motivo.
- **C5** [x] T0–T12 `[x]` con un commit `F-065 Tn:` por tarea (T13 MANUAL y T14 son del humano) · [x] árbol limpio ·
  [x] `features.json` = `in_progress` (fases 2 y 3 pendientes).

## Cobertura requisito → test (todos verdes)

| R | Tests | R | Tests |
|---|---|---|---|
| R1 | `test_f065_r1_*` (×5, repo y JS) | R13 | `test_f065_r13_*` (×8, repo/servicio/portal) |
| R2 | `test_f065_r2_metalfire_...` (falla sin el arreglo) | R14 | `test_f065_r14_*` (×9, incl. JS de masivos) |
| R3 | `test_f065_r3_*` (×3) | R15 | `test_f065_r15_*` (×3, deshacer y JS) |
| R4 | `test_f065_r4_*` (×8; 14 escrituras y 12 rutas parametrizadas) | R16 | `test_f065_r16_se_aprueba_sin_ninguna_fila_bloqueada` |
| R5 | `test_f065_r5_*` (×5, plantilla y `volver=ficha`) | R17 | sv6 `test_f065_bloqueada_ddl.py` (×6) + `test_f065_r17_*` (×5) |
| R6 | `test_f065_r6_*` (dominio, 10 casos a/b/c; repo ×3) | R18 | `test_f065_r18_*` (JS) |
| R7 | `test_f065_r7_*` | R19 | `test_f065_r19_*` (JS) |
| R8 | `test_f065_r8_*` (×22: dominio, repo y JS) | R20 | `test_f065_r20_*` (×7) |
| R9 | `test_f065_r9_*` (×5) | R21 | `test_f065_r21_*` (×6) |
| R10 | `test_f065_r10_*` sv4 ×2 + sv9 `test_f065_partes.py` (×4) | R22 | `test_f065_r22_*` (×7, tres vías) |
| R11 | `test_f065_r11_*` (×4) + F-019/F-036 reescritos | R23 | `test_f065_r23_*` (×8) |
| R12 | `test_f065_r12_*` (×3, plantilla y JS) | | |

## Los nueve puntos del líder

1. **Nada vuelve a lo valorado**: el PUT no toca `albaran_line_valuations` (ni merge ni derivadas): `foto()` antes y
   después en los tests R1; Guardar, Guardar y aprobar, autoguardados de obra/proveedor/contrato, paso 1 de «Valorar
   ahora» y «Guardar y volver a buscar» van todos por ese PUT. METALFIRE falla sin el arreglo (falseado arriba).
2. **Cantidades para sv9**: R6 (a)/(b)/(c) correctas, la convertida nunca queda nula (también sin cambios, R10);
   kg↔t y contenedores probados en dominio, repositorio y sv9 (`[sin_conversion|contenedores|toneladas_a_kg]`, más
   la legada que sv9 rechaza). Nota: en una fila **Nueva** sv9 manda `cantidad_albaran` (F-053), así que en el caso
   (c) Sigrid recibe la cantidad del albarán con `precio = importe / ca`: total correcto; es lo que dice la spec.
3. **PATCH solo de lo cambiado** (front y backend) y precio aplicado: una fila Contrato guardada sin cambios conserva
   precio, origen y valorado (`test_f065_r9_guardar_sin_tocar_...`, `test_f065_r8_sin_cambios_*`).
4. **Aprobado = solo lectura**: `_exigir_editable` en todos los métodos que escriben salvo desaprobar (guardián
   estructural + 14 operaciones + 12 rutas); el PUT nunca pone `approved = False`. Concurrencia: `FOR UPDATE` del merge
   y, después, en sentencias aparte, el alta, `approved` y `bloqueada`; ningún `FOR UPDATE` con `JOIN`. Revalorar y
   volver a buscar miran sin cerrojo, como ya hacía F-053 (design §11).
5. **Bloqueo**: DDL en sv6 (`schema_contribution.py:273`, ORM con `server_default false`, el replace no la nombra) y
   sentencia defensiva en sv4; almacén a todas `AND NOT bloqueada` con recuento; borrar todas se las salta en el
   front y el backend da 409 por fila; bloquear/desbloquear con deshacer.
6. R18–R23 correctos (tabla). R20 en ficha y listado; R23 exige cantidad ≠ 0 (422) y deja filas válidas para sv9.
7. **Tests reescritos**: los 7 de `test_f019_r23_cableado_payload.py` vigilaban mapas que ya no existen; su garantía
   («ausente = no cambia; null = vaciar») la fijan `test_f065_r8_*`. F-036 pasa de 31 a 25: se retiran 6 que solo
   probaban helpers borrados (razones/revisión del recálculo); el resto, caso a caso como en la tabla §6 del informe
   (comprobado nombre por nombre). F-019 16→16. F-051/F-053: cambios de firma y de semántica justificados en cada test.
8. **Decisiones**: razonables D1, D2 (más correcta que el design), D3, D4, D6, D7 y D9. **A corregir o decidir**: D8
   (O1) y el hueco de D5 (O2). Ver abajo.
9. **Reescrituras por equivalentes**: no cambian el comportamiento (RM6 arriba; el redondeo quitado de las sumas solo
   afectaba a la cola binaria del JSON: el aviso redondea la diferencia y pinta 2 decimales).

## Observaciones (no bloquean; numeradas, con severidad)

1. **Media · D8 · «Solo volver a buscar» descarta lo manual sin confirmar** (`static/app.js:2633`,
   `handleRefetchOnly`). Llama al mismo `re-fetch-contratos` que «Guardar y volver a buscar», y sv3 encadena la
   revaloración: es la intención de R22 aunque la spec enumere tres vías. Recomendado: `if (!confirmarRevalorar())
   return;` al principio, con su test. Decide el humano.
2. **Baja · hueco de spec (D5): filas sin línea de contrato ni derivada.** La ficha no las pinta, no se editan
   (`review_repository.py:1929` ⇒ 404) y R20 se las salta (`:3805`), pero sv9 las mandaría como sin vincular si
   tienen importe. Hoy sv6 garantiza que no existen (`valuation_builder.py:1131-1180`, «ninguna línea sin salmón»),
   así que solo aparecerían por datos legados o corruptos. Recomendado (humano): que R20 también las rechace con su
   propio aviso («revalora»), fallo seguro; o pintarlas en F-067.
3. **Baja · el total sin `ROUND` en tres escrituras previas** (`review_repository.py:1850`, `:2326`, `:2551`:
   reapuntar, borrar fila, casar blanca), mientras el helper nuevo `_recalcular_total_in_session` sí redondea (F-019
   R26). Preexistente; reutilizar el helper es una línea en cada sitio (F-067 o fase 2).
4. **Baja · `asignar_almacen_todas_con_saltos`** (`review_service.py:510`) cuenta las saltadas con una foto fuera de
   la transacción: con una edición concurrente el número podría desviarse en uno. Solo es el mensaje.
5. **Baja · aprobar un aprobado no es del todo no-op (D1)**: `set_approved(True)` reescribe `approved_at_utc` y
   `approved_by` (`review_repository.py:3979`). Preexistente; con R4 convendría que fuera no-op real.
6. **Info · F7 (duplicar)** arma el cuerpo con TODOS los campos (`app.js:3151`): con R8, `null` = vaciar. Es inocuo
   sobre la fila recién creada (todo vacío), y la fase 3 quita F7; si F7 sobreviviera, pasarlo a `_camposCambiados`.
7. **Info · `progress/current.md:26`** trae un bloque viejo de F-053 «`in_progress`» que contradice el de la línea 76
   (`blocked`). Viene de `dev`, no de esta rama: podar al fusionar.

## Para el humano (junto con P10–P13)

- Confirmar D1 (papelera fuera de R4), D3 (editar descripción no recalcula el importe), D9 (editar Q en una fila no
  reproducible ya no la manda a revisión: lo tecleado YA son contenedores) y decidir O1 (D8) y O2 (hueco de D5).
- Consecuencia de R4 en el flujo de F-053: con un alta `no_admitido`/`revisar` hay que **desaprobar, corregir y volver a
  aprobar** (el paso a aprobado vuelve a pedir el alta). Coherente con X3; conviene contárselo a Administración.
- Pendiente: MANUAL T13 (local), fusionar en `dev` con `init.sh` y desplegar **sv6 → sv4** antes de F-053 real.

## Automejora (propuesta, no aplicada)

- `reviewer.md`: `init.sh` sirve las suites de servicio de caché; decir que el reviewer relanza sin caché las de los
  servicios que toca la feature (como aquí), o dar a `init.sh` un modo `--sin-cache`.
