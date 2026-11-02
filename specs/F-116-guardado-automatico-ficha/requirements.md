<!-- specs/F-116-guardado-automatico-ficha/requirements.md -->
# F-116 · Guardado automático de la ficha al salir de cada campo, sin bloquear la línea · Requisitos (v1)

Servicio: **sv4** (`albaranes-front`) únicamente; sv6 solo un test (R19). Sin DDL, sin colas, sin comun.
Rigor `estandar`. Ficha en `harness/features.json`. Origen: el humano, 2026-11-01: «lo que quiero simplemente es
que al salir de cada celda guarde lo escrito, pero no que bloquee. son 2 comportamientos independientes. los
botones de guardar y guardar todos siguen igual». Lo que hay hoy, leído en código: `design.md` §1.

## Glosario
- **Ficha editable**: la de F-108 (vista merge, albarán sin aprobar). En las demás no cambia nada.
- **Campo de cabecera**: `#fecha`, `#numero_albaran`, `#forma_pago` y `#review_notes`. Son los únicos de la
  cabecera que se escriben a mano: proveedor, CIF, obra, nombre y dirección de obra son `readonly` y se cambian
  con sus combos, que ya guardan solos (PUT y recarga), igual que el contrato. Esos no cambian.
- **Celda**: cada `input.js-cedit` de una `tr.concilia-editable` (partida, descripción, cantidad, unidad,
  precio, importe, dto, código externo).
- **Lo guardado** de un campo: el último valor que el servidor confirmó (al cargar, el pintado). De una celda,
  su `defaultValue`; de un campo de cabecera, `data-guardado`.
- **Bloquear**: lo de hoy (design §1.1): `albaran_line_valuations.bloqueada = TRUE`. Solo lo hacen los botones.
- **Autoguardado**: el guardado que lanza la ficha al salir de un campo, sin botón y sin recargar.
- **Cola de escritura**: la única fila de espera, en serie, de toda petición que escribe desde la ficha.
- **Autoguardada**: fila con un autoguardado que fue bien en esta carga de la ficha.

## A. Cabecera · servidor (endpoint propio, D1)
R1. `PATCH /api/documents/{id}/cabecera` con un subconjunto de `fecha`, `numero_albaran`, `forma_pago` y
`review_notes` debe guardar solo los campos que vienen (ausente = no cambia; `null` o vacío = vaciar): la fecha
con `normalizar_fecha_albaran` (F-108 R1–R3), el número con `normalizar_numero_albaran` (F-108 R8, R9) y los
otros dos recortados. Debe sellar `last_modified_at_utc` y `reviewed_at_utc` (como el PUT) y responder 200 con
`{"ok": true, "document_id", "cabecera": {campo: valor guardado}}`.
R2. El PATCH de R1 no debe cambiar ningún otro campo del documento: ni proveedor, CIF, obra, contrato
seleccionado, aprobación ni motivos, ni relanzar la búsqueda de contratos.
R3. SI la fecha no se admite o el número pasa de 128 caracteres, ENTONCES debe responder 422 con `detail` el
aviso de F-108 (texto, no lista) y no cambiar nada.
R4. SI el albarán está aprobado o tiene un alta bloqueante, ENTONCES 409 con el aviso de hoy
(`_exigir_editable`) sin cambiar nada; SI no existe, 404.
R5. SI el cuerpo trae un campo que no es de R1, ENTONCES 422; SI no trae ninguno, 200 sin escribir.
R6. Cada PATCH de R1 que escribe debe dejar una entrada de deshacer del albarán (acción `cabecera`,
«Editar cabecera · {campos}») que devuelva la cabecera a como estaba.

## B. Cabecera · ficha
R7. CUANDO un Campo de cabecera pierda el foco con un valor admitido distinto de Lo guardado (la fecha comparada
en `AAAA-MM-DD`; los textos, recortados), la ficha debe encolar el PATCH de R1 con solo ese campo, sin recargar.
R8. CUANDO se elija un día en el Calendario (F-108 R15), la ficha debe hacer lo de R7 con `#fecha`.
R9. SI al perder el foco la fecha no se admite, ENTONCES la ficha no debe enviar nada y debe dejar la marca de
F-108 R17, como hoy.
R10. CUANDO el autoguardado de un Campo de cabecera vaya bien, Lo guardado debe pasar a ser lo enviado, el campo
debe llevar la marca discreta `campo-guardado` (`title` «Guardado automáticamente») y `#autoguardado-estado`
(`aria-live="polite"`) debe decir «{Campo} guardado».
R11. SI el autoguardado de un Campo de cabecera falla (D8), ENTONCES lo escrito debe quedarse, el campo debe
llevar `campo-no-guardado` con el motivo en el `title`, `#autoguardado-estado` debe decir «No se pudo guardar
{campo}: {motivo}», sin `alert`; Lo guardado no cambia, así el siguiente R7 lo reintenta.
R12. MIENTRAS la ficha no sea editable, no debe haber autoguardado ni `#autoguardado-estado`.

## C. Líneas · ficha y servidor
R13. CUANDO una Celda pierda el foco y su fila tenga campos distintos de Lo guardado, la ficha debe encolar el
PATCH de fila (`.../conciliacion/campos`) **sin** `?bloquear=1`, con el cuerpo de `_camposCambiados` (todos los
cambiados de la fila, con la regla de importe/precio de F-106 R12), sin recargar.
R14. El cuerpo de R13 debe armarse cuando le toca en la Cola, tras esperar la lista de partidas, y validarse y
enviarse sin nada entre medias (CR4 de F-065): lo validado es lo enviado.
R15. SI la fila tiene una partida cambiada fuera de la lista de la obra, ENTONCES no debe enviarse nada de esa
fila y la partida debe quedar en rojo (F-065 R27 v5), sin `alert` (D5).
R16. CUANDO el PATCH de R13 vaya bien, el `defaultValue` de cada Celda de la fila debe pasar a ser el valor que
tenía al armar el cuerpo (lo tecleado después sigue con cambios); ninguna Celda ni el «Guardar» de la fila deben
quedar desactivados; la fila debe llevar `fila-autoguardada` (`title` «Guardada automáticamente, sin bloquear»)
y `data-autoguardada="1"`; y `#autoguardado-estado` debe decir «Línea {n} guardada».
R17. SI el PATCH de R13 falla, ENTONCES la fila debe quedar en rojo con el motivo (`marcarFilaNoGuardada`),
nada consolidado y sin `alert`; el siguiente R13 de esa fila o los botones lo reintentan.
R18. Un PATCH de fila sin `?bloquear=1` debe aplicar la fila con el recálculo de F-106 (R5–R12), registrar su
edición (F-106 R20, así sale «✋» al recargar) y su deshacer «Editar línea», y dejar `bloqueada = FALSE` sin
`bloqueada` en la edición. (Ya es así; un test lo fija.)
R19. Una fila con edición y sin bloquear debe conservarse al revalorar (sv6, F-106 R23–R27, sin cambios en sv6):
un test de sv6, nuevo o existente y citado, lo fija con una edición sin `bloqueada`.
R20. Enter en una Celda debe seguir siendo el «Guardar» de la fila (guarda y bloquea), como hoy.

## D. Los botones siguen igual
R21. «Guardar» de la fila debe seguir mandando lo pendiente con `?bloquear=1` (también vacío) y recargar.
R22. DONDE D2 = a, «Guardar todas», «Guardar» y «Guardar y aprobar» deben mandar con `?bloquear=1` las filas con
cambios pendientes y las Autoguardadas sin bloquear, en el orden de la tabla y con lo pendiente como cuerpo
(`{}` si no queda nada); «No hay cambios en las líneas» solo si no hay ninguna de las dos.
R23. Los botones de R21–R22, «Guardar y aprobar» incluido, deben empezar a enviar solo cuando la Cola esté
vacía (F-077 y F-108 R18 siguen igual).

## E. Cola de escritura y carreras (D3)
R24. Toda petición PUT, POST, PATCH o DELETE de la ficha (autoguardados, botones, combos, contrato, valorar,
almacén, dividir, traer líneas, borrar, producto, desbloquear, deshacer…) debe pasar por la Cola y empezar solo
cuando termine la anterior, en el orden en que se pidió. Los GET no esperan.
R25. El autoguardado que provoca una pérdida de foco debe entrar en la Cola en el mismo tick del `blur`, antes
de que corra el `click` que la provocó (p. ej. «Guardar y aprobar» con el cursor en la fecha).
R26. SI un autoguardado responde 409 (aprobado, alta, línea bloqueada, «La valoración ha cambiado»), ENTONCES
debe marcarse con ese aviso (R11, R17) y no reintentarse solo.
R27. DONDE D6 = a, MIENTRAS haya peticiones en la Cola sin terminar, salir o recargar la página debe pedir la
confirmación nativa del navegador (`beforeunload`).

## F. Deshacer (D7)
R28. Cada autoguardado que escribe debe ser una entrada del «Deshacer» del albarán (widget global, etiqueta
«Cabecera» o «Línea»), y el widget debe refrescarse tras cada autoguardado que va bien. Deshacer pasa por la
Cola (R24) y recarga, como hoy. El «Deshacer» local (`#undo-btn`, que no actúa en filas editables) no cambia.

## G. Lo que no cambia
R29. El PUT `/api/documents/{id}` y sus vías (F-108 §1.2), los combos de proveedor y obra, el contrato, el
listado y las vistas crudas no cambian de comportamiento.
R30. Los tests de F-065, F-077, F-106 y F-108 siguen en verde sin relajar aserciones, salvo los declarados:
`test_f077_r12_una_sola_peticion_patch_de_fila` (la URL deja de llevar `?bloquear=1` fijo: pasa a afirmar que
`enviarFila` es la única que construye `conciliacion/campos`) y `test_f106_r12_las_tres_vias...` (3 ⇒ 4 vías).

## H. Documentación y verificación
R31. `docs/ARCHITECTURE.md` (regla 20, «Guardar = bloquear»), `services/albaranes-front/sv4.md` (endpoint
nuevo y autoguardado) y `azure-apps/albaranes.md` (viñeta de `bloqueada`: autoguardar no bloquea) lo recogen.
R32. Verificación MANUAL del líder en Chrome y Edge con sv4 local (design §7); en producción, solo lectura.
