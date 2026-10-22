<!-- progress/mutacion_F-084.md -->
# F-084 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-084` el 2026-10-22 22:31.

## Alcance

Origen del diff: **rama** (`ac34ad8fa49c58048b8d20a14c6a65e7a73a6067` .. `feature/F-084-banco-valoracion`).

| Fichero | Líneas en alcance |
|---|---|
| `evals/contratos.py` | 764 |
| `evals/informe.py` | 26 |
| `evals/modelos.py` | 6 |
| `evals/procesos/sv5_documentos.py` | 286 |
| `evals/procesos/sv5_modelos.py` | 2 |
| `evals/procesos/sv5_valoracion.py` | 165 |
| `evals/procesos/sv6_build.py` | 122 |
| `evals/revision/escritura.py` | 3 |
| `evals/runner.py` | 166 |
| **Total** | **1540** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 198 |
| Mutantes evaluados | 198 |
| Muertos | 194 |
| Supervivientes | 4 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 19300.7 s |
| SHA de HEAD medido | `d4dbe97c18826d163683da0272296498ef86f424` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ytghpori/wk_0` | 491.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ytghpori/wk_1` | 473.9 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ytghpori/wk_2` | 474.0 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-084_ytghpori/wk_3` | 491.2 |
| Media por mutante evaluado (s) | 97.5 |
| Timeout efectivo por mutante (s) | 984 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `evals/procesos/sv5_documentos.py:222` [comparacion]

- Original: `if crear is None or abrir is None:  # pragma: no cover - las reales`
- Mutado:   `if crear is not None or abrir is None:  # pragma: no cover - las reales`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `evals/procesos/sv5_documentos.py:222` [logico]

- Original: `if crear is None or abrir is None:  # pragma: no cover - las reales`
- Mutado:   `if crear is None and abrir is None:  # pragma: no cover - las reales`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `evals/procesos/sv5_documentos.py:222` [comparacion]

- Original: `if crear is None or abrir is None:  # pragma: no cover - las reales`
- Mutado:   `if crear is None or abrir is not None:  # pragma: no cover - las reales`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `evals/procesos/sv5_documentos.py:274` [entero]

- Original: `sys.path.insert(0, str(RAIZ_SV5))`
- Mutado:   `sys.path.insert(1, str(RAIZ_SV5))`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

