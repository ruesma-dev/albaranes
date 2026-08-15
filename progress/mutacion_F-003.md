<!-- progress/mutacion_F-003.md -->
# F-003 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-003` el 2026-08-15 13:19.

## Alcance

Origen del diff: **rama** (`c9bd5df571e750da532d212181ab80b44d26057e` .. `feature/F-003-valorados-match-estricto`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-api/application/pipelines/value_albaran_pipeline.py` | 17 |
| `services/albaran-valoracion-api/application/services/unit_category_prefilter.py` | 2 |
| `services/albaran-valoracion-api/domain/models/valuation_context.py` | 13 |
| `services/albaran-valoracion-api/domain/ports/valuation_context_repository.py` | 18 |
| `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py` | 59 |
| `services/albaran-valoracion-persist/application/services/atributo_sustantivo_guard.py` | 229 |
| `services/albaran-valoracion-persist/application/services/guard_aritmetico.py` | 186 |
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | 139 |
| `services/albaran-valoracion-persist/config/settings.py` | 23 |
| `services/albaran-valoracion-persist/domain/models/valuation_envelope.py` | 27 |
| `services/albaran-valoracion-persist/interface_adapters/api/app.py` | 6 |
| `services/albaran-valoracion-persist/interface_adapters/composition.py` | 6 |
| `services/albaranes-api/domain/models/albaran_models.py` | 23 |
| `services/albaranes-persistencia/application/services/albaran_confidence_service.py` | 66 |
| `services/albaranes-persistencia/application/services/descuento_cascada.py` | 75 |
| `services/albaranes-persistencia/domain/models/extraction_models.py` | 22 |
| `services/albaranes-persistencia/infrastructure/database/orm_models.py` | 22 |
| `services/albaranes-persistencia/infrastructure/database/schema_contribution.py` | 18 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 41 |
| **Total** | **992** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 90 |
| Mutantes evaluados | 90 |
| Muertos | 69 |
| Supervivientes | 21 |
| Timeouts | 0 |
| Tiempo total | 42.9 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py:372` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py:374` [booleano]

- Original: `return False`
- Mutado:   `return True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/albaran-valoracion-persist/application/services/atributo_sustantivo_guard.py:180` [logico]

- Original: `if albaran_line is None or contrato_line is None:`
- Mutado:   `if albaran_line is None and contrato_line is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/albaran-valoracion-persist/application/services/atributo_sustantivo_guard.py:222` [logico]

- Original: `(getattr(dto, "razon_corta", "") or "")`
- Mutado:   `(getattr(dto, "razon_corta", "") and "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/albaran-valoracion-persist/application/services/atributo_sustantivo_guard.py:225` [entero]

- Original: `)[:500]`
- Mutado:   `)[:501]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:38` [entero]

- Original: `_DECIMALES_MOTIVO = 2`
- Mutado:   `_DECIMALES_MOTIVO = 3`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:57` [comparacion]

- Original: `if a == 0.0 and b == 0.0:`
- Mutado:   `if a != 0.0 and b == 0.0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:57` [logico]

- Original: `if a == 0.0 and b == 0.0:`
- Mutado:   `if a == 0.0 or b == 0.0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:57` [comparacion]

- Original: `if a == 0.0 and b == 0.0:`
- Mutado:   `if a == 0.0 and b != 0.0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:60` [comparacion]

- Original: `return abs(a - b) / denominador * 100.0 <= float(tolerance_pct)`
- Mutado:   `return abs(a - b) / denominador * 100.0 < float(tolerance_pct)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:89` [comparacion]

- Original: `if descuento < 0.0 or descuento > 100.0:`
- Mutado:   `if descuento <= 0.0 or descuento > 100.0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:89` [logico]

- Original: `if descuento < 0.0 or descuento > 100.0:`
- Mutado:   `if descuento < 0.0 and descuento > 100.0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/albaran-valoracion-persist/application/services/guard_aritmetico.py:89` [comparacion]

- Original: `if descuento < 0.0 or descuento > 100.0:`
- Mutado:   `if descuento < 0.0 or descuento >= 100.0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/albaran-valoracion-persist/application/services/valuation_builder.py:499` [logico]

- Original: `and line.merge_line_id in albaran_by_id`
- Mutado:   `or line.merge_line_id in albaran_by_id`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/albaran-valoracion-persist/application/services/valuation_builder.py:1231` [not]

- Original: `or not category_match`
- Mutado:   `or category_match`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:1333` [aritmetico]

- Original: `tolerancia = max(0.15, abs(esperado) * 0.02)`
- Mutado:   `tolerancia = max(0.15, abs(esperado) // 0.02)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:1334` [comparacion]

- Original: `return abs(esperado - float(line.importe)) <= tolerancia`
- Mutado:   `return abs(esperado - float(line.importe)) < tolerancia`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:1337` [aritmetico]

- Original: `tolerancia = max(0.01, abs(precio_con_dto) * 0.02)`
- Mutado:   `tolerancia = max(0.01, abs(precio_con_dto) // 0.02)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:1338` [comparacion]

- Original: `return abs(precio_con_dto - float(line.precio_neto)) <= tolerancia`
- Mutado:   `return abs(precio_con_dto - float(line.precio_neto)) < tolerancia`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:1340` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:89` [booleano]

- Original: `return json.dumps(valores, ensure_ascii=False)`
- Mutado:   `return json.dumps(valores, ensure_ascii=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

