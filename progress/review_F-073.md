<!-- progress/review_F-073.md -->
Revisión completa (pasada 1), `git diff dev...HEAD` con `dev` = `e09916f` y HEAD = `234afec`.

# F-073 · Review del reviewer (2026-10-17)

**Veredicto: APPROVED.** No hay ningún `[ ]`. Hay cinco hallazgos (H1–H5) que no bloquean. El líder los resuelve
sin otra pasada; H1 debe estar resuelto antes de pedir al humano la aceptación de los equivalentes.

**Rigor: `critico`**, declarado en `features.json`. Exige fase RED, cobertura ≥ 80 % y campaña completa con 0
supervivientes sin justificación aceptada por el humano. También exige RM5 (una muestra) y la MANUAL listada.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` (Git Bash): **EXIT=0**. Resultados por suite:
  - raíz 1237;
  - sv1 205 · sv2 397 · **sv3 1496** · sv4 1715 · sv5 43 · sv6 444 (+1 skipped) · sv9 670.

  Puertas:
  - `PUERTA COBERTURA: 100.0% de 117 líneas (117/117, crítico)`;
  - rutas sensibles N/A, con motivo impreso;
  - tamaño: requirements 138/150, design 194/250, impl 208/220.
- Suite de sv3 sin caché (`python -m pytest -q -p no:cacheprovider`): **1496 passed**.
- `git status`: limpio antes de este informe.

## Checkpoints

- **C1** `[x]` `init.sh` en verde. `[x]` Ficheros del arnés presentes.
- **C2**:
  - `[x]` Solo F-073 está `in_progress` (F-076/F-077/F-078 están `blocked`).
  - `[x]` Rama `feature/F-073-proveedor-por-similitud`.
  - `[x]` `current.md`: el bloque de F-073 va arriba y lo demás es el estado vivo de `dev`.
  - `[x]` Las features `done` tienen su historia.
- **C3**:
  - `[x]` Hexagonal: el módulo puro va en `application/services/` (precedente `familia_detector`). El motivo nuevo va
    en `domain/models`, que no importa infraestructura.
  - `[x]` Todos los ficheros nuevos empiezan con su ruta.
  - `[x]` Sin `print`, sin TODO, sin secretos y sin dependencias nuevas (stdlib + `ruesma_comun.proveedores`).
  - `[x]` Reglas de ARCHITECTURE: sin DDL ni lógica sobre tablas raw ni importes. La regla 24 y la línea de la 17
    concuerdan con R1–R20.
- **C3 bis** `N/A`: no toca `docs/referencia/`.
- **C4**:
  - `[x]` R1–R20 trazables y en verde (tabla de abajo).
  - `[x]` Sin red ni BBDD: dobles en memoria y `DobleSigridApi`.
  - `[x]` MANUAL T12 en `current.md` con sus comandos (punto 5).
- **C4 bis**:
  - `[x]` El rigor está declarado.
  - `[x]` Fase RED con trazas reales en `impl` §3 (T1–T7). R18 se midió con el resolver de `7c4bfc4`: 6 failed.
    T9 no tiene RED posible y lo dice.
  - `[x]` La puerta de cobertura sale en `[OK]`.
  - `[x]` Totales de mutación recalculados por mí (abajo).
  - `[x]` Tiempo total 293,2 s, más de 60 s: **campaña no reejecutada, 293 s según el informe**. Valen el recálculo
    puro, RM1–RM6 y la demostración de RM5.
  - `[x]` Coste por mutante: 293,2 × 4 / 71 = **16,5 s**, frente a líneas base de 22,6–33,9 s. Es coherente con `-x` y
    69 muertos de 71, y está por encima de 1 s.
  - `[x]` Sin «⚠ CAMPAÑA NO VÁLIDA». «Sin veredicto (base rota)» = 0.
  - `[x]` RM1: medido en `0c169a1`. Desde ahí, `git diff 0c169a1..HEAD` solo toca `progress/` y `tasks.md`, nada del
    alcance.
  - `[x]` RM2: media × W = 16,4 s frente a una base de 22,7 s, sin salto de orden de magnitud.
  - `[x]` RM5: reproducido por mí (punto 2).
  - `[x]` RM6: no aplica. Ningún mutante se mató quitando una guarda: los 7 huecos se cerraron con tests (`0a5d6d3`,
    `0c169a1`).
  - `[x]` Supervivientes analizados, ninguno `PENDIENTE`. La aceptación escrita del humano la pide el líder.
  - `[x]` «Evidencias» con los números, los 4 workers incluidos.
  - `[x]` Ningún N/A sin motivo.
- **C4 ter** `N/A`: la puerta de `init.sh` imprime que F-073 no toca rutas sensibles.
- **C5**:
  - `[x]` T1–T11 y T13 marcadas `[x]`, con commits `F-073 Tn:`. T12 es MANUAL posterior a la fusión, como en
    F-076/F-077.
  - `[x]` Sin artefactos sin trackear.
  - `[x]` `features.json` dice `in_progress`, que es el estado real.

**Mutación, recálculo propio.** `harness.alcance` da 334 líneas en 4 ficheros (123/204/4/3). `generar_mutantes` da
**71**, lo mismo que el informe. Los dos supervivientes existen con el mismo operador y el mismo texto:
- `similitud_proveedor.py:93 [entero] <= 1 -> <= 2`;
- `:202 [comparacion] < -> <=`.

## Cobertura · requisito → test

| R | Tests (`services/albaranes-persistencia/tests/`) |
|---|---|
| R1, R8 | `test_f073_eleccion::test_f073_r1_r8_el_resolver_no_tiene_criterio_propio`, `…r1_el_script_de_verificacion…` |
| R2–R7 | `test_f073_similitud` (r2 listas/palabras, r3, r4, r5, r6 casos exactos, r7 simetría sobre todos los pares) |
| R8 | `test_f073_similitud::test_f073_r8_distancia_edicion` + los dos de F-062 con alias |
| R9 | `test_f073_eleccion::test_f073_r9_*` (umbral y margen inclusivos, coma flotante, agrupación por CIF, paso 1 y 2) |
| R10, R11 | `…r10_p6_…`, `…r10_r11_…`, `…r11_*` (orden, tope, idempotencia, sustitución de nota, fallo best-effort) |
| R12 | `…r12_misma_decision_con_cualquier_orden`, `…r12_paso1_…`, `…r12_paso2_…` (barajados de semilla fija) |
| R13 | `…r13_log_al_elegir`, `…r13_log_en_empate_dice_cuantos`, `…r13_log_sin_nadie_que_llegue` |
| R14 | `…r14_*` (sin nota ni motivo, la nota del paso 1 sobrevive, 3.543 del doble) |
| R15 | `…r15_*`, incluido P0 (`…r15_p0_una_forma_juridica_sola…`) |
| R16 | `…r16_la_obra_con_s_a_puntua_como_hoy` |
| R17 | `test_f052_resumen_obra` (`nombre-debil-y-familia`), `test_f062_r3` (sin `solo-forma-juridica`), `test_f052_r29…` |
| R18 | `test_f073_incidencia_0694` (3 rutas × FEYMACO/TEYMACO, más el control) |
| R19 | `test_f073_corpus` (31/0/0 y el control) |
| R20 | `…r20_*` (defecto, en INSTANCIADO, se aplica, las dos composiciones sin cambios) |

R17: solo cambian las tres expectativas que la spec autoriza. Lo comprobé leyendo el diff de los 4 tests que ya
existían.

## Puntos que pidió juzgar el líder

1. **Desviaciones de `impl` §2.**
   - **#5, el corpus de R19: sí vale como prueba.** Comprobaciones:
     - Los 18 candidatos son exactamente las 18 razones de `evals/fixtures/final/`. Las extraje con grep de
       `"proveedor"`.
     - Las 31 lecturas siguen las categorías y los ejemplos de design §5.
     - R19 exige 31 aciertos y 0 errores, y se cumple.

     El «hoy 23/7» es descriptivo. La diferencia, 24/6/1, está en una sola lectura: «H0RPRESOL S.L.». Con el
     criterio viejo empata a 0,50 con CUBAS por «s.l.», y aquí acierta solo porque HORPRESOL (B04…) llega antes
     que CUBAS (B93…). Es un acierto **por orden de llegada**, y eso refuerza la tesis de la feature. → H2.
   - **#6, `proveedor_nombre_ambiguo` no se retira: lo cubre la spec, no es un hueco de F-073.** Los textos que lo
     fijan:
     - design §3: «ningún `depurar_motivos_proveedor` lo toca, como `proveedor_cif_propio:`»;
     - la regla 24: «la red no lo retira».

     Es además la política vigente del humano (2026-08-22, `review_repository.py:4065`): sv4 solo retira
     `proveedor_cif_no_casa:` y deja «un motivo SIN CIF sellado» a una ficha aparte. Ni sv6 ni sv9 leen los motivos
     del documento. El efecto es solo visual: el código crudo sigue en la ficha después de elegir el proveedor.
     Retirarlo sería código de sv4, y F-073 es solo de sv3. → H3, en otra ficha.
2. **Equivalentes (RM5): los dos se confirman.** Script propio en el scratchpad (`rm5/rm5_demo.py`):
   - **`|Δlongitud| ≤ 1 → ≤ 2`: equivalente.** Levenshtein ≥ |Δlongitud|, así que la distancia ≤ 1 lo implica.
     - Exhaustivo sobre el alfabeto {a,b} con longitudes 5–8: 230.400 pares, 40.960 de ellos con |Δ| = 2, **0
       diferencias**.
     - Aleatorio: 200.000 pares, 0 diferencias.
   - **`< → <=` en la agrupación: equivalente para todo lo observable, pero la justificación escrita no es exacta.**
     `_orden` compara `nombre or ""`, así que `None` y `""` empatan sin ser iguales campo a campo.
     - Con `(A28733558, None)` y `(A28733558, "")`, el original se queda con `nombre=None` y el mutante con `""`.
     - Los dos tienen similitud 0, y la nota pinta `nombre or '?'`.
     - CIF, similitud, decisión, nota y log coinciden: 50.000 × 2 casos aleatorios (umbral 0,5/0,25 y 0/0), **0
       diferencias**.

     → H1.
3. **«Nunca se elige en un empate».** Se cumple:
   - Atajo y global usan `elegir_por_nombre`: agrupan por CIF normalizado y ordenan por (−similitud, cif, nombre).
     No dependen del orden de llegada (R12, con barajados).
   - Con empate y puntos indecisos, sale `marcar_revision_cabecera(proveedor_nombre_ambiguo, nota R11)` y la línea
     va a revisión (`…r10_r11_…`).
   - P6: deduce por familia con `det_familia_obra` y aviso. El paso por puntos solo decide con margen ≥ 2, así que
     un empate a puntos nunca elige.
   - La red por CIF solo cambia la función de similitud. La propuesta sigue siendo «el primero en empate» (P5, con
     test).
   - `_resolve_obra` sigue con `_match_score` (R16).
   - Matiz de P6 → H4.
4. **Cobertura: el 93,4 % salía de un `coverage.json` viejo.** `harness.cobertura` no ejecuta la suite: lee el
   `coverage.json` que haya en `services/albaranes-persistencia/` (ignorado por git) y lo cruza con el alcance.
   `init.sh` lo regenera justo antes (§7/7 bis). La medición suelta de `cd67656` leyó un informe de una ejecución
   anterior, con otra numeración de líneas: de ahí 122 líneas relevantes en vez de 117, y 8 sin cubrir.
   Comprobación: tras mi `init.sh`, la misma orden suelta da **100,0 % de 117 (117/117)**. Vale el 100 %.
5. **MANUAL T12 en `current.md`.**
   - `[x]` Las acciones que escriben llevan la marca [ESCRIBE EN PRODUCCIÓN], con quién y con el sí expreso del
     humano:
     - paso 0: el revisor humano en sv4;
     - paso 1 (despliegue) y la vuelta atrás: el humano.

     La lectura previa de la imagen y el log van como solo lectura. Ningún agente lanza nada.
   - `[x]` El paso 0 va marcado «ya, sin esperar al despliegue», con «`54b82479` está también en la lista de
     «Valorar ahora» de F-076 T19: haz antes este paso 0». Pero el bloque de T19 de F-076 no remite a él. → H5.
   - `[x]` Encaja con la secuencia combinada F-078/F-076/F-077 sin romperla:
     - sv3 no está en sus pasos 1–7, y desplegarlo antes o después no cambia ningún VERDE de esos pasos;
     - «Guardar y volver a buscar» con el CIF `manual` funciona con el sv3 viejo y con el nuevo.

     Hay un matiz de precisión en H5.

## Hallazgos (no bloquean; los resuelve el líder)

1. **H1 · Corregir el texto del equivalente #2 en `progress/mutacion_F-073.md` antes de pedir la aceptación.**
   Donde dice «igual campo a campo», debe decir:
   > `<` y `<=` difieren solo si `_orden` coincide: misma similitud, mismo CIF recortado y mismo `nombre or ""`.
   > Eso incluye `None` frente a `""`, que dan objetos distintos. En ese caso los dos tienen similitud 0 y la nota
   > los pinta igual (`'?'`): CIF, decisión, nota y log no cambian. Demostrado con 100.000 casos aleatorios (reviewer).

   El #1 está bien escrito.
2. **H2 · R19 / design §5: anotar el corpus reconstruido.** Nota de implementación: el control medido es 24/6/1, no
   23/7/1, porque «H0RPRESOL S.L.» acierta por orden de llegada con el criterio viejo. El docstring del test ya lo
   dice, pero la spec sigue diciendo 23/7.
3. **H3 · Ciclo de vida de los motivos sin CIF.** Proponer al humano que `proveedor_nombre_ambiguo` (y
   `proveedor_cif_propio:`) se retire en sv4 cuando el revisor fija el proveedor (origen `manual`). Puede ir como
   ampliación de F-059 o como ficha nueva. No es de F-073.
4. **H4 · P6, decisión para el humano.** Tras un empate por nombre, el paso por puntos (sin cambios, R10) puede
   elegir a un candidato **ajeno al empate**, con similitud 0, si la familia le da ≥ 2 puntos de margen.
   Reproducido así:
   - empatados «HORMIGONES DEL SUR/NORTE» (gasóleo, 2 puntos);
   - «ARIDOS PEPE» (hormigón + mortero, 6 puntos).

   El resultado es `('B9', 'det_familia_obra')` con aviso. Es literal a la spec y P6 se aprobó así, pero la
   redacción de P6 («un empate que la familia separa») sugiere elegir entre los empatados. Si el humano lo quiere
   así, va en una ficha posterior que limite los puntos a los empatados.
5. **H5 · MANUAL, dos retoques en `current.md`:**
   - En el T19 del bloque de F-076, una línea: «antes, el paso 0 de F-073 sobre `54b82479` y los otros dos merges
     de la incidencia».
   - En el paso 1 de F-073, donde dice «sv3 no usa esos módulos», precisar: «sv3 importa `ruesma_comun.sigrid`, que
     ahora carga `sigrid.partidas` (solo stdlib, sin dependencias nuevas; la suite de sv3 pasa con esa comun)».

## Propuesta de automejora (para el humano, no aplicada)

En `reviewer.md` §Puntos de rigor, añadir: «si la cobertura suelta del informe del implementer difiere de la de
`init.sh`, manda la de `init.sh`: `harness.cobertura` suelto lee el `coverage.json` que haya en disco, que puede
ser viejo». Vale para `arnes-base` (es genérico).
