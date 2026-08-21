<!-- progress/mutacion_F-040.md -->
# F-040 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-040` el 2026-08-21 20:51.

## Alcance

Origen del diff: **rama** (`2ccb8acd8e85e9eff1cfc80bcf7cf9c52cfeb11b` .. `feature/F-040-campana-dimensionada-y-honesta`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 362 |
| `harness/mutacion_paralela.py` | 30 |
| `harness/rigor.py` | 20 |
| **Total** | **412** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 49 |
| Mutantes evaluados | 20 |
| Muertos | 17 |
| Supervivientes | 3 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 336.3 s |
| SHA de HEAD medido | `e73a20791b106ca47bb929ca8051068ebf2a462b` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_fly11ff6/wk_0` | 64.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_fly11ff6/wk_1` | 68.3 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_fly11ff6/wk_2` | 64.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-040_fly11ff6/wk_3` | 64.7 |
| Media por mutante evaluado (s) | 16.8 |
| Timeout efectivo por mutante (s) | 137 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | sí — 20 de 49 mutantes, semilla `20260820`, nivel `estandar` |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/mutacion.py:1942` [entero]

- Original: `return min(max(1, ((os.cpu_count() or 1) - 2) // 2), TOPE_WORKERS)`
- Mutado:   `return min(max(2, ((os.cpu_count() or 1) - 2) // 2), TOPE_WORKERS)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `harness/mutacion.py:1942` [entero]

- Original: `return min(max(1, ((os.cpu_count() or 1) - 2) // 2), TOPE_WORKERS)`
- Mutado:   `return min(max(1, ((os.cpu_count() or 2) - 2) // 2), TOPE_WORKERS)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `harness/mutacion_paralela.py:407` [booleano]

- Original: `timeout_fijado: bool = False,`
- Mutado:   `timeout_fijado: bool = True,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

