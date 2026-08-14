<!-- progress/mutacion_F-012.md -->
# F-012 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-012` el 2026-08-14 03:20.

## Alcance

Origen del diff: **rama** (`73e4db0819466c1083c28a8fdf4dee2da65533e5` .. `feature/F-012-mutacion-paralela`).

| Fichero | Líneas en alcance |
|---|---|
| `harness/mutacion.py` | 88 |
| `harness/mutacion_paralela.py` | 453 |
| `harness/rigor.py` | 15 |
| **Total** | **556** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 61 |
| Mutantes evaluados | 61 |
| Muertos | 53 |
| Supervivientes | 8 |
| Timeouts | 0 |
| Tiempo total | 837.6 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/mutacion.py:587` [entero]

- Original: `return min(max(1, (os.cpu_count() or 1) - 2), TOPE_WORKERS)`
- Mutado:   `return min(max(1, (os.cpu_count() or 2) - 2), TOPE_WORKERS)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `harness/mutacion.py:664` [booleano]

- Original: `eco=lambda linea: print(linea, flush=True),`
- Mutado:   `eco=lambda linea: print(linea, flush=False),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `harness/mutacion.py:677` [booleano]

- Original: `eco=lambda linea: print(linea, flush=True),`
- Mutado:   `eco=lambda linea: print(linea, flush=False),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `harness/mutacion_paralela.py:142` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `harness/mutacion_paralela.py:214` [comparacion]

- Original: `if codigo != 0:`
- Mutado:   `if codigo == 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `harness/mutacion_paralela.py:214` [entero]

- Original: `if codigo != 0:`
- Mutado:   `if codigo != 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `harness/mutacion_paralela.py:218` [booleano]

- Original: `shutil.rmtree(ruta, ignore_errors=True)`
- Mutado:   `shutil.rmtree(ruta, ignore_errors=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `harness/mutacion_paralela.py:222` [booleano]

- Original: `shutil.rmtree(self._temporal, ignore_errors=True)`
- Mutado:   `shutil.rmtree(self._temporal, ignore_errors=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

