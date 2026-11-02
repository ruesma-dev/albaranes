<!-- specs/F-116-guardado-automatico-ficha/design.md -->
# F-116 · Diseño técnico (v1)

Solo **sv4** (`services/albaranes-front`); en sv6, como mucho un test (R19). Sin DDL, sin colas, sin comun, sin
sigrid-api. Límite de servicio: es edición humana de la ficha, responsabilidad de sv4. Decisiones en §8.

## 1. Lo que hay hoy (leído en código, 2026-11-01, rama sobre `dev` `108cabc`)

1.1 **Qué es «bloquear».** `?bloquear=1` en `PATCH .../lines/{vid}/conciliacion/campos`
(`app.py:1572`, `bloquear: bool = Query(default=False)`) hace, en la MISMA transacción que aplica los campos
(`review_repository.update_line_conciliacion`, ≈2193): `bloqueada = TRUE`; quita el aviso «revisa la
cantidad» (`front_unidad_cambiada_revisa_cantidad`) aunque la cantidad no cambie; y añade `bloqueada` a la
edición. Sin `bloquear`, el mismo PATCH ya existe y funciona: aplica, recalcula (F-106), escribe
`edicion_manual_json` con los campos cambiados (`_registrar_edicion_in_session`, ≈2564) y su deshacer
«Editar línea» (`review_service.update_line_conciliacion`, ≈490). Una fila `bloqueada`: la plantilla la pinta
sin celdas editables y con «Desbloquear»; el servidor responde 409 «Línea guardada» a editarla, reapuntarla,
almacén, producto o borrado (`_exigir_linea_desbloqueada`); los masivos se la saltan.

1.2 **¿Un guardado sin bloquear sobrevive a revalorar? Sí.** sv6 (`sqlalchemy_valuation_repository.py`,
`_ediciones_previas` ≈371 y `_reaplicar` ≈519) reaplica toda fila con `edicion_manual_json`, bloqueada o no;
`bloqueada` solo cuenta para las legadas sin edición (`es_fila_manual`). El «✋» (F-106 R29) sale de la edición,
no del bloqueo: una fila autoguardada lo enseña al recargar. Lo que NO hace el autoguardado es quitar el aviso
«revisa la cantidad» (salvo que cambie la cantidad): eso sigue siendo del «Guardar».

1.3 **Cabecera.** Editables a mano: `#fecha`, `#numero_albaran`, `#forma_pago`, `#review_notes`
(`document_detail.html` ≈340–394). Proveedor/CIF y obra/nombre/dirección son `readonly`; se cambian con los
combos, que guardan solos (`choose` ⇒ `sendSave(false)`, PUT con `?buscar_si_cambia=1` y recarga, ≈2404); el
contrato, con `persistSelection` (PUT, ≈3313). Hoy los cuatro campos solo se guardan por un PUT (los botones o,
de paso, cualquiera de esas vías, porque `collectPayload` manda la cabecera entera).

1.4 **El PUT no sirve para autoguardar** (D1). `update_document_y_transicion` (≈4442) escribe TODA la cabecera
con lo que manda el navegador, incluido `selected_contrato_codigo` (del `hidden`) y `obra_direccion`. sv3
escribe la cabecera por su cuenta (auto-selección de contrato, dirección de obra al re-buscar): una ficha
abierta antes, al autoguardar las notas, devolvería el contrato a `null` o vaciaría la dirección. Con un botón
eso ya puede pasar hoy; con un guardado en cada `blur` pasaría a menudo.

1.5 **Botones.** Las tres vías de filas usan `enviarFila` (siempre `?bloquear=1`, ≈1256) y eligen las filas con
`filasConCambios` (cuerpo de `_camposCambiados` no vacío, comparando con `defaultValue`). «Guardar» de la fila
bloquea también sin cambios y recarga; «Guardar todas» solo manda las que tienen cambios; `guardarCabecera`
(≈2869) manda antes las filas con cambios y luego el PUT. Si el autoguardado actualiza `defaultValue`, esas
filas dejan de «tener cambios» y los botones ya no las bloquearían: por eso R22 (D2).

1.6 **Carreras.** Ninguna escritura de la ficha espera a otra: ~22 `fetch` no-GET en el bloque de la ficha
(`app.js` 17–4040) y el deshacer global (≈4104). `blur` ocurre antes del `click` del botón que lo provoca. Muchas
vías recargan al terminar (24 `window.location.reload()`); una recarga con un PATCH en vuelo puede cortarlo.

1.7 **Deshacer.** Dos: el global por albarán (`/api/undo`, `undo_log`, widget `#undo-global-*`, deshace la
última entrada y recarga) y el local `#undo-btn` («cambios no guardados», `_captureState` del `tbody`), que
sale en las filas que NO son `conciliacion-row`: no actúa en filas editables y F-116 no lo toca.

1.8 **Valores no válidos.** Fecha: `parseFechaEs` ⇒ `null` y marca roja en `blur` (F-108 R17). Partida: el
`blur` del combo vuelve al valor de antes si no es de la lista (`volverSiNoVale`); si la lista aún no llegó,
`partidasMalas` la deja en rojo al validar (F-065 R27 v5). Número: `maxlength="128"` y 422 en el servidor.

## 2. Ficheros a crear
- `services/albaranes-front/tests/test_f116_cabecera_api.py` — R1–R6 (repositorio real sobre SQLite,
  `f065_bbdd`, y `build_app` con servicio falso, como `test_f108_guardado.py`).
- `services/albaranes-front/tests/test_f116_lineas_api.py` — R18 (PATCH sin `bloquear` sobre SQLite).
- `services/albaranes-front/tests/test_f116_autoguardado_js.py` — R7–R17, R20–R28 (node + `tests/dom_falso.js`,
  patrón `test_f077_guardar_y_aprobar_js.py`, `con_node`).
- `services/albaranes-front/tests/test_f116_ficha.py` — R10, R12 (render con `render_detalle`).
- Solo si no existe ya un test equivalente (citarlo en el informe): uno en
  `services/albaran-valoracion-persist/tests/test_f106_reaplicar.py` con edición sin `bloqueada` (R19).

## 3. Ficheros a modificar
- `domain/models/review_models.py` — `CabeceraEditBody` (§4.1).
- `infrastructure/database/review_repository.py` — `update_cabecera_campos` (§4.2).
- `application/services/review_service.py` — `editar_cabecera` (§4.3).
- `interface_adapters/web/app.py` — `PATCH /api/documents/{id}/cabecera` (§4.3); los 422/409 de F-108 y F-065
  ya tienen manejador.
- `static/app.js` — cola, autoguardado de cabecera y de filas, `enviarFila` con opciones, `filasParaGuardar`,
  evento para el widget de deshacer (§4.4–§4.6).
- `templates/document_detail.html` — `#autoguardado-estado` (solo editable) junto a los botones de cabecera;
  `data-guardado` en los cuatro Campos de cabecera (la fecha, en ISO).
- `static/styles.css` — `.campo-guardado`, `.campo-no-guardado`, `.fila-autoguardada` (discretas: borde o fondo
  tenue; la roja de `fila-no-guardada` ya existe).
- Tests declarados en R30: `tests/test_f077_guardar_y_aprobar_js.py` (R12) y `tests/test_f106_js.py` (R12).
- `docs/ARCHITECTURE.md` (regla 20), `services/albaranes-front/sv4.md`, `azure-apps/albaranes.md` (R31).

## 4. Clases y funciones

### 4.1 `CabeceraEditBody` (domain/models, junto a `ConciliacionEditBody`)
```python
class CabeceraEditBody(BaseModel):
    model_config = ConfigDict(extra="forbid")          # R5: campo desconocido ⇒ 422
    fecha: str | None = None
    numero_albaran: str | None = None
    forma_pago: str | None = None
    review_notes: str | None = None
    def campos(self) -> dict[str, str | None]: ...      # solo model_fields_set (ausente = no cambia)
```
Sin validador de fecha aquí (daría un 422 en lista; F-108 §6): la valida el repositorio.

### 4.2 `ReviewRepository.update_cabecera_campos(*, document_id, campos) -> dict[str, str | None]`
Una sesión: `_exigir_editable(session, document_id)` (alta y aprobado, R4), `session.get(...)` (`KeyError` si no
existe), normalizar ANTES de asignar nada (`normalizar_fecha_albaran`, `normalizar_numero_albaran`,
`_clean_text`; un error sale sin `commit`, R3), asignar solo las claves de `campos`, sellar
`last_modified_at_utc` y `reviewed_at_utc`, `commit`. Devuelve los valores guardados de esas claves. Nada de
`_depurar_motivos_documento_in_session`, contrato ni búsqueda (R2). Con `campos` vacío, no abre sesión de
escritura y devuelve `{}`.

### 4.3 Servicio y portal
- `ReviewService.editar_cabecera(*, document_id, campos) -> dict`: con campos, `snapshot_row` de
  `albaran_documents_merge`, llamada al repositorio y `record_undo(action="cabecera", description="Editar
  cabecera · Fecha, Notas (…doc_label…)", restore=[snap])` (R6). Sin campos, nada.
- `app.py`: `@app.patch("/api/documents/{document_id}/cabecera")` con `CabeceraEditBody = Body(...)`;
  `KeyError` ⇒ 404; respuesta de R1. `FechaAlbaranNoValidaError`/`NumeroAlbaranNoValidoError` (422 texto) y
  `AlbaranAprobadoError`/`AlbaranBloqueadoError` (409) usan los manejadores que ya existen (`app.py` ≈1942–1966).

### 4.4 `app.js` · cola de escritura (dentro del bloque de la ficha, funciones con nombre)
```js
function instalarColaEscrituras() { ... }  // guarda _fetchRed = window.fetch y lo envuelve (R24)
function encolar(tarea) { ... }            // _cola = _cola.then(tarea) en serie; cuenta pendientes; devuelve su promesa
function hayEscriturasEnCurso() { ... }    // R27
```
`window.fetch` envuelto: método GET/HEAD ⇒ `_fetchRed` directo; cualquier otro ⇒ `encolar(() => _fetchRed(...))`.
Así entran en la Cola, sin tocarlas, las ~22 vías de §1.6 y el deshacer global (usa `window.fetch` al hacer
clic). Las tareas de autoguardado llaman a `_fetchRed` directamente (una tarea que llamara al `fetch` envuelto
se esperaría a sí misma). Un fallo de una tarea no rompe la cadena (`then(t, t)` y `catch`). `beforeunload`:
`preventDefault` y `returnValue = ""` solo si `hayEscriturasEnCurso()` (R27). Se instala solo en ficha editable.

### 4.5 `app.js` · cabecera
- `valorCabeceraParaGuardar(campo)` ⇒ `{ok, valor}`: fecha con `parseFechaEs` (`null` ⇒ `ok: false`; `""` ⇒
  `null`); los textos, recortados (`""` ⇒ `null`).
- `autoguardarCampoCabecera(campo)`: si no `ok` o `valor === dataset.guardado (normalizado)`, nada; si no,
  `encolar` la tarea: `PATCH /cabecera` con `{[id]: valor}` vía `_fetchRed`; bien ⇒ `dataset.guardado` = lo
  devuelto, `campo-guardado`, estado (R10) y `document.dispatchEvent(new CustomEvent("autoguardado"))`; mal ⇒
  `motivoDeRespuesta`, `campo-no-guardado` y estado (R11, R26).
- `wireAutoguardadoCabecera()`: `blur` de los cuatro Campos y `change` de `#fecha_calendario` (R8). Se engancha
  DESPUÉS de `wireFechaAlbaran`, así el `blur` de F-108 ya reescribió o marcó la fecha (R9). Sin
  `#autoguardado-estado` (no editable) no hace nada (R12).

### 4.6 `app.js` · líneas
- `enviarFila(vid, cuerpo, opciones)`: `opciones = {bloquear = true, red = fetch}`; URL `.../conciliacion/campos`
  más `?bloquear=1` si `bloquear`. Sigue siendo la ÚNICA que construye esa URL (R30).
- `autoguardarFila(tr)`: `encolar` una tarea que espera `cargarPartidasObra()`; si `partidasMalas([tr], items)`,
  nada (R15); `const enviado = valoresDeFila(tr)` y `cuerpo = _camposCambiados(tr, lista.items)` en el mismo
  tick (R14; esta es la 4.ª llamada); vacío ⇒ nada; `enviarFila(vid, cuerpo, {bloquear: false, red: _fetchRed})`;
  bien ⇒ `consolidarSinBloquear(tr, enviado)`, `fila-autoguardada`, `dataset.autoguardada = "1"`, estado y evento
  (R16, R28); mal ⇒ `marcarFilaNoGuardada` y estado (R17, R26).
- `valoresDeFila(tr)` ⇒ `{field: value}` de sus Celdas; `consolidarSinBloquear(tr, enviado)`: `defaultValue =
  enviado[field]`, quita `cedit-dirty` donde ya coincide, quita `fila-no-guardada`; NO desactiva (≠
  `consolidarFila`).
- En `wireConciliaEdit`, por cada Celda: `inp.addEventListener("blur", () => autoguardarFila(tr))`. Se engancha
  después de `wirePartidaCombos` (su `blur` revierte primero la partida no válida, §1.8). El `keydown` Enter =
  `saveBtn.click()` no cambia (R20).
- `filasParaGuardar(filas)` = las de `filasConCambios` más las `data-autoguardada="1"` (las bloqueadas ya no
  están en `tr.concilia-editable`), en el orden de la tabla. La usan «Guardar todas» y `guardarFilasPendientes`
  en lugar de `filasConCambios` (R22); `contarFilasConCambios` (Dividir) sigue con `filasConCambios`.
- R23: los botones no necesitan código extra: su primer PATCH/PUT entra en la Cola detrás de los autoguardados,
  y el `blur` del campo ya encoló el suyo (R25). Ojo: `guardarFilasPendientes` lee `_camposCambiados` ANTES de
  que corra la Cola; para que no reenvíe lo que el autoguardado va a mandar, espera primero a que la Cola se
  vacíe (`await encolar(() => null)`) y luego elige filas y arma cuerpos. Lo mismo en «Guardar todas» y en el
  «Guardar» de la fila.
- Widget de deshacer: `etiquetaAccion` gana `cabecera: "Cabecera"`; escucha `"autoguardado"` y llama a
  `refrescar()` (R28).

## 5. Tests (sin red ni BBDD)
- `test_f116_cabecera_api.py`: cada campo solo y juntos (R1), contrato/proveedor/obra/aprobado/motivos intactos
  con un `selected_contrato_codigo` puesto «por sv3» (R2), 422 fecha y número sin escribir (R3), 409 aprobado y
  con alta, 404 (R4), campo extra y cuerpo vacío (R5), entrada de deshacer y deshacerla (R6).
- `test_f116_lineas_api.py`: PATCH sin `bloquear` ⇒ `bloqueada` falsa, edición con los campos y sin
  `bloqueada`, deshacer «Editar línea», importe recalculado (R18).
- `test_f116_autoguardado_js.py` (fetch falso que registra orden y deja respuestas pendientes): R7–R11 (cambio,
  sin cambio, fecha mala, calendario, fallo y reintento); R13–R17 (cuerpo, partida mala, consolidación con
  tecleo posterior, nada desactivado, fallo); R20; R22 (autoguardada sin cambios se bloquea con `{}`); R23–R25
  (`blur` + clic de «Guardar y aprobar»: el PATCH de autoguardado sale antes que nada y el PUT espera); R26
  (409 sin reintento); R27 (`beforeunload` con petición en vuelo); R28 (evento y etiqueta).
- `test_f116_ficha.py`: `#autoguardado-estado` y `data-guardado` en editable; ninguno en aprobado (R12).

## 6. Ficheros que NO se tocan
- sv6 (código), sv3, sv9, `ruesma_comun`: la edición sin bloqueo ya sobrevive (§1.2); el DDL no cambia.
- El PUT (`save_document_api`, `update_document_y_transicion`, `collectPayload`, `sendSave`) y los combos: R29.
- `update_line_conciliacion` del repositorio y del servicio: ya admiten `bloquear=False` (§1.1).
- El deshacer local `#undo-btn` y `_captureState` (§1.7); `consolidarFila` (la del botón, que desactiva).
- `templates/documents_list.html`: el listado no edita.

## 7. Verificación manual (líder, navegador)
- **M1 · sv4 local** (`infra/docs/levantar-pipeline-local.md`, BBDD local), Chrome y Edge, ficha pendiente:
  (1) escribir `28-10-26` + Tab ⇒ `28/10/2026`, marca «guardado»; recargar ⇒ sigue; `SELECT fecha FROM
  albaran_documents_merge WHERE id = '<id>'` ⇒ `2026-10-28`. (2) Calendario ⇒ guardado. (3) `31/02/2026` + Tab
  ⇒ rojo, nada guardado. (4) Número, forma de pago y notas + Tab ⇒ guardados. (5) En una fila, cantidad + Tab
  ⇒ importe recalculado y fila «guardada», sigue editable; recargar ⇒ valores guardados, «✋», sin bloquear.
  (6) Partida inventada + Tab ⇒ vuelve a la de antes, nada guardado. (7) Cursor en la fecha cambiada y clic
  directo en «Guardar y aprobar» ⇒ en la pestaña Red, el PATCH de cabecera termina antes del PUT. (8) Tras un
  autoguardado de fila, «Guardar todas» la bloquea. (9) «Deshacer» global ⇒ devuelve el último campo. (10)
  Revalorar ⇒ la fila autoguardada conserva su edición.
- **M2 · producción tras el despliegue** (solo lectura; no salir de un campo cambiado, no pulsar nada que
  guarde): la ficha carga, `#autoguardado-estado` existe y la consola no tiene errores.

## 8. Decisiones abiertas (PARADA 1)
- **D1 · Endpoint de cabecera.** (a, recomendada) `PATCH /api/documents/{id}/cabecera` parcial (§4.1–4.3): solo
  escribe el campo que se dejó. (b) Reutilizar el PUT entero: pisa lo que sv3 escribió después de abrir la ficha
  (contrato auto-seleccionado, dirección de obra, §1.4) en cada `blur`.
- **D2 · Qué bloquean «Guardar todas», «Guardar» y «Guardar y aprobar».** (a, recomendada) Las filas con cambios
  pendientes MÁS las autoguardadas en esta carga y sin bloquear: para el usuario bloquean lo mismo que hoy («lo
  que he tocado»). (b) Solo las de cambios pendientes: casi nunca habrá («No hay cambios en las líneas»). (c)
  Todas las que tienen «✋» y no están bloqueadas, también de sesiones anteriores.
- **D3 · Cómo se evitan las carreras.** (a, recomendada) Una Cola única en serie para toda escritura de la ficha,
  envolviendo `window.fetch` (§4.4): cubre las ~22 vías y las que vengan. (b) `await` explícito en cada
  manejador: más diff y alguna vía se quedará fuera.
- **D4 · Lo que se repinta tras autoguardar una fila.** (a, recomendada) Nada más que lo que ya repinta al
  teclear (importe/precio, «≠ albarán», «A Sigrid») y la marca: «✋», el paso Contrato ⇒ Nueva, el total y el
  aviso de la suma se ven al recargar (cualquier botón recarga). (b) Devolver el total en la respuesta del PATCH
  y repintar «Total valorado»: más código, poco valor.
- **D5 · Fila con partida no válida.** (a, recomendada) No se guarda nada de esa fila hasta corregirla, como los
  botones. (b) Guardar el resto de celdas sin la partida.
- **D6 · Salir de la página con guardados en vuelo.** (a, recomendada) Aviso nativo solo mientras hay peticiones
  en la Cola. (b) También con autoguardados fallidos sin reintentar. (c) Sin aviso.
- **D7 · Deshacer.** (a, recomendada) Una entrada del deshacer global por autoguardado (por campo de cabecera, por
  envío de fila), como cualquier PATCH de hoy. (b) Agrupar por fila o por minuto: cambia `undo_log`.
- **D8 · Aviso de un fallo.** (a, recomendada) Sin `alert`: marca en el campo o la fila y `#autoguardado-estado`;
  los botones reintentan y avisan como hoy. (b) `alert` en cada fallo (interrumpe al tabular).

**PARADA 1 cerrada por el humano el 2026-11-01 («ok»): D1–D8 = (a).**

## 9. Riesgos
- Envolver `window.fetch` afecta a todo `app.js` en la ficha: si una vía escribiera con un método en minúsculas
  o sin `method`, se compara en mayúsculas y sin `method` es GET. El listado no carga el bloque de la ficha.
- Más filas en `undo_log` (una por `blur` con cambios): crecimiento acotado por albarán; sin limpieza nueva.
- Una fila autoguardada sin bloquear la pueden tocar los masivos («Almacén a todas», «Borrar todas»): es lo
  que pidió el humano («2 comportamientos independientes»).
- `reviewed_at_utc` se sella en cada autoguardado: hoy nadie lo lee (solo el modelo y el ORM).
- Despliegue: solo sv4 (`Set-DeployTag; .\deploy.ps1 -Only sv4`), lo lanza el humano. Un `app.js` en caché
  sigue funcionando como antes (sin autoguardado) contra el sv4 nuevo.
