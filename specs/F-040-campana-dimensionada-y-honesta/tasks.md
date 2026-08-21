<!-- specs/F-040-campana-dimensionada-y-honesta/tasks.md -->
# F-040 · Tareas

Orden por dependencia. Cada tarea = un commit (`F-040 Tn: ...`). Fase RED
obligatoria (nivel `estandar`): la traza del fallo previo va en
`progress/impl_F-040.md`. Ningún test de esta feature ejecuta la suite real ni
una campaña larga: todos usan dobles y ejecutores falsos.

- [ ] T1: Tests RED de R22 y R23 — `timeout_mutacion` con `true`, con `0`, con `-1`, ausente (mensajes distintos) y `--timeout 0 / -5` saliendo 2 | Verificación: `python -m pytest tests/test_f040_r18_r26_huecos.py -k "r22 or r23"` falla por el motivo esperado
- [ ] T2: Implementar R22 en `harness/rigor.py` (rechazo de `bool`, mensaje «falta» vs «no vale») y R23 en `_analizar_argumentos` (`--timeout` > 0, `--workers` >= 1) | Verificación: los tests de T1 en verde
- [ ] T3: Tests RED de R25 y R26 — `python -m harness.rigor` sale 1 con un nivel inexistente; `validar_features` con ficha sin `rigor` y con `rigor: null`, ramas separadas | Verificación: `python -m pytest tests/test_f040_r18_r26_huecos.py -k "r25 or r26"` falla
- [ ] T4: Cerrar R25 y R26 (son huecos de test: solo se añaden tests, no se toca `rigor.py` salvo que el test demuestre defecto) | Verificación: tests de T3 en verde y `python -m harness.rigor` sigue en 0 con el inventario real
- [ ] T5: Test RED de R24 — retirada de worktrees con un `git` doble que hace fallar `worktree remove`, comprobando `rmtree` y `prune` en ese orden | Verificación: `python -m pytest tests/test_f040_r18_r26_huecos.py -k r24` falla
- [ ] T6: Cerrar R24 (hueco de test sobre `_retirar` en `harness/mutacion_paralela.py`) | Verificación: test de T5 en verde
- [ ] T7: Tests RED de R20 y R21 — sección `## Timeouts` sin prefijo duplicado, y `_base_rota_al_final` en sus tres ramas (verde, expirada, fallida) | Verificación: `python -m pytest tests/test_f040_r11_r17_honestidad.py -k "r20 or r21"` falla
- [ ] T8: Implementar D3 (R11, R12, R13) en `_base_rota_al_final`: distinguir `expirado` de `not verde`, mensaje de expiración que NO manda arreglar la suite | Verificación: tests de T7 y de R11/R12 en verde
- [ ] T9: Arreglar la línea de `## Timeouts` en `escribir_informe` (R20) | Verificación: test de T7 en verde
- [ ] T10: Tests RED de R14, R15, R16 y R17 — campaña con cero mutantes por `--feature` y por `--ficheros`: sin informe escrito y código 3; guarda de `alcance_de_ficheros` intacta | Verificación: `python -m pytest tests/test_f040_r11_r17_honestidad.py -k "r14 or r15 or r16 or r17"` falla
- [ ] T11: Implementar D4 en `main` (guarda de alcance vacío antes de la línea base; guarda de `informe.generados == 0` antes de `escribir_informe`), sin tocar `harness/alcance.py` | Verificación: tests de T10 en verde
- [ ] T12: Tests RED de R18 y R19 — centinela sucio con restauración irrecuperable aborta con 3 sin arrancar campaña; códigos de `--restaurar` (0 y 2) | Verificación: `python -m pytest tests/test_f040_r18_r26_huecos.py -k "r18 or r19"` falla
- [ ] T13: Implementar R18 en `main` (si `_modo_restaurar` no devuelve 0, abortar con 3) | Verificación: tests de T12 en verde
- [ ] T14: Tests RED de R8, R9 y R10 — `workers_por_defecto` para 1, 4, 8 y 22 núcleos (1, 1, 3, 4), `TOPE_WORKERS == 4`, `--workers 12` no se recorta, `rigor.json` sin clave `workers` | Verificación: `python -m pytest tests/test_f040_r1_r10_dimensionado.py -k "r8 or r9 or r10"` falla
- [ ] T15: Implementar D2 (`TOPE_WORKERS = 4` y `workers_por_defecto` con `max(1, (núcleos - 2) // 2)`) | Verificación: tests de T14 en verde
- [ ] T16: Tests RED de R1 y R2 — `timeout_derivado` (suelo si no hay medición, `ceil(peor × 2)` si supera el suelo) y `timeout_de_linea_base` (suelo × 5), funciones puras | Verificación: `python -m pytest tests/test_f040_r1_r10_dimensionado.py -k "r1 or r2"` falla
- [ ] T17: Implementar `MARGEN_TIMEOUT`, `FACTOR_HOLGURA_BASE`, `timeout_derivado` y `timeout_de_linea_base` en `harness/mutacion.py` | Verificación: tests de T16 en verde
- [ ] T18: Tests RED de R3, R5, R6 y R7 — la campaña con ejecutor doble deriva el timeout tras la línea base, lo anuncia, respeta `--timeout N` sin derivar, y el aborto por base expirada nombra workers y holgura | Verificación: `python -m pytest tests/test_f040_r1_r10_dimensionado.py -k "r3 or r5 or r6 or r7"` falla
- [ ] T19: Cablear la derivación en `ejecutar_campania` (parámetros `timeout_base_s` y `timeout_fijado`) y propagarla desde `main` | Verificación: tests de T18 en verde
- [ ] T20: Propagar la derivación en `harness/mutacion_paralela.py` (`ejecutar_campania_paralela` y `fusionar`: el timeout efectivo del informe es el máximo de los parciales) | Verificación: `python -m pytest tests/test_f012_r1_r5_r11_coordinador.py tests/test_f040_r1_r10_dimensionado.py`
- [ ] T21: Test RED de R4 e implementación de las filas nuevas del informe (timeout efectivo, suelo, workers) | Verificación: `python -m pytest tests/test_f038_r10_r12_informe.py tests/test_mutacion_informe.py tests/test_f040_r1_r10_dimensionado.py -k r4`
- [ ] T22: Actualizar el `$doc` de `mutacion` en `harness/rigor.json` (timeout = suelo, efectivo derivado, nuevo default de workers) sin declarar la clave `workers` | Verificación: `python -m harness.rigor` en 0 y test de R7/R9 en verde
- [ ] T23: Añadir a `CHECKPOINTS.md` la nota de RM2 sobre `mutantes × media / W` y el timeout efectivo declarado (R27) | Verificación: `python -m pytest tests/test_f038_r17_r21_documentos.py tests/test_f039_r1_r2_r23_r25_documentos.py`
- [ ] T24: Campaña de mutación de la feature con el nuevo dimensionado, analizando cada superviviente | Verificación: `python -m harness.mutacion --feature F-040 --salida progress/mutacion_F-040.md` (informe con supervivientes analizados; SIN reejecutar suites largas a mano)
- [ ] T25: Comprobar los topes del papeleo | Verificación: `python -m harness.tamano --feature F-040` en verde
- [ ] T26: Ejecutar `bash harness/init.sh` en verde | Verificación: `bash harness/init.sh`

## Después del merge en `dev` (NO en esta rama)

- [ ] P1: Portar los cambios del arnés a `arnes-base` como **1.7.2**, con la entrada de `GUIA_INSTALACION.md` avisando de que los tiempos de campañas paralelas anteriores dejan de ser comparables (timeout derivado; tope de workers 16 → 4) | Verificación: MANUAL (humano/líder), tras el merge
