<!-- progress/mutacion_F-108.md -->
# F-108 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-108` el 2026-10-31 22:56.

## Alcance

Origen del diff: **rama** (`c1f703508a325e3022617a53e5772b9ef22ec511` .. `feature/F-108-fecha-numero-editables`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-front/domain/models/review_models.py` | 56 |
| `services/albaranes-front/domain/services/fecha_albaran.py` | 112 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 37 |
| `services/albaranes-front/interface_adapters/web/app.py` | 24 |
| **Total** | **229** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 35 |
| Mutantes evaluados | 20 |
| Muertos | 20 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 1559.9 s |
| SHA de HEAD medido | `372b5a045c1e9936f9db6f0a5d99ca101b3829b6` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-108_9my627zt/wk_0/services/albaranes-front` | 315.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-108_9my627zt/wk_1/services/albaranes-front` | 310.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-108_9my627zt/wk_2/services/albaranes-front` | 317.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-108_9my627zt/wk_3/services/albaranes-front` | 318.5 |
| Media por mutante evaluado (s) | 78.0 |
| Timeout efectivo por mutante (s) | 637 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | sí — 20 de 35 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

