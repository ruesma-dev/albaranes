<!-- progress/mutacion_F-083.md -->
# F-083 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-083` el 2026-10-21 07:01.

## Alcance

Origen del diff: **rama** (`7facc862439cb9c35499e33bf06b9bf5731854fb` .. `feature/F-083-comparar-modelos`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/comparar_modelos.py` | 665 |
| `evals/costes.py` | 437 |
| `evals/decision.py` | 202 |
| `evals/informe_modelos.py` | 238 |
| `evals/procesos/medidor.py` | 210 |
| `evals/procesos/sv2_extraccion.py` | 7 |
| `evals/procesos/sv2_modelos.py` | 127 |
| `evals/procesos/sv5_modelos.py` | 96 |
| `evals/procesos/sv5_valoracion.py` | 61 |
| `evals/runner.py` | 51 |
| `services/albaranes-comun/ruesma_comun/llm/claude_messages_client.py` | 11 |
| **Total** | **2105** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 366 |
| Mutantes evaluados | 366 |
| Muertos | 366 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 21907.1 s |
| SHA de HEAD medido | `96a59a3043db3da53877f18e9353dcd61caab3a2` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_041ylyr3/wk_0` | 306.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_041ylyr3/wk_1` | 306.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_041ylyr3/wk_2` | 324.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-083_041ylyr3/wk_2/services/albaranes-comun` | 143.2 |
| Media por mutante evaluado (s) | 59.9 |
| Timeout efectivo por mutante (s) | 649 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 3 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.

