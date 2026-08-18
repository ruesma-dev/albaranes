<!-- progress/mutacion_F-019.md -->
# F-019 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-019` el 2026-08-18 21:55.

## Alcance

Origen del diff: **rama** (`cd904cdcecee56311280ee54d81a7158d0529eb5` .. `feature/F-019-importe-unitario-manda`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py` | 64 |
| `services/albaran-valoracion-persist/application/services/importe_calculator.py` | 32 |
| `services/albaran-valoracion-persist/application/services/price_reconciler.py` | 63 |
| `services/albaran-valoracion-persist/domain/models/valuation_envelope.py` | 17 |
| `services/albaranes-comun/ruesma_comun/importes.py` | 107 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 232 |
| **Total** | **515** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 31 |
| Mutantes evaluados | 31 |
| Muertos | 28 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Tiempo total | 219.2 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-comun/ruesma_comun/importes.py:72` [comparacion]

- Original: `if 0.0 < valor <= 100.0:`
- Mutado:   `if 0.0 <= valor <= 100.0:`

#### Análisis — **mutante EQUIVALENTE**, justificado

La diferencia entre `0.0 <` y `0.0 <=` solo se notaría con `valor == 0.0`,
y ese caso **ya ha vuelto en la línea anterior** (`if valor == 0.0: return
"cero", 0.0`). El `-0.0` tampoco lo distingue: en Python `-0.0 == 0.0` es
`True`, así que también sale por la rama del cero. La rama mutada es
inalcanzable para el único valor que la separaría de la original.

Comprobado ejecutando ambas versiones sobre los 13 valores de frontera
relevantes —`0.0`, `-0.0`, `±1e-12`, `0.5`, `40.0`, `100.0`,
`100.0000001`, `-5.0`, `1000.0`, `±inf` y `nan`—: **0 diferencias**.

Decisión: **equivalente**. No se toca el código: escribir el rango
abierto por abajo dice lo que se quiere decir (un descuento aplicable es
estrictamente mayor que cero) aunque el cero ya se haya filtrado antes.

### 2. `services/albaranes-comun/ruesma_comun/importes.py:101` [logico]

- Original: `if cantidad is None or precio_unitario is None:`
- Mutado:   `if cantidad is None and precio_unitario is None:`

#### Análisis — **mutante EQUIVALENTE**, justificado

Mismo mecanismo que ya se analizó en la pasada anterior para la copia de
sv4, que este round trip ha sustituido por esta función compartida: con
`and`, un solo `None` deja pasar la línea siguiente
—`float(cantidad) * float(precio_unitario)`—, que lanza `TypeError` y cae
en el `except (TypeError, ValueError): return None`. El valor devuelto es
`None` en los dos casos.

Comprobado ejecutando ambas versiones sobre las **81 combinaciones** de
`None`, `0.0`, `1.0`, `-2.5`, `"3"`, `"x"`, `object()`, `True` y `nan`:
**0 diferencias**.

Decisión: **equivalente**. La guarda explícita se queda: expresa la
intención sin depender de que una excepción caiga en el sitio adecuado,
que es lo que cualquiera espera leer.

### 3. `services/albaranes-front/infrastructure/database/review_repository.py:3780` [logico]

- Original: `if a is None or b is None:`
- Mutado:   `if a is None and b is None:`

#### Análisis — **mutante EQUIVALENTE**, justificado

Ya analizado y aceptado por el reviewer en la pasada anterior (era
entonces la línea 3737; solo ha cambiado de número al crecer el fichero).
Es **inalcanzable por construcción**: la línea inmediatamente anterior ya
devolvió `True` para el caso `(None, None)`, así que al llegar aquí la
condición mutada (`and`) es siempre falsa; la ejecución sigue al `try`,
donde `float(None)` lanza `TypeError` y el `except` devuelve `False` —
exactamente lo que devolvía la guarda original.

El reviewer lo verificó de forma independiente sobre 121 pares:
`mutante 3737: diferencias = 0`.

Decisión: **equivalente**. Se conserva la guarda por legibilidad.


---

## Nota sobre esta campaña (round trip 3, 2026-08-18)

Evolución de las tres pasadas sobre la misma feature:

| Pasada | Mutantes | Muertos | Supervivientes |
|---|---|---|---|
| Round trip 1 (solo sv5+sv6) | 4 | 4 | 0 |
| Round trip 2 (+ el fix de sv4) | 24 | 22 | 2 (equivalentes) |
| **Round trip 3 (+ `ruesma_comun`)** | **31** | **28** | **3 (equivalentes)** |

Los 7 mutantes nuevos salen de `ruesma_comun/importes.py`, la función que
este round trip extrajo para que sv4 y sv6 dejaran de tener cada uno su
copia: 6 mueren y el séptimo es el equivalente del borde del cero.

**Ninguno de los tres supervivientes es un hueco de test**: los tres son
diferencias inalcanzables o absorbidas por un `except` que ya existía, y
los tres quedan verificados ejecutando original y mutante, no razonando.
Nivel `critico`: cero supervivientes sin justificación.

La campaña se lanza con `--workers 1` porque la paralela crea worktrees
desde `HEAD` y se niega a correr mientras haya ficheros sin versionar en
el árbol; los que hay (`progress/revision_hormigones_20260818.md` y
`progress/revision_resto_lote_20260818.md`) son de otra sesión y ajenos a
esta feature. Además, el reviewer midió que lanzar suites completas en
paralelo con otra ejecución tumba `init.sh` en Windows por presión de
recursos (`git init` devolviendo `0xC0000142`), así que todo lo de este
round trip se ha ejecutado **en serie**.
