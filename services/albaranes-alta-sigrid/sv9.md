# albaranes-alta-sigrid (Servicio 9 / sv9)

> F-053 · alta en Sigrid de los albaranes aprobados. Spec: `specs/F-053-alta-sigrid/`.
> Contrato con sigrid-api: `sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md`
> (v8.3, `871cc0c` (rama F-015 de sigrid-api): la forma de la petición es la de la v8.2 `13fd99d` y la v8
> `8a6ecab`; dueño sigrid-api, aquí se enlaza, no se copia).

## Qué hace

Worker sin HTTP sobre la cola `q-feedback`. Por cada `MensajeFeedback`:

- `accion="alta"`: reclama el documento (fila del merge `FOR UPDATE`), valida en
  local (sin llamar a nadie), busca altas a mano en Sigrid (`sql/read`), hace la
  **previa** del modo extendido de `POST /api/sigrid/albaran` (`commit=false`) y la
  compara con lo aprobado; en **simulación** se queda en `simulado`; en **real**
  graba una sola vez (`commit=true`, sin reintento) y adjunta el PDF con
  `concepto-grafico`.
- `accion="verificar_anulacion"`: comprueba con `sql/read` si el albarán
  registrado sigue en Sigrid (`anulado` si ya no está).
- Un `accion="alta"` sobre un alta `registrado` sin el PDF colgado solo
  reintenta el adjunto (`solo_adjunto`): es lo que publica «Reintentar adjunto»
  en la ficha de sv4 (v8, O1 = a).

## Usuario y empleado de Sigrid (`usu` y `empide`, F-053 v8 y F-069)

Spec de F-069: `specs/F-069-usuario-empleado-sigrid/`. Un solo punto decide cada
uno (`AltaSigridService._resolver_usuario` y `_resolver_empleado`), primero el
`usu` y luego el `empide`, los dos antes de la validación local (R14).

- **Login**: la parte antes de la @ del `approved_by` del merge (leído bajo el
  cerrojo; en Azure es el UPN de Easy Auth) si es un correo `@ruesma.es` (sin
  distinguir mayúsculas, ≤ 24). Sin correo de Ruesma no hay Login ni Entrada.
- **Lista de equivalencias** `ALTA_SIGRID_EQUIVALENCIAS_USUARIO` (JSON objeto,
  solo en sv9): clave = Login; valor = `{"usu": "<cod de dbo.usu>", "empide":
  <ide de dbo.emp>}` con una de las dos o las dos. Solo Logins e `ide`, nunca
  correos completos, nombres ni DNI. Mal formada = sv9 no arranca, con la clave
  culpable en el mensaje (R2). Al arrancar dice cuántas Entradas tiene.
- **`usu`**: (1) el `usu` de la Entrada, casado con `dbo.usu` (si no casa, Aviso
  `usuario_lista_no_existe` y sigue); (2) el Login casado con `dbo.usu.cod`;
  (3) el Respaldo `ALTA_SIGRID_USUARIO_RESPALDO` (`pgris`), que el panel marca
  «(respaldo)». Lectura de `dbo.usu` caída tras los reintentos, o Respaldo vacío
  cuando hace falta: `error` `usuario_no_resuelto`, sin previa ni grabación.
- **`empide`** (nunca bloquea el alta): (1) el `empide` de la Entrada si es un
  empleado de alta (`fecbaj` 0 o nulo; si no, `empleado_lista_no_valido`); (2) el
  ÚNICO empleado de alta cuyo `dbo.emp.traele` es el correo de quien aprobó (avisos
  `empleado_correo_ambiguo`, `empleado_correo_de_baja`,
  `empleado_correo_sin_empleado`, `empleado_sin_correo`); (3) nulo, y sigrid-api
  pone su defecto `SIGRID_ALBARAN_EMPIDE` (aviso `defecto_sigrid_api`). Una lectura
  de `dbo.emp` caída es el aviso `empleado_lectura_fallida` y el escalón siguiente.
  Los empleados de baja no cuentan nunca.
- **Avisos de resolución**: se guardan en `peticion_json.resolucion` =
  `{"usu": <origen>, "empide": <origen>, "avisos": [{codigo, detalle}]}` y el log
  dice `usu`, `empide`, sus orígenes y los códigos. `resolucion` **nunca** viaja a
  sigrid-api (su contrato es `extra="forbid"`). El panel de sv4 enseña el empleado
  y los avisos, como aviso, no como error.
- Un `incierto` retomado reenvía su petición con su `usu` y su `empide`, sin
  resolver de nuevo; el adjunto (también el reintento) usa el `usu` guardado.
- `ALTA_SIGRID_EMPIDE` (F-053) ya no existe: ningún `empide` sale de la
  configuración (R4); si sigue puesta en la app, se ignora.
- Medición de solo lectura de cuántos aprobadores tienen empleado por correo y de
  las altas ya escritas: `scripts/medir_empleados_f069.py` (F-069 T5).

## Altas a mano (R14, v8)

`dca.entref` se teclea a mano en formato libre: la búsqueda compara el número
del proveedor **normalizado** en los dos lados (mayúsculas, sin espacio, `.`,
`-` ni `/`; `UPPER` y `REPLACE` anidados en T-SQL y `normalizar_referencia` en
Python). `2.172.946` casa con `2172946`; un número que se queda vacío no busca.

Estado de cada alta: tabla `albaran_altas_sigrid` (la crea sv3, la escribe solo
sv9, la lee sv4). Producto de las líneas sin vincular: columna
`albaran_line_valuations.producto_sigrid` (la crea sv6) o el del mapeo
`ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (`ruesma_comun.alta_sigrid`).

## Códigos del contrato v8.3 (F-104)

Spec: `specs/F-104-codigos-contrato-v83/`. Contrato v8.3 §3.2–§3.3 (`871cc0c`).

- **Errores de cabecera** `proveedor_no_encontrado`, `proveedor_ambiguo` y `retencion_no_soportada` ⇒
  `no_admitido` (alta a mano), con el código como motivo y el `error` de sigrid-api de detalle.
- **Avisos de cabecera** `retencion_del_contrato` y `cabecera_sin_dato`: informativos. No están en
  `ALTA_SIGRID_AVISOS_BLOQUEANTES` (ni en el defecto ni en `infra/`); se guardan en `avisos_json` y el panel
  de sv4 los enseña con su texto y el `mensaje` de sigrid-api. `totales.tot`, `retenciones` y `filas.dcarec`
  no se comparan (la previa sigue por línea) y `filas` no se guarda.
- **`proveedor_sin_albaran_previo`** (retirado en la v8.3): **retirado** también de `CODIGOS_CABECERA` (T8, D1,
  2026-10-27), tras verificar con la F-015 de sigrid-api desplegada que ya no llega (M2). Si llegase, va a `error`
  como cualquier código desconocido (H25). sv4 conserva su texto (altas antiguas).

## Llaves (design §7)

| Variable | Defecto | Nota |
|---|---|---|
| `ALTA_SIGRID_DESDE_UTC` | vacía | vacía = feature apagada |
| `ALTA_SIGRID_COMMIT` | `false` | solo el literal `true` = real; lo cambia el humano; nunca en local |
| `ALTA_SIGRID_ESPERA_INCIERTO_MIN` | 15 | antes, un `en_curso`/`incierto` no se retoma |
| `ALTA_SIGRID_TOLERANCIA_EUR` | 0,05 | por línea, al comparar la previa |
| `ALTA_SIGRID_AVISOS_BLOQUEANTES` | `producto_sin_historico` | CSV |
| `ALTA_SIGRID_USUARIO_RESPALDO` | — (sin defecto; `pgris` en `infra/00_capps_vars.ps1`) | login de `dbo.usu` cuando quien aprobó no casa con uno (v8, R47); vacía = esas altas a `error` (R48) |
| `ALTA_SIGRID_EQUIVALENCIAS_USUARIO` | vacía | Lista de equivalencias Login → `usu`/`empide` (F-069); mal formada = no arranca (R2); solo en sv9 |
| `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` | `{"alquiler_maquinaria":"QA9999","medios_auxiliares":"XA9999","*":"MA9999"}` | mal formado = no arranca (R44); mismo valor en sv4 |

Además `SIGRID_API_*`, `PG_*`, `GRAPH_KEY`/`SHAREPOINT_*` y `COLAS_*` con los
nombres de sv3/sv6 (`.env.example`, sin valores).

## Reglas

- Solo llama a `sql/read` (altas a mano, `dbo.usu`, `dbo.emp`, ¿sigue el `con.ide`?), `sigrid/albaran` (modo extendido) y `concepto-grafico`.
- Nunca `sql/write`. Nunca `commit=true` en simulación.
- La grabación no se reintenta sola; un `incierto` se retoma tras la Espera
  reenviando la misma petición (la idempotencia de F-009 devuelve `idempotente`).
- Máximo una réplica (KEDA sobre `q-feedback`).
- Visibilidad de `q-feedback` por encima del peor caso de un mensaje (2460 s con los
  timeouts por defecto desde F-069, que suma dos lecturas de `dbo.usu` y dos de `dbo.emp`; `main_worker.visibilidad_cola_s`): un mensaje largo no se
  vuelve a entregar mientras se procesa.
- Una configuración inválida se registra con el campo y el motivo, nunca con los valores.
- Ni la clave de sigrid-api, ni el PDF, ni datos bancarios en logs ni en la tabla.

## Arranque local

```powershell
cd services\albaranes-alta-sigrid
python main.py      # = python main_worker.py
```

Tests: `python -m pytest -q` desde esta carpeta (sola: no mezclar con sv3/sv5/sv6).
