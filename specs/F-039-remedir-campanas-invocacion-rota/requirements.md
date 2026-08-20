<!-- specs/F-039-remedir-campanas-invocacion-rota/requirements.md -->
# F-039 · Requisitos

Estabilizar la suite de la raíz y **medir de verdad la maquinaria de mutación**,
después de que F-038 arreglara la invocación de `ejecutor_para` que dejó sin
valor las campañas de los ficheros de fuera de `services/`.

**Fuera de alcance por decisión previa**: el test inestable de la suite de la
raíz —cerrado por F-038 T17—, la remedición de `mutacion_F-011.md` —invalidada
para siempre— y `mutacion_F-034.md`, ya remedido a mano.

## Bloque A · Inventario de campañas afectadas

**R1.** El sistema debe publicar `progress/inventario_mutacion_F-039.md` con
una fila por cada `progress/mutacion_*.md` existente, y en cada fila: si su
alcance incluye ficheros fuera de `services/`, y su veredicto —`VÁLIDA`,
`INVÁLIDA (no se repone)`, `REMEDIDA`, `INVALIDADA PARA SIEMPRE`, `MANUAL` o
`SIN SUJETO`—.

**R2.** SI aparece un informe `progress/mutacion_*.md` que no figura en el
inventario, ENTONCES la suite debe fallar (el inventario no puede quedarse
atrás cuando se añada una campaña).

## Bloque B · La deuda heredada: el filtro de filas de reloj

**R3.** `harness/mutacion.py` debe exponer, junto a `escribir_informe`, la
constante `FILAS_DE_RELOJ` con los prefijos de las filas del informe cuyo valor
depende del reloj, y la función `lineas_comparables(texto: str) -> list[str]`
que las descarta.

**R4.** CUANDO se escriben dos informes que solo difieren en sus tiempos
(`segundos`, `segundos_linea_base` y la media derivada), `lineas_comparables`
debe devolver dos listas **iguales**.

**R5.** SI alguien añade al informe una fila nueva cuyo valor depende del reloj
y no la declara en `FILAS_DE_RELOJ`, ENTONCES el test de R4 debe fallar. Es el
requisito que impide repetir el flake de F-038 T5.

**R6.** CUANDO dos informes difieren en algo que **no** es reloj —alcance,
totales, SHA, muestreo, fichas de supervivientes—, `lineas_comparables` debe
seguir mostrando esa diferencia.

**R7.** El test
`test_f012_r1_r4_el_informe_paralelo_es_identico_al_de_la_campania_en_serie`
debe comparar con `lineas_comparables`, sin lista de prefijos propia.

## Bloque C · Verificar que la campaña paralela arranca

**R8.** MIENTRAS no esté verificada la campaña paralela (R9), el sistema no
debe lanzar la campaña del bloque D: medir con la maquinaria sin verificar es
medir dos veces mal.

**R9.** CUANDO se ejecuta, en sesión dedicada y sin otra suite en marcha,
`python -m harness.mutacion --feature F-038 --workers 5 --max-mutantes 1
--salida <ruta fuera de progress/>`, la campaña debe superar su **línea base**
en los cinco worktrees sin abortar con `LÍNEA BASE EN ROJO` y llegar a evaluar
el mutante. Verificación **MANUAL (humano)**.

**R10.** SI el proceso muere por `0xC0000142` (la máquina no soporta cinco
suites simultáneas), ENTONCES se repite con N descendente (5 → 3 → 2) y se
declara por escrito el mayor N con línea base verde; eso cierra R9 como
**límite de la máquina**, no como fallo del paralelo.

**R11.** SI la línea base sale en rojo por una causa distinta del reloj ya
arreglado, ENTONCES esa causa **sí** es trabajo de esta feature: se diagnostica
por escrito antes de seguir, y si el arreglo excede el arnés se marca `blocked`.

**R12.** CUANDO termine la verificación, el árbol principal debe quedar limpio
(`git status --porcelain` vacío) y sin worktrees registrados.

## Bloque D · Campaña nueva sobre la maquinaria de mutación de HOY

**R13.** El sistema debe medir una **campaña nueva sobre la maquinaria de
mutación tal como es hoy**, sobre `HEAD` de la rama de esta feature. **No es la
campaña de F-012 repetida** y no repone sus números: aquella medía el código de
agosto, y lo que interesa es si está protegido el código que corre HOY.

**R14.** El alcance deben ser `harness/mutacion.py`,
`harness/mutacion_paralela.py` y `harness/rigor.py` **enteros, en su versión
actual** —los tres ficheros del alcance original de F-012, con el código de
hoy—, muestreados por el nivel `estandar`: 20 mutantes con semilla `20260820`,
que es lo que hace asequible mutar un `mutacion.py` de ~1.900 líneas.

**R15.** CUANDO se invoque `python -m harness.mutacion --ficheros
RUTA[,RUTA...]`, el sistema debe sustituir el cálculo del alcance por esos
ficheros **enteros** del árbol de trabajo, y el informe debe declarar
`Origen del diff: **ficheros** (alcance declarado en la orden)`.

**R16.** SI `--ficheros` recibe una ruta inexistente o que no es código de
producción según `harness.alcance.es_produccion`, ENTONCES debe abortar con
mensaje explícito y sin mutar nada.

**R17.** El resultado debe escribirse en
`progress/mutacion_maquinaria_paralela_F-039.md` —nunca encima de un informe
existente—, con los tres datos que exigen RM1/RM2 de `CHECKPOINTS.md`: **SHA de
HEAD medido**, **línea base** y **media por mutante evaluado**.

**R18.** El informe debe llevar cabecera escrita a mano con el **comando
exacto** que lo reproduce y esta advertencia: mide **otro código** que
`mutacion_F-012.md`, así que ni lo repone ni es comparable con él.

**R19.** CUANDO la campaña produzca supervivientes, cada uno debe tener su
sección de análisis **completada** (ninguna en `PENDIENTE`): test que falta o
justificación de equivalencia. Si son muchos, se agrupan por causa y cada ficha
remite a su grupo; ninguna queda vacía.

**R20.** Los supervivientes **no se cierran en esta feature** y **no se abre
ficha automáticamente**: se presenta al humano la lista agrupada por causa y
decide él si se abre, con qué prioridad y qué entra.

**R21.** SI un superviviente revela un defecto real de comportamiento —y no un
hueco de test—, ENTONCES se para, se anota en `progress/current.md` y se avisa
al humano antes de tocar nada.

**R22.** SI la línea base de la suite de la raíz sale en rojo en el árbol de
hoy, ENTONCES la campaña **no se lanza**: se arregla la suite (objeto del
bloque B/C) o la feature se marca `blocked`. Sobre base roja, el cero de
supervivientes es falso.

## Bloque E · Cabeceras de invalidez

**R23.** El aviso `⚠ CAMPAÑA NO VÁLIDA` de `progress/mutacion_F-012.md`
**no se retira nunca**: sus números son inválidos y **ya no se van a reponer**.
El puntero que se le añade debe decir que
`mutacion_maquinaria_paralela_F-039.md` mide **otro código** —la maquinaria de
hoy—, no la misma campaña rehecha.

**R24.** El aviso de `progress/mutacion_F-011.md` debe conservarse y
actualizarse con la decisión del humano del 2026-08-20 —invalidada para
siempre, sin ficha— y su consecuencia: la puerta de evals de F-011 no tiene
detrás ninguna medición de mutación válida.

**R25.** No debe modificarse `progress/mutacion_F-034.md`: ya está remedido a
mano y lo dice su cabecera.

**R26.** CUANDO se cierre la feature, `bash harness/init.sh` debe terminar en
verde, topes de tamaño incluidos.

## Decisiones del humano (2026-08-20)

1. **No se mide el árbol de la rama F-012** (R13/R14): eso diría qué habría
   salido en agosto; los huecos que encontrase pueden ya no existir y los de
   hoy no aparecerían. Se mide el código que corre hoy.
2. **R9 se cierra con el mayor N verde**, documentado (R10). Si 5 no entra, es
   límite de la máquina, no fallo del paralelo.
3. **No se declara `mutacion.workers` en `harness/rigor.json`**: sin declarar,
   el default se calcula por máquina y por eso viaja bien a los cinco
   proyectos. Para bajarlo puntualmente está `--workers`.
4. **La ficha de huecos de test no se abre automáticamente** (R20): la lista
   agrupada se presenta y el humano decide.
