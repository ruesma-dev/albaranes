# Propuestas a sigrid-api desde F-069 (usuario y empleado de Sigrid)

> Origen: `specs/F-069-usuario-empleado-sigrid/design.md` §10. Redactado por el
> implementer el 2026-10-24. **No se ha tocado el repositorio de sigrid-api.**
> El humano lo revisa y, si está de acuerdo, se lo pasa a la sesión de
> sigrid-api. Ninguna de las tres cosas es requisito previo de F-069.

## 1. Rechazar un `empide` que no existe o que está de baja

**Qué pasa hoy.** El alta de albarán (F-009 de sigrid-api) acepta cualquier
`empide` ≥ 1 (`ge=1` en el modelo) y lo usa tal cual:
`request.empide or settings.sigrid_albaran_empide`
(`create_albaran_compra_use_case.py:844`, según el design de F-069). No comprueba
que la fila exista en `dbo.emp` ni que esté de alta (`fecbaj` 0 o nulo).

**Propuesta.** Un rechazo `empleado_no_valido` con la misma forma que el
`usuario_no_valido` que ya devuelve para `usu`, antes de la previa.

**Mientras tanto.** sv9 solo manda un `empide` que acaba de leer de `dbo.emp` de
alta (por la Lista o por el correo) o nulo. Con el rechazo, albaranes no
cambiaría nada: no le llegaría nunca uno de esos.

## 2. Aviso: albaranes depende de `SIGRID_ALBARAN_EMPIDE`

Cuando ni la Lista ni el correo dan un empleado, sv9 manda `empide` nulo (Aviso
`defecto_sigrid_api`) y sigrid-api pone su defecto `SIGRID_ALBARAN_EMPIDE` (hoy
2425207). Es el **último escalón** de albaranes (decisión E8): si sigrid-api
cambia ese valor o deja de aplicarlo con `empide` nulo, cambia el empleado de esas
altas. Pedimos que se trate como parte del contrato con albaranes y que nos avise
antes de tocarlo.

## 3. Las altas ya escritas con el empleado por defecto (E5), junto con F-103

Las altas que el pipeline ya escribió llevan el empleado por defecto. El script
de solo lectura `services/albaranes-alta-sigrid/scripts/medir_empleados_f069.py`
(T5 de F-069, lo ejecuta el líder) las lista con el empleado que les
correspondería. El humano decide: dejarlas, corregirlas a mano en Sigrid o
pedírselo a sigrid-api. Si se lo pide, **en una sola petición junto con la
limpieza de F-103** (mismas altas, misma tabla `dca`). Nada de esto va en el
código de albaranes.
