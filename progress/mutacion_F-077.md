<!-- progress/mutacion_F-077.md -->
# F-077 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-077` el 2026-10-17 10:16.

## Alcance

Origen del diff: **rama** (`20bf230e474ce59b6f9502a4d092ad87c66379ae` .. `feature/F-077-guardar-y-aprobar`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-front/application/services/review_service.py` | 34 |
| `services/albaranes-front/domain/models/alta_sigrid_models.py` | 125 |
| `services/albaranes-front/domain/models/review_models.py` | 50 |
| `services/albaranes-front/domain/services/alta_sigrid.py` | 76 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 7 |
| `services/albaranes-front/interface_adapters/web/app.py` | 9 |
| **Total** | **301** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 39 |
| Mutantes evaluados | 20 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 980.8 s |
| SHA de HEAD medido | `e1d99376e6f90d702d863cee1739a543fddcd422` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_6uvmcvjx/wk_0/services/albaranes-front` | 169.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_6uvmcvjx/wk_1/services/albaranes-front` | 169.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_6uvmcvjx/wk_2/services/albaranes-front` | 169.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-077_6uvmcvjx/wk_3/services/albaranes-front` | 169.9 |
| Media por mutante evaluado (s) | 49.0 |
| Timeout efectivo por mutante (s) | 340 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | sí — 20 de 39 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-front/interface_adapters/web/app.py:1761` [booleano]

- Original: `@app.get("/api/documents/{document_id}/alta-sigrid/fase", include_in_schema=False)`
- Mutado:   `@app.get("/api/documents/{document_id}/alta-sigrid/fase", include_in_schema=True)`

#### Análisis (implementer, 2026-10-17)

> Por qué ningún test lo caza: los tests de la ruta (R18, R20) la llaman con `TestClient` y miran la respuesta, el
> 404 y que no publique; ninguno miraba el esquema OpenAPI, y `include_in_schema` solo cambia `/openapi.json`.
> Decisión: **hueco real, cerrado con test**. Design §1 la declara ruta interna del JS de sv4 (por eso no se toca
> `azure-apps/albaranes.md`): publicarla en el esquema sería exponerla. Test nuevo
> `test_f077_r18_la_ruta_queda_fuera_del_esquema_openapi` (`tests/test_f077_alta_fase.py`): con el mutante aplicado
> a mano falla (`1 failed`), con el código, verde. La campaña no se ha relanzado: con la semilla fija elegiría los
> mismos 20 y este quedaría muerto.

