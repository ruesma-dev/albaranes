<!-- specs/F-108-fecha-numero-editables/tasks.md -->
# F-108 · Tareas (v1)

Rama `feature/F-108-fecha-numero-editables` (desde `dev` `43e87e5`), worktree `../albaranes-F-108`. Rigor `estandar`: **fase RED** en cada tarea con test (el test se escribe primero, se ve fallar y la traza va a `progress/impl_F-108.md`; un test de guarda que nace en verde demuestra su RED con la mutación inversa, anotada), cobertura de líneas cambiadas ≥ 80 % y mutación muestreada a 20. Un commit por tarea, `F-108 Tn: ...`. Sin `git push`. Tests sin red ni BBDD; la suite de sv4 se ejecuta sola (si `init.sh` da KO por el `.venv` de sv4 en el worktree, *junction* como en F-104, a quitar con `cmd /c rmdir` antes de `git worktree remove`). Precondición de `in_progress`: D1–D7 (`design.md` §8) validadas por el humano; si D4 = b, T4 se reduce a R5–R10 y R11 se retira; si D2 = b, la vista de R4 pasa a `AAAA-MM-DD`.

## Bloque A · dominio

- [x] T1: RED de `test_f108_fecha_albaran.py` con la tabla `CASOS` (R1–R4) y el contraste con `_RE_FECHA` leído de la fuente de sv9 (R10); luego `domain/services/fecha_albaran.py` (design §4.1) y los tres errores en `review_models.py` (§4.2) hasta verde  |  Verificación: `pytest services/albaranes-front -k "f108_r1 or f108_r2 or f108_r3 or f108_r4 or f108_r10"`

## Bloque B · servidor

- [x] T2: RED de `test_f108_guardado.py` para el guardado: `28/10/2026`, `28-10-26` y `2026-10-28` guardan `2026-10-28` (R5), vacío guarda nulo (R6), `31/02/2026` y `abc` ⇒ error sin cambios en el documento (R7), número recortado y sin otro cambio (R8), 129 caracteres ⇒ error sin cambios (R9), aprobado con fecha mala ⇒ sigue el 409 de aprobado (orden de §4.3); luego el repositorio (§4.3) hasta verde  |  Verificación: `pytest services/albaranes-front -k "f108_r5 or f108_r6 or f108_r7 or f108_r8 or f108_r9"`
- [x] T3: RED de los tests de ruta (TestClient con servicio falso): PUT con fecha mala ⇒ 422 con `detail` texto igual al aviso de R3; número largo ⇒ 422 con su aviso (R7, R9); luego los manejadores de `app.py` y el filtro `fecha_albaran_ver` (§4.3) hasta verde  |  Verificación: `pytest services/albaranes-front -k "f108_r7 or f108_r9"`
- [x] T4: RED de R11 (D4 = a): «Guardar y aprobar» sin fecha, con fecha `dd/mm/aaaa` guardada que el PUT normaliza (sí aprueba), sin número ⇒ no aprueba; listado (`set_approved`) con fecha nula, `08/10/2026` guardada o número vacío ⇒ no aprueba y vuelve con el aviso; un documento completo aprueba como hoy; luego `_exigir_cabecera_completa`, el 409 y el `except` de `approve_from_list` hasta verde  |  Verificación: `pytest services/albaranes-front -k "f108_r11 or f065_r20 or f053_t20"`

## Bloque C · ficha

- [x] T5: RED de `test_f108_ficha.py` (render): ficha editable con `#fecha` en `dd/mm/aaaa`, `placeholder`, sin `readonly`, botón «Calendario» `type="button"` con `title`/`aria-label`, `#fecha_calendario` `type="date"` y `#fecha-error` oculto; `#numero_albaran` con `maxlength="128"` (R12, R13); aprobado ⇒ los dos `readonly`, fecha en `dd/mm/aaaa`, sin botón ni selector (R22); fecha guardada ilegible se ve tal cual (R4); vistas crudas con la fecha de la IA (R23); luego plantilla, `conftest.py` y `styles.css` hasta verde  |  Verificación: `pytest services/albaranes-front -k "f108_r12 or f108_r13 or f108_r22 or f108_r23"`
- [x] T6: RED de `test_f108_fecha_js.py` (node + `dom_falso.js`): `parseFechaEs` da lo mismo que Python en toda la tabla `CASOS` (R20); el literal del aviso en `app.js` = `AVISO_FECHA_NO_VALIDA` (R3); `blur` reescribe `28-10-26` ⇒ `28/10/2026` (R16) y marca en rojo con aviso `31/02/2026`, que se quita al corregir (R17); `collectPayload` manda ISO, nulo o lo escrito (R19); luego `parseFechaEs`, `fechaParaVer`, `fechaParaEnviar`, el `blur`/`input` de `wireFechaAlbaran` y `collectPayload` hasta verde  |  Verificación: `pytest services/albaranes-front -k "f108_r16 or f108_r17 or f108_r19 or f108_r20 or f108_r3"`
- [x] T7: RED del calendario y de la guarda de guardado (node): el botón pone en el selector el día escrito (o vacío) y llama a `showPicker` (R14); sin `showPicker` o si lanza, el selector queda visible y con el foco (R14); `change` del selector escribe `dd/mm/aaaa` y quita la marca (R15); «Guardar» y «Guardar y aprobar» con fecha mala ⇒ ningún PATCH ni PUT, `alert` con el aviso y foco en `#fecha` (R18); ningún manejador nuevo deja un `keydown` con `defaultPrevented` (R21); luego el resto de `wireFechaAlbaran` y la guarda de `guardarCabecera` hasta verde; los tests de F-077 siguen en verde  |  Verificación: `pytest services/albaranes-front -k "f108_r14 or f108_r15 or f108_r18 or f108_r21 or f077"`

## Bloque D · documentación y calidad

- [x] T8: Viñeta en la regla 20 de `docs/ARCHITECTURE.md` y apartado en `services/albaranes-front/sv4.md`: sv4 guarda la fecha en `AAAA-MM-DD`, la enseña en `dd/mm/aaaa`, formatos admitidos, 422 con texto, calendario y (si D4 = a) qué impide aprobar (R27). `azure-apps/albaranes.md` no cambia (no cambia lo que sv4 expone ni consume)  |  Verificación: revisión del reviewer contra R27
- [x] T9: Campaña de mutación muestreada (20, semilla fija) sobre `domain/services/fecha_albaran.py` y lo cambiado del repositorio; supervivientes con test nuevo o justificación en `progress/mutacion_F-108.md`  |  Verificación: `python -m harness.mutacion --feature F-108`
- [x] T10: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`

## Bloque E · verificación manual (tras APPROVED)

- [x] M1: Navegador sobre sv4 local con BBDD local: guion de design §7 M1 en Chrome y Edge, con el `SELECT` de la fecha guardada (R12–R19, R21, R22, R28)  |  Verificación: MANUAL (líder) — design §7 M1
- [ ] M-D: Despliegue de sv4 sola  |  Verificación: MANUAL (humano) — `Set-DeployTag; .\deploy.ps1 -Only sv4` desde `infra/` y arranque limpio en los logs
- [ ] M2: Producción tras el despliegue, solo lectura, sin pulsar Guardar, Aprobar ni Valorar: ficha `ec291d76…` con `09/10/2026` y el calendario abriéndose (R28)  |  Verificación: MANUAL (líder, solo lectura) — design §7 M2
- [ ] M3: Las 2 fechas guardadas en `dd/mm/aaaa` (`ae044452…`, `6ae1d618…`) según D5  |  Verificación: MANUAL (humano) — design §7 M3
- [ ] T11: Ejecutar `bash harness/init.sh` en verde (cierre, tras M1–M3)  |  Verificación: `bash harness/init.sh`
