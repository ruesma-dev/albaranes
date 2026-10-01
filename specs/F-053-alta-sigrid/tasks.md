<!-- specs/F-053-alta-sigrid/tasks.md -->
# F-053 · Tareas

Rama `feature/F-053-alta-sigrid`. Rigor `critico`: **fase RED obligatoria** en
toda tarea con test (falla antes, pasa después; traza en `progress/impl_F-053.md`).
Un commit por tarea, `F-053 Tn: ...`. Sin `git push`. Tests `test_f053_rN_*`,
sin red ni BBDD: fakes de `AltaRepository`, `SigridAltaPort` y `PdfAlbaranPort`,
y `httpx.MockTransport` para el cliente. **No se empieza sin la PARADA 1**
(aprobar esta v4: todas las decisiones están cerradas en `progress/spec_F-053.md`),
**sin T0 ni con PRE-1 (= F-009 de sigrid-api) sin desplegar** (design §1–§2), y
**no se fusiona en `dev` antes que F-052 y F-051** (design §8). Los tests del
cliente usan el contrato de F-009 tal como quede en sigrid-api, no el de design §2 si difiere.

## Bloque 0 · medición (humano, 2026-10-01: «medir antes»)

- [ ] T0b: Verificación de solo lectura (antigua pregunta 6): ¿las altas manuales llevan el número del proveedor en «Referencia» (`dca.entref`)? Propuesta por defecto: sí, y se busca por CIF + `entref` (R14). Comprobarlo con `sql/read` (`SELECT TOP 50 c.cod, d.entcif, d.entref FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.tip = 14 AND c.fec >= 20260901 ORDER BY c.ide DESC`) contra 5 albaranes en papel  |  Verificación: MANUAL (humano), con autorización; si no se cumple, se para y se replantea R14
- [ ] T0c: Verificación de solo lectura (antigua pregunta 9): fijar el login de Sigrid para `ALTA_SIGRID_USUARIO` (debe existir en `dbo.usu`; propuesta: un usuario de servicio del área de compras) y comprobar en las App Settings de sigrid-api que `SIGRID_DOCUMENT_ALLOWED_GRATIPIDE` incluye `0` y `SIGRID_DOCUMENT_ALLOWED_MAGIC` la firma de PDF  |  Verificación: MANUAL (humano) — `az functionapp config appsettings list` (solo lectura); si falta alguno, cambiarlo es del proyecto sigrid-api
- [ ] T0: Ejecutar la medición de solo lectura (script y tests ya en la rama: `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py`) y decidir con el resultado si se sigue y con qué alcance  |  Verificación: MANUAL (humano) — comando en `progress/spec_F-053.md`; tests del script: `pytest services/albaranes-persistencia -k f053_medicion`

## Bloque A · contratos y esquema

- [ ] T1: `MensajeFeedback.accion` (`alta` | `verificar_anulacion`, defecto `alta`), docstring con sv9 como consumidor (R32), y `ruesma_comun/valoracion.py` con `esta_valorado` (cada caso del glosario: `ok`, manual completa, `manual`/`no_contract` con importe nulo o sin importes, `partial`, `failed`, sin valoración) (R38)  |  Verificación: `pytest services/albaranes-comun -k f053`
- [ ] T2: DDL de `albaran_altas_sigrid` e índice en `schema_contribution.py` de sv3, idempotente (R36, design §6)  |  Verificación: `pytest services/albaranes-persistencia -k f053_r36`
- [ ] T3: Esqueleto de sv9 (`services/albaranes-alta-sigrid`): settings con los defectos de design §7 (`ALTA_SIGRID_COMMIT` solo es `true` con el literal `true`), logging, Dockerfile, requirements, `sv9.md`, `.env.example` sin valores, alta en `harness/servicios.json`  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_r19_modo` y `pytest tests/test_estructura_monorepo.py`
- [ ] T4: Modelos de dominio y los tres puertos de sv9 (design §3)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_modelos`

## Bloque B · dominio puro de sv9

- [ ] T5: `validador_alta.validar_y_construir`: los 10 motivos de R10 (con `no_valorado` vía `esta_valorado`) (uno por test y uno con todos a la vez), sin vincular y negativas admisibles (R11), petición de PRE-1 de R12 (una línea por línea a registrar, con su signo; vinculadas con `ctrpro_ide`; sin vincular con `producto` = `ALTA_SIGRID_PRODUCTO_POR_DEFECTO`; `partida` o `almacen`; `referencia_externa`, `referencia_linea`, `empide`) y exclusión de las de importe nulo o 0 (R13)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r10 or f053_r11 or f053_r12 or f053_r13"`
- [ ] T6: `comparador_previa.comparar`: `importe_distinto` (en el borde de la tolerancia y fuera), `lineas_distintas` (sobra y falta), `partida_distinta` (partida y almacén) y `aviso_bloqueante` (R17)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_r17`
- [ ] T7: `clasificador`: 200 ok con `committed` o `idempotente` → `registrado`; 400 → `error`; 401/403 → `error`; 5xx, tiempo agotado y conexión → `incierto` (R18, R20, R21)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r18 or f053_r21"`

## Bloque C · servicio de sv9

- [ ] T8: `AltaSigridService`, entrada: reclamación y sus salidas `ignorar`, `solo_adjunto`, `a_incierto`, `procesar` (R5–R8) y el `finally` de R9 (excepción antes y durante la grabación)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r5 or f053_r6 or f053_r7 or f053_r8 or f053_r9"`
- [ ] T9: No admitido sin llamadas al puerto de Sigrid, y duplicados: `synckey` nuestra → `registrado`, ajena → `ya_en_sigrid` (en los dos modos), y retomar `incierto`: encontrado → `registrado`, no encontrado → reenvío y `idempotente` → `registrado` (R10, R14, R15)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r14 or f053_r15 or f053_r10_sin_llamadas"`
- [ ] T10: Previa y simulación: se guardan petición y respuesta, 400 de la previa → `error`, previa limpia → `simulado`, y en simulación ninguna llamada lleva `commit=true` (R16, R18, R19)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r16 or f053_r19"`
- [ ] T11: Modo real: una sola grabación sin reintento, `registrado` con `con_ide`/`cod`; adjunto con `contip` 14, `gratipide` 0 y `sha256`; `idempotente` cuenta como colgado; fallo del adjunto y reintento solo del adjunto (R20–R23)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r20 or f053_r22 or f053_r23"`
- [ ] T12: `verificar_anulacion` en sv9: `anulado` si el `con.ide` ya no existe, aviso «sigue en Sigrid» si existe, e ignorada si el alta no está `registrado` (R28)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_r28`

## Bloque D · adaptadores de sv9

- [ ] T13: `sigrid_api_alta_client`: cuerpos exactos de `sql/read`, el alta de PRE-1 y `concepto-grafico`, reintento con tenacity en lecturas/previa/adjunto y **ninguno** en la grabación, `timeout` 240 s, la clave nunca en logs (R24, R33, R35)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f053_r24 or f053_r33 or f053_r35"`
- [ ] T14: `sql_alta_repository`: reclamación con `FOR UPDATE`, lectura de datos, guardado con `historial_json`; tests del SQL generado y de la traducción fila → `DatosAlta`  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_repositorio` + MANUAL de T26
- [ ] T15: `pdf_sharepoint` con `GraphSharePointClient` falso (ruta relativa del merge; sin ruta → adjunto en error)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_pdf`
- [ ] T16: Worker, composición y `main_worker.py` sobre `COLA_FEEDBACK`: resultado de negocio confirma, fallo de infraestructura antes de reclamar reencola, mensaje de otro `tipo` a poison  |  Verificación: `pytest services/albaranes-alta-sigrid -k f053_worker`

## Bloque E · sv4

- [ ] T17: Settings de sv4 y puerto/cliente de colas: `notify_document_approved` devuelve si publicó y `solicitar_alta_sigrid(document_id, accion)`  |  Verificación: `pytest services/albaranes-front -k f053_colas`
- [ ] T18: `ReviewService` publica solo en el paso a aprobado, por los dos caminos; nada con DESDE vacía; fallo al publicar no deshace la aprobación y se avisa (R1–R4)  |  Verificación: `pytest services/albaranes-front -k "f053_r1 or f053_r2 or f053_r3 or f053_r4"`
- [ ] T19: Repositorio de sv4: `leer_alta_sigrid`, `es_aprobado` y `_exigir_desbloqueado` llamado en la sesión de cada método de R26; sin tabla = sin alta; sv4 no escribe la tabla (R26, R34)  |  Verificación: `pytest services/albaranes-front -k "f053_r26 or f053_r34"` + MANUAL de T26
- [ ] T20: `app.py`: las 16 rutas que escriben o publican rechazan con alta bloqueante (parametrizado: 409 en API, redirección con aviso en formularios, nada cambia); saltos de R27; rutas nuevas de R28 y R30  |  Verificación: `pytest services/albaranes-front -k "f053_r25 or f053_r27 or f053_r28 or f053_r30"`
- [ ] T21b: No se aprueba un albarán no valorado (`esta_valorado`; uno valorado a mano sin contrato sí) por ninguno de los dos caminos, con DESDE vacía o no, sin cambiar nada; botones deshabilitados en ficha y listado (R37)  |  Verificación: `pytest services/albaranes-front -k f053_r37`
- [ ] T21: Panel `_alta_sigrid.html` en la ficha y estado en el listado, con cada estado y los dos modos (R29–R31)  |  Verificación: `pytest services/albaranes-front -k "f053_r29 or f053_r31"`

## Bloque F · documentación, infra y puertas

- [ ] T22: `infra/`: sv9 en `$APPS`, build y `create_capps` (KEDA sobre `q-feedback`, máximo 1 réplica, secreto de Key Vault), redactado  |  Verificación: MANUAL (humano) — leer el diff; `.\deploy.ps1 -Only sv9 -WhatIf` si el script lo admite
- [ ] T23: `docs/ARCHITECTURE.md`, `docs/referencia/dominio_negocio_albaranes.md` §5.2 y `azure-apps/albaranes.md` (commit aparte en ese repo) según design §9; NO `CLAUDE.md` ni `sigrid_api.md` (los decide el humano)  |  Verificación: revisión del reviewer
- [ ] T24: Cobertura de líneas cambiadas ≥ 80 %  |  Verificación: `python -m harness.cobertura --base dev --config harness/rigor.json`
- [ ] T25: Campaña de mutación COMPLETA, 0 supervivientes sin test nuevo o justificación aceptada  |  Verificación: `python -m harness.mutacion --feature F-053`

## Bloque G · verificación REAL (solo el humano; cada paso con su autorización)

- [ ] T26: LOCAL (Azurite + PostgreSQL local + sigrid-api en **simulación**, `ALTA_SIGRID_COMMIT` sin poner): aprobar cinco documentos —uno todo vinculado, uno con líneas sin vincular con partida (producto MA9999 en la previa), uno con una línea negativa, uno sin contrato valorado a mano, uno con una línea sin partida ni almacén, uno cuyo número ya está en Sigrid— e intentar aprobar uno sin valorar (rechazado); leer `psql "$env:ALBARANES_DB_URL" -c "SELECT document_id, estado, modo, sigrid_cod, motivos_json FROM albaran_altas_sigrid;"`. VERDE si salen `simulado` ×4 (con partidas, producto y signo pedidos en la previa), `no_admitido` (`linea_sin_partida`) y `ya_en_sigrid`, y desaprobar el primero funciona (no es bloqueante)  |  Verificación: MANUAL (humano)
- [ ] T27: Cerrojo real: con un alta puesta a mano en `registrado` en la BBDD LOCAL, probar en `http://localhost:8004` guardar, desaprobar, deshacer, borrar y revalorar; todos rechazados y la fila del merge sin cambios  |  Verificación: MANUAL (humano)
- [ ] T28: AZURE en simulación (tras desplegar sv3 → sv9 → sv4 con DESDE puesta): revisar a diario los `simulado`/`revisar`/`no_admitido` y comparar con la medición de T0  |  Verificación: MANUAL (humano) — mismo SELECT contra la BBDD real, solo lectura
- [ ] T29: PRIMERA GRABACIÓN REAL, con autorización expresa y sobre un albarán elegido por el humano: `ALTA_SIGRID_COMMIT=true`, aprobar, comprobar en la UI de Sigrid cabecera, líneas (vinculadas y MA9999), partidas, stock, `canser` y el PDF adjunto; volver a publicar a mano en `q-feedback` el mensaje de alta de ese documento y comprobar que no se crea otro (sigue `registrado` sin cambios)  |  Verificación: MANUAL (humano)
- [ ] T30: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
