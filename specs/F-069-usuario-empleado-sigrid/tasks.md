<!-- specs/F-069-usuario-empleado-sigrid/tasks.md -->
# F-069 · Tareas (v1)

Rama `feature/F-069-usuario-empleado-sigrid`. Rigor `critico`: **fase RED obligatoria** en cada tarea con test (traza en `progress/impl_F-069.md`), mutación sin tope y 0 supervivientes sin justificar. Un commit por tarea, `F-069 Tn: ...`. Sin `git push`. Tests `test_f069_rN_*` sin red ni BBDD (fakes de `f053_fakes.py`, `httpx.MockTransport`). **No se empieza sin la PARADA 1** (E1–E7 de `design.md` §9); si el humano cambia una recomendación, el spec-author ajusta los R y estas tareas antes. Las MANUAL de solo lectura las hace el líder o el humano; las que escriben en producción, solo el humano.

## Bloque A · medición (antes de tocar sv9)

- [ ] T1: Script `services/albaranes-alta-sigrid/scripts/proponer_equivalencias_f069.py` (+ `scripts/__init__.py`): funciones puras `veredicto`, `proponer`, `lista_json`, `filas_csv` y `main()` de solo lectura (design §6–§7); CSV UTF-8 BOM `;`; sin nombres ni DNI (R23–R26)  |  Verificación: `pytest services/albaranes-alta-sigrid -k f069_script` (veredictos `coinciden`/`un_dato`/`discrepan`/`sin_dato`, JSON solo con `coinciden`, todas las sentencias empiezan por `SELECT`, ninguna ruta distinta de `/api/sql/read`)
- [ ] T2: Ejecutar el script contra producción con las `PG_*` de Azure en la consola (el `.env` apunta a local) y validar cada consulta de design §7 (en especial el cruce `log`↔`con` de (d) y si `emp.ele` existe); resultado en `progress/medicion_F-069.md` (logins e `ide`, sin nombres ni DNI); el humano valida la Lista y decide E5 con el listado de R25  |  Verificación: MANUAL (líder o humano, solo lectura) — `python services/albaranes-alta-sigrid/scripts/proponer_equivalencias_f069.py --dias 180 --salida progress/`

## Bloque B · la Lista y la configuración de sv9

- [ ] T3: `Equivalencia`, `leer_equivalencias` y `entrada_de` en `domain/services/usuario_sigrid.py`: cada caso de R2 (no objeto, clave sin @ o con dos, partes vacías, clave repetida literal y por mayúsculas/espacios, valor no objeto, clave desconocida, sin `usu` ni `empide`, `usu` vacío o > 24, `empide` booleano/texto/decimal/0) y Entrada sin distinguir mayúsculas (R1)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f069_r1 or f069_r2"`
- [ ] T4: `Settings`: `ALTA_SIGRID_EQUIVALENCIAS_USUARIO` con validador (arranque fallido con motivo en el log), propiedades `equivalencias` y `empide_respaldo`; docstring; `.env.example` sin valores; log de arranque y aviso de Lista vacía con DESDE (R2–R3)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f069_r2_config or f069_r3"`
- [ ] T5: `existe_empleado` en el puerto, el cliente (`SQL_EXISTE_EMPLEADO`, etiqueta `f069-empleado`, reintentos de R24, `truncated`) y `SigridFalso` (R7, R12)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f069_cliente or f053_cliente"`

## Bloque C · resolución en el servicio

- [ ] T6: `OrigenUsuario`/`OrigenEmpleado`, `UsuarioResuelto`/`EmpleadoResuelto`; `_resolver_usuario` con la Entrada primero (R4–R6) y `UsuarioNoResuelto` cuando el `usu` de la Lista no casa  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f069_r4 or f069_r5 or f069_r6 or f053_r47 or f053_r48"`
- [ ] T7: `_resolver_empleado` y `MOTIVO_EMPLEADO`: cada fila de la tabla de design §2, `False` y excepción de `existe_empleado` ⇒ `error` sin previa ni búsqueda de altas a mano, sin leer `dbo.emp` si falla el `usu` (R7–R13)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f069_r7 or f069_r8 or f069_r9 or f069_r10 or f069_r11 or f069_r12 or f069_r13"`
- [ ] T8: `ConfigAlta` sin `empide` y `validar_y_construir(..., *, empide=None)`; `composition.py` con `equivalencias` y `empide_respaldo`; los 4 sitios de `ConfigAlta(empide=...)` de design §4 ajustados (R7–R9)  |  Verificación: `pytest services/albaranes-alta-sigrid` (toda la suite de sv9 en verde)
- [ ] T9: `resolucion` en `peticion_json` (R15), conservada al retomar un `incierto` sin resolver nada (R14), nunca en el cuerpo enviado por previa, grabación ni retoma (R16, con `httpx.MockTransport`), log de R17 y adjunto con el `usu` guardado (R19)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f069_r14 or f069_r15 or f069_r16 or f069_r17 or f069_r19"`
- [ ] T10: `peor_caso_mensaje_s` con las lecturas de `dbo.usu` y `dbo.emp`; ajustar el test que fije la visibilidad de hoy (R18)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f069_r18 or worker"`

## Bloque D · panel de sv4

- [ ] T11: `alta_sigrid_models.py`: `empide`, `usu_respaldo` por `resolucion` con la regla de hoy como respaldo, textos de `empleado_no_resuelto` y `usuario_no_resuelto`; constante `"resolucion"` contrastada con la fuente de sv9; `_alta_sigrid.html` con «Empleado de Sigrid» (R20–R22)  |  Verificación: `pytest services/albaranes-front -k "f069 or f077_motivos"`

## Bloque E · infra, documentación y coordinación

- [ ] T12: `infra/00_capps_vars.ps1` (Lista validada en T2, `EscaparJsonNativo` compartida con el mapeo), `create_capps_sv9.ps1` y `set_alta_sigrid.ps1` (solo sv9, escapada, releída; nunca `ALTA_SIGRID_COMMIT`) (R27)  |  Verificación: `pytest services/albaranes-alta-sigrid -k "f069_r27 or f053_r47_config"` (tests de texto sobre los `.ps1`, como los de F-053)
- [ ] T13: `sv9.md`, regla 19 de `docs/ARCHITECTURE.md` y §10 de `azure-apps/albaranes.md` (commit local en `azure-apps`, sin push) (R28)  |  Verificación: revisión del reviewer contra R28; `git -C C:\Users\pgris\PycharmProjects\azure-apps log -1`
- [ ] T14: `progress/propuestas_a_sigrid_api_F-069.md` con las dos peticiones de design §10 (validar `empide`; las 46 altas junto con F-103), sin secretos  |  Verificación: revisión del humano antes de pasarla a la sesión de sigrid-api
- [ ] T15: Campaña de mutación sobre los ficheros cambiados de sv9 y sv4 (sin tope, rigor `critico`), supervivientes con test nuevo o justificación en `progress/mutacion_F-069.md`  |  Verificación: `python -m harness.mutacion --feature F-069`

## Bloque F · despliegue y verificación real (humano, tras APPROVED y fusión en `dev`)

- [ ] T16: Orden de design §8: Lista en sv9 con `set_alta_sigrid.ps1` y relectura → desplegar sv9 → desplegar sv4; comprobar en el log de arranque el número de Entradas y que la revisión nueva está activa  |  Verificación: MANUAL (humano, ESCRIBE EN PRODUCCIÓN) — `.\set_alta_sigrid.ps1`, `.\deploy.ps1 -Only sv9`, `.\deploy.ps1 -Only sv4`, `az containerapp logs show -n ca-sv9-alta-sigrid -g $RG --tail 200 | Select-String "Entradas|empleado_no_resuelto"`
- [ ] T17: Tras la primera alta real de un aprobador de la Lista, comprobar en solo lectura que `dca.empide` del AC nuevo es el de su Entrada y que el panel lo enseña  |  Verificación: MANUAL (líder o humano, solo lectura) — `sql/read` `SELECT c.cod, d.empide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.ide = <sigrid_con_ide>`
- [ ] T18: Ejecutar `bash harness/init.sh` en verde  |  Verificación: `bash harness/init.sh`
