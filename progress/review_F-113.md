<!-- progress/review_F-113.md -->
Revisión completa (pasada 1), `dev` 5dd1f45 .. HEAD `879056d`

# F-113 · Review

**Veredicto: APPROVED** (T1–T8). T9–T11 son MANUAL y T12 es el `init.sh` de cierre: siguen pendientes y no bloquean.

**Rigor:** `estandar`, declarado en la ficha de F-113 (`chore/alta-F-111-F-112:harness/features.json`, `status`
`spec_ready`, que **no está** en esta rama ni en `dev`). Exige fase RED, cobertura ≥ 80 % y mutación muestreada
(20 mutantes, semilla 20260820) con los supervivientes analizados. Como la ficha no está en la rama, `init.sh` midió
las puertas con la ficha de F-106 (`critico`). El umbral de cobertura es el mismo (80 %) y el diff es el de esta
rama, así que el número vale. La mutación se lanzó con `--rama` y con los valores de `estandar`: los he
recalculado y coinciden (abajo). La puerta de rutas sensibles y la de tamaño **no** midieron F-113: las compruebo a
mano más abajo.

## Verificación ejecutada por el reviewer

- `bash harness/init.sh` con `PYTHONPATH` a la comun del worktree y `ARNES_SIN_CACHE=1` (la forma aceptada en F-086 y F-098): **exit 0, «ENTORNO LISTO»**. Resultados: raíz 1919, sv1 236, sv2 496, sv3 1576, sv4 1933, sv5 125, sv6 480 (1 skipped), sv9 1027 y comun 1202 (3 skipped), **0 fallos**. `PUERTA COBERTURA: 99.4% de 168 líneas (167/168)`. La línea sin cubrir es `_conectar`, con `pragma: no cover`, porque necesita la BBDD real.
- Alcance recalculado con `harness.alcance` (5dd1f45..be9439c): 7 ficheros y **415 líneas**. `generar_mutantes` da **44**. El sorteo `Random(20260820).sample(·, 20)` incluye el superviviente declarado (`medir_f113_octet_stream.py:151`, `entero`, `splitlines()[0]` → `[1]`) y lo incluye con el mismo texto. Todo coincide con el informe.
- RM4: apliqué el mutante superviviente sobre una copia de sv1 en el scratchpad y corrí `test_f113_medicion.py`: **1 failed, 16 passed**. El test nuevo lo mata. `git status` del worktree, limpio.
- `azure-apps` `cff9063` (`albaranes.md` l. 28–35): es un commit local y no está publicado. El texto es correcto.

## Checkpoints

**C1**
- [x] `init.sh` exit 0 (con el entorno del worktree; ver arriba).
- [x] Los ficheros base del arnés existen.

**C2**
- [x] Una sola feature `in_progress`, F-106, según `dev`. F-113 va en paralelo por orden del líder: es URGENTE y entra antes que F-106 (D-8).
- [x] La rama es `feature/F-113-mime-adjuntos-octet-stream`.
- [x] `current.md` describe las sesiones vivas, y la de F-113 lleva su estado y lo que falta.
- N/A: «toda feature `done` tiene su resumen en `history.md`». F-113 no se cierra en esta review.

**C3**
- [x] Arquitectura hexagonal respetada. La detección del MIME es infraestructura sin dominio y vive en `ruesma_comun`. sv1 y sv2 la llaman desde `application/` igual que ya llaman a `ruesma_comun.correo`. Nada copiado entre servicios.
- [x] La primera línea de cada fichero lleva su ruta.
- [x] Sin prints de debug: los `print` del script de medición son su salida de consola, a propósito. Sin secretos, sin dependencias nuevas (solo stdlib).
- [x] Trampas de dominio: N/A justificado. No hay schema, ni tablas merge/raw, ni importes.

**C3 bis**
- N/A: no toca `docs/referencia/`.

**C4**
- [x] Cada requisito tiene tests, en la tabla de abajo. R22 está retirado.
- [x] Los tests no tocan ni red ni BBDD. El script se prueba con una conexión falsa y `_conectar` se sustituye.
- [x] Las verificaciones MANUAL T9–T11 están en `current.md`. Su comando exacto está en `tasks.md` y en el §5 del informe del implementer.

**C4 bis**
- [x] El rigor está declarado (`estandar`). Es una ficha fuera de la rama, y eso queda anotado arriba.
- [x] Fase RED con la salida real del fallo en T1–T6 (§3 del informe), y los verdes previos explicados (no regresión).
- [x] Cobertura `[OK]` 99,4 %.
- [x] Mutación con los totales verificados de forma independiente (arriba).
- [x] Los muertos están comprobados, no solo contados: la campaña tardó 650,2 s (> 60 s), así que **no la reejecuté**. Basta el recálculo puro más RM1–RM6 y el RM4 del superviviente.
- [x] Coste por mutante: 650,2 × 4 / 20 = 130 s, por encima de 1 s.
- [x] Sin «⚠ CAMPAÑA NO VÁLIDA». «Sin veredicto (base rota)» = 0, y la línea base corrió en los 4 workers.
- [x] RM1: SHA medido `be9439c`. Después solo cambiaron `tests/test_f113_medicion.py` y ficheros de `progress/` y `tasks.md`: ninguno está en el alcance.
- [x] RM2: media 32,5 s × 4 workers = 130 s por mutante. Las líneas base son comun ≈ 185 s y sv1 ≈ 17 s, y la muestra tiene 9 mutantes de comun y 11 de sv1, con `-x`. Es coherente: no hay salto de orden de magnitud.
- [x] RM3: repasé los 19 muertos (por ejemplo, `extra_meta and {}` da `TypeError` y `data[9:12]` nunca casa con `WEBP`). Ninguno es equivalente.
- N/A: RM5 solo aplica en `critico`, y aquí no hay equivalentes declarados.
- [x] RM6: no se quitó código defensivo. El superviviente se mató con un test nuevo.
- N/A: campaña manual. La automática dio 44 mutantes.
- [x] El superviviente tiene su análisis completo (hueco real, cerrado con un test).
- [x] Evidencias: los cuatro números y los 4 workers (§6 del informe).

**C4 ter (rutas sensibles)**
- La puerta midió F-106 y salió N/A, pero **F-113 sí toca** `services/albaranes-comun/ruesma_comun/llm/**` (`llm_client.py`). La exigencia es `aviso`, no hay `progress/evals_F-113.md` y lo dejo **justificado**: el cambio no altera ningún texto que lea la IA (ni prompts ni schemas). Solo corrige el MIME y el `kind` del adjunto, y R10 lo cubre con el SDK de OpenAI simulado. Además, con los `_indice.json` de `evals/fixtures/` vacíos, la pasada daría NO_EVALUABLE.

**Tamaño (puerta medida sobre F-106; cuento F-113 a mano)**
- [x] requirements 87/150, design 186/250, impl 167/220, review < 140.

**C5**
- [x] `tasks.md`: T1–T8 `[x]`, con un commit `F-113 Tn:` por tarea. T9–T12 están pendientes por diseño (MANUAL y cierre).
- [x] No hay temporales: el árbol está limpio. La *junction* `.venv` de sv4 es del entorno, no se versiona y no la he tocado.
- N/A: `features.json` refleja el estado. Justificación: la ficha vive en `chore/alta-F-111-F-112` con `spec_ready`. Pasarla a su estado real al fusionar es tarea del líder (ver O1).

## Desviaciones del §2 del informe: juicio

1. **`normalizar_mime` público.** Aceptada. Evita importar un privado entre paquetes y está en `__all__` con su test. R6 exige cuatro nombres, no «solo» cuatro.
2. **Test de versión de F-098** (pasa a ser «≥ 0.9.0 y pyproject = `__version__`»). Aceptada: es la misma relajación que hizo F-098 con F-076 y no oculta ninguna regresión. Al fusionar F-106 (0.10.0) habrá un conflicto trivial en ese test.
3. **R15 por encima de design §5.2.** Aceptada: el requisito manda sobre el diseño. Si solo se corrige el nombre, el meta no lleva el declarado y queda un WARNING propio, sin nombre. Lo cubre `test_f113_r13_jpeg_declarado_jpeg_con_nombre_pdf_tampoco_se_trocea`.
4. **El declarado equivalente se conserva tal cual.** Aceptada: es la lectura conservadora de R15 (flujo byte a byte igual) y tiene test (`…_declarado_con_mayusculas_y_parametros_se_conserva_tal_cual`). sv2 y `normalizar_adjuntos` lo normalizan al leer.
5. **Filtro `email:%` y `split_part` en el script.** Aceptada: es correcto, porque `workflow_runs.correlation_key` de sv1 es `email:{message_id}:{page_sha256}`, y sin el filtro la rama `''` contaría workflows de otro tipo. **Es de solo lectura de verdad**: la sesión va con `default_transaction_read_only=on`, la transacción empieza por `SET TRANSACTION READ ONLY` y después solo hay dos `SELECT`. No hay DDL ni DML. Las credenciales salen solo del entorno, y en un error solo se imprime el tipo. Los tipos (`started_at_utc` String, `payload_json` Text) casan con el `substr` y el `::jsonb` de `ruesma_comun/workflows/orm.py`.

## Cobertura de requisitos

| Req | Tests |
|---|---|
| R1–R4 | `test_f113_mime.py::test_f113_r1_*` (firmas, ventana PDF de 1024, WebP, HEIC, extensión, octet-stream), `r2_*`, `r3_*`, `r4_datos_cortos_o_vacios` |
| R5 | `test_f113_r5_nombre_coherente`, `r5_defecto_configurable`, `r5_mime_con_mayusculas_y_parametros`, `r5_respeta_el_tallo` |
| R6 | `test_f113_r6_exporta_la_api`, `r6_version_091` |
| R7–R9 | `test_f113_llm_adjuntos.py::test_f113_r7_*`, `r8_warning_sin_nombre`, `r8_sin_correccion_no_hay_warning`, `r9_identidad_*`, `r9_regla_de_attachment_y_attachments` |
| R10 | `test_f113_r10_openai_jpeg_octet_stream_va_como_image_jpeg`, `r10_openai_jpeg_declarado_pdf_no_va_como_input_file` |
| R11–R14 | `test_f113_mime_real.py::test_f113_r11_*` (incluido el documento interior y el PDF multipágina), `r12_whatsapp_*`, `r13_*`, `r14_warning_sin_nombre`, `r14_nombre_corregido_avisa_sin_nombre` |
| R15–R16 | `test_f113_r15_*` (4), `test_f113_r16_*` (2) |
| R17–R19 | `test_f113_build_attachments.py::test_f113_r17_*` (3), `r18_*` (3 casos), `r19_*` (4) |
| R20–R21 | `test_f113_medicion.py::test_f113_r20_*` (solo lectura, solo SELECT, sin campos sensibles, `PG_*`, error sin detalle, ayuda) y `r21_*` (resumen, CSV, `main`) |
| R23 | El reviewer leyó el README de comun, `ARCHITECTURE.md` §Blobs y `azure-apps` `cff9063` |

## Cambios requeridos

Ninguno.

## Observaciones (no bloquean)

- **O1 (líder):** al fusionar en `dev`, pasar la ficha de F-113 al estado real y dejarla en el mismo `features.json` que F-106. Mientras no esté, cualquier `init.sh` mide las puertas de otra feature.
- **O2:** el texto de `azure-apps/albaranes.md` ya habla en presente («Desde F-113 … es el MIME real») y producción todavía no lo hace. Conviene publicar ese commit solo después de T10, o añadir «pendiente de despliegue» hasta entonces: un documento que parece vigente y no lo es hace daño (regla de `azure-apps`).
- **O3:** ruff en los ficheros nuevos: `I001` (orden de imports) en los tres tests nuevos de comun y sv2, y `RUF059` en `test_f113_build_attachments.py:106` (`ok` sin usar). No bloquea, porque ruff es aviso en `init.sh`, pero son líneas nuevas que ya nacen con deuda.
- **O4:** caso límite en sv1. Si llegara `content_type` vacío con bytes sin firma, pasaría a `application/octet-stream` y se anotaría el declarado `""`. Hoy no puede pasar (`mail_client.py:239` pone `application/octet-stream` por defecto y el extractor MIME usa `get_content_type()`), y por eso no exige cambios.

## Propuesta de automejora (no aplicada)

`init.sh` y `harness.mutacion` deberían aceptar `--feature F-XXX` u otra forma de medir una feature que no es la
`in_progress` de la rama. Esta es la segunda vez que una feature urgente en paralelo hace que las puertas de rutas
sensibles y de tamaño midan otra feature y den N/A falsos. Iría a `arnes-base` si el humano lo aprueba.
