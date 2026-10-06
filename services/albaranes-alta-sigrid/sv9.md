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
| `ALTA_SIGRID_USUARIO` | — | login de `dbo.usu` (T0c) |
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
- Ni la clave de sigrid-api, ni el PDF, ni datos bancarios en logs ni en la tabla.

## Arranque local

```powershell
cd services\albaranes-alta-sigrid
python main.py      # = python main_worker.py
```

Tests: `python -m pytest -q` desde esta carpeta (sola: no mezclar con sv3/sv5/sv6).
