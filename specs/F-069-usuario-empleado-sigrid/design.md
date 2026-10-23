<!-- specs/F-069-usuario-empleado-sigrid/design.md -->
# F-069 · Usuario y empleado de Sigrid de quien aprueba · Diseño (v1)

Requisitos: `requirements.md`. Base: F-053 v8 (`specs/F-053-alta-sigrid/`). Contrato de sigrid-api:
`sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md` (fila `empide`: `int | null`, ≥ 1, opcional;
nulo ⇒ `SIGRID_ALBARAN_EMPIDE`). Se enlaza, no se copia. **Decisiones abiertas para la PARADA 1: §9.**

## 1. Encaje y límite de servicio

Ninguna responsabilidad nueva: sv9 ya decide la identidad del alta (`usu`, F-053 R47) en un único punto
(`AltaSigridService._resolver_usuario`, cuyo docstring ya reserva el sitio a F-069). Esta feature amplía ese punto
para que dé también el `empide` y añade una lista de equivalencias en su configuración. sv4 solo cambia el panel
del alta (lee lo que sv9 guarda). Sin cambios en `ruesma_comun` (solo lo usa sv9: no hay lógica compartida que
subir) ⇒ solo se reconstruyen las imágenes de sv9 y sv4. Sin DDL. Sin cambios en sigrid-api: el contrato ya admite
`empide`. Sigrid se sigue leyendo solo por `sql/read` y escribiendo solo por `sigrid/albaran` y `concepto-grafico`.

## 2. Resolución (una petición nueva; un `incierto` retomado no resuelve nada, R14)

| Entrada de Quien aprobó | `usu` | `empide` |
|---|---|---|
| con `usu` y `empide` | `buscar_usuario(entrada.usu)` o `error` (R4–R5) | `entrada.empide` comprobado (R7) |
| solo `empide` | R47 de F-053: correo o Respaldo (R6) | `entrada.empide` comprobado (R7), también con Respaldo |
| solo `usu` | como la primera fila | Origen `lista`/`correo` ⇒ `error` (R10) |
| sin Entrada, `usu` por correo | R47 | `error` `empleado_no_resuelto` (R10) **[E3]** |
| sin Entrada, `usu` por Respaldo | R47 (Respaldo) | `ALTA_SIGRID_EMPIDE` comprobado, o nulo (R8) |

«Comprobado» = `existe_empleado(ide)`; `False` ⇒ `error` (R11); excepción tras reintentos ⇒ `error` (R12). Orden: `usu`
→ `empide` → validación local → altas a mano → previa (R13). Ninguna rama manda `empide` nulo salvo la última con
`ALTA_SIGRID_EMPIDE` vacía, que es lo que pasa hoy con el Respaldo (sigrid-api pone su defecto, el empleado del
propio Respaldo `pgris`).

## 3. Ficheros a crear

- `services/albaranes-alta-sigrid/scripts/__init__.py` (vacío) y
  `services/albaranes-alta-sigrid/scripts/proponer_equivalencias_f069.py`: script de solo lectura (R23–R26), §7.
- `services/albaranes-alta-sigrid/tests/test_f069_*.py`: un fichero por bloque (`lista`, `config`, `cliente`,
  `servicio_usu`, `servicio_empide`, `peticion`, `worker`, `script`, `infra`). Nombres `test_f069_rN_...`.
- `services/albaranes-front/tests/test_f069_panel.py` (R20–R22).
- `progress/propuestas_a_sigrid_api_F-069.md`: petición de coordinación (§10), como la de F-053.

## 4. Ficheros a modificar

**sv9** (`services/albaranes-alta-sigrid/`):
- `domain/services/usuario_sigrid.py`: `Equivalencia`, `leer_equivalencias`, `entrada_de` (§6). Puro.
- `domain/models/alta_models.py`: `OrigenUsuario`, `OrigenEmpleado`, `UsuarioResuelto`, `EmpleadoResuelto`;
  constante `CLAVE_RESOLUCION = "resolucion"`. `PeticionAlbaran` NO cambia (`a_dict` sigue siendo el cuerpo exacto
  que se manda; `desde_dict` ya ignora claves que no conoce ⇒ R16 al retomar).
- `domain/ports/sigrid_alta_port.py`: método nuevo `existe_empleado(ide: int) -> bool` (lanza si la lectura falla
  tras los reintentos). El docstring pasa de «cinco» a «seis operaciones»; si algún test fija el número, se ajusta.
- `infrastructure/sigrid/sigrid_api_alta_client.py`: `SQL_EXISTE_EMPLEADO` y `existe_empleado` (`_leer`, etiqueta
  `f069-empleado`, `max_rows` 2).
- `domain/services/validador_alta.py`: `ConfigAlta` pierde `empide`; `validar_y_construir(datos, config, hoy, usu, *,
  empide: int | None = None)`. El servicio lo pasa siempre (lo prueban R7–R8); los ~25 tests que llaman sin él
  siguen igual.
- `application/alta_sigrid_service.py`: constructor con `equivalencias: Mapping[str, Equivalencia]` y
  `empide_respaldo: int | None`; `_resolver_usuario` devuelve `UsuarioResuelto`; nuevo `_resolver_empleado`;
  `EmpleadoNoResuelto` y `MOTIVO_EMPLEADO = "empleado_no_resuelto"`; `_flujo` guarda `resolucion` (R15) y la conserva
  al retomar (`{**peticion.a_dict(), "resolucion": previa.peticion["resolucion"]}` si estaba); log de R17.
- `config/settings.py`: `alta_sigrid_equivalencias_usuario: str = Field("", alias="ALTA_SIGRID_EQUIVALENCIAS_USUARIO")`
  con `field_validator` que llama a `leer_equivalencias` (R2; el `ValueError` lleva el motivo al log como R44);
  propiedades `equivalencias` y `empide_respaldo` (renombra `empide`; la variable sigue siendo `ALTA_SIGRID_EMPIDE`).
  Docstring: `ALTA_SIGRID_EMPIDE` = empleado del Respaldo, ya no de todas las altas.
- `interface_adapters/composition.py`: pasa `equivalencias` y `empide_respaldo`; `ConfigAlta(mapeo=...)`.
- `main_worker.py`: log de arranque con el número de Entradas y aviso de Lista vacía (R3); `peor_caso_mensaje_s`
  suma dos `_con_reintentos_s` más (`dbo.usu` y `dbo.emp`, R18; hoy ya faltaba la de `dbo.usu`).
- `tests/f053_fakes.py`: `SigridFalso.empleados: set[int]`, `existe_empleado` registrado en `llamadas` y con
  `fallar_en`. `tests/f053_datos.py` y los tests que construyen `ConfigAlta(empide=...)` (4 sitios: `composition`,
  `f053_datos.py`, `test_f053_r47_servicio.py:138`, `test_f053_validador.py:251`): sin `empide`; el de
  `test_f053_validador.py:251` pasa a probar `empide=` como argumento.
- `.env.example`, `sv9.md` (sección «Usuario de Sigrid» → «Usuario y empleado de Sigrid»; tabla de variables).

**sv4** (`services/albaranes-front/`):
- `domain/models/alta_sigrid_models.py`: `computed_field` `empide` (de `peticion["empide"]`, entero o `None`);
  `usu_respaldo` lee `peticion["resolucion"]["usu"]` si es un dict con esa clave y, si no, la regla de hoy (R21);
  `TEXTOS_MOTIVO_ALTA["empleado_no_resuelto"]` y texto nuevo de `usuario_no_resuelto` (R22). La clave
  `"resolucion"` se repite aquí como constante (sv4 no importa sv9); un test la contrasta con la fuente de sv9,
  como `TEXTOS_MOTIVO_ALTA` en F-077.
- `templates/_alta_sigrid.html`: «Empleado de Sigrid» junto al usuario (R20).

**infra y documentación**:
- `infra/00_capps_vars.ps1`: `$Global:ALTA_SIGRID_EQUIVALENCIAS_USUARIO` (JSON en comillas simples de PowerShell,
  con los valores que el humano valide en T2) y una función `EscaparJsonNativo` que reutilizan el mapeo y la Lista
  (la lógica de `AltaSigridEnvComun` de hoy, sin cambiar su resultado). Comentario: ni nombres ni DNI.
- `infra/create_capps_sv9.ps1` y `infra/set_alta_sigrid.ps1`: la Lista en los pares solo de sv9, escapada, y
  releída después de aplicarla (`set_alta_sigrid.ps1` ya relee: se añade al bucle de comprobación).
- `docs/ARCHITECTURE.md` regla 19, viñeta «Usuario de Sigrid» → «Usuario y empleado de Sigrid».
- `C:\Users\pgris\PycharmProjects\azure-apps\albaranes.md` §10: variable nueva, `empide` que se manda, lectura de
  `dbo.emp` en lo que consume, motivo nuevo. Commit local en `azure-apps` (regla de mantenimiento).

## 5. Ficheros que NO se tocan

- `ruesma_comun` (ni `alta_sigrid.py` ni `colas/mensajes.py`: `approved_by` ya viaja y se guarda).
- El DDL de `albaran_altas_sigrid` (sv3): `resolucion` va dentro de `peticion_json`, que ya es JSON.
- `PeticionAlbaran.a_dict`/`desde_dict` y el cuerpo que se manda: lo único nuevo es el valor de `empide`.
- sv4 al aprobar (`approved_by` de F-053 R49), sv3, sv5, sv6.
- `ALTA_SIGRID_COMMIT` (sigue en `true`; ningún script lo toca), `ALTA_SIGRID_USUARIO_RESPALDO`, DESDE.
- El repositorio de sigrid-api. Lo que haga falta de ellos va en §10.

## 6. Clases y funciones (capa)

- **domain** `usuario_sigrid.py`:
  - `@dataclass(frozen=True) class Equivalencia: usu: str | None; empide: int | None`.
  - `leer_equivalencias(texto: str | None) -> dict[str, Equivalencia]`: vacío ⇒ `{}`; `json.loads` con
    `object_pairs_hook` para detectar claves repetidas literales; claves normalizadas `strip().casefold()`; lanza
    `ValueError` con motivo y clave para cada caso de R2 (`bool` es `int` en Python: se rechaza explícitamente).
  - `entrada_de(approved_by: str | None, equivalencias) -> Equivalencia | None` (R1 glosario «Entrada»).
- **domain** `alta_models.py`: `class OrigenUsuario(StrEnum): LISTA, CORREO, RESPALDO`;
  `class OrigenEmpleado(StrEnum): LISTA, RESPALDO, DEFECTO_SIGRID_API` (valores en minúsculas como en el glosario);
  `UsuarioResuelto(usu: str, origen)`, `EmpleadoResuelto(empide: int | None, origen)`.
- **application** `AltaSigridService`:
  - `_resolver_usuario(document_id, approved_by) -> UsuarioResuelto` (R4–R6; lanza `UsuarioNoResuelto`).
  - `_resolver_empleado(document_id, approved_by, usuario: UsuarioResuelto) -> EmpleadoResuelto` (R7–R12; lanza
    `EmpleadoNoResuelto`; `_comprobar_empleado(ide)` envuelve `existe_empleado` y traduce excepción y `False`).
  - `_flujo`: `usuario` → `empleado` → `validar_y_construir(..., usuario.usu, empide=empleado.empide)` →
    `paso.peticion = {**peticion.a_dict(), CLAVE_RESOLUCION: {"usu": ..., "empide": ...}}`.
- **infrastructure** `SigridApiAltaClient.existe_empleado(ide) -> bool`.
- **script** (fuera de la hexagonal, como `medir_admisibilidad_f053.py` de sv3; `print` permitido): funciones puras
  `veredicto(pruebas) -> str`, `proponer(usuarios) -> list[Propuesta]`, `lista_json(propuestas) -> str`,
  `filas_csv(propuestas) -> list[list[str]]` (testeadas sin red); E/S en `main()` con `httpx` contra `sql/read` y
  `psycopg` contra PostgreSQL, credenciales del entorno (`SIGRID_API_BASE_URL`, `SIGRID_API_FUNCTION_KEY`, `PG_*`).
  No reutiliza `SigridApiAltaClient` para no abrirle una lectura genérica (F-053 R33).

## 7. SQL (solo lecturas; sin DDL)

sv9, por petición nueva: `SELECT TOP (1) ide FROM dbo.emp WHERE ide = ?` (además de la de `dbo.usu` de hoy).

Script (T2 valida cada una antes de fiarse; las del líder del 2026-10-23 son la referencia):
- (a) `SELECT TOP (1) cod, codemp FROM dbo.usu WHERE cod = ?`.
- (b) `SELECT TOP (3) ide, fecbaj FROM dbo.emp WHERE tarseg = ? AND ISNULL(tarseg, '') <> ''` (con `usu.codemp`).
- (c) `SELECT TOP (1) * FROM dbo.emp` para ver si existe `ele`; si existe,
  `SELECT TOP (3) ide, fecbaj FROM dbo.emp WHERE LOWER(ele) = LOWER(?)`.
- (d) `SELECT TOP (20) d.empide, COUNT(*) AS n FROM dbo.log l JOIN dbo.con c ON c.cod = l.cod AND c.tip = 14 JOIN
  dbo.dca d ON d.ide = c.ide WHERE l.tab = 'con' AND l.ope = 1 AND l.tip = 14 AND l.usu = ? AND l.fec >= ? AND
  ISNULL(d.synckey, '') NOT LIKE 'ALB-%' GROUP BY d.empide ORDER BY n DESC` (casar `log` con `con` por `cod` es
  lo que hizo el líder; `con.cod` es único por empresa, no global: T2 comprueba que no mezcla empresas).
- R25: `SELECT d.ide, d.empide FROM dbo.dca d WHERE d.ide IN (?, …)` (troceado si pasa de 500 parámetros).
- PostgreSQL: `SELECT DISTINCT approved_by FROM albaran_documents_merge WHERE approved` y
  `SELECT sigrid_con_ide, sigrid_cod, approved_by, peticion_json::json->>'usu' FROM albaran_altas_sigrid WHERE
  estado = 'registrado' AND sigrid_con_ide IS NOT NULL`. Comprueba `truncated` de cada `sql/read`.

## 8. Configuración y despliegue (lo ejecuta el humano)

- Orden **obligatorio**: (1) T2 y la Lista validada en `00_capps_vars.ps1`; (2) `set_alta_sigrid.ps1` pone la Lista
  en sv9 (la imagen de hoy la ignora: `extra="ignore"`) y la relee; (3) desplegar sv9; (4) desplegar sv4 (puede ir
  antes o después: sin `resolucion` aplica la regla de hoy). Si sv9 nuevo sale **sin** la Lista, con E3 = bloquear,
  toda alta de quien case por correo va a `error` `empleado_no_resuelto` (se ve en el panel y R3 lo avisa al
  arrancar); se arregla poniendo la Lista y pulsando «Solicitar alta» en cada una (estado `error` repetible, F-077).
- Vuelta atrás: imagen anterior de sv9 (vuelve a `empide` nulo). La Lista puede quedarse puesta.
- Cambiar la Lista después: editar `00_capps_vars.ps1` + `set_alta_sigrid.ps1` (revisión nueva, sin build).

## 9. Decisiones abiertas (PARADA 1), con la recomendación del spec-author

**E1 · De dónde sale el empleado.** (A) Lista explícita; (B) el `empide` más frecuente de sus altas a mano, leído en
cada alta; (C) `usu.codemp = emp.tarseg` en cada alta; (D) cadena A → B → C. **Recomendación: A en ejecución; B, C y
`emp.ele` solo en el script, para sembrar y mantener la Lista.** Motivos: escribir en el ERP pide una regla
determinista y auditable; C falla en 3 de 6 usuarios medidos, entre ellos `odomingo`, que aprueba; B no da nada para
quien nunca ha dado de alta a mano (un aprobador nuevo o un jefe de obra), da el ajeno a quien registra por otros, y
añade a cada alta una consulta pesada sobre `dbo.log` con un cruce por `cod` que no es único entre empresas. Un fallo
de B o C escribiría un empleado equivocado sin que nadie lo vea, que es justo el problema de hoy. Coste de A: dar de
alta una Entrada cuando llega un aprobador nuevo (pocos; el motivo `empleado_no_resuelto` lo hace visible).

**E2 · Dónde vive la Lista y quién la mantiene.** (a) variable JSON de sv9 versionada en `infra/00_capps_vars.ps1`;
(b) fichero de datos versionado dentro de la imagen de sv9; (c) tabla propia en PostgreSQL. **Recomendación: (a)**,
igual que el mapeo de productos: se valida al arrancar, cambiarla es una revisión sin build y queda en git. (b) exige
build y despliegue por cada usuario; (c) exige DDL en sv3 (dueño del schema), alguien que la escriba (no hay pantalla:
sería SQL a mano en producción) y otra tabla que lea sv9, para una decena de filas. **La mantiene el humano**: el
script propone, el líder prepara el cambio, el humano aplica `set_alta_sigrid.ps1`. Los `ide` de empleado y los logins
no son secretos (ya se versiona `pgris`); no se guardan nombres ni DNI.

**E3 · Si no se encuentra el empleado.** (i) bloquear: `error` `empleado_no_resuelto`; (ii) no mandar `empide`: gana
el defecto de sigrid-api (2425207) y queda un aviso. **Recomendación: (i)** para quien se identificó por la Lista o por
su correo: lo que pide el humano es que no salga el empleado de otro, y (ii) lo perpetúa en silencio. El alta no se
pierde: se ve en el panel y, tras añadir la Entrada, «Solicitar alta» la repite. Con el `usu` del Respaldo (quien
aprobó no es de Ruesma o no casa) se mantiene lo de hoy (R8). Si el humano elige (ii): R10 pasa a «manda `empide`
nulo y guarda el aviso `empleado_por_defecto`» y R3 cambia su aviso; el resto no cambia.

**E4 · Caché.** **Recomendación: ninguna.** La Lista está en memoria (variable leída al arrancar). `dbo.usu` y
`dbo.emp`: una lectura cada una por petición nueva (decenas al día), como hoy `dbo.usu`; una caché escondería un
empleado borrado y obligaría a invalidarla. Coste: una lectura más por alta (R18 la cuenta en la visibilidad).

**E5 · Las 46 altas ya escritas con 2425207.** Albaranes no reescribe en Sigrid. **Recomendación:** el script las
lista con el `empide` propuesto (R25) y el humano elige: dejarlas, corregirlas a mano en Sigrid o pedir a sigrid-api
una corrección; en ese caso, **una sola petición junto con la limpieza de F-103** (mismas altas, misma tabla `dca`).
Nada de esto entra en el código de F-069.

**E6 · El panel de sv4 enseña el empleado (R20–R21).** **Recomendación: sí** (poco código, y el administrativo ve
con qué empleado se dio de alta sin ir a Sigrid). Si no: fuera R20–R21; R22 se queda (sin texto, el motivo nuevo
saldría crudo y el test de F-077 falla).

**E7 · Empleado de baja (`emp.fecbaj`).** **Recomendación: no filtrar en v1**: sigrid-api no lo hace y una Entrada
es una decisión del humano; el script enseña `fecbaj` para que no se dé de alta una Entrada de baja.

## 10. Coordinación con sigrid-api (sin tocar su repositorio)

`progress/propuestas_a_sigrid_api_F-069.md`, para que el humano la pase a su sesión: (1) sigrid-api no comprueba que
el `empide` exista (`request.empide or settings.sigrid_albaran_empide`, `create_albaran_compra_use_case.py:844`;
modelo `ge=1`): proponer un rechazo `empleado_no_valido` como `usuario_no_valido`; mientras, sv9 lo comprueba (R7,
R11). (2) E5, unida a la limpieza de F-103. Ninguna es requisito previo de F-069.

## 11. Riesgos

- **Desplegar sv9 sin la Lista** ⇒ altas a `error` (§8): orden obligatorio, aviso al arrancar (R3) y T16 lo repite.
- **Lista mal escrita** ⇒ sv9 no arranca (R2): la revisión nueva falla y la anterior sigue sirviendo (modo single:
  comprobarlo en T16 con `az containerapp revision list`, solo lectura).
- **`resolucion` dentro de `peticion_json`**: si algo mandase ese JSON tal cual a sigrid-api, rompería
  (`extra="forbid"`). Hoy nada lo hace (se manda siempre `PeticionAlbaran.a_dict()`); R16 lo fija con tests, también
  al retomar. Descartado: columna nueva (DDL en sv3 para un dato de rastro) y meterlo en `historial_json` (cambia el
  repositorio y el formato del historial).
- **Datos personales**: la Lista lleva correos e `ide` internos; ni nombres, ni DNI, ni `tarseg` en git ni en progress.

## 12. Relacionadas (fuera de alcance)

F-103 (facturación heredada de la plantilla, la arregla sigrid-api), F-095 (descuentos en el alta), F-053 (base).
