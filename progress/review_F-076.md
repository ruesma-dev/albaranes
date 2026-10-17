<!-- progress/review_F-076.md -->
Revisión incremental desde bceff77 (pasada 2) · delta `bceff77..4471d72`; pasada 1 completa en `febcaf0`

# F-076 · Normalizar partidas contra las de la obra · Review (2026-10-17)

**Veredicto: APPROVED.** Los tres cambios de la pasada 1 están aplicados y el delta no toca código.

## Pasada 2 (incremental)

El delta `4471d72` solo toca `progress/current.md`, `progress/impl_F-076.md`, `harness/features.json` y `BACKLOG.md`
(más esta review): **cero código**. No invalida nada de lo aprobado en la pasada 1, que no se relee.

- **P2.1 · Orden (cambio 1).** La «Secuencia combinada F-078 + F-076» de `current.md` va así: 1 tenacity y lectura de
  F-078 T12; 2 `set_partidas_sv6.ps1` y `deploy -Only sv6`; 3 relleno `--aplicar` y relectura; 4 `deploy -Only sv4` y
  `check_deploy`; 5 relectura tras sv4; 6 F-078 T14; 7 F-076 T19 y el log de T18. Respeta **sv6 ⇒ relleno ⇒ sv4**, y
  los comandos y VERDE de F-078 coinciden literalmente con su bloque.
- **P2.2 · Pegable en PowerShell 5.1.** Cada paso lleva su `cd` absoluto, sin `&&`, ternarios ni here-strings. Hay
  dot-source de `00_vars`/`00_capps_vars` en la misma consola, con lo que `$RG` sirve después para el log, y los
  comentarios `#` son inertes. Cada paso trae su `VERDE:`, y el texto dice «si un paso no da su VERDE, para ahí».
  Observación, no bloquea: está todo en un único bloque de código, y pegarlo entero de una vez ejecutaría el `--aplicar`
  aunque el paso 2 hubiera fallado; el humano debe pegarlo paso a paso, como dice el texto.
- **P2.3 · Nota simétrica en F-078.** «Con F-076 fusionada en `dev` … usa la secuencia combinada»; el bloque suelto vale
  solo si F-078 se despliega antes. Es coherente con la secuencia y no la contradice. `impl` §6 queda como puntero a
  `current.md`, única copia.
- **P2.4 · `features.json` (cambio 2).** La `description` dice «spec APROBADA el 2026-10-16: P1–P11 por defecto y
  ampliación R23–R25». Se conserva la etiqueta «PROPUESTA:» delante del resumen técnico, que se lee como el contenido de
  la propuesta aprobada: aceptable. `BACKLOG.md` regenerado («al día»).
- **P2.5 · `Remove-Item` (cambio 3).** Está justo después de `-m scripts.medir_f076_partidas` en T19, que la secuencia
  ejecuta en el paso 7.
- **P2.6 · `init.sh`.** Git Bash, mismo `PYTHONPATH` (comun del worktree) ⇒ **exit 0, «ENTORNO LISTO»**. Raíz 1237
  passed. Los 8 servicios salen verdes por la caché de suite: el verde es el de la pasada 1, sin caché y en serie, y
  desde entonces no ha cambiado ningún fichero de servicio. `COBERTURA` [OK] 97,3 %; `TAMAÑO` [OK].

Checkpoints que estaban en `[ ]` y ahora pasan a `[x]`: C4 (MANUAL) y C5 (`features.json`). El resto, como en la
pasada 1.

# Pasada 1 (completa, `bceff77`), resumida

## 1. Verificación ejecutada (resultados reales)

- **`bash harness/init.sh`** (Git Bash, `PYTHONPATH` = comun del worktree, `ARNES_SIN_CACHE=1`: suites en serie y sin
  caché) ⇒ **exit 0, «ENTORNO LISTO»**. Raíz 1237; sv1 205; sv2 397; sv3 703; **sv4 1549**; sv5 43; **sv6 444 + 1
  skipped**; **sv9 670**; **comun 818 + 3 skipped**. `PUERTA COBERTURA` [OK] 97,3 % (583/599, umbral 80 %); `TAMAÑO`
  [OK]. Avisos ajenos o previstos: F-078 `blocked`, ruff, infra sin tests, rutas sensibles [evals], [ADAPTAR].
- **Test saltado de `app.py`**: lo ejecuté sobre una copia de sv6 en el scratchpad con un intérprete con FastAPI (venv
  de sv4 + tenacity/yaml en el `PYTHONPATH`): `test_f076_cableado.py` **8 passed**, incluido el saltado.
- **Evals deterministas** (`python -m evals.runner --feature F-076`, sin LLM ni red, salida al scratchpad): ROJO, pero
  **idéntico línea a línea** al mismo comando sobre `dev` (`a8b9f7d`): sin regresión. `git status` limpio después.

## 2. Las 10 desviaciones de `impl_F-076.md` §2

Todas caben en la spec aprobada; ninguna exige volver al humano. La tabla con el juicio de cada una está en la pasada 1
(`git show febcaf0:progress/review_F-076.md`, §2): #1 manda R11, #2 es R5 literal, #7 es consecuencia de P7 y #9 no deja
hueco (el test saltado lo ejecuté con FastAPI: 8 passed).

## 3. Puntos expresos del líder

**Fusión con F-078 en sv6.** Un único `replace_valuation` con líneas, que recibe `lines = completar_registros(...)`;
`test_f078_pipeline_todo_replace_valuation_con_lineas_va_tras_completar_registros` sigue vivo y verde. Orden:
normalizar ⇒ `no_contract` ⇒ IA4 ⇒ `build` ⇒ `completar_registros` ⇒ `anotar` (en su sitio, sin reasignar `lines`) ⇒
`replace_valuation`; lo fija `test_f076_t10_...`. `anotar` solo toca `codigo_partida_albaran`, `review_reasons` y
`review_required`, y `completar_registro` no lee la partida: descripción, unidad y cantidad de F-078 intactas.

**Seguridad e infra.**
- `set_partidas_sv6.ps1`: grep 0 GUID/URL/`subscriptions/`/secretos (todo de `00_vars`/`00_capps_vars`);
  `secretref:sigrid-key` sobre `keyvaultref`; idempotente (`secret set`, `--set-env-vars`); comprobación OK/KO; UTF-8
  BOM y CRLF; `deploy.ps1` (`update --image`) conserva las variables.
- `SigridApiLector`: solo `RUTA_SQL_READ`; el log lleva etiqueta, estado, filas, `base_url` y `database`, nunca la
  clave ni el cuerpo (test con `caplog`; `__repr__` sin clave).
- Script de medición: sesión `default_transaction_read_only=on` comprobada con `SHOW` antes de leer; un SELECT;
  `NO_TOLERA`; solo recuentos; errores sin detalle.
- `.env` de sv3 en T19: **aceptable**. La regla protege de modificarlo o subirlo; aquí no se modifica, no se imprime
  y no sale de la consola del humano. Falta limpiar las variables al terminar (cambio 3).

**Rutas sensibles [evals].** Exigencia `aviso`; motivo documentado en P8, `impl` §5 y design §10. Las evals
deterministas existen y las ejecuté (§1), pero no pueden medir F-076: `evals/procesos/sv6_build.py` usa el
`ValuationBuilder` directamente, sin `RunValuationPipeline` ni la lista de la obra. No ejecutarlas no deja hueco; lo
que mide F-076 es T19.

**MANUAL T18–T20.** Los comandos de T18 y T19 son exactos (`current.md` = `impl` §6). **Fallo:** la combinación con
F-078 es una remisión («sigue el orden de F-078 … con estos mismos despliegues») y el bloque literal de T18 encadena
`deploy sv6` ⇒ `deploy sv4` sin el relleno `--aplicar` en medio. F-078 está `blocked` esperando sus MANUAL, así que el
caso combinado es el esperado: copiar el bloque tal cual rompe su orden obligatorio (sv6 ⇒ relleno ⇒ sv4). Cambio 1.

**Notas de solape** (`current.md`), correctas y suficientes: F-077 compone el `title` (✓ normalizada ⇒ nota F-076;
⚠ ⇒ aviso F-077) y ajusta su R22; F-075 llama a `anotar` tras `completar_registros`; F-049, add/add de `partidas.py`
conservando lo de F-076, comun 0.9.0.

## 4. Checkpoints

Rigor **`critico` declarado**: RED, cobertura ≥ 80 %, mutación completa con 0 supervivientes sin justificar, RM5.

- **C1**: [x] `init.sh` exit 0. [x] Arnés. **C2**: [x] Una `in_progress`. [x] Rama. [x] `current.md` (F-076 + el
  `blocked` vigente de F-078). [x] `history.md`.
- **C3**:
  - [x] Hexagonal: puertos en `domain/ports`; HTTP y SELECT en `infrastructure`; el dominio de sv4 solo importa la
    función pura `normalizar_partida`; `ruesma_comun.sigrid` sin E/S.
  - [x] Ruta en la primera línea. [x] `print` solo en el script (design §3). [x] Sin secretos. [x] Única dependencia
    nueva, prevista (R18).
  - [x] ARCHITECTURE: se lee el merge, no el raw; lector en la regla 3; sin schema ni importes; las sintéticas heredan
    la partida y no se anotan.
- **C3 bis**: N/A, no entra ningún documento externo.
- **C4**: [x] Trazabilidad (§4.1). [x] Unit tests sin red ni BBDD (`MockTransport`, SQLite en memoria, puertos
  falsos). [x] MANUAL con la secuencia combinada exacta (pasada 2, P2.1).
- **C4 bis**:
  - [x] `rigor` declarado. [x] RED real de los centrales (R5, R15, R23/24, R9/10, R7/8/14); T12 y T15 justificados
    (R16 «sin cambio», R22 no central). [x] Cobertura 97,3 %.
  - [x] Mutación 173/173 muertos, 0 supervivientes, sin «CAMPAÑA NO VÁLIDA», 0 sin veredicto.
  - [x] **Tiempo total 1242,2 s > 60 s: campaña no reejecutada (≈21 min según el informe).** Recálculo puro
    (`harness.alcance` + `generar_mutantes`): 17 ficheros, 1500 líneas, **173 mutantes**; coincide.
  - [x] Coste por mutante 1242,2 × 4 / 173 = 28,7 s.
  - [x] RM1: SHA medido `fdb9c58…`; después solo cambian `progress/` y `tasks.md`.
  - [x] RM2: 28,7 s frente a líneas base de 12,6 (sv6), ≈130 (comun) y ≈125 (sv4). Más de una décima; con 100 % de
    muertos y `-x`, cuadra.
  - [x] RM3: recorrí los 173; ningún equivalente sale muerto.
  - [x] RM4: tres mutantes de frontera sobre una copia en el scratchpad con los tests de su módulo. `< ttl` → `<=` ⇒
    falla `r6_caducada_se_reconsulta`; `ahora < fallo_hasta` → `<=` ⇒ falla `r6_fallo_sin_lista_previa_...`;
    `>= 500` → `> 500` ⇒ falla `r18_reintenta_los_transitorios[500]`.
  - [x] RM6: lo quitado en `fdb9c58` no era defensivo. `and cambia`: solo exacta y normalizada cambian;
    `_alm or None`: el ALM ya lo filtra `_es_lectura`; `coincide_partida`: test `t16`; `if lista is not None`: la
    clave es canónica y no vacía en origen (`canonizar_codigo_obra`) y queda `or ListaPartidasObra(...)`.
  - [x] RM5: sin equivalentes declarados. [x] «Evidencias» con los cuatro números y los workers. [x] Sin N/A mudos.
- **C4 ter**: [x] Ruta tocada `normalizador_partidas.py`; `aviso` sin `progress/evals_F-076.md`; motivo en §3.
- **C5**: [x] T1–T17 y T5b `[x]` con commit (T18–T20 del humano). [x] Sin artefactos sueltos. [x] `features.json`
  con la spec APROBADA (pasada 2, P2.4).

### 4.1 Requisito ⇒ test

R1–R25 cubiertos (R19–R21 por lectura); la tabla, en `febcaf0` §4.1.

## 5. Cambios requeridos

Ninguno. Los tres de la pasada 1 están aplicados en `4471d72`.

## 6. Automejora (propuesta al humano, no aplicada)

- Los `_indice.json` de `evals/fixtures/` ya tienen casos: o D5 (`aviso` ⇒ `bloqueo`) ya se cumple o el texto de C4 ter
  y de `rutas_sensibles.json` está desfasado.
- Las evals deterministas no pasan por `RunValuationPipeline`.
- El intérprete del arnés no trae FastAPI, así que `app.py` de sv6 nunca se ejecuta. Lo resolvería un intérprete por
  servicio en `servicios.json`.
