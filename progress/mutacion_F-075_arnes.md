<!-- progress/mutacion_F-075_arnes.md -->
# F-075 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-075` el 2026-10-18 19:03.

## Alcance

Origen del diff: **rama** (`a3c9e6a36287b5feaad69ada3015eded2f5599ba` .. `feature/F-075-importe-leido`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/conversor.py` | 7 |
| `evals/informe.py` | 18 |
| `evals/modelos.py` | 2 |
| `evals/procesos/sv2_extraccion.py` | 26 |
| `evals/procesos/sv2_obra.py` | 40 |
| `evals/procesos/sv2_proveedor.py` | 17 |
| `evals/runner.py` | 6 |
| `services/albaran-valoracion-api/application/pipelines/value_albaran_pipeline.py` | 5 |
| `services/albaran-valoracion-persist/application/pipelines/run_valuation_pipeline.py` | 48 |
| `services/albaran-valoracion-persist/application/services/valoracion_directa.py` | 181 |
| `services/albaranes-api/application/services/phase_merge.py` | 24 |
| `services/albaranes-api/domain/models/albaran_models.py` | 7 |
| `services/albaranes-comun/ruesma_comun/importes.py` | 168 |
| `services/albaranes-front/domain/models/review_models.py` | 178 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 156 |
| `services/albaranes-front/interface_adapters/web/app.py` | 13 |
| `services/albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py` | 58 |
| `services/albaranes-persistencia/application/services/albaran_confidence_service.py` | 7 |
| `services/albaranes-persistencia/application/services/albaran_normalizer.py` | 5 |
| `services/albaranes-persistencia/application/services/pie_guard_service.py` | 135 |
| `services/albaranes-persistencia/config/settings.py` | 4 |
| `services/albaranes-persistencia/domain/models/extraction_models.py` | 6 |
| `services/albaranes-persistencia/domain/ports/albaran_repository.py` | 6 |
| `services/albaranes-persistencia/infrastructure/database/orm_models.py` | 7 |
| `services/albaranes-persistencia/infrastructure/database/phase2_ddl.py` | 22 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 82 |
| `services/albaranes-persistencia/interface_adapters/api/app.py` | 8 |
| `services/albaranes-persistencia/interface_adapters/composition.py` | 8 |
| **Total** | **1244** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 175 |
| Mutantes evaluados | 175 |
| Muertos | 153 |
| Supervivientes | 22 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 5586.7 s |
| SHA de HEAD medido | `d33f00961ec8dfd9fc19ae6c66b2ba664ef29f5b` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_0` | 320.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_0/services/albaran-valoracion-persist` | 27.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_0/services/albaranes-api` | 19.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_0/services/albaranes-comun` | 137.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_0/services/albaranes-front` | 238.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_0/services/albaranes-persistencia` | 34.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_1` | 330.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_1/services/albaran-valoracion-persist` | 16.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_1/services/albaranes-api` | 19.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_1/services/albaranes-comun` | 129.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_1/services/albaranes-front` | 243.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_1/services/albaranes-persistencia` | 47.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_2` | 330.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_2/services/albaran-valoracion-persist` | 16.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_2/services/albaranes-api` | 20.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_2/services/albaranes-comun` | 123.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_2/services/albaranes-front` | 244.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_2/services/albaranes-persistencia` | 32.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_3` | 320.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_3/services/albaran-valoracion-persist` | 27.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_3/services/albaranes-api` | 19.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_3/services/albaranes-comun` | 133.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_3/services/albaranes-front` | 241.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-075_a8hb3ozc/wk_3/services/albaranes-persistencia` | 35.2 |
| Media por mutante evaluado (s) | 31.9 |
| Timeout efectivo por mutante (s) | 662 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/procesos/sv2_proveedor.py:100` [booleano]

- Original: `def montar_servicio(ficheros: dict[str, Path], especificaciones: list, *, sin_pie: bool = False):`
- Mutado:   `def montar_servicio(ficheros: dict[str, Path], especificaciones: list, *, sin_pie: bool = True):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `evals/procesos/sv2_proveedor.py:110` [booleano]

- Original: `def _servicio(ficheros: dict[str, Path], especificaciones: list, *, sin_pie: bool = False):  # pragma: no cover - subproceso del test de la base`
- Mutado:   `def _servicio(ficheros: dict[str, Path], especificaciones: list, *, sin_pie: bool = True):  # pragma: no cover - subproceso del test de la base`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `evals/procesos/sv2_proveedor.py:184` [comparacion]

- Original: `variante: montar_servicio(rutas, especificaciones, sin_pie=variante == "base")`
- Mutado:   `variante: montar_servicio(rutas, especificaciones, sin_pie=variante != "base")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `evals/runner.py:594` [logico]

- Original: `if opciones.con_llm and "IA1" in fases`
- Mutado:   `if opciones.con_llm or "IA1" in fases`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/albaranes-api/application/services/phase_merge.py:51` [logico]

- Original: `if not isinstance(cabecera2, dict) or not isinstance(cabecera1, dict):`
- Mutado:   `if not isinstance(cabecera2, dict) and not isinstance(cabecera1, dict):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/albaranes-comun/ruesma_comun/importes.py:254` [entero]

- Original: `if round(abs(suma_num - referencia), 2) <= tolerancia:`
- Mutado:   `if round(abs(suma_num - referencia), 3) <= tolerancia:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/albaranes-front/domain/models/review_models.py:273` [entero]

- Original: `lineas_albaran: int = 0`
- Mutado:   `lineas_albaran: int = 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/albaranes-front/domain/models/review_models.py:1714` [entero]

- Original: `return round(float(valorado) - float(albaran), 2)  # type: ignore[arg-type]`
- Mutado:   `return round(float(valorado) - float(albaran), 3)  # type: ignore[arg-type]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/albaranes-front/infrastructure/database/review_repository.py:636` [booleano]

- Original: `exc_info=True,`
- Mutado:   `exc_info=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/albaranes-front/infrastructure/database/review_repository.py:673` [booleano]

- Original: `exc_info=True,`
- Mutado:   `exc_info=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/albaranes-front/infrastructure/database/review_repository.py:808` [entero]

- Original: `importes_doc[row.id].lineas if row.id in importes_doc else 0`
- Mutado:   `importes_doc[row.id].lineas if row.id in importes_doc else 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/albaranes-front/infrastructure/database/review_repository.py:812` [entero]

- Original: `if row.id in importes_doc else 0`
- Mutado:   `if row.id in importes_doc else 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py:528` [comparacion]

- Original: `if self._pie_guard_service is None:`
- Mutado:   `if self._pie_guard_service is not None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:70` [entero]

- Original: `"base_imponible": {"weight": 0, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`
- Mutado:   `"base_imponible": {"weight": 1, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:70` [booleano]

- Original: `"base_imponible": {"weight": 0, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`
- Mutado:   `"base_imponible": {"weight": 0, "required": False, "critical": True, "kind": "number", "tolerance": 0.01},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:71` [entero]

- Original: `"tipo_iva_pct": {"weight": 0, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`
- Mutado:   `"tipo_iva_pct": {"weight": 1, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:71` [booleano]

- Original: `"tipo_iva_pct": {"weight": 0, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`
- Mutado:   `"tipo_iva_pct": {"weight": 0, "required": False, "critical": True, "kind": "number", "tolerance": 0.01},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:72` [entero]

- Original: `"cuota_iva": {"weight": 0, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`
- Mutado:   `"cuota_iva": {"weight": 1, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:72` [booleano]

- Original: `"cuota_iva": {"weight": 0, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`
- Mutado:   `"cuota_iva": {"weight": 0, "required": False, "critical": True, "kind": "number", "tolerance": 0.01},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:73` [entero]

- Original: `"total_albaran": {"weight": 0, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`
- Mutado:   `"total_albaran": {"weight": 1, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/albaranes-persistencia/application/services/albaran_confidence_service.py:73` [booleano]

- Original: `"total_albaran": {"weight": 0, "required": False, "critical": False, "kind": "number", "tolerance": 0.01},`
- Mutado:   `"total_albaran": {"weight": 0, "required": False, "critical": True, "kind": "number", "tolerance": 0.01},`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/albaranes-persistencia/config/settings.py:222` [booleano]

- Original: `pie_guard_enabled: bool = Field(True, alias="PIE_GUARD_ENABLED")`
- Mutado:   `pie_guard_enabled: bool = Field(False, alias="PIE_GUARD_ENABLED")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

