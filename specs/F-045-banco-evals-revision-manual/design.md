<!-- specs/F-045-banco-evals-revision-manual/design.md -->
# F-045 · Diseño

## 1. Encaje y límite de servicio

Todo ocurre en `evals/`, la herramienta de banco de pruebas del monorepo. **No
se toca ni una línea de sv1–sv6 ni de `ruesma_comun`**: F-045 siembra la red,
no arregla lo que la red detecta. La ficha declara `servicios: [sv2, sv5,
sv6]`; son los servicios **vigilados** por los casos, no los modificados
(decisión abierta D6).

El flujo existente no cambia de forma: revisión manual → **libros de
`ground_truth/`** → `evals.conversor` → `evals/fixtures/*.json` → `evals.runner`.
Esta feature añade un escalón **antes** de los libros y deja el conversor como
única puerta hacia los fixtures (y por tanto único sitio donde corre el barrido
de C3 bis).

Reglas de dominio que gobiernan el reparto: `docs/ARCHITECTURE.md` §6
(`codigo_imputacion` = partida impresa; `codigo_partida_final` = decisión del
matching), §7 (sintéticas y derivadas), §13 (`precio` bruto, `precio_neto` =
importe de la línea; el unitario leído manda) y §14 (la familia la decide IA1).

## 2. Ficheros

### A crear

| Ruta | Qué es | Capa |
|---|---|---|
| `evals/revision/__init__.py` | paquete del importador | — |
| `evals/revision/modelos.py` | `FilaPlana`, `LineaRevisada`, `CasoRevisado`, `InformeImportacion` | dominio |
| `evals/revision/vocabulario.py` | carga y valida `vocabulario.json`; normaliza etiquetas | dominio |
| `evals/revision/reparto.py` | **el núcleo**: de filas planas a las tablas de los seis libros | dominio (puro) |
| `evals/revision/albaranes.py` | emparejado caso ↔ PDF y plan de copia | dominio (puro) |
| `evals/revision/lectura.py` | Excel plano → `list[FilaPlana]` (openpyxl) | infraestructura |
| `evals/revision/escritura.py` | tablas → los seis libros, con copia previa | infraestructura |
| `evals/revision/__main__.py` | CLI `python -m evals.revision` | entrada |
| `evals/revision/vocabulario.json` | familias, orígenes de línea y de precio aceptados | datos |
| `evals/mapa_casos.json` | clave natural (CIF + código normalizado) → `caso_id` | datos |
| `evals/patrones.json` | catálogo de los nueve patrones y sus decisiones | datos |
| `tests/test_f045_r*.py` | un fichero por bloque de requisitos | tests |

### A modificar

- `evals/procesos/sv2_extraccion.py`: constante `OBSERVABLES` para las tablas
  `cabeceras`, `lineas` y `contexto`, igual que la de `sv6_build.py` (R23).
- `evals/runner.py`: `_comparar_tablas_de` pasa esos observables y acumula
  `campos_no_observables`, que hoy descarta para IA1/IA2 (R23, R24).
- `evals/README.md`: el comando nuevo, el catálogo de patrones y qué se
  versiona del importador.
- `harness/features.json`: las fichas de arreglo de §7 (R29).

### Que NO se tocan

`evals/conversor.py`, `evals/comparador.py`, `evals/criticidad.py|json`,
`evals/barrido.py`, `evals/modelos.py`, `evals/procesos/sv5_valoracion.py`,
`evals/procesos/sv6_build.py`, y **todo** `services/`. Tentaciones concretas:
no se añade un campo `unidad` a `LineaAlbaran` (eso es F-024) ni se cambia el
formato de los libros (rompería los 7 casos RES ya sembrados).

## 3. La tabla de reparto (NORMATIVA)

La tabla plana tiene una fila por **línea de albarán** y mezcla lo leído del
papel con lo valorado. Medido el 2026-09-15 (142 filas con datos, 59 códigos de
albarán, 10 etiquetas de familia; puede haber crecido).

| Columna plana | Destino | Por qué |
|---|---|---|
| `codigo alabran` | clave natural del caso (§4); `IA1.cabeceras.numero_albaran` = `?` | el código del humano no es el literal impreso (`0000168` vs `SS-0000168`): compararlo daría rojo falso (R11) |
| `Tipo de albaran` | pestaña de los seis libros + `INPUTS.CASOS.tipologia` | es la familia del catálogo, traducida por `vocabulario.json` (R6) |
| `cif` | `RESULTADO_FINAL.datos_generales.CIF`; en IA1 `?` | el CIF correcto es el del proveedor identificado, no siempre el impreso; así lo tienen ya los 7 casos RES |
| `nombre empresa (el bueno…)` | `IA1.cabeceras.proveedor_nombre` **y** `FINAL.proveedor` | es la razón social con la que se guarda, y coincide con lo impreso en los casos ya sembrados |
| `codigo obra` | `FINAL.datos_generales.obra`; en IA1 `obra_codigo` y `obra_nombre` = `?` | deducir la obra NO es extraer: el papel a menudo no la trae (R12) |
| `fecha` | `IA1.cabeceras.fecha` **y** `FINAL.fecha` | impresa en el papel |
| `codigo contrato` | `FINAL.datos_generales.contrato_elegido` + `INPUTS.CASOS.contrato_codigo` | el contrato no está en el papel: lo elige la valoración |
| `partida` | fila impresa con partida en el papel → `IA1.lineas.codigo_imputacion`; **siempre** → `IA3.lineas_valoradas.codigo_partida_final` y `FINAL.lineas.partida_final` | §6 de la arquitectura; el patrón 1 vive en la decisión, no solo en la lectura |
| `linea esta en albaran o deducida` | **discrimina la fila entera**: `EN ALBARAN` → `IA1.lineas` + `FINAL` TABLA 2; `DEDUCIDA …` → `IA3` TABLA 2 (sintéticas esperadas) + `FINAL` TABLA 3 | una línea deducida no existe en el papel: escribirla en IA1 exigiría a IA1 inventarla |
| `linea en contrato de sigrid o nueva` | `EN CONTRATO` → `IA3.codigo_producto_contrato` con su `match_method`; `NUEVA` → sin match, el caso pasa a `IA4` (`concilia`); `OFERTA` → `precio_source=oferta` (F-017) | |
| `concepto` | `IA1.lineas.descripcion_esperada` (campo laxo) y `FINAL.lineas.descripcion` | |
| `cantidad` | fila impresa → `IA1.lineas.cantidad`; fila deducida → `IA3` sintéticas `.cantidad`; siempre `FINAL.cantidad_final` | |
| `unidad` | `FINAL.lineas.unidad_final`; en IA1 se escribe y el runner la declara **no observable** | sv2 no extrae unidad hoy (F-024); exigirla en IA1 sería un rojo permanente (R24) |
| `precio unitario` + `unitario viene en…` | `ALBARAN` → `IA1.lineas.precio_unitario` (bruto) y `IA3.precio_source=albaran`; `CONTRATO` u `OFERTA` → IA1 **vacío** (null afirmado, R10) y `IA3.precio_unitario_final` + `precio_source` | **la separación extracción/valoración que pide el humano** |
| `importe` + `importe viene en…` | `ALBARAN` → `IA1.lineas.importe` (que es `precio_neto`, §13); valorado → `IA3.importe_calculado` y `FINAL.importe_final` | §13: el importe leído se transcribe, no se recompone |
| `descuento` | `IA1.lineas.descuentos` | es dato del papel y entra en la fórmula de §13 |
| `LER o codigo linea o producto` | familia `residuos` → `IA2.contexto` (`campo_contexto=codigo_LER`); resto → `IA3.codigo_producto_contrato` | el LER es contexto de línea, no dato de cabecera |
| `Comentarios` | columna `comentario` del libro (laxo, no se compara) **y** patrón en `evals/patrones.json` | es el diagnóstico de hoy, no el resultado esperado |

Lo que la tabla plana **no** alimenta hoy: `INPUTS.CONTRATO_LINEAS` (las líneas
del contrato no están en la revisión) y `IA3` TABLA 3 (sintéticas prohibidas).
Se dejan vacías y el informe lo dice: sin líneas de contrato los casos nuevos
solo son evaluables en la corrida **con LLM**; la determinista seguirá viviendo
de los 7 casos RES hasta que el humano rellene `INPUTS`.

## 4. Firmas principales

```python
# evals/revision/reparto.py  (puro: dict in, dict out)
def clave_natural(fila: FilaPlana) -> str                  # CIF + código normalizado
def agrupar_por_albaran(filas: list[FilaPlana]) -> list[CasoRevisado]
def repartir(caso: CasoRevisado) -> dict[str, dict[str, list[dict]]]
    # {"IA1": {"cabeceras": [...], "lineas": [...]}, "IA2": {...}, ...}
def asignar_casos_id(casos, mapa: dict[str, str]) -> tuple[dict[str, str], list[str]]
```

```python
# evals/revision/albaranes.py
def normalizar_codigo(texto: str) -> str                   # "2.115.714" -> "2115714"
def emparejar(codigos: dict[str, str], ficheros: list[str]) -> tuple[dict, list]
```

```python
# evals/revision/escritura.py  (infraestructura)
def copia_de_seguridad(ruta: Path, momento: dt.datetime) -> Path
def escribir_libro(ruta: Path, tablas: dict[str, list[dict]], propios: set[str]) -> None
```

`reparto.py`, `vocabulario.py` y `albaranes.py` no importan `openpyxl` ni tocan
disco: son las que llevan la cobertura y la campaña de mutación.

## 5. Convenios de celda

- Celda vacía copiada → `?` (R9). Celda **derivada** de una columna de origen
  que afirma que el dato no está en el papel → vacía (R10).
- Los valores de origen llegan con ruido (`CONTRATO` / `DE CONTRATO`,
  `EN OFERTA` / `OFERTTA`). Los sinónimos aceptados viven en
  `vocabulario.json`; lo no reconocido **aborta** (R5), no se adivina.
- Las etiquetas de familia se traducen al catálogo único: `HORMIGON`→`hormigon`,
  `MORTERO`→`mortero`, `RESIDUOS` y `CONTENEDORES`→`residuos`, `GENERICO`,
  `FERRETERIA`, `MATERIALES` y `GRAVA`→`generico`, `GASOLEO`→`combustible`,
  `CAMION GRUA`→`alquiler_maquinaria`. Es propuesta: la valida el humano (D1).

## 6. Riesgos y decisiones

- **D1 · `CONTENEDORES`→`residuos` y `CAMION GRUA`→`alquiler_maquinaria`** son
  interpretación nuestra de una etiqueta del humano. Van en fichero de datos
  precisamente para cambiarlas sin tocar código. Pendiente de validación.
- **D2 · El importador escribe LIBROS, no fixtures.** Alternativa descartada:
  generar los JSON directamente. Saltaría el barrido de C3 bis, duplicaría la
  normalización del conversor y dejaría al humano sin poder corregir a mano.
- **D3 · Vacío → `?`.** Alternativa descartada: vacío → `null` esperado. El
  **Validada por el humano el 2026-09-15.** El
  humano deja celdas sin rellenar porque aún no las ha mirado, no porque afirme
  que el sistema no debe devolver nada; comparar eso sería inventar ground
  truth (R13). El coste es un banco más laxo, y el informe de R14 dice
  exactamente dónde está ciego.
- **D4 · `numero_albaran` y la obra de IA1 quedan sin vigilar** (patrón 9 y la
  mitad de extracción del patrón 2). Es lo que ya hacen los 7 casos RES y es el
  precio de no fabricar literales. Se recupera en cuanto el humano escriba el
  número impreso en el libro.
- **D5 · Riesgo de pisar trabajo manual.** Mitigado por R16 (copia previa) y
  R17 (solo se reescriben los `caso_id` de la importación). Los libros están en
  `.gitignore` (`*.xlsx`): git no los recupera.
- **D6 · El campo `servicios` de la ficha.** F-045 no toca sv2/sv5/sv6; se
  propone al humano anotarlo como «servicios vigilados» o vaciar el campo.
- **Riesgo de deriva**: el Excel cambia bajo nuestros pies. Por eso todo es
  reejecutable (R18) y nada del código depende de un valor concreto.

## 7. Fichas de arreglo propuestas (NO entran en F-045)

Ordenadas por cuántas líneas de la revisión toca cada patrón (medido el
2026-09-15). Todas pasan el filtro de robustez de R27 salvo donde se indica.

1. **Patrón 1 · la partida se lee mal** (el más repetido: 5 albaranes, 4
   familias). Decisión: no leer la partida a ciegas, sino **elegirla de la
   lista de partidas de la obra** (el nivel justo por encima de los
   descompuestos), vía sigrid-api. Estrecha el espacio de búsqueda: sobrevive a
   un cambio de formato y a un proveedor nuevo. Relacionada: F-021.
2. **Patrón 3 · líneas deducidas que no se generan.** El incremento por cambio
   de año existe en mortero y en residuos, no solo en hormigón; la carga
   incompleta, también en mortero; y hay incrementos subrayados a mano. Regla
   del humano: si sale en el contrato hay que analizarlo; si no, buscarlo en la
   oferta (F-017).
3. **Patrón 2 · la obra se deduce mal.** Decisión: con el proveedor
   identificado con certeza, deducir la obra **solo entre las obras con
   contrato con ese proveedor**. Estrecha el espacio de búsqueda.
4. **Patrón 5 · unitario equivocado dentro del contrato** (grava 20/40). Roza
   §12 (matching estricto): candidata a resolverse por contexto de línea, nunca
   por una regla de producto.
5. **Patrón 8 · dos contratos candidatos y no elige ninguno.** Propuesta del
   humano: coger los dos, fusionarlos dejando marcada la fusión y seguir.
   Revisar contra §12 antes de aceptarla.
6. **Patrón 4 · devoluciones** (cantidad negativa que referencia el número de
   albarán del proveedor). Funcionalidad nueva, un solo caso hoy.
7. **Patrón 6 · el código LER no se ve en la vista detallada**: verificar si se
   persiste. Barata y cerrada.
8. **Patrones 7 y 9** (CIF raro, número de albarán mal leído): un caso cada
   uno. Con un solo caso no se distingue defecto de casualidad: quedan
   registrados en `evals/patrones.json` y esperan un segundo caso.
