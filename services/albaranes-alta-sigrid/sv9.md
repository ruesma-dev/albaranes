# albaranes-alta-sigrid (Servicio 9 / sv9)

> F-053 · alta en Sigrid de los albaranes aprobados. Spec: `specs/F-053-alta-sigrid/`.
> Contrato con sigrid-api: `sigrid-api/specs/F-009-alta-albaran-compra/contrato_albaranes.md`
> (v8.2, `13fd99d`, misma forma que la v8 `8a6ecab`; dueño sigrid-api, aquí se enlaza, no se copia).

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

## Usuario de Sigrid (`usu`, v8: R47–R48)

- Una petición nueva lleva el login de **quien aprobó**: la parte antes de la @
  del `approved_by` del merge (leído bajo el cerrojo; en Azure es el UPN de Easy
  Auth, R49) si es un correo `@ruesma.es` (sin distinguir mayúsculas, ≤ 24),
  casada con `dbo.usu.cod` por `sql/read`; se manda el `cod` que devuelve Sigrid.
- Si no es correo de Ruesma o no casa: `ALTA_SIGRID_USUARIO_RESPALDO` (`pgris`).
  El panel de sv4 lo marca «(respaldo)».
- Lectura de `dbo.usu` caída tras los reintentos, o Respaldo vacío cuando hace
  falta: `error` `usuario_no_resuelto`, sin previa ni grabación.
- Un `incierto` retomado reenvía su petición con su `usu`; el adjunto (también el
  reintento) usa el `usu` de la petición guardada.
- Un único punto lo decide (`AltaSigridService._resolver_usuario`): ahí entrará
  la lista de equivalencias correo → login de F-069.

## Altas a mano (R14, v8)

`dca.entref` se teclea a mano en formato libre: la búsqueda compara el número
del proveedor **normalizado** en los dos lados (mayúsculas, sin espacio, `.`,
`-` ni `/`; `UPPER` y `REPLACE` anidados en T-SQL y `normalizar_referencia` en
Python). `2.172.946` casa con `2172946`; un número que se queda vacío no busca.

Estado de cada alta: tabla `albaran_altas_sigrid` (la crea sv3, la escribe solo
sv9, la lee sv4). Producto de las líneas sin vincular: columna
`albaran_line_valuations.producto_sigrid` (la crea sv6) o el del mapeo
`ALTA_SIGRID_PRODUCTO_POR_DEFECTO` (`ruesma_comun.alta_sigrid`).

## Llaves (design §7)

| Variable | Defecto | Nota |
|---|---|---|
| `ALTA_SIGRID_DESDE_UTC` | vacía | vacía = feature apagada |
| `ALTA_SIGRID_COMMIT` | `false` | solo el literal `true` = real; lo cambia el humano; nunca en local |
| `ALTA_SIGRID_ESPERA_INCIERTO_MIN` | 15 | antes, un `en_curso`/`incierto` no se retoma |
| `ALTA_SIGRID_TOLERANCIA_EUR` | 0,05 | por línea, al comparar la previa |
| `ALTA_SIGRID_AVISOS_BLOQUEANTES` | `producto_sin_historico` | CSV |
| `ALTA_SIGRID_USUARIO_RESPALDO` | — (sin defecto; `pgris` en `infra/00_capps_vars.ps1`) | login de `dbo.usu` cuando quien aprobó no casa con uno (v8, R47); vacía = esas altas a `error` (R48) |
| `ALTA_SIGRID_EMPIDE` | vacía | vacía = defecto de sigrid-api |
| `ALTA_SIGRID_PRODUCTO_POR_DEFECTO` | `{"alquiler_maquinaria":"QA9999","medios_auxiliares":"XA9999","*":"MA9999"}` | mal formado = no arranca (R44); mismo valor en sv4 |

Además `SIGRID_API_*`, `PG_*`, `GRAPH_KEY`/`SHAREPOINT_*` y `COLAS_*` con los
nombres de sv3/sv6 (`.env.example`, sin valores).

## Reglas

- Solo llama a `sql/read`, `sigrid/albaran` (modo extendido) y `concepto-grafico`.
- Nunca `sql/write`. Nunca `commit=true` en simulación.
- La grabación no se reintenta sola; un `incierto` se retoma tras la Espera
  reenviando la misma petición (la idempotencia de F-009 devuelve `idempotente`).
- Máximo una réplica (KEDA sobre `q-feedback`).
- Visibilidad de `q-feedback` por encima del peor caso de un mensaje (1740 s con los
  timeouts por defecto; `main_worker.visibilidad_cola_s`): un mensaje largo no se
  vuelve a entregar mientras se procesa.
- Una configuración inválida se registra con el campo y el motivo, nunca con los valores.
- Ni la clave de sigrid-api, ni el PDF, ni datos bancarios en logs ni en la tabla.

## Arranque local

```powershell
cd services\albaranes-alta-sigrid
python main.py      # = python main_worker.py
```

Tests: `python -m pytest -q` desde esta carpeta (sola: no mezclar con sv3/sv5/sv6).
