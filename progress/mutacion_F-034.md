<!-- progress/mutacion_F-034.md -->
# F-034 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-034` el 2026-08-20 01:12.

> ## CÓMO SE REPRODUCE ESTA CAMPAÑA · no la lances con el CLI a secas
>
> `python -m harness.mutacion --feature F-034 --workers 1` **da un falso
> verde** en esta feature: 19 muertos, 0 supervivientes, 35,5 s. El alcance es
> `harness/mutacion.py`, que no es de ningún servicio, así que `ejecutor_para`
> lo juzga con `python -m pytest` **sin ruta**; como no hay configuración de
> pytest en la raíz, esa invocación recoge `services/**/tests` y **revienta en
> la recolección en 0,81 s** haga lo que haga el mutante (exit 1 = MUERTO).
> Está dado de alta como **F-038**; no se arregla en F-034.
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
> (Lánzalo con `PYTHONPATH=.`.) **Cuesta ~18 minutos de CPU** y muta
> `harness/mutacion.py` **en el árbol principal** todo ese rato: mientras corra,
> nadie puede lanzar `init.sh` ni una suite, porque mediría un mutante y no el
> código. En esta rama **no existe el centinela** que avisaría de ello (es de la
> 1.6.0, revertida). Comprobado al terminar: `git status` sin diff en
> `harness/mutacion.py`.
>
> Este aviso está escrito a mano: `escribir_informe` lo borrará si alguien
> regenera el fichero. Los análisis de los supervivientes, en cambio, sí los
> conserva (`clave_de_mutante`).

> ## LOS NÚMEROS ANTERIORES DE ESTE FICHERO ERAN FALSOS. Éstos están remedidos
>
> Hasta el 2026-08-20 este informe declaraba **18 muertos / 1 superviviente /
> 0 timeouts en 111,0 s**. El review de F-034, en su segunda pasada, reejecutó
> la campaña con el método de arriba y obtuvo **9 / 8 / 2 en 3.812 s**. Tenía
> razón él, por dos motivos que conviene no olvidar:
>
> 1. Un superviviente significa que la suite terminó **en verde** con el
>    mutante puesto. Una máquina cargada puede inventar *muertos* falsos;
>    *supervivientes* falsos, no: ningún test que fallaba pasa a aprobar por ir
>    lento.
> 2. Dos de los mutantes que este fichero daba por muertos son **semánticamente
>    idénticos al original** (`220 [comparacion]` y `221 [entero]`). Ningún test
>    puede matarlos, así que declararlos muertos era imposible. Se ve leyendo,
>    sin gastar CPU.
>
> **Causa probable**: bytecode rancio. CPython reutiliza el `.pyc` cuando el
> fuente conserva tamaño y `mtime` truncado a segundos, y dos mutantes
> consecutivos de una campaña en serie lo cumplen a menudo; el segundo se juzga
> con el bytecode del primero y sale «muerto» sin haber sido evaluado. El arnés
> **1.6.0** lo arregla, pero esta rama corre a propósito con el `mutacion.py`
> anterior: la propagación se revirtió (`163846b`) y se rehará tras el merge, en
> su rama `chore/`.
>
> **Qué se hizo con los 8 supervivientes** (detalle en `progress/impl_F-034.md`
> §T16): **cuatro eran huecos reales de test** y se han cerrado con tres tests
> nuevos en `tests/test_mutacion_operadores.py`, cada uno con su fase RED
> pegada; los **cuatro restantes son equivalentes**, comprobados uno a uno por
> barrido exhaustivo antes de firmarlos.
>
> **Coherencia interna de estos números** (la comprobación que el review
> propone como invariante): 1.063,1 s / 19 mutantes = **56 s por mutante**,
> contra una suite de la raíz que tarda ~50 s con `-x` y un timeout de 120 s
> para el único que se cuelga. Cuadra. Los 111,0 s del informe anterior daban
> 5,8 s por mutante contra esa misma suite: no cuadraba, y ahí estaba la pista.

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
| Muertos | 14 |
| Supervivientes | 4 |
| Timeouts | 1 |
| Tiempo total | 1063.1 s |
| Muestreo | no: campaña completa |

Salida completa de la campaña, mutante a mutante:

```
F-034: 1 fichero(s), 56 línea(s) de producción (origen rama, 28971321108528484c52c5c91108afc02af59084..feature/F-034-mutacion-is-y-coherencia-evals)
[1/19] muerto        harness/mutacion.py:207 [logico] and _PARTE_DE_PALABRA.match(objetivo[:1]) -> or _PARTE_DE_PALABRA.match(objetivo[:1])
[2/19] superviviente harness/mutacion.py:207 [entero] and _PARTE_DE_PALABRA.match(objetivo[:1]) -> and _PARTE_DE_PALABRA.match(objetivo[:2])
[3/19] muerto        harness/mutacion.py:208 [logico] and _PARTE_DE_PALABRA.match(objetivo[-1:]) -> or _PARTE_DE_PALABRA.match(objetivo[-1:])
[4/19] muerto        harness/mutacion.py:208 [entero] and _PARTE_DE_PALABRA.match(objetivo[-1:]) -> and _PARTE_DE_PALABRA.match(objetivo[-2:])
[5/19] muerto        harness/mutacion.py:220 [aritmetico] anterior = bruta[ini - 1 : ini] if ini > 0 else b"" -> anterior = bruta[ini + 1 : ini] if ini > 0 else b""
[6/19] muerto        harness/mutacion.py:220 [entero] anterior = bruta[ini - 1 : ini] if ini > 0 else b"" -> anterior = bruta[ini - 2 : ini] if ini > 0 else b""
[7/19] superviviente harness/mutacion.py:220 [comparacion] anterior = bruta[ini - 1 : ini] if ini > 0 else b"" -> anterior = bruta[ini - 1 : ini] if ini >= 0 else b""
[8/19] muerto        harness/mutacion.py:220 [entero] anterior = bruta[ini - 1 : ini] if ini > 0 else b"" -> anterior = bruta[ini - 1 : ini] if ini > 1 else b""
[9/19] muerto        harness/mutacion.py:221 [aritmetico] siguiente = bruta[fin : fin + 1] -> siguiente = bruta[fin : fin - 1]
[10/19] superviviente harness/mutacion.py:221 [entero] siguiente = bruta[fin : fin + 1] -> siguiente = bruta[fin : fin + 2]
[12/19] muerto        harness/mutacion.py:222 [logico] return not (_PARTE_DE_PALABRA.match(anterior) or _PARTE_DE_PALABRA.match(siguiente)) -> return not (_PARTE_DE_PALABRA.match(anterior) and _PARTE_DE_PALABRA.match(siguiente))
[13/19] muerto        harness/mutacion.py:246 [comparacion] while posicion != -1: -> while posicion == -1:
[14/19] muerto        harness/mutacion.py:246 [entero] while posicion != -1: -> while posicion != -2:
[15/19] muerto        harness/mutacion.py:247 [not] if not exigir_palabra or _delimitado( -> if exigir_palabra or _delimitado(
[16/19] muerto        harness/mutacion.py:247 [logico] if not exigir_palabra or _delimitado( -> if not exigir_palabra and _delimitado(
[17/19] muerto        harness/mutacion.py:248 [aritmetico] bruta, posicion, posicion + len(objetivo) -> bruta, posicion, posicion - len(objetivo)
[18/19] timeout       harness/mutacion.py:251 [aritmetico] posicion = bruta.find(objetivo, posicion + 1, hasta) -> posicion = bruta.find(objetivo, posicion - 1, hasta)
[19/19] superviviente harness/mutacion.py:251 [entero] posicion = bruta.find(objetivo, posicion + 1, hasta) -> posicion = bruta.find(objetivo, posicion + 2, hasta)
19 mutantes evaluados, 14 muertos, 4 supervivientes, 1 timeouts en 1063.1 s
Informe: progress/mutacion_F-034.md
```

**El `[11/19]` que falta en esa lista no se ha perdido: no llega a ejecutarse.**
Es `harness/mutacion.py:222 [not]`, que quita el `not` de una expresión entre
paréntesis y deja el paréntesis de cierre huérfano:

```
$ python -c "... compile(aplicar_mutante(fuente, mutantes[10])) ..."
mutante 11/19: harness/mutacion.py:222 [not] return not (_PARTE_DE_PALABRA.match(anterior) or _PARTE_DE_PALABRA.match(siguiente)) -> return _PARTE_DE_PALABRA.match(anterior) or _PARTE_DE_PALABRA.match(siguiente))
NO COMPILA -> SyntaxError unmatched ')' linea 222
```

`evaluar_mutantes` lo cuenta como **muerto** sin lanzar la suite (`compile`
falla ⇒ cualquier test lo cazaría) y hace `continue` **antes** del eco, así que
no sale por pantalla. Los totales sí lo incluyen: 14 muertos = 13 juzgados por
la suite + 1 que no compila. Observación para el arnés, fuera del alcance de
F-034: ese `continue` deja un hueco en el rastro, y el operador `not` sobre una
expresión entre paréntesis genera mutantes sintácticamente inválidos que no
miden nada.

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

**Los cuatro son equivalentes**, y no de palabra: comprobados uno a uno con un
barrido exhaustivo que compara la expresión sana con la mutada.

```
207 [entero]  objetivo[:1]->[:2]   : 0 diferencias sobre 16843008 tokens de 1..3 bytes
220 [comparacion] ini>0 -> ini>=0  : 0 diferencias sobre 21834 casos
    (bruta[-1:0] == b'' para toda bruta: la rama then con ini==0 da lo mismo que el else)
221 [entero]  fin+1 -> fin+2       : 0 diferencias sobre 21834 casos
251 [entero]  posicion+1 -> +2      : 0 diferencias sobre 391902 lineas x token
    control con un token inventado de bytes repetidos (b'aa'): 0 diferencias
    _PARTE_DE_PALABRA = b'[A-Za-z0-9_\x80-\xff]' (clase de UN carácter, y re.Pattern.match ancla al byte 0)
```

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
> Comprobado por fuerza bruta, no por analogía: **0 diferencias sobre los
> 16.843.008 tokens de 1 a 3 bytes** (todos los valores de byte posibles).
>
> **CORRECCIÓN (2026-08-20).** La versión anterior de este análisis se apoyaba
> además en esto, y era **falso**: «los otros 18 mutantes de esta misma función
> y de `_delimitado`/`_localizar` mueren todos, incluido el gemelo de la línea
> 208 (`objetivo[-1:]` → `objetivo[-2:]`), que sí lo caza `test_f034_r7`. La
> suite no tiene un hueco aquí». El gemelo de la 208 **sobrevivía** —lo midió el
> reviewer, `[4/19] superviviente`— y `test_f034_r7` no tenía nada que ver con
> él (R7 comprueba que `is  not` con espaciado no canónico no genera mutante, y
> no interroga ningún extremo de `_es_palabra`). Y la conclusión que colgaba de
> ahí era la contraria de la verdad: **el hueco existía, y eran cuatro**.
>
> Hoy, medido: el gemelo de la 208 **muere** (`[4/19] muerto`), y muere por el
> test nuevo `test_f034_r5_es_palabra_exige_que_LOS_DOS_extremos_sean_de_palabra`,
> con su fase RED pegada en `progress/impl_F-034.md` §T16. La conclusión sobre
> ESTE mutante se sostiene sola, por el argumento de arriba, sin apoyarse en
> ningún gemelo.
>
> **Decisión: mutante equivalente, no se escribe test.** Un test que lo matara
> tendría que depender de que `match` mire más de un byte, que es justo lo que
> no hace. Se deja `objetivo[:1]` y no `objetivo` a secas —que eliminaría el
> mutante por no tener literal entero— porque la rodaja **documenta la
> intención** («el primer byte») sin obligar al lector a recordar que `match`
> ancla. Reescribir código para complacer al mutador es cambiar la vara por el
> resultado.

### 2. `harness/mutacion.py:220` [comparacion]

- Original: `anterior = bruta[ini - 1 : ini] if ini > 0 else b""`
- Mutado:   `anterior = bruta[ini - 1 : ini] if ini >= 0 else b""`

#### Análisis — **mutante EQUIVALENTE**, justificado

> `ini` nunca es negativo: viene de `bruta.find(...)` dentro de un
> `while posicion != -1`, así que en la única llamada real `ini >= 0` es cierto
> siempre. Las dos condiciones solo pueden discrepar en `ini == 0`, y ahí la
> rama *then* del mutante evalúa `bruta[-1:0]`, que es **la cadena vacía para
> cualquier `bruta`** —el índice `-1` cae en el último byte y el corte va hacia
> atrás, luego no selecciona nada—: exactamente lo que devuelve el `else`. No
> hay entrada que las distinga.
>
> Comprobado por barrido: **0 diferencias sobre 21.834 casos** (todas las
> líneas de hasta 4 símbolos del alfabeto `{i, s, a, espacio, =, \xc3}` por
> todos los pares `(ini, fin)` válidos).
>
> **Decisión: mutante equivalente, no se escribe test.** Cualquier test que lo
> matara tendría que llamar a `_delimitado` con `ini` negativo, que es un
> estado que la función no puede recibir. El `> 0` se conserva porque **dice lo
> que quiere decir** («si hay un byte antes, míralo»); escribirlo `>= 0` sería
> apoyarse en una casualidad del corte negativo de Python.
>
> Nota: este mutante es uno de los dos que el informe anterior declaraba
> MUERTOS siendo imposible matarlos. Ver el aviso de cabecera.

### 3. `harness/mutacion.py:221` [entero]

- Original: `siguiente = bruta[fin : fin + 1]`
- Mutado:   `siguiente = bruta[fin : fin + 2]`

#### Análisis — **mutante EQUIVALENTE**, justificado

> Mismo argumento que el superviviente 1, en el otro extremo: `siguiente` solo
> se usa como `_PARTE_DE_PALABRA.match(siguiente)`, el patrón es una clase de
> **un solo carácter** y `match` **ancla al byte 0**. La rodaja de dos bytes
> interroga el mismo byte que la de uno; el segundo no se mira jamás.
>
> Comprobado por barrido: **0 diferencias sobre 21.834 casos**.
>
> **Decisión: mutante equivalente, no se escribe test.** Lo que sí faltaba
> —y era un hueco real— es comprobar que este byte **se mira**: lo cierra
> `221 [aritmetico]` (`fin + 1` → `fin - 1`), que hoy muere con los dos tests
> nuevos `test_f034_r5_bis_no_muta_una_palabra_que_EMPIEZA_por_is` y
> `test_f034_r5_delimitado_mira_los_dos_bytes_que_rodean_la_coincidencia`.
>
> Nota: este mutante es el otro de los dos que el informe anterior declaraba
> MUERTOS siendo imposible matarlos.

### 4. `harness/mutacion.py:251` [entero]

- Original: `posicion = bruta.find(objetivo, posicion + 1, hasta)`
- Mutado:   `posicion = bruta.find(objetivo, posicion + 2, hasta)`

#### Análisis — **mutante EQUIVALENTE**, justificado

> El review lo señaló como hueco real («la búsqueda se salta un byte»). Lo he
> analizado y **no lo es**: no falta un test, es que **no puede existir**, y se
> demuestra en tres pasos.
>
> 1. La línea 251 solo se ejecuta cuando `exigir_palabra` es cierto —si no, el
>    `if not exigir_palabra or ...` de la línea 247 ya ha devuelto en la primera
>    vuelta—, es decir cuando `_es_palabra(objetivo)` es cierto, es decir cuando
>    **`objetivo[0]` es un byte de palabra**.
> 2. `+1` y `+2` solo pueden diferir si hay una coincidencia **en
>    `posicion + 1`**, que es la única que el salto se come.
> 3. Esa coincidencia tendría en `bruta[posicion]` el byte `objetivo[0]` —de
>    palabra, por (1)—, así que `_delimitado(bruta, posicion + 1, ...)` leería
>    `anterior = bruta[posicion : posicion + 1]`, la daría por parte de una
>    palabra y **la rechazaría igualmente**.
>
> Saltársela no cambia nunca lo que devuelve `_localizar`: solo ahorra una
> vuelta del bucle. Comprobado además por fuerza bruta: **0 diferencias sobre
> 391.902 combinaciones** de línea × token, con los siete tokens de palabra de
> las tablas; y **0 diferencias** también con un token inventado de bytes
> repetidos (`b"aa"`), que es el único caso en el que dos coincidencias del
> mismo token pueden solaparse —justo el que la demostración predice que
> tampoco distingue—.
>
> **Decisión: mutante equivalente, no se escribe test.** Fase RED intentada y
> pegada en `progress/impl_F-034.md` §T16 (RED 5): con la mutación puesta, los
> 12 tests del fichero **pasan**, que es lo que la demostración anticipaba.

## Timeouts

- `harness/mutacion.py:251` `[aritmetico]` `posicion = bruta.find(objetivo, posicion + 1, hasta)` → `posicion = bruta.find(objetivo, posicion - 1, hasta)`

### Análisis del timeout — **bucle infinito del mutante**, no fallo de la herramienta

> Con `posicion - 1`, `find` vuelve a encontrar la **misma** `posicion` que
> acaba de rechazarse, que se vuelve a rechazar, para siempre. El bucle
> `while posicion != -1` no termina nunca en cuanto una coincidencia no está
> delimitada, y eso pasa en el primer test que use `FUENTE_COMENTARIO`.
>
> Medido, no supuesto (mutación aplicada + la misma suite que juzga la campaña,
> con tope de 200 s):
>
> ```
> MUTANTE mutacion.py:251  posicion = bruta.find(objetivo, posicion + 1, hasta)  ->  posicion = bruta.find(objetivo, posicion - 1, hasta)
> ........................................................................ [ 25%]
> ........................................................................ [ 51%]
> ........................................................................ [ 77%]
> ........................................................exit=124  segundos=200  (124 = cortado por timeout)
> ```
>
> **El timeout es el único veredicto posible**: un mutante que cuelga la suite
> no se puede declarar ni muerto ni superviviente. No exige test ni corrección.
>
> El **otro** timeout que vio el reviewer (`207 [logico]`) **no era esto**: en
> esta campaña **muere** (`[1/19] muerto`), y medido aparte tarda 48,28 s en
> caer. Aquel timeout fue la máquina cargada (63 min para 19 mutantes = ~200 s
> de media contra una suite de ~50 s y un tope de 120 s por mutante), no el
> mutante. Detalle en `progress/impl_F-034.md` §T16.
