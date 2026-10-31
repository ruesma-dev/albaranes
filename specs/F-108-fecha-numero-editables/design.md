<!-- specs/F-108-fecha-numero-editables/design.md -->
# F-108 · Diseño técnico (v1)

Solo **sv4** (`services/albaranes-front`). Sin DDL, sin mensajes de cola, sin comun. Requisitos en
`requirements.md`; decisiones abiertas en §8 (PARADA 1).

## 1. Lo que hay hoy (leído en código y en producción, solo lectura, 2026-10-28)

1.1 **Cuándo es editable.** `document_detail.html:34`: `editable = document.is_editable and not
document.approved`; `is_editable` es la vista merge (`review_repository.py:3721`; las crudas, `False`).
`#fecha` y `#numero_albaran` (líneas 328 y 332) son `input type=text` con `readonly` solo si no es
editable. Un alta bloqueante solo existe sobre un aprobado y además impide desaprobar (F-053 R25).

1.2 **Guardado.** `app.js` `collectPayload` (≈2283) manda `fecha` y `numero_albaran` recortados, tal cual
se escriben, por el PUT `/api/documents/{id}` (`app.py:1227`), que usan 5 vías: «Guardar»/«Guardar y
aprobar» (`sendSave`), elegir obra/proveedor (auto-guardado, ≈2137), «Valorar» (≈2542), elegir contrato
(≈2842) y «Guardar y volver a buscar» (≈3006). Todas enseñan `detail` como texto. El repositorio
(`update_document_y_transicion`, ≈4056) hace `document.fecha = _clean_text(payload.fecha)`: **ni valida
ni normaliza**. `MergeDocumentUpdatePayload.fecha: str | None`. Ninguna revaloración ni re-fetch reescribe
la cabecera (sv3 sella `fecha` solo al crear el merge; sv6 no la toca).

1.3 **Teclado.** Ningún manejador toca `#fecha`/`#numero_albaran`: los de `document` solo actúan con F7
dentro de `tr.conciliacion-row`, F8 dentro de `.js-cedit` y Escape (panel de «Traer líneas»). El
formulario no tiene botón submit, así que Enter no lo envía. En producción (ficha `ec291d76…`, pendiente)
los dos campos no son `readonly` ni `disabled`, nada los tapa (`elementFromPoint`) y ningún `keydown` de
`1`, `/`, Retroceso, Supr, flechas, Enter, F7 o F8 ni un `beforeinput` sale con `defaultPrevented`.

1.4 **Lo que espera el resto.** sv3 sella `AAAA-MM-DD` (`AlbaranNormalizer.normalize_date`). sv9
(`validador_alta.py`): `_fecha` solo admite `^\d{4}-\d{2}-\d{2}$`; si no, `fecha_ilegible` ⇒
`no_admitido`; con fecha futura o de hace más de 365 días, `fecha_no_plausible` ⇒ `revisar`; manda
`fecha_albaran = AAAAMMDD`. sv3 usa la fecha para la vigencia del contrato en caché
(`_fecha_iso_a_yyyymmdd`): `05/06/2026` le da el entero `5062026`, una vigencia absurda.

1.5 **En producción** (listado, 157 documentos activos, solo lectura): 2 con la fecha en `dd/mm/aaaa`,
los dos con `reviewed_at_utc` (guardados a mano en sv4): `ae044452…` («05/06/2026», pendiente) y
`6ae1d618…` («08/10/2026», aprobado el 13-10, «Sin alta en Sigrid todavía»); 3 sin fecha.

**Hipótesis del síntoma (D1):** el teclado funciona, pero la fecha «no se edita con normalidad» porque
se ve y se tiene que escribir como `2026-10-09`; quien la escribe a la española (`dd/mm/aaaa`) la guarda
sin aviso y luego sv9 la rechaza (`fecha_ilegible`) y la caché de contratos de sv3 falla. Sin calendario.

## 2. Ficheros a crear
- `services/albaranes-front/domain/services/fecha_albaran.py` — dominio puro (§4.1).
- `services/albaranes-front/tests/test_f108_fecha_albaran.py` — R1–R4, R10, R20 (tabla común `CASOS`).
- `services/albaranes-front/tests/test_f108_guardado.py` — R5–R9, R11 (repositorio real sobre SQLite,
  `f065_bbdd`, y `build_app` con servicio falso, como `test_f065_f1_cabecera.py`).
- `services/albaranes-front/tests/test_f108_ficha.py` — R12, R13, R22, R23 (render con `render_detalle`).
- `services/albaranes-front/tests/test_f108_fecha_js.py` — R14–R21 (node + `tests/dom_falso.js`, patrón
  `test_f077_guardar_y_aprobar_js.py`; `con_node`).

## 3. Ficheros a modificar
- `domain/models/review_models.py` — `FechaAlbaranNoValidaError`, `NumeroAlbaranNoValidoError`,
  `CabeceraIncompletaError` (§4.2).
- `infrastructure/database/review_repository.py` — `update_document_y_transicion`: fecha por
  `normalizar_fecha_albaran`, número por `normalizar_numero_albaran`; `_exigir_cabecera_completa`
  llamada junto a `_exigir_lineas_completas` en `update_document_y_transicion` y en `set_approved` (D4).
- `interface_adapters/web/app.py` — filtro Jinja `fecha_albaran_ver`; manejador 422 de los dos errores
  de entrada; `CabeceraIncompletaError` en el manejador de 409 / ficha y en el `except` de
  `approve_from_list` (vuelta a la lista con el aviso).
- `templates/document_detail.html` — bloque de la fecha (§4.4); `maxlength="128"` y `autocomplete="off"`
  en `#numero_albaran`; la `<dd>` de la vista de solo lectura (línea ≈984) con el filtro.
- `static/app.js` — `parseFechaEs`, `fechaParaVer`, `fechaParaEnviar`, `wireFechaAlbaran` y la guarda
  de `guardarCabecera`; `collectPayload` usa `fechaParaEnviar` (§4.5).
- `static/styles.css` — `.campo-fecha` (input + botón en línea), `.fecha-calendario` (selector
  visualmente oculto, nunca `display:none`, para que `showPicker` funcione), `.campo-no-valido`.
- `tests/conftest.py` — `render_detalle` registra el filtro `fecha_albaran_ver` importado del dominio
  (sin él, toda plantilla falla por filtro desconocido).
- `docs/ARCHITECTURE.md` (regla 20, viñeta nueva) y `services/albaranes-front/sv4.md` (R27).

## 4. Clases y funciones

### 4.1 `domain/services/fecha_albaran.py` (domain, sin dependencias)
```python
AVISO_FECHA_NO_VALIDA = ("Fecha del albarán no válida: «{texto}». Escríbela como dd/mm/aaaa "
                         "(p. ej. 28/10/2026) o elígela en el calendario.")
MAX_NUMERO_ALBARAN = 128  # String(128) de albaran_documents_merge.numero_albaran

def normalizar_fecha_albaran(texto: str | None) -> str | None: ...   # R1–R3; lanza FechaAlbaranNoValidaError
def normalizar_numero_albaran(texto: str | None) -> str | None: ...  # R8, R9
def es_fecha_guardada_valida(valor: str | None) -> bool: ...         # AAAA-MM-DD real (R11)
def fecha_para_ver(valor: str | None) -> str: ...                    # R4 (nunca lanza)
```
Una sola expresión: `^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2}|\d{4})$` (día, mes, año; 2 cifras ⇒ `2000+`) o
`^(\d{4})-(\d{2})-(\d{2})$`, y `datetime.date(...)` para rechazar días que no existen. Sin `strptime`
(depende de la configuración regional) ni plausibilidad (es de sv9, D6).

### 4.2 Errores (`domain/models/review_models.py`)
- `FechaAlbaranNoValidaError(ValueError)` con `texto` y `aviso` (R3, R7).
- `NumeroAlbaranNoValidoError(ValueError)` con `aviso` (R9).
- `CabeceraIncompletaError(Exception)` con `document_id`, `faltan` y `aviso` (R11), como
  `LineasIncompletasError`.

### 4.3 Repositorio y portal (infrastructure / interface_adapters)
- `update_document_y_transicion`: tras `_exigir_editable` (un aprobado sigue dando 409 antes que una
  fecha mala), `document.fecha = normalizar_fecha_albaran(payload.fecha)` y el número igual. El error sale
  antes del `commit`: la sesión se cierra sin escribir (R7, R9). Con `paso_a_aprobado`,
  `_exigir_cabecera_completa(document)` (R11).
- `set_approved`: `_exigir_cabecera_completa(document)` con `paso_a_aprobado`, sin normalizar (el
  listado no edita la cabecera: una fecha guardada `dd/mm/aaaa` da «ábrelo y corrígela»).
- `app.py`: `@app.exception_handler(FechaAlbaranNoValidaError)` y `(NumeroAlbaranNoValidoError)` ⇒
  `JSONResponse(422, {"detail": exc.aviso})` (texto: las 5 vías de §1.2 lo enseñan sin cambios).
  `templates.env.filters["fecha_albaran_ver"] = fecha_para_ver`.

### 4.4 Plantilla (bloque de `#fecha`, ficha editable)
```html
<span class="campo-fecha">
  <input type="text" id="fecha" value="{{ document.fecha | fecha_albaran_ver }}"
         placeholder="dd/mm/aaaa" autocomplete="off" aria-describedby="fecha-error">
  <button type="button" class="btn secondary small js-fecha-calendario"
          title="Elegir la fecha en el calendario" aria-label="Elegir la fecha en el calendario">Calendario</button>
  <input type="date" id="fecha_calendario" class="fecha-calendario" tabindex="-1" aria-hidden="true">
</span>
<small id="fecha-error" class="error js-fecha-error" hidden></small>
```
No editable: solo el `input` con `readonly` y el filtro, sin botón ni selector (R22). Las crudas
(`provider_snapshots`, `readonly-grid` de la vista cruda) siguen con `{{ item.fecha }}` (R23).

### 4.5 `static/app.js` (funciones con nombre, extraíbles por `_funcion_js`)
- `parseFechaEs(texto)` ⇒ `"AAAA-MM-DD"`, `""` (vacía) o `null` (no admitida): misma regla que §4.1.
- `fechaParaVer(iso)` ⇒ `dd/mm/aaaa`; `fechaParaEnviar()` ⇒ ISO, `null` si vacía o lo escrito si no
  admitida (R19).
- `wireFechaAlbaran()`: `blur` de `#fecha` (R16, R17), `input` quita la marca, botón del Calendario (R14:
  `cal.value = parseFechaEs(fecha.value) || ""`, luego `cal.showPicker()`; si no existe o lanza, quita la
  clase que lo oculta y `cal.focus()`), `change` del selector (R15). Ninguno llama a `preventDefault`
  sobre teclas (R21). Sin `#fecha` (no editable) no hace nada.
- `guardarCabecera`: al principio, antes de desactivar los botones y de `guardarFilasPendientes`, si
  `parseFechaEs(...) === null` ⇒ marca, `alert` con el aviso de R3 (mismo texto que
  `AVISO_FECHA_NO_VALIDA`, contrastado en test), `focus` y `return` (R18). Las otras 4 vías no se guardan: mandan lo escrito y el 422 lo dice (R19).

## 5. Tests (sin red ni BBDD)
- `CASOS` (tabla común, ≈20 filas: los de R1, vacío, espacios, `31/02/2026`, `29/02/2024`, `2026/10/28`,
  `28/10`, `abc`, `28/13/2026`, `1/1/26`): el test Python la pasa por §4.1 y el de node por
  `parseFechaEs`, y los dos comparan con la columna esperada (R20).
- R10: el test lee `validador_alta.py` de sv9 como texto, saca `_RE_FECHA` y comprueba que toda salida
  ISO de `CASOS` casa con ella.
- El texto del aviso: `AVISO_FECHA_NO_VALIDA` de Python y el literal de `app.js` deben coincidir.

## 6. Ficheros que NO se tocan
- sv3 (`albaran_normalizer.py`, `contrato_enrichment_service.py`, `fecha_guard_service.py`): ya sella
  ISO; si alguna vez recibe otra cosa es por sv4, y eso es lo que se corrige aquí.
- sv9 (`validador_alta.py`): `_RE_FECHA`, `fecha_ilegible`, `fecha_no_plausible` y `fecha_albaran`
  AAAAMMDD siguen igual; con sv4 guardando ISO, su entrada queda bien.
- `ruesma_comun`: la regla de lectura es de entrada humana de sv4 (D7).
- `templates/documents_list.html` y el filtro de fecha del listado (D3); `orm_models.py` (sin DDL).
- `MergeDocumentUpdatePayload`: sin validador Pydantic (daría un 422 con lista, que las 5 vías pintarían
  como `[object Object]`).

## 7. Verificación manual (líder, navegador)
- **M1 · sv4 local** (`infra/docs/levantar-pipeline-local.md`, BBDD local): en una ficha pendiente,
  escribir en `#fecha` y `#numero_albaran` (también Enter, F7, F8 y Escape con el foco en ellos: no hacen
  nada raro, R21); `28-10-26` + Tab ⇒ `28/10/2026`; `31/02/2026` + Tab ⇒ rojo y aviso; «Guardar» con eso
  ⇒ aviso, nada guardado; botón «Calendario» ⇒ se abre el selector en el día escrito y elegir otro lo
  escribe; «Guardar» ⇒ la ficha recarga con `dd/mm/aaaa` y en BBDD local `SELECT fecha FROM
  albaran_documents_merge WHERE id = '<id>'` da `AAAA-MM-DD`. En un aprobado: solo lectura y sin botón.
  Chrome y Edge.
- **M2 · producción tras el despliegue** (solo lectura; NO pulsar Guardar, Aprobar ni Valorar): la
  ficha `ec291d76…` enseña `09/10/2026`, el botón abre el calendario y el campo admite escritura; cerrar
  sin guardar. Guardar en producción solo con autorización expresa del humano.
- **M3 · humano**: decidir qué hacer con `ae044452…` y `6ae1d618…` (D5).

## 8. Decisiones abiertas (PARADA 1)
- **D1 · Síntoma.** (a, recomendada) Trabajar con la hipótesis de §1 hasta que conteste el humano: cubre
  formato, aviso y calendario. (b) Esperar su respuesta. Si contesta otra cosa (p. ej. «no me deja
  escribir» en un caso concreto), se reabre la spec con ese caso.
- **D2 · Formato.** (a, recomendada) Se ve `dd/mm/aaaa`, se guarda `AAAA-MM-DD`, se admite cualquiera de
  los Formatos admitidos. (b) Se ve y se guarda `AAAA-MM-DD` (lo escrito a la española se convierte al
  salir del campo). (c) Guardar `dd/mm/aaaa`: descartada (rompe sv9 y la caché de sv3).
- **D3 · Listado.** (a, recomendada) Sin cambios (`AAAA-MM-DD`, ordena y filtra bien). (b) También
  `dd/mm/aaaa` en la columna y el filtro: feature aparte.
- **D4 · Aprobar sin fecha o sin número.** (a, recomendada) No se aprueba (ficha y listado), R11: sv9 lo
  rechazaría igual (`fecha_ilegible`, `falta_numero_albaran`) y el aviso llega antes. (b) Como hoy: se
  aprueba y lo dice el panel del alta.
- **D5 · Las 2 fechas ya guardadas en `dd/mm/aaaa`.** (a, recomendada) No migrar: la pendiente se
  arregla al guardarla; la aprobada (sin alta) se desaprueba y se guarda si se quiere dar de alta. (b)
  Script de una vez: escritura en producción, exige autorización expresa.
- **D6 · Aviso de fecha poco plausible en la ficha.** (a, recomendada) Fuera: sv9 ya la marca `revisar` y
  el panel lo enseña; meterla en sv4 obliga a llevar su regla (365 días) a comun y tocar sv9. (b) Dentro,
  como aviso no bloqueante, con la regla en `ruesma_comun.alta_sigrid`.
- **D7 · Dónde vive la regla de lectura.** (a, recomendada) Dominio de sv4: es entrada humana y estricta
  (rechaza); la de sv3 es tolerante (deja pasar lo que no entiende). Distinta responsabilidad, no copia.
  (b) `ruesma_comun.fechas` (comun 0.10.0) y sv3 la usa: toca comun y sv3, más despliegue.

**PARADA 1 cerrada por el humano el 2026-10-28 («Todo a»): D1–D7 = (a).**

## 9. Riesgos
- `showPicker` necesita gesto del usuario y el selector renderizado: por eso va oculto con opacidad y
  tamaño mínimo junto al botón (el calendario se ancla ahí), no con `display:none`; fallback de R14.
- Año de 2 cifras: `26` ⇒ 2026 siempre (no hay albaranes del siglo XX).
- `dd/mm` frente a `mm/dd`: se asume siempre día primero (España); `05/06/2026` es 5 de junio.
- Despliegue: solo sv4 (`Set-DeployTag; .\deploy.ps1 -Only sv4`), lo lanza el humano; un `app.js` en
  caché sigue mandando lo escrito y el servidor lo normaliza o lo rechaza con texto.
