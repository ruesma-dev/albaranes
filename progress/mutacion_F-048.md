<!-- progress/mutacion_F-048.md -->
# F-048 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-048` el 2026-09-24 05:57.

## Alcance

Origen del diff: **rama** (`1807e8340a2764486c5f0892836b55294a54297f` .. `feature/F-048-correo-contexto-ia1`).

| Fichero | Líneas en alcance |
|---|---|
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
| **Total** | **1883** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 175 |
| Mutantes evaluados | 175 |
| Muertos | 149 |
| Supervivientes | 26 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 617.2 s |
| SHA de HEAD medido | `e7fe2c0750cf8c8417cbd5f9e44c955842529474` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_0/services/albaranes-api` | 9.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_0/services/albaranes-comun` | 115.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_0/services/albaranes-email` | 3.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_0/services/albaranes-front` | 7.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-api` | 6.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-comun` | 110.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-email` | 4.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-front` | 7.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_1/services/albaranes-persistencia` | 3.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-api` | 9.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-comun` | 106.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-email` | 4.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-front` | 7.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_2/services/albaranes-persistencia` | 3.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_3/services/albaranes-api` | 9.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_3/services/albaranes-comun` | 117.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_3/services/albaranes-email` | 3.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-048___lbqr4z/wk_3/services/albaranes-front` | 7.3 |
| Media por mutante evaluado (s) | 3.5 |
| Timeout efectivo por mutante (s) | 235 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-api/application/services/albaran_extraction_service.py:454` [logico]

- Original: `if "{sigrid_context}" not in plantilla and sigrid_context is not None:`
- Mutado:   `if "{sigrid_context}" not in plantilla or sigrid_context is not None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/albaranes-api/application/services/origen_datos_resolver.py:174` [logico]

- Original: `data["cabecera"] = {**(cabecera or {}), "obra_codigo": obra.valor_final}`
- Mutado:   `data["cabecera"] = {**(cabecera and {}), "obra_codigo": obra.valor_final}`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/albaranes-api/encolar_extraccion.py:57` [logico]

- Original: `if not isinstance(datos, dict) or "asunto" not in datos or "cuerpo" not in datos:`
- Mutado:   `if not isinstance(datos, dict) and "asunto" not in datos or "cuerpo" not in datos:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/albaranes-api/encolar_extraccion.py:88` [entero]

- Original: `f"(sha={correo.sha256[:8]} caracteres={correo.caracteres_originales} "`
- Mutado:   `f"(sha={correo.sha256[:9]} caracteres={correo.caracteres_originales} "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/albaranes-comun/ruesma_comun/correo/contexto.py:105` [entero]

- Original: `if max_caracteres <= 0:`
- Mutado:   `if max_caracteres <= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/albaranes-comun/ruesma_comun/llm/llm_call_logger.py:120` [booleano]

- Original: `ensure_ascii=False,`
- Mutado:   `ensure_ascii=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/albaranes-comun/ruesma_comun/llm/llm_call_logger.py:121` [entero]

- Original: `indent=2,`
- Mutado:   `indent=3,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/albaranes-email/application/pipelines/polling_pipeline.py:399` [entero]

- Original: `contexto.sha256[:8],`
- Mutado:   `contexto.sha256[:9],`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/albaranes-email/capturar_correo.py:69` [booleano]

- Original: `check=False,`
- Mutado:   `check=True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/albaranes-email/capturar_correo.py:70` [booleano]

- Original: `capture_output=True,`
- Mutado:   `capture_output=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/albaranes-email/capturar_correo.py:71` [entero]

- Original: `timeout=30,`
- Mutado:   `timeout=31,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/albaranes-email/capturar_correo.py:99` [booleano]

- Original: `ruta.parent.mkdir(parents=True, exist_ok=True)`
- Mutado:   `ruta.parent.mkdir(parents=False, exist_ok=True)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/albaranes-email/capturar_correo.py:100` [booleano]

- Original: `ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")`
- Mutado:   `ruta.write_text(json.dumps(datos, ensure_ascii=True, indent=2), encoding="utf-8")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/albaranes-email/capturar_correo.py:100` [entero]

- Original: `ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")`
- Mutado:   `ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=3), encoding="utf-8")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `services/albaranes-email/capturar_correo.py:117` [booleano]

- Original: `analizador.add_argument("--message-id", required=True, help="id de Graph del mensaje")`
- Mutado:   `analizador.add_argument("--message-id", required=False, help="id de Graph del mensaje")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `services/albaranes-email/capturar_correo.py:118` [booleano]

- Original: `analizador.add_argument("--caso", required=True, help="id del caso del banco de evals")`
- Mutado:   `analizador.add_argument("--caso", required=False, help="id del caso del banco de evals")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `services/albaranes-email/capturar_correo.py:144` [entero]

- Original: `f"Guardado {ruta} (sha={ctx.sha256[:8]} caracteres={ctx.caracteres_originales} "`
- Mutado:   `f"Guardado {ruta} (sha={ctx.sha256[:9]} caracteres={ctx.caracteres_originales} "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `services/albaranes-email/config/settings.py:48` [entero]

- Original: `MAX_CARACTERES_DEFECTO, alias="CORREO_MAX_CARACTERES", gt=0`
- Mutado:   `MAX_CARACTERES_DEFECTO, alias="CORREO_MAX_CARACTERES", gt=1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `services/albaranes-email/domain/models/email_models.py:26` [booleano]

- Original: `@dataclass(frozen=True)`
- Mutado:   `@dataclass(frozen=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `services/albaranes-email/infrastructure/colas/intake_cola_adapter.py:89` [booleano]

- Original: `payload_json=json.dumps(meta_workflow, ensure_ascii=False),`
- Mutado:   `payload_json=json.dumps(meta_workflow, ensure_ascii=True),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `services/albaranes-email/infrastructure/colas/intake_cola_adapter.py:178` [entero]

- Original: `f"SI(sha={contexto.sha256[:8]} caracteres={contexto.caracteres_originales}"`
- Mutado:   `f"SI(sha={contexto.sha256[:9]} caracteres={contexto.caracteres_originales}"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `services/albaranes-email/infrastructure/graph/mail_client.py:39` [aritmetico]

- Original: `self._dentro_sin_texto += 1`
- Mutado:   `self._dentro_sin_texto -= 1`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `services/albaranes-email/infrastructure/graph/mail_client.py:45` [entero]

- Original: `self._dentro_sin_texto = max(0, self._dentro_sin_texto - 1)`
- Mutado:   `self._dentro_sin_texto = max(0, self._dentro_sin_texto - 2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `services/albaranes-email/infrastructure/graph/mail_client.py:305` [comparacion]

- Original: `if response.status_code >= 300:`
- Mutado:   `if response.status_code > 300:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 25. `services/albaranes-email/infrastructure/graph/mail_client.py:305` [entero]

- Original: `if response.status_code >= 300:`
- Mutado:   `if response.status_code >= 301:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 26. `services/albaranes-front/domain/models/review_models.py:928` [entero]

- Original: `historia = [aviso.replace("Obra: ", "Al extraer, ", 1)] if aviso else []`
- Mutado:   `historia = [aviso.replace("Obra: ", "Al extraer, ", 2)] if aviso else []`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

