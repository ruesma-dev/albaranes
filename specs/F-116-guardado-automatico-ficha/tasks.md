<!-- specs/F-116-guardado-automatico-ficha/tasks.md -->
# F-116 · Tareas

Rama `feature/F-116-guardado-automatico-ficha`. Un commit por tarea (`F-116 Tn: ...`). Tests antes o junto al código (fase RED en el informe).

- [x] T1: `CabeceraEditBody` en `domain/models/review_models.py` (design §4.1)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_cabecera_api.py -k "r5"`
- [x] T2: `update_cabecera_campos` en el repositorio (§4.2) con sus tests sobre SQLite (R1–R4)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_cabecera_api.py -k "r1 or r2 or r3 or r4"`
- [x] T3: `editar_cabecera` en el servicio con su deshacer y `PATCH /api/documents/{id}/cabecera` en `app.py` (§4.3; R1–R6)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_cabecera_api.py`
- [x] T4: Test de R18 (PATCH de fila sin `bloquear`: no bloquea, edición sin `bloqueada`, deshacer «Editar línea») y R19 en sv6 (citar el existente o añadirlo)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_lineas_api.py` y `pytest services/albaran-valoracion-persist/tests/test_f106_reaplicar.py`
- [x] T5: Plantilla y CSS: `#autoguardado-estado`, `data-guardado` de los cuatro campos, `.campo-guardado`, `.campo-no-guardado`, `.fila-autoguardada` (R10, R12)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_ficha.py`
- [x] T6: Cola de escritura en `app.js`: `instalarColaEscrituras`, `encolar`, `hayEscriturasEnCurso`, `beforeunload` (§4.4; R24, R27)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_autoguardado_js.py -k "r24 or r27"`
- [x] T7: Autoguardado de cabecera: `valorCabeceraParaGuardar`, `autoguardarCampoCabecera`, `wireAutoguardadoCabecera` (§4.5; R7–R12, R26)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_autoguardado_js.py -k "r7 or r8 or r9 or r10 or r11 or r12 or r26"`
- [x] T8: `enviarFila` con opciones y autoguardado de filas: `autoguardarFila`, `valoresDeFila`, `consolidarSinBloquear`, `blur` de cada celda (§4.6; R13–R17, R20); ajustar `test_f077_r12` y `test_f106_r12` como declara R30  |  Verificación: `pytest services/albaranes-front/tests/test_f116_autoguardado_js.py -k "r13 or r14 or r15 or r16 or r17 or r20"` y `pytest services/albaranes-front/tests/test_f077_guardar_y_aprobar_js.py services/albaranes-front/tests/test_f106_js.py services/albaranes-front/tests/test_f065_f1_js.py`
- [x] T9: Botones: `filasParaGuardar` en «Guardar todas» y `guardarFilasPendientes`; los tres esperan a la Cola antes de elegir filas (§4.6; R21–R23, R25)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_autoguardado_js.py -k "r21 or r22 or r23 or r25"` y `pytest services/albaranes-front/tests/test_f077_guardar_y_aprobar_js.py`
- [x] T10: Deshacer global: etiqueta `cabecera` y refresco con el evento `autoguardado` (R28)  |  Verificación: `pytest services/albaranes-front/tests/test_f116_autoguardado_js.py -k "r28"`
- [x] T11: Suite completa de sv4 sin relajar aserciones (R29, R30)  |  Verificación: `pytest services/albaranes-front/tests`
- [x] T12: Documentación: `docs/ARCHITECTURE.md` regla 20, `services/albaranes-front/sv4.md` (endpoint y autoguardado), `azure-apps/albaranes.md` (viñeta de `bloqueada`; commit local en `azure-apps`, sin push) (R31)  |  Verificación: revisión del reviewer contra R31
- [x] T13: M1 en Chrome y Edge con sv4 local (design §7)  |  Verificación: MANUAL (líder)
- [ ] T14: Despliegue de sv4 sola (`cd infra; Set-DeployTag; .\deploy.ps1 -Only sv4`) y M2 de solo lectura  |  Verificación: MANUAL (humano despliega; líder M2)
- [x] T15: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
