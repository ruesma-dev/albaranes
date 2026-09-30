Revisión completa (pasada 1) del Bloque C: `git diff fb7cf75..8f502c6` (lo aprobado de A y B, hasta fb7cf75, queda dado por bueno)

# F-052 · Review PARCIAL del Bloque C (T11, T12, T13, T13 bis, T15, T17 · sv4)

- **Veredicto del bloque:** CAMBIOS (CHANGES_REQUESTED). No es veredicto de cierre de F-052.
- **Nivel de rigor:** `critico` (declarado en `harness/features.json`): fase RED, cobertura
  ≥ 80 % de lo cambiado, mutación sin supervivientes sin justificar y MANUAL con comando.
  La campaña (T19) y las MANUAL (T20–T23) quedan fuera del bloque por el plan de `tasks.md`.

## Verificación propia

| Qué | Resultado real |
|---|---|
| `bash harness/init.sh` (entero) | exit 0, ENTORNO LISTO; raíz `1067 passed in 286.10s`; servicios en verde (caché) |
| Puerta cobertura | `[OK] 98.0% de 252 líneas cambiadas cubiertas (247/252)`; las 5 sin cubrir son el cableado de `app.py` |
| Puerta tamaño | `requirements 150/150, design 250/250, impl 195/220` |
| sv4 a mano, sin caché | `341 passed in 10.80s` |
| RED T13 (test de HEAD sobre `d1cf760`, copia) | `9 failed, 2 passed`: coincide con el informe |
| RED T17 (test de HEAD sobre `3ec5cb4`, copia) | `5 failed, 5 passed`: coincide con el informe |
| Árbol tras las pruebas | limpio (`git archive` al scratchpad) |

**Mutantes propios** (copias de HEAD, los 6 ficheros `test_f052_*` de sv4, 94 tests), **6/6
muertos**: R1 plantilla sin `sin_datos` en el aviso con contratos (2 failed), R2 rastro con CIF
y obra cruzados en `_rastro_busqueda` (5), R3 «buscando» sin mirar `?buscando` (3), R4 el
desfase ignora el CIF (11), R5 `_sellar` sin best-effort real (7), R6 fecha del sello a `None` (3).

## Revisión por tarea

- **T12** (`busqueda_contratos.py`): los 5 estados según design §5; `desfasada` manda sobre el
  resultado (un rastro viejo que falló no se pinta como `error` de los datos de hoy: correcto);
  resultado desconocido → `sin_rastro`, nunca «no hay contrato». CIF con la misma regla que
  sella sv3 (`strip().upper().replace(" ", "")`, comprobado en
  `contrato_enrichment_service.py:137`). **La obra no**: ver CR-C1.
- **T11**: ORM con las 4 columnas y las mismas longitudes que el DDL de sv3 (64/32/16/64,
  `phase2_ddl.py:110-116`; test que las ata). `update_document` devuelve
  `get_document_detail` → `_build_merge_detail`, así que el detalle que usa D4-A en
  producción sí lleva `busqueda_contratos` (no solo en el doble del test).
- **T13** (plantilla): R23 con CIF, obra y fecha **del rastro**; R24 con «todavía no se han
  buscado» también con contratos listados; R25 «falló … no significa que no haya contrato»;
  R26 «no consta» con los datos actuales solo como tales. El bug de SS-0026122 (pintar el CIF
  actual con el resultado de otro) queda cerrado en la rama `desfasada`: la RED lo muestra.
  Jinja autoescapa los valores del rastro.
- **T13 bis (D4-A)**: relanza solo con `desfasada`, nunca al aprobar ni sin `refetch_client`;
  sin cambio no publica (6 casos, incluido el normalizado). Misma vía que «Guardar y volver a
  buscar» (`ColasRefetchClient`, `force=True`, test con publicador falso). Cola sin cablear:
  el publicador nulo devuelve `False` → outcome `sigrid_error`, sin «buscando…», el guardado
  se queda (`app.py:227-236`). Excepción al relanzar: guardado intacto y aviso con
  `logger.exception`. Sondeo de `app.js`: cada 3 s, tope 60 s con aviso, errores de red
  tragados y reintentados; no rompe con 404 ni sin `busqueda_contratos`. Aprobado: «Guardar»
  de un documento aprobado lo desaprueba (comportamiento previo, `review_repository.py:3181`)
  y entonces sí puede relanzar; «Aprobar» nunca. O-B4: caracterizado con SQLite (fila entera
  restaurada; los contratos de la búsqueda nueva siguen listados: límite previo, anotado).
  **`test_f052_d4a_aviso_de_guardado` sin RED propia: se acepta.** Compara la tupla exacta en
  las 5 ramas del helper (sin búsqueda, aprobado, encolada, local, fallo), así que cualquier
  cambio de rama o de texto muere, no solo M8; el helper es pegamento de presentación, no un
  requisito central, y los centrales de T13 bis (`debe_relanzar_busqueda`, el servicio y la
  marca de la plantilla) sí tienen RED.
- **T15**: mismas salidas que sv3 (sin_datos, error, ninguno, encontrados) más `replace`
  fallido → `error` y re-lanza; best-effort con `logger.exception` (R5 lo confirma); el
  repositorio valida el resultado antes de tocar la BBDD. Documento inexistente no sella.
- **T17**: `politica` obligatoria sin valor por defecto (`TypeError` testeado); proveedores
  `NO_TOLERA`, obras/contratos/partidas `TOLERA`; `comprobar_truncado` tras el `ok`; SQL y
  `max_rows` sin cambios (test). Los 4 endpoints `/api/sigrid/*` ya envuelven la llamada en
  `except Exception` (`app.py:471-477`): con proveedores truncados el usuario ve
  `ok=false`, «Error consultando Sigrid: sigrid-api devolvió una respuesta truncada
  [proveedores_obra_XXXX]: N filas recibidas», y conserva la entrada manual. Nadie más usa
  `SigridLookupClient`.

## Checkpoints (en lo aplicable al bloque)

- C1 [x] init.sh exit 0; ficheros del arnés presentes.
- C2 [x] una sola `in_progress`, rama correcta. «current.md solo la sesión activa»: N/A en
  review de bloque (arrastra sesiones previas; lo poda el líder al cerrar, como en A y B).
- C3 [x] primera línea con ruta en los 17 ficheros; sin prints ni `console.log`; sin
  secretos; en español; sin dependencias nuevas. Hexagonal: `review_repository`
  (infraestructura) importa `estado_busqueda` de aplicación, previsto en design §2 y en la
  dirección permitida (hacia dentro); dominio limpio. Trampa (2): lectores de las columnas
  listados en la review B; sv4 no añade ALTER (design §2). [ ] por CR-C1 en la regla de
  dominio «misma normalización que sv3».
- C3 bis N/A: no toca `docs/referencia/`.
- C4 [x] requisitos del bloque (R22–R28 y D4-A) trazados: R22 → `test_f052_r22_*`,
  R23–R26 → `test_f052_r23_*`…`_r26_*`, R27 → `test_f052_r27_*`, R28 → `test_f052_r28_*`,
  D4-A → `test_f052_d4a_*`. Sin red ni BBDD (fakes, SQLite en memoria). MANUAL en current.md.
- C4 bis [x] rigor declarado; RED real con salida (2 reproducidas por mí); cobertura 98 %;
  Evidencias con los 4 números. Mutación: T19 fuera del bloque (N/A justificado por plan);
  manuales 12/12 del implementer + 6/6 míos. RM1–RM6: N/A sin campaña en el bloque.
- C5 [x] T11–T13 bis, T15, T17 en `[x]` con commit `F-052 Tn:` cada una; árbol limpio.

## Cambios requeridos

**CR-C1 · (bloqueante) La obra se compara con otra normalización que la que sella sv3.**
`busqueda_contratos.py:61` usa `normalize_obra_code` de **sv4** (`^\d{1,4}$` + `zfill`),
pero el rastro de producción lo sella sv3 con la **suya** (3 dígitos → `0`+, 4 dígitos solo
si empiezan por `0`, resto `None`). Divergencia previa (el docstring de sv4 dice «debe
coincidir EXACTAMENTE» y no coincide), pero F-052 es lo primero que compara contra un dato
persistido. Reproducido en el scratchpad (sv3 sella, sv4 compara):

| obra en el merge | sv3 sella | sv4 estado | relanza al guardar |
|---|---|---|---|
| `0691`, `691`, ` 0691 ` | `0691` | vigente | no |
| `12`, `7`, `1234`, `1001` | `None` (`sin_datos`) | **desfasada** | **sí, siempre** |

Efecto: el bloque afirma que los datos actuales «**todavía no se han buscado**» cuando sv3
ya los intentó y los descartó por obra inválida (R24 falsa; debería ser el aviso
`sin_datos`); cada «Guardar» (y cada autoguardado del combo) publica otro mensaje en
`q-persistencia` sin fin (D4-A dice «sin cambio no publica»); el sondeo agota sus 60 s en
cada visita. Arreglo propuesto (lo decide el líder con el humano: toca un fichero fuera de
design §2): alinear `services/albaranes-front/application/services/obra_code_normalizer.py`
con el de sv3 (solo lo usan `estado_busqueda`, `LocalContratoRefetchClient` —que así
sellaría `sin_datos` igual que sv3, R22— y el `ContratoRefetchService` muerto) y atarlos con
un test que cargue el fichero de sv3 por ruta, como ya se hace con los literales de
resultado, con la tabla de arriba más `""`, `"abc"`, `None` y `"12345"`. Con traza RED.

**CR-C2 · (documental) T22/R31 describen el flujo anterior a D4-A.** `tasks.md` T22 espera
«Guardar → aviso "todavía no se han buscado"; "Solo volver a buscar" → CTSU24/0402». Con
D4-A y colas, si SS-0026122 tiene rastro, «Guardar» relanza y la ficha marca «Buscando…»
hasta el rastro nuevo; **si no tiene rastro** (documento anterior al despliegue), sale el
aviso R26 y «Guardar» no busca. Reescribir el paso de T22 con ambos casos (el informe ya lo
describe bien en «pendiente») para que el humano no dé por fallida una prueba correcta.

## Observaciones (no bloquean; para el líder y el humano)

- **O-C1 · D4-A no actúa sin rastro**, es decir, en **todos** los documentos anteriores al
  despliegue hasta su primera re-búsqueda. Decisión razonable y documentada (no hay con qué
  comparar y R26 no miente), pero el humano decidió D4-A pensando en SS-0026122, que es
  justo de ese grupo: conviene que lo sepa.
- **O-C2 · Autoguardado del combo**: elegir obra y luego proveedor publica dos re-búsquedas
  seguidas (la primera con la pareja a medias). sv3 lee CIF y obra al procesar y sv6 valora
  con replace transaccional, así que el resultado final es coherente; solo es trabajo doble.
- **O-C3 · Orden sv3 → sv4 obligatorio**: sin el DDL, el ORM de sv4 rompe todas las lecturas
  del merge. sv4 ya tiene precedente de ALTER defensivo idempotente para columnas de sv3
  (soft-delete, `review_repository.py:233-239`); si se quiere quitar el riesgo de orden en
  local, sería el sitio. Si no, que T16 lo deje escrito en `azure-apps/albaranes.md`.
- **O-C4**: el fallback local sigue usando la copia de `header_and_lines` de sv4 sin
  `comprobar_truncado` (D6, fuera de alcance): podría sellar `ninguno` sobre una respuesta
  truncada; irreal hoy (máx. 989 líneas).
