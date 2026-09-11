<!-- progress/mutacion_F-043.md -->
# F-043 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-043` el 2026-09-10 17:56.

## Alcance

Origen del diff: **rama** (`e29ab4a514cd126ff19bf0f513e353e0ea048ae9` .. `feature/F-043-clasificacion-por-ia1`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-api/application/pipelines/value_albaran_pipeline.py` | 43 |
| `services/albaran-valoracion-api/application/services/valuation_extraction_service.py` | 39 |
| `services/albaran-valoracion-api/domain/models/albaran_models.py` | 21 |
| `services/albaran-valoracion-api/domain/models/valuation_context.py` | 16 |
| `services/albaran-valoracion-api/domain/ports/valuation_context_repository.py` | 12 |
| `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py` | 78 |
| `services/albaran-valoracion-persist/application/services/modifier_contract_matcher.py` | 14 |
| `services/albaran-valoracion-persist/application/services/residuos_container_calc.py` | 45 |
| `services/albaran-valoracion-persist/application/services/residuos_incrementos.py` | 239 |
| `services/albaran-valoracion-persist/application/services/valuation_builder.py` | 258 |
| `services/albaran-valoracion-persist/domain/models/valuation_envelope.py` | 20 |
| `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py` | 15 |
| `services/albaranes-api/application/services/albaran_extraction_service.py` | 95 |
| `services/albaranes-api/application/services/clasificacion_resolver.py` | 168 |
| `services/albaranes-api/application/services/phase_merge.py` | 29 |
| `services/albaranes-api/domain/models/albaran_models.py` | 17 |
| `services/albaranes-api/domain/models/tipologia.py` | 26 |
| `services/albaranes-api/interface_adapters/worker/extraction_worker.py` | 44 |
| `services/albaranes-comun/ruesma_comun/contratos/__init__.py` | 10 |
| `services/albaranes-comun/ruesma_comun/contratos/clasificacion.py` | 84 |
| `services/albaranes-comun/ruesma_comun/contratos/contexto_linea.py` | 14 |
| `services/albaranes-comun/ruesma_comun/contratos/familias.py` | 390 |
| `services/albaranes-comun/ruesma_comun/ler.py` | 144 |
| `services/albaranes-front/domain/models/review_models.py` | 247 |
| `services/albaranes-front/infrastructure/database/orm_models.py` | 14 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 301 |
| `services/albaranes-persistencia/application/services/albaran_confidence_service.py` | 123 |
| `services/albaranes-persistencia/application/services/contexto_linea_merger.py` | 125 |
| `services/albaranes-persistencia/config/settings.py` | 17 |
| `services/albaranes-persistencia/domain/models/extraction_models.py` | 13 |
| `services/albaranes-persistencia/infrastructure/database/orm_models.py` | 26 |
| `services/albaranes-persistencia/infrastructure/database/phase2_ddl.py` | 37 |
| `services/albaranes-persistencia/infrastructure/database/schema_contribution.py` | 2 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 71 |
| `services/albaranes-persistencia/interface_adapters/api/app.py` | 8 |
| `services/albaranes-persistencia/interface_adapters/composition.py` | 8 |
| `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py` | 174 |
| `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py` | 136 |
| **Total** | **3123** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 347 |
| Mutantes evaluados | 347 |
| Muertos | 181 |
| Supervivientes | 163 |
| Timeouts | 3 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 6895.6 s |
| SHA de HEAD medido | `48e3d179972a551edae9fe3d4851f9d4e4b233c4` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_0/services/albaran-valoracion-api` | 10.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_0/services/albaran-valoracion-persist` | 9.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_0/services/albaranes-api` | 11.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_0/services/albaranes-comun` | 137.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_0/services/albaranes-front` | 8.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_0/services/albaranes-persistencia` | 4.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_1/services/albaran-valoracion-api` | 10.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_1/services/albaran-valoracion-persist` | 9.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_1/services/albaranes-api` | 10.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_1/services/albaranes-comun` | 140.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_1/services/albaranes-front` | 6.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_1/services/albaranes-persistencia` | 4.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_2/services/albaran-valoracion-api` | 10.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_2/services/albaran-valoracion-persist` | 9.1 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_2/services/albaranes-api` | 11.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_2/services/albaranes-comun` | 137.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_2/services/albaranes-front` | 7.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_2/services/albaranes-persistencia` | 4.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_3/services/albaran-valoracion-api` | 13.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_3/services/albaran-valoracion-persist` | 9.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_3/services/albaranes-api` | 9.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_3/services/albaranes-comun` | 139.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_3/services/albaranes-front` | 6.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-043_jxbji67d/wk_3/services/albaranes-persistencia` | 4.5 |
| Media por mutante evaluado (s) | 19.9 |
| Timeout efectivo por mutante (s) | 282 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaran-valoracion-persist/application/services/modifier_contract_matcher.py:284` [logico]

- Original: `return lambda d: normalizar_ler(d) == ler or ler in d`
- Mutado:   `return lambda d: normalizar_ler(d) == ler and ler in d`

#### Análisis

> **Hueco real, CERRADO.** La rama existía pero ningún test la distinguía de su contraria: la suite de sv6 pasaba entera con el mutante puesto.
> **Decisión: test nuevo.** Commit `8f36c77` (tests de `test_f036_r15_r20_matcher_ler.py`, `test_f036_r16_r19_sinteticas_ler.py` y `test_f036_r22_contenedores_prioridades.py`). Reinyectado el 2026-09-11 contra la suite de sv6: **muere**. Grupo B de `progress/impl_F-043_T28_supervivientes.md`.

### 2. `services/albaran-valoracion-persist/application/services/residuos_container_calc.py:176` [comparacion]

- Original: `if resta >= 1:`
- Mutado:   `if resta > 1:`

#### Análisis

> **Hueco real, CERRADO.** La rama existía pero ningún test la distinguía de su contraria: la suite de sv6 pasaba entera con el mutante puesto.
> **Decisión: test nuevo.** Commit `8f36c77` (tests de `test_f036_r15_r20_matcher_ler.py`, `test_f036_r16_r19_sinteticas_ler.py` y `test_f036_r22_contenedores_prioridades.py`). Reinyectado el 2026-09-11 contra la suite de sv6: **muere**. Grupo B de `progress/impl_F-043_T28_supervivientes.md`.

### 3. `services/albaran-valoracion-persist/application/services/residuos_container_calc.py:176` [entero]

- Original: `if resta >= 1:`
- Mutado:   `if resta >= 2:`

#### Análisis

> **Hueco real, CERRADO.** La rama existía pero ningún test la distinguía de su contraria: la suite de sv6 pasaba entera con el mutante puesto.
> **Decisión: test nuevo.** Commit `8f36c77` (tests de `test_f036_r15_r20_matcher_ler.py`, `test_f036_r16_r19_sinteticas_ler.py` y `test_f036_r22_contenedores_prioridades.py`). Reinyectado el 2026-09-11 contra la suite de sv6: **muere**. Grupo B de `progress/impl_F-043_T28_supervivientes.md`.

### 4. `services/albaran-valoracion-persist/application/services/residuos_incrementos.py:126` [logico]

- Original: `if not ler or not contrato_lines:`
- Mutado:   `if not ler and not contrato_lines:`

#### Análisis

> **Hueco real, CERRADO.** La rama existía pero ningún test la distinguía de su contraria: la suite de sv6 pasaba entera con el mutante puesto.
> **Decisión: test nuevo.** Commit `8f36c77` (tests de `test_f036_r15_r20_matcher_ler.py`, `test_f036_r16_r19_sinteticas_ler.py` y `test_f036_r22_contenedores_prioridades.py`). Reinyectado el 2026-09-11 contra la suite de sv6: **muere**. Grupo B de `progress/impl_F-043_T28_supervivientes.md`.

### 5. `services/albaran-valoracion-persist/application/services/residuos_incrementos.py:176` [comparacion]

- Original: `"si" if tarifa is not None else "no",`
- Mutado:   `"si" if tarifa is None else "no",`

#### Análisis

> **Hueco real, CERRADO.** La rama existía pero ningún test la distinguía de su contraria: la suite de sv6 pasaba entera con el mutante puesto.
> **Decisión: test nuevo.** Commit `8f36c77` (tests de `test_f036_r15_r20_matcher_ler.py`, `test_f036_r16_r19_sinteticas_ler.py` y `test_f036_r22_contenedores_prioridades.py`). Reinyectado el 2026-09-11 contra la suite de sv6: **muere**. Grupo B de `progress/impl_F-043_T28_supervivientes.md`.

### 6. `services/albaran-valoracion-persist/application/services/residuos_incrementos.py:193` [comparacion]

- Original: `match_confidence_pct=90.0 if tarifa is not None else 0.0,`
- Mutado:   `match_confidence_pct=90.0 if tarifa is None else 0.0,`

#### Análisis

> **Hueco real, CERRADO.** La rama existía pero ningún test la distinguía de su contraria: la suite de sv6 pasaba entera con el mutante puesto.
> **Decisión: test nuevo.** Commit `8f36c77` (tests de `test_f036_r15_r20_matcher_ler.py`, `test_f036_r16_r19_sinteticas_ler.py` y `test_f036_r22_contenedores_prioridades.py`). Reinyectado el 2026-09-11 contra la suite de sv6: **muere**. Grupo B de `progress/impl_F-043_T28_supervivientes.md`.

### 7. `services/albaran-valoracion-persist/application/services/residuos_incrementos.py:201` [comparacion]

- Original: `"" if tarifa is not None`
- Mutado:   `"" if tarifa is None`

#### Análisis

> **Hueco real, CERRADO.** La rama existía pero ningún test la distinguía de su contraria: la suite de sv6 pasaba entera con el mutante puesto.
> **Decisión: test nuevo.** Commit `8f36c77` (tests de `test_f036_r15_r20_matcher_ler.py`, `test_f036_r16_r19_sinteticas_ler.py` y `test_f036_r22_contenedores_prioridades.py`). Reinyectado el 2026-09-11 contra la suite de sv6: **muere**. Grupo B de `progress/impl_F-043_T28_supervivientes.md`.

### 8. `services/albaran-valoracion-persist/application/services/valuation_builder.py:1532` [comparacion]

- Original: `elif parent_record is not None and parent_record.cantidad_albaran is not None:`
- Mutado:   `elif parent_record is not None and parent_record.cantidad_albaran is None:`

#### Análisis

> **Mutante EQUIVALENTE, no un hueco.** Los dos candidatos de la herencia salen del MISMO sitio: `parent_albaran = albaran_by_id.get(parent_merge_line_id)` y, dentro del `parent_record` que guardó la pasada 2 con esa misma clave, `cantidad_albaran = albaran_line.cantidad if albaran_line else None`. Caso por caso —hay línea con cantidad, hay línea con cantidad None, no hay línea— original y mutante dejan la misma `cantidad`.
> **Decisión: equivalente justificado, con guarda.** `services/albaran-valoracion-persist/tests/test_f043_t28_herencia_sintetica.py` NO lo mata —nada puede—: fija el invariante del que depende la justificación, que `cantidad_albaran` se COPIA de la línea de albarán de su propio `merge_line_id`. Verificado en rojo rompiéndolo por dos sitios. Grupo C de `progress/impl_F-043_T28_supervivientes.md`.

### 9. `services/albaran-valoracion-persist/application/services/valuation_builder.py:1708` [logico]

- Original: `and precio_final is None`
- Mutado:   `or precio_final is None`

#### Análisis

> **Hueco real, CERRADO.** La rama existía pero ningún test la distinguía de su contraria: la suite de sv6 pasaba entera con el mutante puesto.
> **Decisión: test nuevo.** Commit `8f36c77` (tests de `test_f036_r15_r20_matcher_ler.py`, `test_f036_r16_r19_sinteticas_ler.py` y `test_f036_r22_contenedores_prioridades.py`). Reinyectado el 2026-09-11 contra la suite de sv6: **muere**. Grupo B de `progress/impl_F-043_T28_supervivientes.md`.

### 10. `services/albaranes-comun/ruesma_comun/ler.py:51` [entero]

- Original: `1: frozenset({1, 3, 4, 5}),`
- Mutado:   `1: frozenset({1, 4, 4, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 11. `services/albaranes-comun/ruesma_comun/ler.py:51` [entero]

- Original: `1: frozenset({1, 3, 4, 5}),`
- Mutado:   `1: frozenset({1, 3, 5, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 12. `services/albaranes-comun/ruesma_comun/ler.py:51` [entero]

- Original: `1: frozenset({1, 3, 4, 5}),`
- Mutado:   `1: frozenset({1, 3, 4, 6}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 13. `services/albaranes-comun/ruesma_comun/ler.py:52` [entero]

- Original: `2: frozenset(range(1, 8)),`
- Mutado:   `3: frozenset(range(1, 8)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 14. `services/albaranes-comun/ruesma_comun/ler.py:52` [entero]

- Original: `2: frozenset(range(1, 8)),`
- Mutado:   `2: frozenset(range(2, 8)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 15. `services/albaranes-comun/ruesma_comun/ler.py:52` [entero]

- Original: `2: frozenset(range(1, 8)),`
- Mutado:   `2: frozenset(range(1, 9)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 16. `services/albaranes-comun/ruesma_comun/ler.py:53` [entero]

- Original: `3: frozenset({1, 2, 3}),`
- Mutado:   `4: frozenset({1, 2, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 17. `services/albaranes-comun/ruesma_comun/ler.py:53` [entero]

- Original: `3: frozenset({1, 2, 3}),`
- Mutado:   `3: frozenset({2, 2, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 18. `services/albaranes-comun/ruesma_comun/ler.py:53` [entero]

- Original: `3: frozenset({1, 2, 3}),`
- Mutado:   `3: frozenset({1, 3, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 19. `services/albaranes-comun/ruesma_comun/ler.py:53` [entero]

- Original: `3: frozenset({1, 2, 3}),`
- Mutado:   `3: frozenset({1, 2, 4}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 20. `services/albaranes-comun/ruesma_comun/ler.py:54` [entero]

- Original: `4: frozenset({1, 2}),`
- Mutado:   `5: frozenset({1, 2}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 21. `services/albaranes-comun/ruesma_comun/ler.py:54` [entero]

- Original: `4: frozenset({1, 2}),`
- Mutado:   `4: frozenset({2, 2}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 22. `services/albaranes-comun/ruesma_comun/ler.py:54` [entero]

- Original: `4: frozenset({1, 2}),`
- Mutado:   `4: frozenset({1, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 23. `services/albaranes-comun/ruesma_comun/ler.py:55` [entero]

- Original: `5: frozenset({1, 6, 7}),`
- Mutado:   `6: frozenset({1, 6, 7}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 24. `services/albaranes-comun/ruesma_comun/ler.py:55` [entero]

- Original: `5: frozenset({1, 6, 7}),`
- Mutado:   `5: frozenset({2, 6, 7}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 25. `services/albaranes-comun/ruesma_comun/ler.py:55` [entero]

- Original: `5: frozenset({1, 6, 7}),`
- Mutado:   `5: frozenset({1, 7, 7}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 26. `services/albaranes-comun/ruesma_comun/ler.py:55` [entero]

- Original: `5: frozenset({1, 6, 7}),`
- Mutado:   `5: frozenset({1, 6, 8}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 27. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `7: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 28. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 29. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 3, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 30. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 4, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 31. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 5, 5, 6, 7, 8, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 32. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 4, 6, 6, 7, 8, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 33. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 4, 5, 7, 7, 8, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 34. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 4, 5, 6, 8, 8, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 35. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 4, 5, 6, 7, 9, 9, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 36. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 10, 10, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 37. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 11, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 38. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 39. `services/albaranes-comun/ruesma_comun/ler.py:56` [entero]

- Original: `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13}),`
- Mutado:   `6: frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 40. `services/albaranes-comun/ruesma_comun/ler.py:57` [entero]

- Original: `7: frozenset(range(1, 8)),`
- Mutado:   `8: frozenset(range(1, 8)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 41. `services/albaranes-comun/ruesma_comun/ler.py:57` [entero]

- Original: `7: frozenset(range(1, 8)),`
- Mutado:   `7: frozenset(range(2, 8)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 42. `services/albaranes-comun/ruesma_comun/ler.py:57` [entero]

- Original: `7: frozenset(range(1, 8)),`
- Mutado:   `7: frozenset(range(1, 9)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 43. `services/albaranes-comun/ruesma_comun/ler.py:58` [entero]

- Original: `8: frozenset({1, 2, 3, 4, 5}),`
- Mutado:   `9: frozenset({1, 2, 3, 4, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 44. `services/albaranes-comun/ruesma_comun/ler.py:58` [entero]

- Original: `8: frozenset({1, 2, 3, 4, 5}),`
- Mutado:   `8: frozenset({2, 2, 3, 4, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 45. `services/albaranes-comun/ruesma_comun/ler.py:58` [entero]

- Original: `8: frozenset({1, 2, 3, 4, 5}),`
- Mutado:   `8: frozenset({1, 3, 3, 4, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 46. `services/albaranes-comun/ruesma_comun/ler.py:58` [entero]

- Original: `8: frozenset({1, 2, 3, 4, 5}),`
- Mutado:   `8: frozenset({1, 2, 4, 4, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 47. `services/albaranes-comun/ruesma_comun/ler.py:58` [entero]

- Original: `8: frozenset({1, 2, 3, 4, 5}),`
- Mutado:   `8: frozenset({1, 2, 3, 5, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 48. `services/albaranes-comun/ruesma_comun/ler.py:58` [entero]

- Original: `8: frozenset({1, 2, 3, 4, 5}),`
- Mutado:   `8: frozenset({1, 2, 3, 4, 6}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 49. `services/albaranes-comun/ruesma_comun/ler.py:59` [entero]

- Original: `9: frozenset({1}),`
- Mutado:   `10: frozenset({1}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 50. `services/albaranes-comun/ruesma_comun/ler.py:59` [entero]

- Original: `9: frozenset({1}),`
- Mutado:   `9: frozenset({2}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 51. `services/albaranes-comun/ruesma_comun/ler.py:60` [entero]

- Original: `10: frozenset(range(1, 15)),`
- Mutado:   `11: frozenset(range(1, 15)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 52. `services/albaranes-comun/ruesma_comun/ler.py:60` [entero]

- Original: `10: frozenset(range(1, 15)),`
- Mutado:   `10: frozenset(range(2, 15)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 53. `services/albaranes-comun/ruesma_comun/ler.py:60` [entero]

- Original: `10: frozenset(range(1, 15)),`
- Mutado:   `10: frozenset(range(1, 16)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 54. `services/albaranes-comun/ruesma_comun/ler.py:61` [entero]

- Original: `11: frozenset({1, 2, 3, 5}),`
- Mutado:   `12: frozenset({1, 2, 3, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 55. `services/albaranes-comun/ruesma_comun/ler.py:61` [entero]

- Original: `11: frozenset({1, 2, 3, 5}),`
- Mutado:   `11: frozenset({2, 2, 3, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 56. `services/albaranes-comun/ruesma_comun/ler.py:61` [entero]

- Original: `11: frozenset({1, 2, 3, 5}),`
- Mutado:   `11: frozenset({1, 3, 3, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 57. `services/albaranes-comun/ruesma_comun/ler.py:61` [entero]

- Original: `11: frozenset({1, 2, 3, 5}),`
- Mutado:   `11: frozenset({1, 2, 4, 5}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 58. `services/albaranes-comun/ruesma_comun/ler.py:61` [entero]

- Original: `11: frozenset({1, 2, 3, 5}),`
- Mutado:   `11: frozenset({1, 2, 3, 6}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 59. `services/albaranes-comun/ruesma_comun/ler.py:62` [entero]

- Original: `12: frozenset({1, 3}),`
- Mutado:   `13: frozenset({1, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 60. `services/albaranes-comun/ruesma_comun/ler.py:62` [entero]

- Original: `12: frozenset({1, 3}),`
- Mutado:   `12: frozenset({2, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 61. `services/albaranes-comun/ruesma_comun/ler.py:62` [entero]

- Original: `12: frozenset({1, 3}),`
- Mutado:   `12: frozenset({1, 4}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 62. `services/albaranes-comun/ruesma_comun/ler.py:63` [entero]

- Original: `13: frozenset({1, 2, 3, 4, 5, 7, 8}),`
- Mutado:   `14: frozenset({1, 2, 3, 4, 5, 7, 8}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 63. `services/albaranes-comun/ruesma_comun/ler.py:63` [entero]

- Original: `13: frozenset({1, 2, 3, 4, 5, 7, 8}),`
- Mutado:   `13: frozenset({2, 2, 3, 4, 5, 7, 8}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 64. `services/albaranes-comun/ruesma_comun/ler.py:63` [entero]

- Original: `13: frozenset({1, 2, 3, 4, 5, 7, 8}),`
- Mutado:   `13: frozenset({1, 3, 3, 4, 5, 7, 8}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 65. `services/albaranes-comun/ruesma_comun/ler.py:63` [entero]

- Original: `13: frozenset({1, 2, 3, 4, 5, 7, 8}),`
- Mutado:   `13: frozenset({1, 2, 4, 4, 5, 7, 8}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 66. `services/albaranes-comun/ruesma_comun/ler.py:63` [entero]

- Original: `13: frozenset({1, 2, 3, 4, 5, 7, 8}),`
- Mutado:   `13: frozenset({1, 2, 3, 5, 5, 7, 8}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 67. `services/albaranes-comun/ruesma_comun/ler.py:63` [entero]

- Original: `13: frozenset({1, 2, 3, 4, 5, 7, 8}),`
- Mutado:   `13: frozenset({1, 2, 3, 4, 6, 7, 8}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 68. `services/albaranes-comun/ruesma_comun/ler.py:63` [entero]

- Original: `13: frozenset({1, 2, 3, 4, 5, 7, 8}),`
- Mutado:   `13: frozenset({1, 2, 3, 4, 5, 8, 8}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 69. `services/albaranes-comun/ruesma_comun/ler.py:63` [entero]

- Original: `13: frozenset({1, 2, 3, 4, 5, 7, 8}),`
- Mutado:   `13: frozenset({1, 2, 3, 4, 5, 7, 9}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 70. `services/albaranes-comun/ruesma_comun/ler.py:64` [entero]

- Original: `14: frozenset({6}),`
- Mutado:   `15: frozenset({6}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 71. `services/albaranes-comun/ruesma_comun/ler.py:64` [entero]

- Original: `14: frozenset({6}),`
- Mutado:   `14: frozenset({7}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 72. `services/albaranes-comun/ruesma_comun/ler.py:65` [entero]

- Original: `15: frozenset({1, 2}),`
- Mutado:   `16: frozenset({1, 2}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 73. `services/albaranes-comun/ruesma_comun/ler.py:65` [entero]

- Original: `15: frozenset({1, 2}),`
- Mutado:   `15: frozenset({2, 2}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 74. `services/albaranes-comun/ruesma_comun/ler.py:65` [entero]

- Original: `15: frozenset({1, 2}),`
- Mutado:   `15: frozenset({1, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 75. `services/albaranes-comun/ruesma_comun/ler.py:66` [entero]

- Original: `16: frozenset(range(1, 12)),`
- Mutado:   `17: frozenset(range(1, 12)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 76. `services/albaranes-comun/ruesma_comun/ler.py:66` [entero]

- Original: `16: frozenset(range(1, 12)),`
- Mutado:   `16: frozenset(range(2, 12)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 77. `services/albaranes-comun/ruesma_comun/ler.py:66` [entero]

- Original: `16: frozenset(range(1, 12)),`
- Mutado:   `16: frozenset(range(1, 13)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 78. `services/albaranes-comun/ruesma_comun/ler.py:67` [entero]

- Original: `17: frozenset({1, 2, 3, 4, 5, 6, 8, 9}),`
- Mutado:   `17: frozenset({2, 2, 3, 4, 5, 6, 8, 9}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 79. `services/albaranes-comun/ruesma_comun/ler.py:67` [entero]

- Original: `17: frozenset({1, 2, 3, 4, 5, 6, 8, 9}),`
- Mutado:   `17: frozenset({1, 3, 3, 4, 5, 6, 8, 9}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 80. `services/albaranes-comun/ruesma_comun/ler.py:67` [entero]

- Original: `17: frozenset({1, 2, 3, 4, 5, 6, 8, 9}),`
- Mutado:   `17: frozenset({1, 2, 4, 4, 5, 6, 8, 9}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 81. `services/albaranes-comun/ruesma_comun/ler.py:67` [entero]

- Original: `17: frozenset({1, 2, 3, 4, 5, 6, 8, 9}),`
- Mutado:   `17: frozenset({1, 2, 3, 5, 5, 6, 8, 9}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 82. `services/albaranes-comun/ruesma_comun/ler.py:67` [entero]

- Original: `17: frozenset({1, 2, 3, 4, 5, 6, 8, 9}),`
- Mutado:   `17: frozenset({1, 2, 3, 4, 5, 7, 8, 9}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 83. `services/albaranes-comun/ruesma_comun/ler.py:67` [entero]

- Original: `17: frozenset({1, 2, 3, 4, 5, 6, 8, 9}),`
- Mutado:   `17: frozenset({1, 2, 3, 4, 5, 6, 9, 9}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 84. `services/albaranes-comun/ruesma_comun/ler.py:68` [entero]

- Original: `18: frozenset({1, 2}),`
- Mutado:   `19: frozenset({1, 2}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 85. `services/albaranes-comun/ruesma_comun/ler.py:68` [entero]

- Original: `18: frozenset({1, 2}),`
- Mutado:   `18: frozenset({2, 2}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 86. `services/albaranes-comun/ruesma_comun/ler.py:68` [entero]

- Original: `18: frozenset({1, 2}),`
- Mutado:   `18: frozenset({1, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 87. `services/albaranes-comun/ruesma_comun/ler.py:69` [entero]

- Original: `19: frozenset(range(1, 14)),`
- Mutado:   `20: frozenset(range(1, 14)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 88. `services/albaranes-comun/ruesma_comun/ler.py:69` [entero]

- Original: `19: frozenset(range(1, 14)),`
- Mutado:   `19: frozenset(range(2, 14)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 89. `services/albaranes-comun/ruesma_comun/ler.py:69` [entero]

- Original: `19: frozenset(range(1, 14)),`
- Mutado:   `19: frozenset(range(1, 15)),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 90. `services/albaranes-comun/ruesma_comun/ler.py:70` [entero]

- Original: `20: frozenset({1, 2, 3}),`
- Mutado:   `20: frozenset({2, 2, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 91. `services/albaranes-comun/ruesma_comun/ler.py:70` [entero]

- Original: `20: frozenset({1, 2, 3}),`
- Mutado:   `20: frozenset({1, 3, 3}),`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 92. `services/albaranes-comun/ruesma_comun/ler.py:133` [logico]

- Original: `if len(solo_digitos) != 6 or not es_ler_valido(solo_digitos):`
- Mutado:   `if len(solo_digitos) != 6 and not es_ler_valido(solo_digitos):`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 93. `services/albaranes-comun/ruesma_comun/ler.py:135` [entero]

- Original: `separador = m.group(2)`
- Mutado:   `separador = m.group(3)`

#### Análisis

> **Hueco real, CERRADO.** El catálogo `_CAPITULOS_LER` se daba por bueno entero: ningún test comprobaba capítulo a capítulo qué subcapítulos existen, así que cambiar un dígito del catálogo no rompía nada y un LER inventado podía pasar por válido.
> **Decisión: test nuevo.** `services/albaranes-comun/tests/test_f036_r14_catalogo_ler_exhaustivo.py` (commit `9568ac2`, 25 tests) recorre los 20 capítulos y sus subcapítulos uno a uno. Reinyectado el 2026-09-11 contra ese fichero: **muere**. Grupo A de `progress/impl_F-043_T28_supervivientes.md`.

### 94. `services/albaranes-front/domain/models/review_models.py:31` [logico]

- Original: `if a is None or b is None:`
- Mutado:   `if a is None and b is None:`

#### Análisis

> **Mutante EQUIVALENTE, no un hueco.** La mutación abre la guarda de None y deja pasar un None al cuerpo de la función, pero el cuerpo lo vuelve a atrapar: `float(None)` lanza `TypeError` y el `except (TypeError, ValueError)` devuelve `False`, que es lo mismo que devolvía la guarda. Es un doble cinturón. Comprobado por enumeración exhaustiva del espacio que estas funciones distinguen (81 pares y 2 × 729 ternas): **cero discrepancias**.
> **Decisión: equivalente justificado, con guarda.** `services/albaranes-front/tests/test_f043_t28_equivalentes.py` fija el segundo cinturón. Verificado en rojo estrechando el `except` a `ValueError`: 6 tests caen. Grupo F de `progress/impl_F-043_T28_supervivientes.md`.

### 95. `services/albaranes-front/domain/models/review_models.py:78` [logico]

- Original: `if factor is None or cantidad_albaran is None or cantidad_convertida is None:`
- Mutado:   `if factor is None and cantidad_albaran is None or cantidad_convertida is None:`

#### Análisis

> **Mutante EQUIVALENTE, no un hueco.** La mutación abre la guarda de None y deja pasar un None al cuerpo de la función, pero el cuerpo lo vuelve a atrapar: `float(None)` lanza `TypeError` y el `except (TypeError, ValueError)` devuelve `False`, que es lo mismo que devolvía la guarda. Es un doble cinturón. Comprobado por enumeración exhaustiva del espacio que estas funciones distinguen (81 pares y 2 × 729 ternas): **cero discrepancias**.
> **Decisión: equivalente justificado, con guarda.** `services/albaranes-front/tests/test_f043_t28_equivalentes.py` fija el segundo cinturón. Verificado en rojo estrechando el `except` a `ValueError`: 6 tests caen. Grupo F de `progress/impl_F-043_T28_supervivientes.md`.

### 96. `services/albaranes-front/domain/models/review_models.py:78` [logico]

- Original: `if factor is None or cantidad_albaran is None or cantidad_convertida is None:`
- Mutado:   `if factor is None or cantidad_albaran is None and cantidad_convertida is None:`

#### Análisis

> **Mutante EQUIVALENTE, no un hueco.** La mutación abre la guarda de None y deja pasar un None al cuerpo de la función, pero el cuerpo lo vuelve a atrapar: `float(None)` lanza `TypeError` y el `except (TypeError, ValueError)` devuelve `False`, que es lo mismo que devolvía la guarda. Es un doble cinturón. Comprobado por enumeración exhaustiva del espacio que estas funciones distinguen (81 pares y 2 × 729 ternas): **cero discrepancias**.
> **Decisión: equivalente justificado, con guarda.** `services/albaranes-front/tests/test_f043_t28_equivalentes.py` fija el segundo cinturón. Verificado en rojo estrechando el `except` a `ValueError`: 6 tests caen. Grupo F de `progress/impl_F-043_T28_supervivientes.md`.

### 97. `services/albaranes-front/infrastructure/database/review_repository.py:3375` [aritmetico]

- Original: `len(motivos) - len(vigentes),`
- Mutado:   `len(motivos) + len(vigentes),`

#### Análisis

> **Hueco real, CERRADO.** Los caminos defensivos de sv4 se tragan la excepción a propósito —sellar trazabilidad no puede tumbar el guardado del revisor—, así que lo único que queda del fallo es el `logger.warning`. La suite comprobaba que el guardado sobrevive; nadie comprobaba que quedara algo con que diagnosticar.
> **Decisión: test nuevo.** Commit `cd35efb` (`test_f036_r1_r8_conversion_no_reproducible.py` y `test_f036_r23_r24_trazabilidad.py`). Reinyectado el 2026-09-11 contra la suite de sv4: **muere**. Grupo D de `progress/impl_F-043_T28_supervivientes.md`.

### 98. `services/albaranes-front/infrastructure/database/review_repository.py:3384` [booleano]

- Original: `"motivos": json.dumps(vigentes, ensure_ascii=False),`
- Mutado:   `"motivos": json.dumps(vigentes, ensure_ascii=True),`

#### Análisis

> **Mutante EQUIVALENTE, no un hueco.** `ensure_ascii` solo decide si un carácter no ASCII se escribe tal cual o escapado como `\uXXXX`. Las dos serializaciones son JSON válido y parsean al MISMO valor, y todo consumidor de `review_reasons_json` entra por `json.loads`/`motivos_de_json` (verificado con grep): la columna se LEE parseada, nunca se compara como texto.
> **Decisión: equivalente justificado, con guarda.** `services/albaranes-front/tests/test_f043_t28_equivalentes.py` fija ese invariante: las dos serializaciones de una lista con acentos y eñes son textos distintos y `motivos_de_json` devuelve de las dos la misma lista. Grupo E de `progress/impl_F-043_T28_supervivientes.md`.

### 99. `services/albaranes-front/infrastructure/database/review_repository.py:3393` [booleano]

- Original: `exc_info=True,`
- Mutado:   `exc_info=False,`

#### Análisis

> **Hueco real, CERRADO.** Los caminos defensivos de sv4 se tragan la excepción a propósito —sellar trazabilidad no puede tumbar el guardado del revisor—, así que lo único que queda del fallo es el `logger.warning`. La suite comprobaba que el guardado sobrevive; nadie comprobaba que quedara algo con que diagnosticar.
> **Decisión: test nuevo.** Commit `cd35efb` (`test_f036_r1_r8_conversion_no_reproducible.py` y `test_f036_r23_r24_trazabilidad.py`). Reinyectado el 2026-09-11 contra la suite de sv4: **muere**. Grupo D de `progress/impl_F-043_T28_supervivientes.md`.

### 100. `services/albaranes-front/infrastructure/database/review_repository.py:3440` [booleano]

- Original: `"razones": json.dumps(razones, ensure_ascii=False),`
- Mutado:   `"razones": json.dumps(razones, ensure_ascii=True),`

#### Análisis

> **Mutante EQUIVALENTE, no un hueco.** `ensure_ascii` solo decide si un carácter no ASCII se escribe tal cual o escapado como `\uXXXX`. Las dos serializaciones son JSON válido y parsean al MISMO valor, y todo consumidor de `review_reasons_json` entra por `json.loads`/`motivos_de_json` (verificado con grep): la columna se LEE parseada, nunca se compara como texto.
> **Decisión: equivalente justificado, con guarda.** `services/albaranes-front/tests/test_f043_t28_equivalentes.py` fija ese invariante: las dos serializaciones de una lista con acentos y eñes son textos distintos y `motivos_de_json` devuelve de las dos la misma lista. Grupo E de `progress/impl_F-043_T28_supervivientes.md`.

### 101. `services/albaranes-front/infrastructure/database/review_repository.py:3450` [booleano]

- Original: `exc_info=True,`
- Mutado:   `exc_info=False,`

#### Análisis

> **Hueco real, CERRADO.** Los caminos defensivos de sv4 se tragan la excepción a propósito —sellar trazabilidad no puede tumbar el guardado del revisor—, así que lo único que queda del fallo es el `logger.warning`. La suite comprobaba que el guardado sobrevive; nadie comprobaba que quedara algo con que diagnosticar.
> **Decisión: test nuevo.** Commit `cd35efb` (`test_f036_r1_r8_conversion_no_reproducible.py` y `test_f036_r23_r24_trazabilidad.py`). Reinyectado el 2026-09-11 contra la suite de sv4: **muere**. Grupo D de `progress/impl_F-043_T28_supervivientes.md`.

### 102. `services/albaranes-front/infrastructure/database/review_repository.py:3478` [booleano]

- Original: `exc_info=True,`
- Mutado:   `exc_info=False,`

#### Análisis

> **Hueco real, CERRADO.** Los caminos defensivos de sv4 se tragan la excepción a propósito —sellar trazabilidad no puede tumbar el guardado del revisor—, así que lo único que queda del fallo es el `logger.warning`. La suite comprobaba que el guardado sobrevive; nadie comprobaba que quedara algo con que diagnosticar.
> **Decisión: test nuevo.** Commit `cd35efb` (`test_f036_r1_r8_conversion_no_reproducible.py` y `test_f036_r23_r24_trazabilidad.py`). Reinyectado el 2026-09-11 contra la suite de sv4: **muere**. Grupo D de `progress/impl_F-043_T28_supervivientes.md`.

### 103. `services/albaranes-persistencia/application/services/contexto_linea_merger.py:92` [booleano]

- Original: `return True`
- Mutado:   `return False`

#### Análisis

> **Mutante EQUIVALENTE, no un hueco.** Esa rama de `_tiene_valor` atiende a un valor que no es None, ni bool, ni str, ni int/float, y hoy ninguno puede llegar: `_tiene_valor` solo se invoca con `getattr(ctx, campo, None)` sobre las nueve medidas de `_CAMPOS_RESIDUOS` de un `ContextoLinea` ya validado, y pydantic rechaza los 45 intentos de meter ahí una lista, un dict, una tupla, un set o un objeto suelto (medido, 45/45).
> **Decisión: equivalente justificado, con guarda.** Commit `805cccb`: el test de `test_f036_r9_r12_contexto_merger.py` no lo mata, guarda la inalcanzabilidad. Grupo G de `progress/impl_F-043_T28_supervivientes.md`.

### 104. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:323` [logico]

- Original: `"_gra_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_gra_ide": r.get("gra_rep_ide") and 0,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 105. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:323` [entero]

- Original: `"_gra_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_gra_ide": r.get("gra_rep_ide") or 1,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 106. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:325` [logico]

- Original: `"_gra_nom": (r.get("gra_nomori") or r.get("gra_nom")`
- Mutado:   `"_gra_nom": (r.get("gra_nomori") and r.get("gra_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 107. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:326` [logico]

- Original: `or r.get("gra_rep_nomori") or r.get("gra_rep_nom")`
- Mutado:   `and r.get("gra_rep_nomori") or r.get("gra_rep_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 108. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:326` [logico]

- Original: `or r.get("gra_rep_nomori") or r.get("gra_rep_nom")`
- Mutado:   `or r.get("gra_rep_nomori") and r.get("gra_rep_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 109. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:327` [logico]

- Original: `or "?"),`
- Mutado:   `and "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 110. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:358` [logico]

- Original: `"_gra_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_gra_ide": r.get("gra_rep_ide") and 0,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 111. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:358` [entero]

- Original: `"_gra_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_gra_ide": r.get("gra_rep_ide") or 1,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 112. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:360` [logico]

- Original: `"_gra_nom": (r.get("gra_nomori") or r.get("gra_nom")`
- Mutado:   `"_gra_nom": (r.get("gra_nomori") and r.get("gra_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 113. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:361` [logico]

- Original: `or r.get("gra_rep_nomori") or r.get("gra_rep_nom")`
- Mutado:   `and r.get("gra_rep_nomori") or r.get("gra_rep_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 114. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:361` [logico]

- Original: `or r.get("gra_rep_nomori") or r.get("gra_rep_nom")`
- Mutado:   `or r.get("gra_rep_nomori") and r.get("gra_rep_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 115. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:362` [logico]

- Original: `or "?"),`
- Mutado:   `and "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 116. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:394` [logico]

- Original: `"_gra_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_gra_ide": r.get("gra_rep_ide") and 0,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 117. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:394` [entero]

- Original: `"_gra_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_gra_ide": r.get("gra_rep_ide") or 1,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 118. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:396` [logico]

- Original: `"_gra_nom": (r.get("gra_nomori") or r.get("gra_nom")`
- Mutado:   `"_gra_nom": (r.get("gra_nomori") and r.get("gra_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 119. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:397` [logico]

- Original: `or r.get("gra_rep_nomori") or r.get("gra_rep_nom")`
- Mutado:   `and r.get("gra_rep_nomori") or r.get("gra_rep_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 120. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:397` [logico]

- Original: `or r.get("gra_rep_nomori") or r.get("gra_rep_nom")`
- Mutado:   `or r.get("gra_rep_nomori") and r.get("gra_rep_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 121. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:398` [logico]

- Original: `or "?"),`
- Mutado:   `and "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 122. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:429` [logico]

- Original: `"_gra_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_gra_ide": r.get("gra_rep_ide") and 0,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 123. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:429` [entero]

- Original: `"_gra_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_gra_ide": r.get("gra_rep_ide") or 1,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 124. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:431` [logico]

- Original: `"_gra_nom": (r.get("gra_nomori") or r.get("gra_nom")`
- Mutado:   `"_gra_nom": (r.get("gra_nomori") and r.get("gra_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 125. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:432` [logico]

- Original: `or r.get("gra_rep_nomori") or r.get("gra_rep_nom")`
- Mutado:   `and r.get("gra_rep_nomori") or r.get("gra_rep_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 126. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:432` [logico]

- Original: `or r.get("gra_rep_nomori") or r.get("gra_rep_nom")`
- Mutado:   `or r.get("gra_rep_nomori") and r.get("gra_rep_nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 127. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:433` [logico]

- Original: `or "?"),`
- Mutado:   `and "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 128. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:457` [not]

- Original: `if not cods:`
- Mutado:   `if cods:`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 129. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:466` [entero]

- Original: `""", list(cods), max_rows=500,`
- Mutado:   `""", list(cods), max_rows=501,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 130. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:487` [not]

- Original: `if not gra_neg_ides:`
- Mutado:   `if gra_neg_ides:`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 131. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:720` [not]

- Original: `sin_negocio = [d for d in gra_found if not d["_gra_neg_ide"]]`
- Mutado:   `sin_negocio = [d for d in gra_found if d["_gra_neg_ide"]]`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 132. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs.py:753` [logico]

- Original: `f"gra_neg_ide={d.get('_gra_neg_ide') or '—'}  "`
- Mutado:   `f"gra_neg_ide={d.get('_gra_neg_ide') and '—'}  "`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 133. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:250` [not]

- Original: `if not cods:`
- Mutado:   `if cods:`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 134. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:259` [entero]

- Original: `""", list(cods), max_rows=500)`
- Mutado:   `""", list(cods), max_rows=501)`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 135. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:373` [logico]

- Original: `"_target_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_target_ide": r.get("gra_rep_ide") and 0,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 136. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:373` [entero]

- Original: `"_target_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_target_ide": r.get("gra_rep_ide") or 1,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 137. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:375` [logico]

- Original: `"_name": (r.get("nomori") or r.get("nom")`
- Mutado:   `"_name": (r.get("nomori") and r.get("nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 138. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:376` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `and r.get("rep_nomori") or r.get("rep_nom") or "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 139. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:376` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `or r.get("rep_nomori") and r.get("rep_nom") or "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 140. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:376` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `or r.get("rep_nomori") or r.get("rep_nom") and "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 141. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:399` [logico]

- Original: `"_target_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_target_ide": r.get("gra_rep_ide") and 0,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 142. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:399` [entero]

- Original: `"_target_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_target_ide": r.get("gra_rep_ide") or 1,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 143. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:401` [logico]

- Original: `"_name": (r.get("nomori") or r.get("nom")`
- Mutado:   `"_name": (r.get("nomori") and r.get("nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 144. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:402` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `and r.get("rep_nomori") or r.get("rep_nom") or "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 145. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:402` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `or r.get("rep_nomori") and r.get("rep_nom") or "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 146. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:402` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `or r.get("rep_nomori") or r.get("rep_nom") and "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 147. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:424` [logico]

- Original: `"_target_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_target_ide": r.get("gra_rep_ide") and 0,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 148. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:424` [entero]

- Original: `"_target_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_target_ide": r.get("gra_rep_ide") or 1,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 149. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:426` [logico]

- Original: `"_name": (r.get("nomori") or r.get("nom")`
- Mutado:   `"_name": (r.get("nomori") and r.get("nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 150. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:427` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `and r.get("rep_nomori") or r.get("rep_nom") or "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 151. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:427` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `or r.get("rep_nomori") and r.get("rep_nom") or "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 152. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:427` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `or r.get("rep_nomori") or r.get("rep_nom") and "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 153. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:449` [logico]

- Original: `"_target_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_target_ide": r.get("gra_rep_ide") and 0,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 154. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:449` [entero]

- Original: `"_target_ide": r.get("gra_rep_ide") or 0,`
- Mutado:   `"_target_ide": r.get("gra_rep_ide") or 1,`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 155. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:451` [logico]

- Original: `"_name": (r.get("nomori") or r.get("nom")`
- Mutado:   `"_name": (r.get("nomori") and r.get("nom")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 156. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:452` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `and r.get("rep_nomori") or r.get("rep_nom") or "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 157. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:452` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `or r.get("rep_nomori") and r.get("rep_nom") or "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 158. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:452` [logico]

- Original: `or r.get("rep_nomori") or r.get("rep_nom") or "?"),`
- Mutado:   `or r.get("rep_nomori") or r.get("rep_nom") and "?"),`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 159. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:624` [comparacion]

- Original: `if d["_store"] == "gra":`
- Mutado:   `if d["_store"] != "gra":`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 160. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:625` [logico]

- Original: `ide_txt = (f"gra_rep_ide={d['_target_ide'] or '—'}  "`
- Mutado:   `ide_txt = (f"gra_rep_ide={d['_target_ide'] and '—'}  "`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 161. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:626` [logico]

- Original: `f"gra_neg_ide={d.get('_neg_ide') or '—'}")`
- Mutado:   `f"gra_neg_ide={d.get('_neg_ide') and '—'}")`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 162. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:688` [not]

- Original: `if not v["neg_ide"]]`
- Mutado:   `if v["neg_ide"]]`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

### 163. `services/albaranes-persistencia/scripts/diagnose_sigrid_contrato_docs_v2.py:695` [logico]

- Original: `gra_ides_csv = ",".join(str(i) for i in neg_a_rep) or "0"`
- Mutado:   `gra_ides_csv = ",".join(str(i) for i in neg_a_rep) and "0"`

#### Análisis

> **Justificado EN BLOQUE**, con autorización expresa del humano del 2026-09-10. `scripts/diagnose_sigrid_contrato_docs*.py` son diagnósticos manuales de un solo uso, ajenos a F-043 y a F-036: entran en el alcance solo porque los commits `ec5b5b0` y `48e3d17` de esta rama los corrigieron. Verificado el 2026-09-11: son código de nivel superior sin `main()` ni guarda `__main__` —importarlos ejecutaría el diagnóstico contra Sigrid—, **ningún** servicio de los seis los referencia (grep: 0 en sv1, sv2, sv4, sv5, sv6 y `comun`; los 63 aciertos de sv3 son los propios `scripts/` citándose entre sí), no hay tests suyos ni los puede haber, y ninguna ruta de producción, Dockerfile ni entrypoint los invoca.
> **Decisión: fuera del pipeline, sin test.** Reinyectados los 60 el 2026-09-11: los 60 siguen vivos, como debe ser —la suite de sv3 ni siquiera importa esos módulos—. Grupo H de `progress/impl_F-043_T28_supervivientes.md`.

## Timeouts

**VEREDICTO (T28, 2026-09-11): los tres eran RUIDO DE LA MÁQUINA, no
mutantes lentos. Los tres son MUERTOS.**

Ninguna de las tres líneas mutadas contiene bucle ni espera: son un `if`,
una expresión `or` y un predicado `lambda`. Ninguna mutación puede colgar
nada. Reinyectados uno a uno el 2026-09-11, cada uno contra la suite de su
servicio, **mata la suite en menos de 3,5 s** frente al timeout de 275 s que
la campaña les dio:

| Mutante | Suite | Veredicto real | Tiempo |
|---|---|---|---|
| `sqlalchemy_valuation_context_repository.py:335` | sv5 | **MUERTO** (7 tests fallan) | 2,66 s |
| `sqlalchemy_valuation_context_repository.py:345` | sv5 | **MUERTO** (2 tests fallan) | 3,44 s |
| `modifier_contract_matcher.py:284` | sv6 | **MUERTO** (3 tests fallan) | 2,93 s |

La causa es la contención del arranque: son los mutantes **6, 7 y 9 de 347**,
o sea la primerísima oleada, con los 4 workers creando worktrees y midiendo
líneas base a la vez sobre una máquina compartida. Las líneas base de sv5 y
sv6 se midieron en 10,5 s y 9,2 s, y hoy esas mismas suites tardan 3,2 s y
3,4 s: el factor 3 de ese momento es la huella de la contención.

El tercero, además, **habría muerto ya en el propio HEAD de la campaña**
(`48e3d17`): repuesto ese fichero de test a su versión de entonces e
inyectado el mutante, caen 2 tests en 3,05 s. No dependía de los tests que
vinieron después.

Con esto, el recuento real de la campaña es **184 muertos y 163
supervivientes**, no 181/163/3.

- `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py:335` [not] if not familia: -> if familia:
- `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py:345` [logico] origen=_opt_str(row.get("tipologia_origen")) or "ia1", -> origen=_opt_str(row.get("tipologia_origen")) and "ia1",
- `services/albaran-valoracion-persist/application/services/modifier_contract_matcher.py:284` [comparacion] return lambda d: normalizar_ler(d) == ler or ler in d -> return lambda d: normalizar_ler(d) != ler or ler in d
