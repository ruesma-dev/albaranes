<!-- progress/impl_F-065_fase1.md -->
# F-065 · fase 1 (T1–T12) · informe del implementer

Rama `feature/F-065-lineas-editadas-y-reparto` (worktree, desde `abec7f8`), `critico`: **sv4**, **sv6** (DDL), sv9 (test). Despliegue **sv6 → sv4**.

## 1. Commits (uno por tarea)

`8129d08` in_progress · `5e15f37` T1 RED · `2b88a49` T2 DDL · `4493b8c` T3 dominio · `01fa9e0` T4 PUT · `8240092` T5
cerrojo · `37169e2` T6 tests F-019/F-036 · `5c61741` T7 PATCH · `16c0f84` T8 · `7b9a5bc` T9 front · `6233bd4` T10 sv9 ·
`a2292ec` T11 docs (+ `azure-apps` `3db4274`, en `master` de ese repo) · `af6733c`, `d4fe841`, `8c5341c` y el de este informe T12.

## 2. Qué cambió (ficheros)

- **sv6** `schema_contribution.py` (`ALTER ... ADD COLUMN IF NOT EXISTS bloqueada BOOLEAN NOT NULL DEFAULT FALSE`) y
  `orm_valuation_models.py` (`server_default false`; el replace no la nombra ⇒ `false` al revalorar).
- **sv4** `domain/models/review_models.py`: `cantidades_tras_editar`, `es_fila_manual`, `orden_filas_ficha`,
  `aviso_suma_importes`, errores `AlbaranAprobadoError`/`LineaBloqueadaError`/`LineasIncompletasError`,
  `ConciliacionEditBody.campos()` (movido desde `app.py`), `TraerLineasBody`, `unitario_contrato`, `bloqueada`,
  `suma_filas`/`suma_leida`/`n_filas_manuales`/`aviso_suma` en el detalle. `review_repository.py`: PUT solo cabecera
  (−660 líneas: fuera `_recalc_valuation_importes`, los mapas del payload, `_apply_valuation_line_updates_in_session`
  y los sellos de razones que solo usaba el recálculo), `_exigir_editable`, `update_line_conciliacion(campos,
  bloquear)` reescrito, bloquear/desbloquear, total con `ROUND`, almacén a todas `AND NOT bloqueada`,
  `_exigir_lineas_completas` en los dos aprobar, precio aplicado, sumas y filas manuales, traer con `(id, Q)`, DDL
  defensivo. `review_service.py`, `app.py` (409 de los errores nuevos, `?bloquear=1`, `POST .../bloquear|desbloquear`,
  `from-contrato` con cantidades, `saltadas`, aviso R20 en «Aprobar», `volver=ficha`), `static/app.js`,
  `templates/document_detail.html` (§4).
- **Docs**: `docs/ARCHITECTURE.md` regla 20; `azure-apps/albaranes.md` (`bloqueada`, `line_kind` `manual`, cantidades).
- **Tests**: nuevos `test_f065_f1_{cabecera,fila,bloqueo,aprobar,js}.py` y `f065_bbdd.py`, sv6
  `test_f065_bloqueada_ddl.py`, sv9 `test_f065_partes.py`; adaptados F-019, F-036 (§6), F-051 y F-053 (§7).

## 3. Decisiones y desviaciones (justificadas)

- **D1 · Papelera fuera de R4**: mover a la papelera y purgar no son edición (R4 enumera las escrituras; el borrado
  múltiple y «Vaciar papelera» solo saben saltar `AlbaranBloqueadoError`): siguen con el cerrojo de F-053. Aprobar un
  aprobado sigue siendo un no-op, no un 409.
- **D2 · «Sin cambios» con tolerancia 1e-9** (`_mismo_numero`), no `numeros_iguales` (5e-3, design §5.1): con 5
  milésimas no contaba como cambio un precio de 4 decimales (0,0045 → 0,0040 €/kg). El front compara cada input con
  su propio valor inicial: sin falsos cambios.
- **D3 · El importe solo se recalcula si cambia cantidad, precio o descuento**: editar descripción, partida o código
  externo no reetiqueta un importe declarado (F-019 R24 en la fila); `review_required` baja con cualquier cambio (R11).
- **D4 · Descuento saneado al guardar** (0 → NULL) y número ilegible en el PATCH ⇒ **422** (con R8 `null` es
  «vaciar»: un «abc» ya no puede borrar la cantidad).
- **D5 · R20 numera como la tabla de la ficha** (`orden_filas_ficha`); las filas sin línea de contrato ni derivada no
  se pintan y no cuentan.
- **D6 · El confirm «pasará a NUEVA» sigue** en la fase 1 (lo quita R25) pero solo sobre campos que viajan; la regla
  F-051 Contrato → Nueva (partida, unidad, precio) sigue en el backend.
- **D7 · Sin `DisplayLine.bloqueada`**: la plantilla lee `LineValuationPayload.bloqueada`, que ya tienen todas las filas.
- **D8 · «Solo volver a buscar» sin el confirm de R22** (la spec enumera tres vías); anotado por si el humano lo quiere.
- **D9 · F-036 R3/R4 cambian de sentido**: editar Q en una fila no reproducible ya no va a revisión ni sella razones
  (lo tecleado YA son contenedores: decide quien edita, R11); `front_sin_cantidad_convertida` desaparece (R10).

## 4. Front (T9)

`collectPayload` sin líneas; `_camposCambiados` (sustituye a `_conciliaBody`: números como números, partida `""` =
almacén, el importe no viaja); «Guardar» y «Guardar todas» (solo filas con cambios; si no, «No hay cambios en las
líneas») con `?bloquear=1`; `guardarCabecera` (R19 y, al aprobar, `data-aviso-suma`, R21); `confirmarRevalorar`
(R22); `importeDeFila` (R12); «Traer» con cantidad por línea (`lineasATraer`); «Desbloquear»; masivos que dicen
cuántas guardadas saltaron. Plantilla: `editable = is_editable and not approved` gobierna todo lo que escribe;
aprobado ⇒ «Aprobado · solo lectura» + «Desaprobar para editar» (`volver=ficha`); fila bloqueada ⇒ solo lectura +
«Desbloquear»; precio aplicado con el del contrato en el `title`; importe = siempre el guardado.

## 5. Fase RED (trazas reales)

sv4 con `.venv\Scripts\python -m pytest ... -p no:cacheprovider` desde su carpeta; sv6/sv9 con `python -m pytest`.

**T1 (R1–R23), sobre `5e15f37`** — `pytest tests/test_f065_f1_cabecera.py tests/test_f065_f1_fila.py
tests/test_f065_f1_bloqueo.py tests/test_f065_f1_aprobar.py --tb=line` ⇒ `144 failed, 14 passed, 1 warning in 7.07s`.
Los centrales, con la regresión de METALFIRE a la vista (fila 11 que la administrativa dejó en 6/6/690 € y el PUT
devolvió a 8/8/920 €):
```
tests\test_f065_f1_cabecera.py:77: in test_f065_r1_put_con_las_blancas_no_toca_las_filas
E   AssertionError: albaran_line_valuations
E     At index 0 diff: (11, 'f065-val-1', 701, 501, ..., 1.0, 8.0, 8.0, 920.0, None, 'calculated', ...) != (11, 'f065-val-1', 701, 501, ..., 1.0, 6.0, 6.0, 690.0, None, 'calculated', ...)
tests\test_f065_f1_cabecera.py:89: in test_f065_r1_put_sin_lineas_no_borra_las_blancas
E   AssertionError: assert [(801, 'f065-...e, None, ...)] == [(701, 'f065-...e, None, ...)]
E     Right contains 3 more items, first extra item: (702, 'f065-doc-0000-0000-000000000359', 'merge', 2, None, None, ...)
tests\test_f065_f1_cabecera.py:155: in test_f065_r3_put_sin_aprobar_sobre_un_aprobado_no_lo_desaprueba
E   Failed: DID NOT RAISE Exception
tests\test_f065_f1_cabecera.py:180: in test_f065_r3_put_sin_aprobar_de_un_pendiente_no_toca_la_aprobacion
E   AssertionError: assert None == 'nadie'
tests\test_f065_f1_fila.py:282: in test_f065_r9_la_ficha_pinta_el_precio_aplicado_en_filas_contrato
E   assert 115.0 == 120.0 ± 1.2e-04
tests\test_f065_f1_fila.py:403: in test_f065_r12_plantilla_el_importe_es_el_guardado_tambien_si_es_reproducible
E   assert 'value="19.99"' in '<td class="concilia-td td-num" data-col="importe" data-sort-value="20.0">...'
```
El resto falla porque la API aún no existe: `unexpected keyword argument 'campos'` ×26, `cannot import name
'AlbaranAprobadoError'` ×24 (y `es_fila_manual`, `cantidades_tras_editar`, `ConciliacionEditBody`,
`aviso_suma_importes`, `LineaBloqueadaError`, `LineasIncompletasError`), `'lineas'` ×4, rutas 404/400. Los 14 que
pasaban son guardas de regresión (p. ej. R3 aprobar un pendiente, R16).

**T2 (R17)** — sv6 `pytest tests/test_f065_bloqueada_ddl.py` ⇒ `5 failed, 1 passed` (`KeyError: 'bloqueada'`); sv4
`-k ddl` ⇒ `2 failed` (`'LineValuationPayload' object has no attribute 'bloqueada'`). **T6** (`37169e2`): F-019/F-036
reescritos ⇒ `37 failed, 19 passed` (`... got an unexpected keyword argument 'campos'` ×36 y el R8 de plantilla).
**T9** — `test_f065_f1_js.py` + 3 de plantilla ⇒ `22 failed`: `ValueError: substring not found` (las funciones JS aún
no existían), `assert '_camposCambiados(tr)' in 'saveBtn.addEventListener(...'`, `assert 'No hay cambios en las
líneas' in ...`, `assert 'saltadas' in ...`, `assert 'id="save-btn"' not in ...` (R5), `data-aviso-suma` (R21).

**T10 (sv9, sin código)** — el entregable es el test: se rompió A PROPÓSITO, en una copia aislada del servicio en el
scratchpad (borrada después), `validador_alta._cantidad` para mandar siempre `cantidad_albaran`:
```
...\sv9_red\tests\test_f065_partes.py:50: assert 3.0 == 3000.0 ± 0.003
E   AssertionError: assert PeticionAlbaran(... cantidad=7.0, precio=115.0, ctrpro_ide=700101, ...) == [Motivo(codigo='cantidad_sin_convertir', detalle='', referencia_linea='11')]
FAILED ...::test_f065_r10_fila_contrato_editada_se_admite_con_cantidad_q[contenedores]   (y [toneladas_a_kg])
FAILED ...::test_f065_r10_la_fila_legada_sin_convertida_es_la_que_se_rechaza
3 failed, 1 passed in 0.68s
```
En verde: `4 passed in 0.72s` sobre el código real.

## 6. T6 · tabla caso viejo → caso nuevo

Casos contra el PATCH (`update_line_conciliacion(campos=...)`), mismos números medidos; el PUT ya no recalcula (R1).
«=» = mismo nombre y misma aserción de fondo.

| Caso viejo (F-019, `_recalc_valuation_importes` / payload) | Caso nuevo |
|---|---|
| r23 guardar sin tocar no infla el total (139,66) / cada línea conserva su importe (×5) | = (PATCH solo de la partida / PATCH vacío) |
| r23 descuento sobre la cantidad nueva (32,58) / sin descuento (20) / fuera de rango (20) / editado manda (43,98) | = (PATCH `cantidad` o `descuento`) |
| r23 una línea ilegible no rompe el guardado | `..._de_otra` (PATCH a otra línea; la ilegible conserva 35,19) |
| r25 total recalculado (139,66) / r26 sin ruido float (3392,72) | `r25_..._al_guardar_la_fila` / r26 con 3671,58 |
| r24 declarado discrepante no se pisa / cede con cantidad (30) / cede con descuento (75) | = (PATCH código externo / cantidad / descuento) |
| r24 intacta / cambiar cantidad ⇒ `calculated` / reenviar el mismo descuento / cero y nulo (×2) | = (PATCH descripción / cantidad / lo mismo: sin cambios) |
| `test_f019_r23_cableado_payload.py` (7: el payload llega al recálculo; cantidades filtradas `is not None`, descuentos no) | **borrado** (design T6): no hay mapas del payload. «Ausente = no cambia; `null` = vaciar» lo fijan `test_f065_r8_dominio_campos_presentes` (descuento `null`), `..._descuento_a_null_lo_vacia`, `..._cantidad_a_null_la_vacia`; que el PUT no toca líneas, `test_f065_r1_*` |

| Caso viejo (F-036) | Caso nuevo |
|---|---|
| r1 reproducible solo si cuadra el producto (×11) / tolerancia | = (importado del dominio) |
| r2 guardar sin tocar no multiplica por seis | = (PATCH vacío: 120 €, convertida 1) |
| r2 importe con la convertida conservada (108) | = (PATCH descuento 10) |
| r2 reproducible se rehace (2 t → 3 t) | = con Q en kg: PATCH 3000 ⇒ ca 3, cc 3000, 150 €; además sin revisión ni razones (antes r3 «reproducible no va a revisión») |
| r2 sin convertida manda la cruda (cc NULL) | `..._manda_la_cantidad_editada`: cc = 8 (R10) |
| r2 convertida ilegible cae a la cruda (960) | `..._no_tumba_el_guardado`: caso (c), cc = 2, ca = 6, 240 € |
| r5 la convertida no entra en «sin cambios» / reenviar mismas entradas | = (PATCH vacío / Q = 1 y descuento `null`) |
| r6 vale para cualquier familia (72) / el código no mira la familia | = / ampliado a `cantidades_tras_editar` |
| r7 factor 1 con convertida distinta (108) / punto ciego (240) | = (en el punto ciego la del albarán pasa también a 2, caso a) |
| r3 editar cantidad no reproducible va a revisión | `..._la_decide_el_revisor`: sin revisión ni razón (D9) |
| r3 sin editar cantidad no avisa / la razón no pisa las de sv6 | = / `..._las_razones_que_dejo_sv6_no_se_tocan` |
| r4 sin convertida se deja dicho / línea que nadie toca sin razones | `..._la_edicion_la_fija` (R10) / = |
| r3 helper idempotente, razones ilegibles, línea inexistente, BBDD sin columna (×6) | **retirados** con `_anadir_reason_linea_in_session` y `_marcar_linea_en_revision_in_session`, que solo usaba el recálculo |
| r3 «el aviso de lo defensivo lleva la traza» (3 helpers) / r24 depurar motivos | `test_f036_r24_...traza_del_fallo` (queda `_depurar_motivos`) / = |
| r8 importe persistido / ordenación / sin persistido / descuento una vez | = |
| r8 «reproducible sigue calculando en Jinja» (20,00) | `..._tambien_ensena_lo_guardado` (99,00, R12) |

## 7. Verificación (resultado real)

- Criterio de cada tarea ejecutado al cerrarla. Suites completas por separado (nunca dos a la vez): **sv4 1015 passed**
  (49,7 s), **sv6 295 passed**, **sv9 526 passed**; JS con node v24.
- Adaptados (motivo en cada test): F-051 (cuerpo del PATCH = `_camposCambiados`, `saltadas`, `campos=`), F-053 (un
  aprobado ya no se edita: lo de alta no bloqueante se prueba sobre un pendiente; producto con el albarán pendiente;
  `comprobar_editable`; traer con `lineas`). Esquemas de test: `bloqueada` y `approved` en `conftest.py`/`f053_sv4_bbdd.py`.
- **`bash harness/init.sh`** (tal cual, worktree, sobre `8c5341c`): raíz `1083 passed`, sv4 `1015`, sv6 `295`, sv9
  `526`, resto en verde (caché); **`PUERTA COBERTURA: 100.0% de 309 líneas cambiadas cubiertas (309/309, umbral 80%,
  nivel critico)`**; tamaño dentro de topes; **`ENTORNO LISTO. Puedes trabajar.`** Avisos previos (ruff, F-053
  `blocked`, `[ADAPTAR]`). Entorno: *junction* `services\albaranes-front\.venv` → venv de sv4 del árbol principal
  (quitarla con `cmd /c rmdir services\albaranes-front\.venv` antes de `git worktree remove`). Sin KO de entorno.

## 8. Mutación

`python -m harness.mutacion --feature F-065 --salida progress/mutacion_F-065_fase1.md` (sin `--workers`: 4 por
defecto; comun no cambia, así que los worktrees de la campaña importan el comun editable del árbol principal sin
riesgo). **Campaña válida (2.ª), `progress/mutacion_F-065_fase1.md`: SHA `d4fe841`, 6 ficheros, 925 líneas, 131
mutantes, 131 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto, 1693,2 s**, media 12,9 s × 4 workers = 51,6 s
por mutante frente a una línea base de sv4 de 84,5–89,4 s (con `-x` el mutante muere en el primer fallo: coherente,
RM2). Después de `d4fe841` solo entran el informe, el inventario, `tasks.md`, este informe y orden de imports/un
`pytest.raises` más estricto en tests: el código de producción medido es el de HEAD.

**Campaña 1** (`af6733c`, 140 mutantes, 119 muertos, **21 supervivientes**, 1917,2 s; informe archivado fuera de git).
Cada uno, con su cierre (comprobado aplicando el mutante a mano sobre `d4fe841` y lanzando el fichero de tests: los 16
que siguen existiendo mueren, 1–5 fallos cada uno):

| # | Mutante | Por qué sobrevivía | Cierre |
|---|---|---|---|
| 3, 4, 129 | `frozen=True → False` (`ResultadoAlmacenTodas`); `bloquear=False → True` (servicio y `Query` de la ruta) | nadie los ejercitaba por defecto | tests: `FrozenInstanceError`; editar sin `bloquear` no bloquea; ruta sin y con `?bloquear=1` |
| 27, 28, 33 | clave de `orden_filas_ficha` (`merge_line_id is None`, `or 0 → and 0 / or 1`) | **equivalentes**: las sintéticas y sueltas tienen `merge_line_id` nulo | código reescrito: clave `(sintética, id)` (docstring lo explica) |
| 42, 47, 59 | `round(dif, 2) → 3`; `n_filas_manuales = 0 → 1`; `< 1e-9 → <=` | sin caso frontera ni del defecto | 2120,006 vs 2120 ⇒ aviso; detalle sin valoración ⇒ 0; `_mismo_numero(1e-9, 0)` falso |
| 62 | `a is None or b is None → and` | **equivalente** (el `try` daba lo mismo) | reescrito: el `except` decide «dos vacíos»; ahora lo matan 5 tests |
| 63, 70 | `_txt(...) or None → and None` (descripción, código externo actuales) | sin «reenviar lo mismo» | tests: la misma descripción / el mismo código externo no son cambio |
| 85 | almacén `and → or` | sin edición en almacén | test: editar la cantidad en almacén no reescribe la marca |
| 95 | identidad `or "precio_unitario" → and` | sin cambio de precio/unidad aislado | test: precio o unidad ⇒ Nueva (regla F-051 vigente) |
| 99 | override de descripción `!= → ==` | sin test del override | test: distinta ⇒ override; la del contrato ⇒ NULL |
| 105, 116 | `round(sum, 2) → 3` en las sumas del detalle | **equivalentes** (importes de 2 decimales; el aviso redondea) | redondeo cosmético quitado |
| 125, 128, 130, 132 | `_exp_imp` con `unitario_contrato` (`and/or`, `is None`, `* → //`) | `agree_importe` sin test (código previo tocado al renombrar) | test parametrizado de ✓/⚠ contra el precio del contrato |

No queda ningún superviviente ni equivalente sin demostrar (RM5 no aplica: 0 equivalentes en la campaña válida).

## 9. MANUAL T13 (humano, pipeline LOCAL; nada contra Azure)

Requisito: rama fusionada en `dev` (o el worktree) y el pipeline local arrancado; sv6 y sv4 ponen `bloqueada` al
arrancar (DDL de sv6 y sentencia defensiva de sv4). Solo lecturas en BBDD. PowerShell:
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes
.\infra\local\arrancar_local.ps1
# Navegador: http://localhost:8004 -> un albarán con dos filas Contrato (8 y 10 ud).
#  1) Cantidad 6 en la primera -> «Guardar» (queda en solo lectura con «Desbloquear»); 7 en la segunda -> «Guardar».
#  2) «Traer líneas contrato» -> marcar una -> poner 5 -> «Incorporar».
#  3) «Guardar y aprobar» (si la suma no cuadra con lo leído, confirma el aviso).
$doc = '<ID del documento>'
psql -h localhost -U <usuario_local> -d albaranes -c "SELECT lv.id, lv.cantidad_albaran, lv.cantidad_convertida, lv.importe_calculado, lv.bloqueada FROM albaran_line_valuations lv JOIN albaran_valuations v ON v.id = lv.valuation_id WHERE v.document_id = '$doc' ORDER BY lv.id;"
psql -h localhost -U <usuario_local> -d albaranes -c "SELECT v.total_valorado, m.approved FROM albaran_valuations v JOIN albaran_documents_merge m ON m.id = v.document_id WHERE v.document_id = '$doc';"
#  4) Recargar la ficha: sale «Aprobado · solo lectura» (sin inputs). «Desaprobar para editar» vuelve a la ficha editable.
```
Criterio: filas con 6, 7 y 5 y `cantidad_convertida` igual a la cantidad; `total_valorado` = suma de
`importe_calculado`; aprobado no editable hasta desaprobar.

## 10. Fuera de alcance y lo que falta

- Fuera (spec): fases 2 y 3 (origen «Contrato», combo de partidas de la obra, «Origen ✎», F6 dividir), X4, X12
  (F-066), datos ya dañados en producción (O2, F-067), conservar lo manual al revalorar (F-058).
- Falta: review de la fase 1 (T14), MANUAL T13, fusionar en `dev` y repetir `bash harness/init.sh` en el árbol
  principal, despliegue **sv6 → sv4** (humano) **antes** de pasar F-053 a real. Para el líder: confirmar con el humano
  D1, D3, D8 y D9 (y P10–P13 de la spec).

## 11. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv4 **1015 passed** (de ellos 212 de F-065: cabecera 55, fila 75, bloqueo 30, aprobar 33, js 19, según `pytest --co`); sv6 295 passed (6 nuevos); sv9 526 passed (4 nuevos); raíz 1083 passed |
| Cobertura de las líneas cambiadas | `PUERTA COBERTURA: 100.0% de 309 líneas cambiadas cubiertas (309/309, umbral 80%, nivel critico)` |
| Mutación | `progress/mutacion_F-065_fase1.md`: **131 generados, 131 muertos, 0 supervivientes**, 0 timeouts, 0 sin veredicto, campaña completa, **4 workers**, 1693,2 s, media 12,9 s/mutante (51,6 s × 4), base sv4 84,5–89,4 s / sv6 8,6 s, SHA `d4fe841` |
| Tiempo de la suite | sv4 49,7 s (75 s con coverage en `init.sh`); sv6 6,8 s; sv9 27,6 s; raíz 157 s |
