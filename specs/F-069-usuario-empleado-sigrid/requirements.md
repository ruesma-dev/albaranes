<!-- specs/F-069-usuario-empleado-sigrid/requirements.md -->
# F-069 · Usuario y empleado de Sigrid de quien aprueba · Requisitos (v3)

Rigor **critico** (escribe en el ERP de producción). Servicios: **sv9** (`services/albaranes-alta-sigrid`), **sv4**
(solo el panel del alta), `infra` y documentación. No toca `ruesma_comun`, ni el DDL, ni sigrid-api. Base: F-053 v8
(R5, R15, R22, R24, R47–R49 de `specs/F-053-alta-sigrid/requirements.md`). **v3** (PARADA 1 cerrada, 2026-10-23):
todas las decisiones E1–E8 están DECIDIDAS (`design.md` §9); la Lista va primero en los dos campos y el último escalón
del empleado manda `empide` nulo.

Reglas del humano (2026-10-23): «el usuario es el mismo que el del portal: al hacer login en Sigrid se usa el email del
portal; si no lo encuentra usa la lista, y si no, pgris por defecto. Debe buscar en los emails del empleado», y «antes
debe mirar en la lista, porque hay algún usuario cuyo email de portal y el de Sigrid pueden no coincidir». Medido por el
líder (solo lectura): el correo corporativo del empleado está en `dbo.emp.traele` (tipo `text`); casa con el `empide`
de las altas a mano y con todos los que aprueban hoy; hay un correo en dos empleados de alta.

## Glosario
- **Quien aprobó**: el `approved_by` que sv9 lee al reclamar (F-053 R5, R49): el UPN de Easy Auth en Azure.
- **Correo de Ruesma**: Quien aprobó sin espacios alrededor y en minúsculas, si tiene una sola @, la parte local no
  vacía y de ≤ 24 caracteres y el dominio `ruesma.es`; si no, no hay. **Login**: su parte local.
- **Lista**: la variable `ALTA_SIGRID_EQUIVALENCIAS_USUARIO` de sv9: objeto JSON Login → `{"usu"?, "empide"?}`, solo para
  excepciones; vacía es lo normal. Ejemplo ficticio: `{"login1": {"usu": "login1b"}, "login2": {"empide": 1234567}}`.
- **Entrada**: la de la Lista cuya clave es el Login (sin distinguir mayúsculas). Sin Correo de Ruesma, no hay.
- **Respaldo**: `ALTA_SIGRID_USUARIO_RESPALDO` (`pgris`).
- **Empleado de alta**: fila de `dbo.emp` con `fecbaj` 0 o nulo. **Empleados del correo**: los de `dbo.emp` cuyo
  `traele`, convertido a texto, sin espacios alrededor y en minúsculas, es el Correo de Ruesma.
- **Origen del usuario**: `lista`, `correo` o `respaldo`. **Origen del empleado**: `lista`, `correo` o
  `defecto_sigrid_api` (`empide` nulo: sigrid-api pone el suyo).
- **Aviso de resolución**: código que deja constancia de un escalón que no sirvió; nunca bloquea el alta.
- **Petición nueva**: la que sv9 construye (no la de un `incierto` retomado, F-053 R15).

## A. La Lista (configuración)
R1. sv9 debe leer la Lista de `ALTA_SIGRID_EQUIVALENCIAS_USUARIO`; ausente o vacía es la lista vacía, sin aviso.
R2. SI la Lista no es un objeto JSON; o una clave está vacía, lleva @ o espacios, o pasa de 24; o dos claves coinciden
sin distinguir mayúsculas; o un valor no es un objeto con solo las claves `usu` y `empide` y al menos una; o `usu` no es
un texto no vacío de ≤ 24 tras recortar; o `empide` no es un entero JSON ≥ 1 (un booleano, un texto o un decimal no
valen), ENTONCES sv9 no debe arrancar y el log debe dar el motivo y la clave (como F-053 R44).
R3. CUANDO sv9 arranca, debe escribir en el log, como información, cuántas Entradas tiene la Lista.
R4. sv9 ya no debe leer `ALTA_SIGRID_EMPIDE`: ningún `empide` sale de la configuración (E8).

## B. Usuario (`usu`): Lista → correo → Respaldo
R5. CUANDO sv9 construye una petición nueva y hay Entrada con `usu`, el `usu` debe ser el `cod` de `dbo.usu` que
devuelva la consulta de F-053 R47 para ese `usu` (Origen `lista`), sin probar el Login.
R6. SI la Entrada con `usu` no casa con `dbo.usu`, ENTONCES sv9 debe dejar el Aviso `usuario_lista_no_existe` y seguir
al escalón siguiente.
R7. CUANDO no hay Entrada con `usu` o no casó, el `usu` debe ser el de F-053 R47 si el Login casa con `dbo.usu`
(Origen `correo`) y, si no casa o no hay Correo de Ruesma, el Respaldo (Origen `respaldo`).
R8. SI la lectura de `dbo.usu` falla tras los reintentos o hace falta el Respaldo y está vacío, ENTONCES sv9 debe pasar
el alta a `error` `usuario_no_resuelto` sin previa ni grabación (F-053 R48, sin cambios) y sin leer `dbo.emp`.

## C. Empleado (`empide`): Lista → correo → nulo; nunca bloquea
R9. CUANDO sv9 construye una petición nueva y hay Entrada con `empide`, debe comprobar por `sql/read` que ese `ide` es
un Empleado de alta y mandarlo (Origen `lista`); SI no existe o es de baja, ENTONCES deja el Aviso
`empleado_lista_no_valido` y sigue al escalón siguiente.
R10. CUANDO la Lista no da empleado y hay Correo de Ruesma, sv9 debe leer por `sql/read` los Empleados del correo; SI
hay exactamente uno de alta, ENTONCES `empide` debe ser su `ide` (Origen `correo`), sea cual sea el Origen del usuario.
R11. SI hay dos o más Empleados del correo de alta, ENTONCES no cuenta como encontrado y queda el Aviso
`empleado_correo_ambiguo` con cuántos (hasta «3 o más»; sin sus `ide` ni nombres); SI todos son de baja, el Aviso
`empleado_correo_de_baja`; SI no hay ninguno, `empleado_correo_sin_empleado`; y sin Correo de Ruesma, sin leer
`dbo.emp`, `empleado_sin_correo`.
R12. CUANDO ni la Lista ni el correo dan empleado, sv9 debe mandar `empide` nulo (Origen `defecto_sigrid_api`) y dejar
el Aviso `defecto_sigrid_api`.
R13. SI una lectura de `dbo.emp` falla tras los reintentos (F-053 R24), ENTONCES sv9 debe dejar el Aviso
`empleado_lectura_fallida` y seguir al escalón siguiente; ningún caso de este bloque debe pasar el alta a `error`,
`revisar` ni `no_admitido`, ni impedir la previa o la grabación.
R14. sv9 debe resolver primero el `usu` y luego el `empide`, y los dos antes de la validación local (F-053 R47).

## D. Petición guardada, reintentos y rastro
R15. CUANDO sv9 retoma un `incierto` (F-053 R15), debe reenviar la petición guardada con su `usu` y su `empide` sin
volver a resolverlos ni leer la Lista, `dbo.usu` o `dbo.emp`.
R16. sv9 debe guardar en `peticion_json`, junto al cuerpo, la clave `resolucion` = `{"usu": <Origen del usuario>,
"empide": <Origen del empleado>, "avisos": [{"codigo", "detalle"}]}` y conservarla al retomar un `incierto`.
R17. La clave `resolucion` nunca debe viajar a sigrid-api: ni en la previa, ni en la grabación, ni al retomar un
`incierto` (el contrato de sigrid-api es `extra="forbid"`).
R18. CUANDO sv9 resuelve una petición nueva, debe escribir en el log `usu`, `empide`, sus orígenes y los códigos de
Aviso; nunca el correo completo ni el cuerpo.
R19. El peor caso de un mensaje (`main_worker.peor_caso_mensaje_s`) debe contar dos lecturas de `dbo.usu` y dos de
`dbo.emp`, con sus reintentos.
R20. El adjunto (F-053 R22, también «Reintentar adjunto») debe seguir usando el `usu` de la petición guardada.

## E. Panel del alta en sv4
R21. MIENTRAS el alta tenga petición guardada, el panel debe enseñar «Empleado de Sigrid: N» junto al usuario y, con
`empide` nulo, «Empleado de Sigrid: el de defecto de sigrid-api».
R22. MIENTRAS `resolucion.avisos` no esté vacía, el panel debe enseñar el texto legible de cada Aviso como aviso, no
como error, y sin bloquear nada; un código sin texto se enseña tal cual.
R23. La marca «(respaldo)» del usuario debe salir de `resolucion.usu == "respaldo"`; SI la petición no tiene
`resolucion` (altas anteriores a F-069), ENTONCES la regla de hoy (el `usu` no es la parte local del correo).
R24. Los textos de los Avisos y la clave `resolucion` deben coincidir con las constantes de sv9 (un test las contrasta,
como `TEXTOS_MOTIVO_ALTA` en F-077); el texto de `usuario_no_resuelto` debe valer para el alta, no solo para el PDF.

## F. Medición (script de solo lectura) (E5)
R25. `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py` debe medir la cobertura de los Empleados del
correo sobre cada Quien aprobó distinto de los merges aprobados y de `albaran_altas_sigrid`, con la misma consulta y la
misma clasificación que sv9 (las importa): `unico`, `ambiguo`, `de_baja`, `sin_empleado` o `sin_correo`.
R26. El script debe listar las altas ya escritas por el pipeline (`registrado`, con `sigrid_con_ide`) con `con.ide`,
`cod`, Login, `usu`, `dca.empide` actual y el que les correspondería con R9–R12, y si difieren; sin escribir nada.
R27. El script debe sacar un CSV (UTF-8 con BOM, `;`) y un resumen con Logins e `ide`; nunca correos completos, nombres
ni DNI. Solo lecturas: `sql/read` (sentencias `SELECT`) y `SELECT` en PostgreSQL.

## G. Configuración desplegada y documentación
R28. `infra/00_capps_vars.ps1` debe versionar la Lista (vacía de inicio; Logins e `ide`, nunca correos completos, nombres
ni DNI), y `create_capps_sv9.ps1` y `set_alta_sigrid.ps1` deben pasarla SOLO a sv9, con las comillas escapadas como el
mapeo de producto, y releerla; deben dejar de pasar `ALTA_SIGRID_EMPIDE` (R4); ninguno toca `ALTA_SIGRID_COMMIT`.
R29. `.env.example` de sv9, `sv9.md`, la regla 19 de `docs/ARCHITECTURE.md` y §10 de `azure-apps/albaranes.md` deben
describir la resolución de `usu` y `empide`, la Lista, la lectura nueva de `dbo.emp`, los Avisos de resolución y la
retirada de `ALTA_SIGRID_EMPIDE`.
