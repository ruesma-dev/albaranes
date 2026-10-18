# F-075 · Informe del implementer (2026-10-18)

Rama `feature/F-075-importe-leido`, worktree `C:\Users\pgris\PycharmProjects\albaranes-F-075`. Spec v2 (PARADA 1 v2
aprobada el 2026-10-15) **más el ajuste del humano del 2026-10-18** (opción A y M1, §1). Rigor `critico`.
**Estado: T1–T16 y T19 hechas; pendientes del humano T0 (opcional), T17 (evals con LLM) y T18 (despliegue).**
Detalle de la fase RED: `progress/impl_F-075_red.md`. Mutación: `progress/mutacion_F-075.md`.

## 1. Bloqueo previo y decisión del humano

Antes de T1 la rama quedó `blocked` (`44a050f`): el sobre `no_contract` de sv5 (`_raw_albaran_line_to_dict`) no
llevaba `precio_neto_albaran` ni `descuento_albaran`. Por eso la valoración directa no se habría disparado nunca, y la
spec daba por hecho que sv5 no cambiaba. El humano decidió el 2026-10-18:

- **Opción A**: sv5 añade esas dos claves (R5 bis). El despliegue pasa a comun → sv3 → sv5 → sv6 → sv4.
- **M1**: sv3 solo publica sin contrato cuando el contrato seleccionado es nulo. Con contrato seleccionado y 0 líneas,
  SKIP como hasta ahora.

La spec está ajustada en `cb54d23` (R3, R4, R5 bis, design §1/§3/§6/§10/§11, T1b y T18). `servicios` incluye sv5.

## 2. Fusiones de `dev`

- `a3c9e6a` → `155868e`. Solo hubo conflictos de texto (`features.json` y `current.md`), y se conservó todo lo de
  `dev`.
- `bee817d` → ``256871e``. Es solo `infra/manifests/sv6/requirements.txt` (tenacity) y no tuvo conflictos.

El contraste de la spec con `dev` está en §2–§3 del informe anterior (`git show 44a050f:progress/impl_F-075.md`). Encaja
con F-078 (`completar_registros`), F-076 (`anotar`, partida normalizada), F-077 R11, F-078 R17, F-053 R37 y F-064.

## 3. Qué cambió (un commit por tarea, `f1c3a45`…`d33f009` y T16)

| T | Servicio | Ficheros de producción | Qué |
|---|---|---|---|
| T1 | comun | `ruesma_comun/importes.py` | `ImporteAlbaran`, `importe_albaran`, `difieren`, `ComparacionPie`, `referencia_pie`, `pie_cuadra` y `unitario_despejado` (R1, R2, R6) |
| T1b | sv5 | `value_albaran_pipeline.py` | El sobre `no_contract` lleva `precio_neto_albaran` y `descuento_albaran` (R5 bis) |
| T2–T4 | sv6 | `valoracion_directa.py` (nuevo), `run_valuation_pipeline.py` | `ValoracionDirectaBuilder`; la rama `no_contract` lo usa y pasa por `completar_registros` + `anotar`; `anotar_valorado_distinto` tras el builder con contrato (R5–R12) |
| T5 | sv3 | `persist_albaran_pipeline.py`, `sqlalchemy_albaran_repository.py` (`importes_leidos`), puerto | Disparo sin contrato con importes; M1; best-effort (R3, R4) |
| T6–T8, T13 | sv4 | `review_models.py`, `review_repository.py`, `app.py`, `app.js`, 4 plantillas, `styles.css` | Columna «Importe», orden, filtro, tarjeta, Obras/Proveedores con SQL portable; ficha con importe, pie, valorado y diferencia; «Valorar ahora» sin contrato (R9, R10, R19–R25) |
| T9 | sv9 | — (solo tests) | Contrato del alta de una valoración directa (R26) |
| T10–T11 | sv3 | ORM, `phase2_ddl.py`, `extraction_models.py`, normalizador, `_HEADER_CONFIGS`, `pie_guard_service.py` (nuevo), `settings.py`, `composition.py`, `api/app.py` | Pie en las dos tablas y `PieGuardService` en los tres puntos del pipeline (R15–R18) |
| T12 | sv2 | `albaran_models.py`, `prompts.yaml`, `phase_merge.py` | Pie en `CabeceraAlbaran`, sección «## Pie del albarán» en IA1 y conservación del pie de fase 1 (R13, R14) |
| T14 | evals | `sv2_extraccion.py`, `runner.py`, `informe.py`, `modelos.py`, `conversor.py`, `criticidad.json`, `sv2_obra.py`, `sv2_proveedor.py` | Pie observable; «no medido» en el informe; comparadores de F-048 y F-064 sin el pie en su variante base (R27) |
| T15 | docs | `ARCHITECTURE.md` (regla 25), `sv2/3/4/5/6.md`; `azure-apps/albaranes.md` (`c5fd3b0`, sin push) | — |

Hay tres tests de otras features ajustados (justificado en §4): `test_f064_prompt_ia2_proveedor.py` (lista de campos de
R11), `test_f064_comparar_proveedor_base.py` (R11 compara sin el pie) y `test_f064_comparar_proveedor.py` (`sin_pie`
explícito).

## 4. Decisiones de diseño y desviaciones (justificadas)

- **sv6 · `precio_unitario_source`** (design §5 deja elegir entre los `Literal` que ya existen):
  - `albaran_declared` si hay unitario leído distinto de 0;
  - `albaran_calculated` si el unitario se despeja del importe;
  - `none` si no hay ninguno de los dos.

  Un unitario 0 cuenta como ausente, como en `PriceReconciler`.
- **sv6 · `partida_action`**: `new_line_created` si hay partida impresa (se crea su derivada) y `almacen_sin_partida`
  si no la hay (F-051).
- **sv6 · resto de campos de la línea**:
  - `unidad_category_match=True`, porque la unidad es la misma y el factor es 1;
  - `codigo_producto=None` en la derivada, como hace sv4: sv9 elige el producto por familia;
  - si alguna línea va a revisión, la cabecera lleva también `at_least_one_line_requires_review`, como el builder;
  - `total_valorado` se redondea a 2 decimales, como `ValuationBuilder`.
- **sv6 · ubicación del código nuevo**: `_persistir_directa` está al final de la clase. Así la convención de F-076
  `test_f076_t10_…` (la primera aparición de `lines = completar_registros(` va antes de `anotar`) sigue valiendo, y la
  de F-078 se cumple con `directas = completar_registros(…)`.
- **comun · `unitario_despejado`**: es nuevo. R6 pide «el despejado del importe (`ruesma_comun.importes`)». No se toca
  `PriceReconciler`, que es de sv6 y está fuera de alcance. `pie_cuadra` devuelve también la referencia cuando la suma
  es nula, para que se pueda pintar.
- **sv3 · peso del pie en `_HEADER_CONFIGS`**: es 0, no un «peso bajo». Es la única forma de cumplir «no cambian la
  confianza de hoy», porque `_weighted_average` ignora los pesos 0. Hay un test con un conflicto entre IAs que lo fija.
- **sv3 · prefijo de la nota**: es el literal de R16, «[AVISO] La suma de las líneas no cuadra con el pie del
  albarán», y no el «[AVISO] Pie» del design. Manda el requisito, y el texto añade «puede ser un albarán de varias
  páginas» (v2-P5).
- **sv3 · interruptores y retirada**:
  - `PIE_GUARD_ENABLED` (defecto `true`) es un interruptor de vuelta atrás, como `FECHA_GUARD_ENABLED`;
  - al retirar el motivo, `review_required` no baja, como `retirar_motivos_proveedor`;
  - `importes_leidos` va en el puerto con un cuerpo que lanza `NotImplementedError` y no como abstracto, para no romper
    los dobles de otros tests: sin ese método, el disparo no publica.
- **sv4 · qué es «valorado»**: una valoración **sin filas** (la cabecera `no_contract` vacía) no cuenta como valorado.
  Se pinta «—» y no «0,00 € contrato». Las sumas no cambian, porque esa cabecera vale 0.
- **sv4 · la columna**: se reutiliza `data-col="importe"`, así que el orden de columnas que cada usuario tenía guardado
  sigue valiendo. Si falla la consulta del importe (R25), toda la columna pinta «—»; enseñar el valorado como
  «contrato» sin saber si el albarán trae importes contradiría «manda el albarán».
- **sv4 · la ficha no recalcula la tolerancia**:
  - `no_cuadra` sale del motivo que pone sv3;
  - sin ese motivo, es `no_comparable` si no hay suma o referencia, y `cuadra` en otro caso;
  - el pie se lee con un SELECT defensivo dentro de un SAVEPOINT, para no abortar la transacción de la ficha en
    PostgreSQL.
- **sv4 · Obras y Proveedores**: el campo `importe_valorado` pasa a llamarse `importe` (ningún test lo usaba).
- **sv2 · sitio de la sección del pie**: va justo antes de «## Reglas generales para las líneas», detrás de toda la
  parte de cabecera (obras y correo). Así no se toca ninguna línea de F-064, y la regla de líneas «Evita subtotales,
  totales, IVA» sigue siendo coherente: la sección dice «El pie va a la cabecera, nunca como línea».
- **Tests de F-064 ajustados**:
  - R11 de F-064 fijaba que F-064 no añadía campos. F-075 los añade a propósito, así que la lista incluye el pie y la
    comparación con la base se hace sin él;
  - las variantes base de los comparadores de F-048 y F-064 recortan el pie, que la base no conoce (si no, pedirían al
    LLM un campo que el prompt de la base no explica);
  - `create_model` conserva ahora la docstring, que es la `description` del schema.
- **Sin cambios de interfaz**: el banner «Albarán valorado · Contrato aplicado: —» no cambia para la valoración
  directa, porque ningún requisito lo pide.

## 5. Fase RED (requisitos centrales; trazas íntegras en `progress/impl_F-075_red.md`)

Cada tarea con código se escribió test primero. Comando y última línea del fallo:

| T | Comando (desde la carpeta del servicio, `PYTHONPATH` = comun del worktree) | Fallo real |
|---|---|---|
| T1 comun | `pytest tests/test_f075_importes.py` | `ImportError: cannot import name 'ComparacionPie' from 'ruesma_comun.importes'` · 1 error |
| T1b sv5 | `pytest tests/test_f075_no_contract.py` | `KeyError: 'precio_neto_albaran'` · 3 failed |
| T2 sv6 | `pytest tests/test_f075_valoracion_directa.py -k "r5 or r6 or r7 or r8 or r9"` | `ModuleNotFoundError: No module named 'application.services.valoracion_directa'` |
| T3 sv6 | `… -k pipeline` | `where None = ValuationHeaderRecord(…status='no_contract'…).prompt_key` · 3 failed, 2 passed |
| T4 sv6 | `… -k r12` | `assert 'valorado_distinto_de_albaran:30.00!=20.00' in ['at_least_one_line_requires_review', 'lines_without_match:1']` · 3 failed |
| T5 sv3 | `pytest tests/test_f075_disparo.py` | `assert [] == [('dfdc8aab-0..., None, True)]` · 3 failed, 5 passed |
| T6 sv4 | `pytest tests/test_f075_bandeja.py tests/test_f075_vistas.py` | `'DocumentListItem' object has no attribute 'importe_mostrado'`; `assert 0.0 == 350.0` · 14 failed |
| T7 sv4 | `pytest tests/test_f075_ficha.py` | `no attribute 'importe_leido'`; `no se pinta el bloque del importe` · 10 failed, 7 passed |
| T8 sv4 | `… -k r10` | `{"detail":"El documento no tiene contrato seleccionado…"}` `assert 409 == 200` · 4 failed |
| T10 sv3 | `pytest tests/test_f075_pie.py -k r15` | `KeyError: 'base_imponible'`; `Extra inputs are not permitted` |
| T11 sv3 | `… -k "r16 or r17 or r18"` | `No module named 'application.services.pie_guard_service'` · 15 failed |
| T12 sv2 | `pytest tests/test_f075_pie_ia1.py` | `Extra inputs are not permitted`; `no está la sección «## Pie del albarán»` · 7 failed, 8 passed |
| T13 sv4 | `… -k pie` | `no attribute 'pie_comparacion'`; `'Albarán 100,...orado 70,00 €' == '… Pie 110,00 €'` · 14 failed |
| T14 raíz | `pytest tests/test_f075_evals.py` | `assert 'base_imponible' in (…)`; `no attribute 'campos_no_medidos'` · 7 failed |
| T14 bis/ter | suite de la raíz | F-048 y F-064: `json.dumps(schema)` distinto (la base no conoce el pie) · 1 y 6 failed |

Después de cada tarea, el test va en verde y la suite del servicio también (§7).

## 6. Mutación (T16)

- Campaña completa de la herramienta (nivel `critico`, sin muestreo), 4 workers, sobre `d33f009`: 28 ficheros y
  1244 líneas, **175 mutantes, 153 muertos, 22 supervivientes, 0 timeouts, 0 sin veredicto, 5586,7 s**
  (`progress/mutacion_F-075_arnes.md`).
- Los 22, analizados uno a uno en `progress/mutacion_F-075.md`: 18 eran huecos de test (tests nuevos en `efda093`)
  y 4 desaparecen al simplificar el código (`sin_pie` keyword obligatoria; `importes_doc.get(…, sin_lineas)`).
  Re-juicio a mano de los 18 (suite entera del servicio, sin `-x`): **18 de 18 muertos**.
- **Total: 175 mutantes, 171 muertos, 4 desaparecidos, 0 supervivientes, 0 equivalentes.** Inventario de F-039
  con las dos filas nuevas.

## 7. `bash harness/init.sh` y verificaciones

`bash harness/init.sh` tal cual (Git Bash, `PYTHONPATH` a la comun del worktree), sobre `256871e` (T16 + `dev`
`bee817d`): **`ENTORNO LISTO. Puedes trabajar.`**, código 0. Repetido tras el último commit (lint de los ficheros
nuevos y este informe): ver la última línea de §Evidencias.

- Avisos que no bloquean: features `blocked` (de otras), ruff (deuda previa; los ficheros NUEVOS de F-075 quedan sin
  avisos de orden de imports, `noqa` sobrantes ni f-strings vacías tras `ruff --fix` acotado), infra sin tests,
  marcas `[ADAPTAR]` de F-034/F-035 y **PUERTA RUTAS SENSIBLES [evals]** (aviso): pide la pasada completa con LLM por
  `prompts.yaml`, `albaran_models.py` y `valoracion_directa.py`; es la T17 del humano (§8).
- Evals deterministas (`python -m evals.runner --feature F-075`, sin LLM): tabla de casos **idéntica** a la de `dev`
  (`diff` vacío); IA3 y E2E en ROJO también en `dev` (deuda del banco), IA4 VERDE.
- La valoración directa, la bandeja y la ficha están probadas con el repositorio real sobre SQLite y con la plantilla
  renderizada; **no** se ha probado en pantalla ni contra Azure (no se toca producción): es la comprobación de T18.

## 8. MANUAL del humano (PowerShell; lo que escribe va marcado)

Todo desde **PowerShell 5.1**, tras el APPROVED del reviewer, salvo T0 (solo lectura).

**T0 (opcional, SOLO LECTURA)**: consultas de los Anexos A y B de `progress/spec_F-075.md` contra la BBDD
`albaranes` (sesión con `default_transaction_read_only=on`). Anotar en `progress/spec_F-075.md` §v2.2.

**T17 · evals con LLM** (se facturan ≈ 190 llamadas, como en F-064 T10). En el worktree, antes de fusionar:
```powershell
Copy-Item -Recurse C:\Users\pgris\PycharmProjects\albaranes\evals\inputs C:\Users\pgris\PycharmProjects\albaranes-F-075\evals\inputs
cd C:\Users\pgris\PycharmProjects\albaranes-F-075
$env:PYTHONPATH = "C:\Users\pgris\PycharmProjects\albaranes-F-075\services\albaranes-comun"
$s = Read-Host "GEMINI_API_KEY" -AsSecureString
$env:GEMINI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
$s = Read-Host "OPENAI_API_KEY" -AsSecureString
$env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
& C:\Users\pgris\PycharmProjects\albaranes\.venv\Scripts\python.exe -m evals.runner --con-llm --feature F-075
Remove-Item env:GEMINI_API_KEY, env:OPENAI_API_KEY, env:PYTHONPATH
```
Criterio de verde (el banco está en ROJO de base, `VERDE` literal no es alcanzable): en `progress/evals_F-075.md`,
`MODO: completa` y `FASES: IA1,IA2,IA3,IA4,E2E`; **IA1 ≤ 154 e IA2 ≤ 4 fallos críticos** (F-064 T10: 152 y 2), la
sección «Campos no medidos» con los cuatro del pie, e IA3/IA4/E2E iguales a la pasada determinista (que es idéntica
a `dev`, §7). El aviso de la puerta de rutas sensibles (`prompts.yaml`, `albaran_models.py`, `valoracion_directa.py`)
se cierra con ese informe.

**T18 · despliegue** (tras fusionar en `dev` e `init.sh` en verde en el árbol principal). Cada `deploy.ps1` es
**[ESCRIBE EN PRODUCCIÓN · humano]**; lo demás solo lee. Orden: sv3 (DDL y disparo) → sv5 → sv6 → sv4 → sv2 (sv3
rechazaría la cabecera con el pie si sv2 saliera antes). sv9 no se redespliega; `ALTA_SIGRID_COMMIT` sigue `false`.
```powershell
cd C:\Users\pgris\PycharmProjects\albaranes\infra
. .\00_vars.ps1
. .\00_capps_vars.ps1
foreach ($a in "ca-sv3-persistencia","ca-sv5-valuation","ca-sv6-valorador","ca-sv4-front","ca-sv2-extraccion") { az containerapp show -n $a -g $RG --query "properties.template.containers[0].image" -o tsv }
.\deploy.ps1 -Only sv3
.\check_deploy.ps1
.\deploy.ps1 -Only sv5
.\check_deploy.ps1
.\deploy.ps1 -Only sv6
.\check_deploy.ps1
.\deploy.ps1 -Only sv4
.\check_deploy.ps1
.\deploy.ps1 -Only sv2
.\check_deploy.ps1
```
VERDE de cada paso: `check_deploy.ps1` con el servicio en el tag nuevo y réplicas arriba (la primera línea apunta
las imágenes actuales por si hay que volver atrás). Comprobación en pantalla: en sv4, ficha de uno de los merges de
DISCOIN (`dfdc8aab-08e1-49f0-978d-bb906515e748`) → «Valorar ahora» **[ESCRIBE EN PRODUCCIÓN · humano: reemplaza su
valoración]** → valoración directa, bandeja con «Importe» y rótulo «albarán · sin IVA», «Aprobar» habilitado si todas
las líneas traen importe; aprobar **[ESCRIBE EN PRODUCCIÓN · humano]** y ver el alta `simulado` en el panel de F-053.
Antes de `ALTA_SIGRID_COMMIT=true`, revisar en simulación 3 altas directas (D6: analítica `<obra>.<sufijo>`).

## 9. Qué falta y qué queda fuera

- Review (reviewer) contra `CHECKPOINTS.md`; fusionar en `dev` e `init.sh` en el árbol principal; T17 y T18 (§8).
- Antes de `git worktree remove`, quitar la *junction* `services\albaranes-front\.venv` con `cmd /c rmdir`.
- Fuera de alcance (spec): valorar sin contrato los albaranes sin importes, quitar las sintéticas con contrato,
  aprobación automática, el backfill por script (v2-P6: «Revalorar» uno a uno, R10) y F-066 X12.

## Evidencias

| Evidencia | Valor (medido, `init.sh` sobre `256871e`) |
|---|---|
| Tests ejecutados | raíz 1328; sv1 205; sv2 485; sv3 1538; sv4 1771 (1 warning); sv5 46; sv6 471 (+1 skipped); sv9 673; comun 859 (+3 skipped). **0 fallos** |
| Tests nuevos de F-075 (casos recogidos) | comun 41, sv5 3, sv6 27, sv3 42 (disparo 8, pie 34), sv4 56, sv2 17, sv9 3, raíz 11 |
| Cobertura de las líneas cambiadas | **98,1 %** (463/472), umbral 80 %, nivel `critico` (`PUERTA COBERTURA`) |
| Mutantes | **175 generados, 171 muertos, 4 desaparecidos, 0 supervivientes** (tras el re-juicio; herramienta: 153 / 22) |
| Tiempo de la suite | raíz 193,6 s; sv4 165,0 s; comun 121,4 s; sv1 41,4 s; sv9 35,5 s; sv2 24,5 s; sv3 20,1 s; sv6 13,4 s; sv5 2,6 s |
| Fase RED | 15 trazas (T1–T14 ter) en §5 y `progress/impl_F-075_red.md` |
| `init.sh` final | ULTIMO_INIT |
