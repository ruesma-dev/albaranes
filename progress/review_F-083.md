<!-- progress/review_F-083.md -->
Revisión incremental desde 96a59a3 (pasada 2) · HEAD `d261a05` · la pasada 1 fue completa, sobre `96a59a3043db3da53877f18e9353dcd61caab3a2`

# F-083 · Review

**Veredicto: APPROVED.**
- Pasada 1: CHANGES_REQUESTED solo por papeleo. El código está bien, y la campaña de mutación que
  lanzó el reviewer es VÁLIDA: 366 mutantes, 366 muertos, 0 supervivientes.
- Pasada 2: `d261a05` aplica los cambios 1 y 2.

**Rigor:** `critico`, declarado. Exige fase RED, cobertura ≥ 80 %, campaña completa con 0
supervivientes y MANUAL con comando exacto. La MANUAL (T13–T15) queda pendiente del humano.

## Pasada 2 (delta `96a59a3..d261a05`)

- **El delta es solo documental.** `git diff --name-only` toca solo `progress/` (`current.md`,
  `impl_F-083*.md`, `inventario_mutacion_F-039.md`, `mutacion_F-083.md`, esta review) y
  `specs/.../tasks.md`. Ni código ni tests: la campaña sobre `96a59a3` sigue valiendo (RM1) y no se
  repite.
- **Cambio 1, hecho.**
  - `progress/mutacion_F-083.md` es idéntico al informe de la herramienta: `diff` solo da la
    línea 1 (la ruta).
  - La fila del inventario es `VÁLIDA`, con «fuera de `services/`» = Sí (correcto: `evals/`),
    3 workers, 366/366 y SHA completo. El recuento pasa a 47 / 11.
  - T16 marcada `[x]`.
  - En `impl_F-083.md` desaparece «Pendiente para cerrar» y «Evidencias» trae la campaña válida
    con sus 3 workers. `impl_F-083_mutacion.md` la enlaza.
- **Cambio 2, hecho** (`current.md`).
  - Fuera «Decisiones abiertas de la PARADA 1» y «Qué propone»; el estado de T16 está al día.
  - O1 y O2 van antes de T13. El aviso de IA3/IA4 dice ahora «no hasta F-084» y alcanza también
    al humo de IA3.
  - Nota menor, no bloquea: la última línea aún remite a «los comandos de design §8», que traen
    la lista vieja de 11 modelos. Los que valen son los de `current.md`.
- **`bash harness/init.sh` en el worktree sobre `d261a05`: exit 0, `ENTORNO LISTO`.**
  - Tests: raíz 1575 (incluye `test_f039_*`, que valida el inventario), sv1 205, sv2 485,
    sv3 1576, sv4 1774, sv5 46, sv6 473 (+1 skip), sv9 673; comun en verde por caché.
  - Puertas: COBERTURA `[OK] 99.4 %`, TAMAÑO `[OK]`, RUTAS SENSIBLES `[AVISO]` (C4 ter, aceptado).
- **Checkpoints** `[ ]` de la pasada 1 que pasan a `[x]`: C2, C4 bis (mutación y «Evidencias») y C5.

## Pasada 1

### Lo que ejecutó el reviewer

- **`bash harness/init.sh`: exit 0, `ENTORNO LISTO`.**
  - Tests: raíz 1575, sv1 205, sv2 485, sv3 1576, sv4 1774, sv5 46, sv6 473 (+1 skip), sv9 673;
    comun en verde por caché.
  - Puertas: COBERTURA `[OK] 99.4 %` (957/963), TAMAÑO `[OK]`, RUTAS SENSIBLES `[AVISO]` (C4 ter).
  - Aviso: sv1–sv9 importan `ruesma_comun` del repo principal, así que T11 solo lo prueba la suite
    de comun, la del worktree. Riesgo bajo: el valor por defecto es el de hoy.
- **Campaña repetida con la máquina libre de este repo**:
  `python -m harness.mutacion --feature F-083 --workers 3 --salida <scratchpad>`. Corrían 2 suites
  de otros proyectos.
- **Recálculo puro** (`alcance_de_feature` + `generar_mutantes`): 11 ficheros, 2105 líneas,
  366 mutantes. Cuadra fichero a fichero con c1, c2 y la campaña del reviewer.
- **Barrido de secretos** (`sk-`, `AIza`, GUID, IP, `password`, `api_key=`): limpio. Árbol limpio.

### Checkpoints (pasada 1; los `[ ]` se cierran en la pasada 2)

- **C1** [x] init.sh exit 0 · [x] están los 7 ficheros del arnés.
- **C2** [x] una sola `in_progress` · [x] rama de la feature · [ ] `current.md` (cambio 2) ·
  [x] historia de las `done`.
- **C3**
  - [x] Hexagonal: todo vive en `evals/`; sv2/sv5 solo se importan dentro de los subprocesos y
    comun recibe un parámetro de su adaptador LLM.
  - [x] Primera línea con la ruta en los 19 `.py` · [x] los `print` son la salida del CLI; sin
    TODO, sin secretos, sin dependencias nuevas.
  - [x] Trampas del monorepo: N/A justificado. No hay BBDD, schema ni importes; el build de sv6
    se usa tal cual, vía `runner.evaluar_valoracion`.
- **C3 bis** N/A: no toca `docs/referencia/`.
- **C4**
  - [x] R1–R38 trazados (tabla abajo) y en verde.
  - [x] Sin red ni BBDD: van dobles de subprocesos, build y SDK. Con `--estimar`, sin clave o con
    tope, las fábricas no se llaman.
  - [x] MANUAL T13–T15 en `current.md`, con el PowerShell exacto.
- **C4 bis**
  - [x] `rigor` declarado · [x] fase RED de T1–T11 con la traza real · [x] cobertura 99,4 %.
  - [ ] **Mutación** (cambio 1). `_c1`/`_c2` son «NO VÁLIDA». La del reviewer es VÁLIDA: **366/366
    muertos, 0 supervivientes, 0 timeouts**, 21.907,1 s, 3 workers, SHA `96a59a3…`.
  - [x] Muertos comprobados con campaña propia · [x] coste por mutante: 21.907,1 × 3 ÷ 366 = 179,6 s.
  - [x] RM1: el SHA medido es HEAD; desde `6c40149` solo cambió `progress/`.
  - [x] RM2: base 306–324 s; media 59,9 s × 3 = 179,7 s (0,57× la base, por `-x`); 366 × 59,9 ≈ 21.923 s.
  - RM3: ningún muerto parece equivalente. RM4: reproducido en copia el mutante 328 (`medidor.py:133`, `ensure_ascii=False`→`True`). Lo
    caza `test_f083_t16_el_fichero_de_registros_crea_su_carpeta_y_guarda_utf8`: es observable.
  - RM5: N/A justificado (sin supervivientes ni equivalentes declarados).
  - [x] RM6: `6c40149` no quita ninguna guarda. Solo defectos sin uso, `text=True` (redundante),
    `ensure_ascii` en el stdin e `insert(0)`.
  - Campaña manual: N/A, no la hubo · [x] 0 supervivientes, nada en `PENDIENTE`.
  - [ ] «Evidencias» cita las dos campañas no válidas y no da los workers de la válida (cambio 1).
- **C4 ter** (exigencia `aviso`): [ ] falta `progress/evals_F-083.md`. Motivo aceptado:
  el defecto de T11 deja la petición como hoy (`test_f083_r38_por_defecto_*` fija los `kwargs` y
  el mutante `True`→`False` muere). La pasada con LLM cuesta dinero y la decide el humano.
- **C5** [ ] T16 sin `[x]` (cambio 1); T13–T15 son MANUAL del humano · [x] un commit `F-083 Tn:`
  por tarea · [x] sin temporales · [x] `features.json` coherente.

### Requisito → test (resumen; detalle en `tests/test_f083_*.py`)

| R | Tests | R | Tests |
|---|---|---|---|
| R1–R3 | `test_f083_precios.py` (R3 lee `infra/create_capps.ps1`) | R19 | `sv2_r19_*`, `tope_alcanzado_*`, `r19_cortado_por_tope` |
| R4–R7, R10 | `test_f083_costes.py` | R20–R23 | `sv2_r20/r21_*`, `sv5_r22/r23_*`, `bloque_ia3/ia4_*` (build real de sv6) |
| R8–R10 | `test_f083_medidor.py`, con centinelas | R24–R26 | `*_r24_*`, `repeticion_*`, `bloque_muerto_*`, `r26_*` |
| R11–R18 | `r11`…`r18_*`, con fronteras | R27, R30–R35 | `test_f083_decision.py`, un test por umbral y frontera |
| R28–R29, R37 | `test_f083_informe.py` (`r29_r37_*`); `comprobar_claves` solo da nombres | R36 | en `tests/` solo se añade; `test_f083_runner_*`; init.sh no lanza el comparador |
| R38 | comun `test_f083_r38_*` (4) | | |

### Lo que pidió el líder

- **R-1 y R-3 fuera de alcance: correcto según la spec.**
  - R-1: R22 mide IA3 contra su libro con INPUTS, y el banco es cosa de F-084. Comprobado: 52 de
    los 59 casos de INPUTS no traen `contrato_lineas`.
  - R-3: el design §2 deja escrito «decide el parseo de hoy» y F-086 lleva el arreglo. Si Opus 5.5
    responde en texto, la llamada sale `ERROR` pagado (R10), con «Parada» `end_turn` a la vista.
- **¿Da por medido lo que no mide?** En lo que pide la spec, no; quedan dos rincones (O2, O4).
- **R3 hoy y tras F-085:** O1.

## Observaciones para el humano (no bloquean)

- **O1 · Producción cambió el 20-10, según el líder** (no lo he leído en Azure).
  - La tabla sigue a `create_capps.ps1`, como pide R3: IA1 `gemini-3.7-flash`, IA2 `gpt-5.4`,
    IA3/IA4 `claude-opus-4-8`. **R3 pasa hoy.**
  - Producción ya usa Argon en IA1 y `gpt-6.1-sol` en IA2–IA4. Pagar T13–T15 ahora compararía
    contra modelos retirados, y prepararía IA2 con 3.7-flash e IA4 con Opus 4.8.
  - Simulado con F-085 R1: **R3 falla en IA1 e IA2**, que es lo correcto. **En IA3/IA4 pasa sin
    deber**: lee `ANTHROPIC_MODEL`, que F-085 mantiene, y no ve `IA3_PROVIDER/IA4_PROVIDER=openai`.
  - Propuesta: F-085 antes de T13. Después, quien se fusione segunda (D4 de F-085) ajusta
    `referencias` y `papel` y hace que R3 lea el proveedor de sv5.
- **O2 · El banco de IA3/IA4 no discrimina**: R33 podría decir «cambiar» por puro ahorro. No pagar IA3/IA4 hasta F-084.
- **O3 · F-085 se contradice.** Su P1 = (a) y su §7.1 dan el arreglo de `_parse_response` a
  «F-083 T11»; su P3 y F-086 lo dan a F-086. Hay que corregir el texto de F-085.
- **O4 · `fallo_medidor` cuenta 0 USD sin avisar.**
  - `Metricas.fallos_medidor` no sale en ningún informe, así que R19 y `GASTO:` se quedarían
    cortos en silencio. Improbable; conviene un AVISO en una ficha de `evals/`.
- **O5 · Si el padre revienta después de pagar, `GASTO:` no se escribe.** Lo pagado solo queda en
  `registros_*.jsonl`. Propuesta: escribirlo en un `finally`, en la misma ficha que O4.
- **O6 · Desviación de R6, documentada.** Un campo opcional ausente (caché, pensamiento) cuenta 0
  sin marcar `uso_incompleto`. Es razonable; pide el visto bueno del humano.

**Automejora (propuesta, no aplicada)** para `reviewer.md`: si las campañas del implementer son
NO VÁLIDAS y el reviewer repite la campaña con `--salida`, el cambio requerido es copiar ese
informe más su fila de inventario, sin una tercera campaña. Aquí la campaña costó unas 6 h.
