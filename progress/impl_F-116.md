<!-- progress/impl_F-116.md -->
# F-116 · Informe del implementer

Guardado automático de la ficha de sv4 al salir de cada campo, **sin bloquear la
línea**. Rama `feature/F-116-guardado-automatico-ficha` (worktree
`../albaranes-F-116`), sobre `dev` `108cabc`. Rigor `estandar`. PARADA 1 cerrada
por el humano el 2026-11-01 (D1–D8 = a). Implementer, 2026-11-01/02.

## 1. Qué cambió (para el humano)

- **Cabecera**: fecha, número de albarán, forma de pago y notas de revisión se
  guardan solas al salir del campo (y la fecha también al elegirla en el
  calendario), sin recargar. Endpoint nuevo `PATCH /api/documents/{id}/cabecera`
  que escribe SOLO el campo que se dejó (no el PUT entero: no pisa el contrato,
  la dirección ni nada de lo que sv3 escriba después de abrir la ficha). Fecha
  no válida: no se envía y queda en rojo, como en F-108.
- **Líneas**: al salir de CADA celda de una fila editable se guarda lo escrito de
  la fila (el PATCH de siempre sin `?bloquear=1`: recálculo de F-106, edición
  «✋» y «Deshacer»), **sin bloquear**: la fila sigue editable y queda con una
  marca discreta. Partida fuera de la lista: no se guarda nada de esa fila, en rojo.
- **Botones, igual**: «Guardar» de la fila, «Guardar todas», «Guardar» y «Guardar
  y aprobar» siguen guardando y bloqueando; además bloquean las filas
  autoguardadas en esa carga (D2 = a), con cuerpo `{}` si ya no queda nada. Enter
  en una celda sigue siendo «Guardar» de la fila.
- **Sin carreras**: toda escritura de la ficha va por una cola en serie (se
  envuelve `fetch`); los botones esperan a los autoguardados en curso; salir de la
  página con escrituras sin terminar pide la confirmación del navegador.
- **Fallos sin `alert`**: marca en el campo o la fila (motivo en el `title`) y el
  texto de `#autoguardado-estado`; el siguiente `blur` con cambios o un botón
  reintentan. Un 409 no se reintenta solo.
- **Deshacer global**: una entrada por autoguardado (etiqueta «Cabecera» o
  «Línea»); el widget se refresca tras cada autoguardado que va bien.

## 2. Ficheros tocados

| Fichero | Qué |
|---|---|
| `services/albaranes-front/domain/models/review_models.py` | `CabeceraEditBody` (4 campos, `extra="forbid"`, `campos()`) |
| `.../infrastructure/database/review_repository.py` | `update_cabecera_campos` (+ `CAMPOS_CABECERA_AUTOGUARDADO`) |
| `.../application/services/review_service.py` | `editar_cabecera` con su deshacer (`ETIQUETAS_CABECERA`) |
| `.../interface_adapters/web/app.py` | `PATCH /api/documents/{id}/cabecera` |
| `.../static/app.js` | Cola (`_estadoCola`, `fetchRed`, `encolar`, `hayEscriturasEnCurso`, `instalarColaEscrituras`); cabecera (`avisarAutoguardado`, `etiquetaCampoCabecera`, `valorCabeceraParaGuardar`, `valorGuardadoCabecera`, `autoguardarCampoCabecera`, `wireAutoguardadoCabecera`); filas (`enviarFila(vid, cuerpo, opciones)`, `valoresDeFila`, `consolidarSinBloquear`, `numeroDeLinea`, `autoguardarFila`, `wireAutoguardadoFilas`, `filasParaGuardar`); botones esperan a la Cola; deshacer global (`cabecera`, evento `autoguardado`) |
| `.../templates/document_detail.html` | `#autoguardado-estado` (`aria-live="polite"`, solo editable) y `data-guardado` en los 4 campos |
| `.../static/styles.css` | `.campo-guardado`, `.campo-no-guardado`, `tr.fila-autoguardada`, `.autoguardado-estado` |
| Tests nuevos | `tests/test_f116_cabecera_api.py` (46), `test_f116_lineas_api.py` (6), `test_f116_ficha.py` (12), `test_f116_autoguardado_js.py` (51) |
| Tests viejos ajustados | `test_f077_guardar_y_aprobar_js.py`, `test_f106_js.py`, `test_f098_combo_js.py`, `test_f065_f3bis_front.py` (§3) |
| Docs | `docs/ARCHITECTURE.md` (regla 20), `services/albaranes-front/sv4.md` (§4.2 y §11); `azure-apps/albaranes.md` (commit `ec9ed4d` en `azure-apps`, local, sin push) |
| Arnés | `harness/features.json` (F-116 `in_progress`), `BACKLOG.md` (regenerado), `progress/current.md`, `tasks.md` |

Commits (uno por tarea): `ebdb90d` T1, `8aca3a0` T2, `472728a` T3, `2af5755` T4,
`c60bbc2` T5, `f2bc024` T6, `3925b38` T7, `3926ac4` T8, `81e9d52` T9, `b7c07f3`
T10, T11 (marca), `24479a0` T12, `aa59535` (test de cobertura), `0245fd6`
(BACKLOG/current).

## 3. Decisiones de diseño y desviaciones (justificadas)

1. **`test_f098_r21` no estaba en la lista de R30.** Cuenta lo mismo que el
   declarado `test_f106_r12` (`_camposCambiados(tr, lista.items)` 3 ⇒ 4: la
   cuarta vía es el autoguardado). Se cambió el 3 por un 4 y se **añadió** que
   `autoguardarFila` también arma el cuerpo con la lista. No se relaja nada; es la
   misma cuenta que R30 ya autoriza. Si el reviewer o el líder no lo aceptan, la
   alternativa sería reescribir la spec, no el código.
2. **Listas de funciones extraídas de tests viejos de JS** (como hizo F-108): los
   tests que sacan `guardarFilasPendientes` o `wireConciliaEdit` de `app.js` y las
   ejecutan con node necesitan las funciones nuevas a las que llaman. Se
   añadieron `_estadoCola`, `encolar` y `filasParaGuardar` a `_FUNCIONES` de
   `test_f077_guardar_y_aprobar_js.py` (la reutiliza también
   `test_f108_fecha_js.py`) y a dos listas de `test_f065_f3bis_front.py`. Ninguna
   aserción cambia.
3. **El `blur` de las celdas va en `wireAutoguardadoFilas()`**, llamada justo
   después de `wireConciliaEdit()` (design §4.6 decía «en `wireConciliaEdit`»).
   Mismo orden de enganche (después de `wirePartidaCombos`, R13) y
   `wireConciliaEdit` no gana dependencias en los tests viejos que la ejecutan.
4. **Cabecera: se compara con lo último ENCOLADO si lo hay** (si no, con
   `data-guardado`). Con la comparación literal de R7 («distinto de Lo
   guardado»), cambiar un campo y volver a dejarlo como estaba mientras el
   primer PATCH sigue en la Cola no enviaba nada y quedaba guardado el valor
   intermedio. Test `test_f116_r11_lo_que_se_vuelve_a_dejar_como_estaba_tambien_viaja`.
5. **`filasParaGuardar(filas, conCambios)`** recibe las de `filasConCambios`: el
   filtro de cambios sigue viviendo en la función compartida (lo afirman
   `test_f065_r8` y `test_f065_r18` sobre el bloque de «Guardar todas»).
6. **«Guardar todas» desactiva el botón y espera a la Cola ANTES de mirar si hay
   filas** (antes miraba primero): si no, con un autoguardado en vuelo diría «No
   hay cambios» o reenviaría lo suyo. Con «No hay cambios» vuelve a activarse.
7. **Una fila bloqueada por `guardarFilasPendientes` pierde `data-autoguardada`**
   (en la propia `guardarFilasPendientes`, `consolidarFila` no se toca): así un
   reintento tras un fallo posterior no la reenvía (daría 409; F-077 R5).
8. **Evento `autoguardado` con `new Event(...)`**, no `CustomEvent` (no lleva
   datos; funciona igual en el navegador y en el DOM falso de los tests).
9. **La Cola envuelve `globalThis.fetch`** (es `window` en el navegador; en los
   tests de node el `window` falso no es el global). El `fetch` real se guarda
   con `bind` (si no, llamarlo como método de otro objeto da «Illegal invocation»).
10. **Avisos literales de la spec**: «Fecha guardado» / «Línea 2 guardada»; el de
    fallo pone la etiqueta en minúsculas («No se pudo guardar número albarán: …»).
    Las etiquetas son las de la ficha.
11. **R19 se cita, no se añade**: `services/albaran-valoracion-persist/tests/test_f106_reaplicar.py::
    test_f106_r25_r32c_cantidad_editada_sobrevive_con_el_precio_nuevo` edita solo
    `{"cantidad"}` (sin `bloqueada`) sobre una fila sin bloquear y la revalora: la
    edición se conserva. sv6 sin cambios (26 passed en ese fichero).
12. **R18 ya era así**: sus 6 tests pasan desde el primer momento (fijan lo que
    hay, design §1.1); no tienen fase RED posible.

## 4. Fase RED (trazas reales, test escrito antes que el código)

**T1–T3 (cabecera, servidor)** — `cd services/albaranes-front; .venv/Scripts/python.exe -m pytest tests/test_f116_cabecera_api.py -q --tb=line -p no:warnings`:
```
27 tests\test_f116_cabecera_api.py:44: AttributeError: 'AlbaranReviewRepository' object has no attribute 'update_cabecera_campos'
 4 E   AttributeError: 'ReviewService' object has no attribute 'editar_cabecera'
 3 E   ImportError: cannot import name 'CabeceraEditBody' from 'domain.models.review_models' (domain\models\review_models.py)
 8 E   AssertionError: {"detail":"Not Found"}
44 failed, 1 passed in 6.12s
```
(el que pasaba: `test_f116_r4_ruta_no_existe_404`, que un 404 de ruta inexistente
cumple por casualidad; tras T3 da el 404 del `KeyError`). Verde: 45 passed (46
con el test de cobertura).

**T5 (plantilla y CSS)** — `... -m pytest tests/test_f116_ficha.py -q --tb=line -p no:warnings`:
```
tests\test_f116_ficha.py:46: AssertionError: no está #autoguardado-estado
tests\test_f116_ficha.py:108: AssertionError: .campo-guardado
tests\test_f116_ficha.py:108: AssertionError: .campo-no-guardado
tests\test_f116_ficha.py:108: AssertionError: tr.fila-autoguardada
10 failed, 2 passed in 2.97s
```
(los 2 que pasaban son los de R12 «sin nada en solo lectura», ciertos de partida). Verde: 12 passed.

**T6–T10 (JS)** — `... -m pytest tests/test_f116_autoguardado_js.py -q --tb=line -p no:warnings`:
```
42 tests\test_f116_autoguardado_js.py:182: AssertionError: faltan en app.js: ['_estadoCola', 'fetchRed', 'encolar', 'hayEscriturasEnCurso', 'instalarColaEscrituras', 'avisarAutoguardado', 'etiquetaCampoCabecera', 'valorCabeceraParaGuardar', 'valorGuardadoCabecera', 'au...
 4 E   ValueError: substring not found
 1 E   AssertionError: assert ['Cambio', 'Línea'] == ['Cabecera', 'Línea']
50 failed in 17.53s
```
Después se partió la lista de funciones en grupos (Cola / cabecera / todo) para
poder verificar cada tarea por separado. Tres tests eran incorrectos y se
corrigieron (no el código): el GET sale antes que la 1.ª escritura encolada (lo
dice R24: «los GET no esperan»); R15 leía la marca antes de que corriera la Cola;
el recuento de la URL contaba también un comentario. Verde: 51 passed.

## 5. Verificación (resultados reales)

- Por tarea: la verificación de `tasks.md` de cada una, en verde antes de su commit.
- T8/T9, suites viejas de JS: `test_f077_guardar_y_aprobar_js.py test_f106_js.py
  test_f065_f1_js.py test_f065_f3bis_front.py test_f098_combo_js.py
  test_f108_fecha_js.py test_f116_autoguardado_js.py` ⇒ **225 passed**.
- T11, suite completa de sv4 (`pytest tests`, con `PYTHONPATH` y
  `ARNES_SIN_CACHE=1`): **2500 passed in 190.83s**.
- sv6 `tests/test_f106_reaplicar.py`: **26 passed** (R19, sin cambios en sv6).
- **T15 `bash harness/init.sh`** (con `PYTHONPATH=…\albaranes-F-116\services\albaranes-comun`
  y `ARNES_SIN_CACHE=1`): **salida 0, «ENTORNO LISTO»**. sv4 2500 passed (412.64s),
  resto de servicios en verde (1919, 236, 496, 1608, 125, 506+1 skipped, 1073, 1342
  passed), `PUERTA COBERTURA: 97.9% de 48 líneas cambiadas (47/48, umbral 80%)`,
  `PUERTA TAMAÑO` dentro de topes. La línea sin cubrir era la defensa del
  repositorio ante campos que no son de la cabecera: test añadido en `aa59535`
  (`test_f116_r2_el_repositorio_rechaza_otros_campos_sin_escribir`). Ver §7 sobre
  la pasada final.

## 6. Fuera de alcance / lo que falta

- **MANUAL, sin marcar** (líder y humano): **T13** (M1, Chrome y Edge con sv4 local,
  design §7: los 10 pasos, en especial el 7 — cursor en la fecha y clic directo en
  «Guardar y aprobar» ⇒ en Red el PATCH de cabecera termina antes del PUT) y **T14**
  (el humano despliega sv4 sola: `cd infra; Set-DeployTag; .\deploy.ps1 -Only sv4`;
  el líder hace M2 de solo lectura).
- No repinta «✋», el paso Contrato ⇒ Nueva ni el total tras autoguardar (D4 = a):
  se ven al recargar.
- El autoguardado no quita el aviso «revisa la cantidad» (salvo que cambie la
  cantidad): eso sigue siendo del «Guardar» (design §1.2).
- Dos pestañas editando el mismo albarán: fuera (ficha de la feature).
- La campaña de mutación no cubre `app.js` (la herramienta solo muta Python): el
  JS lo cubren los 51 tests de node, ejecutados contra el DOM falso.
- *Junction* `.venv` de sv4 en el worktree (a la del árbol principal): quitarla con
  `cmd /c rmdir services\albaranes-front\.venv` antes de `git worktree remove`.

## 7. Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados (sv4, suite completa) | **2501 passed** en la pasada final (2500 en T11), 0 failed (190.83 s suelta; 412.64 s dentro de `init.sh`, con cobertura) |
| Tests nuevos de F-116 | 115 (46 + 6 + 12 + 51), todos en verde |
| Cobertura de las líneas cambiadas | **100.0 %** (48/48, pasada final); 97.9 % (47/48) en la primera, la que faltaba tiene test desde `aa59535` |
| Mutantes generados / supervivientes | **7 generados, 7 muertos, 0 supervivientes, 0 timeouts** (`python -m harness.mutacion --feature F-116`, HEAD `0245fd6`, 4 workers, 1020.9 s; nivel `estandar` con tope 20: hubo 7, campaña completa). Detalle en `progress/mutacion_F-116.md` |
| Análisis de supervivientes | No hay |
| Tiempo de la suite de sv4 | 190.83 s (suelta) |
| `bash harness/init.sh` | salida 0, «ENTORNO LISTO» (pasada sobre `24479a0`; la pasada final sobre el commit del informe, abajo) |

Pasada final de `init.sh` (tras commitear este informe y la mutación): ver la
línea siguiente, la escribe el implementer con el resultado real.

- Pasada final (sobre `5ff3fa9`): **salida 0, «ENTORNO LISTO»**. sv4 2501 passed (257.69 s), resto en verde (1919, 236, 496, 1608, 125, 506+1 skipped, 1073, 1342), `PUERTA COBERTURA: 100.0% de 48 líneas (48/48)`, `PUERTA TAMAÑO` (impl 190/220). Una pasada anterior salió en rojo solo por `test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`: faltaba la fila de `progress/mutacion_F-116.md` en `progress/inventario_mutacion_F-039.md` (añadida en `5ff3fa9`).

## 8. T13 · M1 en Chrome con sv4 local (líder, 2026-11-02)

sv4 de esta rama en local (BBDD local, Azurite), Chrome, ficha pendiente `e00f581b…` (3 líneas, la 3.ª sin bloquear).
Edge no está al alcance del líder: queda para el humano si quiere repetirlo.

| Paso | Resultado |
|---|---|
| 1 | `28-10-26` + Tab ⇒ `28/10/2026`, `campo-guardado`, «Fecha guardado»; BBDD `2026-10-28`; sigue tras recargar |
| 2 | No probado a mano (el calendario nativo no se maneja desde la extensión); lo cubre `test_f116_r8_elegir_en_el_calendario_guarda` |
| 3 | `31/02/2026` + Tab ⇒ `campo-no-valido`, nada enviado (`data-guardado` y BBDD siguen en `2026-10-28`) |
| 4 | Número `230.285-P`, forma de pago y notas + Tab ⇒ guardados (BBDD comprobada) |
| 5 | Cantidad 78 ⇒ 80 + Tab ⇒ importe 136, `fila-autoguardada`, sigue editable; al recargar 80,0 / 136,00, «✋», sin bloquear |
| 6 | Partida `ZZ99.INVENTADA` + Tab ⇒ vuelve a la de antes (almacén), sin marca ni PATCH |
| 7 | Fecha cambiada con el cursor dentro + clic en «Guardar y aprobar» ⇒ en Red, PATCH `/cabecera` 200 **antes** del PUT; BBDD con la fecha nueva. El PUT dio 409 por una validación previa ajena («Líneas sin descripción: 1, 2, 3», datos del documento local) |
| 8 | Autoguardado (PATCH sin `?bloquear=1`) y «Guardar todas» ⇒ PATCH `?bloquear=1` de esa fila; tras recargar, bloqueada |
| 9 | Forma de pago autoguardada ⇒ entrada «Editar cabecera · Forma de pago» en el deshacer; «Deshacer» la devuelve |
| 10 | No probado: sin sv6 local. Lo cubre `test_f106_r25_r32c_…` de sv6 (R19, verificado por el reviewer) |

Observación menor (no bloquea): con la fecha en rojo (paso 3) el `title` del campo sigue diciendo «Guardado
automáticamente», del guardado anterior. Al probar se tocó por error la unidad de la línea (KG ⇒ 80 ⇒ KG, ambos
autoguardados): BBDD local solamente.
