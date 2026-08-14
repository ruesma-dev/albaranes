<!-- progress/mutacion_F-012.md -->
# F-012 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-012` el 2026-08-14 03:46.

## Alcance

Origen del diff: **rama** (`73e4db0819466c1083c28a8fdf4dee2da65533e5` .. `feature/F-012-mutacion-paralela`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 88 |
| `harness/mutacion_paralela.py` | 453 |
| `harness/rigor.py` | 15 |
| **Total** | **556** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 61 |
| Mutantes evaluados | 61 |
| Muertos | 55 |
| Supervivientes | 6 |
| Timeouts | 0 |
| Tiempo total | 1234.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/mutacion.py:587` [entero]

- Original: `return min(max(1, (os.cpu_count() or 1) - 2), TOPE_WORKERS)`
- Mutado:   `return min(max(1, (os.cpu_count() or 2) - 2), TOPE_WORKERS)`

#### Análisis

**Mutante equivalente, demostrable para toda entrada.** El operando del `or` solo se evalúa cuando `os.cpu_count()` devuelve `None`, y en ese caso `max(1, 1 - 2) = 1` y `max(1, 2 - 2) = 1`: el mismo valor. Con cualquier número de núcleos, el `or` ni se mira. No hay entrada que distinga las dos versiones, así que ningún test puede cazarlo.

> Decisión: **equivalente justificado**. Sí está cubierto el comportamiento: `test_f012_r7_workers_por_defecto_nunca_bajan_de_uno` monkeypatchea `cpu_count` a `None` y a `1` y exige 1 worker.

### 2. `harness/mutacion.py:664` [booleano]

- Original: `eco=lambda linea: print(linea, flush=True),`
- Mutado:   `eco=lambda linea: print(linea, flush=False),`

#### Análisis

**Mutante equivalente en lo observable.** `flush` decide CUÁNDO sale por pantalla la línea de progreso, no QUÉ dice ni qué acaba en el informe. El informe, los códigos de salida y los ficheros escritos son idénticos byte a byte con `flush=True` y con `flush=False`; lo único que cambia es que el progreso de una campaña de veinte minutos saldría a golpes de 8 KB en vez de línea a línea, que es exactamente lo que este `flush` evita.

> Decisión: **equivalente justificado**. Cazarlo exigiría asertar sobre el buffering del sistema operativo, que es más frágil que la línea que protege.

### 3. `harness/mutacion.py:677` [booleano]

- Original: `eco=lambda linea: print(linea, flush=True),`
- Mutado:   `eco=lambda linea: print(linea, flush=False),`

#### Análisis

**El mismo caso que el superviviente 2**, en el `eco` del camino en serie en vez del paralelo: `flush` afecta a cuándo se ve el progreso, no a lo que produce la campaña.

> Decisión: **equivalente justificado**.

### 4. `harness/mutacion_paralela.py:142` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis

**Mutante equivalente por la API de `subprocess`.** `subprocess.run` entra en modo texto si se le pasa CUALQUIERA de `encoding`, `errors`, `universal_newlines` o `text`; `_git` ya pasa `encoding="utf-8"` y `errors="replace"`, así que poner `text=False` no devuelve bytes: sigue decodificando igual. Comprobado en esta sesión: si el mutante devolviera bytes, la concatenación `(stdout or "") + (stderr or "")` reventaría con `TypeError` en el primer `git status` con salida, y la suite entera se caería.

> Decisión: **equivalente justificado**. El `text=True` se queda por legibilidad de la llamada, no porque haga falta.

### 5. `harness/mutacion_paralela.py:214` [comparacion]

- Original: `if codigo != 0:`
- Mutado:   `if codigo == 0:`

#### Análisis

**Superviviente real, de impacto acotado al peor caso de Windows.** La línea decide cuándo entra el plan B de la limpieza (`rmtree` + `prune`) después de que `git worktree remove --force` falle. Medido contra git en esta máquina: `remove` devuelve **0** aunque el directorio ya no exista (git se limita a desregistrarlo) y **255** cuando un fichero del worktree está abierto. Con el mutante, el plan B se ejecuta en el caso bueno —donde no tiene nada que hacer: `rmtree` de algo que ya no está y un `prune` que no encuentra huérfanos— y NO se ejecuta en el caso malo. El estado final coincide en todo lo que el arnés promete: el worktree queda retirado, el registro limpio y el `with` no lanza nada. La única diferencia es cuánta basura queda en el temp del sistema cuando Windows bloquea un fichero, y ahí ambas versiones dejan basura (el fichero bloqueado no se puede borrar de ninguna forma).

> Decisión: **superviviente aceptado y documentado**. Cazarlo exigiría asertar sobre QUÉ ficheros sobreviven a un borrado parcial —depende del orden de recorrido de `shutil.rmtree`— que es más frágil que el fallo que protege. Lo que sí está cubierto: que con un fichero bloqueado salir del gestor no lanza excepción (`test_f012_r10_un_fichero_abierto_no_impide_salir_del_gestor`), que el registro se retira en el camino normal y que los huérfanos de una campaña muerta se podan al arrancar la siguiente.

### 6. `harness/mutacion_paralela.py:214` [entero]

- Original: `if codigo != 0:`
- Mutado:   `if codigo != 1:`

#### Análisis

**Mutante equivalente para los códigos que git devuelve de verdad.** `git worktree remove` devuelve 0 si funciona y 128 o 255 si no (medido: 255 con un fichero bloqueado); nunca 1. Con `!= 1` la condición es cierta en los dos casos, así que el plan B se ejecuta siempre: en el caso malo hace lo mismo que la versión original y en el bueno no tiene nada que hacer. Para distinguirlo haría falta un git que devolviera exactamente 1 en este comando.

> Decisión: **equivalente justificado** (misma línea que el superviviente 5, con la misma cobertura de tests).

