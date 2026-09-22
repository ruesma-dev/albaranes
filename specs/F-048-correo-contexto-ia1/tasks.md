<!-- specs/F-048-correo-contexto-ia1/tasks.md -->
# F-048 · Tareas

Rama `feature/F-048-correo-contexto-ia1`. Rigor `critico`: **fase RED
obligatoria** en toda tarea con test (falla antes, pasa después; la traza va a
`progress/impl_F-048.md`). Un commit por tarea, `F-048 Tn: ...`. Sin `git push`.
Ningún test usa un correo real: textos inventados, con un centinela
(`CENTINELA-F048`) en el cuerpo para las comprobaciones de logs.

## Bloque A · comun

- [ ] T1: `ruesma_comun/correo/contexto.py` — `ContextoCorreo`, `construir_contexto_correo` (normaliza, recorta, sha256), `nombre_blob_correo`, `guardar_contexto_correo`, `leer_contexto_correo` (None si falta o no valida) (R1)  |  Verificación: `pytest services/albaranes-comun/tests/test_f048_r1_contexto.py`
- [ ] T2: `MensajeExtraccion.correo_blob` opcional; tests de ida y vuelta con un modelo sin el campo y de tamaño con cuerpo de 60.000 caracteres (R8, R9)  |  Verificación: `pytest services/albaranes-comun/tests/test_f048_r8_r9_mensaje.py`
- [ ] T3: `ruesma_comun/correo/prompt.py` — marcas, `render_bloque_correo` (advertencia de DATO, neutraliza marcas, nota fija sin contexto) y `redactar_correo` (R12, R13)  |  Verificación: `pytest services/albaranes-comun/tests/test_f048_r13_prompt.py`
- [ ] T4: `LlmCallLogger` aplica `redactar_correo` a todo texto de `request_summary`; test que escribe a `tmp_path` y busca el centinela (R31)  |  Verificación: `pytest services/albaranes-comun/tests/test_f048_r31_llm_logger.py`
- [ ] T5: `ruesma_comun/contratos/origen_datos.py` — `OrigenDatos`, `OrigenCampo`, `DiscrepanciaPartida`, motivos, propiedad `hay_discrepancia` (la usa sv4 y, el día que se apruebe, la rebaja de fiabilidad) y evidencia recortada a 160 (R25)  |  Verificación: `pytest services/albaranes-comun/tests/test_f048_r25_origen_datos.py`

## Bloque B · sv1 (primera suite de tests del servicio)

- [ ] T6: Crear `services/albaranes-email/tests/conftest.py` y un test de humo que importe el pipeline con dobles del buzón y del intake; confirmar que `init.sh` deja de avisar «sin directorio de tests» para sv1  |  Verificación: `pytest services/albaranes-email/tests -k humo`
- [ ] T7: `ContenidoCorreo` + `MailboxClient.get_contenido`; `GraphMailClient` hace GET con `$select=subject,uniqueBody` y `Prefer` texto; HTML ⇒ texto con `html.parser`; test con `httpx.MockTransport` que falla si ve un método distinto de GET (R2, R4)  |  Verificación: `pytest services/albaranes-email/tests/test_f048_r2_r4_graph.py`
- [ ] T8: Pipeline — contenido una vez por mensaje; `uniqueBody` vacío ⇒ solo asunto; fallo ⇒ sigue sin contexto y sin mover a Errores (R3, R5)  |  Verificación: `pytest services/albaranes-email/tests/test_f048_r3_r5_pipeline.py`
- [ ] T9: Pipeline — el MISMO contexto (mismo sha256) llega a todas las páginas de todos los adjuntos del mensaje, sean uno o varios albaranes, y el destino Procesados/Errores no cambia respecto a hoy (todo bien / un adjunto falla / sin elegibles) (R6)  |  Verificación: `pytest services/albaranes-email/tests/test_f048_r6_todos_los_albaranes.py`
- [ ] T10: `IntakeColaClient` — blob lateral ANTES de publicar (orden comprobado con un doble que registra llamadas), `correo_blob` en el mensaje, `correo_sha256` en meta sin cuerpo, nada en duplicado (R7, R10)  |  Verificación: `pytest services/albaranes-email/tests/test_f048_r7_r10_intake.py`
- [ ] T11: sv1 no loguea el cuerpo: `caplog` a DEBUG sobre un ciclo completo con centinela (R30)  |  Verificación: `pytest services/albaranes-email/tests/test_f048_r30_logs.py`
- [ ] T12: `capturar_correo.py` — solo `get_contenido`, escribe `evals/inputs/correos/{caso_id}.json`; test con doble de buzón que revienta si se llama a `move_message` u otro método de escritura; `git check-ignore` de la ruta de salida (R32, R33)  |  Verificación: `pytest services/albaranes-email/tests/test_f048_r33_captura.py`

## Bloque C · sv2

- [ ] T13: `LecturaCorreo` y `DocumentoAlbaran.lectura_correo` opcional; un envelope sin él valida (R15, R17)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r15_schema.py`
- [ ] T14: `_render_task_fase_1(task, correo)` — marcador sustituido, nota sin contexto, bloque al final si falta el marcador (R12)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r12_render_fase1.py`
- [ ] T15: Fase 2 recibe el MISMO bloque dentro de `{prompt_fase_1}`: test que carga el `config/prompts.yaml` REAL y recorre TODOS los prompts de fase 2 del catálogo, con y sin correo, buscando el literal `{contexto_correo}` y cualquier `{...}` de marcador conocido sin sustituir (R14)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r14_fase2_sin_marcadores.py`
- [ ] T16: `config/prompts.yaml` — marcador, instrucciones R15–R16 (el papel sigue en cabecera y líneas; si el correo trae el dato no se deduce del papel) y `lectura_correo` en `schema_hint`; test de que el task real contiene el marcador y las frases clave (R15, R16)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r16_prompt_yaml.py`
- [ ] T17: `origen_datos_resolver.sellar_origen_datos` — obra: único+en lista, único+lista None, ambiguo, fuera de lista, sin dato, sin lectura, sin correo (R17–R20, R23)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r18_r20_obra.py`
- [ ] T18: Resolver — partida: única a todas las líneas, ambigua, `validada=null`; discrepancias por línea con normalización de mayúsculas y espacios; se guardan las dos lecturas y su fuente, y NO se añade motivo de revisión (R21, R22)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r21_r22_partida.py`
- [ ] T19: Resolver — lo que la IA ponga en `origen_datos` se ignora, `lectura_correo` sale del `data` final, el resolver no muta el envelope de entrada y corre sobre el documento de fase 2 (R24, R26)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r24_r26_sellado.py`
- [ ] T20: Worker — `FuenteContextoCorreoBlob`; lee `correo_blob` con `getattr`; blob ausente o roto ⇒ sigue sin él; pasa el contexto a las dos fases; sella tras `construir_envelope_final`; cableado en `main_worker.py` (R11)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r11_worker.py`
- [ ] T21: sv2 no loguea el cuerpo: `caplog` sobre el handler completo con LLM doble y centinela (R30)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r30_logs.py`
- [ ] T22: `encolar_extraccion.py --correo <json>` usa `guardar_contexto_correo` y pone `correo_blob` (R36)  |  Verificación: `pytest services/albaranes-api/tests/test_f048_r36_encolar.py`

## Bloque D · sv3

- [ ] T23: `DocumentoAlbaran.origen_datos` opcional en sv3; envelope viejo y nuevo validan; envelope con `origen_datos` NO va a poison (R27)  |  Verificación: `pytest services/albaranes-persistencia/tests/test_f048_r27_modelo.py`
- [ ] T24: El merge conserva `origen_datos` y acaba en `raw_extraction_json` del merge (repositorio con sesión doble, sin BBDD) (R28)  |  Verificación: `pytest services/albaranes-persistencia/tests/test_f048_r28_merge.py`
- [ ] T25: Test de regresión: obra del correo inexistente en Sigrid ⇒ la red de sv3 la descarta y marca revisión igual que si viniera del papel (R29)  |  Verificación: `pytest services/albaranes-persistencia/tests/test_f048_r29_red_obra.py`

## Bloque D bis · sv4 (solo pintar)

- [ ] T26: `review_models.py` — propiedades `origen_datos` (parsea `raw_extraction_json` con el modelo de `comun`) y `avisos_origen_datos`; JSON roto, ausente o sin bloque ⇒ `None` y la ficha abre igual (R41)  |  Verificación: `pytest services/albaranes-front/tests/test_f048_r41_vista_modelo.py`
- [ ] T27: `document_detail.html` — bloque de aviso con cada discrepancia (campo, valor del correo, valor del papel, línea en partidas) y con los códigos del correo no aplicados cuando hubo `correo_ambiguo` o `correo_fuera_de_lista`; sv4 no escribe nada (R39, R40)  |  Verificación: `pytest services/albaranes-front/tests/test_f048_r39_r40_vista_avisos.py`

## Bloque E · evals (depende de F-047)

- [ ] T28: `evals/correos.py` — carga `evals/inputs/correos/{caso_id}.json` con `construir_contexto_correo`; sin fichero ⇒ None; test de que ningún fichero versionado bajo `evals/` o `tests/` contiene un contexto de correo real (R32)  |  Verificación: `pytest tests/test_f048_evals_correos.py`
- [ ] T29: PRECONDICIÓN — `evals/inyeccion.py` de F-047 integrado en esta rama; si no lo está, PARAR, marcar T29–T30 `blocked` en `progress/current.md` y seguir con el bloque F  |  Verificación: `git merge-base --is-ancestor 9f8a008 HEAD`
- [ ] T30: La inyección de F-047 acepta `correo` y lo guarda con `guardar_contexto_correo` (misma puerta que sv1); `--sin-correo` fuerza la inyección sin él (R34, R35)  |  Verificación: `pytest tests -k "f048 and inyeccion"`

## Bloque F · documentación y puertas

- [ ] T31: `docs/ARCHITECTURE.md` (regla 15 y orden de despliegue sv3 → sv2 → sv1), `harness/rutas_sensibles.json` y `azure-apps/albaranes.md` (commit aparte en ese repo)  |  Verificación: `python -m harness.rutas_sensibles` y revisión del reviewer
- [ ] T32: Cobertura de líneas cambiadas ≥ 80 % (R38)  |  Verificación: `python -m harness.cobertura --base dev --config harness/rigor.json` (sin `--feature`: la deduce de la rama)
- [ ] T33: Campaña de mutación COMPLETA, 0 supervivientes sin test nuevo o justificación escrita (R38)  |  Verificación: `python -m harness.mutacion --feature F-048`
- [ ] T34: Topes de tamaño del papeleo  |  Verificación: `python -m harness.tamano --feature F-048`

## Bloque G · verificación REAL (en F-047 tres defectos salieron solo al ejecutar)

- [ ] T35: Graph real, SOLO LECTURA: con tres correos de `Procesados` elegidos por el humano —uno directo, un `RE:` con historial y un `RV:`— comprobar que `uniqueBody` trae lo esperado y no la cadena citada  |  Verificación: MANUAL (humano) — `cd services\albaranes-email; .\.venv\Scripts\python.exe capturar_correo.py --message-id <ID> --caso <CASO>` ×3 y abrir `evals\inputs\correos\<CASO>.json`
- [ ] T36: Extremo a extremo LOCAL con correo real y su albarán real: `infra\local\arrancar_local.ps1 -SinSv1`; `cd services\albaranes-api; .\.venv\Scripts\python.exe seed_input.py <DOC_ID> "<pdf>"` y `.\.venv\Scripts\python.exe encolar_extraccion.py <DOC_ID> --correo ..\..\evals\inputs\correos\<CASO>.json`; sha del PDF con `(Get-FileHash "<pdf>" -Algorithm SHA256).Hash.ToLower()`; leer `psql "$env:ALBARANES_DB_URL" -c "SELECT obra_codigo, raw_extraction_json::json->'data'->'origen_datos' FROM albaran_documents_merge WHERE source_sha256='<SHA>' AND is_active;"` y `psql "$env:ALBARANES_DB_URL" -c "SELECT l.line_index, l.codigo_imputacion FROM albaran_lines_merge l JOIN albaran_documents_merge d ON d.id=l.document_id WHERE d.source_sha256='<SHA>' AND d.is_active ORDER BY l.line_index;"`. ES VERDE si `origen_datos` existe con `correo_presente=true`, obra y partida finales son las del correo, la discrepancia aparece si el papel decía otra cosa Y se ve como aviso en la ficha de `http://localhost:8004` (R39), y ni el log de sv2 ni `LLM_CALL_LOG_DIR` contienen el cuerpo (buscar una frase del cuerpo con `Select-String`)  |  Verificación: MANUAL (humano)
- [ ] T37: Reproceso desde sv4 («Volver a buscar», `q-persistencia` con `force`) sobre el documento de T36: `origen_datos` sigue en el merge  |  Verificación: MANUAL (humano) — portal `http://localhost:8004` y el primer SELECT de T36
- [ ] T38: Compatibilidad hacia atrás real: dar de baja lógica el documento de T36 en la papelera de sv4 y reinyectar el mismo PDF SIN `--correo` con otro `<DOC_ID2>`; debe llegar con `origen_datos.obra.motivo='sin_correo'` y la obra del papel  |  Verificación: MANUAL (humano) — mismo SELECT que T36
- [ ] T39: Pasada de evals con LLM real sobre la muestra con correo (ruta sensible: `prompts.yaml`), con y sin correo. SE FACTURA: requiere visto bueno del humano  |  Verificación: MANUAL (humano) — `python -m evals.runner --con-llm --feature F-048`, informe en `progress/evals_F-048.md` (fuera de git)
- [ ] T40: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
