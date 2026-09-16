<!-- progress/mutacion_F-045.md -->
# F-045 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-045` el 2026-09-15 19:05.

## Alcance

Origen del diff: **rama** (`946752d37389c9bf84d4eaad385727d8b2725d75` .. `feature/F-045-banco-evals-revision-manual`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/conversor.py` | 6 |
| `evals/revision/__init__.py` | 19 |
| `evals/revision/__main__.py` | 287 |
| `evals/revision/albaranes.py` | 307 |
| `evals/revision/escritura.py` | 348 |
| `evals/revision/informe.py` | 164 |
| `evals/revision/lectura.py` | 117 |
| `evals/revision/mapa.py` | 75 |
| `evals/revision/modelos.py` | 189 |
| `evals/revision/reparto.py` | 674 |
| `evals/revision/vocabulario.py` | 185 |
| **Total** | **2371** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 266 |
| Mutantes evaluados | 266 |
| Muertos | 176 |
| Supervivientes | 90 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 6381.0 s |
| SHA de HEAD medido | `1c3e8d77504a45e789b040dbdb01fa6bf53cd11f` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_xkdvr0rm/wk_0` | 141.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_xkdvr0rm/wk_1` | 141.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_xkdvr0rm/wk_2` | 143.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-045_xkdvr0rm/wk_3` | 142.8 |
| Media por mutante evaluado (s) | 24.0 |
| Timeout efectivo por mutante (s) | 288 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes: resultado del análisis

**Los 90 supervivientes están analizados; ninguno queda pendiente.** Reparto
final: **74 cerrados con test nuevo** y **16 justificados como mutantes
equivalentes**.

> **Corregido tras el review (pasada 1).** La primera versión declaraba 19
> equivalentes y **dos eran falsos**: el 49 (`sort_keys`) afirmaba que el mapa
> salía «byte a byte igual» sin comprobarlo, y el 8 (`ejecutar=False`) pasaba
> por alto que la comprobación previa guardaría el libro ANTES de la copia de
> seguridad, incumpliendo R16. Los dos se cierran ahora con test, y con ellos
> el 9, que era dudoso y se resolvió por la misma regla: **ante la duda, test**.
> Las 16 que quedan llevan cada una su comprobación EJECUTADA, no su prosa.

### Cómo se verificó

La campaña de arriba midió el banco **antes** de los tests de T18. Volver a
lanzarla entera costaba otras dos horas —y el intento se degradó: cinco horas
en el primer fichero, con un worker bloqueado—, así que cada superviviente se
**reinyectó uno a uno** y se juzgó con la suite acotada a F-045 (~11 s por
mutante, 90 mutantes en tres tandas). Es la misma técnica que el inventario
documenta para F-043. El veredicto de cada uno está en su ficha.

| Tanda | Reinyectados | Mueren |
|---|---:|---:|
| Tras `test_f045_r14_recuento_y_convenios.py` y `test_f045_r17_r18_fusion.py` | 90 | 61 |
| Tras la segunda tanda de tests (IA4, gemelos, rutas, fórmulas, `frozen`) | 29 | 8 |
| Tras afinar la comprobación de rutas por defecto | 21 | 2 |
| Tras el review: mapa byte a byte, R16 en `escritura` e informe anidado | 19 | 2 |
| Tras subir el test de R16 al nivel de la CLI, que es donde vive el mutante 8 | 17 | 1 |
| **Total** | **90** | **74** |

### Los seis grupos de equivalencia

| Grupo | Qué comparten | Supervivientes |
|---|---|---|
| G1 | el índice de celda no cambia el número de fila (`fila[0].row` ≡ `fila[1].row`) | 19, 21, 22, 24, 33 |
| G2 | valor por defecto de un dataclass que siempre se sobrescribe antes de leerse | 15, 16, 17 |
| G3 | aritmética sobre un centinela que solo se compara con «> 0» | 31 |
| G4 | rama inalcanzable (un `setdefault` cuya clave ya existe siempre) | 6 |
| G5 | argumento que no cambia el resultado observable | 18, 44, 71 |
| G6 | mutación semánticamente idéntica | 10, 45, 72 |

El criterio con el que se admite una equivalencia es el que el review dejó
claro: **solo vale si demuestra que NINGÚN comportamiento observable cambia, y
la demostración se ejecuta**. Los 8, 9 y 49 estaban en G5 con prosa plausible y
se cayeron; por eso las 16 restantes traen su comprobación corrida.

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/revision/__main__.py:29` [entero]

- Original: `RUTA_INFORME = Path(__file__).resolve().parents[2] / "progress" / "import_F-045.md"`
- Mutado:   `RUTA_INFORME = Path(__file__).resolve().parents[3] / "progress" / "import_F-045.md"`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 2. `evals/revision/__main__.py:32` [entero]

- Original: `RUTA_ORIGINALES = Path(__file__).resolve().parents[1] / "inputs" / "albaranes"`
- Mutado:   `RUTA_ORIGINALES = Path(__file__).resolve().parents[2] / "inputs" / "albaranes"`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 3. `evals/revision/__main__.py:40` [booleano]

- Original: `dry_run: bool = False,`
- Mutado:   `dry_run: bool = True,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 4. `evals/revision/__main__.py:41` [booleano]

- Original: `renombrar: bool = False,`
- Mutado:   `renombrar: bool = True,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 5. `evals/revision/__main__.py:135` [logico]

- Original: `"gemelo_de": copia.gemelo_de or None,`
- Mutado:   `"gemelo_de": copia.gemelo_de and None,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 6. `evals/revision/__main__.py:143` [logico]

- Original: `registro.setdefault("gemelo_de", caso.gemelo_de or None)`
- Mutado:   `registro.setdefault("gemelo_de", caso.gemelo_de and None)`

#### Análisis

- **Por qué ningún test lo caza**: es un `setdefault` que nunca llega a disparar: cuando `_anotar_documentos` lo ejecuta, `asignar_casos_id` ya ha escrito `gemelo_de` en ese mismo registro (línea 164 de `reparto.py`, que sí muere con el test nuevo), así que la clave existe siempre y el valor del `setdefault` se descarta.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G4 · rama inalcanzable**. Es defensa en profundidad: el día que alguien llame a `_anotar_documentos` sin pasar por `asignar_casos_id`, esa línea es lo que evita un `KeyError`. Comprobado ejecutando `asignar_casos_id` sobre un caso real: `gemelo_de` ya está en el registro (con valor `None`) antes de que el `setdefault` se ejecute.

### 7. `evals/revision/__main__.py:176` [booleano]

- Original: `creadas = False`
- Mutado:   `creadas = True`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 8. `evals/revision/__main__.py:198` [booleano]

- Original: `ruta, pestana, _definiciones(defs), filas, caso_ids, ejecutar=False`
- Mutado:   `ruta, pestana, _definiciones(defs), filas, caso_ids, ejecutar=True`

#### Análisis

- **Por qué sobrevivía**: la primera justificación decía que la pasada de comprobación con `ejecutar=True` acaba en el mismo sitio porque `escribir_pestana` solo guarda cuando `cambia`. **Era falsa**: cuando `cambia` es cierto —que es justo el caso en que se escribe—, la comprobación GUARDA el libro **antes** de `copia_de_seguridad(ruta)`, así que la copia deja de ser el estado previo. Eso incumple R16 y con él la mitigación de D5: la copia es la única red del trabajo manual del humano, porque los libros no se versionan.
- **Decisión**: TEST NUEVO, en los dos niveles. `test_f045_r16_la_copia_es_el_libro_tal_como_estaba_antes_de_escribir` cubre `escritura`, y `test_f045_r16_la_copia_del_libro_es_el_estado_ANTES_de_la_importacion` cubre la CLI, que es donde vive el mutante. Reinyectado, **muere**.

### 9. `evals/revision/__main__.py:277` [booleano]

- Original: `destino.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `destino.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis

- **Por qué sobrevivía**: `mkdir(parents=True)` solo se distingue de `parents=False` cuando falta un directorio intermedio, y `progress/` existe siempre. Pero `--informe` admite cualquier ruta, así que la diferencia es real aunque el banco no la pisara: ante la duda, test.
- **Decisión**: TEST NUEVO. `test_f045_r14_el_informe_se_deja_aunque_su_carpeta_no_exista` apunta `--informe` a dos niveles que no existen. Reinyectado, **muere**.

### 10. `evals/revision/albaranes.py:67` [entero]

- Original: `return tronco.rsplit("_", 1)[-1].strip() if "_" in tronco else tronco`
- Mutado:   `return tronco.rsplit("_", 2)[-1].strip() if "_" in tronco else tronco`

#### Análisis

- **Por qué ningún test lo caza**: `rsplit("_", 1)[-1]` y `rsplit("_", 2)[-1]` devuelven siempre el mismo trozo: cambiar cuántos cortes se hacen no cambia cuál es el ÚLTIMO.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G6 · mutación semánticamente idéntica**. Comprobado sobre cinco nombres reales, incluidos `a__b` y `_`: `rsplit('_', 1)[-1] == rsplit('_', 2)[-1]` en todos.

### 11. `evals/revision/albaranes.py:113` [comparacion]

- Original: `or (len(sin_ceros(codigo)) >= MINIMO_SUBCADENA and sin_ceros(codigo) in tronco)`
- Mutado:   `or (len(sin_ceros(codigo)) > MINIMO_SUBCADENA and sin_ceros(codigo) in tronco)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 12. `evals/revision/albaranes.py:120` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 13. `evals/revision/albaranes.py:134` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 14. `evals/revision/escritura.py:62` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 15. `evals/revision/escritura.py:75` [entero]

- Original: `fila_encabezados: int = 0`
- Mutado:   `fila_encabezados: int = 1`

#### Análisis

- **Por qué ningún test lo caza**: son los valores por defecto de los tres campos de `Bloque`, y `localizar_bloques` los asigna todos antes de que nadie los lea; un bloque que se quedara sin encabezados no llega a usarlos porque levanta `ErrorEscritura` primero.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G2 · valor por defecto que siempre se sobrescribe antes de leerse**. Cubrirlo exigiría un test que construyera un `Bloque` a medias, que es un estado que el código nunca produce. Comprobado sobre el código de `localizar_bloques`: asigna los tres campos en el mismo bloque y, sin encabezados, levanta `ErrorEscritura` antes de devolver nada.

### 16. `evals/revision/escritura.py:77` [entero]

- Original: `primera_fila: int = 0`
- Mutado:   `primera_fila: int = 1`

#### Análisis

- **Por qué ningún test lo caza**: son los valores por defecto de los tres campos de `Bloque`, y `localizar_bloques` los asigna todos antes de que nadie los lea; un bloque que se quedara sin encabezados no llega a usarlos porque levanta `ErrorEscritura` primero.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G2 · valor por defecto que siempre se sobrescribe antes de leerse**. Cubrirlo exigiría un test que construyera un `Bloque` a medias, que es un estado que el código nunca produce. Comprobado sobre el código de `localizar_bloques`: asigna los tres campos en el mismo bloque y, sin encabezados, levanta `ErrorEscritura` antes de devolver nada.

### 17. `evals/revision/escritura.py:78` [entero]

- Original: `ultima_fila: int = 0`
- Mutado:   `ultima_fila: int = 1`

#### Análisis

- **Por qué ningún test lo caza**: son los valores por defecto de los tres campos de `Bloque`, y `localizar_bloques` los asigna todos antes de que nadie los lea; un bloque que se quedara sin encabezados no llega a usarlos porque levanta `ErrorEscritura` primero.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G2 · valor por defecto que siempre se sobrescribe antes de leerse**. Cubrirlo exigiría un test que construyera un `Bloque` a medias, que es un estado que el código nunca produce. Comprobado sobre el código de `localizar_bloques`: asigna los tres campos en el mismo bloque y, sin encabezados, levanta `ErrorEscritura` antes de devolver nada.

### 18. `evals/revision/escritura.py:91` [booleano]

- Original: `destino.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `destino.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis

- **Por qué ningún test lo caza**: `mkdir(parents=True)` solo se distingue de `parents=False` cuando falta un directorio intermedio, y tanto `progress/` como el directorio de los libros existen siempre: son parte del repositorio.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G5 · argumento que no cambia el resultado observable**. Cazarlo pediría un test que apuntara el informe a una ruta con dos niveles nuevos, que es un caso que la CLI no ofrece. Comprobado: `copia_de_seguridad` exige que el libro exista, así que su directorio también, y `copias` es el ÚNICO nivel que crea.

### 19. `evals/revision/escritura.py:146` [entero]

- Original: `actual.ultima_fila = fila[0].row - 1`
- Mutado:   `actual.ultima_fila = fila[1].row - 1`

#### Análisis

- **Por qué ningún test lo caza**: todas las celdas de una fila de openpyxl comparten el mismo `.row`, así que `fila[0].row` y `fila[1].row` devuelven exactamente el mismo número.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G1 · el índice de celda no cambia el número de fila**: la mutación es sintáctica, no semántica, y ningún test puede distinguirla porque no hay nada que distinguir. Comprobado ejecutando sobre una hoja de dos filas: `fila[0].row == fila[1].row == fila[2].row` en todas.

### 20. `evals/revision/escritura.py:146` [entero]

- Original: `actual.ultima_fila = fila[0].row - 1`
- Mutado:   `actual.ultima_fila = fila[0].row - 2`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 21. `evals/revision/escritura.py:157` [entero]

- Original: `actual.fila_encabezados = fila[0].row`
- Mutado:   `actual.fila_encabezados = fila[1].row`

#### Análisis

- **Por qué ningún test lo caza**: todas las celdas de una fila de openpyxl comparten el mismo `.row`, así que `fila[0].row` y `fila[1].row` devuelven exactamente el mismo número.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G1 · el índice de celda no cambia el número de fila**: la mutación es sintáctica, no semántica, y ningún test puede distinguirla porque no hay nada que distinguir. Comprobado ejecutando sobre una hoja de dos filas: `fila[0].row == fila[1].row == fila[2].row` en todas.

### 22. `evals/revision/escritura.py:158` [entero]

- Original: `actual.primera_fila = fila[0].row + 1`
- Mutado:   `actual.primera_fila = fila[1].row + 1`

#### Análisis

- **Por qué ningún test lo caza**: todas las celdas de una fila de openpyxl comparten el mismo `.row`, así que `fila[0].row` y `fila[1].row` devuelven exactamente el mismo número.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G1 · el índice de celda no cambia el número de fila**: la mutación es sintáctica, no semántica, y ningún test puede distinguirla porque no hay nada que distinguir. Comprobado ejecutando sobre una hoja de dos filas: `fila[0].row == fila[1].row == fila[2].row` en todas.

### 23. `evals/revision/escritura.py:158` [aritmetico]

- Original: `actual.primera_fila = fila[0].row + 1`
- Mutado:   `actual.primera_fila = fila[0].row - 1`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 24. `evals/revision/escritura.py:159` [entero]

- Original: `actual.ultima_fila = max(hoja.max_row, fila[0].row)`
- Mutado:   `actual.ultima_fila = max(hoja.max_row, fila[1].row)`

#### Análisis

- **Por qué ningún test lo caza**: todas las celdas de una fila de openpyxl comparten el mismo `.row`, así que `fila[0].row` y `fila[1].row` devuelven exactamente el mismo número.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G1 · el índice de celda no cambia el número de fila**: la mutación es sintáctica, no semántica, y ningún test puede distinguirla porque no hay nada que distinguir. Comprobado ejecutando sobre una hoja de dos filas: `fila[0].row == fila[1].row == fila[2].row` en todas.

### 25. `evals/revision/escritura.py:189` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 26. `evals/revision/escritura.py:191` [logico]

- Original: `return bool(texto) and texto != "?"`
- Mutado:   `return bool(texto) or texto != "?"`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 27. `evals/revision/escritura.py:276` [booleano]

- Original: `cambia = False`
- Mutado:   `cambia = True`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 28. `evals/revision/escritura.py:287` [not]

- Original: `if not caso_ids or fila.get("caso_id") in caso_ids`
- Mutado:   `if caso_ids or fila.get("caso_id") in caso_ids`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 29. `evals/revision/escritura.py:295` [logico]

- Original: `if ejecutar and cambia:`
- Mutado:   `if ejecutar or cambia:`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 30. `evals/revision/escritura.py:319` [logico]

- Original: `ancho = len(bloque.encabezados or [])`
- Mutado:   `ancho = len(bloque.encabezados and [])`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 31. `evals/revision/escritura.py:320` [entero]

- Original: `ultima = bloque.primera_fila - 1`
- Mutado:   `ultima = bloque.primera_fila - 2`

#### Análisis

- **Por qué ningún test lo caza**: `ultima` es el centinela de «este bloque no tiene datos» y lo único que se hace con él es `sobrantes = ultima - primera + 1` y `if sobrantes > 0`: con `- 1` da 0 y con `- 2` da -1, y las dos ramas no borran nada.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G3 · aritmética sobre un centinela que solo se compara con «> 0»**. Comprobado: `_ultima_con_datos` tiene UN solo llamador, y `0 > 0` y `-1 > 0` son ambos falsos.

### 32. `evals/revision/escritura.py:322` [not]

- Original: `if not all(_vacia(celda.value) for celda in fila[:ancho]):`
- Mutado:   `if all(_vacia(celda.value) for celda in fila[:ancho]):`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 33. `evals/revision/escritura.py:323` [entero]

- Original: `ultima = fila[0].row`
- Mutado:   `ultima = fila[1].row`

#### Análisis

- **Por qué ningún test lo caza**: todas las celdas de una fila de openpyxl comparten el mismo `.row`, así que `fila[0].row` y `fila[1].row` devuelven exactamente el mismo número.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G1 · el índice de celda no cambia el número de fila**: la mutación es sintáctica, no semántica, y ningún test puede distinguirla porque no hay nada que distinguir. Comprobado ejecutando sobre una hoja de dos filas: `fila[0].row == fila[1].row == fila[2].row` en todas.

### 34. `evals/revision/escritura.py:329` [aritmetico]

- Original: `sobrantes = _ultima_con_datos(hoja, bloque) - bloque.primera_fila + 1`
- Mutado:   `sobrantes = _ultima_con_datos(hoja, bloque) - bloque.primera_fila - 1`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 35. `evals/revision/escritura.py:330` [entero]

- Original: `if sobrantes > 0:`
- Mutado:   `if sobrantes > 1:`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 36. `evals/revision/escritura.py:347` [logico]

- Original: `return ";".join(str(trozo) for trozo in valor) or None`
- Mutado:   `return ";".join(str(trozo) for trozo in valor) and None`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 37. `evals/revision/informe.py:45` [logico]

- Original: `f"- Libros escritos: {', '.join(informe.libros_escritos) or '(ninguno: en seco)'}",`
- Mutado:   `f"- Libros escritos: {', '.join(informe.libros_escritos) and '(ninguno: en seco)'}",`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 38. `evals/revision/informe.py:68` [comparacion]

- Original: `casos = [c.caso_id for c in informe.casos if c.clasificacion == clasificacion]`
- Mutado:   `casos = [c.caso_id for c in informe.casos if c.clasificacion != clasificacion]`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 39. `evals/revision/informe.py:69` [logico]

- Original: `lineas += [f"{titulo}: {', '.join(sorted(casos)) or '(ninguno)'}", ""]`
- Mutado:   `lineas += [f"{titulo}: {', '.join(sorted(casos)) and '(ninguno)'}", ""]`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 40. `evals/revision/informe.py:107` [aritmetico]

- Original: `lineas += ["Sin incidencias: cada caso tiene su documento.", ""]`
- Mutado:   `lineas -= ["Sin incidencias: cada caso tiene su documento.", ""]`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 41. `evals/revision/informe.py:162` [not]

- Original: `if not informe.avisos:`
- Mutado:   `if informe.avisos:`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 42. `evals/revision/lectura.py:25` [entero]

- Original: `Path(__file__).resolve().parents[1] / "inputs" / "fuente" / "evals_summary.xlsx"`
- Mutado:   `Path(__file__).resolve().parents[2] / "inputs" / "fuente" / "evals_summary.xlsx"`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 43. `evals/revision/lectura.py:92` [booleano]

- Original: `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)`
- Mutado:   `libro = openpyxl.load_workbook(ruta, data_only=False, read_only=True)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 44. `evals/revision/lectura.py:92` [booleano]

- Original: `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)`
- Mutado:   `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=False)`

#### Análisis

- **Por qué ningún test lo caza**: `read_only=True` devuelve una hoja de solo lectura, y lo único que hace `lectura.leer` con ella es `iter_rows(values_only=True)`, que funciona igual en los dos modos. El `read_only=False` está puesto por prudencia, no porque se use ninguna capacidad de escritura.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G5 · argumento que no cambia el resultado observable**. Comprobado ejecutando: `iter_rows(values_only=True)` devuelve exactamente las mismas filas con `read_only=True` y con `False`.

### 45. `evals/revision/lectura.py:104` [comparacion]

- Original: `clave: _celda(celdas[indice]) if indice < len(celdas) else None`
- Mutado:   `clave: _celda(celdas[indice]) if indice <= len(celdas) else None`

#### Análisis

- **Por qué ningún test lo caza**: openpyxl rellena cada fila hasta el ancho de la hoja, así que `len(celdas)` es constante y todos los índices caen por debajo; `indice == len(celdas)`, que es lo único que distinguiría `<` de `<=`, no se da nunca. El caso que parecía cubrirlo —una fila más corta que los encabezados— se comprueba en `test_f045_r1_una_fila_mas_corta_que_los_encabezados_no_revienta`, y pasa con los dos operadores porque openpyxl ya ha rellenado la fila.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G6 · mutación semánticamente idéntica**. Comprobado ejecutando: openpyxl rellena las filas cortas hasta el ancho de la hoja, así que `len(celdas)` es constante y el índice nunca roza el límite que distinguiría `<` de `<=`.

### 46. `evals/revision/lectura.py:117` [not]

- Original: `return valor is None or (isinstance(valor, str) and not valor.strip())`
- Mutado:   `return valor is None or (isinstance(valor, str) and valor.strip())`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 47. `evals/revision/mapa.py:64` [booleano]

- Original: `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "casos": completo}, ensure_ascii=True, indent=2, sort_keys=True`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 48. `evals/revision/mapa.py:64` [entero]

- Original: `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=3, sort_keys=True`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 49. `evals/revision/mapa.py:64` [booleano]

- Original: `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=False`

#### Análisis

- **Por qué sobrevivía**: la primera justificación decía que el fichero sale «byte a byte igual» con `sort_keys` en `True` o en `False`. **Era falsa**, y la tumbó el reviewer ejecutando: `guardar` monta cada registro en el orden de `CAMPOS` —`clave`, `codigo`, `nombre_original`, `formato`, `gemelo_de`, `pestana`, `familia_documento`—, que NO es alfabético, y es `sort_keys` quien lo reordena. Con `False` sale otro fichero y una reimportación reescribe el mapa entero por un cambio de forma, no de dato. Comprobado: `json.dumps` con las dos opciones sobre un registro real → `IGUALES: False`.
- **Decisión**: TEST NUEVO. `test_f045_r7_el_mapa_se_escribe_byte_a_byte_como_dice_su_docstring` fija el CONTENIDO escrito, no solo el orden de los casos. Reinyectado, el mutante **muere**.

### 50. `evals/revision/modelos.py:60` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 51. `evals/revision/modelos.py:84` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 52. `evals/revision/modelos.py:150` [entero]

- Original: `filas_leidas: int = 0`
- Mutado:   `filas_leidas: int = 1`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 53. `evals/revision/modelos.py:175` [entero]

- Original: `.setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 0})`
- Mutado:   `.setdefault(columna, {"valor": 1, "interrogante": 0, "vacia": 0})`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 54. `evals/revision/modelos.py:175` [entero]

- Original: `.setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 0})`
- Mutado:   `.setdefault(columna, {"valor": 0, "interrogante": 1, "vacia": 0})`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 55. `evals/revision/modelos.py:175` [entero]

- Original: `.setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 0})`
- Mutado:   `.setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 1})`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 56. `evals/revision/modelos.py:177` [comparacion]

- Original: `if valor == INTERROGANTE:`
- Mutado:   `if valor != INTERROGANTE:`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 57. `evals/revision/modelos.py:178` [aritmetico]

- Original: `cubo["interrogante"] += 1`
- Mutado:   `cubo["interrogante"] -= 1`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 58. `evals/revision/modelos.py:178` [entero]

- Original: `cubo["interrogante"] += 1`
- Mutado:   `cubo["interrogante"] += 2`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 59. `evals/revision/modelos.py:179` [comparacion]

- Original: `elif valor is None or (isinstance(valor, str) and not valor.strip()):`
- Mutado:   `elif valor is not None or (isinstance(valor, str) and not valor.strip()):`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 60. `evals/revision/modelos.py:179` [logico]

- Original: `elif valor is None or (isinstance(valor, str) and not valor.strip()):`
- Mutado:   `elif valor is None and (isinstance(valor, str) and not valor.strip()):`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 61. `evals/revision/modelos.py:179` [not]

- Original: `elif valor is None or (isinstance(valor, str) and not valor.strip()):`
- Mutado:   `elif valor is None or (isinstance(valor, str) and valor.strip()):`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 62. `evals/revision/modelos.py:180` [aritmetico]

- Original: `cubo["vacia"] += 1`
- Mutado:   `cubo["vacia"] -= 1`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 63. `evals/revision/modelos.py:180` [entero]

- Original: `cubo["vacia"] += 1`
- Mutado:   `cubo["vacia"] += 2`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 64. `evals/revision/modelos.py:182` [aritmetico]

- Original: `cubo["valor"] += 1`
- Mutado:   `cubo["valor"] -= 1`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 65. `evals/revision/modelos.py:182` [entero]

- Original: `cubo["valor"] += 1`
- Mutado:   `cubo["valor"] += 2`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 66. `evals/revision/modelos.py:186` [entero]

- Original: `reparto = {NO_REGRESION: 0, DEFECTO_CONOCIDO: 0}`
- Mutado:   `reparto = {NO_REGRESION: 1, DEFECTO_CONOCIDO: 0}`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 67. `evals/revision/modelos.py:186` [entero]

- Original: `reparto = {NO_REGRESION: 0, DEFECTO_CONOCIDO: 0}`
- Mutado:   `reparto = {NO_REGRESION: 0, DEFECTO_CONOCIDO: 1}`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 68. `evals/revision/modelos.py:188` [aritmetico]

- Original: `reparto[caso.clasificacion] += 1`
- Mutado:   `reparto[caso.clasificacion] -= 1`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 69. `evals/revision/modelos.py:188` [entero]

- Original: `reparto[caso.clasificacion] += 1`
- Mutado:   `reparto[caso.clasificacion] += 2`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 70. `evals/revision/reparto.py:164` [logico]

- Original: `"gemelo_de": caso.gemelo_de or None,`
- Mutado:   `"gemelo_de": caso.gemelo_de and None,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 71. `evals/revision/reparto.py:180` [entero]

- Original: `ultimos[prefijo] = max(ultimos.get(prefijo, 0), numero)`
- Mutado:   `ultimos[prefijo] = max(ultimos.get(prefijo, 1), numero)`

#### Análisis

- **Por qué ningún test lo caza**: `max(ultimos.get(prefijo, 0), numero)` con el defecto a 1 solo daría otro resultado si existiera un caso numerado 0, y el formateo `{:03d}` empieza en 1: `RES-000` no lo produce nadie.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G5 · argumento que no cambia el resultado observable**. Comprobado: `max(0, n) == max(1, n)` para todo n de 1 a 999, y `{:03d}` no produce el 0.

### 72. `evals/revision/reparto.py:206` [logico]

- Original: `if isinstance(valor, bool) or valor is None:`
- Mutado:   `if isinstance(valor, bool) and valor is None:`

#### Análisis

- **Por qué ningún test lo caza**: con `and`, `_numero(None)` deja de cortar en la primera guarda pero acaba en el mismo sitio: `isinstance(None, (int, float))` es falso, `str(None).strip()` da `'None'`, `float('None')` levanta `ValueError` y el `except` devuelve el valor original, que es `None`. Y para un booleano el camino largo acierta también, porque `bool` es subclase de `int`.
- **Decisión**: MUTANTE EQUIVALENTE, justificado. Grupo **G6 · mutación semánticamente idéntica**. La guarda está por legibilidad y para no depender del `except`, no porque cambie el resultado. Comprobado ejecutando las dos versiones sobre `None`, `True`, `False`, `0`, `7`, `'72,50'`, `''` y `'no es'`: idéntica salida.

### 73. `evals/revision/reparto.py:206` [comparacion]

- Original: `if isinstance(valor, bool) or valor is None:`
- Mutado:   `if isinstance(valor, bool) or valor is not None:`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 74. `evals/revision/reparto.py:214` [comparacion]

- Original: `return float(texto.replace(",", ".")) if texto.count(",") == 1 else float(texto)`
- Mutado:   `return float(texto.replace(",", ".")) if texto.count(",") != 1 else float(texto)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 75. `evals/revision/reparto.py:214` [entero]

- Original: `return float(texto.replace(",", ".")) if texto.count(",") == 1 else float(texto)`
- Mutado:   `return float(texto.replace(",", ".")) if texto.count(",") == 2 else float(texto)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 76. `evals/revision/reparto.py:336` [logico]

- Original: `comentario = " | ".join(caso.comentarios) or None`
- Mutado:   `comentario = " | ".join(caso.comentarios) and None`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 77. `evals/revision/reparto.py:445` [logico]

- Original: `"comentario": linea.fila.texto("comentarios") or None,`
- Mutado:   `"comentario": linea.fila.texto("comentarios") and None,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 78. `evals/revision/reparto.py:475` [logico]

- Original: `"comentario": linea.fila.texto("comentarios") or None,`
- Mutado:   `"comentario": linea.fila.texto("comentarios") and None,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 79. `evals/revision/reparto.py:493` [logico]

- Original: `"comentario": linea.fila.texto("comentarios") or None,`
- Mutado:   `"comentario": linea.fila.texto("comentarios") and None,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 80. `evals/revision/reparto.py:507` [logico]

- Original: `"comentario": linea.fila.texto("comentarios") or None,`
- Mutado:   `"comentario": linea.fila.texto("comentarios") and None,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 81. `evals/revision/reparto.py:556` [logico]

- Original: `"unidad": linea.fila.texto("unidad") or None,`
- Mutado:   `"unidad": linea.fila.texto("unidad") and None,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 82. `evals/revision/reparto.py:576` [logico]

- Original: `"fichero": caso.fichero or None,`
- Mutado:   `"fichero": caso.fichero and None,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 83. `evals/revision/reparto.py:578` [logico]

- Original: `"proveedor": primera.texto("nombre_empresa") or INTERROGANTE,`
- Mutado:   `"proveedor": primera.texto("nombre_empresa") and INTERROGANTE,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 84. `evals/revision/reparto.py:580` [logico]

- Original: `"fecha": primera.texto("fecha") or INTERROGANTE,`
- Mutado:   `"fecha": primera.texto("fecha") and INTERROGANTE,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 85. `evals/revision/reparto.py:601` [entero]

- Original: `return int(total) if float(total).is_integer() else round(total, 2)`
- Mutado:   `return int(total) if float(total).is_integer() else round(total, 3)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 86. `evals/revision/reparto.py:606` [comparacion]

- Original: `casa = linea.origen_contrato == "contrato"`
- Mutado:   `casa = linea.origen_contrato != "contrato"`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 87. `evals/revision/vocabulario.py:58` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 88. `evals/revision/vocabulario.py:72` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 89. `evals/revision/vocabulario.py:162` [entero]

- Original: `key=lambda par: len(par[0]),`
- Mutado:   `key=lambda par: len(par[1]),`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).

### 90. `evals/revision/vocabulario.py:163` [booleano]

- Original: `reverse=True,`
- Mutado:   `reverse=False,`

#### Análisis

- **Por qué sobrevivía**: la campaña del 2026-09-15 midió el banco ANTES de los tests de T18; nadie comprobaba esa línea.
- **Decisión**: TEST NUEVO. Reinyectado uno a uno tras escribirlo, este mutante **muere** (`reinyección individual con la suite acotada a F-045`).
