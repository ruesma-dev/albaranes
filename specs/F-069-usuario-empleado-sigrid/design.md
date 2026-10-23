<!-- specs/F-069-usuario-empleado-sigrid/design.md -->
# F-069 · Usuario y empleado de Sigrid de quien aprueba · Diseño (v2)

Requisitos: `requirements.md`. Base: F-053 v8 (`specs/F-053-alta-sigrid/`). Contrato de sigrid-api:
`sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md` (fila `empide`: `int | null`, ≥ 1, opcional;
nulo ⇒ `SIGRID_ALBARAN_EMPIDE`). Se enlaza, no se copia. **v2** tras la PARADA 1 (2026-10-23): E1 y E3 los decide el
humano; queda abierta **E8** (§9).

## 1. Encaje y límite de servicio

Ninguna responsabilidad nueva: sv9 ya decide la identidad del alta (`usu`, F-053 R47) en un único punto
(`AltaSigridService._resolver_usuario`, cuyo docstring ya reserva el sitio a F-069). Esta feature amplía ese punto
para que dé también el `empide` y añade una lista de excepciones en su configuración. sv4 solo cambia el panel del
alta (lee lo que sv9 guarda). Sin cambios en `ruesma_comun` (solo lo usa sv9) ⇒ solo se reconstruyen sv9 y sv4. Sin
DDL. Sin cambios en sigrid-api: el contrato ya admite `empide`. Sigrid se sigue leyendo solo por `sql/read`.

## 2. Resolución (petición nueva; un `incierto` retomado no resuelve nada, R15)

**`usu`** (escalones; el primero que da valor gana):
1. Login contra `dbo.usu` (R47 de F-053) → Origen `correo`.
2. Entrada con `usu` contra `dbo.usu` → Origen `lista`. Si no existe: Aviso `usuario_lista_no_existe` y sigue.
3. Respaldo → Origen `respaldo`. Vacío, o lectura de `dbo.usu` caída: `error` `usuario_no_resuelto` (R7, como hoy).

**`empide`** (nunca bloquea, R13):
1. Con Correo de Ruesma: `buscar_empleados_por_correo(correo)` → `clasificar_empleados_correo(filas)`:
   uno de alta ⇒ Origen `correo`; dos o más de alta ⇒ `empleado_correo_ambiguo`; solo de baja ⇒
   `empleado_correo_de_baja`; ninguno ⇒ `empleado_correo_sin_empleado`. Sin Correo: `empleado_sin_correo`.
2. Entrada con `empide`: `empleado_de_alta(ide)` ⇒ Origen `lista`; si no, `empleado_lista_no_valido`.
3. Empleado por defecto (`ALTA_SIGRID_EMPIDE`) ⇒ Origen `defecto`; vacía ⇒ nulo, `defecto_sigrid_api` **[E8]**.

Cualquier lectura de `dbo.emp` que falle tras los reintentos deja `empleado_lectura_fallida` y pasa al escalón
siguiente. El escalón 1 de `empide` no depende del Origen del usuario: con `usu` = Respaldo (quien aprobó no tiene
login), el empleado sigue siendo el de su correo. Orden global: `usu` → `empide` → validación local → altas a mano →
previa (R14). Avisos posibles por alta: hasta tres (uno de `usu`, dos de `empide`).

## 3. Ficheros a crear

- `services/albaranes-alta-sigrid/scripts/__init__.py` (vacío) y `scripts/medir_empleados_f069.py` (R25–R27, §7).
- `services/albaranes-alta-sigrid/tests/test_f069_*.py`: un fichero por bloque (`lista`, `config`, `cliente`,
  `clasificar`, `servicio_usu`, `servicio_empide`, `peticion`, `worker`, `script`, `infra`). Nombres `test_f069_rN_...`.
- `services/albaranes-front/tests/test_f069_panel.py` (R21–R24).
- `progress/propuestas_a_sigrid_api_F-069.md`: petición de coordinación (§10), como la de F-053.

## 4. Ficheros a modificar

**sv9** (`services/albaranes-alta-sigrid/`):
- `domain/services/usuario_sigrid.py`: `correo_ruesma`, `Equivalencia`, `leer_equivalencias`, `entrada_de`,
  `clasificar_empleados_correo` y los códigos `AVISO_*` (§6). Puro. `candidato_usuario` pasa a apoyarse en
  `correo_ruesma` sin cambiar su resultado (los tests de F-053 R47 lo vigilan).
- `domain/models/alta_models.py`: `EmpleadoSigrid`, `OrigenUsuario`, `OrigenEmpleado`, `AvisoResolucion`,
  `Resolucion`; `CLAVE_RESOLUCION = "resolucion"`. `PeticionAlbaran` NO cambia (`a_dict` sigue siendo el cuerpo
  exacto que se manda; `desde_dict` ya ignora claves que no conoce ⇒ R17 al retomar).
- `domain/ports/sigrid_alta_port.py`: `buscar_empleados_por_correo(correo: str) -> list[EmpleadoSigrid]` y
  `empleado_de_alta(ide: int) -> bool` (ambos lanzan si la lectura falla tras los reintentos). El docstring pasa de
  «cinco» a «siete operaciones»; si algún test fija el número, se ajusta.
- `infrastructure/sigrid/sigrid_api_alta_client.py`: `SQL_EMPLEADOS_POR_CORREO`, `SQL_EMPLEADO_DE_ALTA` (§7) y los
  dos métodos (`_leer`, etiquetas `f069-empleado-correo` y `f069-empleado-lista`, `max_rows` 3 y 2).
- `domain/services/validador_alta.py`: `ConfigAlta` pierde `empide`; `validar_y_construir(datos, config, hoy, usu, *,
  empide: int | None = None)`. El servicio lo pasa siempre (lo prueban R8–R12); los ~25 tests que llaman sin él siguen.
- `application/alta_sigrid_service.py`: constructor con `equivalencias: Mapping[str, Equivalencia]` y
  `empide_defecto: int | None`; `_resolver_usuario` devuelve `(usu, origen, avisos)`; nuevo `_resolver_empleado`
  (no lanza nunca: traduce cada excepción de lectura en `empleado_lectura_fallida`); `_flujo` guarda `resolucion`
  (R16) y la conserva al retomar (`{**peticion.a_dict(), "resolucion": previa.peticion["resolucion"]}` si estaba);
  log de R18 con el Login, nunca el correo.
- `config/settings.py`: `alta_sigrid_equivalencias_usuario: str = Field("", alias="ALTA_SIGRID_EQUIVALENCIAS_USUARIO")`
  con `field_validator` que llama a `leer_equivalencias` (R2; el `ValueError` lleva el motivo al log como R44);
  propiedades `equivalencias` y `empide_defecto` (renombra `empide`; la variable sigue siendo `ALTA_SIGRID_EMPIDE`).
  Docstring: `ALTA_SIGRID_EMPIDE` = último escalón, ya no el empleado de todas las altas.
- `interface_adapters/composition.py`: pasa `equivalencias` y `empide_defecto`; `ConfigAlta(mapeo=...)`.
- `main_worker.py`: log informativo de arranque (R3; sin `warning` por Lista vacía); `peor_caso_mensaje_s` suma cuatro
  `_con_reintentos_s` más (dos de `dbo.usu`, dos de `dbo.emp`, R19; hoy ya faltaba la de `dbo.usu`).
- `tests/f053_fakes.py`: `SigridFalso.empleados_por_correo: dict[str, list[EmpleadoSigrid]]`,
  `empleados_de_alta: set[int]`, los dos métodos registrados en `llamadas` y con `fallar_en`. Los 4 sitios que
  construyen `ConfigAlta(empide=...)` (`composition.py`, `f053_datos.py`, `test_f053_r47_servicio.py:138`,
  `test_f053_validador.py:251`): sin `empide`; el último pasa a probar `empide=` como argumento.
- `.env.example`, `sv9.md` (sección «Usuario de Sigrid» → «Usuario y empleado de Sigrid»; tabla de variables).

**sv4** (`services/albaranes-front/`):
- `domain/models/alta_sigrid_models.py`: `computed_field` `empide` (de `peticion["empide"]`, entero o `None`),
  `empide_por_defecto` (Origen `defecto`/`defecto_sigrid_api`), `avisos_resolucion` (lista de `(codigo, texto)` con
  `TEXTOS_AVISO_RESOLUCION`; código desconocido ⇒ el código); `usu_respaldo` lee `resolucion.usu` si existe y si no
  la regla de hoy (R23); texto nuevo de `usuario_no_resuelto` (R24). `"resolucion"` y los códigos se repiten aquí
  (sv4 no importa sv9); un test los contrasta con la fuente de sv9, como `TEXTOS_MOTIVO_ALTA` en F-077.
- `templates/_alta_sigrid.html`: «Empleado de Sigrid» junto al usuario (R21) y los avisos con el estilo de aviso del
  panel, nunca el de error ni el de bloqueo (R22).

**infra y documentación**:
- `infra/00_capps_vars.ps1`: `$Global:ALTA_SIGRID_EQUIVALENCIAS_USUARIO = ""` (vacía; JSON en comillas simples de
  PowerShell cuando haga falta), `$Global:ALTA_SIGRID_EMPIDE` según E8 y una función `EscaparJsonNativo` que
  reutilizan el mapeo y la Lista (la lógica de hoy de `AltaSigridEnvComun`, sin cambiar su resultado). Comentario:
  claves = Login; ni correos completos, ni nombres, ni DNI.
- `infra/create_capps_sv9.ps1` y `infra/set_alta_sigrid.ps1`: la Lista en los pares solo de sv9, escapada, y releída
  (`set_alta_sigrid.ps1` ya relee: se añade al bucle). Lista vacía: el par se pasa vacío (`env_ignore_empty`).
- `docs/ARCHITECTURE.md` regla 19, viñeta «Usuario de Sigrid» → «Usuario y empleado de Sigrid».
- `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` §10: la resolución, la variable nueva, el `empide` que se
  manda, la lectura de `dbo.emp` en lo que consume. Commit local en `azure-apps` (regla de mantenimiento).

## 5. Ficheros que NO se tocan

- `ruesma_comun` (ni `alta_sigrid.py` ni `colas/mensajes.py`: `approved_by` ya viaja y se guarda).
- El DDL de `albaran_altas_sigrid` (sv3): `resolucion` va dentro de `peticion_json`, que ya es JSON.
- `PeticionAlbaran.a_dict`/`desde_dict` y el cuerpo que se manda: lo único nuevo es el valor de `empide`.
- `motivos_json` y `estado_de_motivos`: los Avisos de resolución no son motivos (no cambian el estado).
- sv4 al aprobar (`approved_by` de F-053 R49), sv3, sv5, sv6.
- `ALTA_SIGRID_COMMIT` (sigue en `true`; ningún script lo toca), `ALTA_SIGRID_USUARIO_RESPALDO`, DESDE.
- El repositorio de sigrid-api. Lo que haga falta de ellos va en §10.

## 6. Clases y funciones (capa)

- **domain** `usuario_sigrid.py`:
  - `correo_ruesma(approved_by: str | None) -> str | None` (glosario; minúsculas).
  - `@dataclass(frozen=True) class Equivalencia: usu: str | None; empide: int | None`.
  - `leer_equivalencias(texto: str | None) -> dict[str, Equivalencia]`: vacío ⇒ `{}`; `json.loads` con
    `object_pairs_hook` para detectar claves repetidas literales; claves `casefold()`; `ValueError` con motivo y
    clave por cada caso de R2 (`bool` es `int` en Python: se rechaza explícitamente).
  - `entrada_de(approved_by, equivalencias) -> Equivalencia | None` (por Login).
  - `clasificar_empleados_correo(empleados: list[EmpleadoSigrid]) -> tuple[int | None, AvisoResolucion | None]`:
    un único `de_alta` ⇒ `(ide, None)`; si no, `(None, aviso)` con R9–R10. La importa también el script (R25).
- **domain** `alta_models.py`: `EmpleadoSigrid(ide: int, de_alta: bool)`; `OrigenUsuario(StrEnum)`: `correo`,
  `lista`, `respaldo`; `OrigenEmpleado(StrEnum)`: `correo`, `lista`, `defecto`, `defecto_sigrid_api`;
  `AvisoResolucion(codigo: str, detalle: str)`; `Resolucion(usu, origen_usu, empide, origen_empide, avisos)` con
  `a_dict()` para `peticion_json` (sin el `usu` ni el `empide`, que ya van en el cuerpo).
- **application** `AltaSigridService._resolver_usuario` (R4–R7; lanza `UsuarioNoResuelto` solo en R7),
  `_resolver_empleado(approved_by) -> tuple[int | None, OrigenEmpleado, list[AvisoResolucion]]` (R8–R13).
- **infrastructure** `SigridApiAltaClient.buscar_empleados_por_correo`, `.empleado_de_alta`.
- **script** (fuera de la hexagonal, como `medir_admisibilidad_f053.py` de sv3; `print` permitido): importa
  `correo_ruesma`, `clasificar_empleados_correo` y `SQL_EMPLEADOS_POR_CORREO` (mide lo mismo que hará sv9); funciones
  puras `resumen(medidas)`, `filas_csv(medidas, altas)` y `empide_que_corresponde(...)` (testeadas sin red); E/S en
  `main()` con `httpx` contra `sql/read` y `psycopg` contra PostgreSQL, credenciales del entorno
  (`SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY`, `PG_*`). No usa `SigridApiAltaClient` (F-053 R33).

## 7. SQL (solo lecturas; sin DDL)

sv9, por petición nueva (además de la de `dbo.usu`, que puede ir dos veces):
- `SQL_EMPLEADOS_POR_CORREO = "SELECT TOP (3) ide, ISNULL(fecbaj, 0) AS fecbaj FROM dbo.emp WHERE
  LOWER(LTRIM(RTRIM(CAST(traele AS varchar(512))))) = ? ORDER BY CASE WHEN ISNULL(fecbaj, 0) = 0 THEN 0 ELSE 1 END,
  ide"`: los de alta primero; con `TOP (3)` basta para distinguir uno, varios («3 o más» en el detalle) o solo de
  baja. El parámetro va ya en minúsculas y recortado (`correo_ruesma`). `traele` es `text`: sin `CAST` no se compara.
- `SQL_EMPLEADO_DE_ALTA = "SELECT TOP (1) ide FROM dbo.emp WHERE ide = ? AND ISNULL(fecbaj, 0) = 0"`.

Script: las dos anteriores por cada Quien aprobó; `SELECT d.ide, d.empide FROM dbo.dca d WHERE d.ide IN (?, …)`
(troceado si pasa de 500 parámetros) para R26; en PostgreSQL, `SELECT DISTINCT approved_by FROM
albaran_documents_merge WHERE approved` y `SELECT sigrid_con_ide, sigrid_cod, approved_by, peticion_json::json->>'usu'
FROM albaran_altas_sigrid WHERE estado = 'registrado' AND sigrid_con_ide IS NOT NULL`. Comprueba `truncated`.
T5 mide además el tiempo de la primera (recorre `dbo.emp` con `CAST`; el líder la ejecutó sin problema).

## 8. Configuración y despliegue (lo ejecuta el humano)

- Orden: (1) T5 en verde y E8 aplicada en `00_capps_vars.ps1`; (2) `set_alta_sigrid.ps1` pone Lista (vacía) y
  Empleado por defecto en sv9 y los relee; (3) desplegar sv9; (4) desplegar sv4 (antes o después: sin `resolucion`
  aplica la regla de hoy). Ningún orden bloquea altas: sin Lista, sv9 nuevo resuelve por correo o cae al defecto.
- Vuelta atrás: imagen anterior de sv9 (vuelve a mandar `ALTA_SIGRID_EMPIDE` a todas: con E8 = explícito, 2425207,
  igual que hoy en Sigrid). La Lista puede quedarse puesta (la imagen anterior la ignora, `extra="ignore"`).
- Cambiar la Lista después: editar `00_capps_vars.ps1` + `set_alta_sigrid.ps1` (revisión nueva, sin build).

## 9. Decisiones (PARADA 1 del 2026-10-23)

**E1 · De dónde sale el empleado — DECIDIDA (humano).** El correo del portal contra `emp.traele` de empleados de alta,
con un único resultado; si no, la Entrada de la Lista; si no, el defecto (§2). El `usu`: correo → Lista → Respaldo.
Descartadas: `codemp/tarseg` (no casa en todos), `emp.ele` (correo personal) y el `empide` de sus altas a mano.

**E2 · Dónde vive la Lista — se mantiene (a)**, ahora solo para excepciones: variable JSON de sv9 versionada en
`infra/00_capps_vars.ps1`, vacía de inicio, mantenida por el humano. Cambio respecto a v1: **la clave es el Login**,
no el correo completo, para no versionar correos de terceros; basta porque solo un Correo de Ruesma llega a ella.

**E3 · Si no se encuentra el empleado — DECIDIDA (humano): nunca se bloquea.** Se cae al defecto y queda un Aviso de
resolución en `peticion_json.resolucion`, visible en el panel como aviso (R22). No es un motivo: los motivos deciden el
estado (`revisar`, `error`) y se pintan como error. El bloqueo de F-053 R48 (sin `usu` posible) no cambia.

**E4 · Caché — ninguna** (sin cambios): Lista en memoria; `dbo.usu` y `dbo.emp`, lecturas por petición nueva
(decenas al día), como hoy `dbo.usu`; una caché escondería una baja reciente.

**E5 · Las 46 altas ya escritas con 2425207** (sin cambios): el script las lista con el empleado que les
correspondería (R26) y el humano decide: dejarlas, corregirlas a mano en Sigrid o pedirlo a sigrid-api, en ese caso
**en una sola petición junto con la limpieza de F-103** (mismas altas, misma tabla `dca`). Nada de esto va en el código.

**E6 · El panel enseña empleado y avisos — sí** (R21–R22); con E3 es además la única forma de ver que se cayó al defecto.

**E7 · Empleados de baja — DECIDIDA: no cuentan** (ni por correo ni por Lista, R10–R11).

**E8 · El defecto: explícito o nulo — ABIERTA.** (x) `ALTA_SIGRID_EMPIDE=2425207` versionado en `00_capps_vars.ps1`:
sv9 lo manda; (y) vacía: `empide` nulo y sigrid-api pone el suyo (hoy 2425207). **Recomendación: (x).** El Respaldo
`pgris` ya es configuración nuestra y su empleado debe serlo también: `peticion_json` dice con qué empleado se pidió
cada alta sin depender de `SIGRID_ALBARAN_EMPIDE` (de otro proyecto, que puede cambiar sin avisarnos) y la vuelta
atrás de §8 queda igual que hoy. Coste: si ese empleado causa baja, hay que cambiar la variable (T5 lo comprueba ahora;
`sv9.md` lo deja escrito). Con (y), R12 y R21 ya cubren el nulo.

## 10. Coordinación con sigrid-api (sin tocar su repositorio)

`progress/propuestas_a_sigrid_api_F-069.md`, para que el humano la pase a su sesión: (1) sigrid-api no comprueba que
el `empide` exista (`request.empide or settings.sigrid_albaran_empide`, `create_albaran_compra_use_case.py:844`;
modelo `ge=1`): proponer un rechazo `empleado_no_valido` como `usuario_no_valido`; mientras, sv9 solo manda empleados
leídos de alta o el defecto revisado. (2) E5, unida a la limpieza de F-103. Ninguna es requisito previo de F-069.

## 11. Riesgos

- **Un correo en varios empleados de alta** (hoy uno): cae al defecto con aviso; se arregla en Sigrid (ficha del
  empleado) o con una Entrada de la Lista. El correo gana siempre a la Lista: la Lista no puede corregir un correo que
  casa con un único empleado equivocado; eso se corrige en `emp.traele`, en Sigrid.
- **Lista mal escrita** ⇒ sv9 no arranca (R2): la revisión nueva falla y la anterior sigue sirviendo (modo single:
  comprobarlo en T16 con `az containerapp revision list`, solo lectura).
- **`resolucion` dentro de `peticion_json`**: si algo mandase ese JSON tal cual a sigrid-api, rompería
  (`extra="forbid"`). Hoy nada lo hace (se manda siempre `PeticionAlbaran.a_dict()`); R17 lo fija con tests, también
  al retomar. Descartado: columna nueva (DDL en sv3 para un dato de rastro) y `historial_json` (cambia su formato).
- **Datos personales**: en git y en progress solo Logins e `ide`; el correo completo solo viaja como parámetro a
  `sql/read` y nunca al log (R18, R27).

## 12. Relacionadas (fuera de alcance)

F-103 (facturación heredada de la plantilla, la arregla sigrid-api), F-095 (descuentos en el alta), F-053 (base).
