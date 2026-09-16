<!-- progress/review_F-045.md -->
# F-045 · Review de las dos decisiones del humano (segundo lote)

**Revisión incremental desde `5132bdc` (pasada 3)** — HEAD `490db12`, 6
commits. Lo aprobado en las pasadas 1 y 2 queda dado por bueno; aquí se revisa
`5132bdc..HEAD`, más las puertas enteras.

## Veredicto: CHANGES_REQUESTED

Las dos decisiones están bien aplicadas y la regla nueva de la huella es
correcta. **Bloquean dos cosas**: se perdieron **35 valores afirmados más** del
ground truth escrito a mano —además de los tres `modifier_source` que sí se
vieron y se restauraron—, y **este lote no tiene campaña de mutación**, que en
`critico` no es opcional y aquí mide justo el código que causó la pérdida.

## Las puertas, ejecutadas enteras

`bash harness/init.sh` → **exit 0**: **846 tests** en 118 s; COBERTURA `[OK]
96,2 % de 106 líneas`; RUTAS SENSIBLES `N/A` con su motivo; TAMAÑO `design
249/250`, `impl 220/220`. Árbol limpio. `services/` sin tocar: **sv5 y sv6
siguen sin implementar nada** y sus casos nacen rojos a propósito (§5 ter).

## BLOQUEANTE 1 · se perdieron 35 valores afirmados más, y nadie los vio

Comparé fixture a fixture `5132bdc..HEAD` buscando la firma exacta del daño: un
valor afirmado que pasa a `@@NO_COMPARAR@@`. Aparecen **35**, todos de los 7
casos RES, que son **los únicos que hoy miden IA3** (sus líneas de contrato las
escribió el humano):

| Tabla · campo | Casos | Lo que había |
|---|---:|---|
| `IA1.cabeceras.numero_albaran` | 7 | `SS-0000168`, `SS-0003935`, `SS-0000589`, `SS-0003967`, `SS-0001977`, `SS-0025146`, `SS-0026122` |
| `FINAL.datos_generales.numero_albaran` | 7 | los mismos |
| `IA3.lineas_valoradas.match_method` | 6 | `semantic` |
| `IA3.lineas_valoradas.codigo_producto_contrato` | 6 | `C1` |
| `FINAL.lineas.linea_contrato` | 6 | la línea de contrato afirmada |
| `FINAL.datos_generales.requiere_revision` | 3 | su valor |

No es una lectura de fixtures: lo comprobé **en los libros**, que son la fuente
y lo que NO se versiona. `IA3_valoracion.xlsx`/Residuos/RES-001 trae hoy
`match_method='?'` y `codigo_producto_contrato='?'`, e `IA1_extraccion.xlsx`
trae `numero_albaran='?'`. En `5132bdc` y en `697f00e` estaban; son los mismos
que la pasada 1 presumía de conservar («RES-001 conserva `SS-0000168` y su
`match_method` semántico»).

**Por qué importa**: `match_method` y `codigo_producto_contrato` son lo único
que comprueba que la valoración eligió **el producto correcto del contrato** —el
patrón 5, «unitario equivocado dentro del contrato»—, y `SS-0001977` es el caso
que dio nombre al precedente de F-045 («manda el código del papel, no el
persistido»). Con `?` no salen rojos: dejan de mirarse, en silencio.

**Qué hay que hacer**: restaurarlos en los libros desde los fixtures de
`5132bdc` (idénticos a `697f00e` en estos campos), regenerar, y decir por escrito
**por qué camino se fueron**. Con el código de hoy `fundir()` no degrada un `?`
sobre un valor afirmado y `_solo_del_importador` impide retirar la fila, así que
lo más probable es **daño viejo sin restaurar**: la restauración de los tres
`modifier_source` se quedó corta y nadie volvió a mirar el resto. Si quedara
algún camino vivo, hay que cerrarlo. **Y falta la defensa**: los libros no se
versionan, así que nada avisa de un valor afirmado que desaparece. Propongo un
test que fije los valores del humano en los 7 RES —una instantánea versionada de
esas celdas, barata— y falle si se degradan. Sin eso, la próxima pérdida también
será invisible.

## BLOQUEANTE 2 · este lote no tiene campaña de mutación

`progress/mutacion_F-045.md` sigue midiendo `1c3e8d7`, 2371 líneas y 266
mutantes: el lote anterior. Tras el merge, el alcance de la feature es **otro**:
recalculado con `harness.alcance` da **325 líneas y 44 mutantes**, y ninguno se
ha juzgado. Lo que queda sin medir es exactamente lo que más lo necesita:

| Fichero | Líneas | Mutantes |
|---|---:|---:|
| `escritura.py` (fusión, retirada, prefijo) | 131 | **26** |
| `huella.py` (nuevo) | 81 | **7** |
| `reparto.py`, `informe.py`, `__main__.py`, `vocabulario.py` | 106 | 11 |

Son ~20 minutos con los 4 workers de siempre (`python -m harness.mutacion
--feature F-045` ya mide solo este lote, porque la rama sale de `dev`). En
`critico`, T18 pide campaña completa y cero supervivientes injustificados; y tras
una pérdida de datos, dar por buena la lógica nueva porque la suite pasa es justo
lo que esta puerta existe para evitar.

## Lo que sí está bien, y lo he verificado

- **Tipología por pestaña**: `design.md` §3 corregida diciendo lo que el sistema
  hace —`INPUTS.CASOS.tipologia` = pestaña; la familia de documento va al mapa y
  al informe— con el motivo (`MAPA_TIPO_FAMILIA` indexado por pestaña). No queda
  ningún resto que la llame desviación: el aviso del informe desapareció y la
  lista de decisiones la marca CERRADA.
- **El incremento por LER**: los 7 RES quedan con **1 línea en IA1** (el
  material impreso), **1 sintética en IA3** con `modifier_source=gestion_residuos`,
  `rol_linea=incremento_residuos` y su precio (51, 90, 90, 77 y el centinela
  `@@ESPERA_REVISION@@` donde el contrato no tarifa el LER), 1 en
  `FINAL.lineas_anadidas` y el `codigo_ler` intacto en el contexto de IA2. La
  contradicción de RES-004 desaparece sin elegir, que es lo que decía el humano.
  Contra `697f00e`: **ninguna clave del ground truth original ha desaparecido**.
- **La regla nueva de la huella es correcta**: retirar solo lo que está en la
  huella Y `_solo_del_importador`, es decir, ninguna columna con un valor que el
  importador nunca escribe. Cierra el camino por el que una fila fusionada se
  daba por propia. Con tres tests que lo fijan, incluido el del agujero.
- **El guardián funciona**: reintroduje la fuga en una copia aislada —quitar la
  ruta de huella de la llamada a `cli.ejecutar`— y
  `test_f045_r17_los_tests_no_escriben_la_huella_del_repositorio` **falla**.
- **La reimportación no mueve nada**: corrí `python -m evals.revision --dry-run`
  con el informe a mi scratchpad y sale **idéntico** al versionado salvo el
  aviso de seco: 59 casos, 0 nuevos, 11 no regresión y 48 defecto conocido,
  «ningún caso cambia de grupo». El `git status` queda limpio.

## Checkpoints

- **C1** [x] exit 0 y ficheros obligatorios. **C2** [x] una feature
  `in_progress`, rama correcta, `current.md` al día.
- **C3** [x] `huella.py` es dominio puro (solo `json` y `pathlib`), ruta en la
  primera línea, sin prints ni secretos ni dependencias nuevas. La huella no
  guarda valores, solo claves: ni precios ni datos de proveedor.
- **C3 bis** N/A **justificado**: no toca `docs/referencia/`.
- **C4** [ ] los 846 pasan y el LER trae 13 tests nuevos, pero **ningún test
  protege los valores afirmados del humano en los libros**, que es R17 y lo que
  se ha perdido dos veces.
- **C4 bis** [ ] **sin campaña de mutación de este lote** (bloqueante 2). Fase
  RED sí (traza del incremento deducido, `12 failed, 1 passed`), cobertura
  `[OK]` 96,2 %, y RM1 es precisamente lo que falla: el alcance medido no es el
  que se revisa.
- **C4 ter** [x] la puerta corre y sale N/A con su motivo.
- **C5** [x] commits por tarea y estado real; `tasks.md` sin cambios (estas dos
  decisiones eran T19, que sigue abierta a la espera del resto).

## Condiciones de cierre que siguen siendo del humano

1. **Copiar los documentos de entrada**: 57 de 59 ya renombrados; RES-020 y
   RES-021 siguen sin papel y salen OMITIDOS.
2. **`codigo_imputacion` sale `?` en las 114 líneas** (columna nueva en el Excel
   o aceptar la ceguera de la mitad de extracción del patrón 1).
3. **`INPUTS.CONTRATO_LINEAS` y `CONDICIONES`**: sin ellas IA3, IA4 y el E2E no
   miden nada; las tres vías están medidas en `impl_F-045_contrato_lineas.md`.

El dato de la última pasada (IA1 en 128 fallos reales y 12 verdes, sin el ruido
de `caso_id`, `fichero_albaran` ni `unidad`) es coherente con lo que mide el
banco hoy y no cambia el veredicto: lo que bloquea no es lo que el banco ve,
sino lo que ha dejado de ver sin avisar.
