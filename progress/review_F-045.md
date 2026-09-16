<!-- progress/review_F-045.md -->
# F-045 · Review de la restauración, el guardián y la campaña del lote

**Revisión incremental desde `490db12` (pasada 4)** — HEAD `e7ca7e5`, 4
commits. Lo aprobado antes queda dado por bueno; aquí se revisa
`490db12..HEAD`, más las puertas enteras.

## Veredicto: CHANGES_REQUESTED

**La restauración es exacta y completa, y el guardián es el que hacía falta**:
eso queda cerrado y verificado abajo, valor a valor. Lo que bloquea es la
campaña: **uno de los 9 supervivientes NO está cerrado** —sobrevive hoy y
sobrevivía en el commit donde se dice haberlo matado—, y **otro está mal
etiquetado**. Es poco trabajo, pero es justo la lógica de fusión que ya se
comió datos una vez.

## Las puertas, ejecutadas enteras

`bash harness/init.sh` → **exit 0**: **865 tests** en 121 s; COBERTURA `[OK]
98,3 % de 115 líneas`; RUTAS SENSIBLES `N/A` con su motivo; TAMAÑO todo dentro.
Árbol limpio, sin ficheros borrados en el lote (`git log --diff-filter=D` vacío:
el incidente del `git checkout` no se llevó nada versionado por delante).

## Lo primero, y está BIEN: los 35 y el método

Repetí mi barrido —todos los fixtures, todas las tablas, todos los campos,
buscando un valor afirmado que pase a `@@NO_COMPARAR@@`—, ahora contra las dos
referencias:

- **`5132bdc..HEAD`: 0 degradados** (eran 35). Los seis campos restaurados
  coinciden **exactamente** con el estado sano: 42 valores comparados uno a uno,
  cero diferencias.
- **`697f00e..HEAD`: 0 degradados y 0 filas del original sin pareja hoy.** Del
  ground truth que escribió el humano antes de F-045 no falta nada.
- **Las «28 filas movidas a propósito» lo están de verdad**: son exactamente 28
  y sus 112 valores se reparten en dos grupos sin residuo —20 filas
  `num_linea=2` (el incremento por LER retirado en IA1, IA2, IA3, INPUTS y
  FINAL) y 8 sintéticas/añadidas re-tecleadas con el concepto largo del Excel—.
  **Cero valores fuera de esas dos categorías**, y todas las re-tecleadas
  existen hoy con su clave nueva: la categoría no tapa ninguna pérdida.

## El guardián: correcto y eficaz

- **Los 496 no son «lo que hay hoy»**: crucé la instantánea contra el estado
  sano previo con las claves del propio test. **433 son idénticos a `5132bdc`**
  y los demás son altas legítimas (las sintéticas bajo su clave nueva). Contra
  el original `697f00e`, 375 coinciden literalmente. **Ningún valor de la
  instantánea es el centinela ni está vacío**: no fija el daño, fija el dato.
- **Falla de verdad**: degradé `IA3.lineas_valoradas[RES-001|1].match_method` a
  `@@NO_COMPARAR@@` en una copia aislada y
  `test_f045_r17_ningun_valor_afirmado_ha_desaparecido` **falla nombrándolo**
  («era `'semantic'`»). Los otros cuatro tests del fichero cubren el cambio de
  valor, los seis campos del disgusto por su nombre, que la instantánea no se
  quede corta y que `fundir()` no degrade.

## La campaña del lote: bien medida, mal cerrada en dos puntos

Totales recalculados por mí: el alcance que declara (325 líneas, 44 mutantes en
`5132bdc..a7de52a`) es correcto, RM2 cuadra (871 s × 4 workers ÷ 44 = 79 s por
mutante frente a línea base 88 s) y no hay cabecera de campaña inválida.

**RM1 · lo que la campaña no vio, lo he medido yo.** El SHA medido es `a7de52a`
y después entró `f14eb68`, que **reescribe la guarda de retirada**. El alcance
de hoy son 357 líneas y 47 mutantes; el delta posterior a la campaña genera
**11 mutantes**, todos en esa guarda. Los reinyecté uno a uno: **mueren los
11**. Ese hueco queda cerrado, y queda escrito aquí.

**Los 9 supervivientes, reinyectados uno a uno por mí: 7 mueren, 2 no.**

1. **BLOQUEANTE · el 3 no está cerrado.** `escritura.py`, `if nueva is None and
   campo_prefijo:` → `or`: **sobrevive** a la suite acotada (296 tests) **en
   HEAD y también en `a7de52a`**, el commit donde el informe dice «reinyectado
   uno a uno, muere». El test que lo nombra,
   `test_f045_r17_el_casado_por_prefijo_no_pisa_una_coincidencia_exacta`,
   **existe y pasa con el mutante puesto**: monta el resultado en un `dict`
   por descripción, y ahí la fila duplicada se colapsa. Con el mutante,
   `fundir_filas` devuelve **3 filas donde debe devolver 2** —la del humano con
   `20` conservada y la del importador con `99` añadida—, que es exactamente el
   defecto que este lote vino a matar: el banco exigiendo lo mismo por dos
   caminos. **Arréglese el test** (que compare la lista de filas, no un `dict`
   que se traga los duplicados) y corríjase la ficha.
2. **El 7 está mal etiquetado.** `huella.py`, `sort_keys=True` → `False`:
   **sobrevive**, como corresponde a un mutante que el propio análisis reconoce
   equivalente («aquí sí da el mismo fichero»). El test byte a byte no puede
   matarlo porque el byte no cambia. Que se declare **EQUIVALENTE con su
   demostración ejecutada** —que la tiene— en vez de «cerrado con test»: con
   esa ficha, la frase «los 9 cerrados con test, ninguno equivalente» del
   informe y de «Evidencias» es falsa, y esa frase es la que lee el siguiente.

Los otros siete (1, 2, 4, 5, 6, 8, 9) mueren con el test que dice cada ficha, y
los cacé nombrando el test que falla en cada caso.

## La guarda reescrita: el arreglo es correcto

`_solo_del_importador` pasa de deducir las columnas en duda de las filas de la
pestaña de turno a recibirlas declaradas para **toda la importación**
(`_columnas_en_duda`). Es más estricto, no menos: el conjunto de columnas
protegidas crece, y sin columnas declaradas devuelve `False`, o sea **no retira
nada**. Corrige el defecto real que describe —una pestaña donde esta vez no se
escribe nada no podía retirar, que es justo cuando el humano borra una línea— y
los 11 mutantes de ese código mueren.

**Riesgo residual, no bloqueante**: la fila se protege por las columnas que el
importador deja en `?`. Un valor del humano en una columna que el importador
**nunca escribe ni deja en `?`** no protege su fila. Hoy no es alcanzable en los
7 RES —los cubre la instantánea—, pero si algún día se retiran filas de otros
casos, conviene que `interrogantes` sea «todas las columnas que el importador
produce en esa tabla», no solo las que deja en duda.

## Checkpoints

- **C1** [x] exit 0 y ficheros obligatorios. **C2** [x] estado coherente, rama
  correcta, `current.md` al día.
- **C3** [x] `huella.py` sigue siendo dominio puro y sin valores (solo claves);
  ruta en la primera línea, sin prints, secretos ni dependencias nuevas.
- **C3 bis** N/A **justificado**: no toca `docs/referencia/`.
- **C4** [x] 865 en verde y **el hueco que señalé está cubierto**: la
  instantánea de R17 es el test que faltaba.
- **C4 bis** [ ] campaña del lote presente, bien medida y verificada por mí,
  pero **un superviviente sigue vivo con la ficha diciendo que muere** y otro
  está etiquetado al revés. En `critico` eso es el checkbox vacío.
- **C4 ter** [x] la puerta corre y sale N/A con su motivo.
- **C5** [x] commits por tarea, sin temporales, estado real. Bien separado el
  informe del lote (`mutacion_F-045_lote2.md`), como F-043.

## Fuera de este lote

Los dos hallazgos nuevos del banco —`ALBARAN VALORADO` leído al revés (9 líneas,
17 fallos falsos) y la consolidación de FER-002 (37)— **no son de este lote y no
entran en el veredicto**; anotados para su ficha. Siguen abiertas las tres
condiciones del humano: los documentos que faltan (RES-020, RES-021),
`codigo_imputacion` en `?` y las líneas de contrato de IA3/IA4/E2E.
