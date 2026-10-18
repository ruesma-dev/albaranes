<!-- progress/mutacion_F-073.md -->
# F-073 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-073` el 2026-10-17 15:35.

## Alcance

Origen del diff: **rama** (`e09916fcd8431454e9ec6a76aa3346a9c865f9ac` .. `feature/F-073-proveedor-por-similitud`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaranes-persistencia/application/services/header_resolver_service.py` | 123 |
| `services/albaranes-persistencia/application/services/similitud_proveedor.py` | 204 |
| `services/albaranes-persistencia/domain/models/header_resolution_models.py` | 4 |
| `services/albaranes-persistencia/scripts/verificar_f052_proveedores_obra.py` | 3 |
| **Total** | **334** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 71 |
| Mutantes evaluados | 71 |
| Muertos | 69 |
| Supervivientes | 2 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 293.2 s |
| SHA de HEAD medido | `0c169a14fd8bbe851dda20b5e0bdc618262e4046` |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-073_4mo5gjk9/wk_0/services/albaranes-persistencia` | 22.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-073_4mo5gjk9/wk_1/services/albaranes-persistencia` | 22.7 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-073_4mo5gjk9/wk_2/services/albaranes-persistencia` | 22.6 |
| Línea base (s) — `C:/Users/pgris/AppData/Local/Temp/mutacion_F-073_4mo5gjk9/wk_3/services/albaranes-persistencia` | 33.9 |
| Media por mutante evaluado (s) | 4.1 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 4 |
| Muestreo | no: campaña completa |

## Historia de la campaña

| Pasada | Mutantes | Muertos | Supervivientes | Qué se hizo |
|---|---|---|---|---|
| 1 (HEAD `9f7f489`) | 71 | 60 | 11 | 7 eran huecos de test: commit `0a5d6d3` (5 tests en `test_f073_eleccion.py`, sección T11) |
| 2 (HEAD `0a5d6d3`) | 71 | 67 | 4 | los 2 de la frontera margen − tolerancia: test en el commit siguiente |
| 3 (esta) | 71 | **69** | **2** | los 2 son equivalentes (abajo) |

En la pasada 1 sobrevivieron: el `_clave_cif` del resolver (`or`→`and`), «≥ 5» en la palabra leída y en la del otro,
el desempate por nombre de `_orden`, `frozen=True` en las dos dataclasses, la contención (`or`→`and`), y `>=`/`<`
contra la tolerancia, además de los dos equivalentes de abajo.

## Supervivientes

Cada superviviente es una línea que ningún test comprueba de verdad, o una mutación equivalente. Distinguirlo es trabajo del implementer: ningún análisis puede quedarse sin completar al cerrar la feature.

### 1. `services/albaranes-persistencia/application/services/similitud_proveedor.py:93` [entero]

- Original: `and abs(len(otra) - len(palabra)) <= 1  # condición necesaria`
- Mutado:   `and abs(len(otra) - len(palabra)) <= 2  # condición necesaria`

#### Análisis (implementer, 2026-10-17): EQUIVALENTE · **ACEPTADO por el humano (2026-10-17, por el chat al líder: «Acepto los dos»)**; confirmado por el reviewer (RM5)

> Por qué ningún test lo caza: es un filtro previo que solo ahorra cálculo. Una distancia de Levenshtein ≤ 1
> implica |Δlongitud| ≤ 1, así que `distancia_edicion(palabra, otra) <= 1`, en la condición siguiente, rechaza
> igualmente todo par que deje pasar `<= 2` y no `<= 1`. El resultado de `_casa` es el mismo para cualquier entrada;
> solo cambia el tiempo.
> Decisión: equivalente. El filtro se queda: medido sobre los 3.543 proveedores del doble, una búsqueda global tarda
> 0,22 s con filtro y 0,37 s sin él.

### 2. `services/albaranes-persistencia/application/services/similitud_proveedor.py:202` [comparacion]

- Original: `if actual is None or _orden(candidato) < _orden(actual):`
- Mutado:   `if actual is None or _orden(candidato) <= _orden(actual):`

#### Análisis (implementer, 2026-10-17): EQUIVALENTE · **ACEPTADO por el humano (2026-10-17, por el chat al líder: «Acepto los dos»)**; confirmado por el reviewer (RM5)

> Por qué ningún test lo caza: `<` y `<=` solo difieren cuando `_orden(candidato) == _orden(actual)`, es decir,
> con la misma similitud, el mismo CIF recortado y el mismo nombre. Como la similitud depende solo del nombre leído
> y del nombre del candidato, ese candidato es un `CandidatoNombre` igual campo a campo al que ya estaba (dataclass
> congelada con igualdad por valor). Sustituirlo por un igual no cambia `por_clave` ni el resultado.
> **Precisión de la review (H1, 2026-10-17):** `_orden` compara `nombre or ""`, así que también coinciden `None` y
> `""`: objetos distintos, los dos con similitud 0 y pintados `'?'` en la nota. CIF, decisión, nota y log no cambian
> (100.000 casos aleatorios del reviewer, 0 diferencias).
> Decisión: equivalente. Con el nombre distinto ya lo mata
> `test_f073_t11_mismo_cif_misma_similitud_gana_el_nombre_menor_sin_mirar_el_orden`.

