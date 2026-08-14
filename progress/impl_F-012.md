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
| `tests/test_f012_*.py` | 5 ficheros, **67 tests** nuevos. |
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

**Rotura A — `fusionar` deja de ordenar por la clave estable** (el corazón de
R4: sin ese orden el informe paralelo delata en qué worker cayó cada mutante).

```
$ # rotura: setattr(informe, atributo, juntos)  en vez de  sorted(juntos, key=clave_estable)
$ .venv/Scripts/python.exe -m pytest tests/test_f012_r3_r4_reparto_agregacion.py tests/test_f012_r1_r5_r11_coordinador.py -q --tb=line
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\albaranes\tests\test_f012_r3_r4_reparto_agregacion.py:144: AssertionError: assert [('harness/un...s/dos.py', 1)] == [('harness/do...s/uno.py', 8)]
E   AssertionError: assert [('codigo.py'...racion'), ...] == [('codigo.py'...logico'), ...]

      At index 1 diff: ('codigo.py', 5, 17, 'aritmetico') != ('codigo.py', 3, 17, 'aritmetico')
      Use -v to get more diff
C:\Users\pgris\PycharmProjects\albaranes\tests\test_f012_r1_r5_r11_coordinador.py:132: AssertionError: assert [('codigo.py'...racion'), ...] == [('codigo.py'...logico'), ...]
=========================== short test summary info ===========================
FAILED tests/test_f012_r3_r4_reparto_agregacion.py::test_f012_r4_fusionar_suma_totales_y_ordena_por_clave_estable
FAILED tests/test_f012_r3_r4_reparto_agregacion.py::test_f012_r4_fusionar_agrega_y_ordena_los_timeouts
FAILED tests/test_f012_r1_r5_r11_coordinador.py::test_f012_r1_evalua_todos_los_mutantes_una_sola_vez
3 failed, 18 passed in 4.75s
[arbol restaurado]
```

**Rotura B — los workers mutan el ÁRBOL PRINCIPAL en vez de su worktree** (el
corazón de R2). El `IndexError` de la traza es el propio mecanismo delatándose:
dos hilos escribiendo el mismo fichero a la vez lo dejan inservible.

```
$ # rotura: args=(indice, raiz)  en vez de  args=(indice, ruta)
$ .venv/Scripts/python.exe -m pytest tests/test_f012_r1_r5_r11_coordinador.py -q --tb=line
E   IndexError: list index out of range
C:\Users\pgris\PycharmProjects\albaranes\harness\mutacion.py:256: IndexError: list index out of range
E   IndexError: list index out of range
C:\Users\pgris\PycharmProjects\albaranes\harness\mutacion.py:256: IndexError: list index out of range
=========================== short test summary info ===========================
FAILED tests/test_f012_r1_r5_r11_coordinador.py::test_f012_r1_evalua_todos_los_mutantes_una_sola_vez
FAILED tests/test_f012_r1_r5_r11_coordinador.py::test_f012_r1_reparte_el_trabajo_entre_varios_worktrees
FAILED tests/test_f012_r1_r5_r11_coordinador.py::test_f012_r1_r4_el_informe_paralelo_es_identico_al_de_la_campania_en_serie
FAILED tests/test_f012_r1_r5_r11_coordinador.py::test_f012_r2_el_arbol_principal_queda_intacto_y_sin_worktrees
4 failed, 6 passed in 4.84s
[arbol restaurado]
```

## T5 · Comparación serie-vs-paralelo (criterio de éxito)

### Tres desviaciones respecto a los comandos literales de `tasks.md`

Las tres se aplican **igual a las dos mitades**, así que la comparación sigue
siendo entre iguales; las tres están medidas, no supuestas.

1. **`--rama ""` en ambos comandos.** La rama `feature/F-011-evals-ia` sigue
   existiendo Y ya está mergeada en `dev`, así que el camino por rama de
   `harness.alcance` calcula `merge-base(dev, rama)` = la propia punta de la
   rama y el alcance sale **vacío**:

   ```
   $ python -c "from harness.alcance import alcance_de_feature; print(alcance_de_feature('F-011', base='dev', rama='feature/F-011-evals-ia').descripcion())"
   F-011: 0 fichero(s), 0 línea(s) de producción (origen rama, 4b57de8c1a45...^..feature/F-011-evals-ia)
   ```

   Comparar dos informes vacíos no demuestra nada. Con `--rama ""` se fuerza
   el camino por commit de merge, que es el que `harness.alcance` tiene
   previsto para features cerradas, y sale el alcance REAL de F-011: 13
   ficheros, 3.812 líneas, **305 mutantes generados** — exactamente los del
   informe histórico `progress/mutacion_F-011.md`.

2. **`--timeout 300` en ambos comandos** (el flag ya existía; no se toca
   `rigor.json`). Con el 120 s configurado, todo mutante superviviente daría
   timeout en las DOS mitades, porque la suite del árbol completo tarda hoy
   ~130 s. Ver «Hallazgo colateral».

3. **Informes fuera de `progress/` y campaña en serie sobre un worktree
   dedicado.** Lo primero, porque un `progress/tmp_*.md` sin commitear ensucia
   el árbol y la campaña paralela (R9) no arranca con el árbol sucio —lo
   comprobé en carne propia, ver más abajo—; los informes van al scratchpad de
   la sesión, que es donde `tasks.md` los quería (temporales, se pegan aquí y
   se tiran). Lo segundo, porque la campaña en serie muta EL ÁRBOL en el que
   corre durante dos horas: lanzarla con
   `--raiz <worktree detached en b23497a> --workers 1` la deja mutando un
   checkout desechable del MISMO commit que usaron los workers de la mitad
   paralela, en vez de bloquear el repositorio. Es el propio `--raiz` de
   siempre, y el commit es idéntico, así que la suite que juzga cada mutante
   es la misma en las dos mitades.

### Los comandos, tal y como se lanzaron

```bash
# Mitad paralela (16 workers por defecto: 22 núcleos lógicos - 2, con tope 16)
python -m harness.mutacion --feature F-011 --rama "" --base dev \
    --max-mutantes 60 --semilla 20260813 --timeout 300 \
    --salida <scratchpad>/mutacion_paralelo.md

# Mitad en serie, sobre un worktree desechable del mismo commit
git worktree add --detach C:/.../Temp/f012_serie_f011 b23497a
python -m harness.mutacion --feature F-011 --rama "" --base dev \
    --raiz C:/.../Temp/f012_serie_f011 --workers 1 \
    --max-mutantes 60 --semilla 20260813 --timeout 300 \
    --salida <scratchpad>/mutacion_serie.md
```

### Resultado

| Métrica | En serie (`--workers 1`) | En paralelo (16 workers) |
|---|---|---|
| Mutantes generados | 305 | 305 |
| Mutantes evaluados | 60 | 60 |
| Muertos | 37 | 37 |
| Supervivientes | 23 | 23 |
| Timeouts | 0 | 0 |
| Muestreo | sí — 60 de 305, semilla `20260813` | sí — 60 de 305, semilla `20260813` |
| **Tiempo total** | **6.491,0 s** (1 h 48 min) | **743,4 s** (12 min 23 s) |
| Segundos por mutante | 108,2 | 12,4 |

**Ganancia: 8,7× más rápido** (6.491,0 / 743,4), con 16 workers sobre 22
núcleos lógicos. No es 16× y no puede serlo: los 16 worktrees se crean al
arrancar (~40 s), el reparto no reparte trabajo idéntico —un mutante que muere
pronto cuesta menos que uno que sobrevive a la suite entera— y 16 suites
simultáneas se estorban entre ellas. Para el que espera: **de hora y tres
cuartos a doce minutos**.

Línea final de cada una, tal cual:

```
# serie
60 mutantes evaluados, 37 muertos, 23 supervivientes, 0 timeouts en 6491.0 s
INICIO 14/08/2026  5:02:41.16   FIN 14/08/2026  6:50:52.40

# paralelo
60 mutantes evaluados, 37 muertos, 23 supervivientes, 0 timeouts en 743.4 s
real    12m23.644s
```


### Diff de los dos informes (criterio de éxito)

El `diff` **crudo**, sin filtrar nada, de los dos informes completos:

```
$ diff mutacion_serie.md mutacion_paralelo.md
1c1
< <!-- .../scratchpad/mutacion_serie.md -->
---
> <!-- .../scratchpad/mutacion_paralelo.md -->
4c4
< Generado por `python -m harness.mutacion --feature F-011` el 2026-08-14 06:50.
---
> Generado por `python -m harness.mutacion --feature F-011` el 2026-08-14 02:24.
36c36
< | Tiempo total | 6491.0 s |
---
> | Tiempo total | 743.4 s |
```

**Tres líneas y ni una más**, en 154 líneas de informe: la fecha y la fila
«Tiempo total» que la spec admite (R4), y la primera línea, que es la ruta del
propio fichero y difiere por construcción —hay dos ficheros porque hay que
comparar dos informes—. Todo lo demás es idéntico: la tabla de alcance fichero
a fichero, los cinco totales, la fila de muestreo y **las 23 secciones de
supervivientes, en el mismo orden**.

Quitando esas tres líneas:

```
$ diff <(filtrar serie) <(filtrar paralelo)
SIN DIFERENCIAS
```

Los dos informes temporales se han borrado tras pegar esta evidencia, como
pedía `tasks.md`: no son informes de campaña oficiales.


## T7 · Campaña de mutación de la propia F-012

Informe: `progress/mutacion_F-012.md` (61 mutantes, campaña completa, sin
muestreo). La campaña se lanzó **con la propia implementación paralela**, que
es en sí misma parte de la evidencia de T5: el código que se está juzgando es
el que reparte a los jueces.

La campaña se ejecutó cuatro veces, y las tres primeras sirvieron para cerrar
huecos de test reales:

| Campaña | Mutantes | Muertos | Supervivientes | Timeouts | Tiempo | Qué cambió |
|---|---|---|---|---|---|---|
| 1ª (`--timeout 300`) | 61 | 37 | 24 | 0 | 910,0 s | estado tras T4 |
| 2ª (`--timeout 300`) | 61 | 51 | 7 | 3 | 871,9 s | +15 tests que cazan 17 supervivientes |
| 3ª (`--timeout 900`) | 61 | 53 | 8 | 0 | 837,6 s | mismo código; se sube el timeout y desaparecen los 3 timeouts |
| **4ª (final)** | **61** | **55** | **6** | **0** | **1.234,0 s** | +1 test del fallback de limpieza con fichero bloqueado |

- **Los 3 timeouts de la 2ª campaña eran contención, no mutantes lentos.** Con
  16 suites simultáneas la suite del árbol completo (~130 s en reposo) puede
  pasar de 300 s. Es el riesgo que anticipa el `design.md`, y se resolvió como
  dice: subiendo el timeout, sin tocar código. Los tres mutantes «lentos»
  volvieron a su sitio (dos muertos, uno equivalente) en cuanto tuvieron
  margen.
- **De 24 supervivientes a 6**: los 18 cazados eran huecos de verdad —la
  frontera de dos workers, el ejecutor inyectado, el muestreo exacto, el fallo
  de un worker, el reloj del informe, el fallback de limpieza—, no ruido.
- **Los 6 supervivientes finales están analizados uno a uno** en
  `progress/mutacion_F-012.md`, sin ningún `PENDIENTE`: cinco son equivalentes
  demostrables (dos `flush` de la línea de progreso, el `or 1` del contador de
  núcleos que da 1 worker en ambas versiones, el `text=True` que `subprocess`
  ya deduce de `encoding=`, y un `!= 1` sobre códigos de salida que git nunca
  devuelve) y el sexto es un superviviente aceptado: cambia CUÁNDO corre el
  plan B de la limpieza sin cambiar el estado final, y cazarlo exigiría
  asertar sobre los restos de un borrado parcial.

Mutation score final: **55/61 = 90,2 %**; contando como no-cazables los cinco
equivalentes demostrables, 55/56 = 98,2 %.

## T6 · Portado a arnes-base (R12)

Copiados `mutacion.py`, `mutacion_paralela.py`, `rigor.py` y `rigor.json` a
`C:\Users\pgris\PycharmProjects\arnes-base\arnes-base\harness\`, con commit
local **`0436314`** («Campana de mutacion en paralelo: N workers, cada uno en
su git worktree») y **sin push**, como manda el convenio. `VERSION` no se toca:
arnes-base sigue en 1.4.0 con commits pendientes de push, y la spec no pide
subirla.

Verificación de que las dos copias son la misma (el contenido **commiteado**,
que es lo que se versiona):

```
$ git show HEAD:harness/mutacion_paralela.py | md5sum
fb1ff7941742016bab4191d1fe4700e4 *-
$ git -C ../arnes-base show HEAD:arnes-base/harness/mutacion_paralela.py | md5sum
fb1ff7941742016bab4191d1fe4700e4 *-
$ for f in mutacion.py mutacion_paralela.py rigor.py rigor.json; do
      diff -q --strip-trailing-cr ../arnes-base/arnes-base/harness/$f harness/$f; done
(sin salida: idénticos)
```

`diff` a secas sí marca diferencia en `mutacion_paralela.py`, y conviene saber
por qué: `core.autocrlf` de esta máquina deja el fichero de trabajo de
albaranes en CRLF (se recheckeó al restaurarlo tras las roturas deliberadas de
la fase RED) y el de arnes-base en LF. El contenido versionado es idéntico
—mismo md5 del objeto de git—, que es lo que R12 exige. De ahí el
`--strip-trailing-cr` en la comprobación.

Los tests `test_f012_*` NO se portan: arnes-base no versiona suites de tests
hoy, y cambiar eso no es de esta feature (así lo fija el `design.md`).

## Hallazgo colateral (no es de esta feature, pero conviene saberlo)

La campaña de mutación juzga los ficheros que no pertenecen a ningún servicio
con la suite de la RAÍZ, y esa suite se lanza sin acotar ruta, así que recoge
todo el árbol. Hoy tarda **~130 s**, y **93 s** se los come el `setup` de un
solo test:

```
$ .venv/Scripts/python.exe -m pytest services/albaranes-comun/tests -q --durations=8
92.87s setup    tests/test_humo_colas.py::test_publicar_y_consumir
 1.35s call     tests/test_humo_sharepoint.py::test_validacion_de_modos
 ...
19 passed, 3 skipped in 104.08s (0:01:44)
```

Consecuencias medidas:

- En la campaña de F-011 (2026-08-13) el coste era de **12,1 s por mutante**;
  hoy es de **~130 s**, diez veces más. La diferencia no está en el mutador:
  está en ese fixture.
- Con el `timeout_por_mutante_s` de 120 s de `harness/rigor.json`, **cualquier
  campaña de este repositorio daría timeout en todos los mutantes que
  sobreviven**, en serie y en paralelo. Por eso las dos mitades de T5 se
  lanzaron con `--timeout 300` (el mismo valor en ambas: la comparación sigue
  siendo justa) y la campaña de F-012 con `--timeout 900`.
- Se deja apuntado, no arreglado: no es de esta feature. Candidatos obvios
  para otra: marcar ese test de humo con un marcador que la campaña pueda
  deseleccionar, o subir `timeout_por_mutante_s` en `rigor.json`.

## Verificaciones MANUAL pendientes

Ninguna. La feature es herramienta del arnés: no toca sistemas reales, ni
colas, ni base de datos, ni servicios. Todo lo verificable se verifica con la
suite y con las dos campañas de mutación de este informe.

## Evidencias

Todos los números están medidos en esta sesión, no estimados.

| Evidencia | Valor | De dónde sale |
|---|---|---|
| **Tests ejecutados y resultado** | **242 pasados, 0 fallos** en la suite de la raíz (**67 nuevos de F-012**), más 19 pasados y 3 saltados en la suite del servicio `comun` | `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **95,8 %** (184/192 líneas), umbral 80 %, nivel `estandar` | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | **61 generados, 55 muertos, 6 supervivientes, 0 timeouts** (los 6 analizados, ninguno en `PENDIENTE`) | `python -m harness.mutacion --feature F-012` → `progress/mutacion_F-012.md` |
| **Tiempo de ejecución de la suite** | **34,18 s** la suite de la raíz bajo `coverage`; **~130 s** la del árbol completo, que es la que juzga cada mutante | salida de pytest en `init.sh` |

Veredicto del portero:

```
$ bash harness/init.sh
...
242 passed in 34.18s
[OK] pytest en verde (con medición de cobertura)
[OK] servicio comun (services/albaranes-comun): pytest en verde (caché: árbol sin cambios desde el último verde)
[OK] PUERTA COBERTURA: 95.8% de 192 líneas cambiadas cubiertas (184/192, umbral 80%, nivel estandar)
[OK] PUERTA RUTAS SENSIBLES [evals]: N/A (F-012 no toca ninguna ruta sensible declarada)
[OK] Rama actual: feature/F-012-mutacion-paralela
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
(exit 0)
```

### Evidencia extra, regalada por un accidente

A mitad de la campaña en serie (mutante 33 de 60) el arnés mató la tarea de
fondo que la contenía. Un `kill` en seco: el `try/finally` de
`ejecutar_campania` no llegó a ejecutarse. El estado que quedó es exactamente
el que el diseño promete:

```
$ git -C <worktree de la serie> status --porcelain
 M evals/procesos/sv5_valoracion.py      <-- el mutante que estaba en vuelo, aplicado

$ git status            # árbol principal
 M progress/current.md                   <-- solo mis propias ediciones
 M progress/impl_F-012.md
```

La mutación se quedó **dentro del checkout desechable** y el árbol de trabajo
real no se enteró. Se restauró con un `git checkout -- .` en el worktree y la
campaña se relanzó desde cero. Es el peor caso de R10 ocurrido de verdad, no
en un test.

