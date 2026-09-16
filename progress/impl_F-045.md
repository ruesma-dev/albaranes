<!-- progress/impl_F-045.md -->
# F-045 · Implementación de la CAPA 1 (T1–T12)

Volcado de la revisión manual del humano al banco de evals. **T13 en adelante
(deuda del banco, catálogo de patrones, fichas de arreglo) NO entran aquí.**

## Qué cambió

El banco pasa de **7 casos** —una familia, un proveedor— a **59 casos** de
ocho familias y 18 proveedores, con `python -m evals.revision` como escalón
nuevo ANTES de los libros: tabla plana → libros de `ground_truth/` →
`evals.conversor` → fixtures. El conversor sigue siendo la única puerta a los
fixtures y el único sitio donde corre el barrido de datos sensibles.

### Ficheros nuevos (paquete `evals/revision/`)

| Fichero | Qué hace |
|---|---|
| `vocabulario.json` + `.py` | la tabla de §5 bis, los tres ejes de origen y la política de vacíos por columna. Lo que no reconoce, ABORTA |
| `modelos.py` | `FilaPlana`, `LineaRevisada`, `CasoRevisado`, `InformeImportacion`. Puro |
| `lectura.py` | del `.xlsx` a `list[FilaPlana]`, localizando columnas por NOMBRE |
| `reparto.py` | **el núcleo**: la tabla de reparto de §3, los caso_id, los criterios de residuos |
| `albaranes.py` | del nombre del fichero al caso: escalera de estrategias y los fallos ruidosos |
| `escritura.py` | copia previa, pestañas nuevas y fusión conservadora con lo que ya había |
| `informe.py`, `__main__.py` | el informe de R14 y la CLI |
| `evals/mapa_casos.json` | versionado: `caso_id` ↔ código ↔ nombre ↔ formato ↔ familia ↔ gemelo |
| 19 ficheros `tests/test_f045_*` | 238 tests |

### Ficheros modificados

- `evals/conversor.py`: `Grava` y `Ferreteria` en `TIPOLOGIAS` (su único cambio).
- `tests/conftest.py`: `TIPOLOGIAS` se importa del conversor en vez de copiarse
  —era una copia, y ampliar el contrato dejó 20 tests de F-011 en rojo—.
- `tests/test_mutacion_prueba_de_verdad.py`: ver «El desbloqueo» más abajo.
- Los seis libros de `ground_truth/` y los 264 fixtures (regenerados).

## Decisiones de diseño

1. **Fusión conservadora, no volcado** (R8 + R17). El importador actualiza las
   filas de sus casos pero **nunca degrada a `?` una celda con valor ya
   afirmado**, y conserva las filas que él no genera. Los 7 casos RES están
   TAMBIÉN en el Excel: un volcado a pelo los habría barrido en la primera
   pasada. Verificado sobre RES-001, que conserva `SS-0000168`, su
   `match_method` semántico, su contexto y sus 6 líneas de contrato.
2. **`INPUTS.CASOS.tipologia` lleva la PESTAÑA, no la familia de documento.**
   Desviación medida de §3, **pendiente de que la cierre el humano**:
   `MAPA_TIPO_FAMILIA` de `evals/procesos/{sv5_valoracion,sv6_build}.py` está
   indexado por pestaña (`Residuos` → `residuos`), así que escribir la familia
   deja a TODOS los casos —incluidos los 7 que ya funcionaban— en
   `tipo_familia='otro'`, que es la clasificación equivocada que F-043 vino a
   arreglar. Y esos dos ficheros §2 los declara intocables. La familia no se
   pierde: va a `mapa_casos.json` y agrupada en el informe, que es donde R6
   pide que se vea.
3. **El emparejado es una escalera de estrategias** (`exacto` → `subcadena` →
   `sin_ceros`), tras la medición del líder sobre los 133 ficheros reales: la
   regla de la spec dejaba 24 de 59 códigos sin fichero. La normalización ya
   resolvía puntos de millar y barras; faltaba buscar el código dentro del
   nombre y los ceros a la izquierda —y `sin_ceros` quita SOLO los de la
   izquierda: `SS-0801977` y `SS-0001977` difieren por dentro—.
4. **La ambigüedad no se resuelve sola.** Un fichero cuyo nombre contiene dos
   códigos —existe: un PDF con dos albaranes— sale como
   `fichero_varios_codigos` y no se asigna a ninguno.
5. **Renombrar es opt-in** (`--renombrar`): el plan se propone en el informe
   con la estrategia de cada emparejado, porque deshacer un renombrado
   equivocado es caro y un caso casado con el papel de otro no lo ve nadie.
6. **Un libro que no cambia no se guarda**: cada guardado le mueve el sha256 y
   dejaba 264 fixtures «modificados» sin que cambiara un dato (R18).
7. **`?` jamás en `INPUTS`**, que es una ENTRADA y no una expectativa: el
   sentinela viajaría como texto literal dentro de la carga que lee sv5.
8. **El descuento se traduce a porcentaje** (0,4 → `40`), que es lo que consume
   la fórmula canónica de ARCHITECTURE §13. Declarado en `vocabulario.json`.

## Fase RED (obligatoria, nivel `critico`)

Trazas reales, con el comando exacto. Cada una es el test escrito ANTES del
código.

**T1 · vocabulario** — `python -m pytest tests/test_f045_r5_r6_vocabulario.py -q`

```
tests\test_f045_r5_r6_vocabulario.py:14: in <module>
    from evals.revision import vocabulario as voc
E   ImportError: cannot import name 'vocabulario' from 'evals.revision' (unknown location)
1 error in 0.34s
```

**T4 · impresa vs deducida** — `python -m pytest tests/test_f045_r3_impresa_vs_deducida.py -q`

```
FFFFF                                                                    [100%]
>       tablas, _ = repartir(...)
E       AttributeError: module 'evals.revision.reparto' has no attribute 'repartir'
5 failed in 0.25s
```

**T7 bis · criterios de residuos** — `pytest tests/test_f045_r12bis_residuos.py`:
`10 failed in 0.28s`, empezando por
`test_f045_r12bis_el_minimo_se_aplica_a_lo_que_se_pesa`.

**T11 bis · gemelos** — `python -m pytest tests/test_f045_r22_gemelos.py -q`

```
FAILED ...::test_f045_r22_pdf_e_imagen_del_mismo_codigo_dan_dos_casos
FAILED ...::test_f045_r22_el_gemelo_hereda_el_mismo_ground_truth
4 failed, 2 passed in 0.27s
```

**Ampliación del emparejado** — `python -m pytest tests/test_f045_r20_r21_emparejado.py -q`

```
E       AttributeError: 'Copia' object has no attribute 'estrategia'
7 failed, 5 passed in 0.25s
```

## Mutación: 90 supervivientes, 71 cerrados con test y 19 justificados

La campaña completa (266 mutantes, 106 min) dejó **90 supervivientes**, y casi
todos señalaban lo mismo: el banco comprobaba QUÉ se escribe y casi nada de
**cómo se cuenta** ni de **cuándo se deja de escribir**, que es justamente lo
que prometen R14 y R18. Un informe que suma mal es peor que no tener informe:
se lee igual de convincente.

De ahí 66 tests nuevos en dos ficheros (`test_f045_r14_recuento_y_convenios.py`
y `test_f045_r17_r18_fusion.py`) más refuerzos en los de la CLI. **74 de los 90
mutantes mueren con ellos**; los 16 restantes son equivalentes, agrupados por la
razón que comparten y **cada uno con su comprobación ejecutada**. El detalle,
uno a uno, en `progress/mutacion_F-045.md`; ninguno queda `PENDIENTE`.

**Dos de las equivalencias eran FALSAS y las tumbó el reviewer ejecutando**: el
49 afirmaba que el mapa salía «byte a byte igual» sin `sort_keys` —y no, los
registros se montan en el orden de `CAMPOS`, que no es alfabético—, y el 8 pasaba
por alto que la pasada de comprobación guardaría el libro ANTES de la copia de
seguridad, incumpliendo R16. Los dos se cierran con test, y con ellos el 9, que
era dudoso: la regla es **ante la duda, test**, y la prosa plausible no cuenta.

La mutación también encontró un fallo en un test MÍO: el de las copias de
seguridad contaba NOMBRES de fichero, y la copia lleva la hora con precisión de
minuto, así que dos pasadas seguidas escribían el mismo nombre y el test no
distinguía nada. Ahora lee el recuento del informe.

**Cómo se verificó el cierre.** Repetir la campaña entera costaba otras dos
horas y el intento se degradó (cinco horas en el primer fichero, un worker
bloqueado), así que cada superviviente se **reinyectó uno a uno** contra la
suite acotada a F-045, ~11 s cada uno. Es la técnica que el inventario ya
documenta para F-043.

## El desbloqueo: la línea base de TODA campaña de mutación estaba roja

`harness/mutacion.py` lanza la suite con `PYTHONDONTWRITEBYTECODE=1`, y
`test_C_un_mutante_nunca_se_juzga_con_el_bytecode_del_anterior` heredaba esa
variable en sus subprocesos: `__pycache__` quedaba vacío, su assert en rojo y
—por ser línea base— la campaña abortaba antes de generar un mutante
(«LÍNEA BASE EN ROJO en .: la suite falla SIN mutar nada»).

No es de F-045: muerde a cualquier feature de este repositorio y hace
inalcanzable el nivel `critico`. **Es mejora del arnés y hay que portarla a
`arnes-base`** (regla de propagación de `CLAUDE.md`). Detalle en
`progress/inventario_mutacion_F-039.md`.

## Lo que queda fuera y lo que el humano tiene que decidir

1. **DECISIÓN · `INPUTS.CASOS.tipologia`**: pestaña (lo implementado) o
   familia de documento (§3 literal, que rompe los 7 RES). Ver decisión 2. El
   reviewer confirma que **la spec es la que está mal**, no la implementación.
1 bis. **DECISIÓN · `IA1.lineas.codigo_imputacion` sale `?` en las 114 líneas**,
   segunda desviación de §3. La tabla plana no tiene columna que diga si la
   partida venía IMPRESA —en residuos no viene, en hormigón sí— y suponerlo
   sería inventar (R11). El precio: la mitad de EXTRACCIÓN del patrón 1 queda
   sin vigilar; su mitad de DECISIÓN sí se compara. Se cierra con una columna
   nueva en el Excel o aceptando la ceguera. Declarada en los avisos del
   informe de importación.
2. **DECISIÓN · los incrementos LER de los 7 casos RES**: el Excel los marca
   `EN ALBARAN`, mientras que el libro escrito a mano los tenía como
   sintéticas esperadas. Con la fusión conservadora, RES-004 acaba
   esperándolos por los dos caminos a la vez (línea 2 de IA1 **y** sintética),
   y eso es ground truth contradictorio: el sistema no puede a la vez leerlo
   del papel y deducirlo. Hay que mirar el papel y decidir.
3. **Los documentos de entrada siguen sin copiarse**: los 59 salen como
   `fila_sin_fichero`, uno a uno; el plan se propone y no se renombra nada.
4. **`INPUTS.CONTRATO_LINEAS`, `CONDICIONES` e `IA3` TABLA 3 no se alimentan**
   (§3): sin líneas de contrato los 52 casos nuevos solo son evaluables con
   LLM; la corrida determinista sigue viviendo de los 7 RES.
5. **Fuera de alcance por diseño**: T13/T13 bis (observables y camino de
   lectura), T14 (`patrones.json`), T15 (`evals/README.md`), T16 (fichas de
   arreglo). La clasificación de cada defecto contra un patrón (R10) espera a
   T14; hoy el informe solo reparte no regresión / defecto conocido.

## Verificaciones MANUAL pendientes

- **T19** (R31): validar la tabla de reparto, la política de vacíos y las dos
  decisiones de arriba.
- **T20** (R32): pasada `--con-llm`, que cuesta dinero y lanza el humano.

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (suite de la raíz) | **807 pasan, 0 fallan** |
| De ellos, de F-045 | **238** en 19 ficheros `tests/test_f045_*` |
| Cobertura de las líneas cambiadas | **98,2 %** (896/912), umbral 80 %, nivel `critico` |
| Tiempo de la suite | **71,42 s** |
| Mutación · campaña completa, sin muestreo | **266 mutantes, 176 muertos, 90 supervivientes**, 0 timeouts, 0 sin veredicto, 6381 s |
| Mutación · workers | **4**, uno por `git worktree`, con el `README.md` del humano en un stash |
| Mutación · tras los tests de T18 y del review | de los 90, **74 mueren** y **16 son equivalentes**, cada uno con su comprobación ejecutada; ninguno pendiente |
| Conversor | `python -m evals.conversor` en 0, sin hallazgos del barrido |
| Idempotencia medida | segunda pasada de `revision` + `conversor`: `git status` vacío |

### Lo que el volcado deja en el banco (medido, no estimado)

- 142 filas → **59 casos**: 21 RES, 17 HOR, 10 GEN, 4 MOR, 3 FER, 2 GRA, 1 ALQ, 1 COM.
- **11 casos de no regresión** (deben salir VERDES) y **48 de defecto conocido**.
- Fixtures: 59 en IA1, IA3, INPUTS y FINAL; 9 en IA2 (los que traen LER); 13 en IA4.
- IA1 recibe **114 líneas impresas**; de ellas solo **12 con unitario impreso**
  y **102 con la celda vacía afirmada** porque el precio sale del contrato o de
  una oferta: es la separación extracción/valoración que pidió el humano.
- `match_method`: 27 afirmados (`no_match` de las líneas NUEVA) y 87 `?`.
- Rojos que nacen esperados, agrupados aparte: `combustible` (COM-001),
  `ferreteria` (3), `grava` (2), `minimo_1_tn` (9 casos RES),
  `incremento_por_ano` (6 casos RES).
