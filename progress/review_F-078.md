Revisión completa (pasada 1): `dev...16e048b` (rama `feature/F-078-linea-guarda-lo-que-se-ve`, `dev` fusionado en `ac4d24a`)
<!-- progress/review_F-078.md -->
# F-078 · La línea valorada guarda lo que se ve · review

## Veredicto: CHANGES_REQUESTED

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

## Puntos que pidió juzgar el líder

1. **Desviaciones del §2: todas caben en la spec aprobada. No hace falta volver al humano.**
   - **#2.** «Su línea» es primero la de contrato porque así lo dice el glosario de requirements, que es lo vinculante.
     La ficha decide en ese orden (`matched` primero; si no, `elif derived`, ~L1516); la incoherencia está en design
     §4. Los builders de sv6 nunca ponen las dos (`partida_matcher`: derivada ⇒ `matched=None`).
   - **#3.** R2 acepta expresamente la unidad de su línea y R16 obliga a materializar la original, así que «las
     unidades de la original» de R15 son las ya materializadas. La ficha de antes también pintaba la de su línea, y
     en producción hay 0 casos. El líder debe citarlo en la PARADA 2 como cambio de F-065 R31, sin parar.
   - **#1.** Una blanca sin concepto pasa a la derivada. Se aparta de la letra de la spec, pero evita guardar vacía
     una Nueva de sv6 cuyo papel no trae concepto. Es lo que pintaba la ficha y cabe por R2.
   - **#4–#8.** También caben: el aviso de R17 vive en `LineasIncompletasError` (tests del 303 y del 409),
     `unidad_medida` es columna real del merge de sv3, la conexión no se imprime y la RED de T9 retiró el script.
2. **AVISO [evals]: es un falso positivo y no hacen falta evals con LLM.**
   - `completar_registros` solo toca cinco columnas de presentación y alta, y lo hace después del builder.
   - Importes, partida, `partida_action`, motivos y `review_required` no cambian (lo fija `r5_solo_cambian_los_cinco_…`).
   - `evals/procesos/sv6_build.py` compone `ValuationBuilder`, no `RunValuationPipeline`. Las evals no ejecutan este
     paso y darían lo mismo que en `dev`.
   - Un precio vacío se llena con el de su línea, pero el importe sigue nulo y la fila sigue en revisión. En
     producción, 0 casos.
3. **Orden sv6 → relleno → sv4.** El riesgo está acotado y documentado en design §7, impl §2.6 y T13. Queda una
   ventana:
   - Entre el relleno y el despliegue de sv4, el sv4 viejo sigue escribiendo huecos: `descripcion_linea = NULL` en
     «Origen ✎» → contrato y en `descripcion_para_valoracion`.
   - El sv4 nuevo los pinta vacíos y R17 bloquea la aprobación, así que a Sigrid no sale nada mal.
   - Un PATCH in situ sí copia el vacío a la derivada (L2195).
   - Repetir el relleno lo recupera desde el papel (cambio 2).
4. **Script de relleno: correcto.**
   - Por defecto, `SET TRANSACTION READ ONLY` antes de leer (tests del orden y del dialecto). `--aplicar`: un único
     `conexion.begin()`; si falla, `RellenoIncompleto` deshace y sale con código 2.
   - Idempotente (`fila_a_guardar` es un punto fijo; `r22_segunda_pasada_cero_cambios`). Salta `is_active` falso y
     `ESTADOS_ALTA_BLOQUEANTES`. Solo imprime ids, columnas y el tipo del error. No toca derivadas, importes ni partidas.
5. **sv9:** confirmado, solo cambian sus tests.
6. **Choques:** están anotados solo en `spec_F-078.md` §5 y en `impl_F-078.md` §6, no en `current.md`, así que quien
   implemente F-076 o F-077 no los verá. F-077 R11 da por fijas las validaciones del PUT, y R17 añade una. F-075 trae
   3 `replace_valuation`; el test por grep lo cazaría. Es el cambio 3.

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
