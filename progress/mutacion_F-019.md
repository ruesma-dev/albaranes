<!-- progress/mutacion_F-019.md -->
# F-019 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-019` el 2026-08-18 17:11.

## Alcance

Origen del diff: **rama** (`cd904cdcecee56311280ee54d81a7158d0529eb5` .. `feature/F-019-importe-unitario-manda`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py` | 64 |
| `services/albaran-valoracion-persist/application/services/price_reconciler.py` | 63 |
| `services/albaran-valoracion-persist/domain/models/valuation_envelope.py` | 17 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 184 |
| **Total** | **328** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 24 |
| Mutantes evaluados | 24 |
| Muertos | 22 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Tiempo total | 51.1 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-front/infrastructure/database/review_repository.py:115` [logico]

- Original: `if precio_unitario is None or cantidad is None:`
- Mutado:   `if precio_unitario is None and cantidad is None:`

#### Análisis — **mutante EQUIVALENTE**, justificado

Por qué ningún test lo caza: **porque no hay nada que cazar**. La guarda
es un atajo, no la única defensa. Con `and`, un solo `None` deja pasar la
línea siguiente —`float(precio_unitario) * float(cantidad)`—, que lanza
`TypeError` y cae en el `except (TypeError, ValueError): return None` de
las líneas 119-120. El valor devuelto es `None` en los dos casos, para
toda combinación de entradas.

Comprobado ejecutando las dos versiones sobre la tabla completa de
entradas relevantes —`(None, 10.0)`, `(2.5, None)`, `(None, None)`,
`(2.5, 4.0)`, `('x', 3.0)`, `(3.0, 'y')`, `(None, 'y')`,
`(object(), None)`—: **salida idéntica en las ocho**.

Decisión: **equivalente**. No se añade test (no existe entrada que los
distinga) y no se toca el código: la guarda explícita se queda porque
expresa la intención sin depender de una excepción, que es lo que
cualquiera espera leer.

### 2. `services/albaranes-front/infrastructure/database/review_repository.py:3737` [logico]

- Original: `if a is None or b is None:`
- Mutado:   `if a is None and b is None:`

#### Análisis — **mutante EQUIVALENTE**, justificado

Mismo mecanismo que el anterior, y además **inalcanzable por
construcción**: la línea inmediatamente anterior ya devolvió `True`
cuando `a` y `b` son ambos `None`, así que al llegar aquí la condición
mutada (`and`) es *siempre* falsa. La ejecución sigue al `try`, donde
`float(None)` lanza `TypeError` y el `except` devuelve `False` — que es
exactamente lo que devolvía la guarda original.

Comprobado ejecutando ambas versiones sobre `(None, None)`,
`(None, 1.0)`, `(1.0, None)`, `(1.0, 1.0)`, `(1.0, 2.0)`, `('x', 1.0)`,
`(1.0, 'x')` y `(None, 'x')`: **salida idéntica en las ocho**.

Decisión: **equivalente**. Se conserva la guarda por legibilidad: que
un `None` frente a un número no es «igual» debe leerse en el código, no
deducirse de que una excepción cae en el sitio adecuado.

---

## Nota sobre esta campaña (round trip 2, 2026-08-18)

La campaña anterior de F-019 generó **4 mutantes** porque el diff era
mínimo. Esta genera **24** sobre las mismas 328 líneas de alcance: el fix
de sv4 aporta lógica de verdad (la fórmula canónica, el saneado del
descuento y la decisión de si una fila cambia). De los 24, **22 mueren**;
los 2 supervivientes son equivalentes y quedan analizados arriba.

Dos de los cuatro supervivientes de la primera pasada **sí eran huecos
reales** y se cerraron con test (el aviso de descuento fuera de rango y
la frontera de medio céntimo de `_num_iguales`), no con una
justificación.

