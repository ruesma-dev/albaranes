<!-- progress/mutacion_F-002.md -->
# F-002 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-002` el 2026-08-14 20:59.

## Alcance

Origen del diff: **rama** (`89bc79d62e97bcd5f70b8e60d2ffc4b2f2ce40cc` .. `feature/F-002-obra-proveedor`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-api/application/services/albaran_extraction_service.py` | 88 |
| `services/albaranes-api/config/settings.py` | 37 |
| `services/albaranes-api/domain/ports/obras_activas_provider.py` | 27 |
| `services/albaranes-api/infrastructure/sigrid/__init__.py` | 1 |
| `services/albaranes-api/infrastructure/sigrid/obras_activas_cache.py` | 71 |
| `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py` | 185 |
| `services/albaranes-api/interface_adapters/api/app.py` | 30 |
| `services/albaranes-api/interface_adapters/composition.py` | 30 |
| `services/albaranes-persistencia/application/pipelines/persist_albaran_pipeline.py` | 28 |
| `services/albaranes-persistencia/application/services/fecha_guard_service.py` | 141 |
| `services/albaranes-persistencia/application/services/header_resolver_service.py` | 216 |
| `services/albaranes-persistencia/application/services/obra_enrichment_service.py` | 78 |
| `services/albaranes-persistencia/config/settings.py` | 21 |
| `services/albaranes-persistencia/domain/ports/header_resolver_ports.py` | 36 |
| `services/albaranes-persistencia/domain/ports/obra_merge_repository_port.py` | 30 |
| `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py` | 267 |
| `services/albaranes-persistencia/interface_adapters/api/app.py` | 11 |
| `services/albaranes-persistencia/interface_adapters/composition.py` | 11 |
| `services/albaranes-persistencia/interface_adapters/worker/persistence_worker.py` | 21 |
| `services/albaranes-persistencia/interface_adapters/worker/ports.py` | 18 |
| `services/albaranes-persistencia/interface_adapters/worker/workflow_context_adapter.py` | 118 |
| `services/albaranes-persistencia/main_worker.py` | 19 |
| **Total** | **1484** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 108 |
| Mutantes evaluados | 108 |
| Muertos | 94 |
| Supervivientes | 14 |
| Timeouts | 0 |
| Tiempo total | 50.3 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py:180` [logico]

- Original: `f"{(response.text or '')[:300]}"`
- Mutado:   `f"{(response.text and '')[:300]}"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py:180` [entero]

- Original: `f"{(response.text or '')[:300]}"`
- Mutado:   `f"{(response.text or '')[:301]}"`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `services/albaranes-api/infrastructure/sigrid/sigrid_api_obras_client.py:185` [logico]

- Original: `return list(body.get("columns") or []), list(body.get("rows") or [])`
- Mutado:   `return list(body.get("columns") and []), list(body.get("rows") or [])`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `services/albaranes-persistencia/application/services/header_resolver_service.py:102` [logico]

- Original: `if not a or not b:`
- Mutado:   `if not a and not b:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:147` [booleano]

- Original: `return json.dumps(motivos, ensure_ascii=False, indent=2)`
- Mutado:   `return json.dumps(motivos, ensure_ascii=True, indent=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:147` [entero]

- Original: `return json.dumps(motivos, ensure_ascii=False, indent=2)`
- Mutado:   `return json.dumps(motivos, ensure_ascii=False, indent=3)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:164` [booleano]

- Original: `return json.dumps(motivos, ensure_ascii=False, indent=2)`
- Mutado:   `return json.dumps(motivos, ensure_ascii=True, indent=2)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:164` [entero]

- Original: `return json.dumps(motivos, ensure_ascii=False, indent=2)`
- Mutado:   `return json.dumps(motivos, ensure_ascii=False, indent=3)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1672` [entero]

- Original: `return fila[0] if fila else None`
- Mutado:   `return fila[1] if fila else None`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1697` [comparacion]

- Original: `if nuevas == actuales:`
- Mutado:   `if nuevas != actuales:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1722` [booleano]

- Original: `document.review_required = True`
- Mutado:   `document.review_required = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1760` [booleano]

- Original: `document.review_required = True`
- Mutado:   `document.review_required = False`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1771` [logico]

- Original: `f"'{codigo_leido or '—'}' no corresponde a ninguna obra "`
- Mutado:   `f"'{codigo_leido and '—'}' no corresponde a ninguna obra "`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `services/albaranes-persistencia/infrastructure/database/sqlalchemy_albaran_repository.py:1797` [comparacion]

- Original: `cambio_motivos = nuevos != document.review_reasons_json`
- Mutado:   `cambio_motivos = nuevos == document.review_reasons_json`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

