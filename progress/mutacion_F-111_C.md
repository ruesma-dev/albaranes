<!-- progress/mutacion_F-111_C.md -->
# F-111 · Campaña de mutación

Generado por `python -m harness.mutacion --feature F-111 --base 16023b0 --max-mutantes 0 --workers 1 --salida
progress/mutacion_F-111_C.md` el 2026-11-06 12:57 (pasada 2, definitiva). Alcance: la **parte C** (diff desde la
spec de la parte C, `16023b0`). La campaña de A y B está en `progress/mutacion_F-111.md`. `--workers 1` porque había
ficheros de `progress/` sin commitear (la herramienta se niega a lanzar worktrees desde HEAD en ese caso).

## Alcance

Origen del diff: **rama** (`16023b0a3b2a753b4da34b3c5fb193994f3bcb54` .. `feature/F-111-residuos-contenedores-y-partida`).

| Fichero | Líneas en alcance |
|---|---|
| `services/albaran-valoracion-persist/application/services/partida_residuos.py` | 167 |
| **Total** | **167** |

## Totales

| Métrica | Valor |
|---|---|
| Mutantes generados | 13 |
| Mutantes evaluados | 13 |
| Muertos | 13 |
| Supervivientes | 0 |
| Timeouts | 0 |
| Sin veredicto (base rota) | 0 |
| Tiempo total | 612.3 s |
| SHA de HEAD medido | `2e8ea2e0dcb6064236105a7feb7cf7dc5d0d05d9` |
| Línea base (s) — `services/albaran-valoracion-persist` | 45.0 |
| Media por mutante evaluado (s) | 47.1 |
| Timeout efectivo por mutante (s) | 120 — derivado de la línea base × 2.0 |
| Suelo configurado (s) | 120 |
| Workers | 1 |
| Muestreo | no: campaña completa |

## Supervivientes

Ninguno: cada mutación aplicada la cazó al menos un test.



## Pasada 1 (2026-11-06 12:06, 4 workers, sobre `b69192a`)

14 mutantes, 13 muertos, **1 superviviente**: `partida_residuos.py:251` `caidas = 0` → `caidas = 1`. Por qué
ningún test lo cazaba: `caidas` solo sale en el log (`caidas_al_capitulo=`) y ningún test miraba ese campo. **Hueco
real, test nuevo** (T20, `2e8ea2e`): `test_f111_r46_el_log_dice_el_paso` exige `caidas_al_capitulo=0` y
`test_f111_r46_el_log_cuenta_las_caidas_al_capitulo` exige `=1` con una línea caída.

## Anexo · mutantes a mano (rigor `critico`: la herramienta solo genera 13–14 en este diff)

Script en el scratchpad de la sesión (`mutantes_c.py`); cada mutante se aplica a `partida_residuos.py`, se lanzan
`test_f111_partida_contrato.py`, `test_f111_partida_residuos.py` y `test_f111_pipeline.py` con `-x`, y se restaura.

**Ronda 1 (sobre `b69192a`): 28 mutantes, 4 supervivientes**, todos resueltos en T20:

| Superviviente | Análisis | Decisión |
|---|---|---|
| quitar `if normalizar_partida(lectura) is None: continue` | `resolver_partida_obra` ya da `no_aplica` a una lectura vacía | **equivalente**: código redundante, eliminado |
| quitar `or codigo in vistas` | el dict deduplica y conserva el orden de la primera inserción | **equivalente**: código redundante, eliminado |
| `self._alm` → `None` en `asignar` | solo cambia algo si la obra tiene una hoja `ALM`; ningún test de `asignar` la tenía | **hueco**: `test_f111_r37_asignar_pasa_el_alm_un_alm_del_contrato_no_es_hoja` |
| `lineas_contrato or ()` → `lineas_contrato` | el DTO da `[]` por defecto; nadie probaba `None` | **hueco**: `test_f111_r37_lineas_de_contrato_none_tupla_vacia` |

**Ronda 2 (tras T20): 25 aplicables, 25 muertos, 0 supervivientes** (los 3 que ya no aplican son los dos eliminados y
el de `cod_repetido`, que cambió de forma: su versión nueva, `or lista.cod_repetido(codigo)` → nada, se probó aparte
y **muere**). Cubren: R37 (`fuera_de_lista`/`ambigua` aceptadas, sin `normalizada`, `alm`, `None`), R38 (`not in`,
conjunto del capítulo en vez del contrato), R39 (sin paso 2, paso 2 con el capítulo), R42 (prefijo cambiado), R46
(paso del log, caídas), R43 (sin caída, intento con el capítulo, caída con todas las líneas, con el prefijo del
contrato, sin intento en asignadas/revisión, sin `update`, intento tras el motivo, intento en la cabecera) y
`_resolver` (motivo de vacío, código fuera del conjunto aceptado, motivo sin candidatas).
