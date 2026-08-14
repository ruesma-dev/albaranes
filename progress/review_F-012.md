<!-- progress/review_F-012.md -->
# F-012 · Campaña de mutación en paralelo — Review

- **Veredicto: APPROVED**
- Rama revisada: `feature/F-012-mutacion-paralela` (HEAD `b05797f`), árbol
  principal, `git branch --show-current` confirmado.
- **Nivel de rigor: `estandar`**, declarado en `harness/features.json`. Exige
  fase RED en los requisitos centrales, cobertura de líneas cambiadas ≥ 80 % y
  campaña de mutación con todos los supervivientes analizados. NO exige cero
  supervivientes (eso es `critico`): con `estandar` los supervivientes se
  documentan y el reviewer juzga, y aquí se juzgan aceptables.

Todo lo que sigue está comprobado por el reviewer ejecutando los comandos, no
leyendo el informe del implementer.

## Evidencia de primera mano

| Comprobación | Resultado |
|---|---|
| `bash harness/init.sh` (yo solo, sin nada en paralelo) | **exit 0**. 242 tests en verde, `PUERTA COBERTURA [OK] 95.8%` (184/192, umbral 80), `PUERTA RUTAS SENSIBLES [evals] N/A`, una feature en curso, rama correcta |
| Suite de la raíz | `242 passed in 35.60s` |
| Los 5 ficheros `tests/test_f012_*` | `67 passed in 21.59s` — coincide con los 67 declarados |
| Alcance recalculado (`harness.alcance`) | `3 fichero(s), 556 línea(s)` — `mutacion.py` 88, `mutacion_paralela.py` 453, `rigor.py` 15. **Idéntico** al informe de mutación |
| Mutantes recalculados (`generar_mutantes`, cálculo puro) | **61**, idéntico al informe. Reparto por operador: 20 entero, 14 lógico, 11 booleano, 8 comparación, 5 aritmético, 3 not |
| Propagación a arnes-base | commit `0436314`, 4 ficheros, mismas cifras de diff; **md5 idéntico** en los cuatro blobs commiteados |
| Rutas sensibles (C4 ter) | Los 14 patrones declarados viven todos bajo `services/**`; el diff no toca `services/` |

### Verificación funcional de la campaña paralela (barata, no repetida)

```
python -m harness.mutacion --feature F-012 --workers 2 --max-mutantes 6 --semilla 99 --timeout 300 --salida <scratchpad>/rev_mutacion_F012.md
→ 6 mutantes evaluados, 6 muertos, 0 supervivientes, 0 timeouts en 398.8 s   (exit 0, 6m39s de reloj)
```

Añadí `--timeout 300` por el motivo que documenta el implementer (la suite de
la raíz tarda ~130 s, por encima de los 120 s de `rigor.json`); sin él, los seis
habrían dado timeout y la prueba no habría probado nada.

Lo que observé **durante** la campaña, con ella en vuelo:

```
$ git worktree list
C:/Users/pgris/PycharmProjects/albaranes                        b05797f [feature/F-012-mutacion-paralela]
C:/Users/pgris/AppData/Local/Temp/mutacion_F-012_03yut05p/wk_0  b05797f (detached HEAD)
C:/Users/pgris/AppData/Local/Temp/mutacion_F-012_03yut05p/wk_1  b05797f (detached HEAD)
$ git status --porcelain
(vacío)
```

Dos worktrees detached, en el temp del sistema, **fuera** del repositorio, y el
árbol principal intacto a mitad de campaña: R2 verificado en ejecución real, no
solo en test. Al terminar, `git status --porcelain` vacío, `git worktree list`
con **solo** el árbol principal y el directorio `mutacion_F-012_*` borrado del
temp (R10).

El informe fusionado sale con el formato de siempre: misma cabecera «Generado
por…», misma tabla de alcance (88/453/15/**556**), misma tabla de totales, fila
de muestreo (`sí — 6 de 61 mutantes, semilla 99`) y sección de supervivientes.

**Determinismo del reparto (R3), comprobado aparte y en puro:**
`generar_y_muestrear(alcance, '.', 6, 99)` da los mismos seis mutantes que
evaluó la campaña, y `repartir(...)` con 2 workers da las particiones
`w0 = [mutacion.py:668, mutacion.py:678, mutacion_paralela.py:158]`,
`w1 = [mutacion.py:672, mutacion_paralela.py:158, mutacion_paralela.py:288]`,
que es exactamente el orden en que los dos workers los fueron cantando.

## Verificación independiente de la campaña de mutación (C4 bis)

Alcance y número de mutantes recalculados: **556 líneas / 61 mutantes**,
coincidentes con `progress/mutacion_F-012.md`. No hay cero mutantes, así que no
procede la prueba de control del cero.

Muestreo de supervivientes: los **seis** existen como mutantes reales, con el
mismo operador y el mismo texto original→mutado que declara el informe
(verificado regenerando los mutantes de esas líneas):

| # | Ubicación | Operador | Mutación | ¿Existe? |
|---|---|---|---|---|
| 1 | `mutacion.py:587` | entero | `or 1` → `or 2` | sí (col 41) |
| 2 | `mutacion.py:664` | booleano | `flush=True` → `False` | sí (col 53) |
| 3 | `mutacion.py:677` | booleano | `flush=True` → `False` | sí (col 49) |
| 4 | `mutacion_paralela.py:142` | booleano | `text=True` → `False` | sí (col 13) |
| 5 | `mutacion_paralela.py:214` | comparación | `!= 0` → `== 0` | sí (col 22) |
| 6 | `mutacion_paralela.py:214` | entero | `!= 0` → `!= 1` | sí (col 25) |

Juicio de los análisis (no me limito a comprobar que están escritos):

- **#1 equivalente, demostrado.** El operando derecho del `or` solo se evalúa
  con `os.cpu_count()` a `None`, y ahí `max(1, 1-2)` y `max(1, 2-2)` valen
  ambos 1. Además la línea 587 genera **cinco** mutantes y los otros cuatro
  (`max(1→2)`, `or→and`, `-2→+2`, `-2→-3`) murieron: los tests de
  `workers_por_defecto` son reales, no decorado.
- **#4 equivalente, demostrado y comprobado en el código.** `_git` pasa
  `encoding="utf-8"` (línea 143), y `subprocess` entra en modo texto con
  cualquiera de `encoding`/`errors`/`text`/`universal_newlines`: `text=False`
  no devuelve bytes.
- **#5 superviviente aceptado, y bien clasificado.** El implementer NO lo
  vende como equivalente, que es lo honesto. Verifiqué su argumento leyendo
  `_retirar()`: con el fichero bloqueado, la versión original hace
  `rmtree(ignore_errors) + prune`, pero `prune` no desregistra un worktree cuyo
  directorio **sigue existiendo** (el fichero bloqueado impide borrarlo), así
  que tampoco limpia el registro; y el `rmtree` final del temporal deja el
  árbol en el mismo sitio en ambas versiones. La diferencia observable se
  reduce a cuánta basura queda en el temp, tal y como dice el análisis.
- **#2, #3, #6** equivalentes por el mismo tipo de argumento (buffering de
  `print`; códigos de salida que `git worktree remove` no devuelve). Correctos.

Mutation score 55/61 = 90,2 %. Con `estandar` no hay tope de supervivientes;
los seis están analizados y ninguno en `PENDIENTE`.

## Las tres desviaciones de T5: justificadas

1. **`--rama ""` en ambos comandos — justificada, y la verifiqué yo.**
   Recalculado en esta sesión: con la rama, `F-011: 0 fichero(s), 0 línea(s)`
   (la rama está mergeada en `dev` y el `merge-base` es su propia punta); con
   `--rama ""`, `13 fichero(s), 3.812 línea(s)` por el camino de commit de
   merge, y **305 mutantes**, exactamente los del informe histórico de F-011.
   Sin la desviación, T5 habría comparado dos informes vacíos: la desviación no
   esconde un requisito incumplido, lo salva.
2. **`--timeout 300` en ambos comandos — justificada, y refuerza la
   comparación en vez de debilitarla.** Es el punto que más merecía escrutinio.
   Con los 120 s de `rigor.json` y una suite de raíz de ~130 s, **todo mutante
   que sobrevive habría dado timeout en las dos mitades**: los informes
   habrían coincidido (timeout contra timeout) sin que la suite llegara a
   juzgar nada. Con 300 s las dos mitades reportan **0 timeouts** y los 60
   mutantes se juzgan de verdad: 37 muertos y 23 supervivientes en ambas. Subir
   un timeout solo puede convertir timeouts en veredictos reales, nunca
   fabricar «muertos», así que el criterio de éxito sigue siendo válido —y es
   más exigente— con el cambio aplicado a los dos lados. R6 (mismo timeout en
   todos los workers) queda cubierto aparte por
   `test_f012_r6_el_timeout_configurado_llega_a_todos_los_workers`.
3. **Informes temporales fuera de `progress/` y serie sobre un worktree
   dedicado — justificada.** Lo primero es consecuencia directa de R9 (un
   `progress/tmp_*.md` sin commitear ensucia el árbol y aborta la campaña
   paralela); `tasks.md` los quería temporales y se borraron. Lo segundo usa el
   `--raiz` de siempre sobre un detached del **mismo commit** (`b23497a`), así
   que la suite que juzga cada mutante es la misma en las dos mitades; la
   prueba empírica es que los cinco totales coinciden y las 23 secciones de
   supervivientes salen en el mismo orden.

Diff de los dos informes: tres líneas (ruta del propio fichero, fecha y
«Tiempo total»), todas admitidas por R4. Criterio de éxito cumplido, con
6.491,0 s → 743,4 s (8,7×).

## Checkpoints

### C1 — El arnés está completo y en verde
- [x] `bash harness/init.sh` exit 0 (ejecutado por mí).
- [x] Existen todos los ficheros exigidos (los verifica el propio portero).

### C2 — El estado es coherente
- [x] Una sola feature `in_progress`: F-012.
- [x] Rama `feature/F-012-mutacion-paralela`, no `main` ni `dev`.
- [x] `progress/current.md` describe solo la sesión activa, sin restos.
- [x] Las dos features `done` (F-001, F-011) tienen entrada en
      `progress/history.md`.

### C3 — Código, arquitectura y convenciones
- [x] Primera línea con la ruta en los 6 ficheros nuevos.
- [x] Sin `print()` de debug (los `print` son salida legítima de una CLI, vía
      `eco`), sin TODO/FIXME, sin secretos: barrido de
      `password|secret|token|api_key|connectionstring|PRIVATE KEY` sobre los
      ficheros nuevos y modificados sin un solo acierto real (los dos hits son
      la palabra «token» en un docstring del mutador).
- [x] Sin dependencias nuevas: solo biblioteca estándar, como exige el diseño.
- **N/A justificado — arquitectura hexagonal y las tres trampas del monorepo
  (tablas merge, lectores de schema, unidades).** F-012 es herramienta del
  arnés: no toca `services/**`, ni dominio, ni infraestructura, ni SQL, ni
  colas. El diff son `harness/`, `tests/`, `specs/` y `progress/`. No hay capa
  que violar ni frontera de microservicio que evaluar.

### C3 bis — Documentos que entran de fuera
- **N/A justificado:** el diff no añade ni modifica nada en `docs/referencia/`
  (comprobado con `git diff --name-only`). No hay documento externo que
  barrer.

### C4 — La verificación es real
- [x] Cada requisito EARS tiene tests trazables y todos pasan: R1 (7 tests),
      R2 (3), R3 (10), R4 (5), R5 (3), R6 (2), R7 (10), R8 (6), R9 (6),
      R10 (9), R11 (1). **R12 lo verifiqué yo por md5**, que es como la spec
      dice que se comprueba.
- [x] Los tests no tocan red ni BBDD: git local sobre `tmp_path` y ejecutores
      falsos inyectados. Búsqueda de `requests|httpx|psycopg|pyodbc|socket|
      urlopen|azure` en los cinco ficheros: cero aciertos.
- [x] Verificaciones MANUAL: ninguna, y el motivo es correcto (la feature no
      toca sistemas reales).

### C4 bis — El rigor declarado se cumple
- [x] `rigor: "estandar"` declarado y válido.
- [x] **Fase RED**: trazas reales de las cuatro tareas de código (T1–T4), con
      el `ModuleNotFoundError`/`ImportError` previo al código. Además, y esto
      es lo que le da valor, **dos roturas deliberadas** del mecanismo central
      (el orden por clave estable de `fusionar`; los workers mutando el árbol
      principal) con la traza de qué tests las cazan y el árbol restaurado
      después. Es exactamente el control que pide `CHECKPOINTS.md` cuando las
      trazas RED son de importación.
- [x] **Cobertura**: `[OK] 95.8% de 192 líneas cambiadas (184/192, umbral 80)`
      en mi propia ejecución.
- [x] **Mutación**: `progress/mutacion_F-012.md` existe, generado por la
      herramienta, con totales **recalculados por mí de forma independiente**
      (556 líneas, 61 mutantes) y seis supervivientes muestreados uno a uno.
- [x] Ningún superviviente en `PENDIENTE`; los seis analizados y el análisis se
      sostiene al contrastarlo con el código.
- [x] Sección «Evidencias» con los cuatro números (242 tests / 95,8 % / 61
      mutantes y 6 supervivientes / 34,18 s de suite).
- [x] Ningún punto de este bloque marcado N/A.

### C4 ter — Rutas sensibles
- **N/A justificado:** `harness/rutas_sensibles.json` declara 14 patrones,
  todos bajo `services/albaranes-api`, `services/albaran-valoracion-*` y
  `services/albaranes-comun`. Los 16 ficheros del diff son de `harness/`,
  `tests/`, `specs/` y `progress/`: **ninguna ruta declarada tocada**, tal y
  como confirma la puerta del portero. No hay pasada de evals que exigir.

### C5 — La sesión se cerró bien
- [x] `tasks.md` con las 8 tareas `[x]` y un commit por tarea con el formato
      `F-012 Tn: ...` (T5 y T8 comparten el commit `b05797f`, que las nombra a
      las dos; T8 es «lanzar init.sh», no una tarea de código). Aceptado.
- [x] Sin ficheros temporales ni sin trackear: `git status --porcelain -uall`
      vacío antes y después de mi campaña de prueba.
- [x] `features.json` con F-012 en `in_progress`. Correcto: pasarla a `done` es
      del líder, después de este veredicto.

## Cobertura requisito → test

| Requisito | Test que lo cubre (muestra) |
|---|---|
| R1 | `test_f012_r1_evalua_todos_los_mutantes_una_sola_vez`, `test_f012_r1_r4_el_informe_paralelo_es_identico_al_de_la_campania_en_serie`, `test_f012_r1_el_fallo_de_un_worker_se_relanza_en_el_hilo_principal` |
| R2 | `test_f012_r2_escribir_en_un_worktree_no_toca_el_arbol_principal`, `test_f012_r2_los_worktrees_viven_fuera_del_arbol_principal`, `test_f012_r2_el_arbol_principal_queda_intacto_y_sin_worktrees` |
| R3 | `test_f012_r3_reparto_ni_repite_ni_omite_ningun_mutante`, `test_f012_r3_reparto_es_determinista`, `test_f012_r3_el_muestreo_con_la_misma_semilla_elige_los_mismos_mutantes` |
| R4 | `test_f012_r4_fusionar_suma_totales_y_ordena_por_clave_estable`, `test_f012_r4_clave_estable_es_la_del_orden_de_la_campania_en_serie` |
| R5 | `test_f012_r5_la_fabrica_ejecuta_en_el_worktree_con_el_venv_del_arbol_principal`, `test_f012_r5_sin_raiz_venvs_el_ejecutor_se_comporta_como_siempre` |
| R6 | `test_f012_r6_el_timeout_configurado_llega_a_todos_los_workers`, `test_f012_r6_los_timeouts_de_todos_los_workers_se_agregan_y_se_ordenan` |
| R7 | `test_f012_r7_workers_por_defecto_son_los_nucleos_menos_dos`, `test_f012_r7_workers_por_defecto_tienen_tope`, `test_f012_r7_la_cli_manda_sobre_rigor_json_y_sobre_el_default` |
| R8 | `test_f012_r8_con_workers_1_la_cli_no_llama_a_la_campania_paralela`, `test_f012_r8_con_un_solo_mutante_no_se_crea_ningun_worktree` |
| R9 | `test_f012_r9_con_el_arbol_sucio_aborta_sin_crear_worktrees`, `test_f012_r9_la_cli_devuelve_2_con_el_arbol_sucio` |
| R10 | `test_f012_r10_los_worktrees_se_retiran_con_una_excepcion_en_vuelo`, `test_f012_r10_los_worktrees_se_retiran_con_ctrl_c`, `test_f012_r10_el_arranque_poda_los_huerfanos_de_campanias_muertas` |
| R11 | `test_f012_r11_un_venv_inexistente_falla_antes_de_crear_worktrees` |
| R12 | Verificación por md5 del reviewer: los cuatro ficheros commiteados coinciden con arnes-base `0436314` |

Contraste con `design.md`: el diff toca **solo** los ficheros previstos
(`mutacion_paralela.py` nuevo; `mutacion.py`, `rigor.py` y `rigor.json` con los
tres cambios acotados que anunciaba). `generar_mutantes`, `aplicar_mutante`,
`ejecutar_campania`, `escribir_informe` y `EjecutorPytest` siguen intactos, que
es la condición de la que depende que mi recálculo de C4 bis siga valiendo.

## Observaciones (ninguna bloquea)

1. **Restos en el temp del sistema: 86 directorios `mutacion_mutacion_*`,
   todos vacíos y de 0 bytes.** Vienen de la **suite de tests** (usan la
   etiqueta por defecto), no de las campañas reales: la mía, con etiqueta
   `F-012`, se borró entera. En Windows el `rmtree(ignore_errors=True)` del
   temporal deja a veces el directorio ya vacío. R10 admite explícitamente que
   los directorios queden «inertes en el temp del sistema», así que no es
   incumplimiento; pero la suite deja uno por ejecución, y se acumulan.
   *Sugerencia (no exigencia): que los tests de `Worktrees` usen `tmp_path`
   como padre del temporal, y así el temp del sistema no se llena al correr la
   suite.*
2. **El informe de mutación no deja constancia del `--timeout` con el que se
   lanzó.** La campaña final de F-012 usó `--timeout 900` y la de T5, 300; se
   sabe porque el implementer lo escribió a mano en su informe, no porque el
   informe lo diga. Una fila «Timeout» sería idéntica en serie y en paralelo,
   así que no rompería la identidad que exige R4 ni la decisión del humano de
   no poner fila «Workers». *Propuesta para el humano, a portar a `arnes-base`
   si la acepta.*
3. **El «hallazgo colateral» merece feature propia y pronto.** Con la suite de
   la raíz en ~130 s y `timeout_por_mutante_s: 120`, **cualquier campaña de
   este repositorio daría timeout en todos los supervivientes**, en serie y en
   paralelo, y la puerta de mutación de C4 bis quedaría vacía sin que nadie lo
   note. El culpable está medido: 93 s del `setup` de
   `services/albaranes-comun/tests/test_humo_colas.py::test_publicar_y_consumir`.
   Fuera del alcance de F-012, correctamente; pero conviene abrirla antes de la
   siguiente feature con rigor `estandar` o `critico`.

## Automejora del protocolo (propuesta, no aplicada)

`.claude/agents/reviewer.md` obliga a recalcular alcance y número de mutantes,
y a muestrear supervivientes —lo que ha funcionado bien aquí—, pero **no dice
nada de verificar el `--timeout` con el que se lanzó la campaña**. Una campaña
lanzada con un timeout por debajo de lo que tarda la suite convierte todos los
supervivientes en timeouts y vacía la puerta sin dejar rastro en el informe.
Propongo añadir al bloque de mutación del protocolo: *«comprueba que la fila
Timeouts es 0, o que los timeouts que haya están justificados; una campaña con
timeouts masivos no es una campaña»*. Combinado con la observación 2 (registrar
el timeout en el informe), cierra el hueco. Para el humano y, si lo aprueba,
para `arnes-base`.
