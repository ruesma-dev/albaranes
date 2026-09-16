<!-- specs/F-045-banco-evals-revision-manual/design.md -->
# F-045 · Diseño

## 1. Encaje y límite de servicio

Todo ocurre en `evals/`, el banco de pruebas del monorepo. **No se toca ni una
línea de sv1–sv6 ni de `ruesma_comun`**: F-045 siembra la red, no arregla lo que
detecta. La ficha declara `servicios: [sv2, sv5, sv6]`: son los **vigilados**,
no los modificados (decisión abierta D6). El flujo no cambia de forma: revisión
manual → **libros de `ground_truth/`** → `evals.conversor` → `fixtures/*.json` →
`evals.runner`; esta feature añade un escalón **antes** de los libros y deja el
conversor como única puerta a los fixtures (y único sitio donde corre el barrido
de C3 bis). Reglas de dominio que gobiernan el reparto: `docs/ARCHITECTURE.md`
§6 (`codigo_imputacion` = partida impresa; `codigo_partida_final` = decisión del
matching), §7 (sintéticas), §13 (`precio` bruto, `precio_neto` = importe; el
unitario leído manda) y §14 (la familia la decide IA1).

## 2. Ficheros

### A crear

Paquete `evals/revision/`. **Dominio puro** (sin openpyxl ni disco: es lo que
lleva cobertura y mutación): `modelos.py` (`FilaPlana`, `LineaRevisada`,
`CasoRevisado`, `InformeImportacion`), `vocabulario.py`, `reparto.py` (**el
núcleo**: filas planas → tablas de los seis libros) y `albaranes.py` (código
desde el nombre, emparejado y plan de copia). **Infraestructura**: `lectura.py`
y `escritura.py` (con copia previa). **Entrada**: `__main__.py`. **Datos
versionados**: `evals/revision/vocabulario.json`, `evals/mapa_casos.json` y
`evals/patrones.json`. **Tests**: `tests/test_f045_r*.py`, uno por bloque.

### A modificar

- `evals/procesos/sv2_extraccion.py`: `OBSERVABLES` de `cabeceras`, `lineas` y
  `contexto`, como la de `sv6_build.py` (R25), y devolver el **camino de
  lectura** medido (§4 bis, R23).
- `evals/runner.py`: `_comparar_tablas_de` pasa esos observables y acumula
  `campos_no_observables`, que hoy descarta para IA1/IA2 (R25, R26).
- `evals/informe.py`: agrupar el resumen por camino de lectura. `.gitignore`:
  ignorar `evals/inputs/albaranes/` (hoy solo hay `*.pdf`, R24).
- `evals/conversor.py`: `Grava` y `Ferreteria` en `TIPOLOGIAS` (§5 bis), su
  único cambio. `evals/README.md` (comando, patrones, extensiones) y
  `harness/features.json` (las fichas de §7, R30).

### Que NO se tocan

`comparador.py`, `criticidad.py|json`, `barrido.py`, `modelos.py`,
`procesos/sv5_valoracion.py`, `procesos/sv6_build.py` y **todo**
`services/`. Tentaciones: no se añade `unidad` a `LineaAlbaran` (F-024) ni se
cambia el formato de los libros.

## 3. La tabla de reparto (NORMATIVA)

Una fila por **línea de albarán**, mezclando lo leído del papel con lo valorado.
Medido el 2026-09-15 (142 filas, 59 códigos, 10 etiquetas; puede haber crecido).

| Columna plana | Destino | Por qué |
|---|---|---|
| `codigo alabran` | clave natural del caso (§4); `IA1.cabeceras.numero_albaran` = `?` | el código del humano no es el literal impreso (`0000168` vs `SS-0000168`): compararlo daría rojo falso (R13) |
| `Tipo de albaran` | pestaña del libro **y** `INPUTS.CASOS.tipologia` = familia de DOCUMENTO del catálogo (§5 bis) | pestaña y familia no siempre coinciden: GASOLEO va a la pestaña Combustible con familia `generico` (R6) |
| `cif` | `RESULTADO_FINAL.datos_generales.CIF`; en IA1 `?` | el CIF correcto es el del proveedor identificado, no siempre el impreso; así lo tienen ya los 7 casos RES |
| `nombre empresa (el bueno…)` | `IA1.cabeceras.proveedor_nombre` **y** `FINAL.proveedor` | es la razón social con la que se guarda, y coincide con lo impreso en los casos ya sembrados |
| `codigo obra` | `FINAL.datos_generales.obra`; en IA1 `obra_codigo` y `obra_nombre` = `?` | deducir la obra NO es extraer: el papel a menudo no la trae (R13) |
| `codigo contrato` | `FINAL.datos_generales.contrato_elegido` + `INPUTS.CASOS.contrato_codigo` | el contrato no está en el papel: lo elige la valoración |
| `partida` | fila impresa con partida en el papel → `IA1.lineas.codigo_imputacion`; **siempre** → `IA3.lineas_valoradas.codigo_partida_final` y `FINAL.lineas.partida_final` | §6 de la arquitectura; el patrón 1 vive en la decisión, no solo en la lectura |
| `linea esta en albaran o deducida` | **discrimina la fila entera**: `EN ALBARAN` → `IA1.lineas` + `FINAL` TABLA 2; `DEDUCIDA …` → `IA3` TABLA 2 (sintéticas esperadas) + `FINAL` TABLA 3 | una línea deducida no existe en el papel: escribirla en IA1 exigiría a IA1 inventarla |
| `linea en contrato de sigrid o nueva` | `EN CONTRATO` → `IA3.codigo_producto_contrato` con su `match_method`; `NUEVA` → sin match, el caso pasa a `IA4` (`concilia`); `OFERTA` → `precio_source=oferta` (F-017) | |
| `fecha` y `concepto` | `IA1.cabeceras.fecha` / `IA1.lineas.descripcion_esperada` (laxo), y sus columnas del FINAL | impresos en el papel |
| `cantidad` | fila impresa → `IA1.lineas.cantidad`; fila deducida → `IA3` sintéticas `.cantidad`; siempre `FINAL.cantidad_final` | |
| `unidad` | `FINAL.lineas.unidad_final`; en IA1 se escribe y el runner la declara **no observable** | sv2 no extrae unidad hoy (F-024); exigirla en IA1 sería un rojo permanente (R26) |
| `precio unitario` + `unitario viene en…` | `ALBARAN` → `IA1.lineas.precio_unitario` (bruto) y `IA3.precio_source=albaran`; `CONTRATO` u `OFERTA` → IA1 **vacío** (null afirmado, R4) y `IA3.precio_unitario_final` + `precio_source` | **la separación extracción/valoración que pide el humano** |
| `importe` + `importe viene en…` | `ALBARAN` → `IA1.lineas.importe` (que es `precio_neto`, §13); valorado → `IA3.importe_calculado` y `FINAL.importe_final` | §13: el importe leído se transcribe, no se recompone |
| `descuento` | `IA1.lineas.descuentos` | es dato del papel y entra en la fórmula de §13 |
| `LER o codigo linea o producto` | familia `residuos` → `IA2.contexto` (`campo_contexto=codigo_LER`); resto → `IA3.codigo_producto_contrato` | el LER es contexto de línea, no dato de cabecera |
| `Comentarios` | columna `comentario` del libro (laxo, no se compara) **y** clasificación del caso: con texto → defecto conocido y patrón de `evals/patrones.json`; vacía → **caso de no regresión** | es el diagnóstico de hoy, no el resultado esperado; el vacío afirma que eso salió BIEN (R9) |

No alimenta `INPUTS.CONTRATO_LINEAS` ni `IA3` TABLA 3: se dejan vacías y el
informe lo dice. Sin líneas de contrato los casos nuevos solo son evaluables
**con LLM**; la corrida determinista vivirá de los 7 RES.

## 4. Firmas principales

```python
# reparto.py (puro: dict in, dict out)
def clave_natural(fila: FilaPlana) -> str            # CIF + código normalizado
def agrupar_por_albaran(filas: list[FilaPlana]) -> list[CasoRevisado]
def repartir(caso: CasoRevisado) -> dict[str, dict[str, list[dict]]]
def asignar_casos_id(casos, mapa: dict) -> tuple[dict[str, str], list[str]]
# albaranes.py
def codigo_desde_nombre(n: str) -> str   # "PROV_SS-0003967.pdf" -> "SS-0003967"
def normalizar_codigo(texto: str) -> str  # "2.115.714" -> "2115714"
def emparejar(codigos: dict, ficheros: list[str]) -> tuple[dict, list]
```

**El puente entre los tres mundos** (convenio del humano, 2026-09-15): del
**nombre del fichero** sale el **código de albarán** —con el que él identifica
cada fila del Excel— y de ahí el **`caso_id`**. Si el nombre sin extensión trae
`_`, el código es lo de después del último; si no, el nombre entero
(`PROVEEDOR_SS-0003967.pdf` y `SS-0003967.png` → `SS-0003967`). Sin él, casar 59
albaranes con ~142 filas es manual; el renombrado es script (T11). **Manda el
código del papel**, nunca el persistido: el precedente es `SS-0801977` leído
donde el papel decía `SS-0001977`. **Cuatro fallos ruidosos** (R21): dos
ficheros con el mismo código, un código sin fila, una fila sin fichero y un
nombre vacío tras la regla; el informe los lista uno a uno. El **mapa**
(`mapa_casos.json`, R7) guarda `caso_id` ↔ código ↔ nombre ↔ formato ↔
`gemelo_de`: sin él un caso rojo no se audita contra el papel.

## 4 bis. Los tres caminos de lectura y los casos gemelos

Verificado en `extract_albaran_pipeline.py` de sv2 (rama de imágenes, ~línea
249) y en `ruesma_comun/imaging/preprocess.py`. Son tres, no dos:

| Camino | Qué recibe la IA y con qué realce |
|---|---|
| `pdf_texto` | el PDF tal cual, lee caracteres; sin realce |
| `pdf_escaneado` | una imagen JPEG por página, cadena de realce con flags `PREPROCESO_*` |
| `imagen` (PNG/JPG suelto) | la imagen pasada por `preparar_imagen_para_ia`, mismos flags |

Límite conocido: lo indecodificable (HEIC) va sin realzar, best-effort. La rama
de imágenes es de julio de 2026 y **hoy no la mide nadie**; leer píxeles rinde
peor, y un fallo solo del tercer camino es FORMATO, no extracción (R23).

**Dónde vive el formato: en ningún libro.** Se **mide** en la corrida:
`sv2_extraccion.py` ya resuelve la ruta con `EXTENSIONES = (".pdf", ".jpg",
".jpeg", ".png")` y el mime con `mimetypes`; devolverá el camino y
`evals/informe.py` agrupa por él. Descartada una columna `formato`: sería ground
truth afirmado sobre algo observable. **Casos gemelos**: el mismo albarán en PDF
y en PNG son DOS casos con el MISMO ground truth y distinta entrada, `HOR-012` y
`HOR-012-IMG` (R22), hermanados por `gemelo_de`. **No se deduplica**: es el
único experimento que aísla el formato.

**Qué no cambia y qué sí.** `evals/barrido.py` solo mira texto de celda y
`evals/conversor.py` no toca ficheros de entrada: ninguno asume PDF. Sí cambia
el `.gitignore`, que ignora `*.pdf` pero **no** `*.png`: hoy un original en PNG
entraría en git (R24). Se ignora `evals/inputs/albaranes/` entera, no `*.png`
global, por los assets del front sv4.

## 5. Convenios de celda: dos ejes que NO se mezclan

El primer eje es el **comentario** y solo decide qué se espera HOY: vacío → **no
regresión**, VERDE, y hay que comprobar en cada pasada que lo sigue siendo; con
texto → **defecto conocido**, ROJO hasta que se arregle. Se compara igual en los
dos casos, y un comentario vacío no produce jamás un `?`: son los que avisan de
que hemos roto algo que funcionaba, y son la mitad larga del banco (2026-09-15:
107 de 142 filas sin comentario, 36 de los 59 albaranes sin ninguno). El segundo
eje es el **valor esperado**, y su política por columna vive en
`vocabulario.json` (R11, R12):

| Columna | Vacía significa | Se escribe | Vacías el 2026-09-15 |
|---|---|---|---|
| `descuento` | sin descuento | vacío (`null`; factor 1 de §13) | 58 de 142 |
| `LER o codigo…` | no aplica a esa familia | no genera fila de IA2 | 128 de 142 |
| `partida`, `precio unitario`, `importe` y el resto | el humano no lo ha afirmado | `?` | 8, 1, 1 y 0 |

El banco es **poco laxo**: la ceguera real son ~10 celdas `?` y los campos de
IA1 que no se vigilan por D4, no las 107 filas.

- Los valores de origen llegan con ruido (`CONTRATO` / `DE CONTRATO`,
  `EN OFERTA` / `OFERTTA`). Los sinónimos aceptados viven en
  `vocabulario.json`; lo no reconocido **aborta** (R5), no se adivina.
- Las etiquetas de familia se traducen con la tabla de §5 bis, que vive en
  `vocabulario.json` y en ningún otro sitio.

## 5 bis. Etiquetas, familias y pestañas: tres espacios de nombres

Hoy nadie los reconcilia. La **etiqueta** del Excel la escribe el humano (10
valores); la **familia de documento** solo puede ser hoy una de CUATRO
—`generico`, `hormigon`, `mortero`, `residuos`—, porque `combustible`,
`alquiler_maquinaria` y `otro` son de alcance LÍNEA
(`ruesma_comun/contratos/familias.py`); y la **pestaña** es organización del
banco, no familia.

| Etiqueta (filas/albaranes, 2026-09-15) | Familia doc. | Pestaña |
|---|---|---|
| HORMIGON 55/17 · MORTERO 10/4 · RESIDUOS 38/19 | la suya | Hormigon · Mortero · Residuos |
| GENERICO 11/3 · MATERIALES 8/7 | `generico` | Generico-Suministros |
| CONTENEDORES 3/2 | `residuos` (gestión de RCD) | Residuos |
| CAMION GRUA 3/1 | `generico` + línea `alquiler_maquinaria` | Alquiler |
| GASOLEO 1/1 | **`combustible`**, que hoy es solo de LÍNEA | Combustible |
| FERRETERIA 11/3 | **`ferreteria`**, que no existe | Ferreteria (nueva) |
| GRAVA 2/2 | **`grava`**, que no existe | Grava (nueva) |

Las diez etiquetas tienen destino; ninguna cae en «desconocida». Pero **tres
apuntan a familias de documento que hoy no existen** (decisión del humano,
2026-09-15): subir `combustible` de línea a documento y añadir `grava` y
`ferreteria` —más **`ferralla`**, que ni siquiera aparece en el Excel—. Ampliar
el catálogo **no se hace en F-045**: `familias.py` es ruta sensible, su texto se
inyecta en el prompt de IA1 y toca F-043; es **ficha propia** (§7). Mientras no
exista, esos casos **nacen ROJOS a propósito** y el informe los agrupa bajo «la
familia aún no existe en el catálogo», aparte de los defectos reales de
clasificación, para que un rojo esperado no parezca regresión. **Riesgos de esa
ficha, no de esta**: `grava` llega con 2 líneas en 2 albaranes y `ferralla` con
**ninguno**, así que ni su definición ni su prompt de fase 2 tendrían con qué
probarse, y el doc de dominio **no documenta ninguna regla de ferralla**, pese a
que en obra tiene vida propia (armaduras, despieces, kilos de acero).

Las pestañas **`Grava`** y **`Ferreteria`** no existen en los libros: se crean en
los seis copiando la estructura de `Generico-Suministros` (mismas tablas y
encabezados) y se añaden a `TIPOLOGIAS` de `evals/conversor.py`, con prefijos
`GRA-` y `FER-`; `Ferralla` se añadirá igual cuando el humano traiga albaranes,
y su ausencia hoy no rompe nada. **Bombeo** no tiene etiqueta ni familia: nadie
escribe ahí y el informe lo dice. Una etiqueta desconocida **aborta** (R5).

## 5 ter. Criterio de valoración de residuos (ground truth)

Criterios del humano del 2026-09-15, verificados contra sv6 y el §10.6 del doc
de dominio. Son de VALORACIÓN, no de extracción, y pasan el filtro de R29.

| Criterio | Hoy |
|---|---|
| Si el contrato no tarifa ese LER, el incremento se deduce del **canon**, localizado por el código LER | **NO implementado**: `residuos_incrementos.py` emite la sintética sin precio y deja el enganche para F-006 (canon de vertedero, `spec_ready`) |
| **Mínimo facturable de 1 tn en lo que se PESA**: canon y tratamiento (0,42 tn → 1; 3,10 tn → 3,10). El **movimiento de contenedor no se toca**: sigue en unidades, 1 cambio = 1 UD (§10.6) | **NO implementado** |
| **Incremento por año también en residuos** | **NO implementado**: la red M1 de `valuation_builder` corta con `!= "hormigon"` |

Los tres nacen como **defecto conocido**: salen ROJOS hasta que exista el código
y sus arreglos son fichas propias (§7). El alcance del mínimo fija el ground
truth de los 19 albaranes de residuos: se aplica a lo que se pesa, no a lo que
se cuenta.

## 6. Riesgos y decisiones

- **D1 · El mapeo de etiquetas (§5 bis) vive solo en `vocabulario.json`**, para
  cambiarlo sin tocar código. **D2 · El importador escribe LIBROS, no fixtures**:
  generar los JSON directos saltaría el barrido de C3 bis.
- **D3 · El vacío del comentario y el del valor son cosas distintas** (§5).
  **Corregida por el humano el 2026-09-15**: «celda vacia EN COMENTARIOS no es
  que no se compare. es que ha salido ok en las pruebas. pero hay que seguir
  validando en los evals que sigue saliendo bien». El `?` solo lo produce un
  **valor esperado** ausente, y ni siempre (R12); tratar las 107 filas sin
  comentario como huecos habría tirado los casos más valiosos del banco.
- **D4 · `numero_albaran` y la obra de IA1 quedan sin vigilar** (patrón 9 y la
  mitad de extracción del 2), como ya hacen los 7 casos RES. **Deriva**: el
  Excel cambia; por eso todo es reejecutable (R18).
- **D5 · Pisar trabajo manual**: mitigado por R16 y R17. **D6 · `servicios` de
  la ficha**: F-045 no toca sv2/sv5/sv6, son «vigilados».

## 7. Fichas de arreglo propuestas (NO entran en F-045)

Por cuántas líneas toca cada patrón (2026-09-15); todas pasan el filtro de R29.

| # | Patrón | Decisión candidata |
|---|---|---|
| 1 | **1 · la partida se lee mal** (5 albaranes, 4 familias) | elegirla de la **lista de partidas de la obra** (el nivel sobre los descompuestos), vía sigrid-api. Estrecha el espacio de búsqueda. F-021 |
| 2 | **3 · líneas deducidas que no se generan** | incremento por año en mortero **y residuos**, carga incompleta en mortero, incrementos subrayados a mano. Si sale en el contrato, analizarlo; si no, en la oferta (F-017) |
| 3 | **2 · la obra se deduce mal** | con el proveedor identificado, deducirla **solo entre las obras con contrato con él** |
| 4 | **residuos: canon e incremento por año** (§5 ter) | canon por LER (F-006, ya `spec_ready`), mínimo facturable y M1 fuera de hormigón |
| 5 | **5 · unitario equivocado en el contrato** (grava 20/40) | por contexto de línea, nunca por regla de producto (§12) |
| 6 | **8 · dos contratos candidatos y no elige** | coger los dos y fusionarlos marcando la fusión. Revisar contra §12 |
| 7 | **4 · devoluciones** (cantidad negativa que cita el albarán del proveedor) y **6 · el LER no se ve en la vista detallada** | la primera es funcionalidad nueva con un solo caso; la segunda, verificar si se persiste: barata y cerrada |
| 9 | **7 y 9** (CIF raro, número mal leído) | un caso cada uno: esperan un segundo antes de ser ficha |
| 10 | **ampliar el catálogo de familias** (§5 bis) | `combustible` de línea a documento, más `grava`, `ferreteria` y `ferralla`. Ruta sensible (prompt de IA1, F-043); **bloquea** 14 filas / 6 albaranes del banco, y `ferralla` llega sin ningún caso |
