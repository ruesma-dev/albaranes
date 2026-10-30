<!-- progress/mutacion_F-113.md -->
# F-113 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-113` el 2026-10-30 23:04.

## Alcance

Origen del diff: **rama** (`5dd1f455924ea9cf4a8912ee5a35b9ec8c812c89` .. `feature/F-113-mime-adjuntos-octet-stream`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-api/application/pipelines/extract_albaran_pipeline.py` | 7 |
| `services/albaranes-comun/ruesma_comun/__init__.py` | 1 |
| `services/albaranes-comun/ruesma_comun/llm/llm_client.py` | 37 |
| `services/albaranes-comun/ruesma_comun/mime.py` | 164 |
| `services/albaranes-email/application/pipelines/polling_pipeline.py` | 30 |
| `services/albaranes-email/scripts/__init__.py` | 2 |
| `services/albaranes-email/scripts/medir_f113_octet_stream.py` | 174 |
| **Total** | **415** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 44 |
| Mutantes evaluados | 20 |
| Muertos | 19 |
| Supervivientes | 1 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 650.2 s |
| SHA de HEAD medido | `be9439c2099a1871c339dc48112cf3a9d756cc11` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-113_kqcpy9x0/wk_0/services/albaranes-comun` | 182.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-113_kqcpy9x0/wk_0/services/albaranes-email` | 18.2 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-113_kqcpy9x0/wk_1/services/albaranes-comun` | 187.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-113_kqcpy9x0/wk_1/services/albaranes-email` | 17.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-113_kqcpy9x0/wk_2/services/albaranes-comun` | 186.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-113_kqcpy9x0/wk_2/services/albaranes-email` | 17.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-113_kqcpy9x0/wk_3/services/albaranes-comun` | 187.4 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-113_kqcpy9x0/wk_3/services/albaranes-email` | 16.7 |
| Media por mutante evaluado (s) | 32.5 |
| Timeout efectivo por mutante (s) | 376 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | sí — 20 de 44 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-email/scripts/medir_f113_octet_stream.py:151` [entero]

- Original: `parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])`
- Mutado:   `parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[1])`

#### Análisis (implementer, 2026-10-30)

> Por qué ningún test lo caza: solo cambia el texto de `--help` (la línea 1 del
> docstring es la vacía) y ningún test pedía la ayuda. No es equivalente: la
> ayuda dejaría de decir qué mide el script.
> Decisión: **test nuevo** `test_f113_r20_la_ayuda_dice_que_mide`
> (`services/albaranes-email/tests/test_f113_medicion.py`). Comprobado a mano:
> con el mutante aplicado el test cae (`1 failed`); con el original, 17 passed.
> Hueco real cerrado: **0 supervivientes** tras el test.

