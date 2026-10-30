<!-- specs/F-113-mime-adjuntos-octet-stream/tasks.md -->
# F-113 · Tareas (v1)

Rama `feature/F-113-mime-adjuntos-octet-stream`, worktree `../albaranes-F-113`. Rigor `estandar`:
- fase RED en cada tarea con test (traza en `progress/impl_F-113.md`);
- cobertura de líneas cambiadas ≥ 80 %;
- mutación muestreada (20);
- un commit por tarea, `F-113 Tn: ...`;
- sin `git push`;
- tests sin red ni BBDD.

URGENTE: no espera a F-106 y se fusiona en `dev` antes que ella (D-8). Las tareas MANUAL de producción son de solo
lectura, salvo el despliegue y el reenvío del correo, que los hace el humano.

- [ ] T1: `ruesma_comun/mime.py` (`detectar_mime`, `nombre_coherente`, `es_mime_generico`, `MIME_PDF`, `MIME_GENERICO`; tablas de design §4), con sus tests parametrizados de firmas, contradicciones, datos cortos o vacíos y nombres (R1–R5)  |  Verificación: `pytest services/albaranes-comun/tests/test_f113_mime.py`
- [ ] T2: `normalizar_adjuntos` pasa por `_con_mime_real`, con WARNING sin nombre e identidad si no cambia; test del `image_url` de OpenAI con el SDK simulado y un JPEG declarado `octet-stream` (R7–R10)  |  Verificación: `pytest services/albaranes-comun/tests/test_f113_llm_adjuntos.py services/albaranes-comun -k "llm"`
- [ ] T3: versión 0.9.1 en `__init__.py` y `pyproject.toml`, y README de comun (R6, R23 en su parte de comun)  |  Verificación: `pytest services/albaranes-comun`
- [ ] T4: sv1 `_ingerir`: MIME real y nombre coherente antes del troceo; `attachment_content_type_declarado` solo si hay corrección; WARNING sin nombre; casos WhatsApp `.jpeg` `octet-stream` y JPEG con nombre `.pdf` (R11–R16)  |  Verificación: `pytest services/albaranes-email/tests/test_f113_mime_real.py services/albaranes-email -k "f054 or f048 or intake"`
- [ ] T5: sv2 `_build_attachments` con `detectar_mime` y `nombre_coherente` al principio; JPEG `octet-stream` ⇒ imagen realzada; PDF genérico sin `.pdf` ⇒ PDF; caso coherente idéntico al de hoy (R17–R19)  |  Verificación: `pytest services/albaranes-api/tests/test_f113_build_attachments.py services/albaranes-api -k "build_attachments or preproceso"`
- [ ] T6: script `medir_f113_octet_stream.py` de solo lectura y su test sin BBDD (R20, R21)  |  Verificación: `pytest services/albaranes-email/tests/test_f113_medicion.py`
- [ ] T7: documentación: `docs/ARCHITECTURE.md` (regla de blobs de `input/`) y `azure-apps/albaranes.md`, este último con commit local en ese repo y sin push (R23)  |  Verificación: lectura del reviewer
- [ ] T8: `bash harness/init.sh` en verde (cierre del código, antes de la review)  |  Verificación: `bash harness/init.sh`
- [ ] T9: MANUAL (líder o humano, solo lectura): el script de T6 contra Azure antes de desplegar, con las `PG_*` de Azure en la consola; anotar el recuento en `progress/impl_F-113.md` (D-6)  |  Verificación: MANUAL (humano) · recuento anotado
- [ ] T10: MANUAL (humano): desplegar sv1 y después sv2 desde `infra/`: `Set-DeployTag; .\deploy.ps1 -Only sv1`, `.\deploy.ps1 -Only sv2` y `.\check_deploy.ps1` (D-8)  |  Verificación: MANUAL (humano) · los dos con la revisión nueva en `Running`
- [ ] T11: MANUAL (humano): recuperar los 5 documentos del 2026-10-30 según D-5 y comprobar en sv4 que aparecen los 5 albaranes de FEYMACO de la 0728 (R22)  |  Verificación: MANUAL (humano) · 5 albaranes nuevos en sv4
- [ ] T12: MANUAL (líder, solo lectura): el script de T6 a las 24 h del despliegue; debe salir 0 casos nuevos (D-6)  |  Verificación: MANUAL (humano) · recuento anotado
- [ ] T13: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
