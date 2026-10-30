<!-- progress/impl_F-106.md -->
# F-106 · informe del implementer

Rama `feature/F-106-precio-al-cambiar-medicion` (worktree `../albaranes-F-106`). Rigor `critico`. Hechas T0–T21; no
se hacen aquí T22 (líder, Chrome), T23 y T24 (humano) ni la T25 final (líder con el reviewer).

## Lo hecho

| Tarea | Commit | Resumen |
|---|---|---|
| fusión / T0 | `dc9e4c2` / `0ca72d2` | `dev` 5dd1f45 en la rama; medición en producción (abajo) |
| T1 / T2 | `c93f1f4` / `546679f` | comun 0.10.0: `cuadra_linea`, `TOLERANCIA_CUADRE_EUR`, `linea_a_sigrid`, `recalcular_fila` |
| T3 / T4 | `3939d3f` / `7d8ca8f` | sv9: P y d en `LineaAlta`/`SQL_LINEAS`; `linea_no_cuadra` ⇒ `no_admitido`; petición con `linea_a_sigrid` |
| T5 / T6 | `8bc8578` / `50dcffd` | sv4 dominio: `importe` y `cuadrar` en el cuerpo, `recalculo_de_fila`, `no_cuadran` |
| T7 / T8 | `dc15389` / `041edb9` | sv4 PATCH con `importe` (despeja P) y `cuadrar`; 422 de R4 y R7 |
| T9 | `f83c1f3`, `bef559b` | regresión del PATCH; dos tests de F-065 R8 declarados (enmienda del humano) |
| T10 | `4d80f3f`, `a5322fa` | R16 al aprobar; almacén = fila sin partida (humano); fixtures de F-075/F-078 declarados |
| T11 | `287fe41`, `11f8546` | ficha: rojo con la cuenta, botones, «≠ albarán», «A Sigrid», precio hasta 6 decimales (R15 literal) |
| T12 | `b3f32c0` | JS: P a 6, rojo sin despejar, `importe` o P en el PATCH, repintado, botones; texto de `linea_no_cuadra` |
| T13 / T14 | `e1c8dfc` / `418a1d3` | comun fase B: `EdicionManual`, `registrar_edicion`, `leer_edicion`, `aplicar_edicion`, `es_fila_manual` |
| T15 / T16 | `08cee12` / `32578fc` | sv6: columna `edicion_manual_json`; `replace_valuation` con `FOR UPDATE` y reaplicación (R23–R28) |
| T17 / T18 | `e988163` / `23490f7` | sv4 fase B: las nueve vías registran la edición, «✋», «Volver a lo calculado», 409 de R28 |
| T19 | `86141a4` | `scripts/listar_altas_descuadradas_f106.py` de sv9 (solo `SELECT`) |
| T20 | `dc725e8` + azure-apps `9a369c3` | ARCHITECTURE reglas 13, 20, 22, 25 y acceso a datos; sv4.md, sv6.md, sv9.md; `azure-apps/albaranes.md` |
| T21 | `eb579da`…`cc850d3`, `0babedb` | mutación (`progress/mutacion_F-106.md`) y 16 tests que matan supervivientes |

Ficheros de producción: comun `importes.py`, `alta_sigrid.py`, `edicion_manual.py` (nuevo), `__init__.py`,
`pyproject.toml`; sv9 `alta_models.py`, `sql_alta_repository.py`, `validador_alta.py`,
`scripts/listar_altas_descuadradas_f106.py` (nuevo); sv6 `schema_contribution.py`, `orm_valuation_models.py`,
`sqlalchemy_valuation_repository.py`; sv4 `review_models.py`, `alta_sigrid_models.py`, `review_repository.py`,
`review_service.py`, `app.py`, `document_detail.html`, `app.js`, `styles.css`.

## Tests de features anteriores tocados (todos en R31 o sin tocar aserciones)

Declarados en R31:
- `test_f065_f1_js.py`: `importe_solo_ajusta_el_precio` ⇒ `{"importe": 1000}` (R12), y en T18 los dos textos de
  `avisoRevalorar` («Revalorar conserva N líneas puestas a mano», R30).
- Los dos de F-065 R8 (clave `importe_calculado`).
- Los fixtures de `test_f075_r9…` y `test_f078_r17…` (R16).
- `test_f065_r9_plantilla…` (`value="120.00"`, R15).
- `test_f065_bloqueada_ddl.py::test_f065_r17…` (R27).

Sin tocar ninguna aserción, solo el esquema de los fixtures para que tengan las columnas de producción:
- `tests/conftest.py` y `tests/f053_sv4_bbdd.py` de sv4 llevan `edicion_manual_json`.
- `conftest.py` lleva `producto_sigrid`. La columna existe en producción desde F-053 y la lectura de la edición la nombra.

`test_f051_r16_todas_en_un_unico_update` no cambia: almacén escribe la edición en el MISMO UPDATE (CASE por id), así
que sigue siendo una sola sentencia.

## Decisiones de diseño (y desviaciones, justificadas)

Fase A (pasadas 1–3):
1. `importe` o `cuadrar` a `null` ⇒ 422 (vaciar el importe no encaja en D1). Importe + precio ⇒ 422 ya en el cuerpo.
2. Un importe igual al de hoy se descarta (F-065 R8) salvo que cambien Q o d en el mismo PATCH (entonces manda).
3. Un P despejado igual al actual no es un precio cambiado (no pasa a Nueva por redondeos).
4. `NoDespejable` se calcula antes de escribir. sv9 compara con Q = convertida ?? albarán. P y d de `LineaAlta`
   llevan defecto `None`, así que la petición sale idéntica a la de hoy.
5. Equivalente #6 de F-053 T25 rehecho: la línea se movió a comun y ya no es equivalente.
   `test_f098_t5_version_090` pasa a «≥ 0.9.0 y pyproject igual»; la versión exacta la exige `test_f106_t2_version_0100`.
6. Ficha y botones: solo las filas a registrar se pintan en rojo; el `title` del precio junta «Precio del contrato» y
   «A Sigrid»; los botones mandan solo `{cuadrar}` por `enviarFila` (guardar = bloquear); sin `ultimoCampo` y con el
   importe cambiado, viaja el importe; `linea_no_cuadra` = «La línea no cuadra (cantidad × precio × (1 − dto) ≠ importe)».
7. `syncImporteUnitario` sigue anidada en `wireConciliaEdit`, su único llamador. Sacada fuera rompía los tests de
   F-065 f3bis, que extraen `wireConciliaEdit` sin ella.

Fase B (T13–T18):
8. La edición guarda cada campo como `{columna: valor}` de sus columnas. La firma es `registrar_edicion(previa, *,
   fila_antes, fila_despues, campos, fila_entera)`, por palabras clave, en vez del `(previa, fila_antes, cambios)` del
   design.
9. `calculado` lleva además `precio_unitario_source` y `_agreement` (el «origen» del design §5). Sin ellos, «Volver a
   lo calculado» desde Nueva dejaría `agreement = manual` y la fila seguiría contando como tocada.
10. `aplicar_edicion` conserva el I editado si no se puede despejar (Q 0): la fila no cuadrará y R16 la para.
11. sv6:
    - Solo se recalculan `total_valorado` y `total_lines`; los demás contadores quedan como salen de sv6.
    - Una fila conservada con blanca sustituye a la nueva de esa blanca.
    - `codigo_externo` (columna de sv4) se escribe con un UPDATE tolerante.
    - La fila legada se reconoce también por `bloqueada`.
12. Qué registra el PATCH:
    - Los campos cambiados.
    - Con el P despejado (importe tecleado o «Recalcular precio»), `importe` y no el precio.
    - Si eso pasa la fila a Nueva (R8), también `origen`: sv6 tiene que recrear la derivada (R27).
    - «Recalcular importe» registra `cantidad`: es «como cambiar Q» (R9) y sv6 rehará I.

    Por eso cambié dos tests RED míos de T17, de `["importe"]` a `["importe", "origen"]`, y añadí
    `test_f106_r20_recalcular_importe_guarda_la_cantidad`. Otro test RED usaba `mode="derived"`, que no existe; pasa a
    `mode="nueva"`.
13. «+ a Sigrid» sobre una blanca ya valorada reapunta la fila y registra `origen`; si la crea, `fila_entera`.
    Dividir registra en la original `cantidad`, y también `codigo_partida` y `origen` si cambian.
14. «Volver a lo calculado» no exige la fila desbloqueada: desbloquear es parte de volver. Da 404 sin edición o en una
    `fila_entera`. Si la línea calculada ya no existe, no se restauran ni el origen ni la fuente del precio.
15. Fila desaparecida en el PATCH ⇒ `ValoracionCambiadaError` (409). Una fila de otro documento sigue siendo 404.
16. Script R18: «precio difiere» si `|enviado − P(1 − d)| × |cantidad enviada| > 0,02 €` (la tolerancia del cuadre, para
    que el redondeo a céntimos no liste media base); solo altas `modo = 'real'`; sin fila o ilegibles, no se comparan.

## Propuesta al líder (D11)

F-058 («lo manual se pierde al revalorar») queda **absorbida** por la fase B de F-106 (R19–R30, D11; ya anotado en
`de8e289`). Propongo marcarla así en `features.json` al cerrar F-106. Yo no he tocado `features.json`.

## Fase RED (trazas reales)

Comando y salida resumida de cada RED, en el orden de `tasks.md` (PYTHONPATH a la comun del worktree). sv4 usa
`.venv/Scripts/python.exe`:

```
### T1 RED: python -m pytest tests/test_f106_cuadre.py -q (comun)
E   ImportError: cannot import name 'linea_a_sigrid' from 'ruesma_comun.alta_sigrid'   — 1 error during collection
### T3 RED: python -m pytest tests/test_f106_validador.py -q (sv9)
     11 E   TypeError: LineaAlta.__init__() got an unexpected keyword argument 'precio_unitario_final'
      1 E   AssertionError: assert PeticionAlbaran(... cantidad=48.0, precio=2.17, ...) ==
            [Motivo(codigo='linea_no_cuadra', detalle='48 × 11,2 × (1 − 7 %) = 499,97 ≠ 104,16', referencia_linea='7')]
      14 failed, 1 passed
### T5 RED: pytest tests/test_f106_fila.py -k dominio -q (sv4)
     16 E   ImportError: cannot import name 'recalculo_de_fila' ; 15 E Failed: DID NOT RAISE ValidationError
      38 failed
### T7 RED: pytest tests/test_f106_fila.py -q (sv4)
     22 E   TypeError: AlbaranReviewRepository.update_line_conciliacion() got an unexpected keyword argument 'cuadrar'
      25 failed, 43 passed  (los 43: dominio de T6 y los 422 del cuerpo)
### T10 RED: pytest tests/test_f106_aprobar.py -q (sv4)
      4 E   Failed: DID NOT RAISE LineasIncompletasError ; 1 E assert [] == [2, 4]
      6 failed, 5 passed  (los 5: lo que ya se aprobaba)
### T11 RED: pytest tests/test_f106_ficha.py -q (sv4)
E   ImportError: cannot import name 'a_sigrid_de_fila' from 'domain.models.review_models'   — 1 error during collection
### T12 RED: pytest tests/test_f106_js.py tests/test_f065_f1_js.py -q (sv4)
     13 E   ValueError: substring not found   (precioDespejado, precioASigrid, avisoImporte… no existen en app.js)
      1 E   KeyError: 'linea_no_cuadra'
      1 E   AssertionError: assert {'precio_unitario': 125} == {'importe': 1000}
### T13 RED: pytest tests/test_f106_edicion.py -q (comun)
E   ImportError: cannot import name 'EdicionManual' from 'ruesma_comun.edicion_manual'   — 1 error during collection
### T15 RED: pytest tests/test_f106_reaplicar.py -q (sv6)
     12 E   sqlite3.OperationalError: no such column: edicion_manual_json
      4 E   [SQL: UPDATE albaran_line_valuations SET cantidad_albaran = ?, cantidad_convertida = ?, edicion_manual_json = ? ...]
### T17 RED: pytest tests/test_f106_edicion.py -q (sv4) — 37 de 38 en rojo
     18 E   KeyError: 'edicion_manual_json'
      5 E   AttributeError: 'AlbaranReviewRepository' object has no attribute 'volver_a_calculado'
      3 E   ImportError: cannot import name 'texto_edicion' ; 2 E ImportError: cannot import name 'ValoracionCambiadaError'
      1 E   assert (404 == 200) ; 1 E assert '>✋ añadida a mano<' in '<!-- templates/document_detail.html -->...'
      1 E   AssertionError: assert [None, 'Reval... ¿Continuar?'] == [None, 'Reval... ¿Continuar?'] ; 1 E assert 0 >= 1
### T19 RED: python -m pytest tests/test_f106_script.py -q (sv9)
E   ImportError: cannot import name 'listar_altas_descuadradas_f106' from 'scripts'   — 1 error during collection
```

La traza de T3 es el caso AC26/30435: sin F-106, sv9 manda 48 × 2,17 en vez de rechazarla.

GREEN:

| Tarea | Tests | Resultado |
|---|---|---|
| T2 | | 244 passed |
| T4 | | 15 passed |
| T6 | | 38 passed |
| T8 | | 68 passed |
| T14 | `test_f106_edicion` (comun) | 41 passed |
| T16 | `test_f106_reaplicar` | 18 passed |
| T18 | `test_f106_{edicion,fila,ficha,js}` + `test_f065_f1_js` | 184 passed |
| T19 | `test_f106_script` | 19 passed |

## Suites completas (una cada vez, `ARNES_SIN_CACHE=1`, comun del worktree)

| Suite | Resultado | Tiempo |
|---|---|---|
| sv4 tras T18 | **2111 passed** (ver nota) | 410 s |
| sv6 tras T18 | 498 passed, 1 skipped | 33 s |
| comun `test_f106_edicion` tras T18 | 41 passed (la suite entera, en `init.sh`) | 5 s |
| sv9 tras T19 | 1062 passed, 1 failed: el KO de entorno de abajo | 108 s |

Nota sobre sv4: la primera pasada dio 30 rojos (19 de F-051 por `producto_sigrid` en el fixture; 10 de f3bis y 1 de
F-077 por `syncImporteUnitario`), arreglados sin tocar aserciones; la segunda, 2111 passed.

**KO de entorno del worktree (no del código)**: `sv9 test_f069_t15_script_arranca_fuera_de_sv9…` lanza un script en un
subproceso con el entorno vacío. Sin `PYTHONPATH`, coge la comun editable del árbol principal (`../albaranes`, 0.9.0,
sin `linea_a_sigrid`) ⇒ `ImportError`. Es el caso que aceptaron F-053 y F-062: se verifica en el árbol principal tras
fusionar en `dev`.

## `bash harness/init.sh` (2026-10-30, sobre `0babedb`)

- **Tal cual**: rojo, 4 KO, todos del entorno del worktree. sv4, sv6 y sv9 importan la comun editable del árbol
  principal (0.9.0) y mueren en la recolección (`ImportError`); con eso la cobertura baja al 19,1 %.
- **Con `PYTHONPATH` a la comun del worktree y `ARNES_SIN_CACHE=1`** (como F-086 y F-098): **1 KO, el ya aceptado**
  (sv9 `test_f069_t15_script_arranca…`); el resto en verde. Raíz 1919, sv1 205, sv2 485, sv3 1576, sv4 2131, sv5 125,
  sv6 506 (+1 skipped), comun 1191 (+3 skipped). `PUERTA COBERTURA` 85,5 % (657/768), `PUERTA TAMAÑO` en verde.
  `init.sh` corre con `-x`, así que sv9 paró en ese test (903 passed); sv9 entera sin `-x`: **1 failed (ese), 1072 passed**.

## T0 · cuántas líneas pendientes no cuadran (2026-10-28, solo lectura)

Medido contra la BBDD `albaranes` de Azure en solo lectura (`SHOW transaction_read_only` = `on`). La clave solo vivió
en `$env:PG_PASSWORD` y se borró en `finally`. Solo `SELECT` y recuentos.

- 57 documentos pendientes, 50 con valoración.
- U1: 5 de 98 filas no cuadran (5,10 %), todas `declared_albaran`, en 2 documentos. Bajo el umbral del 10 % (R-1).
- U3 (las que pinta la ficha, sin almacén): 4 de 78.
- Filas legadas (R27) en pendientes: 16 filas en 8 documentos.

Las 5 que no cuadran quedan paradas por R16 y R17 al aprobar, como dice la spec («no les busques una salida»).

## Falta

- Humano: aceptar (o no) los 5 mutantes equivalentes de `progress/mutacion_F-106.md` (nivel `critico`).
- T22 (líder, Chrome con el pipeline local).
- T23 (humano): el script R18 contra Azure, solo lectura.
- T24 (despliegue, lo hace el humano): comun 0.10.0 ⇒ sv6 → sv9 → sv4.
- T25 final: `init.sh` en verde con el reviewer.
- Verificar en el árbol principal, tras fusionar, el test de entorno de sv9 (`test_f069_t15_script_arranca…`).
- Antes de `git worktree remove`: quitar la *junction* `.venv` de sv4 con `cmd /c rmdir`.
- Marcar F-058 como absorbida (propuesta de arriba).

## Evidencias

| Evidencia | Valor (medido) |
|---|---|
| Tests ejecutados | 9041 passed (+4 skipped) en `init.sh` con `PYTHONPATH` + 169 de sv9 sin `-x`; 1 failed (el KO de entorno aceptado) |
| Tests nuevos de T21 | `test_f106_t21_supervivientes.py` (sv4): 16 passed, 3,8 s |
| Cobertura de las líneas cambiadas | **85,5 %** (657/768, umbral 80 %, nivel `critico`) |
| Mutación (`progress/mutacion_F-106.md`) | **325** generados y evaluados: 302 muertos, **21 supervivientes**, 2 timeouts, 43 509 s en serie |
| Supervivientes tras el análisis | 16 muertos por tests nuevos (repetidos a mano); **5 equivalentes** justificados, **pendientes del sí del humano** (nivel `critico`): sv6 `:537` y `:541`, `alta_sigrid.py:167`, `importes.py:306`, `review_repository.py:2307` |
| Mutante 164 interferido (`edicion_manual.py:316`) | repetido a mano: MUERTO (2 failed en comun) |
| Tiempo de las suites (con `PYTHONPATH`) | raíz 501 s, sv4 431 s, comun 179 s, sv9 64 s (40 s sin `-x`), sv6 37 s |

Desviación de la campaña: `PYTEST_ADDOPTS` deselecciona solo el test de entorno de sv9 (si no, la base de sv9 sale en
rojo y la herramienta aborta). Detalle en `progress/mutacion_F-106.md` § «Condiciones de la campaña».
