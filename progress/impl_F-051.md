<!-- progress/impl_F-051.md -->
# F-051 · Almacén por línea · Informe del implementer

Fecha: 2026-10-05. Worktree `albaranes-F-051`, rama `feature/F-051-almacen-por-linea`.
Spec v4 aprobada por el humano en la PARADA 1 («si», 2026-10-05). Rigor `critico`.
T1–T20 y T25 hechas; **T21–T24 son del humano** (evals con LLM y MANUAL, comandos abajo).

## 0. Fusión de `dev` (paso 0)

`git merge dev` (trae F-054): conflictos **solo de papeleo**, ninguno en código.
`features.json` = F-054 de `dev` + F-051, F-058, F-059, F-060 y F-007 (`pending`,
nota de re-alcance) de esta rama; `current.md` = base de `dev` + bloque de F-051;
`BACKLOG.md` regenerado. Commit `1e76e4a`. F-051 → `in_progress` en `8610c87`.

## 1. Qué cambió

**sv2** (solo prompt): `config/prompts.yaml`, «## Código de imputación manuscrito»: la
viñeta del código único se sustituye por las **cuatro viñetas literales** de design.md
(R25, R29, R30). Fase 2 las recibe por `{prompt_fase_1}`; ningún prompt de fase 2 se toca.

**sv6**:
- `application/services/almacen_politica.py` (nuevo, puro): constantes, `familias_destinadas_de_csv`, `motivo_revision_almacen`.
- `partida_matcher.py`: `almacen_sin_partida=False` en el constructor; rama nueva tras la del ALM
  impreso: sin partida ⇒ `almacen_sin_partida`, final `None`, motivo, conserva el id de la IA si está en el sobre.
- `valuation_builder.py`: `familias_destinadas`; familia efectiva destinada ⇒ motivo
  `partida_ausente_familia_destinada` + `review_required` (no bloqueante).
- `valuation_records.py` (`PartidaAction`), `config/settings.py` (`ALMACEN_SIN_PARTIDA_ENABLED`,
  `FAMILIAS_DESTINADAS`), cableado en `interface_adapters/composition.py` **y** `interface_adapters/api/app.py`.

**sv4**:
- `domain/services/almacen.py` (nuevo, puro): `ACCION_ALMACEN_ELEGIDO`, `estado_partida`, `contar_con_partida`.
- `domain/services/confianza.py`: `_partida_factor` = 1 con valoración, 0 sin ella (R21).
- `review_models.py`: `ConciliacionDisplay.estado_partida`, `DocumentDetailPayload.lineas_con_partida`.
- `review_repository.py`: estado de partida en el mapa de conciliación (en almacén, sin partida
  de la casada ni de la derivada); `_build_display_lines` sin la leída por IA1; `asignar_almacen`
  (un `UPDATE ... RETURNING` con `IN :ids` expandido); `snapshot_lineas_valoracion`;
  `update_line_conciliacion` (R12, R19, R20); `_lineas_con_partida`.
- `review_service.py`: `asignar_almacen_linea` / `asignar_almacen_todas` (una entrada `undo_log`).
- `interface_adapters/web/app.py`: `POST .../lines/{vid}/almacen`, `POST .../almacen-todas` (404 si no toca nada).
- `templates/document_detail.html`, `static/app.js`, `static/styles.css`: «Almacén» en la celda
  (placeholder en editables, texto en solo lectura) y en la tabla de solo lectura; opción fija
  «Almacén (sin partida)» primera en el combo de partida; botón «Almacén a todas las líneas».

**Docs** (T19): `docs/ARCHITECTURE.md` regla 16 (R24, IA1 decide, sv6, sv4, Sigrid);
`dominio_negocio_albaranes.md` §10.8 y enumeración de `partida_action` (corrige `alm_acopio`,
que es `origen`, no acción); `sv2.md` (cuándo sale null `codigo_imputacion`); `sv6.md` (dos variables).
`azure-apps/albaranes.md`: sin cambios (ni colas, ni tablas, ni endpoints entre servicios).

## 2. Decisiones y desviaciones (justificadas)

1. **Cableado también en `api/app.py` de sv6** (design solo cita `composition.py`): la API HTTP
   (`/v1/valuation/run`) construye su propio builder; sin esto R1/R8 no valdrían en modo HTTP.
2. **JS: la partida vaciada viaja como `""`** (design no lo listaba): el «Guardar» de fila y
   «Guardar todas» mandaban `null` para un input vacío, que el backend lee como «no viene»;
   sin el cambio R12 no ocurría nunca desde la UI. El aviso «pasará a NUEVA» ya no salta al vaciar.
3. `update_line_conciliacion`: la partida actual es la **final** (sin el respaldo de la casada,
   como pide el design); la marca `almacen_elegido` solo se escribe al vaciar una partida real
   (guardar otros campos de una línea en almacén conserva la marca de quien la puso, p. ej. sv6).
   Al salir de almacén (R20) **no se reescribe `partida_action`**: el design no lo pide y no hay
   valor de sv4 para «partida a mano»; la marca queda como rastro (no decide estado).
4. Motivo de familia destinada escrito con su **constante**: la suite de la raíz congela el
   vocabulario de motivos del builder (F-027 R22). **Cambio en test de otra feature**:
   `tests/test_f027_r18_r22_contrato.py` añade `partida_ausente_familia_destinada` a
   `MOTIVOS_DEL_BUILDER`, con el motivo escrito en el propio test (consumidores: sv6 escribe,
   sv4 pinta en crudo). Commit `d707e9c`.
5. `snapshot_lineas_valoracion` entró en el commit de T12 (antes de su RED de T15): sus dos
   tests de T15 nacieron en verde. El resto de T15 sí tiene RED.
6. Entorno: *junction* `services/albaranes-front/.venv` → venv del árbol principal (ignorada
   por git), necesaria para que `harness.mutacion` e `init.sh` encuentren el venv declarado de
   sv4. Ningún venv modificado ni nada instalado. Puede borrarse con
   `Remove-Item services\albaranes-front\.venv` (solo quita el enlace).

## 3. Para el humano (no implementado, decide él)

- **O1 · Elegir una línea de contrato en una línea en almacén.** El combo de partida (y el ✎ de
  Origen) re-concilian con `PATCH .../conciliacion` `mode=contract_line`
  (`set_line_conciliacion`), que **no toca `codigo_partida_final`** (como hoy). Una línea en
  almacén a la que se le elige una línea de contrato **sigue en almacén** (ahora se ve, con D1 v4).
  Para sacarla de almacén: teclear la partida y «Guardar» (R20) — o decidir que elegir una línea
  de contrato fije también su partida (cambio de una línea en `set_line_conciliacion`; afecta a
  D4: ¿re-apuntar el contrato de una línea en almacén la mantiene en almacén?). No lo he
  decidido por mi cuenta: la spec no lo dice. Relevante para T24.
- **O2** · Poner a una línea en almacén la partida de su casada (R20) la deja Sigrid en BBDD,
  pero el `confirm()` del navegador sigue avisando «pasará a NUEVA» (el JS no conoce la partida
  de la casada, que en almacén no se pinta). Solo texto del aviso.

## 4. Fase RED (trazas reales; lista completa de tests fallidos en el commit de cada Tn)

```
T1 · cd services/albaran-valoracion-persist && python -m pytest tests -k "f051 and (r4 or r5 or r9)" -q --tb=line
15 failed, 231 deselected
14 × ModuleNotFoundError: No module named 'application.services.almacen_politica'
 1 × AttributeError: 'Settings' object has no attribute 'familias_destinadas'
T3 · python -m pytest tests -k "f051 and (r1 or r2 or r6 or r8)" -q --tb=line
14 failed, 5 passed
13 × TypeError: PartidaMatcher.__init__() got an unexpected keyword argument 'almacen_sin_partida'
 1 × AssertionError: assert 'almacen_sin_partida' in ('existing_matched', 'new_line_created', ...)
```
(R6 cae por el `TypeError` del constructor nuevo; su aserción es de regresión. R8 verde: es regresión.)
```
T5 · python -m pytest tests -k "f051 and (r1 or r2 or r3 or r4 or r5 or r7 or r28)" -q --tb=line
8 failed, 27 passed
8 × TypeError: ValuationBuilder.__init__() got an unexpected keyword argument 'familias_destinadas'
R28 contra el comportamiento de dev (interruptor apagado = matcher de dev, R8):
linea 702 (sin partida) -> 03.02 existing_matched ['only_1a_available', 'ia_match_trusted']
AssertionError: R28 RED: la linea sin partida recibe '03.02' (la del contrato casado)
T7 · cd services/albaranes-api && python -m pytest tests -k "f051" -q --tb=line
11 failed, 12 passed
test_f051_prompt_partida.py:185: AssertionError: assert 'Un código escrito junto a una línea, o que agrupa varias, se aplica SOLO ...
test_f051_prompt_partida.py:191: AssertionError: assert 'Una línea sin código propio, que no sea complemento de otra, ...
test_f051_prompt_partida.py:214: AssertionError: assert 'Un código de documento (en la cabecera, un sello o el margen ...
test_f051_prompt_partida.py:221: AssertionError: assert 'Portes, bombeo, recargos, excesos y demás complementos ...
test_f051_prompt_partida.py:228: AssertionError: assert 'Si solo hay... las líneas.' not in '## Convenci...se lea mal. '
test_f051_prompt_partida.py:260: AssertionError: ('albaran_revision_fase2_es' | _hormigon | _mortero | _residuos, 'Un código escrito junto ...')
```
(Verdes en T7, como pide la tarea: el resto de R26 —cercanía, formatos, márgenes, «el primero», null, mismo vertido— y «sin copia propia» de R27.)
```
T9 · cd services/albaranes-front && python -m pytest tests -k "f051 and (r10 or r21)" -q --tb=line
13 failed, 2 passed
9 × ModuleNotFoundError: No module named 'domain.services.almacen'
3 × AssertionError: assert 0.0 == 1.0        (factor de partida de una línea en almacén)
1 × AssertionError: assert 0.75 == 1.0       (_line_score sin partida frente a con partida)
T11 · python -m pytest tests -k "f051 and (r12 or r14 or r15 or r16 or r19 or r20 or r23)" -q --tb=line
13 failed, 4 passed
8 × AttributeError: 'AlbaranReviewRepository' object has no attribute 'asignar_almacen'
2 × AssertionError: assert 'existing_matched' == 'almacen_elegido'   (vaciar en fila Sigrid)
1 × AssertionError: assert 'new_line_created' == 'almacen_elegido'   (vaciar en fila Nueva)
1 × assert None == 501                       (R19: guardar en almacén la volvía Nueva)
1 × AssertionError: assert '03.02' is None   (R19: guardar en almacén le ponía la de la casada)
```
(Los 4 verdes son guardas: R20 ×3 y «no enviar la partida no la vacía».)
```
T13 · python -m pytest tests -k "f051 and (r11 or r17)" -q --tb=line
7 failed, 1 passed
2 × AssertionError: assert '03.02' is None
2 × AttributeError: 'ConciliacionDisplay' object has no attribute 'estado_partida'
3 × AttributeError: 'DocumentDetailPayload' object has no attribute 'lineas_con_partida'
T15 · python -m pytest tests -k "f051 and (r18 or endpoint)" -q --tb=line
7 failed, 4 passed
2 × AssertionError: {"detail":"Not Found"}
5 × AttributeError: 'ReviewService' object has no attribute 'asignar_almacen_linea' / '..._todas'
T17 · python -m pytest tests -k "f051 and (r11 or r12 or r13 or r17 or r22 or plantilla)" -q --tb=line
10 failed, 18 passed
2 × AssertionError: assert '03.02' == 'Almacén' ; 1 × assert '' == 'Almacén'
1 × AssertionError: falta el botón «Almacén a todas las líneas» ; 1 × ValueError: substring not found
1 × assert 'placeholder="Almacén"' in '<input ... js-partida-combo ...'
1 × assert 'Almacén' in '<td class="concilia-td" data-col="partida" ...'
3 × assert '...' in '// static/app.js ...' ('Almacén (sin partida)', '/almacen`', 'field === "codigo_partida"')
```
GREEN de cada tarea: el mismo comando en verde antes de su commit (T2, T4, T6, T8, T10, T12, T14, T16, T18).

## 5. Verificación

Suites, una tras otra, con el intérprete que usa `init.sh` (raíz `.venv` del árbol principal;
sv4 su `.venv`) y `PYTHONPATH` al `ruesma_comun` del worktree (comprobado: se importa del worktree):

| Suite | Resultado |
|---|---|
| comun | 332 passed (41,0 s) |
| sv2 | 397 passed (14,6 s) |
| sv3 | 421 passed (15,6 s) |
| sv4 | 446 passed (28,9 s) |
| sv6 | 283 passed (8,0 s) |
| raíz | INIT_RAIZ |

La primera pasada de la raíz dio **3 KO**, los tres por F-051 y arreglados: congelación de motivos
de F-027 R22 (2, decisión 4) e inventario de mutación de F-039 (fila de `mutacion_F-051.md`).

`bash harness/init.sh` (T25): INIT_RESUMEN

## 6. Pendiente del humano (T21–T24)

- **T21 · evals** (se factura; autorizar antes). Desde la raíz del worktree:
  `python -m evals.runner --con-llm --feature F-051` → `progress/evals_F-051.md`; comparar la métrica
  de partida con la de F-047 en líneas sin partida marcada (no es regresión si el ground truth también las deja en blanco).
- **T22 · pipeline local**: valorar un albarán genérico sin partida impresa y en PG local
  `SELECT partida_action, codigo_partida_final, matched_contrato_line_id FROM albaran_line_valuations WHERE valuation_id = '<id>';`
  ⇒ `almacen_sin_partida`, NULL y el id del contrato conservado.
- **T23 · sv2 local con LLM real** (se factura) sobre los cinco albaranes de tasks.md; pegar
  `data.lineas[*].codigo_imputacion`.
- **T24 · navegador**: la fila muestra «Almacén»; el combo ofrece «Almacén (sin partida)» primero;
  elegirlo deja la fila «Sigrid»; vaciar la partida de otra fila Sigrid y «Guardar» la deja en
  «Almacén» y «Sigrid»; «Almacén a todas las líneas» pide confirmación con el recuento y el
  «Deshacer» del albarán lo revierte; con `ALMACEN_SIN_PARTIDA_ENABLED=false` en sv6 el albarán sale
  como hoy. Mirar también O1 y O2 (§3).
- Despliegue (lo pide el humano): sv6 → sv4 → sv2 (`.\deploy.ps1 -Only sv6`, `.\check_deploy.ps1`,
  luego `-Only sv4` y `-Only sv2`). Para F-053 y F-049: design §«Contrato con F-053 y con F-049».

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests de F-051 | 144: sv6 53, sv2 23, sv4 68 (todos verdes) |
| Tests ejecutados | comun 332 · sv2 397 · sv3 421 · sv4 446 · sv6 283 · raíz INIT_RAIZ_N — 0 fallos |
| Cobertura de líneas cambiadas | COBERTURA |
| Mutantes | 57 generados, 57 muertos, **0 supervivientes** (campaña completa, sin muestreo, `d707e9c`, 857,5 s). La primera (`3e87861`) dejó 1, hueco real cerrado con test: `progress/mutacion_F-051.md` |
| Tiempo de las suites | comun 41,0 s · sv2 14,6 s · sv3 15,6 s · sv4 28,9 s · sv6 8,0 s · raíz INIT_RAIZ_T |
| Evals (T21) | PENDIENTE del humano (se facturan; no lanzadas por instrucción) |
