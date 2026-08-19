<!-- progress/mutacion_F-034.md -->
# F-034 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-034` el 2026-08-19 14:48.

> ## AVISO AL REVIEWER · no reproduzcas esto con el CLI a secas
>
> `python -m harness.mutacion --feature F-034 --workers 1` **da un falso
> verde** en esta feature: 19 muertos, 0 supervivientes, 35,5 s. El alcance es
> `harness/mutacion.py`, que no es de ningún servicio, así que `ejecutor_para`
> lo juzga con `python -m pytest` **sin ruta**; como no hay configuración de
> pytest en la raíz, esa invocación recoge `services/**/tests` y **revienta en
> la recolección en 0,81 s** haga lo que haga el mutante (exit 1 = MUERTO).
>
> Los números de abajo salen de juzgar con la suite de la raíz de verdad:
>
> ```python
> from harness.mutacion import EjecutorPytest, main
> main(["--feature", "F-034", "--workers", "1",
>       "--salida", "progress/mutacion_F-034.md"],
>      ejecutor=EjecutorPytest(
>          raiz=".",
>          argumentos=["tests", "-x", "-q", "--tb=no", "-p", "no:cacheprovider"]))
> ```
>
> (Lánzalo con `PYTHONPATH=.`.) Este aviso está escrito a mano: `escribir_informe`
> lo borrará si alguien regenera el fichero. Contexto en `progress/impl_F-034.md` §T11.

> ## POR QUÉ ESTE INFORME SIGUE SIENDO VÁLIDO, aunque el historial parezca decir lo contrario
>
> Si miras el `git log` de esta rama vas a encontrar un tramo en el que los
> números de abajo **no cuadraban** con el árbol. Pasó esto, y está resuelto:
>
> 1. La campaña se midió sobre el alcance real de F-034: **1 fichero, 56
>    líneas, 19 mutantes**.
> 2. Después, el commit `e97f9b9` propagó la **1.6.0 de `arnes-base`** a este
>    repositorio **dentro de esta misma rama**. Eso metió ~1.000 líneas de
>    producción ajenas a F-034 en el alcance de la feature: pasaba a **1.057
>    líneas y 172 mutantes**, y la cobertura de líneas cambiadas de 12 a 392.
>    El review de F-034 lo rechazó, con razón (CR-1 y CR-2).
> 3. **Ese commit se ha revertido** (`163846b`). La propagación se rehará tras
>    el merge de F-034, en su propia rama `chore/`.
>
> Recomprobado tras el revert, cálculo puro sin ejecutar ninguna suite
> (`harness.alcance.alcance_de_feature` + `harness.mutacion.generar_mutantes`):
>
> ```
> harness/mutacion.py: 56 lineas, 19 mutantes
> TOTAL: 1 fichero(s), 56 lineas, 19 mutantes
> ```
>
> **Coincide exactamente con la sección «Alcance» y con los «Totales» de abajo.**
>
> Y el método del aviso anterior **vuelve a reproducirse**: el revert repone el
> `harness/mutacion.py` sin comprobación de línea base (esa comprobación es de
> la 1.6.0), así que ya no aborta. Muestra de 3 mutantes con `--max-mutantes 3
> --semilla 7`:
>
> ```
> F-034: 1 fichero(s), 56 línea(s) de producción (origen rama, 28971321108528484c52c5c91108afc02af59084..feature/F-034-mutacion-is-y-coherencia-evals)
> [1/3] muerto        harness/mutacion.py:220 [aritmetico] anterior = bruta[ini - 1 : ini] if ini > 0 else b"" -> anterior = bruta[ini + 1 : ini] if ini > 0 else b""
> [3/3] muerto        harness/mutacion.py:246 [comparacion] while posicion != -1: -> while posicion == -1:
> 3 mutantes evaluados, 3 muertos, 0 supervivientes, 0 timeouts en 82.7 s
> ```
>
> Detalle completo en `progress/impl_F-034.md` §T15.
>
> **Aviso para quien vuelva aquí después del merge de la rama `chore/` de
> propagación**: a partir de ese momento el `harness/mutacion.py` de este
> repositorio **sí** comprobará la línea base, y el método de arriba **volverá a
> abortar** hasta que F-038 arregle el ejecutor de la raíz. Eso no invalidará
> estos números —se midieron sobre el árbol que el review aprobó—, pero sí hará
> falta el arreglo de F-038 para repetirlos.


## Alcance

Origen del diff: **rama** (`28971321108528484c52c5c91108afc02af59084` .. `feature/F-034-mutacion-is-y-coherencia-evals`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 56 |
| **Total** | **56** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 19 |
| Mutantes evaluados | 19 |
| Muertos | 18 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Tiempo total | 111.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/mutacion.py:207` [entero]

- Original: `and _PARTE_DE_PALABRA.match(objetivo[:1])`
- Mutado:   `and _PARTE_DE_PALABRA.match(objetivo[:2])`

#### Análisis — **mutante EQUIVALENTE**, justificado

> **Por qué ningún test lo caza: porque no puede.** `_PARTE_DE_PALABRA` es
> `re.compile(rb"[A-Za-z0-9_\x80-\xff]")`, **una sola clase de carácter**, y
> `Pattern.match` está **anclado al principio** de lo que recibe. Así que
> `match(objetivo[:1])` y `match(objetivo[:2])` interrogan **exactamente el
> mismo byte**: el 0. El segundo byte que el mutante añade a la rodaja nunca se
> mira. Para cualquier `objetivo` no vacío las dos expresiones tienen la misma
> verdad, y `objetivo` vacío ni llega aquí (`_es_palabra` corta antes con
> `objetivo and ...`, y `_localizar` ya ha vuelto `None`).
>
> Comprobado además con el resto de la campaña: los otros **18 mutantes de esta
> misma función y de `_delimitado`/`_localizar` mueren todos**, incluido el
> gemelo de la línea 208 (`objetivo[-1:]` → `objetivo[-2:]`), que **sí** cambia
> el byte interrogado y **sí** lo caza `test_f034_r7`. La suite no tiene un
> hueco aquí: es esta mutación la que no significa nada.
>
> **Decisión: mutante equivalente, no se escribe test.** Un test que lo matara
> tendría que depender de que `match` mire más de un byte, que es justo lo que
> no hace. Se deja `objetivo[:1]` y no `objetivo` a secas —que eliminaría el
> mutante por no tener literal entero— porque la rodaja **documenta la
> intención** («el primer byte») sin obligar al lector a recordar que `match`
> ancla. Reescribir código para complacer al mutador es cambiar la vara por el
> resultado.

