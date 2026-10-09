Revisión incremental desde `44d5d86` (fase 2, pasada 2): `44d5d86..c5ed909`. La pasada 1, abajo, fue desde `e4f57fb`
<!-- progress/review_F-053_fase2.md -->
# Review F-053 · fase 2 · reviewer, 2026-10-09

## Pasada 2 · veredicto: APPROVED (fase 2)

El delta arregla el único cambio requerido (RM5) y además O3 y O5. No toca código de producción: `6e29784` solo
añade tests y la línea «Demostración:», así que la campaña sigue valiendo (RM1). Restricción de máquina igual que en
la pasada 1: solo ficheros sueltos, uno por pytest.
- **[x] RM5.** sv9 `tests/test_f053_t25_equivalentes.py` (#1–#7) da **7 passed** y sv3 (#8–#10) **3 passed**. Cada
  test carga el módulo REAL y fabrica la variante sustituyendo el texto. Antes normaliza la fuente, así que un
  equivalente inyectado no sale muerto (RM3). Los dominios son amplios: #1, 2688 escenarios del servicio; #2 y #3,
  3000 lotes; #4–#6, 338 casos por `validar_y_construir`; #7, 76 entradas; #8–#10, 1644 albaranes. Cada uno lleva un
  control no equivalente con `> 0`.
- **Lo comprobé falseando los tests en una COPIA del scratchpad** (el árbol quedó limpio): metí como «equivalente» un
  mutante que no lo es, y en los cinco casos el test **falla**. F1: #1 con el control como mutado. F2: #6 con
  `con_signo … importe < 1`; esto prueba además que la línea `:267` se ejercita. F3: #7 con `is not None`. F4: #2 y #3
  con `(-1, …)`. F5: sv3 con `(l.importe or 0) < 1`.
- **[x]** Las 10 secciones de `mutacion_F-053.md` enlazan su test por nombre (con su `[equivalente_N]`).
- **[x] O3**: el README pone `Set-DeployTag` antes del build de sv9. **[x] O5**: `current.md` ya no tiene los bloques
  «EN CURSO» de F-062 y F-063.
- Sigue abierto para el cierre: O1 (humano, antes de T29), O2, O4, O6 y O7 (no bloquean), la aceptación del humano de
  los 10 equivalentes, T0d, T30 (`init.sh` en el árbol principal) y las MANUAL.

## Pasada 1 (`e4f57fb..97f70ce`)

**Veredicto de la pasada 1: CHANGES_REQUESTED**, solo por RM5: en `critico` cada equivalente trae demostración
ejecutable, y los 10 solo traían prosa. El código de la fase 2 está bien: las tres carreras usan dos sentencias y mis
controles las cazan, ninguna ruta manda `commit=true` sin el literal `true`, y los 10 equivalentes lo son.
Lo aprobado en la fase 1 (hasta `e4f57fb`) queda dado por bueno. Las fusiones `7ec02a6` y `d53d059` no tocan sv9 ni
R45 de sv3: `_conservar_por_alta` sigue en dos sentencias y `save` lo llama (`:840`).

**Rigor:** `critico` (declarado): fase RED, cobertura ≥ 80 %, cero supervivientes sin justificación aceptada por el
humano, RM5 y MANUAL con comando. **Restricción de máquina (encargo del líder).** F-064 tenía suites y mutación en
marcha: **no** ejecuté `init.sh`, suites completas, la campaña ni coverage global. Ahí me apoyo en el informe
(`impl_F-053_fase2.md` §10–§11), y lo digo en cada punto. Sí ejecuté, con `PYTHONPATH` a la comun del worktree:
- **Ficheros sueltos, uno por pytest, todos en verde:** sv4 `t19_cerrojo` 112, `t18_publicar` 16, `t21b_valorado` 32,
  `t20_rutas` 68; sv9 `t24b_reclamar` 3; comun `comun_fase2` 37.
- **Controles sobre una COPIA en el scratchpad (RM4; el árbol sigue limpio):** M1 sv4, `_exigir_desbloqueado` lee
  el alta ANTES del `FOR UPDATE` → `t19_cerrojo` **3 failed**; M2 sv4, `set_approved(False)` sin mirar el alta →
  **4 failed**; M3 sv4, `guardar_producto_sigrid` sin cerrojo → `t19b_producto` **4 failed**; M4 sv9, `reclamar` lee
  el alta antes del cerrojo → `t24b_reclamar` **3 failed**.

## Los seis puntos del encargo

1. **Seguridad de escritura · [x].**
   - Un solo `commit=True` a `sigrid/albaran` (`alta_sigrid_service.py:282`), detrás de `if SIMULACION: … return`
     (`:273`). El modo sale de `commit_real`, que es `== "true"` sin normalizar (`settings.py:152`).
   - El `"commit": True` de `concepto-grafico` (`sigrid_api_alta_client.py:244`) solo se usa en `REAL` (`:329`, `:390`).
   - sv4 solo publica en `q-feedback`. `create_capps_sv9.ps1:67-72` fija `COMMIT=false` y aborta si entra otro
     valor; `--max-replicas 1` y `--mode single`. `set_alta_sigrid.ps1:32` se niega a tocar `COMMIT`.
     `deploy.ps1:90-101` solo lo lee y actualiza con `--image`. Ningún otro script lo toca (`grep set-env-vars`).
   - Los tests no llaman a sigrid-api (`https://sigrid.invalid` y dobles). Barrido de secretos del diff limpio (GUID,
     IP, claves, `AccountKey`, `sig=`, `azurewebsites`): solo `ana@ruesma.es` (ficticio, tests) y `"x"` en dobles.
2. **Carreras · [x].**
   - **sv9 (T24b):** el cerrojo va sin `JOIN` (`sql_alta_repository.py:52-57`) y `SQL_LEER_ALTA` aparte (`:286-291`).
     `_COLUMNAS_ALTA` no trae `approved_*`, así que el cruce `{**merge, **alta}` no pisa nada.
   - **sv3 R45:** como en la fase 1 (`sqlalchemy_albaran_repository.py:69-75`, `:2278-2283`).
   - **sv4 `_exigir_desbloqueado`** (`review_repository.py:4241-4273`): primero el cerrojo, después el alta. El
     `session.get` posterior lee fresco: el cerrojo selecciona la columna `id`, no la entidad. Así `estaba_aprobado`
     sale de lo ya bloqueado y R2 no tiene carrera entre dos aprobaciones.
   - R26 cubre 13 métodos, `asignar_almacen` de F-051 incluido (`sellar_busqueda_contratos` y
     `replace_contratos_and_select` solo los usa el fallback local de solo-front). Revalorar y re-buscar miran el alta
     sin cerrojo (design §11). La carrera en PostgreSQL 16 es del informe §5; no la reproduje (máquina): T27c.
3. **Ni se pisa ni se casa con otro contrato · [x].** «Vinculada» exige el contrato de la valoración, con la misma
   función de comun en sv4 y sv9 (`es_linea_vinculada`). La casada con otro contrato es «sin vincular» y sv9 la manda
   a `revisar` (R46, fase 1). Las sin vincular siguen admisibles (R11). Con alta bloqueante, sv4 no edita, borra ni
   desaprueba, y sv3 no reingesta.
4. **Los 10 equivalentes · razonamiento [x]; demostración ejecutable [ ] (RM5).** Leídos contra el código: #1,
   `_guardar(REGISTRADO)` ya puso `paso.cerrado`; #2 y #3, la clave `(0,…)` frente a `(1|2,…)` conserva el orden y el
   tercer elemento es igual en todas; #4, #5 y #6, solo llega `|importe| > 1e-9` (ni 0, ni -0.0, ni NaN); #7, `None`
   y `""` caen en el mismo `except`; #8, #9 y #10, `con_importe` excluye el 0 y el nulo.
   - **Mi muestra (RM5), la #7:** la `_json` real frente a la mutada (`:162`, `or` → `and`), 17 entradas: **17/17
     IGUAL**.
5. **R30 y el adjunto en error · decisión pendiente del humano, no incumplimiento.** `registrado` no está en la lista
   de R30, y sv4 la cumple al pie de la letra; R23 describe a sv9, que lo hace (`SOLO_ADJUNTO`). Es un hueco entre R23
   y R30. Solo afecta al modo real: decidir **antes de T29** entre (a) añadir a R30 «`registrado` con adjunto en
   `error`» (barato) y (b) reintentar a mano.
6. **KO de `init.sh` en el worktree · de entorno, confirmado.** En los venvs de sv3 y sv4, `ruesma_comun.__file__`
   apunta al árbol principal, en `dev`, sin `alta_sigrid`, `valoracion` ni `configuracion`: de ahí los tres
   `ModuleNotFoundError` y la cobertura del 4,4 %. Con `PYTHONPATH` al worktree pasan. C1 N/A, como en la fase 1.

## Checkpoints

- **C1 · N/A justificado** (punto 6). Se exige en T30. Los ficheros de C1 existen.
- **C2 · [x].** Solo F-053 está `in_progress` y la rama es la correcta. `current.md` arrastra de `dev` bloques «EN
  CURSO» de F-062 y F-063, ya `done`: podarlos al cerrar (O5).
- **C3 · [x].** Hexagonal (lo puro en `domain/`, lo compartido en comun, el SQL en infraestructura), primera línea con
  la ruta, sin `print` ni TODO. Comun crece con `configuracion.py` y `alta_sigrid.py` (justificado en el informe §3).
  Lógica sobre las tablas merge, sin schema nuevo en esta fase y sin mezclar unidades.
- **C3 bis · [x].** `dominio_negocio_albaranes.md` (§5.2 y una fila) ya tenía cabecera de origen, fecha y redactado.
  Mi barrido de las líneas añadidas (GUID, `@dominio`, IPv4, `password|secret|token|apikey|key=|code=|sig=|Bearer|
  BEGIN KEY`) da **0**, y `git log --diff-filter=A` no encuentra ningún PDF ni fichero de ofimática.
- **C4 · [x].** Tests `test_f053_rN_*` por requisito: R1 5, R2 6, R3 6, R4 6, R25 5, R26 11, R27 6, R28 13, R29 10,
  R30 12, R31 3, R37 18, R38 13, R40 7, R41 20, R42 2, R43 3, R44 18. Sin red ni BBDD (sv4, SQLite en memoria, como
  F-051 y F-052). MANUAL con comando en `tasks.md`, citadas en `current.md`.
- **C4 bis.**
  - [x] `rigor` declarado. [x] Fase RED con salida real y controles negativos (informe §4).
  - [x] **Cobertura**, por evidencia: 96,2 % (1976/2054) medido por el implementer. No la remedí (máquina).
  - [x] **Mutación recalculada (cálculo puro):** **41 ficheros, 5148 líneas y 628 mutantes**, como el informe. Los
    **10 supervivientes existen** con su operador y su texto original → mutado.
  - [x] **Muertos:** el «Tiempo total» es 5625 s, más de 60 s: **campaña no reejecutada** (94 min según el informe;
    además, lo impedía la restricción de máquina). Valen el recálculo y RM1–RM6.
  - [x] **Coste por mutante:** 5625 × 1 ÷ 628 = **9,0 s**. [x] Sin «⚠ CAMPAÑA NO VÁLIDA», «Sin veredicto» a 0 y con
    línea base.
  - [x] **RM1.** Se midió en `7dad2a0`; después solo cambian `progress/` y `tasks.md`. Mi recálculo en HEAD da el
    mismo alcance.
  - [x] **RM2.** Media de 9,0 s (1 worker) frente a una base ponderada de **25,3 s**: 335 mutantes en sv9 (15,2 s),
    148 en sv4 (36,3 s), 103 en sv3 (6,7 s), 41 en comun (115,7 s) y 1 en sv6 (4,4 s). Ratio 0,36 con el 98 % muertos
    y `-x`, y 628 × 9,0 cuadra con el total.
  - [ ] **RM5** (cambio 1). [x] **RM6:** `5a01be3` y `7dad2a0` solo añaden tests; no quitan ninguna guarda.
  - N/A campaña manual (la automática generó 628). [x] Sin `PENDIENTE`; la aceptación del humano es del cierre.
  - [x] «Evidencias» con los cuatro números; 1 worker (§6 y el informe de mutación).
- **C4 ter · N/A.** No toca rutas sensibles.
- **C5 · [x] en el alcance de la fase.** T17–T25 y T24b `[x]`, un commit `F-053 Tn` por tarea (T18 y T19 juntas,
  justificado en §3). T0d, T30 y las MANUAL son del cierre. Árbol limpio (`coverage.json` y `__pycache__`, ignorados).

## Cambios requeridos (pasada 1; resueltos en la pasada 2)

1. **RM5 · media.** Un test diferencial versionado por grupo de equivalentes, como F-048 (`7b8adab`): función real
   frente a variante mutada, dominio amplio y control no equivalente; cada sección de `mutacion_F-053.md`, enlazada.

## Observaciones (no bloquean)

- **O1.** R30 y el adjunto en error (punto 5): decide el humano antes de T29.
- **O2 · baja.** `set_approved(True)` sobre un documento ya aprobado reescribe `approved_at_utc` y `approved_by`
  aunque el alta sea bloqueante (`review_repository.py:4428-4430`); guardar con `approved=true` en estados no
  bloqueantes, igual (`:3475-3478`, ya existía). R25 no cubre «aprobar». Efecto: un aprobado antes de DESDE y vuelto
  a guardar pasa a ofrecer «Solicitar alta» (acción humana; R14 caza las altas a mano). Sugerencia: no tocarlo.
- **O3 · baja (resuelta en la pasada 2).** Faltaba `Set-DeployTag` antes de construir sv9 (`00_vars.ps1:97`).
- **O4 · informativa.** El wiring de `app.py` escribe en el log DESDE, la Espera y los productos: no es secreto (R35),
  pero el §7 del informe es inexacto. Los errores de `Settings` van sin valores (H1).
- **O5.** Podar los bloques heredados de `current.md` al cerrar. **O6 · cosmética.** `ruff` desde la raíz da 13
  `I001` en ficheros nuevos (desde cada servicio, limpio). **O7 · informativa.** Un `deploy.ps1` completo antes de
  crear sv9 da FALLO en sv9 y sigue con sv4 (DESDE vacía): es seguro.

**Automejora (no aplicada; `CHECKPOINTS.md` RM5 y `arnes-base`):** en `critico`, que `harness.mutacion` exija una
línea `Demostración: <test>` en cada equivalente y que `init.sh` avise si falta.
