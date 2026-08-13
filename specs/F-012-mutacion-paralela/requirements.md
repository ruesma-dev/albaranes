<!-- specs/F-012-mutacion-paralela/requirements.md -->
# F-012 · Campaña de mutación en paralelo — Requisitos (EARS)

Contexto medido: la campaña de F-011 evaluó **305 mutantes en 3.694 s**
(~12,1 s/mutante) porque `harness.mutacion` relanza la suite en serie por
cada mutante. Esta feature paraleliza la evaluación en N workers, cada uno
sobre su propio `git worktree`, sin cambiar el contrato del informe que el
reviewer verifica en C4 bis.

Vocabulario: «coordinador» = el proceso `python -m harness.mutacion`;
«worker» = cada evaluador concurrente con su worktree; «árbol principal» =
el directorio de trabajo desde el que se lanza la campaña; «clave estable de
un mutante» = la tupla `(fichero, linea, col, operador)` con la que ya ordena
el código actual.

## Ejecución paralela

- **R1.** CUANDO se ejecuta `python -m harness.mutacion --feature F-XXX
  --workers N` con `N >= 2` y hay al menos 2 mutantes que evaluar, el sistema
  debe evaluar los mutantes repartidos entre workers concurrentes y escribir
  el informe agregado en `progress/mutacion_F-XXX.md` (o en `--salida`), con
  los mismos códigos de salida que hoy: 0 sin supervivientes, 1 con
  supervivientes, 2 error de uso.

- **R2.** MIENTRAS la campaña paralela está en marcha, cada worker debe
  evaluar sus mutantes escribiendo ÚNICAMENTE dentro de su propio
  `git worktree` (creado fuera del árbol principal), y ningún fichero del
  árbol principal debe modificarse en ningún momento de la campaña.

- **R3.** El sistema debe generar los mutantes UNA sola vez en el coordinador
  (y aplicar el muestreo `--max-mutantes`/`--semilla` UNA sola vez, antes del
  reparto), de modo que la unión de las particiones asignadas a los workers
  sea exactamente el conjunto que evaluaría la campaña en serie, sin mutantes
  repetidos ni omitidos, con reparto determinista para las mismas entradas.

- **R4.** El informe agregado debe ser idéntico en formato y totales al que
  produciría la campaña en serie sobre el mismo commit y la misma suite
  (alcance, generados, evaluados, muertos, supervivientes, timeouts, fila de
  muestreo y secciones de supervivientes en el mismo orden por clave
  estable); solo pueden diferir la fecha de la línea «Generado por…» y la
  fila «Tiempo total».

- **R5.** CUANDO un mutante pertenece a un servicio Python declarado en
  `harness/servicios.json`, el worker debe juzgarlo con la suite de ESE
  servicio ejecutada desde el directorio del servicio DENTRO de su worktree,
  con el intérprete del servicio resuelto contra el árbol principal (los
  venvs no están versionados y no existen dentro de un worktree).

- **R6.** El sistema debe aplicar a cada worker el mismo
  `timeout_por_mutante_s` de `harness/rigor.json` que aplica la campaña en
  serie, y agregar los timeouts de todos los workers en la sección
  «Timeouts» del informe.

## Configuración de workers

- **R7.** CUANDO no se pasa `--workers`, el sistema debe tomar el número de
  workers de la clave opcional `mutacion.workers` de `harness/rigor.json` y,
  si no existe, de `min(max(1, núcleos_de_la_máquina - 2), 16)` (decisión
  del humano 2026-08-13: tope de 16 workers; en esta máquina, 22 núcleos
  lógicos ⇒ 16).

- **R8.** CUANDO el número efectivo de workers es `<= 1` —porque se pidió
  `--workers 1`, porque la máquina no da para más o porque hay menos de 2
  mutantes—, el sistema debe ejecutar la campaña por el camino en serie
  actual (mutación in situ en el árbol indicado por `--raiz`, sin crear
  ningún worktree), con el comportamiento de hoy sin cambios. El número
  efectivo es `min(workers_pedidos, nº de mutantes a evaluar)`.

## Guardas y limpieza

- **R9.** SI el árbol principal tiene cambios sin commitear (`git status
  --porcelain` no vacío), ENTONCES la campaña paralela debe abortar con
  código 2 y un mensaje que indique commitear o usar `--workers 1`, sin
  crear ningún worktree ni tocar ningún fichero. (Motivo: los worktrees se
  crean desde `HEAD`; con el árbol sucio evaluarían un código distinto del
  que se ve en disco.)

- **R10.** SI la campaña paralela termina por cualquier vía —éxito,
  excepción o Ctrl-C—, ENTONCES al salir no debe quedar registrado ningún
  worktree creado por ella (`git worktree list` no los muestra y sus
  directorios temporales se han borrado o quedado inertes en el temp del
  sistema), y el árbol principal debe quedar byte a byte como estaba.
  Además, CUANDO arranca una campaña paralela, el sistema debe ejecutar
  `git worktree prune` para retirar registros huérfanos de campañas
  anteriores muertas.

- **R11.** SI un servicio afectado por el alcance declara un `venv` que no
  contiene intérprete, ENTONCES la campaña paralela debe fallar con código 2
  ANTES de crear ningún worktree (la resolución de intérpretes se hace por
  adelantado para todos los ficheros del alcance).

## Portado a arnes-base

- **R12.** El sistema debe dejar los ficheros del arnés creados o
  modificados por esta feature idénticos en
  `C:\Users\pgris\PycharmProjects\arnes-base\arnes-base\harness\`
  (comprobable con un diff sin diferencias), como parte de esta misma
  feature.

## Trazabilidad prevista

| Requisito | Test |
|---|---|
| R1, R5, R11 | `tests/test_f012_r1_r5_r11_coordinador.py` |
| R2, R9, R10 | `tests/test_f012_r2_r9_r10_worktrees.py` |
| R3, R4 | `tests/test_f012_r3_r4_reparto_agregacion.py` |
| R6 | `tests/test_f012_r6_timeout.py` |
| R7, R8 | `tests/test_f012_r7_r8_cli.py` |
| R12 | verificación por diff (T6 de tasks.md) |

Todos los tests corren sin red ni BBDD: git local sobre repositorios
temporales (`tmp_path`) y ejecutores falsos inyectados en lugar de pytest
real. La comparación serie-vs-paralelo sobre una feature real es la
verificación de cierre (T5 de tasks.md), no un unit test.
