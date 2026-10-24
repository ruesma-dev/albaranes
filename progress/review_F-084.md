<!-- progress/review_F-084.md -->
Revisión incremental desde c4bf6f3 (pasada 3) · `git diff c4bf6f3..aed276e` · lo aprobado hasta `c4bf6f3` queda dado por bueno

# F-084 · Review del reviewer: el banco de evals valora de verdad

## Veredicto

**APPROVED.** Las condiciones 1–4 de la pasada 2 están aplicadas, el delta es solo texto (spec,
informes, `current.md`) y `bash harness/init.sh` sale en verde. F-084 se puede cerrar contra
`CHECKPOINTS.md`; antes de integrarla en `dev` hay que tener en cuenta O6 (abajo).

Historial de pasadas anteriores: pasada 1 (APPROVED para lanzar T12, HEAD `fbbabd7`) en
`git show a2aeaaf:progress/review_F-084.md`; pasada 2 (CHANGES_REQUESTED solo por documentación,
HEAD `c4bf6f3`, con la verificación completa de T14, T16 y T17, mutación y recuento de R28) en
`git show aed276e:progress/review_F-084.md`.

## Nivel de rigor

`critico` (declarado): fase RED, cobertura ≥ 80 %, mutación completa con 0 supervivientes, RM5.
Esta pasada no toca ningún `.py`, así que no hay que remedir la mutación (ver «Lo verificado»).

## Lo verificado por el reviewer

- **`bash harness/init.sh`** (worktree, HEAD `aed276e`, ejecutado tal cual): **`ENTORNO LISTO`, exit 0**.
  Raíz 1883 passed (261,2 s); sv1 205, sv2 485, sv3 1576, sv4 1774, sv5 96, sv6 473 (+1 skipped),
  sv9 673, comun en verde; `PUERTA COBERTURA: 98.6% de 638 líneas` `[OK]`; rutas sensibles N/A;
  `PUERTA TAMAÑO`: requirements 150/150, design 250/250, impl 218/220, review 140/140. Antes de
  lanzarlo, ninguna suite de albaranes en marcha (solo un `pytest` de `datamart-seg-anual`).
- **El delta solo es texto**: `git diff c4bf6f3..HEAD --stat -- '*.py' evals tests services` vacío.
  Un solo commit, `aed276e` (`F-084 review 2: …`); árbol limpio. Ese commit versiona también el
  informe de la pasada 2 tal cual lo escribí (comparado byte a byte).
- **Ya no queda texto que diga que algo está pendiente del humano**: `grep` de «pendiente de confirm»,
  «no cambia hasta», «propone al humano el» y «≤ 20» en la spec, `impl_F-084*.md` y `current.md`:
  sin resultados.

## Condiciones de la pasada 2

| # | Condición | Estado |
|---|---|---|
| 1 | R28 (`requirements.md:146-150`): D1 confirmado y línea base 23 de 98 = 23,5 % aceptada (D5), sin R38 ni las 28 sintéticas `?`, con el 40,5 % de hoy y la nota de que T14 es anterior a R39 | [x] los cuatro elementos, literales. R27 se reescribió en 2 líneas para no pasar el tope (sigue siendo el mismo requisito, ver O9) |
| 2 | `design.md` §9 (T14) y §11 (P6, D5) | [x] «confirmado por el humano el 2026-10-23» en §9 y P6; D5 añade «línea base de R28 aceptada: 23,5 % (23 de 98, sin ellas ni la partida), no el 20 %» |
| 3 | `tasks.md:20` (T14) | [x] «D1, confirmado por el humano» |
| 4 | `impl_F-084.md`, `impl_F-084_T14.md`, `current.md:4/7/58/78`, `init.sh` en verde | [x] los cuatro puntos de `current.md` y los dos informes reflejan la decisión; el criterio de T14 en `current.md:78` ya es el 23,5 %. `init.sh` en verde |

## Checkpoints

- **C1** [x] init.sh exit 0 · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama de la feature · [x] `current.md` refleja el estado real
  (antes `[ ]`, condición 4) · [x] historia (la entrada de `history.md` la escribe el líder al cerrar).
- **C3** [x] sin cambios de código en esta pasada; lo de la pasada 2 sigue valiendo.
- **C3 bis** N/A: no toca `docs/referencia/`. **C4 ter** N/A: la puerta no señala rutas sensibles.
- **C4** [x] trazabilidad: R28 ya dice el criterio que el humano aceptó (antes `[ ]`, condición 1),
  y T14 cumple con él: 0 ERROR, `- Modelo: gpt-6.1-sol` y 23 de 98 = 23,5 % (lo recontó el
  reviewer en la pasada 2) · [x] sin red ni BBDD · [x] MANUAL T12/T14 con su comando en `current.md`.
- **C4 bis** [x] rigor · [x] RED · [x] cobertura 98,6 % · [x] mutación: la recalculé en la pasada 2
  (10, 8 y 5 mutantes, sin supervivientes) y RM1 se mantiene, porque de `a4d7653` a `aed276e` no
  cambia ningún `.py` · [x] RM2 · [x] RM3 · RM5 N/A (no se declara ningún equivalente) · [x] RM6 ·
  [x] «Evidencias» · [x] ningún N/A sin motivo.
- **C5** [x] T1–T17 `[x]` con commits `F-084 Tn:` · [x] árbol limpio · [x] `features.json`
  `in_progress` (lo pasa a `done` el líder tras este veredicto), rama, `servicios = evals`.

## Cobertura: requisito → test

Sin cambios respecto a las pasadas 1 y 2 (tablas en sus informes del historial). R28 queda verificado
contra la línea base aceptada (MANUAL T14 y recuento del reviewer).

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- **O6.** `dev` está en `84653d2` (altas de F-099–F-102) y la rama solo lleva fusionado hasta
  `416b55c`: antes de integrar, fusionar `dev` y repetir `init.sh`.
- **O7.** T13 versiona en `evals/fixtures/inputs/` las 3159 líneas de contrato de Sigrid con sus
  precios. Cumple T13 y el `.gitignore` («entran los fixtures JSON ya barridos»), pero son precios
  de proveedor en git, cuando los informes del runner se sacaron de git justo por eso. Conviene que
  el humano lo tenga presente.
- **O8.** La línea base se recontó a partir del texto de T14, que no llevaba la partida (R39) en el
  contexto de IA3: la próxima pasada con LLM no se puede comparar una a una con el 23,5 %.
- **O9 (redacción, no bloquea).** R27 pasa a decir «su informe lleva la de R36», donde antes decía «la
  advertencia de R36»: se entiende por el contexto, pero si hay margen, mejor el nombre completo. En
  `impl_F-084_T14.md:130-131`, «por encima del 20 % original (ahora la línea base)» puede leerse
  como si la línea base fuera el 20 %: la frase siguiente lo aclara (23,5 %).

## Automejora (propuesta, no aplicada)

`leader.md` / `CHECKPOINTS.md` C2: «cuando el humano decide en el chat algo que la spec deja
"pendiente del humano", el líder lo traslada a la spec y a `current.md` **antes** de pedir la
revisión final». En F-084 costó una pasada de review que solo era de documentación.
