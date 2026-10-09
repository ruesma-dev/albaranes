<!-- progress/mutacion_F-065_fase1.md -->
# F-065 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-065` el 2026-10-09 20:25.

## Alcance

Origen del diff: **rama** (`a094f44cc7cad022d9ac9e30aff7e8db8bf9def0` .. `feature/F-065-lineas-editadas-y-reparto`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/infrastructure/database/orm_valuation_models.py` | 10 |
| `services/albaran-valoracion-persist/infrastructure/database/schema_contribution.py` | 9 |
| `services/albaranes-front/application/services/review_service.py` | 85 |
| `services/albaranes-front/domain/models/review_models.py` | 278 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 466 |
| `services/albaranes-front/interface_adapters/web/app.py` | 77 |
| **Total** | **925** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 131 |
| Mutantes evaluados | 131 |
| Muertos | 131 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1693.2 s |
| SHA de HEAD medido | `d4fe841c6af96490aa21f683574e0e7f9bf93784` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-065_xlb129om/wk_0/services/albaran-valoracion-persist` | 8.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-065_xlb129om/wk_0/services/albaranes-front` | 86.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-065_xlb129om/wk_1/services/albaranes-front` | 84.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-065_xlb129om/wk_2/services/albaranes-front` | 89.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-065_xlb129om/wk_3/services/albaranes-front` | 84.5 |
| Media por mutante evaluado (s) | 12.9 |
| Timeout efectivo por mutante (s) | 179 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

