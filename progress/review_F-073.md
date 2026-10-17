<!-- progress/review_F-073.md -->
Revisión completa (pasada 1): `git diff dev...HEAD`, con `dev` = `e09916f` y HEAD = `234afec`.

# F-073 · Review (2026-10-17)

**Veredicto: APPROVED.** No hay ningún `[ ]`. Hay cinco hallazgos (H1–H5). No bloquean y los resuelve el líder sin
otra pasada; H1, antes de pedir al humano que acepte los equivalentes.

**Rigor `critico`** (declarado): fase RED, cobertura ≥ 80 %, campaña completa con 0 supervivientes sin aceptación
del humano, RM5 (una muestra) y MANUAL listada.

## Lo que ejecuté y checkpoints

- `bash harness/init.sh` (Git Bash): **EXIT=0**. Raíz 1237; sv1 205, sv2 397, **sv3 1496**, sv4 1715, sv5 43, sv6 444
  (+1 skip), sv9 670. Cobertura **100,0 % de 117**; rutas sensibles N/A con motivo; tamaño req 138, design 194, impl 208.
- Suite de sv3 sin caché (`python -m pytest -q -p no:cacheprovider`): **1496 passed**. Árbol limpio.
- **C1** `[x]` init.sh en verde · `[x]` ficheros del arnés presentes.
- **C2** `[x]` solo F-073 `in_progress` · `[x]` rama correcta · `[x]` `current.md` (F-073 arriba, el resto es el estado
  vivo de `dev`) · `[x]` las `done` tienen historia.
- **C3** `[x]` hexagonal (módulo puro en `application/services/`; el motivo en `domain/models`, sin infraestructura) ·
  `[x]` primera línea con ruta · `[x]` sin print, TODO, secretos ni dependencias nuevas · `[x]` sin DDL, raw ni
  importes; reglas 24 y 17 de ARCHITECTURE concuerdan con R1–R20.
- **C3 bis** `N/A`: no toca `docs/referencia/`. **C4 ter** `N/A`: init.sh imprime que no toca rutas sensibles.
- **C4** `[x]` R1–R20 trazables y en verde (tabla) · `[x]` sin red ni BBDD · `[x]` MANUAL T12 en `current.md`.
- **C4 bis**:
  - `[x]` rigor declarado · `[x]` RED real en `impl` §3 (T1–T7; R18 contra el resolver de `7c4bfc4`, 6 failed; T9 sin
    RED posible, dicho) · `[x]` cobertura `[OK]`.
  - `[x]` Totales recalculados por mí: `harness.alcance` 334 líneas (123/204/4/3), `generar_mutantes` **71**, como el
    informe. Los 2 supervivientes existen con el mismo operador y texto (`:93 [entero] <= 1 -> <= 2`,
    `:202 [comparacion] < -> <=`).
  - `[x]` 293,2 s > 60 s: **campaña no reejecutada (293 s según el informe)**; recálculo puro + RM1–RM6.
  - `[x]` Coste por mutante 293,2 × 4 / 71 = 16,5 s frente a base 22,6–33,9 s (coherente con `-x` y 69 muertos) ·
    `[x]` sin «NO VÁLIDA», base rota 0 · `[x]` RM1: medido en `0c169a1`; desde ahí solo cambian `progress/` y
    `tasks.md` · `[x]` RM2: media × W = 16,4 s frente a 22,7 s · `[x]` RM5: reproducido (punto 2) · `[x]` RM6 no
    aplica: los 7 huecos se cerraron con tests (`0a5d6d3`, `0c169a1`), sin quitar guardas.
  - `[x]` análisis completos (falta la aceptación del humano, la pide el líder) · `[x]` «Evidencias» con 4 workers ·
    `[x]` ningún N/A sin motivo.
- **C5** `[x]` T1–T11 y T13 `[x]` con commits `F-073 Tn:` (T12 MANUAL tras fusión, como F-076/F-077) · `[x]` sin
  artefactos · `[x]` `features.json` en `in_progress`, estado real.

## Requisito → test (`services/albaranes-persistencia/tests/`)

| R | Test |
|---|---|
| R1, R8 | `test_f073_eleccion::…r1_r8_el_resolver_no_tiene_criterio_propio`, `…r1_el_script_de_verificacion…` |
| R2–R8 | `test_f073_similitud`: r2 listas y palabras, r3, r4, r5, r6 exactos, r7 en todos los pares, r8 |
| R9, R12 | `…r9_*`: umbral y margen inclusivos, coma flotante, agrupación. `…r12_*`: barajados en `elegir`, paso 1 y paso 2 |
| R10, R11 | `…r10_p6_…`, `…r10_r11_…`, `…r11_*`: orden, tope, idempotencia, sustitución, fallo best-effort |
| R13, R14 | `…r13_*` (elige, empate, nadie); `…r14_*` (sin nota ni motivo, sobrevive la del paso 1, 3.543 del doble) |
| R15, R16 | `…r15_*`, con P0 incluido; `…r16_la_obra_con_s_a_puntua_como_hoy` |
| R17 | `test_f052_resumen_obra` (`nombre-debil-y-familia`), `test_f062_r3` (sin «S.L.») y `test_f052_r29…`. No cambia nada más |
| R18, R19, R20 | `test_f073_incidencia_0694` (3 rutas × 2 lecturas + control); `test_f073_corpus` (31/0/0); `…r20_*` |

## Lo que pidió juzgar el líder

1. **#5, el corpus de R19: sí vale como prueba.**
   - Los 18 candidatos son exactamente las razones de `evals/fixtures/final/` (las comprobé con grep de
     `"proveedor"`).
   - Las 31 lecturas siguen design §5.
   - R19 exige 31/0, y se cumple.

   El 24/6/1 frente al 23/7/1 se debe a una sola lectura: «H0RPRESOL S.L.» empata a 0,50 con CUBAS por «s.l.» y
   acierta solo porque HORPRESOL (B04…) llega antes. Es un acierto por orden de llegada, que confirma la tesis (H2).

   **#6, `proveedor_nombre_ambiguo`: lo cubre la spec, no es un hueco de F-073.**
   - Design §3 dice: «ningún `depurar_motivos_proveedor` lo toca, como `proveedor_cif_propio:`». La regla 24 dice:
     «la red no lo retira».
   - Es la política del humano del 2026-08-22 (`review_repository.py:4065`): sv4 solo retira
     `proveedor_cif_no_casa:`, y los motivos sin CIF van a una ficha aparte.
   - Ni sv6 ni sv9 leen los motivos del documento: el efecto es solo que sigue visible.

   Retirarlo es código de sv4, fuera de «solo sv3». Va en otra ficha (H3).
2. **Equivalentes (RM5): los dos se confirman.** Script en el scratchpad del reviewer, `rm5/rm5_demo.py`.
   - **#1, `|Δlen| ≤ 1 → ≤ 2`**: Levenshtein ≥ |Δlen|.
     - Exhaustivo sobre {a,b} con longitudes 5–8: 230.400 pares (40.960 con |Δ| = 2), 0 diferencias.
     - Aleatorio: 200.000 pares, 0 diferencias.
   - **#2, `< → <=`**: equivalente para todo lo observable (CIF, similitud, decisión, nota y log), con 100.000 casos
     aleatorios y 0 diferencias. **Pero su justificación no es exacta.** `_orden` compara `nombre or ""`, así que
     `(cif, None)` y `(cif, "")` empatan sin ser iguales campo a campo: el original se queda con `None` y el mutante
     con `""`. Los dos tienen similitud 0 y la nota pinta `'?'` (H1).
3. **«Nunca se elige en un empate»: se cumple.**
   - Atajo y global usan `elegir_por_nombre`, agrupado por CIF normalizado y ordenado por (−sim, cif, nombre): no
     depende de la llegada.
   - Con empate y puntos indecisos, `marcar_revision_cabecera(proveedor_nombre_ambiguo, nota R11)`.
   - P6: `det_familia_obra` con aviso. Los puntos exigen margen ≥ 2, así que un empate a puntos nunca elige.
   - La red por CIF solo cambia la similitud. La propuesta sigue siendo el primero (P5, con test).
   - `_resolve_obra` sigue con `_match_score`.
   - Hay un matiz en H4.
4. **Cobertura: 93,4 % frente a 100 %.** `harness.cobertura` no ejecuta la suite: lee el `coverage.json` que haya en
   `services/albaranes-persistencia/` (ignorado por git), y `init.sh` lo regenera justo antes.
   - La medición suelta de `cd67656` leyó un informe viejo, con otra numeración: por eso salen 122 líneas en vez de
     117, y 8 sin cubrir.
   - Tras mi `init.sh`, la misma orden suelta da **100,0 % de 117**. Vale el 100 %.
5. **MANUAL T12.**
   - `[x]` Las escrituras van marcadas [ESCRIBE EN PRODUCCIÓN], con quién y con el sí expreso:
     - paso 0: el revisor humano en sv4;
     - paso 1 y la vuelta atrás: el humano.

     La imagen y el log van como solo lectura. Ningún agente lanza nada.
   - `[x]` El paso 0 dice «ya, sin esperar al despliegue» y «haz antes este paso 0» frente a F-076 T19 sobre
     `54b82479`. Pero el T19 de F-076 no remite a F-073 (H5).
   - `[x]` Encaja con la secuencia combinada: sv3 no está en sus pasos 1–7 y su despliegue no altera ningún VERDE de
     esa secuencia. «Guardar y volver a buscar» con el CIF `manual` funciona con el sv3 viejo y con el nuevo.

## Hallazgos (no bloquean; los resuelve el líder)

1. **H1** · En `progress/mutacion_F-073.md`, #2, cambiar «igual campo a campo» por:
   > «`<` y `<=` solo difieren si `_orden` coincide (misma similitud, CIF recortado y `nombre or ""`). Eso incluye
   > `None` frente a `""`: objetos distintos, los dos con similitud 0 y pintados `'?'`. CIF, decisión, nota y log no
   > cambian (100.000 casos del reviewer).»

   Hacerlo antes de pedir la aceptación al humano.
2. **H2** · En R19 / design §5, nota de implementación: el corpus está reconstruido y el control medido da 24/6/1
   (H0RPRESOL acierta por orden).
3. **H3** · Proponer al humano una ficha, o ampliar F-059: sv4 retira `proveedor_nombre_ambiguo` y
   `proveedor_cif_propio:` cuando el revisor fija el proveedor (origen `manual`).
4. **H4** · P6, decisión del humano. Tras un empate por nombre, los puntos (sin cambios, R10) pueden elegir a alguien
   **ajeno al empate**, con similitud 0, si la familia le da margen. Reproducido:
   - empatados «HORMIGONES DEL SUR/NORTE» (gasóleo, 2 puntos);
   - «ARIDOS PEPE» (hormigón y mortero, 6 puntos);
   - resultado: `('B9', 'det_familia_obra')` con aviso.

   Es literal a la spec. Si el humano quería elegir solo entre los empatados, va en una ficha posterior.
5. **H5** · Dos cambios en `current.md`:
   - en el T19 de F-076, una línea: «antes, el paso 0 de F-073 (`54b82479` y los otros dos merges)»;
   - en el paso 1 de F-073, cambiar «sv3 no usa esos módulos» por «sv3 importa `ruesma_comun.sigrid`, que ya carga
     `sigrid.partidas` (solo stdlib; la suite de sv3 pasa con esa comun)».

## Automejora (propuesta, sin aplicar; genérica, para `arnes-base`)

En `reviewer.md`: «si la cobertura suelta del informe del implementer difiere de la de `init.sh`, manda la de
`init.sh`: `harness.cobertura` suelto lee el `coverage.json` que haya en disco, que puede ser viejo».
