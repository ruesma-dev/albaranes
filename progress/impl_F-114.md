<!-- progress/impl_F-114.md -->
# F-114 · Informe del implementer (T1–T7 y T9)

Rama `feature/F-114-proveedor-todos-sigrid`, worktree `../albaranes-F-114`. Rigor `estandar`. Servicio: sv4.
Spec v1 con PARADA 1 cerrada el 2026-10-30 (D1–D7 según la recomendación; D6 ⇒ F-115). T0 la hizo el líder
(`ESCAPE '!'`). **Fuera de este trabajo**: T8 (MANUAL, navegador del líder) y el despliegue (humano).

## 1. Qué cambió (un commit por tarea)

| Tarea | Commit | Qué |
|---|---|---|
| — | `db97dd6` | Fusión de `dev` (`113b208`: F-113, F-106, comun 0.10.0); F-114 `in_progress`. Conflicto solo en `progress/current.md` (entradas de F-113/F-106 de `dev` + la de F-114). |
| T1 | `0a224a3` | `sigrid_lookup_client.py`: `_SQL_PROVEEDORES_TODOS` (la de design §3 con `ESCAPE '!'`), `MINIMO_BUSQUEDA_PROVEEDOR` 3, `LIMITE_BUSQUEDA_PROVEEDOR` 50, `TIP_PROVEEDOR` 5, `EMPRESA_RUESMA` 1, `_patron_like`, `buscar_proveedores`. `review_models.py`: `ProveedorOption.fichas` y `BusquedaProveedores`. |
| T2 | `73cb02e` | `app.py`: `GET /api/sigrid/proveedores/todos?q=` (`include_in_schema=False`). |
| T3 | `5ba60d8` | `document_detail.html`: `div.full-width.campo-combo` con cabecera (rótulo `#proveedor_combo_rotulo` + check `#proveedor_solo_obra` marcado), `data-solo-obra-check`, `data-endpoint-todos`. `styles.css`: `.campo-combo`, `.campo-combo-cabecera`, `.check-inline`. |
| T4 | `b12e085` | `app.js`: `textoBusquedaProveedor`, `urlProveedoresTodos`, `etiquetaProveedorGlobal`, `mensajeListaObraVacia`. |
| T5 | `64332c1` | `app.js` `initCombo`: modo global (debounce 300 ms, secuencia, «Hay más», `title` de varias fichas, `change` del check, R10, R11). |
| T6 | `46eeeef` | Viñeta en la regla 17 de `docs/ARCHITECTURE.md`; fila del endpoint en `sv4.md` §4.2. `azure-apps` **`7109c68`** (`albaranes.md` §8), **local, sin push**. |
| T7 | `5c1cf97` | Campaña de mutación + test que mata su superviviente (`progress/mutacion_F-114.md`). |

Ficheros de producción tocados (todos de sv4): `infrastructure/sigrid/sigrid_lookup_client.py`,
`domain/models/review_models.py`, `interface_adapters/web/app.py`, `templates/document_detail.html`,
`static/app.js`, `static/styles.css`. Tests nuevos: `tests/test_f114_cliente.py` (26), `test_f114_endpoint.py`
(9), `test_f114_plantilla.py` (5), `test_f114_js.py` (15). **Ningún test anterior tocado.** R22:
`git diff --stat dev...HEAD` sin ficheros fuera de sv4 y `docs/` (más `progress/`, `specs/`, `harness/`).

## 2. Decisiones de diseño y desviaciones (justificadas)

1. **Al enfocar en modo global, la caja trae la etiqueta del proveedor actual** («NOMBRE — CIF»): buscar ese
   texto no casaría con nada. `buscarGlobal` lo trata como «sin texto» y enseña el aviso de los 3 caracteres
   (R3) sin llamar. Design §5 dice «`focus` llama a `buscarGlobal()`»: se respeta, con esta regla dentro.
2. **Salir de la caja (blur) en modo global cancela la búsqueda pendiente o en vuelo** (`clearTimeout` +
   `++secuencia`). Sin ello, un debounce que vence tras el blur reabriría el panel con la caja ya fuera de
   foco. No lo pide ningún requisito literal; es la consecuencia directa de R4 («no pinta resultados viejos»).
   Test propio (`test_f114_r4_salir_de_la_caja_cancela…`).
3. **Lista de la obra en vuelo al cambiar el check** (R8): `ensureLoaded` guarda la `secuencia` y, si cambió
   al llegar la respuesta, la descarta (`loading = false`, lista vacía). En modo marcado sin tocar el check el
   comportamiento es el de hoy (R2): la secuencia no cambia.
4. **R10 «sin código de obra»** se detecta por el texto del error del endpoint (`/Falta el codigo de obra/`),
   que es el único que lo dice; se pinta como `combo-msg` (sin «⚠»). Otros errores de la lista: el aviso de hoy.
   Lista vacía: «Sin proveedores con contrato en la obra. Desmarca «Solo de la obra»…».
5. **`fichas` ausente o 0 cuenta como 1** al deduplicar (`int(fichas or 1)`): `COUNT(*)` nunca es 0; defensa.
6. **`.check-inline` con selector `.campo-combo .check-inline`**: `.form-grid label` (0,1,1) le ganaría a
   `.check-inline` (0,1,0) y lo pondría en columna. El rótulo es un `span`; el `label` solo envuelve el check.
7. **Funciones puras de JS autocontenidas** (el 3 y el texto de R10 literales dentro): los tests las sacan una a
   una con `_funcion_js`; una constante del módulo no viajaría con ellas.
8. **`ruff` no está instalado** en el venv de sv4 ni en el PATH del worktree: no se ha pasado el linter.

## 3. Fase RED (trazas reales)

Todas con `PYTHONPATH=C:\Users\pgris\PycharmProjects\albaranes-F-114\services\albaranes-comun` y el venv de sv4,
desde `services/albaranes-front`.

**T1** — `.venv/Scripts/python -m pytest tests/test_f114_cliente.py -q -p no:cacheprovider` (antes del código):
```
E       AttributeError: 'SigridLookupClient' object has no attribute 'buscar_proveedores'
E       AttributeError: module 'infrastructure.sigrid.sigrid_lookup_client' has no attribute 'MINIMO_BUSQUEDA_PROVEEDOR'
E       AttributeError: module 'infrastructure.sigrid.sigrid_lookup_client' has no attribute '_patron_like'
25 failed, 1 passed in 1.52s
```
(el que pasa es R21, la lista de la obra intacta: guarda, no requisito nuevo). Verde: `21 passed, 5 deselected`
con el `-k` de la tarea; el fichero entero, 26 passed.

**T2** — `.venv/Scripts/python -m pytest tests/test_f114_endpoint.py -q -p no:cacheprovider`:
```
E       assert 404 == 200
E        +  where 404 = <Response [404 Not Found]>.status_code
E       KeyError: 'ok'
7 failed, 1 passed, 1 warning in 4.33s
```
(pasa R21). Verde: `8 passed`.

**T3** — `.venv/Scripts/python -m pytest tests/test_f114_plantilla.py -q -p no:cacheprovider`:
```
E       ValueError: substring not found
E       ValueError: substring not found
E       ValueError: not enough values to unpack (expected 1, got 0)
E       AssertionError: assert None
E        +  where None = <function search ...>('\\.campo-combo\\s*\\{[^}]*display:\\s*flex;...', '/* static/styles.css */ ...')
4 failed, 1 passed in 2.12s
```
(pasa «solo lectura no pinta nada», que ya era cierto). Verde: `5 passed`.

**T4** — `.venv/Scripts/python -m pytest tests/test_f114_js.py -q -p no:cacheprovider -k "f114_r3 or f114_r6 or f114_r10"`:
```
E       ValueError: substring not found
E       ValueError: substring not found
E       ValueError: substring not found
3 failed in 0.52s
```
Verde: `3 passed in 0.41s`.

**T5** — `.venv/Scripts/python -m pytest tests/test_f114_js.py -q -p no:cacheprovider` (funciones de T4 ya
puestas, `initCombo` sin tocar):
```
E       AssertionError: assert ['Sin coincidencias'] == ['Sin proveed...es de Sigrid']
E       AssertionError: assert (['Cargando de Sigrid…'] == ['Escribe al ...re o del CIF']
E       AssertionError: TypeError: Cannot read properties of undefined (reading 'responder')
E       AssertionError: assert ['Sin coincidencias'] == ['ALFA SL — B... para afinar']
FAILED tests/test_f114_js.py::test_f114_r10_lista_de_la_obra_vacia_o_sin_obra
FAILED tests/test_f114_js.py::test_f114_r8_cambiar_el_check_vacia_cierra_y_conserva_la_etiqueta
FAILED tests/test_f114_js.py::test_f114_r3_desmarcado_busca_en_el_servidor_sin_refiltrar
FAILED tests/test_f114_js.py::test_f114_r4_debounce_de_300_ms_y_respuestas_viejas_descartadas
FAILED tests/test_f114_js.py::test_f114_r5_r6_hay_mas_y_varias_fichas - Asser...
FAILED tests/test_f114_js.py::test_f114_r8_la_lista_de_la_obra_en_vuelo_no_se_pinta_tras_desmarcar
6 failed, 8 passed in 3.44s
```
Los 8 que pasaban son los 3 de T4 y guardas que ya eran ciertas hoy (R2 modo marcado, R5 sin «más», R7
elegir y guardar, R9 sin `localStorage`, R11 errores): el combo de hoy ya lo hacía con la lista de la obra.
Los centrales (R3, R4, R5/R6, R8, R10) caen. Verde: `14 passed`; con el test del blur (decisión 2), `15 passed`.
Verificación de la tarea: `pytest services/albaranes-front -k "f051 or f065_f1_js or f065_f3bis"` (más
`f098_combo`, `f077`, `f106_js`): `365 passed, 1819 deselected`.

## 4. Verificaciones MANUAL pendientes

- **T8** (líder, Chrome, solo lectura): sv4 local, documento `097191e9-…` si está en la BBDD local; desmarcar,
  buscar por nombre y por CIF, ver «Hay más» y «N fichas»; **no elegir** (guardaría). Revisar también a ojo el
  aspecto de la cabecera (rótulo a la izquierda, check a la derecha; en pantalla estrecha, debajo).
- **Despliegue** (humano, tras APPROVED y fusión): solo sv4, `Set-DeployTag; .\deploy.ps1 -Only sv4`.
- **Publicar `azure-apps` `7109c68`** cuando el humano lo pida (sin push).

## 5. Entorno del worktree

- *Junction* `services/albaranes-front/.venv` ⇒ `.venv` de sv4 del árbol principal, creada con `mklink /J`.
  **Quitarla con `cmd /c rmdir` antes de `git worktree remove`.**
- `init.sh` de precondición, tal cual: único KO = el propio `test_f114_cliente.py` en RED (escrito mientras la
  suite corría); el resto en verde (sv4 `1 failed, 2131 passed`; comun `1316 passed`). Avisos de entorno:
  sv1 y otros importan la comun del árbol principal.

## 6. Evidencias

| Evidencia | Valor |
|---|---|
| Tests de F-114 | 55 (26 cliente + 9 endpoint + 5 plantilla + 15 JS), todos en verde |
| Suite de sv4 en `init.sh` | ver §7 |
| Cobertura de líneas cambiadas | ver §7 (`PUERTA COBERTURA`) |
| Mutación (muestreada, 20, semilla 20260820) | 20 evaluados, 19 muertos, 1 superviviente, 0 timeouts, 1.713 s; el superviviente (`include_in_schema`) matado por un test nuevo ⇒ **0 vivos**. Detalle: `progress/mutacion_F-114.md` |
| Tiempo de la suite | ver §7 |

La mutación solo cubre Python (cliente, modelos, endpoint); el JS (`app.js`) no lo muta la herramienta: lo
cubren los 15 tests con node, con la fase RED de T4 y T5.

## 7. `bash harness/init.sh` final (T9)

PENDIENTE de ejecutar en el momento de escribir esto; se completa abajo.
