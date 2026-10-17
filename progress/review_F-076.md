<!-- progress/review_F-076.md -->
Revisión completa (pasada 1) · `git diff dev...HEAD` (base `a8b9f7d`, HEAD `bceff77`)

# F-076 · Normalizar partidas contra las de la obra · Review (2026-10-17)

**Veredicto: CHANGES_REQUESTED.** El código, los tests y la campaña de mutación están bien. Lo que falla es la
documentación operativa: las MANUAL de F-076 no dan la secuencia exacta combinada con las de F-078, que siguen
pendientes. Hay además dos retoques menores. Son tres cambios de texto, sin tocar código (§5).

## 1. Verificación ejecutada (resultados reales)

- `bash harness/init.sh` (Git Bash, `PYTHONPATH` = comun del worktree, `ARNES_SIN_CACHE=1`: todas las suites en serie
  y sin caché) ⇒ **exit 0, «ENTORNO LISTO»**. Resultados: raíz 1237 passed; sv1 205; sv2 397; sv3 703; **sv4 1549**
  (1 warning); sv5 43; **sv6 444 + 1 skipped**; **sv9 670**; **comun 818 + 3 skipped**.
  `PUERTA COBERTURA` [OK] 97,3 % (583/599, umbral 80 %). `PUERTA TAMAÑO` [OK]. Avisos: `blocked` (F-078), ruff (deuda
  previa), infra sin tests, rutas sensibles [evals] y [ADAPTAR] de otras features.
- Test saltado de `app.py` (§2, #9): lo ejecuté sobre una copia de sv6 en el scratchpad con un intérprete que sí trae
  FastAPI (el venv de sv4 más tenacity/yaml en el `PYTHONPATH`) ⇒ `test_f076_cableado.py` **8 passed**, también
  `test_f076_t11_la_api_cablea_el_normalizador`.
- Evals deterministas (`python -m evals.runner --feature F-076`, sin LLM ni red, informe en el scratchpad): ROJO,
  pero **idéntico línea a línea** al mismo comando sobre `dev` (`a8b9f7d`). No hay regresión: el rojo ya está en `dev`.
- `git status` limpio en el worktree y en el árbol principal después de todo (salvo el `??` previo de F-051).

## 2. Las 10 desviaciones de `impl_F-076.md` §2

| # | Juicio |
|---|---|
| 1 R11 / design §5.2 | **Cabe.** El requisito manda sobre el design. R11 enumera «sin configuración de sigrid-api» entre los casos con motivo. Efecto si se despliega sv6 sin T18: `partidas_obra_no_disponibles` en cabecera, sin revisión. Es inocuo y además sirve de alarma. |
| 2 Guarda de no hoja también en `ambigua` | **Cabe.** Es R5 literal («la lectura no es exacta ⇒ `fuera_de_lista`»). Las dos ramas acaban a revisión; solo cambia el nombre del motivo. Es la opción conservadora (H1). |
| 3 Definición de «lectura» | **Cabe.** Una lectura sin nada alfanumérico ya era `sin_partida` ⇒ `no_aplica`. Por eso es equivalente a R13. |
| 4 `exacta` con espacios recupera la leída; `at_least_one_line_requires_review` | **Cabe.** Lo primero es la regla 6. Lo segundo es el invariante del builder (`valuation_builder.py:1848`). |
| 5 Copia profunda | **Cabe y es necesaria.** IA4 muta el sobre en su sitio. El mutante `deep=False` muere. |
| 6 Alias `_SQL_PARTIDAS_POR_OBRA` | **Cabe.** Es una referencia, no una copia: el test de R15 comprueba la identidad y que no queda `obrparpar`. |
| 7 Tests de F-052 tocados | **Cabe.** Es la consecuencia directa de P7, que está aprobado. Solo se tocan las aserciones que fijaban el `TOLERA`/5000 de partidas y la versión exacta 0.7.0. Es cosmético que `test_f052_r28_proveedores_truncados_lanzan` cubra ahora también partidas y que `..._obras_contratos_y_partidas_toleran...` conserve «partidas» en el nombre. |
| 8 `tenacity` en `requirements.txt` | **Cabe.** R18 la exige y el Dockerfile instala `requirements.txt`. |
| 9 Test de `app.py` saltado | **Cabe, sin hueco real.** El test AST corre siempre y yo ejecuté el de comportamiento con FastAPI (§1). No hay importación circular: `composition` no importa `app`. La limitación ya existía antes (el intérprete del arnés no puede importar `app.py`); la propongo en §6. |
| 10 Separador « · » del `title` | **Cabe.** Es lo que dice design §5.4. |

Ninguna exige volver al humano.

## 3. Puntos expresos del líder

**Fusión con F-078 en sv6.**
- Hay un solo `replace_valuation` con líneas, y recibe `lines = completar_registros(...)`.
- `test_f078_pipeline_todo_replace_valuation_con_lineas_va_tras_completar_registros` sigue vivo y en verde.
- El orden en `run_valuation_pipeline.py` es: normalizar, rama `no_contract`, IA4, `build`, `completar_registros`,
  `anotar` (en su sitio, sin reasignar `lines`) y `replace_valuation`. Lo fija `test_f076_t10_...`.
- `anotar` solo toca `codigo_partida_albaran`, `review_reasons` y `review_required`.
- `completar_registro` no lee la partida: la descripción, la unidad y la cantidad de F-078 no cambian. El sobre
  normalizado solo difiere en `codigo_partida_albaran`.

**Seguridad e infra.**
- `set_partidas_sv6.ps1`:
  - No lleva GUID, URL, `subscriptions/` ni secretos (grep: 0). Toma todo de `00_vars`/`00_capps_vars`.
  - La clave va como `secretref:sigrid-key` sobre `keyvaultref`.
  - Es idempotente: `secret set` y `--set-env-vars` con los mismos valores.
  - Al final comprueba OK/KO, y es UTF-8 con BOM y CRLF.
  - `deploy.ps1` usa `update --image`, que conserva las variables.
- `SigridApiLector`:
  - Solo llama a `RUTA_SQL_READ`.
  - Los logs llevan etiqueta, estado, filas, `base_url` y `database`. No llevan la clave ni el cuerpo
    (`__repr__` también va sin clave; lo comprueba un test con `caplog`).
  - Los mensajes de error no copian el cuerpo.
- `medir_f076_partidas.py`:
  - La conexión se abre con `default_transaction_read_only=on` y se comprueba `SHOW transaction_read_only` antes de
    leer.
  - Hace un único SELECT y usa `NO_TOLERA`.
  - Imprime solo recuentos, y los errores salen sin detalle.
- Lectura del `.env` de sv3 en T19: **aceptable**. «PROHIBIDO tocar `.env`» protege contra modificarlo o subirlo, y
  aquí no se modifica, no se imprime y no sale de la consola del humano. Las variables, eso sí, quedan vivas en esa
  consola: el cambio 3 pide limpiarlas al terminar.

**Rutas sensibles [evals].**
- La exigencia declarada es `aviso` (`rutas_sensibles.json`).
- El motivo está documentado: P8 (aprobado), `impl` §5 y design §10.
- Las evals deterministas sí existen y las ejecuté (§1): sin cambios frente a `dev`. Que el implementer no las
  lanzara no deja hueco, porque `evals/procesos/sv6_build.py` estimula el `ValuationBuilder` directamente: ni
  atraviesa `RunValuationPipeline` ni conoce la lista de la obra. Es decir, **no pueden medir F-076**.
- Lo que medirá F-076 es T19 (script de recuentos sobre producción, en solo lectura).
- C4 ter queda así: con exigencia `aviso`, falta `progress/evals_F-076.md` y el motivo consta aquí.

**MANUAL T18–T20.**
- T18 y T19 traen comandos exactos de PowerShell (`current.md` = `impl` §6).
- **Fallo:** la combinación con F-078 se resuelve con una remisión («sigue entonces el orden de F-078 … con estos
  mismos despliegues»). El bloque literal de T18 encadena `deploy sv6` y `deploy sv4` sin el relleno
  `--aplicar` en medio.
- Hoy F-078 está `blocked` a la espera de sus MANUAL, así que el caso combinado es el esperado y no la excepción.
  Copiar el bloque tal cual rompe el orden obligatorio de F-078 (sv6, relleno, sv4). → Cambio 1.

**Notas de solape para quien fusione después** (`current.md`):
- F-077: compone el `title` (✓ normalizada ⇒ nota de F-076; ⚠ ⇒ aviso de F-077) y ajusta su R22.
- F-075: debe llamar a `anotar` tras `completar_registros` en su rama.
- F-049: conflicto add/add de `partidas.py`, se conserva lo de F-076 y comun pasa a 0.9.0.
- Las tres notas son correctas y suficientes.

## 4. Checkpoints

Nivel de rigor: **`critico`, declarado** en `features.json`. Exige fase RED, cobertura ≥ 80 %, mutación completa con
0 supervivientes sin justificar y RM5.

- **C1:** [x] `init.sh` exit 0. [x] Ficheros del arnés.
- **C2:**
  - [x] Una sola feature `in_progress` (F-076).
  - [x] Rama `feature/F-076-normalizar-partidas`.
  - [x] `current.md`: la sesión activa de F-076 más el bloque `blocked` de F-078, que sigue vigente.
  - [x] Las `done` tienen su resumen en `history.md`.
- **C3:**
  - [x] Hexagonal: los puertos están en `domain/ports`. El lector HTTP y el SELECT están en `infrastructure`. El
    dominio de sv4 importa solo la función pura `normalizar_partida`, y `ruesma_comun.sigrid` no arrastra
    dependencias de E/S.
  - [x] Primera línea con la ruta en todos los ficheros nuevos.
  - [x] `print` solo en el script de medición (permitido por design §3). Sin TODO ni secretos. La única dependencia
    nueva, tenacity, está prevista en R18.
  - [x] Reglas de ARCHITECTURE:
    - sv6 lee `obra_codigo` del merge y no del raw.
    - El nuevo lector consta en la regla 3.
    - No hay cambio de schema ni de importes.
    - Las sintéticas heredan la partida y no se anotan.
- **C3 bis:** N/A. No entra ningún documento externo.
- **C4:**
  - [x] Trazabilidad de requisitos a tests (tabla §4.1).
  - [x] Los unit tests no tocan red ni BBDD: `MockTransport`, SQLite en memoria y puertos falsos.
  - [ ] **Las MANUAL constan, pero no en la secuencia exacta combinada (cambio 1).**
- **C4 bis:**
  - [x] `rigor` declarado.
  - [x] RED con la salida real de los centrales: R5, R15, R23/R24, R9/R10 y R7/R8/R14. T12 y T15 van justificados:
    R16 es «sin cambio» y R22 no es central.
  - [x] Cobertura [OK] 97,3 %.
  - [x] Mutación: 173/173 muertos y 0 supervivientes, sin la cabecera «CAMPAÑA NO VÁLIDA» y con 0 sin veredicto.
  - [x] **Tiempo total 1242,2 s > 60 s: campaña no reejecutada (≈21 min según el informe).** Se aplicaron el
    recálculo puro, RM1–RM6 y RM4:
    - **Recálculo** con `harness.alcance` + `generar_mutantes`: 17 ficheros, 1500 líneas y **173 mutantes**. Coincide.
    - **Coste por mutante:** 1242,2 × 4 / 173 = **28,7 s**.
  - [x] RM1: SHA medido `fdb9c58…`. Desde entonces solo cambian `progress/` y `tasks.md`; ningún fichero del alcance.
  - [x] RM2: `media × W` = 28,7 s, frente a líneas base de 12,6 s (sv6), unos 130 s (comun) y unos 125 s (sv4). La
    media queda dentro de la décima parte (≥ 13 s), así que no hay salto de orden de magnitud. Con 100 % de muertos y
    `-x`, es coherente.
  - [x] RM3: repasé los 173 mutantes y no encontré ningún equivalente marcado como muerto. Los de frontera los
    reproduje (RM4).
  - [x] RM4: probé tres mutantes sobre una copia en el scratchpad con el subconjunto de tests de su módulo:
    - `ahora - leida_en < ttl` → `<=` ⇒ falla `test_f076_r6_caducada_se_reconsulta`;
    - `ahora < fallo_hasta` → `<=` ⇒ falla `test_f076_r6_fallo_sin_lista_previa_...`;
    - `status_code >= 500` → `> 500` ⇒ falla `test_f076_r18_reintenta_los_transitorios[500]`.
  - [x] RM5: no hay ningún «equivalente» declarado. Los de la pasada 1 se eliminaron quitando ramas, no
    declarándolos.
  - [x] RM6: las ramas quitadas en `fdb9c58` no eran defensivas:
    - `motivo in (…) and cambia`: solo `exacta` y `normalizada` cambian.
    - `self._alm or None`: ALM ya se filtra en `_es_lectura`.
    - `or`/`and` de claves `None` en `coincide_partida`: queda cubierto por el test `t16`.
    - El `if lista is not None` del log de la caché: `clave` es canónica y no vacía (`canonizar_codigo_obra`, en
      origen), y queda el `or ListaPartidasObra(...)`.
  - [x] «Evidencias» con los cuatro números y los workers.
  - [x] No hay ningún N/A sin justificar.
- **C4 ter:** [x] Ruta tocada: `normalizador_partidas.py`. La exigencia es `aviso` y el motivo consta en §3.
- **C5:**
  - [x] T1–T17 y T5b `[x]` con sus commits; T18–T20 son del humano.
  - [x] Sin artefactos sueltos.
  - [ ] **La `description` de F-076 en `features.json` dice «PROPUESTA (spec v1, PARADA 1 pendiente …)», pero la spec
    está aprobada (cambio 2).**

### 4.1 Cobertura de requisitos

- **comun** (`test_f076_partidas.py`):
  - R1–R4: `r1_*`, `r2_*`, `r3_*`, `r4_*`.
  - R5: `r5_*`, incluido `03.02`, que es no hoja.
  - R6: `r6_*`, con reloj falso.
- **sv6:**
  - R7, R11, R12, R13: `test_f076_normalizador.py` y `test_f076_pipeline.py`.
  - R8 y R14: `test_f076_pipeline.py`.
  - R9 y R10: `test_f076_normalizador.py`, más `r10` en `test_f076_pipeline.py`.
  - R17 y R18: `test_f076_lector.py`.
  - R22: `test_f076_medicion.py`.
- **sv4:**
  - R15: `test_f076_partidas_sv4.py`.
  - R23–R25: `test_f076_aviso_partida.py`.
- **sv9:** R16 en `test_f076_partida_final.py`.
- **Sin test, verificados por lectura:**
  - R19 (infra): lectura más grep.
  - R20 (docs): ARCHITECTURE, regla 23, porque la 22 ya era de F-078; `sv6.md`; `azure-apps` `8a6f63c`, con el
    árbol limpio.
  - R21 (meta): nomenclatura `test_f076_rN_*` y unit tests sin red.

## 5. Cambios requeridos

1. **`progress/current.md` (bloque «F-076 · MANUAL») y `progress/impl_F-076.md` §6**: sustituir la remisión «sigue
   entonces el orden de F-078» por **un único bloque de PowerShell con la secuencia combinada exacta**, válido
   mientras F-078 siga pendiente:
   1. Árbol principal tras la fusión. En `services\albaran-valoracion-persist`, `pip install "tenacity>=8.2"` y la
      lectura de F-078 T12 (`-m scripts.rellenar_filas_f078`).
   2. En `infra`, cargar `00_vars` y `00_capps_vars`, lanzar `set_partidas_sv6.ps1` y luego `deploy.ps1 -Only sv6`.
   3. En sv6, F-078 T13: `--aplicar` y después la lectura, que debe dar «0».
   4. En `infra`, `deploy.ps1 -Only sv4` y `check_deploy.ps1`.
   5. En sv6, la lectura de F-078 tras sv4, que debe dar «0».
   6. F-078 T14.
   7. F-076 T19 (revalorar y medir) y la comprobación del log de T18.

   Dejar el bloque actual de T18 solo para el caso «F-078 ya cerrada». Añadir también la nota equivalente al bloque
   de F-078 («si F-076 está fusionada, usa la secuencia combinada»), para que las dos MANUAL no se contradigan.
2. **`harness/features.json`, entrada F-076, `description`**: cambiar «PROPUESTA (spec v1, PARADA 1 pendiente,
   preguntas P1-P11)» por el estado real («spec APROBADA 2026-10-16 con P1–P11 por defecto y la ampliación R23–R25»)
   y regenerar `BACKLOG.md` (lo hace `init.sh`).
3. **T19, en el mismo bloque**: tras `-m scripts.medir_f076_partidas`, añadir
   `Remove-Item env:SIGRID_API_BASE_URL, env:SIGRID_API_FUNCTION_KEY, env:SIGRID_API_DATABASE`, para que la clave no
   quede viva en la consola.

Sugerencia opcional (no bloquea): renombrar los dos tests de F-052 afectados por #7 para que el nombre diga lo que
prueban.

## 6. Automejora (propuesta para el humano, no aplicada)

- **`CHECKPOINTS.md` C4 ter y `rutas_sensibles.json`** dicen que «los seis `_indice.json` siguen con la lista de casos
  vacía», pero hoy `evals/fixtures/IA3`, `IA4`, `final` e `inputs` tienen casos. La condición de D5 para pasar de
  `aviso` a `bloqueo` ya se cumple, o el texto está desfasado. Hay que decidirlo y actualizar las dos piezas.
- **Las evals deterministas no atraviesan `RunValuationPipeline`**: lo que vive en el pipeline de sv6 (F-076, F-078)
  queda fuera de ellas. Conviene anotarlo en `evals/README.md`, o bien añadir un proceso que use el pipeline con
  puertos falsos.
- **El intérprete del arnés no trae FastAPI**, así que nada de `interface_adapters/api/app.py` de sv6 se ejecuta en
  `init.sh`. Hay dos salidas: declarar en `harness/servicios.json` un intérprete por servicio, o instalar FastAPI en
  el `.venv` raíz.
