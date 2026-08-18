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

---

## T10 · Verificaciones MANUAL (humano) — PENDIENTES

No las puede ejecutar el implementer: requieren el pipeline local levantado
(Azurite + PostgreSQL local + los dos PDFs del lote `alvaro_17082026`) y
llamadas reales a los proveedores de IA. Guion completo, con los comandos y
las consultas exactas, para que el humano solo tenga que copiar y pegar.

**Preparación** (`infra/docs/levantar-pipeline-local.md` §0 y §3): Azurite y
PostgreSQL en marcha y los servicios arrancados EN ESTE ORDEN — sv5
(`python main.py`), sv6 (`python main_worker.py`), sv3
(`python main_worker.py`), sv2 (`python main_worker.py`), sv4
(`python main.py`). Para F-019 basta con **sv5 + sv6** si los documentos ya
están extraídos y persistidos: la valoración se relanza sobre el merge, que
NO cambia con esta feature (R19).

### 1) Albarán 2.137.569 → total 139,66 € y cinco líneas correctas

Relanzar la valoración (botón «revalorar» de sv4, o a mano desde
`services/albaran-valoracion-persist`):

```powershell
python encolar_valoracion.py <document_id_2137569> CTSU24/0454 --force
```

Comprobación en PostgreSQL local:

```sql
SELECT v.total_valorado, v.total_lines
FROM albaran_valuations v
WHERE v.document_id = '<document_id_2137569>';
-- ESPERADO: total_valorado = 139.66 ; total_lines = 5
--    (antes de F-019: 6238.14)

SELECT l.merge_line_id,
       m.concepto,
       l.cantidad_albaran,
       l.precio_unitario_final,
       l.precio_unitario_source,
       l.importe_calculado,
       l.importe_albaran_declarado,
       l.importe_source
FROM albaran_line_valuations l
JOIN albaran_valuations v ON v.id = l.valuation_id
JOIN albaran_lines_merge m ON m.id = l.merge_line_id
WHERE v.document_id = '<document_id_2137569>'
ORDER BY m.line_index;
```

ESPERADO, línea a línea (`precio_unitario_source = 'albaran_declared'` en las
cinco):

| # | Concepto | Cantidad | `precio_unitario_final` | `importe_calculado` | Antes (mal) |
|---|---|---|---|---|---|
| 1 | PAPEL HIGIENICO (SACO 108) | 108 | 0,543 | 35,19 | 58,6500 / 3.800,52 |
| 2 | LTS. JABON LIQUIDO PH NEUTRO | 10 | 3,422 | 20,53 | 34,2167 / 205,30 |
| 3 | ROLLO PAPEL IND. | 12 | 7,726 | 55,63 | 92,7167 / 667,56 |
| 4 | KGS AÑIL ESPECIAL FEYMACO | 4 | 5,497 | 13,19 | 21,9833 / 52,76 |
| 5 | BOLSA BASURA 52X58 | 100 | 0,252 | 15,12 | 25,2000 / 1.512,00 |

### 2) Albarán 2.139.643 → total 19,41 € (R18)

```powershell
python encolar_valoracion.py <document_id_2139643> <codigo_contrato> --force
```

```sql
SELECT total_valorado FROM albaran_valuations
WHERE document_id = '<document_id_2139643>';
-- ESPERADO: 19.41   (antes de F-019: 970.50)
```

De este albarán solo se conoce el total: 50 ud × 0,647 con 40 % → 19,41 €.

### 3) Ninguna línea marcada por desacuerdo unitario/derivado

```sql
SELECT l.merge_line_id, l.precio_unitario_agreement, l.review_reasons_json
FROM albaran_line_valuations l
JOIN albaran_valuations v ON v.id = l.valuation_id
WHERE v.document_id IN ('<document_id_2137569>', '<document_id_2139643>')
  AND l.review_reasons_json LIKE '%unitario_declarado_vs_derivado_mismatch%';
-- ESPERADO: 0 filas.
```

Si apareciera alguna, NO es un fallo de F-019 en sí: significa que en esa
línea el unitario impreso y el importe impreso no cuadran entre sí, y la
feature está haciendo justo lo que debe (usar el declarado y mandar la línea
a revisión). Habría que mirar el PDF antes que el código.

### 4) Un albarán de hormigón sigue valorándose por contrato (R6)

Tomar cualquier documento de hormigón ya persistido (el albarán no imprime
precios: `precio` y `precio_neto` vienen NULL en sus líneas), relanzar su
valoración y comprobar:

```sql
SELECT l.merge_line_id, l.precio_unitario_final, l.precio_unitario_source,
       l.importe_calculado, l.importe_source
FROM albaran_line_valuations l
JOIN albaran_valuations v ON v.id = l.valuation_id
WHERE v.document_id = '<document_id_hormigon>';
-- ESPERADO: precio_unitario_source ∈ {contract_line_match, both_agreed,
--           pdf_inference} y importe_calculado NO nulo ni 0.
--           Es el comportamiento de HOY: esta feature no debe cambiarlo.
```

Este cuarto punto es el que cierra R19/R21: los documentos anteriores se
revaloran sin migración ni redrive, porque el contexto se relee del merge y la
valoración es un replace transaccional por `document_id`.

### R20 — histórico ya valorado: decisión del humano

Las valoraciones hechas **antes** de esta feature conservan sus importes
inflados hasta que se re-valoren. **No se ha escrito ningún script de
backfill** (decisión D4/R20 de la spec, confirmada por el humano al
aprobarla): el mecanismo para corregirlas ya existe —botón de revalorar de sv4
→ `q-valoracion`— y qué documentos se reprocesan, y cuándo, lo decide el
humano. Una consulta para dimensionarlo:

```sql
SELECT v.document_id, d.numero_albaran, v.total_valorado, v.created_at_utc
FROM albaran_valuations v
JOIN albaran_documents_merge d ON d.id = v.document_id
ORDER BY v.created_at_utc DESC;
```
