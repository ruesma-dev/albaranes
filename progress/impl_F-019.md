<!-- progress/impl_F-019.md -->
# F-019 · Informe de implementación

**Feature**: Importe de línea: manda el unitario leído; el importe solo se
despeja si faltan campos.
**Rama**: `feature/F-019-importe-unitario-manda` (base `dev`, HEAD `cd904cd`).
**Rigor declarado**: `critico` (`harness/features.json`).
**Spec**: `specs/F-019-importe-unitario-manda/` (aprobada por el humano).
**Diagnóstico de origen**: `progress/prueba_local_feymaco_20260818.md`.

Documento en construcción: se completa tarea a tarea. La sección
«Evidencias» y las verificaciones MANUAL están al final.

---

## Fase RED — traza real del fallo antes del código

Rigor `critico`: para los requisitos centrales el test se escribió ANTES que
el código y se ejecutó para ver el fallo. Lo que sigue es la salida REAL
pegada, no un resumen.

### RED 1 — sv5, el SELECT infla el importe (R4, R7, tramo sv5 de R16)

Comando exacto (desde `services/albaran-valoracion-api`, como hace la
sección 7 bis de `init.sh`):

```
python -m pytest tests -q --tb=short
```

Salida (con `_SQL_ALBARAN_LINES` todavía sin corregir):

```
F.F...FF.                                                                [100%]
================================== FAILURES ===================================
_________ test_f019_r4_importe_leido_no_se_multiplica_por_la_cantidad _________
tests\test_f019_r4_r7_importe_select.py:156: in test_f019_r4_importe_leido_no_se_multiplica_por_la_cantidad
    assert filas[0]["importe_albaran"] == pytest.approx(35.19)
E   assert 3800.5199999999995 == 35.19 ± 3.5e-05
E
E     comparison failed
E     Obtained: 3800.5199999999995
E     Expected: 35.19 ± 3.5e-05
_____________ test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco _____________
tests\test_f019_r4_r7_importe_select.py:204: in test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco
    assert fila["importe_albaran"] == pytest.approx(linea[5]), linea[1]
E   AssertionError: PAPEL HIGIENICO (SACO 108)
E   assert 3800.5199999999995 == 35.19 ± 3.5e-05
E
E     comparison failed
E     Obtained: 3800.5199999999995
E     Expected: 35.19 ± 3.5e-05
_______ test_f019_r7_precio_neto_sin_cantidad_conserva_el_importe_leido _______
tests\test_f019_r4_r7_importe_select.py:261: in test_f019_r7_precio_neto_sin_cantidad_conserva_el_importe_leido
    assert filas[0]["importe_albaran"] == pytest.approx(35.19)
E   assert None == 35.19 ± 3.5e-05
E
E     comparison failed
E     Obtained: None
E     Expected: 35.19 ± 3.5e-05
_________ test_f019_r7_precio_neto_sin_precio_unitario_tambien_manda __________
tests\test_f019_r4_r7_importe_select.py:272: in test_f019_r7_precio_neto_sin_precio_unitario_tambien_manda
    assert filas[0]["importe_albaran"] == pytest.approx(35.19)
E   assert 3800.5199999999995 == 35.19 ± 3.5e-05
E
E     comparison failed
E     Obtained: 3800.5199999999995
E     Expected: 35.19 ± 3.5e-05
=========================== short test summary info ===========================
FAILED tests/test_f019_r4_r7_importe_select.py::test_f019_r4_importe_leido_no_se_multiplica_por_la_cantidad
FAILED tests/test_f019_r16_tramo_sv5_las_cinco_lineas_de_feymaco
FAILED tests/test_f019_r4_r7_importe_select.py::test_f019_r7_precio_neto_sin_cantidad_conserva_el_importe_leido
FAILED tests/test_f019_r4_r7_importe_select.py::test_f019_r7_precio_neto_sin_precio_unitario_tambien_manda
4 failed, 5 passed in 0.90s
```

El `3800.5199999999995` es el número del informe del 18-08 (3.800,52 €)
reproducido por el SQL de producción sobre la fila real del albarán. Los
5 tests que pasan en RED son los que describen comportamiento que NO debía
cambiar (R5 cascada, R6 hormigón, columnas del SELECT): que estuvieran ya
verdes es parte de la evidencia de que el fix es quirúrgico.

### RED 2 — sv6, el importe manda sobre el unitario leído (R8, R10)

Comando exacto (desde `services/albaran-valoracion-persist`):

```
python -m pytest tests -q --tb=short
```

Salida (con `price_reconciler.py` todavía con la precedencia de jul 2026):

```
F.....FFFF..................                                             [100%]
================================== FAILURES ===================================
___________ test_f019_r8_unitario_declarado_manda_habiendo_importe ____________
tests\test_f019_r8_r15_precedencia.py:60: in test_f019_r8_unitario_declarado_manda_habiendo_importe
    assert "albaran_unitario_manda_derivado_coincide" in resultado.reasons
E   AssertionError: assert 'albaran_unitario_manda_derivado_coincide' in ['albaran_importe_manda_declarado_coincide']
E    +  where ['albaran_importe_manda_declarado_coincide'] = PriceReconciliation(final_price=0.543, source='albaran_declared', agreement='neither', reasons=['albaran_importe_manda_declarado_coincide']).reasons
__________ test_f019_r10_discrepancia_gana_el_declarado_con_mismatch __________
tests\test_f019_r8_r15_precedencia.py:167: in test_f019_r10_discrepancia_gana_el_declarado_con_mismatch
    assert resultado.final_price == pytest.approx(0.543)
E   assert 58.65 == 0.543 ± 5.4e-07
E
E     comparison failed
E     Obtained: 58.65
E     Expected: 0.543 ± 5.4e-07
________ test_f019_r10_el_mismatch_es_lo_que_lleva_la_linea_a_revision ________
tests\test_f019_r8_r15_precedencia.py:192: in test_f019_r10_el_mismatch_es_lo_que_lleva_la_linea_a_revision
    assert review_required is True
E   assert False is True
_____________ test_f019_r10_dentro_de_tolerancia_no_hay_mismatch ______________
tests\test_f019_r8_r15_precedencia.py:208: in test_f019_r10_dentro_de_tolerancia_no_hay_mismatch
    assert "albaran_unitario_manda_derivado_coincide" in resultado.reasons
E   AssertionError: assert 'albaran_unitario_manda_derivado_coincide' in ['albaran_importe_manda_declarado_coincide']
E    +  where ['albaran_importe_manda_declarado_coincide'] = PriceReconciliation(final_price=1.0, source='albaran_declared', agreement='neither', reasons=['albaran_importe_manda_declarado_coincide']).reasons
____________ test_f019_r10_justo_fuera_de_tolerancia_hay_mismatch _____________
tests\test_f019_r8_r15_precedencia.py:220: in test_f019_r10_justo_fuera_de_tolerancia_hay_mismatch
    assert resultado.final_price == pytest.approx(1.0)
E   assert 1.03 == 1.0 ± 1.0e-06
E
E     comparison failed
E     Obtained: 1.03
E     Expected: 1.0 ± 1.0e-06
=========================== short test summary info ===========================
FAILED tests/test_f019_r8_r15_precedencia.py::test_f019_r8_unitario_declarado_manda_habiendo_importe
FAILED tests/test_f019_r8_r15_precedencia.py::test_f019_r10_discrepancia_gana_el_declarado_con_mismatch
FAILED tests/test_f019_r8_r15_precedencia.py::test_f019_r10_el_mismatch_es_lo_que_lleva_la_linea_a_revision
FAILED tests/test_f019_r8_r15_precedencia.py::test_f019_r10_dentro_de_tolerancia_no_hay_mismatch
FAILED tests/test_f019_r8_r15_precedencia.py::test_f019_r10_justo_fuera_de_tolerancia_hay_mismatch
5 failed, 23 passed in 0.30s
```

El `58.65` es exactamente el unitario inventado que denunció el informe del
18-08. Los 23 tests verdes en RED son los de regresión (R11 contrato, R12
partidas alzadas, R13 ceros, R14 derivaciones imposibles, R15 descuento fuera
de rango) más R9: describen lo que NO debía cambiar, y estaban verdes ANTES y
DESPUÉS. Que R9 pase en ambos lados es el resultado esperado: sin unitario
declarado, la vieja prioridad 1 y la nueva prioridad 2 hacen lo mismo.

### RED 3 — la semántica no estaba escrita donde se consume (R3)

Comando exacto (desde la raíz del monorepo):

```
python -m pytest tests/test_f019_r1_r2_r3_semantica_precio_neto.py -q --tb=short
```

Salida antes de escribir la regla 13 de `docs/ARCHITECTURE.md`:

```
.....F                                                                   [100%]
================================== FAILURES ===================================
_______ test_f019_r3_architecture_documenta_la_semantica_de_precio_neto _______
tests\test_f019_r1_r2_r3_semantica_precio_neto.py:141: in test_f019_r3_architecture_documenta_la_semantica_de_precio_neto
    assert "`precio_neto` de una línea de albarán es el IMPORTE" in arquitectura
E   AssertionError: assert '`precio_neto` de una línea de albarán es el IMPORTE' in '<!-- docs/ARCHITECTURE.md --> # Arquitectura · albaranes (monorepo) > Este documento es NORMATIVO: el spec-author dis...ionados; los valores reales viven en `infra/*.local.ps1` (gitignored). - `.env` nunca viaja: ni a git ni a una imagen.'
=========================== short test summary info ===========================
FAILED tests/test_f019_r1_r2_r3_semantica_precio_neto.py::test_f019_r3_architecture_documenta_la_semantica_de_precio_neto
1 failed, 5 passed in 0.24s
```

Los 5 verdes son R1 (el prompt de IA1 ya definía bien el campo: el equivocado
era el consumidor) y R2 (sv5, ya corregido en T2). Es exactamente el reparto
que sostiene la decisión D1 de la spec.

---

## T9 · Puerta de rutas sensibles (R22) — evidencia y su límite

El diff toca tres rutas declaradas en `harness/rutas_sensibles.json`:

| Ruta tocada | Patrón declarado | Motivo declarado |
|---|---|---|
| `services/albaran-valoracion-persist/application/services/price_reconciler.py` | `.../application/services/**` | redes deterministas de sv6 |
| `services/albaran-valoracion-persist/domain/models/valuation_envelope.py` | `.../domain/models/**` | envelope DTO y records finales de sv6 |
| `services/albaran-valoracion-api/infrastructure/database/...` | — (no declarada) | — |

**No se ha tocado ningún prompt YAML ni ningún schema Pydantic que rellene la
IA**, tal como sostenía la spec: el cambio de sv5 es una expresión de un
SELECT y el de `valuation_envelope.py` es un bloque de comentarios (ni un
campo nuevo, ni un tipo cambiado). El saneado le llega a la IA3 por el dato,
no por el prompt.

### La pasada declarada NO se pudo ejecutar. Motivo, literal:

```
$ python -m evals.runner --con-llm --feature F-019
no se puede lanzar la pasada completa: faltan en el entorno GEMINI_API_KEY, OPENAI_API_KEY. No se ha consumido ningún caso.
$ echo $?
2
```

Las claves de LLM son secretos: no están en el entorno de esta sesión y este
repositorio prohíbe escribirlas en ningún fichero (`CLAUDE.md`, reglas duras).
El implementer NO improvisa una vía alternativa para conseguirlas.

### Lo que sí se ejecutó, y lo que demuestra

```
$ python -m evals.runner --feature F-019
NO_EVALUABLE · informe en C:\Users\pgris\PycharmProjects\albaranes\progress\evals_F-019.md
$ echo $?
2
```

El informe generado (`progress/evals_F-019.md`) dice, en sus propias líneas
parseables, `MODO: determinista` y `FASES: IA3,IA4,E2E`: **no cumple** las
tres líneas que exige `harness/rutas_sensibles.json` (`MODO: completa`,
`FASES: IA1,IA2,IA3,IA4,E2E`, `VEREDICTO: VERDE`), y no pretende hacerlo.
Lo que sí demuestra, con la salida de la propia herramienta, es el motivo de
fondo:

```
- Casos evaluados: 0 · omitidos: 0
- Motivo: no hay ningún caso en evals/fixtures/inputs/
```

Es decir: **aunque hubiera claves, la pasada completa daría `NO_EVALUABLE`
igual**, porque los libros de `evals/ground_truth/` siguen vacíos. Es
exactamente el supuesto que R22 anticipa y por el que la exigencia declarada
arranca en `aviso` (decisión D5 de F-011), no en `bloqueo`.

**Para el reviewer (C4 ter)**: la evidencia declarada falta y este es el
motivo por escrito — (1) claves LLM ausentes en el entorno local, que el
implementer no puede ni debe suplir; (2) ground truth sin casos, que hace la
pasada no evaluable por diseño. No se marca N/A: se declara ausente con causa.
Rellenar los libros de `evals/ground_truth/` sigue siendo el pendiente del
humano que permitiría subir esta puerta a `bloqueo`.
