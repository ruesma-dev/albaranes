<!-- progress/review_F-084.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` · HEAD `fbbabd7`, `dev` `2721e06` fusionado

# F-084 · Review del reviewer: el banco de evals valora de verdad

## Veredicto

**APPROVED para lanzar T12** (el alcance que pidió el líder). **No es cerrable todavía**: los
cambios 1 y 2, **antes de T13**; el 3, **antes de T14**. Ninguno cambia lo que T12 lee ni lo que
produce (libro, caché e índice): T12 puede lanzarse ya con los comandos de `impl_F-084.md`.

## Nivel de rigor

`critico` (declarado): fase RED, cobertura ≥ 80 %, mutación completa con 0 supervivientes y las
MANUAL con su comando exacto.

## Lo verificado por el reviewer

- **`bash harness/init.sh`**: raíz 1839 passed; sv1 205, sv2 485, sv3 1576, sv4 1774, sv5 96, sv6 473
  (+1 skipped), sv9 673, comun en verde; `PUERTA COBERTURA: 98.5% de 598 líneas`; rutas sensibles N/A.
  Primera pasada con un único `[KO]`, PUERTA TAMAÑO de **este** informe (167 > 140), recortado y
  reejecutado: `ENTORNO LISTO` (exit 0), mismos totales, tamaño 135/140.
- **Solo lectura.** sigrid-api: solo `POST /api/sql/read`, `SELECT` parametrizado (`con_ctr.cod = ?`,
  `emp = 1`, `ORDER BY` estable), `max_rows` 500.000, `NO_TOLERA`; la clave va en
  `x-functions-key` y no sale en `__repr__` ni en errores. BBDD: `_SQL_CONTRATO_HEADER` de sv5
  (un test la compara en subproceso) en sesión `-c default_transaction_read_only=on`, sin commit.
  SharePoint: solo los dos `download_*` del descargador de sv5; en `ruesma_comun/sharepoint/
  graph_client.py` esos caminos solo hacen `GET` (los `post/put/delete` no se alcanzan). Las
  credenciales van al subproceso por `env`, nunca por stdin (lo fija un test).
- **Secretos.** Barrido de las líneas añadidas del diff con `https?://`, `.postgres.database`,
  `sharepoint.com`, `azurewebsites`, GUID, `b![A-Za-z0-9_-]{20,}`, IPv4, `password=`, `api_key=`,
  `sk-…`, `psql-`, `rs9k2`: solo hosts `*.invalid` de tests y `Read-Host -AsSecureString`. Los
  comandos de T12 sacan `PG_HOST` y `$SP` de `infra/00_vars.ps1`, que carga `00_vars.local.ps1`
  (no versionado): ni URL, ni host, ni drive id en el informe.
- **`azure-apps` `a6bc26a`**: párrafo en §8 de `albaranes.md`, fiel al código. Commit local; el
  repositorio **no tiene remoto**, no hay push posible.
- **R23**: `git diff dev...HEAD -- services/` vacío.
- **Fidelidad a sv5** (leído en sv5): `COALESCE(precio_neto, cantidad × precio × (1 − dto/100))`,
  `descuento`/`precio_neto` de `RawAlbaranLine`, `extract(…, contrato_markdown=…)` y MD > PDF con
  el tope de `ValueAlbaranPipeline` coinciden con el banco.

## Desviaciones declaradas

- **D1 · aceptada en el código, falta la spec.** Defecto = referencia IA3 de
  `evals/precios_modelos.json` (`openai` / `gpt-6.1-sol`, comprobado): cumple P6 = (a) y el OBJETIVO
  («línea base con el modelo de producción»). R20, R28, design §9 y T14 siguen diciendo
  `claude-opus-4-8`, y T14 es de pago → cambio 3.
- **D2 · aceptada.** Los tests de F-083 pasan a RES-001/004/006 con la misma intención; el doble de
  F-048 solo acepta `**_`. Ninguna expectativa cambia.
- **D3 · aceptada.** F-084 no toca `afirmado_por_el_humano_RES.json`; lo cambió `dev` (banco IA1
  confirmado por el humano), solo en claves `IA1.*`. El guardián fija las 419 de fuera de IA1.

## Mutación (C4 bis)

- **Recálculo puro** (`harness.alcance.parsear_diff` + `filtrar_produccion` + `generar_mutantes`
  sobre cada SHA): 2.ª campaña `ac34ad8..d4dbe97` → **1540 líneas, 198 mutantes**; remedida de
  `sv5_documentos.py` en `3ce021f` → **286 líneas, 39 mutantes**. Coinciden. Los 4 supervivientes
  de la 2.ª (línea 222 ×3, 274) existen con el mismo operador y texto original → mutado.
- **Campaña no reejecutada**: 19.300,7 s y 4.533,4 s según los informes (> 60 s).
- Coste por mutante (total × 4 ÷ mutantes): 390 s y 465 s frente a líneas base de 474–492 s y
  526–544 s; coherente con `-x`. **RM2** [x]. Sin «NO VÁLIDA», sin veredicto = 0.
- **RM1** [x]: desde `d4dbe97` solo cambió `sv5_documentos.py` en el alcance, remedido en `3ce021f`;
  desde ahí nada del alcance cambia (`dev` trae `comparador.py`, fixtures y tests ajenos).
- **RM3** [x] ningún equivalente sale muerto. **RM5** N/A justificado: no queda ningún equivalente
  declarado; los 4 dejaron de serlo al reescribir (`d0f91b1`) y la remedida los mata. **RM6** [x]:
  no se quitó ninguna guarda (una condición partida en dos, un `ensure_ascii=False` inocuo).

## Checkpoints

- **C1** [x] init.sh exit 0 (tras recortar este informe) · [x] ficheros base.
- **C2** [x] una `in_progress` · [x] rama de la feature · [x] `current.md` según la práctica · [x] historia.
- **C3** [x] hexagonal N/A dentro de `evals/` (herramienta, design §6), sv5 intacto · [x] primera
  línea con ruta · [x] los `print` son salida de CLI (como `runner.py`), sin secretos ni
  dependencias nuevas · [x] trampas: lee el merge, sin schema, importes en `Decimal`.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4** [x] trazabilidad · [x] sin red ni BBDD (`MockTransport`, dobles, LLM doble en subproceso,
  `tmp_path`) · **[ ] MANUAL T12/T14 sin su comando en `progress/current.md`** (cambio 2).
- **C4 bis** [x] rigor · [x] RED real T1–T9 (T11, guardián, N/A justificado) · [x] cobertura `[OK]`
  98,5 % · [x] mutación verificada · [x] muertos: recálculo puro · [x] coste por mutante · [x] RM1
  · [x] RM2 · RM5 N/A · [x] RM6 · manual N/A (la automática dio 198 y 39) · [x] sin pendientes ·
  [x] «Evidencias» con 4 workers · [x] ningún N/A sin motivo.
- **C4 ter** N/A: la puerta no señala rutas sensibles.
- **C5** [x] T1–T11 y T15 `[x]` con commit `F-084 Tn:`; T12–T14 pendientes, como pide el líder ·
  [x] sin temporales · [x] `features.json` `in_progress`, rama, `servicios = evals`.

## Cobertura: requisito → test

| Req | Test (o verificación) |
|---|---|
| R1–R11 | `tests/test_f084_contratos.py::test_f084_r1_*` … `r11_*` (R3 ×3 variables, R4 truncado y HTTP 500) |
| R29–R31, R34 | `test_f084_r29_*` (SQL de sv5, MD > PDF), `r30_*`, `r31_*`, `r34_*` (solo lectura, `env`) |
| R12–R17, R32 | `tests/test_f084_contexto_valoracion.py::test_f084_r12_*` (FER-001 19,41) … `r17_*`, `r32_*` y el subproceso de sv5 con doble |
| R33 | `test_f084_r33_*` (contexto y runner) |
| R18–R21, R36 | `tests/test_f084_runner.py::test_f084_r18_*` … `r21_*`, `r36_*` |
| R24 | `test_f084_r24_*` |
| R23, R25, R26 | Revisión: diff de `services/` vacío, tests sin red, `evals/README.md` |
| R27, R28 | MANUAL T12 → T13 y T14, pendientes |

## Cambios requeridos

1. **(Antes de T13) R33 en el determinista dejará la suite en rojo en todo árbol sin la caché.**
   `evals/runner.py:192` aplica `motivo_para_omitir` (R18 **y R33**) en la corrida determinista,
   que no usa el documento. Cuando T13 versione `evals/fixtures/contratos/_indice.json`, todo árbol
   sin `evals/inputs/contratos/` (`dev` sin la copia manual, cualquier worktree nuevo) verá los RES
   OMITIDO, y caen `test_f084_r24_el_determinista_de_los_7_res_no_empeora` (afirma que ninguno sale
   OMITIDO) y los dos de F-083 de D2. **Reproducido**: copia de los fixtures con un índice `md` para
   el contrato de RES-001 → IA3/IA4/E2E `OMITIDO · documento del contrato no disponible en local`.
   En el worktree de F-084 sí está la caché, así que el init.sh de T13 no lo vería. Igual con
   `construir_contexto` sin índice explícito (lee el versionado), que usa el comparador de F-083.
   Es de diseño (design §4 pone R33 en las dos corridas): (a) R33 solo con LLM y en el comparador,
   o (b) los tests sobre fixtures reales con índice vacío o aislado. Que decidan líder y humano, se
   ajusten design §4 y R33, y un test lo fije **sin** caché.
2. **(Antes de T13) C4:** listar en `progress/current.md` las MANUAL T12 y T14 con su comando exacto
   (el bloque de `impl_F-084.md` §«MANUAL del humano»), como en F-083 y F-085.
3. **(Antes de T14) D1 en la spec:** R20 («o `claude`»), R28 (`claude-opus-4-8`), design §9 y T14 al
   modelo de producción (`gpt-6.1-sol`), y que el humano confirme el modelo de la línea base de pago.
   Hoy `test_f084_r20_*` afirma lo contrario del literal de R20.

## Observaciones (no bloquean)

- **O1.** T12 usa `PG_USER = $PG_ADMIN`. Solo hay `SELECT` y la sesión es de solo lectura, pero
  eso es un defecto de sesión, no un permiso: si hay usuario de lectura, mejor ese (design §9).
- **O2.** `00_capps_vars.ps1` llama a `az identity show` (lectura): T12 necesita `az login`.
- **O3.** En T13 el índice versiona `nombre_proveedor`/`cif_proveedor` (R30): si algún proveedor es
  persona física, son datos personales. Que el humano repase el índice antes del commit.
- **O4.** R16: en los 52 casos importados solo entra `fecha_albaran` (R9); `numero_albaran` sigue
  vacío salvo en los RES. La spec no pide más.
- **O5.** La `description` de F-084 aún dice `evals/contratos_sigrid.py` y «estímulo por precio
  único» (anterior a la PARADA 1). Limpiarla en T13.

## Automejora (propuesta, no aplicada)

`CHECKPOINTS.md` C4: «si la feature versiona algo que hace depender la corrida de ficheros locales
no versionados (cachés, documentos), un test la ejecuta **sin** ellos y la suite sigue en verde en
un clon limpio».
