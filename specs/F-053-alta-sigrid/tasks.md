<!-- specs/F-053-alta-sigrid/tasks.md -->
# F-053 · Tareas

Rama `feature/F-053-alta-sigrid`. Rigor `critico`: **fase RED obligatoria** en
toda tarea con test (falla antes, pasa después; traza en `progress/impl_F-053.md`).
Un commit por tarea, `F-053 Tn: ...`. Sin `git push`. Tests `test_f053_rN_*`,
sin red ni BBDD: fakes de `AltaRepository`, `SigridAltaPort` y `PdfAlbaranPort`,
y `httpx.MockTransport` para el cliente. **No se empieza sin la PARADA 1**
(preguntas 1, 4 y 5 de `progress/spec_F-053.md`) y **no se fusiona en `dev` antes que F-052 y F-051** (design §8).

## Bloque A · contratos y esquema

- [ ] T1: `MensajeFeedback.accion` (`alta` | `verificar_anulacion`, defecto `alta`) y docstring con sv9 como consumidor (R32)  |  Verificación: `pytest services/albaranes-comun -k f053`
- [ ] T2: DDL de `albaran_altas_sigrid` e índice en `schema_contribution.py` de sv3, idempotente (R36, design §6)  |  Verificación: `pytest services/albaranes-persistencia -k f053_r36`
- [ ] T3: Esqueleto de sv9 (`services/albaranes-alta-sigrid`): settings con los defectos de design §7 (`ALTA_SIGRID_COMMIT` solo es `true` con el literal `true`), logging, Dockerfile, requirements, `sv9.md`, `.env.example` sin valores, alta en `harness/servicios.json`  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_r19_modo` y `pytest tests/test_estructura_monorepo.py`
- [ ] T4: Modelos de dominio y los tres puertos de sv9 (design §3)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_modelos`

## Bloque B · dominio puro de sv9

- [ ] T5: `validador_alta.validar_y_construir`: los 13 motivos de R10 (uno por test y uno con todos a la vez), partidas de R11, construcción de R12 y exclusión de R13  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r10 or f053_r11 or f053_r12 or f053_r13"`
- [ ] T6: `comparador_previa.comparar`: `importe_distinto` (en el borde de la tolerancia y fuera), `lineas_distintas` (sobra y falta) y `aviso_bloqueante` (R17)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_r17`
- [ ] T7: `clasificador`: 200 ok/committed → `registrado`; 400 → `error`; 401/403 → `error`; 5xx, tiempo agotado y conexión → `incierto` (R18, R20, R21)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r18 or f053_r21"`

## Bloque C · servicio de sv9

- [ ] T8: `AltaSigridService`, entrada: reclamación y sus salidas `ignorar`, `solo_adjunto`, `a_incierto`, `procesar` (R5–R8) y el `finally` de R9 (excepción antes y durante la grabación)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r5 or f053_r6 or f053_r7 or f053_r8 or f053_r9"`
- [ ] T9: No admitido sin llamadas al puerto de Sigrid, y duplicados: `ya_en_sigrid` en los dos modos y retomar `incierto` con 0, 1 y 2 resultados (R10, R14, R15)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r14 or f053_r15 or f053_r10_sin_llamadas"`
- [ ] T10: Previa y simulación: se guardan petición y respuesta, 400 de la previa → `error`, previa limpia → `simulado`, y en simulación ninguna llamada lleva `commit=true` (R16, R18, R19)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r16 or f053_r19"`
- [ ] T11: Modo real: una sola grabación sin reintento, `registrado` con `con_ide`/`cod`; adjunto con `contip` 14, `gratipide` 0 y `sha256`; `idempotente` cuenta como colgado; fallo del adjunto y reintento solo del adjunto (R20–R23)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r20 or f053_r22 or f053_r23"`
- [ ] T12: `verificar_anulacion` en sv9: `anulado` si el `con.ide` ya no existe, aviso «sigue en Sigrid» si existe, e ignorada si el alta no está `registrado` (R28)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_r28`

## Bloque D · adaptadores de sv9

- [ ] T13: `sigrid_api_alta_client`: cuerpos exactos de las tres rutas, reintento con tenacity en lecturas/previa/adjunto y **ninguno** en la grabación, `timeout` 240 s, la clave nunca en logs (R24, R33, R35)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r24 or f053_r33 or f053_r35"`
- [ ] T14: `sql_alta_repository`: reclamación con `FOR UPDATE`, lectura de datos, guardado con `historial_json`; tests del SQL generado y de la traducción fila → `DatosAlta`  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_repositorio` + MANUAL de T26
- [ ] T15: `pdf_sharepoint` con `GraphSharePointClient` falso (ruta relativa del merge; sin ruta → adjunto en error)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_pdf`
- [ ] T16: Worker, composición y `main_worker.py` sobre `COLA_FEEDBACK`: resultado de negocio confirma, fallo de infraestructura antes de reclamar reencola, mensaje de otro `tipo` a poison  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_worker`

## Bloque E · sv4

- [ ] T17: Settings de sv4 y puerto/cliente de colas: `notify_document_approved` devuelve si publicó y `solicitar_alta_sigrid(document_id, accion)`  |  Verificación: `pytest services/albaranes-front -k f053_colas`
- [ ] T18: `ReviewService` publica solo en el paso a aprobado, por los dos caminos; nada con DESDE vacía; fallo al publicar no deshace la aprobación y se avisa (R1–R4)  |  Verificación: `pytest services/albaranes-front -k "f053_r1 or f053_r2 or f053_r3 or f053_r4"`
- [ ] T19: Repositorio de sv4: `leer_alta_sigrid`, `es_aprobado` y `_exigir_desbloqueado` llamado en la sesión de cada método de R26; sin tabla = sin alta; sv4 no escribe la tabla (R26, R34)  |  Verificación: `pytest services/albaranes-front -k "f053_r26 or f053_r34"` + MANUAL de T26
- [ ] T20: `app.py`: las 16 rutas que escriben o publican rechazan con alta bloqueante (parametrizado: 409 en API, redirección con aviso en formularios, nada cambia); saltos de R27; rutas nuevas de R28 y R30  |  Verificación: `pytest services/albaranes-front -k "f053_r25 or f053_r27 or f053_r28 or f053_r30"`
- [ ] T21: Panel `_alta_sigrid.html` en la ficha y estado en el listado, con cada estado y los dos modos (R29–R31)  |  Verificación: `pytest services/albaranes-front -k "f053_r29 or f053_r31"`

## Bloque F · documentación, infra y puertas

- [ ] T22: `infra/`: sv9 en `$APPS`, build y `create_capps` (KEDA sobre `q-feedback`, máximo 1 réplica, secreto de Key Vault), redactado  |  Verificación: MANUAL (humano) — leer el diff; `.\deploy.ps1 -Only sv9 -WhatIf` si el script lo admite
- [ ] T23: `docs/ARCHITECTURE.md`, `docs/referencia/dominio_negocio_albaranes.md` §5.2 y `azure-apps/albaranes.md` (commit aparte en ese repo) según design §9; NO `CLAUDE.md` ni `sigrid_api.md` (los decide el humano)  |  Verificación: revisión del reviewer
- [ ] T24: Cobertura de líneas cambiadas ≥ 80 %  |  Verificación: `python -m harness.cobertura --base dev --config harness/rigor.json`
- [ ] T25: Campaña de mutación COMPLETA, 0 supervivientes sin test nuevo o justificación aceptada  |  Verificación: `python -m harness.mutacion --feature F-053`

## Bloque G · verificación REAL (solo el humano; cada paso con su autorización)

- [ ] T26: LOCAL (Azurite + PostgreSQL local + sigrid-api en **simulación**, `ALTA_SIGRID_COMMIT` sin poner): aprobar tres documentos —uno admisible, uno con línea fuera de contrato, uno cuyo número ya está en Sigrid— y leer `psql "$env:ALBARANES_DB_URL" -c "SELECT document_id, estado, modo, sigrid_cod, motivos_json FROM albaran_altas_sigrid;"`. VERDE si salen `simulado`, `no_admitido` (`linea_fuera_de_contrato`) y `ya_en_sigrid`, y desaprobar el primero funciona (no es bloqueante)  |  Verificación: MANUAL (humano)
- [ ] T27: Cerrojo real: con un alta puesta a mano en `registrado` en la BBDD LOCAL, probar en `http://localhost:8004` guardar, desaprobar, deshacer, borrar y revalorar; todos rechazados y la fila del merge sin cambios  |  Verificación: MANUAL (humano)
- [ ] T28: AZURE en simulación (tras desplegar sv3 → sv9 → sv4 con DESDE puesta): revisar a diario los `simulado`/`revisar`/`no_admitido` y medir cuántos aprobados serían admisibles  |  Verificación: MANUAL (humano) — mismo SELECT contra la BBDD real, solo lectura
- [ ] T29: PRIMERA GRABACIÓN REAL, con autorización expresa y sobre un albarán elegido por el humano: `ALTA_SIGRID_COMMIT=true`, aprobar, comprobar en la UI de Sigrid cabecera, líneas, stock, `canser` y el PDF adjunto; volver a publicar a mano en `q-feedback` el mensaje de alta de ese documento y comprobar que no se crea otro (sigue `registrado` sin cambios)  |  Verificación: MANUAL (humano)
- [ ] T30: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
