Revisión incremental desde 16e048b (pasada 2): `16e048b..a201c6d`. La pasada 1 (completa, `dev...16e048b`) va debajo
<!-- progress/review_F-078.md -->
# F-078 · La línea valorada guarda lo que se ve · review

## Pasada 2 · veredicto: APPROVED

- **Delta:** `a201c6d` toca solo `progress/current.md` (+56), `harness/features.json` y `BACKLOG.md` (una palabra cada
  uno). `git diff 16e048b..a201c6d -- services harness/*.py` está **vacío**: no cambia código ni tests, así que lo
  aprobado en la pasada 1 sigue en pie (campaña sobre `f3094c9`, RM1 intacto; sin campaña nueva).
- **CR1** [x] `current.md` trae «F-078 · MANUAL del humano (T12–T14)» con fusión previa en `dev`, orden sv6 → relleno
  `--aplicar` → sv4 y «sv9 no se redespliega». Extraje los bloques de código PowerShell y SQL de `current.md` y de
  `impl_F-078.md` §7 y los comparé con `diff`: **idénticos**, salvo la línea añadida de la relectura (CR2).
- **CR2** [x] T13 termina con el relleno en solo lectura **tras desplegar sv4**, «Filas que cambiarían: 0» y, si da
  más, `--aplicar` otra vez con la misma autorización y nueva lectura.
- **CR3** [x] La nota para quien fusione después es correcta: F-075 debe pasar por `completar_registros` (cita el
  nombre exacto del test, que existe); F-077 R11 incluye R17 y la fila 13 de `f065_bbdd` lleva «PORTES»; conflictos de
  texto de F-076 (pipeline de sv6) y de F-075/F-077 (`review_repository.py`, plantilla), como en `spec_F-078.md` §5.
- **CR4** [x] `features.json` dice `fila_a_guardar`; `init.sh` da «BACKLOG.md al día».
- **`bash harness/init.sh`** desde Git Bash con `export PYTHONPATH=<worktree>/services/albaranes-comun`: `ENTORNO
  LISTO`, exit 0. Raíz `1237 passed` (205 s); servicios de caché (válida: el delta no toca `services/`, y en la pasada 1
  ejecuté sin caché sv4, sv6, sv9 y comun); `COBERTURA [OK] 98.0%`; tamaño impl 220/220. Sigue el
  AVISO [evals], ya justificado como falso positivo (C4 ter).
- **Checkpoints:** el `[ ]` de C4 (MANUAL en `current.md`) pasa a `[x]`; el resto, como en la pasada 1. C4 ter queda
  en `aviso` con su motivo escrito. Cierre: falta solo lo MANUAL del humano (T12–T14), que no bloquea el veredicto.
- **Observación:** el tercer bloque de T13 (relectura tras sv4) no repite el `cd` a `serviceslbaran-valoracion-persist`; si
  el humano despliega sv4 desde `infra\`, que vuelva antes a esa carpeta. Que el líder lo diga al pasarle los comandos.

## Pasada 1 · veredicto: CHANGES_REQUESTED (resuelto en la pasada 2)

No pido ningún cambio de código: el código, los tests y la campaña están bien. Rechazo por un checkpoint vacío de C4,
porque las MANUAL T12–T14 no están en `progress/current.md`. Van tres arreglos de documentación más en el mismo commit
(cambios 1–4). La pasada 2 puede ser incremental, solo sobre ese delta documental.

**Nivel de rigor:** `critico`, declarado. Exige RED, cobertura ≥ 80 % y campaña completa. Exige también cero
supervivientes salvo equivalentes que acepte el humano, RM5 con una muestra y MANUAL listadas con su comando.

## Lo que verifiqué yo (no copiado del informe)

| Comprobación | Resultado |
|---|---|
| `bash harness/init.sh` en Git Bash con `export PYTHONPATH=<worktree>/services/albaranes-comun` (como pidió el líder) | `ENTORNO LISTO`, exit 0. Raíz `1237 passed` (336 s). Servicios servidos de caché. `COBERTURA [OK] 98.0% (241/246)`. Tamaño del impl 220/220. AVISO [evals] |
| Suites de lo tocado, **sin caché**, en serie y con la misma `PYTHONPATH` | sv6 `340 passed`. sv9 `660 passed`. sv4 `1487 passed`. comun `684 passed, 3 skipped`. Total 394 s |
| `git diff --stat dev -- services/albaranes-alta-sigrid` | Solo `tests/test_f078_contrato_fila.py` (+162). sv9 no cambia de código |
| Alcance y mutantes recalculados (`alcance_de_feature` + `generar_mutantes`) | 6 ficheros, **734 líneas** y **81 mutantes**: coinciden. Los 8 supervivientes existen con el mismo operador y el mismo texto |
| RM4 en una copia `git archive`, en mi scratchpad y sin bytecode | Script L92 `frozen=False`: 1 fallo (`r21_un_cambio_es_inmutable`). sv4 L297 `es_contrato=True`: 1 fallo (`r16_materializar_una_nueva_con_blanca_…`). Las dos filas del re-juicio coinciden. Un muerto de la herramienta (`fila_completa.py` L36 `es_contrato=False`): 5 fallos. El worktree quedó limpio |
| Ramas F-075, F-076 y F-077 | Aún sin código (`git diff --name-only dev...` vacío en `services/`). El choque está en sus specs y en quien implemente después |

## Puntos que pidió juzgar el líder (pasada 1, resumen; texto íntegro en `git show 0a3851f:progress/review_F-078.md`)

1. Las desviaciones #1–#8 del §2 caben en la spec. #2: el glosario de requirements manda y la ficha decide igual. #3:
   R2 + R16 lo cubren; citarlo en la PARADA 2 como cambio de F-065 R31. 2. El AVISO [evals] es un falso positivo: el
   paso va tras el builder, no cambia ninguna decisión (R5) y `evals/procesos/sv6_build.py` no ejecuta el pipeline.
3. Orden sv6 → relleno → sv4: acotado; la ventana del sv4 viejo la cierra la relectura tras sv4. 4. Script correcto
   (READ ONLY, una transacción, idempotente, salta papelera y alta bloqueante, sin credenciales). 5. sv9: solo tests.
6. Choques: ahora anotados en `current.md` (pasada 2).

## Checkpoints

**C1** [x] init.sh exit 0 · [x] ficheros base.
**C2** [x] una sola `in_progress` · [x] rama de la feature · [x] `current.md` con F-078 activa · [x] ninguna `done` nueva.
**C3**
- [x] Hexagonal: comun puro, `fila_completa` en `application`, sv4 en `infrastructure` y el script en `scripts/`.
- [x] Ruta en la primera línea de los 21 ficheros.
- [x] Sin `print` de debug (los del script son su salida de CLI), sin TODOs, sin secretos, sin dependencias nuevas.
- [x] Trampas: lee de las tablas merge, no hay DDL, la Q y la unidad solo se copian con factor = 1, y que la
  sintética no herede la blanca es una decisión explícita.
**C3 bis** N/A: no toca `docs/referencia/`.
**C4**
- [x] R1–R25 con tests `test_f078_rN_*` en verde (tabla abajo). R26 es documental; lo verifiqué yo: regla 22 en
  ARCHITECTURE L522 y commit `fde767a` en `azure-apps`.
- [x] Sin red ni BBDD: SQLite en memoria y dobles.
- [ ] **Las MANUAL T12–T14 no están en `current.md` con su comando exacto**: solo hay un puntero (cambio 1).
**C4 bis**
- [x] `rigor: critico`.
- [x] RED: trazas reales de T1–T7 y T9. T8 es de caracterización y lo explica.
- [x] Cobertura `[OK]` al 98 %.
- [x] Totales recalculados por mí.
- [x] Muertos: el «Tiempo total» es 2980 s > 60 s y **la campaña no se reejecutó** (50 min según el informe).
  Valen el recálculo, RM1–RM6 y RM4.
- [x] Coste por mutante: 2980,1 × 4 ÷ 81 = 147 s, por encima de 1 s y coherente con las bases (24, 190 y 335 s).
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA»; «Sin veredicto» = 0, con línea base en los 4 workers.
- [x] **RM1:** medida sobre `f3094c9`. `git diff f3094c9..HEAD` solo toca tests, `progress/` y `docs/`; nada del alcance.
- [x] **RM2:** 36,8 × 4 = 147 s frente a bases de 24–336 s, con 73/81 muertos en `-x`; 81 × 36,8 = 2981.
- N/A **RM5:** no hay equivalentes declarados.
- [x] **RM6:** `2a6c462` solo añade tests.
- N/A campaña manual: la automática dio 81. Del re-juicio, que trae el texto exacto, reproduje 2 filas.
- [x] Los 8 supervivientes, analizados en `mutacion_F-078.md` (el `_arnes.md` conserva el PENDIENTE bruto), y 0
  equivalentes.
- [x] «Evidencias» con los 4 números y los 4 workers.
- [x] Ningún N/A sin motivo.
**RM3** (criterio): ningún muerto de los que miré es equivalente.
**C4 ter** La puerta señala `fila_completa.py` y no existe `progress/evals_F-078.md`. La exigencia es `aviso` y el
motivo está en el punto 2. Si el humano quiere la pasada: `python -m evals.runner --con-llm --feature F-078`.
**C5** [x] T1–T11 y T15 `[x]` con commits `F-078 Tn:`; T12–T14 MANUAL, pendientes · [x] `git status` limpio ·
[x] `in_progress` (errata en la descripción: cambio 4).

## Cobertura de requisitos

| Req. | Tests |
|---|---|
| R1–R3 | comun: tabla `r1_*` (12, con 385/386, inmutables y borde), `r2_no_vacia_*`, `r3_con_conversion_*` |
| R4, R5, R19 | sv6: `r4_*` (10, con el builder real), `pipeline_*` (2), `r5_*` (2), `r19_*` (2). sv9: `r19_nueva_de_ferreteria_*` |
| R6–R8 | `test_f078_ficha_pinta_fila.py`: `r6_*` (5), `r7_*` (5), `r8_*` (2) |
| R9–R16 | `test_f078_escrituras.py`: `r9_*` (4), `r10_*` (6), `r11_*` (4), `r12_*` (4), `r13_*` (2), `r14_*`, `r15_*` (3), `r16_*` (7) |
| R17, R20 | `test_f078_aprobar.py`: `r17_*` (10, con el 303 y el 409 del portal), `r20_producto_pintado_*` |
| R18 | `test_f078_contrato_fila.py`: `r18_*` (4) y `vinculada_sin_convertida_*`, contra el código real de sv9 |
| R21–R25 | `test_f078_relleno.py`: `r21_*` (7), `r22_*` (5), `r23_*` (4), `r24_*` (5), `r25_*` |
| R26 | Documental, verificado por mí (C4) |

## Cambios requeridos

1. **`progress/current.md`, bloque de F-078 (L4–7).** Añadir «MANUAL del humano» con T12, T13 y T14 y sus comandos
   PowerShell exactos, los de `impl_F-078.md` §7. Precede: fusionar en `dev` y respetar el orden sv6 → relleno
   `--aplicar` → sv4; sv9 no se redespliega. Es C4. `impl_F-078.md` no puede crecer, está en 220/220.
2. **En esa T13, un paso más tras desplegar sv4:** `.\.venv\Scripts\python.exe -m scripts.rellenar_filas_f078` en solo
   lectura, que debe dar «Filas que cambiarían: 0». Si da más, `--aplicar` otra vez con la misma autorización. Cierra
   la ventana del punto 3.
3. **`progress/current.md`, nota para quien fusione después** (junto a «Siguiente», L11):
   - F-075 debe llamar a `completar_registros` antes de cada `replace_valuation` con líneas (lo exige
     `test_f078_pipeline_todo_replace_valuation_…`).
   - F-077 R11 incluye ahora R17 («Líneas sin descripción»), y la fila 13 de `f065_bbdd` lleva «PORTES».
   - F-076 tiene un conflicto de texto en `run_valuation_pipeline.py`.
4. **`harness/features.json`, descripción de F-078:** cita `ruesma_comun.linea_valorada.fila_como_se_ve`, que no
   existe. Debe decir `fila_a_guardar`; `init.sh` regenera `BACKLOG.md`.

## Observaciones (no bloquean)

- `azure-apps/albaranes.md` dice «llena en toda fila», pero «Añadir línea» nace vacía y el PATCH puede vaciarla (lo cubre
  R17). El test por grep corta en el primer `)`: falla en rojo, nunca en verde. R25 reimplementa la ficha de antes.

## Automejora (propuesta, no aplicada)

C4 ter pide evals para todo `application/services/**` de sv6, pero las evals no ejecutan `RunValuationPipeline`: un
paso posterior al builder les es invisible. Propongo que `rutas_sensibles.json` admita excepciones por fichero con
su motivo.
