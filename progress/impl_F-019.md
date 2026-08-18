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

---

## Qué cambió, en concreto

### Código de producción (2 ficheros, 2 cambios reales)

| Fichero | Cambio |
|---|---|
| `services/albaran-valoracion-api/infrastructure/database/sqlalchemy_valuation_context_repository.py` | `_SQL_ALBARAN_LINES`: el `cantidad *` se mueve DENTRO de la segunda rama del `COALESCE`. Un solo movimiento de paréntesis. Reescrito el bloque de comentarios que afirmaba que `precio_neto` era un unitario neto. |
| `services/albaran-valoracion-persist/application/services/price_reconciler.py` | `reconcile`: los bloques 1 y 2 intercambian el orden (manda el unitario declarado; el importe solo se despeja si no hay unitario) y el desacuerdo pasa a viajar como `agreement="mismatch"`. Firma sin cambios; helpers `_no_cero`, `_derivar_bruto` y `_match` intactos. Docstring reescrito. |

`services/albaran-valoracion-persist/domain/models/valuation_envelope.py` se
toca **solo en comentarios** (aviso de que `precio_neto_albaran` es un
importe, no un unitario): ni un campo nuevo, ni un tipo cambiado, ni un
default distinto — R21 se cumple por construcción.

### Tests (4 ficheros nuevos, 52 tests)

| Fichero | Tests | Cubre |
|---|---|---|
| `services/albaran-valoracion-api/tests/test_f019_r4_r7_importe_select.py` | 9 | R4, R5, R6, R7 y el tramo sv5 de R16 |
| `services/albaran-valoracion-persist/tests/test_f019_r8_r15_precedencia.py` | 28 | R8-R15 |
| `services/albaran-valoracion-persist/tests/test_f019_r16_r17_feymaco.py` | 9 | R16, R17 |
| `tests/test_f019_r1_r2_r3_semantica_precio_neto.py` | 6 | R1, R2, R3 |

Más los dos `conftest.py` que anclan `sys.path` de sv5 y sv6 (patrón copiado
de `services/albaranes-api/tests/conftest.py`).

### Documentación

`docs/ARCHITECTURE.md` (regla 13, nueva), `services/albaran-valoracion-api/sv5.md`
(§9), `services/albaran-valoracion-persist/sv6.md` (§5.3, §6.1 reescrita, §6.4
corregida) y el comentario del DTO del envelope.

## Decisiones de diseño tomadas al implementar

1. **El `derivado_bruto` se sigue calculando ANTES de decidir la prioridad**,
   aunque el bloque 1 (unitario declarado) gane. Es lo que conserva intactos
   los motivos de auditoría de R13/R14 (`importe_albaran_cero_ignorado`,
   `importe_leido_sin_cantidad_no_derivable`, `descuento_100_no_derivable`)
   en el caso —frecuente— de que además haya unitario declarado. Si se hubiera
   calculado solo dentro del bloque 2, la auditoría habría enmudecido justo en
   las líneas mejor leídas.
2. **Un `return` propio para la rama de mismatch**, en vez de compartir el
   final con un flag de `agreement`: así el `final_price=declarado` queda
   escrito explícitamente en los dos caminos. Es dinero: antes la repetición
   que la elegancia.
3. **Los tests de sv5 ejecutan el SQL real, importado del módulo de
   producción**, contra SQLite en memoria. Un test que copiara el SQL a mano
   habría pasado igual con el bug dentro. Confirmada la viabilidad que la spec
   anticipaba: `_SQL_ALBARAN_LINES` corre sin un solo cambio.
4. **La fixture de las cinco líneas de Feymaco está duplicada** en las suites
   de sv5 y sv6, con un comentario cruzado en ambas. No es descuido: sv5 y sv6
   tienen paquetes `application`/`domain`/`infrastructure` homónimos de primer
   nivel y no pueden convivir en una misma sesión de pytest.

## Desviaciones respecto a la spec

1. **La regla 13 de `docs/ARCHITECTURE.md` (parte de R3, asignada a T7) se
   escribió en T5.** Motivo: el test (c) de T5 vigila justamente esa regla y
   la verificación de T5 exige la suite en verde. Se dejó primero el test en
   RED (traza arriba) y después la regla. El resto de R3 —`sv5.md`, `sv6.md`,
   DTO del envelope— sí se hizo en T7.
2. **T9 no pudo producir la evidencia declarada** (faltan claves LLM en el
   entorno local). Motivo completo, con las salidas literales, en la sección
   «T9 · Puerta de rutas sensibles» de este informe. No se improvisó ninguna
   vía alternativa para obtener las claves.
3. **`sv6.md` §6.4 y §5.3 se corrigieron más allá de lo estrictamente pedido**
   (la spec pedía §6.1 y §6.4). §6.4 estaba desactualizada desde jul 2026 en
   el punto del importe declarado —lo dice la propia spec— y §5.3 describía
   `agreement == 'mismatch'` como si solo pudiera venir del contraste 1a/1b,
   que es exactamente lo que esta feature cambia (D3). Dejarlo sin tocar
   habría creado documentación falsa en el servicio que estamos tocando.
4. **T10 queda `[ ]` en `tasks.md`**, siguiendo la convención de F-002: es una
   verificación MANUAL del humano y marcarla hecha sería falso. Su guion
   completo está en este informe.

## Lo que quedó FUERA del alcance (a propósito)

- **sv2 no se toca** (decisión D1, confirmada por el humano). El prompt de IA1
  define bien `precio_neto`; el equivocado era el consumidor. El campo con
  nombre no ambiguo (`importe_linea`) es F-003 R1/R2.
- **Ningún script de backfill** (D4/R20): el histórico se sanea revalorando
  desde sv4. Consulta para dimensionarlo, en el guion de T10.
- **`ImporteCalculator` sin tocar**: el importe declarado sigue mandando sobre
  el calculado. Endurecer ese contraste es el guard aritmético de F-003 R6.
- **`ValuationBuilder` sin tocar** (D3): el mismatch llega a revisión por
  `agreement`, que el builder ya mira.
- **Descuento expresado en euros en vez de en porcentaje**: riesgo residual
  conocido, anotado en la spec, y que corresponde a F-003 R2/R3.

## Lo que falta para cerrar

1. Las cuatro verificaciones **MANUAL (humano)** de T10.
2. El veredicto del **reviewer** contra `CHECKPOINTS.md` (con C4 ter leído
   sobre la sección T9 de este informe).
3. Pendiente heredado, no de esta feature: rellenar `evals/ground_truth/` para
   que la puerta de rutas sensibles pueda subir de `aviso` a `bloqueo`.
4. Pendiente para el humano al arrancar **F-003**: su R4 manda conservar «la
   derivación actual `cantidad × precio_neto`», que es exactamente el bug que
   F-019 corrige, y su R6 es la evolución del R10 de aquí, no un duplicado.

---

## Evidencias

Números medidos, no estimados. Todos reproducibles con los comandos que se
citan.

| Evidencia | Valor | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados y resultado** | **248 passed** (suite raíz) + **11 passed** (sv5) + **40 passed** (sv6); **0 fallos**. De ellos, **57 son nuevos de F-019** (6 en la raíz, 11 en sv5, 40 en sv6), incluidos los **5 de R18** del round trip. sv2, sv3 y `comun` en verde por caché de árbol sin cambios. | `bash harness/init.sh` (secciones 7 y 7 bis) |
| **Cobertura de las líneas cambiadas** | **100,0 % (5/5 líneas, umbral 80 %, nivel `critico`)** | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | **4 generados, 4 muertos, 0 supervivientes, 0 timeouts** sobre 144 líneas de producción en alcance (3 ficheros) | `python -m harness.mutacion --feature F-019` → `progress/mutacion_F-019.md` |
| **Tiempo de ejecución de la suite** | tras el round trip: raíz **94,58 s**; sv5 **1,11 s**; sv6 **0,18 s**. (Antes del round trip: 65,30 / 0,79 / 0,12 s — la diferencia de la raíz es ruido de máquina, no de los 5 tests nuevos, que viven en sv5 y sv6 y cuestan centésimas.) | salida de cada pytest en `bash harness/init.sh` |

Sobre los 4 mutantes: es un número bajo *porque el diff lo es*. De las 144
líneas en alcance, el grueso son comentarios y docstrings (la corrección
documental de R1/R3 es media feature), el SQL vive dentro de un `text()`
multilínea que el mutador no puede tocar —previsto en `tasks.md` T8— y el
código mutable real es `price_reconciler.py`. Los 4 mutantes caen todos ahí,
en la condición y en las listas de motivos que decide esta feature, y los
cuatro mueren. Nivel `critico`: **cero supervivientes, sin justificación
pendiente**.

### Estado de las puertas de `bash harness/init.sh`

```
[OK] PUERTA COBERTURA: 100.0% de 5 líneas cambiadas cubiertas (5/5, umbral 80%, nivel critico)
[AVISO] PUERTA RUTAS SENSIBLES [evals]: aviso: falta la evidencia de 2 ruta(s) sensible(s) tocada(s):
      - services/albaran-valoracion-persist/application/services/price_reconciler.py (redes deterministas de sv6)
      - services/albaran-valoracion-persist/domain/models/valuation_envelope.py (envelope DTO y records finales de sv6)
      Sin cumplir: MODO: completa, FASES: IA1,IA2,IA3,IA4,E2E, VEREDICTO: VERDE
      Lanzalo con: python -m evals.runner --con-llm --feature F-019
[OK] Rama actual: feature/F-019-importe-unitario-manda
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

---

## Round trip de review — R18 con test automático

`progress/review_F-019.md`: **CHANGES_REQUESTED por un solo punto**. El fondo
técnico (corrección de sv5, precedencia de sv6, protección contra partidas
alzadas, mutación y puerta de rutas sensibles) quedó verificado contra el diff
real. Lo que faltaba:

> **R18 no tenía ningún test automático.** `grep` sobre todos los `.py` del
> repositorio: cero apariciones de `19.41`, `970.50`, `2139643` o `0.647`. El
> segundo albarán del incidente —el que abre el diagnóstico del 18-08— no
> tenía red de seguridad de ninguna clase.

Tenía razón, y el reviewer además señaló la incoherencia que lo delataba: el
guion MANUAL de §T10 afirmaba «50 ud × 0,647 con 40 % → 19,41 €» mientras la
spec decía que de ese albarán «solo se conoce el total». Las dos cosas a la
vez, no.

### Qué se añadió

| Suite | Test | Comprueba |
|---|---|---|
| sv5 | `test_f019_r18_el_albaran_2139643_vale_1941_euros` | `_SQL_ALBARAN_LINES` sobre la fila real ⇒ `importe_albaran == 19.41`, `!= 970.50`, con su concepto y su unitario |
| sv5 | `test_f019_r18_la_derivacion_del_2139643_coincide_con_su_neto` | sin `precio_neto`, la fórmula canónica da el mismo 19,41 (50 × 0,647 × 0,6 exacto) |
| sv6 | `test_f019_r18_el_albaran_2139643_conserva_su_unitario_leido` | `final_price == 0.647`, `source == "albaran_declared"`, `agreement != "mismatch"`, y el precio de contrato ruidoso no entra |
| sv6 | `test_f019_r18_el_albaran_2139643_vale_1941_euros` | encadenando `ImporteCalculator` ⇒ `importe_calculado == 19.41`, `!= 970.50` |
| sv6 | `test_f019_r18_el_importe_del_2139643_tambien_sale_del_calculo` | el importe se **calcula** (sin declarado que se lo regale) y sale 19,41 con `importe_source == "calculated"` |

El último cubre de paso la observación no bloqueante nº 1 del reviewer: en el
test equivalente de R16, el `ImporteCalculator` recibe el importe declarado y
lo prefiere, así que esa mitad del aserto es en parte tautológica. Aquí no.

### Corrección al informe del reviewer: los números NO son una reconstrucción

El reviewer pedía documentar la fixture como «reconstrucción aritmética a
partir del total conocido (`970,50 / 19,41 = 50`)». **No hace falta deducir
nada**: la composición de esa línea es un dato **leído y verificado por el
líder de dos fuentes independientes que coinciden campo a campo**:

- el PDF `Feymaco_2139643.pdf` del lote `alvaro_17082026` — línea única,
  código `1 11 00353`, concepto `DISCO ESPECIAL ACERO INOX. 115X1X22`,
  cantidad `50,00`, precio `0,647`, dto `40,0`, neto `19,41`;
- el ground truth del administrativo `alvaro_17082026.xlsx` — misma fila, con
  partida `CI.4.18` y el descuento expresado en fracción (`0,4`).

Los docstrings de los tests nuevos lo dicen así, con las dos fuentes citadas,
y la nota de R18 en `requirements.md` se reescribió en el mismo sentido: la
composición es transcripción, no deducción. Es una diferencia que importa —un
dato deducido del propio bug no puede después usarse para juzgar el bug— y por
eso no se copió la redacción propuesta.

### Spec ajustada

- `requirements.md` R18: incorpora la composición de la línea con sus dos
  fuentes y deja de declararse «solo verificación MANUAL».
- `tasks.md`: la tabla de trazabilidad pasa R18 de `T10 (MANUAL)` a
  **`T1 (tramo sv5) + T6 (tramo sv6) + T10 (MANUAL)`**, y T1 y T6 recogen en
  su enunciado la fila del 2.139.643.

**T10 se mantiene intacta**: la verificación MANUAL del humano sobre el
pipeline local sigue pendiente y sigue siendo necesaria. El test la acompaña,
no la sustituye — comprueba las dos piezas deterministas de la cadena, no el
extremo a extremo con IA real.

### Verificación del round trip

```
python -m pytest tests -q -k "f019_r18"   (desde services/albaran-valoracion-api)
  2 passed, 9 deselected
python -m pytest tests -q -k "f019_r18"   (desde services/albaran-valoracion-persist)
  3 passed, 37 deselected

bash harness/init.sh
  sv5: 11 passed · sv6: 40 passed · raíz: 248 passed
  [OK] PUERTA COBERTURA: 100.0% de 5 líneas cambiadas cubiertas (5/5, umbral 80%, nivel critico)
  ENTORNO LISTO. Puedes trabajar.
```

No se tocó nada más de la feature: el resto lo dio por bueno el reviewer. En
particular, **no se tocó ningún fichero de producción** en este round trip —
solo tests, spec y documentación—, así que la campaña de mutación de T8 sigue
siendo válida sobre el mismo código (4 mutantes, 0 supervivientes) y la puerta
de rutas sensibles no cambia de estado.

### Observaciones no bloqueantes del reviewer, no aplicadas

Las tres son correctas y ninguna es de esta feature; se dejan anotadas para
que el humano decida, en vez de colarlas en un round trip acotado:

1. La mitad tautológica de `test_f019_r16_cada_linea_conserva_su_unitario_y_su_importe`
   — mitigada de hecho por el tercer test de R18, que sí calcula el importe.
2. La descripción de `price_tolerance_pct` en `config/settings.py:48` («para
   considerar que precio 1a y 1b coinciden») se quedó corta: esa tolerancia
   gobierna además el contraste declarado-vs-derivado. Ya era así antes de
   F-019, así que no es regresión de esta feature.
3. `TOLERANCIA_PRECIO_PCT` / `TOLERANCIA_IMPORTE_PCT` del `conftest.py` de sv6
   están fijados a mano (2.0 y 5.0, comprobados contra los defaults reales) y
   nada avisaría si alguien cambiara el default. Un test de tres líneas lo
   cerraría.

También queda para el humano su **propuesta de mejora del protocolo**:
extender la prueba de control de C4 bis de «si la campaña declara cero
mutantes» a «cero mutantes **en cualquier fichero del alcance**». Si se
acepta, es genérica y debe portarse a `arnes-base`.

---

# Round trip 2 (2026-08-18) — el importe PERSISTIDO

La prueba local del humano midió en la BBDD, **con esta rama ya en
ejecución**, `albaran_valuations.total_valorado = 232,76 €` en el albarán
Feymaco 2.137.569, que vale **139,66 €**. El criterio de aceptación de la
feature no se cumplía. F-019 se reabrió (`in_progress`, con el motivo escrito
en `harness/features.json`) y la spec se amplió con G6 (R23–R26).

## La causa real, y por qué las otras no lo eran

**Causa: `services/albaranes-front/infrastructure/database/review_repository.py`
`::_recalc_valuation_importes`.** sv4 recalcula el importe de TODAS las líneas
de un documento cada vez que el revisor guarda —aunque no haya tocado ninguna
cantidad— con la fórmula `cantidad × precio_unitario_final`, **sin el factor
del descuento**, y fuerza `importe_source = 'calculated'`. Después reescribe
`total_valorado` con un `SUM()` de esa columna. sv5 y sv6 hacían lo correcto;
otro servicio lo pisaba seis minutos más tarde.

### La prueba que lo cierra

La pinza definitiva es la marca de tiempo, no el razonamiento:

| Albarán | `created_at_utc` | `updated_at_utc` | Total | Estado |
|---|---|---|---|---|
| 2.137.569 | 13:24:26 | **13:30:31** | 232,76 € | pisado |
| 2.139.643 | 13:24:48 | 13:24:48 | 19,41 € | intacto |

Los dos se valoraron con el mismo código y con 22 s de diferencia. El único
que salió mal es el único cuya fila fue **modificada después de crearse**: el
que el revisor abrió y guardó en el front. El otro conserva `declared_albaran`
y su total correcto. Consultado en la BBDD local, solo lecturas.

Y explica la contradicción que abría el encargo —`importe_albaran_declarado =
35,19` no nulo con `importe_source = 'calculated'`, imposible en
`ImporteCalculator.compute`— porque **`compute` nunca produjo esa fila**. El
`UPDATE` de sv4 reescribe importe y fuente pero **no toca**
`descuento_albaran_aplicado`, `importe_albaran_declarado` ni
`review_reasons_json`: los tres siguen siendo los que dejó sv6. De ahí el dato
internamente contradictorio —un descuento del 40 % registrado y no aplicado,
con el motivo `descuento_aplicado:40.0%` en los reasons— que era justamente la
firma del culpable.

### Las cuatro hipótesis del encargo, descartadas una a una

1. **`albaran_line.importe_albaran` llega `None` a `compute`.** NO. Las líneas
   1067 y 1165 de `valuation_builder.py` leen la MISMA expresión
   (`albaran_line.importe_albaran if albaran_line else None`): si una fuera
   `None`, la columna `importe_albaran_declarado` habría quedado nula, y vale
   35,19. Descartada por construcción, sin necesidad de ejecutar nada.
2. **El `descuento_pct` que llega a `compute` es `None` y el motivo
   `descuento_aplicado:40.0%` viene del reconciliador.** NO. `price_reconciler.py`
   no emite ese motivo en ninguna de sus ramas — sus cadenas son
   `albaran_unitario_manda_derivado_coincide`,
   `unitario_declarado_vs_derivado_mismatch`, `albaran_importe_manda_derivado`,
   `descuento_100_no_derivable` e `importe_leido_sin_cantidad_no_derivable`.
   El único emisor de `descuento_aplicado:N%` es `ImporteCalculator` (línea 121).
3. **Un recálculo posterior pisa `importe_result`.** **SÍ — esta era.** Pero no
   en el builder ni en el repositorio de sv6:
   `sqlalchemy_valuation_repository.py` solo copia `line.importe_calculado` al
   ORM (líneas 350 y 430), sin tocarlo. El recálculo estaba en **otro
   servicio**, sv4, que no figuraba en el alcance de la feature. Es lo que hizo
   falta ampliar.
4. **La línea entra por otra ruta del builder.** NO. `LineValuationRecord(` se
   construye en exactamente dos sitios de sv6 (`valuation_builder.py:1139` y
   `:1491`); el segundo es el de líneas sintéticas y fija
   `importe_albaran_declarado=None`, que no es el caso. Y el test de T13, que
   hace pasar el documento entero por `ValuationBuilder.build` con
   `match_method='no_match'`, sale en verde: la ruta con `ia_no_match` produce
   los 35,19 correctos.

### El apunte del front, comprobado

Cierto que `document_detail.html:619` recalcula al vuelo y por eso el portal se
veía bien. Pero no era una pista falsa del todo: **el front no solo pintaba
bien un dato malo, es que además era quien lo había escrito**. La plantilla y
el repositorio discrepaban porque solo uno de los dos aplicaba el descuento.

## Qué cambió

### Código de producción (1 fichero)

`services/albaranes-front/infrastructure/database/review_repository.py`:

| Cambio | Qué |
|---|---|
| `_importe_de_linea` (nuevo) | Fórmula canónica ÚNICA del servicio: `cantidad × unitario × (1 − dto/100)`, con `_sanear_descuento` alineado con `ImporteCalculator._sanitize_descuento` de sv6. |
| Los **4** puntos que escribían un importe | Pasan a pedírselo. Tres de los cuatro se dejaban el descuento: `_recalc_valuation_importes` (el culpable), `set_line_conciliacion` y la conciliación desde la línea del merge. El cuarto (`update_line_valuation`) ya lo aplicaba y ahora comparte la fórmula. |
| `_recalc_valuation_importes` | Recibe además el descuento nuevo del payload (`new_line_discounts`); persiste el descuento que aplica; **no toca la fila si cantidad y descuento no han cambiado** (R24); redondea el `SUM()` de la cabecera a 2 decimales (R26). |
| `_num_iguales` (nuevo) | Decide si una fila cambia de verdad, con media unidad de céntimo de margen. |
| Dos `SELECT` y un `INSERT` | Traen y persisten el descuento que antes no viajaba. |

**sv5 y sv6 no se han tocado en este round trip.** Su corrección era correcta y
así lo demuestra el test de T13, que pasó a la primera.

### Tests (3 ficheros nuevos)

| Fichero | Tests | Cubre |
|---|---|---|
| `services/albaranes-front/tests/test_f019_r23_r26_recalculo_importe.py` | 15 | R23, R24, R25, R26 contra SQLite en memoria |
| `services/albaranes-front/tests/test_f019_r23_formula_canonica.py` | 29 | R23: la fórmula, el saneado del descuento, `_num_iguales` y el **guardián estructural** |
| `services/albaran-valoracion-persist/tests/test_f019_r25_r26_total_documento.py` | 4 | R25, R26: el TOTAL por `ValuationBuilder.build` completo |

Más `services/albaranes-front/tests/conftest.py`: **sv4 no tenía directorio de
tests**. `bash harness/init.sh` lo avisaba en cada pasada («NADIE está
comprobando los tests de sv4-front») y el aviso tenía razón — el fallo vivía
justo ahí. Ahora corre en la sección 7 bis como los demás.

### Documentación

`docs/ARCHITECTURE.md` regla 13: la fórmula canónica obliga a **todo el que
escriba un importe**, no solo al valorador, y un servicio no reetiqueta como
`calculated` un importe que el albarán declara si nadie ha tocado la línea.

## Fase RED — trazas reales

### RED 4 — sv6 NO era el culpable (T13, R25)

Comando exacto (desde `services/albaran-valoracion-persist`):

```
python -m pytest tests/test_f019_r25_r26_total_documento.py -q --tb=short
```

```
....                                                                     [100%]
4 passed in 0.49s
```

**Cuatro verdes a la primera, y ese es el hallazgo.** El test hace pasar el
documento entero de cinco líneas por `ValuationBuilder.build` —guard,
reconciliador, matcher, conversor, calculador de importe y cabecera— con el
contexto medido en la BBDD (`unidad_medida` NULL, `match_method='no_match'`) y
la cabecera sale con `total_valorado == 139.66`, igualdad exacta. sv6 ya
escribía lo correcto y ya redondeaba su total. Sin este test, la única forma de
saberlo era el razonamiento; con él, es una medida.

### RED 5 — el pisado de sv4, reproducido (T14, R23-R26)

Comando exacto (desde `services/albaranes-front`):

```
python -m pytest tests -q --tb=line
```

```
FFFFFFF..FFFF                                                            [100%]
================================== FAILURES ===================================
E   assert 232.76 != 232.76 ± 2.3e-04
     +  where 232.76 = _leer_total(<sqlalchemy.orm.session.Session object at 0x000002AB95C26390>)
tests\test_f019_r23_r26_recalculo_importe.py:126: assert 232.76 != 232.76 ± 2.3e-04
E   AssertionError: PAPEL HIGIENICO (SACO 108)
    assert 58.64 != 58.64 ± 5.9e-05
tests\test_f019_r23_r26_recalculo_importe.py:147: AssertionError: PAPEL HIGIENICO (SACO 108)
E   AssertionError: LTS. JABON LIQUIDO PH NEUTRO
    assert 34.22 != 34.22 ± 3.4e-05
tests\test_f019_r23_r26_recalculo_importe.py:147: AssertionError: LTS. JABON LIQUIDO PH NEUTRO
E   AssertionError: ROLLO PAPEL IND.
    assert 92.71 != 92.71 ± 9.3e-05
tests\test_f019_r23_r26_recalculo_importe.py:147: AssertionError: ROLLO PAPEL IND.
E   AssertionError: KGS ANIL ESPECIAL FEYMACO
    assert 21.99 != 21.99 ± 2.2e-05
tests\test_f019_r23_r26_recalculo_importe.py:147: AssertionError: KGS ANIL ESPECIAL FEYMACO
E   AssertionError: BOLSA BASURA 52X58
    assert 25.2 != 25.2 ± 2.5e-05
E   assert 54.3 == 32.58 ± 3.3e-05
E   AssertionError: assert 'calculated' == 'declared_albaran'
E   assert 232.76 == 139.66 ± 1.4e-04
E   assert 3392.7200000000003 == 3392.72
=========================== short test summary info ===========================
11 failed, 2 passed in 0.73s
```

Los `!=` que fallan son deliberados: el test afirma «esto NO puede volver a
salir» con el número exacto medido en la BBDD, y en RED sale **clavado** —
232,76 de total y 58,64 / 34,22 / 92,71 / 21,99 / 25,20 por línea, con
`importe_source` degradado a `calculated`. No es una reconstrucción del fallo:
es el fallo.

### RED 6 — el guardián estructural, contrastado contra el código anterior

El test `test_f019_r23_nadie_multiplica_precio_por_cantidad_fuera_de_la_formula`
sería un adorno si nadie comprobara que reconoce el patrón. Aplicado al fichero
tal como estaba en `HEAD` antes del fix:

```
1443 return round(float(precio) * float(cantidad), 2)
1702 base = float(new_precio) * float(new_cantidad)
2013 round(float(precio) * float(cantidad), 2)
3230 nuevo_importe = round(float(pu) * float(cantidad_efectiva), 2)
```

Las cuatro copias, incluida la culpable (3230). Además el fichero lleva una
prueba de control (`test_f019_r23_el_guardian_detecta_de_verdad_el_patron`) que
fija esas líneas literales como entradas que el patrón DEBE reconocer.

## Decisiones de diseño

1. **La corrección va a sv4, no a sv6.** Podría haberse «arreglado» haciendo
   que sv6 escribiera un importe que sobreviviera al pisado, pero eso es tapar:
   el que estaba mal era el que recalculaba. Alcance ampliado de sv5+sv6 a
   sv5+sv6+sv4, declarado en G6 de `requirements.md` (regla LÍMITE DE SERVICIO
   de `CLAUDE.md`). No es responsabilidad nueva: es la misma fórmula del
   dominio, aplicada en el otro punto que la escribe.
2. **Se arreglan las cuatro copias, no solo la culpable.** Dejar tres formas
   defectuosas de calcular lo mismo, en el mismo fichero, junto a la que se
   acaba de arreglar, es cómo se repite un incidente con otro botón del front.
3. **Guardián estructural además de tests de comportamiento.** El defecto no
   era un valor mal calculado: era una fórmula duplicada. La red que faltaba
   tiene que vigilar la duplicación, no solo el resultado.
4. **R24 (no tocar lo que nadie ha tocado) en vez de solo aplicar el
   descuento.** Aplicar el descuento bastaba para que el total diera 139,66.
   Pero un guardado que solo movía una partida seguía degradando las cinco
   líneas de `declared_albaran` a `calculated`, es decir, afirmando en la BBDD
   que ese importe lo habíamos calculado nosotros cuando lo declara el albarán.
   Es la misma regla de jul 2026 que ya sostiene `ImporteCalculator`.
5. **`_num_iguales` con margen de medio céntimo**, no igualdad exacta: sobre
   `DOUBLE PRECISION`, `==` haría que casi toda fila pareciera cambiada y el
   guardado volvería a reescribirlo todo.
6. **El `ROUND` del `SUM()` va con `CAST(... AS numeric)`**, que funciona igual
   en PostgreSQL (producción) y en SQLite (los tests).

## Lo que quedó FUERA (a propósito)

- **`_apply_valuation_line_updates_in_session` no tiene test de integración**:
  usa `lv.id = ANY(:ids)`, sintaxis exclusiva de PostgreSQL, que SQLite no
  ejecuta (el propio método lo captura y sale silenciosamente, así que un test
  pasaría en vacío y mentiría). Su fórmula sí queda cubierta: ahora llama a
  `_importe_de_linea`, que tiene 29 tests, y el guardián estructural impide que
  vuelva a escribirla a mano. **Portar ese `ANY` a un `bindparam` expanding
  haría el método testable**; es un cambio con riesgo propio sobre la ruta de
  producción y no se cuela en un round trip acotado.
- **No se ha reparado la fila ya corrupta de la BBDD local** (2.137.569,
  232,76 €). Sigue la regla R20: el histórico se sanea revalorando desde sv4, y
  qué se reprocesa lo decide el humano. Contra la BBDD solo se han hecho
  lecturas.
- **`total_valorado` de sv6 no se ha tocado**: ya redondeaba.

## Verificaciones MANUAL (humano) — T17, PENDIENTE

Requieren el pipeline local levantado. Las de T10 siguen vigentes; estas dos
son nuevas y son las que habrían cazado esto:

### 1) Revalorar y comprobar el total

```sql
SELECT d.numero_albaran, v.total_valorado, v.created_at_utc, v.updated_at_utc
FROM albaran_valuations v
JOIN albaran_documents_merge d ON d.id = v.document_id
WHERE d.numero_albaran IN ('2.137.569', '2.139.643');
-- ESPERADO: 139.66 y 19.41.
```

### 2) Guardar desde el front y volver a mirar (la nueva)

Abrir el 2.137.569 en sv4, cambiar algo que NO sea una cantidad (una partida,
una descripción), guardar, y repetir la consulta anterior:

- `total_valorado` sigue siendo **139,66** (antes pasaba a 232,76);
- `updated_at_utc` cambia (el guardado ocurrió), pero
- las cinco líneas conservan `importe_source = 'declared_albaran'` y sus
  importes 35,19 / 20,53 / 55,63 / 13,19 / 15,12.

```sql
SELECT l.merge_line_id, l.importe_calculado, l.importe_source,
       l.descuento_albaran_aplicado
FROM albaran_line_valuations l
JOIN albaran_valuations v ON v.id = l.valuation_id
JOIN albaran_documents_merge d ON d.id = v.document_id
WHERE d.numero_albaran = '2.137.569'
ORDER BY l.merge_line_id;
```

Después, cambiar **sí** una cantidad y comprobar que esa línea —y solo esa—
pasa a `calculated` con el importe recalculado **con su descuento**.

---

## Evidencias (round trip 2)

Números medidos, no estimados.

| Evidencia | Valor | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados y resultado** | **248** (raíz) + **11** (sv5) + **44** (sv6) + **44** (sv4) = **347 passed, 0 fallos**. De ellos **48 nuevos** en este round trip: 44 de la suite nueva de sv4 y 4 de la de sv6. sv6 pasa de 40 a 44; sv4 de **0 a 44** (no tenía suite). | `bash harness/init.sh` (secciones 7 y 7 bis) |
| **Cobertura de las líneas cambiadas** | **89,1 % (49/55 líneas, umbral 80 %, nivel `critico`)** | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | **24 generados, 22 muertos, 2 supervivientes, 0 timeouts** sobre 328 líneas de producción en alcance. Los 2 supervivientes son **equivalentes**, demostrado ejecutando original y mutante sobre la tabla completa de entradas relevantes (8 casos cada uno, salida idéntica). Análisis completo en `progress/mutacion_F-019.md`. | `python -m harness.mutacion --feature F-019 --workers 1` |
| **Tiempo de ejecución de la suite** | raíz **46,42 s**; sv5 **0,46 s**; sv6 **0,51 s**; sv4 **0,59 s** | salida de cada pytest |

Sobre la mutación: la campaña anterior generó 4 mutantes (diff mínimo, casi
todo comentarios); esta genera **24** porque el fix de sv4 aporta lógica real.
En la primera pasada sobrevivieron 4; **dos eran huecos de verdad y se cerraron
con test** —el aviso de descuento fuera de rango, cuyo mutante callaba ante un
descuento absurdo y avisaba en cada línea sin descuento; y la frontera de medio
céntimo de `_num_iguales`—, no con una justificación.

La campaña se lanzó con `--workers 1`: la paralela crea worktrees desde `HEAD`
y se negó a correr por un fichero sin versionar de **otra sesión**
(`progress/revision_hormigones_20260818.md`), que no es de esta feature y no se
ha tocado.

### Estado de las puertas de `bash harness/init.sh`

```
[OK] PUERTA COBERTURA: 89.1% de 55 líneas cambiadas cubiertas (49/55, umbral 80%, nivel critico)
[AVISO] PUERTA RUTAS SENSIBLES [evals]: aviso: falta la evidencia de 2 ruta(s) sensible(s) tocada(s):
      - services/albaran-valoracion-persist/application/services/price_reconciler.py
      - services/albaran-valoracion-persist/domain/models/valuation_envelope.py
[OK] Rama actual: feature/F-019-importe-unitario-manda
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

El aviso de rutas sensibles es **el mismo de antes y por el mismo motivo**
(claves LLM ausentes del entorno local y `evals/ground_truth/` vacío, sección
T9 de este informe). Este round trip **no ha tocado ninguna ruta sensible**:
los dos ficheros que la puerta señala son los de sv5/sv6 del trabajo original,
sin cambios desde entonces.

## Lo que falta para cerrar

1. Las verificaciones **MANUAL (humano)** de T10 y las dos nuevas de **T17**,
   en particular «guardar desde el front y volver a mirar el total».
2. El veredicto del **reviewer** contra `CHECKPOINTS.md`.
3. Decisión del humano sobre **revalorar el 2.137.569** en la BBDD local para
   sanear la fila que quedó en 232,76 € (R20: no se ha escrito backfill).
4. Pendiente heredado: rellenar `evals/ground_truth/`.
5. Anotado, no hecho: hacer testable `_apply_valuation_line_updates_in_session`
   sustituyendo `ANY(:ids)` por un `bindparam` expanding.

---

# Round trip 3 (2026-08-18) — CHANGES_REQUESTED del reviewer

Sobre `3add86e`. `progress/review_F-019.md` §«Tercera pasada». Tres cambios,
**los tres aplicados** por decisión del humano (incluido el 2, que el reviewer
dejaba a su elección). El reviewer dio por bueno el fondo del round trip 2 —el
fix del descuento, los 139,66 € fijados sobre el valor persistido, la campaña
de mutación verificada de forma independiente y sv4 pasando de 0 a 44 tests—;
lo que faltaba estaba en los bordes.

## Cambio 1 · R24 se decidía por el resultado, no por las entradas

**Tenía razón, y era el bloqueante de verdad.** `sin_cambios` incluía
`_num_iguales(importe_anterior, nuevo_importe)`: la fila se actualizaba siempre
que el importe guardado difiriera del recalculado, **aunque el revisor no
hubiera tocado nada**.

Lo que lo convierte en un defecto y no en una redundancia es que **sv6 genera
esas filas a propósito**: `ImporteCalculator.compute` devuelve el importe
DECLARADO cuando declarado y calculado discrepan, dejando el motivo
`declared_vs_calculated_mismatch` (regla de jul 2026, y la propia regla 13: si
ambos existen y discrepan, gana el declarado y la línea va a revisión). Es
decir: el criterio del resultado pisaba exactamente las líneas que sv6 había
decidido proteger.

El Feymaco 2.137.569 se salvaba **por casualidad**, porque sus cinco líneas
cuadran al céntimo. Basta con que el importe impreso difiera medio céntimo del
producto —redondeos por línea del proveedor, descuentos en cascada— para caer
en el camino malo.

### RED 7 — la sonda del reviewer, reproducida

```
python -m pytest tests -q --tb=line     (desde services/albaranes-front)
```

```
............................................F..FFF                       [100%]
================================== FAILURES ===================================
E   AssertionError: R24: el importe declarado fue pisado
    assert 60.0 == 100.0 ± 1.0e-04
      Obtained: 60.0
      Expected: 100.0 ± 1.0e-04
tests\test_f019_r23_r26_recalculo_importe.py:410: AssertionError: R24: el importe declarado fue pisado
E   assert 60.0 == 100.0 ± 1.0e-04
tests\test_f019_r23_r26_recalculo_importe.py:474: assert 60.0 == 100.0 ± 1.0e-04
E   assert 25.0 == 30.0 ± 3.0e-05
      Obtained: 25.0
      Expected: 30.0 ± 3.0e-05
=========================== short test summary info ===========================
FAILED tests/test_f019_r23_r26_recalculo_importe.py::test_f019_r24_el_declarado_discrepante_no_se_pisa
FAILED tests/test_f019_r23_r26_recalculo_importe.py::test_f019_r24_reenviar_el_mismo_descuento_no_es_un_cambio
FAILED tests/test_f019_r23_r26_recalculo_importe.py::test_f019_r24_cero_y_nulo_son_el_mismo_descuento[0.0]
FAILED tests/test_f019_r23_r26_recalculo_importe.py::test_f019_r24_cero_y_nulo_son_el_mismo_descuento[None]
4 failed, 46 passed in 1.20s
```

El `60.0` frente a `100.0` es exactamente el número de la sonda del informe del
reviewer, con las mismas entradas (cantidad 100, unitario 1,00, dto 40 %).

### El arreglo

`sin_cambios` pasa a comparar **solo entradas**: `cantidad_albaran`,
`cantidad_convertida` y el **descuento ya saneado**. Dos detalles que no son
adorno:

- **El descuento se compara saneado** porque el front reenvía el descuento en
  *cada* guardado (`static/app.js`: `descuento: pick("descuento")`) y `0` y
  `NULL` significan lo mismo. Sin sanear, todo guardado vería un cambio
  inexistente y el guardián no protegería nada. Cubierto por
  `test_f019_r24_reenviar_el_mismo_descuento_no_es_un_cambio` y por
  `..._cero_y_nulo_son_el_mismo_descuento`.
- **Se cae el conjunto `importe_anterior is not None`**, que ya no hace falta:
  una fila sin importe previo tampoco tiene entradas distintas, y si las tiene
  se actualiza igual.

6 tests nuevos, incluidos los tres simétricos que fijan que la línea **sí**
cede cuando el revisor cambia la cantidad o el descuento (no vale proteger de
más).

## Cambio 2 · La fórmula duplicada ENTRE servicios → `ruesma_comun`

El round trip 2 unificó las cuatro copias **dentro** de sv4 y dejó en pie la
duplicación **entre** sv4 y sv6. `CLAUDE.md`, LÍMITE DE SERVICIO: «la lógica
compartida va a `services/albaranes-comun`, **nunca copiada entre servicios**».

Y el reviewer demostró que ya no era teórico: las dos copias **habían empezado
a divergir** en tres puntos. Estado tras el cambio:

| Divergencia señalada | sv4 antes | sv6 antes | Ahora |
|---|---|---|---|
| Descuento ilegible (`'x'`) | `None` | **`ValueError`** (reventaba una valoración por cola) | Los dos: `invalido` → se ignora, sin excepción |
| Traza de lo ignorado | solo `logger.warning` | `reasons` auditable | Cada uno conserva la suya (es política) |
| Borde del cero | `<= 0.0` → `None` | `< 0.0`, devolviendo `0.0` | Un solo criterio de rango; **cada servicio decide qué persiste** |

### Qué se movió y qué NO

**A `services/albaranes-comun/ruesma_comun/importes.py` (nuevo)**: la función
pura. `clasificar_descuento` (`ausente` / `cero` / `aplicable` / `invalido`),
`factor_descuento` e `importe_de_linea`. Aritmética y rangos, nada más. No
lanza nunca: al otro lado hay una valoración por cola y el guardado de un
revisor.

**NO se movió la política**, siguiendo la instrucción explícita: la precedencia
declarado-vs-calculado, los motivos de revisión y qué se persiste siguen en
quien los aplica. Es la razón de que `clasificar_descuento` distinga `cero` de
`ausente` aunque el importe salga igual: **sv6 persiste `0.0` y sv4 persiste
`NULL` para el mismo dato**, y las dos decisiones son correctas en su servicio.
Sin esa distinción, mover la función habría cambiado en silencio lo que se
guarda.

### La red que impide que vuelvan a separarse

Tests de **identidad**, no de igualdad, uno en cada servicio:

```python
assert review_repository.importe_de_linea is compartida      # sv4
assert importe_calculator.importe_de_linea is importe_de_linea  # sv6
```

Un test de igualdad pasaría el primer día con una copia recién hecha —que es
justo como empezó esta divergencia—. El de identidad cae en cuanto alguien
reintroduce una copia local, aunque sea correcta.

`comun` se instala en modo editable (`pip install -e ../comun`) en los venvs de
ambos servicios: comprobado que las dos suites la ven, y `init.sh` corre las
tres en verde.

### Efecto colateral bueno

`ImporteCalculator` ya no revienta con un descuento, una cantidad o un precio
ilegibles: degrada a «no se puede calcular» y usa el declarado si lo hay. Antes
un `float('x')` sin proteger tumbaba la valoración en mitad de la cola.
Fijado por `test_f019_r27_un_descuento_ilegible_ya_no_revienta` y
`..._un_precio_ilegible_no_revienta_la_valoracion`.

### La observación no bloqueante, aplicada

El docstring afirmaba «NINGÚN sitio de este servicio vuelve a multiplicar
precio por cantidad». No era exacto: `templates/document_detail.html:619` y
`static/app.js:1003` tienen su copia para pintar al vuelo (ambas **con** el
descuento, así que no hay defecto). Rebajado a «ningún sitio del **backend**»,
con la excepción nombrada y el motivo — el guardián estructural vigila el
backend, que es quien persiste.

## Cambio 3 · El cableado `payload → descuento`, por test

La línea que conecta todo el arreglo con la realidad no la ejecutaba ningún
test: todos pasaban los mapas a mano al método privado. Extraída a dos métodos
con nombre —`_cantidades_del_payload` y `_descuentos_del_payload`— y cubierta
con 7 tests.

Lo que protegen es **la asimetría**, que es el matiz que el reviewer identificó
como peligroso:

- las **cantidades** se filtran con `is not None` — una línea sin cantidad
  conserva la que ya tiene la fila valorada;
- los **descuentos NO** — `None` significa «el revisor ha borrado el
  descuento» y tiene que llegar al recálculo.

Escribir el segundo como el primero es un cambio de una palabra que devolvería
el incidente entero y en silencio. Hay un test que afirma la asimetría de
frente (`..._los_dos_mapas_no_se_filtran_igual`) para que nadie la «arregle».

## Qué cambió, en concreto

| Fichero | Cambio |
|---|---|
| `services/albaranes-comun/ruesma_comun/importes.py` | **NUEVO**. La función pura compartida. |
| `services/albaranes-comun/tests/test_importes.py` | **NUEVO**. 27 tests del contrato compartido. |
| `services/albaranes-front/.../review_repository.py` | `sin_cambios` por entradas; `_sanear_descuento` e `_importe_de_linea` delegan en `comun`; cableado del payload a dos métodos con nombre. |
| `services/albaran-valoracion-persist/.../importe_calculator.py` | `_sanitize_descuento` delega los rangos en `comun`; el cálculo usa `importe_de_linea`; el guard de «no se puede calcular» pasa a mirar el resultado de la fórmula, lo que de paso cubre los valores ilegibles. |
| `services/albaranes-front/tests/test_f019_r23_cableado_payload.py` | **NUEVO**. 7 tests del cableado. |
| `services/albaran-valoracion-persist/tests/test_f019_r27_formula_compartida.py` | **NUEVO**. 9 tests: identidad, política conservada y no-regresión. |
| `specs/.../requirements.md` | G7 (R27-R29) y R24 reformulado: por entradas, nunca por resultado. |
| `specs/.../tasks.md` | T18-T21. |
| `docs/ARCHITECTURE.md` | Regla 13: la fórmula vive en `ruesma_comun.importes`; aritmética vs política; y cómo se decide que una línea «no ha cambiado». |

## Lo que quedó FUERA (a propósito)

- **`_apply_valuation_line_updates_in_session` sigue sin test de
  integración** (`ANY(:ids)` es de PostgreSQL y SQLite no lo ejecuta). Sin
  cambios respecto al round trip 2; sigue anotado como pendiente.
- **Los `reasons` obsoletos tras un recálculo legítimo de sv4** (observación no
  bloqueante 1 del reviewer): cuando sv4 sí actualiza una fila, los motivos que
  escribió sv6 se quedan como estaban. Real, y la siguiente piedra para quien
  lea la BBDD — pero no entra en R23-R29 y el encargo dice «no toques nada más
  de la feature».
- **Las tres propuestas de mejora del protocolo** del reviewer (C4 con el «caso
  difícil», `mutacion_paralela.py` y los ficheros sin versionar, y el reintento
  ante `0xC0000142`): son genéricas y, si el humano las acepta, se portan a
  `arnes-base`. No se aplican por cuenta propia.

## Evidencias (round trip 3)

| Evidencia | Valor | Cómo se obtuvo |
|---|---|---|
| **Tests ejecutados y resultado** | **248** (raíz) + **11** (sv5) + **53** (sv6) + **59** (sv4) + **49** (`comun`) = **420 passed, 0 fallos**. Nuevos en este round trip: **42** — 6 de R24, 2 de identidad y 7 del cableado en sv4; 9 de R27 en sv6; y **27** del contrato compartido en `comun`. | `bash harness/init.sh` |
| **Cobertura de las líneas cambiadas** | **93,1 % (81/87 líneas, umbral 80 %, nivel `critico`)** — sube desde el 89,1 % del round trip 2 pese a crecer el alcance de 55 a 87 líneas | línea `PUERTA COBERTURA` de `bash harness/init.sh` |
| **Mutantes generados y supervivientes** | **31 generados, 28 muertos, 3 supervivientes, 0 timeouts**. Los 3 son **equivalentes**, verificados ejecutando original y mutante (13 valores de frontera y 81 combinaciones). Análisis completo en `progress/mutacion_F-019.md`. | `python -m harness.mutacion --feature F-019 --workers 1` |
| **Tiempo de ejecución de la suite** | raíz **≈46 s**; sv4 **1,30 s**; sv6 **1,13 s**; sv5 **0,46 s**; `comun` **25,43 s** | salida de cada pytest |

Evolución de la mutación en las tres pasadas: 4 mutantes / 0 supervivientes →
24 / 2 → **31 / 3**. Los 7 nuevos salen de `ruesma_comun/importes.py`; 6 mueren
y el séptimo es el equivalente del borde del cero (inalcanzable: la línea
anterior ya devolvió por el caso `valor == 0.0`).

**Todo se ha ejecutado EN SERIE**, según el aviso del reviewer: él midió que
lanzar `init.sh` en paralelo con otra ejecución lo tumba en Windows por presión
de recursos (`git init` devolviendo `0xC0000142`, *STATUS_DLL_INIT_FAILED*), y
que en aislamiento pasa. Ninguna medida de este round trip se ha tomado con
otra cosa corriendo a la vez.

### Estado de las puertas

```
[OK] PUERTA COBERTURA: 93.1% de 87 líneas cambiadas cubiertas (81/87, umbral 80%, nivel critico)
[AVISO] PUERTA RUTAS SENSIBLES [evals]: aviso: falta la evidencia de 2 ruta(s) sensible(s) tocada(s):
      - services/albaran-valoracion-persist/application/services/price_reconciler.py
      - services/albaran-valoracion-persist/domain/models/valuation_envelope.py
[OK] Rama actual: feature/F-019-importe-unitario-manda
----------------------------------------
ENTORNO LISTO. Puedes trabajar.
```

**Atención, esto ha cambiado y lo digo yo antes de que lo encuentre nadie**: la
puerta pasa de señalar **2 rutas sensibles a 3**. Este round trip toca
`services/albaran-valoracion-persist/application/services/importe_calculator.py`,
que cae bajo el patrón `.../application/services/**` de
`harness/rutas_sensibles.json` («redes deterministas de sv6»). En los dos round
trips anteriores el único fichero de producción era de sv4, que no está
declarado; ahora sí se toca sv6, porque el cambio 2 exige que `ImporteCalculator`
consuma la fórmula compartida.

El **estado** de la puerta no cambia (`aviso`) ni cambia la causa de fondo, que
es la de siempre y no es de esta feature: las claves LLM no están en el entorno
local —son secretos y este repositorio prohíbe escribirlas— y
`evals/ground_truth/` sigue **sin un solo caso**, así que la pasada declarada
daría `NO_EVALUABLE` aunque hubiera claves. Motivo completo y salidas literales
en §T9 de este informe; exigencia declarada `aviso` por la decisión D5 de
F-011. **No se marca N/A: se declara ausente con causa** (CHECKPOINTS.md C4
ter), y ahora con una ruta más que antes.

## Lo que falta para cerrar

1. Las verificaciones **MANUAL (humano)** de T10 y T17, en particular «guardar
   desde el front y volver a mirar el total».
2. El veredicto del **reviewer** sobre esta tercera pasada.
3. Decisión del humano sobre revalorar el 2.137.569 en la BBDD local (R20).
4. Pendientes heredados: `evals/ground_truth/` vacío; hacer testable
   `_apply_valuation_line_updates_in_session`; los `reasons` obsoletos tras un
   recálculo de sv4; y las tres propuestas de protocolo del reviewer, que si se
   aceptan se portan a `arnes-base`.
