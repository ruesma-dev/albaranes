<!-- specs/F-077-guardar-y-aprobar/design.md -->
# F-077 · Ficha: guardar y aprobar de una vez · Diseño (v2, 2026-10-16, tras la PARADA 1)

Requisitos en `requirements.md`; decisiones y Anexo A (textos de motivos) en `progress/spec_F-077.md`. Rutas
relativas a `services/albaranes-front/` salvo que se diga otra cosa.

## 1. Encaje y límite de servicio

Todo es **sv4** (front de revisión; regla 20 de ARCHITECTURE: «lo editado en las líneas manda»; regla 19: sv4 pinta el
alta, sv9 la escribe). Ninguna responsabilidad nueva. Sin DDL ni SQL nuevo (el panel reutiliza `estado_aprobacion` y
`leer_alta_sigrid`, de solo lectura), sin colas, sin cambios en comun, sv3, sv6 ni sv9. La ruta nueva (R18) solo la
consume el JS de sv4: no cambia lo que el proyecto expone, así que `azure-apps/albaranes.md` no se toca. sv4 no puede
recibir la respuesta de sv9 de forma síncrona (el alta va por `q-feedback`): «esperar la respuesta» = sondear.

## 2. Ficheros a modificar

| Fichero | Cambio | R |
|---|---|---|
| `static/app.js` | §3 guardado previo de filas y PATCH único; fuera `avisoFilasSinGuardar` y `contarFilasConCambios`; §4 sondeo | R1–R13, R19 |
| `templates/_alta_sigrid.html` | tres fases (§4); `data-fase`, `data-document-id`; clase `error`; motivos con texto y código en `title` (§6) | R15–R17, R24–R28 |
| `templates/document_detail.html` | casilla de partida (~L742) y ⚠ de solo lectura (~L750): condición `c.aviso_partida` y su `title` | R21–R23 |
| `static/styles.css` | `tr.fila-no-guardada`; `.alta-sigrid.error` y `.alta-sigrid-en-curso` | R4, R15–R17 |
| `domain/models/alta_sigrid_models.py` | `ESTADOS_ALTA_ERROR`, `AltaSigridVista.es_error`; `TEXTOS_MOTIVO_ALTA`, `texto_motivo_alta`; `texto` en cada motivo; `motivos_linea_sueltos` | R17, R24, R26–R28 |
| `domain/models/review_models.py` | `aviso_partida_texto`, `posiciones_filas_ficha` (puras); `ConciliacionDisplay.aviso_partida`; `DocumentDetailPayload.alta_fase` (`"resultado"` por defecto) y `alta_motivos_linea` | R14, R21–R25 |
| `infrastructure/database/review_repository.py` | `aviso_partida` en la rama con blanca (~L4641); la sintética (~L4787) no lo pone | R21, R22 |
| `domain/services/alta_sigrid.py` | `fase_alta(...)`, `motivos_linea_vista(...)` (puras) | R14, R24, R25 |
| `application/services/review_service.py` | `get_document` añade `alta_fase` y `alta_motivos_linea`; método `fase_alta(document_id, *, ahora=None)` | R14, R18 |
| `interface_adapters/web/app.py` | `GET /api/documents/{document_id}/alta-sigrid/fase` | R18 |
| `tests/test_f065_f1_js.py`, `tests/test_f065_f3bis_front.py` | §7 | R12, R13 |
| `docs/ARCHITECTURE.md` (raíz), `sv4.md` | reglas 19 y 20; tabla de endpoints | R30 |

**Ficheros a crear**: `tests/test_f077_guardar_y_aprobar_js.py` (A), `tests/test_f077_alta_fase.py` (B),
`tests/test_f077_aviso_partida.py` (C), `tests/test_f077_motivos_alta.py` (D).

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
> Nota 2026-10-17 (implementación, aceptado en review): sí tenían otro uso, la confirmación de «Dividir» (`wireDividir`, F-065 R29), que §8 deja
> fuera: se quedan para ella; `guardarCabecera` ya no las usa (R13). Se borra `partidasInvalidas`, que solo usaba R19.

## 4. B · Fases del panel del alta

**Dominio** (`domain/services/alta_sigrid.py`, puro): constantes `FASE_EN_CURSO`, `FASE_SIN_RESPUESTA`,
`FASE_RESULTADO` y `TOPE_RESPUESTA_ALTA = timedelta(minutes=5)` (decisión del humano: «la escritura en Sigrid es
rápida»; constante de dominio, no variable de entorno: nadie ha pedido ajustarla).

```python
def fase_alta(*, aprobado: bool, activo: bool, approved_at_utc: str | None,
              alta: AltaSigridVista | None, config: ConfigAltaSigrid, ahora: datetime) -> str
```

R14 literal: sin `_documento_admite_alta(...)` (ya existe) ⇒ `FASE_RESULTADO`; `aprobado_en = _instante(
approved_at_utc)`; esperando = sin alta, o alta anterior (instante nulo o `<` `aprobado_en`) en
`ESTADOS_ALTA_REPETIBLES`, o alta de la vigente (`==`) en `en_curso`; no esperando ⇒ `FASE_RESULTADO`; esperando y
`ahora - aprobado_en < TOPE_RESPUESTA_ALTA` ⇒ `FASE_EN_CURSO`; si no ⇒ `FASE_SIN_RESPUESTA`. Con `ya_en_sigrid`,
`registrado` o `incierto` anteriores sv9 ignora la aprobación nueva (`reclamacion.py`, F-053 R7): esa fila **es** la
respuesta y nunca se queda «en curso».

`alta_sigrid_models.py`: `ESTADOS_ALTA_ERROR = frozenset({"no_admitido", "revisar", "error"})` y
`AltaSigridVista.es_error` (computed). `incierto` sigue como hoy (aviso de bloqueo, «pendiente de confirmar»): no es
un rechazo sino una grabación sin confirmar que sv9 retoma tras la Espera.

**Servicio** (`ReviewService`): `fase_alta(document_id, *, ahora=None) -> str | None` — feature apagada ⇒
`FASE_RESULTADO` sin leer (R18); `estado_aprobacion` nulo ⇒ `None` (la ruta da 404); si no, la función de dominio
con `leer_alta_sigrid`. `get_document` añade `"alta_fase": self.fase_alta(document_id) or FASE_RESULTADO` al
`model_copy` que ya hace con DESDE puesta (con DESDE vacía queda el defecto, R3 de F-053 intacto).

**Ruta** (`app.py`, junto a las de F-053): `@app.get("/api/documents/{document_id}/alta-sigrid/fase",
include_in_schema=False)` → `{"fase": valor}` o `HTTPException(404)`. Solo lectura, sin cerrojo ni publicación (R20).

**Plantilla** (`_alta_sigrid.html`): la `<section>` gana `data-document-id` y `data-fase="{{ document.alta_fase }}"`.
`en_curso` ⇒ clase `info alta-sigrid-en-curso`, «Alta en curso…» y la frase de R15, nada más. `sin_respuesta` ⇒
clase `error`, el texto de R16 y solo el formulario «Solicitar alta» si `document.alta_puede_solicitar`.
`resultado` ⇒ el bloque de hoy; la clase pasa a `error` con `alta.es_error` («Error en el alta en Sigrid:
{{ alta.estado_texto }}» en lugar de «Estado: …»), `warning` si es bloqueante, `info` en el resto.

**«Solicitar alta» en `sin_respuesta` (R16)**: se ofrece con la regla de siempre (`puede_solicitar_alta`, la misma con
la que decide sv9). Sin fila o con una fila repetible anterior, sí: a los 5 min sin que sv9 haya reclamado (lo hace en
segundos) lo más probable es un mensaje perdido o no publicado, y volver a publicarlo es para lo que existe el botón;
un duplicado no hace daño (sv9 reclama con `FOR UPDATE`; el segundo ve `en_curso` y lo ignora dentro de la Espera,
R7). Con `en_curso` de la aprobación vigente, no hasta la Espera: sv9 lo ignoraría (R7) y el botón prometería algo que
no pasa.

**JS** (bloque autónomo al final de `app.js`, como el del producto de F-053, porque la ficha aprobada no monta el
bloque de edición): `SONDEO_ALTA_MS = 3000`; `sondearAltaEnCurso(panel)`: sin panel o con `data-fase` distinta de
`en_curso`, nada; si no, `setTimeout` encadenado (nunca `setInterval`: una respuesta lenta no apila peticiones);
`fetch` con `Accept: application/json`; 404 ⇒ para; `fase !== "en_curso"` ⇒ `window.location.reload()` y para; error
de red, no ok o JSON ilegible ⇒ vuelve a programar. Arranque: `sondearAltaEnCurso(document.getElementById(
"alta-sigrid"))`.

**Alternativa evaluada: long-poll** (`GET …/fase?esperar=25`, que relee cada segundo y responde en cuanto cambia la
fase o a los 25 s). Viable —la ruta es síncrona y ocupa un hilo del *threadpool* por ficha abierta; el balanceador
corta a los 230 s— pero no más sencilla: reloj y `sleep` inyectables en los tests, una cota de hilos, y gana menos de
3 s de latencia. Queda fuera; el contrato `{"fase": …}` permite añadirla después cambiando solo la URL del JS.

## 5. C · El ⚠ de la partida

`aviso_partida_texto(agree: bool | None, *, kind: str | None, leida: str | None) -> str | None` (pura, en
`review_models.py` junto a `aviso_suma_importes`): solo si `agree is False`, `kind == "assigned"` y `leida`
recortada no vacía ⇒ «No coincide con la partida leída en el albarán (<leida>)»; si no, `None`.

Repositorio: en `_build_display_lines` (~L4641, filas `from_albaran`) `_conc.aviso_partida = aviso_partida_texto(
_conc.agree_partida, kind=_conc.kind, leida=line.codigo_imputacion)`. En `_synthetic_to_display` (~L4787) no se pone
(queda `None`): sintéticas, `manual` y `reparto` nunca llevan ⚠ (R21). `agree_partida` se sigue calculando igual en
las dos (R23; lo usan el ✓ y F-076).

Plantilla: la clase `cedit-warn` de la casilla (~L742) pasa de `c.agree_partida == false` a `c.aviso_partida`
(`cedit-ok` sigue con `agree_partida == true`); la rama `{% elif c.agree_partida == false %}` del ⚠ de solo lectura
(~L749) pasa a `{% elif c.aviso_partida %}`. El `title` de las dos: `{{ c.descripcion_partida or '' }}` y, con
`c.aviso_partida`, un salto de línea y el aviso (nota 2026-10-17 (implementación, aceptado en review): « · » en vez del salto,
`[descripción, nota F-076, aviso] | select | join(' · ')`). `marcarPartida` (F-065 R27 v5) guarda el `title` en
`data-titulo-antes` y lo devuelve: R23 sale gratis; un test con node lo fija.

## 6. D · Motivos del alta visibles y legibles

- `alta_sigrid_models.py`: `TEXTOS_MOTIVO_ALTA: dict[str, str]` con la lista cerrada del Anexo A de
  `progress/spec_F-077.md` y `texto_motivo_alta(codigo)` (`http_\d{3}` ⇒ «sigrid-api respondió con HTTP <NNN>»;
  desconocido ⇒ el código). En `AltaSigridVista`, `motivos_documento`, los `motivos` de cada fila de `lineas` y el
  nuevo `motivos_linea_sueltos` (motivos con `referencia_linea` que no está entre las de `lineas`) devuelven cada
  motivo con una clave más, `texto` (R26, R28).
- `review_models.py`: `posiciones_filas_ficha(display_lines) -> dict[int, int]`: `valuation_line_id` ⇒ posición
  (desde 1) entre las `display_lines` con `concilia`, en su orden: las filas que pinta la tabla
  (`{% if dline.concilia %}`, ~L712), la misma numeración que F-065 R20 obtiene con `orden_filas_ficha`.
- `domain/services/alta_sigrid.py`: `motivos_linea_vista(alta, posiciones) -> list[dict]` con `linea` («Línea 3» o
  «Línea (ref. 386)»), `texto`, `detalle`, `codigo`; `get_document` lo guarda en `alta_motivos_linea` (R24, R25).
- `_alta_sigrid.html`: cada motivo (documento, fila de la tabla, suelto) se pinta `<li title="{{ m.codigo }}">{{
  m.texto }}{% if m.detalle %} · {{ m.detalle }}{% endif %}</li>` (en la tabla, `<div>` igual); los sueltos con
  «{{ m.linea }}: » delante y después de los del documento; la `<ul>` sale si hay de alguno de los dos. En fase
  distinta de `resultado`, ninguno.
- R27 (catálogo completo): el test lee como texto los ficheros de sv9 (no los importa: sv4 y sv9 tienen
  paquetes de primer nivel con el mismo nombre) y extrae `Motivo("<codigo>"`, las claves de los dos mapas de
  `clasificador.py` (`"<codigo>": _NO_ADMITIDO|_REVISAR|_ERROR`), las constantes `CODIGO_* = "<codigo>"` y los
  valores de `TipoFallo` de `alta_models.py` (también se lee).
- RED (fichero D): el caso real literal (`no_admitido`, `falta_descripcion` ref `"386"`, sin petición ni respuesta)
  ⇒ «Línea N: La línea no tiene descripción» con N la posición de la fila 386; sin esa fila ⇒ «Línea (ref. 386)»;
  motivo de una línea de la petición ⇒ solo en su fila, con texto; motivo de documento ⇒ texto legible y código en
  `title`; código desconocido tal cual; `http_503`; catálogo completo (R27).

## 7. Tests de F-065 y F-053 que cambian y por qué

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
Ningún test de F-053 debería cambiar de expectativas: `alta_fase` vale `"resultado"` por defecto, los códigos de
motivo siguen en el HTML (en el `title`) y `estado_texto` sigue saliendo con la clase `error`. Si alguno compara los
dicts de `motivos_documento` o `lineas` por igualdad, se adapta a la clave `texto` nueva (anotarlo en el informe).

## 8. Ficheros que NO se tocan

- Servidor de guardado: `MergeDocumentUpdatePayload`, el PUT, el PATCH de fila, `_exigir_editable`, el cerrojo de
  F-053 R25, R20 de F-065 (R11).
- `wireDividir`, F7 y la fila activa (**F-068**); `wirePartidaCombos`, `partidasMalas`, `cargarPartidasObra`.
- `/api/sigrid/partidas` y `infrastructure/sigrid/*` (**F-076** R15); `_agree_txt`, `_txt`, `_partida_del_contrato`
  (**F-076** R23 los cambia).
- `puede_solicitar_alta` / `puede_reintentar_adjunto` (el panel solo decide cuándo enseñar sus botones); el listado
  (F-053 R31); sv9, sv3, sv6, comun.

## 9. Solapes con otras ramas

- **F-076** (`feature/F-076-normalizar-partidas`, spec en curso). Su R15 rehace `/api/sigrid/partidas` con los mismos
  `items`: F-077 solo los consume. Su **R23** cambia `agree_partida` para comparar por la clave normalizada de comun
  (`CI.04.18` ≡ `CI.4.18` ⇒ ✓) en las mismas líneas del repositorio (~L4641, ~L4787), y su **R24** añade al mismo
  `title` de la casilla y del span «Normalizada: X → Y». Semántica compatible: `aviso_partida` se deriva de
  `agree_partida` sea cual sea la comparación, y la nota de F-076 y el ⚠ de F-077 son excluyentes. Conflicto de
  **texto** en `review_repository.py` y `document_detail.html`: quien fusione segundo deja el `title` como
  «descripción ⏎ [nota F-076] ⏎ [aviso F-077]». F-077 no toca nada de F-076. Nota 2026-10-17 (implementación, aceptado en review):
  fusionó F-077 y el separador quedó « · » (el de F-076), no «⏎».
- **F-068** (pendiente): `wireDividir`/F7 en `app.js`, otra zona. **F-058**: sin relación directa.

## 10. Riesgos y decisiones

- **D1 · Parar al primer fallo** (no seguir con las demás filas como «Guardar todas»): «si alguna no se puede
  guardar, se para»; seguir dejaría más estado parcial sin aprobar nada.
- **D2 · Consolidar en vez de recargar tras un fallo**: recargar perdería lo tecleado en la fila en rojo y en las
  siguientes; consolidar evita el 409 al reintentar.
- **D3 · Aviso de suma releído tras guardar**: el `data-aviso-suma` se calcula al pintar; tras guardar filas sería
  falso. Descartado recalcularlo en el cliente (duplicaría `suma_leida` y `aviso_suma_importes`).
- **D4 · Fases con tope de 5 min desde la aprobación** (humano, PARADA 1): «en curso» solo mientras sv9 procesa; un
  resultado malo es un error, nunca «en curso»; sin respuesta en 5 min, error de tiempo honesto.
- **D5 · Recargar la página al cambiar de fase** en vez de repintar el panel: la ficha aprobada es de solo lectura y
  no hace falta una ruta que renderice el fragmento.
- **D6 · Una sola función de PATCH** para los tres guardados. **D7 · «Línea N»** con la posición en la tabla.
- **R-1 · «Guardar» con `?buscar_si_cambia=1`**: si cambió CIF u obra, la revaloración descarta lo editado (F-058).
  Es el comportamiento de hoy.
- **R-2 · Fuera de alcance**: «Solicitar alta» sin reaprobar no pasa por `en_curso` hasta que sv9 marca la fila (la
  vieja se ve unos segundos, como hoy); el listado sigue pintando el estado guardado.
- **R-3 · Reloj**: la fase compara el reloj de sv4 con el `approved_at_utc` que escribió el propio sv4.
- **R-4 · Mutación**: `harness.mutacion` muta Python (dominio, servicio, repositorio, ruta); el JS lo cubren los tests
  con node. Rigor `estandar`: no escribe en sistemas compartidos ni cambia lo que recibe sv9.
