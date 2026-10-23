<!-- specs/F-069-usuario-empleado-sigrid/requirements.md -->
# F-069 · Usuario y empleado de Sigrid de quien aprueba · Requisitos (v1)

Rigor **critico** (escribe en el ERP de producción). Servicios: **sv9** (`services/albaranes-alta-sigrid`), **sv4**
(solo el panel del alta), `infra` y documentación. No toca `ruesma_comun`, ni el DDL, ni sigrid-api. Base: F-053 v8
(R5, R15, R22, R24, R47–R49 de `specs/F-053-alta-sigrid/requirements.md`). **Pendiente de PARADA 1**: los R marcados
**[En]** dependen de la decisión abierta En de `design.md` §9; están escritos con la recomendación del spec-author.

Petición del humano (2026-10-23): «primero que la escritura sea con el usuario/emp que usa la plataforma». Hecho medido
(solo lectura, 2026-10-23): el `usu` ya es el de quien aprueba; el `empide` va nulo y sigrid-api pone su defecto
(2425207) en las 46 altas del pipeline; en las altas a mano cada usuario lleva su empleado; `dbo.usu` y `dbo.emp` no
comparten una clave fiable (`usu.dni` vacío; `usu.codemp ≈ emp.tarseg` casa en unos usuarios y no en otros).

## Glosario
- **Quien aprobó**: el `approved_by` que sv9 lee al reclamar (F-053 R5, R49): el UPN de Easy Auth en Azure.
- **Lista**: la variable `ALTA_SIGRID_EQUIVALENCIAS_USUARIO` de sv9 **[E2]**: objeto JSON correo → `{"usu"?, "empide"?}`.
  Ejemplo: `{"odomingo@ruesma.es": {"empide": 1234567}, "x@ruesma.es": {"usu": "xlogin", "empide": 7654321}}`.
- **Entrada**: la de la Lista cuya clave es Quien aprobó, ambos sin espacios alrededor y sin distinguir mayúsculas.
- **Respaldo**: `ALTA_SIGRID_USUARIO_RESPALDO` (F-053 R47). **Empleado del Respaldo**: `ALTA_SIGRID_EMPIDE` (vacía = nulo).
- **Origen del usuario**: `lista`, `correo` (parte local, R47) o `respaldo`. **Origen del empleado**: `lista`,
  `respaldo` (Empleado del Respaldo puesto) o `defecto_sigrid_api` (`empide` nulo).
- **Petición nueva**: la que sv9 construye (no la de un `incierto` retomado, F-053 R15).

## A. La Lista (configuración)
R1. sv9 debe leer la Lista de `ALTA_SIGRID_EQUIVALENCIAS_USUARIO`; ausente o vacía es la lista vacía, y entonces el
`usu` sale exactamente como en F-053 R47–R48.
R2. SI la Lista no es un objeto JSON; o una clave no es un correo con una sola @ y las dos partes no vacías; o dos
claves coinciden sin espacios alrededor y sin distinguir mayúsculas; o un valor no es un objeto con solo las claves
`usu` y `empide` y al menos una de ellas; o `usu` no es un texto no vacío de ≤ 24 caracteres tras recortar; o `empide`
no es un entero JSON ≥ 1 (un booleano, un texto o un decimal no valen), ENTONCES sv9 no debe arrancar y el log debe
dar el motivo y la clave afectada (como F-053 R44).
R3. CUANDO sv9 arranca, debe escribir en el log cuántas Entradas tiene la Lista, y si DESDE está puesta y la Lista
está vacía, un aviso de que las altas de quien case por correo irán a `error` `empleado_no_resuelto` (R10) **[E3]**.

## B. Usuario (`usu`)
R4. CUANDO sv9 construye una petición nueva y la Entrada trae `usu`, el `usu` debe ser el `cod` de `dbo.usu` que
devuelva la consulta de F-053 R47 para ese `usu`, sin probar la parte local del correo; Origen del usuario `lista`.
R5. SI la Entrada trae `usu` y ese `usu` no casa con `dbo.usu`, ENTONCES sv9 debe pasar el alta a `error`
`usuario_no_resuelto` sin previa ni grabación, con el `usu` en el detalle (no cae al correo ni al Respaldo).
R6. CUANDO no hay Entrada o la Entrada no trae `usu`, el `usu` debe resolverse como en F-053 R47–R48 (Origen
`correo` o `respaldo`), con la misma consulta y los mismos motivos.

## C. Empleado (`empide`) **[E1, E3]**
R7. CUANDO sv9 construye una petición nueva y la Entrada trae `empide`, sv9 debe comprobar por `sql/read` que ese
`ide` existe en `dbo.emp` y mandarlo en `empide` como entero JSON; Origen del empleado `lista`. Vale también cuando el
`usu` salió del Respaldo: el empleado es el de la persona que aprobó.
R8. CUANDO no hay Entrada con `empide` y el Origen del usuario es `respaldo`, `empide` debe ser el Empleado del
Respaldo, comprobado como en R7 (Origen `respaldo`), o nulo si `ALTA_SIGRID_EMPIDE` está vacía (Origen
`defecto_sigrid_api`): el comportamiento de hoy.
R9. sv9 no debe mandar el Empleado del Respaldo en ningún caso distinto de R8.
R10. SI no hay Entrada con `empide` y el Origen del usuario es `lista` o `correo`, ENTONCES sv9 debe pasar el alta a
`error` `empleado_no_resuelto`, sin previa ni grabación, con Quien aprobó en el detalle **[E3]**.
R11. SI el `empide` de R7 o de R8 no existe en `dbo.emp`, ENTONCES sv9 debe pasar el alta a `error`
`empleado_no_resuelto` sin previa ni grabación, con ese `ide` en el detalle.
R12. SI la lectura de `dbo.emp` falla tras los reintentos (F-053 R24), ENTONCES sv9 debe pasar el alta a `error`
`empleado_no_resuelto` sin previa ni grabación; nunca debe mandar `empide` nulo para salir del paso.
R13. sv9 debe resolver el `usu` antes que el `empide`; SI el `usu` no se resuelve (R5, F-053 R48), ENTONCES no debe
leer `dbo.emp`. Las dos resoluciones van antes de la validación local, como hoy la del `usu` (F-053 R47).

## D. Petición guardada, reintentos y rastro
R14. CUANDO sv9 retoma un `incierto` (F-053 R15), debe reenviar la petición guardada con su `usu` y su `empide` sin
volver a resolverlos ni leer la Lista, `dbo.usu` o `dbo.emp`.
R15. sv9 debe guardar en `peticion_json`, junto al cuerpo, la clave `resolucion` = `{"usu": <Origen del usuario>,
"empide": <Origen del empleado>}`, y conservarla al retomar un `incierto`.
R16. La clave `resolucion` nunca debe viajar a sigrid-api: ni en la previa, ni en la grabación, ni al retomar un
`incierto` (el contrato de sigrid-api es `extra="forbid"`).
R17. CUANDO sv9 resuelve una petición nueva, debe escribir en el log `usu`, `empide` y sus dos orígenes, sin el cuerpo.
R18. El peor caso de un mensaje (`main_worker.peor_caso_mensaje_s`, visibilidad de la cola) debe contar las lecturas
de `dbo.usu` y de `dbo.emp` con sus reintentos.
R19. El adjunto (F-053 R22, también «Reintentar adjunto») debe seguir usando el `usu` de la petición guardada.

## E. Panel del alta en sv4 **[E6]**
R20. MIENTRAS el alta tenga petición guardada, el panel debe enseñar «Empleado de Sigrid: N» junto al usuario y, con
`empide` nulo, «Empleado de Sigrid: el de defecto de sigrid-api».
R21. La marca «(respaldo)» del usuario debe salir de `resolucion.usu == "respaldo"`; SI la petición no tiene
`resolucion` (altas anteriores a F-069), ENTONCES la regla de hoy (el `usu` no es la parte local del correo).
R22. `TEXTOS_MOTIVO_ALTA` de sv4 debe dar un texto legible para `empleado_no_resuelto` (cubierto por el test de F-077
que contrasta los motivos con las fuentes de sv9), y el de `usuario_no_resuelto` debe valer también para el alta, no
solo para el PDF.

## F. Medición y mantenimiento de la Lista (script de solo lectura) **[E1, E5]**
R23. `services/albaranes-alta-sigrid/scripts/proponer_equivalencias_f069.py` debe proponer, por cada Quien aprobó
distinto de `albaran_altas_sigrid` y de los merges aprobados, un `usu` y un `empide` con sus pruebas: (a) `dbo.usu`
de la parte local; (b) `emp.tarseg = usu.codemp`; (c) `emp.ele` igual al correo, si la columna existe; (d) el `empide`
más frecuente de sus albaranes de compra a mano (`con.tip` 14, `synckey` sin prefijo `ALB-`, autor por `dbo.log`) en
los últimos `--dias` (180); y un veredicto por usuario sobre (b), (c) y (d): `coinciden` (dos o más dan el mismo
`ide` y ninguna otro), `un_dato` (solo una da `ide`), `discrepan` (dan `ide` distintos) o `sin_dato` (ninguna).
R24. El script debe escribir el JSON propuesto para la Lista (solo los `coinciden`) y un CSV (UTF-8 con BOM, `;`, coma
decimal) con todas las pruebas, incluida `emp.fecbaj`, para que el humano decida; nunca nombres ni DNI.
R25. El script debe listar las altas ya escritas por el pipeline (`registrado`, con `sigrid_con_ide`) con `con.ide`,
`cod`, Quien aprobó, `usu`, `dca.empide` actual y el propuesto, sin escribir nada **[E5]**.
R26. El script solo debe hacer lecturas: `sql/read` de sigrid-api (sentencias `SELECT`) y `SELECT` en PostgreSQL;
nunca `sql/write`, `sigrid/albaran`, `concepto-grafico` ni escrituras en PostgreSQL.

## G. Configuración desplegada y documentación
R27. `infra/00_capps_vars.ps1` debe versionar la Lista (correos, logins y `ide` de empleado; ningún secreto, nombre ni
DNI), y `create_capps_sv9.ps1` y `set_alta_sigrid.ps1` deben pasarla SOLO a sv9, con las comillas escapadas como el
mapeo de producto y releyéndola tras aplicarla; ningún script toca `ALTA_SIGRID_COMMIT`.
R28. `.env.example` de sv9, `sv9.md`, la regla 19 de `docs/ARCHITECTURE.md` y §10 de
`azure-apps/albaranes.md` deben describir la Lista, el `empide` que ahora se manda, la lectura nueva de `dbo.emp`
y el motivo `empleado_no_resuelto`.
