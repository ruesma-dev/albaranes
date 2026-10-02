# F-052 · Review PARCIAL del Bloque A (T1–T6)

Revisión incremental desde 9d24b34 (pasada 2) hasta f766178. La pasada 1 revisó el
bloque completo (`git diff dev...a0bd84e`); su resumen queda abajo, condensado.

- **Veredicto del bloque (pasada 2):** APROBADO. CR-A1 y CR-A2 resueltos con RED real,
  O2 resuelto. No es veredicto de cierre de F-052.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`): fase RED,
  cobertura ≥ 80 % de lo cambiado, mutación con 0 supervivientes sin justificar y MANUAL
  con comando. Mutación (T19) y MANUAL (T20–T23) quedan fuera del bloque.

## Pasada 2 · verificación de las correcciones

Delta revisado (`git diff 9d24b34..f766178`): `lectura.py` (+9), `test_f052_sigrid_lectura.py`
(+23), `test_f052_resumen_obra.py` (+33/−6), `impl_F-052.md` (condensado), `current.md`.
Ningún cambio en el cliente de sv3 ni en el doble: lo aprobado en la pasada 1 no se toca.

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` (entero) | exit 0, ENTORNO LISTO; raíz `1067 passed in 543.30s` |
| Puerta cobertura | `[OK] 100.0% de 91 líneas cambiadas cubiertas (91/91, umbral 80%, nivel critico)` |
| Puerta tamaño | `impl 104/220` (O2 resuelto) |
| sv3 a mano, sin caché | `284 passed in 13.08s` |
| comun a mano, después | `308 passed in 69.20s` |
| ruff sobre los ficheros tocados | `All checks passed!` |
| Árbol tras las pruebas | limpio (todo en el scratchpad) |

**CR-A1 · test de R5 «mismo ganador»** (`test_f052_resumen_obra.py:154-192`). Ahora fija
por caso la decisión esperada, la nota esperada (o ninguna), una sola petición (la
agregada) y ningún `search_proveedores`. Verificado por mí en dos copias del scratchpad:

- contra el cliente de T4 (`6d9c795`): `3 failed` —
  `assert (None, 'deterministic') == ('B82899550', 'deterministic')`,
  `assert [] == [{'database':...}]`, `assert (None, 'deterministic') == ('B10000000', ...)`.
  Coincide con la RED del informe.
- **caso degenerado** (cliente de HEAD con `fetch_contratos_resumen_por_obra` lanzando
  siempre `RuntimeError`): `3 failed` — las dos decisiones esperadas y `assert 0 == 1`
  (peticiones) en `familia-sin-nombre`. Antes de CR-A1 ese caso pasaba: ya no.

**CR-A2 · `leer_paginado` con página de más filas** (`lectura.py:167-174`). La
comprobación va antes de acumular y de mirar `truncated`, y lanza `RuntimeError` con
etiqueta, página y recuentos (sin datos) con cualquier política. Test
`test_f052_r14_leer_paginado_pagina_con_filas_de_mas_lanza[TOLERA|NO_TOLERA]` con una
fuente de `tamano + 1`, que además fija que no se pide una segunda página. RED
reproducida por mí con la `lectura.py` de 9d24b34 por delante en `PYTHONPATH` (comprobado
el `__file__` cargado): `Failed: DID NOT RAISE RuntimeError` ×2 — `2 failed, 29 passed`.
Coincide con el informe.

**O2 · tamaño**: `impl_F-052.md` condensado a 104 líneas; conserva por tarea la línea
clave de cada RED, el commit y el recuento, las decisiones, las notas para el Bloque B
(incluida O1 para T16) y la sección «Evidencias» con sus números.

## Resumen de la pasada 1 (revisión completa, 2026-09-30)

Veredicto entonces: CAMBIOS por CR-A1 y CR-A2; el código de producción era correcto.

- **Verificación propia**: init.sh verde (`1067 passed`), cobertura 95/95, sv3 284 y
  comun 306 a mano; SQL agregada idéntica a design §4 (`diff` literal); RED de T4
  reproducida con el cliente de `dcf9292` (`7 failed, 1 passed`: `[500, 500] ==
  [500, 700]`, `1000 == 3543`, `assert 1000 > 5000`) y de T5/T6 con el de `6d9c795`
  (`9 failed, 10 passed`); dos mutantes propios muertos (M1 quitar el `sort` del
  resumen: 5 fallos; M3 `max_rows=tamano` en la página: 7 fallos).
- **`truncated` nunca en silencio**: `politica` keyword-only, sin defecto y tipada; las
  7 consultas con la política de design §3 (5 NO_TOLERA, 2 TOLERA), ninguna sin ella.
- **Paginación**: `max_rows = pagina + 1`, tope `max_paginas` → excepción; `ORDER BY`
  únicos (`header_and_lines` une solo por `ide`; `search_proveedores` sobre `DISTINCT`).
- **Doble**: `truncated = filas >= max_rows` (conservador frente a `sigrid_api.md` §6.1),
  400 con `OFFSET` sin `ORDER BY`, consulta antigua cortada a 1.000 sin SALMEDINA,
  barajado de lo no fijado por `OFFSET`. No pasa por construcción (RED y mutantes).
- **T6** compara el `texto` del cliente real sobre la vía agregada con el texto por
  líneas del código anterior, en 84 CIF y 4 casos dirigidos.
- **Consumidores**: puerto intacto; resolver y grounding en verde; sv4 (D6) sin tocar.

## Checkpoints (en lo aplicable al bloque)

- C1 [x] init.sh exit 0 (pasada 2); ficheros del arnés presentes.
- C2 [x] una sola `in_progress` (F-052), rama correcta. «current.md solo la sesión
  activa»: N/A en review de bloque — arrastra sesiones previas; lo resuelve el líder
  antes del cierre.
- C3 [x] hexagonal (`ruesma_comun.sigrid` puro; cliente en infraestructura; doble en
  `tests/`); primera línea con ruta; sin `print`, TODO, secretos, IPs ni GUID (barrido
  del diff); sin dependencias nuevas; sin tocar merge/raw, schema ni importes.
- C3 bis N/A: no toca `docs/referencia/`.
- C4 [x] R2–R5 y R7–R14 con tests `test_f052_rN_*` en verde; sin red ni BBDD.
  MANUAL T20–T23 listados en `current.md`, fuera del bloque.
- C4 bis [x] rigor `critico` declarado; [x] RED real en el informe y reproducida por mí
  (T4, T5/T6, CR-A1, CR-A2); [x] cobertura 91/91. N/A mutación y RM1–RM6: la campaña es
  T19, fuera del Bloque A por plan de `tasks.md`; no hay campaña que revisar.

## Trazabilidad requisito → test (Bloque A)

| Req. | Tests |
|---|---|
| R2 | `test_f052_r2_el_resumen_trae_los_81_*`, `_r2_paso_obra_familia_puntua_los_81` |
| R3 | `test_f052_r3_una_sola_peticion_*`, `_r3_truncado_lanza_y_no_pagina`, `_r3_sin_obra_no_consulta`, `_r3_un_resumen_por_cif_*` |
| R4 | `test_f052_r4_mismas_familias_por_cif_*[0691,0668]`, `_r4_el_fixture_no_es_trivial`, `_r4_casos_dirigidos` ×4 |
| R5 | `test_f052_r5_barajado_*` ×3, `_r5_mismo_ganador_*` ×3 (reforzado, CR-A1). «Red por nombre»: T7 |
| R7 | `test_f052_r7_politica_es_obligatoria_*`, `_r7_max_rows_opcional_*`, `_r7_politica_invalida_*` |
| R8/R9 | `test_f052_r8_*`, `test_f052_r9_*` (comun y cliente) |
| R10 | `test_f052_r10_consultas_no_tolera_*` ×5, `_r10_documentos_*`, `_r10_sin_truncado_*`, `_r10_docstring_*` |
| R11 | `test_f052_r11_fetch_contratos_1200_*`, `_r11_caso_normal_*`, `_r11_pagina_lineas_configurable` |
| R12 | `test_f052_r12_*_3543`, `_r12_hallazgo_el_max_rows_*`, `_r12_*_pagina_si_la_pagina_es_menor` |
| R13 | `test_f052_r13_*` (cliente y comun). Rastro `error`: T10 |
| R14 | `test_f052_r14_*` (comun), incluido `_pagina_con_filas_de_mas_lanza` (CR-A2) |

## Cambios requeridos

Ninguno. CR-A1 y CR-A2 de la pasada 1: resueltos (ver «Pasada 2»).

## Observaciones (no bloquean)

- **O1 · grounding**: con R12, `HeaderGroundingService` toma los 200 primeros por CIF de
  3.543 (antes, de una lista cortada a 1.000) y una respuesta truncada lanza. Anotado ya
  en el informe como tarea para T16 (`azure-apps/albaranes.md`).
- **O3 · `con_paginacion`** acepta cualquier `ORDER BY`, también uno interno; SQL Server
  rechazaría el `OFFSET` sin orden exterior, así que no es silencioso.
- **O4 · dedupe por CIF**: el orden es por punto de código, no por la collation de
  Sigrid; solo puede cambiar el nombre mostrado de un CIF con dos `raz`.
- **O5**: R5 «red por nombre» y R13 «rastro `error`» se cierran en T7 y T10.
- **O6 · redacción del informe**: la fila T4 de `impl_F-052.md:17` dice que la RED se
  lanzó «contra el código ORIGINAL», pero sale del cliente de T2 (`dcf9292`, que ya acepta
  `transport`): contra el original los 8 tests caerían por `TypeError` en el
  constructor. Los números son correctos (reproducidos); corregir la frase en el Bloque B.

## Propuesta de automejora (no aplicada)

`reviewer.md`, sección de fase RED: pedir que el reviewer mire también los tests que
**pasaron** en la traza RED de un requisito central y justifique por qué pasaban, y que
compruebe el test reforzado contra un caso degenerado (consulta que siempre falla). Fue
lo que destapó CR-A1 y lo que demostró su corrección.
