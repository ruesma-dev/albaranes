<!-- progress/mutacion_F-048.md -->
# F-048 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-048` el 2026-09-25 05:37.

## Alcance

Origen del diff: **rama** (`1807e8340a2764486c5f0892836b55294a54297f` .. `feature/F-048-correo-contexto-ia1`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/comparar_obra.py` | 548 |
| `evals/correos.py` | 148 |
| `evals/informe.py` | 38 |
| `evals/inyeccion.py` | 401 |
| `evals/modelos.py` | 24 |
| `evals/procesos/errores.py` | 129 |
| `evals/procesos/sv2_extraccion.py` | 65 |
| `evals/procesos/sv2_obra.py` | 261 |
| `evals/procesos/sv5_valoracion.py` | 57 |
| `evals/procesos/sv6_build.py` | 33 |
| `evals/runner.py` | 184 |
| `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py` | 23 |
| `services/albaranes-api/application/services/albaran_extraction_service.py` | 134 |
| `services/albaranes-api/application/services/origen_datos_resolver.py` | 184 |
| `services/albaranes-api/domain/models/albaran_models.py` | 9 |
| `services/albaranes-api/domain/models/lectura_correo.py` | 90 |
| `services/albaranes-api/domain/ports/obras_activas_provider.py` | 19 |
| `services/albaranes-api/encolar_extraccion.py` | 77 |
| `services/albaranes-api/infrastructure/sigrid/obras_activas_cache.py` | 48 |
| `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py` | 25 |
| `services/albaranes-api/interface_adapters/worker/correo_adapter.py` | 29 |
| `services/albaranes-api/interface_adapters/worker/extraction_worker.py` | 74 |
| `services/albaranes-api/interface_adapters/worker/ports.py` | 17 |
| `services/albaranes-api/main_worker.py` | 7 |
| `services/albaranes-comun/ruesma_comun/colas/mensajes.py` | 8 |
| `services/albaranes-comun/ruesma_comun/contratos/__init__.py` | 18 |
| `services/albaranes-comun/ruesma_comun/contratos/origen_datos.py` | 133 |
| `services/albaranes-comun/ruesma_comun/correo/__init__.py` | 35 |
| `services/albaranes-comun/ruesma_comun/correo/contexto.py` | 165 |
| `services/albaranes-comun/ruesma_comun/correo/prompt.py` | 94 |
| `services/albaranes-comun/ruesma_comun/llm/llm_call_logger.py` | 34 |
| `services/albaranes-comun/ruesma_comun/llm/retry_policy.py` | 17 |
| `services/albaranes-email/application/pipelines/polling_pipeline.py` | 61 |
| `services/albaranes-email/capturar_correo.py` | 151 |
| `services/albaranes-email/config/settings.py` | 10 |
| `services/albaranes-email/domain/models/email_models.py` | 18 |
| `services/albaranes-email/domain/ports/mailbox_client.py` | 14 |
| `services/albaranes-email/domain/ports/orchestrator_port.py` | 10 |
| `services/albaranes-email/infrastructure/colas/intake_cola_adapter.py` | 52 |
| `services/albaranes-email/infrastructure/graph/mail_client.py` | 99 |
| `services/albaranes-email/infrastructure/http/orchestrator_client.py` | 8 |
| `services/albaranes-email/main.py` | 1 |
| `services/albaranes-front/domain/models/review_models.py` | 164 |
| `services/albaranes-persistencia/application/services/albaran_confidence_service.py` | 43 |
| `services/albaranes-persistencia/domain/models/extraction_models.py` | 12 |
| **Total** | **3771** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 410 |
| Mutantes evaluados | 410 |
| Muertos | 330 |
| Supervivientes | 80 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 21051.1 s |
| SHA de HEAD medido | `14cee8ac07a422680c0293995e38b76e2911feb9` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0` | 534.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-api` | 26.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-comun` | 155.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-email` | 14.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-front` | 19.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_0/services/albaranes-persistencia` | 17.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1` | 521.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-api` | 25.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-comun` | 158.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-email` | 17.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-front` | 17.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048_5f_ap43y/wk_1/services/albaranes-persistencia` | 16.0 |
| Media por mutante evaluado (s) | 51.3 |
| Timeout efectivo por mutante (s) | 1068 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 2 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/comparar_obra.py:211` [logico]

- Original: `if clasificacion["categoria"] == "inestable" and len(corrida.variantes) > 1:`
- Mutado:   `if clasificacion["categoria"] == "inestable" or len(corrida.variantes) > 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `evals/comparar_obra.py:211` [comparacion]

- Original: `if clasificacion["categoria"] == "inestable" and len(corrida.variantes) > 1:`
- Mutado:   `if clasificacion["categoria"] == "inestable" and len(corrida.variantes) >= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `evals/comparar_obra.py:214` [comparacion]

- Original: `if clasificacion["categoria"] == "con_errores":`
- Mutado:   `if clasificacion["categoria"] != "con_errores":`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `evals/comparar_obra.py:217` [entero]

- Original: `for indice, vuelta in enumerate(corrida.resultados[variante], start=1):`
- Mutado:   `for indice, vuelta in enumerate(corrida.resultados[variante], start=2):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `evals/comparar_obra.py:230` [logico]

- Original: `f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · dev `{commits.get('dev') or '?'}`",`
- Mutado:   `f"- Fecha: {fecha} · rama `{commits.get('rama') and '?'}` · dev `{commits.get('dev') or '?'}`",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `evals/comparar_obra.py:230` [logico]

- Original: `f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · dev `{commits.get('dev') or '?'}`",`
- Mutado:   `f"- Fecha: {fecha} · rama `{commits.get('rama') or '?'}` · dev `{commits.get('dev') and '?'}`",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `evals/comparar_obra.py:239` [comparacion]

- Original: `+ (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones == 1 else "")`
- Mutado:   `+ (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones != 1 else "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `evals/comparar_obra.py:239` [entero]

- Original: `+ (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones == 1 else "")`
- Mutado:   `+ (" Con 1 repetición la estabilidad no se mide." if corrida.repeticiones == 2 else "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `evals/comparar_obra.py:276` [comparacion]

- Original: `if c["categoria"] == categoria`
- Mutado:   `if c["categoria"] != categoria`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `evals/comparar_obra.py:290` [comparacion]

- Original: `return "—" if valor is None else ("sí" if valor else "no")`
- Mutado:   `return "—" if valor is not None else ("sí" if valor else "no")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `evals/comparar_obra.py:300` [entero]

- Original: `for indice in range(1, corrida.repeticiones + 1)`
- Mutado:   `for indice in range(2, corrida.repeticiones + 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `evals/comparar_obra.py:300` [aritmetico]

- Original: `for indice in range(1, corrida.repeticiones + 1)`
- Mutado:   `for indice in range(1, corrida.repeticiones - 1)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `evals/comparar_obra.py:300` [entero]

- Original: `for indice in range(1, corrida.repeticiones + 1)`
- Mutado:   `for indice in range(1, corrida.repeticiones + 2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `evals/comparar_obra.py:303` [comparacion]

- Original: `coinciden = ["coinciden"] if len(corrida.variantes) > 1 else []`
- Mutado:   `coinciden = ["coinciden"] if len(corrida.variantes) >= 1 else []`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `evals/comparar_obra.py:303` [entero]

- Original: `coinciden = ["coinciden"] if len(corrida.variantes) > 1 else []`
- Mutado:   `coinciden = ["coinciden"] if len(corrida.variantes) > 2 else []`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `evals/comparar_obra.py:335` [entero]

- Original: `for indice, vuelta in enumerate(corrida.resultados[variante], start=1)`
- Mutado:   `for indice, vuelta in enumerate(corrida.resultados[variante], start=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `evals/comparar_obra.py:342` [entero]

- Original: `for indice, vuelta in enumerate(corrida.resultados[variante], start=1)`
- Mutado:   `for indice, vuelta in enumerate(corrida.resultados[variante], start=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `evals/comparar_obra.py:345` [logico]

- Original: `lineas += ["", "## obra_nombre leído", "", *(nombres or ["(ninguno)"])]`
- Mutado:   `lineas += ["", "## obra_nombre leído", "", *(nombres and ["(ninguno)"])]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `evals/comparar_obra.py:346` [logico]

- Original: `lineas += ["", "## Errores", "", *(errores or ["(ninguno)"])]`
- Mutado:   `lineas += ["", "## Errores", "", *(errores and ["(ninguno)"])]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `evals/comparar_obra.py:355` [booleano]

- Original: `salida.mkdir(parents=True, exist_ok=True)`
- Mutado:   `salida.mkdir(parents=False, exist_ok=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `evals/comparar_obra.py:355` [booleano]

- Original: `salida.mkdir(parents=True, exist_ok=True)`
- Mutado:   `salida.mkdir(parents=True, exist_ok=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `evals/comparar_obra.py:366` [booleano]

- Original: `json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8"`
- Mutado:   `json.dumps(carga, ensure_ascii=True, indent=2), encoding="utf-8"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `evals/comparar_obra.py:366` [entero]

- Original: `json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8"`
- Mutado:   `json.dumps(carga, ensure_ascii=False, indent=3), encoding="utf-8"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `evals/comparar_obra.py:371` [booleano]

- Original: `resumen.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `resumen.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `evals/comparar_obra.py:371` [booleano]

- Original: `resumen.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `resumen.parent.mkdir(parents=True, exist_ok=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `evals/comparar_obra.py:421` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 27. `evals/comparar_obra.py:422` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 28. `evals/comparar_obra.py:424` [comparacion]

- Original: `return proceso.stdout.strip() if proceso.returncode == 0 else ""`
- Mutado:   `return proceso.stdout.strip() if proceso.returncode != 0 else ""`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 29. `evals/comparar_obra.py:424` [entero]

- Original: `return proceso.stdout.strip() if proceso.returncode == 0 else ""`
- Mutado:   `return proceso.stdout.strip() if proceso.returncode == 1 else ""`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 30. `evals/comparar_obra.py:452` [logico]

- Original: `modelo = entorno.get(variable_modelo) or modelo_por_defecto`
- Mutado:   `modelo = entorno.get(variable_modelo) and modelo_por_defecto`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 31. `evals/comparar_obra.py:453` [entero]

- Original: `llamadas = sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = sum(2 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 32. `evals/comparar_obra.py:453` [aritmetico]

- Original: `llamadas = sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = sum(1 for r in rutas.values() if r) // len(variantes) * opciones.repeticiones`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 33. `evals/comparar_obra.py:453` [aritmetico]

- Original: `llamadas = sum(1 for r in rutas.values() if r) * len(variantes) * opciones.repeticiones`
- Mutado:   `llamadas = sum(1 for r in rutas.values() if r) * len(variantes) // opciones.repeticiones`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 34. `evals/comparar_obra.py:496` [booleano]

- Original: `analizador.add_argument("--casos", required=True, help="caso_id separados por coma")`
- Mutado:   `analizador.add_argument("--casos", required=False, help="caso_id separados por coma")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 35. `evals/correos.py:139` [booleano]

- Original: `check=True,`
- Mutado:   `check=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 36. `evals/inyeccion.py:84` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 37. `evals/inyeccion.py:125` [logico]

- Original: `if len(partes) != 2 or not all(partes):`
- Mutado:   `if len(partes) != 2 and not all(partes):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 38. `evals/inyeccion.py:166` [booleano]

- Original: `sin_correo: bool = False,  # --sin-correo (F-048, R41)`
- Mutado:   `sin_correo: bool = True,  # --sin-correo (F-048, R41)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 39. `evals/inyeccion.py:218` [booleano]

- Original: `payload_json=json.dumps(payload, ensure_ascii=False),`
- Mutado:   `payload_json=json.dumps(payload, ensure_ascii=True),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 40. `evals/inyeccion.py:258` [entero]

- Original: `f"SI(sha={correo.sha256[:8]})" if correo is not None else "NO",`
- Mutado:   `f"SI(sha={correo.sha256[:9]})" if correo is not None else "NO",`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 41. `evals/inyeccion.py:265` [booleano]

- Original: `duplicado=False,`
- Mutado:   `duplicado=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 42. `evals/inyeccion.py:308` [booleano]

- Original: `force: bool = True,`
- Mutado:   `force: bool = False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 43. `evals/inyeccion.py:349` [logico]

- Original: `self.codigo_contrato = (codigo_contrato or "").strip()`
- Mutado:   `self.codigo_contrato = (codigo_contrato and "").strip()`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 44. `evals/inyeccion.py:350` [booleano]

- Original: `self.realizado = False`
- Mutado:   `self.realizado = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 45. `evals/inyeccion.py:357` [booleano]

- Original: `self.contrato_ausente = False`
- Mutado:   `self.contrato_ausente = True`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 46. `evals/inyeccion.py:374` [not]

- Original: `if not self.codigo_contrato:`
- Mutado:   `if self.codigo_contrato:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 47. `evals/inyeccion.py:386` [logico]

- Original: `and self.codigo_contrato not in self.contratos_disponibles`
- Mutado:   `or self.codigo_contrato not in self.contratos_disponibles`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 48. `evals/inyeccion.py:393` [booleano]

- Original: `self.realizado = True`
- Mutado:   `self.realizado = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 49. `evals/inyeccion.py:400` [aritmetico]

- Original: `self.motivo += "; además, sv3 no trajo ese contrato"`
- Mutado:   `self.motivo -= "; además, sv3 no trajo ese contrato"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 50. `evals/procesos/errores.py:29` [entero]

- Original: `TOPE_MOTIVO = 200`
- Mutado:   `TOPE_MOTIVO = 201`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 51. `evals/procesos/errores.py:50` [booleano]

- Original: `print(f"{servicio}: {texto}", file=sys.stderr, flush=True)`
- Mutado:   `print(f"{servicio}: {texto}", file=sys.stderr, flush=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 52. `evals/procesos/errores.py:64` [logico]

- Original: `if isinstance(linea, int) and isinstance(columna, int):`
- Mutado:   `if isinstance(linea, int) or isinstance(columna, int):`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 53. `evals/procesos/errores.py:80` [booleano]

- Original: `errores = metodo(include_input=False, include_url=False, include_context=False)`
- Mutado:   `errores = metodo(include_input=True, include_url=False, include_context=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 54. `evals/procesos/errores.py:80` [booleano]

- Original: `errores = metodo(include_input=False, include_url=False, include_context=False)`
- Mutado:   `errores = metodo(include_input=False, include_url=True, include_context=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 55. `evals/procesos/errores.py:80` [booleano]

- Original: `errores = metodo(include_input=False, include_url=False, include_context=False)`
- Mutado:   `errores = metodo(include_input=False, include_url=False, include_context=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 56. `evals/procesos/errores.py:91` [comparacion]

- Original: `if resto > 0:`
- Mutado:   `if resto >= 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 57. `evals/procesos/errores.py:91` [entero]

- Original: `if resto > 0:`
- Mutado:   `if resto > 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 58. `evals/procesos/errores.py:129` [comparacion]

- Original: `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"`
- Mutado:   `return texto if len(texto) < TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 59. `evals/procesos/errores.py:129` [aritmetico]

- Original: `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"`
- Mutado:   `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO + 1]}…"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 60. `evals/procesos/errores.py:129` [entero]

- Original: `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 1]}…"`
- Mutado:   `return texto if len(texto) <= TOPE_MOTIVO else f"{texto[: TOPE_MOTIVO - 2]}…"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 61. `evals/procesos/sv2_obra.py:60` [entero]

- Original: `COD_MIN_OBRAS = ("OBRAS_ACTIVAS_COD_MIN", 450)`
- Mutado:   `COD_MIN_OBRAS = ("OBRAS_ACTIVAS_COD_MIN", 451)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 62. `evals/procesos/sv2_obra.py:61` [entero]

- Original: `MAX_OBRAS = ("OBRAS_ACTIVAS_MAX", 300)`
- Mutado:   `MAX_OBRAS = ("OBRAS_ACTIVAS_MAX", 301)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 63. `evals/procesos/sv2_obra.py:72` [entero]

- Original: `sys.path.insert(0, ruta)`
- Mutado:   `sys.path.insert(1, ruta)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 64. `evals/procesos/sv2_obra.py:85` [logico]

- Original: `if proceso.returncode != 0 or not proceso.stdout:`
- Mutado:   `if proceso.returncode != 0 and not proceso.stdout:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 65. `evals/procesos/sv2_obra.py:143` [entero]

- Original: `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[1]),`
- Mutado:   `timeout_s=float(entorno.get(TIMEOUT_SIGRID[1]) or TIMEOUT_SIGRID[1]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 66. `evals/procesos/sv2_obra.py:143` [logico]

- Original: `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[1]),`
- Mutado:   `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) and TIMEOUT_SIGRID[1]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 67. `evals/procesos/sv2_obra.py:143` [entero]

- Original: `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[1]),`
- Mutado:   `timeout_s=float(entorno.get(TIMEOUT_SIGRID[0]) or TIMEOUT_SIGRID[2]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 68. `evals/procesos/sv2_obra.py:144` [entero]

- Original: `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[1]),`
- Mutado:   `cod_min=int(entorno.get(COD_MIN_OBRAS[1]) or COD_MIN_OBRAS[1]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 69. `evals/procesos/sv2_obra.py:144` [logico]

- Original: `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[1]),`
- Mutado:   `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) and COD_MIN_OBRAS[1]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 70. `evals/procesos/sv2_obra.py:144` [entero]

- Original: `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[1]),`
- Mutado:   `cod_min=int(entorno.get(COD_MIN_OBRAS[0]) or COD_MIN_OBRAS[2]),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 71. `evals/procesos/sv2_obra.py:147` [comparacion]

- Original: `if catalogo is None or not catalogo.activas:`
- Mutado:   `if catalogo is not None or not catalogo.activas:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 72. `evals/procesos/sv2_obra.py:147` [logico]

- Original: `if catalogo is None or not catalogo.activas:`
- Mutado:   `if catalogo is None and not catalogo.activas:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 73. `evals/procesos/sv2_obra.py:147` [not]

- Original: `if catalogo is None or not catalogo.activas:`
- Mutado:   `if catalogo is None or catalogo.activas:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 74. `evals/procesos/sv2_obra.py:243` [entero]

- Original: `obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[1])`
- Mutado:   `obras_max = int(entorno.get(MAX_OBRAS[1]) or MAX_OBRAS[1])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 75. `evals/procesos/sv2_obra.py:243` [logico]

- Original: `obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[1])`
- Mutado:   `obras_max = int(entorno.get(MAX_OBRAS[0]) and MAX_OBRAS[1])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 76. `evals/procesos/sv2_obra.py:243` [entero]

- Original: `obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[1])`
- Mutado:   `obras_max = int(entorno.get(MAX_OBRAS[0]) or MAX_OBRAS[2])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 77. `evals/runner.py:210` [logico]

- Original: `return motivo_muerte or "sv6 no devolvió resultado"`
- Mutado:   `return motivo_muerte and "sv6 no devolvió resultado"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 78. `services/albaranes-email/capturar_correo.py:69` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis

> **EQUIVALENTE.** Con `check=True` y un código distinto de 0, `subprocess.run` lanza `CalledProcessError`, que es `SubprocessError` y cae en el `except` que devuelve `False`; con `check=False` se devuelve `returncode == 0`, también `False`. Código 0: `True` en los dos. `TimeoutExpired` y `OSError`: `False` en los dos. La excepción no se loguea ni se imprime. No hay código de salida de git que distinga.
> **Decisión: equivalente con guarda y demostración.** Guarda parametrizada 0/1/128 con un doble que respeta `check` (`7317fc6`, `services/albaranes-email/tests/test_f048_t34_supervivientes.py`); con el mutante inyectado en un worktree, la suite de sv1 entera (incluidos los tests con git real: ignorada=0, versionada=1, fuera del repositorio=128) da **98 passed** con y sin él. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 79. `services/albaranes-email/infrastructure/graph/mail_client.py:39` [aritmetico]

- Original: `self._dentro_sin_texto += 1`
- Mutado:   `self._dentro_sin_texto -= 1`

#### Análisis

> **EQUIVALENTE.** `HTMLParser` trata el contenido de `script`/`style` como CDATA: tras abrir uno, el siguiente evento de etiqueta es SU cierre (o el fin). El contador vale 0 o 1 (original) y 0 o -1 (mutante); 1 y -1 son los dos verdaderos, y al cerrar `max(0, ...)` deja 0 en los dos. No hay HTML que distinga.
> **Decisión: equivalente con guarda y demostración.** Guarda de CDATA y test diferencial (25.620 secuencias, 0 discrepancias, con control no ciego) en `services/albaranes-email/tests/test_f048_t34_supervivientes.py` (`7317fc6`, `7b8adab`); versión larga, 321.452 secuencias, 0 discrepancias; suite de sv1 con el mutante en worktree: **98 passed**. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

### 80. `services/albaranes-email/infrastructure/graph/mail_client.py:45` [entero]

- Original: `self._dentro_sin_texto = max(0, self._dentro_sin_texto - 1)`
- Mutado:   `self._dentro_sin_texto = max(0, self._dentro_sin_texto - 2)`

#### Análisis

> **EQUIVALENTE.** Mismo invariante que el 22: como el contador nunca pasa de 1, `max(0, c - 1)` y `max(0, c - 2)` dan 0 para c ∈ {0, 1}.
> **Decisión: equivalente con guarda y demostración**, las mismas que el 22. Suite de sv1 con el mutante en worktree: **98 passed**. Detalle en `progress/impl_F-048_T34_supervivientes.md`.

> _Análisis traído de la campaña anterior de esta feature: el mutante volvió a sobrevivir con el mismo operador y el mismo texto. Reléelo si el código de alrededor ha cambiado._

