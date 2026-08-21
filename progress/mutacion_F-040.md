<!-- progress/mutacion_F-040.md -->
# F-040 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-040` el 2026-08-21 20:51.

## Alcance

Origen del diff: **rama** (`2ccb8acd8e85e9eff1cfc80bcf7cf9c52cfeb11b` .. `feature/F-040-campana-dimensionada-y-honesta`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 362 |
| `harness/mutacion_paralela.py` | 30 |
| `harness/rigor.py` | 20 |
| **Total** | **412** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 49 |
| Mutantes evaluados | 20 |
| Muertos | 17 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 336.3 s |
| SHA de HEAD medido | `e73a20791b106ca47bb929ca8051068ebf2a462b` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_fly11ff6/wk_0` | 64.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_fly11ff6/wk_1` | 68.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_fly11ff6/wk_2` | 64.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_fly11ff6/wk_3` | 64.7 |
| Media por mutante evaluado (s) | 16.8 |
| Timeout efectivo por mutante (s) | 137 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | sí — 20 de 49 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

> **Los tres analizados.** De los tres, uno es un mutante **equivalente**, otro
> era un **hueco real** (cerrado con test) y el tercero es un **FALSO
> superviviente**: la suite lo caza y este informe dice que no. Contrastado con
> una campaña en serie de los mismos 20 mutantes (`--workers 1`, 18 muertos,
> 2 supervivientes), que acertó en ése y falló en otro distinto
> (`mutacion.py:677`, también reproducido y también muerto). El recuento
> honesto de los 20: **19 cazados y 1 equivalente**. Ver
> `progress/impl_F-040.md`, «El quinto defecto».


Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/mutacion.py:1942` [entero]

- Original: `return min(max(1, ((os.cpu_count() or 1) - 2) // 2), TOPE_WORKERS)`
- Mutado:   `return min(max(2, ((os.cpu_count() or 1) - 2) // 2), TOPE_WORKERS)`

#### Análisis

**FALSO superviviente.** La suite SÍ lo caza; este veredicto no describe lo que
hace la suite. Reproducido dos veces, las dos en rojo:

- En el árbol principal: `python -m pytest tests -x -q --tb=line`
  -> `FAILED tests/test_f012_r7_r8_cli.py::test_f012_r7_workers_por_defecto_nunca_bajan_de_uno`
  (`assert 2 == 1`), `1 failed, 230 passed in 31.76s`.
- En un `git worktree --detach` recién creado desde HEAD, con la MISMA
  invocación que usa un worker
  (`python -m pytest -x -q --tb=no -p no:cacheprovider tests`, `cwd` = worktree):
  `EXIT=1`, o sea `PYTEST_FALLOS` = **muerto**.

Y la campaña en serie de los mismos 20 mutantes lo declaró **muerto**
(`[6/20] muerto`). Decisión: **no se añade test** —ya hay dos que lo matan—,
se abre hallazgo. Ver `progress/impl_F-040.md`, «El quinto defecto».

### 2. `harness/mutacion.py:1942` [entero]

- Original: `return min(max(1, ((os.cpu_count() or 1) - 2) // 2), TOPE_WORKERS)`
- Mutado:   `return min(max(1, ((os.cpu_count() or 2) - 2) // 2), TOPE_WORKERS)`

#### Análisis

**Mutante equivalente**, demostrado por aritmética. El literal solo se usa
cuando `os.cpu_count()` devuelve `None`, y en ese caso:

- original: `(1 - 2) // 2 = -1` -> `max(1, -1) = 1` -> `min(1, 4) = **1**`
- mutado:   `(2 - 2) // 2 =  0` -> `max(1,  0) = 1` -> `min(1, 4) = **1**`

Los dos devuelven 1, que es lo que exige R8 («nunca menos de un worker»).
De hecho cualquier valor del 1 al 5 da 1: el `max(1, ...)` de al lado absorbe
la diferencia. Ningún test puede distinguirlos porque no hay nada que
distinguir. Sobrevivió también en la campaña en serie, como corresponde a un
equivalente de verdad. Decisión: **equivalente aceptado**, sin test nuevo.

### 3. `harness/mutacion_paralela.py:407` [booleano]

- Original: `timeout_fijado: bool = False,`
- Mutado:   `timeout_fijado: bool = True,`

#### Análisis

**Hueco de test REAL, ya cerrado.** El único llamador de producción (`main`)
pasa siempre `timeout_fijado=` explícito, y los dobles de los demás tests no
saben correr una línea base: sin medición, el derivado coincide con el suelo y
nadie nota la diferencia. Con el default en `True` la derivación de D1 se
apagaría entera y la suite seguiría verde.

Cerrado en el commit `6d582b9` con
`test_f040_r6_la_campania_paralela_deriva_por_defecto`, que monta un
repositorio de juguete y exige `timeout_fijado is False` y un efectivo por
encima del suelo. Verificado a mano: con el mutante puesto el test cae
(`AssertionError: ... assert True is False`) y sin él pasa. La campaña en serie
posterior ya lo dio por **muerto** (`[16/20] muerto`).

