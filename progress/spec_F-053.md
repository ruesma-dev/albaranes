<!-- progress/spec_F-053.md -->
# Spec F-053 · Alta en Sigrid de los albaranes aprobados (spec-author)

Rama `feature/F-053-alta-sigrid` (worktree `../albaranes-F-053`, desde `dev` c8a295e).
Estado `spec_ready`, rigor `critico`, prioridad 1. v1 del 2026-09-30; v2, v3 y
**v4 del 2026-10-01**. **Todas las decisiones están cerradas**: no quedan
preguntas abiertas; solo la aprobación de esta v4 (PARADA 1).

## Qué hay en la rama

- `specs/F-053-alta-sigrid/requirements.md` — R1–R38 en EARS (150/150 líneas).
- `specs/F-053-alta-sigrid/design.md` — sv9, PRE-1 (= F-009 de sigrid-api),
  flujo, DDL, configuración, orden y cambio de reglas (249/250).
- `specs/F-053-alta-sigrid/tasks.md` — T0, T0b, T0c, T1–T30 y T21b; T0–T0c,
  T22 y T26–T29 son MANUAL del humano.
- `services/albaranes-persistencia/scripts/medir_admisibilidad_f053.py` y
  `tests/test_f053_medicion_admisibilidad.py` (14 tests en verde; `compileall`
  ok). **No se ha ejecutado contra ninguna BBDD.**
- `BACKLOG.md` regenerado (`python harness/backlog.py`; los commits anteriores de
  esta rama lo habían dejado desfasado respecto de `features.json`).
- No se ha llamado a sigrid-api ni a Azure.

## Decisiones del humano (todas del 2026-10-01 salvo indicación)

| Tema | Decisión |
|---|---|
| Aprobar | ES registrar; los dos botones de sv4 (2026-09-30) |
| Vía | Solo endpoints de dominio de sigrid-api, nunca `sql/write` (2026-09-30) |
| Servicio | sv9 nuevo en el monorepo, consume `q-feedback` |
| F-013 | Sustituida por F-053 (ver más abajo cómo queda en `features.json`) |
| Alcance | «Medir antes» (T0) |
| Líneas | Solo con importe (`importe_calculado` ≠ 0); vinculadas (consumen medición) y sin vincular en el mismo albarán; cada una con partida o en almacén |
| Producto | El de la línea de contrato; sin vincular, `MA9999` por código (`ALTA_SIGRID_PRODUCTO_POR_DEFECTO`); elegir entre MA9999/SM9999/SB9999/QA9999, mejora futura |
| Negativas | Entran ya |
| Sin valorar | No se aprueba ni se registra; el bloqueo de sv4 va **dentro** de F-053 (R37); `partial` no cuenta |
| Valorado | `ok` de sv6, o valoración manual completa del administrativo (ver abajo) |
| Empleado | Fijo y configurable (`ALTA_SIGRID_EMPIDE`) |
| Clave | La de siempre; riesgo anotado (design §11) |
| DDL | En sv3 |
| Tolerancia | 0,05 € por línea; avisos bloqueantes: «plantilla de otro proveedor» y «sin histórico de dcapro» |
| Simulados | No se graban solos al pasar a real; uno a uno desde la ficha |
| Re-aprobación | Desaprobar y aprobar cuenta como aprobación nueva |
| F-015 | Las tachadas se excluyen cuando llegue; el «solo llevar» de F-006 ya queda fuera por no tener importe |
| Registrado | Bloqueado en sv4; se corrige anulando en Sigrid y «Ya lo he anulado» |
| Documentación ajena | Con la redacción propuesta (design §9), también `azure-apps/sigrid_api.md` §10 |
| Antiguas 6 y 9 | Verificaciones de solo lectura T0b (Referencia en altas manuales) y T0c (usuario `usu`, GRATIPIDE 0 y firma PDF), con su propuesta por defecto |

## «Valorado»: comprobado en el código

El humano: «el administrativo valora el albaran aunque tenga contrato. pero
siempre ira valorado». **sv4 ya permite valorar a mano un albarán sin contrato,
así que no hay hueco** (`services/albaranes-front/infrastructure/database/review_repository.py`):
- `add_standalone_valuation_line` y `add_conciliacion_for_merge_line` crean líneas
  de valoración (`line_kind` `manual`/`from_albaran`) y, si el documento no tenía
  valoración, una cabecera `albaran_valuations` con `status = 'manual'`. Si sv6
  ya había dejado la cabecera vacía `no_contract`, se mantiene ese estado.
- `ValuationLineUpdate` deja editar y persiste partida, descripción, cantidad,
  unidad, precio e importe de cada línea.

Definición adoptada (R38, `ruesma_comun.valoracion.esta_valorado`, compartida por
sv4 y sv9): **valorado** = cabecera en `ok`, o cabecera `manual`/`no_contract` con
alguna línea con importe ≠ 0 y ninguna línea valorada con importe nulo. `partial`,
`failed`, `pending`, `running` o sin cabecera: no valorado. Aviso: «Valorar ahora»
regenera la valoración y borra lo hecho a mano (comportamiento ya existente).

## F-013 en `features.json`

Título con el prefijo `[SUSTITUIDA POR F-053]` y descripción que lo explica, pero
**sigue en `pending`**: el arnés solo admite `pending`/`spec_ready`/`in_progress`/
`done`/`blocked`, `done` exige init.sh en verde y review APROBADO (regla dura del
`CLAUDE.md`) y `blocked` haría que el protocolo la retomase la primera. El líder o
el humano deciden si se borra la entrada o se marca de otra forma.

## Requisito previo: PRE-1 = F-009 de sigrid-api

La especifica otro agente en el repositorio sigrid-api. Lo que F-053 necesita está
en design §2: `cod_contrato` opcional; `referencia_externa` → `dca.synckey` con
idempotencia; por línea `partida` (código) o `almacen: true` y `referencia_linea`;
vinculadas (`ctrpro_ide`, consumen `canser`, varias al mismo `ctrpro`) y
`lineas_sin_contrato[]` con **producto por código**; **cantidades negativas**
replicando al escritorio de Sigrid (stock, PMP —hay que medir si lo recalcula—,
`canser`, `estser/estfac`); respuesta por línea y errores con código. Si el
contrato de F-009 difiere, manda el suyo y se ajusta la petición de R12.

## Medición (T0): comando para PowerShell

Solo lectura (`SET TRANSACTION READ ONLY`, solo SELECT). El worktree no tiene
`.venv` ni `.env`: se usan los del árbol principal sin tocarlos. El `.env` de
sv3 decide a qué BBDD va; para que la cifra valga, la de Azure (solo lectura).

```powershell
cd C:\Users\pgris\PycharmProjects\albaranes-F-053\services\albaranes-persistencia
$sv3 = "C:\Users\pgris\PycharmProjects\albaranes\services\albaranes-persistencia"
& "$sv3\.venv\Scripts\python.exe" -m scripts.medir_admisibilidad_f053 --env "$sv3\.env" --csv "$env:TEMP\f053_aprobados.csv"
& "$sv3\.venv\Scripts\python.exe" -m scripts.medir_admisibilidad_f053 --env "$sv3\.env" --todos --csv "$env:TEMP\f053_todos.csv"
```

Agregado por pantalla y CSV por albarán (UTF-8 BOM, `;`): valorados (con la
definición de arriba), con contrato, cabecera completa, líneas con importe y sin
él, negativas, con importe y sin cantidad, las cinco categorías
(`casa_misma_partida`, `casa_partida_distinta`, `partida_sin_casar`,
`almacen_sin_casar`, `sin_partida_ni_almacen`), cuántas irían con MA9999 y el %
registrable **(a)** con sigrid-api tal cual y **(b)** con el criterio del humano.
Antes de F-051 casi no hay marcas de almacén: (b) sale **por debajo** de lo real.

## Orden

**Medición → F-009 de sigrid-api → F-052 → F-051 → F-053** (design §8).

## Hallazgos que siguen vigentes

1. sigrid-api hoy: 400 con texto libre (salvo `concepto-grafico`), 500 lo inesperado.
2. sv4 pone `approved_at_utc = ahora` en cada guardado aprobado: el disparo es
   solo el paso de no aprobado a aprobado (R1–R2).
3. El deshacer de sv4 restaura la fila del merge: el estado del alta va en
   `albaran_altas_sigrid`, que solo escribe sv9.
4. `features.json` de esta rama no tiene F-051 ni F-052: conflicto trivial al fusionar.

## Riesgo residual

Ninguna escritura real hasta F-009 desplegada y `ALTA_SIGRID_COMMIT=true`. Con la
clave de siempre, el único control de quién escribe es el código y la revisión.
