<!-- progress/impl_F-045_contrato_lineas.md -->
# F-045 · La pasada con LLM, campo a campo, y qué falta para IA3/IA4/E2E

## El ruido de IA1 que quitó T13, medido sobre la pasada del 2026-09-16

| Campo | Fallos | Por qué no se le puede exigir a la IA |
|---|---:|---|
| `IA1.lineas.caso_id` | 72 | etiqueta del banco, no la imprime ningún albarán |
| `IA1.lineas.unidad` | 72 | sv2 no la extrae (F-024): deuda declarada, no rojo |
| `IA1.cabeceras.caso_id` | 57 | ídem |
| `IA1.cabeceras.fichero_albaran` | 57 | el nombre se lo pusimos nosotros al renombrar |
| `IA1.lineas.descuentos` | 8 | sv2 tampoco los proyecta hoy |
| **Total de ruido** | **266** | |

Y los **86 que quedan, que son los defectos de verdad**: 27
`proveedor_nombre`, 27 `cantidad`, 16 `importe`, 11 `precio_unitario`, 4
`fecha` y 1 `numero_albaran`. Más 81 avisos de ruido que también se van.

# Qué haría falta para que IA3, IA4 y el E2E midan algo

**Medición para que el humano decida. No se ha implementado nada de esto.**

## El problema, en números de la pasada real del 2026-09-16

`design.md` §3 dejó fuera `INPUTS.CONTRATO_LINEAS` e `INPUTS.CONDICIONES`, y se
anotó como «los casos nuevos solo son evaluables con LLM». **El alcance real es
mayor**: sin líneas de contrato, IA3 no tiene contra qué valorar, así que sus
fallos son todos `obtenido None` y no miden al sistema, sino a la tabla vacía.

| Fase | Fallos en la pasada | Qué los causa |
|---|---:|---|
| IA3 `lineas_valoradas` | 107 partida + 103 importe + 95 precio + 95 `precio_source` | no hay contrato |
| FINAL `lineas` | 107 + 103 + 95 + 95 + 79 `casa_con_contrato` | lo mismo, aguas abajo |
| FINAL `datos_generales` | 54 `total_valorado_esperado` | lo mismo |
| IA4 `conciliacion` | 27 `precio_unitario_esperado` | lo mismo |

Son **~865 fallos** que no informan de nada, y dejan 52 casos nuevos en rojo por
una razón que no es la suya. Los 7 casos RES sí miden, porque sus líneas de
contrato las escribió el humano a mano.

## Lo que hay que llenar

- `CONTRATO_LINEAS`: `caso_id`, `codigo_producto`, `descripcion_recurso`,
  `unidad`, `precio_unitario`, `codigo_partida`. Una fila por recurso del
  contrato, **por caso** (el fixture es por caso, así que las líneas se repiten
  en cada albarán del mismo contrato).
- `CONDICIONES`: pares campo/valor. Los 7 RES declaran cinco
  (`fecha_albaran`, `numero_albaran`, `codigo_ler`, `volumen_m3`,
  `tamano_contenedor_contrato`); fuera de residuos harían falta otros
  (`anio_contrato` para el incremento por año, `rendimiento_minimo_bombeo`…).

**Tamaño del problema**: 59 casos, **20 contratos distintos** (el mayor,
`CTSB23/0964`, cubre 10 casos), 114 líneas impresas —94 marcadas `EN CONTRATO`,
45 `NUEVA`, 3 `OFERTA`— y 28 deducidas. Con ~6 líneas de contrato por caso, como
los RES, salen **~350 filas** en `CONTRATO_LINEAS`.

## Las tres vías, con su coste

### A · Sintetizarlas del propio Excel

Por cada línea marcada `EN CONTRATO` se fabrica su línea de contrato con el
`concepto`, el `precio unitario` y la `partida` que el humano ya escribió.

- **Trabajo del humano: ninguno.** Sale del volcado, automático.
- **Coste real: el eval deja de medir lo que importa.** Se le estaría dando a
  IA3 la respuesta como entrada: el matching acierta por construcción y el
  patrón 5 —«unitario equivocado dentro del contrato»— se vuelve inobservable,
  porque el contrato tendría exactamente una línea y sería la correcta. Los 7
  RES tienen **señuelos a propósito** (C2 con el mismo precio que C1) y eso es
  justo lo que un contrato sintetizado no puede tener.
- **Veredicto**: mide la aritmética y las sintéticas, no el matching. Serviría
  como red parcial, pero hay que decir en el informe qué NO vigila.

### B · Leerlas del ERP por `sigrid-api` (la fiel)

El Excel ya trae el `codigo contrato` de los 59 casos. `sigrid-api` expone
`sql/read` sobre la base `ruesma`, que es donde viven los contratos, y desde
local **solo lectura** está permitido.

- **Trabajo del humano: casi ninguno** —autorizar la consulta y revisar una
  muestra—; 20 consultas, muy por debajo del tope de 1.000 filas y 230 s.
- **Coste**: hay que averiguar el modelo de datos del contrato en Sigrid
  (`azure-apps/sigrid_tablas.md`) y mapear sus columnas a las seis del libro. Es
  trabajo de exploración, no de volumen.
- **Riesgo**: el contrato de HOY puede no ser el que estaba vigente cuando se
  emitió el albarán —hay casos de 2024 y de 2026—. Si el ERP versiona precios,
  hay que leer la versión de la fecha del albarán; si no, algunos casos
  quedarían valorados contra un precio que no es el que se aplicó.
- **Veredicto**: es la única vía que mide el matching de verdad, incluidos los
  señuelos naturales. **Es la que recomiendo**, con la fecha como salvedad.

### C · Tomarlas de lo ya persistido (`albaran_contrato_lines_merge`)

- **Trabajo del humano: ninguno**, pero solo cubre los albaranes que el sistema
  ya procesó, y son justo los que se están evaluando.
- **Coste**: circular. El ground truth saldría de lo que el sistema decidió, que
  es lo que el banco tiene que juzgar. Y en producción solo hay lectura.
- **Veredicto**: descartada salvo como atajo para rellenar la vía B.

## Recomendación

**Vía B**, y en ficha propia: no es capa 1. Mientras tanto, que el informe de la
pasada **no cuente IA3, IA4 y E2E como rojos de sistema**, porque hoy dicen algo
sobre el banco y nada sobre el código. Eso es barato: la fase ya sabe si su
entrada está vacía, y `NO_EVALUABLE` existe justamente para esto.

## Lo que costó aplicar la decisión 2 (y el agujero que destapó)

Separar las dos líneas no bastaba: las importaciones anteriores habían escrito
el incremento como línea de IA1, y **la fusión conservadora mantiene lo que no
genera** (R17), así que esas filas se quedaban y el banco seguía exigiendo lo
mismo por los dos caminos. De ahí `evals/huella_importacion.json`: las CLAVES
—no los valores— de lo que el importador escribió la vez anterior. Lo que está
en la huella y ya no se produce, se retira; lo que no está, se conserva, porque
es del humano.

Y la huella tenía su propio agujero, que **costó el `modifier_source` de tres
casos RES antes de verse**: al fusionar, la fila del humano toma la clave del
importador y desde ese momento la huella la da por suya. Ahora solo se retira
una fila si no lleva **nada** que el importador no pudiera escribir; los tres
valores se restauraron desde los fixtures de `697f00e`. Con eso los 7 RES
conservan su `gestion_residuos`, su `incremento_residuos` y sus precios, y
tienen UNA línea en IA1 —el material— y UNA sintética en IA3 —el incremento—.

## Por qué mi comprobación vio 3 y el reviewer 38

No es que mirara mal: es que **miré poco**. Cuando la retirada demasiado amplia
se llevó datos, comprobé el campo que ya sabía roto —`modifier_source`— en los
tres casos donde lo había visto, y di por bueno el resto. Es el mismo error que
el banco entero existe para evitar: comprobar lo que sospechas en vez de todo
lo que puede romperse.

**El método arreglado**: comparar los fixtures versionados campo a campo entre
dos commits, emparejando las filas por su clave, y buscar **la firma exacta del
daño** —un valor afirmado que pasa a `@@NO_COMPARAR@@`, a `null` o a nada—.
Con él, el recuento reproduce los 35 del reviewer exactamente, y además separa
las **28 filas que se movieron a propósito** (el incremento por LER que pasó de
IA1 a las sintéticas de IA3) de las pérdidas de verdad, que era la distinción
que a ojo no se podía hacer.

**El camino está muerto**, y esto se midió, no se supuso: tras restaurar los 35,
tres reimportaciones seguidas no degradan ni uno. Era daño viejo sin restaurar
—de la retirada amplia que ya se corrigió—, no un camino vivo.

**La defensa que faltaba**: los libros `.xlsx` no se versionan, así que un
`git diff` no podía avisar. `tests/datos/afirmado_por_el_humano_RES.json` guarda
los **496 valores afirmados** de los 7 casos RES y el test los compara uno a
uno, fallando **con el nombre** de cada pérdida. Comprobado que muerde:
degradando a mano un `match_method` se pone en rojo.

## El patrón que me ha mordido dos veces: el test que pasa con el fallo puesto

Dos veces en esta feature un test ha dicho cubrir algo y ha pasado **con el
defecto dentro**:

1. El de **R16**, que comprobaba la copia de seguridad en `escritura` cuando el
   mutante vivía un nivel más arriba, en el camino de la CLI. No mataba nada.
2. El del **casado por prefijo**, que metía las filas en un `dict` por
   descripción: la fila duplicada pisaba a su gemela y el `dict` salía idéntico
   con mutante y sin él, aunque hubiera **3 filas donde debían ir 2**.

Los dos tienen la misma forma: **comparar una proyección en vez del resultado**.
Un `dict` por clave pierde los duplicados; un nivel por debajo pierde el camino
real. Y las dos veces el mutante correspondía a un defecto de verdad —la copia
que deja de ser el estado previo, la sintética del humano duplicada—, así que la
proyección no solo no cazaba: tapaba.

**Repaso hecho sobre los 23 ficheros de test de F-045.** El colapso a `dict`
sobre filas aparecía en **un solo sitio**, el ya citado, y está reescrito para
comparar la lista entera. Los `set()` que quedan son todos sobre **nombres de
columna, de tabla o de caso**, donde un duplicado es imposible por
construcción. Los tests de fusión que solo miraban el recuento (`len(...) == N`)
sí habrían cazado esta duplicación —de hecho es lo único que la habría cazado—,
y aun así se han reforzado para decir **qué fila queda y con qué valores**, que
es lo que distingue «hay dos filas» de «hay las dos filas correctas».
