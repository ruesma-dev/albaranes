<!-- progress/mutacion_F-012.md -->
# F-012 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-012` el 2026-08-14 02:41.

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
| Muertos | 37 |
| Supervivientes | 24 |
| Timeouts | 0 |
| Tiempo total | 910.0 s |
| Muestreo | no: campaña completa |

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `harness/mutacion.py:587` [entero]

- Original: `return min(max(1, (os.cpu_count() or 1) - 2), TOPE_WORKERS)`
- Mutado:   `return min(max(1, (os.cpu_count() or 2) - 2), TOPE_WORKERS)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 2. `harness/mutacion.py:649` [comparacion]

- Original: `if workers >= 2 and ejecutor is None:`
- Mutado:   `if workers > 2 and ejecutor is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 3. `harness/mutacion.py:649` [entero]

- Original: `if workers >= 2 and ejecutor is None:`
- Mutado:   `if workers >= 3 and ejecutor is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 4. `harness/mutacion.py:649` [logico]

- Original: `if workers >= 2 and ejecutor is None:`
- Mutado:   `if workers >= 2 or ejecutor is None:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 5. `harness/mutacion.py:664` [booleano]

- Original: `eco=lambda linea: print(linea, flush=True),`
- Mutado:   `eco=lambda linea: print(linea, flush=False),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 6. `harness/mutacion.py:677` [booleano]

- Original: `eco=lambda linea: print(linea, flush=True),`
- Mutado:   `eco=lambda linea: print(linea, flush=False),`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 7. `harness/mutacion.py:678` [logico]

- Original: `ejecutor_de=factoria if servicios and ejecutor is None else None,`
- Mutado:   `ejecutor_de=factoria if servicios or ejecutor is None else None,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 8. `harness/mutacion_paralela.py:142` [booleano]

- Original: `text=True,`
- Mutado:   `text=False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 9. `harness/mutacion_paralela.py:147` [logico]

- Original: `return proceso.returncode, (proceso.stdout or "") + (proceso.stderr or "")`
- Mutado:   `return proceso.returncode, (proceso.stdout or "") + (proceso.stderr and "")`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 10. `harness/mutacion_paralela.py:214` [comparacion]

- Original: `if codigo != 0:`
- Mutado:   `if codigo == 0:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 11. `harness/mutacion_paralela.py:214` [entero]

- Original: `if codigo != 0:`
- Mutado:   `if codigo != 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 12. `harness/mutacion_paralela.py:218` [booleano]

- Original: `shutil.rmtree(ruta, ignore_errors=True)`
- Mutado:   `shutil.rmtree(ruta, ignore_errors=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 13. `harness/mutacion_paralela.py:222` [booleano]

- Original: `shutil.rmtree(self._temporal, ignore_errors=True)`
- Mutado:   `shutil.rmtree(self._temporal, ignore_errors=False)`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 14. `harness/mutacion_paralela.py:288` [comparacion]

- Original: `if max_mutantes is not None and generados > max_mutantes:`
- Mutado:   `if max_mutantes is not None and generados >= max_mutantes:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 15. `harness/mutacion_paralela.py:293` [booleano]

- Original: `True,`
- Mutado:   `False,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 16. `harness/mutacion_paralela.py:305` [entero]

- Original: `resto = linea.split("] ", 1)[1] if linea.startswith("[") and "] " in linea else linea`
- Mutado:   `resto = linea.split("] ", 2)[1] if linea.startswith("[") and "] " in linea else linea`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 17. `harness/mutacion_paralela.py:305` [logico]

- Original: `resto = linea.split("] ", 1)[1] if linea.startswith("[") and "] " in linea else linea`
- Mutado:   `resto = linea.split("] ", 1)[1] if linea.startswith("[") or "] " in linea else linea`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 18. `harness/mutacion_paralela.py:339` [entero]

- Original: `workers: int = 2,`
- Mutado:   `workers: int = 3,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 19. `harness/mutacion_paralela.py:393` [aritmetico]

- Original: `segundos=time.monotonic() - inicio,`
- Mutado:   `segundos=time.monotonic() + inicio,`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 20. `harness/mutacion_paralela.py:401` [comparacion]

- Original: `if efectivo < 2:`
- Mutado:   `if efectivo <= 2:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 21. `harness/mutacion_paralela.py:401` [entero]

- Original: `if efectivo < 2:`
- Mutado:   `if efectivo < 3:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 22. `harness/mutacion_paralela.py:451` [entero]

- Original: `raise fallos[0]`
- Mutado:   `raise fallos[1]`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 23. `harness/rigor.py:131` [comparacion]

- Original: `if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:`
- Mutado:   `if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 1:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

### 24. `harness/rigor.py:131` [entero]

- Original: `if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:`
- Mutado:   `if isinstance(valor, bool) or not isinstance(valor, int) or valor < 2:`

#### Análisis (PENDIENTE del implementer)

> Por qué ningún test lo caza: PENDIENTE.
> Decisión: ¿test nuevo o mutante equivalente justificado?

