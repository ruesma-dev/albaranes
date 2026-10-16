<!-- specs/F-077-guardar-y-aprobar/design.md -->
# F-077 · Ficha: guardar y aprobar de una vez · Diseño (v1, 2026-10-16)

Requisitos en `requirements.md`; decisiones y preguntas en `progress/spec_F-077.md`. Rutas relativas a
`services/albaranes-front/` salvo que se diga otra cosa.

## 1. Encaje y límite de servicio

Todo es **sv4** (front de revisión, regla 20 de ARCHITECTURE: «lo editado en las líneas manda»; regla 19: sv4 pinta el
alta, sv9 la escribe). No hay responsabilidad nueva: ni otro dominio ni integración. Sin DDL, sin SQL nuevo (el panel
reutiliza `estado_aprobacion` y `leer_alta_sigrid`, ya existentes y de solo lectura), sin colas, sin cambios en comun,
sv3, sv6 ni sv9. La ruta nueva (R16) solo la consume el propio JS de sv4: **no** cambia lo que el proyecto expone a
otros, así que `azure-apps/albaranes.md` no se toca.

## 2. Ficheros a modificar

| Fichero | Cambio | R |
|---|---|---|
| `static/app.js` | §3: guardado previo de filas en `guardarCabecera`; función única de PATCH; fuera `avisoFilasSinGuardar` y `contarFilasConCambios`; §4: sondeo del alta | R1–R13, R17 |
| `templates/document_detail.html` | `title` de la casilla de partida (~L742) y del ⚠ de solo lectura (~L750) con `c.aviso_partida` | R20–R22 |
| `templates/_alta_sigrid.html` | rama `document.alta_pendiente`; `data-pendiente` y `data-document-id` en la `<section>`; motivos de línea sueltos (§5 bis) | R15, R19, R25 |
| `domain/models/alta_sigrid_models.py` | `TEXTOS_MOTIVO_LINEA` y `texto_motivo_alta(codigo)`; `AltaSigridVista.motivos_linea_sueltos` | R25, R27, R28 |
| `static/styles.css` | `tr.fila-no-guardada` (fondo y borde rojos, los de `.partida-invalida`) y `.alta-sigrid-pendiente` | R4, R15 |
| `domain/models/review_models.py` | `aviso_partida_texto(...)` y `posiciones_filas_ficha(...)` (puras); campo `ConciliacionDisplay.aviso_partida`; campos `DocumentDetailPayload.alta_pendiente: bool = False` y `alta_motivos_linea: list[dict] = []` | R14, R20–R22, R26 |
| `infrastructure/database/review_repository.py` | rellena `aviso_partida` donde hoy calcula `agree_partida` (~L4641 con blanca, ~L4787 sin blanca) | R20, R21 |
| `domain/services/alta_sigrid.py` | `alta_pendiente(...)` (pura) | R14 |
| `application/services/review_service.py` | `get_document` añade `alta_pendiente` y `alta_motivos_linea`; método `alta_pendiente(document_id, *, ahora=None)` | R14, R16, R25, R26 |
| `interface_adapters/web/app.py` | `GET /api/documents/{document_id}/alta-sigrid/pendiente` | R16 |
| `tests/test_f065_f1_js.py`, `tests/test_f065_f3bis_front.py` | §6 | R12, R13 |
| `docs/ARCHITECTURE.md` (raíz), `sv4.md` | reglas 19 y 20; tabla de endpoints | R24 |

**Ficheros a crear**: `tests/test_f077_guardar_y_aprobar_js.py` (A), `tests/test_f077_alta_pendiente.py` (B),
`tests/test_f077_aviso_partida.py` (C), `tests/test_f077_motivos_linea.py` (D).

## 3. A · Guardar las filas antes de la cabecera (`static/app.js`)

Funciones nuevas (dentro del bloque de edición, nombres únicos para que `_funcion_js` las extraiga):

- `filasConCambios(filas)` → las `tr` de `filas` con `data-for-valuation-line-id` y `_camposCambiados` no vacío.
  Sustituye a `contarFilasConCambios` (que solo contaba) y al `conCambios()` interno de «Guardar todas».
- `async motivoDeRespuesta(resp)` → el texto de error de hoy (`detail` como cadena o la lista de 422 unida con « | »;
  si no, `statusText`). Hoy está copiado en el «Guardar» de fila y en «Guardar todas».
- `async enviarFila(vid, cuerpo)` → `null` si el PATCH de fila responde ok; si no, el motivo (`motivoDeRespuesta`), y
  `"error de red"` si `fetch` lanza. **Única** petición `PATCH …/conciliacion/campos?bloquear=1` del fichero (R12):
  la usan el «Guardar» de fila (mismo `alert("Error al guardar la línea: " + motivo)` y recarga de hoy), «Guardar
  todas» (mismos «Línea <vid>: <motivo>» de hoy) y `guardarFilasPendientes`.
- `consolidarFila(tr)` (R5): por cada `.js-cedit`, `defaultValue = value`, quita `cedit-dirty`, `disabled = true`; y
  `.js-cedit-save` desactivado. Así `_camposCambiados(tr)` vuelve vacío y no se reenvía (el servidor la tiene ya
  bloqueada: reenviarla daría 409 «Línea guardada…»).
- `marcarFilaNoGuardada(tr, motivo)`: `fila-no-guardada` + `title = motivo`; `limpiarFilasNoGuardadas()` las quita al
  empezar cada intento.
- `async guardarFilasPendientes()` → `{malas: bool, guardadas: n, motivo: texto|null}`:
  `lista = await cargarPartidasObra()`; **después**, en el mismo tick: `filas = filasConCambios(todas las editables)`,
  `partidasMalas(filas, lista.items)` (si hay: `{malas: true}` sin enviar nada, R3) y los cuerpos; luego, en orden,
  `enviarFila`; al primer fallo, `marcarFilaNoGuardada` y devuelve `{guardadas, motivo}` (R4); cada éxito,
  `consolidarFila` (R5).
- `async avisoSumaVigente()` → el `aviso_suma` de `GET /api/documents/{documentId}` (`""` si es nulo), o `null` si la
  lectura falla (R6, R8).

`guardarCabecera(markApproved)` queda (orden, R1–R10):

1. Si ya hay un intento en marcha, nada. Desactiva `saveBtn` y `approveBtn` (R10).
2. `limpiarFilasNoGuardadas()`; `r = await guardarFilasPendientes()`.
3. `r.malas` ⇒ alerta R3, reactiva, fin. `r.motivo` ⇒ alerta R4 (texto según `markApproved`), reactiva, fin.
4. Si `markApproved`: `aviso = r.guardadas ? await avisoSumaVigente() : approveBtn.dataset.avisoSuma`. `aviso === null`
   ⇒ alerta R8 y `location.reload()`. Aviso no vacío y `!confirm(aviso)` ⇒ R7 (recarga si `r.guardadas`, si no
   reactiva).
5. `ok = await sendSave(markApproved)` (sin cambios: alerta «Error al guardar…» o navega a `redirect_url`). Si `!ok`:
   `r.guardadas` ⇒ `location.reload()` (R9); si no, reactiva.

Los listeners de `#save-btn` y `#approve-btn` no cambian de texto (`guardarCabecera(false)` / `(true)`). La bandera
de «intento en marcha» es una variable del bloque (no el `disabled` del botón: `approveBtn` puede venir `disabled` de
la plantilla cuando no está valorado y eso no se toca).

Se borran `avisoFilasSinGuardar` y `contarFilasConCambios` (sin otros usos: `grep` en `app.js`).

## 4. B · «Alta en curso…»

**Dominio** (`domain/services/alta_sigrid.py`, puro):

```python
def alta_pendiente(*, aprobado: bool, activo: bool, approved_at_utc: str | None,
                   alta: AltaSigridVista | None, config: ConfigAltaSigrid, ahora: datetime) -> bool
```

R14 literal: `_documento_admite_alta(...)` (ya existe) o `False`; `aprobado_en = _instante(approved_at_utc)`;
`de_otra = alta is None or alta.estado in ESTADOS_ALTA_REPETIBLES and (instante del alta is None or < aprobado_en)`;
si `de_otra`: `not espera_pasada(aprobado_en, ahora, config.espera)`; si el alta es de esta aprobación (`==`) y
`en_curso`: `not espera_pasada(_instante(alta.ultimo_intento_at_utc), ahora, config.espera)`; si no, `False`.
Por qué los repetibles: con `ya_en_sigrid` (o `registrado`, `incierto`) sv9 ignora la nueva aprobación (R7 de F-053,
`reclamacion.py`) y la fila vieja **es** la respuesta; esperar 15 min a nada sería peor que hoy.

**Servicio** (`ReviewService`): `alta_pendiente(document_id, *, ahora=None) -> bool | None` — feature apagada ⇒
`False` sin leer (R16); `estado_aprobacion` nulo ⇒ `None` (la ruta da 404); si no, la función de dominio con
`leer_alta_sigrid`. `get_document` añade `"alta_pendiente": self.alta_pendiente(document_id) is True` al
`model_copy` que ya hace con DESDE puesta (con DESDE vacía queda el `False` por defecto, R3 de F-053 intacto).

**Ruta** (`app.py`, junto a las de F-053): `@app.get("/api/documents/{document_id}/alta-sigrid/pendiente",
include_in_schema=False)` → `{"pendiente": valor}` o `HTTPException(404)`. Solo lectura: ni cerrojo ni publicación
(R18). Las rutas de escritura con cerrojo de F-053 R25 no la incluyen (no escribe).

**Plantilla** (`_alta_sigrid.html`): la `<section>` gana `data-document-id` y, con `document.alta_pendiente`,
`data-pendiente="1"`, clase `info` y solo «Alta en curso…» + la frase de R15; el bloque de hoy (`{% if alta %}…`) y
`.alta-sigrid-acciones` van en el `{% else %}` sin cambios (R19).

**JS** (bloque autónomo al final de `app.js`, como el del producto de F-053, porque la ficha aprobada no monta el
bloque de edición):

- `intervaloSondeoAlta(transcurridoMs)` → `3000` si `< 60000`, si no `15000` (R17).
- `sondearAltaPendiente(panel)`: sin panel o sin `data-pendiente="1"`, nada. Si no, `setTimeout` encadenado (nunca
  `setInterval`: una respuesta lenta no apila peticiones) con `intervaloSondeoAlta(Date.now() - inicio)`;
  `fetch` con `Accept: application/json`; 404 ⇒ para; `{pendiente: false}` ⇒ `window.location.reload()` y para;
  error de red, no ok o JSON ilegible ⇒ vuelve a programar.
- Arranque: `sondearAltaPendiente(document.getElementById("alta-sigrid"))`.

## 5. C · Tooltip del ⚠ (`review_models.py`, repositorio, plantilla)

`aviso_partida_texto(agree: bool | None, *, leida: str | None, contrato: str | None) -> str | None` (pura, junto a
`aviso_suma_importes`): `agree is not False` ⇒ `None`; `leida` no vacía ⇒ «No coincide con la partida leída en el
albarán (<leida recortada>)»; si no, «No coincide con la partida de su línea de contrato (<contrato>)».

Repositorio: en `_build_display_lines` (~L4641) `_conc.aviso_partida = aviso_partida_texto(_conc.agree_partida,
leida=line.codigo_imputacion, contrato=_partida_del_contrato(_conc))`; en `_synthetic_to_display` (~L4787)
`conc.aviso_partida = aviso_partida_texto(conc.agree_partida, leida=None, contrato=_partida_del_contrato(conc))`.
El cálculo de `agree_partida` (`_agree_txt` / `_txt`) no se toca (R22).

Plantilla: en la casilla editable (~L742, solo fuera de almacén) y en el `<span class="concilia-price-warn">`
(~L750): `title="{{ c.descripcion_partida or '' }}{% if c.aviso_partida %}{{ '\n' if c.descripcion_partida }}{{
c.aviso_partida }}{% endif %}"` (salto de línea real dentro del atributo; Jinja lo escapa). `marcarPartida` (F-065
R27 v5) guarda el `title` en `data-titulo-antes` y lo devuelve: R22 sale gratis; un test lo fija.

## 5 bis. D · Motivos de línea que no caben en la tabla del panel

- `alta_sigrid_models.py`: `TEXTOS_MOTIVO_LINEA: dict[str, str]` (la tabla de R27) y `texto_motivo_alta(codigo) ->
  str` (desconocido ⇒ el código). `AltaSigridVista.motivos_linea_sueltos` (computed): los motivos con
  `referencia_linea` no vacía cuya referencia no está entre las de `self.lineas` (R25, R28); `motivos_documento` y
  `lineas` no cambian.
- `review_models.py`: `posiciones_filas_ficha(display_lines) -> dict[int, int]`: `valuation_line_id` ⇒ posición
  (desde 1) entre las `display_lines` con `concilia`, en su orden: exactamente las filas que pinta la tabla de la
  ficha (`{% if dline.concilia %}`, ~L712), la misma numeración que da F-065 R20 con `orden_filas_ficha`.
- `review_service.get_document` (rama con DESDE puesta): `alta_motivos_linea = [{"linea": "Línea 3" | "Línea (ref.
  386)", "texto": texto_motivo_alta(c), "detalle": d, "codigo": c} …]` desde `alta.motivos_linea_sueltos` y
  `posiciones_filas_ficha(detalle.display_lines)`. Una función pura `motivos_linea_vista(alta, posiciones)` en
  `domain/services/alta_sigrid.py` hace el cálculo (el servicio solo la llama).
- `_alta_sigrid.html`: la `<ul class="alta-sigrid-motivos">` se pinta si hay `alta.motivos_documento` **o**
  `document.alta_motivos_linea`; tras los del documento (sin cambios), un `<li class="alta-sigrid-motivo-linea">` por
  cada uno: «{{ linea }}: {{ texto }}», « · {{ detalle }}» si no está vacío y `<code>{{ codigo }}</code>`.
- Tests RED (fichero D): el caso real literal (`no_admitido`, un `falta_descripcion` con `referencia_linea` `"386"`,
  sin petición ni respuesta) ⇒ el panel contiene «La línea no tiene descripción» y «Línea N» con la posición de la fila
  386 en la ficha; sin esa fila en la ficha ⇒ «Línea (ref. 386)»; con petición que trae la 386 ⇒ el motivo sale en su
  fila y **no** en la lista; código desconocido ⇒ el código tal cual; pendiente ⇒ nada (R28). Hoy fallan los cuatro
  primeros (la lista solo pinta `motivos_documento`).
- Fuera: el texto de los motivos del **documento** (siguen con su código, F-053 R29) y los motivos dentro de la tabla.

## 6. Tests de F-065 que cambian y por qué

| Test | Qué pasa | Por qué |
|---|---|---|
| `test_f065_f1_js.py::test_f065_r19_js_aviso_de_filas_sin_guardar` | se borra | `avisoFilasSinGuardar` desaparece (R13); lo sustituye `test_f077_r13_…` (el texto no aparece en `app.js`) |
| `test_f065_f1_js.py::test_f065_r19_guardar_y_aprobar_miran_las_filas_sucias_antes_del_put` | se reescribe como `test_f077_r1_…` (en el fichero nuevo) y se borra aquí | el orden ahora es «guardar filas ⇒ PUT», no «aviso ⇒ nada» |
| `test_f065_f1_js.py::test_f065_r18_js_cuenta_las_filas_con_cambios` | pasa a `filasConCambios` (longitud de la lista y filas sin vid fuera) | `contarFilasConCambios` se sustituye (R12) |
| `test_f065_f1_js.py::test_f065_r18_guardar_todas_salta_las_filas_sin_cambios_y_avisa_si_no_hay` | la regex `Object.keys(cuerpo).length` pasa a `filasConCambios(` | el filtro vive ahora en la función compartida |
| `test_f065_f1_js.py::test_f065_r21_aprobar_confirma_con_el_aviso_de_la_suma` | se mantiene (sigue habiendo `approveBtn.dataset.avisoSuma` y `window.confirm(aviso)` en `guardarCabecera`) | R6 conserva F-065 R21 |
| `test_f065_f3bis_front.py::test_f065_r27v5_guardar_y_aprobar_marca_la_partida_mala` | misma escena; espera la alerta de R3 y sigue con 0 PUT y 0 PATCH | ya no hay «Hay 1 línea…»; la partida mala sigue parando todo |
| `test_f065_f3bis_front.py`: `_GUARDAR`, `_todas()`, `_FICHA` | `_GUARDAR` añade `filasConCambios`, `motivoDeRespuesta`, `enviarFila`, `consolidarFila`; `_FICHA` pierde los dobles `contarFilasConCambios`/`avisoFilasSinGuardar` | el «Guardar» de fila y «Guardar todas» llaman a las funciones compartidas |

Los CR4 (`test_f065_cr4_*`) y R27 v5 de fila y de «Guardar todas» **no** cambian de expectativas: son la red de R12.
Ningún test de F-053 cambia: `alta_pendiente` vale `False` por defecto y los dobles de `test_f053_t21_panel.py`
aprobaron el 2026-10-05 (fuera de la Espera con el reloj real); los tests nuevos del servicio inyectan `ahora`.

## 7. Ficheros que NO se tocan

- Servidor de guardado: `MergeDocumentUpdatePayload`, el PUT, el PATCH de fila, `_exigir_editable`, el cerrojo de
  F-053 R25, R20 de F-065 (R11).
- `wireDividir`, F7 y la fila activa (**F-068**); `wirePartidaCombos`, `partidasMalas`, `cargarPartidasObra`.
- `/api/sigrid/partidas` y `infrastructure/sigrid/*` (**F-076** R15 los rehace desde comun; §8).
- `_agree_txt`, `_txt`, `_partida_del_contrato`: la equivalencia `CI.04.18` = `CI.4.18` es de F-076.
- `domain/services/alta_sigrid.py::puede_solicitar_alta` / `puede_reintentar_adjunto` (el panel solo oculta sus
  botones mientras está pendiente); el listado (F-053 R31); sv9, sv3, sv6, comun.

## 8. Solapes con otras ramas

- **F-076** (`feature/F-076-normalizar-partidas`, spec en curso): su R15 rehace el origen de `/api/sigrid/partidas`
  con los mismos `items`; F-077 solo consume esa lista en el cliente: sin conflicto de comportamiento. Si F-076 tocara
  `review_repository.py` cerca de `agree_partida`, el conflicto sería de texto (dos líneas por sitio). Con F-076
  activa, una lectura `CI.04.18` normalizada a `CI.4.18` sigue dando ⚠ (la lectura se conserva y `agree_partida`
  compara texto) y el tooltip de R20 explica justo eso; si F-076 decide que lo equivalente no avisa, cambia
  `agree_partida` y R20–R22 siguen valiendo.
- **F-068** (pendiente): toca `wireDividir`/F7 en `app.js`; zona distinta de §3.
- **F-058** (pendiente): revalorar conserva lo editado; sin relación directa.

## 9. Riesgos y decisiones

- **D1 · Parar al primer fallo** (no seguir con las demás filas como «Guardar todas»): el humano quiere «si alguna no
  se puede guardar, se para»; seguir guardando tras un fallo deja más estado parcial sin aprobar nada.
- **D2 · Consolidar en vez de recargar tras un fallo**: recargar perdería lo tecleado en la fila en rojo y en las
  siguientes; consolidar evita el 409 al reintentar.
- **D3 · Aviso de suma releído tras guardar**: el `data-aviso-suma` se calcula con las filas guardadas al pintar;
  tras guardar filas sería falso. Alternativa descartada: recalcularlo en el cliente (duplicaría `suma_leida` y
  `aviso_suma_importes`). Coste: un GET del detalle solo cuando se guardaron filas.
- **D4 · Pendiente acotado por la Espera**: sin cota, una publicación perdida dejaría «Alta en curso…» para siempre y
  escondería «Solicitar alta». Con la Espera (la misma de `puede_solicitar_alta` para `en_curso`), pasado ese tiempo
  vuelve el panel de hoy con su botón. Riesgo aceptado: hasta 15 min sin «Solicitar» si la publicación falló (sv4 ya
  avisa de «alta no pedida» al aprobar, F-053 R1/R4). El coordinador pidió «mientras la aprobación sea más reciente
  (o no haya fila), sin botón»: la cota y la restricción a estados repetibles son precisiones de este diseño, abiertas
  como P1 en `progress/spec_F-077.md` (quitarlas es borrar una condición de `alta_pendiente`).
- **D5 · Recargar la página al terminar** en vez de repintar solo el panel: la ficha aprobada es de solo lectura (no
  se pierde nada) y no hace falta una ruta que renderice el fragmento.
- **R-1 · «Guardar» con `?buscar_si_cambia=1`**: si cambió CIF u obra, el PUT relanza la búsqueda y la revaloración
  descarta lo editado (F-058). Es el comportamiento de hoy; antes había que guardar las filas a mano igual.
- **R-2 · Fuera de alcance**: «Solicitar alta en Sigrid» sin reaprobar no pasa por pendiente hasta que sv9 marca
  `en_curso` (la fila vieja se ve unos segundos, como hoy); el listado sigue pintando el estado guardado.
- **R-3 · Mutación**: la campaña de `harness.mutacion` muta Python (dominio, servicio, repositorio, ruta); el JS lo
  cubren los tests con node. Rigor `estandar`: no escribe en sistemas compartidos ni cambia lo que recibe sv9.
