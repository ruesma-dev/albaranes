<!-- specs/F-104-codigos-contrato-v83/tasks.md -->
# F-104 · Tareas (v1)

Rama `feature/F-104-codigos-contrato-v83`, worktree `../albaranes-F-104` (*junction* `.venv` de sv4: quitarla con `cmd /c rmdir` antes de `git worktree remove`). Rigor `critico`: **fase RED obligatoria** en cada tarea con test (traza en `progress/impl_F-104.md`; un test de guarda que nace en verde demuestra su RED con la mutación inversa, anotada), mutación sin tope y 0 supervivientes sin justificar. Un commit por tarea, `F-104 Tn: ...`. Sin `git push`. Tests sin red ni BBDD; las suites de sv9 y sv4 se ejecutan cada una sola. Precondición de `in_progress`: D1 y D2 (`design.md` §8) validadas por el humano. Las MANUAL son de solo lectura y las hace el líder.

## Bloque A · sv9

- [x] T1: Los tres Errores v8.3 → `no_admitido` en `CODIGOS_CABECERA` (comentario y docstring v8.3), `proveedor_sin_albaran_previo` intacto; `TABLA_CABECERA` de `test_f053_clasificador.py` ampliada; tests de cada código en previa y grabación con su motivo de cabecera, del retirado aún `no_admitido` y de un código desconocido a `error` (R1–R3)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f104_r1 or f104_r2 or f104_r3 or f053_clasificador"`
- [x] T2: Tests de guarda de los avisos: defecto de `ALTA_SIGRID_AVISOS_BLOQUEANTES` sin los Avisos v8.3 y ningún `infra/*.ps1` ni `.env.example` que los nombre; una previa con los dos avisos de cabecera, configuración por defecto, sin `aviso_bloqueante` y con ambos (código y mensaje) en `avisos_json` en `simulado`, `revisar` y `registrado`; un 200 con `totales.tot`, `retenciones`, `n_retenciones` y `filas.dcarec` da los mismos motivos y lo guardado sin `filas` (R4–R6). Sin cambios de código de producción  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f104_r4 or f104_r5 or f104_r6"`

## Bloque B · sv4

- [x] T3: Los cinco textos de design §3.2 en `TEXTOS_MOTIVO_ALTA` (el del retirado se queda) y tests: texto exacto, no vacío, distinto del código; F-077 R27 en verde (R7, R10 en su parte de sv4)  |  Verificación: `pytest services/albaranes-front -k "f104_r7 or f104_r10 or f077_r27"`
- [ ] T4: `AltaSigridVista.avisos_sigrid` y la rama `texto` de «Avisos de Sigrid» en `_alta_sigrid.html` (D2): un aviso con texto sale «texto · mensaje (línea N)» con el código en `title`; uno sin texto, igual que hoy; los avisos no cambian estado ni bloqueo (R8, R9)  |  Verificación: `pytest services/albaranes-front -k "f104_r8 or f104_r9 or f077 or f053_t20"`

## Bloque C · documentación y calidad

- [ ] T5: `sv9.md` (cabecera v8.3 y sección «Códigos del contrato v8.3 (F-104)») y viñeta en §10 de `azure-apps/albaranes.md` (commit local en `azure-apps`, sin push) (R12)  |  Verificación: revisión del reviewer contra R12
- [ ] T6: Campaña de mutación sobre `clasificador.py` y `alta_sigrid_models.py` (sin tope); supervivientes con test nuevo o justificación en `progress/mutacion_F-104.md`  |  Verificación: `python -m harness.mutacion --feature F-104`
- [ ] T7: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`

## Bloque D · despliegue y verificación (MANUAL; tras APPROVED, fusión en `dev` e `init.sh` en verde)

- [ ] M1: Antes de desplegar, `ALTA_SIGRID_AVISOS_BLOQUEANTES` de `ca-sv9-alta-sigrid` sin Avisos v8.3 (R13)  |  Verificación: MANUAL (líder, solo lectura) — comando de design §6 M1
- [ ] M-D: Despliegue de sv9 y sv4, antes o a la vez que la F-015 de sigrid-api (design §7)  |  Verificación: MANUAL (humano) — `Set-DeployTag; .\deploy.ps1 -Only sv9,sv4` y arranque limpio en los logs
- [ ] M2: Tras el despliegue de F-015 de sigrid-api: SQL de design §6 M2 en verde y panel de un alta con `retencion_del_contrato` (M3); recuentos por estado en `progress/impl_F-104.md` (R14)  |  Verificación: MANUAL (líder, solo lectura) — SQL de design §6 M2 y navegador

## Bloque E · retirada (D1; solo con M2 en verde)

- [ ] T8: Quitar `proveedor_sin_albaran_previo` de `CODIGOS_CABECERA` y de `TABLA_CABECERA`; el test de R2 pasa a R10 (el retirado va a `error` por H25) y el caso de `test_f053_servicio_previa.py` usa `proveedor_no_encontrado`; el texto de sv4 se queda; `sv9.md` y §10 de `azure-apps` dicen «retirado»; mutación de `clasificador.py` repetida (R10)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f104 or f053_clasificador or f053_r18"` y `pytest services/albaranes-front -k "f104 or f077_r27"`
- [ ] T9: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
