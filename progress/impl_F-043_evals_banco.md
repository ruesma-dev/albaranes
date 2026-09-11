<!-- progress/impl_F-043_evals_banco.md -->
# F-043 · Siembra del banco de evals con el lote de residuos SALMEDINA

Siembra de **IA3, IA4 y RESULTADO_FINAL** (más `INPUTS`, que es su entrada) con
los siete albaranes de SALMEDINA. **No es implementación**: no se ha tocado ni
una línea de código de producción ni del arnés de evals.

## 1. Qué se sembró

Siete casos, tipología `Residuos`, `caso_id` con prefijo `RES` (convenio del
README). Ground truth: la tabla validada por el humano el **2026-09-11** y el
**§8** de `progress/revision_residuos_salmedina_20260819.md`.

| caso_id | Albarán | Obra | Contrato | Base esperada | Sintética LER | Total |
|---|---|---|---|---|---|---|
| RES-001 | SS-0000168 | 687 | CTSU24/0228 | C1 CAMBIO 6M3 · 120 € | 170201 · REVISIÓN | 120,00 € |
| RES-002 | SS-0003935 | 687 | CTSU24/0228 | C1 CAMBIO 6M3 · 120 € | 170107 · REVISIÓN | 120,00 € |
| RES-003 | SS-0000589 | 687 | CTSU24/0228 | C1 CAMBIO 6M3 · 120 € | 170802 · 51 € | 171,00 € |
| RES-004 | SS-0003967 | 687 | CTSU24/0228 | C1 CAMBIO 6M3 · 120 € | 170604 · 90 € | 210,00 € |
| RES-005 | SS-0801977 | 687 | CTSU24/0228 | C1 CAMBIO 6M3 · 120 € | 170604 · 90 € | 210,00 € |
| RES-006 | SS-0025146 | 691 | CTSU24/0402 | C1 CONTENEDOR 6 M3 · 136 € | 170904 · REVISIÓN | 136,00 € |
| RES-007 | SS-0026122 | 691 | CTSU24/0402 | (`?`) 9 M3 · 183 € OFERTA | 170802 · 77 € OFERTA | 260,00 € |

En los siete, `cantidad final = 1` y `unidad final = UD`: el 6 (o el 9) del
albarán es la **capacidad del contenedor**, no una cantidad de material (§8.1).
La partida esperada es `CI.03A.7` en los siete.

### Las dos exigencias del humano, dónde quedan escritas

1. **RES-007 entra con sus 260 € aunque dé ROJO por F-017.** La causa está
   escrita en el propio caso, en cuatro celdas de comentario (las tres tablas
   de `RESULTADO_FINAL` y la TABLA 1 de `IA3`): *«ROJO ESPERADO HASTA F-017, no
   es una regresión: la tarifa de 9 M3 (183 €) y su incremento (77 €) vienen de
   la OFERTA, no del contrato»*. Viaja al fixture
   `evals/fixtures/final/RES-007.json`: el rojo llega con nombre y apellidos.
2. **RES-001 se exige por CONCEPTO y PARTIDA, no solo por total.** El catálogo
   del caso incluye a la vez `C1 CAMBIO CONTENEDOR 6M3` (120 €) y el señuelo
   `C2 LLEVADA CONTENEDOR 6M3` (120 €), y el ground truth exige
   `codigo_producto_contrato = C1` y `codigo_partida_final = CI.03A.7`. Casar
   C2 da el mismo importe y **falla igual**: el acierto del total ya no tapa el
   error de match.

### Entradas (`INPUTS.xlsx`)

- **CASOS** (7): `tipologia=Residuos`, `origen=manual`, `ia_destino=IA3`.
- **LINEAS_ALBARAN** (7): `cantidad` 6,0 (9,0 en RES-007), `unidad` vacía (los
  siete traen `unidad_medida` null, §5 / F-024), sin precio ni importe
  impresos. `descripcion` = `<LER> <concepto>`, reconstruida de las columnas
  LER y Concepto del §1 — **entrada observada**, no ground truth.
- **CONTRATO_LINEAS** (32): seis líneas conocidas del CTSU24/0228 (CAMBIO,
  LLEVADA y los cuatro INCREMENTO LER de §2.1) y la única conocida del
  CTSU24/0402. Los códigos `C1…C6` son **sintéticos y neutros**: los reales de
  Sigrid no constan en el informe, el conversor necesita un código para enlazar
  IA3 con su línea de contrato, y neutros no le regalan pistas al LLM en T30.
- **CONDICIONES** (35): `fecha_albaran`, `numero_albaran`, `codigo_ler`,
  `volumen_m3` y `tamano_contenedor_contrato` por caso.

## 2. Dónde NO se inventó nada

Lo que el ground truth del humano no fija se dejó con el sentinela `?` (no se
compara) en vez de rellenarlo a ojo:

- `review_required` (IA3), `requiere_revision` (FINAL, salvo los tres del punto
  siguiente) y `linea_a_revision` (FINAL) → `?` en los siete.
- RES-007: `codigo_producto_contrato` y `precio_source` → `?`. La línea que el
  administrativo valora (CONTENEDOR 9 M3, de la OFERTA) **no existe** en el
  contrato y el vocabulario del libro (`contrato_db | pdf | null`) no sabe
  decir «oferta». Se anota en el comentario; lo resuelve F-017.
- `codigo_partida` de los dos incrementos que ningún caso del lote usa (LER
  170202 y 170302) → vacío: su partida real no consta.
- `match_method` = `semantic` en los seis con match (el método con el que casan
  los escenarios de F-036 para estos mismos albaranes); `?` en RES-007.

### El único sitio donde se fue más allá del §8, y por qué

Los siete casos declaran una **sintética de incremento LER** (`modifier_source
= gestion_residuos`, `rol_linea = incremento_residuos`). En RES-001, RES-002 y
RES-006 el contrato **no tarifa** ese LER, y esa sintética se declara con
precio e importe `REVISIÓN` y el documento con `requiere_revision = SI`.

Eso no sale del Excel del administrativo: sale de la **decisión del humano del
2026-08-22** (R16/R17 de F-036), recogida literalmente en el docstring de
`services/albaran-valoracion-persist/tests/test_f036_r25_salmedina_importes.py`:
*«los tres GANAN una línea sintética SIN precio y pasan a review_required. Eso
es lo QUERIDO […], no una regresión»*. Sin declararla, la comparación de
`lineas_anadidas` (que trata los sobrantes como **fallo**) daría ROJO a un
comportamiento que el humano ya aprobó.

**Es reversible en tres celdas** si el humano lo ve de otro modo: borrar las
filas de TABLA 3 de RES-001/002/006 en `RESULTADO_FINAL.xlsx`.

## 3. Lo que quedó fuera

- **IA1_extraccion.xlsx e IA2_contexto.xlsx: sin tocar.** Su entrada son los
  PDF de los albaranes (`evals/inputs/albaranes/<caso_id>.pdf`) y **no hay
  ninguno en local**: viven en el Blob de producción (`input/{document_id}.pdf`)
  y el directorio `evals/inputs/` ni existe. Sin el PDF, `corrida_completa`
  marca esos casos `OMITIDO` («no existe el fichero del albarán»), no ROJO.
- **IA4_conciliacion.xlsx: sin tocar, y es lo correcto.** IA4 evalúa las líneas
  que IA3 dejó **sin match o sin precio**; aquí las siete casan contra el
  contrato, así que no hay nada que conciliar. El runner las marca `OMITIDO` y
  la fase queda `NO_EVALUABLE`. Forzar una fila sería inventar ground truth.
- **`evals/criticidad.json`: sin tocar.** El informe avisa de tres campos «sin
  clasificar» (`cantidad_final`, `caso_id`, `cif`). No relajan nada —sin
  clasificar se tratan como críticos— y tocar la criticidad es diseño del
  banco, no parte de sembrarlo.

## 4. Verificación ejecutada

### Conversor (fixtures + barrido de datos sensibles)

```
$ python -m evals.conversor
6 libro(s) convertidos, 27 fichero(s) escritos (FINAL: 7, IA1: 0, IA2: 0, IA3: 7, IA4: 0, INPUTS: 7)
```

21 fixtures nuevos (7 × `inputs`, `IA3`, `final`) + los 6 `_indice.json`
actualizados con el `sha256` de su libro. El barrido de C3 bis corre **dentro**
del conversor y no encontró nada: si hubiera saltado, no se habría escrito ni
un fichero.

### Runner determinista (cero llamadas LLM, cero coste)

```
$ python -m evals.runner --feature F-043 --informes <scratchpad>
ROJO · informe en <scratchpad>/evals_F-043.md          (exit 1)
```

Se lanzó **sin `--con-llm`** y con el informe fuera de `progress/`, para no
ocupar el nombre `progress/evals_F-043.md` que T30 tiene que producir.

**El banco carga y compara**: IA3 7 evaluados, E2E 7 evaluados, IA4 7 omitidos.
Y cuadran todos los campos comparables salvo los del punto 5: partida
`CI.03A.7`, precios 120/136, `precio_source = contrato_db`, `match_method =
semantic`, `casa_con_contrato`, `modifier_source`, `rol_linea` y el sentinela
`REVISIÓN` de los tres sin tarifa.

## 5. Los ROJOS y su causa (lo que falta para que T30 sea ejecutable)

**Causa única de 6 de los 7 rojos, y NO es un defecto de sv6**: todos los
importes salen multiplicados por 6 (o por 9).

```
RES-001 · FALLO · FINAL.lineas[1].importe_final: esperado 120, obtenido 720.0
RES-003 · FALLO · FINAL.datos_generales[].total_valorado_esperado: esperado 171, obtenido 1026.0
RES-004 · FALLO · FINAL.lineas_anadidas[1].importe: esperado 90, obtenido 540.0
RES-006 · FALLO · FINAL.lineas[1].importe_final: esperado 136, obtenido 816.0
RES-007 · FALLO · FINAL.lineas_anadidas[1].cantidad: esperado 1, obtenido 9.0
```

720 = 6 × 120, 1026 = 6 × 171, 816 = 6 × 136, 693 = 9 × 77. Es la regla 4.bis
de residuos (`calcular_contenedores_residuos`) que **nunca llega a ejecutarse**.

**El agujero, con nombre y línea.** La regla lee `contexto_linea.volumen_m3`
(y `codigo_ler`, y `contenedores`). Los dos adaptadores que fabrican el
contexto para el banco —`evals/procesos/sv6_build.py` →
`construir_envelope_estimulado()` y `evals/procesos/sv5_valoracion.py` →
`construir_contexto()`— escriben solo `{"tipo_familia", "rol_linea",
"descripcion_extendida"}`. Sin `volumen_m3` la regla sale por
`residuos_sin_volumen_m3`, cae a `cantidad_convertida` (6, porque la unidad del
albarán es null) y multiplica. **Afecta igual al modo determinista y a la
pasada `--con-llm`**: es el mismo código. Comparar con
`tests/f036_escenarios_residuos.py`, que sí construye el `ContextoLinea`
completo y por eso sus escenarios dan 120/171/210/136.

**Falta para T30, exactamente:**

1. **Propagar las CONDICIONES al `contexto_linea`** en esas dos funciones. El
   banco ya trae los valores sembrados (`volumen_m3`, `codigo_ler`,
   `tamano_contenedor_contrato`): solo falta el mapeo. El LEEME de `INPUTS`
   anticipa justo eso («CONDICIONES: parámetros del caso […] p.ej.
   `tamano_contenedor_contrato=6`»), así que el libro ya lo contemplaba y el
   adaptador no. **NO se ha tocado**: cambia el contrato del banco para todas
   las tipologías y es decisión del humano, no de una siembra.
2. **Los PDF de los siete albaranes en `evals/inputs/albaranes/RES-00N.pdf`**
   si se quieren las fases IA1 e IA2 que T30 exige (`FASES: IA1,IA2,IA3,IA4,E2E`).
   Hoy no están en local. Sin ellos, T30 puede dar `VEREDICTO: VERDE` en IA3 /
   IA4 / E2E, pero IA1 e IA2 saldrán con los 7 casos `OMITIDO`, que es
   `NO_EVALUABLE`, no verde.
3. **Claves LLM en el entorno** (`OPENAI_API_KEY` / `GEMINI_API_KEY` /
   `ANTHROPIC_API_KEY`): `comprobar_claves` aborta antes de consumir un caso.
4. **F-017** para que RES-007 pueda dar verde; hasta entonces su rojo es el
   recordatorio que el humano pidió.

### Discrepancia entre libros que conviene arreglar (no bloquea)

El encabezado de `RESULTADO_FINAL` dice que el precio sale de
`contrato / albarán / PDF contrato`, pero el sistema proyecta el vocabulario de
`IA3` (`contrato_db | pdf | albaran`, ver `MAPA_PRECIO_SOURCE`). Se sembró
`contrato_db`, que es el que compara verde: si el administrativo sigue su
propio encabezado y escribe «contrato», tendrá un rojo falso. Se arregla
cambiando el encabezado o admitiendo el sinónimo en el comparador.

## 6. Ficheros tocados

- `evals/ground_truth/INPUTS.xlsx`, `IA3_valoracion.xlsx`,
  `RESULTADO_FINAL.xlsx` — **NO versionados** (`.gitignore:18 *.xlsx`,
  verificado con `git check-ignore -v`). `git ls-files "*.xlsx"` sale vacío.
- `evals/fixtures/{inputs,IA3,final}/RES-00{1..7}.json` — 21 nuevos, **sí
  versionados**, tras el barrido; más 3 `_indice.json` modificados.
- `progress/impl_F-043_evals_banco.md` — este informe.

Sin cambios en `services/`, `harness/` ni en `evals/*.py`.

## 7. Evidencias

| Evidencia | Valor |
|---|---|
| Libros convertidos / fixtures escritos | 6 libros → 27 ficheros (21 casos + 6 índices) |
| Casos evaluados por el runner determinista | IA3 7/7, E2E 7/7, IA4 0/7 (omitidos) |
| Veredicto del runner determinista | **ROJO**, exit 1 — 5 causas identificadas, ninguna nueva |
| Barrido de datos sensibles (C3 bis) | 0 hallazgos |
| `.xlsx` en el índice de git | 0 |
| `bash harness/init.sh` | ver cierre |

**Fase RED**: no aplica — esta tarea no escribe código ni tests, su artefacto
es ground truth. La evidencia equivalente es que el banco **arranca en ROJO**
con causas trazadas: uno que naciera verde estaría midiendo el sistema contra
sí mismo. **Mutación y cobertura de líneas cambiadas**: no aplican, no hay
líneas de código Python cambiadas (solo fixtures JSON de datos).
