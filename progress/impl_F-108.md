<!-- progress/impl_F-108.md -->
# F-108 · Informe del implementer

Fecha y número de albarán editables con calendario. Solo **sv4**. Rama
`feature/F-108-fecha-numero-editables` (worktree `../albaranes-F-108`), con
`dev` fusionado el 2026-10-31 (`281ebdb`: F-106, F-113, F-114, F-115; único
conflicto en `progress/current.md`, de texto, resuelto conservando las dos
partes). Rigor `estandar`. PARADA 1: D1–D7 = (a).

## 1. Qué cambió

| Tarea | Commit | Qué |
|---|---|---|
| T1 | `5f4987b` | `domain/services/fecha_albaran.py` (nuevo): `normalizar_fecha_albaran`, `normalizar_numero_albaran`, `es_fecha_guardada_valida`, `fecha_para_ver`, `AVISO_FECHA_NO_VALIDA`, `MAX_NUMERO_ALBARAN`. Errores `FechaAlbaranNoValidaError`, `NumeroAlbaranNoValidoError`, `CabeceraIncompletaError` en `review_models.py` |
| T2 | `4531087` | `update_document_y_transicion`: fecha y número normalizados antes de escribir nada (R5–R9) |
| T3 | `1c985f6` | `app.py`: 422 con `detail` de texto para los dos errores; filtro Jinja `fecha_albaran_ver` |
| T4 | `b7d2ba3` | `_exigir_cabecera_completa` en la ficha y en `set_approved` (R11); `CabeceraIncompletaError` en el 409 de la API/formulario y en `approve_from_list` |
| T5 | `96810df` | Plantilla: `#fecha` en `dd/mm/aaaa` con `placeholder`, botón «Calendario», `#fecha_calendario` `type=date`, `#fecha-error`; `#numero_albaran` con `maxlength="128"` y `autocomplete="off"`; aprobado sin calendario. `conftest.py` registra el filtro real. CSS `.campo-fecha`, `.fecha-calendario` (opacidad 0, nunca `display:none`), `.fecha-calendario.visible`, `.campo-no-valido` |
| T6 | `c86aa1b` | `app.js`: `avisoFechaNoValida`, `parseFechaEs`, `fechaParaVer`, `fechaParaEnviar`, `marcarFechaNoValida`, `limpiarMarcaFecha`, `fechaEscritaValida`, `wireFechaAlbaran`; `collectPayload` manda `fechaParaEnviar()` |
| T7 | `844405d` | Guarda de `guardarCabecera` (R18), al principio, antes de desactivar botones y de guardar filas |
| T8 | `372b5a0` | Viñeta en la regla 20 de `docs/ARCHITECTURE.md` y §11.0 de `sv4.md` |
| T9 | `b35c996` | `progress/mutacion_F-108.md` |

`azure-apps/albaranes.md` no cambia (lo que sv4 expone y consume es lo mismo;
la forma del PUT no cambia, solo su validación). Nada en sv3, sv9, comun, DDL
ni colas (R26).

Ficheros de producción: `domain/services/fecha_albaran.py`,
`domain/models/review_models.py`, `infrastructure/database/review_repository.py`,
`interface_adapters/web/app.py`, `templates/document_detail.html`,
`static/app.js`, `static/styles.css` (todos bajo `services/albaranes-front/`).
Tests nuevos: `test_f108_fecha_albaran.py`, `test_f108_guardado.py`,
`test_f108_ficha.py`, `test_f108_fecha_js.py`.

## 2. Decisiones de diseño

- **Regla de lectura**: dos expresiones ASCII (`re.ASCII`: sin él `\d` de
  Python admite cifras de ancho completo y la de JS no) con `fullmatch`
  (`$` de Python casa antes de un `\n` final) y `datetime.date` para los días
  que no existen y el año 0. En JS, sin `Date` (años 0–99, zona horaria):
  bisiesto y días del mes a mano. La tabla `CASOS` (33 filas) es la misma
  para los dos lados (R20).
- **El aviso de R3** vive en `fecha_albaran.py`; el error lo recibe ya armado
  (`FechaAlbaranNoValidaError(texto, aviso)`) para que `review_models` no
  importe del servicio (sería circular). `{texto}` es lo escrito recortado.
- **Aviso de R11 con dos faltas**: «No se puede aprobar: falta la fecha del
  albarán; falta el número de albarán» (la spec solo da los textos sueltos;
  con una sola falta es exactamente el de la spec).
- **Fecha guardada solo con espacios** cuenta como «falta» (no como «no
  válida»); `" 2026-10-28"` guardada (con espacio) cuenta como no válida.
- **`fechaEscritaValida`** no para nada si no hay `#fecha` o es `readOnly`
  (ficha aprobada, o los tests viejos sin campo).
- **`change` del selector sin día** no borra lo escrito.

## 3. Desviaciones respecto a la spec (justificadas)

1. **Orden de R11**: design §3 dice «junto a `_exigir_lineas_completas`».
   Se comprueba **lo último** al pasar a aprobado (tras líneas y contrato
   vigente). Así los tests de F-065 R20, F-078 R17, F-106 R16 y F-115 R13, que
   aprueban con payloads sin fecha para fijar SUS avisos, siguen viendo su
   aviso; ponerlo primero obligaba a tocar ~10 tests más sin ganar nada.
2. **Fixtures compartidos**: con R11, los 58 tests de aprobar de la suite
   caían (sus documentos no tenían fecha). `f053_sv4_bbdd._merge` gana
   `fecha="2026-10-08"`; `CABECERA` de `f053_sv4_bbdd` y `f065_bbdd` gana
   `fecha` y `numero_albaran`. Por el kwarg duplicado, `test_f053_t21b_valorado`
   y `test_f065_r3_put_aprobando…` pasan a `**{**CABECERA, "numero_albaran": …}`;
   `test_f115_r13_guardar_y_aprobar_con_el_mismo_contrato_aprueba` añade fecha y
   número a su payload. Ninguna aserción relajada.
3. **Tests de JS viejos** (`test_f065_f1_js` R1, `test_f077_guardar_y_aprobar_js`,
   `test_f065_f3bis_front` R27v5): añaden las funciones nuevas a su lista de
   funciones extraídas (`collectPayload` y `guardarCabecera` las llaman). Sin
   cambiar aserciones.
4. **`<dd>` de solo lectura** (design §3, «línea ≈984»): es la de las vistas
   crudas (`is_editable` falso). Sigue `{{ document.fecha }}` por R23 y §4.4; el
   aprobado de la vista merge usa el `input readonly` con el filtro (R22).
5. **T6 implementó también el calendario** (`wireFechaAlbaran` entero): los
   tests de R14, R15 y R21 de T7 nacieron en verde; su RED se demuestra con la
   mutación inversa (§4).
6. *Junction* `services/albaranes-front/.venv` → la del árbol principal
   (quitarla con `cmd /c rmdir` antes de `git worktree remove`).

## 4. Fase RED (trazas reales)

Comando base (desde `services/albaranes-front`, con
`PYTHONPATH=C:\Users\pgris\PycharmProjects\albaranes-F-108\services\albaranes-comun`):
`.venv/Scripts/python -m pytest <fichero> -q --tb=line -p no:cacheprovider`.

**T1** `tests/test_f108_fecha_albaran.py`:
```
E   ModuleNotFoundError: No module named 'domain.services.fecha_albaran'
61 failed in 1.10s
```
**T2** `tests/test_f108_guardado.py`:
```
E   AssertionError: assert '28/10/2026' == '2026-10-28'
E   AssertionError: assert '28-10-26' == '2026-10-28'
E   AssertionError: assert '05/06/2026' == '2026-06-05'
E   Failed: DID NOT RAISE FechaAlbaranNoValidaError
E   Failed: DID NOT RAISE NumeroAlbaranNoValidoError
7 failed, 7 passed in 2.65s
```
**T3** (`-k "f108_r7 or f108_r9"`): sin manejador, el error sale del PUT:
```
E   domain.models.review_models.FechaAlbaranNoValidaError: Fecha del albarán no válida: «31/02/2026». Escríbela como dd/mm/aaaa (p. ej. 28/10/2026) o elígela en el calendario.
E   domain.models.review_models.NumeroAlbaranNoValidoError: El número de albarán no puede pasar de 128 caracteres
4 failed, 5 passed, 9 deselected, 1 warning in 4.26s
```
**T4** (`-k f108_r11`):
```
E   Failed: DID NOT RAISE CabeceraIncompletaError        (x11)
E   domain.models.review_models.CabeceraIncompletaError: No se puede aprobar: falta la fecha del albarán
13 failed, 4 passed, 18 deselected, 1 warning in 5.31s
```
**T5** `tests/test_f108_ficha.py`:
```
E   assert 'value="09/10/2026"' in '<input type="text" id="fecha" value="2026-10-09">'
E   assert 'maxlength="128"' in '<input type="text" id="numero_albaran" value="AB-12">'
E   AssertionError: no está el botón del calendario
E   AssertionError: .campo-fecha
7 failed, 4 passed, 1 warning in 20.61s
```
**T6** `tests/test_f108_fecha_js.py`:
```
E   AssertionError: faltan en app.js: ['avisoFechaNoValida', 'parseFechaEs', 'fechaParaVer', 'fechaParaEnviar', 'marcarFechaNoValida', 'limpiarMarcaFecha', 'fechaEscritaValida', 'wireFechaAlbaran']
E   AssertionError: assert 'fecha: fechaParaEnviar(),' in 'function collectPayload(markApproved) {...'
17 failed in 13.87s
```
**T7** (R18, antes de la guarda):
```
E   assert ['PATCH /api/...odigo":null}'] == []      (Guardar y Guardar y aprobar)
E   ValueError: substring not found                 (la guarda no existe en guardarCabecera)
4 failed, 27 passed in 16.21s
```
**T7, mutación inversa** (R14, R15, R21 nacidos en verde): `app.js` con el
`click` del botón y el `change` del selector desenganchados y un `keydown`
con `preventDefault` en `#fecha`; `-k "f108_r14 or f108_r15 or f108_r21"`:
```
E   AssertionError: assert {'abiertos': ...': '28-10-26'} == {'abiertos': ...': '28-10-26'}
E   AssertionError: assert {'visible': F...se, 'dia': ''} == {'visible': T... '2026-06-05'}
E   AssertionError: assert {'roja': True...02/2026', ...} == {'roja': Fals...11/2026', ...}
E   AssertionError: assert ['fecha:Enter...fecha:/', ...] == []
E   AssertionError: wireFechaAlbaran
8 failed, 1 passed, 22 deselected in 1.30s
```
(`app.js` restaurado después; `git diff` vacío.) Tras cada código: verde
(61, 35, 11 y 31 passed en los cuatro ficheros nuevos).

## 5. Verificación

- Suite de sv4 completa tras T4 (fixtures ajustados): `2348 passed` (los 7
  rojos restantes eran la RED de T5, aún sin código).
- Tests de JS afectados (f065_f1_js, f077, f065_f3bis, f108_fecha_js): `137 passed`.
- `node --check static/app.js`: sin errores de sintaxis.
- `bash harness/init.sh`: ver «Evidencias».

## 6. Fuera del alcance / pendiente

- **M1** (líder): Chrome y Edge sobre sv4 local, guion de design §7 (incluido
  `showPicker` real, que el DOM falso no puede probar, y el `SELECT` de la
  fecha guardada).
- **M-D** (humano): `Set-DeployTag; .\deploy.ps1 -Only sv4` desde `infra/`.
- **M2** (líder, solo lectura en producción) y **M3** (humano: `ae044452…`,
  `6ae1d618…`, D5 = no migrar), **T11** (`init.sh` de cierre).
- Fuera por decisión: listado en `dd/mm/aaaa` (D3), aviso de fecha poco
  plausible (D6), regla en comun (D7).

## Evidencias

`bash harness/init.sh` (con `PYTHONPATH` a la comun del worktree y
`ARNES_SIN_CACHE=1`) sobre `67f355b`: **verde, exit 0**. Una primera pasada
dio KO en la raíz (`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`:
faltaba la fila de `mutacion_F-108.md` en `progress/inventario_mutacion_F-039.md`);
añadida la fila (y el recuento: 63) en `67f355b`, la segunda pasada salió verde.
Después (`2abe295`), `ruff --fix` de orden de imports y 4 avisos (`BLE001`,
`RUF059`) en los tests nuevos, sin cambiar lo que comprueban: `ruff` limpio en
los ficheros de F-108 y sus 138 tests en verde.

| Evidencia | Valor real |
|---|---|
| Tests ejecutados | raíz 1919 passed; sv1 236, sv2 496, sv3 1608, **sv4 2386 passed** (1 warning), sv5 125, sv6 506 (+1 skipped), sv9 1073, comun 1342; 0 fallos |
| Tests nuevos de F-108 | 138 (61 dominio, 35 guardado/rutas, 11 ficha, 31 JS con node) |
| Cobertura de líneas cambiadas | **100,0 %** de 104 líneas (104/104, umbral 80 %, `estandar`) |
| Mutantes | 20 muestreados de 35 (semilla `20260820`, 4 workers, sobre `372b5a0`): **20 muertos, 0 supervivientes**, 0 timeouts (`progress/mutacion_F-108.md`); ningún superviviente que analizar |
| Tiempo de la suite | sv4 377,80 s; raíz 462,83 s; campaña de mutación 1559,9 s |
| Topes | requirements 97/150, design 191/250, impl dentro de 220 |

`ruff` global: 1432 avisos en la pasada verde (deuda previa más los 6 de
F-108, ya corregidos).

## M1 · navegador (líder, 2026-11-01)

sv4 del worktree en local (BBDD local, Azurite), Chrome, albarán local pendiente `cfd43549…` y uno aprobado `385ce560…`:

- La ficha enseña `11/06/2024` (guardada `2024-06-11`); fecha y número admiten escritura; botón «Calendario».
- `28-10-26` + Tab ⇒ `28/10/2026`.
- `31/02/2026`: F7, F8, Enter y Escape con el foco en el campo no hacen nada (foco y texto intactos, sin envío); Tab ⇒
  campo en rojo con aviso; «Guardar» ⇒ aviso «Fecha del albarán no válida: «31/02/2026». Escríbela como dd/mm/aaaa
  (p. ej. 28/10/2026) o elígela en el calendario.» y 0 `PUT` en el log de sv4.
- «Calendario» con `15/10/2026` escrito: el selector se abre en `2026-10-15`; elegir el 20 escribe `20/10/2026` (el
  selector nativo no sale en las capturas de la extensión: la elección se simuló sobre el `input type=date`).
- «Guardar» ⇒ la ficha recarga con `20/10/2026`; en BBDD local `fecha = '2026-10-20'`.
- Aprobado: fecha y número `readonly`, sin botón de calendario.
- **Edge no probado** (la extensión solo maneja Chrome): queda para el humano junto con M2.

## M-D y M2 · producción (2026-11-01)

- M-D (humano): sv4 `r20261101-0929`, `check_deploy` en orden, arranque limpio en los logs.
- M2 (líder, solo lectura, sin Guardar, Aprobar ni Valorar): `ec291d76…` enseña `09/10/2026` (guardada `2026-10-09`);
  ya está **aprobada**, así que sale en solo lectura y sin calendario, como manda R22. La parte editable se comprobó en un
  pendiente de la bandeja (`c7ca52cc…`): campo editable, botón «Calendario» que abre el selector y 0 peticiones `/api/` al
  cerrarlo; pestaña cerrada sin guardar.
