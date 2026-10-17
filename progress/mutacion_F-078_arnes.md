<!-- progress/mutacion_F-078_arnes.md -->
# F-078 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-078` el 2026-10-17 02:29.

## Alcance

Origen del diff: **rama** (`ac4d24af4884e66bd507240cac0f684fd665b2c1` .. `feature/F-078-linea-guarda-lo-que-se-ve`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/application/pipelines/run_valuation_pipeline.py` | 5 |
| `services/albaran-valoracion-persist/application/services/fila_completa.py` | 94 |
| `services/albaran-valoracion-persist/scripts/rellenar_filas_f078.py` | 257 |
| `services/albaranes-comun/ruesma_comun/linea_valorada.py` | 160 |
| `services/albaranes-front/domain/models/review_models.py` | 12 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 206 |
| **Total** | **734** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 81 |
| Mutantes evaluados | 81 |
| Muertos | 73 |
| Supervivientes | 8 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 2980.1 s |
| SHA de HEAD medido | `f3094c9e3ab4e3eb8bddf0abb240874ee8add096` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_0/services/albaran-valoracion-persist` | 23.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_0/services/albaranes-comun` | 190.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_0/services/albaranes-front` | 336.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_1/services/albaran-valoracion-persist` | 23.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_1/services/albaranes-comun` | 193.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_1/services/albaranes-front` | 331.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_2/services/albaran-valoracion-persist` | 23.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_2/services/albaranes-comun` | 194.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_2/services/albaranes-front` | 335.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_3/services/albaran-valoracion-persist` | 23.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_3/services/albaranes-comun` | 192.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-078_a8dhmmb8/wk_3/services/albaranes-front` | 331.9 |
| Media por mutante evaluado (s) | 36.8 |
| Timeout efectivo por mutante (s) | 674 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaran-valoracion-persist/scripts/rellenar_filas_f078.py:92` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/albaran-valoracion-persist/scripts/rellenar_filas_f078.py:230` [entero]

- Original: `parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])`
- Mutado:   `parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/albaranes-comun/ruesma_comun/linea_valorada.py:48` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/albaranes-comun/ruesma_comun/linea_valorada.py:61` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/albaranes-comun/ruesma_comun/linea_valorada.py:91` [comparacion]

- Original: `return abs(float(factor) - 1.0) <= TOLERANCIA_FACTOR`
- Mutado:   `return abs(float(factor) - 1.0) < TOLERANCIA_FACTOR`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/albaranes-front/infrastructure/database/review_repository.py:290` [comparacion]

- Original: `if fila["cl_id"] is not None:`
- Mutado:   `if fila["cl_id"] is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/albaranes-front/infrastructure/database/review_repository.py:295` [comparacion]

- Original: `if fila["d_id"] is not None:`
- Mutado:   `if fila["d_id"] is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/albaranes-front/infrastructure/database/review_repository.py:297` [booleano]

- Original: `es_contrato=False, descripcion=fila["d_descripcion"],`
- Mutado:   `es_contrato=True, descripcion=fila["d_descripcion"],`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

