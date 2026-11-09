<!-- progress/mutacion_F-112.md -->
# F-112 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-112` el 2026-11-09 10:59.

## Alcance

Origen del diff: **rama** (`6c7707fc06b780da71216dd08fd6eb51c4a8b024` .. `feature/F-112-anio-fecha-albaran`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/comparar_fecha.py` | 866 |
| `evals/procesos/sv2_fecha.py` | 122 |
| `evals/sinteticos_fecha.py` | 131 |
| `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py` | 8 |
| `services/albaranes-api/application/services/albaran_extraction_service.py` | 42 |
| `services/albaranes-api/application/services/fecha_recepcion.py` | 122 |
| `services/albaranes-api/interface_adapters/worker/extraction_worker.py` | 9 |
| **Total** | **1300** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 236 |
| Mutantes evaluados | 20 |
| Muertos | 20 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 4662.9 s |
| SHA de HEAD medido | `618c46ca64c8ccc5b0869ef8998f2d54e9c0d525` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-112_dh17n2eh/wk_0` | 467.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-112_dh17n2eh/wk_0/services/albaranes-api` | 42.5 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-112_dh17n2eh/wk_1` | 469.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-112_dh17n2eh/wk_1/services/albaranes-api` | 24.0 |
| Media por mutante evaluado (s) | 233.1 |
| Timeout efectivo por mutante (s) | 940 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 2 |
| Muestreo | sí — 20 de 236 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

