<!-- progress/review_F-076.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (base `a8b9f7d`, HEAD `bceff77`)

# F-076 · Normalizar partidas contra las de la obra · Review (2026-10-17)

**Veredicto: CHANGES_REQUESTED.** Código, tests y mutación correctos. Falla la documentación operativa: las MANUAL de
F-076 no dan la secuencia exacta combinada con las de F-078, aún pendientes. Más dos retoques menores. Son tres cambios
de texto, sin código (§5).

## 1. Verificación ejecutada (resultados reales)

- **`bash harness/init.sh`** (Git Bash, `PYTHONPATH` = comun del worktree, `ARNES_SIN_CACHE=1`: suites en serie y sin
  caché) ⇒ **exit 0, «ENTORNO LISTO»**. Raíz 1237; sv1 205; sv2 397; sv3 703; **sv4 1549**; sv5 43; **sv6 444 + 1
  skipped**; **sv9 670**; **comun 818 + 3 skipped**. `PUERTA COBERTURA` [OK] 97,3 % (583/599, umbral 80 %); `TAMAÑO`
  [OK]. Avisos ajenos o previstos: F-078 `blocked`, ruff, infra sin tests, rutas sensibles [evals], [ADAPTAR].
- **Test saltado de `app.py`**: lo ejecuté sobre una copia de sv6 en el scratchpad con un intérprete con FastAPI (venv
  de sv4 + tenacity/yaml en el `PYTHONPATH`): `test_f076_cableado.py` **8 passed**, incluido el saltado.
- **Evals deterministas** (`python -m evals.runner --feature F-076`, sin LLM ni red, salida al scratchpad): ROJO, pero
  **idéntico línea a línea** al mismo comando sobre `dev` (`a8b9f7d`): sin regresión. `git status` limpio después.

## 2. Las 10 desviaciones de `impl_F-076.md` §2: todas caben; ninguna exige volver al humano

| # | Juicio |
|---|---|
| 1 R11 frente a design §5.2 | Manda el requisito, y R11 enumera «sin configuración». Si sv6 se despliega sin T18: motivo de cabecera sin revisión, inocuo y además avisa. |
| 2 Guarda de no hoja en `ambigua` | Es R5 literal («no exacta ⇒ `fuera_de_lista`»). Las dos ramas van a revisión; solo cambia el motivo. Conservador (H1). |
| 3 «Lectura» | Sin nada alfanumérico ya era `sin_partida` ⇒ `no_aplica`. Equivale a R13. |
| 4 `exacta` con espacios y motivo de cabecera | Regla 6; `at_least_one_line_requires_review` es el invariante del builder (`valuation_builder.py:1848`). |
| 5 Copia profunda | Necesaria: IA4 muta el sobre en su sitio. El mutante `deep=False` muere. |
| 6 Alias `_SQL_PARTIDAS_POR_OBRA` | Referencia, no copia: el test de R15 comprueba la identidad y que no quede `obrparpar`. |
| 7 Tests de F-052 tocados | Consecuencia directa de P7 (aprobado). Solo cambian las aserciones de `TOLERA`/5000 de partidas y la versión 0.7.0. Que dos nombres digan aún «partidas toleran» es cosmético. |
| 8 `tenacity` | La exige R18; el Dockerfile instala `requirements.txt`. |
| 9 `app.py` saltado | Sin hueco real: el test AST corre siempre y el de comportamiento lo ejecuté yo (§1). Sin ciclo de imports. Limitación previa (§6). |
| 10 Separador « · » | El de design §5.4. |

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
  falsos). [ ] **Las MANUAL no traen la secuencia exacta combinada** (cambio 1).
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
- **C5**: [x] T1–T17 y T5b `[x]` con commit (T18–T20 del humano). [x] Sin artefactos sueltos. [ ] **La `description`
  de F-076 en `features.json` dice «PROPUESTA (spec v1, PARADA 1 pendiente …)»** y la spec está APROBADA (cambio 2).

### 4.1 Requisito ⇒ test

| Requisitos | Tests |
|---|---|
| R1–R6 | comun `test_f076_partidas.py` (`r1_*`…`r6_*`; R5 con `03.02` no hoja; R6 con reloj falso) |
| R7, R11–R13 / R8, R14 | sv6 `test_f076_normalizador.py` y `test_f076_pipeline.py` / `test_f076_pipeline.py` |
| R9–R10 / R17–R18 / R22 | `test_f076_normalizador.py` (+ `r10` del pipeline) / `test_f076_lector.py` / `test_f076_medicion.py` |
| R15 / R23–R25 / R16 | sv4 `test_f076_partidas_sv4.py` / sv4 `test_f076_aviso_partida.py` / sv9 `test_f076_partida_final.py` |
| R19, R20, R21 | Por lectura: R19 + grep; R20 = ARCHITECTURE regla 23 (la 22 es de F-078), `sv6.md`, `azure-apps` `8a6f63c` con árbol limpio; R21 por nomenclatura y sin red |

## 5. Cambios requeridos

1. **`progress/current.md` (bloque «F-076 · MANUAL») y `progress/impl_F-076.md` §6.** Sustituir la remisión «sigue
   entonces el orden de F-078» por **un único bloque PowerShell con la secuencia combinada exacta**, válido mientras
   F-078 siga pendiente:
   1. En `services\albaran-valoracion-persist` del árbol principal: `pip install "tenacity>=8.2"` y la lectura de
      F-078 T12 (`-m scripts.rellenar_filas_f078`).
   2. En `infra`: `. .\00_vars.ps1`, `. .\00_capps_vars.ps1`, `.\set_partidas_sv6.ps1`, `.\deploy.ps1 -Only sv6`.
   3. En sv6: `rellenar_filas_f078 --aplicar` y la lectura (debe dar 0).
   4. En `infra`: `.\deploy.ps1 -Only sv4` y `.\check_deploy.ps1`.
   5. En sv6: la lectura de F-078 (debe dar 0). 6. F-078 T14. 7. F-076 T19 y la comprobación del log de T18.
   El bloque actual de T18 queda para «F-078 ya cerrada»; nota simétrica en el de F-078 para que no se contradigan.
2. **`harness/features.json`, F-076, `description`**: «PROPUESTA (spec v1, PARADA 1 pendiente, preguntas P1-P11)» ⇒
   «spec APROBADA el 2026-10-16: P1–P11 por defecto y ampliación R23–R25». `init.sh` regenera `BACKLOG.md`.
3. **T19, mismo bloque**: tras `-m scripts.medir_f076_partidas`, añadir
   `Remove-Item env:SIGRID_API_BASE_URL, env:SIGRID_API_FUNCTION_KEY, env:SIGRID_API_DATABASE`, para que la clave no
   quede viva en la consola.

## 6. Automejora (propuesta al humano, no aplicada)

- C4 ter de `CHECKPOINTS.md` y `rutas_sensibles.json` dicen que los `_indice.json` están vacíos, pero `evals/fixtures/`
  ya tiene casos: o D5 (`aviso` ⇒ `bloqueo`) ya se cumple o el texto está desfasado. Además, las evals deterministas no
  pasan por `RunValuationPipeline` (F-076 y F-078 quedan fuera) y el intérprete del arnés, sin FastAPI, nunca ejecuta
  `app.py` de sv6: un intérprete por servicio en `harness/servicios.json` lo cerraría.
