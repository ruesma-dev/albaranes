<!-- progress/impl_F-012.md -->
# F-012 · Campaña de mutación en paralelo — Informe de implementación

Rama `feature/F-012-mutacion-paralela`. Nivel de rigor **estandar** (fase RED,
cobertura de líneas cambiadas y campaña de mutación con supervivientes
analizados).

## Qué cambió

La campaña de mutación evaluaba los mutantes **en serie**, relanzando la suite
entera por cada uno (F-011: 305 mutantes en 3.694 s). Ahora
`python -m harness.mutacion` los reparte entre **N workers concurrentes**, cada
uno sobre su propio `git worktree` desechable creado desde `HEAD` en el temp
del sistema. El informe resultante es **idéntico** al de la campaña en serie
salvo la fecha y la fila «Tiempo total».

El paralelismo se monta **por fuera** de `ejecutar_campania`, que no cambia ni
una línea: cada worker la llama tal cual con `raiz=<su worktree>` y
`mutantes=<su partición>`, así que su `try/finally` y su red de seguridad
—la parte más delicada del módulo— valen por worker sin duplicar código.

### Ficheros tocados

| Fichero | Qué |
|---|---|
| `harness/mutacion_paralela.py` | **Nuevo** (≈450 líneas). Todo lo nuevo vive aquí: `clave_estable`, `repartir`, `fusionar`, `arbol_limpio`, `Worktrees`, `fabrica_de_ejecutores`, `resolver_interpretes`, `generar_y_muestrear`, `renumerar`, `_ParticionCancelable` y el coordinador `ejecutar_campania_paralela`. Solo biblioteca estándar. |
| `harness/mutacion.py` | Tres cambios acotados: `raiz_venvs` opcional en `ejecutor_para`; flag `--workers`; `main()` delega en el coordinador cuando el número de workers es ≥ 2. Añadidos `TOPE_WORKERS`, `workers_por_defecto()` y `resolver_workers()`. **Sin tocar** `generar_mutantes`, `aplicar_mutante`, `ejecutar_campania`, `escribir_informe` ni `EjecutorPytest`. |
| `harness/rigor.py` | `workers_mutacion(rigor) -> int \| None`: lee la clave **opcional** `mutacion.workers`. A diferencia del timeout, su ausencia no es error. |
| `harness/rigor.json` | Solo el texto `$doc` del bloque `mutacion`, documentando la clave opcional. **No se declara ningún número**: un valor cableado viajaría de máquina en máquina. |
| `tests/test_f012_*.py` | 5 ficheros, 50 tests nuevos. |
| `specs/F-012-mutacion-paralela/tasks.md` | Tareas marcadas `[x]`. |
| `progress/current.md`, `progress/impl_F-012.md`, `progress/mutacion_F-012.md` | Memoria de la sesión. |

### Decisiones de diseño (y por qué)

1. **Hilos + subprocesos, no `multiprocessing`.** El coste real es el pytest de
   cada mutante, que ya es un subproceso: los hilos solo esperan E/S y el GIL
   no pinta nada. `multiprocessing` obligaría a picklear `Mutante`/`Alcance` y
   a duplicar la gestión de Ctrl-C en Windows sin aportar CPU.
2. **Worktrees `--detach` en el temp del sistema.** Sin rama efímera (no
   ensucia `git branch` ni colisiona entre campañas) y fuera del repositorio
   (dentro saldrían en `git status`, en la recolección de pytest y en el radar
   del portero). El peor caso imaginable —proceso matado— deja basura en el
   temp, que el `git worktree prune` de arranque desregistra.
3. **Limpieza en tres capas.** `__exit__` de `Worktrees` (se ejecuta con
   excepción o `KeyboardInterrupt` en vuelo) → `worktree remove --force`; si
   falla (fichero bloqueado en Windows) → `rmtree` + `prune`; y al arrancar la
   campaña siguiente, `prune` otra vez. **Desviación menor respecto al
   `design.md`:** el fallback es `rmtree` y **después** `prune`, no al revés;
   `prune` solo desregistra worktrees cuyo directorio ya no existe, así que en
   el otro orden no haría nada.
4. **Cancelación cooperativa sin tocar `ejecutar_campania`.** La partición se
   envuelve en `_ParticionCancelable`, que responde a `len()` y deja de rendir
   mutantes cuando el `threading.Event` está puesto. Ni una línea nueva dentro
   de la campaña en serie.
5. **La guarda de árbol limpio va DESPUÉS de decidir el número efectivo.** Con
   menos de dos mutantes la campaña degrada al camino en serie (R8), que muta
   in situ y siempre ha funcionado con el árbol sucio; abortar ahí rompería el
   «comportamiento de hoy sin cambios» que exige R8. Con dos o más mutantes se
   exige árbol limpio y se aborta con código 2 (R9).
6. **Un fallo en cualquier worker cancela la campaña y se relanza en el hilo
   principal.** Seguir gastando minutos para entregar después un informe
   incompleto sería lo peor de las dos opciones.
7. **`git` propio en vez de `harness.alcance.ejecutar_git`.** Aquel devuelve
   cadena vacía cuando git falla, y aquí la diferencia entre «no hay cambios» y
   «git ha fallado» decide si se aborta: un `git status` que revienta cuenta
   como árbol **no** limpio.
8. **Informe sin fila «Workers»** (criterio del humano en la spec): identidad
   estricta con el informe en serie. El número de workers se imprime por
   stdout y queda en este informe.

### Qué quedó fuera del alcance

- `harness/init.sh` no cambia: la campaña sigue sin correr en el portero (es
  cara). `CHECKPOINTS.md` tampoco: `python -m harness.mutacion --feature F-XXX`
  sigue funcionando igual y `--workers` es opcional.
- Los tests `test_f012_*` **no** se portan a arnes-base: no versiona suites de
  tests hoy y cambiar eso no es de esta feature.
- La lentitud de la suite del árbol completo (ver «Hallazgo colateral») no se
  arregla aquí: no es de esta feature.

## Fase RED (obligatoria en nivel `estandar`)

Traza real de cada tarea, con el comando exacto, **antes** de escribir el
código correspondiente.

### T1 — `repartir` / `fusionar`

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_r3_r4_reparto_agregacion.py -q
ImportError while importing test module '...\tests\test_f012_r3_r4_reparto_agregacion.py'.
Traceback:
tests\test_f012_r3_r4_reparto_agregacion.py:13: in <module>
    from harness.mutacion_paralela import clave_estable, fusionar, repartir
E   ModuleNotFoundError: No module named 'harness.mutacion_paralela'
=========================== short test summary info ===========================
ERROR tests/test_f012_r3_r4_reparto_agregacion.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.32s
```

Después del código: `11 passed in 0.05s`.

### T2 — `Worktrees` / `arbol_limpio`

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_r2_r9_r10_worktrees.py -q
ImportError while importing test module '...\tests\test_f012_r2_r9_r10_worktrees.py'.
Traceback:
tests\test_f012_r2_r9_r10_worktrees.py:17: in <module>
    from harness.mutacion_paralela import Worktrees, arbol_limpio
E   ImportError: cannot import name 'Worktrees' from 'harness.mutacion_paralela'
=========================== short test summary info ===========================
ERROR tests/test_f012_r2_r9_r10_worktrees.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.38s
```

Después del código: `12 passed in 6.22s`.

### T3 — coordinador

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_r1_r5_r11_coordinador.py tests/test_f012_r6_timeout.py -q
tests\test_f012_r1_r5_r11_coordinador.py:27: in <module>
    from harness.mutacion_paralela import (
E   ImportError: cannot import name 'ejecutar_campania_paralela' from 'harness.mutacion_paralela'
tests\test_f012_r6_timeout.py:18: in <module>
    from harness.mutacion_paralela import clave_estable, ejecutar_campania_paralela
E   ImportError: cannot import name 'ejecutar_campania_paralela' from 'harness.mutacion_paralela'
=========================== short test summary info ===========================
ERROR tests/test_f012_r1_r5_r11_coordinador.py
ERROR tests/test_f012_r6_timeout.py
!!!!!!!!!!!!!!!!!!! Interrupted: 2 errors during collection !!!!!!!!!!!!!!!!!!!
2 errors in 0.38s
```

Después del código: `12 passed in 5.39s`.

### T4 — CLI

```
$ .venv/Scripts/python.exe -m pytest tests/test_f012_r7_r8_cli.py -q
tests\test_f012_r7_r8_cli.py:17: in <module>
    from harness.mutacion import (
E   ImportError: cannot import name 'TOPE_WORKERS' from 'harness.mutacion'
=========================== short test summary info ===========================
ERROR tests/test_f012_r7_r8_cli.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.20s
```

Después del código: `15 passed in 3.00s`.

### Control del cero: los tests centrales fallan cuando se rompe lo que vigilan

Las trazas de arriba demuestran que los tests no existían antes del código.
Como esas cuatro son de importación, se añade la comprobación complementaria:
romper A PROPÓSITO el mecanismo central y ver **qué test lo caza**. (Trazas
reales en la sección siguiente; el árbol se restauró con `git checkout --`
después de cada una.)

PENDIENTE_CONTROL_CERO

## T5 · Comparación serie-vs-paralelo (criterio de éxito)

PENDIENTE_T5

## T7 · Campaña de mutación de la propia F-012

PENDIENTE_T7

## Verificaciones MANUAL pendientes

Ninguna. La feature es herramienta del arnés: no toca sistemas reales, ni
colas, ni base de datos, ni servicios. Todo lo verificable se verifica con la
suite y con las dos campañas de mutación de este informe.

## Evidencias

PENDIENTE_EVIDENCIAS
