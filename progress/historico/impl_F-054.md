<!-- progress/impl_F-054.md -->
# F-054 · Informe del implementer — sv1 ingiere los PDF e imágenes de correos adjuntos

Rama `feature/F-054-correo-adjunto-encadenado`, árbol principal (no el worktree `../albaranes-F-054` que cita
`tasks.md`: así lo pidió el líder). Spec v2 (`specs/F-054-correo-adjunto-encadenado/`), rigor `estandar`.
T1–T11 hechas, un commit local por tarea (`397ad07` … `246cba9`); T12 es MANUAL del humano; T13 = `init.sh`.

## Qué cambió (solo sv1 + un párrafo de ARCHITECTURE)

Antes: un correo cuyo único adjunto era otro correo (`itemAttachment`, `message/rfc822`) iba a `Errores` («sin
adjuntos elegibles»); si venía junto a un PDF directo, el interior se perdía en silencio y el correo iba a
`Procesados`; un `.eml` como `fileAttachment` viajaba opaco a sv2. Ahora:

- **Clasificación** (R1–R4): un adjunto con `contentType` `message/rfc822` (sin mayúsculas; item, file o sin
  `@odata.type`) es «correo adjunto» salvo inline, `referenceAttachment` o > `MAX_ATTACHMENT_MB` (descarte con log
  INFO/WARNING, sin `name`). Uno de tipo correo descartado NO cae a la regla de directos. Los directos, igual que hoy.
- **Extracción** (R5–R12): `$value` con la misma llamada de siempre (una por correo adjunto) y
  `MimeDocumentoExtractor` recorre el MIME con recursión propia: PDF (tipo o nombre `.pdf`) e imágenes `image/*`
  con disposición `attachment`; `inline` y sin disposición se ignoran y cuentan. Tope 5 niveles, todo o nada.
- **Ingesta** (R13–R19): cada documento interior bajo el límite va por el camino del directo (troceo, sha256,
  intake, `correlation_key = email:{exterior}:{sha página}`), con `correo_adjunto_id` y `correo_adjunto_nivel`
  extra en el `meta`. Contexto de IA1: el del exterior, pedido una vez.
- **Destino** (R20–R24): una pasada en el orden de Graph; `Procesados` sii nada falló (descarga, extracción,
  tope, troceo, intake) y entró ≥ 1 página aceptada. Correo adjunto sin documentos = WARNING, no fallo.

### Ficheros (bajo `services/albaranes-email/` salvo el último)

| Fichero | Cambio |
|---|---|
| `domain/models/email_models.py` | + `DocumentoInterior`, `ExtraccionCorreoAdjunto` |
| `domain/ports/extractor_correo_adjunto.py` (nuevo) | `CorreoAdjuntoIlegible` + `ExtractorCorreoAdjunto` (Protocol) |
| `domain/ports/mailbox_client.py` | solo docstring de `download_attachment_value` |
| `infrastructure/document/mime_documento_extractor.py` (nuevo) | el extractor (stdlib `email`, sin red ni disco) |
| `application/pipelines/polling_pipeline.py` | clasificación, `_process_correo_adjunto`, `_ingerir`, `meta` R15, destino R21, docstring |
| `main.py` | construye e inyecta `MimeDocumentoExtractor()` (R27) |
| `tests/eml_sinteticos.py` (nuevo) | correos RFC 822 en memoria, `@ejemplo.test`, centinela `CENTINELA-F054` |
| `tests/dobles_sv1.py` | `adjunto()` con `content_type`/`odata_type`/`size`; `construir_pipeline` inyecta el extractor real |
| `tests/test_f048_r36_logs.py` | sus dos `PollingPipeline(...)` reciben `extractor_correo=`; **ninguna aserción cambia** |
| `tests/test_f054_{extractor_mime,clasificacion,pipeline,logs,cableado}.py` (nuevos) | 107 tests |
| `docs/ARCHITECTURE.md` | párrafo «Correos adjuntos (F-054)» en la regla 9 (10 líneas) |

Además: `harness/features.json` (F-054 `in_progress`), `BACKLOG.md` regenerado, `progress/current.md`,
`progress/mutacion_F-054.md`, fila nueva en `progress/inventario_mutacion_F-039.md` (la exige
`test_f039_r2_todo_informe_de_mutacion_figura_en_el_inventario`) y `[x]` de T1–T11 en `tasks.md`.

No se tocó: `mail_client.py`, `pdf_page_splitter.py`, `intake_cola_adapter.py`, `config/`, `ruesma_comun`, sv2–sv6,
`infra/`, `evals/`, colas ni el blob de F-048. Ningún test llama a Graph, buzón, Azure ni BBDD.
`azure-apps/albaranes.md` no cambia (design §1: mismos endpoints, permisos, colas y blobs).

## Decisiones de diseño y desviaciones (todas menores, ya anotadas en `progress/current.md`)

1. `_ingerir` recibe además `att_id`: así el log de troceo conserva literal `msg=… att=… error splitting PDF`.
2. `_submit_page_to_orchestrator` deja de recibir el `attachment`: no lo usaba (el `meta` sale de `prepared`,
   como antes) y design §7 no necesita `nombre`/`content_type` ahí. Con `extra_meta=None` produce el dict de hoy (R16).
3. El fallo de descarga de un **correo adjunto** loguea solo el tipo de la excepción (el texto del error de
   Graph podría citar el correo, R25); el de un directo sigue como hoy.
4. Un PDF interior entra sea cual sea su disposición (R7a no la condiciona); la regla de disposición solo
   aplica a imágenes (R7b, DA8).
5. Log de R23: `sin adjuntos elegibles: ni directos ni correos adjuntos (total=N) → Errores` (conserva el
   texto «sin adjuntos elegibles» que la T12 busca en los logs viejos). Log final con recuentos:
   `movido a X (directos=N correos_adjuntos=M paginas_aceptadas=P)`.
6. El `name` de Graph de un correo adjunto no se loguea en ningún sitio (DA6); el de los documentos interiores sí.
7. Si el tope se excede, el extractor devuelve lo hallado hasta entonces con `tope_excedido=True` y es el
   pipeline quien no ingiere nada (R9 se prueba en `test_f054_r9_r21_…`).

## Fase RED (requisitos centrales: R1, R7, R9, R15, R21, R25)

**R7 y R9 (T3, antes de existir el extractor).** Comando:
`python -m pytest "services/albaranes-email/tests/test_f054_extractor_mime.py::test_f054_r7_png_y_jpeg_con_disposicion_attachment_entran" "services/albaranes-email/tests/test_f054_extractor_mime.py::test_f054_r9_nivel_6_marca_tope_excedido" -q`

```
_ ERROR at setup of test_f054_r7_png_y_jpeg_con_disposicion_attachment_entran _
E   ModuleNotFoundError: No module named 'infrastructure.document.mime_documento_extractor'
_________ ERROR at setup of test_f054_r9_nivel_6_marca_tope_excedido __________
E   ModuleNotFoundError: No module named 'infrastructure.document.mime_documento_extractor'
ERROR services/albaranes-email/tests/test_f054_extractor_mime.py::test_f054_r7_png_y_jpeg_con_disposicion_attachment_entran
ERROR services/albaranes-email/tests/test_f054_extractor_mime.py::test_f054_r9_nivel_6_marca_tope_excedido
2 errors in 1.29s
```

(Las 30 pruebas del fichero, en rojo por el mismo motivo: `30 errors in 1.56s`.)

**R1, R15, R21 y R25 (T6, con `polling_pipeline.py` aún sin modificar).** Comando (ids entre comillas):
`python -m pytest "…/test_f054_clasificacion.py::test_f054_r1_message_rfc822_no_inline_se_abre_como_correo_adjunto[message/rfc822-item]" "…/test_f054_pipeline.py::test_f054_r15_meta_de_una_imagen_interior" "…/test_f054_pipeline.py::test_f054_r21_procesados_si_y_solo_si_nada_falla_y_hay_pagina_aceptada[tope_excedido-carpeta-errores]" "…/test_f054_logs.py::test_f054_r25_ningun_log_lleva_datos_del_correo_interior[descartes_r2]" -q --show-capture=no`
(`…` = `services/albaranes-email/tests`)

```
    def test_f054_r1_message_rfc822_no_inline_se_abre_como_correo_adjunto(odata_type, content_type):
E       AssertionError: assert 0 == 1
E        +  where 0 = veces('download_attachment_value')
services\albaranes-email\tests\test_f054_clasificacion.py:103: AssertionError
    def test_f054_r15_meta_de_una_imagen_interior():
E       ValueError: not enough values to unpack (expected 1, got 0)
services\albaranes-email\tests\test_f054_pipeline.py:294: ValueError
    def test_f054_r21_procesados_si_y_solo_si_nada_falla_y_hay_pagina_aceptada(escenario, destino):
E       AssertionError: assert [('msg-1', 'c...-procesados')] == [('msg-1', 'carpeta-errores')]
E         At index 0 diff: ('msg-1', 'carpeta-procesados') != ('msg-1', 'carpeta-errores')
services\albaranes-email\tests\test_f054_pipeline.py:424: AssertionError
    def test_f054_r25_ningun_log_lleva_datos_del_correo_interior(caplog, escenario):
E       assert 'c1' in "INFO     application.pipelines.polling_pipeline:polling_pipeline.py:156 polling: 1 mensaje(s) con adjuntos\nINFO     ...sg='encolado'\nINFO     application.pipelines.polling_pipeline:polling_pipeline.py:238 msg=msg-1 movido a Procesados\n"
services\albaranes-email\tests\test_f054_logs.py:119: AssertionError
4 failed in 1.47s
```

Lectura: R1 — el itemAttachment ni se descargaba; R15 — no llegaba ninguna página interior; R21 — un correo
adjunto con tope excedido junto a un directo iba a `Procesados` (el interior se perdía en silencio); R25 — los
descartes de correos adjuntos no dejaban rastro (la parte «sin datos del interior» es la que valida el verde).
Totales de T6 en rojo: clasificación 17/30 fallidos, pipeline 24/33, logs 9/9.

**Verde** tras T7 (mismos 4 + los 2 de T3): `6 passed in 1.16s`. Suite de sv1 completa tras T7: `200 passed`.

**T5 (no regresión, sin RED a propósito):** R3 (tabla de 13 tipos directos) y R16 (dict literal del `meta`
directo, PDF e imagen) se escribieron y pasaron en verde **contra el pipeline sin modificar**
(`16 passed in 1.25s`, `git diff` vacío en `application/`), y siguen en verde tras T7.

## Verificación

- Suite de sv1 (`python -m pytest services/albaranes-email/tests -q`): **205 passed in 5.85s** (98 previos de
  F-048 sin tocar aserciones + 107 de F-054).
- `bash harness/init.sh`: resultado final en «Evidencias».
- Ninguna verificación contra Graph, el buzón ni Azure (prohibido y no necesario).

## Fuera de alcance (DH4) y lo que falta

- Fuera: `conversationId`/hilo, enlaces SharePoint/OneDrive, `.msg`, cabeceras del interior en el contexto,
  reproceso automático de `Errores`, tamaño mínimo de imagen (riesgo de logos adjuntados como `attachment`,
  design §9), y el `token_provider.py` duplicado en sv1 (hallazgo de la spec, ficha aparte).
- **Pendiente del humano (T12, MANUAL, no bloquea el `done`)**: tras merge a `dev`, `.\deploy.ps1 -Only sv1` y
  `.\check_deploy.ps1`, devolver UNO de los correos de `Errores` con correo adjunto a la carpeta origen como no
  leído y comprobar en los logs de sv1 la línea `documentos interiores: N PDF y M imagen(es)`, los
  `intake encolado` y `movido a Procesados`; luego el resto por tandas. Procedimiento completo en
  `progress/current.md` («PENDIENTE DEL HUMANO · verificación MANUAL de F-054»).
- Observación ajena a F-054: quedan en `git worktree list` 28 worktrees huérfanos de campañas de mutación de
  F-047 en `%TEMP%` (no los creé yo; no los toco).

## Evidencias

| Evidencia | Valor medido |
|---|---|
| Tests ejecutados | sv1: **205 passed** (107 nuevos de F-054); `init.sh` raíz + 7 servicios: ver línea siguiente |
| `bash harness/init.sh` | **ENTORNO LISTO** (HEAD con el commit de ruff): raíz `1067 passed in 202.26s`; sv1 `205 passed in 30.92s`; sv2–sv6 y comun en verde (caché); ruff 1167 avisos (1166 antes: +1 `BLE001` del `except Exception` de la descarga del correo adjunto, igual que el de los directos) |
| Cobertura de líneas cambiadas | **PUERTA COBERTURA: 100.0 % de 184 líneas cambiadas cubiertas (184/184, umbral 80 %, nivel estandar)** |
| Mutación (muestreada, semilla `20260820`) | **77 generados, 20 evaluados, 19 muertos, 1 superviviente** (equivalente), 0 timeouts, 142,8 s, 4 workers, HEAD `3fb2bb8` (después solo cambió una línea en blanco y el lint de tests) |
| Tiempo de la suite de sv1 | 5,85 s en local (21,9 s dentro de `init.sh`; línea base de mutación 23,3–23,8 s por worktree) |

**Supervivientes** (detalle en `progress/mutacion_F-054.md`, ninguno `PENDIENTE`):

- Campaña final: 1 — `mime_documento_extractor.py:155` `split("/", 1)` → `split("/", 2)`: **equivalente**.
  `get_content_type()` siempre devuelve `maintype/subtype` con una sola barra (ante un tipo mal formado,
  la biblioteca `email` cae a `text/plain`), así que ambos `split` dan el mismo `[1]`. Sin test posible.
- Primera pasada (HEAD `cea0788`, misma semilla, 17 muertos / 3 supervivientes): los otros 2 eran **huecos
  reales** y se mataron con tests nuevos (commit `c309db9`), verificado reinyectando cada mutante a mano:
  `polling_pipeline.py:305` (recuento de directos del log final; test
  `test_f054_r21_el_log_final_cuenta_directos_correos_adjuntos_y_paginas`) y `polling_pipeline.py:657`
  (`max_bytes > 0` → `>= 0`: con límite 0, «sin límite», descartaría todo correo adjunto; test
  `test_f054_r2_sin_limite_configurado_no_se_descarta_por_tamano`).
