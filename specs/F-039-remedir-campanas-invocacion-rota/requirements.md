<!-- specs/F-039-remedir-campanas-invocacion-rota/requirements.md -->
# F-039 · Requisitos

Remedir las campañas de mutación que se juzgaron con la invocación rota de
`ejecutor_para` (arreglada en F-038), después de verificar que la campaña
paralela arranca en esta máquina.

**Fuera de alcance por decisión previa** (no se replantea aquí): el test
inestable de la suite de la raíz —cerrado por F-038 T17—, la remedición de
`progress/mutacion_F-011.md` —invalidada para siempre, decisión del humano del
2026-08-20— y `progress/mutacion_F-034.md`, ya remedido a mano.

## Bloque A · Inventario de campañas afectadas

**R1.** El sistema debe publicar `progress/inventario_mutacion_F-039.md` con
una fila por cada `progress/mutacion_*.md` existente, y en cada fila: si su
alcance incluye ficheros fuera de `services/`, y su veredicto —`VÁLIDA`,
`INVÁLIDA (pendiente)`, `REMEDIDA`, `INVALIDADA PARA SIEMPRE`, `MANUAL` o `SIN
SUJETO`—.

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
debe comparar con `lineas_comparables`, sin su lista de prefijos escrita a
mano.

## Bloque C · Verificar que la campaña paralela arranca

**R8.** MIENTRAS no esté verificada la campaña paralela (R9), el sistema no
debe lanzar ninguna remedición: remedir con la maquinaria sin verificar es
medir dos veces mal.

**R9.** CUANDO se ejecuta, en sesión dedicada y sin ninguna otra suite en
marcha, `python -m harness.mutacion --feature F-038 --workers 5
--max-mutantes 1 --salida <ruta fuera de progress/>`, la campaña debe superar
su **línea base** en los cinco worktrees sin abortar con `LÍNEA BASE EN ROJO` y
llegar a evaluar el mutante. Verificación **MANUAL (humano)**.

**R10.** SI el proceso muere por `0xC0000142` (la máquina no soporta cinco
suites simultáneas), ENTONCES se repite con N descendente (5 → 3 → 2) y se
declara por escrito el mayor N con línea base verde; ese resultado cierra R9
como *límite de la máquina*, no como fallo del paralelo.

**R11.** SI la línea base sale en rojo por una causa distinta del reloj ya
arreglado, ENTONCES esa causa **sí** es trabajo de esta feature: se diagnostica
por escrito antes de seguir, y si el arreglo excede el arnés se marca la
feature `blocked`.

**R12.** CUANDO termine la verificación, el árbol principal debe quedar limpio
(`git status --porcelain` vacío) y sin worktrees registrados
(`git worktree list` con una sola línea).

## Bloque D · Remedir la campaña de F-012

**R13.** La remedición de F-012 debe medirse sobre el **árbol de la rama
`feature/F-012-mutacion-paralela`**, en un worktree desechable pasado por
`--raiz`, ejecutando el arnés de HOY. El alcance original apunta a números de
línea de aquella versión de los ficheros: `harness/mutacion.py` ha crecido
+1.346 líneas desde entonces, así que aplicarlo al árbol de hoy mutaría líneas
que no tienen nada que ver.

**R14.** El sistema debe escribir el resultado en
`progress/mutacion_F-012_remedida.md` —nunca encima de `mutacion_F-012.md`—,
con los tres datos que exige RM1/RM2 de `CHECKPOINTS.md`: **SHA de HEAD
medido**, **línea base** y **media por mutante evaluado**.

**R15.** El informe remedido debe llevar una cabecera escrita a mano con el
**comando exacto** que lo reproduce (worktree incluido) y con la advertencia de
que sus números no son comparables con los de la campaña invalidada.

**R16.** CUANDO la remedición produzca supervivientes, cada uno debe tener su
sección de análisis **completada** (ninguna en `PENDIENTE`): test que falta, o
justificación de equivalencia. Si son muchos, se agrupan por causa y cada ficha
remite a su grupo, pero ninguna queda vacía.

**R17.** Los supervivientes que revelen huecos de test **no se cierran en esta
feature**: se propone **UNA** ficha nueva con la lista agrupada. Una feature no
puede comprometerse a cerrar N huecos que aún no conoce.

**R18.** SI un superviviente revela un defecto real de comportamiento —y no un
hueco de test—, ENTONCES se para, se anota en `progress/current.md` y se avisa
al humano antes de tocar nada.

**R19.** SI la línea base del worktree de F-012 sale en rojo (deriva de
dependencias desde agosto), ENTONCES no se improvisa un alcance alternativo: se
marca `blocked` con el diagnóstico y se consulta al humano.

## Bloque E · Cabeceras de invalidez

**R20.** El aviso `⚠ CAMPAÑA NO VÁLIDA` de `progress/mutacion_F-012.md`
**no se retira**: sus números siguen siendo los inválidos. Se le añade el
puntero a `mutacion_F-012_remedida.md` como sitio donde viven los válidos.

**R21.** El aviso de `progress/mutacion_F-011.md` debe conservarse y
actualizarse con la decisión del humano del 2026-08-20 —invalidada para
siempre, sin ficha de remedición— y con su consecuencia: la puerta de evals de
F-011 no tiene detrás ninguna medición de mutación válida.

**R22.** El sistema no debe modificar `progress/mutacion_F-034.md`: ya está
remedido a mano y lo dice su cabecera.

**R23.** CUANDO `bash harness/init.sh` se ejecute al cerrar la feature, debe
terminar en verde, incluidos los topes de tamaño
(`python -m harness.tamano --feature F-039` con código 0).

## Preguntas abiertas para el humano

1. R9: ¿se acepta cerrar la verificación con el mayor N verde si 5 tumba la
   máquina, o el criterio es 5 o nada?
2. Si N=5 resulta inviable aquí, ¿se declara `mutacion.workers` en
   `harness/rigor.json`? Hoy está deliberadamente sin declarar.
3. R17: ¿la ficha nueva de huecos de test se abre en esta sesión o se deja
   propuesta por escrito para que la priorices tú?
4. R13: ¿confirmas medir sobre el árbol de F-012 en vez de sobre HEAD? Es la
   decisión de más peso del diseño (D1).
