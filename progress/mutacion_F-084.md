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

#### Análisis

> Por qué ningún test lo caza: el bloque resolvía las dos costuras a la vez con `crear or create_engine` y `abrir or Session`; entrar en él con una costura ya inyectada no cambia nada (el `or` conserva la inyectada), así que las tres variantes de la condición se comportan igual. Equivalente en el código de `d4dbe97`.
> Decisión: código reescrito en `d0f91b1` (una condición por costura, `if crear is None: from sqlalchemy import create_engine as crear`): ahí la mutación ya no es equivalente y `test_f084_t15_la_sesion_real_es_de_solo_lectura_sin_conectar` la caza. Remedido en `progress/mutacion_F-084_sv5_documentos.md`.

### 2. `evals/procesos/sv5_documentos.py:222` [logico]

- Original: `if crear is None or abrir is None:  # pragma: no cover - las reales`
- Mutado:   `if crear is None and abrir is None:  # pragma: no cover - las reales`

#### Análisis

> Por qué ningún test lo caza: el bloque resolvía las dos costuras a la vez con `crear or create_engine` y `abrir or Session`; entrar en él con una costura ya inyectada no cambia nada (el `or` conserva la inyectada), así que las tres variantes de la condición se comportan igual. Equivalente en el código de `d4dbe97`.
> Decisión: código reescrito en `d0f91b1` (una condición por costura, `if crear is None: from sqlalchemy import create_engine as crear`): ahí la mutación ya no es equivalente y `test_f084_t15_la_sesion_real_es_de_solo_lectura_sin_conectar` la caza. Remedido en `progress/mutacion_F-084_sv5_documentos.md`.

### 3. `evals/procesos/sv5_documentos.py:222` [comparacion]

- Original: `if crear is None or abrir is None:  # pragma: no cover - las reales`
- Mutado:   `if crear is None or abrir is not None:  # pragma: no cover - las reales`

#### Análisis

> Por qué ningún test lo caza: el bloque resolvía las dos costuras a la vez con `crear or create_engine` y `abrir or Session`; entrar en él con una costura ya inyectada no cambia nada (el `or` conserva la inyectada), así que las tres variantes de la condición se comportan igual. Equivalente en el código de `d4dbe97`.
> Decisión: código reescrito en `d0f91b1` (una condición por costura, `if crear is None: from sqlalchemy import create_engine as crear`): ahí la mutación ya no es equivalente y `test_f084_t15_la_sesion_real_es_de_solo_lectura_sin_conectar` la caza. Remedido en `progress/mutacion_F-084_sv5_documentos.md`.

### 4. `evals/procesos/sv5_documentos.py:274` [entero]

- Original: `sys.path.insert(0, str(RAIZ_SV5))`
- Mutado:   `sys.path.insert(1, str(RAIZ_SV5))`

#### Análisis

> Por qué ningún test lo caza: en el subproceso `python -m`, `sys.path[0]` es la raíz del repositorio, que no tiene paquetes `domain`, `application` ni `infrastructure`; poner sv5 en la posición 1 resuelve los mismos imports. Equivalente.
> Decisión: en `d0f91b1` el subproceso pone sv5 delante con `sys.path = [str(RAIZ_SV5), *sys.path]`, como `sv5_modelos`; sin literal entero que mutar. Remedido en `progress/mutacion_F-084_sv5_documentos.md`.

