<!-- specs/F-040-campana-dimensionada-y-honesta/design.md -->
# F-040 · Diseño técnico

## 0. Verificado antes de diseñar (dos premisas de la ficha no se sostienen)

La feature va de no mentir sobre lo medido, así que se empieza por casa. Dos
afirmaciones de la ficha se comprobaron leyendo y ejecutando el código:

- **`## Timeouts` NO lanza `TypeError`.** Se escribió un informe con un timeout
  y salió `- \`a.py:3\` a.py:3 [op] x -> y`: el camino funciona, pero **duplica**
  `fichero:linea` porque `Mutante.descripcion()` ya lo incluye. El hueco es real
  (nadie lo prueba) pero el defecto es cosmético, no una excepción → R20.
- **`timeout_mutacion` SÍ rechaza enteros `<= 0`** (`harness/rigor.py:110`,
  `not isinstance(valor, int) or valor <= 0`, desde la instalación del arnés).
  Lo que se cuela es un **booleano**: `isinstance(True, int)` es cierto y
  `True > 0`, así que `"timeout_por_mutante_s": true` da **1 s** y toda la
  campaña sale «timeout». Y el mensaje dice «Falta la clave» cuando el valor
  está pero no vale. Además `--timeout -5` entra sin validar ninguna. Eso es lo
  que se arregla en R22/R23.

Tampoco es cierto que `CHECKPOINTS.md` reconozca el factor de workers al juzgar
el coste por mutante: no aparece «worker» ni «paralel» ni en `CHECKPOINTS.md`
ni en `.claude/agents/reviewer.md`. De ahí sale R27.

## 1. La decisión de D1: el timeout se deriva de la línea base ya medida

Tres opciones sobre la mesa:

| Opción | Por qué no / por qué sí |
|---|---|
| `timeout × workers` | **Descartada.** El dato de campo lo desmiente: ~51 s en reposo, 97,5 s con 1 worker, 119-122 s con 3. De 1 a 3 workers el tiempo crece un 25 %, no un 300 %. Multiplicar por los workers concedería ~360 s donde bastan ~240 y taparía suites que de verdad se han desmadrado. |
| Medir la suite **una vez** aparte y dimensionar | **Descartada.** Cuesta una suite entera de más (~51 s) antes de cada campaña, y esa medición sería en reposo: no ve la contención de los W workers, que es justo lo que hay que medir. |
| **Derivar de la línea base que ya se corre** | **Elegida.** `comprobar_linea_base` ya ejecuta la suite limpia **dentro de cada worktree, con los W workers compitiendo**, y ya devuelve los segundos (`tiempos`, R11 de F-012). La medición correcta ya está hecha y hoy se tira: usarla no cuesta ni un segundo extra y absorbe máquina, workers y tamaño de suite sin ninguna fórmula que adivine. |

Fórmula: `timeout_efectivo = max(suelo, ceil(peor_base_s × MARGEN))`, con
`MARGEN = 2.0` y `peor_base_s = max(tiempos.values())`. El suelo es
`mutacion.timeout_por_mutante_s` (120 s, sin tocar): un mutante nunca recibe
menos que hoy. Con la medición de campo: `max(120, ceil(121,6 × 2)) = 244 s`.

**Huevo y gallina**: la línea base necesita un timeout para poder correr. Se le
concede el suyo, holgado y aparte: `timeout_base = suelo × FACTOR_HOLGURA_BASE`
con `FACTOR_HOLGURA_BASE = 5` → 600 s. Es defendible porque se paga **una vez
por worker**, no una por mutante: ser generoso ahí tiene coste acotado, y si ni
con 10 minutos cabe la suite limpia, el problema es la suite (mensaje de R5).

Ningún número de esta máquina entra en `rigor.json`: cambia el **mecanismo**
(medir y derivar), no un valor. Se respeta la decisión del 2026-08-20; si el
humano quiere revisarla, está como pregunta abierta 2, no como cambio.

## 2. La decisión de D2: `min(max(1, (núcleos - 2) // 2), 4)`

Hoy: `min(max(1, núcleos - 2), 16)` → **16** en 22 núcleos. Supone que el cuello
es la CPU. No lo es: cada worker arranca un **proceso pytest completo**
—intérprete, importaciones, recolección, E/S de disco— y en este monorepo, un
venv por servicio. El recurso escaso es la máquina entera, no el núcleo.

Argumento del nuevo, sin apelar a «va bien aquí»:

- **`// 2`**: se reserva del orden de dos núcleos por suite (pytest no es
  monohilo: importa, compila, escribe caché) además de los dos que ya se dejaban
  para la máquina y el coordinador. En 4 núcleos da 1; en 8 da 3; en 22 da 4.
- **Tope 4**: el único punto con medición real y verde es **3** workers, y ya
  ahí el tiempo de suite ha subido un 25 %. Por encima nadie ha medido; el arnés
  viaja a cinco proyectos y a máquinas más pequeñas, donde un tope alto no es
  optimista sino directamente dañino. 4 es un paso sobre lo medido, no un salto.
- Subir el tope es una decisión **con datos**, y `--workers N` sigue sin límite
  para quien quiera producirlos (R10).

D1 hace este tope seguro por otra vía: con el timeout derivado de lo medido, un
número alto de workers ya no produce el falso «todo expiró»; produce una campaña
lenta que **el informe declara** (R4).

## 3. La decisión de D4: la guarda en el embudo, no en cada puerta

Van tres veces el mismo modo de fallo por tres puertas distintas (F-038 T0,
F-039 CR-2, y ahora `--feature`). Poner una cuarta guarda en `alcance_de_feature`
sería tapar la tercera puerta y esperar a la cuarta.

`alcance.py` seguirá con su guarda de **entrada** (CR-2): es la que sabe *qué*
ruta sobra y lo dice (R17). Lo que falta es la guarda de **salida**, y el único
punto por el que pasan todas las vías —presentes y futuras— es `main`, que es
además quien escribe el informe y elige el código. Ahí va, una sola vez:

- Tras resolver el alcance y **antes** de arrancar líneas base o worktrees: si
  `not alcance.lineas` → aborta (R16). Hoy imprime «Sin líneas de producción» y
  **sigue**; eso es lo que produce el informe de cero.
- Tras la campaña y **antes** de `escribir_informe`: si `informe.generados == 0`
  → aborta (R14). Red final para el caso «hay líneas pero nada mutable».

Código **3**, el que ya significa «no se ha medido nada» frente al 1 de «hay
supervivientes». Mismo criterio que `CampaniaAbortada`, sin mecanismo nuevo.

## 4. Ficheros

### Se modifican

- **`harness/mutacion.py`**
  - `TOPE_WORKERS`: 16 → **4**; docstring nuevo con el argumento de recurso.
  - `workers_por_defecto()`: `min(max(1, (os.cpu_count() or 1) - 2) // 2, ...)`
    → cuidado con el orden: `max(1, (núcleos - 2) // 2)`.
  - **Nuevas** constantes `MARGEN_TIMEOUT = 2.0` y `FACTOR_HOLGURA_BASE = 5`.
  - **Nueva** función pura `timeout_derivado(suelo: int, tiempos_base:
    dict[str, float], margen: float = MARGEN_TIMEOUT) -> int` — sede única de la
    fórmula de R1; con `tiempos_base` vacío devuelve el suelo.
  - **Nueva** función pura `timeout_de_linea_base(suelo: int) -> int` (R2).
  - `ejecutar_campania(...)`: acepta `timeout_base_s` y, tras
    `comprobar_linea_base`, recalcula el timeout por mutante con
    `timeout_derivado` salvo que llegue `timeout_fijado=True` (R6). Registra
    `informe.timeout_efectivo`, `informe.timeout_suelo`, `informe.workers`.
  - `_base_rota_al_final(...)`: distingue `resultado.expirado` de `not verde`,
    con dos mensajes (R11/R12), igual que hace ya `comprobar_linea_base`.
  - `escribir_informe(...)`: filas nuevas en la tabla (R4) y línea de `##
    Timeouts` sin el prefijo duplicado (R20).
  - `_analizar_argumentos(...)`: `--timeout` validado (>0) → `SystemExit(2)`
    (R23); se valida igual `--workers` (>=1) por ser la misma guarda.
  - `main(...)`: guardas de D4 (R14/R16), aborto si `_modo_restaurar` devuelve
    distinto de 0 (R18), y traslado del timeout base a la campaña.
- **`harness/mutacion_paralela.py`**: `ejecutar_campania_paralela` propaga
  `timeout_base_s` y `timeout_fijado` a cada `ejecutar_campania`, y `fusionar`
  toma el timeout efectivo **máximo** de los parciales (el peor worker manda).
- **`harness/rigor.py`**: `timeout_mutacion` rechaza `bool` explícitamente (como
  ya hace `workers_mutacion`) y separa el mensaje «falta» de «no vale» (R22).
- **`harness/rigor.json`**: `$doc` de `mutacion` reescrito — el timeout es
  **suelo**, el efectivo se deriva de la línea base, y el default de workers
  pasa a ser `min(max(1, (núcleos-2)//2), 4)`. **La clave `workers` sigue sin
  declararse** (R9).
- **`CHECKPOINTS.md`**: nota en RM2 sobre `mutantes × media / W` (R27) y
  mención de que el informe declara workers y timeout efectivo.

### Se crean (tests, `tests/`)

- `tests/test_f040_r1_r10_dimensionado.py` — R1..R10 con dobles: sin suite real.
- `tests/test_f040_r11_r17_honestidad.py` — R11..R17 (D3 y D4).
- `tests/test_f040_r18_r26_huecos.py` — R18..R26 (los ocho de D5).

### NO se tocan

- `harness/alcance.py` — salvo lectura. Su guarda de CR-2 se queda como está
  (R17); D4 se resuelve fuera, en el embudo. **Tentación explícita: no añadir
  una guarda gemela en `alcance_de_feature`.**
- `harness/init.sh`, `harness/tamano.py`, `harness/backlog.py`, `.claude/agents/`.
- El superviviente `mutacion.py:1348` (equivalente, aceptado en F-039).
- Todo `services/` — esta feature es solo arnés.

## 5. Riesgos y decisiones

- **El quinto defecto.** Cada vez que se ha mirado dentro de esta maquinaria ha
  salido uno nuevo (van cuatro en dos días, más las dos premisas corregidas en
  la sección 0). **Si al implementar aparece un quinto: se anota en
  `progress/impl_F-040.md` con su evidencia y se PROPONE al humano. No entra en
  esta feature sin preguntar.** Ampliar el alcance sobre la marcha es lo que
  convierte una feature acotada en una que no cierra nunca.
- **Cambio de semántica del timeout.** Los tiempos de campañas anteriores dejan
  de ser comparables: antes 120 s fijos, ahora un derivado (~244 s medidos aquí).
  Va escrito en el informe (R4) para que el reviewer no compare peras con
  manzanas.
- **Riesgo de la fórmula**: una suite con un test lento y variable podría dar un
  `peor_base_s` alto y conceder timeouts generosos, dejando pasar mutantes que
  cuelgan. Mitigación: el margen es 2, no 10, y el informe declara ambos números.
- **Descartado**: declarar `mutacion.workers` en `rigor.json` con un valor bajo.
  Resolvería el síntoma en esta máquina y cablearía el límite de esta máquina en
  un arnés que viaja a cinco proyectos. Contradice la decisión del 2026-08-20.
- **Descartado**: dejar el timeout fijo y limitarse a subir el suelo a 300 s.
  Es el mismo defecto un poco más tarde: en una máquina más lenta o con más
  workers vuelve a quedarse corto y nadie se entera hasta que expira la campaña.

## 6. Fuera de alcance y trabajo posterior

- **El porte a `arnes-base` 1.7.2 va DESPUÉS del merge en `dev`, nunca dentro de
  esta rama.** En F-034 hacerlo dentro costó un rechazo entero. Es tarea del
  líder tras el merge, y la entrada de `GUIA_INSTALACION.md` debe avisar de que
  **los tiempos de campañas paralelas anteriores dejan de ser comparables**
  (timeout derivado y tope de workers 16 → 4).
- Ninguna tarea de esta feature ejecuta campañas largas ni suites completas: los
  tests usan dobles y ejecutores falsos. La campaña de mutación de cierre la
  lanza el implementer al final, como en cualquier feature de nivel `estandar`.
