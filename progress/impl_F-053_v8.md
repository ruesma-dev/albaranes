<!-- progress/impl_F-053_v8.md -->
# F-053 v8 · Bloque H (T41–T50, T52) · informe del implementer

Rama `feature/F-053-alta-sigrid` (worktree `albaranes-F-053`, con `dev` fusionado). Rigor **critico**. Spec v8
aprobada por el humano el 2026-10-14 (U1–U7 con la recomendación; `progress/spec_F-053.md` §«v8»). Un commit por
tarea: `ca717e8` T41, `754f651` T42, `de48d9b` T43, `0cb760f` T44, `9d4a5e3` T45, `aa60264` T46, `568600e` T47,
`8183771` T48, `1b3c8e5` T49, `77b6257` y `1c8b685` T50; T52 al final. En `azure-apps`: `77c6bf6` (sin push).

## 1. Qué cambió

**sv9** (`services/albaranes-alta-sigrid`)
- `domain/services/usuario_sigrid.py` (nuevo, T41): `candidato_usuario(approved_by)`: parte antes de la @ si es
  un correo `@ruesma.es` (sin distinguir mayúsculas, espacios alrededor recortados, una sola @, parte no vacía y
  ≤ 24); si no, `None`. La parte local va tal cual: se manda el `cod` que devuelve Sigrid.
- Puerto y cliente (T42): `buscar_usuario(cod)` por `sql/read` con `SELECT TOP (1) cod FROM dbo.usu WHERE cod = ?`
  (la de sigrid-api), devuelve el `cod` de la fila recortado o `None`, `truncated` no tolerado, reintentos de
  lectura y `SigridLecturaError` al agotarlos. `adjuntar_pdf(..., *, usu)`: el cliente ya no tiene usuario fijo.
- Servicio (T43): `AltaSigridService._resolver_usuario` es el **único punto** que decide el `usu` (R47–R48): el
  `cod` de Sigrid de quien aprobó o el Respaldo; lectura caída o Respaldo vacío ⇒ `UsuarioNoResuelto` ⇒ alta
  `error` `usuario_no_resuelto`, sin buscar altas a mano ni previa. Su docstring dice dónde entrará F-069 (antes de
  la parte local); no hay código especulativo. El `approved_by` llega en `Reclamacion.approved_by`, que `decidir`
  copia del merge leído bajo el cerrojo (R5). Un `incierto` retomado no relee `dbo.usu` (R15). El adjunto, también
  `solo_adjunto`, usa el `usu` de `peticion_json`; si no lo hay, no llama y deja el adjunto en error (R22).
  `validar_y_construir(datos, config, hoy, usu)`; `ConfigAlta` ya no lleva `usu`. **Orden**: el usuario se
  resuelve antes de la validación local (design §5.3).
- Configuración (T44): `ALTA_SIGRID_USUARIO` → `ALTA_SIGRID_USUARIO_RESPALDO` (`Settings.usuario_respaldo`, sin
  defecto en código: vacía), aviso de arranque si DESDE está puesta y el respaldo vacío o en blanco;
  `.env.example`, `sv9.md`.
- R14 normalizado (T45): `normalizar_referencia` y `SEPARADORES_REFERENCIA` en `validador_alta.py`; el SQL de
  `buscar_albaranes` se construye con los MISMOS separadores (`UPPER(REPLACE(...))` sobre `d.entref`) y el cliente
  manda el número normalizado; si queda vacío, no consulta (casaría con los `entref` vacíos).

**sv4** (`services/albaranes-front`)
- R49 (T46): `_reviewer_from_request(request, propuesto)` = cabecera `X-MS-CLIENT-PRINCIPAL-NAME` > formulario o
  cuerpo > `DEFAULT_REVIEWER`. «Aprobar» del listado la usa con el formulario; el PUT `/api/documents/{id}` recibe
  `Request` y pone el resultado en `payload.approved_by`. Borrar sigue como estaba (formulario > cabecera).
- «Reintentar adjunto» (T47): regla pura `puede_reintentar_adjunto` (con `_documento_admite_alta` compartida con
  `puede_solicitar_alta`), `ReviewService.puede_reintentar_adjunto` / `reintentar_adjunto_sigrid` (publica
  `accion="alta"`), ruta `POST /documents/{id}/alta-sigrid/reintentar-adjunto` y sus mensajes; la ficha lleva
  `alta_puede_reintentar_adjunto`. No escribe en BBDD: R25 no la bloquea.
- Panel (T48): `AltaSigridVista.approved_by` (lo lee el repositorio del alta), `usu` (de `peticion_json`) y
  `usu_respaldo` (no es la parte local de `approved_by`, sin distinguir mayúsculas); `_alta_sigrid.html` enseña
  «Usuario de Sigrid: `<usu>` (respaldo)» y el botón.

**infra** (T44): `00_capps_vars.ps1` con `$Global:ALTA_SIGRID_USUARIO_RESPALDO = "pgris"` (U5, versionado);
`create_capps_sv9.ps1` y `set_alta_sigrid.ps1` pasan la variable nueva (el segundo la relee de sv9 y falla si está
vacía); `README_capps.md`. Ningún `*.local.ps1` tocado. CRLF y BOM conservados.

**Documentación** (T49): `sv4.md` (§12 punto 10 y §13.5 cerrados, `DEFAULT_REVIEWER` solo local), `sv9.md`
(usuario y R14), `docs/ARCHITECTURE.md` (regla 19), `azure-apps/albaranes.md` §10 (commit `77c6bf6` en su repo).
**sigrid-api no se ha tocado**: las filas de consumo del contrato que citan `ALTA_SIGRID_USUARIO` (y la de R14, cuya
consulta cambia) van como propuesta exacta en `progress/propuestas_a_sigrid_api_F-053.md` §C, para que el líder
las coordine. No cambia la forma de F-009 ni la configuración de sigrid-api.

## 2. Decisiones de diseño (y lo que no dice la spec)

1. `Reclamacion.approved_by` en vez de releer el merge: `decidir` ya recibe el `EstadoDocumento` leído bajo el
   `FOR UPDATE`; así hay una sola fuente (U2) y el repositorio SQL no cambia de sentencias.
2. El Respaldo vive en el servicio (`usuario_respaldo`, obligatorio en el constructor) y no en `ConfigAlta`: así
   `validar_y_construir` recibe el `usu` ya resuelto y nada puede usar el respaldo por error.
3. La parte local NO se pasa a minúsculas: se manda el `cod` que devuelve Sigrid (si la intercalación es CI, como
   es lo habitual, `PGris` encuentra `pgris`). El `cod` devuelto se recorta (por si `cod` fuera `CHAR`).
4. `max_rows` 2 en `buscar_usuario` (como `existe_concepto`): no depende de cómo marca `truncated` sigrid-api.
5. Adjunto sin `usu` en la petición guardada (no debería pasar: toda alta registrada tiene petición): no se llama y
   queda `adjunto_no_colgado` con detalle `usuario_no_resuelto`, en vez de llamar con un `usu` vacío.
6. sv4 `usu_respaldo`: un `approved_by` sin @ (p. ej. `DEFAULT_REVIEWER`) nunca casa ⇒ «(respaldo)», como en sv9.
7. Desviación menor: T42 dejó un paso intermedio (`usu=self._config.usu` en el adjunto); T43 lo sustituyó, con RED.

## 3. Fase RED (comandos y salida real, recortada)

T41 — `python -m pytest -q -k f053_r47_candidato` (desde sv9), primero sin módulo y luego con un stub que devolvía
`None`:
```
E   ModuleNotFoundError: No module named 'domain.services.usuario_sigrid'
E       AssertionError: assert None == 'a'
E        +  where None = candidato_usuario('a@ruesma.es')
5 failed, 14 passed, 534 deselected in 2.71s
```
T42 — `python -m pytest -q -k "f053_r47_cliente or f053_r22_adjunto_lleva or f053_r22_el_cliente or
buscar_usuario_es_del or cinco_operaciones"`:
```
E       AttributeError: 'SigridApiAltaClient' object has no attribute 'buscar_usuario'
E       TypeError: SigridApiAltaClient.adjuntar_pdf() got an unexpected keyword argument 'usu'
E       AssertionError: assert 'buscar_usuario' in frozenset({'adjuntar_pdf', 'alta_albaran', 'buscar_albaranes', 'existe_concepto'})
16 failed, 552 deselected in 6.48s
```
T43 — `python -m pytest -q tests/test_f053_r47_servicio.py` (con el constructor y el campo nuevos aún sin usar):
```
E       AssertionError: assert ('buscar_alba...000000000002') == ('buscar_usuario', 'Ana')
E       AssertionError: assert ['USU_ALTA'] == ['pgris']
E       AssertionError: assert None == 'ana@ruesma.es'   (Reclamacion.approved_by)
E       AssertionError: assert <EstadoAlta.SIMULADO: 'simulado'> is <EstadoAlta.ERROR: 'error'>
23 failed in 2.82s
```
T44 — `python -m pytest -q tests/test_f053_r47_config.py`:
```
E                   AttributeError: 'Settings' object has no attribute 'usuario_respaldo'
E       AssertionError: assert ('ALTA_SIGRID_USUARIO_RESPALDO vacío' in '... ALTA_SIGRID_USUARIO vacío: sigrid-api rechazará las altas\n') is True
E       assert 'ALTA_SIGRID_USUARIO_RESPALDO' in '# 00_capps_vars.ps1 ...'
10 failed, 2 passed in 6.74s
```
T45 — `python -m pytest -q -k f053_r14` (con un stub de `normalizar_referencia` que no normalizaba):
```
E       AssertionError: assert '2.172.946' == '2172946'
E       AssertionError: assert '26/28193' == '26-28193'
E         + f = ? AND d.entref = ? AND ISNULL(d.synckey, '') <> ?
12 failed, 8 passed, 599 deselected in 5.60s
```
T46 — `.venv\Scripts\python -m pytest -q tests/test_f053_r49_revisor.py` (sv4):
```
E       At index 0 diff: ('f053-t18-doc', True, 'falso@ruesma.es') != ('f053-t18-doc', True, 'ana@ruesma.es')
E       AssertionError: assert ['revisor-local'] == ['ana@ruesma.es']
4 failed, 11 passed, 1 warning in 10.64s
```
(los 11 que pasan son el camino local sin cabecera, que ya funcionaba; fallan justo los 4 con cabecera).
T47 — `.venv\Scripts\python -m pytest -q tests/test_f053_r30_reintentar_adjunto.py` (sin la función y después
con stubs que decían «no»):
```
E   ImportError: cannot import name 'puede_reintentar_adjunto' from 'domain.services.alta_sigrid'
E       AssertionError: assert False is True
E        +  where False = puede_reintentar_adjunto('f053-t20-doc')
10 failed, 14 passed, 1 warning in 5.56s
```
T48 — `.venv\Scripts\python -m pytest -q tests/test_f053_r29_panel_usu.py`:
```
E                   AttributeError: 'AltaSigridVista' object has no attribute 'usu'
E       assert None == 'Usuario de Sigrid: <code>pgris</code> (respaldo)'
15 failed, 3 passed in 5.88s
```
Todas en verde tras su código (salidas en los commits de cada tarea).

## 4. Verificación real

- sv9: `python -m pytest -q` ⇒ **621 passed** (534 antes de la v8; +87).
- sv4: `.venv\Scripts\python -m pytest -q` ⇒ **1350 passed** (1302 antes; +48).
- Raíz: 1083 passed (sin cambios).
- `bash harness/init.sh` (T52): ver §7.
- **No** se ha arrancado sv9 contra sigrid-api real, ni se ha llamado a sigrid-api, Azure ni BBDD; los tests del
  cliente usan `httpx.MockTransport`. `ALTA_SIGRID_COMMIT` no se ha tocado. `.env` y `*.local.ps1`, intactos.

## 5. Mutación (T50) y cobertura

Pasada 1: solo la campaña a mano (`progress/mutacion_F-053_v8.md`, 64 mutantes). La review pidió además la de la
herramienta, la tabla reproducible y las demostraciones de los equivalentes: ver §«Pasada 2». Cobertura de líneas
cambiadas: `PUERTA COBERTURA: 100.0% de 128 líneas cambiadas cubiertas`.

## 6. Fuera del alcance y lo que falta

- **T51 (MANUAL del humano)**: comandos exactos en `progress/current.md`; antes, review y fusión. La §C de
  `propuestas_a_sigrid_api_F-053.md` la coordina el líder con la sesión de sigrid-api.
- F-069 (lista de equivalencias correo → login): no implementada; entrará en `_resolver_usuario`.
- Riesgos (spec §v8): UPN que no es `cod` ⇒ respaldo `pgris` (visible en el panel); intercalación de `dbo.usu` y
  `dca.entref` sin medir; la función sobre `d.entref` impide su índice (va tras `entcif`, una consulta por alta).
- Siguen pendientes de antes: T26–T28, T27b, T27c, T29 (MANUAL) y la propuesta de `CLAUDE.md` de design §9.

## 7. `bash harness/init.sh` (T52)

`bash harness/init.sh` sobre `1c8b685` (más este informe, `current.md` y la fila del inventario de mutación):
**`ENTORNO LISTO. Puedes trabajar.`** (exit 0). Raíz **1083 passed** en 241,1 s (con cobertura); sv4 **1350
passed** (196,6 s) y sv9 **621 passed** (48,8 s), medidos en la pasada anterior sobre el mismo código (esta los da
por caché: «árbol sin cambios desde el último verde»); sv1, sv2, sv3, sv5, sv6 y comun en verde (caché).
`PUERTA COBERTURA: 100.0% de 128 líneas cambiadas cubiertas (128/128, umbral 80%, nivel critico)`;
`PUERTA TAMAÑO` dentro de los topes; avisos de siempre (ruff 1262, deuda previa; infra sin tests; `[ADAPTAR]` de
F-034/F-035). La pasada anterior salió en rojo por un único test de la raíz,
`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`: faltaba la fila de `mutacion_F-053_v8.md` en
`progress/inventario_mutacion_F-039.md`; añadida (recuento 33).

## Pasada 2 (review `progress/review_F-053_v8.md`, CHANGES_REQUESTED solo por la mutación)

Commits `4be8eb2` (cambio 3), `a558b02` (cambios 1 y 4) y el de informes. O1, O2 y F-070 sin tocar.

**Cambio 3 · el mutante 38 no era equivalente.** `_reviewer_from_request` devolvía `DEFAULT_REVIEWER` sin recortar:
el merge quedaba igual, el `MensajeFeedback` no. Arreglo en `app.py`: `return (settings.default_reviewer or
"").strip() or None`. RED — `.venv\Scripts\python -m pytest -q tests/test_f053_r49_revisor.py` con el test nuevo y
el código viejo:
```
E       AssertionError: assert [' revisor-local '] == ['revisor-local']
FAILED tests/test_f053_r49_revisor.py::test_f053_r49_default_reviewer_recortado[listado-None]
FAILED tests/test_f053_r49_revisor.py::test_f053_r49_default_reviewer_recortado[ficha-   ]
6 failed, 17 passed, 1 warning in 26.30s
```
(listado y ficha × sin propuesta, vacía, en blanco; merge Y mensaje). Tras el arreglo, 23 passed.

**Cambio 1 · campaña de la herramienta** (`python -m harness.mutacion --feature F-053 --salida
progress/mutacion_F-053_v8_arnes.md`, completa, 4 workers). Primera sobre `4be8eb2`: 66 mutantes, **63 muertos, 3
supervivientes**, 1864,5 s. Los tres eran huecos de test (ningún equivalente); `test_f053_v8_supervivientes_arnes.py`
los mata. RED de cada uno, con su mutante aplicado al código y el fichero nuevo:
```
review_models.py:1456 bool = False -> True       E   AssertionError: assert True is False      2 failed, 6 passed
app.py:473 .strip() or None -> .strip() and None E   AssertionError: assert [{... 'solicitado_por': None}] == [{... 'revisor-local'}]   4 failed, 4 passed
app.py:1771 include_in_schema=False -> True      E   AssertionError: assert '/documents/{document_id}/alta-sigrid/reintentar-adjunto' not in {...}   1 failed, 7 passed
```
(#1: con DESDE vacía o en una vista de proveedor la ficha no ofrece «Reintentar adjunto»; #2: «Solicitar alta» sin
cabecera publica el defecto recortado, el servicio no lo rellena en ese camino; #3: las rutas de formulario del alta
no salen en el OpenAPI). **Campaña final sobre `a558b02460d113e41dbc4bacb53f4a6b4ccf84ab`: 66 mutantes, 66 muertos,
0 supervivientes, 0 timeouts, 2416,6 s, 4 workers.** Es la evidencia de C4 bis.

**Cambio 2 · tabla manual reproducible** (`progress/mutacion_F-053_v8.md`): texto completo original → mutado en las
64 filas (sin «…»), anexo JSON con cada sustitución exacta, fila 25 de «Supervivientes … cerrados» corregida,
tiempo total **2965,6 s en serie, 1 worker** (más 347,0 s de la re-medida de los 7 vivos). Se conserva como
complemento (plantilla y texto SQL).

**Cambio 4 · RM5.** `services/albaranes-front/tests/test_f053_v8_equivalentes.py`, patrón de
`test_f053_t25_equivalentes.py` (módulo real, variante con el texto exacto, fuente normalizada, control): **#50**
sobre 320 combinaciones de `desde` × aprobado × activo × 8 `approved_at_utc` × 5 altas en las tres funciones,
idénticas; control `<` → `<=` distinto. **#38** (tras el cambio 3) con `app.py` real y su variante en `build_app`,
cabecera × formulario/cuerpo × `DEFAULT_REVIEWER` (5 × 5 × 5) por listado y PUT: mismo merge y mismos mensajes;
control `return propuesto` distinto. 2 passed (54 s). Los dos equivalentes esperan la aceptación escrita del humano.

**Verificación**: `bash harness/init.sh` ⇒ `ENTORNO LISTO` (exit 0): raíz 1083 passed; **sv4 1366 passed** (502,3 s,
entera); sv9 621 (caché: sin cambios desde la pasada 1); `PUERTA COBERTURA: 100.0% de 129 líneas` (critico).

## Evidencias

| Evidencia | Valor |
|---|---|
| Tests ejecutados | pasada 2: sv9 621 passed; sv4 1366 passed; raíz 1083 passed; resto en verde (caché) |
| Cobertura de líneas cambiadas | 100.0 % (128/128), umbral 80 %, nivel critico |
| Mutantes generados / supervivientes | **Herramienta**: 66 generados, 66 muertos, 0 supervivientes (`progress/mutacion_F-053_v8_arnes.md`, 4 workers, 2416,6 s; la primera, 63/66). **A mano** (complemento): 64, 62 muertos, 2 equivalentes demostrados (`progress/mutacion_F-053_v8.md`, 1 worker, 2965,6 s) |
| Tiempo de la suite | pasada 2 (máquina cargada): sv4 502,3 s; raíz 753,6 s; sv9 48,8 s (pasada 1). Pasada 1: sv4 196,6 s; raíz 241,1 s |
