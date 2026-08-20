<!-- progress/review_F-039.md -->
# F-039 · Review

**Revisión incremental desde `29d7fd6` (pasada 2).** Se revisa
**`29d7fd6..6da533a`** (4 commits: `282f07d`, `adea6ab`, `8623187`, `6da533a`;
7 ficheros, +298/−60). Lo aprobado en la pasada 1 —rango `d3422ee..29d7fd6`,
revisión completa— queda dado por bueno y no se vuelve a mirar. Árbol limpio al
empezar y al terminar: lo que tocaba ficheros se hizo sobre un worktree
desechable en el scratchpad, ya retirado.

## Veredicto: APPROVED

Los dos CR de la pasada 1 están cerrados y **verificados en vivo, no leídos**:
las guardas de R18 muerden al degradar la cabecera, y la guarda de alcance vacío
ahora sale por el camino por el que se llega. **Nivel de rigor:** `estandar`
(declarado en `features.json`): exige fase RED, cobertura ≥ 80 %, campaña
analizada y sección «Evidencias». RM5 no aplica (solo `critico`).

## Resumen de la pasada 1 (cerrada, no se revisa de nuevo)

CHANGES_REQUESTED con el **fondo aprobado**: `init.sh` en verde, T11 recalculada
al dígito (2.742 líneas, 417 mutantes, los 20 del muestreo reproducidos con
`Random(20260820)` y los 7 supervivientes entre ellos), los 33 mutantes de las
dos campañas reejecutados por RM4 sobre copia con veredictos idénticos, R5 y R16
provocados en vivo, `arnes-base` intacto (T17 bien aplazado),
`mutacion_F-034.md` fuera del diff y `features.json` sin ficha nueva. RM1–RM4 y
RM6 `[x]`; C1, C2, C3, C4 bis y C5 `[x]`; C3 bis y C4 ter N/A justificados;
**C4 en `[ ]`** por R18. Sus tres observaciones no bloqueantes (orden T16/T11,
`_base_rota_al_final` bien dejado fuera, el mutante de `mutacion.py:1807` como
hueco de test y no como defensa que falte) siguen en pie. Los dos CR eran:

- **CR-1** · R18 sin ningún test, y T12 citando en `tasks.md` un test inexistente.
- **CR-2** · la guarda de lista vacía de `alcance_de_ficheros` inalcanzable desde
  el CLI: `--ficheros ","` terminaba en **exit 0** con un informe de 0 mutantes.

## Pasada 2 · verificación independiente del delta

- **`bash harness/init.sh` tal cual, exit 0**: `420 passed in 76.44s`,
  `COBERTURA 100.0%` (32/32, umbral 80 %), `RUTAS SENSIBLES N/A`, `TAMAÑO
  requirements 150/150, design 224/250, impl 220/220, review 140/140`. Los
  avisos (`ruff` 1108, sv1/`infra` sin tests, `[ADAPTAR]` de F-034/F-035) son
  deuda previa. La suite entera, no solo el delta, como manda el protocolo.
- **CR-1 cerrado · las guardas de R18 muerden.** Degradada la cabecera de
  `mutacion_maquinaria_paralela_F-039.md` sobre el worktree, cinco veces, y el
  test que toca **falla** cada vez: (1) `--ficheros` recortado a dos de los tres
  ficheros → `la cabecera no lleva el --ficheros COMPLETO`; (2) «mide OTRO
  código» → «mide el código de»; (3) «no repone sus números» → «actualiza»;
  (4) `mutacion_F-012.md` renombrado en **todo** el fichero; (5) borrado el
  bloque `>` entero (38 líneas) → **fallan los dos**. Sin degradar, `-k r18`
  da `2 passed`. Y las cadenas exigidas aparecen **una sola vez** en el fichero,
  todas dentro de la cabecera: no hay copia en otro sitio que deje pasar el test
  con la cabecera perdida, que era el riesgo de comprobar el texto completo.
- **T12 en `tasks.md` ya cita un test que existe**: ejecutado tal cual está
  escrito, `-k r18` → `2 passed, 7 deselected`.
- **CR-2 cerrado · comprobado en vivo**, que es donde estaba el defecto. Con
  `--salida` al scratchpad: `--ficheros ","` → **exit 2**; `--ficheros ",,,"` →
  **exit 2**; `--ficheros " "` → **exit 2**; y **no se escribió ningún informe**
  (`ls` del destino: no existe). El mensaje nombra la lista recibida
  (`(['', ''])`), que es lo que hace diagnosticable el aborto.
- **La cuarta entrada, `--ficheros ""`, no se cuela**, pero por otro camino:
  `if opciones.ficheros:` la trata como falsa y `main` cae al alcance del diff
  (comprobado: `origen rama, d3422ee..feature/F-039…`). No es la campaña vacía
  con exit 0 sino una legítima, así que no bloquea; queda como observación 2.
- **RM6 · no se ha quitado defensa para matar nada.** La guarda vieja
  (`if not rutas`) desaparece, pero la nueva la **contiene**: con `[]` el
  diccionario queda vacío y aborta igual, y
  `test_f039_r16_una_lista_vacia_aborta` (línea 164) sigue verde. Guarda movida
  y ampliada, no retirada.

## La campaña de T19, reejecutada (RM1–RM3)

- **RM1 [x]** · SHA declarado `adea6abba5453dbf2be032d027793f2304e0bf41`.
  `git diff --name-only adea6ab..HEAD` = `progress/impl_F-039.md` y
  `progress/mutacion_F-039.md`: **ningún fichero del alcance se ha movido**.
  Recálculo independiente en HEAD con `alcance_de_feature`: 2 ficheros,
  `alcance.py` 67 + `mutacion.py` 73 = **140 líneas**, idéntico al informe (el
  alcance creció de 134 a 140 justo por CR-2, y por eso tocaba remedir).
  `generar_mutantes` da **13** mutantes, los mismos 13 del informe.
- **RM2 [x]** · 13 × 37,1 = 482,3 ≈ **482,2 s** declarados: coherente al
  decimal. Media (37,1 s) por debajo de la línea base (51,5 s) es el caso
  legítimo de `-x` con 13/13 muertos, como F-038. **Campaña no reejecutada:
  482,2 s, muy por encima del umbral de 60 s de C4 bis**; en su lugar,
  recálculo puro + RM3/RM4 sobre muestra.
- **RM3 [x]** · Ningún equivalente sale MUERTO. Revisados los 13: tres tocan
  `range(1, total + 1)`, uno revienta por índice (`ref_diff[2]`), el resto
  invierten guardas vivas o el `and` de `lineas_comparables`. **Tres muertes
  reproducidas de verdad (RM4)** sobre el worktree: `alcance.py:262`
  (`if not lineas:` → `if lineas:`) mata con `SystemExit … (['harness/rigor.py'])`
  —**es el mutante de la guarda nueva**, la prueba de que CR-2 quedó cubierto
  por test y no solo escrito—; `alcance.py:254` (`total + 2`, el único candidato
  serio a equivalente) mata con `AssertionError: 270`; y `mutacion.py:1402`
  (`and` → `or`) mata el test de paridad serie/paralelo de F-012.
- **T11 no se reejecuta** y sigue siendo válida: `git diff --name-only
  b0761e8..HEAD` sobre `mutacion.py`, `mutacion_paralela.py` y `rigor.py` sale
  **vacío** también en HEAD. Confirmado, y adelante.

## CHECKPOINTS.md (solo lo que el delta cambia)

- **C4 [x]** · Cerrado el `[ ]` de la pasada 1: R18 tiene dos tests que muerden
  y T12 cita uno que existe. El resto de C4 no lo toca el delta.
- **C4 bis [x]** · Fase RED presente para los dos CR (mensajes de aserción
  reales, no «se siguió TDD»), corroborada por mi propia degradación; cobertura
  en `[OK]` al 100 %; `mutacion_F-039.md` regenerado por la herramienta con
  totales verificados; cero `PENDIENTE`; «Evidencias» con los cuatro números
  actualizados; no es campaña de cero mutantes.
- **C1, C2, C3, C5 [x]** · `init.sh` exit 0, una sola feature `in_progress`,
  rama correcta, árbol limpio. Los cuatro commits del delta llevan el prefijo
  `F-039` y dicen qué CR cierran; `tasks.md` mantiene sus `[ ]` justificados
  (T5–T7 MANUAL, T17 tras el merge). **C3 bis, C4 ter · N/A** justificados igual
  que en la pasada 1 (ningún documento externo; ninguna ruta sensible).
- **Tamaño del informe del implementer: medición correcta.** `wc -l` = **220
  exactas**, clavado en el tope, que es legal. Revisadas sus cinco compresiones:
  ninguna pierde nada exigible —la traza RED de T2/T4 pasa de bloque a línea
  pero **conserva el mensaje de aserción literal**, y las decisiones 2–5 se
  funden en 2–4 sin perder el `--workers 1`, el `--timeout 400` ni el motivo de
  aplazar T17.

## Trazabilidad (delta)

| Req | Test |
|---|---|
| **R18** | `test_f039_r18_la_cabecera_lleva_el_comando_exacto…` y `…avisa_de_que_mide_otro_codigo_que_f012` — **cerrado** |
| R16 | + `…ficheros_solo_con_separadores_aborta_desde_el_cli` y `…el_aborto_por_alcance_vacio_no_escribe_informe` |

El resto de la tabla no cambia: vale la de la pasada 1.

## Observaciones (no bloquean)

1. Las tres de la pasada 1 siguen en pie sin cambios.
2. **`--ficheros ""` se ignora en silencio** (`mutacion.py:1822`, `if
   opciones.ficheros:`): el flag explícito desaparece y la campaña mide el diff
   de la feature. No es el defecto de CR-2 —no hay campaña vacía con exit 0—,
   pero un flag que se pasa y no se aplica merece un aborto igual que `","`.
   Propuesta para el humano, no CR de esta feature.
3. **Propuesta al protocolo del reviewer** (`.claude/agents/reviewer.md`): esta
   pasada ha valido por **degradar la evidencia y ver si el test falla** —una
   guarda documental que pasa con el documento correcto no demuestra nada—.
   Escribirlo como regla: si un CR se cierra con un test sobre un fichero de
   `progress/`, el reviewer lo degrada sobre copia y comprueba el rojo. Es
   barato, y es lo único que separa un test de un adorno.
