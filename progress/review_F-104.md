<!-- progress/review_F-104.md -->
Revisión incremental desde a8fa77b (pasada 3). Lo aprobado en las pasadas 1 y 2 (T1–T7) queda dado por bueno.

# F-104 · Review (pasada 3) · alcance T8–T9

**Veredicto: CHANGES_REQUESTED.** El código de la T8 está bien: es correcto, tiene su RED real, la mutación
está limpia y los tests pasan. Lo que falta es la **evidencia de la precondición**. R10 dice «CUANDO se haya
cumplido R14», y el design (D1 y §6 M2) dice «tras M2 en verde» y que «el resultado (solo recuentos por estado)
va a `progress/impl_F-104.md`». En la rama no hay ningún recuento de M2: `tasks.md` tiene M1, M-D y M2 en `[ ]`,
`current.md` sigue diciendo «Espera: su despliegue, luego M2 (líder, solo lectura) y T8», y `impl_F-104.md`
se limita a afirmar «Tras M2 en verde (líder)». En rigor `critico`, una frase no vale como evidencia. Es solo
documental: no hace falta tocar código.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige fase RED, cobertura, mutación con
0 supervivientes y las MANUAL con su comando exacto.

**Delta revisado:** `4a81091` (T8, código y docs), `953dc23` (mutación T8), `934eceb` (T9). `9c5617d` es el merge
de `dev` (`7af0762`) y solo trae contenido ajeno a F-104. En `azure-apps` revisé `ac1f414` (local).

## Verificaciones ejecutadas
- `bash harness/init.sh`, tal cual, en el worktree: **exit 0, «ENTORNO LISTO»**. Raíz 1919; sv1 205,
  sv2 485, sv3 1576, sv4 1933, sv5 125, sv6 480 (+1 skipped), sv9 1027. Cobertura N/A con su motivo; tamaño `[OK]`.
- `pytest services/albaranes-alta-sigrid -k "f104 or f053_clasificador or f053_r18"`: **152 passed**, 875 deselected.
- `pytest services/albaranes-front -k "f104 or f077_r27"` (con el `.venv` de sv4): **28 passed**, 1905 deselected.
- **RED de la T8 reproducido (M18)** sobre una copia (`git archive HEAD`) en mi scratchpad (`rev104t8`), con la
  línea del retirado otra vez en `CODIGOS_CABECERA`: **7 failed / 145 passed**, los mismos 7 que da el informe
  (`f053_r18_la_tabla`, `f104_r10_*` ×5 y `f104_r3_la_tabla`).
- **Merge de `dev` (`9c5617d`).** No pisa nada de F-104: `git diff 953dc23 9c5617d` solo cambia `BACKLOG.md`,
  `features.json` (F-069 `done`, F-107 nueva), `current.md` (bloque F-069), `history.md` y el `tasks.md` de F-069.
  Ningún fichero de `services/` ni de `specs/F-104-*` ni de `progress/*F-104*`. `git diff 4a81091 HEAD -- services`
  sale vacío. F-104 sigue `blocked`, con su `branch` y rigor `critico`.
- **sv4 no pinta nada roto.** `TEXTOS_MOTIVO_ALTA` conserva `proveedor_sin_albaran_previo`
  (`alta_sigrid_models.py:106`, sin cambios), así que las altas antiguas siguen saliendo con su texto. Un alta
  nueva que trajese el código iría a `error` con ese texto como motivo, y eso es justo H25. R27 de F-077 mira
  clasificador → texto, y un texto sin entrada en el clasificador no lo rompe (28 passed). Busqué el código en
  `services/`: aparece solo en el texto de sv4, en los tests de R10 y en `sv9.md`.

## Mutación (T8)
- Recálculo puro: `generar_mutantes` sobre `clasificador.py` entero (141 líneas) da **13 mutantes**, con las mismas
  líneas y los mismos operadores que lista el informe (`:92`, `:93`, `:102`×3, `:104`, `:116`, `:129`×3, `:137`, `:138`,
  `:139`). El informe de la herramienta (`scratchpad/mutacion_F-104_T8.md`) coincide con lo transcrito en
  `progress/mutacion_F-104.md` § T8.
- **Campaña no reejecutada: 218,7 s según el informe (> 60 s).** Me quedé en el recálculo, RM1–RM6 y la muestra
  (RM4): sobre la copia, el mutante `:138` `or ""`→`and ""` con la suite de sv9 entera da **2 failed / 1025
  passed** ⇒ muerto. Más M18, de arriba.
- Coste por mutante: 218,7 × 1 ÷ 13 = 16,8 s. La base de sv9 es 70,9 s, así que la media se queda en el 24 % de la
  base: es un `-x` con 13/13 muertos, no hay salto de orden de magnitud (RM2). La salida fue a scratchpad para
  no pisar el informe de T6. Lo acepto así porque hay transcripción completa con SHA, base, media y workers.

## Checkpoints
- C1 [x] init.sh exit 0 · [x] ficheros del arnés.
- C2 [x] ninguna `in_progress` nueva (F-104 `blocked`) · [x] rama `feature/F-104-codigos-contrato-v83` · [ ] **current.md
  describe la sesión**: dice «Espera: su despliegue, luego M2 (líder, solo lectura) y T8» (l. 19) y, dos viñetas
  más abajo, «T8 y T9 hechas»; ver el cambio 2 · [x] sin `done` nuevas de F-104.
- C3 [x] hexagonal (solo un dato del dominio de sv9) · [x] primera línea con la ruta · [x] sin prints, TODOs ni
  secretos · [x] reglas de dominio: no toca merge/raw, schema ni importes.
- C3 bis N/A (no entra ningún documento externo). C4 ter N/A (`init.sh` no declara ninguna ruta sensible para F-104).
- C4 [x] R10 trazado (`test_f104_r10_*` en sv9 y sv4) y en verde · [x] sin red ni BBDD · [ ] **MANUAL**: R10 depende
  de M2, y M2 no tiene registro (cambio 1).
- C4 bis [x] rigor declarado · [x] RED real de la T8 (7 failed), reproducido por mí · [x] cobertura: `N/A` impreso
  con su motivo («no cambia líneas Python de producción frente a dev»; la T8 solo borra) · [x] totales
  recalculados (13) · [x] más de 60 s: recálculo más muestra, dicho arriba · [x] coste 16,8 s/mutante con 1 worker ·
  [x] sin «CAMPAÑA NO VÁLIDA», sin veredicto = 0 · [x] RM1: medido en `4a81091`, y desde entonces no cambia nada
  de `services/` · [x] RM2 coherente · [x] RM3: ninguno de los 13 es equivalente · RM5 N/A (sin equivalentes) ·
  RM6 N/A (la T8 quita una entrada de datos, no una guarda; la guarda H25 `CODIGOS_CABECERA.get(…, _ERROR)`
  sigue y R10 la prueba) · [x] la regla de la campaña manual, cubierta por M18, reproducido · [x] 0 supervivientes
  · [x] «Evidencias» con las filas T8 y T9 y los workers.
- C5 [ ] **tasks.md**: T8 y T9 están en `[x]` con sus commits, pero M1, M-D y M2, que son su precondición («Bloque E
  · solo con M2 en verde»), siguen en `[ ]` (cambio 1) · [x] árbol limpio · [x] `features.json`: `blocked`, como pidió el líder.

## Cobertura requisito → test (delta)
| R | Tests |
|---|---|
| R10 (sv9) | `test_f104_r10_el_retirado_ya_no_esta_en_la_tabla`, `…_se_clasifica_error[False/True]`, `…_previa_rechazada_por_el_retirado_es_error[simulacion/real]` |
| R10 (sv4) | `test_f104_r10_*` de `test_f104_textos_avisos.py` (texto conservado) |
| R3 | `test_f104_r3_la_tabla_es_la_v82_sin_el_retirado_mas_los_tres_errores`; `test_f053_r18_la_tabla_es_la_del_contrato_v8` |
| R12 | `sv9.md` l. 85–87 y `azure-apps` `ac1f414` §10, revisados en el diff |
| R14 | MANUAL: **sin registro** (cambio 1) |

## azure-apps `ac1f414`
Correcto, sin secretos, local y sin push. La viñeta de §10 pasa de «sin desplegar» a «sv9 y sv4 desplegados el
2026-10-24», dice «retirado también de sv9 … tras verificar con la F-015 desplegada que ya no llega» y aclara que
la retirada sale con el siguiente despliegue de sv9. Esa afirmación solo será cierta cuando exista el registro de
M2 del cambio 1, y no hace falta tocarla. En el árbol de `azure-apps` hay un `M datamart_seg_anual.md` sin commit,
ajeno a F-104.

## Cambios requeridos
1. **Registrar M2 (y cerrar M1 y M-D) antes de dar la T8 por buena.** En `progress/impl_F-104.md`, en la sección
   T8 o en una sección «M1 / M-D / M2» encima de ella, van: la fecha `:desde` (el despliegue de F-015, `60db955`,
   2026-10-24 18:21:18 UTC) y la tabla de recuentos por `estado` del SQL de design §6 M2 (`altas`, `retirado`,
   `errores_v83`, `con_retencion`, `sin_dato`, `aviso_v83_bloqueo`), con el criterio de verde aplicado. En `tasks.md`,
   marcar `[x]` M1 (verde el 24-10, según `current.md`), M-D (sv9 `r20261024-1838`, sv4 `r20261024-1841`) y M2. Si
   `con_retencion` = 0, M3 queda pendiente (design §6: «se repite más tarde, no es rojo») y se anota así. Lo hace
   el líder, que es el dueño de M2. **Si M2 no se ha ejecutado de verdad**, se ejecuta ahora en solo lectura. Si
   `retirado` > 0, se revierte `4a81091` y `sv9.md` y `azure-apps` `ac1f414` vuelven a «sigue mapeado».
2. **`progress/current.md` l. 19**: la cabecera de F-104 sigue diciendo «Espera: su despliegue, luego M2 … y T8».
   Debe decir lo que pasa ahora: F-015 desplegada, M2 hecho (con el enlace al registro del cambio 1), T8–T9 en la
   rama en review, y que falta fusionar y desplegar sv9 con la siguiente imagen (D1).

No hay cambios de código. En la pasada 4 me basta con mirar el delta documental y repetir `init.sh`.

## Pasadas 1 y 2 (resumen)
T1–T7 APPROVED en la pasada 2 (`a8fa77b`). La pasada 1 rechazó solo porque la campaña manual no se podía reproducir;
se corrigió en `1a66c6b`. Reproduje 6 de las 17 filas manuales. El detalle completo está en `git show a8fa77b:progress/review_F-104.md`.

## Automejora (propuesta, no aplicada)
Las tareas condicionadas por una MANUAL («Bloque E · solo con M2 en verde») no tienen ninguna puerta que mire el
orden. `init.sh` podría avisar cuando en un `tasks.md` hay una tarea `[x]` en un bloque «solo con Mx en verde»
y esa Mx sigue en `[ ]`. Es genérico, iría también a `arnes-base`, y aquí lo habría cazado antes de llegar a review.
