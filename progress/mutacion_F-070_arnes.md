<!-- progress/mutacion_F-070_arnes.md -->
# F-070 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-070` el 2026-10-15 00:14.

## Alcance

Origen del diff: **rama** (`4f1e80224f0c831ac2822106c35d4734fec9f04f` .. `feature/F-070-obra-con-cero-inicial`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-alta-sigrid/domain/services/validador_alta.py` | 11 |
| `services/albaranes-comun/ruesma_comun/obras/__init__.py` | 14 |
| `services/albaranes-comun/ruesma_comun/obras/codigo.py` | 37 |
| `services/albaranes-front/infrastructure/database/review_repository.py` | 6 |
| `services/albaranes-front/infrastructure/sigrid/sigrid_lookup_client.py` | 10 |
| `services/albaranes-persistencia/application/services/albaran_normalizer.py` | 13 |
| `services/albaranes-persistencia/application/services/header_resolver_service.py` | 4 |
| **Total** | **95** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 4 |
| Mutantes evaluados | 4 |
| Muertos | 4 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 446.4 s |
| SHA de HEAD medido | `67e18985cfc4d18e63bb9cecbfc70b72ba5540d3` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-070_6zn0_i5n/wk_0/services/albaranes-alta-sigrid` | 38.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-070_6zn0_i5n/wk_1/services/albaranes-comun` | 212.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-070_6zn0_i5n/wk_2/services/albaranes-comun` | 209.8 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-070_6zn0_i5n/wk_3/services/albaranes-comun` | 211.7 |
| Media por mutante evaluado (s) | 111.6 |
| Timeout efectivo por mutante (s) | 425 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

