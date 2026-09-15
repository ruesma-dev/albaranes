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

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/revision/__main__.py:29` [entero]

- Original: `RUTA_INFORME = Path(__file__).resolve().parents[2] / "progress" / "import_F-045.md"`
- Mutado:   `RUTA_INFORME = Path(__file__).resolve().parents[3] / "progress" / "import_F-045.md"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `evals/revision/__main__.py:32` [entero]

- Original: `RUTA_ORIGINALES = Path(__file__).resolve().parents[1] / "inputs" / "albaranes"`
- Mutado:   `RUTA_ORIGINALES = Path(__file__).resolve().parents[2] / "inputs" / "albaranes"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `evals/revision/__main__.py:40` [booleano]

- Original: `dry_run: bool = False,`
- Mutado:   `dry_run: bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `evals/revision/__main__.py:41` [booleano]

- Original: `renombrar: bool = False,`
- Mutado:   `renombrar: bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `evals/revision/__main__.py:135` [logico]

- Original: `"gemelo_de": copia.gemelo_de or None,`
- Mutado:   `"gemelo_de": copia.gemelo_de and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `evals/revision/__main__.py:143` [logico]

- Original: `registro.setdefault("gemelo_de", caso.gemelo_de or None)`
- Mutado:   `registro.setdefault("gemelo_de", caso.gemelo_de and None)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `evals/revision/__main__.py:176` [booleano]

- Original: `creadas = False`
- Mutado:   `creadas = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `evals/revision/__main__.py:198` [booleano]

- Original: `ruta, pestana, _definiciones(defs), filas, caso_ids, ejecutar=False`
- Mutado:   `ruta, pestana, _definiciones(defs), filas, caso_ids, ejecutar=True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `evals/revision/__main__.py:277` [booleano]

- Original: `destino.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `destino.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `evals/revision/albaranes.py:67` [entero]

- Original: `return tronco.rsplit("_", 1)[-1].strip() if "_" in tronco else tronco`
- Mutado:   `return tronco.rsplit("_", 2)[-1].strip() if "_" in tronco else tronco`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `evals/revision/albaranes.py:113` [comparacion]

- Original: `or (len(sin_ceros(codigo)) >= MINIMO_SUBCADENA and sin_ceros(codigo) in tronco)`
- Mutado:   `or (len(sin_ceros(codigo)) > MINIMO_SUBCADENA and sin_ceros(codigo) in tronco)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `evals/revision/albaranes.py:120` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `evals/revision/albaranes.py:134` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `evals/revision/escritura.py:62` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `evals/revision/escritura.py:75` [entero]

- Original: `fila_encabezados: int = 0`
- Mutado:   `fila_encabezados: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `evals/revision/escritura.py:77` [entero]

- Original: `primera_fila: int = 0`
- Mutado:   `primera_fila: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `evals/revision/escritura.py:78` [entero]

- Original: `ultima_fila: int = 0`
- Mutado:   `ultima_fila: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `evals/revision/escritura.py:91` [booleano]

- Original: `destino.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `destino.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `evals/revision/escritura.py:146` [entero]

- Original: `actual.ultima_fila = fila[0].row - 1`
- Mutado:   `actual.ultima_fila = fila[1].row - 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `evals/revision/escritura.py:146` [entero]

- Original: `actual.ultima_fila = fila[0].row - 1`
- Mutado:   `actual.ultima_fila = fila[0].row - 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `evals/revision/escritura.py:157` [entero]

- Original: `actual.fila_encabezados = fila[0].row`
- Mutado:   `actual.fila_encabezados = fila[1].row`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `evals/revision/escritura.py:158` [entero]

- Original: `actual.primera_fila = fila[0].row + 1`
- Mutado:   `actual.primera_fila = fila[1].row + 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `evals/revision/escritura.py:158` [aritmetico]

- Original: `actual.primera_fila = fila[0].row + 1`
- Mutado:   `actual.primera_fila = fila[0].row - 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `evals/revision/escritura.py:159` [entero]

- Original: `actual.ultima_fila = max(hoja.max_row, fila[0].row)`
- Mutado:   `actual.ultima_fila = max(hoja.max_row, fila[1].row)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `evals/revision/escritura.py:189` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `evals/revision/escritura.py:191` [logico]

- Original: `return bool(texto) and texto != "?"`
- Mutado:   `return bool(texto) or texto != "?"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `evals/revision/escritura.py:276` [booleano]

- Original: `cambia = False`
- Mutado:   `cambia = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `evals/revision/escritura.py:287` [not]

- Original: `if not caso_ids or fila.get("caso_id") in caso_ids`
- Mutado:   `if caso_ids or fila.get("caso_id") in caso_ids`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `evals/revision/escritura.py:295` [logico]

- Original: `if ejecutar and cambia:`
- Mutado:   `if ejecutar or cambia:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `evals/revision/escritura.py:319` [logico]

- Original: `ancho = len(bloque.encabezados or [])`
- Mutado:   `ancho = len(bloque.encabezados and [])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `evals/revision/escritura.py:320` [entero]

- Original: `ultima = bloque.primera_fila - 1`
- Mutado:   `ultima = bloque.primera_fila - 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `evals/revision/escritura.py:322` [not]

- Original: `if not all(_vacia(celda.value) for celda in fila[:ancho]):`
- Mutado:   `if all(_vacia(celda.value) for celda in fila[:ancho]):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `evals/revision/escritura.py:323` [entero]

- Original: `ultima = fila[0].row`
- Mutado:   `ultima = fila[1].row`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `evals/revision/escritura.py:329` [aritmetico]

- Original: `sobrantes = _ultima_con_datos(hoja, bloque) - bloque.primera_fila + 1`
- Mutado:   `sobrantes = _ultima_con_datos(hoja, bloque) - bloque.primera_fila - 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `evals/revision/escritura.py:330` [entero]

- Original: `if sobrantes > 0:`
- Mutado:   `if sobrantes > 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `evals/revision/escritura.py:347` [logico]

- Original: `return ";".join(str(trozo) for trozo in valor) or None`
- Mutado:   `return ";".join(str(trozo) for trozo in valor) and None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `evals/revision/informe.py:45` [logico]

- Original: `f"- Libros escritos: {', '.join(informe.libros_escritos) or '(ninguno: en seco)'}",`
- Mutado:   `f"- Libros escritos: {', '.join(informe.libros_escritos) and '(ninguno: en seco)'}",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `evals/revision/informe.py:68` [comparacion]

- Original: `casos = [c.caso_id for c in informe.casos if c.clasificacion == clasificacion]`
- Mutado:   `casos = [c.caso_id for c in informe.casos if c.clasificacion != clasificacion]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `evals/revision/informe.py:69` [logico]

- Original: `lineas += [f"{titulo}: {', '.join(sorted(casos)) or '(ninguno)'}", ""]`
- Mutado:   `lineas += [f"{titulo}: {', '.join(sorted(casos)) and '(ninguno)'}", ""]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `evals/revision/informe.py:107` [aritmetico]

- Original: `lineas += ["Sin incidencias: cada caso tiene su documento.", ""]`
- Mutado:   `lineas -= ["Sin incidencias: cada caso tiene su documento.", ""]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `evals/revision/informe.py:162` [not]

- Original: `if not informe.avisos:`
- Mutado:   `if informe.avisos:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `evals/revision/lectura.py:25` [entero]

- Original: `Path(__file__).resolve().parents[1] / "inputs" / "fuente" / "evals_summary.xlsx"`
- Mutado:   `Path(__file__).resolve().parents[2] / "inputs" / "fuente" / "evals_summary.xlsx"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `evals/revision/lectura.py:92` [booleano]

- Original: `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)`
- Mutado:   `libro = openpyxl.load_workbook(ruta, data_only=False, read_only=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `evals/revision/lectura.py:92` [booleano]

- Original: `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)`
- Mutado:   `libro = openpyxl.load_workbook(ruta, data_only=True, read_only=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 45. `evals/revision/lectura.py:104` [comparacion]

- Original: `clave: _celda(celdas[indice]) if indice < len(celdas) else None`
- Mutado:   `clave: _celda(celdas[indice]) if indice <= len(celdas) else None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 46. `evals/revision/lectura.py:117` [not]

- Original: `return valor is None or (isinstance(valor, str) and not valor.strip())`
- Mutado:   `return valor is None or (isinstance(valor, str) and valor.strip())`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 47. `evals/revision/mapa.py:64` [booleano]

- Original: `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "casos": completo}, ensure_ascii=True, indent=2, sort_keys=True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 48. `evals/revision/mapa.py:64` [entero]

- Original: `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=3, sort_keys=True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 49. `evals/revision/mapa.py:64` [booleano]

- Original: `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=True`
- Mutado:   `{"_doc": _DOC, "casos": completo}, ensure_ascii=False, indent=2, sort_keys=False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 50. `evals/revision/modelos.py:60` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 51. `evals/revision/modelos.py:84` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 52. `evals/revision/modelos.py:150` [entero]

- Original: `filas_leidas: int = 0`
- Mutado:   `filas_leidas: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 53. `evals/revision/modelos.py:175` [entero]

- Original: `.setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 0})`
- Mutado:   `.setdefault(columna, {"valor": 1, "interrogante": 0, "vacia": 0})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 54. `evals/revision/modelos.py:175` [entero]

- Original: `.setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 0})`
- Mutado:   `.setdefault(columna, {"valor": 0, "interrogante": 1, "vacia": 0})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 55. `evals/revision/modelos.py:175` [entero]

- Original: `.setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 0})`
- Mutado:   `.setdefault(columna, {"valor": 0, "interrogante": 0, "vacia": 1})`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 56. `evals/revision/modelos.py:177` [comparacion]

- Original: `if valor == INTERROGANTE:`
- Mutado:   `if valor != INTERROGANTE:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 57. `evals/revision/modelos.py:178` [aritmetico]

- Original: `cubo["interrogante"] += 1`
- Mutado:   `cubo["interrogante"] -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 58. `evals/revision/modelos.py:178` [entero]

- Original: `cubo["interrogante"] += 1`
- Mutado:   `cubo["interrogante"] += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 59. `evals/revision/modelos.py:179` [comparacion]

- Original: `elif valor is None or (isinstance(valor, str) and not valor.strip()):`
- Mutado:   `elif valor is not None or (isinstance(valor, str) and not valor.strip()):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 60. `evals/revision/modelos.py:179` [logico]

- Original: `elif valor is None or (isinstance(valor, str) and not valor.strip()):`
- Mutado:   `elif valor is None and (isinstance(valor, str) and not valor.strip()):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 61. `evals/revision/modelos.py:179` [not]

- Original: `elif valor is None or (isinstance(valor, str) and not valor.strip()):`
- Mutado:   `elif valor is None or (isinstance(valor, str) and valor.strip()):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 62. `evals/revision/modelos.py:180` [aritmetico]

- Original: `cubo["vacia"] += 1`
- Mutado:   `cubo["vacia"] -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 63. `evals/revision/modelos.py:180` [entero]

- Original: `cubo["vacia"] += 1`
- Mutado:   `cubo["vacia"] += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 64. `evals/revision/modelos.py:182` [aritmetico]

- Original: `cubo["valor"] += 1`
- Mutado:   `cubo["valor"] -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 65. `evals/revision/modelos.py:182` [entero]

- Original: `cubo["valor"] += 1`
- Mutado:   `cubo["valor"] += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 66. `evals/revision/modelos.py:186` [entero]

- Original: `reparto = {NO_REGRESION: 0, DEFECTO_CONOCIDO: 0}`
- Mutado:   `reparto = {NO_REGRESION: 1, DEFECTO_CONOCIDO: 0}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 67. `evals/revision/modelos.py:186` [entero]

- Original: `reparto = {NO_REGRESION: 0, DEFECTO_CONOCIDO: 0}`
- Mutado:   `reparto = {NO_REGRESION: 0, DEFECTO_CONOCIDO: 1}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 68. `evals/revision/modelos.py:188` [aritmetico]

- Original: `reparto[caso.clasificacion] += 1`
- Mutado:   `reparto[caso.clasificacion] -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 69. `evals/revision/modelos.py:188` [entero]

- Original: `reparto[caso.clasificacion] += 1`
- Mutado:   `reparto[caso.clasificacion] += 2`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 70. `evals/revision/reparto.py:164` [logico]

- Original: `"gemelo_de": caso.gemelo_de or None,`
- Mutado:   `"gemelo_de": caso.gemelo_de and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 71. `evals/revision/reparto.py:180` [entero]

- Original: `ultimos[prefijo] = max(ultimos.get(prefijo, 0), numero)`
- Mutado:   `ultimos[prefijo] = max(ultimos.get(prefijo, 1), numero)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 72. `evals/revision/reparto.py:206` [logico]

- Original: `if isinstance(valor, bool) or valor is None:`
- Mutado:   `if isinstance(valor, bool) and valor is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 73. `evals/revision/reparto.py:206` [comparacion]

- Original: `if isinstance(valor, bool) or valor is None:`
- Mutado:   `if isinstance(valor, bool) or valor is not None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 74. `evals/revision/reparto.py:214` [comparacion]

- Original: `return float(texto.replace(",", ".")) if texto.count(",") == 1 else float(texto)`
- Mutado:   `return float(texto.replace(",", ".")) if texto.count(",") != 1 else float(texto)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 75. `evals/revision/reparto.py:214` [entero]

- Original: `return float(texto.replace(",", ".")) if texto.count(",") == 1 else float(texto)`
- Mutado:   `return float(texto.replace(",", ".")) if texto.count(",") == 2 else float(texto)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 76. `evals/revision/reparto.py:336` [logico]

- Original: `comentario = " | ".join(caso.comentarios) or None`
- Mutado:   `comentario = " | ".join(caso.comentarios) and None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 77. `evals/revision/reparto.py:445` [logico]

- Original: `"comentario": linea.fila.texto("comentarios") or None,`
- Mutado:   `"comentario": linea.fila.texto("comentarios") and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 78. `evals/revision/reparto.py:475` [logico]

- Original: `"comentario": linea.fila.texto("comentarios") or None,`
- Mutado:   `"comentario": linea.fila.texto("comentarios") and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 79. `evals/revision/reparto.py:493` [logico]

- Original: `"comentario": linea.fila.texto("comentarios") or None,`
- Mutado:   `"comentario": linea.fila.texto("comentarios") and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 80. `evals/revision/reparto.py:507` [logico]

- Original: `"comentario": linea.fila.texto("comentarios") or None,`
- Mutado:   `"comentario": linea.fila.texto("comentarios") and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 81. `evals/revision/reparto.py:556` [logico]

- Original: `"unidad": linea.fila.texto("unidad") or None,`
- Mutado:   `"unidad": linea.fila.texto("unidad") and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 82. `evals/revision/reparto.py:576` [logico]

- Original: `"fichero": caso.fichero or None,`
- Mutado:   `"fichero": caso.fichero and None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 83. `evals/revision/reparto.py:578` [logico]

- Original: `"proveedor": primera.texto("nombre_empresa") or INTERROGANTE,`
- Mutado:   `"proveedor": primera.texto("nombre_empresa") and INTERROGANTE,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 84. `evals/revision/reparto.py:580` [logico]

- Original: `"fecha": primera.texto("fecha") or INTERROGANTE,`
- Mutado:   `"fecha": primera.texto("fecha") and INTERROGANTE,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 85. `evals/revision/reparto.py:601` [entero]

- Original: `return int(total) if float(total).is_integer() else round(total, 2)`
- Mutado:   `return int(total) if float(total).is_integer() else round(total, 3)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 86. `evals/revision/reparto.py:606` [comparacion]

- Original: `casa = linea.origen_contrato == "contrato"`
- Mutado:   `casa = linea.origen_contrato != "contrato"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 87. `evals/revision/vocabulario.py:58` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 88. `evals/revision/vocabulario.py:72` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 89. `evals/revision/vocabulario.py:162` [entero]

- Original: `key=lambda par: len(par[0]),`
- Mutado:   `key=lambda par: len(par[1]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 90. `evals/revision/vocabulario.py:163` [booleano]

- Original: `reverse=True,`
- Mutado:   `reverse=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

