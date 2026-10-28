<!-- progress/review_F-104.md -->
Revisión incremental desde 5ba0dc6 (pasada 4). Lo de las pasadas 1–3 queda dado por bueno salvo lo que dice abajo.

# F-104 · Review (pasada 4) · alcance T8–T9

**Veredicto: APPROVED (T8–T9).** El delta es solo `6dbb263`, del líder, y solo documental: `tasks.md`,
`impl_F-104.md` y `current.md`. Ahí se resuelven los dos cambios de la pasada 3, y en el código de la T8
no había nada que objetar.

**Nivel de rigor:** `critico`, declarado en `features.json`. Exige RED, cobertura, mutación con 0 supervivientes
y las MANUAL con su comando y su resultado.

## Pasada 4 (delta `5ba0dc6..6dbb263`)
- `bash harness/init.sh`, tal cual: INIT4.
- **Cambio 1: hecho.** En `impl_F-104.md` § «MANUAL (líder, solo lectura)» quedan registrados:
  - M1: verde el 24-10 y repetida el 28-10;
  - M-D: sv9 `r20261024-1838`, sv4 `r20261024-1841`;
  - M2: SQL de design §6, `:desde` = `2026-10-24T18:21:18Z`, en solo lectura. Por estado, `registrado` 17 y
    `ya_en_sigrid` 1, con `retirado`, `errores_v83`, `con_retencion`, `sin_dato` y `aviso_v83_bloqueo` a 0 en las dos.

  Con el criterio de §6 es **verde**: `retirado` = 0 en todas las filas, ningún `errores_v83` fuera de
  `no_admitido` (no hay ninguno) y `aviso_v83_bloqueo` = 0. En `tasks.md`, M1, M-D y M2 pasan a `[x]` y la nota
  de M2 deja el panel M3 pendiente. El recuento no lo puedo reproducir yo: es una lectura del líder contra Azure,
  fuera de mi rol y sin credenciales en el worktree. Lo tomo como registro de una MANUAL, que es lo que pide §6.
- **El orden, declarado con honestidad.** El informe dice que «la T8 se escribió el 27-10, antes de anotar este
  recuento», y D1 pedía «tras M2 en verde». No lo trato como defecto: la retirada no tiene efecto hasta que se
  fusione y se despliegue la siguiente imagen de sv9 (D1, design §7), y eso pasa después de un M2 en verde ya
  registrado. Lo que la puerta protege, que no se quite el mapeo mientras el código aún llegue, queda cubierto.
  sv9 sigue en `r20261024-1838`, sin la T8.
- **Cambio 2: hecho.** La cabecera de F-104 en `current.md` dice ahora: F-015 desplegada, M2 en verde el 28-10
  con enlace a los recuentos, T8–T9 hechas, a la espera de review, fusión y despliegue de sv9, y M3 cuando pase
  la primera alta con retención. La viñeta «Alcance de esta pasada: T1–T7» que va debajo es histórica, no
  contradice nada y la dejo pasar.

## ¿Bloquea M3 el APPROVED de T8–T9? No.
- R10 dice «CUANDO se haya cumplido R14», y R14, al pie de la letra, incluye el panel (M3). Pero la decisión del
  humano D1 (design §8), el Bloque E de `tasks.md` («solo con M2 en verde») y design §6 concretan la condición en
  el **SQL de M2**. §6 dice expresamente que `con_retencion` = 0 «no es rojo: se repite más tarde».
- M3 verifica R8 y R9: el panel de los Avisos v8.3, que es código de T4, aprobado en la pasada 2. No tiene
  relación causal con la retirada, cuya seguridad depende solo de `retirado` = 0.
- **M3 sí bloquea el `done` de F-104**, porque R14 no está cumplido entero. F-104 debe seguir `blocked` tras la
  fusión y el despliegue, hasta que el líder registre M3 en `impl_F-104.md`. La salida tiene que decirlo:
  `current.md` ya lo dice.

## Checkpoints (pasada 4; los de la 3 que no cambian siguen en `[x]`)
- C1 [x] init.sh exit 0. C2 [x] `current.md` coherente (resuelve el `[ ]` de la pasada 3) · [x] F-104 `blocked`.
- C3 N/A en este delta: no hay código. C3 bis N/A (no entra ningún documento externo). C4 ter N/A (no declara
  ninguna ruta sensible).
- C4 [x] R10 trazado y en verde · [x] MANUAL: M1, M-D y M2 con comando y resultado. M3 sigue pendiente,
  con su comando en design §6 y listado en `current.md` (resuelve el `[ ]` de la pasada 3).
- C4 bis: sin cambios desde la pasada 3, todo `[x]` (RED reproducido; mutación T8 13/13, recalculada y muestreada).
- C5 [x] `tasks.md` todo `[x]`, con M3 anotado como pendiente dentro de M2 · [x] árbol limpio · [x] `features.json`
  sin tocar (`blocked`).

## Pasada 3 (resumen; `5ba0dc6`, CHANGES_REQUESTED)
- init.sh exit 0 (raíz 1919; sv1 205, sv2 485, sv3 1576, sv4 1933, sv5 125, sv6 480 +1 skipped, sv9 1027;
  cobertura N/A con su motivo, porque la T8 solo borra).
- Verificaciones de la T8: sv9 `-k "f104 or f053_clasificador or f053_r18"` **152 passed**; sv4 `-k "f104 or
  f077_r27"` **28 passed**.
- **RED reproducido (M18)** sobre una copia en mi scratchpad, volviendo a poner la línea: **7 failed / 145 passed**,
  los mismos 7 del informe.
- **Mutación T8.** El recálculo puro da 13 mutantes en `clasificador.py`, con las mismas líneas y operadores que
  el informe. La campaña dura 218,7 s (> 60 s), así que no la reejecuté. RM4: `:138` `or ""`→`and ""` da
  **2 failed / 1025** ⇒ muerto. RM1: medido en `4a81091`, y desde entonces no cambia nada de `services/`. RM2:
  16,8 s por mutante con 1 worker frente a una base de 70,9 s, coherente con `-x` y 13/13 muertos. RM3, RM5 y RM6
  no aplican: no hay equivalentes, y la T8 quita un dato, no una guarda; H25 `get(…, _ERROR)` sigue y R10 la prueba.
- **Merge de `dev` (`9c5617d`).** No pisa F-104: solo cambia `BACKLOG.md`, `features.json` (F-069 `done` y F-107),
  `current.md` (F-069), `history.md` y el `tasks.md` de F-069. `git diff 4a81091 HEAD -- services` sale vacío.
- **sv4 no pinta nada roto.** `TEXTOS_MOTIVO_ALTA` conserva el texto del retirado (`alta_sigrid_models.py:106`),
  así que las altas antiguas siguen con su texto. Si llegase uno nuevo, iría a `error` con ese texto (H25). R27 de
  F-077 sigue en verde.
- **azure-apps `ac1f414`.** Correcto, sin secretos, local y sin push. §10 dice «retirado también de sv9 … sale
  con el siguiente despliegue». Con el registro de M2, su «tras verificar que ya no llega» queda respaldado.

## Cobertura requisito → test (delta T8–T9)
| R | Tests / evidencia |
|---|---|
| R10 (sv9) | `test_f104_r10_el_retirado_ya_no_esta_en_la_tabla`, `…_se_clasifica_error[False/True]`, `…_previa_rechazada_por_el_retirado_es_error[simulacion/real]` |
| R10 (sv4) | `test_f104_r10_*` de `test_f104_textos_avisos.py` (texto conservado) |
| R3 | `test_f104_r3_la_tabla_es_la_v82_sin_el_retirado_mas_los_tres_errores`; `test_f053_r18_la_tabla_es_la_del_contrato_v8` |
| R12 | `sv9.md` l. 85–87 y `azure-apps` `ac1f414` §10 |
| R13 / R14 | M1 y M2 registrados en `impl_F-104.md`; **M3 pendiente** (bloquea `done`, no esta review) |

## Cambios requeridos
Ninguno para T8–T9. Pasos siguientes, que no son de esta review: fusionar en `dev` con `init.sh` en verde,
desplegar sv9 (el humano) con la T8, y luego M3 en el navegador cuando `con_retencion` > 0. Solo después, `done`.

## Pasadas 1 y 2 (resumen)
T1–T7 APPROVED en la pasada 2 (`a8fa77b`). Detalle en `git show a8fa77b:progress/review_F-104.md`.

## Automejora (propuesta, no aplicada)
1. Una puerta en `init.sh` que avise cuando una tarea `[x]` cuelga de un bloque «solo con Mx en verde» y esa Mx
   sigue en `[ ]`. Es genérica, iría también a `arnes-base`. Aquí habría ahorrado la pasada 3.
2. En las specs, que la condición de una retirada nombre **la misma** verificación en requirements y en design.
   Aquí R10 decía «R14» (que incluye M3) y D1 decía «M2», y hubo que decidir cuál mandaba. Va en `specs/SPECS.md`
   y es genérico.
