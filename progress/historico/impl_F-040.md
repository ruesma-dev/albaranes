<!-- progress/impl_F-040.md -->
# F-040 · Informe de implementación

**La campaña de mutación se dimensiona sola y deja de mentir sobre lo que ha
medido.** 27 requisitos, 26 tareas, un commit por tarea, todo del arnés: ni una línea de
`services/`. La prueba de campo de que D1 funciona es que **la campaña de esta
feature se lanzó sin `--timeout`** —imposible en esta máquina el 2026-08-21— y
sus cuatro líneas base pasaron en verde con **4 workers**, el tope nuevo.

## Qué cambió, por tarea

| Tareas | Qué |
|---|---|
| T1–T2 | **R22**: `timeout_mutacion` rechaza el booleano (`true` daba **1 s** por mutante y toda la campaña en «timeout») y separa «falta la clave» de «el valor no vale»; `null` cuenta como ausencia. **R23**: `--timeout <= 0` y `--workers < 1` salen con **2** y mensaje de uso; antes `--timeout 0` era falsy y caía en silencio al valor configurado. |
| T3–T6 | **R25/R26**: los dos supervivientes que dejó F-039 en `rigor.py`. **R24**: la retirada de worktrees con un `git` que FALLA (`rmtree` y luego `prune`, en ese orden). Huecos de **test**: no se toca el código. |
| T7–T9 | **D3 (R11–R13)**: `_base_rota_al_final` distingue `expirado` de `not verde`. **R20**: la fila de `## Timeouts` deja de duplicar `fichero:línea`. |
| T10–T11 | **D4 (R14–R17)**: las dos guardas de «nada que juzgar», en `main`, el embudo. |
| T12–T13 | **R18**: `main` deja de tirar el código de `_modo_restaurar`. **R19**: hueco de test. |
| T14–T15 | **D2 (R8–R10)**: `TOPE_WORKERS` 16 → 4 y `workers_por_defecto` con `(núcleos-2)//2`. |
| T16–T17 | **R1/R2**: `timeout_derivado` y `timeout_de_linea_base`, puras, con `MARGEN_TIMEOUT = 2.0` y `FACTOR_HOLGURA_BASE = 5` como constantes del código. |
| T18–T20 | **D1** cableado en `ejecutar_campania` y propagado a la paralela; `fusionar` declara el timeout del **peor** worker. **R5**: el aborto por base expirada nombra workers, reloj concedido y la clave que se sube. |
| T21–T23 | **R4**: filas nuevas del informe (timeout efectivo, suelo, workers) y `FILAS_DE_RELOJ` ampliada. **R7/R9**: `$doc` de `mutacion` reescrito, sin declarar `workers`. **R27**: RM2 de `CHECKPOINTS.md` (ver «Desviaciones»). |
| T24–T26 | Campaña, análisis de supervivientes, topes de papeleo e `init.sh`. |

Ficheros tocados: `harness/{mutacion,mutacion_paralela,rigor}.py`, `rigor.json`,
`CHECKPOINTS.md`, 3 ficheros de test nuevos, 3 tests previos actualizados (ver
«Desviaciones») y el inventario de campañas.

## Fase RED

Nivel `estandar`. Trazas reales; comando siempre
`python -m pytest <fichero> -k <sel> -q --no-header -p no:cacheprovider`.

**T1 · R22/R23** (`test_f040_r18_r26_huecos.py -k "r22 or r23"`):

```
E       assert 'no vale' in "Falta 'mutacion.timeout_por_mutante_s' en la configuración de rigor."
...
E       Failed: DID NOT RAISE SystemExit
12 failed, 5 passed in 0.19s
```

**T7 · R11/R20** (`test_f040_r11_r17_honestidad.py`):

```
E   AssertionError: assert 'no falló' in 'La línea base estaba VERDE al empezar y ROJA
    al terminar en wk_0 (código -1). ... Arregla la suite y repite la campaña.'
E   AssertionError: el aviso tiene que decir cuánto tiempo se concedió
E   AssertionError: fichero:línea duplicado en la fila de timeouts:
    '- `harness/mutacion.py:42` harness/mutacion.py:42 [comparacion] a == b -> a != b'
3 failed, 7 passed in 0.21s
```

**T10 · R14–R17** (`-k "r14 or r15 or r16 or r17"`):

```
E   AssertionError: el mensaje tiene que decir el porqué: alcance vacío o sin código mutable
6 failed, 13 passed in 0.62s
```
Los seis: el alcance vacío seguía adelante y la campaña de cero escribía informe
y salía **0**.

**T14 · R8** (`test_f040_r1_r10_dimensionado.py -k "r8 or r9 or r10"`):

```
E   assert 16 == 4
E    +  where 16 = workers_por_defecto()
8 failed, 10 passed in 0.19s
```

- **T12 · R18** (`-k "r18 or r19"`): `2 failed, 38 passed` — la campaña arrancaba sobre un árbol con un mutante viejo sin deshacer.
- **T16 · R1/R2**: error de recolección — `ImportError: cannot import name 'FACTOR_HOLGURA_BASE' from 'harness.mutacion'`.
- **T18 · R3/R5/R6**: `8 failed, 29 passed in 6.20s` — `TypeError: ejecutar_campania() got an unexpected keyword argument 'workers'`.
- **T21 · R4**: `4 failed, 2 passed` (no existían las tres filas del informe). **T23 · R27**: `1 failed, 45 passed` (RM2 no nombraba los workers).

### RED de los huecos de test (T3–T6): matando el mutante que sobrevivió

R24–R26 son huecos de **test**, no de código: el test nuevo pasa desde el primer
momento y una traza en rojo sería imposible. La evidencia equivalente —y más
fuerte— es aplicar el mutante que sobrevivió en F-039 y ver que ahora muere.
Los cuatro, aplicados y restaurados (`git diff` vacío después):

| Mutante aplicado | Con el mutante puesto |
|---|---|
| `rigor.py`: `or` → `and` en `validar_features` | 5 tests en rojo (`KeyError: 'rigor'`) |
| `rigor.py`: `return 1` → `return 2` en `main` | 1 test en rojo (`assert 2 == 1`) |
| `mutacion_paralela.py`: `codigo != 0` → `== 0` | 2 tests en rojo |
| `mutacion_paralela.py`: `prune` antes de `rmtree` | 1 test en rojo (`assert 1 > 2`) |

## `bash harness/init.sh`

**En verde** (`ENTORNO LISTO. Puedes trabajar.`):

```
530 passed in 81.35s (0:01:21)   -> pytest en verde (con medición de cobertura)
PUERTA COBERTURA: 100.0% de 79 líneas cambiadas cubiertas (79/79, umbral 80%, nivel estandar)
PUERTA TAMAÑO: F-040 dentro de los topes (requirements 117/150, design 176/250, impl 218/220)
```

Los avisos restantes son deuda previa, no de F-040: ruff (1108, los mismos que en
`dev`), sv1-email e infra sin tests, y marcas `[ADAPTAR]` en F-034 y F-035.

## Campaña de mutación

`python -m harness.mutacion --feature F-040 --salida progress/mutacion_F-040.md`,
**sin `--timeout`**:

```
Timeout por mutante: se derivará de la línea base medida, con suelo 120 s y
margen 2.0. La propia línea base dispone de 600 s.
Campaña paralela: hasta 4 workers, uno por worktree.
[base] .../wk_3: en verde (64.7 s)   [.../wk_0: 64.9]   [.../wk_2: 64.9]
[base] .../wk_1: en verde (68.3 s)
[base] timeout por mutante: 137 s = max(suelo 120 s, peor línea base 68.3 s × margen 2.0)
20 mutantes evaluados, 17 muertos, 3 supervivientes, 0 timeouts, 0 sin veredicto en 336.3 s
```

Los tres supervivientes quedan analizados **en el propio informe**: uno es
**equivalente**, otro era un **hueco real** (el default `timeout_fijado = False`
de `ejecutar_campania_paralela` apagaría la derivación entera sin que nada se
quejara), cerrado con test nuevo en `6d582b9`, y el tercero es **falso**.

## El QUINTO defecto: la campaña etiqueta mal algún mutante, y no siempre el mismo

**NO entra en esta feature** (regla del `design.md` §5): lo decide el humano.
Los mismos 20 mutantes, medidos dos veces sobre el mismo `harness/`:

| Mutante | Paralela (4 workers) | Serie (`--workers 1`) | Reproducido a mano |
|---|---|---|---|
| `mutacion.py:1942` `max(1,` → `max(2,` | **superviviente** | muerto | **muerto** |
| `mutacion.py:677` `*` → `//` | muerto | **superviviente** | **muerto** |
| `mutacion.py:1942` `or 1` → `or 2` | superviviente | superviviente | equivalente |
| `mutacion_paralela.py:407` `False` → `True` | superviviente | muerto (test añadido) | hueco real |

Totales: paralela 17/3 en 336,3 s; serie 18/2 en 832,8 s. **Cada modo declaró
superviviente a un mutante distinto que la suite sí caza.** Reproducciones, con
la invocación exacta del ejecutor (`pytest -x -q --tb=no -p no:cacheprovider tests`):

```
(max(1,→max(2,) FAILED test_f012_r7_workers_por_defecto_nunca_bajan_de_uno
                assert 2 == 1  ->  EXIT=1 (= PYTEST_FALLOS = muerto)
(*→//)          FAILED test_f040_r2_la_linea_base_recibe_el_suelo_por_el_factor
                1 failed, 464 passed  ->  EXIT=1
```
La primera se repitió dentro de un `git worktree --detach` recién creado desde
HEAD, para descartar el worktree como causa: también `EXIT=1`.

Un falso superviviente es el espejo del falso muerto que arreglaron F-012 y
F-038: hace trabajar de más en vez de dar por bueno lo que no lo es, pero rompe
la misma promesa —que el veredicto describa lo que hace la suite—, y el mismo
mecanismo podría fallar hacia el otro lado. **Descartado por medición**: no es
que la suite no cace el mutante (lo caza), ni que el worktree importe el código
del árbol principal (habrían sobrevivido los 20 y murieron 17), ni el paralelo
(la serie falla igual, en otro mutante). Es **no determinista**.

**Propuesta**: ficha nueva, rigor `critico`, con una primera tarea de
diagnóstico —que `EjecutorPytest.ejecutar` guarde en el informe el **código de
salida** de cada mutante—. Hoy un `superviviente` puede ser un `exit 0` o un
`exit 5` («ningún test recogido»), que `ResultadoSuite.verde` cuenta igual, y
sin ese dato la campaña no puede demostrar de qué habla.

Efecto sobre esta feature: **ninguno en el recuento de muertos**. Uniendo las
dos campañas y las reproducciones, los 20 mutantes son **19 cazados y 1
equivalente**.

## Desviaciones respecto a la spec

1. **R27, la fórmula de RM2.** La spec pedía escribir que con W workers el
   «Tiempo total» es `mutantes × media / W`. No cuadra: `media` es tiempo de
   **pared** entre los mutantes, así que `mutantes × media` ES el Tiempo total
   por construcción y la media **ya viene dividida entre W**. Lo que engaña —y
   es lo que R27 quiere evitar— es compararla con la «Línea base (s)». RM2 dice
   ahora que el coste real por mutante es `media × W`, con los números medidos
   aquí (base 64,9 s, media 16,8 s, 4 workers → 67 s). El propósito se cumple
   entero; el texto literal, no.
2. **La línea base de CIERRE recibe el timeout de base, no el de mutante.** No
   lo pide ningún requisito, pero R2 razona que una línea base se paga una vez
   por worker: darle el reloj corto convertiría en «base expirada» lo que solo es
   una máquina ocupada, que es justo la mentira que quita R11.
3. **Tres tests previos actualizados.** Los dobles de `test_f012_r7_r8_cli.py`
   (×2) y `test_f039_r15_r16_alcance_por_ficheros.py` (×1) devolvían un informe
   de **cero mutantes en verde**, que es lo que R14 prohíbe; se les pone un
   recuento real, porque su sujeto era qué argumentos recibió la campaña. Y dos
   de `test_f012` fijaban la fórmula vieja de workers: se actualizan con el
   motivo escrito y un puntero al fichero nuevo.

## Para el humano

1. **El quinto defecto**: ficha nueva o no. No entra aquí.
2. **`TOPE_WORKERS = 4` queda validado en campo** —era la decisión 3, sin medir—:
   4 líneas base en verde a 64,7–68,3 s con los cuatro workers compitiendo, y
   **cero timeouts** en 20 mutantes.
3. **Verificaciones MANUAL pendientes: ninguna.**

## Después del merge en `dev` (NO en esta rama)

Porte a `arnes-base` **1.7.2**; `arnes-base` no se ha tocado.

| Fichero | Qué se porta |
|---|---|
| `harness/mutacion.py` | `TOPE_WORKERS = 4` y `workers_por_defecto` con `// 2`; `MARGEN_TIMEOUT`, `FACTOR_HOLGURA_BASE`, `timeout_derivado`, `timeout_de_linea_base`; `comprobar_linea_base(..., workers=)` y `mensaje_base_expirada_al_arrancar`; `_base_rota_al_final` con su rama de expiración; `ejecutar_campania(timeout_base_s, timeout_fijado, workers)`; filas nuevas del informe y `FILAS_DE_RELOJ` ampliada; `## Timeouts` sin duplicar; guardas de D4 y R18 en `main`; validación de `--timeout`/`--workers` |
| `harness/mutacion_paralela.py` | propagación de `timeout_base_s`/`timeout_fijado`/`workers` y `fusionar(workers=)` |
| `harness/rigor.py` + `rigor.json` | `timeout_mutacion` (booleano rechazado, mensajes separados) y el `$doc` de `mutacion`; la clave `workers` NO se declara |
| `CHECKPOINTS.md` + `tests/test_f040_*.py` | la nota de RM2; los tres ficheros de test, si `arnes-base` lleva la suite del arnés |

**Aviso obligatorio en `GUIA_INSTALACION.md`**: los tiempos de campañas
paralelas anteriores **dejan de ser comparables** (timeout derivado; tope 16→4).
## Evidencias

| Evidencia | Valor (medido, no estimado) |
|---|---|
| Tests ejecutados (raíz) | **530** en verde, 81,35 s. Las 6 suites de servicio, en verde (caché: árbol sin cambios) |
| Cobertura de las líneas cambiadas | **100,0 %** — 79/79 líneas cambiadas (umbral 80 %, nivel `estandar`) |
| Mutantes generados / evaluados | 49 / 20 (muestreo del nivel `estandar`, semilla `20260820`) |
| Muertos / supervivientes / timeouts / sin veredicto | 17 / 3 / 0 / 0 (paralela) · 18 / 2 / 0 / 0 (serie de contraste) |
| Supervivientes analizados | 3 de 3, ninguno en `PENDIENTE`: 1 equivalente, 1 hueco cerrado con test, 1 falso |
| Tiempo de la campaña | 336,3 s con 4 workers; líneas base 64,7–68,3 s; timeout efectivo **137 s** (suelo 120) |
| Tiempo de ejecución de la suite | **81,35 s** (raíz, bajo medición de cobertura) |
| Ruff en lo tocado | los 3 ficheros de test, sin avisos; `harness/` mantiene los mismos que `dev` (8 en `mutacion.py`, 4 en `rigor.py`). Detalle de la campaña: `progress/mutacion_F-040.md` |
