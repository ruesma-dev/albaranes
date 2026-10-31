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
| Suite de sv4 en `init.sh` | 2186 passed, 1 warning (antes de F-114: 2131 + el RED) |
| Cobertura de líneas cambiadas | **100,0 %** de 54 líneas (54/54, umbral 80 %) — `PUERTA COBERTURA` |
| Mutación (muestreada, 20, semilla 20260820) | 20 evaluados, 19 muertos, 1 superviviente, 0 timeouts, 1.713 s; el superviviente (`include_in_schema`) matado por un test nuevo ⇒ **0 vivos**. Detalle: `progress/mutacion_F-114.md` |
| Tiempo de la suite | sv4 419,9 s; F-114 sola: cliente 0,95 s, endpoint ~5 s, plantilla 1,4 s, JS ~13,5 s |

La mutación solo cubre Python (cliente, modelos, endpoint); el JS (`app.js`) no lo muta la herramienta: lo
cubren los 15 tests con node, con la fase RED de T4 y T5.

## 7. `bash harness/init.sh` final (T9)

`bash harness/init.sh` **tal cual** (sin `PYTHONPATH` ni `ARNES_SIN_CACHE`) sobre `da1e7c5`: **exit 0, verde**.
Arnés 1919 passed; sv1 236; sv2 496; sv3 1576; **sv4 2186 passed, 1 warning**; sv5 125; sv6 506 (1 skipped);
sv9 1073; comun en verde (caché). `PUERTA COBERTURA` 100,0 % (54/54); `PUERTA TAMAÑO` dentro (impl 145/220).

La primera pasada de T9 (sobre `8c0562d`) salió en rojo por **un** test del arnés,
`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`: `progress/mutacion_F-114.md` no figuraba en
`progress/inventario_mutacion_F-039.md`. Arreglado añadiendo su fila (veredicto `VÁLIDA`, 60 informes) en
`da1e7c5`; ese test pasa (`9 passed`) y la segunda pasada, entera, en verde.

## 8. T8 (líder, 2026-10-31) y su arreglo

**Resultado de la T8** (Chrome, sv4 local sobre `dev` `1c4b8fb`, solo lectura, sin elegir; la hizo el líder): bien
el check marcado por defecto, la lista de la obra intacta al volver a marcarlo, el rótulo al desmarcar, 50
resultados por nombre con «Hay más proveedores…», el aviso con 2 letras, `50%_!` con 200 y «· 2 fichas en
Sigrid» buscando por CIF; ninguna escritura. **FALLO contra D2**: la SQL filtraba por nombre ANTES del
`GROUP BY v.cif`, así que `COUNT(*)` y `MIN(v.raz)` solo veían las fichas que casaban: un CIF vivo con 2 fichas
de razón social distinta salía con `fichas: 2` por CIF y `fichas: 1` (sin aviso) por el nombre de una.

**Arreglo, versión 1** (`3272e04`, tras avanzar la rama a `dev` `1c4b8fb` sin conflictos): subconsulta
`v.cif IN (SELECT m.cif … fichas vivas que casan)`. Correcta, pero el líder la midió vía sigrid-api (solo
lectura, mismas 5 búsquedas, mismo momento): **4,5–5,2 s por búsqueda frente a 0,7–1,0 s** de la anterior
(salvo una búsqueda de 3 caracteres alfanuméricos, ≈4 s con todas las variantes): 5 veces más lenta por tecleo.

**Arreglo, versión 2 (la que queda)** (`4630aad`, propuesta del líder): una sola pasada; el texto pasa del
`WHERE` al `HAVING MAX(CASE WHEN <nombre LIKE> OR <cif LIKE> THEN 1 ELSE 0 END) = 1`. Se agrupan todas las
fichas vivas de cada CIF (nombre = la menor, fichas = todas) y sale si alguna casa. Medida por el líder con las
mismas búsquedas: **0,7–1,1 s**, como la original, y el CIF de 2 fichas sale con 2 buscando por nombre. Se
conservan `TOP (?)`, orden, `ESCAPE '!'`, `COLLATE`, todo por parámetro y solo lectura; **vuelven los 6
parámetros de design §3** (`[51, 5, 1, 0, nombre, cif]`): sin desviación de parámetros. Una ficha de baja, de
otro `tip` o de otra empresa que case NO trae su CIF (el `WHERE` ya las quita antes de agrupar). Único efecto
visible: el `MIN(raz)` mostrado puede no contener lo escrito (es el de otra ficha viva del mismo CIF).

**Fase RED** — `.venv/Scripts/python -m pytest tests/test_f114_cliente.py -q -p no:cacheprovider -k t8` (tests
nuevos que EJECUTAN la SQL sobre SQLite en memoria: `TOP (?)` ⇒ `LIMIT ?`, sin `COLLATE`; datos inventados):
```
E       AssertionError: assert ('B00000001', 1) == ('B00000001', 2)
E       AssertionError: assert [('B00000001'...STROS SL', 1)] == [('B00000001'...OBRAS SL', 2)]
2 failed, 2 passed, 26 deselected in 1.49s
```
(pasaban ya: «baja/ajena no trae el CIF» y «escape y límite ejecutados»). Verde con la versión 2: cliente +
endpoint + F-052, `49 passed`. Comprobado otra vez con la SQL original restaurada a mano: los mismos 2 tests
caen (`2 failed, 2 passed`); con la del `HAVING`, `4 passed`. `test_f114_r15_la_sql…` fija ahora el `HAVING`,
que el `LIKE` va después del `GROUP BY` y 6 `?`; ninguna aserción relajada.

**Mutación**: `progress/mutacion_F-114_T8.md` es de la versión 1 (`3272e04`): 1 mutante (el `0` del `fecbaj`
de la subconsulta), 1 muerto, 446,9 s. La versión 2 no añade líneas ejecutables mutables (solo el literal SQL y
quita parámetros): no se relanza. La SQL la cubren los 4 tests que la ejecutan sobre SQLite. Inventario: 61.

**Riesgo de rendimiento: retirado.** La versión 2 recorre `prv`+`con` una vez, como la original; el líder midió
0,7–1,1 s (T0: 1,2–1,6 s en otro momento).

**`bash harness/init.sh`** tal cual sobre `e80e645` (versión 2): **exit 0, «ENTORNO LISTO»**. Arnés 1919; sv1 236; sv2 496;
sv3 1576; **sv4 2190 passed** (+4 de la T8); sv5 125; sv6 506 (1 skipped); sv9 1073. `PUERTA COBERTURA`: N/A
(las líneas cambiadas frente a `dev` son la SQL y la lista de parámetros, sin sentencias nuevas). Tamaño: impl 191/220.

**T8 repetida (líder, 2026-10-31, Chrome, sv4 de la rama sobre `d8dac4b`, solo lectura, sin elegir): VERDE.** El CIF de 2 fichas sale con «· 2 fichas en Sigrid» también buscando por nombre; «Hay más» con 50 por nombre; volver a marcar el check recupera la lista de la obra; ninguna escritura. Tiempos a través de sv4: 0,7–0,8 s en repetición y ~4,5 s en algunas primeras búsquedas (la misma variación que tenía la SQL original en la T0 y en la medición del líder; es de Sigrid, no del HAVING).
