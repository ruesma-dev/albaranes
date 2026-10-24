# impl F-069 · Usuario y empleado de Sigrid de quien aprueba (sv9, sv4, infra)

> Implementer, 2026-10-24. Rama `feature/F-069-usuario-empleado-sigrid` (worktree
> `../albaranes-F-069`), spec v3 (PARADA 1 cerrada el 2026-10-23), rigor `critico`.
> Un commit por tarea (`git log --oneline dev..HEAD`; T15 en dos: `8d21097` y `254ea38`).
> En `azure-apps`: `3119ae3` (local, sin push). Hechas T1–T15 y T18 (T5 por el líder);
> MANUAL pendientes: T16, T17. Review 1 (CHANGES_REQUESTED, 3 condiciones) aplicada en `33c6d6c`.

## Qué cambió

**sv9 (`services/albaranes-alta-sigrid`)**
- `domain/services/usuario_sigrid.py`: `correo_ruesma` (el Correo de Ruesma, base del
  Login), `leer_equivalencias` (la Lista; cada caso de R2 es un `ValueError` con la
  clave culpable y nunca su valor), `entrada_de`, los 8 códigos `AVISO_*` y
  `clasificar_empleados_correo` (único de alta / ambiguo / de baja / sin empleado).
- `domain/models/alta_models.py`: `EmpleadoSigrid`, `AvisoResolucion`, `OrigenUsuario`,
  `OrigenEmpleado`, `Resolucion` y `CLAVE_RESOLUCION = "resolucion"`.
- Puerto + cliente: `empleado_de_alta(ide)` y `buscar_empleados_por_correo(correo)`
  (`sql/read`, `TOP (1)`/`TOP (3)` con `max_rows` 2/3: nunca `truncated`; `traele` con
  `CAST` porque es `text`). El doble `SigridFalso` las imita.
- `config/settings.py`: `ALTA_SIGRID_EQUIVALENCIAS_USUARIO` (mal formada = no arranca);
  fuera `ALTA_SIGRID_EMPIDE` (si sigue en el entorno, se ignora: `extra="ignore"`).
- `application/alta_sigrid_service.py`: `_resolver_usuario` (Entrada → Login → Respaldo;
  lectura caída o Respaldo vacío = `usuario_no_resuelto`) y `_resolver_empleado`
  (Entrada de alta → único del correo → nulo; **nunca lanza ni bloquea**), en ese orden
  y antes de validar; `resolucion` guardada en `peticion_json` junto al cuerpo, en el
  log (R18) y conservada al retomar un `incierto` (sin inventar una si no la había).
  A sigrid-api sigue yendo solo `PeticionAlbaran.a_dict()`.
- `domain/services/validador_alta.py`: `ConfigAlta` solo con `mapeo`;
  `validar_y_construir(..., *, empide=None)`.
- `main_worker.py`: log de arranque con el nº de Entradas; peor caso + 4 lecturas
  (2141 s; visibilidad 2460 s con los defectos).
- `scripts/medir_empleados_f069.py` (T4): medición de **solo lectura** (solo `SELECT`,
  PG con `read_only = True`), CSV `;` con BOM y resumen sin correos ni nombres.
- `.env.example` y `sv9.md` al día.
**sv4 (`services/albaranes-front`)**: `AltaSigridVista.empide`, `avisos_resolucion` y
`usu_respaldo` desde `resolucion.usu`; textos `TEXTOS_AVISO_RESOLUCION` y el nuevo de
`usuario_no_resuelto`; `_alta_sigrid.html` con «Empleado de Sigrid» y la lista de
avisos (estilo de aviso, nunca de error ni bloqueo).

**infra**: `00_capps_vars.ps1` (Lista vacía con su comentario, `EscaparJsonNativo`
compartida con el mapeo, fuera `ALTA_SIGRID_EMPIDE`); `create_capps_sv9.ps1` y
`set_alta_sigrid.ps1` pasan la Lista solo a sv9, escapada, y la releen. Ninguno toca
`ALTA_SIGRID_COMMIT`. BOM y CRLF de cada script, como estaban (`00_capps_vars.ps1`
sigue sin BOM, como antes).

**docs**: regla 19 de `docs/ARCHITECTURE.md`, §10 de `azure-apps/albaranes.md` y
`progress/propuestas_a_sigrid_api_F-069.md` (design §10; las revisa el humano) y la fila de
F-069 en `progress/inventario_mutacion_F-039.md` (la exige `test_f039_r2`).

## Decisiones de diseño y desviaciones

- **Numeración**: el mensaje del líder llama T2 a la medición y T13 a azure-apps; en
  `tasks.md` son **T5** y **T14**. Sigo `tasks.md`.
- **Desviación transitoria (T6→T9)**: entre T6 y T9 `composition.py` pasaba
  `ConfigAlta(empide=None)`; T9 quitó el campo. No queda nada de eso.
- Los Avisos de resolución viven solo en `peticion_json.resolucion`: el cliente sigue
  mandando `PeticionAlbaran.a_dict()` (contrato `extra="forbid"`), y hay test de que
  ni la previa, ni la grabación, ni el retomar llevan la clave.
- `_resolver_empleado` atrapa cualquier excepción de lectura y la deja como
  `empleado_lectura_fallida` con solo el nombre del tipo (nada del mensaje, que podría
  llevar datos).
- Script: `difiere` solo es cierto si el empleado que correspondería no es nulo y es
  distinto del escrito (con nulo, sigrid-api pondría el mismo defecto). Las
  credenciales salen solo del entorno de la consola, nunca de un `.env`.
- `ALTA_SIGRID_EMPIDE` se queda en la Container App y sv9 la ignora:
  `--remove-env-vars` no está en la spec (opcional, lo decide el humano).
- **Review 1** (`progress/review_F-069.md`): (1) el script ya no usa `zip(strict=False)`:
  una fila desparejada con `columns` es `RuntimeError` («fila desparejada»), como
  `truncated`, porque sin `fecbaj` el empleado contaba «de alta» en silencio; (2) campaña
  repetida y demostración ejecutable (RM5) del equivalente que queda; (3) `servicios` de
  F-069 en `features.json`: `sv9-alta-sigrid`, `sv4-front` e `infra` (encargo del líder).

## Fuera del alcance

- Nada contra producción, ni escrituras en Sigrid o en la BBDD de Azure; no he tocado
  `ALTA_SIGRID_COMMIT` ni el repositorio de sigrid-api; F-103 sin tocar.
- Corregir las altas ya escritas con el empleado por defecto (E5): lo decide el
  humano con el resultado de T5, junto con F-103.

## Tareas MANUAL

**T5 · HECHA por el líder** (solo lectura, 2026-10-24): `progress/medicion_F-069.md`
(comprobado: sin correos completos, ni una «@»). 7 aprobadores: 5 con empleado único, 1 sin
empleado, 1 sin correo de Ruesma; 68 altas escritas, 65 con un empleado distinto del que les
correspondería (E5: lo decide el humano, junto con F-103).

**T16 · despliegue (humano, ESCRIBE EN PRODUCCIÓN, tras APPROVED y fusión en `dev`).**
Desde `infra\`:
```powershell
. .\00_vars.ps1; . .\00_capps_vars.ps1
.\set_alta_sigrid.ps1          # pone la Lista (vacía) en sv9 y la relee
.\deploy.ps1 -Only sv9
.\deploy.ps1 -Only sv4
az containerapp revision list -n ca-sv9-alta-sigrid -g $RG -o table
az containerapp logs show -n ca-sv9-alta-sigrid -g $RG --tail 200 | Select-String "Entradas|empide"
```

**T17 · comprobación real (solo lectura).** Tras la primera alta real de un aprobador,
`sql/read` de sigrid-api con
`SELECT c.cod, d.empide FROM dbo.con c JOIN dbo.dca d ON d.ide = c.ide WHERE c.ide = <sigrid_con_ide>`:
`empide` debe ser el de su Entrada o el de su correo; y el panel debe enseñar
«Empleado de Sigrid» y los avisos.

## Fase RED (trazas reales)

sv9 con el `.venv` de la raíz, desde `services/albaranes-alta-sigrid`. Comando exacto y
líneas del fallo, de la salida real; tras el código, el mismo comando en verde.

T1 (R1, R2) · `python -m pytest tests -q -k "f069_r1 or f069_r2 or f053_r47_candidato"`
```
E   ImportError: cannot import name 'Equivalencia' from 'domain.services.usuario_sigrid'
654 deselected, 1 error in 4.60s
```
T2 (R11) · `python -m pytest tests -q -k "f069_r11_clasificar"`
```
E   ImportError: cannot import name 'AvisoResolucion' from 'domain.models.alta_models'
755 deselected, 1 error in 4.40s
```
T3 (R9, R10, R13) · `python -m pytest tests -q -k "f069_cliente or f053_cliente"`
```
E   ImportError: cannot import name 'SQL_EMPLEADO_DE_ALTA' from 'infrastructure.sigrid.sigrid_api_alta_client'
737 deselected, 1 error in 3.22s
```
T4 (R25–R27) · `python -m pytest tests -q -k f069_script`
```
E   ImportError: cannot import name 'medir_empleados_f069' from 'scripts' (...\services\albaranes-alta-sigrid\scripts\__init__.py)
799 deselected, 1 error in 3.54s
```
T6 (R1–R4) · `python -m pytest tests -q -k "f069_r2_config or f069_r3 or f069_r4 or f069_r1_config" --tb=line`
```
E   AttributeError: 'Settings' object has no attribute 'equivalencias'
E   Failed: DID NOT RAISE ValidationError            (test_f069_config.py:65, los 5 casos de R2)
FAILED tests/test_f069_config.py::test_f069_r4_ningun_codigo_de_sv9_lo_nombra
FAILED tests/test_f069_config.py::test_f069_r4_env_example_sin_empide_y_con_la_lista
17 failed, 846 deselected in 18.30s
```
T7 (R5–R8; `OrigenUsuario` ya creado, para ver el fallo de comportamiento) ·
`python -m pytest tests -q -k "f069_r5 or f069_r6 or f069_r7 or f069_r8" --tb=line`
```
19 E   TypeError: AltaSigridService.__init__() got an unexpected keyword argument 'equivalencias'
19 failed, 1 passed, 863 deselected in 3.07s
```
T8 (R9–R14; `OrigenEmpleado` ya creado) ·
`python -m pytest tests -q -k "f069_r9 or f069_r10 or f069_r11 or f069_r12 or f069_r13 or f069_r14" --tb=line`
```
19 E   AttributeError: 'AltaSigridService' object has no attribute '_resolver_empleado'
 2 E   AssertionError: assert ['buscar_usuario'] == ['buscar_usuario', 'empleado_de_alta']   (R14)
21 failed, 23 passed, 870 deselected in 3.08s
```
(Los 23 en verde: los de T2 y los de R13 que el flujo de antes ya cumplía, sin lectura de `dbo.emp`.)

T9 · `python -m pytest tests -q -k "f069_r10_el_empide or f069_r9_validar or f069_r1_config_la_lista" --tb=line`
```
E   AssertionError: assert {} == {'login1': Eq...pide=1234567)}          (composition no pasa la Lista)
E   assert [None, None] == [1234567, 1234567]                            (Entrada de alta: no se manda)
E   assert [None, None] == [1000001, 1000001]                            (único del correo: no se manda)
4 failed, 2 passed, 914 deselected in 3.64s
```
T10 (R15–R18, R20; `Resolucion` ya creado) ·
`python -m pytest tests -q -k "f069_r15 or f069_r16 or f069_r17 or f069_r18 or f069_r20" --tb=line`
```
3 E   KeyError: 'resolucion'
1 E   AssertionError: assert 'resolucion' in {'cod_obra': '0404', 'cif_proveedor': 'B00000000', ...
1 E   AssertionError: assert {'cod_obra': ...} == {'cod_obra': ...}      (R15: al retomar se pierde la resolucion)
6 failed, 7 passed, 921 deselected in 3.22s
```
T11 (R19) · `python -m pytest tests -q -k "f069_r19" --tb=line`
```
E   AssertionError: assert 1409.0 == 2141
E   AssertionError: assert 1740 == 2460
E   AssertionError: assert 1508.0 == 2372
3 failed, 934 deselected in 4.63s
```
T12 (R21–R24, sv4) · `cd services/albaranes-front && .venv/Scripts/python.exe -m pytest tests -q -k "f069 or f077_motivos" --tb=line`
```
9 E   AttributeError: 'AltaSigridVista' object has no attribute 'avisos_resolucion'
6 E   AttributeError: 'AltaSigridVista' object has no attribute 'empide'
1 E   AttributeError: module 'domain.models.alta_sigrid_models' has no attribute 'TEXTOS_AVISO_RESOLUCION'
2 E   AssertionError: assert True is False          (R23: la Lista salía como respaldo)
1 E   assert None == 'Empleado de Sigrid: <code>1000001</code>'
26 failed, 33 passed, 1749 deselected, 1 warning in 14.61s
```
T13 (R28, infra) · `python -m pytest tests -q -k "f069_r28" --tb=line`
```
E   ValueError: not enough values to unpack (expected 1, got 0)
E   assert 'ALTA_SIGRID_EMPIDE' not in '# 00_capps_... Yellow\n}\n'
E   assert '"ALTA_SIGRID_EQUIVALENCIAS_USUARIO=$(EscaparJsonNativo $Global:ALTA_SIGRID_EQUIVALENCIAS_USUARIO)"' in '...'
E   assert 'ALTA_SIGRID_EQUIVALENCIAS_USUARIO' in '$soloSv9 = @("ALTA_SIGRID_USUARIO_RESPALDO=...'
7 failed, 8 passed, 937 deselected in 3.55s
```
T15 · cada test nuevo, contra su mutante aplicado a mano (y el fichero restaurado):
`python -m pytest tests/test_f069_t15_supervivientes.py -q` → con cada uno de los 8
primeros mutantes `1 failed, 5 passed`; con el de la espera (test añadido después),
`1 failed, 6 passed`.

Review 1 · `python -m pytest tests -q -k "f069_script_fila_desparejada" --tb=line`
```
...	ests	est_f069_script.py:285: Failed: DID NOT RAISE RuntimeError
FAILED tests/test_f069_script.py::test_f069_script_fila_desparejada_es_fallo[fila0]
FAILED tests/test_f069_script.py::test_f069_script_fila_desparejada_es_fallo[fila1]
2 failed, 959 deselected in 2.29s
```
Con el código: `2 passed`; con `strict=False` restaurado a mano, otra vez `2 failed`.

## Evidencias

| Evidencia | Valor real |
|---|---|
| Tests sv9 | 961 passed en 28,55 s (`python -m pytest tests -q`, tras la review 1) |
| Tests sv4 | 1808 passed (sin cambios en sv4 desde T12) |
| `bash harness/init.sh` | **verde** («ENTORNO LISTO», exit 0, tras la review 1): raíz 1883 passed (363,52 s), sv1 205, sv2 485, sv3 1576, sv4 1808 (174,63 s), sv5 96, sv6 473 + 1 skipped, sv9 961 (37,98 s), comun verde |
| Cobertura de las líneas cambiadas | **99,6 %** de 445 (443/445, umbral 80 %, nivel `critico`): `PUERTA COBERTURA` de `init.sh` |
| Mutación | 1.ª (`8ede6ca`): 148, 137 muertos, 11 supervivientes. 2.ª (`8d21097`): 148, 146, 2. **3.ª (`33c6d6c`): 148 generados, 147 muertos, 1 superviviente**, 0 timeouts, 2047,7 s, 4 workers. Detalle: `progress/mutacion_F-069.md` |
| Supervivientes | 1 **equivalente** (`sys.path.insert(1, …)` del script), con demostración ejecutable (RM5) en el informe; **pendiente de que el humano acepte la justificación** (rigor `critico`, máximo 0) |

Pendiente para cerrar: APPROVED del reviewer, aceptación humana del equivalente y, tras
fusionar, T16 y T17.
