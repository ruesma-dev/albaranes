<!-- progress/review_F-048_bloque_B.md -->
Revisión incremental desde 4a6802b (bloque B, pasada 1; el bloque A quedó aprobado en 4a6802b)

# F-048 · Review del bloque B (sv1, T6–T12)

**Veredicto: APPROVED** — HEAD revisado `5b9637a`. Sin bloqueantes; seis menores, que no frenan el bloque C.

**Rigor**: `critico` (declarado en `harness/features.json`). Exige fase RED, cobertura ≥ 80 % de lo
cambiado, mutación con 0 supervivientes injustificados y MANUAL con comando exacto. La mutación va
con la feature completa (T34): en un bloque intermedio es N/A, justificado abajo.

## Qué se ejecutó (resultados reales)

- `bash harness/init.sh` tal cual: **ENTORNO LISTO, exit 0**. Raíz `865 passed in 160.19s`.
  **sv1 corrió DE VERDAD**: borré antes `.arnes_cache/suite_sv1-email.ok` (el hash coincidía con
  HEAD y habría salido de caché) y salió `62 passed in 25.24s` →
  `[OK] servicio sv1-email: pytest en verde`, **sin** «(caché…)» y **sin** «sin directorio de
  tests». La caché se regeneró con el hash de HEAD (`ff3c930…`). `PUERTA COBERTURA: 99.3% de 299
  líneas (297/299)`; `PUERTA TAMAÑO` impl 188/220. `[AVISO]` de rutas sensibles por
  `llm_call_logger.py` (evals, T40): esperado y del bloque A.
- `git status` limpio antes y después. No se lanzó ninguna suite en paralelo.

## RED reproducidos (tres, en copias aisladas del scratchpad, nunca en el árbol)

1. **T7, RED de verdad**: `git archive e0e0a82` (T6) + el test de `2e6bf67` →
   `ImportError: cannot import name 'ContenidoCorreo' from 'domain.models.email_models'`,
   `1 error in 0.66s`. Coincide con la traza del informe.
2. **T11, «rompiendo una copia aislada»**: copia de HEAD donde el pipeline loguea
   `contexto.cuerpo`, el aviso de R5 lleva `exc` y el error de Graph lleva `response.text[:400]` →
   `5 failed, 20 passed`: los tres de `test_f048_r36_logs.py`, el aviso de R5 de
   `test_f048_r3_r5_pipeline.py` y `test_f048_r5_error_de_graph_lanza_sin_texto_de_la_respuesta`.
3. **T10 + solo lectura** (copia de HEAD): publicar ANTES de guardar el blob lateral, y `get` → `post`
   en `get_contenido` → `12 failed, 8 passed`: tres de orden/no-publicación en
   `test_f048_r7_r10_intake.py` y nueve de `test_f048_r2_r4_graph.py` (el transporte revienta con
   un método distinto de GET).

## Comprobaciones pedidas

- **Solo lectura del buzón**: `get_contenido` (`mail_client.py:288-318`) hace un único GET; el
  diff no añade ningún `post/patch/put/delete` (los POST de `ensure_folder` y `move_message` son
  de antes). `capturar_correo.py` solo llama a `get_contenido` (doble que revienta con lo demás).
- **R36**: aviso de R5 solo con `type(exc).__name__` (`polling_pipeline.py:388-394`), error de
  Graph sin `response.text`, intake con `correo=SI(sha=…)`; el SDK de Blob no usa `logging_enable`.
  El test a DEBUG usa las piezas reales y comprueba que el cuerpo SÍ llegó al blob (no es vacuo).
- **R6**: un único `get_contenido` por mensaje y el mismo objeto a cada página de cada adjunto;
  test con 3 adjuntos/6 páginas, un único sha256, y la matriz destino × {con, sin contexto} × {todo
  bien, adjunto falla, intake falla, sin elegibles} = el destino de hoy.
- **R7/R10**: orden `crear_si_no_existe → put_bytes → put_json → publicar`; `correo_blob` bien y
  legible con `leer_contexto_correo`; duplicado = solo `crear_si_no_existe`; sin contexto, payload
  byte a byte el de hoy y `correo_blob is None`.
- **R38**: `git check-ignore -v` → `.gitignore:36:evals/inputs/`; tests con textos inventados.

## Las diez decisiones del implementer

1. HTML ⇒ texto con `html.parser` sin mirar el contenido: **correcta** (R4, D2). Los comentarios
   condicionales de Outlook los ignora el parser.
2. Errores sin `response.text` y aviso solo con el tipo: **correcta** y necesaria para R36.
3. Contenido solo con adjuntos elegibles: **correcta**; es literalmente el «CUANDO» de R2, y un
   correo sin elegibles va a Errores sin tocar Graph, como hoy (test que lo fija).
4. `HttpOrchestratorClient` acepta el parámetro: **aceptable**; sin él, cablear ese adaptador
   daría `TypeError`. Fuera de la lista de design §5, pero declarado. Ver menor 6.
5. Si guardar el contexto falla, falla la página y no se publica: **coherente con R5**, que habla
   de «la petición del contexto» (el GET a Graph), no de escribir en Blob; se trata como un fallo
   del blob del PDF y nunca sale un `correo_blob` inexistente. Ver menor 2.
6. `correo_sha256` solo con contexto: **correcta**, es lo que garantiza el byte a byte de R10.
7. `CORREO_MAX_CARACTERES` con `gt=0` y defecto de `comun`: **correcta**; sv1 no tiene
   `.env.example`, así que no había nada que actualizar.
8. Captura sin normalizar ni recortar: **correcta**; el test demuestra que da el mismo contexto que
   sv1 al pasar por `construir_contexto_correo`. Ver menor 5.
9. sv1 con el intérprete de la raíz: **correcta**; solo sv4 declara `venv`. Raíz 3.12.7 como el
   Dockerfile, httpx 0.28.1 en los dos; el `.venv` de sv1 existe con `ruesma_comun` editable, así
   que el comando de T36 funciona.
10. El asunto se sigue logueando: decisión del humano; los tests ponen el centinela solo en el cuerpo.

## Checkpoints (bloque intermedio)

- **C1** [x] init.sh exit 0 · [x] ficheros del arnés.
- **C2** [x] una sola `in_progress` (F-048) · [x] rama `feature/F-048-correo-contexto-ia1` ·
  [x] `current.md`: la sección viva describe F-048; arrastra notas de F-045 de antes, que se podan
  al cerrar la feature (no es de este bloque) · N/A `history.md`: ninguna feature pasa a `done`.
- **C3** [x] hexagonal: el dominio solo importa `ruesma_comun` bajo `TYPE_CHECKING`; `html.parser`
  y httpx en `infrastructure` · [x] primera línea con ruta en los 19 ficheros · [x] sin prints (el
  de `capturar_correo.py` es de script, permitido), sin secretos, sin dependencias nuevas
  (`html.parser` es de la stdlib) · [x] trampas de ARCHITECTURE: sin merge, schema ni importes.
- **C3 bis** N/A: el bloque no toca `docs/referencia/`.
- **C4** [x] R2, R3, R4, R5, R6, R7, R10, R36, R38, R39 con `test_f048_rN_*` en verde · [x] sin red
  ni BBDD (`MockTransport` y dobles; el test de R38 solo lanza `git check-ignore`) · [x] MANUAL T36
  listada con su comando en `current.md` y en el informe.
- **C4 bis** [x] rigor declarado · [x] fase RED con traza real, reproducida (3 de 3) · [x] cobertura
  `[OK]` 99,3 % · **N/A mutación, RM1–RM6, campaña manual y supervivientes**: la campaña es T34,
  sobre la feature completa; medirla ahora quedaría obsoleta (RM1) en cuanto entren sv2–sv4 · [x]
  «Evidencias» con tests, cobertura, mutación (pendiente T34) y tiempo de la suite · [x] ningún N/A
  sin motivo.
- **C4 ter** [x] ninguna ruta sensible nueva en el bloque B; el `[AVISO]` es del bloque A (evals,
  T40, `aviso`, se factura: pendiente del visto bueno del humano).
- **C5** [x] T6–T12 `[x]` en `tasks.md` con un commit `F-048 Tn:` cada una (`e0e0a82..8e2a309`) ·
  [x] sin artefactos sin trackear · [x] `features.json` en `in_progress`, que es lo real.

## Trazabilidad

| R | Tests (services/albaranes-email/tests/) |
|---|---|
| R2 | `test_f048_r2_r4_graph.py::test_f048_r2_*` (1 GET, `$select`, `Prefer`), `test_f048_r3_r5_pipeline.py::test_f048_r2_*` (1 por mensaje; nada sin elegibles) |
| R3 | `test_f048_r2_r4_graph.py::test_f048_r3_*`, `test_f048_r3_r5_pipeline.py::test_f048_r3_*` |
| R4 | `test_f048_r2_r4_graph.py::test_f048_r4_*` (html/HTML, no interpreta, texto no pasa por el conversor) |
| R5 | `test_f048_r3_r5_pipeline.py::test_f048_r5_*`, `test_f048_r2_r4_graph.py::test_f048_r5_*` |
| R6 | `test_f048_r6_todos_los_albaranes.py` (12) |
| R7 / R10 | `test_f048_r7_r10_intake.py::test_f048_r7_*` / `::test_f048_r10_*` |
| R36 | `test_f048_r36_logs.py` (4), `test_f048_r7_r10_intake.py::test_f048_r36_*` |
| R38 / R39 | `test_f048_r39_captura.py::test_f048_r38_*` / `::test_f048_r39_*` |

## Bloqueantes

Ninguno.

## Menores (no bloquean; que el líder decida si van al bloque F o a la nota de cierre)

1. `capturar_correo.py:93` — `--directorio` deja escribir un correo real en cualquier ruta,
   también versionada: se salta R38 con un parámetro. Propuesta: rechazar un directorio que
   `git check-ignore` no confirme ignorado, o quitar la opción (los tests ya usan `capturar(...,
   directorio=tmp_path)`).
2. `intake_cola_adapter.py:87` y `:131/:144` — la fila de `workflow_runs` se crea ANTES de los
   blobs. Si falla `put_json` (decisión 5), el correo va a Errores y un reintento manual lo verá
   «duplicado» y **nunca** publicará esa página. La trampa ya existía con el PDF y con `publicar`;
   F-048 añade un punto de fallo más. No es de este bloque arreglarla; que conste en
   `docs/ARCHITECTURE.md` (T32) o en una ficha.
3. `polling_pipeline.py:341` — el log de `OrchestratorError` lleva `%s` de `f"blob/cola: {exc}"`
   (`intake_cola_adapter.py:144`). Hoy ninguna excepción de Blob ni de la cola cita el cuerpo
   (reportan la respuesta del servidor), pero R36 no tiene test en ese camino. Un test con un
   almacén que falle citando el centinela lo dejaría vigilado.
4. `mail_client.py:300` — sin reintento: un 429/503 transitorio deja el correo sin contexto (R5
   lo admite); contar los `sin contexto de correo` en la medición de §7.
5. `capturar_correo.py:62-71` — no guarda `receivedDateTime`: en evals `recibido_utc=None`. No
   cambia la huella.
6. `orchestrator_client.py:40` — `object | None` en vez de `ContextoCorreo | None`. Cosmético.

## Automejora (propuesta, no aplicada)

Para comprobar que una suite corre «sin caché», borrar `.arnes_cache/suite_<servicio>.ok` antes
de `init.sh`: aquí la caché del implementer la habría saltado. Candidata a `arnes-base`.
