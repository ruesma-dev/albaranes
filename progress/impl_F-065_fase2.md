<!-- progress/impl_F-065_fase2.md -->
# F-065 · fase 2 (T15–T18) · informe del implementer

Rama `feature/F-065-lineas-editadas-y-reparto` (worktree `../albaranes-F-065`), con `dev` fusionado (`8c180b0`, fast
forward: la fase 1 aprobada y desplegada). Rigor `critico`. Servicio: **solo sv4** (sin DDL). Despliegue: **sv4**.
Alcance: R24–R28 más las decisiones del humano del 2026-10-11 sobre la review de la fase 1 (O1, O2 + almacén, O3, O5,
O7).

## 1. Commits

`14d8b99` T13/T14 marcadas (MANUAL de la fase 1 OK, review aprobada, desplegada) · `02d3524` T15 RED · `7cb686c` T16
dominio y repositorio · `ccf5643` T17 front, docs y `current.md` · `488b432` T18 tests de bordes · `db31771` T18
mutación, inventario e informe · el commit de este informe.

## 2. Qué cambió

- **Dominio** (`review_models.py`): `cambia_origen(es_contrato, partida_casada, cambios)` (R25/R26, pura: Contrato y
  partida no vacía distinta de la de su línea, o precio, o unidad ⇒ Nueva; vaciar o la de su línea, no; lo demás,
  nunca). `LineasIncompletasError` gana `huerfanas` y su aviso «Hay N líneas sin línea de contrato ni Nueva que la
  ficha no enseña: revalora el albarán» (O2), que se suma al de R20 si hay de las dos.
- **Repositorio** (`review_repository.py`): `update_line_conciliacion` decide el origen con `cambia_origen` (el
  comportamiento ya era ese desde F-051: ahora vive en una función probada). `set_line_conciliacion` reescrito (R28):
  `contract_line` copia de la línea elegida la **partida**, la **unidad** y el **precio** (o `precio_unitario` si
  viene), quita el override de descripción y recalcula el importe; `nueva` crea la derivada con los **valores actuales**
  de la fila (partida final, descripción, unidad y precio que pinta la ficha; antes copiaba la blanca) y solo recalcula
  el importe si el precio cambia. O3: reapuntar, borrar y casar una blanca usan `_recalcular_total_in_session` (ROUND).
  O2: `_exigir_lineas_completas` cuenta las filas sin línea de contrato ni derivada (en los dos aprobar); una fila en
  almacén es una fila normal y nunca bloquea. O5: `set_approved(True)` sobre un aprobado devuelve `False` sin escribir.
- **Front** (`static/app.js`): combo de partida nuevo (`attachPartidaCombo` + puras `partidasDeRespuesta`,
  `opcionesPartida`, `partidaValida`, `siguienteActivo`; `cargarPartidasObra` = una carga por ficha de
  `/api/sigrid/partidas?obra=`): «Almacén (sin partida)» primero (sigue el POST de F-051), partidas hoja de la obra
  filtradas por código y descripción agregada, flechas/Enter/Esc, solo valores de la lista (al salir con otro texto
  vuelve al de antes), obra sin partidas ⇒ solo «Almacén», `ok: false` o red caída ⇒ solo «Almacén» + «No se pudieron
  cargar las partidas». Elegir una partida solo la escribe y marca la fila (viaja al «Guardar», R8/R13); ya no
  reapunta. Se registra ANTES que `wireConciliaEdit` para que Enter con el panel abierto elija y no guarde. Fuera:
  `attachInputCombo`/`loadPartidas`/`PARTIDAS_FALLBACK` (código muerto), `attachContratoLineCombo`,
  `wireConceptoCombos`, `_contratoLineItems`, `_setRowField` y `ITEM_ALMACEN` (concepto = texto, R28), `cambiaIdentidad`
  y el `confirm` «pasará a NUEVA» (R25). O1: `handleRefetchOnly` llama a `confirmarRevalorar()` primero.
- **Plantilla**: «Contrato ✎»/«Contrato» y `data-sort-value="Contrato"` (R24); fuera `data-partida-casada` y el JSON
  `partidas-json` de las partidas del contrato; concepto sin `js-concepto-combo`; «➕ Nueva — con los valores actuales
  de la fila» en «Origen ✎»; textos de «Guardar» al día.
- **Docs**: `docs/ARCHITECTURE.md` regla 20 (origen Contrato/Nueva, combo de la obra, «Origen ✎», «Solo volver a
  buscar», almacén y huérfanas). `azure-apps/albaranes.md` ya documentaba que el selector de partidas de sv4 usa la
  consulta de partidas de la obra (§F-049): sin cambio de lo que se expone o consume. `progress/current.md`: podado el
  bloque viejo de F-053 `in_progress` (O7; lo que tenía de propio se pasó al bloque `blocked`).
- **Tests**: nuevo `test_f065_f2_origen.py` (49). Adaptados con su motivo: F-051 (Almacén primero ahora en
  `opcionesPartida`; el aviso de Nueva y `data-partida-casada` ya no existen), F-053 (`f053_sv4_bbdd`: las sin vincular
  llevan su derivada, como las deja sv6, porque una fila sin ninguna ya no se aprueba; t25: una segunda valoración con
  una fila huérfana sigue siendo «valorado» por R37, pero aprobar la rechaza, como sv9 que lee todas las filas),
  F-065 fase 1 (la fila sin línea cuenta como huérfana).

## 3. Decisiones (a confirmar en la review)

- **E1 · Elegir partida no guarda sola**: escribe la partida y deja la fila con cambios; la guarda (y bloquea) el
  «Guardar» de la fila o «Guardar todas», que mandan solo `codigo_partida` si es lo único que cambió (R27 «solo manda
  `codigo_partida`»). «Almacén» sigue siendo inmediato (POST de F-051), como hasta ahora.
- **E2 · «Origen ✎» → línea de contrato copia también la unidad** (además de partida y precio, R28) y quita el override
  de descripción: la fila «cuadra» con la línea elegida (lo que la ficha ya pintaba, porque la unidad y la descripción
  de una fila Contrato salen de su línea).
- **E3 · Nueva no recalcula el importe si el precio no cambia** (como D3 de la fase 1: no se reetiqueta un declarado).
- **E4 · Obra sin código** ⇒ ni se consulta Sigrid: solo «Almacén», sin aviso (no es un fallo de Sigrid).
- **E5 · O2 cuenta las huérfanas de TODAS las valoraciones del documento** (como sv9 `SQL_LINEAS`), aunque «valorado»
  (R37) mire solo la primera.
- **E6 · O3 sin prueba de comportamiento en SQLite**: SQLite ≥ 3.43 suma con compensación y no reproduce la cola
  binaria; lo vigila el test estructural (las tres escrituras llaman al helper y no hay `SUM(` suelto) y los de
  comportamiento quedan de guarda.

## 4. Fase RED (traza real)

`.venv\Scripts\python -m pytest tests/test_f065_f2_origen.py --tb=line -p no:cacheprovider` sobre `02d3524` ⇒
`29 failed, 13 passed in 5.78s`:
```
test_f065_f2_origen.py:77: ImportError: cannot import name 'cambia_origen' from 'domain.models.review_models'   (×10)
test_f065_f2_origen.py:131: AssertionError: assert 'cambia_origen(' in '    def update_line_conciliacion(...'
test_f065_f2_origen.py:150: AssertionError: assert '01.01' == '01.03'           (R28: reapuntar no traía la partida)
test_f065_f2_origen.py:171: AssertionError: assert {'descripcion... '07.07', ...} == {...}   (R28: Nueva copiaba la blanca)
test_f065_f2_origen.py:190: assert ('Contrato ✎' in '<td class="concilia-td td-origen" data-col="origen" data-sort-value="Sigrid">...
test_f065_f2_origen.py:212: assert 'id="partidas-json"' not in '<!-- templa...'
test_f065_f2_origen.py:330: AssertionError: assert 'pasará a NUEVA' not in '// static/a...'
test_f065_f2_origen.py:337: assert 'function wi...ceptoCombos(' not in '// static/a...'
test_f065_f2_origen.py:348: AssertionError: assert 'confirmarRevalorar()' in 'async function handleRefetchOnly() {\n        '
test_f065_f2_origen.py:371: Failed: DID NOT RAISE LineasIncompletasError        (O2: la huérfana se aprobaba)
test_f065_f2_origen.py:382: TypeError: LineasIncompletasError.__init__() got an unexpected keyword argument 'huerfanas'
test_f065_f2_origen.py:435: AssertionError: set_line_conciliacion                (O3: el total sin el helper)
test_f065_f2_origen.py:449: AssertionError: assert {'albaran_doc...} == {...}    (O5: aprobar un aprobado reescribía)
```
y `ValueError: substring not found` ×6 de las funciones JS que no existían (`partidasDeRespuesta`, `opcionesPartida`,
`partidaValida`, `siguienteActivo`, `attachPartidaCombo`, `cargarPartidasObra`). Los 13 que pasaban son guardas de lo
que ya hacía bien (partida/precio/unidad ⇒ Nueva, R26, almacén aprueba, totales en SQLite).

## 5. Verificación (resultado real)

- Criterios de las tareas: T16 `pytest tests/test_f065_f2_origen.py -k "not js"` (backend) y
  `pytest tests/test_f051_almacen_front.py` en verde; T17 los `js`/plantilla en verde (node v24).
- Suite completa de sv4 (sola): **1061 passed** (91,8 s con coverage dentro de `init.sh`).
- **`bash harness/init.sh`** (tal cual, worktree): sobre `db31771`: raíz `1083 passed`; sv4 `1061 passed`; el resto en verde (caché: sin cambios); **`PUERTA COBERTURA: 100.0% de 33 líneas cambiadas cubiertas (33/33, umbral 80%, nivel critico)`**; rutas sensibles N/A; tamaño dentro de topes; **`ENTORNO LISTO. Puedes trabajar.`** Avisos previos (ruff, F-053 `blocked`, `[ADAPTAR]`). Entorno: la misma *junction* de sv4 de la fase 1. Sin KO de entorno.

## 6. Cobertura y mutación (T18)

- `PUERTA COBERTURA`: `100.0% de 33 líneas cambiadas cubiertas (33/33, umbral 80%, nivel critico)`. La primera medida (93,9 %, 31/33) dejaba sin cubrir la rama de «Nueva con otro precio»;
  la cubren los tests de bordes de T18.
- **Mutación** `python -m harness.mutacion --feature F-065 --salida progress/mutacion_F-065_fase2.md` (alcance:
  `8c180b0..rama`, 2 ficheros, 147 líneas de sv4; el JS y la plantilla no los muta la herramienta: los vigilan los tests
  con node y de render). **`progress/mutacion_F-065_fase2.md`: SHA `488b432`, 29 mutantes, 29 muertos, 0 supervivientes, 0 timeouts, 0 sin veredicto, 695,4 s**, 4 workers, media 24,0 s × 4 = 96 s por mutante frente a una línea base de sv4 de 106,5–107,4 s (coherente, RM2). Una primera pasada sobre el mismo SHA dio lo mismo (29/29, 758,7 s; archivada fuera de git). Después de `488b432` solo entran el informe, el inventario y `tasks.md`.
- Sin supervivientes ni equivalentes: RM5 no aplica.

## 7. MANUAL T19 (humano, pipeline LOCAL; solo lecturas en BBDD)

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes
.\infra\local\arrancar_local.ps1
# http://localhost:8004, un albarán pendiente con filas Contrato y obra con partidas en Sigrid:
#  1) Partida de una fila Contrato: el combo ofrece «Almacén (sin partida)» y las partidas de la OBRA; con flechas y
#     Enter elegir otra (la fila queda con cambios), «Guardar» SIN ningún aviso -> la fila sale «Nueva».
#  2) En otra fila Contrato elegir «Almacén (sin partida)» -> sigue «Contrato», partida vacía.
#  3) Teclear «zzz» en una partida y salir con Tab -> vuelve la partida de antes (no se guarda).
#  4) «Contrato ✎» -> elegir otra línea de contrato -> la fila toma su partida y su precio.
#  5) En un albarán de una obra SIN partidas, el combo solo ofrece «Almacén».
#  6) «Solo volver a buscar» con filas guardadas -> pide «Revalorar descarta N líneas…».
#  7) Pasar TODAS las filas a almacén y «Guardar y aprobar» -> se aprueba.
$vid = <id de la fila>
psql -h localhost -U <usuario_local> -d albaranes -c "SELECT lv.matched_contrato_line_id, lv.derived_contrato_line_id, lv.codigo_partida_final, lv.precio_unitario_final FROM albaran_line_valuations lv WHERE lv.id = $vid;"
psql -h localhost -U <usuario_local> -d albaranes -c "SELECT id, codigo_partida, origen FROM contrato_lines_derived WHERE id = (SELECT derived_contrato_line_id FROM albaran_line_valuations WHERE id = $vid);"
```
Criterio: tras 1), derivada `manual_override` con la partida elegida y `matched` nulo; tras 2), la misma línea de
contrato y partida final nula; tras 4), `matched` = la línea elegida y su partida/precio; 5) y 6) como se describe; 7)
aprobado.

## 8. Fuera de alcance y lo que falta

- Fuera: fase 3 (F6 dividir), X4, X12 (F-066), conservar lo manual al revalorar (F-058). La consulta de partidas sigue
  siendo la de sv4 (`sigrid_lookup_client.py` sin tocar; F-049 la moverá a comun).
- Falta: MANUAL T19 (humano), review de la fase 2 (T20), fusionar en `dev`, `init.sh` en el árbol principal y
  desplegar **solo sv4**. Para el líder: confirmar E1–E5 con el humano.

## 9. Evidencias

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | sv4 **1059 passed** (49 nuevos en `test_f065_f2_origen.py`); raíz 1083 passed; sv6, sv9, comun, sv1–sv3, sv5 sin cambios (caché verde) |
| Cobertura de las líneas cambiadas | `100.0% de 33 líneas cambiadas cubiertas (33/33, umbral 80%, nivel critico)` |
| Mutación | `progress/mutacion_F-065_fase2.md`: **29 generados, 29 muertos, 0 supervivientes**, 0 timeouts, campaña completa, **4 workers**, 695,4 s, media 24,0 s/mutante, base sv4 ≈ 107 s, SHA `488b432` |
| Tiempo de la suite | sv4 91,8 s con coverage (≈ 60 s sin); raíz 168,7 s |
