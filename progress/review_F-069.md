Revisión completa (pasada 1), `dev` (`6601a92`)..`d84f27a`
<!-- progress/review_F-069.md -->
# Review F-069 · Usuario y empleado de Sigrid de quien aprueba

**Veredicto: CHANGES_REQUESTED** (RECHAZADO con 3 condiciones). Reviewer, 2026-10-24. El código
cumple la spec v3; falta cerrar la mutación `critico` (un «equivalente» que no lo es) y `servicios`.

**Nivel de rigor:** `critico`, declarado en `harness/features.json`. Exige fase RED, cobertura
≥ 80 % de lo cambiado, mutación con 0 supervivientes salvo justificación aceptada por el humano,
RM5 y verificaciones MANUAL con su comando exacto.

## init.sh y suites (ejecutado por el reviewer, en el worktree, sin otra suite de albaranes en marcha)

Todas las suites en verde: raíz 1883, sv1 205, sv2 485, sv3 1576, sv4 1808, sv5 96, sv6 473 + 1
skipped, sv9 959 (61 s), comun en caché verde. **PUERTA COBERTURA [OK] 99,5 %** (440/442,
umbral 80 %). Rutas sensibles N/A. Única KO: **PUERTA TAMAÑO por este mismo informe** (el
borrador, de 143 líneas, estaba en disco mientras corría init.sh). Recortado y comprobado con
`python -m harness.tamano --feature F-069`: dentro de topes (review 140/140). No es de la feature.

## Lo pedido por el líder

- **`resolucion` nunca viaja a sigrid-api: se cumple.** El cliente monta el cuerpo con
  `peticion.a_dict()` (`sigrid_api_alta_client.py:254`), nunca con `paso.peticion`, que es el
  único dict que lleva la clave (`alta_sigrid_service.py:387-389`); al retomar,
  `PeticionAlbaran.desde_dict` ignora la clave. Lo fijan `test_f069_r17_*` con `httpx.MockTransport`
  sobre el cliente real (previa, grabación y retoma: `b"resolucion" not in peticion.content`).
- **Datos personales y secretos: limpio en lo que añade la rama.** Barrido de las líneas añadidas
  (`git diff dev...HEAD`): correos (`[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}`) solo ficticios
  (`login1..5@ruesma.es`, `a@`, `b@`, `otro@`, `login1@gmail.com`, variantes de mayúsculas);
  GUID, IP, `password=`, `secret=`, `api_key`, `AccountKey`, `sig=`, `code=`: solo los marcadores
  `<contraseña>` del informe y la lectura de `PG_PASSWORD` del entorno en el script. En
  `progress/` (impl, mutación, propuestas, current) solo Logins e `ide`. Observación ajena a la
  rama: la `description` de F-069 en `features.json` (ya en `dev`) trae un nombre completo y
  logins de terceros; no lo añade esta feature.
- **`ALTA_SIGRID_COMMIT`: ningún script de infra lo toca en el diff** (ninguna línea `+`/`-` lo
  nombra en `infra/`). `set_alta_sigrid.ps1` sigue abortando si un par lo nombra y solo lo lee;
  `create_capps_sv9.ps1` conserva su `ALTA_SIGRID_COMMIT=false` de creación (F-053, sin cambios).
- **Los 2 «equivalentes»**: ver «Mutación». El 1 se sostiene (reproducido); el 2 **no**.

## Mutación (`progress/mutacion_F-069.md`)

- **Recálculo independiente** (`harness.alcance.alcance_de_feature` + `generar_mutantes`, puro):
  11 ficheros, **1002 líneas, 148 mutantes**: coincide. Los dos supervivientes existen con el
  mismo operador y texto (`:46 [entero]` y `:306 [booleano]`).
- **Campaña no reejecutada: 2510 s (42 min) según el informe** (> 60 s): recálculo puro + RM1–RM6.
- **RM1** SHA medido `8d21097`; de ahí a HEAD solo cambian `BACKLOG.md`, `progress/` y `tasks.md`:
  ningún fichero del alcance. Válido. **RM2** 4 workers; media 17,0 s × 4 = 68 s por mutante,
  frente a líneas base de 68 s (sv9) y 198 s (sv4) con `-x`: coherente; 148 × 17,0 ≈ 2510 s.
  Coste por mutante 2510 × 4 / 148 = 67,8 s (> 1 s). Sin cabecera «NO VÁLIDA», sin veredicto 0.
- **RM3** repasados los 148: ningún equivalente muerto (los `frozen=False` de `alta_models.py`
  los mata `test_f053_t25_los_modelos_son_inmutables`; el de `Equivalencia`, su test de R1).
- **RM5 (muestra de UNO: el superviviente 1)** — el informe no trae demostración ejecutable de
  ninguno de los dos (solo texto). La he hecho yo sobre dos copias en el scratchpad (original y
  mutante `insert(1, …)`), lanzando el script como `__main__` con `sys.path[0]` = `scripts/`:
  en las dos `domain`, `domain.services.usuario_sigrid` e
  `infrastructure.sigrid.sigrid_api_alta_client` resuelven a la copia de sv9 y `httpx`, `psycopg`
  y `tenacity` a site-packages; `--help` sale 0. **Equivalente: se sostiene.**
- **Superviviente 2 (`zip(..., strict=False)` → `strict=True`, `medir_empleados_f069.py:306`):
  NO es equivalente.** Cambia el comportamiento observable con una fila de `rows` más corta que
  `columns`: con `strict=False` el dict sale sin `fecbaj`, `empleados_de_filas` hace
  `f.get("fecbaj") or 0` y el empleado cuenta **de alta en silencio** (medición falsa sin aviso);
  con `strict=True` el script aborta. «Equivalente bajo el contrato» es una suposición sobre
  sigrid-api, no una equivalencia, y un test de una línea lo decide. Ver condición 1.
- **RM6** N/A justificado: ningún mutante se mató quitando una guarda (los nueve de la 1.ª
  campaña se cerraron con tests nuevos, `test_f069_t15_supervivientes.py`, sin tocar código).

## Checkpoints

**C1** [x] init.sh exit 0 (arriba) · [x] ficheros del arnés presentes.
**C2** [x] una sola `in_progress` (F-069) · [x] rama `feature/F-069-usuario-empleado-sigrid` ·
[x] `current.md` describe la sesión activa (F-069 arriba; el resto son estados vigentes) ·
[x] F-084 `done` con su resumen en `history.md`.
**C3** [x] hexagonal: dominio puro (`usuario_sigrid.py` solo importa `alta_models`), lecturas en
el puerto y el cliente, `resolucion` armada en application; el script vive fuera de la hexagonal
como dice design §6 · [x] primera línea con ruta en todos los ficheros nuevos y tocados (el
`scripts/__init__.py` vacío, como los otros 44 `__init__.py` vacíos del monorepo) · [x] sin
`print` de debug (los del script son su salida, permitidos por design §6), sin TODO, sin
secretos, sin dependencias nuevas (`psycopg`, `httpx`, `tenacity` ya estaban) · [x] reglas de
`ARCHITECTURE.md`: sin DDL, Sigrid solo por `sql/read`, comun intacto; las tres trampas N/A
justificadas (no toca merge/raw, ni schema, ni importes).
**C3 bis** N/A: la rama no toca `docs/referencia/`.
**C4** [x] cada requisito con test (tabla abajo), todos en verde · [x] sin red ni BBDD
(`SigridFalso`, `httpx.MockTransport`, conexión PG falsa; el subproceso del script usa
`sigrid.invalid`) · [x] MANUAL listadas en `current.md` (T5, T16, T17) con el comando exacto para
PowerShell en `progress/impl_F-069.md`, al que remite.
**C4 bis** [x] rigor declarado · [x] fase RED con trazas reales de T1–T4 y T6–T15 · [x] cobertura
(ver init) · [x] mutación con totales verificados · [x] campaña > 60 s: recálculo puro, dicho
arriba · [x] coste por mutante 67,8 s · [x] sin «NO VÁLIDA» ni base rota · [x] RM1 · [x] RM2 ·
**[ ] RM5**: los equivalentes no traen demostración ejecutable; el 2 ni siquiera es equivalente ·
[x] RM6 N/A justificado · N/A campaña manual (la automática dio 148) ·
**[ ] supervivientes**: en `critico` hacen falta 0 o justificación aceptada; la del 2 no se
sostiene · [x] «Evidencias» con los cuatro números y los workers (4).
**C4 ter** N/A: la puerta de rutas sensibles de init.sh no señala rutas tocadas (prompts, schemas
IA, clientes LLM y redes de sv6 fuera del diff).
**C5** [x] `tasks.md`: T1–T4, T6–T15 y T18 `[x]` con su commit `F-069 Tn:`; T5, T16 y T17 son
MANUAL de líder/humano (T16–T17 tras APPROVED), listadas con su comando · [x] árbol limpio ·
**[ ] `features.json`**: `servicios` solo dice `sv9-alta-sigrid` y la feature toca también
`sv4-front` (panel) e `infra`. Lo avisan el spec-author y el implementer; es del líder.

## Cobertura requisito → test

| Req. | Tests (`services/albaranes-alta-sigrid/tests/` salvo sv4) |
|---|---|
| R1–R2 | `test_f069_lista.py` (13 y 11 casos: cada motivo de R2, bool/texto/decimal/0), `test_f069_config.py` |
| R3–R4 | `test_f069_config.py`, `test_f069_worker.py`, `test_f053_worker.py` (EMPIDE ignorada) |
| R5–R8 | `test_f069_servicio_usu.py` (orden de escalones, aviso, respaldo, R48 sin leer `dbo.emp`) |
| R9–R14 | `test_f069_servicio_empide.py`, `test_f069_clasificar.py`, `test_f069_cliente.py` (SQL, `max_rows`, reintentos) |
| R15–R18, R20 | `test_f069_peticion.py` (incluye R17 con `MockTransport` y R18 sin correo en el log) |
| R19 | `test_f069_worker.py` (2141 s, 2460 s) |
| R21–R24 | `services/albaranes-front/tests/test_f069_panel.py` (contraste de constantes con sv9) |
| R25–R27 | `test_f069_script.py` (`test_f069_script_rN_*`), `test_f069_t15_supervivientes.py` |
| R28 | `test_f069_infra.py` (10 tests de texto sobre los `.ps1`) |
| R29 | revisión: `sv9.md`, regla 19 de `ARCHITECTURE.md`, `.env.example` y `azure-apps` `3119ae3` (§10, local) al día |

## Cambios requeridos

1. **Superviviente 2** (`services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py:306`):
   matarlo con un test. Recomendado: `strict=True` y que `LectorSigrid.leer` convierta el
   `ValueError` en `RuntimeError("sql/read: fila desparejada…")`, como ya hace con `truncated`
   (una medición que decide E5 debe fallar alto, no clasificar «de alta» en silencio); test en
   `test_f069_script.py` con una fila más corta que `columns`. Si el humano prefiere mantener
   `strict=False`, el test fija ese comportamiento igualmente.
2. **Repetir la campaña** con la herramienta (`python -m harness.mutacion --feature F-069`) sobre
   el HEAD nuevo y añadir al análisis del superviviente 1 su **demostración ejecutable** (RM5):
   por ejemplo, la de este informe (lanzar el script con `--help` desde una copia original y otra
   mutada e imprimir `sys.modules[m].__file__` de `domain`, `infrastructure.*`, `httpx`). Sigue
   pendiente de que el humano acepte esa justificación.
3. **Líder**: `servicios` de F-069 en `harness/features.json` con `sv4-front` e `infra` además de
   `sv9-alta-sigrid` (regla LÍMITE DE SERVICIO: toda feature declara lo que toca).

## Observaciones (no bloquean)

- `create_capps_sv9.ps1` y `set_alta_sigrid.ps1` comparan la Lista releída con `-ne`, que en
  PowerShell no distingue mayúsculas; `-cne` sería exacto. La Lista se valida además al arrancar.
- El cliente de sv9 (`sigrid_api_alta_client.py:208`, F-053, fuera del diff) tiene el mismo
  `zip(strict=False)`: con una fila desparejada, `empleado_de_alta`/`empleados_de_filas` darían
  «de alta». Candidato a una mejora aparte.
- `ruff` en los ficheros nuevos: 11 `I001` y 5 `RUF100`, autocorregibles (deuda previa: 1382).
- **Automejora** (propuesta, no aplicada): RM5 de `CHECKPOINTS.md` podría decir que «equivalente
  bajo el contrato de un tercero» no es equivalente, sino un comportamiento sin test.
