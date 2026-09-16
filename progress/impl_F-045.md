<!-- progress/impl_F-045.md -->
# F-045 · Implementación de la CAPA 1 (T1–T12, T17, T18) y de T13

Volcado de la revisión manual al banco de evals; T13 bis y T14–T16 no entran.

## Qué cambió

El banco pasa de **7 casos** —una familia, un proveedor— a **59** de ocho
familias y 18 proveedores, con `python -m evals.revision` como escalón nuevo
ANTES de los libros: tabla plana → `ground_truth/` → `evals.conversor` →
fixtures, que sigue siendo la única puerta y el único sitio donde corre el
barrido de datos sensibles.

### Ficheros nuevos (paquete `evals/revision/`)

| Fichero | Qué hace |
|---|---|
| `vocabulario.json` + `.py` | §5 bis, los ejes de origen y la política de vacíos; lo que no reconoce, ABORTA |
| `modelos.py` + `lectura.py` | los modelos puros, y del `.xlsx` a `list[FilaPlana]` por NOMBRE de columna |
| `huella.py` | las claves de lo que escribió el importador: lo único que él puede retirar |
| `reparto.py` | **el núcleo**: la tabla de reparto de §3, los caso_id, los criterios de residuos |
| `albaranes.py` | del nombre del fichero al caso: escalera de estrategias y los fallos ruidosos |
| `escritura.py` | copia previa, pestañas nuevas y fusión conservadora con lo que ya había |
| `informe.py`, `__main__.py` | el informe de R14 y la CLI |
| `evals/mapa_casos.json` | `caso_id` ↔ código ↔ nombre ↔ formato ↔ familia ↔ grupo ↔ gemelo |

### Ficheros modificados

- `evals/conversor.py`: `Grava` y `Ferreteria` en `TIPOLOGIAS`, su único cambio.
- `evals/procesos/sv2_extraccion.py`, `runner.py`, `informe.py`: T13.
- `tests/conftest.py`: `TIPOLOGIAS` se importa del conversor en vez de copiarse
  —era una copia, y ampliar el contrato dejó 20 tests de F-011 en rojo—.
- `tests/test_mutacion_prueba_de_verdad.py`: el desbloqueo de la línea base.
- Los seis libros de `ground_truth/` y los 264 fixtures (regenerados).

## Decisiones de diseño

1. **Fusión conservadora, no volcado** (R8 + R17): el importador actualiza las
   filas de sus casos pero **nunca degrada a `?` una celda ya afirmada**, y
   conserva las que él no genera. Los 7 RES están TAMBIÉN en el Excel y un
   volcado a pelo los habría barrido. Lo vigila un guardián versionado, porque
   los libros no se versionan y un `git diff` no puede avisar.
2. **`INPUTS.CASOS.tipologia` lleva la PESTAÑA, no la familia de documento.**
   Desviación medida de §3: `MAPA_TIPO_FAMILIA` de
   `evals/procesos/{sv5_valoracion,sv6_build}.py` está indexado por pestaña
   (`Residuos` → `residuos`), así que escribir la familia deja a TODOS los casos
   —incluidos los 7 que ya funcionaban— en `tipo_familia='otro'`, la
   clasificación equivocada que F-043 vino a arreglar; y §2 declara esos dos
   ficheros intocables. **El reviewer confirma que la spec es la que está mal.**
   La familia no se pierde: va a `mapa_casos.json` y al informe, que es donde R6
   pide que se vea.
3. **El emparejado es una escalera** (`exacto` → `subcadena` → `sin_ceros`): la
   regla de la spec dejaba 24 de 59 códigos sin fichero, y `sin_ceros` quita SOLO
   los de la izquierda —`SS-0801977` y `SS-0001977` difieren por dentro—. **La
   ambigüedad no se resuelve sola**: un nombre con dos códigos sale sin asignar.
4. **Renombrar es opt-in** (`--renombrar`): el plan se propone en el informe
   con la estrategia de cada emparejado, porque deshacer un renombrado
   equivocado es caro y un caso casado con el papel de otro no lo ve nadie.
5. **Un libro que no cambia no se guarda**: cada guardado le mueve el sha256 y
   dejaba 264 fixtures «modificados» sin que cambiara un dato (R18).
6. **`?` jamás en `INPUTS`**, que es una ENTRADA y no una expectativa: el
   sentinela viajaría como texto literal dentro de la carga que lee sv5. Y **el
   descuento se traduce a porcentaje** (0,4 → `40`), que es lo que consume la
   fórmula canónica de ARCHITECTURE §13. Los dos, en `vocabulario.json`.
7. **Observable = lo que la proyección del proceso produce** (T13, R25): las
   columnas de control no se le exigen a la IA, y lo que sv2 no extrae se
   declara en vez de darse por malo.

## Fase RED (obligatoria, nivel `critico`)

Trazas reales, con el comando exacto. Cada una es el test escrito ANTES del
código.

**T1**, **T2** y **T11** fallaron con el mismo `ImportError: cannot import name
'vocabulario' from 'evals.revision' (unknown location)`: el test ya existía y el
módulo no.

**T4 · impresa vs deducida** — `python -m pytest tests/test_f045_r3_impresa_vs_deducida.py -q`

```
FFFFF                                                                    [100%]
>       tablas, _ = repartir(...)
E       AttributeError: module 'evals.revision.reparto' has no attribute 'repartir'
5 failed in 0.25s
```

**T13 · observables** — `python -m pytest tests/test_f045_r25_r26_observables.py -q`

```
E       TypeError: render() got an unexpected keyword argument 'no_observables'
7 failed, 1 passed in 0.79s
```

Y las demás igual, el test antes que el módulo: **T7 bis** (`10 failed`),
**T11 bis** (`4 failed, 2 passed`), la **ampliación del emparejado**
(`AttributeError: 'Copia' object has no attribute 'estrategia'`) y el
**incremento deducido** (`12 failed, 1 passed in 0.21s`).

## Mutación: 90 supervivientes, 74 con test y 16 justificados

La campaña completa (266 mutantes, 106 min) dejó **90 supervivientes**, casi
todos señalando lo mismo: el banco comprobaba QUÉ se escribe y casi nada de
**cómo se cuenta** ni de **cuándo se deja de escribir**, que es lo que prometen
R14 y R18. De ahí 66 tests nuevos; **74 mueren con ellos** y los 16 restantes
son equivalentes, **cada uno con su comprobación ejecutada**. Uno a uno, en
`progress/mutacion_F-045.md`; ninguno `PENDIENTE`.

**Dos equivalencias eran FALSAS y las tumbó el reviewer ejecutando**: el 49
afirmaba que el mapa salía «byte a byte igual» sin `sort_keys` —y no— y el 8
pasaba por alto que la comprobación previa guardaría el libro ANTES de la copia,
incumpliendo R16. Cerradas con test, y con ellas el 9: **ante la duda, test**.

**Cómo se verificó el cierre**: repetir la campaña costaba otras dos horas y el
intento se degradó, así que cada superviviente se **reinyectó uno a uno** contra
la suite acotada (~11 s); el reviewer reprodujo 5 de 5 por su cuenta. **Y de
paso, un desbloqueo del arnés**: `harness/mutacion.py` lanza la suite con
`PYTHONDONTWRITEBYTECODE=1` y un test del propio mutador heredaba esa variable,
con lo que la **línea base de CUALQUIER campaña de este repositorio estaba
roja**. Arreglado; **hay que portarlo a `arnes-base`**.

## Lo que queda fuera y lo que el humano tiene que decidir

1. **CERRADA (2026-09-16) · `INPUTS.CASOS.tipologia` lleva la pestaña**: el
   humano la valida y **§3 queda corregida**, que era la que estaba mal. Deja
   de ser una desviación declarada.
1 bis. **DECISIÓN ABIERTA · `codigo_imputacion` sale `?` en las 114 líneas**:
   la tabla plana no dice si la partida venía IMPRESA —en residuos no, en
   hormigón sí— y suponerlo sería inventar (R11). El precio: la mitad de
   EXTRACCIÓN del patrón 1 sin vigilar; la de DECISIÓN sí se compara. Se cierra
   con una columna nueva en el Excel o aceptando la ceguera.
2. **CERRADA (2026-09-16) · el incremento por LER se DEDUCE del contrato**: la
   línea de material sí está impresa con su LER, pero el incremento sale de
   mirar el contrato con ese código. Son dos líneas, una por fase —material a
   IA1, incremento a las sintéticas de IA3—, así que el ground truth
   contradictorio de RES-004 desaparece: no había que elegir. Regla en
   `vocabulario.json`; §5 ter lo recoge. **No implementa nada en sv5/sv6**: sus
   casos siguen naciendo rojos a propósito.
3. **Documentos de entrada**: 57 de 59 ya están renombrados a su `caso_id`;
   RES-020 y RES-021 siguen sin papel y salen OMITIDOS.
4. **DECISIÓN ABIERTA · `INPUTS.CONTRATO_LINEAS` y `CONDICIONES` no se
   alimentan** (§3), y el precio es mayor del anotado: IA3, IA4 y el E2E **no
   miden nada**. Tres vías medidas en `impl_F-045_contrato_lineas.md`.
5. **Fuera de alcance**: T13 bis, T14 (`patrones.json`), T15 (`README`) y T16.
   **T13 sí entró** tras la pasada con LLM: sin ella el banco no era legible.

## Lo que dijo la pasada con LLM (2026-09-16) y qué se arregló

Veredicto ROJO, pero **1295 de los 1456 fallos eran «obtenido None»**: ruido del
banco, con dos causas y dos respuestas.

**Arreglado aquí (T13, R25 y R26).** IA1 e IA2 se comparaban por TODO el ground
truth: las columnas de control del banco —`caso_id` y `fichero_albaran`, que las
ponemos nosotros— y los campos que sv2 no extrae (`unidad`, `descuentos`,
F-024). Ahora se podan con `OBSERVABLES` y se **declaran** en sección propia.
Regla: **observable es exactamente lo que la proyección del proceso produce**,
con un test que ata las dos listas para que no diverjan. Con eso **IA1 + IA2
pasa de 352 fallos críticos a 86** y de 141 avisos a 60; los 86 que quedan son
los defectos de verdad, encabezados por 27 `proveedor_nombre` y 27 `cantidad`.
El informe además anunciaba los no observables como «campos sin clasificar en
`criticidad.json`»: ahora son dos secciones, que son dos problemas.

**Medido, NO arreglado: IA3, IA4 y E2E no miden nada.** Sin
`INPUTS.CONTRATO_LINEAS` IA3 no tiene contra qué valorar y sus ~865 fallos
hablan de la tabla vacía, no del código; las tres vías, con su coste y la
recomendada, en **`impl_F-045_contrato_lineas.md`**.

**Qué esperar de otra pasada** (la lanza el humano): IA1 baja de 352 a 86; IA2
sigue en 0; IA3, IA4 y E2E **no cambian** hasta que se decida la vía de las
líneas de contrato. Solo merece la pena para confirmar el recuento de IA1.

## Cómo se aplicaron las dos decisiones del humano (2026-09-16)

La tipología por pestaña ya estaba implementada: lo que cambia es que **§3 queda
corregida** y deja de ser desviación. El incremento por LER pasa a sintética de
IA3 con una regla en `vocabulario.json`, y para que las filas viejas de IA1 no
se quedaran ahí hizo falta `evals/huella_importacion.json`: las CLAVES de lo que
el importador escribió antes, que es lo único que él puede retirar.

**Y costó 38 valores afirmados de los 7 RES.** La huella tenía un agujero —al
fusionar, la fila del humano toma la clave del importador y desde ese momento la
da por suya—, ya cerrado; pero la comprobación posterior **miró un campo de tres
casos y dio por bueno el resto**, restauró 3 y dejó 35 que encontró el reviewer:
`numero_albaran` (con `SS-0001977`, el del precedente de esta ficha),
`match_method='semantic'`, `codigo_producto_contrato='C1'`, `linea_contrato` y
`requiere_revision`. **Con `?` dejan de mirarse en silencio**, y lo que dejaban
de mirar es que la valoración elige el producto correcto del contrato: el
patrón 5. Los 35 están restaurados desde `5132bdc` valor a valor, **el camino
está muerto** (tres reimportaciones ya no degradan ni uno), el método está
arreglado —comparación campo a campo, que reproduce los 35 exactamente— y hay
guardián: `tests/datos/afirmado_por_el_humano_RES.json` fija los **496 valores
afirmados** y el test falla nombrando cada pérdida. Relato entero en
`progress/impl_F-045_contrato_lineas.md`.

## Verificaciones MANUAL pendientes

**T19** (R31): validar la tabla de reparto, la política de vacíos y las cuatro
decisiones de arriba. **T20** (R32) ya se lanzó el 2026-09-16; otra pasada la
decide el humano con los números de la sección anterior.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite de la raíz) | **865 pasan, 0 fallan** |
| De ellos, de F-045 | **296** en 23 ficheros `tests/test_f045_*` |
| Cobertura de las líneas cambiadas | **98,3 %** (113/115) de lo último cambiado; **97,9 %** sobre la feature entera |
| Tiempo de la suite | **82,37 s** |
| Mutación · capa 1 | **266 mutantes, 176 muertos, 90 supervivientes**, 0 timeouts, 6381 s, 4 workers; de los 90, **74 mueren** con los tests nuevos y **16 son equivalentes** con su comprobación ejecutada |
| Mutación · lote de las dos decisiones | 325 líneas, **44 mutantes, 35 muertos, 9 supervivientes**, 871 s con 4 workers; de los 9, **8 mueren con test nuevo y 1 es equivalente** con su comprobación ejecutada (`progress/mutacion_F-045_lote2.md`) |
| Conversor e idempotencia | `python -m evals.conversor` en 0, sin hallazgos del barrido; segunda pasada de `revision` + `conversor` deja `git status` vacío |

### Lo que el volcado deja en el banco (medido, no estimado)

- 142 filas → **59 casos** (21 RES, 17 HOR, 10 GEN, 4 MOR, 3 FER, 2 GRA, 1 ALQ,
  1 COM), **11 de no regresión** y **48 de defecto conocido**.
- IA1 recibe **114 líneas impresas**, solo **12 con unitario impreso** y **102
  con la celda vacía afirmada**: la separación extracción/valoración del humano.
- Rojos que nacen esperados, agrupados aparte: `combustible` (COM-001),
  `ferreteria` (3), `grava` (2), `minimo_1_tn` (9 RES), `incremento_por_ano` (6).
