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

### Ficheros modificados

- `evals/conversor.py`: `Grava` y `Ferreteria` en `TIPOLOGIAS` (su único cambio).
- `tests/conftest.py`: `TIPOLOGIAS` se importa del conversor en vez de copiarse.
- `tests/test_mutacion_prueba_de_verdad.py`: ver «El desbloqueo» más abajo.
- Los seis libros de `ground_truth/` y los 264 fixtures (regenerados).

## Decisiones de diseño

1. **Fusión conservadora, no volcado** (R8 + R17). El importador actualiza las
   filas de sus casos pero **nunca degrada a `?` una celda con valor ya
   afirmado**, y conserva las filas que él no genera. Los 7 casos RES están
   TAMBIÉN en el Excel, así que un volcado a pelo los habría barrido en la
   primera pasada. Verificado: RES-001 conserva `SS-0000168`, su
   `match_method` semántico, sus filas `tipo_familia`/`volumen_m3` y sus 6
   líneas de contrato.
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
   resolvía los puntos de millar y las barras; faltaba buscar el código dentro
   del nombre y contemplar los ceros a la izquierda. `sin_ceros` quita SOLO
   los de la izquierda: `SS-0801977` y `SS-0001977` difieren por dentro.
4. **La ambigüedad no se resuelve sola.** Un fichero cuyo nombre contiene dos
   códigos del Excel —existe: un PDF con dos albaranes— sale como
   `fichero_varios_codigos` y no se asigna a ninguno.
5. **Renombrar es opt-in** (`--renombrar`). El plan se propone en el informe
   con la estrategia de cada emparejado: deshacer un renombrado equivocado es
   caro y un caso casado con el papel de otro no lo detecta nadie.
6. **Un libro que no cambia no se guarda.** Cada guardado reescribe el zip del
   `.xlsx` y le mueve el sha256, con lo que dos importaciones seguidas dejaban
   264 fixtures «modificados» sin que hubiera cambiado un dato (R18).
7. **`?` jamás en `INPUTS`.** Es una ENTRADA, no una expectativa: el sentinela
   viajaría como texto literal dentro de la carga que lee sv5.
8. **El descuento se traduce a porcentaje** (0,4 → `40`): es lo que consume la
   fórmula canónica de ARCHITECTURE §13. Declarado en `vocabulario.json`.

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

**T5 · clasificación** — `python -m pytest tests/test_f045_r9_r10_clasificacion.py -q`

```
>       grupos = reparto.clasificar(casos)
E       AttributeError: module 'evals.revision.reparto' has no attribute 'clasificar'
1 failed, 6 passed in 0.21s
```

**T7 bis · criterios de residuos** — `python -m pytest tests/test_f045_r12bis_residuos.py -q`

```
FAILED ...::test_f045_r12bis_el_minimo_se_aplica_a_lo_que_se_pesa
FAILED ...::test_f045_r12bis_el_movimiento_de_contenedor_no_se_toca
FAILED ...::test_f045_r12bis_el_minimo_marca_el_caso_como_criterio_pendiente
FAILED ...::test_f045_r12bis_los_tres_criterios_estan_declarados_en_el_vocabulario
10 failed in 0.28s
```

**T11 bis · gemelos** — `python -m pytest tests/test_f045_r22_gemelos.py -q`

```
FAILED ...::test_f045_r22_pdf_e_imagen_del_mismo_codigo_dan_dos_casos
FAILED ...::test_f045_r22_el_gemelo_de_imagen_apunta_a_su_hermano
FAILED ...::test_f045_r22_el_gemelo_hereda_el_mismo_ground_truth
FAILED ...::test_f045_r22_sin_gemelos_no_se_crea_ningun_caso_extra
4 failed, 2 passed in 0.27s
```

**Ampliación del emparejado** — `python -m pytest tests/test_f045_r20_r21_emparejado.py -q`

```
E       AttributeError: 'Copia' object has no attribute 'estrategia'
FAILED ...::test_f045_r20_el_codigo_en_medio_del_nombre_se_encuentra
FAILED ...::test_f045_r21_un_fichero_con_dos_albaranes_no_se_asigna_a_ninguno
7 failed, 5 passed in 0.25s
```

## El desbloqueo: la línea base de TODA campaña de mutación estaba roja

`harness/mutacion.py` lanza la suite con `PYTHONDONTWRITEBYTECODE=1`, y
`test_C_un_mutante_nunca_se_juzga_con_el_bytecode_del_anterior` heredaba esa
variable en sus dos subprocesos: `__pycache__` quedaba vacío, su assert en
rojo y —por ser línea base— la campaña abortaba antes de generar un mutante.

```
LÍNEA BASE EN ROJO en .: la suite falla SIN mutar nada.
Campaña abortada sin escribir informe: sobre una base roja TODO mutante
saldría «muerto» y el cero de supervivientes sería falso.
  Tests que fallan sin mutar:
    - tests/test_mutacion_prueba_de_verdad.py::test_C_un_mutante_nunca_se_juzga_con_el_bytecode_del_anterior
```

No es de F-045: muerde a cualquier feature de este repositorio y hace
inalcanzable el nivel `critico`. **Es mejora del arnés y hay que portarla a
`arnes-base`** (regla de propagación de `CLAUDE.md`).

## Lo que queda fuera y lo que el humano tiene que decidir

1. **DECISIÓN · `INPUTS.CASOS.tipologia`**: pestaña (lo implementado) o
   familia de documento (§3 literal, que rompe los 7 RES). Ver decisión 2.
2. **DECISIÓN · los incrementos LER de los 7 casos RES**: el Excel los marca
   `EN ALBARAN`, mientras que el libro escrito a mano los tenía como
   sintéticas esperadas. Con la fusión conservadora, RES-004 acaba
   esperándolos por los dos caminos a la vez (línea 2 de IA1 **y** sintética),
   y eso es ground truth contradictorio: el sistema no puede a la vez leerlo
   del papel y deducirlo. Hay que mirar el papel y decidir.
3. **Los documentos de entrada siguen sin copiarse**: los 59 casos salen como
   `fila_sin_fichero` en el informe, uno a uno. El plan de renombrado se
   propone pero **no se ha renombrado nada**.
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
| Tests ejecutados (suite de la raíz) | **742 pasan, 0 fallan** |
| De ellos, de F-045 | **173** en 12 ficheros `tests/test_f045_*` |
| Cobertura de las líneas cambiadas | **97,4 %** (888/912), umbral 80 %, nivel `critico` |
| Tiempo de la suite | **123,56 s** |
| Mutación | PENDIENTE |
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
