<!-- progress/impl_F-045.md -->
# F-045 · Implementación de la CAPA 1 (T1–T12, T17, T18) y de T13

Volcado de la revisión manual del humano al banco de evals. T13 bis, T14, T15 y
T16 NO entran aquí.

## Qué cambió

El banco pasa de **7 casos** —una familia, un proveedor— a **59** de ocho
familias y 18 proveedores, con `python -m evals.revision` como escalón nuevo
ANTES de los libros: tabla plana → `ground_truth/` → `evals.conversor` →
fixtures. El conversor sigue siendo la única puerta a los fixtures y el único
sitio donde corre el barrido de datos sensibles.

### Ficheros nuevos (paquete `evals/revision/`)

| Fichero | Qué hace |
|---|---|
| `vocabulario.json` + `.py` | la tabla de §5 bis, los tres ejes de origen y la política de vacíos. Lo que no reconoce, ABORTA |
| `modelos.py` + `lectura.py` | los modelos puros, y del `.xlsx` a `list[FilaPlana]` localizando columnas por NOMBRE |
| `reparto.py` | **el núcleo**: la tabla de reparto de §3, los caso_id, los criterios de residuos |
| `albaranes.py` | del nombre del fichero al caso: escalera de estrategias y los fallos ruidosos |
| `escritura.py` | copia previa, pestañas nuevas y fusión conservadora con lo que ya había |
| `informe.py`, `__main__.py` | el informe de R14 y la CLI |
| `evals/mapa_casos.json` | versionado: `caso_id` ↔ código ↔ nombre ↔ formato ↔ familia ↔ gemelo |
| 20 ficheros `tests/test_f045_*` | 250 tests |

### Ficheros modificados

- `evals/conversor.py`: `Grava` y `Ferreteria` en `TIPOLOGIAS` (su único cambio).
- `evals/procesos/sv2_extraccion.py`, `evals/runner.py`, `evals/informe.py`:
  T13, los campos observables de IA1/IA2 (abajo).
- `tests/conftest.py`: `TIPOLOGIAS` se importa del conversor en vez de copiarse
  —era una copia, y ampliar el contrato dejó 20 tests de F-011 en rojo—.
- `tests/test_mutacion_prueba_de_verdad.py`: el desbloqueo de la línea base.
- Los seis libros de `ground_truth/` y los 264 fixtures (regenerados).

## Decisiones de diseño

1. **Fusión conservadora, no volcado** (R8 + R17): el importador actualiza las
   filas de sus casos pero **nunca degrada a `?` una celda ya afirmada**, y
   conserva las filas que él no genera. Los 7 RES están TAMBIÉN en el Excel y un
   volcado a pelo los habría barrido; verificado sobre RES-001, que conserva
   `SS-0000168`, su `match_method` semántico y sus 6 líneas de contrato.
2. **`INPUTS.CASOS.tipologia` lleva la PESTAÑA, no la familia de documento.**
   Desviación medida de §3: `MAPA_TIPO_FAMILIA` de
   `evals/procesos/{sv5_valoracion,sv6_build}.py` está indexado por pestaña
   (`Residuos` → `residuos`), así que escribir la familia deja a TODOS los casos
   —incluidos los 7 que ya funcionaban— en `tipo_familia='otro'`, la
   clasificación equivocada que F-043 vino a arreglar; y §2 declara esos dos
   ficheros intocables. **El reviewer confirma que la spec es la que está mal.**
   La familia no se pierde: va a `mapa_casos.json` y al informe, que es donde R6
   pide que se vea.
3. **El emparejado es una escalera de estrategias** (`exacto` → `subcadena` →
   `sin_ceros`): la regla de la spec dejaba 24 de 59 códigos sin fichero, y
   `sin_ceros` quita SOLO los de la izquierda —`SS-0801977` y `SS-0001977`
   difieren por dentro—. **La ambigüedad no se resuelve sola**: un nombre con
   dos códigos —existe, un PDF con dos albaranes— sale sin asignar.
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
   columnas de control del banco no se le exigen a la IA, y lo que sv2 no
   extrae se declara en vez de darse por malo.

## Fase RED (obligatoria, nivel `critico`)

Trazas reales, con el comando exacto. Cada una es el test escrito ANTES del
código.

**T1 · vocabulario**, **T2 · lectura** y **T11 · emparejado** fallaron con el
mismo `ImportError: cannot import name 'vocabulario' from 'evals.revision'
(unknown location)`: el test existía y el módulo no.

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

Y las demás con el mismo patrón, el test antes que el módulo: **T7 bis**
(`10 failed in 0.28s`), **T11 bis** (`4 failed, 2 passed in 0.27s`) y la
**ampliación del emparejado** (`AttributeError: 'Copia' object has no attribute
'estrategia'`, `7 failed, 5 passed in 0.25s`).

## Mutación: 90 supervivientes, 74 con test y 16 justificados

La campaña completa (266 mutantes, 106 min) dejó **90 supervivientes**, casi
todos señalando lo mismo: el banco comprobaba QUÉ se escribe y casi nada de
**cómo se cuenta** ni de **cuándo se deja de escribir**, que es lo que prometen
R14 y R18. Un informe que suma mal es peor que no tenerlo: se lee igual de
convincente. De ahí 66 tests nuevos; **74 mueren con ellos** y los 16 restantes
son equivalentes, agrupados por razón y **cada uno con su comprobación
ejecutada**. Uno a uno, en `progress/mutacion_F-045.md`; ninguno `PENDIENTE`.

**Dos equivalencias eran FALSAS y las tumbó el reviewer ejecutando**: el 49
afirmaba que el mapa salía «byte a byte igual» sin `sort_keys` —y no: los
registros se montan en el orden de `CAMPOS`, que no es alfabético— y el 8 pasaba
por alto que la comprobación previa guardaría el libro ANTES de la copia de
seguridad, incumpliendo R16. Cerradas con test, y con ellas el 9, que era
dudoso: **ante la duda, test**; la prosa plausible no cuenta.

La mutación también encontró un fallo en un test MÍO: el de las copias contaba
NOMBRES de fichero, y la copia lleva la hora con precisión de minuto, así que dos
pasadas seguidas escribían el mismo nombre y no distinguía nada.

**Cómo se verificó el cierre**: repetir la campaña costaba otras dos horas y el
intento se degradó, así que cada superviviente se **reinyectó uno a uno** contra
la suite acotada (~11 s), la técnica que el inventario documenta para F-043; el
reviewer reprodujo 5 de 5 por su cuenta. **Y de paso, un desbloqueo del arnés**:
`harness/mutacion.py` lanza la suite con `PYTHONDONTWRITEBYTECODE=1` y
`test_C_un_mutante_nunca_se_juzga...` heredaba esa variable, con lo que la
**línea base de CUALQUIER campaña de este repositorio estaba roja** y `critico`
era inalcanzable. Arreglado; **hay que portarlo a `arnes-base`**.

## Lo que queda fuera y lo que el humano tiene que decidir

1. **DECISIÓN · `INPUTS.CASOS.tipologia`**: pestaña (lo implementado) o
   familia de documento (§3 literal, que rompe los 7 RES). Ver decisión 2. El
   reviewer confirma que **la spec es la que está mal**, no la implementación.
1 bis. **DECISIÓN · `IA1.lineas.codigo_imputacion` sale `?` en las 114 líneas**,
   segunda desviación de §3: la tabla plana no dice si la partida venía IMPRESA
   —en residuos no viene, en hormigón sí— y suponerlo sería inventar (R11). El
   precio: la mitad de EXTRACCIÓN del patrón 1 queda sin vigilar; su mitad de
   DECISIÓN sí se compara. Se cierra con una columna nueva en el Excel o
   aceptando la ceguera. Declarada en los avisos del informe de importación.
2. **DECISIÓN · los incrementos LER de los 7 casos RES**: el Excel los marca
   `EN ALBARAN` y el libro escrito a mano los tenía como sintéticas esperadas,
   así que RES-004 acaba esperándolos por los dos caminos a la vez (línea 2 de
   IA1 **y** sintética). Es ground truth contradictorio —el sistema no puede a
   la vez leerlo del papel y deducirlo—: hay que mirar el papel.
3. **Los documentos de entrada siguen sin copiarse**: los 59 salen como
   `fila_sin_fichero`, uno a uno; el plan se propone y no se renombra nada.
4. **DECISIÓN · `INPUTS.CONTRATO_LINEAS` y `CONDICIONES` no se alimentan**
   (§3), y el precio es mayor del que se anotó: IA3, IA4 y el E2E **no miden
   nada**. Las tres vías, medidas, en `progress/impl_F-045_contrato_lineas.md`.
5. **Fuera de alcance**: T13 bis (camino de lectura), T14 (`patrones.json`),
   T15 (`evals/README.md`) y T16 (fichas de arreglo). **T13 sí entró**, tras la
   pasada con LLM: sin ella el banco no era legible. La clasificación de cada
   defecto contra un patrón (R10) espera a T14.

## Lo que dijo la pasada con LLM (2026-09-16) y qué se arregló

Veredicto ROJO, pero **1295 de los 1456 fallos eran «obtenido None»**: ruido del
banco, no defectos del sistema. Dos causas, dos respuestas.

**Arreglado aquí (T13, R25 y R26).** IA1 e IA2 se comparaban por TODO el ground
truth: las columnas de control del banco —`caso_id`, la etiqueta que ponemos
nosotros, y `fichero_albaran`, el nombre que nosotros le dimos al papel— y los
campos que sv2 no extrae (`unidad`, `descuentos`, F-024). Ahora se podan con
`OBSERVABLES` y se **declaran** en sección propia. Regla: **observable es
exactamente lo que la proyección del proceso produce**, con un test que ata las
dos listas para que no diverjan.

**IA1 + IA2 pasa de 352 fallos críticos a 86**, y de 141 avisos a 60. Los 266
que se van son `caso_id` (129), `unidad` (72), `fichero_albaran` (57) y
`descuentos` (8); **los 86 que quedan son los defectos de verdad**, encabezados
por 27 `proveedor_nombre` y 27 `cantidad`. Desglose campo a campo en
`progress/impl_F-045_contrato_lineas.md`.

El informe también anunciaba los no observables como «campos sin clasificar en
`criticidad.json`» —el runner los colaba por ese parámetro—, que es otro problema
y con otro arreglo: ahora son dos secciones.

**Medido, NO arreglado: IA3, IA4 y E2E no miden nada.** Sin
`INPUTS.CONTRATO_LINEAS` IA3 no tiene contra qué valorar y sus ~865 fallos
hablan de la tabla vacía, no del código. Las tres vías, con su coste y la
recomendada, en **`progress/impl_F-045_contrato_lineas.md`**.

**Qué esperar de otra pasada** (no la lanzo yo: cuesta dinero): IA1 baja de 352
a 86 fallos y quedan a la vista los seis campos de arriba; IA2 sigue en 0; IA3,
IA4 y E2E **no cambian** hasta que se decida la vía de las líneas de contrato.
Con eso, otra pasada solo merece la pena si se quiere confirmar el recuento de
IA1: los defectos que destapa ya están nombrados aquí.

## Verificaciones MANUAL pendientes

**T19** (R31): validar la tabla de reparto, la política de vacíos y las cuatro
decisiones de arriba. **T20** (R32) ya se lanzó el 2026-09-16; otra pasada la
decide el humano con los números de la sección anterior.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite de la raíz) | **819 pasan, 0 fallan** |
| De ellos, de F-045 | **250** en 20 ficheros `tests/test_f045_*` |
| Cobertura de las líneas cambiadas | **97,9 %** (914/934), umbral 80 %, nivel `critico` |
| Tiempo de la suite | **165,20 s** |
| Mutación · campaña completa, sin muestreo | **266 mutantes, 176 muertos, 90 supervivientes**, 0 timeouts, 0 sin veredicto, 6381 s |
| Mutación · workers | **4**, uno por `git worktree`, con el `README.md` del humano en un stash |
| Mutación · tras los tests de T18 y del review | de los 90, **74 mueren** y **16 son equivalentes**, cada uno con su comprobación ejecutada; ninguno pendiente |
| Conversor e idempotencia | `python -m evals.conversor` en 0, sin hallazgos del barrido; segunda pasada de `revision` + `conversor` deja `git status` vacío |

### Lo que el volcado deja en el banco (medido, no estimado)

- 142 filas → **59 casos** (21 RES, 17 HOR, 10 GEN, 4 MOR, 3 FER, 2 GRA, 1 ALQ,
  1 COM), **11 de no regresión** y **48 de defecto conocido**. Fixtures: 59 en
  IA1, IA3, INPUTS y FINAL; 9 en IA2 (los que traen LER); 13 en IA4.
- IA1 recibe **114 líneas impresas**; solo **12 con unitario impreso** y **102
  con la celda vacía afirmada**, porque el precio sale del contrato o de una
  oferta: la separación extracción/valoración que pidió el humano.
- Rojos que nacen esperados, agrupados aparte: `combustible` (COM-001),
  `ferreteria` (3), `grava` (2), `minimo_1_tn` (9 RES), `incremento_por_ano` (6).
